#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -f venv/bin/activate ]; then
    echo "エラー: venv が見つかりません。以下でセットアップしてください:" >&2
    echo "  python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt" >&2
    exit 1
fi
source venv/bin/activate
python cli_organizer.py "$@"
