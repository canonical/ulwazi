"""Tests for the bundled sphinx-notfound-page integration.

The theme activates ``sphinx-notfound-page`` automatically via
``app.setup_extension()`` from its ``setup()`` (idempotent, so projects that
also list ``notfound.extension`` in ``extensions`` are unaffected), and
provides an opt-out via the ``notfound_disabled`` config value.

These tests run minimal in-process Sphinx builds with four configurations,
covering every adoption path:

1. Ulwazi only -- the extension is auto-activated and the 404 page is
   generated with Ulwazi's template and prefix.
2. Ulwazi + the extension listed explicitly -- no double registration, the
   404 page is still generated with Ulwazi's overrides (the
   ``setup_extension`` call becomes a no-op).
3. Ulwazi + ``notfound_disabled = True`` -- no 404 page is generated.
4. Ulwazi + ``notfound_disabled = True`` + the extension listed explicitly
   -- the extension's own behaviour applies, but Ulwazi's prefix/template
   overrides are skipped (``notfound_template`` keeps the extension's
   default, ``page.html``).

Each build uses a tiny throwaway source directory under ``tmp_path`` so the
developer's environment and the sample docs are never touched.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sphinx.application import Sphinx

CONF_TEMPLATE = """
project = "bundling-test"
extensions = [{extensions}]
html_theme = "ulwazi"
{extra_config}
"""

INDEX_RST = """
Test page
=========

Content.
"""


def _build(
    tmp_path: Path,
    extensions: list[str],
    extra_config: str = "",
) -> tuple[Sphinx, Path]:
    """Run a minimal in-process Sphinx build and return (app, outdir)."""
    srcdir = tmp_path / "src"
    srcdir.mkdir()
    (srcdir / "conf.py").write_text(
        CONF_TEMPLATE.format(
            extensions=", ".join(f'"{ext}"' for ext in extensions),
            extra_config=extra_config,
        ),
        encoding="utf-8",
    )
    (srcdir / "index.rst").write_text(INDEX_RST, encoding="utf-8")

    outdir = tmp_path / "out"
    app = Sphinx(
        srcdir=str(srcdir),
        confdir=str(srcdir),
        outdir=str(outdir),
        doctreedir=str(tmp_path / "doctrees"),
        buildername="dirhtml",
        warningiserror=False,
    )
    app.build()
    return app, outdir


def _page_404(outdir: Path) -> Path:
    """Return the path of the generated 404 page (dirhtml: 404/index.html)."""
    return outdir / "404" / "index.html"


def test_auto_activation(tmp_path: Path) -> None:
    """Ulwazi alone activates the extension and generates the 404 page."""
    app, outdir = _build(tmp_path, extensions=["ulwazi"])
    assert "notfound.extension" in app.extensions, (
        "sphinx-notfound-page was not auto-activated by the theme"
    )
    page = _page_404(outdir)
    assert page.exists(), "404 page was not generated"
    content = page.read_text(encoding="utf-8")
    # Ulwazi's 404.html template renders the penguin image.
    assert "404.svg" in content, "404 page does not use Ulwazi's template"
    # Ulwazi's prefix computation ran (empty off RTD, but the config value
    # must have been assigned, not left at the extension's default).
    assert app.config.notfound_template == "404.html"


def test_coexistence_with_explicit_extension(tmp_path: Path) -> None:
    """Listing notfound.extension explicitly does not break the build."""
    app, outdir = _build(
        tmp_path, extensions=["ulwazi", "notfound.extension"]
    )
    # No double registration: the extension appears exactly once.
    assert "notfound.extension" in app.extensions
    page = _page_404(outdir)
    assert page.exists(), "404 page was not generated"
    content = page.read_text(encoding="utf-8")
    assert "404.svg" in content, "404 page does not use Ulwazi's template"
    assert app.config.notfound_template == "404.html"


def test_opt_out(tmp_path: Path) -> None:
    """notfound_disabled = True skips activation and the 404 page."""
    app, outdir = _build(
        tmp_path,
        extensions=["ulwazi"],
        extra_config="notfound_disabled = True",
    )
    assert "notfound.extension" not in app.extensions, (
        "notfound_disabled did not prevent the extension activation"
    )
    assert not _page_404(outdir).exists(), (
        "404 page was generated despite notfound_disabled = True"
    )


def test_opt_out_with_explicit_extension(tmp_path: Path) -> None:
    """With the extension listed explicitly, the flag only skips Ulwazi's
    overrides: the extension still runs, but with its own defaults."""
    app, outdir = _build(
        tmp_path,
        extensions=["ulwazi", "notfound.extension"],
        extra_config="notfound_disabled = True",
    )
    # The extension is active (explicit user intent wins)...
    assert "notfound.extension" in app.extensions
    page = _page_404(outdir)
    assert page.exists(), "404 page was not generated"
    # ...but Ulwazi's template override was skipped.
    assert app.config.notfound_template == "page.html", (
        "notfound_disabled did not skip Ulwazi's template override"
    )


@pytest.mark.parametrize(
    ("extensions", "extra_config", "expected"),
    [
        (["ulwazi"], "", "404.html"),
        (["ulwazi", "notfound.extension"], "", "404.html"),
        (["ulwazi"], "notfound_disabled = True", None),
        (["ulwazi", "notfound.extension"], "notfound_disabled = True", "page.html"),
    ],
)
def test_notfound_template_config(
    tmp_path: Path,
    extensions: list[str],
    extra_config: str,
    expected: str | None,
) -> None:
    """Consolidated check: the effective notfound_template per configuration.

    ``None`` means the extension is not active at all (opt-out without the
    explicit extension entry), in which case the config value is not
    registered by anyone.
    """
    app, _outdir = _build(
        tmp_path, extensions=extensions, extra_config=extra_config
    )
    if expected is None:
        assert "notfound.extension" not in app.extensions
    else:
        assert app.config.notfound_template == expected
