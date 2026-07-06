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
