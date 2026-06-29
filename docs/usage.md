# Usage

## Installation

```bash
pip install split_markdown4gpt
```

## CLI

```bash
mdsplit4gpt large_doc.md --model gpt-3.5-turbo --limit 4096 --separator "=== SPLIT ==="
```

Outputs all chunks joined by the separator. Redirect to a file or pipe to another tool.

| Flag | Default | Description |
|---|---|---|
| `--model` | `gpt-3.5-turbo` | Tiktoken model (determines token counting) |
| `--limit` | model max | Max tokens per chunk |
| `--separator` | `=== SPLIT ===` | String inserted between chunks in output |

## Python — quick API

```python
from split_markdown4gpt import split

# From a file path
chunks = split("large_doc.md", model="gpt-3.5-turbo", limit=4096)

# From a string
chunks = split(markdown_string, model="gpt-4", limit=8000)

# From a file object
with open("doc.md") as f:
    chunks = split(f, limit=2000)

for chunk in chunks:
    # Each chunk is a Markdown string within the token limit
    print(len(chunk), "chars")
```

## Python — class API

Use `MarkdownLLMSplitter` directly for more control:

```python
from split_markdown4gpt import MarkdownLLMSplitter

splitter = MarkdownLLMSplitter(gptok_model="gpt-4", gptok_limit=6000)

# Load content
splitter.load_md("doc.md")        # from path
splitter.load_md_str(md_string)   # from string
splitter.load_md_file(file_obj)   # from file object

# Build sections
splitter.build()

# Access results
texts = splitter.list_section_texts()   # list[str]
dicts = splitter.list_section_dicts()   # list[{"md": str, "gptok_size": int}]

# Or use generators
for text in splitter.gen_section_texts():
    print(text)

for section in splitter.gen_section_dicts():
    print(section["gptok_size"], "tokens:", section["md"][:80])
```

## Supported models

Any model supported by `tiktoken`, including all `gpt-3.5-turbo` and `gpt-4` variants.

```python
from split_markdown4gpt.splitter import OPENAI_MODELS
print(OPENAI_MODELS)
# {"gpt-4": 8192, "gpt-4-turbo": 128000, "gpt-4o": 128000, ...}
```

## Processing with OpenAI

```python
from openai import OpenAI
from split_markdown4gpt import split

client = OpenAI()

chunks = split("large_doc.md", model="gpt-4", limit=6000)

summaries = []
for chunk in chunks:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Summarise the following documentation section."},
            {"role": "user", "content": chunk},
        ],
    )
    summaries.append(response.choices[0].message.content)

final_summary = "\n\n".join(summaries)
```

## YAML front matter

Front matter is automatically stripped before chunking. Metadata is available on the splitter instance:

```python
splitter = MarkdownLLMSplitter()
splitter.load_md("doc.md")
print(splitter.md_meta)   # {"title": "...", "author": "..."}
splitter.build()
```
