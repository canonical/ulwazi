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

import io
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest
import tinycss2
from bs4 import BeautifulSoup
from playwright.sync_api import Page, sync_playwright
from sphinx.application import Sphinx
from sphinx.util.docutils import docutils_namespace, patch_docutils

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

# Ulwazi's temporary structured-TOC styling (see
# ulwazi/theme/ulwazi/static/css/structured-toc.css); checked here rather
# than re-tested in test_assets_structure.py since it is specific to this
# extension's integration, not a general asset check.
STRUCTURED_TOC_CSS = Path("docs/_build/_static/css/structured-toc.css")

# Light/dark separator colours the stylesheet falls back to when a project
# does not set ulwazi_structured_toc_separator_color_light/_dark.
DEFAULT_SEPARATOR_RGB = {"light": "rgb(233, 84, 32)", "dark": "rgb(255, 255, 255)"}

CONF_TEMPLATE = """
project = "structured-toc-styling-test"
extensions = [{extensions}]
html_theme = "ulwazi"
{extra_config}
"""

INDEX_RST = """
Test page
=========

Content.
"""

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


def _check_structured_toc_css_order(name: str, soup: BeautifulSoup) -> list[str]:
    """Ulwazi's temporary styling must load after the extension's own CSS.

    Loading later (and at a higher CSS priority, see
    ulwazi/__init__.py:_setup_structured_toc_styling) means a project's own
    html_css_files still wins without needing "!important" anywhere.
    """
    hrefs = [
        cast(str, link.get("href", ""))
        for link in soup.find_all("link", attrs={"rel": "stylesheet"})
    ]
    domain_list = next(
        (i for i, href in enumerate(hrefs) if "domain-list.css" in href), None
    )
    structured_toc = next(
        (i for i, href in enumerate(hrefs) if "structured-toc.css" in href), None
    )
    if domain_list is None or structured_toc is None:
        return [f"[{name}] structured-toc.css or domain-list.css is not linked"]
    if structured_toc <= domain_list:
        return [f"[{name}] structured-toc.css must be linked after domain-list.css"]
    return []


def _check_no_color_override(name: str, soup: BeautifulSoup) -> list[str]:
    """The sample docs don't set the separator colour options, so no colour
    override <style> block should be injected (see layout.html)."""
    if soup.find(id="ulwazi-structured-toc-colors"):
        message = (
            f"[{name}] unexpected colour override <style> on a page that "
            "does not set either separator colour option"
        )
        return [message]
    return []


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
    errors.extend(_check_structured_toc_css_order(name, soup))
    errors.extend(_check_no_color_override(name, soup))
    return errors


def _structured_toc_stylesheet_errors() -> list[str]:
    """Check the scope and shape of Ulwazi's temporary structured-TOC CSS.

    Guards the design intent documented at the top of
    ulwazi/theme/ulwazi/static/css/structured-toc.css: every rule stays
    scoped to the extension's own "domain-list" class, and the separator
    rule only recolours the extension's own border (sets
    "border-left-color" and no other "border-left-*" longhand or shorthand),
    so it keeps composing instead of fighting a future upstream change.
    """
    if not STRUCTURED_TOC_CSS.exists():
        return [f"[css] {STRUCTURED_TOC_CSS} not found -- run 'make docs' first"]

    rules = tinycss2.parse_stylesheet(
        STRUCTURED_TOC_CSS.read_text(encoding="utf-8"),
        skip_comments=True,
        skip_whitespace=True,
    )
    errors: list[str] = []
    saw_visited_override = False
    saw_separator_rule = False
    for rule in rules:
        if rule.type != "qualified-rule":
            continue
        selector = tinycss2.serialize(rule.prelude).strip()
        if "domain-list" not in selector:
            errors.append(f"[css] selector {selector!r} is not scoped to .domain-list")
        declarations = tinycss2.parse_declaration_list(
            rule.content, skip_comments=True, skip_whitespace=True
        )
        prop_names = {
            cast(str, d.lower_name) for d in declarations if d.type == "declaration"
        }
        if "border-left-color" in prop_names:
            saw_separator_rule = True
            extra_border = prop_names & {
                "border-left",
                "border-left-style",
                "border-left-width",
            }
            if extra_border:
                errors.append(
                    f"[css] separator rule {selector!r} also sets {sorted(extra_border)}; "
                    "should only set border-left-color"
                )
        if "--vf-color-link-visited" in prop_names:
            saw_visited_override = True

    if not saw_separator_rule:
        errors.append("[css] no border-left-color separator rule found")
    if not saw_visited_override:
        errors.append("[css] no --vf-color-link-visited override found")
    return errors


