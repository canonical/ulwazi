"""Regressions for the three coverage summaries and V8 range conversion."""

import json

import pytest

from coverage_summary import summary
from js_coverage import JSCoverageRecorder, _covered_lines
from pr_coverage import compare


def test_nested_v8_ranges_do_not_count_unexecuted_lines():
    """A zero-count inner function overrides its executed outer script."""
    source = "const value = 1;\nfunction idle() {\n  return 0;\n}\n"
    ranges = [
        {"startOffset": 0, "endOffset": len(source), "count": 1},
        {
            "startOffset": source.index("function idle"),
            "endOffset": source.index("}\n") + 1,
            "count": 0,
        },
    ]
    assert _covered_lines(source, ranges) == {1}


def test_v8_ranges_use_utf16_offsets_and_skip_comments():
    """An emoji before a code line must not shift its V8 offset."""
    source = "// 😀\n/* documentation */\nconst result = true;\n"
    start = len("// 😀\n/* documentation */\n".encode("utf-16-le")) // 2
    ranges = [{"startOffset": start, "endOffset": start + 20, "count": 1}]
    assert _covered_lines(source, ranges) == {3}


def test_js_report_includes_unvisited_theme_scripts(tmp_path):
    """Every shipped script belongs in the denominator, even if not loaded."""
    scripts = tmp_path / "js"
    scripts.mkdir()
    (scripts / "unvisited.js").write_text("const x = 1;\n")
    data = JSCoverageRecorder(tmp_path).report()
    assert data["unvisited.js"] == {
        "covered_lines": [],
        "total_lines": 1,
        "percent": 0.0,
    }


def test_final_summary_uses_aggregate_js_and_python_line_rates(tmp_path):
    """Never average per-file percentages or conflate lines with branches."""
    scripts = tmp_path / "ulwazi/theme/ulwazi/static/js"
    scripts.mkdir(parents=True)
    (scripts / "short.js").write_text("a();\n")
    (scripts / "long.js").write_text("a();\nb();\nc();\n")
    results = tmp_path / "results"
    results.mkdir()
    (results / "coverage.xml").write_text(
        '<coverage lines-valid="10" lines-covered="7" line-rate="0.7" '
        'branches-valid="4" branches-covered="0" />'
    )
    (results / "js-coverage.json").write_text(
        json.dumps(
            {
                "short.js": {"covered_lines": [1], "total_lines": 1},
                "long.js": {"covered_lines": [1], "total_lines": 3},
            }
        )
    )
    (results / "feature-coverage.json").write_text(
        json.dumps({"covered": ["a"], "missing": ["b"]})
    )
    output = summary(tmp_path)
    assert "Python (ulwazi package, line coverage): 7/10 (70.0%)" in output
    assert "JavaScript (theme scripts, V8 code lines): 2/4 (50.0%)" in output
    assert "Features (curated manifest, all mapped checks pass): 1/2 (50.0%)" in output


def test_final_summary_rejects_incomplete_js_report(tmp_path):
    """Missing script data must never yield a flattering percentage."""
    scripts = tmp_path / "ulwazi/theme/ulwazi/static/js"
    scripts.mkdir(parents=True)
    (scripts / "script.js").write_text("a();\n")
    results = tmp_path / "results"
    results.mkdir()
    (results / "coverage.xml").write_text(
        '<coverage lines-valid="1" lines-covered="1" />'
    )
    (results / "js-coverage.json").write_text("{}")
    with pytest.raises(ValueError, match="JS coverage files differ"):
        summary(tmp_path)


def test_pr_coverage_compares_unrounded_percentages():
    """Even a regression hidden by display rounding fails the PR check."""
    current = {
        "python": {"percent": 69.34},
        "javascript": {"percent": 53.9},
        "features": {"percent": 85.7},
    }
    base = {
        "python": {"percent": 69.35},
        "javascript": {"percent": 53.9},
        "features": {"percent": 85.7},
    }
    report, decreased = compare(current, base)
    assert decreased
    assert "Coverage: Py: 69.3%, JS: 53.9%, Feat: 85.7%" in report


def test_pr_coverage_skips_unavailable_baseline():
    """Never treat a missing or pre-reporting base as 0% coverage."""
    current = {key: {"percent": 50.0} for key in ("python", "javascript", "features")}
    report, decreased = compare(current, None)
    assert not decreased
    assert "baseline unavailable" in report
    assert "comparison is skipped" in report
    assert "Result: baseline unavailable (comparison skipped)" in report
