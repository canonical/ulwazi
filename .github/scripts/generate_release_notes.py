"""Generate a deterministic release-notes draft for the Ulwazi theme.

Collect the merged pull requests between two Git refs (two tags, or the
previous tag and HEAD), classify them into the house sections, group
dependency bumps, detect upgrade-note material from ``pyproject.toml``,
compute new contributors, and render the release body in the current
style (see the 1.0.0 release for the reference formatting).

The intro paragraph is intentionally not generated: pass ``--intro-file``
or fill in the placeholder comment the script emits. The output is a
draft for human review; publishing remains a manual, explicit step.

Requires Python 3.11+ (stdlib only) and the ``gh`` and ``git`` CLI tools.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# INP001: this is a standalone script, not a package module.

PYPI_LINE = "The package is published on [PyPI](https://pypi.org/project/ulwazi/)."
CLOSING_LINE = "Feedback and contributions are welcome!"
INTRO_PLACEHOLDER = (
    "<!-- INTRO: replace this comment with 1-3 sentences: the release ordinal, "
    "e.g. This is the Nth public release of the Ulwazi theme for Sphinx "
    "documentation, or a maintenance release for patch versions, plus the "
    "headline changes in plain language. For pre-stable releases add: This "
    "release is recommended for testing purposes only. -->"
)
SECTION_ORDER = (
    "Features and enhancements",
    "Bug fixes",
    "Documentation",
    "Testing and CI",
)
DOCS_ONLY_THRESHOLD = 0.7
_TWO_PACKAGES = 2

RELEASE_PREP_RE = re.compile(
    r"(?i)\b(?:prepare\w*|prep)\b.*\brelease\b|\brelease\b.*\bprep\b"
)
CONVENTIONAL_RE = re.compile(
    r"^(?P<type>[a-z]+)(?:\([^)]*\))?(?P<breaking>!)?:\s*(?P<rest>.+)$"
)
TICKET_PREFIX_RE = re.compile(r"^\[[A-Z][A-Z0-9-]*\]:\s*")
TRAILING_PR_RE = re.compile(r"\s*\(#\d+\)\s*$")
BUMP_RE = re.compile(
    r"^[a-z]+(?:\([^)]*\))?(?:!)?:\s*[Bb]ump\s+(?P<package>\S+)\s+from\s+\S+\s+to\s+\S+"
)
TESTING_WORD_RE = re.compile(r"(?i)\b(?:test|tests|testing|coverage|playwright|ci)\b")
DOCS_WORD_RE = re.compile(r"(?i)\b(?:docs|documentation)\b")
DOCS_FILE_RE = re.compile(r"^(?:docs/|README\.md$|agents\.md$)")
LOCKFILE_RE = re.compile(r"^(?:uv\.lock|package-lock\.json)$")
PR_IN_URL_RE = re.compile(r"/pull/(\d+)$")
PR_LOG_RE = re.compile(r"\(#(\d+)\)\s*$")
API_ENTRY_RE = re.compile(r"^\* (?P<title>.+) by @(?P<author>\S+) in (?P<url>\S+)$")
PYTHON_CLASSIFIER_RE = re.compile(r"^Programming Language :: Python :: (\d+\.\d+)$")
REQUIRES_PYTHON_RE = re.compile(r"^[><=!~]*(?P<floor>[\d.]+)")
DEP_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*")

PAST_TENSE = {
    "add": "Added",
    "allow": "Allowed",
    "bump": "Bumped",
    "change": "Changed",
    "clean": "Cleaned",
    "correct": "Corrected",
    "create": "Created",
    "delete": "Deleted",
    "document": "Documented",
    "drop": "Dropped",
    "enable": "Enabled",
    "ensure": "Ensured",
    "fix": "Fixed",
    "implement": "Implemented",
    "improve": "Improved",
    "incorporate": "Incorporated",
    "introduce": "Introduced",
    "make": "Made",
    "preserve": "Preserved",
    "rebuild": "Rebuilt",
    "redirect": "Redirected",
    "refactor": "Refactored",
    "remove": "Removed",
    "resolve": "Resolved",
    "restore": "Restored",
    "support": "Supported",
    "switch": "Switched",
    "turn": "Turned",
    "update": "Updated",
    "upgrade": "Upgraded",
    "use": "Used",
}


@dataclass
class PullRequest:
    """A merged pull request in the release scope."""

    number: int
    title: str
    author: str
    files: list[str]


@dataclass
class Draft:
    """Everything needed to render the release-notes draft."""

    repo: str
    prev: str
    target: str
    intro: str
    sections: dict[str, list[PullRequest]]
    deps: list[PullRequest]
    upgrade: list[str]
    contributors: list[tuple[str, int]]


def run_tool(args: list[str], *, what: str) -> str:
    """Run a CLI tool and return its stdout, exiting on failure."""
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=True,
            timeout=120,
        )
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip() or error.stdout.strip() or "unknown error"
        sys.exit(f"error: {what} failed:\n{detail}")
    except subprocess.TimeoutExpired:
        sys.exit(f"error: {what} timed out")
    return result.stdout


def try_tool(args: list[str]) -> str | None:
    """Run a CLI tool and return its stdout, or None on failure."""
    result = subprocess.run(
        args, check=False, capture_output=True, text=True, timeout=120
    )
    return result.stdout if result.returncode == 0 else None


def resolve_repo(explicit: str | None) -> str:
    """Return the owner/repo slug, from --repo or the origin remote."""
    if explicit:
        return explicit
    remote = run_tool(
        ["git", "remote", "get-url", "origin"],
        what="git remote get-url",
    )
    match = re.search(r"github[/:]([^/]+/[^/.]+?)(?:\.git)?$", remote.strip())
    return match.group(1) if match else "canonical/ulwazi"


def latest_tag() -> str:
    """Return the most recent tag reachable from HEAD."""
    return run_tool(
        ["git", "describe", "--tags", "--abbrev=0"],
        what="git describe (run git fetch --tags first)",
    ).strip()


def pr_url(repo: str, number: int) -> str:
    """Return the canonical pull-request URL."""
    return f"https://github.com/{repo}/pull/{number}"


def render_author(login: str) -> str:
    """Render a GitHub login as the handle used in release notes."""
    if login.startswith("app/"):
        return f"{login.removeprefix('app/')}[bot]"
    return login


def is_bot(author: str) -> bool:
    """Return True for bot accounts (never listed as contributors)."""
    return author.endswith("[bot]") or author.startswith("app/")


def pr_files(repo: str, number: int) -> list[str]:
    """Return the file paths a pull request changed."""
    output = run_tool(
        ["gh", "pr", "view", str(number), "--repo", repo, "--json", "files"],
        what=f"gh pr view {number}",
    )
    return [entry["path"] for entry in json.loads(output)["files"]]


def collect_scope_tag_mode(
    repo: str, prev: str, target: str
) -> list[PullRequest] | None:
    """Collect the merged PRs via GitHub's generate-notes API.

    The API is authoritative for tag-to-tag ranges: it includes PRs whose
    squash commits lost their (#N) suffix.
    """
    output = try_tool(
        [
            "gh",
            "api",
            f"repos/{repo}/releases/generate-notes",
            "-f",
            f"tag_name={target}",
            "-f",
            f"previous_tag_name={prev}",
        ]
    )
    if output is None:
        return None
    body = json.loads(output)["body"]
    prs: list[PullRequest] = []
    for line in body.splitlines():
        if line.startswith("## New Contributors"):
            break
        match = API_ENTRY_RE.match(line)
        if not match:
            continue
        url_match = PR_IN_URL_RE.search(match["url"])
        if not url_match:
            continue
        number = int(url_match.group(1))
        prs.append(
            PullRequest(
                number=number,
                title=match["title"].strip(),
                author=match["author"],
                files=pr_files(repo, number),
            )
        )
    return prs


def collect_scope_head_mode(repo: str, prev: str, target: str) -> list[PullRequest]:
    """Collect the merged PRs from the local git log (HEAD mode)."""
    log = run_tool(
        ["git", "log", "--oneline", f"{prev}..{target}"],
        what=f"git log {prev}..{target}",
    )
    numbers = []
    for line in log.splitlines():
        match = PR_LOG_RE.search(line)
        if match:
            numbers.append(int(match.group(1)))
    prs: list[PullRequest] = []
    for number in numbers:
        output = run_tool(
            [
                "gh",
                "pr",
                "view",
                str(number),
                "--repo",
                repo,
                "--json",
                "number,title,author,files",
            ],
            what=f"gh pr view {number}",
        )
        data = json.loads(output)
        prs.append(
            PullRequest(
                number=data["number"],
                title=data["title"].strip(),
                author=render_author(data["author"]["login"]),
                files=[entry["path"] for entry in data["files"]],
            )
        )
    return prs


def direct_push_commits(prev: str, target: str, prs: list[PullRequest]) -> list[str]:
    """Return in-range commits with no PR link (excluding release prep).

    A commit whose title matches a collected PR is not reported: the
    generate-notes API already linked it (squash commits sometimes lose
    their (#N) suffix).
    """
    log = run_tool(
        ["git", "log", "--oneline", f"{prev}..{target}"],
        what=f"git log {prev}..{target}",
    )
    collected_titles = {TRAILING_PR_RE.sub("", pr.title).strip() for pr in prs}
    orphans = []
    for line in log.splitlines():
        if PR_LOG_RE.search(line) or RELEASE_PREP_RE.search(line):
            continue
        title = TRAILING_PR_RE.sub(
            "", line.split(" ", 1)[1] if " " in line else ""
        ).strip()
        if title in collected_titles:
            continue
        orphans.append(line)
    return orphans


def parse_timestamp(value: str) -> datetime:
    """Parse an ISO-8601 timestamp with either a Z or a +00:00 suffix."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def unlinked_pr_warnings(repo: str, prev: str, prs: list[PullRequest]) -> list[str]:
    """Warn about PRs merged after the previous tag but missing from scope.

    Catches squash commits that lost their (#N) suffix when working from
    HEAD. Only used in HEAD mode; the generate-notes API is authoritative
    for tag ranges.
    """
    prev_date = parse_timestamp(
        run_tool(
            ["git", "log", "-1", "--format=%cI", prev],
            what=f"git log {prev}",
        ).strip()
    )
    output = run_tool(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            repo,
            "--state",
            "merged",
            "--base",
            "main",
            "--limit",
            "1000",
            "--json",
            "number,title,mergedAt",
        ],
        what="gh pr list",
    )
    collected = {pr.number for pr in prs}
    return [
        f"PR #{entry['number']} ({entry['title']}) was merged after "
        f"{prev} but is not linked from a commit in range; add it "
        "manually if it belongs in this release"
        for entry in json.loads(output)
        if parse_timestamp(entry["mergedAt"]) > prev_date
        and entry["number"] not in collected
    ]


def is_dependency_bump(pr: PullRequest) -> bool:
    """Return True for bot dependency bumps touching only lockfiles."""
    if BUMP_RE.match(pr.title):
        return True
    return (
        is_bot(pr.author)
        and bool(pr.files)
        and all(LOCKFILE_RE.match(path) for path in pr.files)
    )


def is_docs_only(pr: PullRequest) -> bool:
    """Return True when a PR's files are overwhelmingly documentation."""
    if not pr.files:
        return False
    docs = sum(1 for path in pr.files if DOCS_FILE_RE.match(path))
    return docs / len(pr.files) >= DOCS_ONLY_THRESHOLD


def classify_conventional(pr: PullRequest, commit_type: str, rest: str) -> str:
    """Classify a PR whose title carries a conventional-commit prefix."""
    if commit_type == "docs":
        return "Documentation"
    if commit_type in ("test", "ci"):
        return "Testing and CI"
    if TESTING_WORD_RE.search(rest):
        return "Testing and CI"
    if commit_type == "fix":
        return "Bug fixes"
    if commit_type == "chore":
        return "Documentation" if is_docs_only(pr) else "Features and enhancements"
    return "Features and enhancements"


def classify(pr: PullRequest) -> str | None:
    """Return the section for a PR, or None for release-prep PRs.

    Classification is a first draft for human review: it follows the
    commit type, then title keywords, and cannot judge user-facing impact
    the way a human does.
    """
    if RELEASE_PREP_RE.search(pr.title):
        return None
    if is_dependency_bump(pr):
        return "deps"
    conventional = CONVENTIONAL_RE.match(pr.title)
    if conventional:
        return classify_conventional(pr, conventional["type"], conventional["rest"])
    if TESTING_WORD_RE.search(pr.title):
        return "Testing and CI"
    if DOCS_WORD_RE.search(pr.title):
        return "Documentation"
    return "Features and enhancements"


def clean_title(title: str) -> str:
    """Turn a PR title into a release-notes entry description.

    Strips the conventional-commit prefix, ticket prefixes, and trailing
    (#N); converts the leading verb to past tense where known.
    """
    text = TRAILING_PR_RE.sub("", title).strip()
    text = TICKET_PREFIX_RE.sub("", text)
    conventional = CONVENTIONAL_RE.match(text)
    if conventional:
        text = conventional["rest"].strip()
    words = text.split()
    if not words:
        return text
    first = words[0].lower()
    if first in PAST_TENSE:
        words[0] = PAST_TENSE[first]
    else:
        words[0] = words[0][0].upper() + words[0][1:]
    return " ".join(words)


def dependency_bullet(repo: str, deps: list[PullRequest]) -> str:
    """Render the single grouped dependency-bumps bullet."""
    packages = []
    for pr in deps:
        match = BUMP_RE.match(pr.title)
        packages.append(match["package"] if match else f"PR {pr.number}")
    if len(packages) == 1:
        names = f"`{packages[0]}`"
    elif len(packages) == _TWO_PACKAGES:
        names = f"`{packages[0]}` and `{packages[1]}`"
    else:
        joined = ", ".join(f"`{package}`" for package in packages[:-1])
        names = f"{joined}, and `{packages[-1]}`"
    authors = []
    for pr in deps:
        if pr.author not in authors:
            authors.append(pr.author)
    parts = []
    for author in authors:
        urls = ", ".join(pr_url(repo, pr.number) for pr in deps if pr.author == author)
        parts.append(f"by @{author} in {urls}")
    return f"Updated transitive dependencies, including {names}, {', '.join(parts)}."


def pyproject_at(ref: str) -> dict[str, Any]:
    """Return the parsed pyproject.toml at a Git ref."""
    content = run_tool(
        ["git", "show", f"{ref}:pyproject.toml"],
        what=f"git show {ref}:pyproject.toml",
    )
    return tomllib.loads(content)


def python_versions(classifiers: list[str]) -> list[str]:
    """Return the sorted Python versions from trove classifiers."""
    versions = []
    for classifier in classifiers:
        match = PYTHON_CLASSIFIER_RE.match(classifier)
        if match:
            versions.append(match.group(1))
    return sorted(versions, key=lambda v: tuple(int(p) for p in v.split(".")))


def dependency_names(data: dict[str, Any]) -> set[str]:
    """Return every dependency name declared anywhere in pyproject.toml."""
    names: set[str] = set()
    project = data.get("project", {})
    pools = [project.get("dependencies", [])]
    pools.extend(project.get("optional-dependencies", {}).values())
    pools.extend(data.get("dependency-groups", {}).values())
    for pool in pools:
        for dep in pool:
            match = DEP_NAME_RE.match(dep.strip())
            if match:
                names.add(match.group(0))
    return names


def upgrade_notes(
    prev: str, target: str, prs: list[PullRequest], repo: str
) -> list[str]:
    """Detect upgrade-note material: Python changes, removed deps, breaks."""
    notes: list[str] = []
    prev_data = pyproject_at(prev)
    target_data = pyproject_at(target)
    prev_project = prev_data.get("project", {})
    target_project = target_data.get("project", {})
    prev_floor_match = REQUIRES_PYTHON_RE.match(prev_project.get("requires-python", ""))
    target_floor_match = REQUIRES_PYTHON_RE.match(
        target_project.get("requires-python", "")
    )
    prev_floor = prev_floor_match["floor"] if prev_floor_match else ""
    target_floor = target_floor_match["floor"] if target_floor_match else ""
    prev_versions = python_versions(prev_project.get("classifiers", []))
    target_versions = python_versions(target_project.get("classifiers", []))
    if (prev_floor != target_floor) or (prev_versions != target_versions):
        if target_versions:
            notes.append(
                f"Python {target_floor} or newer is required; builds are "
                f"tested on Python {target_versions[0]}\u2013{target_versions[-1]}."
            )
        else:
            notes.append(f"Python {target_floor} or newer is required.")
    removed = sorted(dependency_names(prev_data) - dependency_names(target_data))
    notes.extend(f"`{name}` is no longer a dependency." for name in removed)
    notes.extend(
        f"Breaking change: {clean_title(pr.title)} ({pr_url(repo, pr.number)})."
        for pr in prs
        if (conventional := CONVENTIONAL_RE.match(pr.title))
        and conventional["breaking"]
    )
    return notes


def new_contributors(repo: str, prs: list[PullRequest]) -> list[tuple[str, int]]:
    """Return authors whose first merged PR is in this release's scope.

    Computed from the full merged-PR history rather than GitHub's
    auto-generated list: the house convention is first merged PR in
    range, which matches the published releases exactly.
    """
    output = run_tool(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            repo,
            "--state",
            "merged",
            "--limit",
            "1000",
            "--json",
            "number,author,mergedAt",
        ],
        what="gh pr list",
    )
    merged = sorted(json.loads(output), key=lambda entry: entry["mergedAt"])
    first_by_author: dict[str, int] = {}
    for entry in merged:
        author = render_author(entry["author"]["login"])
        if is_bot(author):
            continue
        first_by_author.setdefault(author, entry["number"])
    in_range = {pr.number for pr in prs}
    contributors = [
        (author, number)
        for author, number in first_by_author.items()
        if number in in_range
    ]
    contributors.sort(key=lambda item: item[1])
    return contributors


def render(draft: Draft) -> str:
    """Render the full release-notes draft."""
    version = "X.Y.Z" if draft.target == "HEAD" else draft.target
    lines = [f"# Ulwazi theme release {version}", ""]
    lines.append(draft.intro if draft.intro else INTRO_PLACEHOLDER)
    lines.append("")
    lines.append(PYPI_LINE)
    lines.append("")
    has_changes = any(draft.sections.get(section) for section in SECTION_ORDER) or (
        draft.deps
    )
    if has_changes:
        lines.append("## What's changed")
        lines.append("")
    for section in SECTION_ORDER:
        entries = draft.sections.get(section, [])
        deps = draft.deps if section == "Testing and CI" else []
        if not entries and not deps:
            continue
        lines.append(f"### {section}")
        lines.append("")
        lines.extend(
            f"- {clean_title(pr.title)}, by @{pr.author} "
            f"in {pr_url(draft.repo, pr.number)}."
            for pr in entries
        )
        if deps:
            lines.append(f"- {dependency_bullet(draft.repo, deps)}")
        lines.append("")
    if draft.upgrade:
        lines.append("## Upgrade notes")
        lines.append("")
        lines.extend(f"- {note}" for note in draft.upgrade)
        lines.append("")
    lines.append(
        f"**Full Changelog**: https://github.com/{draft.repo}/compare/"
        f"{draft.prev}...{draft.target}"
    )
    lines.append("")
    if draft.contributors:
        lines.append("## New contributors")
        lines.append("")
        for author, number in draft.contributors:
            lines.append(
                f"- @{author} made their first contribution in "
                f"{pr_url(draft.repo, number)}"
            )
        lines.append("")
    lines.append(CLOSING_LINE)
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    """Parse the command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate a deterministic release-notes draft."
    )
    parser.add_argument(
        "--prev",
        help="previous tag (default: the latest tag reachable from HEAD)",
    )
    parser.add_argument(
        "--target",
        default="HEAD",
        help="new tag or HEAD (default: HEAD)",
    )
    parser.add_argument(
        "--repo",
        help="owner/repo slug (default: derived from the origin remote)",
    )
    parser.add_argument(
        "--intro-file",
        type=Path,
        help="Markdown file with the hand-written intro paragraph",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="output file (default: print to stdout)",
    )
    return parser.parse_args()


def main() -> None:
    """Orchestrate scope collection, classification, and rendering."""
    args = parse_args()
    repo = resolve_repo(args.repo)
    prev = args.prev or latest_tag()
    target = args.target
    if prev == target:
        sys.exit(f"error: --prev and --target are both {prev}")
    intro = ""
    if args.intro_file:
        intro = args.intro_file.read_text(encoding="utf-8").strip()

    prs = collect_scope_tag_mode(repo, prev, target)
    warnings: list[str] = []
    if prs is None:
        warnings.append(
            f"generate-notes API unavailable for {target}; fell back to the "
            "local git log (tag missing locally or on the remote?)"
        )
        prs = collect_scope_head_mode(repo, prev, target)
    else:
        warnings.extend(
            f"direct push without a PR (not in the draft): {commit}"
            for commit in direct_push_commits(prev, target, prs)
        )
    if target == "HEAD":
        warnings.extend(unlinked_pr_warnings(repo, prev, prs))

    sections: dict[str, list[PullRequest]] = {}
    deps: list[PullRequest] = []
    for pr in prs:
        section = classify(pr)
        if section == "deps":
            deps.append(pr)
        elif section is not None:
            sections.setdefault(section, []).append(pr)

    draft = Draft(
        repo=repo,
        prev=prev,
        target=target,
        intro=intro,
        sections=sections,
        deps=deps,
        upgrade=upgrade_notes(prev, target, prs, repo),
        contributors=new_contributors(repo, prs),
    )
    output = render(draft)
    if args.out:
        args.out.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    if warnings:
        print("\nReview warnings:", file=sys.stderr)
        for warning in warnings:
            print(f"- {warning}", file=sys.stderr)
    print(
        "\nDraft generated. Human steps: fill the INTRO placeholder following "
        ".github/instructions/release-notes.instructions.md (release framing, "
        "headline changes grounded in the diff, breaking-change callout if "
        "any), then apply only minimal polish — the script's output structure "
        "is canonical. Never publish without an explicit request.",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
