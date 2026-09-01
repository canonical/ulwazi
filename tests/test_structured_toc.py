"""Regression tests for the sphinx-structured-toc extension integration.

Scope follows the Ulwazi testing strategy (see docs/content/testing-strategy.md
and docs/content/tests/structured-toc.md): we only check that Ulwazi's build
wires the extension up correctly and that its accessibility markup survives
Ulwazi's HTML post-processing (``_html_page_context`` in ``ulwazi/__init__.py``
rewrites parts of the page). We do not re-test the extension's internals --
only that:

* the ``domain``/``slice`` directives render in both RST and MyST source
  syntax (the MyST path goes through the ``colon_fence`` extension, which is
  a genuine compatibility risk);
* the ARIA wiring is intact: every ``aria-labelledby`` value resolves to an
  element ``id`` on the same page, and marked items carry both ``id`` and
  ``aria-labelledby``;
* the extension's ``domain-list.css`` is shipped and linked on every page.

All structural checks are grouped into a single test so CI output stays a
single line when everything passes. On failure, every individual problem
found (across all checked pages) is listed in the assertion message.

The rendered-appearance checks (inline flow, visually-hidden domain span)
run in a separate, Playwright-based test marked ``slow``.
"""

import subprocess
import sys
from pathlib import Path
from typing import cast

import pytest
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# Both fixture pages use the same slice/domain names so the same assertions
# apply to the RST and the MyST rendering path. Keep these in sync with
# docs/content/structured-toc.rst and docs/content/structured-toc-myst.md.
PAGES = {
    "rst": Path("docs/_build/content/structured-toc/index.html"),
    "myst": Path("docs/_build/content/structured-toc-myst/index.html"),
}

# One nav per domain on each fixture page: the first derives its name from
# the section heading, the second uses an explicit ``.. domain::`` argument.
EXPECTED_NAV_COUNT = 2

# Slices on each fixture page, in document order.
EXPECTED_SLICES = ["Content", "Tests", "Reference", "Meta"]

# The explicitly named domain on each fixture page.
EXPLICIT_DOMAIN_NAME = "Ulwazi sample documentation"


def _load(name: str, path: Path) -> tuple[BeautifulSoup | None, list[str]]:
    """Parse a built page, returning (soup, errors).

    A missing build yields a friendly message instead of an obscure error.
    """
    if not path.exists():
        return None, [f"[{name}] {path} not found -- run 'make docs' first"]
    with path.open(encoding="utf-8") as f:
        return BeautifulSoup(f, "lxml"), []


def _check_nav_count(name: str, soup: BeautifulSoup) -> list[str]:
    """Both domains must render as <nav class="domain-list">."""
    navs = soup.find_all("nav", class_="domain-list")
    if len(navs) != EXPECTED_NAV_COUNT:
        return [
            (
                f"[{name}] expected {EXPECTED_NAV_COUNT} domain-list <nav> "
                f"elements, found {len(navs)}"
            )
        ]
    return []


def _check_aria_references(name: str, soup: BeautifulSoup) -> list[str]:
    """Every aria-labelledby value must resolve to an element id on the page.

    This is the core accessibility contract of the extension: the nav
    landmark, the slice labels, and the marked links are all tied together
    by id references. If Ulwazi's post-processing ever strips or duplicates
    ids, screen readers lose the context these attributes provide.
    """
    errors: list[str] = []
    ids = {cast(str, el["id"]) for el in soup.find_all(id=True)}

    labelled = soup.find_all(
        attrs={"aria-labelledby": True}  # pyright: ignore[reportArgumentType]
    )
    if not labelled:
        return [f"[{name}] no aria-labelledby attributes found at all"]

    for element in labelled:
        refs = cast(str, element["aria-labelledby"]).split()
        missing = [ref for ref in refs if ref not in ids]
        if missing:
            errors.append(
                f"[{name}] aria-labelledby on <{element.name}> references "
                f"missing ids: {missing}"
            )
    return errors


def _check_slices(name: str, soup: BeautifulSoup) -> list[str]:
    """Each slice must render a labelled <span class="domain-list-label">."""
    labels = [
        span.get_text(strip=True)
        for span in soup.find_all("span", class_="domain-list-label")
    ]
    if labels != EXPECTED_SLICES:
        return [f"[{name}] slice labels are {labels}, expected {EXPECTED_SLICES}"]
    return []


def _check_marked_items(name: str, soup: BeautifulSoup) -> list[str]:
    """Items marked with the `slice`/`domain` keywords must carry both id
    and aria-labelledby on their <a> tag; unmarked items must not."""
    errors: list[str] = []
    navs = soup.find_all("nav", class_="domain-list")
    if len(navs) != EXPECTED_NAV_COUNT:
        # Already reported by _check_nav_count; skip to avoid duplicate noise.
        return errors

    # Second nav = the explicitly named domain, whose items are all marked.
    explicit_nav = navs[1]
    links = explicit_nav.find_all("a")
    if not links:
        return [f"[{name}] no links inside the explicit domain nav"]

    for link in links:
        if not link.get("id"):
            errors.append(
                f"[{name}] marked item <a>{link.get_text(strip=True)}</a> "
                "is missing its id attribute"
            )
        if not link.get("aria-labelledby"):
            errors.append(
                f"[{name}] marked item <a>{link.get_text(strip=True)}</a> "
                "is missing its aria-labelledby attribute"
            )

    # First nav = the heading-derived domain, whose items are all unmarked:
    # their accessible name is just the visible text.
    errors.extend(
        f"[{name}] unmarked item <a>{link.get_text(strip=True)}</a> "
        "unexpectedly carries id/aria-labelledby"
        for link in navs[0].find_all("a")
        if link.get("id") or link.get("aria-labelledby")
    )
    return errors


