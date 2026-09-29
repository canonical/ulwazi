"""Print the three scoped coverage metrics at the end of make test-coverage."""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def summary(root: Path = ROOT) -> str:
    """Summarize the current run; fail if any metric is missing or invalid."""
    results = root / "results"
    python = ET.parse(results / "coverage.xml").getroot()  # noqa: S314
    lines = int(python.attrib["lines-valid"])
    executed = int(python.attrib["lines-covered"])
    if not lines:
        raise ValueError("Python coverage contains no executable lines")

    js = json.loads((results / "js-coverage.json").read_text(encoding="utf-8"))
    expected = {
        path.name for path in (root / "ulwazi/theme/ulwazi/static/js").glob("*.js")
    }
    if not expected or set(js) != expected:
        raise ValueError(
            f"JS coverage files differ from theme scripts: {expected ^ set(js)}"
        )
    js_lines = sum(data["total_lines"] for data in js.values())
    js_executed = sum(len(data["covered_lines"]) for data in js.values())
    if not js_lines or js_executed > js_lines:
        raise ValueError("JS coverage has no valid executable lines")

    features = json.loads(
        (results / "feature-coverage.json").read_text(encoding="utf-8")
    )
    checked = len(features["covered"])
    total = checked + len(features["missing"])
    if not total:
        raise ValueError("Feature manifest contains no features")

    return "\n".join(
        (
            "=== Coverage summary (current run) ===",
            f"Python (ulwazi package, line coverage): {executed}/{lines} ({100 * executed / lines:.1f}%)",
            f"JavaScript (theme scripts, V8 code lines): {js_executed}/{js_lines} ({100 * js_executed / js_lines:.1f}%) across {len(js)} files",
            f"Features (curated manifest, all mapped checks pass): {checked}/{total} ({100 * checked / total:.1f}%)",
            "Feature percentage is limited to tests/features.yaml; it is not exhaustive cheatsheet coverage.",
            "Unverified: " + (", ".join(features["missing"]) or "none"),
        )
    )


if __name__ == "__main__":
    print(summary())
