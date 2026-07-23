import subprocess
import sys
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

INDEX_PATH = "docs/_build/index.html"
EXPECTED_COLOR = ("rgb(128, 0, 128)", "purple")

TYPOGRAPHY_PATH = "docs/_build/content/typography-verification/index.html"


def test_scss_styles_propagation():
    assert Path(INDEX_PATH).exists(), f"index.html not found in {INDEX_PATH}"

    with Path(INDEX_PATH, encoding="utf-8").open() as f:
        soup = BeautifulSoup(f, "lxml")

    target = soup.find("p", class_="heading-test-scss")
    assert target is not None, "Expected <p class='heading-test-scss'> not found"
    assert "This is a test about SCSS propagation." in target.text, (
        "Expected text not found inside <p class='heading-test-scss'>"
    )


@pytest.mark.slow
def test_rendered_color():
    index_path = Path("docs/_build/index.html").resolve()
    assert Path(index_path).exists(), f"index.html not found in {index_path}"
    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=True,
    )
    with sync_playwright() as p:
        browser = p.chromium.launch()
        assert browser, "Failed to launch Chromium browser"
        page = browser.new_page()
        assert page, "Failed to create a new browser page"
        page.goto(f"file://{index_path}")
        assert page.content(), "Page failed to load content"

        # Check if element exists
        assert page.query_selector("p.heading-test-scss"), (
            "Element <p class='heading-test-scss'> not found"
        )

        color = page.eval_on_selector(
            "p.heading-test-scss", "el => window.getComputedStyle(el).color"
        )
        assert color is not None, "Failed to retrieve computed color from element"

        print(f"[DEBUG] Computed color: {color}")
        assert color in EXPECTED_COLOR, (
            f"Color is not correct (check SCSS properties propagation): {color}"
        )

        browser.close()

@pytest.mark.slow
def test_ordered_list_marker_matches_text_size():
    typography_path = Path(TYPOGRAPHY_PATH).resolve()
    assert typography_path.exists()
    assert Path(typography_path).exists(), f"index.html not found in {typography_path}"

    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=True,
    )
    with sync_playwright() as p:
        browser = p.chromium.launch()
        assert browser, "Failed to launch Chromium browser"
        page = browser.new_page()
        assert page, "Failed to create a new browser page"
        page.goto(f"file://{typography_path}")
        assert page.content(), "Page failed to load content"

        # Check if list element exists
        li_selector = "#lists-typography ol.p-list--ordered > li"
        assert page.query_selector(li_selector), (
            f"Expected element '{li_selector}' not found"
        )

        marker_size = page.eval_on_selector(
               li_selector, "el => window.getComputedStyle(el, '::marker').fontSize"
        )

        text_selector = f"{li_selector} > p"
        assert page.query_selector(text_selector), (
            f"Expected element '{text_selector}' not found"
        )

        text_size = page.eval_on_selector(
               text_selector, "el => window.getComputedStyle(el).fontSize"
        )

        assert marker_size == text_size, (
            f"Marker font-size ({marker_size}) does not match "
            f"list text font-size ({text_size})"
        )

        browser.close()

