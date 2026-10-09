"""Code quality checks: repository consistency (fast) and the ``make lint`` linters (slow).

The fast checks catch drift that the linters cannot see: version lists that
must agree across files, theme templates and scripts that only fail when a
browser or Sphinx loads them, and test bookkeeping that the documentation
relies on. The slow cases run each target of ``make lint`` and report it as
a separate result, so one failing linter does not hide the others.

See ``docs/content/tests/code-quality.md``.
"""

from __future__ import annotations

import ast
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from jinja2 import TemplateSyntaxError
from jinja2.sandbox import SandboxedEnvironment

from conftest import SLOW_CATEGORY_OVERRIDES, TEST_CATEGORIES, _category
from test_python_versions import SUPPORTED_PYTHON_VERSIONS

if sys.version_info >= (3, 11):
    import tomllib
else:
    # tomllib joined the standard library in Python 3.11. On 3.10, pytest
    # itself depends on tomli (see uv.lock), so it is always installed.
    import tomli as tomllib  # pyright: ignore[reportMissingImports]

REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = REPO_ROOT / "tests"
THEME_DIR = REPO_ROOT / "ulwazi" / "theme" / "ulwazi"
INVENTORY_PAGE = REPO_ROOT / "docs" / "content" / "tests" / "index.md"
FEATURES_MANIFEST = TESTS_DIR / "features.yaml"
PYTHON_VERSIONS_WORKFLOW = (
    REPO_ROOT / ".github" / "workflows" / "test-python-versions.yaml"
)


def _lint_targets() -> list[str]:
    """Read the prerequisites of ``make lint`` so new linters are picked up."""
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    match = re.search(r"^lint:([^#\n]*)", makefile, re.MULTILINE)
    return match[1].split() if match else []


LINT_TARGETS = _lint_targets()

# Tools each lint target needs on PATH (in addition to make). A missing tool
# skips the case instead of letting common.mk's install-* targets run
# `sudo snap install` in the middle of a test session. Every target in
# `make lint` must have an entry; test_test_bookkeeping_in_sync enforces it.
REQUIRED_TOOLS: dict[str, tuple[str, ...]] = {
    "lint-ruff": ("ruff",),
    "lint-codespell": ("codespell", "uv"),
    # lint-mypy depends on setup-lint, which installs shellcheck and pyright.
    "lint-mypy": ("uv", "shellcheck", "pyright"),
    # Downloads the pinned prettier through npm on first use.
    "lint-prettier": ("npm",),
    "lint-pyright": ("uv",),
    "lint-shellcheck": ("git", "file", "shellcheck"),
    "lint-twine": ("uv",),
    "lint-uv-lockfile": ("uv",),
}
LINT_TIMEOUT = 600
OUTPUT_TAIL_LINES = 40

# Files that pin the same tool; common.mk is synced from canonical/starbase,
# so it is the reference that other pins must follow.
TOOL_PINS = {"prettier": ("common.mk", ".pre-commit-config.yaml")}

MODULE_ENTRY = re.compile(r"`(?P<file>test_\w+\.py)` \(\*\*(?P<counts>[^*]+)\*\*")
TOTALS = re.compile(
    r"\*\*Full selection:\*\* (?P<cases>\d+) cases across (?P<modules>\d+) "
    r"modules \((?P<fast>\d+) fast, (?P<slow>\d+) slow\)"
)
COLLECTED = re.compile(r"^(tests/test_\w+\.py): (\d+)$", re.MULTILINE)


def _fail(title: str, problems: list[str]) -> None:
    if problems:
        pytest.fail(
            f"{title}:\n" + "\n".join(f"- {problem}" for problem in problems),
            pytrace=False,
        )


def _version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


# ---------------------------------------------------------------------------
# Fast checks
# ---------------------------------------------------------------------------


def test_python_versions_in_sync():
    """Every declaration of the supported Python range matches the tested list."""
    supported = list(SUPPORTED_PYTHON_VERSIONS)
    floor = supported[0]
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text("utf-8"))
    tool = pyproject["tool"]
    problems = []

    if supported != sorted(supported, key=_version_key):
        problems.append(f"SUPPORTED_PYTHON_VERSIONS is not ascending: {supported}")

    requires = pyproject["project"]["requires-python"]
    match = re.fullmatch(r">=\s*(\d+\.\d+)", requires)
    if not match or match[1] != floor:
        problems.append(
            f"pyproject.toml requires-python is {requires!r}; expected '>={floor}'"
        )

    classifiers = sorted(
        (
            entry.rsplit(" :: ", 1)[1]
            for entry in pyproject["project"]["classifiers"]
            if re.fullmatch(r"Programming Language :: Python :: 3\.\d+", entry)
        ),
        key=_version_key,
    )
    if classifiers != supported:
        problems.append(
            f"pyproject.toml Python classifiers are {classifiers}; expected {supported}"
        )

    workflow = yaml.safe_load(PYTHON_VERSIONS_WORKFLOW.read_text(encoding="utf-8"))
    matrices = [
        job.get("strategy", {}).get("matrix", {}).get("python-version")
        for job in workflow["jobs"].values()
    ]
    matrices = [matrix for matrix in matrices if matrix is not None]
    if matrices != [supported]:
        problems.append(
            f"{PYTHON_VERSIONS_WORKFLOW.relative_to(REPO_ROOT)} matrix is "
            f"{matrices}; expected one matrix {supported}"
        )

    targets = {
        "[tool.ruff] target-version": (
            tool["ruff"]["target-version"],
            "py" + floor.replace(".", ""),
        ),
        "[tool.mypy] python_version": (tool["mypy"]["python_version"], floor),
        "[tool.pyright] pythonVersion": (tool["pyright"]["pythonVersion"], floor),
    }
    problems.extend(
        f"pyproject.toml {name} is {actual!r}; expected {expected!r}"
        for name, (actual, expected) in targets.items()
        if actual != expected
    )

    _fail(
        "Python version declarations disagree with SUPPORTED_PYTHON_VERSIONS "
        "(tests/test_python_versions.py)",
        problems,
    )


