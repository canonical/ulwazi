# Tests

These are the tests currently available in Ulwazi. The
{doc}`testing strategy <../testing-strategy>` describes the broader goals;
not every check proposed there is implemented yet.

## Test inventory

Each row is one **exact CLI group**. Entries in the second column account for
its test modules (`test_layout_smoke.py` is split between groups 3 and 6).
Counts are **selected pytest cases**: parameters count separately; many
assertions inside one grouped case do not.

```{list-table}
:widths: 26 74
:header-rows: 1

* - CLI group
  - Test module, selected cases and verified behavior
* - 1 Build process
  - `test_preview_theme.py` (**1 fast**) — preview invalidation for theme versus content changes; changed SCSS compiles before invalidation.

    `test_pdf_generation.py` (**1 slow**) — the PDF produced by the build prerequisite exists; its contents are not checked.
* - 2 Smoke
  - `test_smoke.py` (**1 fast**, {doc}`details <smoke>`) — home-page content, header/navigation/footer, skip link, active Home link, and no visible template delimiters.
* - 3 Assets and structure
  - `test_assets_structure.py` (**1 fast, 1 slow**, {doc}`details <assets-structure>`) — representative built assets and theme controls; the slow remote-asset probe reports availability **advisorially**, not as a release gate.

    `test_seo_metadata.py` (**1 fast**, {doc}`details <seo-metadata>`) — titles, descriptions, canonical URLs, favicons and Open Graph tags on three sample pages, including overrides.

    `test_layout_smoke.py` (**1 fast**) — every built page's article is inside the docs main column.
* - 4 Features and regressions
  - `test_config_robustness.py` (**5 fast**) — four Read the Docs branch-selection cases; one grouped case for minimal, default, depth, legacy, maximum and fallback configuration.

    `test_features.py` (**1 fast, 1 slow**, {doc}`details <features>`) — grouped theme markup (TOCs, tabs, headings, admonitions, lists, tables, code, search mapping) and browser journeys (consent, navigation, drawer, tabs, copy, theme, search).

    `test_scss_propagation.py` (**1 fast, 3 slow**) — SCSS fixture markup; computed colour, sidebar indicator spacing, and ordered-list marker size in Chromium.
* - 5 Extension compatibility
  - `test_extension_compatibility.py` (**1 fast, 1 slow**, {doc}`details <extension-compatibility>`) — grouped Sphinx Stack extension markup/artifact checks; the slow case checks the expected PDF exists. Not every extension has an asserted rendered feature.

    `test_structured_toc.py` (**1 fast, 1 slow**, {doc}`details <structured-toc>`) — RST/MyST domain/slice markup, links and ARIA; Chromium styling and generated LaTeX content.

    `test_notfound_bundling.py` (**14 fast**) — bundled 404 activation/order, opt-outs and overrides, rendered 404 shell/asset, and sitemap exclusion across parametrized cases.
* - 6 Responsive layout
  - `test_layout_smoke.py` (**1 slow**) — all built pages at 1440px: no viewport overflow or unclipped spill from the main column.

    `test_responsive.py` (**5 slow**, {doc}`details <responsive-layout>`) — home-page columns and top bar at 1280px; top-bar menu and side drawer at 375px and 768px.
* - 7 Python and environments
  - `test_notfound_prefix.py` (**9 fast**) — 404 URL prefixes across local, single/versioned/translated Read the Docs URLs, mismatches and slug normalization.

    `test_python_versions.py` (**5 slow**, {doc}`details <python-versions>`) — isolated installs and warning-free documentation builds on Python 3.10–3.14.
* - 9 Accessibility
  - `test_accessibility.py` (**1 fast**) — axe **colour-contrast violations only** on the MyST cheat sheet in light and dark Chromium themes.
* - Test infrastructure
  - `test_coverage_metrics.py` (**7 fast**) — V8 line accounting, aggregate coverage summaries, missing-report rejection and PR baseline comparisons.

    `test_test_reporting.py` (**9 fast**) — CLI category/tier assignments, parameter and outcome accounting, and unmapped-case visibility.
```

