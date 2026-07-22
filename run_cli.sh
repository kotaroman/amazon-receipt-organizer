#!/bin/bash
# CWD は変更しない（引数の相対パスを呼び出し元基準で解決するため）
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ ! -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    echo "エラー: venv が見つかりません。以下でセットアップしてください:" >&2
    echo "  python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt" >&2
    exit 1
fi
source "$SCRIPT_DIR/venv/bin/activate"
python "$SCRIPT_DIR/cli_organizer.py" "$@"