def test_theme_templates_parse():
    """Every theme template is valid Jinja for the environment Sphinx uses."""
    # Mirrors sphinx.jinja2glue.BuiltinTemplateLoader: a sandboxed environment
    # with the i18n extension, which provides {% trans %}.
    environment = SandboxedEnvironment(extensions=["jinja2.ext.i18n"])
    templates = sorted(THEME_DIR.rglob("*.html"))
    assert templates, f"no templates found under {THEME_DIR}"
    problems = []
    for template in templates:
        name = template.relative_to(REPO_ROOT).as_posix()
        try:
            environment.parse(
                template.read_text(encoding="utf-8"), name=name, filename=name
            )
        except TemplateSyntaxError as exc:
            problems.append(f"{name}:{exc.lineno}: {exc.message}")
    _fail("Theme templates have Jinja syntax errors", problems)


def test_theme_javascript_syntax():
    """Every theme script parses, so a typo fails before a browser test runs."""
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not on PATH; install Node.js to check theme scripts")
    scripts = sorted((THEME_DIR / "static" / "js").glob("*.js"))
    assert scripts, f"no scripts found under {THEME_DIR / 'static' / 'js'}"
    problems = []
    for script in scripts:
        result = subprocess.run(
            [node, "--check", str(script)],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        if result.returncode:
            detail = result.stderr.strip() or result.stdout.strip()
            problems.append(f"{script.relative_to(REPO_ROOT)}:\n{detail}")
    _fail("Theme JavaScript has syntax errors", problems)


def test_tool_versions_in_sync():
    """A tool pinned in several files uses the same version everywhere."""
    problems = []
    for tool, files in TOOL_PINS.items():
        pins = {
            name: set(
                re.findall(
                    rf"{tool}@(\d+(?:\.\d+)*)",
                    (REPO_ROOT / name).read_text(encoding="utf-8"),
                )
            )
            for name in files
        }
        problems.extend(
            f"{name}: no {tool}@<version> pin found"
            for name, versions in pins.items()
            if not versions
        )
        reference, *others = files
        expected = pins[reference]
        problems.extend(
            f"{name} pins {tool} {sorted(pins[name])}; {reference} pins "
            f"{sorted(expected)}"
            for name in others
            if pins[name] and expected and pins[name] != expected
        )
    _fail("Tool version pins disagree", problems)


def _unresolved(check: str) -> str | None:
    """Explain why a pytest node ID in features.yaml names no test, if it does not."""
    path, _, name = check.partition("::")
    test_file = REPO_ROOT / path
    if not test_file.is_file():
        return "test file does not exist"
    nodes = ast.parse(test_file.read_text(encoding="utf-8")).body
    for part in re.sub(r"\[.*\]$", "", name).split("::"):
        found = next(
            (
                node
                for node in nodes
                if isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                )
                and node.name == part
            ),
            None,
        )
        if found is None:
            return f"no test named {part!r} in {path}"
        nodes = found.body
    return None


def test_test_bookkeeping_in_sync():
    """Reporting categories, feature mappings and lint tools name real things."""
    files = {path.name for path in TESTS_DIR.glob("test_*.py")}
    problems = [
        f"{name}: not mapped in TEST_CATEGORIES (tests/conftest.py)"
        for name in sorted(files - TEST_CATEGORIES.keys())
    ]
    problems.extend(
        f"{name}: TEST_CATEGORIES entry has no test file"
        for name in sorted(TEST_CATEGORIES.keys() - files)
    )
    problems.extend(
        f"{name}: SLOW_CATEGORY_OVERRIDES entry is not in TEST_CATEGORIES"
        for name in sorted(SLOW_CATEGORY_OVERRIDES.keys() - TEST_CATEGORIES.keys())
    )

    manifest = yaml.safe_load(FEATURES_MANIFEST.read_text(encoding="utf-8"))
    for group, features in manifest.items():
        for feature in features:
            for check in feature.get("checks", []):
                reason = _unresolved(check)
                if reason:
                    problems.append(
                        f"features.yaml {group} {feature['name']!r}: {check}: {reason}"
                    )

    if not LINT_TARGETS:
        problems.append("Makefile: no `lint:` prerequisites found")
    problems.extend(
        f"Makefile lint target {target}: add it to REQUIRED_TOOLS in "
        "tests/test_code_quality.py"
        for target in LINT_TARGETS
        if target not in REQUIRED_TOOLS
    )
    problems.extend(
        f"REQUIRED_TOOLS entry {target}: not a prerequisite of `make lint`"
        for target in REQUIRED_TOOLS
        if target not in LINT_TARGETS
    )
    _fail("Test bookkeeping is out of sync", problems)


