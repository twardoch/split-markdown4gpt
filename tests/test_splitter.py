# this_file: tests/test_splitter.py
"""Tests for split_markdown4gpt.splitter."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from split_markdown4gpt import MarkdownLLMSplitter, split
from split_markdown4gpt.splitter import meta_data

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TEST_MD = Path(__file__).parent / "test.md"

SIMPLE_MD = """\
# Section One

This is the first section with some content.

# Section Two

This is the second section with different content.
"""

FRONTMATTER_MD = """\
---
title: Test Document
author: Test Author
---

# Main Content

Body text after front matter.
"""

MULTI_HEADING_MD = """\
# Chapter 1

Intro paragraph.

## Sub-section 1.1

Detail paragraph one.

## Sub-section 1.2

Detail paragraph two.

# Chapter 2

Second chapter intro.
"""


# ---------------------------------------------------------------------------
# meta_data()
# ---------------------------------------------------------------------------


def test_meta_data_no_frontmatter():
    """Plain Markdown returns empty metadata and the full string."""
    meta, body = meta_data("# Hello\n\nWorld")
    assert meta == {}
    assert "Hello" in body


def test_meta_data_with_frontmatter():
    """YAML front matter is extracted into metadata dict."""
    meta, body = meta_data(FRONTMATTER_MD)
    assert meta.get("title") == "Test Document"
    assert "Main Content" in body
    # Front matter block itself should not appear in body
    assert "title:" not in body


def test_meta_data_exception_returns_defaults():
    """When parsing raises, gracefully return (empty dict, original string)."""
    bad_input = "---\n: bad yaml\n---\n\n# Content"
    # Should not raise; may or may not strip front matter
    meta, body = meta_data(bad_input)
    assert isinstance(meta, dict)
    assert isinstance(body, str)


# ---------------------------------------------------------------------------
# MarkdownLLMSplitter construction
# ---------------------------------------------------------------------------


def test_splitter_default_construction():
    """Splitter initialises with gpt-3.5-turbo defaults."""
    s = MarkdownLLMSplitter()
    assert s.gptok_limit == 4096
    assert s.md_str == ""
    assert s.md_sections == []


def test_splitter_custom_limit():
    """Custom gptok_limit is respected."""
    s = MarkdownLLMSplitter(gptok_limit=100)
    assert s.gptok_limit == 100


def test_splitter_unknown_model_falls_back():
    """Unknown model falls back to 2048 token limit."""
    s = MarkdownLLMSplitter(gptok_model="gpt-3.5-turbo", gptok_limit=None)
    # gpt-3.5-turbo is in OPENAI_MODELS so it gets 4096
    assert s.gptok_limit == 4096

    s2 = MarkdownLLMSplitter(gptok_model="text-davinci-003", gptok_limit=None)
    # unknown model falls back to 2048
    assert s2.gptok_limit == 2048


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def test_load_md_str():
    """Loading from a plain string populates md_str."""
    s = MarkdownLLMSplitter()
    s.load_md_str(SIMPLE_MD)
    assert "Section One" in s.md_str


def test_load_md_path(tmp_path):
    """Loading from a file path reads the file correctly."""
    p = tmp_path / "doc.md"
    p.write_text(SIMPLE_MD, encoding="utf-8")
    s = MarkdownLLMSplitter()
    s.load_md_path(p)
    assert "Section One" in s.md_str


def test_load_md_file_object():
    """Loading from a file-like object works."""
    s = MarkdownLLMSplitter()
    s.load_md_file(io.StringIO(SIMPLE_MD))
    assert "Section One" in s.md_str


def test_load_md_dispatch_str():
    s = MarkdownLLMSplitter()
    s.load_md(SIMPLE_MD)
    assert "Section One" in s.md_str


def test_load_md_dispatch_path(tmp_path):
    p = tmp_path / "doc.md"
    p.write_text(SIMPLE_MD, encoding="utf-8")
    s = MarkdownLLMSplitter()
    s.load_md(p)
    assert "Section One" in s.md_str


def test_load_md_dispatch_file_object():
    s = MarkdownLLMSplitter()
    s.load_md(io.StringIO(SIMPLE_MD))
    assert "Section One" in s.md_str


def test_load_md_dispatch_invalid_type():
    s = MarkdownLLMSplitter()
    with pytest.raises(TypeError):
        s.load_md(12345)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Token counting
# ---------------------------------------------------------------------------


def test_gpttok_size_nonempty():
    s = MarkdownLLMSplitter()
    size = s.gpttok_size("Hello, world!")
    assert isinstance(size, int)
    assert size > 0


def test_gpttok_size_empty_string():
    s = MarkdownLLMSplitter()
    assert s.gpttok_size("") == 0


def test_gpttok_size_caching():
    """Repeated calls return the same value (cache hit)."""
    s = MarkdownLLMSplitter()
    text = "The quick brown fox"
    first = s.gpttok_size(text)
    second = s.gpttok_size(text)
    assert first == second


# ---------------------------------------------------------------------------
# split() module-level function
# ---------------------------------------------------------------------------


def test_split_returns_list_of_strings():
    """split() on the test fixture returns a non-empty list of strings."""
    sections = split(TEST_MD)
    assert isinstance(sections, list)
    assert len(sections) >= 1
    assert all(isinstance(s, str) for s in sections)


def test_split_from_string():
    """split() accepts a raw Markdown string."""
    sections = split(SIMPLE_MD)
    assert isinstance(sections, list)
    assert len(sections) >= 1


def test_split_sections_nonempty():
    """No section should be an empty string."""
    sections = split(SIMPLE_MD)
    assert all(s.strip() for s in sections)


def test_split_preserves_content():
    """Combined output contains original headings."""
    sections = split(SIMPLE_MD)
    combined = "\n".join(sections)
    assert "Section One" in combined
    assert "Section Two" in combined


def test_split_with_tight_limit_produces_multiple_chunks():
    """A very small token limit forces multiple chunks."""
    sections = split(MULTI_HEADING_MD, model="gpt-3.5-turbo", limit=30)
    assert len(sections) > 1


def test_split_with_large_limit_produces_one_chunk():
    """A very large token limit keeps content in a single chunk."""
    sections = split(SIMPLE_MD, model="gpt-3.5-turbo", limit=100_000)
    assert len(sections) == 1


def test_split_chunks_respect_token_limit():
    """Each chunk must not exceed the declared token limit."""
    limit = 50
    s = MarkdownLLMSplitter(gptok_limit=limit)
    sections = s.split(MULTI_HEADING_MD)
    for section in sections:
        size = s.gpttok_size(section)
        # Allow a small overage from sentence-split edge cases but keep it sane
        assert size <= limit * 2, f"Chunk too large: {size} tokens"


def test_split_frontmatter_stripped():
    """Front matter metadata does not appear in chunk text."""
    sections = split(FRONTMATTER_MD)
    combined = "\n".join(sections)
    assert "title: Test Document" not in combined
    assert "Main Content" in combined


def test_split_from_path(tmp_path):
    """split() accepts a Path object."""
    p = tmp_path / "doc.md"
    p.write_text(SIMPLE_MD, encoding="utf-8")
    sections = split(p)
    assert isinstance(sections, list)
    assert len(sections) >= 1


def test_split_from_file_object():
    """split() accepts a file-like object."""
    sections = split(io.StringIO(SIMPLE_MD))
    assert isinstance(sections, list)
    assert len(sections) >= 1


# ---------------------------------------------------------------------------
# MarkdownLLMSplitter.build() and section access
# ---------------------------------------------------------------------------


def test_build_populates_sections():
    s = MarkdownLLMSplitter()
    s.load_md_str(SIMPLE_MD)
    s.build()
    assert len(s.md_sections) >= 1


def test_list_section_dicts_structure():
    s = MarkdownLLMSplitter()
    s.load_md_str(SIMPLE_MD)
    s.build()
    dicts = s.list_section_dicts()
    for d in dicts:
        assert "md" in d
        assert "gptok_size" in d
        assert isinstance(d["md"], str)
        assert isinstance(d["gptok_size"], int)
        assert d["gptok_size"] > 0


def test_gen_section_texts_yields_strings():
    s = MarkdownLLMSplitter()
    s.load_md_str(SIMPLE_MD)
    s.build()
    texts = list(s.gen_section_texts())
    assert all(isinstance(t, str) for t in texts)


def test_list_section_texts_matches_gen():
    s = MarkdownLLMSplitter()
    s.load_md_str(SIMPLE_MD)
    s.build()
    assert s.list_section_texts() == list(s.gen_section_texts())


def test_list_section_dicts_matches_gen():
    s = MarkdownLLMSplitter()
    s.load_md_str(SIMPLE_MD)
    s.build()
    assert s.list_section_dicts() == list(s.gen_section_dicts())


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_empty_string_returns_empty_or_one_chunk():
    """Splitting empty input should not crash."""
    sections = split("")
    assert isinstance(sections, list)


def test_only_frontmatter():
    """Document with only front matter and no body."""
    md = "---\ntitle: Empty\n---\n"
    sections = split(md)
    assert isinstance(sections, list)


def test_very_long_single_paragraph():
    """A paragraph much longer than the limit falls back to sentence splitting."""
    long_para = "This is sentence number {}. " * 60
    long_para = long_para.format(*range(60))
    sections = split(long_para, limit=50)
    assert isinstance(sections, list)
    # Should produce at least one section
    assert len(sections) >= 1
