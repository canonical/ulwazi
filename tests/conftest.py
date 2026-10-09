"""Fresh, shared Sphinx build for tests of Ulwazi's rendered HTML."""

import json
import os
import time
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
    "test_preview_theme.py": "1. Build process",
    "test_pdf_generation.py": "1. Build process",
    "test_smoke.py": "2. Smoke",
    "test_assets_structure.py": "3. Assets and structure",
    "test_seo_metadata.py": "3. Assets and structure",
    "test_layout_smoke.py": "3. Assets and structure",
    "test_features.py": "4. Features and regressions",
    "test_config_robustness.py": "4. Features and regressions",
    "test_scss_propagation.py": "4. Features and regressions",
    "test_notfound_bundling.py": "5. Extension compatibility",
    "test_extension_compatibility.py": "5. Extension compatibility",
    "test_structured_toc.py": "5. Extension compatibility",
    "test_responsive.py": "6. Responsive layout",
    "test_notfound_prefix.py": "7. Python and environments",
    "test_python_versions.py": "7. Python and environments",
    "test_code_quality.py": "8. Code quality",
    "test_accessibility.py": "9. Accessibility",
    "test_coverage_metrics.py": "Test infrastructure",
    "test_test_reporting.py": "Test infrastructure",
}
SLOW_CATEGORY_OVERRIDES = {"test_layout_smoke.py": "6. Responsive layout"}
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


DURATIONS_CACHE_KEY = "ulwazi/test-durations"


def _format_seconds(seconds: float) -> str:
    seconds = max(1, round(seconds))
    return f"{seconds}s" if seconds < 60 else f"{seconds // 60}m {seconds % 60:02d}s"


class LiveProgress:
    """Show `` 45% (~12s left)`` after pytest's progress dots in a terminal.

    The estimate adds up each remaining test's duration from the previous run
    (stored in the pytest cache), falling back to this run's average. The status
    is drawn between save/restore-cursor escapes, so pytest's next dot or final
    ``[100%]`` overwrites it. Disable with ``-p no:ulwazi-live-progress``.
    """

    def __init__(self, config) -> None:
        self.config = config
        # No cache with `-p no:cacheprovider`: estimate from this run only.
        self.cache = getattr(config, "cache", None)
        self.history: dict[str, float] = (
            self.cache.get(DURATIONS_CACHE_KEY, {}) if self.cache else {}
        )
        self.durations: dict[str, float] = defaultdict(float)
        self.pending: set[str] = set()
        self.done = 0
        self.writer = None
        self.drawn = False

    def estimate(self) -> float | None:
        """Seconds left: previous durations, else the average so far."""
        known = self.durations or self.history
        fallback = sum(known.values()) / len(known) if known else None
        remaining = [self.history.get(nodeid, fallback) for nodeid in self.pending]
        return None if None in remaining else sum(remaining)  # type: ignore[arg-type]

    def status(self) -> tuple[str, str]:
        """Percentage and optional time-left text, kept separate for styling."""
        percent = 100 * self.done // (self.done + len(self.pending))
        eta = self.estimate()
        return f" {percent}%", "" if eta is None else f" (~{_format_seconds(eta)} left)"

    def _draw(self) -> None:
        writer = self.writer
        if writer is None or not self.pending:
            return
        percent, eta = self.status()
        room = writer.fullwidth - writer.width_of_current_line - 1
        if len(percent + eta) > room:
            eta = ""
        if len(percent) > room:
            return
        if writer.hasmarkup:
            percent = f"\x1b[36m{percent}\x1b[0m"
            eta = f"\x1b[2m{eta}\x1b[0m" if eta else ""
        writer._file.write(f"\x1b7\x1b[K{percent}{eta}\x1b8")
        writer.flush()
        self.drawn = True

    def _clear(self) -> None:
        if self.drawn and self.writer is not None:
            self.writer._file.write("\x1b[K")
            self.writer.flush()
            self.drawn = False

    def pytest_collection_finish(self, session) -> None:
        self.pending = {item.nodeid for item in session.items}
        reporter = self.config.pluginmanager.get_plugin("terminalreporter")
        if (
            reporter is not None
            and reporter.isatty()
            and os.environ.get("TERM") != "dumb"
            and not self.config.option.collectonly
        ):
            self.writer = reporter._tw

    @pytest.hookimpl(trylast=True)
    def pytest_runtest_logstart(self, nodeid) -> None:
        if not self.done:
            self._draw()  # 0% and the estimate while the first test runs

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_logreport(self, report) -> None:
        self.durations[report.nodeid] += report.duration
        if report.when == "call" or not report.passed:
            self._clear()  # pytest is about to print this test's letter

    @pytest.hookimpl(trylast=True)
    def pytest_runtest_logfinish(self, nodeid) -> None:
        self.done += 1
        self.pending.discard(nodeid)
        self._draw()

    def pytest_keyboard_interrupt(self) -> None:
        self._clear()

    def pytest_sessionfinish(self) -> None:
        if self.cache is not None and self.durations:
            self.cache.set(DURATIONS_CACHE_KEY, {**self.history, **self.durations})


