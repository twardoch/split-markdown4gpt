import pytest
from pathlib import Path
from split_markdown4gpt.splitter import MarkdownLLMSplitter, split

def test_split():
    # Assuming you have a test.md file in your tests directory
    md_path = Path(__file__).parent / "test.md"
    sections = split(md_path)
    assert isinstance(sections, list)
    assert all(isinstance(section, str) for section in sections)

