"""Facts about the upstream Sphinx Stack repository."""

from __future__ import annotations

import hashlib
import logging

from packaging.version import InvalidVersion, Version

from tools.adoption.process.github import GitHub

LOG = logging.getLogger("adoption")


def git_blob_sha(data: bytes) -> str:
    """Return the Git object id of file content (``git hash-object``)."""
    return hashlib.sha1(  # noqa: S324 - Git object ids are SHA-1 by definition
        b"blob %d\x00" % len(data) + data
    ).hexdigest()


def sort_versions(versions: list[str]) -> list[str]:
    """Sort dotted version strings, oldest first; unparsable ones are dropped."""
    parsed: list[tuple[Version, str]] = []
    for text in versions:
        try:
            parsed.append((Version(text), text))
        except InvalidVersion:
            continue
    return [text for _, text in sorted(parsed)]


class Upstream:
    """Reads release tags and tagged files of the Sphinx Stack repository."""

    def __init__(self, github: GitHub, repo: str) -> None:
        self.github = github
        self.repo = repo
        self.owner, _, self.name = repo.partition("/")
        self._versions: list[str] | None = None
        # Per-run results derived from upstream files (see corrections.py).
        self.memo: dict[object, object] = {}

    def versions(self) -> list[str]:
        """Return published (non-draft, non-prerelease) release tags, oldest first."""
        if self._versions is None:
            tags = [
                str(release["tag_name"])
                for release in self.github.releases(self.repo)
                if not release.get("draft") and not release.get("prerelease")
            ]
            self._versions = sort_versions(tags)
            LOG.info("Sphinx Stack releases: %s", ", ".join(self._versions))
        return self._versions

    def latest(self) -> str | None:
        """Return the newest release tag."""
        versions = self.versions()
        return versions[-1] if versions else None

    def file_at_tag(self, tag: str, path: str) -> bytes | None:
        """Read a file as it was at release ``tag``."""
        return self.github.raw(self.owner, self.name, tag, path)

    def text_at_tag(self, tag: str, path: str) -> str | None:
        """Read a text file as it was at release ``tag``."""
        data = self.file_at_tag(tag, path)
        return None if data is None else data.decode("utf-8", errors="replace")
