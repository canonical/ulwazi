"""Unit tests for the Ulwazi-native notfound_urls_prefix computation.

The helper ``ulwazi._notfound_urls_prefix`` was absorbed from the
canonical-sphinx-config extension. It must mirror the URL schema of the
hosting site, which varies per project:

- single-version projects serve at the root: ``/<slug>/``
- versioned projects add a version segment: ``/<slug>/<version>/``
- translated projects add a language segment: ``/<slug>/<language>/<version>/``

``READTHEDOCS_VERSION`` and ``READTHEDOCS_LANGUAGE`` are always set on
Read the Docs builds, even when the corresponding segment is absent from
the URL schema, so the helper detects the schema from
``READTHEDOCS_CANONICAL_URL`` instead of appending them unconditionally.

The prefix must start and end with a slash so that links on the 404 page
resolve regardless of the depth at which the 404 page is served (see the
sphinx-stack production bug where a missing slug produced broken links on
every 404 page).

All scenarios run through a single parametrised test: each case in
``CASES`` carries a descriptive ``id`` and a comment documenting its
rationale.
"""

from __future__ import annotations

from typing import Any

import pytest
from ulwazi import _notfound_urls_prefix

RTD_VARS = (
    "READTHEDOCS_CANONICAL_URL",
    "READTHEDOCS_VERSION",
    "READTHEDOCS_LANGUAGE",
)


@pytest.fixture(autouse=True)
def _clean_rtd_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure no Read the Docs environment leaks into or between tests."""
    for var in RTD_VARS:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def prefix(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest) -> str:
    """Compute the prefix for the case passed indirectly via ``request.param``.

    ``request.param`` is a dict with two keys:

    - ``slug``: the project slug config value
    - ``env``: the Read the Docs environment variables for the case

    Environment variables are set through monkeypatch so they are reverted
    automatically after each test.
    """
    case: dict[str, Any] = request.param
    for var, value in case["env"].items():
        monkeypatch.setenv(var, value)

    class _Config:
        """Minimal stand-in for the Sphinx config object."""

        def __init__(self, slug: str) -> None:
            self.slug = slug

    return _notfound_urls_prefix(_Config(case["slug"]))  # type: ignore[arg-type]


CASES = [
    # Off Read the Docs (no canonical URL): the prefix is empty so links on
    # the 404 page stay relative and work under `make run` / file:// access.
    pytest.param(
        {"slug": "", "env": {}},
        "",
        id="no-rtd-env",
    ),
    # A slug alone must not produce a prefix either: the prefix only applies
    # on RTD builds, because sphinx-notfound-page absolutises every link on
    # the 404 page with it and would break local builds.
    pytest.param(
        {"slug": "ulwazi", "env": {}},
        "",
        id="slug-without-rtd-env",
    ),
    # Single-version projects serve at the root of the canonical URL.
    # READTHEDOCS_VERSION and READTHEDOCS_LANGUAGE are still set on the build
    # machine, but the canonical URL has no version or language segment, so
    # neither may appear in the prefix (this is how ulwazi itself is hosted).
    pytest.param(
        {
            "slug": "ulwazi",
            "env": {
                "READTHEDOCS_CANONICAL_URL": "https://canonical-ulwazi.readthedocs-hosted.com/",
                "READTHEDOCS_VERSION": "main",
                "READTHEDOCS_LANGUAGE": "en",
            },
        },
        "/ulwazi/",
        id="single-version-schema",
    ),
    # Versioned projects add the version segment to the canonical URL.
    pytest.param(
        {
            "slug": "ulwazi",
            "env": {
                "READTHEDOCS_CANONICAL_URL": "https://canonical-ulwazi.readthedocs-hosted.com/latest/",
                "READTHEDOCS_VERSION": "latest",
                "READTHEDOCS_LANGUAGE": "en",
            },
        },
        "/ulwazi/latest/",
        id="versioned-schema",
    ),
    # Translated projects add language and version segments.
    pytest.param(
        {
            "slug": "ulwazi",
            "env": {
                "READTHEDOCS_CANONICAL_URL": "https://canonical-ulwazi.readthedocs-hosted.com/fr/latest/",
                "READTHEDOCS_VERSION": "latest",
                "READTHEDOCS_LANGUAGE": "fr",
            },
        },
        "/ulwazi/fr/latest/",
        id="translated-schema",
    ),
    # If the RTD version is not the canonical URL's last segment, the URL
    # schema has no version segment and the env value must not leak in.
    pytest.param(
        {
            "slug": "ulwazi",
            "env": {
                "READTHEDOCS_CANONICAL_URL": "https://canonical-ulwazi.readthedocs-hosted.com/",
                "READTHEDOCS_VERSION": "1.2",
            },
        },
        "/ulwazi/",
        id="version-mismatch-ignored",
    ),
    # If the RTD language is not the segment right before the version, the
    # URL schema has no language segment and the env value must not leak in.
    pytest.param(
        {
            "slug": "ulwazi",
            "env": {
                "READTHEDOCS_CANONICAL_URL": "https://canonical-ulwazi.readthedocs-hosted.com/latest/",
                "READTHEDOCS_VERSION": "latest",
                "READTHEDOCS_LANGUAGE": "en",
            },
        },
        "/ulwazi/latest/",
        id="language-mismatch-ignored",
    ),
    # On RTD without a slug, the prefix is just the schema segments.
    pytest.param(
        {
            "slug": "",
            "env": {
                "READTHEDOCS_CANONICAL_URL": "https://docs.example.com/en/latest/",
                "READTHEDOCS_VERSION": "latest",
                "READTHEDOCS_LANGUAGE": "en",
            },
        },
        "/en/latest/",
        id="rtd-env-without-slug",
    ),
    # A user-supplied slug with stray slashes is normalised.
    pytest.param(
        {
            "slug": "/ulwazi/",
            "env": {
                "READTHEDOCS_CANONICAL_URL": "https://canonical-ulwazi.readthedocs-hosted.com/latest/",
                "READTHEDOCS_VERSION": "latest",
            },
        },
        "/ulwazi/latest/",
        id="slug-stray-slashes-normalised",
    ),
]


@pytest.mark.parametrize(("prefix", "expected"), CASES, indirect=["prefix"])
def test_notfound_prefix(prefix: str, expected: str) -> None:
    """The prefix mirrors the hosting site's URL schema (see ``CASES``).

    Every expected value is an exact string, which also enforces the
    invariant sphinx-notfound-page validates: the prefix is either empty or
    starts and ends with a slash. Getting it wrong silently breaks every
    link on the 404 page.
    """
    assert prefix == expected
