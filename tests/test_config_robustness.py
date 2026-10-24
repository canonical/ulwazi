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

import copy
import io
import runpy
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import cast

import pytest
from bs4 import BeautifulSoup
from bs4.element import Tag
from sphinx.application import Sphinx
from sphinx.util.docutils import docutils_namespace, patch_docutils
from ulwazi import _configure_html_context

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
    # Opt-in Get help panel: rendered behaviour is asserted separately.
    "help_links": {
        "title": "Get help",
        "links": [
            {"text": "Ask on the forum", "url": "https://forum.example.com/maximum"},
            {
                "text": "Report a doc issue",
                "url": f"{REPOSITORY}/issues/new",
            },
        ],
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
    with patch_docutils(str(source)), docutils_namespace():
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
    assert soup.select_one(
        ".p-toc-feedback-block .content-icon-container.navigation-only button.js-drawer-toggle"
    ), "Pages without feedback still need a mobile navigation opener"


def _check_default_footer(output: Path) -> None:
    """Without footer configuration, the documented defaults render."""
    footer = _page(output).select_one('footer nav[aria-label="Footer"]')
    assert footer is not None, "Footer nav missing from the built page"
    tracker = footer.select_one("a.js-revoke-cookie-manager")
    assert tracker is not None, "Default tracker-settings entry missing"
    assert tracker.get("href") == "#tracker-settings"
    assert tracker.get_text(strip=True) == "Manage your tracker settings"


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
    # The sample docs opt into the Get help panel (docs/conf.py): it must
    # render below the Global ToC with the configured links.
    soup = BeautifulSoup(CHEAT_SHEET_PATH.read_text(encoding="utf-8"), "html.parser")
    panel = soup.select_one("nav#drawer div.p-help-links")
    assert panel is not None, "Get help panel missing from the sample docs"
    heading = panel.select_one("p.caption span.caption-text")
    assert heading is not None, "Get help panel heading missing from the sample docs"
    assert heading.get_text(strip=True) == "Get help"
    hrefs = [link.get("href") for link in panel.select("a.p-help-links__link")]
    assert "https://discourse.ubuntu.com/c/documentation/7" in hrefs
    assert "https://github.com/canonical/ulwazi/issues/new" in hrefs


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


def _check_maximum_help_links(page: BeautifulSoup) -> None:
    """The configured Get help panel renders, without toctree link classes."""
    panel = page.select_one("nav#drawer div.p-help-links")
    assert panel is not None, "Get help panel missing from the side navigation"
    heading = panel.select_one("p.caption span.caption-text")
    assert heading is not None, "Get help panel heading missing"
    assert heading.get_text(strip=True) == "Get help"
    links = panel.select(
        "ul.p-help-links__list li.p-help-links__item a.p-help-links__link"
    )
    assert len(links) == 2, "Expected the two configured help links"
    assert links[0].get("href") == "https://forum.example.com/maximum"
    assert links[0].get_text(strip=True) == "Ask on the forum"
    assert links[1].get("href") == f"{REPOSITORY}/issues/new"
    assert links[1].get_text(strip=True) == "Report a doc issue"
    for link in links:
        # Help links are external resources, not toctree entries: they must
        # not pick up navigation-link or current-page classes.
        classes = link.get_attribute_list("class")
        assert "p-side-navigation__link" not in classes
        assert "is-active" not in classes
        assert link.get("aria-current") is None


def _check_no_help_links(page: BeautifulSoup) -> None:
    """Without configuration, no Get help panel renders."""
    assert page.select_one("nav#drawer div.p-help-links") is None


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


@pytest.mark.parametrize(
    ("version_type", "identifier", "expected_branch"),
    [
        ("branch", "feature/docs", "feature/docs"),
        ("branch", "", "stable"),
        ("external", "123", "stable"),
        ("tag", "v2.0", "stable"),
    ],
)
def test_rtd_source_branch(
    monkeypatch: pytest.MonkeyPatch,
    version_type: str,
    identifier: str,
    expected_branch: str,
) -> None:
    """RTD builds use only a real branch identifier in source links."""
    monkeypatch.setenv("READTHEDOCS", "True")
    monkeypatch.setenv("READTHEDOCS_VERSION_TYPE", version_type)
    monkeypatch.setenv("READTHEDOCS_GIT_IDENTIFIER", identifier)
    context = {"repo_branch": "stable", "repo_folder": "guides"}

    _configure_html_context(context)

    assert context["repo_branch"] == expected_branch
    assert context["repo_folder"] == "/guides/"


def test_repo_default_branch_alias() -> None:
    """The canonical-sphinx-era repo_default_branch key maps to repo_branch."""
    context = {"repo_default_branch": "release/2.0"}
    _configure_html_context(context)
    assert context["repo_branch"] == "release/2.0"


def test_footer_defaults() -> None:
    """Unset and partial footer configs get the documented defaults per key."""
    default_entries = [
        (
            '<a href="#tracker-settings" class="js-revoke-cookie-manager muted-link">'
            "Manage your tracker settings</a>"
        )
    ]

    # The whole footer dict is unset: every key gets its default.
    unset: dict = {}
    _configure_html_context(unset)
    assert unset["footer"] == {
        "product": True,
        "license": True,
        "entries": default_entries,
    }

    # A partial footer keeps its explicit value and fills in the rest.
    partial: dict = {"footer": {"entries": ['<a href="https://example.com">Link</a>']}}
    _configure_html_context(partial)
    assert partial["footer"] == {
        "product": True,
        "license": True,
        "entries": ['<a href="https://example.com">Link</a>'],
    }

    # An explicit footer is never overridden.
    explicit: dict = {"footer": {"product": False, "license": False, "entries": []}}
    _configure_html_context(explicit)
    assert explicit["footer"] == {"product": False, "license": False, "entries": []}


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
        _record(errors, "default footer", lambda: _check_default_footer(minimal[1]))
        _record(
            errors,
            "TOC unset",
            lambda: _check_depth(minimal[1], minimal[2], includes_h5=False),
        )
        _record(
            errors, "help links unset", lambda: _check_no_help_links(_page(minimal[1]))
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
                errors, "maximum help links", lambda: _check_maximum_help_links(page)
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


@pytest.mark.parametrize(
    ("help_links", "expected_warning"),
    [
        # Missing keys
        ({"title": "Get help"}, "'links'"),
        ({"links": [{"text": "a", "url": "https://example.com"}]}, "'title'"),
        # Empty values
        (
            {"title": "  ", "links": [{"text": "a", "url": "https://example.com"}]},
            "'title'",
        ),
        ({"title": "Get help", "links": []}, "'links'"),
        # Malformed links
        (
            {"title": "Get help", "links": [{"text": "a"}]},
            "'url'",
        ),
        (
            {"title": "Get help", "links": [{"url": "https://example.com"}]},
            "'text'",
        ),
        # Unsafe or non-absolute URLs
        (
            {
                "title": "Get help",
                "links": [{"text": "a", "url": "javascript:alert(1)"}],
            },
            "http(s)",
        ),
        (
            {"title": "Get help", "links": [{"text": "a", "url": "/relative/path"}]},
            "http(s)",
        ),
        # Wrong types
        ("Get help", "mapping"),
        ([{"text": "a", "url": "https://example.com"}], "mapping"),
    ],
)
def test_help_links_invalid_config(
    tmp_path: Path, help_links: object, expected_warning: str
) -> None:
    """Invalid help_links values warn once and render no panel, without crashing."""
    snapshot = copy.deepcopy(help_links)

    app, output, warnings = _build(
        "maximum-conf", tmp_path, {"html_context.help_links": help_links}
    )

    # The build succeeds and warns exactly once, naming the offending key.
    assert app.statuscode == 0
    assert "help_links" in warnings
    assert expected_warning in warnings
    assert warnings.count("help_links") == 1, (
        f"Expected exactly one help_links warning, got:\n{warnings}"
    )

    # No panel renders anywhere.
    for built in output.glob("**/*.html"):
        page = BeautifulSoup(built.read_text(encoding="utf-8"), "html.parser")
        assert page.select_one("div.p-help-links") is None, (
            f"Get help panel rendered in {built.name} despite invalid config"
        )

    # The caller's configuration value is not mutated.
    assert help_links == snapshot


def test_help_links_theme_only_loading(tmp_path: Path) -> None:
    """The panel also renders when Ulwazi is selected only via html_theme."""
    source = FIXTURES / "maximum-conf"
    output = tmp_path / "theme-only" / "_build"
    warnings = io.StringIO()
    with patch_docutils(str(source)), docutils_namespace():
        app = Sphinx(
            srcdir=str(source),
            confdir=str(source),
            outdir=str(output),
            doctreedir=str(tmp_path / "theme-only" / "_doctrees"),
            buildername="html",
            # Select the theme only: no "ulwazi" in extensions, so
            # config-inited never fires and builder-inited must carry it.
            confoverrides={"extensions": []},
            status=io.StringIO(),
            warning=warnings,
        )
        app.build()
    assert app.statuscode == 0, warnings.getvalue()
    page = _page(output)
    panel = page.select_one("nav#drawer div.p-help-links")
    assert panel is not None, "Get help panel missing in theme-only loading"
    assert panel.select_one("a.p-help-links__link") is not None


# ---------------------------------------------------------------------------
# MyST compatibility defaults (restored from canonical-sphinx)
# ---------------------------------------------------------------------------

# The three syntax extensions canonical-sphinx enabled by default.
MYST_DEFAULT_EXTENSIONS = frozenset({"substitution", "deflist", "linkify"})

MYST_CONF_TEMPLATE = """
project = "myst-defaults"
extensions = [{extensions}]
html_theme = "ulwazi"
{extra_config}
"""

MYST_INDEX_MD = """\
# MyST defaults

Replacement: {{ product }}.

Example term
: A specific definition.

Bare URL: https://example.com/myst-defaults
"""


def _build_myst(
    tmp_path: Path,
    extensions: list[str],
    extra_config: str = "",
    overrides: dict | None = None,
    *,
    warningiserror: bool = True,
) -> tuple[Sphinx, Path, str]:
    """Build a tiny MyST site and return (app, outdir, warnings).

    The site is generated under ``tmp_path`` so the developer environment,
    the sample docs, and other tests' fixtures are never touched. Builds run
    in-process (with docutils patched) so coverage observes the theme hooks.
    """
    srcdir = tmp_path / "src"
    srcdir.mkdir(parents=True)
    (srcdir / "conf.py").write_text(
        MYST_CONF_TEMPLATE.format(
            extensions=", ".join(f'"{ext}"' for ext in extensions),
            extra_config=extra_config,
        ),
        encoding="utf-8",
    )
    (srcdir / "index.md").write_text(MYST_INDEX_MD, encoding="utf-8")

    output = tmp_path / "_build"
    warnings = io.StringIO()
    with patch_docutils(str(srcdir)), docutils_namespace():
        app = Sphinx(
            srcdir=str(srcdir),
            confdir=str(srcdir),
            outdir=str(output),
            doctreedir=str(tmp_path / "_doctrees"),
            buildername="html",
            confoverrides=overrides,
            status=io.StringIO(),
            warning=warnings,
            warningiserror=warningiserror,
        )
        app.build()
    assert app.statuscode == 0, (
        f"Sphinx exited with status {app.statuscode}: {warnings.getvalue()}"
    )
    return app, output, warnings.getvalue()


def _myst_page(output: Path) -> BeautifulSoup:
    """Return the parsed article of the built MyST index page."""
    path = output / "index.html"
    assert path.is_file(), f"Built page not found: {path}"
    return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")


def _myst_env_extensions(app: Sphinx) -> set[str]:
    """Return MyST's snapshot enable_extensions from the build environment.

    myst_parser assigns ``app.env.myst_config`` dynamically at
    ``builder-inited``; Sphinx's BuildEnvironment has no static attribute
    for it, so ``getattr`` keeps pyright satisfied.
    """
    myst_config = getattr(app.env, "myst_config", None)
    assert myst_config is not None, "myst_parser did not initialize env config"
    return set(myst_config.enable_extensions)


def _check_myst_rendering(
    output: Path, enabled: frozenset[str] | set[str]
) -> list[str]:
    """Assert which MyST syntax features rendered; return labelled failures."""
    page = _myst_page(output)
    article = page.select_one("main#content")
    assert article is not None, "Built page has no main#content article"
    text = article.get_text(" ", strip=True)
    return [
        *(
            _check_substitution(article, text)
            if "substitution" in enabled
            else _check_disabled(
                "substitution rendered the configured value",
                rendered="Replacement: Ulwazi." in text,
            )
        ),
        *(
            _check_deflist(article)
            if "deflist" in enabled
            else _check_disabled(
                "deflist rendered a definition list",
                rendered=article.select_one("dl.simple") is not None,
            )
        ),
        *(
            _check_linkify(article)
            if "linkify" in enabled
            else _check_disabled(
                "linkify rendered a link",
                rendered=article.select_one(
                    'a[href="https://example.com/myst-defaults"]'
                )
                is not None,
            )
        ),
    ]


def _check_disabled(feature: str, *, rendered: bool) -> list[str]:
    """A disabled feature must not render; report a labelled failure if it did."""
    return [f"{feature} despite being disabled"] if rendered else []


def _check_substitution(article: Tag, text: str) -> list[str]:
    """substitution: {{ product }} is replaced by the configured value."""
    failures: list[str] = []
    if "Replacement: Ulwazi." not in text:
        failures.append("substitution did not render the configured value")
    if "{{ product }}" in text:
        failures.append("literal {{ product }} remains; substitution inactive")
    return failures


def _check_deflist(article: Tag) -> list[str]:
    """deflist: the term/definition pair becomes a definition list."""
    deflist = article.select_one("dl.simple")
    if deflist is None:
        return ["deflist did not render a definition list"]
    failures: list[str] = []
    term = deflist.select_one("dt")
    definition = deflist.select_one("dd")
    if term is None or term.get_text(" ", strip=True) != "Example term":
        failures.append("deflist term did not render")
    if definition is None or (
        "A specific definition" not in definition.get_text(" ", strip=True)
    ):
        failures.append("deflist definition did not render")
    return failures


def _check_linkify(article: Tag) -> list[str]:
    """linkify: the bare URL becomes an anchor with the exact URL."""
    anchor = article.select_one('a[href="https://example.com/myst-defaults"]')
    if anchor is None:
        return ["linkify did not render the bare URL as a link"]
    if anchor.get_text(strip=True) != "https://example.com/myst-defaults":
        return ["linkify anchor text does not match the URL"]
    return []


@pytest.mark.parametrize(
    "extensions",
    [["ulwazi", "myst_parser"], ["myst_parser", "ulwazi"]],
    ids=["ulwazi-first", "myst-first"],
)
def test_myst_defaults_restored(tmp_path: Path, extensions: list[str]) -> None:
    """Unset myst_enable_extensions gets the former canonical-sphinx defaults."""
    app, output, warnings = _build_myst(
        tmp_path,
        extensions=extensions,
        extra_config='myst_substitutions = {"product": "Ulwazi"}',
    )
    assert not warnings, f"Unexpected warnings:\n{warnings}"
    assert app.config.myst_enable_extensions == MYST_DEFAULT_EXTENSIONS
    assert _myst_env_extensions(app) == MYST_DEFAULT_EXTENSIONS
    failures = _check_myst_rendering(output, MYST_DEFAULT_EXTENSIONS)
    assert not failures, "; ".join(failures)


# One representative value per distinct behaviour: an explicitly empty
# collection disables the defaults, a custom collection is preserved
# as-is, and selecting a single extension does not add the others. The
# container type is irrelevant to the guard (it checks the key's absence
# in _raw_config/overrides, never the value), and the extension order is
# covered by test_myst_defaults_restored: Sphinx loads every extension
# before any config-inited handler runs, so the guard sees the same
# registered setting in both orders.
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ([], set()),
        (["colon_fence", "tasklist"], {"colon_fence", "tasklist"}),
        (["deflist"], {"deflist"}),
    ],
    ids=["empty-list", "custom-list", "singleton-deflist"],
)
def test_myst_explicit_extensions_preserved(
    tmp_path: Path, value: object, expected: set[str]
) -> None:
    """Explicit myst_enable_extensions values replace the defaults, not extend."""
    app, output, warnings = _build_myst(
        tmp_path,
        extensions=["ulwazi", "myst_parser"],
        extra_config=(
            f"myst_substitutions = {{'product': 'Ulwazi'}}\n"
            f"myst_enable_extensions = {value!r}"
        ),
    )
    assert not warnings, f"Unexpected warnings:\n{warnings}"
    # The explicit value is preserved exactly: no defaults are added, the
    # container type is not changed, and the project-owned collection in
    # _raw_config is not replaced or mutated in place.
    effective = app.config.myst_enable_extensions
    owned = app.config._raw_config["myst_enable_extensions"]
    assert isinstance(effective, type(value))
    assert isinstance(owned, type(value))
    assert [str(item) for item in cast("Iterable[object]", effective)] == [
        str(item) for item in cast("Iterable[object]", owned)
    ]
    assert effective is owned
    assert _myst_env_extensions(app) == expected
    failures = _check_myst_rendering(output, expected)
    assert not failures, "; ".join(failures)


