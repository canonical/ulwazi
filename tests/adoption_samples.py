"""Sample ``adoption.json`` data for the adoption dashboard tests.

Run ``python tests/adoption_samples.py <directory>`` to write ``adoption.json``
and ``history.jsonl`` for a manual look at the dashboard::

    python tests/adoption_samples.py /tmp/adoption-sample
    python -m tools.adoption --data-dir /tmp/adoption-sample render
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

from tools.adoption import SCHEMA_VERSION
from tools.adoption.process.summary import deltas, summarize

TODAY = dt.date(2026, 11, 27)
GENERATED = "2026-11-27T03:00:12+00:00"


def project(
    slug: str,
    *,
    stack: str | None = "3.0",
    declared: str | None = None,
    kind: str = "released",
    latest: str = "3.0",
    ulwazi: str | None = None,
    ulwazi_precision: str = "exact",
    ulwazi_state: str | None = None,
    reason: str | None = None,
    archived: bool = False,
    docs_path: str | None = "docs",
    built_days_ago: int | None = 3,
    manual: list[str] | None = None,
    since: str | None = None,
) -> dict[str, Any]:
    """Build one project record in the layout the pipeline writes."""
    detected = stack is not None
    state = ulwazi_state or ("live" if ulwazi else "none")
    built = (
        (
            dt.datetime(2026, 11, 27, tzinfo=dt.UTC) - dt.timedelta(days=built_days_ago)
        ).isoformat()
        if built_days_ago is not None
        else None
    )
    name = slug.replace("-", " ").title()
    evidence = [
        {
            "label": "Documentation folder",
            "text": f"{docs_path} (found by: common location)",
            "url": f"https://github.com/canonical/{slug}/tree/abc/{docs_path}",
        },
    ]
    if detected:
        evidence.append(
            {
                "label": "Version file",
                "text": f"{docs_path}/_dev/version says {declared or stack}",
                "url": f"https://github.com/canonical/{slug}/blob/abc/{docs_path}/_dev/version",
            }
        )
    return {
        "slug": slug,
        "name": name,
        "docs_url": f"https://documentation.ubuntu.com/{slug}/",
        "repo": {
            "url": f"https://github.com/canonical/{slug}",
            "label": f"canonical/{slug}",
            "host": "github.com",
            "default_branch": "main",
            "docs_path": docs_path,
            "docs_url": f"https://github.com/canonical/{slug}/tree/abc/{docs_path}"
            if docs_path
            else None,
            "archived": archived,
        },
        "scope": {"reason": reason, "note": None},
        "sphinx_stack": {
            "detected": detected,
            "kind": kind if detected else "none",
            "version": stack,
            "declared": declared or stack,
            "corrected": declared is not None and declared != stack,
            "is_latest": stack == latest,
            "version_file": f"{docs_path}/_dev/version" if detected else None,
            "version_file_url": None,
        },
        "ulwazi": {
            "uses": state in ("live", "repo"),
            "state": state,
            "version": ulwazi,
            "precision": ulwazi_precision if ulwazi else None,
            "repo_theme": "ulwazi" if state != "none" else "furo",
            "requirement": "~=1.0" if ulwazi else None,
            "requirement_file": f"{docs_path}/requirements.txt" if ulwazi else None,
            "live_checked": True,
            "live_ok": state != "repo",
            "live_error": "HTTP 403" if state == "repo" else None,
            "since": since,
            "primary_checksum": None,
        },
        "activity": {
            "last_build_at": built,
            "last_build_commit": None,
            "docs_last_commit_at": "2026-11-20T10:00:00+00:00" if detected else None,
            "head_commit": "a" * 40,
            "head_commit_at": "2026-11-26T10:00:00+00:00",
        },
        "manual": manual or [],
        "evidence": evidence,
    }


def sample_projects() -> list[dict[str, Any]]:
    """A varied set that exercises every state of the table."""
    corrected_evidence = {
        "label": "Version corrected",
        "text": "Version file says 2.0, but this is a known upstream problem: Sphinx Stack 3.0 still ships '2.0'. Detected 3.0 from: requirements.txt lists ulwazi instead of canonical-sphinx; requirements.txt needs sphinx-roles >= 1.0",
        "url": None,
    }
    projects = [
        project("ulwazi", ulwazi="1.0.3", since="2026-11-20"),
        project("sphinx-stack-docs", ulwazi="1.0.3"),
        project(
            "juju-docs", stack="3.0", declared="2.0", ulwazi="1.0.2", since="2026-11-12"
        ),
        project(
            "lxd", stack="2.0", ulwazi="1.0.1\u20131.0.2", ulwazi_precision="range"
        ),
        project("maas", stack="2.0", ulwazi="0.6"),
        project("landscape", stack="1.6", built_days_ago=45),
        project("multipass", stack="1.4.1", built_days_ago=130),
        project("charmcraft", stack="3.0", ulwazi="1.0.3"),
        project("rockcraft", stack="3.0", ulwazi="1.0.3"),
        project("snapcraft", stack="3.0", ulwazi="1.0.3"),
        project(
            "ubuntu-pro-client",
            stack="2.0",
            ulwazi="1.0.3",
            ulwazi_precision="estimated",
            ulwazi_state="repo",
        ),
        project("ops", stack="3.0", ulwazi_state="pending"),
        project("microcloud", stack="2.0"),
        project("microceph", stack="2.0"),
        project("microovn", stack="1.6"),
        project("pebble", stack="1.5", built_days_ago=400),
        project(
            "starter-pack-legacy", stack="< 1.0", kind="legacy", built_days_ago=900
        ),
        project("dev-build-docs", stack="3.0", ulwazi="dev", ulwazi_precision="dev"),
        project("custom-sphinx", stack=None, reason="not_sphinx_stack", ulwazi=None),
        project("mkdocs-site", stack=None, reason="not_sphinx_stack", docs_path=None),
        project(
            "old-project",
            stack="1.0.1",
            reason="archived",
            archived=True,
            built_days_ago=1200,
        ),
        project(
            "internal-notes",
            stack=None,
            reason="opted_out",
            built_days_ago=None,
            docs_path=None,
        ),
        project(
            "launchpad-docs", stack=None, reason="unsupported_host", docs_path=None
        ),
        project("broken-repo", stack=None, reason="error", docs_path=None),
        project(
            "themed-without-stack",
            stack=None,
            reason="not_sphinx_stack",
            ulwazi="1.0.3",
        ),
        project(
            "pinned-docs",
            stack="3.0",
            ulwazi="1.0.3",
            manual=["Sphinx Stack version", "docs path"],
        ),
    ]
    projects[2]["evidence"].append(corrected_evidence)
    # A long tail of ordinary projects so the table is longer than a screen.
    for index in range(1, 31):
        version = ("3.0", "2.0", "2.0", "1.6", "3.0")[index % 5]
        projects.append(
            project(
                f"product-{index:02d}",
                stack=version,
                ulwazi="1.0.3" if index % 3 == 0 else None,
                built_days_ago=index * 4,
            )
        )
    projects[-1]["scope"]["reason"] = "error"
    projects[-1]["scope"]["note"] = "HTTP 502 reading canonical/product-30:docs/conf.py"
    return projects


def sample_history() -> list[dict[str, Any]]:
    """Daily history rows with a rising adoption share."""
    rows = []
    for offset in range(40, -1, -4):
        day = TODAY - dt.timedelta(days=offset)
        rows.append(
            {
                "date": day.isoformat(),
                "total": 50 + (40 - offset) // 8,
                "sphinx_stack": 44 + (40 - offset) // 10,
                "latest": 10 + (40 - offset) // 3,
                "ulwazi": 4 + (40 - offset) // 3,
                "out_of_scope": 6,
            }
        )
    return rows


def sample_adoption(history: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Return a complete ``adoption.json`` payload."""
    records = sample_projects()
    summary = summarize(records, latest_stack="3.0", latest_ulwazi="1.0.3", today=TODAY)
    rows = history if history is not None else sample_history()
    summary["deltas"] = deltas(summary, rows, today=TODAY)
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": GENERATED,
        "tracking_mode": "auto",
        "summary": summary,
        "projects": sorted(records, key=lambda r: r["name"].lower()),
    }


def write_sample(directory: Path) -> None:
    """Write ``adoption.json`` and ``history.jsonl`` into ``directory``."""
    directory.mkdir(parents=True, exist_ok=True)
    history = sample_history()
    (directory / "adoption.json").write_text(
        json.dumps(sample_adoption(history), indent=2) + "\n", encoding="utf-8"
    )
    (directory / "history.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in history), encoding="utf-8"
    )


if __name__ == "__main__":
    write_sample(Path(sys.argv[1] if len(sys.argv) > 1 else "adoption-sample"))