def _documented_inventory() -> tuple[dict[tuple[str, str, str], int], dict[str, int]]:
    """Read per-group module counts and the totals line from the inventory page."""
    text = INVENTORY_PAGE.read_text(encoding="utf-8")
    table = text.split("```{list-table}", 1)[1].split("```", 1)[0]
    counts: dict[tuple[str, str, str], int] = {}
    group = ""
    for line in table.splitlines():
        if line.startswith("* - "):
            group = line[4:].strip()
        elif entry := MODULE_ENTRY.search(line):
            for count, tier in re.findall(r"(\d+) (fast|slow)", entry["counts"]):
                counts[(group, entry["file"], tier)] = int(count)
    totals = TOTALS.search(text)
    return counts, (
        {key: int(value) for key, value in totals.groupdict().items()} if totals else {}
    )


def _collected_inventory() -> dict[tuple[str, str, str], int]:
    """Collect (without running) each tier in a separate pytest process."""
    # Drop pytest/xdist and coverage-report variables so the child process
    # neither inherits options nor writes results/feature-coverage.json.
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("PYTEST_") and key != "ULWAZI_COVERAGE_REPORT"
    }
    counts: dict[tuple[str, str, str], int] = {}
    for tier, marker in (("fast", "not slow"), ("slow", "slow")):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "--collect-only",
                "-q",
                "-p",
                "no:cacheprovider",
                "-m",
                marker,
            ],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )
        if result.returncode:
            pytest.fail(
                f"pytest --collect-only -m {marker!r} failed:\n"
                f"{result.stdout[-3000:]}\n{result.stderr[-3000:]}",
                pytrace=False,
            )
        for test_file, count in COLLECTED.findall(result.stdout):
            group, _ = _category(f"{test_file}::case", slow=tier == "slow")
            counts[(group, Path(test_file).name, tier)] = int(count)
    return counts


def test_inventory_counts_match_collection():
    """The test inventory table states exactly what pytest collects."""
    documented, totals = _documented_inventory()
    collected = _collected_inventory()
    page = INVENTORY_PAGE.relative_to(REPO_ROOT)
    problems = [
        f"{' / '.join(key)}: page says {documented.get(key, 0)}, "
        f"pytest collects {collected.get(key, 0)}"
        for key in sorted(documented.keys() | collected.keys())
        if documented.get(key) != collected.get(key)
    ]
    expected_totals = {
        "cases": sum(collected.values()),
        "modules": len({name for _, name, _ in collected}),
        "fast": sum(n for (_, _, tier), n in collected.items() if tier == "fast"),
        "slow": sum(n for (_, _, tier), n in collected.items() if tier == "slow"),
    }
    if totals != expected_totals:
        problems.append(
            f"'Full selection' line says {totals or 'nothing (line not found)'}; "
            f"expected {expected_totals}"
        )
    _fail(f"{page} inventory does not match pytest collection", problems)


# ---------------------------------------------------------------------------
# Slow checks: the existing linters, one case per `make lint` target
# ---------------------------------------------------------------------------


@pytest.mark.slow
@pytest.mark.parametrize("target", LINT_TARGETS)
def test_make_lint_target(target):
    """Run one `make lint` target; skip it when its tools are not installed."""
    missing = [
        tool
        for tool in ("make", *REQUIRED_TOOLS.get(target, ()))
        if shutil.which(tool) is None
    ]
    if missing:
        pytest.skip(f"make {target} needs {', '.join(missing)} on PATH")
    # Without CI, common.mk prints no ::group:: markers. Dropping the parent
    # make's variables avoids jobserver warnings when run via `make test-all`.
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"CI", "MAKEFLAGS", "MAKELEVEL", "MFLAGS"}
    }
    try:
        result = subprocess.run(
            ["make", "--no-print-directory", "-s", target],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=LINT_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        pytest.fail(f"make {target} did not finish in {LINT_TIMEOUT}s", pytrace=False)
    if result.returncode:
        output = (result.stdout + result.stderr).strip().splitlines()
        pytest.fail(
            f"make {target} failed (exit {result.returncode}); last lines:\n"
            + "\n".join(output[-OUTPUT_TAIL_LINES:])
            + f"\nReproduce with: make {target}",
            pytrace=False,
        )