# override-only-empty proves Ulwazi's own overrides guard: with the setting
# absent from conf.py, only the overrides check keeps the defaults out.
# override-vs-file proves an override replaces a conflicting conf.py value
# rather than falling back to it or unioning with it. Both use the typed
# confoverrides API: Sphinx itself cannot convert string -D values for this
# set-typed setting (see docs/content/configuration.md). A singleton override
# adds nothing over override-vs-file, and the extension order is irrelevant
# here for the same reason as in test_myst_explicit_extensions_preserved.
@pytest.mark.parametrize(
    ("overrides", "expected", "conf_sets_value"),
    [
        ({"myst_enable_extensions": []}, set(), False),
        (
            {"myst_enable_extensions": ["colon_fence", "tasklist"]},
            {"colon_fence", "tasklist"},
            True,
        ),
    ],
    ids=["override-only-empty", "override-vs-file"],
)
def test_myst_overrides_take_precedence(
    tmp_path: Path,
    overrides: dict,
    expected: set[str],
    *,
    conf_sets_value: bool,
) -> None:
    """Command-line overrides win over Ulwazi's defaults, even against conf.py."""
    # In the override-vs-file case, conf.py sets a conflicting non-empty
    # value: the override must replace it, proving precedence rather than
    # fallback to the file value or a union.
    extra_config = "myst_substitutions = {'product': 'Ulwazi'}"
    if conf_sets_value:
        extra_config += "\nmyst_enable_extensions = ['tasklist']"
    app, output, warnings = _build_myst(
        tmp_path,
        extensions=["ulwazi", "myst_parser"],
        extra_config=extra_config,
        overrides=overrides,
    )
    assert not warnings, f"Unexpected warnings:\n{warnings}"
    assert set(app.config.myst_enable_extensions) == expected
    assert _myst_env_extensions(app) == expected
    failures = _check_myst_rendering(output, expected)
    assert not failures, "; ".join(failures)


