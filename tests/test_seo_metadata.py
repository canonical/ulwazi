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

from bs4 import BeautifulSoup

PAGES = {
    "index": Path("docs/_build/index.html"),
    "contribute": Path("docs/_build/content/contribute/index.html"),
}

REQUIRED_OG_PROPERTIES = {
    "og:title",
    "og:type",
    "og:url",
    "og:site_name",
    "og:description",
    "og:image",
}


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

    # <title> must include the site-name suffix, not just the page heading.
    title = soup.title
    if title is None:
        errors.append(f"[{name}] missing <title> element")
    elif " — " not in title.text and "&#8212;" not in str(title):
        errors.append(
            f"[{name}] <title> is missing the site-name suffix: {title.text!r}"
        )

    # <meta name="description"> must be present and non-empty.
    description = soup.find("meta", attrs={"name": "description"})
    if description is None or not description.get("content"):
        errors.append(f'[{name}] missing or empty <meta name="description">')

    # rel="canonical" link must be present and absolute.
    canonical = soup.find("link", attrs={"rel": "canonical"})
    if canonical is None:
        errors.append(f'[{name}] missing rel="canonical" link')
    else:
        href = cast(str, canonical.get("href", ""))
        if not href.startswith("http"):
            errors.append(f"[{name}] malformed canonical URL: {href!r}")

    # Favicon link must be present.
    favicon = soup.find("link", attrs={"rel": "shortcut icon"})
    if favicon is None or not favicon.get("href"):
        errors.append(f"[{name}] missing favicon <link> tag")

    # All expected Open Graph tags must be present.
    found_properties = {
        cast(str, tag["property"])
        for tag in soup.find_all("meta", attrs={"property": True})
    }
    missing = REQUIRED_OG_PROPERTIES - found_properties
    if missing:
        errors.append(f"[{name}] missing Open Graph tags: {sorted(missing)}")

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
