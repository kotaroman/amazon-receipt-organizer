# Amazon Receipt Organizer

Amazonのデータリクエストで取得したPDF領収書を自動で整理するツール

## 機能

- PDF領収書から請求日を自動抽出
- 請求日の年月（YYYYMM形式）でフォルダを作成
- ファイル名を請求日（YYYYMMDD_元のファイル名）に変更して整理
- GUI版（Windows/Mac）とCLI版（Linux/WSL）を提供
- Windows/Mac/Linux対応

## インストール

### Linux/WSL環境
```bash
# 仮想環境作成（推奨）
python3 -m venv venv
source venv/bin/activate

# パッケージインストール
pip install -r requirements.txt
```

### Windows/Mac環境
```bash
pip install -r requirements.txt
```

## 使い方

### CLI版（Linux/WSL推奨）

```bash
# 実行スクリプトを使用
./run_cli.sh /path/to/amazon-data-folder

# 出力先を指定
./run_cli.sh /path/to/amazon-data-folder -o /path/to/output

# 直接実行
source venv/bin/activate
python cli_organizer.py /path/to/amazon-data-folder

# ヘルプ表示
./run_cli.sh --help
```

### GUI版（Windows/Mac）

```bash
# ツールを起動
python amazon_receipt_organizer.py
# または
./run.sh
```

1. Amazonのデータリクエストで解凍したフォルダをドラッグ&ドロップ
   - または「フォルダを選択」ボタンから選択

2. 自動的に以下のフォルダ内のPDFを処理
   - Retail.TransactionalInvoicing.3.1
   - Retail.TransactionalInvoicing.3.2
   - Retail.TransactionalInvoicing.3.3
   - Retail.TransactionalInvoicing.3.4
   - Retail.TransactionalInvoicing.3.5

3. デフォルトでデスクトップの「整理済み領収書」フォルダに出力
   - 「出力先を変更」ボタンで変更可能

## 出力形式

- フォルダ構造: `出力先/YYYYMM/`
- ファイル名: `YYYYMMDD_元のファイル名.pdf`
- デフォルト出力先: `~/Desktop/整理済み領収書/`

## 対象PDFファイル

以下のフォルダ内のPDFファイルが処理対象です：
- `Retail.TransactionalInvoicing.3.1/`
- `Retail.TransactionalInvoicing.3.2/`  
- `Retail.TransactionalInvoicing.3.3/`
- `Retail.TransactionalInvoicing.3.4/`
- `Retail.TransactionalInvoicing.3.5/`

## ファイル構成

```
amazon-receipt-organizer/
├── pdf_processor.py            # 共通ロジック（日付抽出・整理）
├── amazon_receipt_organizer.py  # GUI版（Windows/Mac）
├── cli_organizer.py            # CLI版（Linux/WSL）
├── requirements.txt            # 依存パッケージ
├── run.sh                     # GUI版実行スクリプト
├── run_cli.sh                 # CLI版実行スクリプト
├── setup.py                   # セットアップファイル
└── README.md                  # このファイル
```

## トラブルシューティング

### WSLでGUIエラーが出る場合
```bash
# CLI版を使用してください
./run_cli.sh /path/to/folder
```

### 仮想環境エラーの場合
```bash
# 仮想環境を削除して再作成
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### tkinterエラーの場合
```bash
# システムパッケージをインストール（Ubuntu/Debian）
sudo apt install python3-tk

# またはCLI版を使用
./run_cli.sh /path/to/folder
```

## 実行例

```bash
# Amazonデータを処理（CLI版）
./run_cli.sh ~/Downloads/amazon-data

# 出力先を指定
./run_cli.sh ~/Downloads/amazon-data -o ~/Documents/領収書

# 処理結果確認
ls ~/Desktop/整理済み領収書/
```