@pytest.mark.parametrize(
    "extensions",
    [["ulwazi", "myst_parser"], ["myst_parser", "ulwazi"]],
    ids=["ulwazi-first", "myst-first"],
)
def test_myst_repeated_builds_stay_isolated(
    tmp_path: Path, extensions: list[str]
) -> None:
    """Repeated and incremental builds neither accumulate nor leak defaults.

    Three sequential builds over the same doctrees/output: unset (defaults),
    explicit empty (features stop rendering), unset again (fresh defaults
    return). This also proves the incremental cache is invalidated by the
    setting change, and that one app's collection is never shared or
    mutated in place.
    """
    srcdir = tmp_path / "src"
    srcdir.mkdir(parents=True)
    (srcdir / "index.md").write_text(MYST_INDEX_MD, encoding="utf-8")
    output = tmp_path / "_build"
    doctrees = tmp_path / "_doctrees"

    def build(extra_config: str) -> tuple[Sphinx, str]:
        """Rewrite conf.py and rebuild incrementally over the same doctrees."""
        (srcdir / "conf.py").write_text(
            MYST_CONF_TEMPLATE.format(
                extensions=", ".join(f'"{ext}"' for ext in extensions),
                extra_config=extra_config,
            ),
            encoding="utf-8",
        )
        warnings = io.StringIO()
        with patch_docutils(str(srcdir)), docutils_namespace():
            app = Sphinx(
                srcdir=str(srcdir),
                confdir=str(srcdir),
                outdir=str(output),
                doctreedir=str(doctrees),
                buildername="html",
                status=io.StringIO(),
                warning=warnings,
                warningiserror=True,
            )
            app.build()
        assert app.statuscode == 0, warnings.getvalue()
        return app, warnings.getvalue()

    substitutions = 'myst_substitutions = {"product": "Ulwazi"}'

    # 1. Unset: all three defaults render.
    app1, warnings1 = build(substitutions)
    assert not warnings1, f"Unexpected warnings:\n{warnings1}"
    assert app1.config.myst_enable_extensions == MYST_DEFAULT_EXTENSIONS
    assert not _check_myst_rendering(output, MYST_DEFAULT_EXTENSIONS)

    # 2. Explicit empty: features stop rendering, cache invalidated.
    app2, warnings2 = build(f"{substitutions}\nmyst_enable_extensions = []")
    assert not warnings2, f"Unexpected warnings:\n{warnings2}"
    assert set(app2.config.myst_enable_extensions) == set()
    assert not _check_myst_rendering(output, set())

    # 3. Unset again: fresh defaults return, not the previous explicit value.
    app3, warnings3 = build(substitutions)
    assert not warnings3, f"Unexpected warnings:\n{warnings3}"
    assert app3.config.myst_enable_extensions == MYST_DEFAULT_EXTENSIONS
    assert not _check_myst_rendering(output, MYST_DEFAULT_EXTENSIONS)
    # Mutating one app's collection must not affect the others' defaults.
    app1.config.myst_enable_extensions.add("tasklist")
    assert app3.config.myst_enable_extensions == MYST_DEFAULT_EXTENSIONS


