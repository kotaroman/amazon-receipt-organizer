from setuptools import setup

setup(
    name="amazon-receipt-organizer",
    version="1.0.0",
    description="Amazon PDF領収書自動整理ツール",
    author="Your Name",
    python_requires=">=3.9",
    py_modules=["amazon_receipt_organizer", "cli_organizer", "pdf_processor"],
    install_requires=[
        "pdfplumber==0.11.4",
        "tkinterdnd2==0.6.2",
        "pillow==10.4.0"
    ],
    entry_points={
        "console_scripts": [
            "amazon-receipt-organizer-cli=cli_organizer:main",
        ],
        "gui_scripts": [
            "amazon-receipt-organizer=amazon_receipt_organizer:main",
        ],
    },
)
