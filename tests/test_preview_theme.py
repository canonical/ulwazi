"""Check preview preparation without editing real theme sources or starting a server."""

import importlib.util
from pathlib import Path
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "docs/preview_theme.py"
spec = importlib.util.spec_from_file_location("preview_theme", MODULE)
assert spec is not None
assert spec.loader is not None
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


def test_preview_theme_fast(tmp_path):
    """Theme edits refresh HTML; content edits do not; Sass runs first."""
    root = tmp_path / "project"
    theme = root / "ulwazi"
    scss = theme / "theme/ulwazi/assets"
    css = theme / "theme/ulwazi/static/css/vanilla-main.css"
    docs = root / "docs"
    state = docs / "_build/.preview-theme-digest"
    html = docs / "_build/index.html"
    scss.mkdir(parents=True)
    css.parent.mkdir(parents=True)
    html.parent.mkdir(parents=True)
    html.write_text("original", encoding="utf-8")
    source = scss / "main.scss"
    source.write_text("a{color:red}", encoding="utf-8")
    css.write_text("a{color:red}", encoding="utf-8")
    script = theme / "theme/ulwazi/static/js/theme.js"
    script.parent.mkdir(parents=True)
    script.write_text("// version one", encoding="utf-8")

    def compile_css(*_args, **_kwargs):
        css.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    with (
        patch.object(preview, "ROOT", root),
        patch.object(preview, "DOCS", docs),
        patch.object(preview, "THEME", theme),
        patch.object(preview, "SCSS", scss),
        patch.object(preview, "CSS", css),
        patch.object(preview, "STATE", state),
        patch.object(preview.subprocess, "run", side_effect=compile_css) as compile_run,
    ):
        preview.prepare()
        assert not html.exists()
        html.write_text("built", encoding="utf-8")
        assert state.is_file()
        assert compile_run.call_count == 0
        preview.prepare()
        assert html.read_text(encoding="utf-8") == "built"
        (docs / "index.md").write_text("content changed", encoding="utf-8")
        preview.prepare()
        assert html.read_text(encoding="utf-8") == "built"

        script.write_text("// version two", encoding="utf-8")
        preview.prepare()
        assert not html.exists()
        html.write_text("rebuilt", encoding="utf-8")

        logo = theme / "theme/ulwazi/static/images/logo.png"
        logo.parent.mkdir(parents=True)
        logo.write_bytes(b"new image")
        preview.prepare()
        assert not html.exists()
        html.write_text("rebuilt", encoding="utf-8")

        source.write_text("a{color:blue}", encoding="utf-8")
        preview.prepare()
        assert compile_run.call_count == 1
        assert css.read_text(encoding="utf-8") == source.read_text(encoding="utf-8")
        assert not html.exists()
