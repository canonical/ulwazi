# Ulwazi Sphinx theme

Ulwazi, Xhosa for information, is a work-in-progress Sphinx theme based on [Vanilla design](https://github.com/canonical/vanilla-framework).

[Demo website](https://canonical-ulwazi.readthedocs-hosted.com/)

Layout and functionality is derived from [sphinx-basic-ng](https://github.com/pradyunsg/sphinx-basic-ng), developed by [pradyunsg](https://github.com/pradyunsg) and [Alabaster](https://github.com/sphinx-doc/alabaster).

The theme will default to a generic Vanilla Framework style but will have options for the specific Canonical theming to support the org's documentation needs.

## Prerequisites

- **Python**: `>=3.10` (managed by [uv](https://docs.astral.sh/uv/))
- **Node.js** and **npm**: required only for compiling SCSS to CSS (see [Installing Node modules](#installing-node-modules))

## Installing Node modules

Make sure you have [npm](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) installed:

```shell
sudo apt install npm
```

If you do not have the `node_modules` directory (for example, after cloning the repository for the first time), install the JavaScript dependencies:

```shell
npm install
```

## Upgrading the Vanilla Framework

The theme styles are built on the [Vanilla Framework](https://vanillaframework.io/).
To upgrade it to a newer version:

1. Check the latest available version:

   ```shell
   npm view vanilla-framework version
   ```

2. Update the version in `package.json` (the `vanilla-framework` entry in `dependencies`).

3. Install the new version and recompile the SCSS:

   ```shell
   make vanilla-main
   ```

   This runs `npm install` and compiles `ulwazi/theme/ulwazi/assets/main.scss` to
   `ulwazi/theme/ulwazi/static/css/vanilla-main.css`.

   If the compilation fails, consult the
   [Vanilla Framework changelog](https://github.com/canonical/vanilla-framework/blob/main/CHANGELOG.md)
   for breaking changes (for example, renamed or removed mixins and settings) and
   update `ulwazi/theme/ulwazi/assets/` accordingly.

4. Rebuild the docs and verify the result:

   ```shell
   make rebuild
   make test
   ```

   Additionally, check the sample documentation in a browser (`make run`) for visual
   regressions, especially on the
   [cheat sheet pages](docs/content/) that exercise most theme components.

Both `package.json` and `package-lock.json` are tracked in git, so commit the
updated lock file together with the version bump.

## Testing

A Makefile includes some basic functionality to build the theme and then build and run the test content with the theme.

To build the sample documentation using the theme, run:

```shell
make docs
```

To build the sample documentation in an interactive preview, run:

```shell
make run
```

This command uses [uv](https://docs.astral.sh/uv/) to set up a virtual environment, installs dependencies, builds the theme, then builds the documentation in this repo, and serves the result via a local web server.

The resulting environment tracks changes in sample content and rebuilds the local website automatically.
However, changes to the theme might require a full rebuild of the theme package:

```shell
make rebuild
```

This command runs `make clean` to delete files built earlier, and then `make docs` again.

If you change dependencies, you will need to re-build the virtual environment entirely.
That can be done by manually deleting the `.venv` folder or with the `make clean`
command.

## Metadata and SEO

Every page gets a complete, working set of SEO/social-preview metadata
automatically -- `<title>`, `<meta name="description">`, Open Graph tags,
`rel="canonical"`, and favicon. **You never need to add anything by hand.**
Overriding a page's title or description for social previews is optional and
only needed for pages you want to promote with custom text (e.g. a landing
page). See [the contribution guide](docs/content/contribute.rst#page-metadata-and-seo)
for defaults and override syntax.

### Running the test suite

The test suite is split into fast and slow tests. Fast tests run on every
change; slow tests (PDF generation, browser-based visual checks, and Python
version compatibility) require extra system dependencies or take longer.

```shell
make test              # Run fast tests only
make test-fast         # Same as 'make test'
make test-slow         # Run slow tests only (PDF builds, browser checks)
make test-all          # Run all tests (fast and slow)
make test-python-versions  # Build theme and docs on every supported Python version (slow)
make test-coverage     # Run tests and generate coverage report
```

The available tests are:

- **test_site_validation.py** — validates built HTML for broken assets (missing CSS, JS, images)
- **test_pdf_generation.py** — verifies PDF generation produces the expected output file _(slow)_
- **test_scss_propagation.py** — tests SCSS compilation and style propagation to rendered HTML using Playwright _(partially slow)_
- **test_python_versions.py** — builds the theme and sample docs on every supported Python version _(slow)_

See the [Tests documentation](https://canonical-ulwazi.readthedocs-hosted.com/content/tests/) for more details on the test suite.

## Contributing

The theme files are located in the `ulwazi` folder:

- `__init__.py` -- initialization script for the theme.
- `navigation.py` -- modifies the global TOC navigation tree
- `theme/ulwazi/` -- contains the theme files
  - theme.toml -- theme configuration file
  - static -- static content to be used by the theme without processing
  - other files -- HTML templates for Sphinx using Jinja templating engine

If you want to modify HTML code of a page generated by Sphinx before the theme gets applied, see the `_html_page_context` function definition in the initialization script.
