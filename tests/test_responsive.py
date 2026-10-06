"""Responsive layout tests: how the page is laid out at each screen class.

The screen classes and their widths are defined in the testing strategy
(docs/content/testing-strategy.md, under the "Responsive layout and cross-browser
tests" title).

The HTML is the same at every width, so these tests open the page
in a real browser and check what is visible and where it sits.
"""

import subprocess
import sys
from pathlib import Path

import pytest
from playwright.sync_api import expect, sync_playwright

INDEX_PATH = "docs/_build/index.html"

# Width in CSS pixels at which each screen class is tested. The height only
# decides how much of the page fits on the first screen.
DESKTOP_WIDTH = 1280
MOBILE_WIDTH = 375
SCREEN_HEIGHT = 900

# The three parts of the page that sit side by side on a desktop screen.
SIDE_NAVIGATION = "#drawer"
MAIN_CONTENT = "main#content"
ON_THIS_PAGE = "aside.p-table-of-contents"

# The dark bar at the top of the page: its links, and the "Menu" button that
# replaces the links on smaller screens.
TOP_BAR_LINKS = "header#navigation .p-navigation__items"
TOP_BAR_MENU_BUTTON = "header#navigation .p-navigation__toggle--open"
TOP_BAR_CLOSE_BUTTON = "header#navigation .p-navigation__toggle--close"

# The three-line (hamburger) icon for the side navigation on smaller screens.
SIDE_MENU_ICON = "label.hide-when-primary-sidebar-shown"


@pytest.mark.slow
def test_desktop_layout():
    """Check how the home page looks on a desktop screen (1280 px wide).

    What we test:

    1. The side navigation on the left is visible.
    2. The main content in the middle is visible.
    3. The "On this page" list on the right is visible.
    4. The top bar shows its links.
    5. The top bar "Menu" button is hidden, because the links already fit.
    6. The side navigation sits to the left of the main content.
    7. The "On this page" list sits to the right of the main content.
    """
    index_path = Path(INDEX_PATH).resolve()
    assert index_path.exists(), f"index.html not found in {index_path}"
    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=True,
    )
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": DESKTOP_WIDTH, "height": SCREEN_HEIGHT}
        )
        page.goto(f"file://{index_path}")

        for name, selector in (
            ("side navigation", SIDE_NAVIGATION),
            ("main content", MAIN_CONTENT),
            ('"On this page" list', ON_THIS_PAGE),
            ("top bar links", TOP_BAR_LINKS),
        ):
            assert page.locator(selector).is_visible(), (
                f"[desktop] {name} is not visible"
            )

        # The top bar links are shown in full, so there is nothing to open.
        assert not page.locator(TOP_BAR_MENU_BUTTON).is_visible(), (
            '[desktop] top bar "Menu" button is visible'
        )

        # Where each part starts, in pixels from the left edge of the screen.
        left_edge = "el => el.getBoundingClientRect().left"
        side_navigation = page.locator(SIDE_NAVIGATION).evaluate(left_edge)
        main_content = page.locator(MAIN_CONTENT).evaluate(left_edge)
        on_this_page = page.locator(ON_THIS_PAGE).evaluate(left_edge)

        assert side_navigation < main_content, (
            "[desktop] side navigation is not to the left of the content"
        )
        assert main_content < on_this_page, (
            '[desktop] "On this page" list is not to the right of the content'
        )

        browser.close()


@pytest.mark.slow
def test_mobile_layout():
    """Check how the home page looks on a mobile screen (375 px wide).

    What we test:

    1. The main content is visible.
    2. The page fits the screen, so there is no sideways scrolling.
    3. The top bar hides its links and shows the "Menu" button instead.
    4. Clicking "Menu" shows the top bar links.
    5. Clicking "Close menu" hides the top bar links again.
    6. The three-line (hamburger) icon for the side navigation is visible.
    """
    index_path = Path(INDEX_PATH).resolve()
    assert index_path.exists(), f"index.html not found in {index_path}"
    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=True,
    )
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": MOBILE_WIDTH, "height": SCREEN_HEIGHT}
        )
        page.goto(f"file://{index_path}")

        assert page.locator(MAIN_CONTENT).is_visible(), (
            "[mobile] main content is not visible"
        )

        # The page is wider than the screen only if something sticks out.
        page_width = page.evaluate("document.documentElement.scrollWidth")
        assert page_width <= MOBILE_WIDTH, (
            f"[mobile] page is {page_width} px wide and scrolls sideways"
        )

        top_bar_links = page.locator(TOP_BAR_LINKS)
        assert page.locator(TOP_BAR_MENU_BUTTON).is_visible(), (
            '[mobile] top bar "Menu" button is not visible'
        )
        assert not top_bar_links.is_visible(), (
            "[mobile] top bar links are visible before the menu is opened"
        )

        # expect() waits a moment for the page to react to the click.
        page.locator(TOP_BAR_MENU_BUTTON).click()
        expect(top_bar_links).to_be_visible()

        page.locator(TOP_BAR_CLOSE_BUTTON).click()
        expect(top_bar_links).to_be_hidden()

        assert page.locator(SIDE_MENU_ICON).is_visible(), (
            "[mobile] three-line icon for the side navigation is not visible"
        )

        browser.close()


@pytest.mark.slow
def test_mobile_side_navigation():
    """Check the side navigation on a mobile screen (375 px wide).

    This test is expected to fail until
    https://github.com/canonical/ulwazi/issues/168 is fixed.

    What we test:

    1. The side navigation is hidden when the page loads.
    2. Clicking the three-line (hamburger) icon shows the side navigation.
    """
    index_path = Path(INDEX_PATH).resolve()
    assert index_path.exists(), f"index.html not found in {index_path}"
    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=True,
    )
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": MOBILE_WIDTH, "height": SCREEN_HEIGHT}
        )
        page.goto(f"file://{index_path}")

        # The links inside the side navigation are what the reader sees.
        side_navigation_links = page.locator(f"{SIDE_NAVIGATION} a").first
        assert not side_navigation_links.is_visible(), (
            "[mobile] side navigation is visible before its icon is clicked"
        )

        page.locator(SIDE_MENU_ICON).click()
        expect(side_navigation_links).to_be_visible()

        browser.close()
