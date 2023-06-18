#!/usr/bin/env python3
from collections import defaultdict, namedtuple
from functools import lru_cache
from io import TextIOWrapper
from pathlib import Path
from typing import Any, Dict, Generator, List, Tuple, Union

try:
    import regex as re
except ImportError:
    import re

import frontmatter
import tiktoken
from mistletoe import Document, block_token, markdown_renderer, span_token
from syntok.segmenter import analyze as syntok_analyze
from yaml.parser import ParserError

OPENAI_MODELS = {
    "gpt-4": 8192,
    "gpt-4-32k": 32768,
    "gpt-4-32k-0613": 32768,
    "gpt-4-0613": 8192,
    "gpt-3.5-turbo": 4096,
    "gpt-3.5-turbo-0613": 4096,
    "gpt-3.5-turbo-16k": 16384,
    "gpt-3.5-turbo-16k-0613": 16384,
}

RE_NEWLINES = re.compile("\n{3,}")

Section = namedtuple("Section", ("md", "size"))


class MarkdownLLMSplitter:
    def __init__(
        self, gptok_model: str = "gpt-3.5-turbo", gptok_limit: int = None
    ) -> None:
        self.gptoker = tiktoken.encoding_for_model(gptok_model)
        self.gptok_limit = gptok_limit or OPENAI_MODELS.get(gptok_model, 2048)
        self.md_meta = {}
        self.md_str = ""
        self.md_doc = Document([])
        self.md_dict = defaultdict(list)
        self.md_path = Path()
        self.md_sections = []

    def load_md_path(self, md_path: Union[Path, str]) -> None:
        self.md_path = Path(md_path).resolve()
        with open(self.md_path, "r") as md_file:
            self.load_md_file(md_file)

    def load_md_file(self, md_file: TextIOWrapper) -> None:
        file_content = md_file.read()
        parsed = frontmatter.loads(file_content)
        self.md_meta = parsed.metadata
        self.md_str = parsed.content

    def load_md_str(self, md_str: str) -> None:
        self.md_str = md_str

    def load_md(self, md: Union[str, Path, TextIOWrapper]) -> None:
        if hasattr(md, "read"):
            self.load_md_file(md)
        elif isinstance(md, Path):
            self.load_md_path(md)
        elif isinstance(md, str):
            self.load_md_str(md)
        else:
            raise TypeError("md must be a file-like object, Path or str")

    @lru_cache(maxsize=None)
    def gpttok_size(self, text: str) -> int:
        return len(list(self.gptoker.encode(text)))

    def build_md_dict(self) -> None:
        self.md_doc = Document(self.md_str)
        current_level = 0
        current_dict = self.md_dict
        dict_stack = [current_dict]

        for child in self.md_doc.children:
            if isinstance(child, block_token.Heading):
                new_dict = {"size": 0, "children": defaultdict(list)}
                if child.level > current_level:
                    current_dict[child.level].append(new_dict)
                    current_dict = new_dict["children"]
                    dict_stack.append(current_dict)
                else:
                    dict_stack = dict_stack[: child.level]
                    current_dict = dict_stack[-1]
                    current_dict[child.level].append(new_dict)
                    current_dict = new_dict["children"]
                current_level = child.level
            if isinstance(child, block_token.BlockToken):
                new_doc = Document([])
                new_doc.children.append(child)
                with markdown_renderer.MarkdownRenderer() as renderer:
                    fragment = renderer.render(new_doc)
                fragment_dict = {"md": fragment, "size": self.gpttok_size(fragment)}
                current_dict[current_level].append(fragment_dict)

    def calculate_sizes(self, md_dict: Dict) -> int:
        total_size = 0
        for key, value in md_dict.items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        if "children" in item:
                            item["size"] = self.calculate_sizes(item["children"])
                        if "size" in item:
                            total_size += item["size"]
        return total_size

    def process_item(
        self,
        item: Dict,
        current_section: List[str],
        current_size: int,
        md_sections: List[Section],
    ) -> Tuple[List[str], int]:
        if "children" in item:
            for child in item["children"].values():
                for subitem in child:
                    current_section, current_size = self.process_item(
                        subitem, current_section, current_size, md_sections
                    )
        if "md" in item:
            current_section, current_size = self.process_md(
                item, current_section, current_size, md_sections
            )
        return current_section, current_size

    def prep_section(self, section_text: str, size: int = None) -> Section:
        if not size:
            size = self.gpttok_size(section_text)
        return Section(RE_NEWLINES.sub("\n\n", section_text), size)

    def process_md(
        self,
        item: Dict,
        current_section: List[str],
        current_size: int,
        md_sections: List[Section],
    ) -> Tuple[List[str], int]:
        if item["size"] > self.gptok_limit:
            for syntok_paragraph in syntok_analyze(item["md"]):
                for syntok_sentence in syntok_paragraph:
                    sentence = (
                        "".join(
                            token.spacing + token.value for token in syntok_sentence
                        ).lstrip()
                        + " "
                    )
                    sentence_size = self.gpttok_size(sentence)
                    if current_size + sentence_size <= self.gptok_limit:
                        current_section.append(sentence)
                        current_size += sentence_size
                    else:
                        md_sections.append(
                            self.prep_section("".join(current_section), current_size)
                        )
                        current_section = [sentence]
                        current_size = sentence_size
                current_section.append("\n\n")
        elif current_size + item["size"] <= self.gptok_limit:
            current_section.append(item["md"] + "\n")
            current_size += item["size"]
        else:
            md_sections.append(
                self.prep_section("".join(current_section), current_size)
            )
            current_section = [item["md"] + "\n"]
            current_size = item["size"]
        return current_section, current_size

    def get_sections_from_md_dict_by_limit(self, md_dict: Dict) -> List[Section]:
        md_sections = []
        current_section = []
        current_size = 0

        for key, value in md_dict.items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        current_section, current_size = self.process_item(
                            item, current_section, current_size, md_sections
                        )
        if current_section:
            md_sections.append(
                self.prep_section("".join(current_section), current_size)
            )
        return md_sections

    def build(self) -> None:
        self.build_md_dict()
        self.calculate_sizes(self.md_dict)
        self.md_sections = self.get_sections_from_md_dict_by_limit(md_dict=self.md_dict)

    def list_section_dicts(self) -> List[Dict[str, Union[str, int]]]:
        return list(self.gen_section_dicts())

    def gen_section_dicts(self) -> Generator[Dict[str, Union[str, int]], None, None]:
        return (
            {"md": section.md, "size": section.size} for section in self.md_sections
        )

    def list_section_texts(self) -> List[str]:
        return list(self.gen_section_texts())

    def gen_section_texts(self) -> Generator[str, None, None]:
        return (section.md for section in self.md_sections)

    def summarize(self):
        for section in self.md_sections:
            section_size = self.gpttok_size(section)
            original_summary = summarize_markdown(markdown=section).replace(
                "[NEW SUMMARY:] ", ""
            )
            original_summary_size = self.gpttok_size(original_summary)
            percentage = int(original_summary_size / section_size * 100)
            reviewed_summary = review_summary_of_reference_markdown(
                provided_summary=original_summary, reference_markdown=section
            ).replace("[NEW SUMMARY:] ", "")
            print(
                f"""\n\n<!-- {original_summary_size} / {section_size} = {percentage}% {original_summary} -->\n"""
            )
            print(f"""\n??? optional-class "Summary">""")
            for line in reviewed_summary.splitlines():
                print(f"""    {line}""")
            print(f"\n{section}\n")

    def split(self, md: Union[str, Path, TextIOWrapper]) -> List[str]:
        self.load_md(md)
        self.build()
        return self.list_section_texts()

def split(md: Union[str, Path, TextIOWrapper], model: str = "gpt-3.5-turbo", limit: int = None) -> List[str]:
    md_splitter = MarkdownLLMSplitter(gptok_model=model, gptok_limit=limit)
    return md_splitter.split(md)
