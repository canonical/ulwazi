# Ulwazi Sphinx theme

Ulwazi, Xhosa for information, is a Sphinx theme based on [Vanilla design](https://github.com/canonical/vanilla-framework).

[Documentation and demo](https://documentation.ubuntu.com/ulwazi/) |
[PyPI](https://pypi.org/project/ulwazi/) |
[Issues](https://github.com/canonical/ulwazi/issues)

Layout and functionality is derived from [sphinx-basic-ng](https://github.com/pradyunsg/sphinx-basic-ng), developed by [pradyunsg](https://github.com/pradyunsg) and [Alabaster](https://github.com/sphinx-doc/alabaster).

The theme will default to a generic Vanilla Framework style but will have options for the specific Canonical theming to support the org's documentation needs.

## Use the theme

1. Install Ulwazi in the Python environment that builds your documentation:

   ```shell
   pip install ulwazi
   ```

2. Enable it in your Sphinx `conf.py`:

   ```python
   extensions = ["ulwazi"]
   html_theme = "ulwazi"
   ```

3. To build the theme and sample documentation from this repository's root, use
   its Makefile target:

   ```shell
   make docs
   ```

   In another Sphinx project, use that project's own Makefile target (often
   `make -C docs html`); `make docs` is specific to this repository.

The [documentation site](https://documentation.ubuntu.com/ulwazi/) describes
the current `main` branch, which can include changes not yet released on PyPI.
To try those changes, install the theme from GitHub:

```shell
pip install "ulwazi @ git+https://github.com/canonical/ulwazi.git@main"
```

For a fuller Canonical-style setup, adapt
[`docs/default-conf.py`](docs/default-conf.py). It enables optional extensions,
so add their packages to your documentation requirements too. See the
[configuration reference](https://documentation.ubuntu.com/ulwazi/content/configuration/)
for every Ulwazi-specific setting. If you are migrating a Sphinx Stack project,
see [Switch to the Ulwazi theme](https://documentation.ubuntu.com/sphinx-stack/latest/how-to/switch-to-ulwazi/).

## Configuration notes

### Metadata and SEO

Ulwazi's templates render the page `<title>`, a canonical link when
`html_baseurl` is set, and a favicon link when `html_favicon` is set.
Descriptions and Open Graph tags come from
[sphinxext-opengraph](https://github.com/sphinx-doc/sphinxext-opengraph):
install `sphinxext-opengraph`, add `"sphinxext.opengraph"` to `extensions`,
and configure `ogp_site_url`, `ogp_site_name`, and `ogp_image` as needed.
The sample [`docs/conf.py`](docs/conf.py) shows a complete setup. Once that
is in place, overriding a page's social-preview title or description is
optional. See [the contribution guide](docs/content/contribute.rst#page-metadata-and-seo)
for defaults and override syntax.

### Analytics

On `main`, Ulwazi includes Canonical's Google Tag Manager container
(`GTM-N384JMX2`) on HTML pages by default. Set
`html_context["tag_id"]` to use a different container. See the
[configuration reference](https://documentation.ubuntu.com/ulwazi/content/configuration/#with-defaults).

### 404 page

The theme bundles the [sphinx-notfound-page](https://github.com/readthedocs/sphinx-notfound-page)
extension and activates it automatically when Ulwazi is enabled -- **you do
not need to list `notfound.extension` separately.** A styled 404 page (with
the Canonical penguin) is generated for HTML builds, and links on it resolve
correctly on Read the Docs.

Set the `slug` config value in your `conf.py` to the path segment of your
docs site URL (e.g. `slug = "ulwazi"` for `https://documentation.ubuntu.com/ulwazi/`)
so that links on the 404 page resolve correctly when hosted on Read the Docs.
If your project sets `notfound_urls_prefix` or `notfound_template` explicitly,
Ulwazi leaves those settings unchanged.

To opt out of the 404-page integration, set `notfound_enabled = False` in your
`conf.py`. If `"ulwazi"` is in `extensions`, you can also pass
`-D notfound_enabled=0` on the command line. With `html_theme = "ulwazi"`
alone, use the `conf.py` flag: Sphinx processes command-line overrides before
loading theme entry points and would warn that the flag is unknown. Projects
that already list `notfound.extension` may keep that entry: Sphinx loads it
only once. In such projects, the opt-out skips **Ulwazi's** 404 defaults but
does not disable the explicitly enabled extension or its 404 page.

### Structured-TOC styling (temporary)

If your project uses [sphinx-structured-toc](https://github.com/canonical/sphinx-structured-toc),
Ulwazi temporarily styles its `domain`/`slice` blocks -- removing bullets
and indent from the slice list, colouring the vertical separators between
slice items in the brand colour, and normalizing visited-link colour --
until the extension ships equivalent styling of its own. Nothing outside a
`domain`/`slice` block is affected.

Set `ulwazi_structured_toc_styling = False` in `conf.py` to opt out, or
`ulwazi_structured_toc_separator_color_light` / `_dark` to override either
separator colour. See the
[configuration reference](docs/content/configuration.md#structured-toc-styling-temporary)
for details.

## Develop Ulwazi

See the [contribution guide](https://documentation.ubuntu.com/ulwazi/content/contribute/)
for the full workflow, including checks and pull request guidance.

### Prerequisites

- **Git**, **make**, and **Python** `>=3.10` (`3.11` is recommended)
- **uv**: the Make targets install it if it is missing
- **Node.js** and **npm**: required only when compiling SCSS to CSS; `make vanilla-main`
  tries to install Node.js if `npm` is missing

The setup targets may use `snap`, Homebrew, or the uv installer when a required
tool is missing. Install the tools yourself first if you prefer not to grant
`sudo` access during setup.

### Build and preview

From the repository root, build the sample documentation:

```shell
make docs
```

Start the live preview:

```shell
make run
```

The preview runs at `http://127.0.0.1:8000`. To use another address, run, for
example, `make run SPHINX_HOST=0.0.0.0 SPHINX_PORT=8080`. Stop it with
`Ctrl+C`.

The preview tracks sample content and theme files. On a theme change it
rebuilds the HTML; SCSS changes are compiled to CSS before Sphinx runs. See
the [preview workflow](https://documentation.ubuntu.com/ulwazi/content/preview-workflow/)
for details. After dependency changes, or to clear a stale build, run:

```shell
make rebuild
```

This deletes earlier build output and the `.venv` virtual environment, then
builds the docs again.

### Run checks

```shell
make test              # Run fast tests
make test-slow         # Run slow tests (PDF builds, browser checks)
make test-all          # Run fast and slow tests
make test-coverage     # Report Python, JS, and feature coverage
make lint              # Run the linters used by CI
```

Slow tests need extra system dependencies. See the
[test inventory](https://documentation.ubuntu.com/ulwazi/content/tests/#test-inventory)
for every suite and the
[coverage guide](https://documentation.ubuntu.com/ulwazi/content/tests/coverage/)
for what the three coverage numbers mean.

### Upgrade the Vanilla Framework

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

### Optional: Workshop development environment

As an alternative to installing the prerequisites locally, you can develop
Ulwazi inside a [Workshop](https://ubuntu.com/workshop) container. The
repository ships a workshop definition (`workshop.yaml`) that provides
Node.js, uv, and VS Code Remote, and forwards the documentation preview to
your host.

After [installing Workshop](https://ubuntu.com/workshop/docs/tutorial/part-1-get-started/)
(including its LXD prerequisite), launch the workshop and open a shell in it:

```shell
workshop launch ulwazi
workshop shell ulwazi
```

From there, use the ordinary build commands, for example `make run` to start
the interactive preview. The preview is forwarded to
`http://localhost:8001` on your host, so it doesn't conflict with a local
(non-Workshop) preview on port 8000.

Workshop is entirely optional; the local setup described above remains the
default way to contribute.

### Project layout

The theme files are located in the `ulwazi` folder:

- `__init__.py` -- initialization script for the theme.
- `navigation.py` -- modifies the global TOC navigation tree
- `product_menu_gen.py` -- generates the Canonical product menu (optional)
- `tabs.py` -- styles and structures sphinx-design tabs in accordance with Vanilla
- `theme/ulwazi/` -- contains the theme files
  - `theme.toml` -- theme configuration file
  - `assets/` -- SCSS sources compiled into `static/css/vanilla-main.css`
  - `components/` and `sections/` -- reusable Jinja template fragments
  - `static/` -- CSS, JavaScript, fonts, and images used without processing
  - other `.html` files -- page templates for Sphinx

If you want to modify HTML code of a page generated by Sphinx before the theme gets applied, see the `_html_page_context` function definition in the initialization script.
