# Tests

These are the tests currently available in Ulwazi. The
{doc}`testing strategy <../testing-strategy>` describes the broader goals;
not every check proposed there is implemented yet.

## Test inventory

- {doc}`Smoke <smoke>` (`tests/test_smoke.py`, **fast**) checks the home-page
	content and essential theme layout.
- {doc}`Assets and structure <assets-structure>`
	(`tests/test_assets_structure.py`, **fast and slow**) checks local assets
	and theme-generated controls, plus advisory remote availability on
	representative pages.
- {doc}`SEO and metadata <seo-metadata>` (`tests/test_seo_metadata.py`, **fast**)
	checks page titles, descriptions, canonical links, favicons, and Open Graph
	tags.
- {doc}`Structured TOC <structured-toc>`
	(`tests/test_structured_toc.py`, **fast and slow**) checks the
	sphinx-structured-toc extension's domain/slice markup and ARIA in both
	cheat sheets, plus browser styling and LaTeX output.
- {doc}`Theme features <features>` (`tests/test_features.py`, **fast and
	slow**) checks generated markup and browser interactions, including tabs,
	dark mode, and search.
- **Accessibility** (`tests/test_accessibility.py`, **fast**) scans the MyST
	cheat sheet in Chromium, in both light and dark themes, for axe-core
	WCAG AA colour contrast violations.
- **Configuration robustness** (`tests/test_config_robustness.py`, **fast**)
	groups minimal builds, local TOC depth defaults and overrides, and feedback
	links with omitted or deprecated repository settings into one reported test.
	The maximum-configuration fixture overrides all defaults in the
	{doc}`configuration reference <../configuration>`, checks supported settings
	in the rendered page, and exercises fallback edit/view URLs. Settings not yet
	supported are checked only for value preservation in `html_context`.
- **SCSS propagation** (`tests/test_scss_propagation.py`, **fast and slow**)
	checks the presence of custom styling in built HTML and selected rendered
	styles in a browser.
- **Layout smoke** (`tests/test_layout_smoke.py`, **fast and slow**) checks
      that every built page renders its article inside the main docs column,
      and, in a browser at 1440px, that no page is wider than the viewport and
      no element (like an unsized icon) spills out of the main column.
- {doc}`Responsive layout <responsive-layout>` (`tests/test_responsive.py`,
	**slow**) checks the home page in Chromium at 375px, 768px, and 1280px,
	including the top-bar menu and small-screen side-navigation drawer.
- **PDF generation** (`tests/test_pdf_generation.py`, **slow**) checks that
      the PDF build produces its expected output file.
- {doc}`Python version compatibility <python-versions>`
      (`tests/test_python_versions.py`, **slow**) checks installation and the
      documentation build on supported Python versions.
- {doc}`Extension compatibility <extension-compatibility>`
      (`tests/test_extension_compatibility.py`, **fast and slow**) checks that
      the theme renders correctly with every Sphinx Stack default extension
      enabled, plus the PDF build.
- **Bundled 404 integration** (`tests/test_notfound_bundling.py` and
  `tests/test_notfound_prefix.py`, **fast**) checks automatic extension
  activation, opt-outs, 404 output, and Read the Docs URL prefixes.
- **Test infrastructure** (`tests/test_coverage_metrics.py` and
  `tests/test_test_reporting.py`, **fast**) checks the coverage calculations
  and the accuracy of the category/tier recap.

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
