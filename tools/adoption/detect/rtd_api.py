"""Read the Docs API v3 client for the detection layer."""

from __future__ import annotations

import datetime as dt
import json
import logging
from collections.abc import Iterator
from typing import Any
from urllib.parse import urlencode, urljoin

from tools.adoption.cache import Cache
from tools.adoption.detect.normalize import (
    is_public,
    is_translation,
    pick,
    project_from_record,
)
from tools.adoption.http import RateLimiter, request
from tools.adoption.models import RtdProject

LOG = logging.getLogger("adoption")

# Read the Docs allows 60 authenticated requests per minute.
MIN_INTERVAL = 1.05
PAGE_SIZE = 100
BUILD_CACHE_SECONDS = 20 * 3600
BUILD_PAGE_SIZE = 25


class RtdError(Exception):
    """Raised when the Read the Docs API cannot be used."""


class RtdClient:
    """Minimal API v3 client with rate limiting and caching."""

    def __init__(self, base_url: str, token: str, cache: Cache) -> None:
        self.base_url = base_url.rstrip("/")
        self._headers = {
            "Authorization": f"Token {token}",
            "Accept": "application/json",
        }
        self._limiter = RateLimiter(MIN_INTERVAL)
        self._cache = cache

    def _get(self, url: str) -> dict[str, Any]:
        response = request(url, headers=self._headers, limiter=self._limiter)
        if response.status in (401, 403):
            raise RtdError(
                f"Read the Docs refused the token (HTTP {response.status}) for {self.base_url}"
            )
        if not response.ok:
            raise RtdError(f"Read the Docs returned HTTP {response.status} for {url}")
        data = response.json()
        if not isinstance(data, dict):
            raise RtdError(f"Unexpected response from {url}")
        return data  # pyright: ignore[reportUnknownVariableType]

    def list_projects(self, organization: str) -> Iterator[dict[str, Any]]:
        """Yield every project item, following pagination."""
        path = (
            f"/api/v3/organizations/{organization}/projects/"
            if organization
            else "/api/v3/projects/"
        )
        url: str | None = f"{self.base_url}{path}?{urlencode({'limit': PAGE_SIZE})}"
        while url:
            page = self._get(url)
            yield from page.get("results", [])
            next_url = page.get("next")
            url = urljoin(self.base_url + "/", next_url) if next_url else None

    def detail(self, slug: str, modified: str | None) -> dict[str, Any]:
        """Fetch project details (privacy level, config path), cached by ``modified``."""
        key = f"{slug}@{modified or 'unknown'}"
        if modified:
            hit = self._cache.get("rtd-detail", key)
            if hit and hit.data:
                return json.loads(hit.data)
        data = self._get(f"{self.base_url}/api/v3/projects/{slug}/")
        if modified:
            self._cache.put("rtd-detail", key, json.dumps(data).encode("utf-8"))
        return data

    def last_successful_build(
        self, slug: str, version: str | None
    ) -> tuple[str, str | None] | None:
        """Return ``(finished, commit)`` of the newest successful build, if any."""
        hit = self._cache.get("rtd-build", slug, max_age=BUILD_CACHE_SECONDS)
        if hit and hit.data:
            cached = json.loads(hit.data)
            return (cached["finished"], cached.get("commit")) if cached else None
        query = urlencode({"limit": BUILD_PAGE_SIZE, "running": "false"})
        page = self._get(f"{self.base_url}/api/v3/projects/{slug}/builds/?{query}")
        found: tuple[str, str | None] | None = None
        for build in page.get("results", []):
            if not build.get("success") or not build.get("finished"):
                continue
            if version and build.get("version") not in (version, None):
                continue
            found = (str(build["finished"]), build.get("commit"))
            break
        payload = {"finished": found[0], "commit": found[1]} if found else None
        self._cache.put("rtd-build", slug, json.dumps(payload).encode("utf-8"))
        return found

    def version_privacy(self, slug: str, version: str) -> str | None:
        """Return the ``privacy_level`` of one version (Business only), cached."""
        key = f"{slug}@{version}"
        hit = self._cache.get("rtd-version", key, max_age=BUILD_CACHE_SECONDS)
        if hit and hit.data:
            return json.loads(hit.data).get("privacy_level")
        data = self._get(f"{self.base_url}/api/v3/projects/{slug}/versions/{version}/")
        level = data.get("privacy_level")
        payload = {"privacy_level": level}
        self._cache.put("rtd-version", key, json.dumps(payload).encode("utf-8"))
        return None if level is None else str(level)


def docs_are_public(client: RtdClient, item: dict[str, Any]) -> bool:
    """Return True when a private project serves its default version publicly.

    On Read the Docs Business the project's ``privacy_level`` and each
    version's ``privacy_level`` are separate settings. A project can be private
    in the dashboard while its documentation is public (Ulwazi's own docs are
    set up like this). Any doubt, including an API error, counts as private.
    """
    if str(pick(item, "privacy_level") or "").lower() != "private":
        return False
    slug, version = pick(item, "slug"), pick(item, "default_version")
    if not slug or not version:
        return False
    try:
        level = client.version_privacy(str(slug), str(version))
    except RtdError as error:
        LOG.debug("Version privacy unknown, treating the project as private: %s", error)
        return False
    return str(level or "").lower() == "public"


def detect_from_api(
    client: RtdClient,
    organization: str,
    *,
    include_builds: bool = True,
    assume_public: bool = False,
    limit: int | None = None,
) -> list[RtdProject]:
    """List public projects. Private projects are dropped and never named."""
    projects: dict[str, RtdProject] = {}
    private = translations = public_docs = 0
    for listed in client.list_projects(organization):
        if is_translation(listed):
            translations += 1
            continue
        item = listed
        if "privacy_level" not in item and "readthedocs_yaml_path" not in item:
            item = {
                **item,
                **client.detail(str(item.get("slug")), item.get("modified")),
            }
        if not is_public(item, base_url=client.base_url, assume_public=assume_public):
            if not docs_are_public(client, item):
                private += 1
                continue
            public_docs += 1
        project = project_from_record(item, base_url=client.base_url)
        if project is None:
            continue
        if include_builds:
            build = client.last_successful_build(
                project.slug, pick(item, "default_version")
            )
            if build:
                project.last_build_at, project.last_build_commit = build
        projects[project.slug] = project
        if limit and len(projects) >= limit:
            break
    LOG.info(
        "Detected %d public projects (%d private projects with public docs "
        "included, %d translations folded, %d non-public skipped)",
        len(projects),
        public_docs,
        translations,
        private,
    )
    return list(projects.values())


def parse_timestamp(value: str | None) -> dt.datetime | None:
    """Parse an ISO-8601 timestamp (``Z`` or an offset) into an aware datetime."""
    if not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.UTC)
