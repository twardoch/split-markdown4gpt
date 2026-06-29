# Why Splitting Matters for LLM Context Windows

## The context-window problem

Every LLM API call operates within a hard token limit — a ceiling on the combined length of the prompt and the generated response. Common limits are:

| Model | Context window |
|---|---|
| GPT-3.5 Turbo | 4,096 tokens |
| GPT-3.5 Turbo 16k | 16,384 tokens |
| GPT-4 | 8,192 tokens |
| GPT-4 Turbo / GPT-4o | 128,000 tokens |

A "token" is roughly 0.75 words in English, so 4,096 tokens is about 3,000 words — just under five pages of dense text. Even 128k tokens is only around 90,000 words; a single large codebase documentation site can easily exceed that.

Exceeding the limit raises an API error. The only remedy is to send less text per call.

## Why naive splitting fails

The obvious fix — splitting on character count or word count — destroys document coherence:

- A sentence split across two chunks loses its meaning.
- A code block cut in the middle becomes invalid.
- A heading at the end of one chunk has no body; the body appears in the next chunk with no heading.
- A bullet list split mid-item confuses the model about list structure.

Models trained on coherent text produce incoherent output when fed incoherent input.

## Structure-aware chunking

`split-markdown4gpt` parses the Markdown document as an abstract syntax tree (AST) using `mistletoe`, then works with complete structural units:

1. **Headings** define section boundaries. The splitter respects the heading hierarchy (H1 → H2 → H3) so a chunk always begins at a logical section start.
2. **Paragraphs, code blocks, lists, and tables** are treated as atomic units. They are never broken mid-block.
3. **Token counting** uses `tiktoken` — the same tokenizer the OpenAI models use — so the count is exact rather than approximated.
4. **Greedy packing** fills each chunk as full as possible without exceeding the limit, minimising the total number of API calls needed.
5. **Sentence-level fallback** handles the edge case where a single paragraph exceeds the limit. `syntok` splits it into sentences and packs those instead.

## Example

Given this document (simplified):

```markdown
# Introduction

OpenAI's GPT models have changed how developers build applications...
[500 tokens]

## Background

The transformer architecture, introduced in 2017...
[800 tokens]

## Key capabilities

GPT-4 can reason, code, summarise, and translate...
[600 tokens]

# Implementation guide

To use the API in Python, first install the SDK...
[3000 tokens]
```

With a 4,096-token limit, naive character splitting might cut the Implementation guide mid-sentence. `split-markdown4gpt` instead produces:

**Chunk 1** (1,900 tokens): Introduction + Background + Key capabilities — all three sections fit together.

**Chunk 2** (3,000 tokens): Implementation guide — the entire section in one piece.

Each chunk is coherent, self-contained, and well within the limit.

## Practical impact

- **Summarisation pipelines**: Each chunk can be summarised independently; summaries can then be re-combined.
- **Question answering over long docs**: Send chunks sequentially; keep only chunks where the model finds relevant content.
- **Fine-tuning data preparation**: Produce training examples that are each within the context window.
- **RAG (retrieval-augmented generation)**: Chunks map naturally to vector-store documents; structure-aware chunking produces more semantically coherent embeddings than character-split chunks.
