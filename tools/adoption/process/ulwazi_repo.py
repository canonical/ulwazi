"""Find out from a repository whether it is set up to use Ulwazi."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field

from tools.adoption.models import Evidence
from tools.adoption.process.github import RepoFiles, join
from tools.adoption.process.locate import DocsLocation, python_requirements
from tools.adoption.process.requirements import (
    Req,
    parse_pyproject,
    parse_requirements_txt,
)

PACKAGE = "ulwazi"
DYNAMIC_THEME = "<dynamic>"
_THEME_FALLBACK = re.compile(
    r"""^\s*html_theme\s*=\s*['"]([\w.-]+)['"]""", re.MULTILINE
)


@dataclass
class ConfFacts:
    """What ``conf.py`` sets, as far as it can be read without running it."""

    theme: str | None = None
    extensions: set[str] = field(default_factory=set)


@dataclass
class RepoUlwazi:
    """What the repository says about Ulwazi."""

    theme: str | None = None
    extension_enabled: bool = False
    requirement: Req | None = None
    requirement_file: str | None = None
    evidence: list[Evidence] = field(default_factory=list)

    @property
    def uses_theme(self) -> bool:
        """True if ``html_theme`` is Ulwazi."""
        return self.theme == PACKAGE


def _strings(node: ast.expr) -> list[str]:
    if isinstance(node, ast.List | ast.Tuple | ast.Set):
        return [
            item.value
            for item in node.elts
            if isinstance(item, ast.Constant) and isinstance(item.value, str)
        ]
    return []


def parse_conf(source: str) -> ConfFacts:
    """Read ``html_theme`` and ``extensions`` from a ``conf.py`` using ``ast``."""
    facts = ConfFacts()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        if match := _THEME_FALLBACK.search(source):
            facts.theme = match[1]
        facts.extensions = (
            {PACKAGE} if re.search(r"""['"]ulwazi['"]""", source) else set()
        )
        return facts
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue
                if target.id == "html_theme":
                    value = node.value
                    facts.theme = (
                        value.value
                        if isinstance(value, ast.Constant)
                        and isinstance(value.value, str)
                        else DYNAMIC_THEME
                    )
                elif target.id == "extensions":
                    facts.extensions = set(_strings(node.value))
        elif (
            isinstance(node, ast.AugAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "extensions"
        ):
            facts.extensions |= set(_strings(node.value))
        elif (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and isinstance(node.value.func.value, ast.Name)
            and node.value.func.value.id == "extensions"
        ):
            for argument in node.value.args:
                facts.extensions |= set(_strings(argument))
                if isinstance(argument, ast.Constant) and isinstance(
                    argument.value, str
                ):
                    facts.extensions.add(argument.value)
    return facts


def _requirement_files(docs: str, rtd_yaml: str | None) -> list[str]:
    paths = list(python_requirements(rtd_yaml)) if rtd_yaml else []
    paths += [
        join(docs, "requirements.txt"),
        join(docs, ".sphinx/requirements.txt"),
        join(docs, "pyproject.toml"),
    ]
    return list(dict.fromkeys(paths))


def analyse_repo(
    files: RepoFiles, docs: DocsLocation | None, rtd_yaml: str | None
) -> RepoUlwazi:
    """Inspect ``conf.py`` and the requirements for Ulwazi."""
    result = RepoUlwazi()
    if docs is None:
        return result
    for name in ("conf.py", "custom_conf.py"):
        path = join(docs.path, name)
        source = files.read(path)
        if source is None:
            continue
        facts = parse_conf(source)
        if facts.theme is None and name == "custom_conf.py":
            continue
        result.theme = facts.theme
        result.extension_enabled = PACKAGE in facts.extensions
        if facts.theme:
            result.evidence.append(
                Evidence(
                    "Theme",
                    f"{path} sets html_theme = {facts.theme!r}",
                    files.url(path),
                )
            )
        break
    for path in _requirement_files(docs.path, rtd_yaml):
        text = files.read(path)
        if text is None:
            continue
        found = (
            parse_pyproject(text)
            if path.endswith(".toml")
            else parse_requirements_txt(text)
        )
        if requirement := found.get(PACKAGE):
            result.requirement = requirement
            result.requirement_file = path
            result.evidence.append(
                Evidence(
                    "Requirement",
                    f"{path} requires ulwazi ({requirement.display})",
                    files.url(path),
                )
            )
            break
    return result
