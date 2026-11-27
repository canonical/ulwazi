"""The processing layer: from detected RTD projects to ``adoption.json``."""

from __future__ import annotations

import dataclasses
import datetime as dt
import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeVar

from tools.adoption import SCHEMA_VERSION
from tools.adoption.cache import Cache
from tools.adoption.config import Config, Override
from tools.adoption.detect.rtd_api import parse_timestamp
from tools.adoption.http import FetchError
from tools.adoption.models import (
    DataError,
    Evidence,
    RtdProject,
    read_json,
    read_rtd_projects,
    write_json,
)
from tools.adoption.process.github import GitHub, GitHubError, RepoFiles, RepoInfo
from tools.adoption.process.live_site import LiveResult, check_live
from tools.adoption.process.locate import DocsLocation, locate_docs, read_rtd_yaml
from tools.adoption.process.stack import StackResult, detect_stack
from tools.adoption.process.summary import (
    HISTORY_FILE,
    deltas,
    in_scope,
    summarize,
    update_history,
)
from tools.adoption.process.ulwazi import UlwaziResult, resolve_ulwazi
from tools.adoption.process.ulwazi_releases import Catalogue
from tools.adoption.process.ulwazi_repo import RepoUlwazi, analyse_repo
from tools.adoption.process.upstream import Upstream

LOG = logging.getLogger("adoption")

ADOPTION_FILE = "adoption.json"
REJECTED_FILE = "adoption.rejected.json"
WORKERS = 8
LIVE_WORKERS = 4
ERROR_NOTE_LENGTH = 200
GITHUB = "github.com"

T = TypeVar("T")
R = TypeVar("R")


class PublishRefusedError(Exception):
    """Raised when too many projects failed to produce trustworthy data."""


@dataclass
class Inspection:
    """What was learned from a repository."""

    docs: DocsLocation | None = None
    stack: StackResult = field(default_factory=StackResult)
    repo_ulwazi: RepoUlwazi | None = None
    files: RepoFiles | None = None


@dataclass
class Entry:
    """A project moving through the pipeline."""

    project: RtdProject
    owner: str | None
    name: str | None
    override: Override | None = None
    reason: str | None = None  # why the project is out of scope
    info: RepoInfo | None = None
    inspection: Inspection = field(default_factory=Inspection)
    live: LiveResult | None = None
    docs_commit_at: str | None = None
    error: str | None = None
    manual: list[str] = field(default_factory=list)


def _parallel(function: Callable[[T], R], items: list[T], workers: int) -> list[R]:
    if not items:
        return []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(function, items))


def prepare_entries(projects: list[RtdProject], config: Config) -> list[Entry]:
    """Apply opt-out/opt-in rules and overrides before any network access."""
    entries = []
    for project in projects:
        override = config.override_for(project.slug)
        owner, name, host = project.repo_owner, project.repo_name, project.repo_host
        manual: list[str] = []
        if override and override.repo:
            host = GITHUB
            owner, _, name = override.repo.partition("/")
            manual.append("repository")
        entry = Entry(project, owner, name, override=override, manual=manual)
        full = f"{owner}/{name}" if owner and name else None
        if config.exclusion(project.slug, full):
            entry.reason = "opted_out"
        elif not config.is_included(project.slug, full):
            entry.reason = "not_included"
        elif host != GITHUB or not (owner and name):
            entry.reason = "unsupported_host"
        entries.append(entry)
    return entries


def _inspect(entry: Entry, services: Services) -> None:
    info = entry.info
    assert info is not None  # noqa: S101 - only called for visible repositories
    if not info.head_oid:
        entry.error = "The repository has no commits on its default branch"
        return
    try:
        files = RepoFiles(services.github, info.owner, info.name, info.head_oid)
        rtd_yaml = read_rtd_yaml(files, entry.project.readthedocs_yaml_path)
        override = entry.override
        docs = locate_docs(
            files, rtd_yaml=rtd_yaml, override=override.docs_path if override else None
        )
        if override and override.docs_path:
            entry.manual.append("docs path")
        stack = detect_stack(
            files,
            docs,
            services.upstream,
            latest=services.latest_stack,
            correct=services.config.correct_known_version_issues,
        )
        entry.inspection = Inspection(
            docs, stack, analyse_repo(files, docs, rtd_yaml), files
        )
    except (GitHubError, FetchError) as error:
        entry.error = str(error)[:ERROR_NOTE_LENGTH]
        LOG.warning("%s: %s", entry.project.slug, entry.error)