def test_structured_toc_markup():
    """Verify the domain/slice markup and its ARIA wiring on the RST and
    MyST fixture pages, that the extension's CSS is linked, and that
    Ulwazi's temporary structured-TOC stylesheet is scoped and ordered
    correctly (see ulwazi/theme/ulwazi/static/css/structured-toc.css).
    """
    errors: list[str] = []
    for name, path in PAGES.items():
        errors.extend(_check_page(name, path))
    errors.extend(_structured_toc_stylesheet_errors())

    assert not errors, "structured-TOC checks failed:\n" + "\n".join(
        f"  - {error}" for error in errors
    )


def _build_styling_fixture(
    tmp_path: Path,
    label: str,
    extensions: list[str],
    extra_config: str = "",
) -> tuple[str, str]:
    """Build a minimal fixture and return (built index.html, build warnings)."""
    srcdir = tmp_path / label / "src"
    srcdir.mkdir(parents=True)
    (srcdir / "conf.py").write_text(
        CONF_TEMPLATE.format(
            extensions=", ".join(f'"{ext}"' for ext in extensions),
            extra_config=extra_config,
        ),
        encoding="utf-8",
    )
    (srcdir / "index.rst").write_text(INDEX_RST, encoding="utf-8")

    outdir = tmp_path / label / "out"
    warnings = io.StringIO()
    with patch_docutils(str(srcdir)), docutils_namespace():
        app = Sphinx(
            srcdir=str(srcdir),
            confdir=str(srcdir),
            outdir=str(outdir),
            doctreedir=str(tmp_path / label / "doctrees"),
            buildername="html",
            warning=warnings,
            status=io.StringIO(),
        )
        app.build()
    return (outdir / "index.html").read_text(encoding="utf-8"), warnings.getvalue()


