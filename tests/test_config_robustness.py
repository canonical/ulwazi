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

"""Grouped regression checks for minimal, default, and maximum configuration.

Each fixture build runs through Sphinx's Python API. Independent checks report
their failures together under one pytest result, without hiding later cases.
"""

import io
import runpy
from collections.abc import Callable
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from sphinx.application import Sphinx

pytestmark = pytest.mark.usefixtures("isolated_sphinx_build")

FIXTURES = Path(__file__).parent / "fixtures"
CHEAT_SHEET_PATH = Path("docs/_build/content/rst-cheat-sheet/index.html")
REPOSITORY = "https://github.com/example/maximum-docs"
EDIT_FALLBACK = f"{REPOSITORY}/edit/main/README.md"
VIEW_FALLBACK = f"{REPOSITORY}/blob/main/README.md"

# Independent of conf.py: these values must survive config-inited unchanged.
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
    "license": {"name": "CC-BY-4.0", "url": "https://example.com/maximum-license"},
    "footer": {
        "product": True,
        "license": True,
        "entries": ['<a href="https://example.com/support">Maximum support</a>'],
    },
    # Reserved settings: verify preservation only, not rendered behavior.
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


def _build(
    fixture: str, root: Path, overrides: dict | None = None
) -> tuple[Sphinx, Path, str]:
    """Build one independent fixture and retain Sphinx warnings for diagnostics."""
    source = FIXTURES / fixture
    output = root / "_build"
    warnings = io.StringIO()
    app = Sphinx(
        srcdir=str(source),
        confdir=str(source),
        outdir=str(output),
        doctreedir=str(root / "_doctrees"),
        buildername="html",
        confoverrides=overrides,
        status=io.StringIO(),
        warning=warnings,
    )
    app.build()
    assert app.statuscode == 0, (
        f"Sphinx exited with status {app.statuscode}: {warnings.getvalue()}"
    )
    return app, output, warnings.getvalue()


def _page(output: Path, name: str = "index") -> BeautifulSoup:
    path = output / f"{name}.html"
    assert path.is_file(), f"Built page not found: {path}"
    return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")


def _record(errors: list[str], label: str, check: Callable[[], object]) -> None:
    """Report a failing part and continue with the remaining independent parts."""
    try:
        check()
    except Exception as exc:  # noqa: BLE001 (report fixture build failures too)
        message = str(exc).split("\nassert ", 1)[0].strip() or repr(exc)
        errors.append(f"[{label}] {message}")


def _local_toc_text(html: str) -> str:
    """Return the text of the local "On this page" TOC only, since heading
    text also legitimately appears in the article body."""
    soup = BeautifulSoup(html, "html.parser")
    nav = soup.find("nav", class_="p-table-of-contents__nav")
    assert nav is not None, "local TOC nav not found in rendered page"
    return nav.get_text()


def _check_minimal(output: Path) -> None:
    """The two-line conf.py produces a themed HTML page."""
    soup = _page(output)
    heading = soup.select_one("main#content h1")
    assert heading is not None, "Fixture title did not render"
    assert heading.get_text(" ", strip=True).startswith("Test"), (
        "Fixture title did not render"
    )
    assert soup.select_one('link[href*="vanilla-main.css"]') is not None, (
        "Built page does not load the Ulwazi stylesheet"
    )


def _check_depth(output: Path, warnings: str, *, includes_h5: bool) -> None:
    toc_text = _local_toc_text((output / "index.html").read_text(encoding="utf-8"))
    failures = []
    if "H4 heading" not in toc_text:
        failures.append("H4 heading missing from local TOC")
    if ("H5 heading" in toc_text) != includes_h5:
        expectation = "present" if includes_h5 else "absent"
        failures.append(f"expected H5 heading {expectation} in local TOC")
    if "localtoc_max_depth" in warnings:
        failures.append("Sphinx warned about localtoc_max_depth")
    assert not failures, "; ".join(failures)


def _check_sample_docs() -> None:
    assert CHEAT_SHEET_PATH.exists(), f"{CHEAT_SHEET_PATH} not found; run 'make docs'"
    toc_text = _local_toc_text(CHEAT_SHEET_PATH.read_text(encoding="utf-8"))
    assert "H4 heading" in toc_text, "H4 heading missing from local TOC"
    assert "H5 heading" not in toc_text, "H5 heading should not appear in local TOC"


def _check_feedback_defaults(output: Path) -> None:
    """Absent repository fields fall back to main/docs and the .rst suffix."""
    html = (output / "index.html").read_text(encoding="utf-8")
    assert (
        'href="https://github.com/canonical/example/edit/main/docs/index.rst"' in html
    )
    assert (
        'href="https://github.com/canonical/example/blob/main/docs/index.rst"' in html
    )


