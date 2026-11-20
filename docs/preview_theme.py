"""Prepare changed theme assets before sphinx-autobuild renders the local preview."""

import hashlib
from collections.abc import Iterable
from pathlib import Path

DOCS = Path(__file__).resolve().parent
ROOT = DOCS.parent
THEME = ROOT / "ulwazi"
STATE = DOCS / "_build/.preview-theme-digest"

# Slopstrap experiment branch: the Vanilla SCSS pipeline (``make
# vanilla-main``) is dormant. The theme ships the vendored ``slopstrap.css``
# plus the hand-written ``slop-bridge.css`` directly from ``static/``, so
# there is no compile step to run here. The digest invalidation below is
# kept: a theme change still invalidates rendered HTML so sphinx-autobuild
# copies fresh static files even when no page content changed.


def _sources() -> list[Path]:
    """Hash all theme inputs, including images/fonts, but not generated outputs."""
    return sorted(
        path
        for path in THEME.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
    )


def _digest(paths: Iterable[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def prepare() -> None:
    """Invalidate theme-dependent HTML output when any theme file changes.

    Autobuild does not copy static files if Sphinx has no outdated pages.
    A theme change invalidates the rendered HTML but not the doctrees, so
    every built ``index.html`` is deleted to force a fresh copy.
    """
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
