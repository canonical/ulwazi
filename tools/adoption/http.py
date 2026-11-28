"""A small, polite HTTP client built on the standard library."""

from __future__ import annotations

import json
import logging
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from tools.adoption import USER_AGENT

LOG = logging.getLogger("adoption")

RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
MAX_BODY_BYTES = 8 * 1024 * 1024
HTTP_OK = 200
HTTP_NOT_FOUND = 404


class FetchError(Exception):
    """Raised when a request cannot be completed (network failure, retries used)."""


@dataclass
class Response:
    """The outcome of a request. HTTP error statuses are values, not exceptions."""

    status: int
    body: bytes
    url: str
    headers: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        """True for a 2xx status."""
        return 200 <= self.status < 300  # noqa: PLR2004

    def text(self) -> str:
        """Decode the body as UTF-8."""
        return self.body.decode("utf-8", errors="replace")

    def json(self) -> Any:  # noqa: ANN401
        """Decode the body as JSON."""
        return json.loads(self.body)


class RateLimiter:
    """Enforce a minimum interval between requests, across threads."""

    def __init__(self, min_interval: float = 0.0) -> None:
        self._min_interval = min_interval
        self._lock = threading.Lock()
        self._next_allowed = 0.0

    def wait(self) -> None:
        """Block until the next request may be sent."""
        if self._min_interval <= 0:
            return
        with self._lock:
            now = time.monotonic()
            delay = self._next_allowed - now
            self._next_allowed = max(now, self._next_allowed) + self._min_interval
        if delay > 0:
            time.sleep(delay)


def request(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
    timeout: float = 30.0,
    retries: int = 3,
    max_bytes: int = MAX_BODY_BYTES,
    limiter: RateLimiter | None = None,
) -> Response:
    """Send a request and return the response, retrying transient failures.

    HTTP statuses such as 403 or 404 are returned for the caller to interpret.
    Only network-level failures (after retries) raise :class:`FetchError`.
    """
    if not url.startswith("https://"):
        raise FetchError(f"Refusing to fetch non-HTTPS URL: {url}")
    all_headers = {"User-Agent": USER_AGENT, "Accept": "*/*", **(headers or {})}
    last_error = "unknown error"
    for attempt in range(retries + 1):
        if limiter is not None:
            limiter.wait()
        req = urllib.request.Request(  # noqa: S310
            url, data=data, headers=all_headers, method=method
        )
        retry_after = 0.0
        try:
            with urllib.request.urlopen(req, timeout=timeout) as raw:  # noqa: S310
                body = raw.read(max_bytes + 1)
                if len(body) > max_bytes:
                    raise FetchError(f"{url} is larger than {max_bytes} bytes")
                return Response(
                    raw.status, body, raw.geturl(), dict(raw.headers.items())
                )
        except urllib.error.HTTPError as error:
            body = error.read(max_bytes)
            response = Response(error.code, body, url, dict(error.headers.items()))
            if error.code not in RETRY_STATUSES:
                return response
            last_error = f"HTTP {error.code}"
            try:
                retry_after = float(error.headers.get("Retry-After", "0"))
            except ValueError:
                retry_after = 0.0
            if attempt == retries:
                return response
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as error:
            last_error = str(getattr(error, "reason", error))
            if attempt == retries:
                raise FetchError(f"{url}: {last_error}") from error
        delay = max(retry_after, 2.0**attempt)
        LOG.debug("Retrying %s in %.0fs (%s)", url, delay, last_error)
        time.sleep(min(delay, 60.0))
    raise FetchError(f"{url}: {last_error}")  # pragma: no cover
