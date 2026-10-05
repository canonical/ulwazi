"""Tests for the bundled sphinx-notfound-page integration.

The theme activates ``sphinx-notfound-page`` automatically via
``app.setup_extension()`` from its ``setup()`` (idempotent, so projects that
also list ``notfound.extension`` in ``extensions`` are unaffected), and
provides an opt-out via the ``notfound_disabled`` config value.

The ``ACTIVATION_CASES`` table covers normal activation, extension ordering,
theme-only entry-point loading, and opt-out. Each case has a descriptive ID
and a nearby comment explaining why it matters. Separate tests cover RTD
prefixes, command-line opt-out, and project-supplied overrides.

Each build uses a tiny throwaway source directory under ``tmp_path`` so the
developer's environment and the sample docs are never touched.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

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
    overrides: dict[str, Any] | None = None,
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
        confoverrides=overrides,
        warningiserror=False,
    )
    app.build()
    return app, outdir


def _page_404(outdir: Path) -> Path:
    """Return the path of the generated 404 page (dirhtml: 404/index.html)."""
    return outdir / "404" / "index.html"


ACTIVATION_CASES = [
    # Ulwazi alone must load notfound and apply its own 404 template and
    # local-build prefix rather than the extension's /en/latest/ default.
    pytest.param(["ulwazi"], "", "404.html", "", id="auto-activation"),
    # Existing projects can keep notfound explicitly after Ulwazi; Sphinx's
    # setup_extension call must not register the extension twice.
    pytest.param(
        ["ulwazi", "notfound.extension"],
        "",
        "404.html",
        "",
        id="explicit-extension-after-ulwazi",
    ),
    # Sphinx Stack can list notfound first; Ulwazi must still apply its defaults.
    pytest.param(
        ["notfound.extension", "ulwazi"],
        "",
        "404.html",
        "",
        id="explicit-extension-before-ulwazi",
    ),
    # Selecting only html_theme loads Ulwazi after config-inited; the 404
    # integration must still get its defaults at this later entry point.
    pytest.param([], "", "404.html", "", id="theme-only"),
    # The flag must prevent automatic activation when Ulwazi is an extension.
    pytest.param(["ulwazi"], "notfound_disabled = True", None, None, id="opt-out"),
    # The same flag must work when Ulwazi is selected only through html_theme.
    pytest.param([], "notfound_disabled = True", None, None, id="theme-only-opt-out"),
    # An explicit notfound entry remains active when Ulwazi's integration is
    # disabled; it retains the extension's own template and prefix defaults.
    pytest.param(
        ["ulwazi", "notfound.extension"],
        "notfound_disabled = True",
        "page.html",
        "/en/latest/",
        id="opt-out-with-explicit-extension",
    ),
]


@pytest.mark.parametrize(
    ("extensions", "extra_config", "expected_template", "expected_prefix"),
    ACTIVATION_CASES,
)
def test_notfound_activation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    extensions: list[str],
    extra_config: str,
    expected_template: str | None,
    expected_prefix: str | None,
) -> None:
    """Build each adoption scenario and check the resulting 404 integration."""
    monkeypatch.delenv("READTHEDOCS_CANONICAL_URL", raising=False)
    app, outdir = _build(tmp_path, extensions=extensions, extra_config=extra_config)
    page = _page_404(outdir)
    assert ("notfound.extension" in app.extensions) == (expected_template is not None)
    assert page.exists() == (expected_template is not None)
    if expected_template is not None:
        assert app.config.notfound_template == expected_template
        assert app.config.notfound_urls_prefix == expected_prefix
        assert ("404.svg" in page.read_text(encoding="utf-8")) == (
            expected_template == "404.html"
        )


def test_theme_entry_point_rtd_prefix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Late theme loading still applies the RTD schema to 404 links."""
    monkeypatch.setenv("READTHEDOCS_CANONICAL_URL", "https://example.com/latest/")
    monkeypatch.setenv("READTHEDOCS_VERSION", "latest")
    monkeypatch.setenv("READTHEDOCS_LANGUAGE", "en")
    app, outdir = _build(tmp_path, extensions=[], extra_config='slug = "ulwazi"')
    assert app.config.notfound_urls_prefix == "/ulwazi/latest/"
    assert 'href="/ulwazi/latest/' in _page_404(outdir).read_text(encoding="utf-8")


def test_cli_opt_out(tmp_path: Path) -> None:
    """Sphinx's -D override skips automatic activation."""
    app, outdir = _build(
        tmp_path, extensions=["ulwazi"], overrides={"notfound_disabled": "1"}
    )
    assert "notfound.extension" not in app.extensions
    assert not _page_404(outdir).exists()


@pytest.mark.parametrize("extensions", [["ulwazi"], []], ids=["extension", "theme"])
def test_project_notfound_settings_are_respected(
    tmp_path: Path, extensions: list[str]
) -> None:
    """Project settings in conf.py take precedence over Ulwazi's defaults."""
    app, outdir = _build(
        tmp_path,
        extensions=extensions,
        extra_config='notfound_template = "page.html"\nnotfound_urls_prefix = "/my-docs/"',
    )
    assert app.config.notfound_template == "page.html"
    assert app.config.notfound_urls_prefix == "/my-docs/"
    assert _page_404(outdir).exists()


def test_cli_notfound_settings_are_respected(tmp_path: Path) -> None:
    """Sphinx command-line -D settings also take precedence."""
    app, _ = _build(
        tmp_path,
        extensions=["ulwazi"],
        overrides={
            "notfound_template": "page.html",
            "notfound_urls_prefix": "/my-docs/",
        },
    )
    assert app.config.notfound_template == "page.html"
    assert app.config.notfound_urls_prefix == "/my-docs/"


def test_built_404_page(built_site) -> None:
    """The sample site's 404 page uses Ulwazi chrome and its bundled asset."""
    soup = built_site.page("404")
    assert soup.find("header") or soup.select_one(".p-navigation")
    assert soup.select_one(".l-footer") or soup.find("footer")
    assert "Page not found" in soup.get_text()

    img = soup.find("img", alt="Penguin with a question mark")
    assert img is not None, "404 page is missing the penguin image"
    assert str(img.get("src", "")).endswith("404.svg")
    # sphinx-notfound-page rewrites relative URLs on 404 pages; check the
    # generated file directly rather than interpreting the rewritten URL.
    assert (built_site.output / "_static" / "404.svg").is_file()


def test_404_page_excluded_from_sitemap(built_site) -> None:
    """The generated 404 page must not appear in the sample site's sitemap."""
    sitemap = built_site.output / "sitemap.xml"
    assert sitemap.is_file()
    assert "/404/" not in sitemap.read_text(encoding="utf-8")
