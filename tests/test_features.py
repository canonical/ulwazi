"""Grouped fast markup and slow interaction regressions for theme-owned features."""

import functools
import http.server
import re
import subprocess
import sys
import threading
from collections import Counter
from contextlib import contextmanager

import pytest
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import expect, sync_playwright

from js_coverage import JSCoverageRecorder

CHEAT_SHEETS = ("content/myst-cheat-sheet", "content/rst-cheat-sheet")
ADMONITIONS = ("content/test6_admonitions", "content/test7_admonitionsMD")
NOTIFICATIONS = {
    "Attention": "caution",
    "Caution": "caution",
    "Danger": "caution",
    "Error": "negative",
    "Hint": "positive",
    "Important": "information",
    "Note": "information",
    "Tip": "positive",
    "Warning": "caution",
}


def _check_toc(name, soup):
    """The theme's local TOC stops at configured depth and retains Vanilla markup."""
    errors = []
    toc = soup.select_one("nav.p-table-of-contents__nav")
    if toc is None:
        return [f"[{name}] local TOC: missing nav"]
    links = [
        link.get("href")
        for link in toc.select(
            "li.p-table-of-contents__item > a.p-table-of-contents__link"
        )
    ]
    if "#h4-heading" not in links or "#h5-heading" in links:
        errors.append(f"[{name}] local TOC: expected H4 but not H5 at depth 3")
    if not toc.select_one('a.p-top__link[href="#"]'):
        errors.append(f"[{name}] local TOC: missing Back to top link")
    return errors


def _check_tabs(name, soup):
    """Every converted sphinx-design set exposes a consistent initial tab state."""
    errors = []
    containers = soup.select("article .p-tabs")
    if not containers:
        return [f"[{name}] tabs: no Vanilla tab sets"]
    sync_ids = set()
    for index, container in enumerate(containers):
        tablist = container.select_one('[role="tablist"].p-tabs__list')
        buttons = tablist.select('[role="tab"].p-tabs__link') if tablist else []
        if not buttons:
            errors.append(f"[{name}] tabs set {index}: missing tablist/buttons")
            continue
        if sum(btn.get("aria-selected") == "true" for btn in buttons) != 1:
            errors.append(
                f"[{name}] tabs set {index}: expected exactly one selected tab"
            )
        for btn in buttons:
            sync_ids.add(btn.get("data-sync-id"))
            panel = container.find(id=btn.get("aria-controls"))
            if (
                not btn.get("id")
                or not panel
                or panel.get("role") != "tabpanel"
                or panel.get("aria-labelledby") != btn.get("id")
            ):
                errors.append(
                    f"[{name}] tabs set {index}: broken panel for {btn.get_text(' ', strip=True)!r}"
                )
            elif panel.has_attr("hidden") == (btn.get("aria-selected") == "true"):
                errors.append(
                    f"[{name}] tabs set {index}: panel visibility disagrees with {btn.get_text(' ', strip=True)!r}"
                )
    if name.endswith("myst-cheat-sheet") and not {"key1", "key2", "key3"} <= sync_ids:
        errors.append(f"[{name}] tabs: missing MyST sync IDs key1/key2/key3")
    return errors