@dataclass
class Services:
    """Shared clients for one pipeline run."""

    config: Config
    github: GitHub
    upstream: Upstream
    catalogue: Catalogue | None
    latest_stack: str | None


def _apply_pins(entry: Entry, stack: StackResult) -> None:
    override = entry.override
    if override and override.sphinx_stack:
        stack.detected, stack.kind = True, "released"
        stack.version = override.sphinx_stack
        stack.corrected = False
        entry.manual.append("Sphinx Stack version")
        stack.evidence.append(
            Evidence("Manual override", f"Version pinned to {override.sphinx_stack}")
        )


def _record(
    entry: Entry, services: Services, previous: dict[str, Any], today: dt.date
) -> dict[str, Any]:
    project, info = entry.project, entry.info
    stack = entry.inspection.stack
    _apply_pins(entry, stack)
    stack.is_latest = bool(stack.version and stack.version == services.latest_stack)
    reason = entry.reason
    note = None
    if entry.error:
        reason, note = "error", entry.error
    elif reason is None and info is not None and info.archived:
        reason = "archived"
    elif reason is None and not stack.detected:
        reason = "not_sphinx_stack"

    built_at = parse_timestamp(project.last_build_at)
    pinned = entry.override.ulwazi if entry.override else None
    if pinned:
        entry.manual.append("Ulwazi version")
    ulwazi: UlwaziResult = resolve_ulwazi(
        entry.inspection.repo_ulwazi,
        entry.live,
        services.catalogue,
        built_at=built_at,
        pinned=pinned,
    )
    before = previous.get(project.slug, {}).get("ulwazi", {})
    if ulwazi.uses:
        ulwazi.since = before.get("since") or (
            today.isoformat() if before and not before.get("uses") else None
        )

    docs = entry.inspection.docs
    files = entry.inspection.files
    repo_url = info.url if info else project.repo_url
    return {
        "slug": project.slug,
        "name": project.name,
        "docs_url": project.docs_url,
        "repo": {
            "url": repo_url,
            "label": f"{info.owner}/{info.name}" if info else _label(entry),
            "host": GITHUB if info else project.repo_host,
            "default_branch": info.default_branch if info else project.default_branch,
            "docs_path": docs.path if docs else None,
            "docs_url": files.url(docs.path, kind="tree") if docs and files else None,
            "archived": bool(info and info.archived),
        },
        "scope": {"reason": reason, "note": note},
        "sphinx_stack": {
            **_without(dataclasses.asdict(stack), "evidence"),
        },
        "ulwazi": {
            **_without(dataclasses.asdict(ulwazi), "evidence"),
            "primary_checksum": (
                entry.live.assets.get("css/vanilla-main.css") if entry.live else None
            ),
        },
        "activity": {
            "last_build_at": project.last_build_at,
            "last_build_commit": project.last_build_commit,
            "docs_last_commit_at": entry.docs_commit_at,
            "head_commit": info.head_oid if info else None,
            "head_commit_at": info.head_date if info else None,
        },
        "manual": sorted(set(entry.manual)),
        "evidence": [
            dataclasses.asdict(item) for item in [*stack.evidence, *ulwazi.evidence]
        ],
    }


def _label(entry: Entry) -> str | None:
    if entry.owner and entry.name:
        return f"{entry.owner}/{entry.name}"
    return entry.project.repo_host


def _without(data: dict[str, Any], *keys: str) -> dict[str, Any]:
    return {key: value for key, value in data.items() if key not in keys}


