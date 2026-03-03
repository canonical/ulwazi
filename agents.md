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
make html
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
- **test_pdf_generation.py**: Verifies PDF generation produces expected output file
- **scss_propagation.py**: Tests SCSS compilation and style propagation to rendered HTML using Playwright

### Cleaning

Clean (delete) the built sample documentation content:

```bash
make clean-doc
```

Clean the built docs and theme files:

```bash
make clean
```

Clean everything including venv:

```bash
make fclean
```

Rebuild theme and docs (combination of `clean` and `run`):

```bash
make rebuild
```

### Styling

```bash
make npm-install  # Install Vanilla Framework modules
make vanilla-main # Compile SCSS to CSS
```

### Quick start

Prefer Makefile targets.
The `make run` command creates the virtualenv and installs Python deps from requirements.

Install Node dependencies (only if you need to compile SCSS):

```bash
yarn install
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
- **[requirements.txt](requirements.txt)**: Development dependencies
- **[ulwazi/__init__.py](ulwazi/__init__.py)**: Theme entry point, `_html_page_context` for HTML modification hooks
- **[ulwazi/theme/ulwazi/layout.html](ulwazi/theme/ulwazi/layout.html)**: Base page layout template

## Development Workflow

### Theme Changes

1. Modify files in [ulwazi/](ulwazi/) or [ulwazi/theme/ulwazi/](ulwazi/theme/ulwazi/)
2. Run `make rebuild` (theme changes require full rebuild)
3. Test in browser at http://127.0.0.1:8000

### Content Changes

- Sample docs in [docs/content/](docs/content/) auto-rebuilds with `make run`

### Dependency Changes

- Update [requirements.txt](requirements.txt) and [pyproject.toml](pyproject.toml)
- Run `make fclean` then `make run` to rebuild venv

### HTML Modifications

- Override templates in [ulwazi/theme/ulwazi/](ulwazi/theme/ulwazi/)
- Modify `_html_page_context` function in [ulwazi/__init__.py](ulwazi/__init__.py) for pre-theme processing

### Testing

Clean up the old files:

```bash
make fclean
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

Run automatic tests to avoid regression:

```bash
make tests
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
- SCSS source in [ulwazi/theme/ulwazi/assets/](ulwazi/theme/ulwazi/assets/)
- Compiled CSS in [ulwazi/theme/ulwazi/static/](ulwazi/theme/ulwazi/static/)

## Important Notes

- **Virtual Environment**: Located at `.venv/`, managed automatically by Make
- **Build Artifacts**: `build/`, `*.egg-info/`, `.venv/`, `docs/_build/` are gitignored
- **Node Modules**: Required for Vanilla Framework compilation
- **Auto-rebuild**: `make run` watches content changes but NOT theme changes
- **Dependencies**: Core deps in [pyproject.toml](pyproject.toml), dev deps in [requirements.txt](requirements.txt)

## Testing Locations

- **Sample docs**: [docs/](docs/) - comprehensive test content
- **Cheatsheet pages**: [docs/content/rst-cheat-sheet.rst](docs/content/rst-cheat-sheet.rst) and [docs/content/myst-cheat-sheet.md](docs/content/myst-cheat-sheet.md) - comprehensive examples of all supported blocks (admonitions, code blocks, tables, etc.). Use these to verify theme rendering. When adding new features, update both cheatsheets with equivalent examples in similar structure.
- **Test scripts**: [tests/](tests/) - validation and PDF generation tests
- **Built output**: [docs/_build/](docs/_build/) - inspect generated HTML

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
