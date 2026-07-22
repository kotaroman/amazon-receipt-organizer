#!/usr/bin/env python3
import os
import argparse
import sys

from pdf_processor import PDFProcessor, setup_logging


def main():
    parser = argparse.ArgumentParser(description='Amazon PDF領収書自動整理ツール')
    parser.add_argument('input_folder', help='処理するフォルダ（Amazonデータリクエストの解凍フォルダ）')
    parser.add_argument('-o', '--output', default=None,
                       help='出力先フォルダ（デフォルト: ~/Desktop/整理済み領収書）')

    args = parser.parse_args()
    setup_logging()

    input_folder = os.path.abspath(args.input_folder)

    if not os.path.isdir(input_folder):
        print(f"エラー: 入力フォルダが見つからないか、フォルダではありません: {input_folder}")
        sys.exit(1)

    if args.output:
        output_folder = os.path.abspath(args.output)
    else:
        output_folder = os.path.join(os.path.expanduser("~"), "Desktop", "整理済み領収書")

    print("Amazon Receipt Organizer - CLI版")
    print("=" * 50)

    processor = PDFProcessor()
    success_count, error_count = processor.organize_receipts(input_folder, output_folder)

    if success_count == 0 and error_count == 0:
        print("入力フォルダ直下の Retail.TransactionalInvoicing.* フォルダにPDFが見つかりませんでした。")
        return 2

    if success_count > 0:
        print("\n整理済みファイルは以下に保存されました:")
        print(f"{output_folder}")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
