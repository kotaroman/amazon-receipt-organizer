from setuptools import setup, find_packages

setup(
    name="amazon-receipt-organizer",
    version="1.0.0",
    description="Amazon PDF領収書自動整理ツール",
    author="Your Name",
    python_requires=">=3.7",
    install_requires=[
        "PyPDF2==3.0.1",
        "pdfplumber==0.11.4",
        "python-dateutil==2.9.0",
        "tkinterdnd2==0.3.0",
        "pillow==10.4.0"
    ],
    entry_points={
        "console_scripts": [
            "amazon-receipt-organizer=amazon_receipt_organizer:main",
        ],
    },
)