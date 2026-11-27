"""Tests of the adoption dashboard's static page, CSV export and browser behaviour."""

import csv
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from adoption_samples import write_sample
from tools.adoption.models import DataError
from tools.adoption.render import RenderError, build_css, render_site
from tools.adoption.render.view import (
    build_view,
    relative_time,
    version_sort_key,
)

NOW = dt.datetime(2026, 11, 27, 12, 0, tzinfo=dt.UTC)


@pytest.fixture(scope="module")
def site(tmp_path_factory) -> Path:
    """Render the dashboard from the sample data once (without compiling CSS)."""
    data = tmp_path_factory.mktemp("adoption-data")
    build = tmp_path_factory.mktemp("adoption-build")
    write_sample(data)
    render_site(
        data / "adoption.json",
        data / "history.jsonl",
        build,
        compile_css=False,
        now=NOW,
    )
    return build


@pytest.fixture(scope="module")
def soup(site) -> BeautifulSoup:
    return BeautifulSoup(
        (site / "index.html").read_text(encoding="utf-8"), "html.parser"
    )


def test_statistics_come_before_the_table(soup):
    stats = soup.select_one("section.adopt-stats")
    table = soup.select_one("table#projects")
    assert stats is not None
    assert table is not None
    assert stats.find_next("table") is table  # the stats section precedes the table
    values = {
        tile.select_one(".adopt-tile__label").text: tile.select_one(
            ".adopt-tile__value"
        ).text
        for tile in soup.select(".adopt-tile")
    }
    assert values["RTD projects"] == "56"
    assert values["Sphinx Stack detected"] == "48"
    assert values["On Sphinx Stack 3.0"] == "20"
    assert values["Out of scope"] == "8"
    assert "41.7" in soup.select_one(".adopt-percent").text
    assert "20 of 48" in soup.select_one(".adopt-headline__text").text


def test_every_project_has_the_requested_information(soup):
    rows = soup.select("tr.adopt-row")
    assert len(rows) == 56
    cells = {row["id"]: row.select("td") for row in rows}
    project, repo, stack, ulwazi, built, _ = cells["row-juju-docs"]
    assert (
        project.select_one("a.adopt-name")["href"]
        == "https://documentation.ubuntu.com/juju-docs/"
    )
    assert (
        repo.select_one("a.adopt-repo")["href"]
        == "https://github.com/canonical/juju-docs"
    )
    assert repo.select_one("a.adopt-repo").text == "canonical/juju-docs"
    assert repo.select_one("a.adopt-path").text == "docs/"
    assert stack.select_one(".adopt-chip").text == "3.0"
    assert "corrected" in stack.text
    assert ulwazi.select_one(".adopt-chip").text == "1.0.2"
    assert built.select_one("time")["datetime"].startswith("2026-11-24")


def test_n_a_is_shown_when_there_is_no_ulwazi(soup):
    plain = soup.select_one("tr#row-landscape")
    chips = [chip.text for chip in plain.select(".adopt-chip")]
    assert chips == ["1.6", "N/A"]
    stackless = soup.select_one("tr#row-custom-sphinx")
    assert [chip.text for chip in stackless.select(".adopt-chip")] == ["N/A", "N/A"]
    pending = soup.select_one("tr#row-ops")
    assert [chip.text for chip in pending.select(".adopt-chip")] == ["3.0", "N/A"]
    assert "Pending deploy" in pending.text


def test_ulwazi_version_notations(soup):
    def ulwazi(slug: str) -> str:
        return soup.select_one(f"tr#row-{slug} td:nth-of-type(4) .adopt-chip").text

    assert ulwazi("charmcraft") == "1.0.3"
    assert ulwazi("lxd") == "1.0.1\u20131.0.2"
    assert ulwazi("ubuntu-pro-client") == "\u2248 1.0.3"
    assert ulwazi("dev-build-docs") == "dev"


def test_out_of_scope_rows_are_explained(soup):
    reasons = {
        slug: soup.select_one(f"tr#row-{slug} .adopt-reason").text
        for slug in (
            "custom-sphinx",
            "old-project",
            "internal-notes",
            "launchpad-docs",
            "broken-repo",
        )
    }
    assert reasons == {
        "custom-sphinx": "Not Sphinx Stack",
        "old-project": "Archived",
        "internal-notes": "Opted out",
        "launchpad-docs": "Unsupported host",
        "broken-repo": "Error",
    }
    assert "is-out" in soup.select_one("tr#row-old-project")["class"]
    assert soup.select_one("tr#row-juju-docs .adopt-reason") is None


def test_evidence_explains_the_corrected_version(soup):
    detail = soup.select_one("tr#ev-juju-docs")
    text = detail.get_text(" ", strip=True)
    assert "Version file says 2.0" in text
    assert "known upstream problem" in text
    assert "ulwazi instead of canonical-sphinx" in text
    assert detail["data-for"] == "row-juju-docs"


