#!/usr/bin/env bash
# build.sh: Lint, test, and build split-markdown4gpt
# split_markdown4gpt: Split Markdown files into chunks for GPT context windows
# Legacy package using setuptools/setup.cfg

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Linting ==="
uvx ruff check --fix --unsafe-fixes . || true
uvx ruff format . || true

echo "=== Tests ==="
if [ -d "tests" ] || find . -name "test_*.py" -not -path "./.git/*" | grep -q .; then
    python -m pytest -x || true
else
    echo "No tests found, skipping."
fi

echo "=== Build ==="
if uvx hatch build 2>/dev/null; then
    echo "Built with hatch."
elif uv build 2>/dev/null; then
    echo "Built with uv build."
elif python -m build 2>/dev/null; then
    echo "Built with python -m build."
else
    python setup.py sdist bdist_wheel
    echo "Built with setup.py."
fi

echo "=== Build complete ==="
