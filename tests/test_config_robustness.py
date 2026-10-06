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
H4 but not H5 in its local TOC (the same depth 3 as the sample docs). Projects
that explicitly set ``-1`` or ``None`` have no depth limit.

The single test builds ``tests/fixtures/minimal-conf`` (a two-line conf.py)
through Sphinx's Python API for omitted, ``None`` and ``-1`` depth settings.
It also checks the already-built sample docs, whose ``docs/conf.py`` sets
``localtoc_max_depth = 3``. Each case reports its own failure details without
adding another pytest result line.
"""

import io
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from sphinx.application import Sphinx

pytestmark = pytest.mark.usefixtures("isolated_sphinx_build")

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "minimal-conf"
CHEAT_SHEET_PATH = Path("docs/_build/content/rst-cheat-sheet/index.html")


def _local_toc_text(html: str) -> str:
    """Return the text of the local "On this page" TOC only, since heading
    text also legitimately appears in the article body."""
    soup = BeautifulSoup(html, "html.parser")
    nav = soup.find("nav", class_="p-table-of-contents__nav")
    assert nav is not None, "local TOC nav not found in rendered page"
    return nav.get_text()


def test_localtoc_depth(tmp_path: Path) -> None:
    """Check each depth setting and the sample docs in one grouped result."""
    errors: list[str] = []
    cases: list[tuple[str, dict[str, int | None], bool]] = [
        ("unset", {}, False),
        ("None", {"localtoc_max_depth": None}, True),
        ("-1", {"localtoc_max_depth": -1}, True),
    ]

    for label, overrides, includes_h5 in cases:
        output = tmp_path / label
        warnings = io.StringIO()
        try:
            app = Sphinx(
                srcdir=str(FIXTURE_DIR),
                confdir=str(FIXTURE_DIR),
                outdir=str(output / "_build"),
                doctreedir=str(output / "_doctrees"),
                buildername="html",
                confoverrides=overrides,
                status=io.StringIO(),
                warning=warnings,
            )
            app.build()
            assert app.statuscode == 0, f"Sphinx exited with status {app.statuscode}"
            toc_text = _local_toc_text((output / "_build" / "index.html").read_text())
        except Exception as exc:  # noqa: BLE001 (report all fixture build failures)
            errors.append(f"[{label}] build or local TOC failed: {exc}")
            continue

        if "H4 heading" not in toc_text:
            errors.append(f"[{label}] H4 heading missing from local TOC")
        if ("H5 heading" in toc_text) != includes_h5:
            expectation = "present" if includes_h5 else "absent"
            errors.append(f"[{label}] expected H5 heading {expectation} in local TOC")
        if "localtoc_max_depth" in warnings.getvalue():
            errors.append(f"[{label}] Sphinx warned about localtoc_max_depth")

    if not CHEAT_SHEET_PATH.exists():
        errors.append(f"[sample docs] {CHEAT_SHEET_PATH} not found; run 'make docs'")
    else:
        try:
            toc_text = _local_toc_text(CHEAT_SHEET_PATH.read_text())
            if "H4 heading" not in toc_text:
                errors.append("[sample docs] H4 heading missing from local TOC")
            if "H5 heading" in toc_text:
                errors.append("[sample docs] H5 heading should not appear in local TOC")
        except AssertionError as exc:
            errors.append(f"[sample docs] {exc}")

    assert not errors, "local TOC depth checks failed:\n- " + "\n- ".join(errors)
