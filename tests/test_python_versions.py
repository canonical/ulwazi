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
   extensions such as ``sphinx_terminal`` that are not runtime
   dependencies of the theme package itself).
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
import shutil
import subprocess
import sys
import venv
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Single source of truth for the supported Python version range.
#
# This list MUST stay in sync with:
#   - ``requires-python`` in ``pyproject.toml`` (currently ``>=3.10``)
#   - the ``matrix.python-version`` list in
#     ``.github/workflows/test-python-versions.yaml``
# ---------------------------------------------------------------------------
SUPPORTED_PYTHON_VERSIONS: tuple[str, ...] = (
    "3.10",
    "3.11",
    "3.12",
    "3.13",
    "3.14",
)

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


# A minimal MyST fixture exercising the three restored defaults:
# substitution ({{ product }}), deflist (term/definition), and linkify
# (bare URL). No myst_enable_extensions assignment: the defaults must apply.
RUNTIME_CONF = """\
project = "runtime-install"
extensions = ["ulwazi", "myst_parser"]
html_theme = "ulwazi"
myst_substitutions = {"product": "Ulwazi"}
"""

RUNTIME_INDEX_MD = """\
# MyST defaults

Replacement: {{ product }}.

Example term
: A specific definition.

Bare URL: https://example.com/myst-defaults
"""

RUNTIME_INDEX_RST = """\
Test page
=========

Content.
"""


