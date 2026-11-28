"""Inspect a project's published documentation for Ulwazi fingerprints."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from tools.adoption.http import FetchError, request
from tools.adoption.process.ulwazi_releases import PRIMARY_ASSET

MAX_PAGE_BYTES = 2 * 1024 * 1024
_ASSET_LINK = re.compile(
    r"""(?:href|src)\s*=\s*["'][^"']*?_static/(?P<path>[^"'?#]+)\?v=(?P<crc>[0-9a-f]{8})["']"""
)
_THEME_SCRIPT_MARKER = "ulwazi-theme"


@dataclass
class LiveResult:
    """What the live documentation page shows."""

    checked: bool = False
    ok: bool = False
    status: int | None = None
    error: str | None = None
    final_url: str | None = None
    uses_ulwazi: bool = False
    assets: dict[str, str] = field(default_factory=dict)


def parse_page(html: str) -> tuple[bool, dict[str, str]]:
    """Return ``(uses_ulwazi, {asset path: checksum})`` found in a page's HTML."""
    assets = {m["path"]: m["crc"] for m in _ASSET_LINK.finditer(html)}
    uses = PRIMARY_ASSET in assets or _THEME_SCRIPT_MARKER in html
    return uses, assets


def check_live(url: str) -> LiveResult:
    """Fetch ``url`` and look for the Ulwazi stylesheet and theme script."""
    result = LiveResult(checked=True)
    try:
        response = request(url, timeout=20, retries=1, max_bytes=MAX_PAGE_BYTES)
    except FetchError as error:
        result.error = str(error)
        return result
    result.status = response.status
    result.final_url = response.url
    if not response.ok:
        result.error = f"HTTP {response.status}"
        return result
    result.ok = True
    result.uses_ulwazi, result.assets = parse_page(response.text())
    return result
