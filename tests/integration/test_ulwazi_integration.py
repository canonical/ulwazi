# This file is part of Ulwazi.
#
# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3, as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranties of MERCHANTABILITY, SATISFACTORY
# QUALITY, or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
# License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

import shutil
import subprocess
from pathlib import Path
from typing import cast
from urllib.parse import urlparse

import bs4
import pytest


@pytest.fixture
def example_project(request) -> Path:
    project_root = request.config.rootpath
    example_dir = project_root / "tests/integration/example"

    target_dir = Path().resolve() / "example"
    shutil.copytree(example_dir, target_dir, dirs_exist_ok=True)

    return target_dir


@pytest.mark.slow
def test_hello_integration(example_project):
    build_dir = example_project / "_build"
    subprocess.check_call(
        ["sphinx-build", "-b", "html", "-W", example_project, build_dir],
    )

    index = build_dir / "index.html"

    # Rename the test output to something more meaningful
    shutil.copytree(
        build_dir, build_dir.parents[1] / ".test_output", dirs_exist_ok=True
    )
    soup = bs4.BeautifulSoup(index.read_text(), features="lxml")

    shutil.rmtree(example_project)  # Delete copied source

    for tag in soup.find_all(["link", "script", "img"]):
        attr = "href" if tag.name == "link" else "src"
        url = cast(str, tag.get(attr))

        if url and not url.startswith(("http", "data:", "#")):
            parsed_url = urlparse(url)
            clean_path = parsed_url.path
            asset_path = build_dir.parents[1] / ".test_output" / clean_path
            assert Path(asset_path).exists(), f"Missing asset: {asset_path}"

    # Test SCSS styles propagation
    target = soup.find("p", class_="heading-test-scss")
    assert target is not None, "Expected <p class='heading-test-scss'> not found"
    assert "This is a test about SCSS propagation." in target.text, (
        "Expected text not found inside <p class='heading-test-scss'>"
    )
