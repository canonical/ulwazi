"""Extension compatibility tests.

Verifies that the Ulwazi theme works with every extension that the
Sphinx Stack enables by default (see
https://documentation.ubuntu.com/sphinx-stack/latest/reference/default-extensions/
and docs/content/tests/extension-compatibility.md).

All extensions are enabled simultaneously in docs/conf.py, and the sample
sections on docs/content/tests/extension-compatibility.md exercise each
of them. These tests parse the built HTML and build artifacts -- no
browser needed.

Each extension gets its own parametrized test case, so the pytest output
shows one line per extension.

Known gaps (documented in docs/content/tests/extension-compatibility.md):
sphinx_contributor_listing and sphinx_related_links expose context
functions that no Ulwazi template consumes yet. They are enabled and
built with, but their rendered output is not asserted.
"""

from pathlib import Path

import pytest
from bs4 import BeautifulSoup

BUILD_DIR = Path("docs/_build")
EXTENSIONS_PAGE = (
    BUILD_DIR / "content" / "tests" / "extension-compatibility" / "index.html"
)
INDEX_PAGE = BUILD_DIR / "index.html"


def _load(path: Path) -> BeautifulSoup:
    """Load a built HTML page, failing with a helpful message if missing."""
    assert path.exists(), f"{path} not found -- run 'make docs' first"
    with path.open(encoding="utf-8") as f:
        return BeautifulSoup(f, "lxml")


def _check_sphinx_design(soup: BeautifulSoup) -> None:
    """sphinx_design: cards, grid items, and badges render with sd-* classes."""
    assert soup.select(".sd-card"), "No sphinx_design cards (.sd-card) found"
    assert soup.select(".sd-row"), "No sphinx_design grid (.sd-row) found"
    assert soup.select(".sd-badge"), "No sphinx_design badge (.sd-badge) found"


def _check_sphinx_tabs(soup: BeautifulSoup) -> None:
    """sphinx_tabs: tab sets render."""
    assert soup.select(".sd-tab-set"), "No sphinx_tabs tab set (.sd-tab-set) found"


def _check_sphinx_terminal(soup: BeautifulSoup) -> None:
    """sphinx_terminal: terminal blocks render with input and output."""
    assert soup.select(".terminal"), "No sphinx_terminal block (.terminal) found"
    assert soup.select(".terminal-code"), (
        "No sphinx_terminal output (.terminal-code) found"
    )


def _check_sphinx_youtube_links(soup: BeautifulSoup) -> None:
    """sphinx_youtube_links: YouTube links render with the play icon."""
    assert soup.select(".youtube_link"), (
        "No sphinx_youtube_links link (.youtube_link) found"
    )


def _check_sphinx_config_options(soup: BeautifulSoup) -> None:
    """sphinx_config_options: config options render with their fields."""
    assert soup.select(".configoption"), (
        "No sphinx_config_options block (.configoption) found"
    )


def _check_sphinx_roles(soup: BeautifulSoup) -> None:
    """sphinx_roles: custom roles render their content."""
    text = soup.get_text()
    assert "PurposelyWrong" in text, "spellexception role content not found"
    assert "some literal text" in text, "literalref role content not found"


def _check_sphinx_ubuntu_images(soup: BeautifulSoup) -> None:
    """sphinx_ubuntu_images: image download links render."""
    links = [
        a for a in soup.find_all("a") if "cdimage.ubuntu.com" in str(a.get("href", ""))
    ]
    assert links, "No sphinx_ubuntu_images download links found"


def _check_intersphinx(soup: BeautifulSoup) -> None:
    """sphinx.ext.intersphinx: external references resolve to real links."""
    links = [
        a for a in soup.find_all("a") if "docs.python.org" in str(a.get("href", ""))
    ]
    assert links, "No intersphinx-resolved link to docs.python.org found"


def _check_sphinxcontrib_jquery(soup: BeautifulSoup) -> None:
    """sphinxcontrib.jquery: jQuery is loaded on the page."""
    scripts = [s for s in soup.find_all("script") if "jquery" in str(s.get("src", ""))]
    assert scripts, "No jQuery script tag found"


def _check_sphinx_filtered_toctree(soup: BeautifulSoup) -> None:
    """sphinx_filtered_toctree: the filtered toctree renders its entries."""
    assert soup.select(".toctree-wrapper"), (
        "No filtered toctree (.toctree-wrapper) found on the extensions page"
    )


def _check_sphinx_structured_toc(soup: BeautifulSoup) -> None:
    """sphinx_structured_toc: domains render as nav elements with slices."""
    navs = soup.select("nav")
    assert navs, "No sphinx_structured_toc nav element found"
    # The domain nav must contain slice list items with links
    links = [a for a in navs[0].find_all("a") if a.get("href")]
    assert links, "No links inside the structured TOC nav found"


def _check_sphinxext_opengraph() -> None:
    """sphinxext.opengraph: Open Graph meta tags are generated."""
    soup = _load(INDEX_PAGE)
    og_tags = {
        str(tag.get("property"))
        for tag in soup.find_all("meta", attrs={"property": True})
    }
    required = {"og:title", "og:type", "og:url", "og:site_name", "og:description"}
    missing = required - og_tags
    assert not missing, f"Missing Open Graph tags: {sorted(missing)}"


