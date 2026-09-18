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

"""Regression tests for the feedback section's html_context defaults.

Covers the "build works from a clean environment" requirement from the
"Build process tests" category in the testing strategy (see
docs/content/testing-strategy.md): a project that enables the feedback
button (``feedback`` and ``github_url``) without also setting
``repo_branch``, ``repo_folder``, or ``default_source_extension`` must still
build successfully, using the same defaults the theme documents in
``docs/default-conf.py``.

Builds ``tests/fixtures/feedback-no-repo-vars`` through Sphinx's Python API,
so coverage.py can attribute the run to the ``setup`` function in
``ulwazi/__init__.py``. It can't reuse the sample docs in ``docs/content``,
because ``docs/conf.py`` always sets these values explicitly.
"""

import io
from pathlib import Path

from sphinx.application import Sphinx

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "feedback-no-repo-vars"


def test_builds_with_feedback_enabled_and_no_repo_vars_set(tmp_path: Path) -> None:
    """A conf.py that enables feedback and github_url without also setting
    repo_branch, repo_folder, or default_source_extension must still build,
    falling back to the theme's documented defaults."""
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
    assert 'href="https://github.com/canonical/example/edit/maindocsindex.rst"' in html
