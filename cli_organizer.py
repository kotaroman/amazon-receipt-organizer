#!/usr/bin/env python3
import os
import shutil
import pdfplumber
import re
from datetime import datetime
from pathlib import Path
import logging
from typing import Optional, Tuple
import argparse
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('receipt_organizer.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PDFProcessor:
    def __init__(self):
        self.invoice_folders = [
            'Retail.TransactionalInvoicing.3.1',
            'Retail.TransactionalInvoicing.3.2',
            'Retail.TransactionalInvoicing.3.3',
            'Retail.TransactionalInvoicing.3.4',
            'Retail.TransactionalInvoicing.3.5'
        ]
        self.date_patterns = [
            r'請求日[：:\s]*(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})',
            r'発行日[：:\s]*(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})',
            r'注文日[：:\s]*(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})',
            r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})[日]?\s*請求',
            r'Date[：:\s]*(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
            r'Invoice\s*Date[：:\s]*(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})'
        ]

    def extract_invoice_date(self, pdf_path: str) -> Optional[datetime]:
        """PDFファイルから請求日を抽出"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages[:2]:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
                
                for pattern in self.date_patterns:
                    match = re.search(pattern, text)
                    if match:
                        year = int(match.group(1))
                        month = int(match.group(2))
                        day = int(match.group(3))
                        
                        if 2000 <= year <= 2099 and 1 <= month <= 12 and 1 <= day <= 31:
                            return datetime(year, month, day)
                
                logger.warning(f"日付が見つかりませんでした: {pdf_path}")
                return None
                
        except Exception as e:
            logger.error(f"PDFの読み取りエラー {pdf_path}: {str(e)}")
            return None

    def process_pdf(self, pdf_path: str, output_base_dir: str) -> Tuple[str, bool, str]:
        """PDFファイルを処理して適切なフォルダに移動"""
        try:
            invoice_date = self.extract_invoice_date(pdf_path)
            
            if not invoice_date:
                error_msg = f"日付を抽出できませんでした: {os.path.basename(pdf_path)}"
                return pdf_path, False, error_msg
            
            year_month = invoice_date.strftime("%Y%m")
            output_dir = os.path.join(output_base_dir, year_month)
            os.makedirs(output_dir, exist_ok=True)
            
            date_str = invoice_date.strftime("%Y%m%d")
            original_name = os.path.basename(pdf_path)
            base_name = os.path.splitext(original_name)[0]
            new_filename = f"{date_str}_{base_name}.pdf"
            
            output_path = os.path.join(output_dir, new_filename)
            
            counter = 1
            while os.path.exists(output_path):
                new_filename = f"{date_str}_{base_name}_{counter}.pdf"
                output_path = os.path.join(output_dir, new_filename)
                counter += 1
            
            shutil.copy2(pdf_path, output_path)
            
            success_msg = f"処理完了: {original_name} → {year_month}/{new_filename}"
            logger.info(success_msg)
            return pdf_path, True, success_msg
            
        except Exception as e:
            error_msg = f"処理エラー {os.path.basename(pdf_path)}: {str(e)}"
            logger.error(error_msg)
            return pdf_path, False, error_msg

    def organize_receipts(self, input_folder: str, output_folder: str) -> Tuple[int, int]:
        """領収書を整理する"""
        print(f"処理開始: {input_folder}")
        print(f"出力先: {output_folder}\n")
        
        pdf_files = []
        
        # 対象フォルダからPDFファイルを検索
        for invoice_folder in self.invoice_folders:
            invoice_path = os.path.join(input_folder, invoice_folder)
            if os.path.exists(invoice_path):
                print(f"フォルダ発見: {invoice_folder}")
                for file in os.listdir(invoice_path):
                    if file.lower().endswith('.pdf'):
                        pdf_files.append(os.path.join(invoice_path, file))
        
        if not pdf_files:
            print("PDFファイルが見つかりませんでした。")
            return 0, 0
        
        print(f"\n{len(pdf_files)}個のPDFファイルを発見しました。\n")
        
        success_count = 0
        error_count = 0
        
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"処理中 ({i}/{len(pdf_files)}): {os.path.basename(pdf_file)}")
            
            pdf_path, success, message = self.process_pdf(pdf_file, output_folder)
            
            if success:
                print(f"✓ {message}")
                success_count += 1
            else:
                print(f"✗ {message}")
                error_count += 1
        
        print(f"\n処理完了！")
        print(f"成功: {success_count}件")
        print(f"エラー: {error_count}件")
        
        return success_count, error_count


def main():
    parser = argparse.ArgumentParser(description='Amazon PDF領収書自動整理ツール')
    parser.add_argument('input_folder', help='処理するフォルダ（Amazonデータリクエストの解凍フォルダ）')
    parser.add_argument('-o', '--output', default=None, 
                       help='出力先フォルダ（デフォルト: ~/Desktop/整理済み領収書）')
    
    args = parser.parse_args()
    
    input_folder = os.path.abspath(args.input_folder)
    
    if not os.path.exists(input_folder):
        print(f"エラー: 入力フォルダが見つかりません: {input_folder}")
        sys.exit(1)
    
    if args.output:
        output_folder = os.path.abspath(args.output)
    else:
        output_folder = os.path.join(os.path.expanduser("~"), "Desktop", "整理済み領収書")
    
    print("Amazon Receipt Organizer - CLI版")
    print("=" * 50)
    
    processor = PDFProcessor()
    success_count, error_count = processor.organize_receipts(input_folder, output_folder)
    
    if success_count > 0:
        print(f"\n整理済みファイルは以下に保存されました:")
        print(f"{output_folder}")
    
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())