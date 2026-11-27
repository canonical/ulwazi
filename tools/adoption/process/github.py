"""GitHub access: batched repository metadata and cached raw file reads."""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote

from tools.adoption.cache import Cache
from tools.adoption.http import HTTP_NOT_FOUND, FetchError, RateLimiter, request

LOG = logging.getLogger("adoption")

API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"
GRAPHQL_BATCH = 40
TAG_CACHE_SECONDS = 24 * 3600
_FULL_OID = re.compile(r"^[0-9a-f]{40}$")
_SAFE_NAME = re.compile(r"^[\w.-]+$")
# Errors GitHub reports for repositories we may not see; treated as "not public".
_HIDDEN_ERROR_TYPES = frozenset({"NOT_FOUND", "FORBIDDEN"})


class GitHubError(Exception):
    """Raised when GitHub cannot answer a request we depend on."""


@dataclass(frozen=True)
class RepoInfo:
    """Metadata of a repository that is visible without special permissions."""

    owner: str
    name: str
    url: str
    archived: bool
    private: bool
    default_branch: str | None
    head_oid: str | None
    head_date: str | None


def find_token() -> str | None:
    """Return a GitHub token from the environment or the ``gh`` CLI."""
    for variable in ("GITHUB_TOKEN", "GH_TOKEN"):
        if token := os.environ.get(variable):
            return token
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() or None if result.returncode == 0 else None


class GitHub:
    """GitHub GraphQL/REST client plus a cache of raw file contents."""

    def __init__(self, token: str | None, cache: Cache) -> None:
        self._token = token
        self._cache = cache
        self._raw_limiter = RateLimiter(0.02)
        self.api_calls = 0

    # -- authenticated API -------------------------------------------------

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _rest(self, path: str) -> Any:  # noqa: ANN401
        self.api_calls += 1
        response = request(f"{API}{path}", headers=self._headers())
        if response.status == HTTP_NOT_FOUND:
            return None
        if not response.ok:
            raise GitHubError(f"GitHub API returned HTTP {response.status} for {path}")
        return response.json()

    def _graphql(self, query: str) -> dict[str, Any]:
        if not self._token:
            raise GitHubError(
                "A GitHub token is required (set GITHUB_TOKEN or run 'gh auth login')"
            )
        self.api_calls += 1
        response = request(
            f"{API}/graphql",
            method="POST",
            headers={**self._headers(), "Content-Type": "application/json"},
            data=json.dumps({"query": query}).encode("utf-8"),
            timeout=60,
        )
        if not response.ok:
            raise GitHubError(f"GitHub GraphQL returned HTTP {response.status}")
        payload = response.json()
        errors = [
            error
            for error in payload.get("errors") or []
            if not (error.get("type") in _HIDDEN_ERROR_TYPES and error.get("path"))
        ]
        if errors:
            raise GitHubError(f"GitHub GraphQL error: {errors[0].get('message')}")
        return payload.get("data") or {}

    @staticmethod
    def _alias(index: int, owner: str, name: str) -> str:
        if not (_SAFE_NAME.match(owner) and _SAFE_NAME.match(name)):
            raise GitHubError(f"Unsupported repository name: {owner}/{name}")
        return f"r{index}: repository(owner: {json.dumps(owner)}, name: {json.dumps(name)})"

    def repo_infos(
        self, repos: Sequence[tuple[str, str]]
    ) -> dict[tuple[str, str], RepoInfo | None]:
        """Look up repositories in batches. ``None`` means not visible (or private)."""
        result: dict[tuple[str, str], RepoInfo | None] = {}
        unique = list(dict.fromkeys(repos))
        for start in range(0, len(unique), GRAPHQL_BATCH):
            batch = unique[start : start + GRAPHQL_BATCH]
            fields = (
                "isArchived isPrivate url nameWithOwner "
                "defaultBranchRef { name target { ... on Commit { oid committedDate } } }"
            )
            body = " ".join(
                f"{self._alias(i, owner, name)} {{ {fields} }}"
                for i, (owner, name) in enumerate(batch)
            )
            data = self._graphql(f"query {{ {body} }}")
            for i, key in enumerate(batch):
                node = data.get(f"r{i}")
                if not node or node.get("isPrivate"):
                    result[key] = None
                    continue
                branch = node.get("defaultBranchRef") or {}
                target = branch.get("target") or {}
                full = str(node.get("nameWithOwner") or "/".join(key))
                owner, _, name = full.partition("/")
                result[key] = RepoInfo(
                    owner=owner,
                    name=name,
                    url=str(node.get("url") or f"https://github.com/{full}"),
                    archived=bool(node.get("isArchived")),
                    private=False,
                    default_branch=branch.get("name"),
                    head_oid=target.get("oid"),
                    head_date=target.get("committedDate"),
                )
        return result

    def docs_commit_dates(
        self, items: Sequence[tuple[str, str, str, str]]
    ) -> dict[tuple[str, str, str, str], str | None]:
        """Return the date of the last commit that touched ``path`` at ``oid``.

        ``items`` are ``(owner, name, oid, path)``; ``path`` ``"."`` means the
        whole repository.
        """
        result: dict[tuple[str, str, str, str], str | None] = {}
        unique = list(dict.fromkeys(items))
        for start in range(0, len(unique), GRAPHQL_BATCH):
            batch = unique[start : start + GRAPHQL_BATCH]
            parts: list[str] = []
            for i, (owner, name, oid, path) in enumerate(batch):
                if not _FULL_OID.match(oid):
                    raise GitHubError(f"Not a commit id: {oid}")
                history_args = "first: 1" + (
                    "" if path == "." else f", path: {json.dumps(path)}"
                )
                parts.append(
                    f'{self._alias(i, owner, name)} {{ object(oid: "{oid}") '
                    f"{{ ... on Commit {{ history({history_args}) "
                    "{ nodes { committedDate } } } } }"
                )
            data = self._graphql("query { " + " ".join(parts) + " }")
            for i, key in enumerate(batch):
                node = ((data.get(f"r{i}") or {}).get("object") or {}).get("history")
                nodes = (node or {}).get("nodes") or []
                result[key] = nodes[0]["committedDate"] if nodes else None
        return result

    def releases(self, repo: str) -> list[dict[str, Any]]:
        """List published releases of ``owner/name``."""
        data = self._rest(f"/repos/{repo}/releases?per_page=100")
        if not isinstance(data, list):
            raise GitHubError(f"Cannot list releases of {repo}")
        return [item for item in data if isinstance(item, dict)]  # pyright: ignore[reportUnknownVariableType]

    def tree(self, owner: str, name: str, oid: str) -> list[str]:
        """List every file path at ``oid`` (may be truncated for huge repositories)."""
        data = self._rest(f"/repos/{owner}/{name}/git/trees/{oid}?recursive=1")
        if not isinstance(data, dict):
            return []
        return [
            str(entry["path"])
            for entry in data.get("tree", [])  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
            if entry.get("type") == "blob"  # pyright: ignore[reportUnknownMemberType]
        ]

    # -- raw files ---------------------------------------------------------

    def raw(self, owner: str, name: str, ref: str, path: str) -> bytes | None:
        """Read a file at ``ref`` (a commit id is cached forever, a tag for a day)."""
        immutable = bool(_FULL_OID.match(ref))
        key = f"{owner}/{name}@{ref}:{path}"
        hit = self._cache.get(
            "raw", key, max_age=None if immutable else TAG_CACHE_SECONDS
        )
        if hit is not None:
            return hit.data
        url = f"{RAW}/{owner}/{name}/{quote(ref, safe='')}/{quote(path)}"
        try:
            response = request(url, limiter=self._raw_limiter, timeout=30)
        except FetchError as error:
            raise GitHubError(str(error)) from error
        if response.status == HTTP_NOT_FOUND:
            self._cache.put("raw", key, None)
            return None
        if not response.ok:
            raise GitHubError(f"HTTP {response.status} reading {owner}/{name}:{path}")
        self._cache.put("raw", key, response.body)
        return response.body


