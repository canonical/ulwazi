"""Layer 1: list the public Read the Docs projects and their repositories."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from tools.adoption import SCHEMA_VERSION
from tools.adoption.models import RtdProject, write_json

RTD_PROJECTS_FILE = "rtd-projects.json"


def write_rtd_projects(path: Path, projects: list[RtdProject], *, source: str) -> None:
    """Write the detection layer's output (public projects only)."""
    write_json(
        path,
        {
            "schema_version": SCHEMA_VERSION,
            "generated_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
            "source": source,
            "projects": [
                dict(vars(project))
                for project in sorted(projects, key=lambda item: item.slug)
            ],
        },
    )
