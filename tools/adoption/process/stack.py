"""Detect which Sphinx Stack version a documentation folder uses."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from tools.adoption.models import Evidence
from tools.adoption.process.corrections import Probe, correct_version
from tools.adoption.process.github import RepoFiles, join
from tools.adoption.process.locate import DocsLocation
from tools.adoption.process.upstream import Upstream

LEGACY_LABEL = "< 1.0"
LEGACY_MARKERS = (
    "custom_conf.py",
    ".sphinx/requirements.txt",
    ".sphinx/get_vale_conf.py",
    ".sphinx/spellingcheck.yaml",
)
_VERSION = re.compile(r"^\d+(?:\.\d+)*$")


@dataclass
class StackResult:
    """The Sphinx Stack finding for one project."""

    detected: bool = False
    kind: str = "none"  # "released", "legacy" or "none"
    version: str | None = None  # the version to show
    declared: str | None = None  # what the version file says
    corrected: bool = False
    is_latest: bool = False
    version_file: str | None = None
    version_file_url: str | None = None
    evidence: list[Evidence] = field(default_factory=list)


def detect_stack(
    files: RepoFiles,
    docs: DocsLocation | None,
    upstream: Upstream,
    *,
    latest: str | None,
    correct: bool = True,
) -> StackResult:
    """Detect the Sphinx Stack version.

    The version file is authoritative. A known upstream problem is corrected
    only with supporting evidence (see :mod:`tools.adoption.process.corrections`).
    """
    result = StackResult()
    if docs is None:
        result.evidence.append(
            Evidence("Documentation folder", "Not found in the repository")
        )
        return result
    result.evidence.append(
        Evidence(
            "Documentation folder",
            f"{docs.path} (found by: {docs.how})",
            files.url(docs.path, kind="tree"),
        )
    )

    if docs.version_file:
        text = (files.read(docs.version_file) or "").strip()
        result.version_file = docs.version_file
        result.version_file_url = files.url(docs.version_file)
        if _VERSION.match(text):
            result.detected = True
            result.kind = "released"
            result.declared = result.version = text
            result.evidence.append(
                Evidence(
                    "Version file",
                    f"{docs.version_file} says {text}",
                    result.version_file_url,
                )
            )
            if correct:
                probe = Probe(files=files, docs=docs.path, upstream=upstream)
                if correction := correct_version(text, probe):
                    result.version = correction.version
                    result.corrected = True
                    result.evidence.extend(correction.evidence)
            result.is_latest = result.version == latest
            return result
        result.evidence.append(
            Evidence(
                "Version file",
                f"{docs.version_file} has unexpected content and was ignored",
                result.version_file_url,
            )
        )

    for marker in LEGACY_MARKERS:
        if files.exists(join(docs.path, marker)):
            result.detected = True
            result.kind = "legacy"
            result.version = LEGACY_LABEL
            result.evidence.append(
                Evidence(
                    "Legacy Starter Pack",
                    f"No version file, but {marker} exists (Starter Pack before 1.0)",
                    files.url(join(docs.path, marker)),
                )
            )
            return result
    result.evidence.append(
        Evidence("Sphinx Stack", "No version file or Starter Pack files found")
    )
    return result
