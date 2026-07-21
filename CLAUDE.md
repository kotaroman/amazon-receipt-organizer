# CLAUDE.md

このファイルは、Claude Code (claude.ai/code) がこのリポジトリで作業する際のガイダンスを提供します。

## プロジェクト概要

Amazon Receipt Organizer - Amazonのデータリクエストで取得したPDF領収書から請求日を抽出し、`YYYYMM/YYYYMMDD_元ファイル名.pdf` 形式に自動整理する個人用ツール。

## コマンド

| コマンド | 説明 |
|---------|------|
| `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt` | 初回セットアップ |
| `./run_cli.sh /path/to/amazon-data-folder` | CLI版実行（Linux/WSLはこちら） |
| `./run_cli.sh /path/to/amazon-data-folder -o /path/to/output` | 出力先を指定して実行 |
| `./run.sh` または `python amazon_receipt_organizer.py` | GUI版実行（Windows/Mac、要ディスプレイ） |

- テスト・リンターは未導入。動作確認は実PDFでの手動実行のみ
- デフォルト出力先は `~/Desktop/整理済み領収書/`
- `run.sh` / `run_cli.sh` は `venv/bin/activate` を相対パスで参照するため、リポジトリルートから実行すること

## アーキテクチャ

- `cli_organizer.py` - CLI版（argparse、逐次処理。終了コードはエラー0件なら0、それ以外は1）
- `amazon_receipt_organizer.py` - GUI版（tkinter/tkinterdnd2、ThreadPoolExecutor max_workers=4 で並列処理）

処理フロー（両ファイル共通）:
1. 入力フォルダ直下の `Retail.TransactionalInvoicing.3.1` ～ `3.5` からPDFを収集
2. pdfplumberで先頭2ページのみテキスト抽出し、`date_patterns` の正規表現を先頭から順に適用（範囲検証を通った最初のマッチを採用）
3. `出力先/YYYYMM/YYYYMMDD_元ファイル名.pdf` にコピー（移動ではなく copy2。同名衝突時は `_1`, `_2`… を付与）

**IMPORTANT: `PDFProcessor` クラスは両ファイルに重複定義されている（import による共有ではない）。日付パターン・対象フォルダリスト等を変更する際は、必ず両ファイルを同期して修正すること。**

## Gotchas

- `date_patterns` は順序依存。汎用パターン `(\d{4})[/-](\d{1,2})[/-](\d{1,2})` は必ず最後に置く（先に置くと請求日以外の日付を誤検出する）
- 抽出した年は 2000～2099 のみ有効とみなす
- `requirements.txt` にGUI版必須の `tkinterdnd2` が入っていない（`setup.py` には有る）。GUI版を動かすには `pip install tkinterdnd2` が別途必要
- `requirements.txt` の `tk==0.1.0` はダミーパッケージ。実際の tkinter はOS側で導入する（Ubuntu: `sudo apt install python3-tk`）
- `PyPDF2` は requirements にあるが未使用（PDF抽出は pdfplumber のみ）
- `setup.py` の entry_point は存在しない `amazon_receipt_organizer:main` を参照しており動作しない
- ログ `receipt_organizer.log` は実行時のカレントディレクトリに追記される（gitignore済み）

## リポジトリ作法

- ブランチは `main` のみ（個人プロジェクト）
- コミットメッセージ: `<type>: <日本語説明>`（type: feat / fix / chore / refactor / docs / test / ci）
- UI文言・ログメッセージ・コード内コメントは日本語、識別子は英語