def pytest_configure(config) -> None:
    """Add live progress for plain local runs; xdist and -v print their own."""
    if (
        config.option.verbose <= 0
        and not hasattr(config, "workerinput")
        and not getattr(config.option, "numprocesses", None)
    ):
        config.pluginmanager.register(LiveProgress(config), "ulwazi-live-progress")


# Recap styling (pytest TerminalWriter markup; dropped without a colour TTY or
# with NO_COLOR). Green is reserved for passing results; structure is muted.
STATE_STYLE = {
    "PASSED": {"green": True, "bold": True},
    "FAILED": {"red": True, "bold": True},
    "INCOMPLETE": {"yellow": True, "bold": True},
}
PASSED_COUNT_STYLE = {"green": True}
DETAIL_STYLE = {
    "failed": {"red": True},
    "skipped": {"yellow": True},
    "not run": {"yellow": True},
}
CATEGORY_STYLE = {"bold": True}
TIER_STYLE = {"cyan": True}
MUTED_STYLE = {"light": True}
PLAIN: dict[str, bool] = {}

Segment = tuple[str, dict[str, bool]]


def _tier_segments(tier, state, good, total, details) -> list[Segment]:
    """Render ``Fast(7/7): PASSED`` or ``Slow(1/3): FAILED (1 failed, ...)``."""
    segments: list[Segment] = [
        (tier.capitalize(), TIER_STYLE),
        ("(", MUTED_STYLE),
        (f"{good}/{total}", PASSED_COUNT_STYLE if state == "PASSED" else PLAIN),
        (")", MUTED_STYLE),
        (": ", PLAIN),
        (state, STATE_STYLE[state]),
    ]
    if details:
        segments.append((" (", MUTED_STYLE))
        for index, (count, label) in enumerate(details):
            if index:
                segments.append((", ", MUTED_STYLE))
            segments.append((f"{count} {label}", DETAIL_STYLE[label]))
        segments.append((")", MUTED_STYLE))
    return segments


def _category_recap(selected, stats):
    """Group registered suites and show every unregistered test by node ID.

    Yields ``(overall state, segments)``, where each segment is ``(text,
    markup)`` so the terminal summary can colour parts of one line.
    """
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

    def outcome(nodeids: set[str]) -> tuple[str, int, list[tuple[int, str]]]:
        """Count call-phase passes, failures, skips and unfinished cases."""
        good = len(nodeids & (passed - failed - skipped))
        bad = len(nodeids & failed)
        omitted = len(nodeids & (skipped - failed))
        remaining = len(nodeids) - good - bad - omitted
        state = "FAILED" if bad else "PASSED" if good == len(nodeids) else "INCOMPLETE"
        details = [
            (count, label)
            for count, label in (
                (bad, "failed"),
                (omitted, "skipped"),
                (remaining, "not run"),
            )
            if count
        ]
        return state, good, details

    for name, tiers in sorted(groups.items()):
        segments: list[Segment] = [(name, CATEGORY_STYLE), (": ", PLAIN)]
        states = []
        for tier in ("fast", "slow"):
            if tier not in tiers:
                continue
            nodeids = tiers[tier]
            state, good, details = outcome(nodeids)
            if states:
                segments.append((" · ", MUTED_STYLE))
            segments += _tier_segments(tier, state, good, len(nodeids), details)
            states.append(state)
        overall = (
            "FAILED"
            if "FAILED" in states
            else "INCOMPLETE"
            if "INCOMPLETE" in states
            else "PASSED"
        )
        yield overall, segments

    for nodeid, tier in sorted(unregistered.items()):
        state, good, details = outcome({nodeid})
        yield (
            state,
            [
                (nodeid, PLAIN),
                (": ", PLAIN),
                *_tier_segments(tier, state, good, 1, details),
            ],
        )


def _category_results(selected, stats):
    """Plain-text recap lines, as they appear without colour."""
    for state, segments in _category_recap(selected, stats):
        yield state, "".join(text for text, _ in segments)


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
        results = list(_category_recap(SELECTED_TESTS, terminalreporter.stats))
        if results:
            terminalreporter.section("test results (selected cases)")
        for _, segments in results:
            terminalreporter.ensure_newline()
            for text, markup in segments:
                terminalreporter.write(text, **markup)
            terminalreporter.write("\n")

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
