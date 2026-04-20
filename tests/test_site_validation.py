import os
from urllib.parse import urlparse

from bs4 import BeautifulSoup

INDEX_PATH = "docs/_build/index.html"


def test_index_has_no_broken_assets():
    assert os.path.exists(INDEX_PATH), "index.html not found in docs/_build"

    with open(INDEX_PATH, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "lxml")

        for tag in soup.find_all(["link", "script", "img"]):
            attr = "href" if tag.name == "link" else "src"
            url = tag.get(attr)

            if url and not url.startswith(("http", "data:", "#")):
                parsed_url = urlparse(url)
                clean_path = parsed_url.path
                asset_path = os.path.normpath(os.path.join("docs/_build", clean_path))
                assert os.path.exists(asset_path), f"Missing asset: {asset_path}"
