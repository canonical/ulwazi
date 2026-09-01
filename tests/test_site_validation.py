import os
from pathlib import Path
from typing import cast
from urllib.parse import urlparse

from bs4 import BeautifulSoup

INDEX_PATH = "docs/_build/index.html"


def test_index_has_no_broken_assets():
    assert Path(INDEX_PATH).exists(), "index.html not found in docs/_build"

    with Path(INDEX_PATH).open() as f:
        soup = BeautifulSoup(f, "lxml")

        for tag in soup.find_all(["link", "script", "img"]):
            attr = "href" if tag.name == "link" else "src"
            url = cast(str, tag.get(attr))

            if url and not url.startswith(("http", "data:", "#")):
                parsed_url = urlparse(url)
                clean_path = parsed_url.path
                asset_path = os.path.normpath(Path("docs/_build") / clean_path)
                assert Path(asset_path).exists(), f"Missing asset: {asset_path}"


def test_404_page_renders_with_theme():
    """The sphinx-notfound-page 404 page must exist, use the Ulwazi chrome,
    show the not-found copy, and reference a resolvable 404.svg asset.

    NOTE: sphinx-notfound-page absolutises links on the 404 page, so relative
    asset checks like test_index_has_no_broken_assets would false-positive
    here; the asset is checked directly against docs/_build/_static instead.
    """
    page = Path("docs/_build/404/index.html")
    assert page.exists(), "404/index.html not found in docs/_build -- run 'make docs' first"

    with page.open(encoding="utf-8") as f:
        soup = BeautifulSoup(f, "lxml")

    # Theme chrome (header/footer are rendered by Ulwazi's page.html)
    assert soup.find("header") or soup.select_one(".p-navigation"), "404 page is missing the Ulwazi header"
    assert soup.select_one(".l-footer") or soup.find("footer"), "404 page is missing the Ulwazi footer"

    # Not-found copy (default notfound_context)
    assert "Page not found" in soup.get_text(), "404 page is missing the 'Page not found' heading"

    # The penguin image must reference the theme's 404.svg and it must exist
    img = soup.find("img", alt="Penguin with a question mark")
    assert img is not None, "404 page is missing the penguin image"
    src = cast(str, img.get("src"))
    assert src.endswith("404.svg"), f"Unexpected 404 image source: {src}"
    assert Path("docs/_build/_static/404.svg").exists(), "Missing asset: docs/_build/_static/404.svg"


def test_404_page_excluded_from_sitemap():
    """The generated 404 page must not appear in the sitemap."""
    sitemap = Path("docs/_build/sitemap.xml")
    assert sitemap.exists(), "sitemap.xml not found in docs/_build -- run 'make docs' first"

    content = sitemap.read_text(encoding="utf-8")
    assert "/404/" not in content, "The 404 page must be excluded from the sitemap"
