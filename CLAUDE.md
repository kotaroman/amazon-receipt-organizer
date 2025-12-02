# CLAUDE.md

このファイルは、Claude Code (claude.ai/code) がこのリポジトリで作業する際のガイダンスを提供します。

## プロジェクト概要

Amazon Receipt Organizer - Amazonのデータリクエストで取得したPDF領収書から請求日を抽出し、YYYYMM形式のフォルダに自動整理するツール。

## コマンド

### セットアップ
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### CLI版の実行（Linux/WSL推奨）
```bash
./run_cli.sh /path/to/amazon-data-folder
./run_cli.sh /path/to/amazon-data-folder -o /path/to/output
# または直接実行:
python cli_organizer.py /path/to/amazon-data-folder
```

### GUI版の実行（Windows/Mac）
```bash
python amazon_receipt_organizer.py
# または:
./run.sh
```

## アーキテクチャ

コードベースには同じコアロジックを共有する2つの実装があります：

- **`cli_organizer.py`** - argparseを使用したCLI版（Linux/WSL向け）
- **`amazon_receipt_organizer.py`** - tkinter/tkinterdnd2を使用したGUI版

両方とも `PDFProcessor` クラスを含み、以下の処理を行います：
1. Amazon請求書フォルダ（`Retail.TransactionalInvoicing.3.1` ～ `3.5`）からPDFを検索
2. pdfplumberで複数の正規表現パターン（日本語・英語の日付形式）を使用して請求日を抽出
3. ファイルを `YYYYMM/YYYYMMDD_元のファイル名.pdf` 構造にコピー

主要な依存関係：PDF テキスト抽出に `pdfplumber`、GUIドラッグ&ドロップに `tkinterdnd2`。
