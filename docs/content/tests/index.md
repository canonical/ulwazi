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
link in the site; it does not replace Sphinx's build warnings.

## Running the tests

- `make test` runs the fast tests and builds the sample HTML first.
- `make test-slow` runs the slow tests, including browser and PDF checks;
	these need additional dependencies.
- `make test-all` runs both tiers.
- `make test-python-versions` runs the Python version checks in parallel.
- `make test-coverage` runs fast tests plus the slow browser feature journey;
	see {doc}`test coverage <coverage>` for its three metrics and limitations.

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

Tests are grouped so that their pytest output stays minimal when everything
passes, but pinpoints every problem when something fails:

- **When green:** all checks of a test run inside a single pytest test case,
  so a passing run reports one `PASSED` line per test. A test file with both
  a fast and a slow test reports one line per tier it runs in (two lines in
  `make test-all`).
- **When red:** the test collects every failed check it can safely run --
  across all checked pages and parts -- and lists them all in one failure
  message, each tagged by page and checked part. A failure on one page or
  part does not hide problems found elsewhere.

For example, a failing structured-TOC run reports which of the RST or MyST
fixture pages broke and which check failed on it:

```text
structured-TOC slow checks failed:
  - [rst] slice items are not rendered inline (y positions: [11031, 11051])
  - [rst] domain-aria-target span not found
```

The exception is tests that are parametrized on purpose, such as the
{ref}`Python version tests <python-version-tests>`, where each parameter
value is an independently reported result.
