"""Map Chromium's V8 coverage output to per-file line coverage.

Chromium's JavaScript coverage reports executed ranges as character offsets
into the script source. This module converts those ranges into covered line
numbers and computes a per-file line-coverage percentage for the theme's own
scripts (files under ``_static/js/`` served by the test HTTP server).

Playwright's Python API does not expose JS coverage directly, so this uses a
CDP session with the Profiler domain (startPreciseCoverage/takePreciseCoverage).
"""

import json
import re
from pathlib import Path

from playwright.sync_api import CDPSession

# Only the theme's own scripts are measured; third-party scripts such as
# jQuery, clipboard.js, or the remote cookie bundle are out of scope.
# Sphinx appends a content-hash query string (?v=...) to asset URLs.
THEME_JS_PATTERN = re.compile(r"/_static/js/([A-Za-z0-9_-]+\.js)(?:\?[^/]*)?$")
RESULTS_PATH = Path("results/js-coverage.json")


def _line_starts(source: str) -> list[int]:
    """Character offsets where each line begins (line 1 starts at 0)."""
    starts = [0]
    starts.extend(match.start() + 1 for match in re.finditer("\n", source))
    return starts


def _bisect_right(sorted_list: list[int], value: int) -> int:
    """Return the insertion point for value to keep the list sorted."""
    low, high = 0, len(sorted_list)
    while low < high:
        mid = (low + high) // 2
        if sorted_list[mid] <= value:
            low = mid + 1
        else:
            high = mid
    return low


def _covered_lines(source: str, ranges: list[dict]) -> set[int]:
    """Convert V8 character-offset ranges to covered 1-based line numbers."""
    starts = _line_starts(source)
    covered: set[int] = set()
    for entry in ranges:
        start, end = entry["startOffset"], entry["endOffset"]
        first = _bisect_right(starts, start)
        last = _bisect_right(starts, max(start, end - 1))
        covered.update(range(first + 1, last + 1))
    return covered


class JSCoverageRecorder:
    """Collect V8 JS coverage for theme scripts across a browser session."""

    def __init__(self, static_dir: Path):
        self.static_dir = static_dir
        self.entries: dict[str, dict] = {}
        self._client: CDPSession | None = None

    def start(self, page) -> None:
        """Begin collecting coverage on a Playwright page via a CDP session."""
        client = page.context.new_cdp_session(page)
        client.send("Profiler.enable")
        client.send(
            "Profiler.startPreciseCoverage", {"callCount": False, "detailed": True}
        )
        self._client = client

    def stop(self, page) -> None:
        """Stop collection and merge results into the running totals."""
        client = self._client
        if client is None:
            raise RuntimeError("stop() called before start()")
        coverage = client.send("Profiler.takePreciseCoverage")
        client.send("Profiler.stopPreciseCoverage")
        client.detach()
        self._client = None
        for entry in coverage["result"]:
            match = THEME_JS_PATTERN.search(entry.get("url", ""))
            if not match:
                continue
            name = match.group(1)
            source = self._source_for(name)
            if source is None:
                continue
            data = self.entries.setdefault(name, {"source": source, "covered": set()})
            for function in entry.get("functions", []):
                data["covered"].update(_covered_lines(source, function["ranges"]))

    def _source_for(self, name: str) -> str | None:
        """Read the theme script's source; None if it is not a theme file."""
        path = self.static_dir / "js" / name
        if not path.is_file():
            return None
        return path.read_text(encoding="utf-8")

    def report(self) -> dict[str, dict]:
        """Per-file line coverage: covered, total, and percentage."""
        return {
            name: {
                "covered_lines": sorted(data["covered"]),
                "total_lines": data["source"].count("\n") + 1,
                "percent": round(
                    100 * len(data["covered"]) / max(1, data["source"].count("\n") + 1)
                ),
            }
            for name, data in sorted(self.entries.items())
        }

    def write(self, path: Path = RESULTS_PATH) -> dict:
        """Write the JSON report and return it."""
        report = self.report()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report
