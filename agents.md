# Ulwazi Sphinx Theme - Agent Guide

## Project Overview

Ulwazi is a Sphinx theme based on Canonical's [Vanilla Framework](https://vanillaframework.io/).
It provides both generic Vanilla styling and Canonical-specific theming for documentation projects.

**Tech Stack**: Python, Sphinx, Jinja2, Vanilla Framework (SCSS), JavaScript
**License**: GPL-3.0
**Python**: >=`3.8` (`3.11` is recommended)

## Common Tasks

### Building

Build theme and docs:

```bash
make docs
```

Build theme and docs, and then run a local web server
(auto-rebuilds on content changes) to serve them:

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
make test         # Run all tests
```

Available tests:

- **test_site_validation.py**: Validates built HTML for broken assets (missing CSS, JS, images)
- **test_pdf_generation.py**: Verifies PDF generation produces expected output file _(slow)_
- **test_scss_propagation.py**: Tests SCSS compilation and style propagation to rendered HTML using Playwright _(partially slow)_
- **test_python_versions.py**: Builds the theme and sample docs on every supported Python version _(slow)_

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
2. Run `make rebuild` (theme changes require full rebuild)
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
- **Auto-rebuild**: `make run` watches content changes but NOT theme changes
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
- [Demo site](https://canonical-ulwazi.readthedocs-hosted.com/)
- [Repository](https://github.com/canonical/ulwazi)

## Maintaining This Guide

If you spot a problem in this guide (outdated information, incorrect commands, missing steps) and fix it, update this file accordingly so the instructions stay accurate for future sessions.
