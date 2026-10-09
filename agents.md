# Ulwazi Sphinx Theme - Agent Guide

## Project Overview

Ulwazi is a Sphinx theme based on Canonical's [Vanilla Framework](https://vanillaframework.io/).
It provides both generic Vanilla styling and Canonical-specific theming for documentation projects.

**Tech Stack**: Python, Sphinx, Jinja2, Vanilla Framework (SCSS), JavaScript
**License**: GPL-3.0
**Python**: >=`3.10` (`3.11` is recommended)

## Common Tasks

### Building

Build theme and docs:

```bash
make docs
```

Build theme and docs, and then run a local web server
(auto-rebuilds on content and theme changes) to serve them:

```bash
make run
```

The web server will continue to run and publish the docs on `http://127.0.0.1:8000` by default.
To override: `make run SPHINX_HOST=0.0.0.0 SPHINX_PORT=8080`

To access the web pages served by web server, you'll need to keep the `make run` command running
and use a different terminal.

When all testing is done, don't forget to terminate the command serving the sample docs
to free up the address for publishing it next time. To terminate the command, use `CTRL+C`
in its terminal.

### Testing

```bash
make test         # Run fast tests only
make test-all     # Run all fast and slow tests (includes PDF and Playwright)
make test-coverage # Run tests and report Python, JS, and feature coverage
```

Available tests:

- **test_smoke.py**: Checks the home-page shell and navigation (fast)
- **test_assets_structure.py**: Checks representative built assets and theme controls (fast)
- **test_features.py**: Checks theme markup (fast) and browser interactions (slow)
- **test_pdf_generation.py**: Verifies PDF generation produces expected output file _(slow)_
- **test_scss_propagation.py**: Tests SCSS compilation and style propagation to rendered HTML using Playwright _(partially slow)_
- **test_accessibility.py**: Scans the MyST cheat sheet in both themes for axe-core WCAG AA colour contrast violations using Playwright (fast, ~7s)
- **test_layout_smoke.py**: Checks every built page renders its article inside `main.l-docs__main`, and (in Chromium at 1440px) that no page overflows the viewport and no element spills out of the main column _(browser check is slow)_
- **test_seo_metadata.py**: Verifies SEO/metadata tags (title, description, canonical, favicon, Open Graph) on built pages
- **test_structured_toc.py**: Verifies domain/slice markup and ARIA in RST and MyST HTML (fast test); browser styling and LaTeX content from both cheat sheets are grouped into a single slow test _(partially slow)_
- **test_python_versions.py**: Builds the theme and sample docs on every supported Python version _(slow)_
- **test_config_robustness.py**: Checks minimal and maximum configurations, defaults, and legacy aliases (fast)
- **test_extension_compatibility.py**: Verifies the theme renders correctly with Sphinx Stack default extensions enabled (grouped fast checks and a slow PDF check). See `docs/content/tests/extension-compatibility.md`
- **test_code_quality.py**: Category 8. Fast consistency checks (Python version declarations, prettier pins, Jinja/JS syntax, test bookkeeping, inventory counts vs. collection) and one slow case per `make lint` target, skipped when its tool is missing. Run both tiers with `make test-code-quality`. See `docs/content/tests/code-quality.md`

#### Test category reporting when adding tests

When adding tests:

1. Prefer an existing `tests/test_*.py` module for the same behavior. For a
   new file, choose its **primary** category from
   `docs/content/testing-strategy.md` and add
   `"test_new.py": "4 Features and regressions"` (for example) to
   `TEST_CATEGORIES` in `tests/conftest.py`.
   Coverage/reporting tests belong to `Test infrastructure`. Use
   `SLOW_CATEGORY_OVERRIDES` only if a file's slow tests need a _different_
   category (see `test_layout_smoke.py`). An unmapped test still runs and
   prints its full pytest ID/result rather than disappearing in a total.
2. Fast is the default; mark PDF, browser, network, or otherwise expensive
   cases `@pytest.mark.slow`. Preserve distinct tests, parameter IDs, and
   fixture isolation—grouping changes output only. For feature checks, also
   follow the `tests/features.yaml` instructions below; category mapping
   does **not** grant feature coverage.
