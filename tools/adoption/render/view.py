"""Turn ``adoption.json`` into the values the dashboard template shows."""

from __future__ import annotations

import datetime as dt
import re
from typing import Any

from tools.adoption.detect.rtd_api import parse_timestamp

REASON_LABELS = {
    "opted_out": "Opted out",
    "not_included": "Not tracked",
    "unsupported_host": "Unsupported host",
    "archived": "Archived",
    "not_sphinx_stack": "Not Sphinx Stack",
    "error": "Error",
}
NONE_STACK = "none"
DAYS_PER_MONTH = 30
DAYS_PER_YEAR = 365
RECENT_DAYS = 30
CHART_WIDTH, CHART_HEIGHT = 600, 120
CHART_PAD_X, CHART_PAD_Y = 8, 10


def relative_time(moment: dt.datetime | None, now: dt.datetime) -> str:
    """Describe how long ago ``moment`` was, in coarse human terms."""
    if moment is None:
        return "\u2014"
    days = max((now - moment).days, 0)
    if days == 0:
        return "today"
    if days == 1:
        return "yesterday"
    if days < DAYS_PER_MONTH:
        return f"{days} days ago"
    if days < DAYS_PER_YEAR:
        months = days // DAYS_PER_MONTH
        return f"{months} month{'s' if months > 1 else ''} ago"
    years = days // DAYS_PER_YEAR
    return f"{years} year{'s' if years > 1 else ''} ago"


def version_sort_key(version: str | None) -> str:
    """Return a string that sorts dotted versions numerically (empty if none)."""
    if not version:
        return ""
    numbers = [int(part) for part in re.findall(r"\d+", version.split("\u2013")[0])]
    return ".".join(f"{number:05d}" for number in numbers) or "00000"


def _cell(**values: Any) -> dict[str, Any]:  # noqa: ANN401
    """Return a table cell with every key the template reads."""
    return {"title": None, "chip": None, "corrected": False, **values}


def _stack_cell(project: dict[str, Any]) -> dict[str, Any]:
    stack = project["sphinx_stack"]
    if not stack["detected"]:
        return _cell(text="N/A", tone="none", filter=NONE_STACK, sort="")
    tone = (
        "latest"
        if stack["is_latest"]
        else ("legacy" if stack["kind"] == "legacy" else "outdated")
    )
    title = None
    if stack["corrected"]:
        title = (
            f"The version file says {stack['declared']}, but this is a known upstream "
            f"issue. Detected {stack['version']} from other files (see details)."
        )
    elif "Sphinx Stack version" in project["manual"]:
        title = "Set manually in config.toml"
    return _cell(
        text=stack["version"],
        tone=tone,
        corrected=bool(stack["corrected"]),
        title=title,
        filter=stack["version"],
        sort=version_sort_key(stack["version"]),
    )


def _ulwazi_cell(project: dict[str, Any]) -> dict[str, Any]:
    ulwazi = project["ulwazi"]
    state, version, precision = ulwazi["state"], ulwazi["version"], ulwazi["precision"]
    if state == "pending":
        return _cell(
            text="N/A",
            tone="none",
            chip="Pending deploy",
            title="The repository uses Ulwazi, but the published site does not yet.",
            filter="pending",
            sort="",
        )
    if not ulwazi["uses"]:
        return _cell(text="N/A", tone="none", filter="no", sort="")
    if precision == "estimated":
        text = f"\u2248 {version}"
        title = (
            f"Estimated from the requirement {ulwazi['requirement']}: the live site "
            "could not be checked."
        )
    elif version:
        text = version
        title = {
            "exact": "Confirmed from the live documentation.",
            "range": "The live documentation matches several releases.",
            "dev": "An unreleased build of Ulwazi.",
            "manual": "Set manually in config.toml",
        }.get(precision or "")
    else:
        text, title = (
            "In use",
            "Ulwazi is used, but its version could not be determined.",
        )
    return _cell(
        text=text,
        tone="dev" if precision == "dev" else "ok",
        title=title,
        filter="yes",
        sort=version_sort_key(version),
    )


def _row(project: dict[str, Any], now: dt.datetime) -> dict[str, Any]:
    reason = project["scope"]["reason"]
    activity = project["activity"]
    built = parse_timestamp(activity["last_build_at"])
    docs_commit = parse_timestamp(activity["docs_last_commit_at"])
    repo = project["repo"]
    stack, ulwazi = _stack_cell(project), _ulwazi_cell(project)
    out = reason is not None
    return {
        "slug": project["slug"],
        "name": project["name"],
        "docs_url": project["docs_url"],
        "repo": repo,
        "out": out,
        "reason": REASON_LABELS.get(reason, reason) if reason else None,
        "error": project["scope"]["note"] if reason == "error" else None,
        "stack": stack,
        "ulwazi": ulwazi,
        "built": {
            "text": relative_time(built, now),
            "iso": built.isoformat() if built else "",
            "title": built.strftime("%-d %b %Y")
            if built
            else "No successful build found",
            "epoch": int(built.timestamp()) if built else 0,
        },
        "docs_commit": relative_time(docs_commit, now) if docs_commit else None,
        "evidence": project["evidence"],
        "manual": project["manual"],
        "latest": bool(project["sphinx_stack"]["is_latest"]),
        "search": " ".join(
            filter(None, [project["name"], project["slug"], repo["label"]])
        ).lower(),
    }


def _delta_text(value: int | None) -> str:
    """Weekly change; a decrease is shown as 0."""
    if value is None:
        return ""
    if value <= 0:
        return "0 this week"
    return f"+{value} this week"


