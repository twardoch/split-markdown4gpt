#!/usr/bin/env bash
# install.sh: Install split-markdown4gpt in editable mode
# split_markdown4gpt: Split Markdown files into chunks for GPT context windows

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Installing split-markdown4gpt (editable) ==="
uv pip install -e .
echo "=== Install complete ==="
