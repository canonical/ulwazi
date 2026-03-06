# Welcome to the Ulwazi theme preview

This site previews the Ulwazi Sphinx theme:
a Vanilla Framework-based theme built for Canonical’s
[Starter Pack](https://github.com/canonical/starter-pack).

- Want to help? See {doc}`content/contribute`.
- Want to use it? Start with {doc}`content/use`.

## Build and test locally

The included Makefile builds the theme and a sample documentation set so you can inspect
changes quickly.

To build and serve the sample documentation:

```shell
make run
```

This sets up a virtual environment, installs dependencies, builds the theme, builds the documentation,
and serves it locally. Content edits rebuild automatically; theme edits usually require
a full rebuild:

```shell
make rebuild
```

The `make rebuild` command runs `make clean` before `make run`.

If you change dependencies (for example, if you add a new Sphinx extension to
`docs/requirements.txt`), you should rebuild the virtual environment:

```shell
make fclean
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
content/use
```