def test_myst_defaults_require_registered_parser(tmp_path: Path) -> None:
    """Without myst_parser in extensions, Ulwazi touches no MyST configuration."""
    # MyST is installed in the test environment but deliberately unregistered.
    # The site is reST-only: a .md source would fail without the parser.
    srcdir = tmp_path / "src"
    srcdir.mkdir(parents=True)
    (srcdir / "conf.py").write_text(
        MYST_CONF_TEMPLATE.format(
            extensions='"ulwazi"',
            extra_config='myst_substitutions = {"product": "Ulwazi"}',
        ),
        encoding="utf-8",
    )
    (srcdir / "index.rst").write_text(
        "Test page\n=========\n\nContent.\n", encoding="utf-8"
    )
    output = tmp_path / "_build"
    warnings = io.StringIO()
    with patch_docutils(str(srcdir)), docutils_namespace():
        app = Sphinx(
            srcdir=str(srcdir),
            confdir=str(srcdir),
            outdir=str(output),
            doctreedir=str(tmp_path / "_doctrees"),
            buildername="html",
            status=io.StringIO(),
            warning=warnings,
            warningiserror=True,
        )
        app.build()
    assert app.statuscode == 0, warnings.getvalue()
    assert not warnings.getvalue(), f"Unexpected warnings:\n{warnings.getvalue()}"
    assert "myst_parser" not in app.extensions
    # No MyST configuration value was registered by Ulwazi.
    assert "myst_enable_extensions" not in app.config.values
    # NOTE: ".md" in app.config.source_suffix is not asserted here: Sphinx
    # shares the class-level source_suffix default dict across in-process
    # applications, so a prior MyST build in the same process leaks the
    # suffix into later apps (an upstream quirk, independent of Ulwazi).
    assert (output / "index.html").is_file()