3. Update `docs/content/tests/index.md` when adding a suite. Run `make test`,
   relevant slow tests, and `make test-coverage` for feature mappings. Check
   that the recap shows the right category/tier and failures retain pytest
   IDs. Change `tests/test_test_reporting.py` if changing the reporter itself.

The **Test inventory** table in `docs/content/tests/index.md` must match the
actual collected cases and CLI groups in `tests/conftest.py` exactly, not just
list representative suites. When adding, removing, parametrizing, re-tiering,
or regrouping tests (even within an existing module), update the corresponding
row, fast/slow counts, and verified-behavior description. Account for every
selected pytest case once, including `SLOW_CATEGORY_OVERRIDES` and parameters;
compare the table totals with `make test-all` and `uv run pytest --collect-only`.
Do not claim behaviors that tests do not assert.
`test_inventory_counts_match_collection` (fast, in `tests/test_code_quality.py`)
enforces the counts and totals; `test_test_bookkeeping_in_sync` enforces
`TEST_CATEGORIES`, `features.yaml` node IDs, and `REQUIRED_TOOLS` for every
`make lint` target. Category 8 linters report under `8 Code quality` (slow);
`make lint` remains the CI entry point.

`docs/content/testing-strategy.md` is a design document (the vision). Do not
edit it to describe implemented tests; document facts in
`docs/content/tests/` instead.

