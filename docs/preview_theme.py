"""Prepare changed theme assets before sphinx-autobuild renders the preview."""

import hashlib
import subprocess
from collections.abc import Iterable
from pathlib import Path

DOCS = Path(__file__).resolve().parent
ROOT = DOCS.parent
THEME = ROOT / "ulwazi"
SCSS = THEME / "theme/ulwazi/assets"
CSS = THEME / "theme/ulwazi/static/css/vanilla-main.css"
STATE = DOCS / "_build/.preview-theme-digest"


def _sources() -> list[Path]:
    """Hash all theme inputs, including images/fonts, but not generated outputs."""
    return sorted(
        path
        for path in THEME.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
        and path.name not in {CSS.name, CSS.name + ".map"}
    )


def _digest(paths: Iterable[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def prepare() -> None:
    """Compile changed SCSS, then invalidate only theme-dependent HTML output."""
    scss = list(SCSS.rglob("*.scss"))
    if not CSS.is_file() or any(
        path.stat().st_mtime_ns > CSS.stat().st_mtime_ns for path in scss
    ):
        subprocess.run(["make", "vanilla-main"], cwd=ROOT, check=True)

    sources = _sources()
    current = _digest(sources)
    previous = STATE.read_text(encoding="ascii") if STATE.is_file() else None
    if previous != current:
        # Autobuild does not copy static files if Sphinx has no outdated pages.
        # A theme change invalidates the rendered HTML but not the doctrees.
        for page in (DOCS / "_build").rglob("index.html"):
            page.unlink()
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(current, encoding="ascii")


if __name__ == "__main__":
    prepare()
