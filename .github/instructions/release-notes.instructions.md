---
description: "Use when preparing release notes, a changelog, or a version summary for Ulwazi — drafting the GitHub release body for a new tag, analyzing changes between two tags or from the last tag to HEAD, classifying merged PRs, writing upgrade notes, or updating a published release."
---

# Release notes preparation

Ulwazi release notes are hand-curated summaries of merged PRs, published as the
GitHub release body for a semver tag (`X.Y.Z`). There is no in-repo changelog
file — the notes live only on the
[releases page](https://github.com/canonical/ulwazi/releases). The
`release-publish.yaml` workflow creates each release with auto-generated notes
and the dist assets; the house convention is to replace the auto-generated body
with a curated one.

**Never publish anything without an explicit request.** Prepare the draft
locally and present it for human review.

Reference styles: the [1.0.0 release](https://github.com/canonical/ulwazi/releases/tag/1.0.0)
is the current convention; 0.6 and older use superseded link/heading styles.

## 1. Generate the draft with the script

The deterministic generator does the mechanical work — no LLM judgment is
needed for the structure:

```bash
python3 .github/scripts/generate_release_notes.py \
  --prev <PREV> --target <TARGET> --out draft.md
```

- `--prev` defaults to the latest tag reachable from HEAD; `--target` defaults
  to `HEAD` (pre-tagging mode; the draft title renders the version as `X.Y.Z`).
- `--intro-file <path>` supplies the hand-written intro paragraph — the only
  part the script does not generate. Without it, the draft carries a placeholder
  comment.
- Tag-to-tag scope comes from GitHub's `generate-notes` API (authoritative — it
  includes PRs whose squash commits lost their `(#N)` suffix); HEAD mode falls
  back to the local `git log`.
- The script prints **review warnings** to stderr: direct pushes without a PR,
  and (in HEAD mode) PRs merged after `--prev` that no in-range commit links.
  Address each before finalizing.

What the script produces deterministically:

- Section classification (Features and enhancements / Bug fixes / Documentation
  / Testing and CI) from the conventional-commit type, title keywords, and the
  files touched — a first draft, not a judgment of user-facing impact.
- One bullet per PR: past-tense title, `by @author in <PR URL>` attribution
  (1.0.0 style).
- All dependency bumps grouped into a single _Testing and CI_ bullet.
- _Upgrade notes_ detected from `pyproject.toml` diffs (Python floor and tested
  versions, removed dependencies) plus breaking commits (`!`).
- _New contributors_ computed from the full merged-PR history (first merged PR
  in range — matches the published releases; GitHub's own auto-generated list
  is less complete, e.g. it found 1 of 5 for 0.6).
- The _Full Changelog_ compare link and the closing line.

## 2. Fill in the intro (required)

The script emits a `<!-- INTRO: ... -->` placeholder comment instead of an
opening summary — the only part it does not generate. Replace the placeholder
with a short paragraph written to the pattern of the published releases:

- Open with the release framing: "This is the Nth public release of the Ulwazi
  theme for Sphinx documentation." for minor releases, "This is a maintenance
  release of the Ulwazi theme for Sphinx documentation." for patch releases,
  or "This is the first stable release …" for milestones.
- Then name the one to three headline changes a theme _user_ cares about, in
  plain language — not the full inventory (that is What's changed below).
- If the release carries a breaking change, add a short bold callout
  paragraph right after the summary sentence, stating what changed and, in
  one sentence, why — the published 1.0.3 explains that the `soupsieve` 4.x
  releases that fix the OSV vulnerabilities themselves require Python 3.11.5,
  so no patched release still supports Python 3.10.
- For pre-stable releases, add "This release is recommended for testing
  purposes only."
- Ground every fact in the release scope: check numbers, sizes, and counts
  against the diff or the PR bodies before writing them (compute
  percentages from the actual byte sizes; verify claims like "N silent
  regressions" against the PR descriptions). Never invent or estimate.
- Match the house voice: plain sentences, no exclamation marks, British
  spelling (colour, behaviour, minimised). Working examples: 1.0.0 ("This is
  the first stable release … Since version 0.6, the theme has gained a
  comprehensive test suite …"), 0.6 ("This is the fifth public release …"),
  1.0.3 ("This is a maintenance release … It shrinks the shipped stylesheet
  by about 79% …").
- Write the intro as one paragraph on a single line (no hard wrapping),
  placed between the title and the PyPI paragraph. For regenerating with the
  intro included, pass it via `--intro-file <path>`.

## 3. Minimal polish of the script's output

The script's output is the canonical structure — keep it for consistency.
Do not rebuild, reorder, or reformat: the section order, heading wording,
`by @author in <PR URL>` attribution, single-line bullets, Full Changelog
line, and New contributors list are already in house style. Edit the content
only where the deterministic rules misjudge:

- Rewrite entry wording into user-visible outcomes: "Fixed the side-navigation
  drawer on mobile and tablet, including keyboard focus behavior and resize
  handling", not "fix: side nav js refactor".
- Merge related PRs into single bullets where they form one change (in the
  published 1.0.0, #158/#160/#169 share one bullet; #161 was folded into
  another).
- Cross-list a PR under several sections when it did several things (#157 and
  #179 appear under both Bug fixes and Documentation in 1.0.0).
- Reclassify where the commit type misleads: a `fix:` touching only sample docs
  is Documentation; a `chore:` users feel (the pip→uv migration) is Features
  and enhancements.
- Expand bare upgrade notes into actionable guidance (the published 1.0.0
  explains _what to do_ about `canonical-sphinx-config`, not just that it was
  removed).

**Do not hard-wrap lines.** Each heading, bullet, paragraph, and the Full
Changelog line is one single line, no matter its length — GitHub reflows
prose when rendering, and hard wraps leave stray line breaks in the rendered
notes (the 1.0.1–1.0.3 releases were published wrapped by mistake and had to
be re-edited). The generator already emits single-line entries; keep that
format when editing by hand, including the intro.

## 4. Verify and deliver

- Every in-scope PR appears at least once; no release-prep commits; nothing
  from before `<PREV>`.
- Spot-check that PR numbers resolve (`gh pr view <N>`).
- The compare URL range matches the scope.
- Save the draft outside the repo tree (or present it in chat) for review.
  Publishing — `gh release edit <TAG> --notes-file <file>` for an existing
  release, or handing the draft over for a manual `gh release create` —
  happens only on explicit request.
