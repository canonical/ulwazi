"""Check that a fully populated Ulwazi configuration overrides theme defaults.

The fixture uses the Ulwazi-specific options illustrated by docs/default-conf.py.
Options not yet consumed by a theme template are checked only in html_context;
supported options are also checked in the rendered HTML.
"""

import io
import runpy
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from sphinx.application import Sphinx

pytestmark = pytest.mark.usefixtures("isolated_sphinx_build")

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "maximum-conf"
REPOSITORY = "https://github.com/example/maximum-docs"
EDIT_FALLBACK = f"{REPOSITORY}/edit/main/README.md"
VIEW_FALLBACK = f"{REPOSITORY}/blob/main/README.md"

# Keep expectations independent of the fixture so deleting an override or
# accidentally reverting to a documented default makes the test fail.
EXPECTED_CONTEXT = {
    "repo_branch": "release/2.0",
    "repo_folder": "/guides/",
    "default_source_extension": ".md",
    "discourse": "https://forum.example.com/maximum",
    "feedback": True,
    "github_url": REPOSITORY,
    "default_edit_url": EDIT_FALLBACK,
    "default_view_url": VIEW_FALLBACK,
    "mattermost": "https://chat.example.com/maximum",
    "matrix": "https://matrix.to/#/#maximum:example.com",
    "product_page": "example.com/maximum",
    "add_product_menu": True,
    "logo_link_URL": "https://example.com/maximum-home",
    "logo_img_URL": "https://example.com/assets/maximum-logo.svg",
    "logo_title": "Maximum docs",
    "license": {
        "name": "CC-BY-4.0",
        "url": "https://example.com/maximum-license",
    },
    "footer": {
        "product": True,
        "license": True,
        "entries": ['<a href="https://example.com/support">Maximum support</a>'],
    },
    # These are reserved; check preservation only, not visual behavior.
    "product_tag": "_static/maximum-tag.svg",
    "github_issues": "disabled",
    "sequential_nav": "both",
    "display_contributors": False,
    "path": "/maximum-docs",
}

DOCUMENTED_DEFAULTS = {
    "repo_branch": "main",
    "repo_folder": "/docs/",
    "default_source_extension": ".rst",
    "discourse": "https://discourse.ubuntu.com",
    "product_tag": "_static/tag.png",
    "github_issues": "enabled",
    "sequential_nav": "none",
    "display_contributors": True,
    "path": "/docs",
}


def _build(tmp_path: Path, overrides: dict | None = None) -> tuple[Sphinx, Path]:
    """Build the fixture in-process, keeping diagnostics for a failed build."""
    output = tmp_path / "_build"
    warnings = io.StringIO()
    app = Sphinx(
        srcdir=str(FIXTURE_DIR),
        confdir=str(FIXTURE_DIR),
        outdir=str(output),
        doctreedir=str(tmp_path / "_doctrees"),
        buildername="html",
        confoverrides=overrides,
        status=io.StringIO(),
        warning=warnings,
    )
    app.build()
    assert app.statuscode == 0, f"Maximum Sphinx build failed: {warnings.getvalue()}"
    return app, output


def _page(output: Path, name: str) -> BeautifulSoup:
    path = output / f"{name}.html"
    assert path.is_file(), f"Maximum Sphinx build did not produce {path}"
    return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")


def _check_navigation(page: BeautifulSoup) -> None:
    """Check the overridden TOC, product menu, logo and resource links."""
    toc = page.select_one("nav.p-table-of-contents__nav")
    assert toc is not None, "The local TOC was not rendered"
    assert "H5 heading" in toc.get_text(" ", strip=True)
    assert "H6 heading" not in toc.get_text(" ", strip=True)

    assert page.select_one("header#product-menu-header") is not None
    header = page.select_one("header#navigation")
    assert header is not None
    logo = header.select_one(".p-navigation__tagged-logo a.p-navigation__link")
    assert logo is not None
    assert logo.get("href") == EXPECTED_CONTEXT["logo_link_URL"]
    image = logo.select_one("img.p-navigation__logo-icon")
    assert image is not None
    assert image.get("src") == EXPECTED_CONTEXT["logo_img_URL"]
    title = logo.select_one(".p-navigation__logo-title")
    assert title is not None
    assert title.get_text(strip=True) == "Maximum docs"
    assert header.select_one('a[href="https://example.com/maximum"]') is not None
    for link in ("discourse", "mattermost", "matrix", "github_url"):
        assert (
            header.select_one(f'#link-2-menu a[href="{EXPECTED_CONTEXT[link]}"]')
            is not None
        ), f"{link} link did not render"


