<a id="split_markdown4gpt"></a>

# split\_markdown4gpt

<a id="split_markdown4gpt.splitter"></a>

# split\_markdown4gpt.splitter

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter"></a>

## MarkdownLLMSplitter Objects

```python
class MarkdownLLMSplitter()
```

A class to split Markdown files into sections according to GPT token size limits. Currently supports OpenAI models only, since it uses the `tiktoken` library for tokenization.

Attributes:
    gptoker: GPT tokenizer instance used to calculate token sizes.
    gptok_limit: The maximum number of GPT tokens allowed per section.
    md_meta: Metadata found in the source Markdown file.
    md_str: The source Markdown string.
    md_doc: The parsed source Markdown document as a mistletoe Document instance.
    md_dict: A dictionary representing the structure of the Markdown document.
    md_path: The absolute path to the source Markdown file.
    md_sections: List of sections (named tuples) containing the Markdown content and its size in tokens.

Args:
    gptok_model: The GPT tokenizer model to use for calculating token sizes, defaults to "gpt-3.5-turbo".
    gptok_limit: The maximum number of GPT tokens allowed per section, defaults to the model's maximum tokens.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.load_md_path"></a>

#### load\_md\_path

```python
def load_md_path(md_path: Union[Path, str]) -> None
```

Load a Markdown file from a file path.

Args:
    md_path: The file path to the source Markdown file.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.load_md_file"></a>

#### load\_md\_file

```python
def load_md_file(md_file: TextIOWrapper) -> None
```

Load a Markdown file from a file-like object.

Args:
    md_file: The file-like object containing the source Markdown content.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.load_md_str"></a>

#### load\_md\_str

```python
def load_md_str(md_str: str) -> None
```

Load a Markdown file from a string.

Args:
    md_str: The source Markdown content as a string.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.load_md"></a>

#### load\_md

```python
def load_md(md: Union[str, Path, TextIOWrapper]) -> None
```

Load a Markdown file from a string, file path, or file-like object.

Args:
    md: The source Markdown content, can be a string, file path or file-like object.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.gpttok_size"></a>

#### gpttok\_size

```python
@lru_cache(maxsize=None)
def gpttok_size(text: str) -> int
```

Calculates the number of GPT tokens in a text string.

Args:
    text: The text string to calculate the token size.

Returns:
    The number of GPT tokens in the text string.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.build_md_dict"></a>

#### build\_md\_dict

```python
def build_md_dict() -> None
```

Builds a dictionary representing the structure of the source Markdown document.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.calculate_sizes"></a>

#### calculate\_sizes

```python
def calculate_sizes(md_dict: Dict) -> int
```

Recursively calculates the total size of GPT tokens in the provided Markdown dictionary.

Args:
    md_dict: The Markdown dictionary to calculate token sizes.

Returns:
    The total number of GPT tokens in the Markdown dictionary.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.process_item"></a>

#### process\_item

```python
def process_item(item: Dict, current_section: List[str], current_size: int,
                 md_sections: List[Section]) -> Tuple[List[str], int]
```

Processes an item in the Markdown dictionary and adds it to the appropriate section.

Args:
    item: The Markdown item to process.
    current_section: The current section being built as a list of strings.
    current_size: The current size of the section in GPT tokens.
    md_sections: The list of sections (named tuples) being built.

Returns:
    A tuple containing the updated current_section and the current_size.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.prep_section"></a>

#### prep\_section

```python
def prep_section(section_text: str, size: int = None) -> Section
```

Prepares a section by removing excessive newlines and calculating the section size if not provided.

Args:
    section_text: The Markdown content of the section.
    size: The size of the section in GPT tokens, defaults to None (automatically calculated).

Returns:
    A Section named tuple containing the prepared Markdown content and its size in tokens.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.process_md"></a>

#### process\_md

```python
def process_md(item: Dict, current_section: List[str], current_size: int,
               md_sections: List[Section]) -> Tuple[List[str], int]
```

Processes a Markdown item and adds it to the appropriate section.

Args:
    item: The Markdown item to process.
    current_section: The current section being built as a list of strings.
    current_size: The current size of the section in GPT tokens.
    md_sections: The list of sections (named tuples) being built.

Returns:
    A tuple containing the updated current_section and the current_size.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.get_sections_from_md_dict_by_limit"></a>

#### get\_sections\_from\_md\_dict\_by\_limit

```python
def get_sections_from_md_dict_by_limit(md_dict: Dict) -> List[Section]
```

Builds the sections from the provided Markdown dictionary by fitting the content within token limits.

Args:
    md_dict: The Markdown dictionary to build sections from.

Returns:
    A list of sections (named tuples) containing the Markdown content and its size in tokens.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.build"></a>

#### build

```python
def build() -> None
```

Builds the sections by processing the loaded Markdown document.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.list_section_dicts"></a>

#### list\_section\_dicts

```python
def list_section_dicts() -> List[Dict[str, Union[str, int]]]
```

Returns a list of section dictionaries containing the Markdown content and its size.

Returns:
    A list of dictionaries with keys 'md' and 'size'.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.gen_section_dicts"></a>

#### gen\_section\_dicts

```python
def gen_section_dicts() -> Generator[Dict[str, Union[str, int]], None, None]
```

Generator that yields section dictionaries containing the Markdown content and its size.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.list_section_texts"></a>

#### list\_section\_texts

```python
def list_section_texts() -> List[str]
```

Returns a list of section texts containing the Markdown content.

Returns:
    A list of strings with the Markdown content of each section.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.gen_section_texts"></a>

#### gen\_section\_texts

```python
def gen_section_texts() -> Generator[str, None, None]
```

Generator that yields the Markdown content of each section.

<a id="split_markdown4gpt.splitter.MarkdownLLMSplitter.split"></a>

#### split

```python
def split(md: Union[str, Path, TextIOWrapper]) -> List[str]
```

Splits the loaded Markdown document into sections according to the GPT token size limits.

Args:
    md: The source Markdown content, can be a string, file path or file-like object.

Returns:
    A list of strings with the Markdown content of each section.

<a id="split_markdown4gpt.splitter.split"></a>

#### split

```python
def split(md: Union[str, Path, TextIOWrapper],
          model: str = "gpt-3.5-turbo",
          limit: int = None) -> List[str]
```

A utility function to split a Markdown document into sections according to GPT token size limits.

Args:
    md: The source Markdown content, can be a string, file path or file-like object.
    model: The GPT tokenizer model to use for calculating token sizes, defaults to "gpt-3.5-turbo".
    limit: The maximum number of GPT tokens allowed per section, defaults to the model's maximum tokens.

Returns:
    A list of strings with the Markdown content of each section.

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

