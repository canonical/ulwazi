import subprocess
import sys
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

INDEX_PATH = "docs/_build/index.html"
EXPECTED_COLOR = ("rgb(128, 0, 128)", "purple")

TYPOGRAPHY_PATH = "docs/_build/content/typography-verification/index.html"

# Sidebar nav geometry: the active-item indicator bar is 3px wide at the very
# left edge of the link, and the gap between the bar and the first letter must
# be exactly 16px, so the link text inset is 3px + 16px = 19px.
NAV_INDICATOR_WIDTH = "3px"
NAV_TEXT_INSET = "19px"


def test_scss_styles_propagation():
    assert Path(INDEX_PATH).exists(), f"index.html not found in {INDEX_PATH}"

    with Path(INDEX_PATH).open(encoding="utf-8") as f:
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
def test_sidebar_active_item_indicator_gap():
    """The active sidebar nav item must have a 16px gap between its 3px
    indicator bar (at the link's left edge) and the link text."""
    index_path = Path(INDEX_PATH).resolve()
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

        active_selector = "a.p-side-navigation__link.is-active"
        assert page.query_selector(active_selector), (
            f"Expected element '{active_selector}' not found"
        )

        padding_left = page.eval_on_selector(
            active_selector, "el => window.getComputedStyle(el).paddingLeft"
        )
        assert padding_left == NAV_TEXT_INSET, (
            f"Active nav link padding-left is {padding_left}, "
            f"expected {NAV_TEXT_INSET}"
        )

        indicator = page.eval_on_selector(
            active_selector,
            "el => {"
            "  const s = window.getComputedStyle(el, '::before');"
            "  return {left: s.left, width: s.width};"
            "}",
        )
        assert indicator["left"] == "0px", (
            f"Active indicator left is {indicator['left']}, expected 0px"
        )
        assert indicator["width"] == NAV_INDICATOR_WIDTH, (
            f"Active indicator width is {indicator['width']}, "
            f"expected {NAV_INDICATOR_WIDTH}"
        )

        # The gap between the indicator bar and the text must be exactly 16px:
        # 19px inset - 3px bar = 16px.
        gap_px = int(padding_left.rstrip("px")) - int(
            indicator["width"].rstrip("px")
        )
        assert gap_px == 16, f"Indicator-to-text gap is {gap_px}px, expected 16px"

        # Active and inactive links at the same level must stay left-aligned.
        inactive_selector = "a.p-side-navigation__link:not(.is-active)"
        assert page.query_selector(inactive_selector), (
            f"Expected element '{inactive_selector}' not found"
        )
        active_left = page.eval_on_selector(
            active_selector, "el => el.getBoundingClientRect().left"
        )
        inactive_left = page.eval_on_selector(
            inactive_selector, "el => el.getBoundingClientRect().left"
        )
        assert active_left == inactive_left, (
            f"Active link left ({active_left}) does not match inactive link "
            f"left ({inactive_left}); nav items are no longer left-aligned"
        )

        browser.close()


@pytest.mark.slow
def test_ordered_list_marker_matches_text_size():
    typography_path = Path(TYPOGRAPHY_PATH).resolve()
    assert typography_path.exists(), f"Typography page not found at {typography_path}"

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
