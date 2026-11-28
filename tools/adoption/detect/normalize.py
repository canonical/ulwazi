"""Turn heterogeneous Read the Docs records into :class:`RtdProject` objects."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from tools.adoption.models import RtdProject

_SCP_LIKE = re.compile(r"^(?:[\w.-]+@)?(?P<host>[\w.-]+):(?P<path>[^/].*)$")


def pick(record: dict[str, Any], *names: str) -> Any:  # noqa: ANN401
    """Return the first non-empty value among ``names`` (dotted names are nested)."""
    for name in names:
        value: Any = record
        for part in name.split("."):
            value = value.get(part) if isinstance(value, dict) else None  # pyright: ignore[reportUnknownMemberType]
        if value not in (None, ""):
            return value
    return None


def parse_repo_url(url: str | None) -> tuple[str, str | None, str | None] | None:
    """Split a repository URL into ``(host, owner, name)``.

    Understands https, ``git://``, ``ssh://`` and scp-like (``git@host:o/r``)
    URLs. ``owner`` and ``name`` are ``None`` unless the path has two segments.
    """
    if not url:
        return None
    text = url.strip()
    host: str
    path: str
    if "://" in text:
        parsed = urlparse(text)
        host, path = (parsed.hostname or ""), parsed.path
    else:
        match = _SCP_LIKE.match(text)
        if not match:
            return None
        host, path = match["host"], match["path"]
    host = host.lower().removeprefix("www.")
    if not host:
        return None
    segments = [
        part for part in path.removesuffix("/").removesuffix(".git").split("/") if part
    ]
    if len(segments) == 2:  # noqa: PLR2004
        return host, segments[0], segments[1]
    return host, None, None


def project_from_record(record: dict[str, Any], *, base_url: str) -> RtdProject | None:
    """Build a project from an API item or a flat (CSV/JSON export) record."""
    slug = pick(record, "slug", "project_slug", "project")
    if not slug:
        return None
    slug = str(slug).strip()
    repo_raw = pick(
        record,
        "repository.url",
        "repository_url",
        "repo_url",
        "repository",
        "repo",
    )
    parsed = parse_repo_url(str(repo_raw)) if repo_raw else None
    repo_url = repo_host = repo_owner = repo_name = None
    if parsed:
        repo_host, repo_owner, repo_name = parsed
        repo_url = (
            f"https://{repo_host}/{repo_owner}/{repo_name}"
            if repo_owner and repo_name
            else f"https://{repo_host}/"
        )
    docs_url = pick(
        record,
        "urls.documentation",
        "docs_url",
        "documentation_url",
        "documentation",
        "url",
    )
    if not docs_url:
        docs_url = (
            f"https://{slug}.readthedocs.io/"
            if "readthedocs.org" in base_url
            else f"https://{slug}.readthedocs-hosted.com/"
        )
    language = pick(record, "language.code", "language")
    return RtdProject(
        slug=slug,
        name=str(pick(record, "name", "project_name") or slug).strip(),
        docs_url=str(docs_url).replace("http://", "https://", 1),
        repo_url=repo_url,
        repo_host=repo_host,
        repo_owner=repo_owner,
        repo_name=repo_name,
        default_branch=pick(record, "default_branch"),
        readthedocs_yaml_path=pick(record, "readthedocs_yaml_path"),
        language=str(language) if language else None,
        subproject_of=_slug_of(pick(record, "subproject_of")),
    )


def _slug_of(value: Any) -> str | None:  # noqa: ANN401
    """Older API versions embed the parent project; newer ones give the slug."""
    if isinstance(value, dict):
        value = value.get("slug")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    return str(value) if value else None  # pyright: ignore[reportUnknownArgumentType]


def is_translation(record: dict[str, Any]) -> bool:
    """Return True for translations, which are folded into their parent project."""
    return pick(record, "translation_of") is not None


def is_public(record: dict[str, Any], *, base_url: str, assume_public: bool) -> bool:
    """Decide whether a project is public on Read the Docs.

    ``privacy_level`` exists only on Read the Docs Business. A record without it
    counts as public on Read the Docs Community (everything there is public) or
    when the caller explicitly vouches for the data; otherwise it is dropped.
    """
    level = pick(record, "privacy_level")
    if level is not None:
        return str(level).lower() == "public"
    return assume_public or "readthedocs.org" in base_url
