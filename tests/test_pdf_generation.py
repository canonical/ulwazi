from pathlib import Path

import pytest

PDF_FILE_PATH = "docs/_build/theulwazithemesample.pdf"


@pytest.mark.slow
def test_pdf_exists():
    assert Path(PDF_FILE_PATH).exists(), f"Missing PDF: {PDF_FILE_PATH}"
