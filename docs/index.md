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

From a clone of this repository, build the theme and sample documentation:

```shell
make docs
```

To preview changes as you make them, run:

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

## Slopstrap demo

```{note}
This section is a **framework demo fixture** for the Slopstrap experiment
branch. The widgets below are auto-hydrated by `slopstrap.js` and their
content is fake by design. Remove this section before merging to `main`.
```

<div class="slop-status"><span class="slop-dot slop-dot-green"></span> All Systems Operational</div>

<h2 class="slop-h2 slop-text-gradient">Supercharge your <span class="slop-serif-emphasis">documentation</span> at scale</h2>

<div class="slop-grid-3">
  <div class="slop-card slop-border-l-purple">
    <div class="slop-icon-box">⚡</div>
    <h3 class="slop-h3">⚡ Glass Cards</h3>
    <p class="slop-muted">Frosted surfaces with cursor spotlight.</p>
  </div>
  <div class="slop-card slop-card-beam slop-border-l-cyan">
    <div class="slop-icon-box slop-icon-cyan">🌀</div>
    <h3 class="slop-h3">🌀 Border Beams</h3>
    <p class="slop-muted">Rotating conic gradient borders.</p>
  </div>
  <div class="slop-card slop-border-l-emerald">
    <div class="slop-icon-box slop-icon-emerald">🚀</div>
    <h3 class="slop-h3">🚀 Bento Grids</h3>
    <p class="slop-muted">Asymmetrical glowing tiles.</p>
  </div>
</div>

<div class="slop-alert slop-border-l-purple">
  <span class="slop-dot slop-dot-purple"></span>
  <div><strong>✨ AI Insight:</strong> This alert is a Slopstrap component rendered through the theme's admonition transform.</div>
</div>

```{toctree}
:hidden:
:caption: Sample content
Home <self>
content/test
content/rst-cheat-sheet.rst
content/myst-cheat-sheet.md
content/slop-demo
```

```{toctree}
:hidden:
:caption: Ulwazi documentation
content/configuration
content/troubleshooting
content/contribute
content/preview-workflow
content/tests/index
Use Ulwazi in your documentation<https://documentation.ubuntu.com/sphinx-stack/latest/how-to/switch-to-ulwazi/>
```