See the [test output convention](docs/content/tests/index.md#test-output-convention)
for the compact recap and `uv run pytest -vv` for per-test results.

#### When adding or changing a theme feature

1. Update representative fixtures in `docs/content/myst-cheat-sheet.md` and
   `docs/content/rst-cheat-sheet.rst` in parallel when applicable; use a
   dedicated sample page for a site-level feature.
2. Add or update an **assertion** for the specific rendered markup or browser
   behavior in `tests/test_features.py` (or the appropriate existing test).
   For grouped tests such as `test_features_fast`, inspect the assertions:
   the test's name or a passing Sphinx build alone is not evidence.
3. Add or edit **one** narrowly scoped entry in `tests/features.yaml` under
   `markup` or `site`: `name` describes only verified behavior, `source`
   identifies the fixture, `checks` lists exact pytest node IDs (for example,
   `tests/test_features.py::test_features_fast`). List **all** required tests;
   if none qualifies yet, set `checks: []`. Do not map to a test that merely
   loads a page or script, or duplicate an existing entry to inflate coverage.
4. Ensure mapped tests run in `make test-coverage`: fast tests are selected;
   slow tests need an explicit coverage marker **and** inclusion in the
   `Makefile` marker expression. Run `make test-coverage` and check the final
   summary and `results/feature-coverage.json`; all mapped tests must be
   selected and pass. Run `make lint` and rebuild the docs after changing
   fixtures.

See `docs/content/tests/coverage.md` for scope and limitations of all three
coverage metrics; do not confuse the curated feature percentage with Python
or JavaScript line coverage.

### Cleaning

Clean (delete) the built sample documentation content:

```bash
make docs-clean
```

Clean the built docs and theme files (also removes the `.venv` virtual environment):

```bash
make clean
```

Rebuild theme and docs (combination of `clean` and `docs`):

```bash
make rebuild
```

### Styling

```bash
make vanilla-main  # Install npm dependencies and compile SCSS to CSS
```

### Upgrading the Vanilla Framework

1. Check the latest version: `npm view vanilla-framework version`
2. Update the `vanilla-framework` version in `package.json` (`dependencies`)
3. Install and recompile: `make vanilla-main` (runs `npm install` and compiles
   `ulwazi/theme/ulwazi/assets/main.scss` to `ulwazi/theme/ulwazi/static/css/vanilla-main.css`)
4. If SCSS compilation fails, check the
   [Vanilla Framework changelog](https://github.com/canonical/vanilla-framework/blob/main/CHANGELOG.md)
   for breaking changes (renamed/removed mixins or settings) and update
   `ulwazi/theme/ulwazi/assets/` accordingly
5. Rebuild and verify: `make rebuild`, then `make test` (and `make test-slow` for
   the Playwright color/typography checks), and review the sample docs in a browser
   (`make run`) for visual regressions
6. Commit `package.json` and `package-lock.json` together (both are tracked in git)

### Quick start

Prefer Makefile targets.
The `make docs` command uses [uv](https://docs.astral.sh/uv/) to create the virtual environment and install Python dependencies.

Install Node dependencies (only required for SCSS compilation via `make vanilla-main`):

```bash
npm install
```

**Node.js**: required only for SCSS compilation via `make vanilla-main` (uses npm).

## Project Structure

```text
ulwazi/                      # Main package
├── __init__.py              # Theme setup, HTML page context hooks
├── navigation.py            # Global TOC navigation tree modifications
├── product_menu_gen.py      # Canonical product menu generator
├── tabs.py                  # Tab component handling
└── theme/ulwazi/            # Theme files
    ├── theme.toml           # Theme configuration
    ├── static/              # CSS, JS, fonts (unprocessed)
    ├── assets/              # SCSS source files
    ├── components/          # Reusable HTML components
    ├── sections/            # Page section templates
    └── *.html               # Jinja2 templates for Sphinx pages

docs/                        # Sample documentation for testing
├── conf.py                  # Sphinx configuration
├── content/                 # Sample content for testing (RST, MD)
└── _build/                  # Built output (generated)

tests/                       # Test scripts
```

## Key Files

- **[pyproject.toml](pyproject.toml)**: Package metadata, dependencies, build config
- **[Makefile](Makefile)**: Build automation and common tasks
- **[ulwazi/**init**.py](ulwazi/**init**.py)**: Theme entry point, `_html_page_context` for HTML modification hooks
- **[ulwazi/theme/ulwazi/layout.html](ulwazi/theme/ulwazi/layout.html)**: Base page layout template
- **[docs/conf.py](docs/conf.py)**: Sample docs Sphinx config

## Development Workflow

### Theme Changes

1. Modify files in [ulwazi/](ulwazi/) or [ulwazi/theme/ulwazi/](ulwazi/theme/ulwazi/)
2. `make run` automatically rebuilds the preview; SCSS is compiled before Sphinx
   copies the resulting CSS. For dependency changes or stale builds, use
   `make rebuild`.
3. Test in browser at http://127.0.0.1:8000

### Content Changes

- Sample docs in [docs/content/](docs/content/) auto-rebuilds with `make run`

### Dependency Changes

- Update [pyproject.toml](pyproject.toml)
- Run `make clean` then `make run` to rebuild the uv virtual environment

### HTML Modifications

- Override templates in [ulwazi/theme/ulwazi/](ulwazi/theme/ulwazi/)
- Modify `_html_page_context` function in [ulwazi/**init**.py](ulwazi/__init__.py) for pre-theme processing

### Testing

Clean up the old files:

```bash
make clean
```

Update the Vanilla Framework styles:

```bash
make vanilla-main
```

Build and serve the theme and the sample docs:

```bash
make run
```

While the last command is running, access the default address in
another terminal to check the results manually.

When all testing is done, make sure to terminate the `make run` command in the original terminal.

Run tests to avoid regression:

```bash
make test         # fast tests only
make test-all     # all tests (fast and slow, including PDF and Python version tests)
```

## Code Conventions

### Python

- Follow PEP 8
- Type hints where possible
- BeautifulSoup4 for HTML manipulation
- Use Sphinx extension hooks in `__init__.py`

### Templates (Jinja2)

- Located in [ulwazi/theme/ulwazi/](ulwazi/theme/ulwazi/)
- Use `{{ }}` for expressions, `{% %}` for statements
- Inherit from base templates using `{% extends %}`

### Styles

- [Vanilla Framework](https://vanillaframework.io/) for base styles
- [Vanilla Framework examples](https://vanillaframework.io/docs/examples) - reference implementations of all components. Note: each example can be switched to dark mode.
- SCSS source in [ulwazi/theme/ulwazi/assets/](ulwazi/theme/ulwazi/assets/)
- Compiled CSS in [ulwazi/theme/ulwazi/static/](ulwazi/theme/ulwazi/static/)

## Important Notes

- **Virtual Environment**: Located at `.venv/`, managed automatically by [uv](https://docs.astral.sh/uv/) through Make targets
- **Build Artifacts**: `build/`, `*.egg-info/`, `.venv/`, `docs/_build/` are gitignored
- **Node Modules**: Required for Vanilla Framework compilation
- **Auto-rebuild**: `make run` watches both content and theme changes. Changes to shared navigation toctrees may leave older pages with stale sidebars; use `make rebuild` to refresh the site when needed.
- **Metadata/SEO**: `<title>` suffix, `rel="canonical"`, favicon link, and Open Graph tags
  (`og:title`, `og:description`, `og:image`, etc.) are all generated automatically via
  `sphinxext-opengraph` (declared in `docs/conf.py` `extensions`, and in `pyproject.toml`
  under the `docs` dependency group) plus the `layout.html` template. Per-page `og:*`
  overrides are plain top-level fields (reST bibliographic field / MyST front matter
  key) placed before the title -- e.g. `:og:title: ...` or `og:title: "..."` -- read
  directly by `sphinxext-opengraph`'s own override mechanism. **Do not** add a
  `property=` prefix; that's a misconception carried over from the generic docutils
  `.. meta::` directive and is unnecessary once `sphinxext-opengraph` is installed --
  it always renders `property="og:..."` regardless. The plain page description
  (`<meta name="description">`) is a separate setting: use `.. meta:: :description:`
  (reST) or nest it under `myst.html_meta` (MyST) -- `description` alone is not a
  recognised bibliographic field. See `docs/content/contribute.rst` and the RST/MyST
  cheat sheets for working examples. Do not remove `sphinxext-opengraph` or the
  `favicon_url`/`pageurl`/`docstitle` references in `layout.html` without re-verifying
  metadata output in the built HTML.
- **Sphinx context variable gotcha**: use `favicon_url` in templates, not `favicon`
  (the latter is a stale sphinx-basic-ng convention that Sphinx 7.4+ no longer
  populates); `favicon_url` is already a fully resolved URL and must not be passed
  through `pathto()` again.
- **Native Canonical config**: the theme itself (in `ulwazi/__init__.py`
  `config_inited`) provides the Canonical configuration defaults that
  historically came from the `canonical-sphinx-config` extension (now removed
  as a dependency). This includes: the `slug` config value (used to compute
  `notfound_urls_prefix` for `sphinx-notfound-page`), `exclude_patterns`
  additions, `html_last_updated_fmt` / `html_permalinks_icon` overrides,
  `html_context` defaults (`repo_branch`, `repo_folder` — must be
  slash-delimited, e.g. `/docs/` — and `discourse`), the Read-the-Docs
  `repo_branch` override, and the Canonical `sphinx_modern_pdf_style`
  branding defaults.
- **Bundled 404-page integration**: `sphinx-notfound-page` is a runtime
  dependency, activated automatically via `app.setup_extension()` from the
  theme's `setup()` (idempotent — projects that also list
  `notfound.extension` in `extensions` are unaffected). The theme ships a
  `404.html` template and a `static/404.svg` asset. Opt out with
  `notfound_enabled = False` in conf.py, or `-D notfound_enabled=0` when
  `"ulwazi"` is in `extensions`. For theme-only loading, Sphinx checks `-D`
  overrides before registering theme config values and warns about an unknown
  setting. When the extension is listed explicitly, the flag only skips
  Ulwazi's prefix/template defaults (the extension still generates its own
  404 page). Explicit `notfound_urls_prefix` and `notfound_template` settings
  in conf.py or `-D` also take precedence over the theme defaults. When the
  theme is selected only via `html_theme`, Sphinx loads it after
  `config-inited`; the theme sets up these 404 defaults during late loading
  too, but other Ulwazi config-inited features still require `"ulwazi"` in
  `extensions`. `tests/test_notfound_bundling.py` keeps activation, ordering,
  and theme-only build scenarios in a documented `ACTIVATION_CASES` table;
  separate tests cover opt-out, RTD prefixes, and explicit settings.
  `tests/test_notfound_prefix.py` tests the prefix helper directly.
- **notfound prefix schema detection**: `_notfound_urls_prefix` detects the
  URL schema from the _path_ of `READTHEDOCS_CANONICAL_URL` — the version
  segment is the last path segment, the language segment the one before it,
  each matched positionally against `READTHEDOCS_VERSION` /
  `READTHEDOCS_LANGUAGE`. This indirection is load-bearing: RTD always sets
  those env vars on builds, even when the segments are absent from the URL
  schema (e.g. single-version projects like ulwazi itself, hosted at
  `documentation.ubuntu.com/ulwazi/` with no version/language segment), so
  joining them unconditionally would produce a prefix for URLs that don't
  exist and break every link on the 404 page. Only the path is read — the
  host is irrelevant, which is why this works behind the
  documentation.ubuntu.com reverse proxy (the slug comes from the `slug`
  config value, never from the RTD URL). Off RTD (no
  `READTHEDOCS_CANONICAL_URL`), the prefix is empty and 404 links stay
  relative. Covered by `tests/test_notfound_prefix.py`.
- **PDF branding and extension order**: the theme sets `modern_pdf_options`
  defaults (`author`, `logo`) for `sphinx-modern-pdf-style`, and stages
  `ulwazi/theme/ulwazi/pdf/Canonical-logo-4x.png` into the LaTeX output
  directory via a `builder-inited` hook (`_copy_pdf_assets`) — the logo is
  referenced by bare filename, so it must sit next to the generated `.tex`.
  **`"ulwazi"` must be listed before `"sphinx_modern_pdf_style"` in
  `extensions`**: Sphinx fires `config-inited` in registration order, and
  `sphinx_modern_pdf_style` reads `modern_pdf_options` in its own handler.
  The theme emits a build warning if the order is wrong. Verify PDF changes
  with `cd docs && make pdf` (not `make test-all`, whose
  `docs-pdf-prep-force` prerequisite blocks on a `sudo apt-get` prompt).
- **sphinx-structured-toc**: enabled in `docs/conf.py` (`sphinx_structured_toc`),
  declared at `>=0.2.0` in the `docs` dependency group in `pyproject.toml`. Provides the
  `domain`/`slice` directives for accessible tables of contents (independent of
  `toctree`s); ships its own `domain-list.css` automatically. Examples live in
  the "Structured tables of contents" sections of the two cheat sheets, which
  double as the HTML and LaTeX fixtures for `tests/test_structured_toc.py`
  (no dedicated sample pages). PDF support in 0.2.0 emits bold slice labels
  and linked list items; ARIA attributes apply only to HTML. No `only html`
  wrapper or custom LaTeX visitor is needed in `docs/conf.py`.
  Gotchas: (1) in MyST, fences do not nest at the same fence count; use
  `{domain}` (4 backticks) > `{slice}` (3). The Tabs section needs
  `{tab-set}` at 5 backticks because it contains a `{tab-item}` (4) that
  itself contains a code block (3); (2) when Sphinx combines both cheat
  sheets into one LaTeX document, identically named unmarked items from
  each sheet trigger ambiguity warnings -- use `:suppress-warnings:` on
  their domains; (3) keep `:suppress-warnings:` for the deliberately
  ambiguous links in the explicitly named domains as well.

## Testing Locations

- **Sample docs**: [docs/](docs/) - comprehensive test content
- **Cheatsheet pages**: [docs/content/rst-cheat-sheet.rst](docs/content/rst-cheat-sheet.rst) and [docs/content/myst-cheat-sheet.md](docs/content/myst-cheat-sheet.md) - comprehensive examples of all supported blocks (admonitions, code blocks, tables, etc.). Use these to verify theme rendering. When adding new features, update both cheatsheets with equivalent examples in similar structure.
- **Test scripts**: [tests/](tests/) - validation, PDF generation, SCSS propagation, and Python version compatibility tests
- **Tests documentation**: [docs/content/tests/](docs/content/tests/) - documentation for the test suite, including [Python version compatibility](docs/content/tests/python-versions.md)
- **Built output**: [docs/\_build/](docs/_build/) - inspect generated HTML

## Syntax

Sample docs use MyST Markdown syntax most of the time, with specific pages, like RST cheat sheet, using reStructuredText.

### Formatting Conventions

When editing documentation or markdown files:

- Make sure there is a blank line after headings before content
- Make sure there is a blank line before lists (bullet or numbered)
- Use MyST Markdown for new content unless RST-specific features are required
- Keep examples in cheat sheets structurally parallel between MyST and RST versions

## External Resources

- [Vanilla Framework](https://github.com/canonical/vanilla-framework)
- [sphinx-basic-ng](https://github.com/pradyunsg/sphinx-basic-ng)
- [Demo site](https://documentation.ubuntu.com/ulwazi/)
- [Repository](https://github.com/canonical/ulwazi)

## Maintaining This Guide

If you spot a problem in this guide (outdated information, incorrect commands, missing steps) and fix it, update this file accordingly so the instructions stay accurate for future sessions.
