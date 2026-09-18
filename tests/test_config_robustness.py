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

"""Regression tests for local table-of-contents depth handling.

Covers the "TOC depth truncation" item from the "Feature and regression
tests" category in the testing strategy (see
docs/content/testing-strategy.md), and the "build works from a clean
environment" requirement from the "Build process tests" category: a project
that never sets ``localtoc_max_depth`` must still build successfully, with an
unbounded local TOC, while a project that sets it keeps the depth it asked
for.

``test_builds_without_localtoc_max_depth_set`` builds
``tests/fixtures/minimal-conf`` -- the smallest possible conf.py a new or
migrating user would write -- through Sphinx's Python API, so coverage.py can
attribute the run to ``truncate_local_toc``. It can't reuse the sample docs in
``docs/content``, because ``docs/conf.py`` always sets
``localtoc_max_depth`` explicitly and needs the ``docs`` dependency group,
which isn't installed for a plain ``pytest`` run (see ``docs-html`` in
``Makefile``/``docs/Makefile``).

``test_localtoc_max_depth_still_truncates_when_set`` instead reads the
already-built ``docs/content/rst-cheat-sheet.rst`` page from ``docs/_build``,
like the other tests in this suite, since that sample page already has the
heading levels needed and the real ``docs/conf.py`` already sets
``localtoc_max_depth = 3``.
"""

import io
from pathlib import Path

from bs4 import BeautifulSoup
from sphinx.application import Sphinx

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "minimal-conf"
CHEAT_SHEET_PATH = Path("docs/_build/content/rst-cheat-sheet/index.html")


def _local_toc_text(html: str) -> str:
    """Return the text of the local "On this page" TOC only, since heading
    text also legitimately appears in the article body."""
    soup = BeautifulSoup(html, "html.parser")
    nav = soup.find("nav", class_="p-table-of-contents__nav")
    assert nav is not None, "local TOC nav not found in rendered page"
    return nav.get_text()


def test_builds_without_localtoc_max_depth_set(tmp_path: Path) -> None:
    """A conf.py that never sets localtoc_max_depth must still build, with
    every heading level present in the local TOC (no depth limit applied)."""
    app = Sphinx(
        srcdir=str(FIXTURE_DIR),
        confdir=str(FIXTURE_DIR),
        outdir=str(tmp_path / "_build"),
        doctreedir=str(tmp_path / "_doctrees"),
        buildername="html",
        status=io.StringIO(),
        warning=io.StringIO(),
    )
    app.build()

    html = (tmp_path / "_build" / "index.html").read_text()
    assert "H5 heading" in _local_toc_text(html)


def test_localtoc_max_depth_still_truncates_when_set() -> None:
    """The sample docs set localtoc_max_depth = 3, so the local TOC must
    stop at H4; this proves the fix didn't disable truncation for projects
    that opt into it."""
    assert CHEAT_SHEET_PATH.exists(), f"{CHEAT_SHEET_PATH} not found; run 'make docs'"

    html = CHEAT_SHEET_PATH.read_text()
    toc_text = _local_toc_text(html)
    assert "H4 heading" in toc_text
    assert "H5 heading" not in toc_text
