# Changelog

All notable changes to `split-markdown4gpt` are documented here.

## [Unreleased]

### Changed
- **Build system**: migrated from `setup.cfg` / `setup.py` + `setuptools_scm` to a
  fully self-contained `pyproject.toml` using `hatchling` + `hatch-vcs`.
- **Linting**: replaced `black` / `isort` / `flake8` with `ruff` (configured in
  `pyproject.toml`).
- **CI**: updated GitHub Actions from `actions/checkout@v2` / `setup-python@v2` to
  `@v4` / `@v5`; added Python 3.11 and 3.12 to the test matrix; switched from
  plain `pip install` to `hatch run test`.
- **Type hints**: modernised from `typing.List / Dict / Tuple` to built-in generics
  (`list`, `dict`, `tuple`); added `from __future__ import annotations` throughout.
- **`meta_data()`**: fixed silent bug in the `except` clause (`meta, data = None`
  would raise `TypeError`; corrected to `meta, data = None, md`).
- **`OPENAI_MODELS`**: added `gpt-4-turbo`, `gpt-4o`, and `gpt-4o-mini` entries.
- **`load_md_path()`**: added explicit `encoding="utf-8"` to `open()`.
- **`__init__.py`**: removed Python 3.7 compatibility shim; use
  `importlib.metadata` directly; added `__all__`.

### Added
- MkDocs Material documentation site (`docs/`, `mkdocs.yml`) with:
  - *Why Splitting Matters* page explaining context-window constraints.
  - *Usage* page with CLI and Python examples.
  - *API Reference* page generated from docstrings.
- Comprehensive test suite (`tests/test_splitter.py`) expanded from 1 test to
  34 tests covering: `meta_data()`, construction, all three load paths,
  token counting, chunking behaviour, token-limit enforcement, front-matter
  stripping, edge cases (empty input, only front matter, very long paragraph).

## [2.7.5] — 2024

- Earlier releases — see git history.
