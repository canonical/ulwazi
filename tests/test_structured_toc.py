"""Regression tests for the sphinx-structured-toc extension integration.

Scope follows the Ulwazi testing strategy (see docs/content/testing-strategy.md
and docs/content/tests/structured-toc.md): we check that Ulwazi's build wires
the extension up, that its accessibility markup survives Ulwazi's HTML
post-processing, and that the PDF includes the links from both cheat sheets.
We do not re-test the extension's internals.

The fixtures are the "Structured tables of contents" sections of the two
cheat sheets, which double as the theme's rendering reference (there are no
dedicated sample pages for this feature):

* the ``domain``/``slice`` directives render in both RST and MyST source
  syntax (the MyST path goes through the ``colon_fence`` extension, which is
  a genuine compatibility risk);
* the ARIA wiring is intact: every ``aria-labelledby`` value resolves to an
  element ``id`` on the same page, and marked items carry both ``id`` and
  ``aria-labelledby``;
* the extension's ``domain-list.css`` is shipped and linked on every page.

The tests are grouped into one fast test and one slow test, so each pytest
run reports a single line for the tier it selects (``make test`` runs the
fast test, ``make test-slow`` the slow one; a full run reports both). On
failure, every individual problem found is listed in the failure message,
tagged by page and checked part. The slow test runs its LaTeX and browser
checks independently, so a LaTeX build failure does not hide browser
problems, and a failure on one page does not hide problems on the other.
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import cast

import pytest
from bs4 import BeautifulSoup
from playwright.sync_api import Page, sync_playwright

# The cheat sheets are the fixtures: their "Structured tables of contents"
# sections use the same slice/domain names in both syntaxes, so the same
# assertions apply to the RST and the MyST rendering path. Keep these in sync
# with docs/content/rst-cheat-sheet.rst and docs/content/myst-cheat-sheet.md.
PAGES = {
    "rst": Path("docs/_build/content/rst-cheat-sheet/index.html"),
    "myst": Path("docs/_build/content/myst-cheat-sheet/index.html"),
}

# One nav per domain on each fixture page: the first derives its name from
# the section heading, the second uses an explicit ``.. domain::`` argument.
EXPECTED_NAV_COUNT = 2

# Slices on each fixture page, in document order.
EXPECTED_SLICES = ["Syntax references", "Guides", "Reference", "Meta"]

# The explicitly named domain on each fixture page.
EXPECTED_DOMAIN_NAME = "Ulwazi cheat sheet links"

DOCS_DIR = Path(__file__).resolve().parents[1] / "docs"

# Each slice must retain two actual linked list items in PDF output, not just
# its label in the prose. The cross-cheat-sheet link differs by format.
PDF_SLICE_LINKS = {
    "rst": {
        "Syntax references": ("This page", "MyST cheat sheet"),
        "Guides": ("Contribution guide", "Testing strategy"),
        "Reference": ("Overview", "Roadmap"),
        "Meta": ("Overview", "Tests"),
    },
    "myst": {
        "Syntax references": ("This page", "RST cheat sheet"),
        "Guides": ("Contribution guide", "Testing strategy"),
        "Reference": ("Overview", "Roadmap"),
        "Meta": ("Overview", "Tests"),
    },
}


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


def _latex_errors(build_dir: Path) -> list[str]:
    """Build LaTeX in an isolated directory and check both cheat sheets' output.

    ``make docs-pdf`` removes the intermediate TeX files, so build into a
    temporary directory instead. This checks actual structured-TOC content
    rather than merely checking that a PDF file exists. No TeX toolchain is
    needed here. Returns a list of human-readable failure messages; an
    empty list means every check passed.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "sphinx",
            "-b",
            "latex",
            "-W",
            "--keep-going",
            ".",
            str(build_dir),
        ],
        cwd=DOCS_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return [
            (
                f"[latex] build failed (exit {result.returncode}):\n"
                f"stdout:\n{result.stdout[-4000:]}\nstderr:\n{result.stderr[-4000:]}"
            )
        ]

    tex_files = list(build_dir.glob("*.tex"))
    if len(tex_files) != 1:
        return [f"[latex] expected one generated TeX file, got {tex_files}"]
    tex = tex_files[0].read_text(encoding="utf-8")

    errors: list[str] = []
    for name, expected_slices in PDF_SLICE_LINKS.items():
        docname = f"content/{name}-cheat-sheet"
        section = rf"\label{{\detokenize{{{docname}:structured-tables-of-contents}}}}"
        if section not in tex:
            errors.append(f"[{name}] missing structured-TOC section in LaTeX")
            continue
        # Stop at the next chapter, so one cheat sheet cannot satisfy checks
        # for the other. In particular, ordinary prose and headings elsewhere
        # in the book must not make this test pass vacuously.
        body = tex.split(section, 1)[1].split(r"\chapter{", 1)[0]
        for slice_name, link_texts in expected_slices.items():
            match = re.search(
                rf"\\textbf\{{{re.escape(slice_name)}:\}}\s*"
                r"\\begin\{itemize\}(.*?)\\end\{itemize\}",
                body,
                flags=re.DOTALL,
            )
            if match is None:
                errors.append(f"[{name}] missing bold '{slice_name}' slice and list")
                continue
            items = match.group(1)
            if items.count(r"\item ") != len(link_texts):
                errors.append(f"[{name}] '{slice_name}' has missing list items")
            errors.extend(
                f"[{name}] '{slice_name}' is missing PDF link {link_text!r}"
                for link_text in link_texts
                if rf"\DUrole{{doc}}{{{link_text}}}" not in items
            )
    return errors


