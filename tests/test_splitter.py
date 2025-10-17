import pytest
from pathlib import Path
import sys
from io import StringIO
from split_markdown4gpt.splitter import MarkdownLLMSplitter, split

def test_split():
    # Assuming you have a test.md file in your tests directory
    md_path = Path(__file__).parent / "test.md"
    sections = split(md_path)
    assert isinstance(sections, list)
    assert all(isinstance(section, str) for section in sections)

def test_new_openai_models():
    """Test that new OpenAI models are recognized and their limits are set correctly."""
    splitter_gpt5 = MarkdownLLMSplitter(gptok_model="gpt-5")
    assert splitter_gpt5.gptok_limit == 400000
    splitter_gpt5_mini = MarkdownLLMSplitter(gptok_model="gpt-5-mini")
    assert splitter_gpt5_mini.gptok_limit == 400000
    splitter_4_1 = MarkdownLLMSplitter(gptok_model="gpt-4.1")
    assert splitter_4_1.gptok_limit == 1000000

def test_unknown_model_warning():
    """Test that a warning is printed for unknown models."""
    # Redirect stderr to capture the warning message
    old_stderr = sys.stderr
    sys.stderr = captured_stderr = StringIO()

    MarkdownLLMSplitter(gptok_model="claude-3-opus-20240229")

    # Restore stderr
    sys.stderr = old_stderr

    warning_message = captured_stderr.getvalue()
    assert "Warning: Model 'claude-3-opus-20240229' not found" in warning_message
