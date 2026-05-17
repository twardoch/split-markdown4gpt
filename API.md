<a id="split_markdown4gpt.splitter"></a>

# split\_markdown4gpt.splitter

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter"></a>

## MarkdownLLMSplitter Objects

```python
class MarkdownLLMSplitter()
```

Splits Markdown files into sections based on GPT token limits. Only supports OpenAI models via the `tiktoken` library.

Attributes:
    gptoker: GPT tokenizer instance.
    gptok_limit: Maximum tokens per section.
    md_meta: Metadata from the Markdown file.
    md_str: Source Markdown content.
    md_doc: Parsed Markdown document.
    md_dict: Structured representation of the document.
    md_path: Path to the source file.
    md_sections: List of sections with content and token counts.

Args:
    gptok_model: Tokenizer model, defaults to "gpt-3.5-turbo".
    gptok_limit: Token limit per section, defaults to model's maximum.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.load_md_path"></a>

#### load\_md\_path

```python
def load_md_path(md_path: Union[Path, str]) -> None
```

Load Markdown from file path.

Args:
    md_path: Path to Markdown file.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.load_md_file"></a>

#### load\_md\_file

```python
def load_md_file(md_file: TextIOWrapper) -> None
```

Load Markdown from file object.

Args:
    md_file: File-like object with Markdown content.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.load_md_str"></a>

#### load\_md\_str

```python
def load_md_str(md_str: str) -> None
```

Load Markdown from string.

Args:
    md_str: Markdown content string.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.load_md"></a>

#### load\_md

```python
def load_md(md: Union[str, Path, TextIOWrapper]) -> None
```

Load Markdown from string, path, or file object.

Args:
    md: Markdown source (string, path, or file object).

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.gpttok_size"></a>

#### gpttok\_size

```python
@lru_cache(maxsize=None)
def gpttok_size(text: str) -> int
```

Count GPT tokens in text.

Args:
    text: Input text.

Returns:
    Number of tokens.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.build_md_dict"></a>

#### build\_md\_dict

```python
def build_md_dict() -> None
```

Parse Markdown into structured dictionary.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.calculate_sizes"></a>

#### calculate\_sizes

```python
def calculate_sizes(md_dict: Dict) -> int
```

Calculate total tokens in Markdown structure.

Args:
    md_dict: Structured Markdown dictionary.

Returns:
    Total token count.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.process_item"></a>

#### process\_item

```python
def process_item(
        item: Dict, current_section: List[str], current_size: int,
        md_sections: List[Dict[str, Union[str,
                                          int]]]) -> Tuple[List[str], int]
```

Add item to section within token limits.

Args:
    item: Markdown element.
    current_section: Current section content.
    current_size: Current section token count.
    md_sections: List of completed sections.

Returns:
    Updated section and token count.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.prep_section"></a>

#### prep\_section

```python
def prep_section(section_text: str,
                 size: int = None) -> Dict[str, Union[str, int]]
```

Clean section text and calculate token size.

Args:
    section_text: Markdown content.
    size: Token count (optional).

Returns:
    Section dictionary with content and size.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.process_md"></a>

#### process\_md

```python
def process_md(
        item: Dict, current_section: List[str], current_size: int,
        md_sections: List[Dict[str, Union[str,
                                          int]]]) -> Tuple[List[str], int]
```

Process Markdown item into sections.

Args:
    item: Markdown element.
    current_section: Current section content.
    current_size: Current section token count.
    md_sections: List of completed sections.

Returns:
    Updated section and token count.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.get_sections_from_md_dict_by_limit"></a>

#### get\_sections\_from\_md\_dict\_by\_limit

```python
def get_sections_from_md_dict_by_limit(
        md_dict: Dict) -> List[Dict[str, Union[str, int]]]
```

Split Markdown structure into token-limited sections.

Args:
    md_dict: Structured Markdown content.

Returns:
    List of section dictionaries.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.build"></a>

#### build

```python
def build() -> None
```

Generate sections from loaded Markdown.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.list_section_dicts"></a>

#### list\_section\_dicts

```python
def list_section_dicts() -> List[Dict[str, Union[str, int]]]
```

Return list of section dictionaries.

Returns:
    List with 'md' and 'size' keys.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.gen_section_dicts"></a>

#### gen\_section\_dicts

```python
def gen_section_dicts() -> Generator[Dict[str, Union[str, int]], None, None]
```

Yield section dictionaries.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.list_section_texts"></a>

#### list\_section\_texts

```python
def list_section_texts() -> List[str]
```

Return list of section texts.

Returns:
    Markdown content strings.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.gen_section_texts"></a>

#### gen\_section\_texts

```python
def gen_section_texts() -> Generator[str, None, None]
```

Yield section texts.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.split"></a>

#### split

```python
def split(md: Union[str, Path, TextIOWrapper]) -> List[str]
```

Split Markdown into token-limited sections.

Args:
    md: Source content (string, path, or file object).

Returns:
    List of section strings.

<a id="split_markdown4gpt.splitter.split"></a>

#### split

```python
def split(md: Union[str, Path, TextIOWrapper],
          model: str = "gpt-3.5-turbo",
          limit: int = None) -> List[str]
```

Split Markdown document into sections.

Args:
    md: Source content.
    model: Tokenizer model, defaults to "gpt-3.5-turbo".
    limit: Token limit per section.

Returns:
    List of section strings.

<a id="split_markdown4gpt.__main__"></a>

# split\_markdown4gpt.\_\_main\_\_

<a id="split_markdown4gpt.__main__.split_md_file"></a>

#### split\_md\_file

```python
def split_md_file(md_path: Union[str, Path],
                  model: str = "gpt-3.5-turbo",
                  limit: int = None,
                  separator: str = "=== SPLIT ===") -> str
```

Split Markdown file into sections.

Args:
    md_path: Source file path.
    model: Tokenizer model, defaults to "gpt-3.5-turbo".
    limit: Token limit per section.
    separator: Section separator string.

Returns:
    Concatenated sections separated by delimiter.