def _check_inline_flow(name: str, page: Page) -> list[str]:
    """Items of one slice must flow inline: the sibling <li> elements of a
    slice's nested <ul> share the same vertical position.

    A small tolerance allows for sub-pixel rounding.
    """
    slice_items = page.query_selector_all("nav.domain-list > ul > li > ul > li")
    if not slice_items:
        return [f"[{name}] no slice items rendered"]

    ys = [
        box["y"] for item in slice_items[:2] if (box := item.bounding_box()) is not None
    ]
    if len(ys) < 2:
        return [f"[{name}] could not measure slice item positions"]
    if abs(ys[0] - ys[1]) >= 2:
        return [f"[{name}] slice items are not rendered inline (y positions: {ys})"]
    return []


def _check_domain_span(name: str, page: Page) -> list[str]:
    """The explicit domain name span must be present in the DOM but visually
    hidden (1px clip), so screen readers announce the domain while sighted
    users see the compact list."""
    target = page.query_selector("span.domain-aria-target")
    if target is None:
        return [f"[{name}] domain-aria-target span not found"]

    errors: list[str] = []
    box = target.bounding_box()
    if box is None:
        errors.append(f"[{name}] domain-aria-target span has no box")
    elif box["width"] > 2 or box["height"] > 2:
        errors.append(
            f"[{name}] domain-aria-target span is not visually hidden (box: {box})"
        )

    text = target.text_content()
    if text != EXPECTED_DOMAIN_NAME:
        errors.append(
            f"[{name}] domain-aria-target span text is {text!r}, "
            f"expected {EXPECTED_DOMAIN_NAME!r}"
        )
    return errors


def _browser_errors() -> list[str]:
    """Check the rendered appearance of the domain lists in a real browser.

    The extension's domain-list.css makes slice items flow inline (one line
    per slice) and visually hides the explicit domain name span while keeping
    it in the accessibility tree. Both behaviours are easy to break with
    theme-level CSS, so they are checked with Playwright against the built
    pages. Returns a list of human-readable failure messages; an empty list
    means every check passed.
    """
    missing = [
        f"[{name}] {path.resolve()} not found -- run 'make docs' first"
        for name, path in PAGES.items()
        if not path.resolve().exists()
    ]
    if missing:
        return missing

    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=True,
    )

    errors: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        assert browser, "Failed to launch Chromium browser"
        page = browser.new_page()
        assert page, "Failed to create a new browser page"

        try:
            for name, path in PAGES.items():
                page.goto(f"file://{path.resolve()}")
                if not page.content():
                    errors.append(f"[{name}] page failed to load content")
                    continue
                errors.extend(_check_inline_flow(name, page))
                errors.extend(_check_domain_span(name, page))
        finally:
            browser.close()
    return errors


@pytest.mark.slow
def test_structured_toc_slow(tmp_path: Path) -> None:
    """Run every slow structured-TOC check and report the outcome once.

    All slow checks (LaTeX content and rendered appearance) are grouped into
    this single test so a successful run reports one PASSED line, while any
    failure lists every specific problem found, tagged by page and part.
    The LaTeX and browser checks run independently: a LaTeX build failure
    does not hide browser problems, and vice versa.
    """
    errors = _latex_errors(tmp_path / "latex")
    errors.extend(_browser_errors())

    if errors:
        pytest.fail(
            "structured-TOC slow checks failed:\n"
            + "\n".join(f"  - {error}" for error in errors),
            pytrace=False,
        )
