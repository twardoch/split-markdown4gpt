# split-markdown4gpt: split large Markdown for LLM context windows

LLMs have finite context windows. A 50,000-word documentation site won't fit in one API call. `split-markdown4gpt` breaks Markdown files into token-bounded chunks that respect document structure — so each chunk stays coherent rather than cutting mid-sentence or mid-section.

## Why splitting matters

Every LLM API call has a hard token limit (e.g. 4,096 tokens for GPT-3.5, 8,192 for GPT-4). Exceeding it raises an error. Naive character-based chunking cuts through sentences, code blocks, and headings — destroying context. This tool:

1. Parses the Markdown AST (via `mistletoe`)
2. Counts tokens using the same tokenizer the model uses (via `tiktoken`)
3. Packs as many complete sections as fit within the limit
4. When a single section exceeds the limit, falls back to sentence-level splitting (via `syntok`)

The result: chunks that respect heading hierarchy, never split a sentence across chunks, and are as large as possible without exceeding the token budget.

## Install

```bash
pip install split_markdown4gpt
```

## CLI

```bash
mdsplit4gpt large_doc.md --model gpt-3.5-turbo --limit 4096 --separator "=== SPLIT ==="
```

Outputs all sections joined by the separator. Redirect to a file or pipe to another tool.

| Flag | Default | Description |
|------|---------|-------------|
| `--model` | `gpt-3.5-turbo` | Tokenizer model (determines token counting) |
| `--limit` | model max | Max tokens per chunk |
| `--separator` | `=== SPLIT ===` | String inserted between chunks in output |

## Python API

```python
from split_markdown4gpt import split

# Returns a list of Markdown strings, each within the token limit
chunks = split("large_doc.md", model="gpt-3.5-turbo", limit=4096)

for i, chunk in enumerate(chunks):
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": chunk}]
    )
```

Also accepts a string or file-like object:

```python
chunks = split(markdown_string, model="gpt-4", limit=8000)
chunks = split(open("doc.md"), limit=2000)
```

## How it works

```
split(md)
  ├── meta_data()        strip YAML front matter
  ├── MarkdownLLMSplitter.build_md_dict()
  │     ├── mistletoe Document  parse Markdown AST
  │     └── build dict tree keyed by heading level
  ├── calculate_sizes()  count tokens recursively (cached with lru_cache)
  └── get_sections_from_md_dict_by_limit()
        ├── walk tree, accumulate blocks until limit reached
        └── oversized blocks → sentence-split via syntok
```

### `MarkdownLLMSplitter` class

```python
from split_markdown4gpt import MarkdownLLMSplitter

splitter = MarkdownLLMSplitter(gptok_model="gpt-4", gptok_limit=6000)
splitter.load_md("doc.md")
splitter.build()

for section in splitter.gen_section_dicts():
    print(section["gptok_size"], "tokens")
    print(section["md"])
```

Methods: `load_md()`, `load_md_path()`, `load_md_str()`, `build()`, `list_section_texts()`, `list_section_dicts()`, `gen_section_texts()`, `gen_section_dicts()`, `split()`.

## Supported models

Any model supported by `tiktoken`, including all `gpt-3.5-turbo` and `gpt-4` variants. The limit defaults to the model's published context window.

## Dependencies

- `tiktoken` — OpenAI-compatible token counting
- `mistletoe` — Markdown AST parser
- `syntok` — sentence segmentation for oversized sections
- `frontmatter` — YAML front matter stripping
- `fire` — CLI
- `regex`, `PyYAML` — utilities

## License

Apache License 2.0. Copyright © 2023 Adam Twardoch.