def _check_admonitions(name, soup, *, full_mapping=False):
    """Test Ulwazi's mapping and preservation, not docutils' parsing rules."""
    errors = []
    notices = soup.select('main#content article [class*="p-notification--"]')
    if not notices:
        return [f"[{name}] admonitions: no converted notifications"]
    found = Counter()
    for notice in notices:
        title = notice.select_one("h5.p-notification__title")
        message = notice.select_one("div.p-notification__message")
        text = title.get_text(" ", strip=True) if title else ""
        expected = NOTIFICATIONS.get(text, "information")
        found[text] += 1
        if f"p-notification--{expected}" not in notice.get("class", []):
            errors.append(f"[{name}] admonition {text!r}: expected {expected}")
        if not title or not message or not message.get_text(" ", strip=True):
            errors.append(f"[{name}] admonition {text!r}: lost title or message")
    if full_mapping:
        errors.extend(
            f"[{name}] admonitions: missing {title!r} fixture"
            for title in NOTIFICATIONS
            if not found[title]
        )
        if not any(title.startswith("Generic Admonition") for title in found):
            errors.append(f"[{name}] admonitions: missing generic fallback")
        if name.endswith("test7_admonitionsMD") and not found["See also"]:
            errors.append(f"[{name}] admonitions: missing See also fallback")
    if name.endswith("test7_admonitionsMD") and (
        not soup.select_one("div#note-reference.p-notification--information")
        or not soup.select_one('a[href="#note-reference"]')
    ):
        errors.append(f"[{name}] admonitions: note-reference target/link lost")
    return errors


def _check_inline_code_and_tables(name, soup):
    """Verify both cheatsheets' inline code and representative table content."""
    errors = []
    inline_code = soup.select_one("#inline-formatting li code")
    if (
        not inline_code
        or inline_code.get_text(strip=True) != "code"
        or inline_code.get("class")
        or inline_code.find() is not None
    ):
        errors.append(f"[{name}] inline code: expected plain <code>code</code>")

    for kind in ("grid-tables", "list-tables", "csv-tables"):
        table = soup.select_one(f"section#{kind} table.docutils")
        cells = table.select("tbody tr:first-child td") if table else []
        if (
            not table
            or [cell.get_text(" ", strip=True) for cell in table.select("thead th")]
            != ["Header 1", "Header 2"]
            or len(cells) != 2
            or not all(
                cell.get_text(" ", strip=True).startswith(expected)
                for cell, expected in zip(cells, ("[1,1]", "[1,2]"))
            )
        ):
            errors.append(f"[{name}] {kind}: expected header and first data row")
    return errors


def test_features_fast(built_site):
    """One grouped fast result for Python post-processing and theme markup."""
    errors = []
    name = "content/test-code-headings"
    soup = built_site.page(name)
    article = soup.select_one("main#content article")
    if article:
        for level in (1, 2, 3):
            heading = article.select_one(f"h{level}.p-heading--{level}")
            expected_code = "code example inserted" if level == 1 else "with code"
            if (
                not heading
                or not heading.select_one("code")
                or expected_code not in heading.get_text(" ", strip=True)
            ):
                errors.append(
                    f"[{name}] headings: h{level} must keep inline code and Vanilla class"
                )
        current = soup.select_one('#drawer a[aria-current="page"]')
        if (
            not current
            or "is-active" not in current.get("class", [])
            or current.select_one("code")
            or "code example inserted" not in current.get_text(" ", strip=True)
        ):
            errors.append(
                f"[{name}] navigation: code title must be plain text and current"
            )
    else:
        errors.append(f"[{name}] headings: missing main article")

    for name in CHEAT_SHEETS:
        soup = built_site.page(name)
        errors.extend(_check_toc(name, soup))
        errors.extend(_check_tabs(name, soup))
        errors.extend(_check_admonitions(name, soup))
        errors.extend(_check_inline_code_and_tables(name, soup))
        body_list = soup.select_one(
            "main#content article ul.p-list--unordered > li.p-list__item"
        )
        if not body_list or body_list.find_parent(class_="toctree-wrapper"):
            errors.append(f"[{name}] lists: expected Vanilla classes on a body list")
        if not soup.select_one(
            "main#content article .highlight-yaml pre span"
        ) or not soup.select_one('script[src*="copybutton.js"]'):
            errors.append(
                f"[{name}] code blocks: missing highlighted YAML or copybutton script"
            )

    for name in ADMONITIONS:
        errors.extend(
            _check_admonitions(name, built_site.page(name), full_mapping=True)
        )

    search = built_site.page("search")
    map_tag = next(
        (
            tag
            for tag in search.select("script:not([src])")
            if "SEARCH_BREADCRUMB_MAP" in tag.get_text()
        ),
        None,
    )
    if (
        not map_tag
        or '"content/test-code-headings"' not in map_tag.get_text()
        or '"This is a test"' not in map_tag.get_text()
    ):
        errors.append(
            "[search] breadcrumb map: code-heading page must have 'This is a test' ancestor"
        )

    assert not errors, "Features [fast] checks failed:\n  - " + "\n  - ".join(errors)


