"""Tracking configuration: opt-out, opt-in and manual overrides."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = Path(__file__).with_name("config.toml")
MODES = ("auto", "manual")


class ConfigError(Exception):
    """Raised for an invalid ``config.toml``."""


@dataclass(frozen=True)
class Rule:
    """Match projects by slug and/or ``owner/repo`` (shell-style, case-insensitive)."""

    slug: str | None = None
    repo: str | None = None
    reason: str = ""

    def matches(self, slug: str, repo: str | None) -> bool:
        """Return True if the project matches the slug or the repository pattern."""
        if self.slug and fnmatchcase(slug.lower(), self.slug.lower()):
            return True
        return bool(self.repo and repo and fnmatchcase(repo.lower(), self.repo.lower()))


@dataclass(frozen=True)
class Override:
    """Manual correction for one project."""

    slug: str
    repo: str | None = None
    docs_path: str | None = None
    sphinx_stack: str | None = None
    ulwazi: str | None = None
    note: str = ""


@dataclass(frozen=True)
class Config:
    """Everything the tool reads from ``config.toml``."""

    rtd_base_url: str = "https://app.readthedocs.com"
    rtd_organization: str = ""
    mode: str = "auto"
    exclude: tuple[Rule, ...] = ()
    include: tuple[Rule, ...] = ()
    overrides: tuple[Override, ...] = ()
    sphinx_stack_repo: str = "canonical/sphinx-stack"
    ulwazi_package: str = "ulwazi"
    max_error_ratio: float = 0.2
    correct_known_version_issues: bool = True
    live_site_checks: bool = True
    path: Path = field(default=DEFAULT_CONFIG)

    def exclusion(self, slug: str, repo: str | None) -> Rule | None:
        """Return the first opt-out rule that matches the project."""
        return next((r for r in self.exclude if r.matches(slug, repo)), None)

    def is_included(self, slug: str, repo: str | None) -> bool:
        """In ``manual`` mode only listed projects are tracked."""
        if self.mode == "auto":
            return True
        return any(rule.matches(slug, repo) for rule in self.include)

    def override_for(self, slug: str) -> Override | None:
        """Return the manual override for a project, if any."""
        return next((o for o in self.overrides if o.slug == slug), None)


def _rules(items: list[dict[str, Any]] | None, section: str) -> tuple[Rule, ...]:
    rules: list[Rule] = []
    for index, item in enumerate(items or [], start=1):
        if not isinstance(item, dict):
            raise ConfigError(f"[[{section}]] entry {index} must be a table")
        slug = item.get("slug")
        repo = item.get("repo")
        if not slug and not repo:
            raise ConfigError(f"[[{section}]] entry {index} needs 'slug' or 'repo'")
        reason = str(item.get("reason", "")).strip()
        if section == "exclude" and not reason:
            raise ConfigError(
                f"[[exclude]] entry {index} ({slug or repo}) needs a 'reason'"
            )
        rules.append(Rule(slug=slug, repo=repo, reason=reason))
    return tuple(rules)


def load_config(path: Path | None = None) -> Config:
    """Load and validate the configuration file."""
    path = path or DEFAULT_CONFIG
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ConfigError(f"Config file {path} does not exist") from error
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"Config file {path} is not valid TOML: {error}") from error

    rtd = raw.get("rtd", {})
    tracking = raw.get("tracking", {})
    upstream = raw.get("upstream", {})
    safety = raw.get("safety", {})
    detection = raw.get("detection", {})

    mode = tracking.get("mode", "auto")
    if mode not in MODES:
        raise ConfigError(f"tracking.mode must be one of {MODES}, not {mode!r}")

    overrides: list[Override] = []
    for index, item in enumerate(raw.get("override", []), start=1):
        if "slug" not in item:
            raise ConfigError(f"[[override]] entry {index} needs 'slug'")
        overrides.append(
            Override(
                slug=item["slug"],
                repo=item.get("repo"),
                docs_path=item.get("docs_path"),
                sphinx_stack=item.get("sphinx_stack"),
                ulwazi=item.get("ulwazi"),
                note=str(item.get("note", "")),
            )
        )

    config = Config(
        rtd_base_url=str(rtd.get("base_url", Config.rtd_base_url)).rstrip("/"),
        rtd_organization=str(rtd.get("organization", "")),
        mode=mode,
        exclude=_rules(raw.get("exclude"), "exclude"),
        include=_rules(raw.get("include"), "include"),
        overrides=tuple(overrides),
        sphinx_stack_repo=str(
            upstream.get("sphinx_stack_repo", Config.sphinx_stack_repo)
        ),
        ulwazi_package=str(upstream.get("ulwazi_package", Config.ulwazi_package)),
        max_error_ratio=float(safety.get("max_error_ratio", Config.max_error_ratio)),
        correct_known_version_issues=bool(
            detection.get("correct_known_version_issues", True)
        ),
        live_site_checks=bool(detection.get("live_site_checks", True)),
        path=path,
    )
    if config.mode == "manual" and not config.include:
        raise ConfigError("tracking.mode = 'manual' needs at least one [[include]]")
    return config