def process_projects(
    projects: list[RtdProject],
    services: Services,
    *,
    previous: dict[str, Any],
    today: dt.date,
    live: bool = True,
) -> list[dict[str, Any]]:
    """Run all detections and return one record per tracked public project."""
    config = services.config
    entries = prepare_entries(projects, config)

    candidates = [e for e in entries if e.reason is None]
    infos = services.github.repo_infos(
        [(e.owner, e.name) for e in candidates if e.owner and e.name]
    )
    dropped = 0
    for entry in candidates:
        info = infos.get((entry.owner or "", entry.name or ""))
        if info is None:
            entry.reason = "dropped"
            dropped += 1
        else:
            entry.info = info
            if info.archived:
                entry.reason = "archived"
    LOG.info("%d repositories are not public and are left out", dropped)

    inspect_list = [e for e in candidates if e.info and e.reason is None]
    _parallel(lambda e: _inspect(e, services), inspect_list, WORKERS)

    located = [
        (e.info.owner, e.info.name, e.info.head_oid, e.inspection.docs.path)
        for e in inspect_list
        if e.info and e.info.head_oid and e.inspection.docs
    ]
    if located:
        dates = services.github.docs_commit_dates(located)
        for entry in inspect_list:
            if entry.info and entry.info.head_oid and entry.inspection.docs:
                key = (
                    entry.info.owner,
                    entry.info.name,
                    entry.info.head_oid,
                    entry.inspection.docs.path,
                )
                entry.docs_commit_at = dates.get(key)

    if live and config.live_site_checks:
        checkable = [
            e
            for e in entries
            if e.reason not in ("opted_out", "not_included", "dropped")
        ]
        results = _parallel(
            lambda e: check_live(e.project.docs_url), checkable, LIVE_WORKERS
        )
        for entry, result in zip(checkable, results, strict=True):
            entry.live = result

    return [
        _record(entry, services, previous, today)
        for entry in entries
        if entry.reason != "dropped"
    ]


def run(
    *,
    config: Config,
    data_dir: Path,
    cache_dir: Path | None,
    github_token: str | None,
    only: list[str] | None = None,
    limit: int | None = None,
    live: bool = True,
    today: dt.date | None = None,
) -> dict[str, Any]:
    """Process ``rtd-projects.json`` and write ``adoption.json`` and the history."""
    today = today or dt.datetime.now(dt.UTC).date()
    _, projects = read_rtd_projects(data_dir / "rtd-projects.json")
    if only:
        projects = [p for p in projects if p.slug in set(only)]
    if limit:
        projects = projects[:limit]
    if not projects:
        raise DataError("No projects to process")

    cache = Cache(cache_dir)
    github = GitHub(github_token, cache)
    upstream = Upstream(github, config.sphinx_stack_repo)
    catalogue: Catalogue | None = None
    try:
        catalogue = Catalogue.load(cache, config.ulwazi_package)
    except (FetchError, KeyError, ValueError) as error:
        LOG.warning("Ulwazi release fingerprints unavailable: %s", error)
    services = Services(config, github, upstream, catalogue, upstream.latest())

    previous_path = data_dir / ADOPTION_FILE
    previous: dict[str, Any] = {}
    if previous_path.is_file():
        previous = {p["slug"]: p for p in read_json(previous_path).get("projects", [])}

    records = process_projects(
        projects, services, previous=previous, today=today, live=live
    )
    latest_ulwazi = (
        catalogue.releases[-1].version if catalogue and catalogue.releases else None
    )
    summary = summarize(
        records,
        latest_stack=services.latest_stack,
        latest_ulwazi=latest_ulwazi,
        today=today,
    )

    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "tracking_mode": config.mode,
        "summary": summary,
        "projects": sorted(records, key=lambda r: r["name"].lower()),
    }
    attempted = [
        r for r in records if r["scope"]["reason"] not in ("opted_out", "not_included")
    ]
    ratio = summary["errors"] / len(attempted) if attempted else 0.0
    partial = bool(only or limit)
    if ratio > config.max_error_ratio:
        write_json(data_dir / REJECTED_FILE, payload)
        raise PublishRefusedError(
            f"{summary['errors']} of {len(attempted)} projects failed "
            f"({ratio:.0%} > {config.max_error_ratio:.0%}); the previous data is kept. "
            f"Details: {data_dir / REJECTED_FILE}"
        )
    if partial:
        out = data_dir / "adoption.partial.json"
        write_json(out, payload)
        LOG.info("Partial run (--only/--limit): wrote %s, history untouched", out)
        return payload
    history = update_history(data_dir / HISTORY_FILE, summary)
    payload["summary"]["deltas"] = deltas(summary, history, today=today)
    write_json(previous_path, payload)
    LOG.info(
        "Wrote %s: %d projects, %d tracked, %.1f%% on Ulwazi (%d GitHub API calls)",
        previous_path,
        summary["total"],
        summary["sphinx_stack"],
        summary["ulwazi_percent"],
        github.api_calls,
    )
    return payload


__all__ = ["PublishRefusedError", "in_scope", "run"]
