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
``docs/default-conf.py``. It also covers the deprecated ``github_version``
and ``github_folder`` aliases inherited from the old canonical-sphinx theme:
if a migrating project still sets them, their values must still be honoured
(with a deprecation warning), rather than silently ignored.

Both tests build their fixture through Sphinx's Python API, so coverage.py
can attribute the run to the ``setup``/``config_inited`` functions in
``ulwazi/__init__.py``. They can't reuse the sample docs in
``docs/content``, because ``docs/conf.py`` always sets these values
explicitly.
"""

import io
from pathlib import Path

from sphinx.application import Sphinx

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "feedback-no-repo-vars"
DEPRECATED_ALIASES_FIXTURE_DIR = (
    Path(__file__).parent / "fixtures" / "deprecated-github-aliases"
)


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


def test_deprecated_github_aliases_are_honoured_with_a_warning(tmp_path: Path) -> None:
    """A conf.py using the deprecated github_version/github_folder aliases
    must have their values applied to repo_branch/repo_folder, and must emit
    a deprecation warning for each alias used."""
    warning_stream = io.StringIO()
    app = Sphinx(
        srcdir=str(DEPRECATED_ALIASES_FIXTURE_DIR),
        confdir=str(DEPRECATED_ALIASES_FIXTURE_DIR),
        outdir=str(tmp_path / "_build"),
        doctreedir=str(tmp_path / "_doctrees"),
        buildername="html",
        status=io.StringIO(),
        warning=warning_stream,
    )
    app.build()

    html = (tmp_path / "_build" / "index.html").read_text()
    assert (
        'href="https://github.com/canonical/example/edit/stable/2.0documentationindex.rst"'
        in html
    )

    warnings = warning_stream.getvalue()
    assert "'github_version' is deprecated" in warnings
    assert "'github_folder' is deprecated" in warnings
