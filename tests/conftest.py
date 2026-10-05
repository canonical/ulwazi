"""Fresh, shared Sphinx build for tests of Ulwazi's rendered HTML."""

import os
from io import StringIO
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from sphinx.application import Sphinx

DOCS = Path(__file__).resolve().parents[1] / "docs"


class BuiltSite:
    """Expose the temporary site and load its generated pages."""

    def __init__(self, output: Path):
        self.output = output

    def page(self, name: str) -> BeautifulSoup:
        """Read a dirhtml page, failing with its path if it is absent."""
        path = self.output / name / "index.html" if name else self.output / "index.html"
        if not path.is_file():
            pytest.fail(f"[{name or 'home'}] missing built page: {path}", pytrace=False)
        return BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")


def _build_site(
    output: Path, root: Path, status: StringIO, warnings: StringIO
) -> Sphinx:
    """Run Sphinx while conf.py's relative includes point at docs/."""
    previous = Path.cwd()
    try:
        os.chdir(DOCS)
        app = Sphinx(
            srcdir=DOCS,
            confdir=DOCS,
            outdir=output,
            doctreedir=root / "doctrees",
            buildername="dirhtml",
            status=status,
            warning=warnings,
            freshenv=True,
            warningiserror=True,
            keep_going=True,
            parallel=0,
        )
        app.build(force_all=True)
        return app
    finally:
        os.chdir(previous)


@pytest.fixture(scope="session")
def built_site(tmp_path_factory):
    """Build once per pytest session so Ulwazi's Sphinx hooks run under coverage."""
    root = tmp_path_factory.mktemp("ulwazi-site")
    output = root / "html"
    status, warnings = StringIO(), StringIO()
    try:
        app = _build_site(output, root, status, warnings)
    except (OSError, RuntimeError, ImportError) as exc:
        pytest.fail(
            f"Sphinx build failed in {output}: {exc}\n"
            f"Warnings:\n{warnings.getvalue()[-6000:]}\n"
            f"Status:\n{status.getvalue()[-3000:]}\n"
            "Install documentation dependencies with uv run --group docs pytest.",
            pytrace=False,
        )
    if app.statuscode:
        pytest.fail(
            f"Sphinx build failed (status {app.statuscode}) in {output}\n"
            f"Warnings:\n{warnings.getvalue()[-6000:]}\n"
            f"Status:\n{status.getvalue()[-3000:]}",
            pytrace=False,
        )
    return BuiltSite(output)
