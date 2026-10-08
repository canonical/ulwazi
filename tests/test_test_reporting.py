"""Keep the compact category recap honest without coupling test outcomes."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from conftest import _category, _category_results

pytest_plugins = ("pytester",)


def _report(nodeid: str, when: str = "call", **attributes):
    return SimpleNamespace(nodeid=nodeid, when=when, **attributes)


def test_reporting_category_matches_test_and_tier():
    """Layout checks split by tier; new suites remain unregistered."""
    layout = "tests/test_layout_smoke.py::test_article_inside_docs_main"
    assert _category(layout, slow=False) == ("3 Assets and structure", "fast")
    assert _category(layout, slow=True) == ("6 Responsive layout", "slow")
    assert _category("tests/test_new_suite.py::test_new", slow=False) == (
        "Other tests",
        "fast",
    )


def test_category_recap_mixed_outcomes():
    """Failures, fixture errors, skips, and interrupted items stay visible."""
    selected = {
        f"tests/test_smoke.py::{case}": ("2 Smoke", "fast")
        for case in ("pass", "failure", "error", "skip", "unfinished")
    }
    stats = {
        "passed": [_report("tests/test_smoke.py::pass")],
        "failed": [_report("tests/test_smoke.py::failure")],
        "error": [_report("tests/test_smoke.py::error", "setup")],
        "skipped": [_report("tests/test_smoke.py::skip", "setup")],
    }

    assert list(_category_results(selected, stats)) == [
        (
            "FAILED",
            "2 Smoke: fast FAILED (1/5 passed; 2 failed, 1 skipped, 1 not run)",
        )
    ]


def test_category_recap_separates_tiers_and_does_not_count_xfails_as_passes():
    """Only ordinary call-phase successes can make a tier green."""
    selected = {
        "tests/test_features.py::fast": ("4 Features and regressions", "fast"),
        "tests/test_features.py::slow": ("4 Features and regressions", "slow"),
    }
    stats = {
        "passed": [
            _report("tests/test_features.py::fast", "setup"),
            _report("tests/test_features.py::fast"),
        ],
        "xfailed": [_report("tests/test_features.py::slow", wasxfail="expected")],
    }

    assert list(_category_results(selected, stats)) == [
        (
            "INCOMPLETE",
            (
                "4 Features and regressions: fast PASSED (1/1 passed) · "
                "slow INCOMPLETE (0/1 passed; 1 skipped)"
            ),
        ),
    ]


def test_category_recap_combines_successful_tiers():
    """Both selected tiers appear on one line, even with multiple cases."""
    selected = {
        "tests/test_features.py::first": ("4 Features and regressions", "fast"),
        "tests/test_features.py::second": ("4 Features and regressions", "fast"),
        "tests/test_features.py::browser": ("4 Features and regressions", "slow"),
    }
    stats = {"passed": [_report(nodeid) for nodeid in selected]}

    assert list(_category_results(selected, stats)) == [
        (
            "PASSED",
            (
                "4 Features and regressions: fast PASSED (2/2 passed) · "
                "slow PASSED (1/1 passed)"
            ),
        )
    ]


def test_category_recap_failure_in_one_tier_keeps_other_tier_green():
    """A failure must not erase the independently passing fast tier."""
    fast = "tests/test_features.py::fast"
    slow = "tests/test_features.py::slow"
    selected = {
        fast: ("4 Features and regressions", "fast"),
        slow: ("4 Features and regressions", "slow"),
    }
    stats = {"passed": [_report(fast)], "failed": [_report(slow)]}

    assert list(_category_results(selected, stats)) == [
        (
            "FAILED",
            (
                "4 Features and regressions: fast PASSED (1/1 passed) · "
                "slow FAILED (0/1 passed; 1 failed)"
            ),
        )
    ]


def test_unregistered_cases_report_individual_ids_and_outcomes():
    """A naively added file exposes each case, including parameter IDs."""
    passed = "tests/test_new_suite.py::test_simple"
    failed = "tests/test_new_suite.py::test_parameterized[bad]"
    skipped = "tests/test_new_suite.py::test_skipped"
    unfinished = "tests/test_new_suite.py::test_unfinished"
    selected = {
        passed: _category(passed, slow=False),
        failed: _category(failed, slow=False),
        skipped: _category(skipped, slow=True),
        unfinished: _category(unfinished, slow=False),
    }
    stats = {
        "passed": [_report(passed)],
        "failed": [_report(failed)],
        "skipped": [_report(skipped, "setup")],
    }

    assert list(_category_results(selected, stats)) == [
        ("FAILED", f"FAILED {failed} [fast] (1 failed)"),
        ("PASSED", f"PASSED {passed} [fast]"),
        ("INCOMPLETE", f"INCOMPLETE {skipped} [slow] (1 skipped)"),
        ("INCOMPLETE", f"INCOMPLETE {unfinished} [fast] (1 not run)"),
    ]


def test_unregistered_cases_do_not_change_registered_category_count():
    """One unmapped case must not conceal or inflate registered summaries."""
    registered = "tests/test_smoke.py::test_smoke_fast"
    unregistered = "tests/test_new_suite.py::test_simple"
    selected = {
        registered: _category(registered, slow=False),
        unregistered: _category(unregistered, slow=False),
    }
    stats = {"passed": [_report(registered), _report(unregistered)]}

    assert list(_category_results(selected, stats)) == [
        ("PASSED", "2 Smoke: fast PASSED (1/1 passed)"),
        ("PASSED", f"PASSED {unregistered} [fast]"),
    ]


def test_new_file_appears_by_name_in_actual_pytest_output(pytester: pytest.Pytester):
    """A new, unregistered test file needs no bookkeeping for useful output."""
    pytester.makeconftest(Path(__file__).with_name("conftest.py").read_text())
    pytester.makepyfile(
        test_new_suite="""
        import pytest

        def test_simple():
            assert True

        @pytest.mark.parametrize("value", [0, 1])
        def test_parameterized(value):
            assert value == 0

        def test_skipped():
            pytest.skip("not available")
        """
    )

    result = pytester.runpytest_subprocess("-q")

    result.assert_outcomes(passed=2, failed=1, skipped=1)
    lines = result.stdout.str().splitlines()
    assert "PASSED test_new_suite.py::test_parameterized[0] [fast]" in lines
    assert "FAILED test_new_suite.py::test_parameterized[1] [fast] (1 failed)" in lines
    assert "PASSED test_new_suite.py::test_simple [fast]" in lines
    assert "INCOMPLETE test_new_suite.py::test_skipped [fast] (1 skipped)" in lines
