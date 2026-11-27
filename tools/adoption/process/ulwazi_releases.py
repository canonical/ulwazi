"""Fingerprint Ulwazi releases so a live site's version can be recognised.

Sphinx appends ``?v=<crc32>`` to the local stylesheets and scripts it links,
where the checksum covers the file content without carriage returns. Computing
the same checksums for every published wheel gives each release a fingerprint
that can be compared with the links of a live documentation page.
"""

from __future__ import annotations

import datetime as dt
import io
import json
import logging
import zipfile
import zlib
from dataclasses import dataclass, field

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version

from tools.adoption.cache import Cache
from tools.adoption.http import FetchError, request

LOG = logging.getLogger("adoption")

PYPI = "https://pypi.org/pypi"
STATIC_PREFIX = "ulwazi/theme/ulwazi/static/"
PRIMARY_ASSET = "css/vanilla-main.css"
ASSET_SUFFIXES = (".css", ".js")
CARRIAGE_RETURN = b"\r"


def asset_checksum(content: bytes) -> str:
    """Return Sphinx's asset checksum (``zlib.crc32`` without carriage returns)."""
    checksum = zlib.crc32(content.translate(None, CARRIAGE_RETURN))
    return f"{checksum:08x}"


@dataclass(frozen=True)
class Release:
    """A published Ulwazi release and the checksums of its static assets."""

    version: str
    uploaded: dt.datetime
    assets: dict[str, str] = field(hash=False)


def _fingerprint_wheel(wheel: bytes) -> dict[str, str]:
    assets: dict[str, str] = {}
    with zipfile.ZipFile(io.BytesIO(wheel)) as archive:
        for name in archive.namelist():
            if name.startswith(STATIC_PREFIX) and name.endswith(ASSET_SUFFIXES):
                assets[name.removeprefix(STATIC_PREFIX)] = asset_checksum(
                    archive.read(name)
                )
    return assets


class Catalogue:
    """The fingerprints of all non-yanked Ulwazi releases."""

    def __init__(self, releases: list[Release]) -> None:
        self.releases = sorted(releases, key=lambda r: Version(r.version))
        self.owned_paths = {path for r in self.releases for path in r.assets}

    @classmethod
    def load(cls, cache: Cache, package: str = "ulwazi") -> Catalogue:
        """Build the catalogue from PyPI, downloading only unseen wheels."""
        response = request(f"{PYPI}/{package}/json", timeout=30)
        if not response.ok:
            raise FetchError(f"PyPI returned HTTP {response.status} for {package}")
        data = response.json()
        releases: list[Release] = []
        for version, files in data.get("releases", {}).items():
            try:
                Version(version)
            except InvalidVersion:
                continue
            wheels = [
                f
                for f in files
                if f.get("packagetype") == "bdist_wheel" and not f.get("yanked")
            ]
            if not wheels:
                continue
            wheel = wheels[0]
            sha256 = wheel["digests"]["sha256"]
            hit = cache.get("ulwazi-assets", sha256)
            if hit and hit.data:
                assets = json.loads(hit.data)
            else:
                LOG.info("Fingerprinting Ulwazi %s", version)
                download = request(wheel["url"], timeout=120)
                if not download.ok:
                    raise FetchError(f"Cannot download Ulwazi {version}")
                assets = _fingerprint_wheel(download.body)
                cache.put("ulwazi-assets", sha256, json.dumps(assets).encode("utf-8"))
            uploaded = dt.datetime.fromisoformat(
                wheel["upload_time_iso_8601"].replace("Z", "+00:00")
            )
            releases.append(Release(version, uploaded, assets))
        return cls(releases)

    def match(self, observed: dict[str, str]) -> list[Release] | None:
        """Return the releases that fit the checksums seen on a live page.

        ``None`` means the page lacks the primary stylesheet, so nothing can be
        said. An empty list means no published release matches (a development
        build). The primary stylesheet decides; other assets only narrow the
        result, because a project may override one of them.
        """
        primary = observed.get(PRIMARY_ASSET)
        if primary is None:
            return None
        candidates = [
            r for r in self.releases if r.assets.get(PRIMARY_ASSET) == primary
        ]
        narrowed = [
            r
            for r in candidates
            if all(
                r.assets[path] == checksum
                for path, checksum in observed.items()
                if path in r.assets
            )
        ]
        return narrowed or candidates

    def newest_matching(
        self, specifier: str, built_before: dt.datetime | None = None
    ) -> Release | None:
        """Return the newest release satisfying ``specifier``.

        Releases uploaded after ``built_before`` are skipped when an older match
        exists, because the build cannot have installed a newer release.
        """
        try:
            spec = SpecifierSet(specifier)
        except InvalidSpecifier:
            return None
        matching = [r for r in self.releases if spec.contains(r.version)]
        if built_before is not None:
            earlier = [r for r in matching if r.uploaded <= built_before]
            matching = earlier or matching
        return matching[-1] if matching else None


def describe_range(releases: list[Release]) -> tuple[str, str]:
    """Return ``(label, precision)`` for one or several matching releases."""
    if len(releases) == 1:
        return releases[0].version, "exact"
    return f"{releases[0].version}\u2013{releases[-1].version}", "range"