@dataclass
class RepoFiles:
    """Read files from one repository at one commit."""

    github: GitHub
    owner: str
    name: str
    ref: str
    _tree: list[str] | None = field(default=None, repr=False)

    def read_bytes(self, path: str) -> bytes | None:
        """Return a file's bytes, or ``None`` if it does not exist."""
        return self.github.raw(self.owner, self.name, self.ref, path.removeprefix("./"))

    def read(self, path: str) -> str | None:
        """Return a file's text, or ``None`` if it does not exist."""
        data = self.read_bytes(path)
        return None if data is None else data.decode("utf-8", errors="replace")

    def exists(self, path: str) -> bool:
        """Return True if the file exists."""
        return self.read_bytes(path) is not None

    def tree(self) -> list[str]:
        """List all file paths (one API request, cached on the object)."""
        if self._tree is None:
            self._tree = self.github.tree(self.owner, self.name, self.ref)
        return self._tree

    def url(self, path: str, *, kind: str = "blob") -> str:
        """Return the github.com URL of a path at this commit."""
        base = f"https://github.com/{self.owner}/{self.name}"
        if path in (".", ""):
            return f"{base}/tree/{self.ref}"
        return f"{base}/{kind}/{self.ref}/{quote(path)}"


def join(directory: str, relative: str) -> str:
    """Join a docs directory (``"."`` for the root) and a relative path."""
    return relative if directory in (".", "") else f"{directory.rstrip('/')}/{relative}"