def _check_accessible_names(name: str, soup: BeautifulSoup) -> list[str]:
    """Marked items must have distinct accessible names even when their
    visible link text is identical.

    The fixture pages deliberately repeat link texts across slices; the
    extension's whole point is that the accessible name (text + labelled-by
    context) disambiguates them for screen reader users.
    """
    errors: list[str] = []
    navs = soup.find_all("nav", class_="domain-list")
    if len(navs) != EXPECTED_NAV_COUNT:
        return errors

    names: dict[str, str] = {}
    for link in navs[1].find_all("a"):
        text = link.get_text(strip=True)
        # Accessible name approximation: visible text + referenced context.
        accessible = " ".join(
            [text, *cast(str, link.get("aria-labelledby", "")).split()]
        )
        if text in names and names[text] == accessible:
            errors.append(
                f"[{name}] duplicate link text {text!r} has an identical "
                "accessible name -- ARIA context is not disambiguating"
            )
        names[text] = accessible
    return errors


def _check_css_shipped(name: str, soup: BeautifulSoup) -> list[str]:
    """The extension's domain-list.css must be linked on the page."""
    for link in soup.find_all("link", attrs={"rel": "stylesheet"}):
        if "domain-list.css" in cast(str, link.get("href", "")):
            return []
    return [f"[{name}] domain-list.css is not linked on the page"]


def _check_page(name: str, path: Path) -> list[str]:
    """Run all structured-TOC checks for one built page.

    Returns a list of human-readable failure messages; an empty list means
    every check passed for this page.
    """
    soup, errors = _load(name, path)
    if soup is None:
        return errors

    errors.extend(_check_nav_count(name, soup))
    errors.extend(_check_aria_references(name, soup))
    errors.extend(_check_slices(name, soup))
    errors.extend(_check_marked_items(name, soup))
    errors.extend(_check_accessible_names(name, soup))
    errors.extend(_check_css_shipped(name, soup))
    return errors


def test_structured_toc_markup():
    """Verify the domain/slice markup and its ARIA wiring on the RST and
    MyST fixture pages, and that the extension's CSS is linked.
    """
    errors: list[str] = []
    for name, path in PAGES.items():
        errors.extend(_check_page(name, path))

    assert not errors, "structured-TOC checks failed:\n" + "\n".join(
        f"  - {error}" for error in errors
    )


@pytest.mark.slow
def test_structured_toc_rendering():
    """Verify the rendered appearance of the domain lists in a real browser.

    The extension's domain-list.css makes slice items flow inline (one line
    per slice) and visually hides the explicit domain name span while
    keeping it in the accessibility tree. Both behaviours are easy to break
    with theme-level CSS, so they are checked with Playwright against the
    built pages.
    """
    for name, path in PAGES.items():
        resolved = path.resolve()
        assert resolved.exists(), (
            f"[{name}] {resolved} not found -- run 'make docs' first"
        )

    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=True,
    )

    with sync_playwright() as p:
        browser = p.chromium.launch()
        assert browser, "Failed to launch Chromium browser"
        page = browser.new_page()
        assert page, "Failed to create a new browser page"

        for name, path in PAGES.items():
            page.goto(f"file://{path.resolve()}")
            assert page.content(), f"[{name}] Page failed to load content"

            # Items of one slice must flow inline: all sibling <li> elements
            # of a slice's nested <ul> share the same vertical position.
            # (Allow a small tolerance for sub-pixel rounding.)
            slice_items = page.query_selector_all("nav.domain-list > ul > li > ul > li")
            assert slice_items, f"[{name}] No slice items rendered"

            first_slice_items = slice_items[:2]
            ys = []
            for item in first_slice_items:
                box = item.bounding_box()
                if box is not None:
                    ys.append(box["y"])
            assert len(ys) == 2, f"[{name}] Could not measure slice item positions"
            assert abs(ys[0] - ys[1]) < 2, (
                f"[{name}] Slice items are not rendered inline (y positions: {ys})"
            )

            # The explicit domain name span must be present in the DOM but
            # visually hidden (1px clip), so screen readers announce the
            # domain while sighted users see the compact list.
            target = page.query_selector("span.domain-aria-target")
            assert target, f"[{name}] domain-aria-target span not found"
            box = target.bounding_box()
            assert box is not None, f"[{name}] domain-aria-target span has no box"
            assert box["width"] <= 2, (
                f"[{name}] domain-aria-target span is not visually hidden (box: {box})"
            )
            assert box["height"] <= 2, (
                f"[{name}] domain-aria-target span is not visually hidden (box: {box})"
            )
            assert target.text_content() == EXPLICIT_DOMAIN_NAME, (
                f"[{name}] domain-aria-target span text is "
                f"{target.text_content()!r}, expected {EXPLICIT_DOMAIN_NAME!r}"
            )

        browser.close()
