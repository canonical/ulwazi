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

"""Python version compatibility tests.

This module implements the "Python version and environment compatibility" test
category (category #7) from the testing strategy
(see ``docs/content/tests/python-versions.md`` and PR #124).

For every supported Python version it verifies that:

1. The theme can be installed into a *fresh* virtual environment (the
   ``docs`` dependency group is required, because ``docs/conf.py`` imports
   extensions such as ``sphinx_terminal`` and ``canonical_sphinx_config`` that
   are not runtime dependencies of the theme package itself).
2. The sample documentation builds with ``--fail-on-warning`` using that
   environment.
3. The Ulwazi theme is actually applied to the output (not just that Sphinx
   ran successfully).

Each version runs in a throwaway venv under ``tmp_path`` so the developer's
``.venv`` is never touched and the source tree stays clean. The test is marked
``slow`` and is therefore excluded from ``make test`` / ``make test-fast``; run
it via ``make test-python-versions`` (which parallelises the versions with
pytest-xdist) or directly with
``uv run pytest -m slow tests/test_python_versions.py``.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Single source of truth for the supported Python version range.
#
# This list MUST stay in sync with:
#   - ``requires-python`` in ``pyproject.toml`` (currently ``>=3.10``)
#   - the ``matrix.python-version`` list in
#     ``.github/workflows/test-python-versions.yaml``
# ---------------------------------------------------------------------------
SUPPORTED_PYTHON_VERSIONS: tuple[str, ...] = ("3.10", "3.11", "3.12", "3.13")

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs"


def _run(
    cmd: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    label: str,
) -> subprocess.CompletedProcess[str]:
    """Run a command and fail the test with a readable message on error.

    We deliberately avoid ``check=True`` so that, on failure, we can surface
    the command, the return code, and the tail of stdout/stderr in the
    ``pytest.fail`` message. Raw ``CalledProcessError`` traces are hard to
    read in CI logs, especially when the failure is deep inside a subprocess
    invoked from a parametrized test.
    """
    result = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        tail = 60
        stdout_tail = "\n".join(result.stdout.splitlines()[-tail:])
        stderr_tail = "\n".join(result.stderr.splitlines()[-tail:])
        pytest.fail(
            f"{label} failed (exit {result.returncode}).\n"
            f"Command: {' '.join(cmd)}\n"
            f"cwd: {cwd}\n"
            f"--- stdout (tail) ---\n{stdout_tail}\n"
            f"--- stderr (tail) ---\n{stderr_tail}",
            pytrace=False,
        )
    return result


@pytest.mark.slow
@pytest.mark.parametrize("python_version", SUPPORTED_PYTHON_VERSIONS)
def test_theme_builds_on_supported_python(python_version: str, tmp_path: Path) -> None:
    """Build the theme and sample docs on a supported Python version.

    Steps:
      1. Ensure the interpreter is available (``uv python install`` downloads
         it on demand; there is no ``.python-version`` file pinning anything).
      2. Create a throwaway venv via ``UV_PROJECT_ENVIRONMENT`` and install the
         theme plus the ``docs`` dependency group with ``uv sync --frozen``.
         ``--frozen`` uses the committed ``uv.lock`` so the test is
         deterministic and matches what users actually get.
      3. Build the sample docs with ``--fail-on-warning`` using the venv's
         Python. The build runs with ``cwd=docs`` because ``conf.py`` resolves
         ``./reuse/substitutions.yaml`` relative to the current working
         directory; building from the repo root would silently drop MyST
         substitutions and then fail on ``--fail-on-warning``.
      4. Assert the output ``index.html`` exists and references the Ulwazi
         stylesheet, proving the theme was applied rather than a bare Sphinx
         build succeeding.
    """
    venv_dir = tmp_path / "venv"
    build_dir = tmp_path / "build"
    doctree_dir = tmp_path / "doctrees"

    # ``UV_PROJECT_ENVIRONMENT`` tells uv to use this path as the project venv
    # instead of the default ``.venv``. We also drop ``VIRTUAL_ENV`` so the
    # currently-active developer venv cannot leak into the resolution.
    env = {**os.environ, "UV_PROJECT_ENVIRONMENT": str(venv_dir)}
    env.pop("VIRTUAL_ENV", None)

    # 1. Provision the interpreter.
    _run(
        ["uv", "python", "install", python_version],
        cwd=REPO_ROOT,
        env=env,
        label=f"uv python install {python_version}",
    )

    # 2. Install the theme + docs group into the throwaway venv.
    _run(
        [
            "uv",
            "sync",
            "--frozen",
            "--no-dev",
            "--group",
            "docs",
            "--python",
            python_version,
        ],
        cwd=REPO_ROOT,
        env=env,
        label=f"uv sync (docs group) for Python {python_version}",
    )

    # 3. Build the sample docs with the venv's Python.
    sphinx_cmd = [
        str(venv_dir / "bin" / "python"),
        "-m",
        "sphinx",
        "-b",
        "dirhtml",
        "--fail-on-warning",
        "--keep-going",
        "-c",
        ".",  # conf.py lives in docs/
        "-d",
        str(doctree_dir),
        ".",  # source dir = docs/ (cwd)
        str(build_dir),
    ]
    _run(
        sphinx_cmd,
        cwd=DOCS_DIR,
        env=env,
        label=f"sphinx-build for Python {python_version}",
    )

    # 4. Verify the Ulwazi theme was actually applied.
    index_html = build_dir / "index.html"
    assert index_html.exists(), (
        f"Build produced no index.html at {index_html} for Python {python_version}"
    )
    content = index_html.read_text(encoding="utf-8")
    assert "vanilla-main.css" in content, (
        f"Built index.html for Python {python_version} does not reference "
        f"vanilla-main.css; the Ulwazi theme was not applied."
    )