def test_myst_theme_only_loading_keeps_myst_default(tmp_path: Path) -> None:
    """Theme-only loading does not inject MyST defaults (documented limitation).

    Ulwazi's config-inited hook never fires when "ulwazi" is absent from
    extensions (the theme entry point loads later, during HTML builder
    setup), so MyST keeps its own empty default. This is the documented
    limitation: list "ulwazi" in extensions for the compatibility defaults.
    """
    app, output, warnings = _build_myst(
        tmp_path,
        extensions=["myst_parser"],
        extra_config='myst_substitutions = {"product": "Ulwazi"}',
    )
    assert not warnings, f"Unexpected warnings:\n{warnings}"
    # The theme entry point loads Ulwazi late (after config-inited), so the
    # extension appears in app.extensions only via the theme, not the list.
    assert "ulwazi" not in app.config.extensions
    assert app.config.myst_enable_extensions == set()
    assert _myst_env_extensions(app) == set()
    failures = _check_myst_rendering(output, set())
    assert not failures, "; ".join(failures)


# ---------------------------------------------------------------------------
# Default HTML title (no duplicated "documentation" suffix)
# ---------------------------------------------------------------------------

TITLE_CONF_TEMPLATE = """
project = {project!r}
extensions = ["ulwazi"]
html_theme = "ulwazi"
{extra_config}
"""

