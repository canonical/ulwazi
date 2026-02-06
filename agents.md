# Ulwazi Sphinx Theme - Agent Guide

## Project Overview

Ulwazi is a Sphinx theme based on Canonical's [Vanilla Framework](https://vanillaframework.io/).
It provides both generic Vanilla styling and Canonical-specific theming for documentation projects.

**Tech Stack**: Python, Sphinx, Jinja2, Vanilla Framework (SCSS), JavaScript  
**License**: GPL-3.0  
**Python**: >=`3.8` (`3.11` is recommended)

## Quick Start

### Setup

Install Node dependencies:

```bash
yarn install
```

Build theme and run dev server (auto-rebuilds on content changes):

```bash
make run
```

Full rebuild (cleans + rebuilds theme and docs):

```bash
make rebuild
```

Clean everything including venv:

```bash
make fclean
```

### Development Server

- Default: http://127.0.0.1:8000
- Override: `make run SPHINX_HOST=0.0.0.0 SPHINX_PORT=8080`

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

## Common Tasks

### Building

```bash
make html         # Build docs only (no serve)
make install      # Build and install theme package
```

### Testing

```bash
make test         # Run all tests
```

### Cleaning

```bash
make clean-doc    # Clean built documentation
make clean-sp     # Clean Sphinx environment
make clean        # Clean theme files and doc environment
```

### Styling

```bash
make npm-install  # Install Vanilla Framework modules
make vanilla-main # Compile SCSS to CSS
```

## Development Workflow

### Theme Changes

1. Modify files in [ulwazi/](ulwazi/) or [ulwazi/theme/ulwazi/](ulwazi/theme/ulwazi/)
2. Run `make rebuild` (theme changes require full rebuild)
3. Test in browser at http://127.0.0.1:8000

### Content Changes

- Sample docs in [docs/content/](docs/content/) auto-rebuild with `make run`
- No rebuild needed for content-only changes

### Dependency Changes

- Update [requirements.txt](requirements.txt) or [pyproject.toml](pyproject.toml)
- Run `make fclean` then `make run` to rebuild venv

### HTML Modifications

- Override templates in [ulwazi/theme/ulwazi/](ulwazi/theme/ulwazi/)
- Modify `_html_page_context` function in [ulwazi/__init__.py](ulwazi/__init__.py) for pre-theme processing

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
- **Test scripts**: [tests/](tests/) - validation and PDF generation tests
- **Built output**: [docs/_build/](docs/_build/) - inspect generated HTML

## External Resources

- [Vanilla Framework](https://github.com/canonical/vanilla-framework)
- [sphinx-basic-ng](https://github.com/pradyunsg/sphinx-basic-ng)
- [Demo site](https://canonical-ulwazi.readthedocs-hosted.com/)
- [Repository](https://github.com/canonical/ulwazi)
