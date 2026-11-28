"""Data contract shared by the detection and processing layers."""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.adoption import SCHEMA_VERSION


class DataError(Exception):
    """Raised when a data file is missing, malformed or has another schema."""


@dataclass
class RtdProject:
    """A public Read the Docs project, as produced by the detection layer."""

    slug: str
    name: str
    docs_url: str
    repo_url: str | None = None
    repo_host: str | None = None
    repo_owner: str | None = None
    repo_name: str | None = None
    default_branch: str | None = None
    readthedocs_yaml_path: str | None = None
    language: str | None = None
    subproject_of: str | None = None
    last_build_at: str | None = None
    last_build_commit: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RtdProject:
        """Build a project from JSON data, ignoring unknown keys."""
        known = {field.name for field in dataclasses.fields(cls)}
        return cls(**{key: value for key, value in data.items() if key in known})


@dataclass
class Evidence:
    """One fact that explains a detection result, shown in the dashboard."""

    label: str
    text: str
    url: str | None = None


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write ``payload`` as stable, human-diffable JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=False, ensure_ascii=False)
    path.write_text(text + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    """Read a JSON object, raising :class:`DataError` when it is unusable."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise DataError(
            f"{path} does not exist; run the previous layer first"
        ) from error
    except json.JSONDecodeError as error:
        raise DataError(f"{path} is not valid JSON: {error}") from error
    if not isinstance(data, dict):
        raise DataError(f"{path} must contain a JSON object")
    return data  # pyright: ignore[reportUnknownVariableType]


def check_schema(path: Path, data: dict[str, Any]) -> None:
    """Fail loudly if ``data`` was written with an incompatible schema."""
    found = data.get("schema_version")
    if found != SCHEMA_VERSION:
        raise DataError(
            f"{path} has schema_version {found!r}; this tool expects {SCHEMA_VERSION}"
        )


def read_rtd_projects(path: Path) -> tuple[dict[str, Any], list[RtdProject]]:
    """Read the detection layer's output."""
    data = read_json(path)
    check_schema(path, data)
    projects = [RtdProject.from_dict(item) for item in data.get("projects", [])]
    return data, projects
