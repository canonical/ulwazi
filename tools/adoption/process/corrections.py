"""Known upstream problems that make the Sphinx Stack version file unreliable.

The Sphinx Stack records its version in ``docs/_dev/version``. The ``3.0``
release shipped that file still saying ``2.0``, so every project that updated
to 3.0 reports 2.0. The correction below recognises such projects from changes
that only the 3.0 release made and reports 3.0 instead.

**Choosing signs.** A sign must come from the release itself, not just from a
commit made after the previous tag: between 2.0 and 3.0, ``main`` gained
``_dev/check_removed_urls.py``, a new ``_dev/update_sp.py`` and the new
Makefile months before 3.0, and ``update_sp.py`` copies itself from ``main``.
Projects that synced from ``main`` (or just ran the updater) have those files
but are still on 2.0. Every sign is therefore checked against upstream before
use: it must hold at the release tag and must *not* hold at ``baseline``, the
last upstream commit before the release changes. Signs that fail this check are
ignored, with a warning.

**Retiring a correction:** delete its entry from :data:`KNOWN_ISSUES`. It also
switches itself off as soon as the upstream tag no longer ships the stale file.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field

from tools.adoption.models import Evidence
from tools.adoption.process.github import RepoFiles, join
from tools.adoption.process.requirements import (
    Req,
    normalize_name,
    parse_requirements_txt,
)
from tools.adoption.process.ulwazi_repo import ConfFacts, parse_conf
from tools.adoption.process.upstream import Upstream

LOG = logging.getLogger("adoption")

VERSION_FILE = "docs/_dev/version"
UPSTREAM_DOCS = "docs"


@dataclass
class Probe:
    """Everything a correction may look at."""

    files: RepoFiles
    docs: str
    upstream: Upstream
    _requirements: dict[str, Req] | None = field(default=None, repr=False)
    _conf: ConfFacts | None = field(default=None, repr=False)

    def requirements(self) -> dict[str, Req]:
        """Return ``<docs>/requirements.txt`` as a mapping (empty if missing)."""
        if self._requirements is None:
            text = self.files.read(join(self.docs, "requirements.txt")) or ""
            self._requirements = parse_requirements_txt(text)
        return self._requirements

    def conf(self) -> ConfFacts:
        """Return what ``<docs>/conf.py`` sets (empty if missing)."""
        if self._conf is None:
            self._conf = parse_conf(self.files.read(join(self.docs, "conf.py")) or "")
        return self._conf


@dataclass(frozen=True)
class Sign:
    """One observable change made by a release."""

    text: str  # shown in the evidence
    check: Callable[[Probe], bool]


@dataclass(frozen=True)
class Correction:
    """A version that replaces the declared one, with the reasons."""

    version: str
    declared: str
    evidence: list[Evidence]


@dataclass(frozen=True)
class VersionIssue:
    """A release whose version file is known to be wrong.

    A project is corrected when at least one ``required`` sign and at least
    ``min_supporting`` ``supporting`` signs hold.
    """

    declared: str  # what the stale file says
    actual: str  # the release that really ships it
    tag: str  # upstream tag to self-check against
    baseline: str  # last upstream commit (full id) before the release changes
    required: tuple[Sign, ...]
    supporting: tuple[Sign, ...]
    min_supporting: int = 1


def _accepts_only_newer(name: str, accepts: str, rejects: str) -> Sign:
    def check(probe: Probe) -> bool:
        req = probe.requirements().get(normalize_name(name))
        return bool(
            req and not req.vcs and req.accepts(accepts) and not req.accepts(rejects)
        )

    return Sign(f"requirements.txt needs {name} >= {accepts}", check)


def _ulwazi_requirement(probe: Probe) -> bool:
    requirements = probe.requirements()
    return "ulwazi" in requirements and "canonical-sphinx" not in requirements


def _ulwazi_extension(probe: Probe) -> bool:
    extensions = probe.conf().extensions
    return "ulwazi" in extensions and "canonical_sphinx" not in extensions


def _modern_pdf_style(probe: Probe) -> bool:
    return (
        "sphinx-modern-pdf-style" in probe.requirements()
        or "sphinx_modern_pdf_style" in probe.conf().extensions
    )


# Sphinx Stack 3.0: everything below was introduced on 2026-10-16 by #634,
# #646 and #650 ("incorporate Ulwazi 1.0"), right before the tag.
KNOWN_ISSUES: tuple[VersionIssue, ...] = (
    VersionIssue(
        declared="2.0",
        actual="3.0",
        tag="3.0",
        baseline="cfc887196ebfd8aed0a0ed69515e524a133a4308",  # #643, 2026-10-05
        required=(
            Sign(
                "requirements.txt lists ulwazi instead of canonical-sphinx",
                _ulwazi_requirement,
            ),
            Sign(
                "conf.py loads the ulwazi extension instead of canonical_sphinx",
                _ulwazi_extension,
            ),
        ),
        supporting=(
            _accepts_only_newer("sphinx-roles", "1.0", "0.1"),
            _accepts_only_newer("sphinx-terminal", "1.1", "1.0"),
            _accepts_only_newer("sphinx-llm", "1.1", "0.4"),
            Sign("uses sphinx-modern-pdf-style (added in 3.0)", _modern_pdf_style),
        ),
    ),
)


def _upstream_probe(upstream: Upstream, ref: str) -> Probe:
    files = RepoFiles(upstream.github, upstream.owner, upstream.name, ref)
    return Probe(files=files, docs=UPSTREAM_DOCS, upstream=upstream)


def verified_signs(
    issue: VersionIssue, upstream: Upstream
) -> tuple[list[Sign], list[Sign]]:
    """Return the required and supporting signs that really mark the release.

    A sign qualifies only if it holds at the release tag and not at the
    baseline commit. The result is computed once per upstream object.
    """
    key = (issue.tag, issue.baseline)
    if key not in upstream.memo:
        at_tag = _upstream_probe(upstream, issue.tag)
        before = _upstream_probe(upstream, issue.baseline)
        groups: list[list[Sign]] = []
        for signs in (issue.required, issue.supporting):
            kept = []
            for sign in signs:
                if sign.check(at_tag) and not sign.check(before):
                    kept.append(sign)
                else:
                    LOG.warning(
                        "Ignoring Sphinx Stack %s sign %r: it does not separate "
                        "the %s tag from upstream commit %s",
                        issue.actual,
                        sign.text,
                        issue.tag,
                        issue.baseline[:7],
                    )
            groups.append(kept)
        upstream.memo[key] = (groups[0], groups[1])
    return upstream.memo[key]  # type: ignore[return-value]


def correct_version(
    declared: str, probe: Probe, issues: tuple[VersionIssue, ...] = KNOWN_ISSUES
) -> Correction | None:
    """Return the real version when ``declared`` matches a known upstream problem."""
    for issue in issues:
        if declared != issue.declared:
            continue
        shipped = probe.upstream.file_at_tag(issue.tag, VERSION_FILE)
        if (
            shipped is None
            or shipped.decode("utf-8", "replace").strip() != issue.declared
        ):
            continue  # upstream fixed the tag: nothing to correct
        required, supporting = verified_signs(issue, probe.upstream)
        found_required = [sign.text for sign in required if sign.check(probe)]
        found_supporting = [sign.text for sign in supporting if sign.check(probe)]
        if not found_required or len(found_supporting) < issue.min_supporting:
            continue
        return Correction(
            issue.actual,
            declared,
            [
                Evidence(
                    "Version corrected",
                    f"Version file says {declared}, but this is a known upstream "
                    f"problem: Sphinx Stack {issue.tag} still ships "
                    f"'{declared}'. Detected {issue.actual} from: "
                    + "; ".join(found_required + found_supporting),
                )
            ],
        )
    return None
