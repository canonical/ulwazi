"""Unit tests for the Ulwazi-native notfound_urls_prefix computation.

The helper ``ulwazi._notfound_urls_prefix`` was absorbed from the
canonical-sphinx-config extension. The prefix must start and end with a
slash so that links on the 404 page resolve regardless of the depth at
which the 404 is served (see the sphinx-stack production bug where a
missing slug produced broken links on every 404 page).
"""

from __future__ import annotations

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
def prefix(monkeypatch: pytest.MonkeyPatch):
    """Return a callable computing the prefix for a slug and RTD environment.

    Environment variables are set through monkeypatch so they are reverted
    automatically after each test.
    """

    def _compute(slug: str = "", **rtd_env: str) -> str:
        for var, value in rtd_env.items():
            monkeypatch.setenv(var, value)

        class _Config:
            """Minimal stand-in for the Sphinx config object."""

            def __init__(self, slug: str) -> None:
                self.slug = slug

        return _notfound_urls_prefix(_Config(slug))  # type: ignore[arg-type]

    return _compute


def test_no_rtd_env(prefix):
    """Outside Read the Docs, the prefix is empty (links stay relative)."""
    assert prefix() == ""


def test_slug_without_rtd_env(prefix):
    """A slug alone does not produce a prefix: it only applies on RTD builds,
    because sphinx-notfound-page absolutises every link with it and would
    break local builds (make run, file:// access)."""
    assert prefix(slug="ulwazi") == ""


def test_slug_with_trailing_slash_normalised(prefix):
    """A user-supplied slug with stray slashes is normalised."""
    assert (
        prefix(
            slug="/ulwazi/",
            READTHEDOCS_CANONICAL_URL="https://documentation.ubuntu.com/ulwazi/latest/",
            READTHEDOCS_VERSION="latest",
        )
        == "/ulwazi/latest/"
    )


def test_slug_and_version(prefix):
    """On RTD with a versioned URL, the version segment is appended."""
    assert (
        prefix(
            slug="ulwazi",
            READTHEDOCS_CANONICAL_URL="https://documentation.ubuntu.com/ulwazi/latest/",
            READTHEDOCS_VERSION="latest",
        )
        == "/ulwazi/latest/"
    )


def test_slug_language_and_version(prefix):
    """On RTD with language and version segments, both are appended."""
    assert (
        prefix(
            slug="ulwazi",
            READTHEDOCS_CANONICAL_URL="https://documentation.ubuntu.com/ulwazi/en/latest/",
            READTHEDOCS_VERSION="latest",
            READTHEDOCS_LANGUAGE="en",
        )
        == "/ulwazi/en/latest/"
    )


def test_version_mismatch_ignored(prefix):
    """If the RTD version is not the URL's version segment, it is ignored."""
    assert (
        prefix(
            slug="ulwazi",
            READTHEDOCS_CANONICAL_URL="https://documentation.ubuntu.com/ulwazi/latest/",
            READTHEDOCS_VERSION="1.2",
        )
        == "/ulwazi/"
    )


def test_rtd_env_without_slug(prefix):
    """On RTD without a slug, the prefix is just the language/version affix."""
    assert (
        prefix(
            READTHEDOCS_CANONICAL_URL="https://docs.example.com/en/latest/",
            READTHEDOCS_VERSION="latest",
            READTHEDOCS_LANGUAGE="en",
        )
        == "/en/latest/"
    )


@pytest.mark.parametrize(
    ("slug", "rtd_env"),
    [
        ("ulwazi", {}),
        ("", {}),
        (
            "ulwazi",
            {
                "READTHEDOCS_CANONICAL_URL": "https://x.io/ulwazi/latest/",
                "READTHEDOCS_VERSION": "latest",
            },
        ),
        (
            "ulwazi",
            {
                "READTHEDOCS_CANONICAL_URL": "https://x.io/ulwazi/en/latest/",
                "READTHEDOCS_VERSION": "latest",
                "READTHEDOCS_LANGUAGE": "en",
            },
        ),
        (
            "",
            {
                "READTHEDOCS_CANONICAL_URL": "https://x.io/en/latest/",
                "READTHEDOCS_VERSION": "latest",
                "READTHEDOCS_LANGUAGE": "en",
            },
        ),
    ],
)
def test_prefix_always_slash_delimited(prefix, slug: str, rtd_env: dict[str, str]):
    """The prefix must always start and end with a slash (or be empty).

    This is the invariant sphinx-notfound-page validates; getting it wrong
    silently breaks every link on the 404 page.
    """
    result = prefix(slug=slug, **rtd_env)
    assert result == "" or (result.startswith("/") and result.endswith("/"))