TITLE_INDEX_RST = """\
Test page
=========

Content.
"""


def _build_title_site(
    tmp_path: Path,
    project: str,
    extra_config: str = "",
    overrides: dict | None = None,
) -> tuple[Sphinx, Path, str]:
    """Build a tiny reST site and return (app, outdir, warnings).

    The site is generated under ``tmp_path`` so the developer environment,
    the sample docs, and other tests' fixtures are never touched. Builds run
    in-process (with docutils patched) so coverage observes the theme hooks.
    """
    srcdir = tmp_path / "src"
    srcdir.mkdir(parents=True)
    (srcdir / "conf.py").write_text(
        TITLE_CONF_TEMPLATE.format(project=project, extra_config=extra_config),
        encoding="utf-8",
    )
    (srcdir / "index.rst").write_text(TITLE_INDEX_RST, encoding="utf-8")

    output = tmp_path / "_build"
    warnings = io.StringIO()
    with patch_docutils(str(srcdir)), docutils_namespace():
        app = Sphinx(
            srcdir=str(srcdir),
            confdir=str(srcdir),
            outdir=str(output),
            doctreedir=str(tmp_path / "_doctrees"),
            buildername="html",
            confoverrides=overrides,
            status=io.StringIO(),
            warning=warnings,
            warningiserror=True,
        )
        app.build()
    assert app.statuscode == 0, (
        f"Sphinx exited with status {app.statuscode}: {warnings.getvalue()}"
    )
    return app, output, warnings.getvalue()


