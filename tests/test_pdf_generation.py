import os
import subprocess

PDF_FILE_PATH = "docs/_build/theulwazithemesample.pdf"

def test_pdf_builds():
    build_process = subprocess.run(["make", "pdf"], check=True, timeout=300)
    assert build_process.returncode == 0, "PDF build process failed"

def test_pdf_exists():
    assert os.path.exists(PDF_FILE_PATH), f"Missing PDF: {PDF_FILE_PATH}"