def _check_notfound_extension() -> None:
    """notfound.extension: the 404 page is built with the Ulwazi theme."""
    page = BUILD_DIR / "404" / "index.html"
    assert page.exists(), "404 page not found in build output"
    content = page.read_text(encoding="utf-8")
    assert "vanilla-main.css" in content, (
        "404 page does not reference the Ulwazi stylesheet"
    )


def _check_sphinx_sitemap() -> None:
    """sphinx_sitemap: sitemap.xml is generated with page entries.

    Note: sphinx-sitemap only collects pages that are actually written
    during the current build, so an incremental rebuild produces a
    partial sitemap. We therefore assert the sitemap exists and contains
    entries, without requiring any specific page.
    """
    sitemap = BUILD_DIR / "sitemap.xml"
    assert sitemap.exists(), "sitemap.xml not found in build output"
    content = sitemap.read_text(encoding="utf-8")
    assert "<loc>" in content, "sitemap.xml contains no page entries"


def _check_sphinx_llm() -> None:
    """sphinx_llm.txt: llms.txt is generated in the build output."""
    assert (BUILD_DIR / "llms.txt").exists(), "llms.txt not found in build output"


def _check_sphinx_reredirects() -> None:
    """sphinx_reredirects: redirect stub page with meta refresh is generated."""
    stub = BUILD_DIR / "content" / "extensions-old" / "index.html"
    assert stub.exists(), (
        "sphinx_reredirects stub page (content/extensions-old) not found"
    )
    content = stub.read_text(encoding="utf-8")
    assert (
        "http-equiv" in content
        or "meta http-equiv" in content.lower()
        or ("refresh" in content.lower())
    ), "sphinx_reredirects stub page has no meta refresh"


def _check_sphinx_rerediraffe() -> None:
    """sphinx_rerediraffe: redirect stub page is generated from redirects.txt."""
    stub = BUILD_DIR / "content" / "extensions-moved" / "index.html"
    assert stub.exists(), (
        "sphinx_rerediraffe stub page (content/extensions-moved) not found"
    )


def _check_sphinx_last_updated_by_git(soup: BeautifulSoup) -> None:
    """sphinx_last_updated_by_git: build succeeds with the extension active.

    The extension populates the last_updated context from git metadata;
    there is no visible marker to assert on, so a rendered page is enough.
    """
    assert soup.title is not None, "Page did not render"


def _check_sphinx_contributor_listing(soup: BeautifulSoup) -> None:
    """sphinx_contributor_listing: enabled and built with (known gap).

    The extension exposes a get_contributors_for_file context function,
    but no Ulwazi template consumes it yet. We only assert the page
    renders; see docs/content/tests/extension-compatibility.md.
    """
    assert soup.title is not None, "Page did not render"


def _check_sphinx_related_links(soup: BeautifulSoup) -> None:
    """sphinx_related_links: enabled and built with (known gap).

    The extension exposes related-links context functions, but no Ulwazi
    template consumes them yet. We only assert the page renders; see
    docs/content/tests/extension-compatibility.md.
    """
    assert soup.title is not None, "Page did not render"


# Registry: extension name -> check function. Checks that only need the
# extensions page take a BeautifulSoup object; checks on other artifacts
# take no argument.
PAGE_CHECKS = {
    "sphinx_design": _check_sphinx_design,
    "sphinx_tabs.tabs": _check_sphinx_tabs,
    "sphinx_terminal": _check_sphinx_terminal,
    "sphinx_youtube_links": _check_sphinx_youtube_links,
    "sphinx_config_options": _check_sphinx_config_options,
    "sphinx_roles": _check_sphinx_roles,
    "sphinx_ubuntu_images": _check_sphinx_ubuntu_images,
    "sphinx.ext.intersphinx": _check_intersphinx,
    "sphinxcontrib.jquery": _check_sphinxcontrib_jquery,
    "sphinx_filtered_toctree": _check_sphinx_filtered_toctree,
    "sphinx_structured_toc": _check_sphinx_structured_toc,
    "sphinx_last_updated_by_git": _check_sphinx_last_updated_by_git,
    "sphinx_contributor_listing": _check_sphinx_contributor_listing,
    "sphinx_related_links": _check_sphinx_related_links,
}

ARTIFACT_CHECKS = {
    "sphinxext.opengraph": _check_sphinxext_opengraph,
    "notfound.extension": _check_notfound_extension,
    "sphinx_sitemap": _check_sphinx_sitemap,
    "sphinx_llm.txt": _check_sphinx_llm,
    "sphinx_reredirects": _check_sphinx_reredirects,
    "sphinx_rerediraffe": _check_sphinx_rerediraffe,
}


@pytest.mark.parametrize("extension", list(PAGE_CHECKS) + list(ARTIFACT_CHECKS))
def test_extension_compatibility(extension: str) -> None:
    """Verify the theme renders one Sphinx Stack default extension correctly."""
    if extension in PAGE_CHECKS:
        soup = _load(EXTENSIONS_PAGE)
        PAGE_CHECKS[extension](soup)
    else:
        ARTIFACT_CHECKS[extension]()


@pytest.mark.slow
def test_cairosvgconverter_pdf() -> None:
    """sphinxcontrib.cairosvgconverter: the PDF build succeeds.

    The extension converts SVG images during LaTeX builds; a successful
    PDF build with the sample content is the smoke test.
    """
    pdf = BUILD_DIR / "theulwazithemesample.pdf"
    assert pdf.exists(), (
        f"PDF not found at {pdf} -- run 'make test-slow' (includes PDF build)"
    )
