"""Report three coverage rates on a PR and compare them with its base revision."""

import argparse
from pathlib import Path

from coverage_summary import METRIC_SCHEMA, read_metrics

LABELS = {"python": "Py", "javascript": "JS", "features": "Feat"}


def compare(current: dict, baseline: dict | None) -> tuple[str, bool]:
    """Create a Markdown summary; fail only on a comparable rate decrease."""
    title = "Coverage: " + ", ".join(
        f"{label}: {current[key]['percent']:.1f}%" for key, label in LABELS.items()
    )
    rows = ["| Metric | PR | Base | Change |", "| --- | ---: | ---: | ---: |"]
    decreased = False
    for key, label in LABELS.items():
        now = current[key]["percent"]
        before = baseline[key]["percent"] if baseline is not None else None
        if before is None:
            base_text, change = "—", "baseline unavailable"
        else:
            delta = now - before
            decreased |= delta < -1e-9
            base_text, change = f"{before:.1f}%", f"{delta:+.1f} pp"
        rows.append(f"| {label} | {now:.1f}% | {base_text} | {change} |")
    if baseline is None:
        rows.append(
            "\nBase has no compatible three-metric reporter; comparison is skipped, "
            "not treated as 0%."
        )
    else:
        rows.append(
            "\nCompared unrounded rates; changes above are rounded percentage points. "
            "The curated feature denominator can change when the manifest changes. "
            "Base values come from the exact base commit, not the historical merge-base."
        )
    if baseline is None:
        result = "baseline unavailable (comparison skipped)"
    else:
        result = "coverage regression" if decreased else "no regression"
    rows.append("\nResult: " + result)
    return title + "\n\n" + "\n".join(rows) + "\n", decreased


def main() -> int:
    """Read reports and write a GitHub step summary and check output."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    current = read_metrics(args.current)
    baseline = None
    if args.baseline is not None:
        baseline = read_metrics(args.baseline)
    report, decreased = compare(current, baseline)
    title = report.split("\n", 1)[0]
    args.summary.write_text(report, encoding="utf-8")
    args.output.write_text(f"title={title}\nschema={METRIC_SCHEMA}\n", encoding="utf-8")
    print(report)
    return int(decreased)


if __name__ == "__main__":
    raise SystemExit(main())
