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
- `run.sh` / `run_cli.sh` は自身の所在ディレクトリへ cd するため任意のディレクトリから実行可

## アーキテクチャ

- `pdf_processor.py` - 共通ロジック（`PDFProcessor`: フォルダ走査・日付抽出・ファイル整理、`setup_logging`）。両エントリポイントから import される
- `cli_organizer.py` - CLI版（argparse、逐次処理。終了コード: 0=全成功 / 1=入力不正または処理エラーあり / 2=対象PDFなし。argparseの引数エラーも2を返す）
- `amazon_receipt_organizer.py` - GUI版（tkinter/tkinterdnd2、ThreadPoolExecutor max_workers=4 で並列処理。ワーカーからのUI更新は `queue.Queue` + `root.after` ポーリング経由）

処理フロー:
1. 入力フォルダ直下の `Retail.TransactionalInvoicing.*` フォルダを前方一致で検出し、サブフォルダも再帰的にPDFを収集（出力先が入力配下にある場合は走査から除外）
2. pdfplumberで先頭2ページのみテキスト抽出し、`date_patterns` の正規表現を優先順に適用（範囲検証と暦検証を通った最初のマッチを採用。2月30日等はスキップして次候補へ）
3. `出力先/YYYYMM/YYYYMMDD_元ファイル名.pdf` にコピー（移動ではない）。出力名は `O_CREAT|O_EXCL` で排他的に確保し、既存と同一内容ならスキップ（再実行は冪等）、同名で内容が異なる場合のみ `_1`, `_2`… を付与

## Gotchas

- `date_patterns` は順序依存。汎用パターンは必ず末尾に置き、境界（否定後読み等）を外さないこと（外すと Order Date や期間表記を請求日として誤検出する）
- 抽出した年は 2000～2099 のみ有効とみなす
- GUI版のワーカースレッドから tkinter API を直接呼ばないこと（`msg_queue` に積んで `_poll_queue` に処理させる）
- tkinter は pip では導入できない。GUI版はOS側のパッケージが必要（Ubuntu: `sudo apt install python3-tk`）
- ログは `~/.amazon-receipt-organizer/receipt_organizer.log` に追記される（CWDには書かない）

## リポジトリ作法

- ブランチは `main` のみ（個人プロジェクト）
- コミットメッセージ: `<type>: <日本語説明>`（type: feat / fix / chore / refactor / docs / test / ci）
- UI文言・ログメッセージ・コード内コメントは日本語、識別子は英語
