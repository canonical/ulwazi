# Welcome to the Ulwazi theme preview

This site previews the Ulwazi Sphinx theme:
a Vanilla Framework-based theme built for Canonical’s
[Sphinx stack](https://github.com/canonical/sphinx-stack).

- Want to help? See {doc}`content/contribute`.
- Want to use it? Start with [Use Ulwazi in your documentation](https://documentation.ubuntu.com/sphinx-stack/latest/contribute/test-ulwazi-theme/).

## Build and test locally

The included Makefile builds the theme and a sample documentation set so you can inspect
changes quickly.

To build the sample documentation:

```shell
make docs
```

To build the sample documentation in an interactive preview, run:

```shell
make run
```

This uses [uv](https://docs.astral.sh/uv/) to set up a virtual environment, installs dependencies, builds the theme, builds the documentation,
and serves it locally. Content edits rebuild automatically; theme edits usually require
a full rebuild:

```shell
make rebuild
```

The `make rebuild` command runs `make clean` before `make docs`.

If you change dependencies (for example, if you add a new package to
`pyproject.toml`), you should rebuild the virtual environment:

```shell
make clean
```

## Contribute

Core theme files live in the `ulwazi` package:

- `__init__.py` — theme initialization and hooks
- `navigation.py` — global TOC shaping
- `theme/ulwazi/` — Jinja templates, `theme.toml` configuration file, and unprocessed `static/` assets

To tweak the HTML before theming, see the `_html_page_context` in `__init__.py`.

## Sample section

This area demonstrates heading levels, spacing, and typography.

For checking the rendering of documentation features and docs,
see the [MyST](myst-ref) and [RST](rst_ref) syntax references.

### Sub-heading (h3)

Subsections inherit the same spacing and typography tokens.

## Second heading (h2)

This is a new higher-level section.

```{rst-class} heading-test-scss
This is a test about SCSS propagation.
```

```{toctree}
:hidden:

Home <self>
content/test
content/contribute
Use Ulwazi in your documentation <https://documentation.ubuntu.com/sphinx-stack/latest/contribute/test-ulwazi-theme/>
```