def _tiles(summary: dict[str, Any]) -> list[dict[str, Any]]:
    deltas = summary.get("deltas") or {}
    latest = summary.get("latest_sphinx_stack")
    return [
        {
            "preset": "all",
            "label": "RTD projects",
            "value": summary["total"],
            "delta": _delta_text(deltas.get("total")),
            "hint": "All public Read the Docs projects",
        },
        {
            "preset": "stack",
            "label": "Sphinx Stack detected",
            "value": summary["sphinx_stack"],
            "delta": _delta_text(deltas.get("sphinx_stack")),
            "hint": "Projects where a Sphinx Stack version was found",
        },
        {
            "preset": "latest",
            "label": f"On Sphinx Stack {latest}"
            if latest
            else "On latest Sphinx Stack",
            "value": summary["latest"],
            "delta": _delta_text(deltas.get("latest")),
            "hint": "Includes projects whose version file was corrected",
        },
        {
            "preset": "out",
            "label": "Out of scope",
            "value": summary["out_of_scope"],
            "delta": _delta_text(deltas.get("out_of_scope")),
            "hint": "Not Sphinx Stack, archived, opted out or unsupported",
        },
    ]


def _stack_bar(summary: dict[str, Any]) -> list[dict[str, Any]]:
    versions: dict[str, int] = summary["sphinx_stack_versions"]
    total = sum(versions.values())
    return [
        {
            "version": version,
            "count": count,
            "percent": round(100 * count / total, 2) if total else 0,
            "index": min(index, 4),
        }
        for index, (version, count) in enumerate(versions.items())
    ]


def _trend(history: list[dict[str, Any]]) -> dict[str, Any] | None:
    points = [
        (dt.date.fromisoformat(row["date"]), 100 * row["ulwazi"] / row["sphinx_stack"])
        for row in history
        if row["sphinx_stack"]
    ]
    if len(points) < 2:  # noqa: PLR2004
        return None
    first, last = points[0][0], points[-1][0]
    span = max((last - first).days, 1)
    top = max(10.0, *(percent for _, percent in points))
    width = CHART_WIDTH - 2 * CHART_PAD_X
    height = CHART_HEIGHT - 2 * CHART_PAD_Y
    coordinates = [
        (
            CHART_PAD_X + width * (day - first).days / span,
            CHART_PAD_Y + height * (1 - percent / top),
        )
        for day, percent in points
    ]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in coordinates)
    baseline = CHART_PAD_Y + height
    area = (
        f"{coordinates[0][0]:.1f},{baseline} {line} {coordinates[-1][0]:.1f},{baseline}"
    )
    return {
        "line": line,
        "area": area,
        "width": CHART_WIDTH,
        "height": CHART_HEIGHT,
        "top": round(top),
        "first": first.isoformat(),
        "last": last.isoformat(),
        "end": {"x": round(coordinates[-1][0], 1), "y": round(coordinates[-1][1], 1)},
        "rows": [
            {"date": day.isoformat(), "percent": round(percent, 1)}
            for day, percent in reversed(points)
        ][:30],
    }


def build_view(
    data: dict[str, Any], history: list[dict[str, Any]], *, now: dt.datetime
) -> dict[str, Any]:
    """Prepare everything the template needs."""
    summary = data["summary"]
    rows = [_row(project, now) for project in data["projects"]]
    stack_versions = list(summary["sphinx_stack_versions"])
    recent_cutoff = (now.date() - dt.timedelta(days=RECENT_DAYS)).isoformat()
    recent = sorted(
        (
            {
                "name": p["name"],
                "docs_url": p["docs_url"],
                "since": p["ulwazi"]["since"],
            }
            for p in data["projects"]
            if p["ulwazi"]["since"] and p["ulwazi"]["since"] >= recent_cutoff
        ),
        key=lambda item: item["since"],
        reverse=True,
    )
    csv_rows = [
        {
            "slug": p["slug"],
            "name": p["name"],
            "docs_url": p["docs_url"],
            "repository": p["repo"]["label"] or "",
            "repository_url": p["repo"]["url"] or "",
            "docs_path": p["repo"]["docs_path"] or "",
            "scope": REASON_LABELS.get(p["scope"]["reason"], "In scope")
            if p["scope"]["reason"]
            else "In scope",
            "sphinx_stack": p["sphinx_stack"]["version"] or "N/A",
            "sphinx_stack_declared": p["sphinx_stack"]["declared"] or "",
            "sphinx_stack_corrected": "yes" if p["sphinx_stack"]["corrected"] else "",
            "ulwazi": r["ulwazi"]["text"],
            "ulwazi_state": p["ulwazi"]["state"],
            "last_build": p["activity"]["last_build_at"] or "",
        }
        for p, r in zip(data["projects"], rows, strict=True)
    ]
    generated = parse_timestamp(data.get("generated_at")) or now
    return {
        "summary": summary,
        "generated": generated.strftime("%-d %b %Y, %H:%M UTC"),
        "tiles": _tiles(summary),
        "stack_bar": _stack_bar(summary),
        "stack_options": stack_versions,
        "rows": rows,
        "trend": _trend(history),
        "recent": recent,
        "csv_rows": csv_rows,
        "reason_labels": REASON_LABELS,
        "has_none": any(r["stack"]["filter"] == NONE_STACK for r in rows),
        "ulwazi_delta": _delta_text((summary.get("deltas") or {}).get("ulwazi")),
        "total_tracked": summary["sphinx_stack"],
    }
