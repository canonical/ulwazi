# Ulwazi adoption dashboard

Tracks how many Canonical documentation projects use the Sphinx Stack and the
Ulwazi theme, and shows the result as a static dashboard: statistics on top, one
table row per public Read the Docs (RTD) project below.

The tool lives in the Ulwazi repository but is not part of the `ulwazi`
package. Keep it outside `ulwazi/`: the CSS pruner reads every file there.

## Quick start

```bash
# Look at the dashboard with made-up data (no tokens needed):
make adoption-sample
make adoption-serve        # http://127.0.0.1:8001

# Real data:
export RTD_TOKEN=...       # Read the Docs API token (profile settings)
gh auth login              # or export GITHUB_TOKEN=...
make adoption              # detect + process + render
make adoption-serve
```

Individual layers, with `uv run --only-group adoption python -m tools.adoption`:

| Command   | Layer            | Reads                       | Writes                                  |
| --------- | ---------------- | --------------------------- | --------------------------------------- |
| `detect`  | 1. Detection     | RTD API, or `--file` export | `data/rtd-projects.json`                |
| `process` | 2. Processing    | `rtd-projects.json`, GitHub | `data/adoption.json`, `history.jsonl`   |
| `render`  | 3. Front end     | `adoption.json`, history    | `_build/index.html`, CSS, JS, CSV, JSON |
| `all`     | all three        |                             |                                         |
| `serve`   | local web server | `_build/`                   |                                         |

Useful options: `--file export.csv` (import instead of calling the API),
`--no-builds` (skip RTD build dates), `--only SLUG ...` and `--limit N` (partial
runs write `adoption.partial.json` and leave the history alone), `--no-live`
(skip live-site checks), `-v`.

## What the dashboard shows

For every RTD project: the project and its docs link, the GitHub repository
(with the docs folder), the Sphinx Stack version, the Ulwazi version (`N/A`
when the project does not use Ulwazi) and the last successful build. A row
expander lists the evidence behind each detection, with links to the files at
the inspected commit.

Out-of-scope projects stay in the table (dimmed, with the reason) but are not
counted in the percentage.

## How the versions are determined

### Sphinx Stack

1. The docs folder is found from the `docs_path` override,
   `sphinx.configuration` in `.readthedocs.yaml`, common folder names, and
   finally the repository's file list.
2. The version is read from `<docs>/_dev/version` (Sphinx Stack 2.0 and later)
   or `<docs>/.sphinx/version` (1.x). A project with `custom_conf.py` or
   `.sphinx/` files but no version file is reported as `< 1.0`.
3. **Known issue, Sphinx Stack 3.0:** the 3.0 release still ships a version file
   that says `2.0`. A project that declares `2.0` is reported as `3.0`
   (marked _corrected_) only when it has the changes the 3.0 release itself
   made: Ulwazi replaces `canonical-sphinx` (in `requirements.txt` or in the
   `conf.py` extensions) **and** at least one of `sphinx-roles` 1.x,
   `sphinx-terminal` 1.1+, `sphinx-llm` 1.1+ or `sphinx-modern-pdf-style`.
   Files that reached `main` between 2.0 and 3.0 are not evidence:
   `_dev/check_removed_urls.py`, the new Makefile and the new
   `_dev/update_sp.py` (which copies itself from `main`) are common in 2.0
   projects. Each sign is checked against upstream on every run: it must hold
   at the `3.0` tag and not at the last upstream commit before the release
   changes, otherwise it is ignored with a warning. The rule applies only while
   the upstream `3.0` tag really ships `2.0`, so it turns itself off once
   upstream fixes the file. The rule lives in `process/corrections.py`; remove
   its entry from `KNOWN_ISSUES`, or set `correct_known_version_issues = false`,
   to retire it.

### Ulwazi

- **Live site (preferred).** Sphinx adds `?v=<crc32>` to the local stylesheets
  and scripts it links. The tool downloads every released `ulwazi` wheel from
  PyPI, computes the same checksums, and matches them with the links of the
  project's published documentation. One match shows the exact version (`1.0.3`),
  several matches a range (`1.0.1–1.0.2`), no match `dev` (an unreleased build).
- **Repository fallback.** If the live site cannot be checked, `html_theme` in
  `conf.py` decides, and the version shown is the newest release allowed by the
  `ulwazi` requirement (`≈ 1.0.3`).
- **Pending deploy.** The repository sets the Ulwazi theme but the live site does
  not serve it yet: shown as `N/A` with a chip, not counted as adopted.

## Scope and privacy

- Only public RTD projects are listed. Private projects (and anything whose
  privacy level is unknown) are dropped before any file is written, and
  private or invisible GitHub repositories are dropped without a trace.
- A project is _in scope_ when the Sphinx Stack was detected and it is not
  archived, opted out or hosted somewhere other than GitHub (v1 supports
  GitHub only). The headline percentage is Ulwazi projects divided by in-scope
  projects.
- Translations count with their parent project.

## Configuration

Edit `tools/adoption/config.toml` through a pull request, so every change has
an author and a date. See the comments in the file for all options:

- `tracking.mode = "auto"` tracks every public project except the `[[exclude]]`
  entries (opt-out). `mode = "manual"` tracks only the `[[include]]` entries
  (opt-in); everything else is listed as _Not tracked_.
- Every `[[exclude]]` needs a `reason`. Patterns are shell-style and case
  insensitive and match the RTD slug or `owner/repo`.
- `[[override]]` corrects one project: another `repo`, a `docs_path`, a pinned
  `sphinx_stack` or `ulwazi` version. Overrides show up as _Manual_ in the
  evidence.

## Data, caching and the daily run

- `tools/adoption/data/` (git-ignored) holds the JSON. In CI it lives on the
  orphan `adoption-data` branch, one commit per change, which is the history
  of the project.
- `tools/adoption/.cache/` (git-ignored) caches RTD details and builds, raw
  repository files by commit and Ulwazi wheel fingerprints. A second run makes
  almost no network requests.
- `.github/workflows/adoption.yaml` runs daily, on manual dispatch, and when the
  tool changes on `main`. It needs the `RTD_TOKEN` secret. It refuses to
  replace the data when more than `safety.max_error_ratio` of the projects
  failed (exit code 2; `adoption.rejected.json` is uploaded for inspection).
- To publish on GitHub Pages: set _Settings → Pages → Source_ to _GitHub
  Actions_ and the repository variable `ADOPTION_PAGES` to `true`.

## Develop

```bash
uv run --group dev pytest tests/test_adoption_pipeline.py tests/test_adoption_dashboard.py
make lint
```

`tests/adoption_samples.py` generates the sample data used by the tests and
`make adoption-sample`. When a Sphinx Stack release changes what the detection
relies on, update `process/corrections.py` and its tests.
