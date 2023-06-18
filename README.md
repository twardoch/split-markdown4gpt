# split_markdown4gpt

`split_markdown4gpt` is a Python tool designed to split large Markdown files into smaller sections based on a specified token limit. This is particularly useful for processing large Markdown files with GPT models, as it allows the models to handle the data in manageable chunks.

_Version 1.0.1_ (2023-06-18)

## Installation

You can install `split_markdown4gpt` via pip:

```bash
pip install split_markdown4gpt
```

## CLI usage

After installation, you can use the `mdsplit4gpt` command to split a Markdown file. Here's the basic syntax:

```bash
mdsplit4gpt path_to_your_file.md --model gpt-3.5-turbo --limit 4096 --separator "=== SPLIT ==="
```

This command will split the Markdown file at `path_to_your_file.md` into sections, each containing no more than 4096 tokens (as counted by the `gpt-3.5-turbo` model). The sections will be separated by `=== SPLIT ===`.

All CLI options: 

```
NAME
    mdsplit4gpt

SYNOPSIS
    mdsplit4gpt MD_PATH <flags>

POSITIONAL ARGUMENTS
    MD_PATH
        Type: Union

FLAGS
    -m, --model=MODEL
        Type: str
        Default: 'gpt-3.5-turbo'
    -l, --limit=LIMIT
        Type: Optional[int]
        Default: None
    -s, --separator=SEPARATOR
        Type: str
        Default: '=== SPLIT ==='
```

## Python usage

You can also use `split_markdown4gpt` in your Python code. Here's a basic example:

```python
from split_markdown4gpt import split

sections = split("path_to_your_file.md", model="gpt-3.5-turbo", limit=4096)
for section in sections:
    print(section)
```

This code does the same thing as the CLI command above, but in Python.

## How it works

`split_markdown4gpt` works by tokenizing the input Markdown file using the specified GPT model's tokenizer (default is `gpt-3.5-turbo`). It then splits the file into sections, each containing no more than the specified token limit.

The splitting process respects the structure of the Markdown file. It will not split a section (as defined by Markdown headings) across multiple output sections unless the section is longer than the token limit. In that case, it will split the section at the sentence level.

The tool uses several libraries to accomplish this:

- `tiktoken` for tokenizing the text according to the GPT model's rules.
- `fire` for creating the CLI.
- `frontmatter` for parsing the Markdown file's front matter (metadata at the start of the file).
- `mistletoe` for parsing the Markdown file into a syntax tree.
- `syntok` for splitting the text into sentences.
- `regex` and `PyYAML` for various utility functions.

## Contributing

Contributions to `split_markdown4gpt` are welcome! Please open an issue or submit a pull request on the [GitHub repository](https://github.com/twardoch/split-markdown4gpt).

## License

- Copyright (c) 2023 Adam Twardoch
- Written with assistance from ChatGPT
- Licensed under the [Apache License 2.0](./LICENSE.txt)