def test_markup_is_accessible_without_javascript(soup):
    assert soup.select_one("table#projects caption")
    assert all(
        th.get("scope") == "col" for th in soup.select("table#projects thead th")
    )
    assert soup.select_one("a.adopt-skip")["href"] == "#projects"
    assert soup.select_one("#result-count")["aria-live"] == "polite"
    # Controls that need JavaScript stay hidden until the script marks the page.
    assert all(
        "js-only" in element["class"]
        for element in soup.select("#filter-q, label.adopt-field, .adopt-expand")
    )
    # Every expandable row names the project it opens.
    for button in soup.select(".adopt-expand"):
        assert button["aria-controls"].startswith("ev-")
        assert button.select_one(".adopt-visually-hidden").text.startswith(
            "Show details for "
        )
    assert [h.name for h in soup.select("h1, h2")][0] == "h1"


def test_filters_offer_every_version(soup):
    options = [o["value"] for o in soup.select("#filter-stack option")]
    assert options[0] == ""
    assert {"3.0", "2.0", "1.6", "< 1.0"} <= set(options)
    assert "none" in options


def test_trend_and_methodology_sections(soup):
    assert soup.select_one(".adopt-trend svg polyline")
    assert soup.select_one(".adopt-mini-table")
    method = soup.select_one(".adopt-method").text
    assert "corrected" in method
    assert "Pending deploy" in method


def test_trend_waits_for_enough_history(tmp_path):
    write_sample(tmp_path)
    (tmp_path / "history.jsonl").write_text(
        json.dumps(
            {
                "date": "2026-11-27",
                "total": 1,
                "sphinx_stack": 1,
                "latest": 1,
                "ulwazi": 1,
                "out_of_scope": 0,
            }
        )
        + "\n"
    )
    build = tmp_path / "build"
    render_site(
        tmp_path / "adoption.json",
        tmp_path / "history.jsonl",
        build,
        compile_css=False,
        now=NOW,
    )
    assert "second daily run" in (build / "index.html").read_text()


