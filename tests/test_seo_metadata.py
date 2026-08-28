"""Regression tests for page metadata and SEO tags.

Scope follows the Ulwazi testing strategy (see docs/content/testing-strategy.md
and PR #124): we only check that Ulwazi's own theme templates and its
`sphinxext-opengraph` integration produce the metadata they're expected to.
We do not re-test Sphinx or extension internals (e.g. whether the extension
correctly truncates descriptions) -- only that Ulwazi's build wires them up.

All checks are grouped into a single test so CI output stays a single line
when everything passes. On failure, every individual problem found (across
all checked pages) is listed in the assertion message.
"""

from pathlib import Path
from typing import cast
from urllib.parse import urlparse

from bs4 import BeautifulSoup

PAGES = {
    "index": Path("docs/_build/index.html"),
    "contribute": Path("docs/_build/content/contribute/index.html"),
    "testing_metadata": Path("docs/_build/content/tests/seo-metadata/index.html"),
}

REQUIRED_OG_PROPERTIES = {
    "og:title",
    "og:type",
    "og:url",
    "og:site_name",
    "og:description",
    "og:image",
}

# Manual overrides set in the front matter of tests/seo-metadata.md, used to
# verify that per-page overrides actually take effect (not just that some
# metadata is present). Keep these in sync with that file.
OVERRIDE_PAGE = "testing_metadata"
OVERRIDES = {
    "og:title": "Testing metadata and SEO overrides",
    "og:description": (
        "Custom Open Graph description set on this page to test the override mechanism."
    ),
    "description": (
        "Custom meta description set on this page to test the SEO override mechanism."
    ),
}


def _check_title(name: str, soup: BeautifulSoup) -> list[str]:
    """<title> must include the site-name suffix, not just the page heading."""
    title = soup.title
    if title is None:
        return [f"[{name}] missing <title> element"]
    if " — " not in title.text and "&#8212;" not in str(title):
        return [f"[{name}] <title> is missing the site-name suffix: {title.text!r}"]
    return []


def _check_description(name: str, soup: BeautifulSoup) -> list[str]:
    """<meta name="description"> must be present, non-empty, and match any
    override set for this page."""
    description = soup.find("meta", attrs={"name": "description"})
    if description is None or not description.get("content"):
        return [f'[{name}] missing or empty <meta name="description">']

    if name == OVERRIDE_PAGE:
        content = cast(str, description.get("content", ""))
        if content != OVERRIDES["description"]:
            return [f"[{name}] description override did not take effect: {content!r}"]
    return []


def _check_canonical(name: str, soup: BeautifulSoup) -> list[str]:
    """rel="canonical" link must be present and an absolute http(s) URL."""
    canonical = soup.find("link", attrs={"rel": "canonical"})
    if canonical is None:
        return [f'[{name}] missing rel="canonical" link']

    href = cast(str, canonical.get("href", ""))
    # urlparse distinguishes the scheme from the rest
    parsed = urlparse(href)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return [f"[{name}] malformed canonical URL: {href!r}"]
    return []


def _check_favicon(name: str, soup: BeautifulSoup) -> list[str]:
    """The favicon <link> tag must be present."""
    favicon = soup.find("link", attrs={"rel": "shortcut icon"})
    if favicon is None or not favicon.get("href"):
        return [f"[{name}] missing favicon <link> tag"]
    return []


def _check_open_graph(name: str, soup: BeautifulSoup) -> list[str]:
    """All required Open Graph tags must be present with `property=` (never
    `name=`), and, on the fixture page, overrides must take effect."""
    errors: list[str] = []

    og_tags = {
        cast(str, tag["property"]): cast(str, tag.get("content", ""))
        for tag in soup.find_all("meta", attrs={"property": True})
    }
    missing = REQUIRED_OG_PROPERTIES - og_tags.keys()
    if missing:
        errors.append(f"[{name}] missing Open Graph tags: {sorted(missing)}")

    # On the dedicated fixture page, manual og:* overrides must take effect
    # -- i.e. their values must match what's set in that page's front matter,
    # not the auto-generated defaults.
    if name == OVERRIDE_PAGE:
        for og_property in ("og:title", "og:description"):
            expected = OVERRIDES[og_property]
            actual = og_tags.get(og_property)
            if actual != expected:
                errors.append(
                    f"[{name}] {og_property} override did not take effect: "
                    f"{actual!r} (expected {expected!r})"
                )

    # Guard against the "name=og:title" regression: no og:* tag should ever
    # be rendered with a `name` attribute instead of `property`.
    wrong_attr = [
        cast(str, tag.get("name"))
        for tag in soup.find_all("meta", attrs={"name": True})
        if cast(str, tag.get("name", "")).startswith("og:")
    ]
    if wrong_attr:
        errors.append(
            f"[{name}] Open Graph tags rendered with name= instead of "
            f"property=: {wrong_attr}"
        )

    return errors


def _check_page(name: str, path: Path) -> list[str]:
    """Run all metadata/SEO checks for one built page.

    Returns a list of human-readable failure messages; an empty list means
    every check passed for this page.
    """
    if not path.exists():
        return [f"[{name}] {path} not found -- run 'make docs' first"]

    with path.open(encoding="utf-8") as f:
        soup = BeautifulSoup(f, "lxml")

    errors: list[str] = []
    errors.extend(_check_title(name, soup))
    errors.extend(_check_description(name, soup))
    errors.extend(_check_canonical(name, soup))
    errors.extend(_check_favicon(name, soup))
    errors.extend(_check_open_graph(name, soup))
    return errors


def test_seo_metadata():
    """Verify title, description, canonical link, favicon, and Open Graph
    tags are all present and correctly formed on every checked page.
    """
    errors: list[str] = []
    for name, path in PAGES.items():
        errors.extend(_check_page(name, path))

    assert not errors, "SEO/metadata checks failed:\n" + "\n".join(
        f"  - {error}" for error in errors
    )
