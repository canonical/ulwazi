import os

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

INDEX_PATH = "docs/_build/index.html"
EXPECTED_COLOR = ("rgb(128, 0, 128)", "purple")


def test_scss_styles_propagation():
    assert os.path.exists(INDEX_PATH), f"index.html not found in {INDEX_PATH}"

    with open(INDEX_PATH, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "lxml")

    target = soup.find("p", class_="heading-test-scss")
    assert target is not None, "Expected <p class='heading-test-scss'> not found"
    assert "This is a test about SCSS propagation." in target.text, (
        "Expected text not found inside <p class='heading-test-scss'>"
    )


def test_rendered_color():
    index_path = os.path.abspath("docs/_build/index.html")
    assert os.path.exists(index_path), f"index.html not found in {index_path}"
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
