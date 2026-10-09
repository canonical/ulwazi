# Code quality checks

`tests/test_code_quality.py` implements the "Code quality checks" category
(category 8) of the testing strategy. It doesn't run the theme in a browser. It
checks that the code and the files describing it stay consistent with each
other, and it runs the project's existing linters.

The module has two tiers:

- **Six fast checks** catch drift that the linters can't see. They run with
  `make test` on every pull request.
- **Eight slow cases** run the targets of `make lint`, one case per target.

## Fast checks

| Test | What it checks | What it doesn't check |
| --- | --- | --- |
| `test_python_versions_in_sync` | `SUPPORTED_PYTHON_VERSIONS` in `tests/test_python_versions.py` matches the `requires-python` floor, the `Programming Language :: Python :: 3.X` classifiers, the matrix in `.github/workflows/test-python-versions.yaml`, and the ruff, mypy and pyright target versions. | That the theme actually works on those versions; see {doc}`python-versions`. |
| `test_theme_templates_parse` | Every `*.html` template under `ulwazi/theme/ulwazi/` parses in a sandboxed Jinja environment with the i18n extension, which is how Sphinx loads templates. | Undefined variables, missing blocks, or rendered output. Rendering is covered by the {doc}`smoke <smoke>` and {doc}`feature <features>` tests. |
| `test_theme_javascript_syntax` | Every script in `ulwazi/theme/ulwazi/static/js/` passes `node --check`. Skipped when `node` isn't on `PATH`. | Behaviour in a browser; see {doc}`features`. |
| `test_tool_versions_in_sync` | The prettier version pinned in `.pre-commit-config.yaml` matches the pin in `common.mk`. `common.mk` is synced from [starbase](https://github.com/canonical/starbase), so it is the reference. | Other pre-commit hooks, such as ruff, whose versions come from the snap or `uv tool`. |
| `test_test_bookkeeping_in_sync` | Every `tests/test_*.py` file has a `TEST_CATEGORIES` entry and every entry has a file. Every `SLOW_CATEGORY_OVERRIDES` key is in `TEST_CATEGORIES`. Every check in `tests/features.yaml` names an existing test function. Every `make lint` target has a `REQUIRED_TOOLS` entry. | Whether a mapped test actually asserts the feature it is mapped to; see {doc}`coverage`. |
| `test_inventory_counts_match_collection` | Each module's fast and slow counts in the {ref}`inventory table <test-inventory>`, and the "Full selection" totals, equal what `pytest --collect-only` collects for each tier. | The prose that describes each module's behaviour. |

## Linters

`test_make_lint_target` is parametrized from the prerequisites of the `lint:`
rule in the `Makefile`, so adding a linter to `make lint` adds a case:

| Case | Runs | Tools needed on `PATH` |
| --- | --- | --- |
| `lint-ruff` | `ruff check` and `ruff format --diff` | `ruff` |
| `lint-codespell` | `codespell` on the Python sources | `codespell`, `uv` |
| `lint-mypy` | `mypy` on the `ulwazi` package | `uv`, `shellcheck`, `pyright` |
| `lint-prettier` | `prettier --check` on YAML, JSON, CSS and Markdown outside `docs/` | `npm` |
| `lint-pyright` | `pyright` (strict for `ulwazi`) | `uv` |
| `lint-shellcheck` | `shellcheck` on tracked shell scripts | `git`, `file`, `shellcheck` |
| `lint-twine` | `twine check` on the built sdist and wheel | `uv` |
| `lint-uv-lockfile` | `uv lock --check` | `uv` |

All cases also need `make`. The Python sources are the root `*.py` files,
`ulwazi/`, `tests/` and `docs/preview_theme.py`.

## How it is tested

The fast checks read the repository files directly. `pyproject.toml` is read
with the standard library's `tomllib` on Python 3.11 and later. Python 3.10
has no `tomllib`, so it uses `tomli`, which pytest already depends on there.
The inventory check starts two `pytest --collect-only` subprocesses, one per
tier. They collect tests without running them and take about a second.

Each linter case runs `make -s <target>` in the repository root with `CI` unset,
and fails with the last lines of the linter output. When a required tool is
missing, the case is **skipped** and the skip reason names the tool. This is
because the `install-*` targets in `common.mk` would otherwise call
`sudo snap install` during the test run. A skipped case makes the category
`INCOMPLETE` in the recap, not `PASSED`.

The linters are slow because together they take tens of seconds and depend on
system tools and network downloads. `lint-prettier` fetches the pinned
prettier through `npm exec`, and `lint-twine` builds the package into `dist/`.

## Running the checks

| Command | What it runs |
| --- | --- |
| `make test` | The six fast checks, with the rest of the fast suite |
| `make test-code-quality` | Both tiers of this module |
| `make test-slow`, `make test-all` | The linter cases, with the rest of the slow suite |
| `make lint` | The linters directly, without pytest |

```shell
uv run pytest -m slow tests/test_code_quality.py -k lint-ruff
```

On every push and pull request, the `QA` workflow runs `make -k lint` through
the shared starflow lint workflow. The `Run make test` workflow runs the fast
checks. The monthly `Run slow tests` workflow includes the linter cases, but
that runner has no linter snaps installed, so most of them are skipped there.

## Adding a linter

1. Add the target to the `lint:` rule in the `Makefile`.
2. Add the target and the tools it needs to `REQUIRED_TOOLS` in
   `tests/test_code_quality.py`. Until you do, `test_test_bookkeeping_in_sync`
   fails.
3. Update the {ref}`inventory <test-inventory>` slow count for
   `test_code_quality.py`, and the totals. Until you do,
   `test_inventory_counts_match_collection` fails.

## Example output

```text
8 Code quality: fast PASSED (6/6 passed) · slow PASSED (8/8 passed)
```

A failing check lists each problem on its own line:

```text
Python version declarations disagree with SUPPORTED_PYTHON_VERSIONS (tests/test_python_versions.py):
- pyproject.toml Python classifiers are ['3.10', '3.11']; expected ['3.10', '3.11', '3.12', '3.13', '3.14']
```