**Full selection:** 73 cases across 18 modules (54 fast, 19 slow); each case
belongs to exactly one CLI group. Category 8 (code quality) is run by
`make lint`, not pytest, so it does not appear in the test recap. CLI grouping
is separate from the curated {doc}`feature coverage <coverage>` metric and
does not imply every feature in a module is fully tested. See
{doc}`../testing-strategy` for goals beyond these implemented checks.

## Running the tests

- `make test` runs the fast tests and builds the sample HTML first.
- `make test-slow` runs the slow tests, including browser and PDF checks;
	these need additional dependencies.
- `make test-all` runs both tiers.
- `make test-python-versions` runs the Python version checks in parallel.
- `make test-coverage` runs fast tests plus the slow browser feature journey
	and the computed-colour check; see {doc}`test coverage <coverage>` for its
	three metrics and limitations.

(test-addition-checklist)=
## Add a test

1. Add a `test_*` function in the relevant `tests/test_*.py` file, or create a
	new file. Keep parametrized cases independent; do not merge them for output.
2. Choose its **primary reporting category** from {doc}`../testing-strategy`.
	For a new file, map its filename in `TEST_CATEGORIES` in
	`tests/conftest.py` (for example, `"test_new_feature.py": "4 Features and
	regressions"`). Use `"Test infrastructure"` for coverage/reporter tests.
	If a file's slow tests belong to a *different* category, add its filename
	to `SLOW_CATEGORY_OVERRIDES`; otherwise one file mapping covers both tiers.
3. Leave quick tests unmarked (**fast**). Add `@pytest.mark.slow` for PDF,
	browser, network, or otherwise expensive tests. `make test` selects fast;
	`make test-slow` and `make test-all` include slow tests. If a new check
	verifies a theme feature, follow {doc}`coverage` to map its exact pytest
	ID in `tests/features.yaml` (separate from the reporting category).
4. Run `make test` and, for slow tests,
	`uv run pytest -m slow tests/test_new_feature.py`. Run `make test-coverage`
	if you changed a feature mapping. Confirm the expected category and tier
	in the recap; update this page's inventory when adding a suite.

Mapping is optional for execution: a new, unmapped file still runs, and every
selected case appears by full pytest ID and result, including parameter IDs.

### Shared test setup

Pytest loads `tests/conftest.py` automatically. Its `built_site` fixture builds
fresh HTML in a temporary directory for the smoke, asset, and feature tests.
This avoids stale `docs/_build` output and lets coverage observe the theme's
Python hooks. The Make targets still run the regular docs build, which also
supports tests that read its output.

```{toctree}
:hidden:
:maxdepth: 1

Smoke <smoke>
Assets and structure <assets-structure>
SEO and metadata <seo-metadata>
Structured TOC <structured-toc>
Theme features <features>
Responsive layout <responsive-layout>
Python versions <python-versions>
Extension compatibility <extension-compatibility>
Test coverage <coverage>
```

(test-output-convention)=
## Test output convention

The default recap shows one line per selected category, with separate results
for the fast and/or slow tiers, plus a line for test infrastructure:

```text
4 Features and regressions: fast PASSED (7/7 passed) · slow PASSED (4/4 passed)
```

`PASSED` requires every selected case in that tier to pass. Failures, fixture
errors, skips, and unfinished cases show `FAILED` or `INCOMPLETE`; pytest still
prints the exact failing ID and traceback. Unmapped cases print their IDs in
the recap instead of a category total. The run also shows `Running N selected
tests...` and pytest progress dots/percentage (xdist shows worker startup).
Progress advances when a test finishes. For individual `PASSED` lines use
`uv run pytest -vv` (or `PYTEST_ADDOPTS=-vv` with Make).

Only selected tiers/categories appear. Code quality (category 8) runs via
`make lint`; the contrast check reports under category 9 Accessibility (fast),
and the responsive browser cases under category 6 Responsive layout (slow).
Grouping changes *only the output*, not pytest IDs, fixtures,
parametrization, or the {ref}`Python-version tests <python-version-tests>`.