def _title_text(output: Path) -> str:
    """Return the rendered <title> text of the built index page."""
    path = output / "index.html"
    assert path.is_file(), f"Built page not found: {path}"
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    title = soup.title
    assert title is not None, "Built page has no <title> element"
    return title.get_text(" ", strip=True)


# One representative value per distinct behaviour: the regression baseline
# (a project name already ending in "documentation" must not gain a second
# suffix), the plain default (suffix appended), a set release (joined
# before the suffix), and the suffix rule tied to the project name rather
# than the joined title (a release must not reintroduce the suffix).
@pytest.mark.parametrize(
    ("project", "release", "expected"),
    [
        ("Project documentation", "", "Project documentation"),
        ("Foo", "", "Foo documentation"),
        ("Foo", "2.0", "Foo 2.0 documentation"),
        ("Project documentation", "2.0", "Project documentation 2.0"),
    ],
    ids=["regression-baseline", "plain-default", "with-release", "release-no-suffix"],
)
def test_html_title_default_computed(
    tmp_path: Path, project: str, release: str, expected: str
) -> None:
    """An unset html_title gets a clean default, without duplication.

    Sphinx's own default is ``'{project} {release} documentation'`` with
    ``release`` defaulting to ``''``, which duplicates the word for projects
    named like Canonical Sphinx Stack's ``project = "Project
    documentation"`` (rendering "Project documentation  documentation").
    Ulwazi computes the default from ``project`` (plus ``release`` when set)
    and appends the " documentation" suffix only when the project name does
    not already end with it.
    """
    extra_config = f"release = {release!r}\n" if release else ""
    app, output, warnings = _build_title_site(tmp_path, project, extra_config)
    assert not warnings, f"Unexpected warnings:\n{warnings}"
    assert app.config.html_title == expected
    # The fixture's index page is the root doc, so layout.html withholds
    # the docstitle suffix there (see test_root_title_without_suffix); the
    # bare page heading is all that renders.
    assert _title_text(output) == "Test page"


@pytest.mark.parametrize(
    ("extra_config", "overrides", "expected"),
    [
        ("html_title = 'Custom title'\n", None, "Custom title"),
        ("", {"html_title": "CLI title"}, "CLI title"),
    ],
    ids=["conf-py-explicit", "cli-override"],
)
def test_html_title_explicit_settings_preserved(
    tmp_path: Path,
    extra_config: str,
    overrides: dict | None,
    expected: str,
) -> None:
    """Explicit html_title settings (conf.py or CLI) always win over the default."""
    app, output, warnings = _build_title_site(
        tmp_path,
        "Foo",
        extra_config=extra_config,
        overrides=overrides,
    )
    assert not warnings, f"Unexpected warnings:\n{warnings}"
    assert app.config.html_title == expected
    assert _title_text(output) == "Test page"