def test_structured_toc_styling_config(tmp_path: Path) -> None:
    """Verify ulwazi_structured_toc_styling and the two separator-colour
    options across the scenarios that control whether and how Ulwazi's
    temporary structured-TOC stylesheet gets linked (see
    ulwazi/__init__.py:_setup_structured_toc_styling and
    _structured_toc_color_css).
    """
    errors: list[str] = []
    full_extensions = ["ulwazi", "sphinx_structured_toc"]

    def _record(label: str, check: Callable[[], None]) -> None:
        try:
            check()
        except Exception as exc:  # noqa: BLE001 (report, don't stop other cases)
            errors.append(f"[{label}] {exc}")

    html, _ = _build_styling_fixture(tmp_path, "default", full_extensions)

    def _check_default() -> None:
        assert "structured-toc.css" in html
        assert 'id="ulwazi-structured-toc-colors"' not in html

    _record("default", _check_default)

    opt_out_html, _ = _build_styling_fixture(
        tmp_path,
        "opt-out",
        full_extensions,
        "ulwazi_structured_toc_styling = False",
    )

    def _check_opt_out() -> None:
        assert "domain-list.css" in opt_out_html
        assert "structured-toc.css" not in opt_out_html

    _record("opt-out", _check_opt_out)

    colors_html, _ = _build_styling_fixture(
        tmp_path,
        "colors",
        full_extensions,
        'ulwazi_structured_toc_separator_color_light = "purple"\n'
        'ulwazi_structured_toc_separator_color_dark = "#123456"',
    )

    def _check_colors() -> None:
        assert "structured-toc.css" in colors_html
        assert "--ulwazi-structured-toc-separator-color-light: purple;" in colors_html
        assert "--ulwazi-structured-toc-separator-color-dark: #123456;" in colors_html

    _record("colour overrides", _check_colors)

    invalid_html, invalid_warnings = _build_styling_fixture(
        tmp_path,
        "invalid-color",
        full_extensions,
        # Attempts to break out of the injected <style> block.
        'ulwazi_structured_toc_separator_color_light = "red; } </style><script>"',
    )

    def _check_invalid_color() -> None:
        assert "structured-toc.css" in invalid_html
        # The malicious value must not have broken out of the <style> block.
        assert "red; } </style><script>" not in invalid_html
        assert 'id="ulwazi-structured-toc-colors"' not in invalid_html
        assert "ulwazi_structured_toc_separator_color_light" in invalid_warnings
        assert "invalid colour" in invalid_warnings

    _record("invalid colour", _check_invalid_color)

    no_extension_html, _ = _build_styling_fixture(tmp_path, "no-extension", ["ulwazi"])

    def _check_no_extension() -> None:
        assert "structured-toc.css" not in no_extension_html

    _record("extension not loaded", _check_no_extension)

    theme_only_html, _ = _build_styling_fixture(
        tmp_path, "theme-only", ["sphinx_structured_toc"]
    )

    def _check_theme_only() -> None:
        assert "structured-toc.css" in theme_only_html

    _record("theme selected only via html_theme", _check_theme_only)

    assert not errors, "structured-TOC styling config checks failed:\n" + "\n".join(
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


def _check_styling_markers_and_indent(name: str, page: Page) -> list[str]:
    """The outer slice list must have no bullets and no left indent (see
    "nav.domain-list > ul" in structured-toc.css)."""
    style = page.eval_on_selector(
        "nav.domain-list > ul",
        "el => { const s = getComputedStyle(el); "
        "return {listStyle: s.listStyleType, marginLeft: s.marginLeft, "
        "paddingLeft: s.paddingLeft}; }",
    )
    errors = []
    if style is None:
        return [f"[{name}] could not measure the outer slice list"]
    if style["listStyle"] != "none":
        errors.append(f"[{name}] outer slice list still shows bullets: {style}")
    if style["marginLeft"] != "0px" or style["paddingLeft"] != "0px":
        errors.append(f"[{name}] outer slice list is still indented: {style}")
    return errors


def _check_separator_color(name: str, page: Page, theme: str) -> list[str]:
    """The second slice item's separator must use the brand colour for the
    active theme, and the first item must have no separator at all (that
    reset stays the extension's responsibility, see structured-toc.css)."""
    colors = page.eval_on_selector_all(
        "nav.domain-list > ul > li > ul > li",
        "els => els.slice(0, 2).map(el => getComputedStyle(el).borderLeftColor)",
    )
    errors = []
    if len(colors) < 2:
        return [f"[{name}/{theme}] expected at least two slice items, got {colors}"]
    expected = DEFAULT_SEPARATOR_RGB[theme]
    if colors[1] != expected:
        errors.append(
            f"[{name}/{theme}] second item separator colour is {colors[1]!r}, "
            f"expected {expected!r}"
        )
    first_item_border = page.eval_on_selector(
        "nav.domain-list > ul > li > ul > li",
        "el => getComputedStyle(el).borderLeftStyle",
    )
    if first_item_border != "none":
        errors.append(
            f"[{name}/{theme}] first item unexpectedly has a separator "
            f"(border-left-style: {first_item_border!r})"
        )
    return errors


def _check_visited_link_colors(name: str, page: Page) -> list[str]:
    """Visited links must look the same as unvisited links inside a
    structured-TOC block, but keep the theme's distinct visited colour
    everywhere else on the page (regression guard for the scoping in
    structured-toc.css)."""
    inside = page.eval_on_selector(
        "nav.domain-list",
        "el => { const s = getComputedStyle(el); "
        "return [s.getPropertyValue('--vf-color-link-default'), "
        "s.getPropertyValue('--vf-color-link-visited')]; }",
    )
    outside = page.eval_on_selector(
        "body",
        "el => { const s = getComputedStyle(el); "
        "return [s.getPropertyValue('--vf-color-link-default'), "
        "s.getPropertyValue('--vf-color-link-visited')]; }",
    )
    errors = []
    if inside is None or inside[0] != inside[1]:
        errors.append(
            f"[{name}] visited links inside a structured-TOC block do not "
            f"match unvisited links: {inside}"
        )
    if outside is None or outside[0] == outside[1]:
        errors.append(
            f"[{name}] visited links outside structured-TOC blocks "
            f"unexpectedly lost their distinct colour: {outside}"
        )
    return errors


def _styling_browser_errors() -> list[str]:
    """Check the rendered appearance of Ulwazi's temporary structured-TOC
    styling (bullets/indent removal, separator colour per theme, and the
    visited-link colour override) in a real browser.

    Separate from _browser_errors()/test_structured_toc_slow, which check
    the extension's own rendering contract (inline flow, hidden domain
    span); this checks only Ulwazi's theme-level additions on top of it.
    Returns a list of human-readable failure messages; an empty list means
    every check passed.
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

                errors.extend(_check_styling_markers_and_indent(name, page))
                errors.extend(_check_separator_color(name, page, "light"))
                errors.extend(_check_visited_link_colors(name, page))

                # ulwazi-theme/static/js/theme-toggle.js: no saved
                # preference starts in light mode; toggling once enters
                # dark mode, toggling again returns to light.
                page.click(".theme-toggle")
                errors.extend(_check_separator_color(name, page, "dark"))
                page.click(".theme-toggle")
        finally:
            browser.close()
    return errors


@pytest.mark.slow
@pytest.mark.coverage_style
def test_structured_toc_styling_slow() -> None:
    """Run every slow check for Ulwazi's temporary structured-TOC styling
    and report the outcome once (see structured-toc.css and
    test_structured_toc_styling_config for the fast, non-browser checks).
    """
    errors = _styling_browser_errors()

    if errors:
        pytest.fail(
            "structured-TOC styling checks failed:\n"
            + "\n".join(f"  - {error}" for error in errors),
            pytrace=False,
        )
