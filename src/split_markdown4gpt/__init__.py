# this_file: src/split_markdown4gpt/__init__.py
"""split-markdown4gpt: Split large Markdown files into token-bounded chunks.

LLMs have finite context windows.  This package breaks Markdown documents
into sections that fit within a specified token budget, respecting heading
hierarchy and never cutting mid-sentence.

Typical usage::

    from split_markdown4gpt import split

    chunks = split("large_doc.md", model="gpt-4", limit=6000)
    for chunk in chunks:
        send_to_llm(chunk)

See :mod:`split_markdown4gpt.splitter` for the full API.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .splitter import MarkdownLLMSplitter, split

try:
    __version__: str = version("split_markdown4gpt")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = ["split", "MarkdownLLMSplitter", "__version__"]
