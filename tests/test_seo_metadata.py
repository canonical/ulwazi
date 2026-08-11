"""Regression tests for page metadata and SEO tags.

Scope follows the Ulwazi testing strategy (see docs/content/testing-strategy.md
and PR #124): we only check that Ulwazi's own theme templates and its
`sphinxext-opengraph` integration produce the metadata they're expected to.
We do not re-test Sphinx or extension internals (e.g. whether the extension
correctly truncates descriptions) -- only that Ulwazi's build wires them up.
"""

from pathlib import Path
from typing import cast

from bs4 import BeautifulSoup

INDEX_PATH = Path("docs/_build/index.html")
CONTRIBUTE_PATH = Path("docs/_build/content/contribute/index.html")


def _load_head(path: Path) -> BeautifulSoup:
    assert path.exists(), f"{path} not found -- run 'make docs' first"
    with path.open(encoding="utf-8") as f:
        return BeautifulSoup(f, "lxml")


def test_title_has_site_suffix():
    """<title> must include the site title, not just the page heading."""
    soup = _load_head(CONTRIBUTE_PATH)
    title = soup.title
    assert title is not None, "Missing <title> element"
    assert " — " in title.text or "&#8212;" in str(title), (
        f"<title> is missing the site-name suffix: {title.text!r}"
    )
    assert "Ulwazi theme sample" in title.text


def test_meta_description_present():
    """Every page must have a <meta name="description"> tag."""
    for path in (INDEX_PATH, CONTRIBUTE_PATH):
        soup = _load_head(path)
        description = soup.find("meta", attrs={"name": "description"})
        assert description is not None, f"Missing meta description in {path}"
        assert description.get("content"), f"Empty meta description in {path}"


def test_canonical_link_present():
    """Every page must have a valid rel="canonical" link."""
    for path in (INDEX_PATH, CONTRIBUTE_PATH):
        soup = _load_head(path)
        canonical = soup.find("link", attrs={"rel": "canonical"})
        assert canonical is not None, f"Missing rel=canonical link in {path}"
        href = cast(str, canonical.get("href", ""))
        assert href.startswith("http"), f"Malformed canonical URL in {path}: {href}"


def test_favicon_link_present():
    """The favicon <link> tag must render on every page."""
    soup = _load_head(INDEX_PATH)
    favicon = soup.find("link", attrs={"rel": "shortcut icon"})
    assert favicon is not None, "Missing favicon <link> tag"
    assert favicon.get("href"), "Favicon <link> has no href"


def test_open_graph_tags_present():
    """Open Graph tags must use `property=`, not `name=` (per the OGP spec)."""
    required_properties = {
        "og:title",
        "og:type",
        "og:url",
        "og:site_name",
        "og:description",
        "og:image",
    }
    for path in (INDEX_PATH, CONTRIBUTE_PATH):
        soup = _load_head(path)
        found = {
            cast(str, tag["property"])
            for tag in soup.find_all("meta", attrs={"property": True})
        }
        missing = required_properties - found
        assert not missing, f"Missing Open Graph tags in {path}: {missing}"

        # Guard against the "name=og:title" regression: no og:* tag should
        # ever be rendered with a `name` attribute instead of `property`.
        wrong_attr = [
            tag
            for tag in soup.find_all("meta", attrs={"name": True})
            if cast(str, tag.get("name", "")).startswith("og:")
        ]
        assert not wrong_attr, (
            f"Open Graph tags rendered with name= instead of property= in "
            f"{path}: {wrong_attr}"
        )
