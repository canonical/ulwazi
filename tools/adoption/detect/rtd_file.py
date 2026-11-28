"""Import a Read the Docs project list from an exported CSV or JSON file."""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any

from tools.adoption.detect.normalize import (
    is_public,
    is_translation,
    project_from_record,
)
from tools.adoption.models import DataError, RtdProject

LOG = logging.getLogger("adoption")


def _records(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
        if isinstance(data, dict):
            data = data.get("results") or data.get("projects") or []  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        if not isinstance(data, list):
            raise DataError(f"{path}: expected a JSON list of projects")
        return [item for item in data if isinstance(item, dict)]  # pyright: ignore[reportUnknownVariableType]
    return [
        {
            key.strip().lower().replace(" ", "_"): value
            for key, value in row.items()
            if key
        }
        for row in csv.DictReader(text.splitlines())
    ]


def detect_from_file(
    path: Path,
    *,
    base_url: str,
    assume_public: bool = False,
    limit: int | None = None,
) -> list[RtdProject]:
    """Read projects from ``path``; only public, non-translation rows are kept.

    A row without a ``privacy_level`` is dropped unless ``assume_public`` is set,
    so an export that does not say which projects are private cannot leak them.
    """
    projects: dict[str, RtdProject] = {}
    skipped = 0
    for record in _records(path):
        if is_translation(record) or not is_public(
            record, base_url=base_url, assume_public=assume_public
        ):
            skipped += 1
            continue
        project = project_from_record(record, base_url=base_url)
        if project is None:
            skipped += 1
            continue
        projects[project.slug] = project
        if limit and len(projects) >= limit:
            break
    LOG.info("Imported %d public projects (%d rows skipped)", len(projects), skipped)
    return list(projects.values())
