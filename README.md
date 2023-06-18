# split_markdown4gpt

`split_markdown4gpt` is a Python tool designed to split large Markdown files into smaller sections based on a specified token limit. This is particularly useful for processing large Markdown files with GPT models, as it allows the models to handle the data in manageable chunks.

_Version 1.0.2_ (2023-06-18)

## Installation

You can install `split_markdown4gpt` via pip:

```bash
pip install split_markdown4gpt
```

## CLI Usage

After installation, you can use the `mdsplit4gpt` command to split a Markdown file. Here's the basic syntax:

```bash
mdsplit4gpt path_to_your_file.md --model gpt-3.5-turbo --limit 4096 --separator "=== SPLIT ==="
```

This command will split the Markdown file at `path_to_your_file.md` into sections, each containing no more than 4096 tokens (as counted by the `gpt-3.5-turbo` model). The sections will be separated by `=== SPLIT ===`.

All CLI options:

```
NAME
    mdsplit4gpt - Splits a Markdown file into sections according to GPT token size limits.

SYNOPSIS
    mdsplit4gpt MD_PATH <flags>

DESCRIPTION
    This tool loads a Markdown file, and splits its content into sections
    that are within the specified token size limit using the desired GPT tokenizing model. The resulting
    sections are then concatenated using the specified separator and returned as a single string.

POSITIONAL ARGUMENTS
    MD_PATH
        Type: Union
        The path of the source Markdown file to be split.

FLAGS
    -m, --model=MODEL
        Type: str
        Default: 'gpt-3.5-turbo'
        The GPT tokenizer model to use for calculating token sizes. Defaults to "gpt-3.5-turbo".
    -l, --limit=LIMIT
        Type: Optional[int]
        Default: None
        The maximum number of GPT tokens allowed per section. Defaults to the model's maximum tokens.
    -s, --separator=SEPARATOR
        Type: str
        Default: '=== SPLIT ==='
        The string used to separate sections in the output. Defaults to "=== SPLIT ===".
```

## Python Usage

You can also use `split_markdown4gpt` in your Python code. Here's a basic example:

```python
from split_markdown4gpt import split

sections = split("path_to_your_file.md", model="gpt-3.5-turbo", limit=4096)
for section in sections:
    print(section)
```

This code does the same thing as the CLI command above, but in Python.

## How it Works

`split_markdown4gpt` works by tokenizing the input Markdown file using the specified GPT model's tokenizer (default is `gpt-3.5-turbo`). It then splits the file into sections, each containing no more than the specified token limit.

The splitting process respects the structure of the Markdown file. It will not split a section (as defined by Markdown headings) across multiple output sections unless the section is longer than the token limit. In that case, it

will split the section at the sentence level.

The tool uses several libraries to accomplish this:

- `tiktoken` for tokenizing the text according to the GPT model's rules.
- `fire` for creating the CLI.
- `frontmatter` for parsing the Markdown file's front matter (metadata at the start of the file).
- `mistletoe` for parsing the Markdown file into a syntax tree.
- `syntok` for splitting the text into sentences.
- `regex` and `PyYAML` for various utility functions.

### Use Cases

`split_markdown4gpt` is particularly useful in scenarios where you need to process large Markdown files with GPT models. For instance:

- **Text Generation**: If you're using a GPT model to generate text based on a large Markdown file, you can use `split_markdown4gpt` to split the file into manageable sections. This allows the GPT model to process the file in chunks, preventing memory overflow errors.

- **Data Preprocessing**: In machine learning projects, you often need to preprocess your data before feeding it into your model. If your data is in the form of large Markdown files, `split_markdown4gpt` can help you split these files into smaller sections based on the token limit of your model.

- **Document Analysis**: If you're analyzing large Markdown documents (e.g., extracting keywords, summarizing content), you can use `split_markdown4gpt` to break down the documents into smaller sections. This makes the analysis more manageable and efficient.

### Usage Examples

Here's an example of how you can use `split_markdown4gpt` in your Python code:

```python
from split_markdown4gpt import split

# Path to your large Markdown file
md_file_path = "path_to_your_file.md"

# Split the file into sections
sections = split(md_file_path, model="gpt-3.5-turbo", limit=4096)

# Process each section with your GPT model
for section in sections:
    # Replace this with your GPT model's processing function
    process_with_gpt_model(section)
```

In this example, `process_with_gpt_model` is a placeholder for your GPT model's processing function. You would replace this with the actual function you're using to process the text with your GPT model.

## Contributing

Contributions to `split_markdown4gpt` are welcome! Please open an issue or submit a pull request on the [GitHub repository](https://github.com/twardoch/split-markdown4gpt).

## License

- Copyright (c) 2023 Adam Twardoch
- Written with assistance from ChatGPT
- Licensed under the [Apache License 2.0](./LICENSE.txt)