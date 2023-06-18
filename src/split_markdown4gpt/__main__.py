#!/usr/bin/env python3
from pathlib import Path
from typing import Union

import fire

from .splitter import MarkdownLLMSplitter

def split_md_file(
    md_path: Union[str, Path],
    model: str = "gpt-3.5-turbo",
    limit: int = None,
    separator: str = "=== SPLIT ===",
) -> str:
    """
    Splits a Markdown file into sections according to GPT token size limits.

    This tool loads a Markdown file, and splits its content into sections
    that are within the specified token size limit using the desired GPT tokenizing model. The resulting
    sections are then concatenated using the specified separator and returned as a single string.

    Args:
        md_path: The path of the source Markdown file to be split.
        model: The GPT tokenizer model to use for calculating token sizes. Defaults to "gpt-3.5-turbo".
        limit: The maximum number of GPT tokens allowed per section. Defaults to the model's maximum tokens.
        separator: The string used to separate sections in the output. Defaults to "=== SPLIT ===".

    Returns:
        A single string containing the Markdown content of the file, split into sections and separated
        by the specified separator.
    """
    md_path = Path(md_path).resolve()
    md_splitter = MarkdownLLMSplitter(gptok_model=model, gptok_limit=limit)
    return f"\n{separator}\n".join(md_splitter.split(md_path))


def cli():
    # Set the display function for 'fire' to print output without extra formatting.
    fire.core.Display = lambda lines, out: print(*lines, file=out)
    fire.Fire(split_md_file)


if __name__ == "__main__":
    cli()