@contextmanager
def _serve_site(output):
    """Serve searchindex.js over HTTP; file:// fetches are browser-dependent."""

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):  # noqa: A002
            """Avoid logging every asset request in a passing pytest recap."""

    handler = functools.partial(QuietHandler, directory=str(output))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.slow
@pytest.mark.coverage_js
def test_features_slow(built_site):  # noqa: PLR0915
    """One browser result for controls that cannot be verified in static HTML."""
    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"], check=True
    )
    errors = []
    js_coverage = JSCoverageRecorder(built_site.output / "_static")
    with _serve_site(built_site.output) as base, sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            context = browser.new_context(viewport={"width": 1280, "height": 900})
            context.grant_permissions(
                ["clipboard-read", "clipboard-write"], origin=base
            )
            page = context.new_page()
            page_errors = []
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            js_coverage.start(page)

            def navigate(path):
                page.goto(f"{base}/{path}", wait_until="domcontentloaded")

            def journey(label, check, start="content/myst-cheat-sheet/"):
                try:
                    navigate(start)
                    check()
                except (AssertionError, PlaywrightError) as exc:
                    errors.append(f"[{label}] {str(exc)[-1600:].strip()}")

            def cookie_consent():
                # A fresh browser context has no consent cookie. Test the
                # integration with Canonical's bundle before other journeys.
                assert not any(
                    cookie.get("name") == "_cookies_accepted"
                    for cookie in context.cookies()
                ), "consent cookie is already set on a first visit"
                notification = page.locator(
                    "dialog.cookie-policy[open] .cookie-notification-modal"
                )
                expect(notification).to_be_visible(timeout=15000)
                notification.get_by_role("button", name="Accept all").click()
                expect(page.locator("dialog.cookie-policy")).to_have_count(0)
                assert any(
                    cookie.get("name") == "_cookies_accepted"
                    and cookie.get("value") == "all"
                    for cookie in context.cookies()
                ), "accepting consent did not save the preference"

                # On a new page in the same context, the saved consent must
                # prevent the first-visit dialog from appearing again.
                navigate("content/rst-cheat-sheet/")
                page.wait_for_load_state("load")
                expect(page.locator("dialog.cookie-policy")).to_have_count(0)

                # The footer is theme-owned; the modal comes from the remote
                # cookie bundle. Check that their integration still works.
                page.locator("footer a.js-revoke-cookie-manager").click()
                expect(notification).to_be_visible(timeout=15000)
                notification.get_by_role("button", name="Accept all").click()
                expect(page.locator("dialog.cookie-policy")).to_have_count(0)

            def navigation():
                item = (
                    page.locator("#drawer .nav-item[data-checkbox]")
                    .filter(
                        has=page.locator(
                            "a.p-side-navigation__link", has_text="This is a test"
                        )
                    )
                    .first
                )
                checkbox = item.locator("input.toctree-checkbox")
                children = item.locator("xpath=following-sibling::ul[1]")
                expect(checkbox).not_to_be_checked()
                item.locator("label").click()
                expect(checkbox).to_be_checked()
                expect(children).to_be_visible()
                item.locator("label").click()
                expect(checkbox).not_to_be_checked()
                expect(children).to_be_hidden()

            def tabs():
                tabset = (
                    page.locator("main .p-tabs")
                    .filter(has=page.get_by_text("Content Tab 1", exact=True))
                    .first
                )
                second = tabset.get_by_role("tab", name="Tab 2")
                second.click()
                expect(second).to_have_attribute("aria-selected", "true")
                expect(
                    tabset.locator(f"#{second.get_attribute('aria-controls')}")
                ).to_contain_text("Content Tab 2")
                second.press(
                    "ArrowRight"
                )  # vanilla-tabs.js selects the next tab on keyup/focus.
                third = tabset.get_by_role("tab", name="Tab 3")
                expect(third).to_be_focused()
                expect(third).to_have_attribute("aria-selected", "true")
                expect(
                    tabset.locator(f"#{third.get_attribute('aria-controls')}")
                ).to_be_visible()

            def copy_button():
                # Test the extension-generated control with a real Chromium
                # clipboard, not merely the presence of copybutton.js.
                block = page.locator(
                    "#code-blocks-font-test .highlight-yaml .highlight"
                ).first
                button = block.locator("button.copybtn")
                expect(button).to_be_attached()
                source = block.locator("pre")
                assert button.get_attribute("data-clipboard-target") == (
                    f"#{source.get_attribute('id')}"
                ), "copy button must target the displayed code block"
                expect(source).to_contain_text("example: true")
                button.click()
                expect(button).to_have_class(re.compile(r"\bsuccess\b"))
                copied = page.evaluate("navigator.clipboard.readText()")
                assert "example: true" in copied, (
                    f"copy button copied unexpected text: {copied!r}"
                )

            def theme():
                toggle = page.locator(".theme-toggle")
                toggle.click()
                expect(page.locator("body")).to_have_class(re.compile(r"\bis-dark\b"))
                expect(toggle).to_have_attribute("aria-pressed", "true")
                assert (
                    page.evaluate("localStorage.getItem('ulwazi-theme')") == "is-dark"
                )
                navigate("content/rst-cheat-sheet/")
                expect(page.locator("html")).to_have_class(re.compile(r"\bis-dark\b"))
                expect(page.locator("body")).to_have_class(re.compile(r"\bis-dark\b"))
                page.locator(".theme-toggle").click()
                expect(page.locator("body")).to_have_class(re.compile(r"\bis-light\b"))
                assert (
                    page.evaluate("localStorage.getItem('ulwazi-theme')") == "is-light"
                )

            def search():
                page.locator("form.p-search-box input[name=q]").fill("Significantly")
                page.locator("form.p-search-box button[type=submit]").click()
                result = (
                    page.locator("#search-results ul.search > li")
                    .filter(has=page.locator('a[href*="content/test-code-headings/"]'))
                    .first
                )
                try:
                    expect(result).to_be_visible(timeout=15000)
                except (AssertionError, PlaywrightError) as exc:
                    raise AssertionError(
                        f"{exc}; URL={page.url}; search markup="
                        f"{page.locator('#search-results').inner_html()[:1200]}; "
                        f"JS errors={page_errors[-6:]}"
                    ) from exc
                crumb = result.locator(".search-result-breadcrumb")
                expect(crumb).to_have_count(1)
                expect(crumb).to_contain_text("This is a test")
                result.locator(":scope > a[href]").click()
                expect(page.locator("main#content h1")).to_contain_text(
                    "Page title with"
                )

            for label, check, start in (
                ("cookie consent", cookie_consent, ""),
                ("navigation", navigation, "content/myst-cheat-sheet/"),
                ("tabs", tabs, "content/myst-cheat-sheet/"),
                ("copy button", copy_button, "content/myst-cheat-sheet/"),
                ("dark mode", theme, "content/myst-cheat-sheet/"),
                ("search", search, "content/myst-cheat-sheet/"),
            ):
                journey(label, check, start)
            js_coverage.stop(page)
            context.close()
        finally:
            browser.close()

    js_report = js_coverage.write()
    for name, data in js_report.items():
        print(f"[js-coverage] {name}: {data['percent']}%")

    assert not errors, "Features [slow] checks failed:\n  - " + "\n  - ".join(errors)
