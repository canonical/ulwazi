"""Fresh, shared Sphinx build for tests of Ulwazi's rendered HTML."""

import json
import os
from collections import defaultdict
from io import StringIO
from pathlib import Path

import pytest
import yaml
from bs4 import BeautifulSoup
from sphinx.application import Sphinx
from sphinx.util.docutils import docutils_namespace, patch_docutils

DOCS = Path(__file__).resolve().parents[1] / "docs"
FEATURES_MANIFEST = Path(__file__).parent / "features.yaml"
FEATURE_STATE = Path("results/feature-coverage.json")

# Primary reporting category from docs/content/testing-strategy.md. Tests still
# run independently (including each parameter and its fixtures); only the CLI
# recap is grouped. A few checks also cover other categories, documented there.
TEST_CATEGORIES = {
    "test_preview_theme.py": "1 Build process",
    "test_pdf_generation.py": "1 Build process",
    "test_smoke.py": "2 Smoke",
    "test_assets_structure.py": "3 Assets and structure",
    "test_seo_metadata.py": "3 Assets and structure",
    "test_layout_smoke.py": "3 Assets and structure",
    "test_features.py": "4 Features and regressions",
    "test_config_robustness.py": "4 Features and regressions",
    "test_scss_propagation.py": "4 Features and regressions",
    "test_notfound_bundling.py": "5 Extension compatibility",
    "test_extension_compatibility.py": "5 Extension compatibility",
    "test_structured_toc.py": "5 Extension compatibility",
    "test_responsive.py": "6 Responsive layout",
    "test_notfound_prefix.py": "7 Python and environments",
    "test_python_versions.py": "7 Python and environments",
    "test_code_quality.py": "8 Code quality",
    "test_accessibility.py": "9 Accessibility",
    "test_coverage_metrics.py": "Test infrastructure",
    "test_test_reporting.py": "Test infrastructure",
}
SLOW_CATEGORY_OVERRIDES = {"test_layout_smoke.py": "6 Responsive layout"}
SELECTED_TESTS: dict[str, tuple[str, str]] = {}


def _category(nodeid: str, *, slow: bool) -> tuple[str, str]:
    """Give a selected test one primary category and its actual pytest tier."""
    filename = Path(nodeid.split("::", 1)[0]).name
    return (
        SLOW_CATEGORY_OVERRIDES.get(
            filename, TEST_CATEGORIES.get(filename, "Other tests")
        )
        if slow
        else TEST_CATEGORIES.get(filename, "Other tests"),
        "slow" if slow else "fast",
    )


def pytest_collection_finish(session) -> None:
    """Remember selected items and announce the start of local test execution."""
    SELECTED_TESTS.clear()
    SELECTED_TESTS.update(
        (
            item.nodeid,
            _category(item.nodeid, slow=item.get_closest_marker("slow") is not None),
        )
        for item in session.items
    )
    if session.items and not session.config.option.collectonly:
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        if reporter is not None and session.config.option.verbose <= 0:
            reporter.write_line(f"Running {len(session.items)} selected tests...")


@pytest.hookimpl(optionalhook=True)
def pytest_xdist_node_collection_finished(ids) -> None:
    """The xdist controller sees node IDs rather than collected Item objects."""
    for nodeid in ids:
        SELECTED_TESTS.setdefault(nodeid, _category(nodeid, slow=False))


def pytest_runtest_logreport(report) -> None:
    """Recover slow markers from worker reports when running with xdist."""
    if report.nodeid in SELECTED_TESTS:
        SELECTED_TESTS[report.nodeid] = _category(
            report.nodeid, slow="slow" in report.keywords
        )


