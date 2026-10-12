# Welcome to the Ulwazi theme preview

This site previews the Ulwazi Sphinx theme:
a Vanilla Framework-based theme built for Canonical’s
[Sphinx Stack](https://github.com/canonical/sphinx-stack).
It documents the current `main` branch, which can include changes that are not
yet in the latest PyPI release.

## Use Ulwazi

1. Install the theme in the Python environment that builds your documentation:

   ```shell
   pip install ulwazi
   ```

2. Enable the theme in your `conf.py`:

   ```python
   extensions = ["ulwazi"]
   html_theme = "ulwazi"
   localtoc_max_depth = 3
   ```

   The 0.6 PyPI release requires `localtoc_max_depth` explicitly. In 1.0.0,
   it defaults to `3`; keep the setting only if you want a different depth.

3. Build your documentation (with `conf.py` in `docs/`):

   ```shell
   sphinx-build -b dirhtml docs docs/_build/html
   ```

To adapt a complete Canonical-style configuration, start with
[`docs/default-conf.py`](https://github.com/canonical/ulwazi/blob/main/docs/default-conf.py).
It enables optional extensions, so add the corresponding Python packages to your
documentation requirements as well. See {doc}`content/configuration` for
settings and defaults. For an existing Sphinx Stack project, follow
[Switch to the Ulwazi theme](https://documentation.ubuntu.com/sphinx-stack/latest/how-to/switch-to-ulwazi/).

To try features from `main` before the next release, install the theme from
GitHub:

```shell
pip install "ulwazi @ git+https://github.com/canonical/ulwazi.git@main"
```

## Work on Ulwazi

To build and preview this sample site from a clone of the repository, run:

```shell
make run
```

The preview runs at `http://127.0.0.1:8000`. For setup, tests, and pull
request guidance, see {doc}`content/contribute`.

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
:caption: Sample content
Home <self>
content/test
content/rst-cheat-sheet.rst
content/myst-cheat-sheet.md
```

```{toctree}
:hidden:
:caption: Ulwazi documentation
content/configuration
content/contribute
content/preview-workflow
content/tests/index
Use Ulwazi in your documentation<https://documentation.ubuntu.com/sphinx-stack/latest/how-to/switch-to-ulwazi/>
```
