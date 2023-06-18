#!/usr/bin/env python3
from collections import defaultdict, namedtuple
from functools import lru_cache
from io import TextIOWrapper
from pathlib import Path
from typing import Any, Dict, Generator, List, Tuple, Union

try:
    import regex as re
except ImportError:
    import re

import frontmatter
import tiktoken
from mistletoe import Document, block_token, markdown_renderer, span_token
from syntok.segmenter import analyze as syntok_analyze
from yaml.parser import ParserError

OPENAI_MODELS = {
    "gpt-4": 8192,
    "gpt-4-32k": 32768,
    "gpt-4-32k-0613": 32768,
    "gpt-4-0613": 8192,
    "gpt-3.5-turbo": 4096,
    "gpt-3.5-turbo-0613": 4096,
    "gpt-3.5-turbo-16k": 16384,
    "gpt-3.5-turbo-16k-0613": 16384,
}

RE_NEWLINES = re.compile("\n{3,}")

Section = namedtuple("Section", ("md", "size"))


class MarkdownLLMSplitter:
    """
    A class to split Markdown files into sections according to GPT token size limits.
    
    Attributes:
        gptoker: GPT tokenizer instance used to calculate token sizes.
        gptok_limit: The maximum number of GPT tokens allowed per section.
        md_meta: Metadata found in the source Markdown file.
        md_str: The source Markdown string.
        md_doc: The parsed source Markdown document as a mistletoe Document instance.
        md_dict: A dictionary representing the structure of the Markdown document.
        md_path: The absolute path to the source Markdown file.
        md_sections: List of sections (named tuples) containing the Markdown content and its size in tokens.

    Args:
        gptok_model: The GPT tokenizer model to use for calculating token sizes, defaults to "gpt-3.5-turbo".
        gptok_limit: The maximum number of GPT tokens allowed per section, defaults to the model's maximum tokens.
    """

    def __init__(
        self, gptok_model: str = "gpt-3.5-turbo", gptok_limit: int = None
    ) -> None:
        self.gptoker = tiktoken.encoding_for_model(gptok_model)
        self.gptok_limit = gptok_limit or OPENAI_MODELS.get(gptok_model, 2048)
        self.md_meta = {}
        self.md_str = ""
        self.md_doc = Document([])
        self.md_dict = defaultdict(list)
        self.md_path = Path()
        self.md_sections = []

    def load_md_path(self, md_path: Union[Path, str]) -> None:
        """
        Load a Markdown file from a file path.

        Args:
            md_path: The file path to the source Markdown file.
        """
        self.md_path = Path(md_path).resolve()
        with open(self.md_path, "r") as md_file:
            self.load_md_file(md_file)

    def load_md_file(self, md_file: TextIOWrapper) -> None:
        """
        Load a Markdown file from a file-like object.

        Args:
            md_file: The file-like object containing the source Markdown content.
        """
        file_content = md_file.read()
        parsed = frontmatter.loads(file_content)
        self.md_meta = parsed.metadata
        self.md_str = parsed.content

    def load_md_str(self, md_str: str) -> None:
        """
        Load a Markdown file from a string.

        Args:
            md_str: The source Markdown content as a string.
        """
        self.md_str = md_str

    def load_md(self, md: Union[str, Path, TextIOWrapper]) -> None:
        """
        Load a Markdown file from a string, file path, or file-like object.

        Args:
            md: The source Markdown content, can be a string, file path or file-like object.
        """
        if hasattr(md, "read"):
            self.load_md_file(md)
        elif isinstance(md, Path):
            self.load_md_path(md)
        elif isinstance(md, str):
            self.load_md_str(md)
        else:
            raise TypeError("md must be a file-like object, Path or str")

    @lru_cache(maxsize=None)
    def gpttok_size(self, text: str) -> int:
        """
        Calculates the number of GPT tokens in a text string.

        Args:
            text: The text string to calculate the token size.

        Returns:
            The number of GPT tokens in the text string.
        """
        return len(list(self.gptoker.encode(text)))

    def build_md_dict(self) -> None:
        """
        Builds a dictionary representing the structure of the source Markdown document.
        """
        self.md_doc = Document(self.md_str)
        current_level = 0
        current_dict = self.md_dict
        dict_stack = [current_dict]

        for child in self.md_doc.children:
            if isinstance(child, block_token.Heading):
                new_dict = {"size": 0, "children": defaultdict(list)}
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
                fragment_dict = {"md": fragment, "size": self.gpttok_size(fragment)}
                current_dict[current_level].append(fragment_dict)

    def calculate_sizes(self, md_dict: Dict) -> int:
        """
        Recursively calculates the total size of GPT tokens in the provided Markdown dictionary.

        Args:
            md_dict: The Markdown dictionary to calculate token sizes.

        Returns:
            The total number of GPT tokens in the Markdown dictionary.
        """
        total_size = 0
        for key, value in md_dict.items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        if "children" in item:
                            item["size"] = self.calculate_sizes(item["children"])
                        if "size" in item:
                            total_size += item["size"]
        return total_size

    def process_item(
        self,
        item: Dict,
        current_section: List[str],
        current_size: int,
        md_sections: List[Section],
    ) -> Tuple[List[str], int]:
        """
        Processes an item in the Markdown dictionary and adds it to the appropriate section.

        Args:
            item: The Markdown item to process.
            current_section: The current section being built as a list of strings.
            current_size: The current size of the section in GPT tokens.
            md_sections: The list of sections (named tuples) being built.

        Returns:
            A tuple containing the updated current_section and the current_size.
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

    def prep_section(self, section_text: str, size: int = None) -> Section:
        """
        Prepares a section by removing excessive newlines and calculating the section size if not provided.

        Args:
            section_text: The Markdown content of the section.
            size: The size of the section in GPT tokens, defaults to None (automatically calculated).

        Returns:
            A Section named tuple containing the prepared Markdown content and its size in tokens.
        """
        if not size:
            size = self.gpttok_size(section_text)
        return Section(RE_NEWLINES.sub("\n\n", section_text), size)

    def process_md(
        self,
        item: Dict,
        current_section: List[str],
        current_size: int,
        md_sections: List[Section],
    ) -> Tuple[List[str], int]:
        """
        Processes a Markdown item and adds it to the appropriate section.

        Args:
            item: The Markdown item to process.
            current_section: The current section being built as a list of strings.
            current_size: The current size of the section in GPT tokens.
            md_sections: The list of sections (named tuples) being built.

        Returns:
            A tuple containing the updated current_section and the current_size.
        """
        if item["size"] > self.gptok_limit:
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
        elif current_size + item["size"] <= self.gptok_limit:
            current_section.append(item["md"] + "\n")
            current_size += item["size"]
        else:
            md_sections.append(
                self.prep_section("".join(current_section), current_size)
            )
            current_section = [item["md"] + "\n"]
            current_size = item["size"]
        return current_section, current_size

    def get_sections_from_md_dict_by_limit(self, md_dict: Dict) -> List[Section]:
        """
        Builds the sections from the provided Markdown dictionary by fitting the content within token limits.

        Args:
            md_dict: The Markdown dictionary to build sections from.

        Returns:
            A list of sections (named tuples) containing the Markdown content and its size in tokens.
        """
        md_sections = []
        current_section = []
        current_size = 0

        for key, value in md_dict.items():
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

    def build(self) -> None:
        """
        Builds the sections by processing the loaded Markdown document.
        """
        self.build_md_dict()
        self.calculate_sizes(self.md_dict)
        self.md_sections = self.get_sections_from_md_dict_by_limit(md_dict=self.md_dict)

    def list_section_dicts(self) -> List[Dict[str, Union[str, int]]]:
        """
        Returns a list of section dictionaries containing the Markdown content and its size.

        Returns:
            A list of dictionaries with keys 'md' and 'size'.
        """
        return list(self.gen_section_dicts())

    def gen_section_dicts(self) -> Generator[Dict[str, Union[str, int]], None, None]:
        """
        Generator that yields section dictionaries containing the Markdown content and its size.
        """
        return (
            {"md": section.md, "size": section.size} for section in self.md_sections
        )

    def list_section_texts(self) -> List[str]:
        """
        Returns a list of section texts containing the Markdown content.

        Returns:
            A list of strings with the Markdown content of each section.
        """
        return list(self.gen_section_texts())

    def gen_section_texts(self) -> Generator[str, None, None]:
        """
        Generator that yields the Markdown content of each section.
        """
        return (section.md for section in self.md_sections)

    def split(self, md: Union[str, Path, TextIOWrapper]) -> List[str]:
        """
        Splits the loaded Markdown document into sections according to the GPT token size limits.

        Args:
            md: The source Markdown content, can be a string, file path or file-like object.

        Returns:
            A list of strings with the Markdown content of each section.
        """
        self.load_md(md)
        self.build()
        return self.list_section_texts()


def split(
    md: Union[str, Path, TextIOWrapper], model: str = "gpt-3.5-turbo", limit: int = None
) -> List[str]:
    """
    A utility function to split a Markdown document into sections according to GPT token size limits.

    Args:
        md: The source Markdown content, can be a string, file path or file-like object.
        model: The GPT tokenizer model to use for calculating token sizes, defaults to "gpt-3.5-turbo".
        limit: The maximum number of GPT tokens allowed per section, defaults to the model's maximum tokens.

    Returns:
        A list of strings with the Markdown content of each section.
    """
    md_splitter = MarkdownLLMSplitter(gptok_model=model, gptok_limit=limit)
    return md_splitter.split(md)
