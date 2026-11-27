"""Statistics, history and change tracking over processed projects."""

from __future__ import annotations

import datetime as dt
import json
from collections import Counter
from pathlib import Path
from typing import Any

from packaging.version import InvalidVersion, Version

HISTORY_FILE = "history.jsonl"
DELTA_DAYS = 7
HISTORY_FIELDS = ("total", "sphinx_stack", "latest", "ulwazi", "out_of_scope")


def _version_key(text: str) -> tuple[int, Version]:
    try:
        return 1, Version(text)
    except InvalidVersion:
        return 0, Version("0")


def _sorted_counts(counter: Counter[str]) -> dict[str, int]:
    return dict(
        sorted(counter.items(), key=lambda item: _version_key(item[0]), reverse=True)
    )


def in_scope(record: dict[str, Any]) -> bool:
    """Return True when the Sphinx Stack was found and the project is tracked."""
    return (
        bool(record["sphinx_stack"]["detected"]) and record["scope"]["reason"] is None
    )


def summarize(
    records: list[dict[str, Any]],
    *,
    latest_stack: str | None,
    latest_ulwazi: str | None,
    today: dt.date,
) -> dict[str, Any]:
    """Compute the numbers shown at the top of the dashboard."""
    tracked = [r for r in records if in_scope(r)]
    ulwazi = [r for r in tracked if r["ulwazi"]["uses"]]
    elsewhere = [r for r in records if not in_scope(r) and r["ulwazi"]["uses"]]
    reasons = Counter(r["scope"]["reason"] for r in records if r["scope"]["reason"])
    stack_versions = Counter(r["sphinx_stack"]["version"] for r in tracked)
    ulwazi_versions = Counter(r["ulwazi"]["version"] or "unknown" for r in ulwazi)
    repos = {r["repo"]["url"] for r in tracked if r["repo"]["url"]}
    return {
        "date": today.isoformat(),
        "total": len(records),
        "sphinx_stack": len(tracked),
        "latest": sum(1 for r in tracked if r["sphinx_stack"]["is_latest"]),
        "ulwazi": len(ulwazi),
        "ulwazi_percent": round(100 * len(ulwazi) / len(tracked), 1)
        if tracked
        else 0.0,
        "ulwazi_elsewhere": len(elsewhere),
        "pending_deploy": sum(1 for r in tracked if r["ulwazi"]["state"] == "pending"),
        "corrected": sum(1 for r in tracked if r["sphinx_stack"]["corrected"]),
        "out_of_scope": len(records) - len(tracked),
        "out_of_scope_reasons": dict(sorted(reasons.items())),
        "unique_repositories": len(repos),
        "errors": reasons.get("error", 0),
        "latest_sphinx_stack": latest_stack,
        "latest_ulwazi": latest_ulwazi,
        "sphinx_stack_versions": _sorted_counts(stack_versions),  # pyright: ignore[reportArgumentType]
        "ulwazi_versions": _sorted_counts(ulwazi_versions),
    }


def read_history(path: Path) -> list[dict[str, Any]]:
    """Read ``history.jsonl`` (missing file means no history yet)."""
    if not path.is_file():
        return []
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return sorted(rows, key=lambda row: row["date"])


def update_history(path: Path, summary: dict[str, Any]) -> list[dict[str, Any]]:
    """Add today's row (replacing an earlier row of the same day) and save."""
    rows = [row for row in read_history(path) if row["date"] != summary["date"]]
    rows.append({"date": summary["date"], **{k: summary[k] for k in HISTORY_FIELDS}})
    rows.sort(key=lambda row: row["date"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    return rows


def deltas(
    summary: dict[str, Any], history: list[dict[str, Any]], *, today: dt.date
) -> dict[str, int | None]:
    """Change of each headline number versus about a week ago (``None`` if unknown)."""
    cutoff = (today - dt.timedelta(days=DELTA_DAYS)).isoformat()
    earlier = [row for row in history if row["date"] <= cutoff]
    if not earlier:
        return dict.fromkeys(HISTORY_FIELDS)
    base = earlier[-1]
    return {key: summary[key] - base[key] for key in HISTORY_FIELDS}
