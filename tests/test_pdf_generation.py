import os

import pytest

PDF_FILE_PATH = "docs/_build/theulwazithemesample.pdf"


@pytest.mark.slow
def test_pdf_exists():
    assert os.path.exists(PDF_FILE_PATH), f"Missing PDF: {PDF_FILE_PATH}"
