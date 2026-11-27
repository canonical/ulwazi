"""Combine repository and live-site findings into the Ulwazi result."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from tools.adoption.models import Evidence
from tools.adoption.process.live_site import LiveResult
from tools.adoption.process.ulwazi_releases import (
    PRIMARY_ASSET,
    Catalogue,
    describe_range,
)
from tools.adoption.process.ulwazi_repo import RepoUlwazi

STATE_LIVE = "live"  # the published site serves Ulwazi
STATE_REPO = "repo"  # the repository uses Ulwazi; the live site could not be checked
STATE_PENDING = "pending"  # the repository uses Ulwazi but the live site does not yet
STATE_NONE = "none"


@dataclass
class UlwaziResult:
    """The Ulwazi finding for one project."""

    uses: bool = False
    state: str = STATE_NONE
    version: str | None = None  # shown as N/A when None
    precision: str | None = None  # exact, range, estimated, dev, manual
    repo_theme: str | None = None
    requirement: str | None = None
    requirement_file: str | None = None
    live_checked: bool = False
    live_ok: bool = False
    live_error: str | None = None
    since: str | None = None
    evidence: list[Evidence] = field(default_factory=list)


def resolve_ulwazi(
    repo: RepoUlwazi | None,
    live: LiveResult | None,
    catalogue: Catalogue | None,
    *,
    built_at: dt.datetime | None = None,
    pinned: str | None = None,
) -> UlwaziResult:
    """Decide whether and which Ulwazi version a project uses.

    The live site is the source of truth: it shows what readers get. When it
    cannot be checked, the repository's theme setting decides and the version
    is the newest release allowed by the requirement (an estimate).
    """
    result = UlwaziResult()
    if repo is not None:
        result.repo_theme = repo.theme
        result.evidence.extend(repo.evidence)
        if repo.requirement is not None:
            result.requirement = repo.requirement.display
            result.requirement_file = repo.requirement_file
    repo_uses = bool(repo and repo.uses_theme)
    if live is not None and live.checked:
        result.live_checked = True
        result.live_ok = live.ok
        result.live_error = live.error

    if pinned:
        result.uses, result.state = True, STATE_LIVE
        result.version, result.precision = pinned, "manual"
        result.evidence.append(
            Evidence("Manual override", f"Version pinned to {pinned}")
        )
        return result

    if live is not None and live.ok:
        if live.uses_ulwazi:
            result.uses, result.state = True, STATE_LIVE
            _version_from_live(result, live, catalogue)
        elif repo_uses:
            result.state = STATE_PENDING
            result.evidence.append(
                Evidence(
                    "Not deployed yet",
                    "The repository sets html_theme to ulwazi, but the published "
                    "documentation does not serve it yet",
                )
            )
        return result

    if live is not None and live.error:
        result.evidence.append(
            Evidence("Live site", f"Could not be checked: {live.error}")
        )
    if repo_uses:
        result.uses, result.state = True, STATE_REPO
        _version_from_requirement(result, repo, catalogue, built_at)
    return result


def _version_from_live(
    result: UlwaziResult, live: LiveResult, catalogue: Catalogue | None
) -> None:
    primary = live.assets.get(PRIMARY_ASSET)
    if catalogue is None or primary is None:
        result.evidence.append(
            Evidence("Live site", "Serves Ulwazi; the version could not be determined")
        )
        return
    matches = catalogue.match(live.assets)
    if matches is None:
        return
    if not matches:
        result.version, result.precision = "dev", "dev"
        result.evidence.append(
            Evidence(
                "Live site",
                f"Stylesheet checksum {primary} matches no published release "
                "(an unreleased build)",
            )
        )
        return
    result.version, result.precision = describe_range(matches)
    result.evidence.append(
        Evidence(
            "Live site",
            f"Stylesheet checksum {primary} matches Ulwazi {result.version}",
        )
    )


def _version_from_requirement(
    result: UlwaziResult,
    repo: RepoUlwazi | None,
    catalogue: Catalogue | None,
    built_at: dt.datetime | None,
) -> None:
    requirement = repo.requirement if repo else None
    if requirement is None:
        result.evidence.append(
            Evidence("Version", "No ulwazi requirement found; the version is unknown")
        )
        return
    if requirement.vcs:
        result.version, result.precision = "dev", "dev"
        return
    release = (
        catalogue.newest_matching(requirement.specifier, built_at)
        if catalogue
        else None
    )
    if release is not None:
        result.version, result.precision = release.version, "estimated"
        result.evidence.append(
            Evidence(
                "Estimated version",
                f"Newest release allowed by '{requirement.display}'"
                + (" before the last build" if built_at else ""),
            )
        )