def test_exports_match_the_page(site, soup):
    exported = json.loads((site / "adoption.json").read_text())
    assert len(exported["projects"]) == len(soup.select("tr.adopt-row"))
    with (site / "projects.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 56
    juju = next(row for row in rows if row["slug"] == "juju-docs")
    assert (
        juju["sphinx_stack"],
        juju["sphinx_stack_declared"],
        juju["sphinx_stack_corrected"],
    ) == ("3.0", "2.0", "yes")
    assert juju["ulwazi"] == "1.0.2"
    assert juju["repository_url"] == "https://github.com/canonical/juju-docs"
    plain = next(row for row in rows if row["slug"] == "landscape")
    assert plain["ulwazi"] == "N/A"


def test_page_loads_only_local_assets(soup):
    assert soup.select_one("link[rel=stylesheet]")["href"] == "dashboard.css"
    assert [s["src"] for s in soup.select("script[src]")] == ["dashboard.js"]


def test_html_is_escaped(tmp_path):
    write_sample(tmp_path)
    data = json.loads((tmp_path / "adoption.json").read_text())
    data["projects"][0]["name"] = "<script>alert(1)</script>"
    (tmp_path / "adoption.json").write_text(json.dumps(data))
    build = tmp_path / "build"
    render_site(
        tmp_path / "adoption.json",
        tmp_path / "history.jsonl",
        build,
        compile_css=False,
        now=NOW,
    )
    html = (build / "index.html").read_text()
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_render_rejects_other_schema_versions(tmp_path):
    write_sample(tmp_path)
    data = json.loads((tmp_path / "adoption.json").read_text())
    data["schema_version"] = 99
    (tmp_path / "adoption.json").write_text(json.dumps(data))
    with pytest.raises(DataError, match="schema_version"):
        render_site(
            tmp_path / "adoption.json",
            tmp_path / "history.jsonl",
            tmp_path / "build",
            compile_css=False,
        )
    with pytest.raises(DataError, match="does not exist"):
        render_site(
            tmp_path / "missing.json",
            tmp_path / "history.jsonl",
            tmp_path / "build",
            compile_css=False,
        )


def test_relative_time_and_sort_keys():
    assert relative_time(None, NOW) == "\u2014"
    assert relative_time(NOW, NOW) == "today"
    assert relative_time(NOW - dt.timedelta(days=1), NOW) == "yesterday"
    assert relative_time(NOW - dt.timedelta(days=12), NOW) == "12 days ago"
    assert relative_time(NOW - dt.timedelta(days=65), NOW) == "2 months ago"
    assert relative_time(NOW - dt.timedelta(days=400), NOW) == "1 year ago"
    assert (
        version_sort_key("1.0.10") > version_sort_key("1.0.9") > version_sort_key("1.0")
    )
    assert version_sort_key("1.0.1\u20131.0.2") == version_sort_key("1.0.1")
    assert version_sort_key(None) == ""


def test_view_handles_a_dashboard_without_deltas_or_history(tmp_path):
    write_sample(tmp_path)
    data = json.loads((tmp_path / "adoption.json").read_text())
    data["summary"].pop("deltas")
    view = build_view(data, [], now=NOW)
    assert view["trend"] is None
    assert all(tile["delta"] == "" for tile in view["tiles"])
    assert view["generated"].startswith("27 Nov 2026")


def test_css_compilation_error_is_reported(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.adoption.render.SCSS_SOURCE", tmp_path / "missing.scss")
    with pytest.raises(RenderError, match="Sass"):
        build_css(tmp_path / "out.css")


# ---------------------------------------------------------------------------
# Browser checks (slow): layout above the fold, interaction and contrast
# ---------------------------------------------------------------------------

VIEWPORTS = {"laptop": (1366, 768, 5), "desktop": (1440, 900, 8)}


@pytest.fixture(scope="module")
def styled_site(tmp_path_factory) -> Path:
    data = tmp_path_factory.mktemp("adoption-styled-data")
    build = tmp_path_factory.mktemp("adoption-styled-build")
    write_sample(data)
    render_site(data / "adoption.json", data / "history.jsonl", build, now=NOW)
    return build


@pytest.fixture(scope="module")
def browser():
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"], check=True
    )
    with sync_playwright() as playwright:
        chromium = playwright.chromium.launch()
        yield chromium
        chromium.close()


@pytest.mark.slow
@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_table_is_visible_on_the_first_screen(browser, styled_site, viewport):
    width, height, minimum_rows = VIEWPORTS[viewport]
    page = browser.new_page(viewport={"width": width, "height": height})
    page.goto((styled_site / "index.html").as_uri())
    measured = page.evaluate(
        """() => {
            const head = document.querySelector('#projects thead').getBoundingClientRect();
            const rows = [...document.querySelectorAll('tr.adopt-row')]
              .map((row) => row.getBoundingClientRect());
            return {
              headBottom: head.bottom,
              visibleRows: rows.filter((r) => r.top >= head.bottom && r.bottom <= innerHeight).length,
              overflow: document.documentElement.scrollWidth - innerWidth,
            };
        }"""
    )
    page.close()
    assert measured["headBottom"] < height * 0.5, (
        "statistics take too much of the first screen"
    )
    assert measured["visibleRows"] >= minimum_rows
    assert measured["overflow"] <= 0


@pytest.mark.slow
def test_mobile_layout_has_no_horizontal_scroll(browser, styled_site):
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.goto((styled_site / "index.html").as_uri())
    measured = page.evaluate(
        """() => ({
            overflow: document.documentElement.scrollWidth - innerWidth,
            firstRowTop: document.querySelector('tr.adopt-row').getBoundingClientRect().top,
            headerHidden: getComputedStyle(document.querySelector('#projects thead')).position === 'absolute',
        })"""
    )
    page.close()
    assert measured["overflow"] <= 0
    assert measured["firstRowTop"] < 844
    assert measured["headerHidden"]


@pytest.mark.slow
def test_dashboard_interaction_and_contrast(browser, styled_site):
    from axe_playwright_python.sync_playwright import Axe  # noqa: PLC0415

    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto((styled_site / "index.html").as_uri())

    def visible_rows() -> int:
        return page.locator("tr.adopt-row:not([hidden])").count()

    assert visible_rows() == 56
    page.click('.adopt-tile[data-preset="out"]')
    assert visible_rows() == 8
    assert (
        page.get_attribute('.adopt-tile[data-preset="out"]', "aria-pressed") == "true"
    )
    assert "scope=out" in page.url
    page.click("#filter-reset")
    page.fill("#filter-q", "juju")
    assert visible_rows() == 1
    assert "Showing 1 of 56" in page.inner_text("#result-count")
    page.fill("#filter-q", "no such project")
    assert page.is_visible("#empty-state")
    page.click("#filter-reset")
    page.select_option("#filter-ulwazi", "pending")
    assert visible_rows() == 1
    page.click("#filter-reset")

    page.click("th[data-key='stack'] button")
    first = page.locator(
        "tr.adopt-row:not([hidden]) td:nth-of-type(3) .adopt-chip"
    ).first.inner_text()
    assert first == "< 1.0"  # ascending: the oldest first, N/A last
    page.click("th[data-key='stack'] button")
    assert page.get_attribute("th[data-key='stack']", "aria-sort") == "descending"

    page.locator("tr.adopt-row:not([hidden]) .adopt-expand").first.click()
    assert page.locator("tr.adopt-evidence.is-open").count() == 1
    assert (
        page.get_attribute(
            "tr.adopt-row:not([hidden]) .adopt-expand >> nth=0", "aria-expanded"
        )
        == "true"
    )

    violations = []
    axe = Axe()
    for dark in (False, True):
        if dark:
            page.click("#theme-toggle")
        page.wait_for_timeout(300)
        results = axe.run(
            page,
            options={
                "runOnly": {"type": "rule", "values": ["color-contrast"]},
                "resultTypes": ["violations"],
            },
        )
        violations.extend(
            f"{'dark' if dark else 'light'}: {node['target']} {node.get('failureSummary', '')}"
            for violation in results.response["violations"]
            for node in violation["nodes"]
        )
    page.close()
    assert not violations, "\n".join(violations[:10])
