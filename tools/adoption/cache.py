"""A tiny file cache keyed by arbitrary strings."""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

MISSING = b"\x00adoption-cache-missing\x00"


@dataclass(frozen=True)
class Cached:
    """A cache hit. ``data`` is ``None`` when a 404 was cached."""

    data: bytes | None
    age: float


class Cache:
    """Store bytes under ``<dir>/<namespace>/<sha256(key)>``.

    A missing remote file is cached as a marker so it is not requested again.
    Writes are atomic so parallel workers and interrupted runs are safe.
    """

    def __init__(self, directory: Path | None) -> None:
        self.directory = directory

    def _path(self, namespace: str, key: str) -> Path | None:
        if self.directory is None:
            return None
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.directory / namespace / digest[:2] / digest

    def get(
        self, namespace: str, key: str, *, max_age: float | None = None
    ) -> Cached | None:
        """Return the cached entry, or ``None`` if absent or older than ``max_age``."""
        path = self._path(namespace, key)
        if path is None or not path.is_file():
            return None
        age = time.time() - path.stat().st_mtime
        if max_age is not None and age > max_age:
            return None
        data = path.read_bytes()
        return Cached(None if data == MISSING else data, age)

    def put(self, namespace: str, key: str, data: bytes | None) -> None:
        """Store ``data`` (``None`` records that the resource does not exist)."""
        path = self._path(namespace, key)
        if path is None:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        # Unique per write: worker threads may store the same key concurrently.
        temporary = path.with_name(f"{path.name}.{uuid.uuid4().hex}.tmp")
        temporary.write_bytes(MISSING if data is None else data)
        temporary.replace(path)
