"""Find the documentation folder of a repository."""

from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass

from tools.adoption.process.github import RepoFiles, join

VERSION_FILES = ("_dev/version", ".sphinx/version")
RTD_CONFIG_FILES = (".readthedocs.yaml", ".readthedocs.yml")
FALLBACK_DIRECTORIES = ("docs", "doc", "documentation", ".")
_CONFIGURATION = re.compile(r"^\s+configuration\s*:\s*(?P<value>.+?)\s*$")
_REQUIREMENTS = re.compile(r"^\s*-?\s*requirements\s*:\s*(?P<value>.+?)\s*$")
_TOP_LEVEL_KEY = re.compile(r"^(?P<key>[A-Za-z_]\w*)\s*:")


@dataclass(frozen=True)
class DocsLocation:
    """Where the documentation lives and how that was found."""

    path: str  # "." for the repository root
    how: str
    version_file: str | None = None  # repository-relative path of the version file


def _clean(value: str) -> str:
    return re.sub(r"\s+#.*$", "", value).strip().strip("'\"")


def sphinx_configuration(rtd_yaml: str) -> str | None:
    """Return ``sphinx.configuration`` from a ``.readthedocs.yaml`` text."""
    in_sphinx = False
    for line in rtd_yaml.splitlines():
        if top := _TOP_LEVEL_KEY.match(line):
            in_sphinx = top["key"] == "sphinx"
            continue
        if in_sphinx and (match := _CONFIGURATION.match(line)):
            value = _clean(match["value"])
            return value or None
    return None


def python_requirements(rtd_yaml: str) -> list[str]:
    """Return the requirements files listed in a ``.readthedocs.yaml`` text."""
    found = []
    for line in rtd_yaml.splitlines():
        if match := _REQUIREMENTS.match(line):
            value = _clean(match["value"])
            if value:
                found.append(value)
    return found


def read_rtd_yaml(files: RepoFiles, configured_path: str | None) -> str | None:
    """Read the project's Read the Docs configuration file."""
    candidates = [configured_path] if configured_path else []
    candidates.extend(RTD_CONFIG_FILES)
    for path in candidates:
        if path and (text := files.read(path)) is not None:
            return text
    return None


def _candidates(rtd_yaml: str | None, override: str | None) -> list[tuple[str, str]]:
    ordered: list[tuple[str, str]] = []
    if override:
        ordered.append((override.strip("/") or ".", "configured override"))
    if rtd_yaml and (configuration := sphinx_configuration(rtd_yaml)):
        ordered.append(
            (
                posixpath.dirname(configuration.removeprefix("./")) or ".",
                "sphinx.configuration in the Read the Docs file",
            )
        )
    ordered.extend((directory, "common location") for directory in FALLBACK_DIRECTORIES)
    seen: set[str] = set()
    unique = []
    for directory, how in ordered:
        if directory not in seen:
            seen.add(directory)
            unique.append((directory, how))
    return unique


def locate_docs(
    files: RepoFiles, *, rtd_yaml: str | None, override: str | None = None
) -> DocsLocation | None:
    """Find the docs folder, preferring one that has a Sphinx Stack version file.

    Order: manual override, ``sphinx.configuration`` of ``.readthedocs.yaml``,
    common folder names, and finally a scan of the repository's file list.
    """
    candidates = _candidates(rtd_yaml, override)
    for directory, how in candidates:
        for version_file in VERSION_FILES:
            path = join(directory, version_file)
            if files.exists(path):
                return DocsLocation(directory, how, path)
    for directory, how in candidates:
        if files.exists(join(directory, "conf.py")):
            return DocsLocation(directory, how)
    return _from_tree(files)


def _from_tree(files: RepoFiles) -> DocsLocation | None:
    paths = files.tree()
    for suffix in VERSION_FILES:
        matches = sorted(
            (p for p in paths if p == suffix or p.endswith(f"/{suffix}")),
            key=lambda p: (p.count("/"), p),
        )
        if matches:
            directory = matches[0][: -len(suffix)].rstrip("/") or "."
            return DocsLocation(directory, "file list scan", matches[0])
    conf_files = sorted(
        (p for p in paths if p == "conf.py" or p.endswith("/conf.py")),
        key=lambda p: (p.count("/"), p),
    )
    if conf_files:
        directory = posixpath.dirname(conf_files[0]) or "."
        return DocsLocation(directory, "file list scan")
    return None