def _check_feedback(page: BeautifulSoup, output: Path) -> None:
    """Check repository and generated-page feedback links."""
    feedback = page.select_one(".p-toc-feedback-block")
    assert feedback is not None
    issue = feedback.select_one("a.p-button--positive")
    assert issue is not None
    issue_url = issue.get("href")
    assert isinstance(issue_url, str)
    assert issue_url.startswith(f"{REPOSITORY}/issues/new?")
    edit = feedback.select_one("a.p-icon--edit")
    view = feedback.select_one("a.p-icon--show")
    assert edit is not None
    assert edit.get("href") == f"{REPOSITORY}/edit/release/2.0/guides/index.rst"
    assert view is not None
    assert view.get("href") == f"{REPOSITORY}/blob/release/2.0/guides/index.rst"

    # Generated pages without a source suffix use default_source_extension.
    generated = _page(output, "genindex")
    generated_edit = generated.select_one(".p-toc-feedback-block a.p-icon--edit")
    generated_view = generated.select_one(".p-toc-feedback-block a.p-icon--show")
    assert generated_edit is not None
    assert generated_edit.get("href") == (
        f"{REPOSITORY}/edit/release/2.0/guides/genindex.md"
    )
    assert generated_view is not None
    assert generated_view.get("href") == (
        f"{REPOSITORY}/blob/release/2.0/guides/genindex.md"
    )


def _check_footer(page: BeautifulSoup) -> None:
    """Check the configured product, license and custom footer entry."""
    footer = page.select_one('footer nav[aria-label="Footer"]')
    assert footer is not None
    product = footer.select_one('a[href="https://example.com/maximum"]')
    assert product is not None
    assert product.get_text(" ", strip=True) == "Maximum configuration example 2.0"
    license_link = footer.select_one('a[href="https://example.com/maximum-license"]')
    assert license_link is not None
    assert license_link.get_text(strip=True) == "CC-BY-4.0"
    support = footer.select_one('a[href="https://example.com/support"]')
    assert support is not None
    assert support.get_text(strip=True) == "Maximum support"


def test_maximum_config_overrides(tmp_path: Path) -> None:
    """Explicit options survive setup; supported options reach the page."""
    app, output = _build(tmp_path)

    assert app.config.localtoc_max_depth == 4  # documented default: 3
    for key, expected in EXPECTED_CONTEXT.items():
        assert app.config.html_context.get(key) == expected, (
            f"html_context[{key!r}] did not retain its configured value"
        )
    for key, default in DOCUMENTED_DEFAULTS.items():
        assert EXPECTED_CONTEXT[key] != default, f"{key} does not override its default"

    page = _page(output, "index")
    _check_navigation(page)
    _check_feedback(page, output)
    _check_footer(page)


def test_maximum_config_fallback_urls(tmp_path: Path) -> None:
    """With no repository URL, feedback uses the explicit edit/view URLs."""
    context = dict(runpy.run_path(str(FIXTURE_DIR / "conf.py"))["html_context"])
    context["github_url"] = ""
    app, output = _build(tmp_path, {"html_context": context})
    assert app.config.html_context["github_url"] == ""

    page = _page(output, "index")
    edit = page.select_one(".p-toc-feedback-block a.p-icon--edit")
    view = page.select_one(".p-toc-feedback-block a.p-icon--show")
    assert edit is not None
    assert edit.get("href") == EDIT_FALLBACK
    assert view is not None
    assert view.get("href") == VIEW_FALLBACK
