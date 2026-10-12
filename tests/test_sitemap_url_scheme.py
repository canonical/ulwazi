"""Sitemap URLs in the sample configuration match the Read the Docs URL schema.

sphinx-sitemap builds each URL as ``html_baseurl`` followed by
``sitemap_url_scheme``, with ``{version}`` filled in from the Sphinx config.
``docs/conf.py`` and the copyable ``docs/default-conf.py`` must therefore add
only the path segments that Read the Docs actually serves.

Like the 404 prefix (see ``tests/test_notfound_prefix.py``), both files detect
those segments from ``READTHEDOCS_CANONICAL_URL``. ``READTHEDOCS_VERSION`` and
``READTHEDOCS_LANGUAGE`` are set on every Read the Docs build, even for
single-version projects whose URLs contain neither segment; appending the
version unconditionally published sitemap URLs such as
``/ulwazi/main/content/...`` that do not exist.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

import pytest

DOCS = Path(__file__).resolve().parents[1] / "docs"
CONF_FILES = ("conf.py", "default-conf.py")
LINK = "content/myst-cheat-sheet/"
RTD_VARS = (
    "READTHEDOCS",
    "READTHEDOCS_CANONICAL_URL",
    "READTHEDOCS_GIT_IDENTIFIER",
    "READTHEDOCS_LANGUAGE",
    "READTHEDOCS_VERSION",
    "READTHEDOCS_VERSION_TYPE",
)

CASES = [
    # Manual builds keep a placeholder segment, so a locally built sitemap
    # never looks like the published one.
    pytest.param({}, "MANUAL/", id="local-build"),
    # Single-version projects (how ulwazi itself is hosted): RTD still sets
    # the version and language variables, but the URL has neither segment.
    pytest.param(
        {
            "READTHEDOCS_CANONICAL_URL": "https://canonical-ulwazi.readthedocs-hosted.com/",
            "READTHEDOCS_VERSION": "main",
            "READTHEDOCS_LANGUAGE": "en",
        },
        "",
        id="single-version-schema",
    ),
    # Versioned projects serve each version under its own segment.
    pytest.param(
        {
            "READTHEDOCS_CANONICAL_URL": "https://canonical-ulwazi.readthedocs-hosted.com/latest/",
            "READTHEDOCS_VERSION": "latest",
            "READTHEDOCS_LANGUAGE": "en",
        },
        "latest/",
        id="versioned-schema",
    ),
    # Translated projects add a language segment before the version.
    pytest.param(
        {
            "READTHEDOCS_CANONICAL_URL": "https://canonical-ulwazi.readthedocs-hosted.com/fr/latest/",
            "READTHEDOCS_VERSION": "latest",
            "READTHEDOCS_LANGUAGE": "fr",
        },
        "fr/latest/",
        id="translated-schema",
    ),
]


def _sitemap_url(conf: str) -> tuple[str, str]:
    """Return (html_baseurl, sitemap URL of LINK) as sphinx-sitemap builds it."""
    namespace = runpy.run_path(str(DOCS / conf))
    version = namespace.get("version") or ""
    language = namespace.get("language") or "en"
    base = namespace["html_baseurl"]
    url = base + namespace["sitemap_url_scheme"].format(
        lang=f"{language}/", version=f"{version}/" if version else "", link=LINK
    )
    return base, url


@pytest.mark.parametrize(("env", "segments"), CASES)
def test_sitemap_url_scheme(
    monkeypatch: pytest.MonkeyPatch, env: dict[str, str], segments: str
) -> None:
    """Both sample configurations produce sitemap URLs that exist when hosted."""
    for var in RTD_VARS:
        monkeypatch.delenv(var, raising=False)
    for var, value in env.items():
        monkeypatch.setenv(var, value)
    # Sphinx runs conf.py from its own directory; docs/conf.py also extends
    # sys.path, which must not leak into other tests.
    monkeypatch.chdir(DOCS)
    monkeypatch.setattr(sys, "path", list(sys.path))

    errors = []
    for conf in CONF_FILES:
        base, url = _sitemap_url(conf)
        expected = base + segments + LINK
        if url != expected:
            errors.append(f"[docs/{conf}] expected {expected}, got {url}")
    assert not errors, "Sitemap URL checks failed:\n  - " + "\n  - ".join(errors)
