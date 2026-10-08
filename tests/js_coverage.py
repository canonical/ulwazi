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


def _code_lines(source: str) -> list[tuple[int, int, int]]:
    """Nonblank, non-comment-only lines with UTF-16 offsets (V8's units)."""
    lines = []
    offset = 0
    in_comment = False
    for number, line in enumerate(source.splitlines(keepends=True), 1):
        text = line.strip()
        if in_comment:
            if "*/" in text:
                in_comment = False
        elif text.startswith("/*"):
            in_comment = "*/" not in text
        elif text.startswith("*/"):
            in_comment = False
        elif not in_comment and text and not text.startswith("//"):
            start = (
                offset
                + len(line[: len(line) - len(line.lstrip())].encode("utf-16-le")) // 2
            )
            end = offset + len(line.rstrip().encode("utf-16-le")) // 2
            lines.append((number, start, end))
        offset += len(line.encode("utf-16-le")) // 2
    return lines


def _covered_lines(source: str, ranges: list[dict]) -> set[int]:
    """Count executed code lines, respecting nested zero-count V8 ranges."""
    code = _code_lines(source)
    if not code:
        return set()
    executed = bytearray(max(end for _, _, end in code))
    # A function's outer range may execute while an inner branch does not.
    # Paint larger ranges first so nested, smaller zero-count ranges override.
    for entry in sorted(
        ranges, key=lambda item: item["endOffset"] - item["startOffset"], reverse=True
    ):
        start, end = entry["startOffset"], entry["endOffset"]
        executed[start:end] = bytes([int(entry["count"] > 0)]) * (end - start)
    return {number for number, start, end in code if any(executed[start:end])}


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
            ranges = [
                item
                for function in entry.get("functions", [])
                for item in function["ranges"]
            ]
            data["covered"].update(_covered_lines(source, ranges))

    def _source_for(self, name: str) -> str | None:
        """Read the theme script's source; None if it is not a theme file."""
        path = self.static_dir / "js" / name
        if not path.is_file():
            return None
        return path.read_text(encoding="utf-8")

    def report(self) -> dict[str, dict]:
        """Per-file line coverage: covered, total, and percentage."""
        for path in self.static_dir.joinpath("js").glob("*.js"):
            self.entries.setdefault(
                path.name,
                {"source": path.read_text(encoding="utf-8"), "covered": set()},
            )
        return {
            name: {
                "covered_lines": sorted(data["covered"]),
                "total_lines": len(_code_lines(data["source"])),
                "percent": round(
                    100 * len(data["covered"]) / len(_code_lines(data["source"])), 1
                )
                if _code_lines(data["source"])
                else 100.0,
            }
            for name, data in sorted(self.entries.items())
        }

    def write(self, path: Path = RESULTS_PATH) -> dict:
        """Write the JSON report and return it."""
        report = self.report()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report