def _check_aliases(output: Path, warnings: str) -> None:
    """Old GitHub field names still affect links and emit deprecations."""
    html = (output / "index.html").read_text(encoding="utf-8")
    failures = []
    for action, prefix in (("edit", "edit"), ("view", "blob")):
        link = (
            f'href="https://github.com/canonical/example/{prefix}/'
            'stable/2.0/documentation/index.rst"'
        )
        if link not in html:
            failures.append(f"{action} link does not use deprecated aliases")
    failures.extend(
        f"{alias} did not emit a deprecation warning"
        for alias in ("github_version", "github_folder")
        if f"'{alias}' is deprecated" not in warnings
    )
    assert not failures, "; ".join(failures)


def _check_maximum_values(app: Sphinx) -> None:
    failures = []
    if app.config.localtoc_max_depth != 4:  # documented default: 3
        failures.append(
            f"localtoc_max_depth is {app.config.localtoc_max_depth!r}, expected 4"
        )
    for key, expected in EXPECTED_CONTEXT.items():
        if app.config.html_context.get(key) != expected:
            failures.append(f"html_context[{key!r}] did not retain {expected!r}")
    for key, default in DOCUMENTED_DEFAULTS.items():
        if EXPECTED_CONTEXT[key] == default:
            failures.append(f"{key} does not override its documented default")
    assert not failures, "; ".join(failures)


def _check_maximum_navigation(page: BeautifulSoup) -> None:
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


def _check_maximum_feedback(page: BeautifulSoup, output: Path) -> None:
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


def _check_maximum_footer(page: BeautifulSoup) -> None:
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


def _check_fallback(output: Path) -> None:
    page = _page(output)
    edit = page.select_one(".p-toc-feedback-block a.p-icon--edit")
    view = page.select_one(".p-toc-feedback-block a.p-icon--show")
    assert edit is not None
    assert edit.get("href") == EDIT_FALLBACK
    assert view is not None
    assert view.get("href") == VIEW_FALLBACK


def test_config_robustness(tmp_path: Path) -> None:
    """Report one result, with separately labelled failures for each scenario."""
    errors: list[str] = []

    def run_build(
        label: str, fixture: str, overrides: dict | None = None
    ) -> tuple[Sphinx, Path, str] | None:
        try:
            return _build(fixture, tmp_path / label, overrides)
        except Exception as exc:  # noqa: BLE001 (a failed build must not hide other cases)
            errors.append(f"[{label}] build failed: {exc}")
            return None

    minimal = run_build("minimal", "minimal-conf")
    if minimal is not None:
        _record(errors, "minimal page", lambda: _check_minimal(minimal[1]))
        _record(
            errors,
            "TOC unset",
            lambda: _check_depth(minimal[1], minimal[2], includes_h5=False),
        )

    for label, value in (("None", None), ("-1", -1)):
        result = run_build(
            f"TOC {label}", "minimal-conf", {"localtoc_max_depth": value}
        )
        if result is not None:
            _record(
                errors,
                f"TOC {label}",
                lambda result=result: _check_depth(
                    result[1], result[2], includes_h5=True
                ),
            )
    _record(errors, "sample docs TOC", _check_sample_docs)

    defaults = run_build("feedback defaults", "feedback-no-repo-vars")
    if defaults is not None:
        _record(
            errors, "feedback defaults", lambda: _check_feedback_defaults(defaults[1])
        )
    aliases = run_build("deprecated aliases", "deprecated-github-aliases")
    if aliases is not None:
        _record(
            errors, "deprecated aliases", lambda: _check_aliases(aliases[1], aliases[2])
        )

    maximum = run_build("maximum", "maximum-conf")
    if maximum is not None:
        _record(errors, "maximum values", lambda: _check_maximum_values(maximum[0]))
        try:
            page = _page(maximum[1])
        except Exception as exc:  # noqa: BLE001 (continue with fallback build)
            errors.append(f"[maximum page] {exc}")
        else:
            _record(
                errors, "maximum navigation", lambda: _check_maximum_navigation(page)
            )
            _record(
                errors,
                "maximum feedback",
                lambda: _check_maximum_feedback(page, maximum[1]),
            )
            _record(errors, "maximum footer", lambda: _check_maximum_footer(page))

    try:
        context = dict(
            runpy.run_path(str(FIXTURES / "maximum-conf/conf.py"))["html_context"]
        )
        context["github_url"] = ""
    except Exception as exc:  # noqa: BLE001 (report fixture setup failures)
        errors.append(f"[fallback URLs] fixture setup failed: {exc}")
    else:
        fallback = run_build("fallback URLs", "maximum-conf", {"html_context": context})
        if fallback is not None:
            _record(errors, "fallback URLs", lambda: _check_fallback(fallback[1]))

    assert not errors, "Configuration robustness checks failed:\n  - " + "\n  - ".join(
        errors
    )
