import os
import shutil
import filecmp
import pdfplumber
import re
from datetime import datetime
import logging
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class PDFProcessor:
    # Amazonデータリクエストの請求書フォルダ名プレフィックス
    # （3.1〜3.5 のような番号はエクスポートごとに可変のため前方一致で検出する）
    INVOICE_FOLDER_PREFIX = 'Retail.TransactionalInvoicing'

    def __init__(self):
        # 優先順位順。汎用パターンは誤検出しやすいため必ず末尾に置く。
        # - Invoice Date は汎用 Date より前に置く（Order Date 等の誤採用防止）
        # - 汎用 Date は直前が英字（OrderDate）や英字+空白（Order Date, Due Date）の
        #   複合ラベルを否定後読みで除外する
        # - 最後の汎用パターンは前後に数字・区切りが続く場合を除外し、
        #   期間表記（2024/4-2025/3）や長い数字列からの日付捏造を防ぐ
        self.date_patterns = [
            r'請求日[：:\s]*(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})',
            r'発行日[：:\s]*(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})',
            r'注文日[：:\s]*(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})',
            r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})[日]?\s*請求',
            r'Invoice\s*Date[：:\s]*(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
            r'(?<![A-Za-z])(?<![A-Za-z][ \t])Date[：:\s]*(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
            r'(?<![\d/-])(\d{4})[/-](\d{1,2})[/-](\d{1,2})(?![\d/-])'
        ]

    def find_invoice_folders(self, input_folder: str) -> List[str]:
        """入力フォルダ直下の請求書フォルダ（Retail.TransactionalInvoicing.*）を列挙"""
        try:
            entries = sorted(os.listdir(input_folder))
        except OSError as e:
            logger.error(f"入力フォルダを読み取れません {input_folder}: {str(e)}")
            return []
        return [
            entry for entry in entries
            if entry.startswith(self.INVOICE_FOLDER_PREFIX)
            and os.path.isdir(os.path.join(input_folder, entry))
        ]

    def find_pdf_files(self, input_folder: str,
                       output_folder: Optional[str] = None) -> Tuple[List[str], List[str]]:
        """請求書フォルダ配下のPDFファイルを再帰的に収集する

        output_folder が請求書フォルダ配下にある場合は走査から除外し、
        出力済みファイルの再取り込みを防ぐ。
        戻り値: (発見した請求書フォルダ名リスト, PDFファイルパスリスト)
        """
        found_folders = []
        pdf_files = []
        exclude = os.path.abspath(output_folder) if output_folder else None

        def on_walk_error(error):
            logger.warning(f"フォルダを読み取れません {error.filename}: {str(error)}")

        for folder_name in self.find_invoice_folders(input_folder):
            folder_path = os.path.join(input_folder, folder_name)
            found_folders.append(folder_name)
            for root, dirs, files in os.walk(folder_path, onerror=on_walk_error):
                if exclude:
                    dirs[:] = [d for d in dirs
                               if os.path.abspath(os.path.join(root, d)) != exclude]
                for file in files:
                    if file.lower().endswith('.pdf'):
                        pdf_files.append(os.path.join(root, file))
        return found_folders, pdf_files

    def extract_invoice_date(self, pdf_path: str) -> Optional[datetime]:
        """PDFファイルから請求日を抽出"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages[:2]:
                    page_text = page.extract_text()
                    if page_text:
                        # ページ境界をまたいだ誤マッチを防ぐため区切りを入れる
                        text += page_text + "\n"
        except Exception as e:
            logger.error(f"PDFの読み取りエラー {pdf_path}: {str(e)}")
            return None

        for pattern in self.date_patterns:
            for match in re.finditer(pattern, text):
                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))

                if not (2000 <= year <= 2099 and 1 <= month <= 12 and 1 <= day <= 31):
                    continue
                try:
                    return datetime(year, month, day)
                except ValueError:
                    # 2月30日など暦上存在しない日付は次の候補へ
                    continue

        logger.warning(f"日付が見つかりませんでした: {pdf_path}")
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

            # O_EXCL による排他的作成で出力名を確保する。
            # exists チェック方式は並列実行時に同名を取り合って上書き消失するため不可。
            counter = 1
            while True:
                try:
                    fd = os.open(output_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                    os.close(fd)
                    break
                except FileExistsError:
                    # 既存ファイルと内容が同一なら再コピー不要（再実行時の冪等化）
                    if self._is_same_content(pdf_path, output_path):
                        success_msg = f"スキップ（処理済み）: {original_name} → {year_month}/{new_filename}"
                        logger.info(success_msg)
                        return pdf_path, True, success_msg
                    new_filename = f"{date_str}_{base_name}_{counter}.pdf"
                    output_path = os.path.join(output_dir, new_filename)
                    counter += 1

            try:
                shutil.copy2(pdf_path, output_path)
            except Exception:
                # コピー失敗時は確保した空ファイルを残さない
                try:
                    os.unlink(output_path)
                except OSError:
                    pass
                raise

            success_msg = f"処理完了: {original_name} → {year_month}/{new_filename}"
            logger.info(success_msg)
            return pdf_path, True, success_msg

        except Exception as e:
            error_msg = f"処理エラー {os.path.basename(pdf_path)}: {str(e)}"
            logger.error(error_msg)
            return pdf_path, False, error_msg

    @staticmethod
    def _is_same_content(path1: str, path2: str) -> bool:
        """2つのファイルの内容が同一か判定する"""
        try:
            return filecmp.cmp(path1, path2, shallow=False)
        except OSError:
            return False

    def organize_receipts(self, input_folder: str, output_folder: str) -> Tuple[int, int]:
        """領収書を整理する"""
        print(f"処理開始: {input_folder}")
        print(f"出力先: {output_folder}\n")

        found_folders, pdf_files = self.find_pdf_files(input_folder, output_folder)
        for folder_name in found_folders:
            print(f"フォルダ発見: {folder_name}")

        if not pdf_files:
            print("PDFファイルが見つかりませんでした。")
            return 0, 0

        print(f"\n{len(pdf_files)}個のPDFファイルを発見しました。\n")

        success_count = 0
        error_count = 0

        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"処理中 ({i}/{len(pdf_files)}): {os.path.basename(pdf_file)}")

            _, success, message = self.process_pdf(pdf_file, output_folder)

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