def _category_results(selected, stats):
    """Group registered suites and show every unregistered test by node ID."""
    groups: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    unregistered: dict[str, str] = {}
    for nodeid, (name, tier) in selected.items():
        if name == "Other tests":
            unregistered[nodeid] = tier
        else:
            groups[name][tier].add(nodeid)

    def reported(category: str) -> set[str]:
        return {report.nodeid for report in stats.get(category, [])}

    passed = {
        report.nodeid
        for report in stats.get("passed", [])
        if report.when == "call" and not hasattr(report, "wasxfail")
    }
    failed = reported("failed") | reported("error") | reported("xpassed")
    skipped = reported("skipped") | reported("xfailed")

    def outcome(nodeids: set[str]) -> tuple[str, int, str]:
        """Count call-phase passes, failures, skips and unfinished cases."""
        good = len(nodeids & (passed - failed - skipped))
        bad = len(nodeids & failed)
        omitted = len(nodeids & (skipped - failed))
        remaining = len(nodeids) - good - bad - omitted
        state = "FAILED" if bad else "PASSED" if good == len(nodeids) else "INCOMPLETE"
        details = ", ".join(
            f"{count} {label}"
            for count, label in (
                (bad, "failed"),
                (omitted, "skipped"),
                (remaining, "not run"),
            )
            if count
        )
        return state, good, details

    for name, tiers in sorted(groups.items()):
        parts = []
        states = []
        for tier in ("fast", "slow"):
            if tier not in tiers:
                continue
            nodeids = tiers[tier]
            state, good, details = outcome(nodeids)
            suffix = f"; {details}" if details else ""
            parts.append(f"{tier} {state} ({good}/{len(nodeids)} passed{suffix})")
            states.append(state)
        overall = (
            "FAILED"
            if "FAILED" in states
            else "INCOMPLETE"
            if "INCOMPLETE" in states
            else "PASSED"
        )
        yield overall, f"{name}: {' · '.join(parts)}"

    for nodeid, tier in sorted(unregistered.items()):
        state, _, details = outcome({nodeid})
        suffix = f" ({details})" if details else ""
        yield state, f"{state} {nodeid} [{tier}]{suffix}"


@pytest.fixture
def isolated_sphinx_build():
    """Restore docutils registrations after an in-process fixture build."""
    with patch_docutils(str(DOCS)), docutils_namespace():
        yield


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
        with patch_docutils(str(DOCS)), docutils_namespace():
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


def pytest_terminal_summary(config, terminalreporter) -> None:
    """Recap selected test categories; report feature checks on coverage runs."""
    if not config.option.collectonly and config.option.verbose <= 0:
        results = list(_category_results(SELECTED_TESTS, terminalreporter.stats))
        if results:
            terminalreporter.section("test results (selected cases)")
        for state, line in results:
            terminalreporter.write_line(
                line,
                **(
                    {"green": True}
                    if state == "PASSED"
                    else {"red": True}
                    if state == "FAILED"
                    else {"yellow": True}
                ),
            )

    if (
        os.environ.get("ULWAZI_COVERAGE_REPORT") != "1"
        or not FEATURES_MANIFEST.is_file()
    ):
        return
    passed = {report.nodeid for report in terminalreporter.stats.get("passed", [])}
    manifest = yaml.safe_load(FEATURES_MANIFEST.read_text(encoding="utf-8"))
    covered, missing = [], []
    for group in manifest.values():
        for feature in group:
            checks = feature.get("checks", [])
            if checks and all(check in passed for check in checks):
                covered.append(feature["name"])
            else:
                missing.append(feature["name"])
    total = len(covered) + len(missing)
    if not total:
        return
    percent = round(100 * len(covered) / total)
    terminalreporter.section("mapped feature checks")
    terminalreporter.write_line(
        f"Feature checks: {len(covered)}/{total} mapped features ({percent}%)"
    )
    if missing:
        terminalreporter.write_line("Unchecked features: " + ", ".join(missing))
    FEATURE_STATE.parent.mkdir(parents=True, exist_ok=True)
    FEATURE_STATE.write_text(
        json.dumps({"covered": covered, "missing": missing}, indent=2),
        encoding="utf-8",
    )
