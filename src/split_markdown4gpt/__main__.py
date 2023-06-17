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
    md_path = Path(md_path).resolve()
    md_splitter = MarkdownLLMSplitter(gptok_model=model, gptok_limit=limit)
    return f"\n{separator}\n".join(md_splitter.split(md_path))


def cli():
    fire.core.Display = lambda lines, out: print(*lines, file=out)
    fire.Fire(split_md_file)


if __name__ == "__main__":
    cli()
