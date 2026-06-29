# split-markdown4gpt

**Split large Markdown files into token-bounded chunks for LLM context windows.**

LLMs have finite context windows. A 50,000-word documentation site will not fit in one API call. `split-markdown4gpt` breaks Markdown files into token-bounded chunks that respect document structure — each chunk stays coherent rather than cutting mid-sentence or mid-section.

## Quick start

```bash
pip install split_markdown4gpt
```

```python
from split_markdown4gpt import split

chunks = split("large_doc.md", model="gpt-4", limit=6000)
for chunk in chunks:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": chunk}],
    )
```

Or from the command line:

```bash
mdsplit4gpt large_doc.md --model gpt-3.5-turbo --limit 4096
```

## How it works

```
split(md)
  ├── meta_data()        strip YAML front matter
  ├── build_md_dict()
  │     ├── mistletoe    parse Markdown AST
  │     └── heading tree keyed by level
  ├── calculate_sizes()  count tokens (tiktoken, cached)
  └── get_sections_from_md_dict_by_limit()
        ├── walk tree, accumulate blocks until limit reached
        └── oversized blocks → sentence-split via syntok
```

See [Why Splitting Matters](why-splitting.md) for the motivation, [Usage](usage.md) for the full API, and the [API Reference](api.md) for generated documentation.
