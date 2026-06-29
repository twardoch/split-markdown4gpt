#!/usr/bin/env python3
# this_file: src/split_markdown4gpt/splitter.py
"""Core splitter logic for split-markdown4gpt.

Splits large Markdown documents into token-bounded chunks that respect
heading hierarchy and never cut mid-sentence, using tiktoken for counting
and mistletoe for AST parsing.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Generator
from functools import cache
from io import TextIOWrapper
from pathlib import Path
from typing import Any

try:
    import regex as re
except ImportError:
    import re  # type: ignore[no-redef]

import frontmatter
import tiktoken
from mistletoe import Document, block_token, markdown_renderer
from syntok.segmenter import analyze as syntok_analyze


def meta_data(md: str) -> tuple[dict, str]:
    """Strip YAML front matter from a Markdown string.

    Supports both the ``frontmatter`` and ``python-frontmatter`` packages.

    Args:
        md: Raw Markdown content, possibly with YAML front matter.

    Returns:
        A ``(metadata_dict, body_str)`` tuple.  ``metadata_dict`` is empty
        when no front matter is present; ``body_str`` is the Markdown without
        the front matter block.
    """
    try:
        if hasattr(frontmatter, "Frontmatter"):
            # frontmatter package
            metadata = frontmatter.Frontmatter.read(md)
            meta = metadata["attributes"]
            data = metadata["body"]
        else:
            # python-frontmatter package (the common one)
            metadata = frontmatter.loads(md)
            meta, data = metadata.metadata, metadata.content
    except Exception:
        meta, data = None, md  # gracefully degrade on parse errors

    return meta or {}, data or md


#: Published context-window sizes for common OpenAI models.
OPENAI_MODELS: dict[str, int] = {
    "gpt-4": 8192,
    "gpt-4-32k": 32768,
    "gpt-4-32k-0613": 32768,
    "gpt-4-0613": 8192,
    "gpt-4-turbo": 128000,
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-3.5-turbo": 4096,
    "gpt-3.5-turbo-0613": 4096,
    "gpt-3.5-turbo-16k": 16384,
    "gpt-3.5-turbo-16k-0613": 16384,
}

RE_NEWLINES = re.compile(r"\n{3,}")


class MarkdownLLMSplitter:
    """Split a Markdown document into token-bounded sections for LLM ingestion.

    The splitter works in three passes:

    1. **Parse** — ``mistletoe`` builds an AST of the document, keyed by
       heading level.
    2. **Count** — ``tiktoken`` tallies tokens recursively and caches results.
    3. **Pack** — sections are greedily accumulated until the token budget is
       exhausted, then flushed.  Individual sections that exceed the limit are
       further split at sentence boundaries via ``syntok``.

    Attributes:
        gptoker: Tiktoken encoding instance used for token counting.
        gptok_limit: Maximum tokens allowed per output chunk.
        md_meta: Front-matter metadata extracted from the source document.
        md_str: Source Markdown body (after front-matter stripping).
        md_doc: Parsed ``mistletoe.Document``.
        md_dict: Nested dict tree representing the heading hierarchy.
        md_path: Resolved path of the source file (when loaded from disk).
        md_sections: List of ``{"md": str, "gptok_size": int}`` dicts produced
            by :meth:`build`.

    Args:
        gptok_model: Tiktoken model name; determines the encoding and the
            default token limit.  Defaults to ``"gpt-3.5-turbo"``.
        gptok_limit: Hard token ceiling per chunk.  Defaults to the model's
            published context-window size (see :data:`OPENAI_MODELS`).
    """

    def __init__(
        self,
        gptok_model: str = "gpt-3.5-turbo",
        gptok_limit: int | None = None,
    ) -> None:
        self.gptoker = tiktoken.encoding_for_model(gptok_model)
        self.gptok_limit = gptok_limit or OPENAI_MODELS.get(gptok_model, 2048)
        self.md_meta: dict = {}
        self.md_str: str = ""
        self.md_doc: Document = Document([])
        self.md_dict: defaultdict = defaultdict(list)
        self.md_path: Path = Path()
        self.md_sections: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Loading helpers
    # ------------------------------------------------------------------

    def load_md_path(self, md_path: Path | str) -> None:
        """Load Markdown from a file path.

        Args:
            md_path: Path to the Markdown file.
        """
        self.md_path = Path(md_path).resolve()
        with open(self.md_path, encoding="utf-8") as md_file:
            self.load_md_file(md_file)

    def load_md_file(self, md_file: TextIOWrapper) -> None:
        """Load Markdown from an open file-like object.

        Args:
            md_file: Readable file-like object containing Markdown content.
        """
        self.load_md_str(md_file.read())

    def load_md_str(self, md_str: str) -> None:
        """Load Markdown from a plain string.

        Front matter is stripped and stored in :attr:`md_meta`.

        Args:
            md_str: Raw Markdown content.
        """
        self.md_meta, self.md_str = meta_data(md_str)

    def load_md(self, md: str | Path | TextIOWrapper) -> None:
        """Dispatch to the appropriate loader based on ``md`` type.

        Args:
            md: Markdown content as a string, :class:`pathlib.Path`, or
                file-like object.

        Raises:
            TypeError: When ``md`` is not one of the supported types.
        """
        if hasattr(md, "read"):
            self.load_md_file(md)  # type: ignore[arg-type]
        elif isinstance(md, Path):
            self.load_md_path(md)
        elif isinstance(md, str):
            # Could be a file path or raw Markdown — prefer raw if it looks
            # like Markdown (contains newlines), otherwise try as a path.
            self.load_md_str(md)
        else:
            raise TypeError("md must be a file-like object, Path, or str")

    # ------------------------------------------------------------------
    # Token counting
    # ------------------------------------------------------------------

    @cache
    def gpttok_size(self, text: str) -> int:
        """Count GPT tokens in *text* using the configured encoding.

        Results are cached so repeated calls on the same string are free.

        Args:
            text: The string to tokenize.

        Returns:
            Number of tokens.
        """
        return len(self.gptoker.encode(text))

    # ------------------------------------------------------------------
    # AST → dict tree
    # ------------------------------------------------------------------

    def build_md_dict(self) -> None:
        """Build :attr:`md_dict` from the current :attr:`md_str`.

        The dict is keyed by heading level (int).  Each heading entry is a
        nested dict with ``"gptok_size"`` and ``"children"`` keys; leaf
        entries (paragraphs, code blocks, etc.) also carry ``"md"``
        containing the rendered Markdown fragment.
        """
        self.md_doc = Document(self.md_str)
        current_level = 0
        current_dict = self.md_dict
        dict_stack: list[defaultdict] = [current_dict]

        for child in self.md_doc.children:
            if isinstance(child, block_token.Heading):
                new_dict: dict[str, Any] = {
                    "gptok_size": 0,
                    "children": defaultdict(list),
                }
                if child.level > current_level:
                    current_dict[child.level].append(new_dict)
                    current_dict = new_dict["children"]
                    dict_stack.append(current_dict)
                else:
                    dict_stack = dict_stack[: child.level]
                    current_dict = dict_stack[-1]
                    current_dict[child.level].append(new_dict)
                    current_dict = new_dict["children"]
                current_level = child.level
            if isinstance(child, block_token.BlockToken):
                new_doc = Document([])
                new_doc.children.append(child)
                with markdown_renderer.MarkdownRenderer() as renderer:
                    fragment = renderer.render(new_doc)
                fragment_dict: dict[str, Any] = {
                    "md": fragment,
                    "gptok_size": self.gpttok_size(fragment),
                }
                current_dict[current_level].append(fragment_dict)

    def calculate_sizes(self, md_dict: dict) -> int:
        """Recursively accumulate token sizes into each node's ``"gptok_size"``.

        Mutates *md_dict* in-place and returns the total token count.

        Args:
            md_dict: The Markdown dict tree (or subtree) to process.

        Returns:
            Total token count for the subtree.
        """
        total_size = 0
        for _key, value in md_dict.items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        if "children" in item:
                            item["gptok_size"] = self.calculate_sizes(item["children"])
                        if "gptok_size" in item:
                            total_size += item["gptok_size"]
        return total_size

    # ------------------------------------------------------------------
    # Section packing
    # ------------------------------------------------------------------

    def process_item(
        self,
        item: dict,
        current_section: list[str],
        current_size: int,
        md_sections: list[dict[str, Any]],
    ) -> tuple[list[str], int]:
        """Recursively process one node from the Markdown dict tree.

        Leaf nodes (those with ``"md"``) are delegated to :meth:`process_md`.
        Branch nodes (those with ``"children"``) are traversed depth-first.

        Args:
            item: A node from the dict tree.
            current_section: Accumulating list of Markdown fragments for the
                current output chunk.
            current_size: Running token count for *current_section*.
            md_sections: Completed chunks collected so far.

        Returns:
            Updated ``(current_section, current_size)`` pair.
        """
        if "children" in item:
            for child in item["children"].values():
                for subitem in child:
                    current_section, current_size = self.process_item(
                        subitem, current_section, current_size, md_sections
                    )
        if "md" in item:
            current_section, current_size = self.process_md(
                item, current_section, current_size, md_sections
            )
        return current_section, current_size

    def prep_section(
        self, section_text: str, size: int | None = None
    ) -> dict[str, Any]:
        """Normalise excessive blank lines and wrap in a section dict.

        Args:
            section_text: Raw Markdown content for the section.
            size: Pre-computed token count; recalculated when *None*.

        Returns:
            ``{"md": str, "gptok_size": int}`` dict.
        """
        if not size:
            size = self.gpttok_size(section_text)
        return {"md": RE_NEWLINES.sub("\n\n", section_text), "gptok_size": size}

    def process_md(
        self,
        item: dict,
        current_section: list[str],
        current_size: int,
        md_sections: list[dict[str, Any]],
    ) -> tuple[list[str], int]:
        """Add one Markdown leaf to the current chunk, flushing when full.

        When a single leaf exceeds the token limit, it is split further at
        sentence boundaries via ``syntok``.

        Args:
            item: Leaf node with ``"md"`` and ``"gptok_size"`` keys.
            current_section: Accumulating fragment list.
            current_size: Running token count.
            md_sections: Completed chunks.

        Returns:
            Updated ``(current_section, current_size)`` pair.
        """
        if item["gptok_size"] > self.gptok_limit:
            # Leaf is too large — split at sentence boundaries.
            for syntok_paragraph in syntok_analyze(item["md"]):
                for syntok_sentence in syntok_paragraph:
                    sentence = (
                        "".join(
                            token.spacing + token.value for token in syntok_sentence
                        ).lstrip()
                        + " "
                    )
                    sentence_size = self.gpttok_size(sentence)
                    if current_size + sentence_size <= self.gptok_limit:
                        current_section.append(sentence)
                        current_size += sentence_size
                    else:
                        md_sections.append(
                            self.prep_section("".join(current_section), current_size)
                        )
                        current_section = [sentence]
                        current_size = sentence_size
                current_section.append("\n\n")
        elif current_size + item["gptok_size"] <= self.gptok_limit:
            current_section.append(item["md"] + "\n")
            current_size += item["gptok_size"]
        else:
            # Flush current chunk and start a new one.
            md_sections.append(
                self.prep_section("".join(current_section), current_size)
            )
            current_section = [item["md"] + "\n"]
            current_size = item["gptok_size"]
        return current_section, current_size

    def get_sections_from_md_dict_by_limit(self, md_dict: dict) -> list[dict[str, Any]]:
        """Walk the dict tree and pack fragments into token-bounded chunks.

        Args:
            md_dict: Root of the Markdown dict tree produced by
                :meth:`build_md_dict`.

        Returns:
            List of ``{"md": str, "gptok_size": int}`` section dicts.
        """
        md_sections: list[dict[str, Any]] = []
        current_section: list[str] = []
        current_size = 0

        for _key, value in md_dict.items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        current_section, current_size = self.process_item(
                            item, current_section, current_size, md_sections
                        )
        if current_section:
            md_sections.append(
                self.prep_section("".join(current_section), current_size)
            )
        return md_sections

    # ------------------------------------------------------------------
    # High-level API
    # ------------------------------------------------------------------

    def build(self) -> None:
        """Parse the loaded Markdown and populate :attr:`md_sections`.

        Call :meth:`load_md` (or one of the ``load_md_*`` variants) first.
        """
        self.build_md_dict()
        self.calculate_sizes(self.md_dict)
        self.md_sections = self.get_sections_from_md_dict_by_limit(md_dict=self.md_dict)

    def list_section_dicts(self) -> list[dict[str, Any]]:
        """Return all section dicts as a list.

        Returns:
            List of ``{"md": str, "gptok_size": int}`` dicts.
        """
        return list(self.gen_section_dicts())

    def gen_section_dicts(self) -> Generator[dict[str, Any], None, None]:
        """Yield section dicts one by one.

        Yields:
            ``{"md": str, "gptok_size": int}`` dicts.
        """
        return (
            {"md": section["md"], "gptok_size": section["gptok_size"]}
            for section in self.md_sections
        )

    def list_section_texts(self) -> list[str]:
        """Return section Markdown strings as a list.

        Returns:
            List of Markdown content strings, one per output chunk.
        """
        return list(self.gen_section_texts())

    def gen_section_texts(self) -> Generator[str, None, None]:
        """Yield section Markdown strings one by one.

        Yields:
            Markdown content string for each output chunk.
        """
        return (section["md"] for section in self.md_sections)

    def split(self, md: str | Path | TextIOWrapper) -> list[str]:
        """Load *md*, split it, and return the chunk texts.

        This is a convenience method combining :meth:`load_md` and
        :meth:`build`.

        Args:
            md: Markdown content as a string, :class:`pathlib.Path`, or
                file-like object.

        Returns:
            List of Markdown strings, each within the token limit.
        """
        self.load_md(md)
        self.build()
        return self.list_section_texts()


def split(
    md: str | Path | TextIOWrapper,
    model: str = "gpt-3.5-turbo",
    limit: int | None = None,
) -> list[str]:
    """Split a Markdown document into token-bounded chunks.

    Convenience wrapper around :class:`MarkdownLLMSplitter`.

    Args:
        md: Markdown content as a string, :class:`pathlib.Path`, or
            file-like object.
        model: Tiktoken model name used for token counting.  Defaults to
            ``"gpt-3.5-turbo"``.
        limit: Maximum tokens per chunk.  Defaults to the model's published
            context-window size.

    Returns:
        List of Markdown strings, each within *limit* tokens.

    Example::

        >>> chunks = split("large_doc.md", model="gpt-4", limit=6000)
        >>> for chunk in chunks:
        ...     print(len(chunk), "chars")
    """
    md_splitter = MarkdownLLMSplitter(gptok_model=model, gptok_limit=limit)
    return md_splitter.split(md)
