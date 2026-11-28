"""Parse dependency declarations from ``requirements.txt`` and ``pyproject.toml``."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass

from packaging.requirements import InvalidRequirement, Requirement
from packaging.specifiers import InvalidSpecifier, SpecifierSet

_EGG = re.compile(r"[#&]egg=([A-Za-z0-9_.-]+)")
_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*")


@dataclass(frozen=True)
class Req:
    """A declared dependency."""

    name: str
    specifier: str
    vcs: bool = False

    def accepts(self, version: str) -> bool:
        """Return True if ``version`` satisfies the specifier."""
        if self.vcs:
            return True
        try:
            return SpecifierSet(self.specifier).contains(version, prereleases=True)
        except InvalidSpecifier:
            return False

    @property
    def display(self) -> str:
        """A short, human-readable form such as ``~=1.0`` or ``git``."""
        return "git" if self.vcs else (self.specifier or "any version")


def normalize_name(name: str) -> str:
    """Normalise a distribution name (PEP 503)."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _parse_line(line: str) -> Req | None:
    text = line.strip()
    if not text or text.startswith(("#", "-r", "--", "-c")):
        return None
    if text.startswith("-e"):
        text = text[2:].strip()
    egg = _EGG.search(text)
    if text.startswith(("git+", "http://", "https://")) and egg:
        return Req(normalize_name(egg[1]), "", vcs=True)
    text = re.sub(r"\s+#.*$", "", text)
    try:
        requirement = Requirement(text)
    except InvalidRequirement:
        match = _NAME.match(text)
        return Req(normalize_name(match[0]), "") if match else None
    return Req(
        normalize_name(requirement.name),
        str(requirement.specifier),
        vcs=bool(requirement.url),
    )


def parse_requirements_txt(text: str) -> dict[str, Req]:
    """Parse the lines of a requirements file, ignoring options and comments."""
    found: dict[str, Req] = {}
    for line in text.splitlines():
        if (req := _parse_line(line)) is not None:
            found.setdefault(req.name, req)
    return found


def parse_pyproject(text: str) -> dict[str, Req]:
    """Collect dependencies from ``[project]`` and ``[dependency-groups]``."""
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return {}
    lines: list[str] = []
    project = data.get("project", {})
    lines.extend(project.get("dependencies", []))
    for group in project.get("optional-dependencies", {}).values():
        lines.extend(group)
    for group in data.get("dependency-groups", {}).values():
        lines.extend(item for item in group if isinstance(item, str))
    found: dict[str, Req] = {}
    for line in lines:
        if (req := _parse_line(line)) is not None:
            found.setdefault(req.name, req)
    return found
