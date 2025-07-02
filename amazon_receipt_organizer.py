#!/usr/bin/env python3
import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import pdfplumber
import re
from datetime import datetime
from pathlib import Path
import logging
from typing import Optional, Tuple
import concurrent.futures
from threading import Thread

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


class ReceiptOrganizerGUI:
    def __init__(self):
        self.root = TkinterDnD.Tk()
        self.root.title("Amazon Receipt Organizer")
        self.root.geometry("800x600")
        
        self.processor = PDFProcessor()
        self.processing = False
        
        self.setup_gui()
        
    def setup_gui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        drop_frame = ttk.LabelFrame(main_frame, text="フォルダをドラッグ&ドロップ", padding="20")
        drop_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=10)
        
        self.drop_label = ttk.Label(drop_frame, text="ここにフォルダをドロップしてください", 
                                   font=("", 12), anchor="center")
        self.drop_label.grid(row=0, column=0, pady=20)
        
        drop_frame.drop_target_register(DND_FILES)
        drop_frame.dnd_bind('<<Drop>>', self.on_drop)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, pady=10)
        
        self.select_button = ttk.Button(button_frame, text="フォルダを選択", 
                                       command=self.select_folder)
        self.select_button.grid(row=0, column=0, padx=5)
        
        self.output_button = ttk.Button(button_frame, text="出力先を変更", 
                                       command=self.select_output)
        self.output_button.grid(row=0, column=1, padx=5)
        
        self.output_path = os.path.join(os.path.expanduser("~"), "Desktop", "整理済み領収書")
        self.output_label = ttk.Label(main_frame, text=f"出力先: {self.output_path}")
        self.output_label.grid(row=2, column=0, sticky=(tk.W), pady=5)
        
        progress_frame = ttk.LabelFrame(main_frame, text="処理状況", padding="10")
        progress_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        progress_frame.columnconfigure(0, weight=1)
        progress_frame.rowconfigure(0, weight=1)
        
        self.progress_text = tk.Text(progress_frame, wrap=tk.WORD, height=15)
        self.progress_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(progress_frame, orient="vertical", 
                                 command=self.progress_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.progress_text.configure(yscrollcommand=scrollbar.set)
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=10)
        
        stats_frame = ttk.Frame(main_frame)
        stats_frame.grid(row=5, column=0, pady=5)
        
        self.stats_label = ttk.Label(stats_frame, text="準備完了")
        self.stats_label.grid(row=0, column=0)

    def on_drop(self, event):
        if self.processing:
            messagebox.showwarning("処理中", "現在処理中です。完了までお待ちください。")
            return
            
        paths = self.root.tk.splitlist(event.data)
        if paths:
            self.process_folder(paths[0])

    def select_folder(self):
        if self.processing:
            messagebox.showwarning("処理中", "現在処理中です。完了までお待ちください。")
            return
            
        folder = filedialog.askdirectory(title="処理するフォルダを選択")
        if folder:
            self.process_folder(folder)

    def select_output(self):
        folder = filedialog.askdirectory(title="出力先フォルダを選択")
        if folder:
            self.output_path = folder
            self.output_label.config(text=f"出力先: {self.output_path}")

    def add_log(self, message: str, tag: str = None):
        self.progress_text.insert(tk.END, f"{message}\n")
        if tag:
            start = self.progress_text.index(f"end-2c linestart")
            end = self.progress_text.index(f"end-1c")
            self.progress_text.tag_add(tag, start, end)
            if tag == "error":
                self.progress_text.tag_config(tag, foreground="red")
            elif tag == "success":
                self.progress_text.tag_config(tag, foreground="green")
        self.progress_text.see(tk.END)
        self.root.update()

    def process_folder(self, folder_path: str):
        if not os.path.isdir(folder_path):
            messagebox.showerror("エラー", "選択されたパスはフォルダではありません。")
            return
        
        thread = Thread(target=self._process_folder_thread, args=(folder_path,))
        thread.daemon = True
        thread.start()

    def _process_folder_thread(self, folder_path: str):
        self.processing = True
        self.progress_bar.start()
        self.select_button.config(state='disabled')
        
        try:
            self.add_log(f"\n処理開始: {folder_path}")
            self.add_log(f"出力先: {self.output_path}\n")
            
            pdf_files = []
            for invoice_folder in self.processor.invoice_folders:
                invoice_path = os.path.join(folder_path, invoice_folder)
                if os.path.exists(invoice_path):
                    self.add_log(f"フォルダ発見: {invoice_folder}")
                    for file in os.listdir(invoice_path):
                        if file.lower().endswith('.pdf'):
                            pdf_files.append(os.path.join(invoice_path, file))
            
            if not pdf_files:
                self.add_log("PDFファイルが見つかりませんでした。", "error")
                return
            
            self.add_log(f"\n{len(pdf_files)}個のPDFファイルを発見しました。\n")
            
            success_count = 0
            error_count = 0
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    executor.submit(self.processor.process_pdf, pdf, self.output_path): pdf 
                    for pdf in pdf_files
                }
                
                for future in concurrent.futures.as_completed(futures):
                    pdf_path, success, message = future.result()
                    if success:
                        self.add_log(f"✓ {message}", "success")
                        success_count += 1
                    else:
                        self.add_log(f"✗ {message}", "error")
                        error_count += 1
                    
                    total = success_count + error_count
                    self.stats_label.config(
                        text=f"処理済み: {total}/{len(pdf_files)} (成功: {success_count}, エラー: {error_count})"
                    )
            
            self.add_log(f"\n処理完了！")
            self.add_log(f"成功: {success_count}件")
            self.add_log(f"エラー: {error_count}件", "error" if error_count > 0 else None)
            
            messagebox.showinfo("完了", 
                              f"処理が完了しました。\n成功: {success_count}件\nエラー: {error_count}件")
            
        except Exception as e:
            self.add_log(f"\n予期しないエラー: {str(e)}", "error")
            messagebox.showerror("エラー", f"処理中にエラーが発生しました。\n{str(e)}")
            
        finally:
            self.processing = False
            self.progress_bar.stop()
            self.select_button.config(state='normal')

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = ReceiptOrganizerGUI()
    app.run()