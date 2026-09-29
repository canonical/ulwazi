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
- {doc}`Theme features <features>` (`tests/test_features.py`, **fast and
	slow**) checks generated markup and browser interactions, including tabs,
	dark mode, and search.
- **SCSS propagation** (`tests/test_scss_propagation.py`, **fast and slow**)
	checks the presence of custom styling in built HTML and selected rendered
	styles in a browser.
- **PDF generation** (`tests/test_pdf_generation.py`, **slow**) checks that
	the PDF build produces its expected output file.
- {doc}`Python version compatibility <python-versions>`
	(`tests/test_python_versions.py`, **slow**) checks installation and the
	documentation build on supported Python versions.

Follow the linked pages for detailed checks, sample content, and limitations.
In particular, the asset test covers representative pages rather than every
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
Theme features <features>
Python versions <python-versions>
Test coverage <coverage>
```