@pytest.mark.slow
def test_myst_runtime_installation(tmp_path: Path) -> None:
    """A normal Ulwazi install supplies the MyST linkify dependency.

    Installs the *packaged* theme (not the editable checkout) into a fresh
    venv with only its runtime dependencies, then adds plain
    ``myst-parser~=4.0`` (no ``linkify`` extra, no manual linkify install).
    This proves the dependency chain that Sphinx Stack relies on: existing
    Stack requirements need no changes to recover the former MyST defaults.
    """
    # Stage packaging inputs outside the checkout so setuptools-scm cannot
    # write into the source tree and the build is reproducible.
    stage = tmp_path / "stage"
    stage.mkdir()
    for name in (
        "pyproject.toml",
        "README.md",
        "LICENSE",
        "MANIFEST.in",
    ):
        shutil.copy2(REPO_ROOT / name, stage / name)
    shutil.copytree(
        REPO_ROOT / "ulwazi",
        stage / "ulwazi",
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__"),
    )

    venv_dir = tmp_path / "venv"
    venv.create(venv_dir, with_pip=True)

    # A clean child environment: no PYTHON* or VIRTUAL_ENV leakage, no
    # coverage/pytest plugins, and a pretend version so the staged copy
    # builds without git metadata.
    child_env = {
        "PATH": f"{venv_dir / 'bin'}:{os.environ.get('PATH', '')}",
        "SETUPTOOLS_SCM_PRETEND_VERSION_FOR_ULWAZI": "0.0.0",
    }

    def vrun(cmd: list[str], label: str) -> subprocess.CompletedProcess[str]:
        """Run a command in the fresh venv with bounded output."""
        result = subprocess.run(
            cmd,
            cwd=str(tmp_path),
            env=child_env,
            capture_output=True,
            text=True,
            check=False,
            timeout=600,
        )
        if result.returncode != 0:
            tail = 30
            stdout_tail = "\n".join(result.stdout.splitlines()[-tail:])
            stderr_tail = "\n".join(result.stderr.splitlines()[-tail:])
            pytest.fail(
                f"{label} failed (exit {result.returncode}).\n"
                f"Command: {' '.join(cmd)}\n"
                f"--- stdout (tail) ---\n{stdout_tail}\n"
                f"--- stderr (tail) ---\n{stderr_tail}",
                pytrace=False,
            )
        return result

    # 1. Install the staged package non-editably with only runtime deps.
    vrun(
        [str(venv_dir / "bin" / "pip"), "install", "--no-input", str(stage)],
        "pip install staged ulwazi",
    )

    # 2. MyST is absent: a reST-only build works and activates nothing.
    src_rst = tmp_path / "rst-site"
    src_rst.mkdir()
    (src_rst / "conf.py").write_text(
        'project = "rst"\nextensions = ["ulwazi"]\nhtml_theme = "ulwazi"\n',
        encoding="utf-8",
    )
    (src_rst / "index.rst").write_text(RUNTIME_INDEX_RST, encoding="utf-8")
    vrun(
        [
            str(venv_dir / "bin" / "python"),
            "-I",
            "-m",
            "sphinx",
            "-b",
            "html",
            "--fail-on-warning",
            "-c",
            str(src_rst),
            str(src_rst),
            str(tmp_path / "rst-out"),
        ],
        "reST-only sphinx build",
    )
    assert (tmp_path / "rst-out" / "index.html").is_file()
    vrun(
        [
            str(venv_dir / "bin" / "python"),
            "-I",
            "-c",
            (
                "import sys; sys.exit(0 if sys.modules.get('myst_parser') is None "
                "and not __import__('importlib.util', fromlist=['x']).find_spec("
                "'myst_parser') else 1)"
            ),
        ],
        "myst_parser absent check",
    )

    # 3. The installed distribution declares the constrained linkify dep.
    metadata = vrun(
        [
            str(venv_dir / "bin" / "python"),
            "-I",
            "-c",
            (
                "from importlib.metadata import requires; print('\\n'.join("
                "r for r in requires('ulwazi') if 'linkify' in r))"
            ),
        ],
        "ulwazi Requires-Dist check",
    )
    assert "linkify-it-py~=2.0" in metadata.stdout, (
        f"Installed ulwazi does not declare linkify-it-py~=2.0: {metadata.stdout!r}"
    )

    # 4. Install plain myst-parser~=4.0: no extra, no manual linkify.
    vrun(
        [
            str(venv_dir / "bin" / "pip"),
            "install",
            "--no-input",
            "myst-parser~=4.0",
        ],
        "pip install myst-parser~=4.0",
    )

    # 5. Build the MyST fixture: all three defaults must render.
    src_md = tmp_path / "md-site"
    src_md.mkdir()
    (src_md / "conf.py").write_text(RUNTIME_CONF, encoding="utf-8")
    (src_md / "index.md").write_text(RUNTIME_INDEX_MD, encoding="utf-8")
    vrun(
        [
            str(venv_dir / "bin" / "python"),
            "-I",
            "-m",
            "sphinx",
            "-b",
            "html",
            "--fail-on-warning",
            "-c",
            str(src_md),
            str(src_md),
            str(tmp_path / "md-out"),
        ],
        "MyST sphinx build",
    )
    page_path = tmp_path / "md-out" / "index.html"
    assert page_path.is_file(), "MyST build produced no index.html"
    soup = BeautifulSoup(page_path.read_text(encoding="utf-8"), "html.parser")
    article = soup.select_one("main#content")
    assert article is not None, "Built page has no main#content article"
    text = article.get_text(" ", strip=True)
    assert "Replacement: Ulwazi." in text, "substitution default not applied"
    assert "{{ product }}" not in text, "literal substitution token remains"
    assert article.select_one("dl dt") is not None, "deflist default not applied"
    assert article.select_one("dl dd") is not None, "deflist definition missing"
    anchor = article.select_one('a[href="https://example.com/myst-defaults"]')
    assert anchor is not None, "linkify default not applied"
    assert anchor.get_text(strip=True) == "https://example.com/myst-defaults", (
        "linkify anchor text does not match the URL"
    )

    # 6. Record the resolved versions for the final report.
    versions = vrun(
        [
            str(venv_dir / "bin" / "python"),
            "-I",
            "-c",
            (
                "from importlib.metadata import version; "
                "print(version('ulwazi'), version('sphinx'), "
                "version('myst-parser'), version('linkify-it-py'))"
            ),
        ],
        "version report",
    )
    print(f"resolved versions: {versions.stdout.strip()}")
    print(f"python: {sys.version.split()[0]}")