# The root page's H1 equals the project name (the Sphinx Stack guide's
# recommended shape), so the docstitle suffix would duplicate the title
# (ulwazi#202): the root page renders no suffix, other pages keep it.
ROOT_TITLE_INDEX_RST = """\
Foo documentation
=================

.. toctree::

   page
"""

ROOT_TITLE_PAGE_RST = """\
Sub page
=========

Content.
"""


def test_root_title_without_suffix(tmp_path: Path) -> None:
    """The root page <title> drops the suffix when its H1 equals the docstitle."""
    srcdir = tmp_path / "src"
    srcdir.mkdir()
    (srcdir / "conf.py").write_text(
        TITLE_CONF_TEMPLATE.format(project="Foo documentation", extra_config=""),
        encoding="utf-8",
    )
    (srcdir / "index.rst").write_text(ROOT_TITLE_INDEX_RST, encoding="utf-8")
    (srcdir / "page.rst").write_text(ROOT_TITLE_PAGE_RST, encoding="utf-8")
    output = tmp_path / "_build"
    warnings = io.StringIO()
    with patch_docutils(str(srcdir)), docutils_namespace():
        app = Sphinx(
            srcdir=str(srcdir),
            confdir=str(srcdir),
            outdir=str(output),
            doctreedir=str(tmp_path / "_doctrees"),
            buildername="html",
            status=io.StringIO(),
            warning=warnings,
            warningiserror=True,
        )
        app.build()
    assert app.statuscode == 0, warnings.getvalue()
    # The root page renders the bare page heading, without duplicated docstitle.
    assert _title_text(output) == "Foo documentation"
    # A subpage keeps the page-heading + docstitle shape.
    sub = BeautifulSoup(
        (output / "page.html").read_text(encoding="utf-8"), "html.parser"
    )
    assert sub.title is not None, "Built subpage has no <title> element"
    assert sub.title.get_text(" ", strip=True) == "Sub page — Foo documentation"


# ---------------------------------------------------------------------------
# Feedback issue body (no duplicated "documentation" suffix)
# ---------------------------------------------------------------------------

FEEDBACK_CONF_TEMPLATE = """
project = {project!r}
extensions = ["ulwazi"]
html_theme = "ulwazi"
html_context = {{
    "feedback": True,
    "github_url": "https://github.com/example/docs",
}}
"""


def _feedback_body(output: Path) -> str:
    """Return the pre-filled issue body of the feedback link."""
    soup = _page(output)
    link = soup.select_one(".p-toc-feedback-block a.p-button--positive")
    assert link is not None, "Feedback link missing from the built page"
    href = link.get("href")
    assert isinstance(href, str), "Feedback link has no href"
    assert "body=" in href, "Feedback link has no body"
    return href.split("body=", 1)[1]


@pytest.mark.parametrize(
    ("project", "expected_phrase"),
    [
        # The regression: a project name ending in "documentation" must not
        # gain a second suffix (ulwazi#203).
        ("X documentation", "facing with X documentation."),
        ("X", "facing with X documentation."),
    ],
    ids=["no-duplication", "suffix-appended"],
)
def test_feedback_body_suffix(
    tmp_path: Path, project: str, expected_phrase: str
) -> None:
    """The feedback issue body appends " documentation" only once."""
    srcdir = tmp_path / "src"
    srcdir.mkdir()
    (srcdir / "conf.py").write_text(
        FEEDBACK_CONF_TEMPLATE.format(project=project), encoding="utf-8"
    )
    (srcdir / "index.rst").write_text("Test\n====\n\nContent.\n", encoding="utf-8")
    output = tmp_path / "_build"
    warnings = io.StringIO()
    with patch_docutils(str(srcdir)), docutils_namespace():
        app = Sphinx(
            srcdir=str(srcdir),
            confdir=str(srcdir),
            outdir=str(output),
            doctreedir=str(tmp_path / "_doctrees"),
            buildername="html",
            status=io.StringIO(),
            warning=warnings,
            warningiserror=True,
        )
        app.build()
    assert app.statuscode == 0, warnings.getvalue()
    assert expected_phrase in _feedback_body(output)
