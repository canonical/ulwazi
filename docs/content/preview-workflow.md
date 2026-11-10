# Live preview workflow

This page explains how the interactive preview (`make run`) detects changes
and decides what to rebuild — and what you need to do (almost nothing) while
iterating on the theme or the sample content.

## How to use it

Start the preview:

```shell
make run
```

Then simply edit files. The preview reacts as follows:

- **Content edits** (`docs/content/**`) — the edited page rebuilds
  incrementally, exactly like a normal `sphinx-build` run.
- **Theme edits** (`ulwazi/**`: templates, JS, fonts, images, Python code) —
  all HTML pages are re-rendered and the changed static files are copied into
  the build output.
- **SCSS edits** (`ulwazi/theme/ulwazi/assets/**`) — the CSS is recompiled
  *before* Sphinx runs, so the preview always serves the fresh
  `vanilla-main.css`. Template, script and Python edits recompile it too,
  because the build keeps only the Vanilla Framework classes that theme
  sources use.

Reload the page in your browser to see the result; the server keeps running
until you stop it with `Ctrl+C`.

```{note}
The preview rebuilds page *content*. Sphinx renders each page's sidebar
navigation at build time, so if you edit a shared table of contents, pages
you did not touch can keep an outdated sidebar. Run `make rebuild` to
refresh the whole site.
```

## How it works

The `make run` target starts `sphinx-autobuild`, which watches both the docs
source directory and the whole `ulwazi` theme package. On every detected
change it runs a small helper, `docs/preview_theme.py`, *before* invoking
Sphinx. The helper does three things:

1. **CSS gate** — if any `.scss` file, or any theme source that can mention
   a Vanilla class (`.py`, `.html`, `.js`, `.css` and similar), is newer than
   the compiled `vanilla-main.css` (or the CSS file is missing), it runs
   `make vanilla-main` to recompile it. The compiled CSS keeps only the
   Vanilla Framework classes that theme sources use, so a template edit can
   change it.
   This guarantees that Sphinx copies a fresh stylesheet into the build
   output.
2. **Theme digest** — it computes a SHA-256 hash over every file in the
   `ulwazi` package (templates, JS, fonts, images, SCSS sources — but not
   generated outputs like the compiled CSS or caches) and compares it with
   the hash stored from the previous build in
   `docs/_build/.preview-theme-digest`.
3. **Targeted invalidation** — if the digest changed, meaning this rebuild was
   caused by a theme edit, it deletes the generated `index.html` files under
   `docs/_build/`.

The deletion in step 3 is the key trick. Sphinx only re-renders a page when
the page's *source* or one of its *templates* is newer than the existing
output, and it only copies static files when at least one page is outdated.
Theme static files (JS, CSS, fonts) are neither sources nor templates, so a
theme edit alone marks zero pages as outdated — Sphinx would report
"no targets are out of date" and never copy the updated assets. Deleting the
output files marks every page as outdated, which forces Sphinx to re-render
all pages *and* recopy the static files.

The invalidation is deliberately cheap: the pickled environment and doctrees
are left untouched, so Sphinx re-runs only the write phase (template
rendering and asset copying) instead of re-parsing every document. Content
edits leave the digest unchanged, so they keep using Sphinx's normal
incremental path.

An `--ignore` flag in the `make run` recipe excludes the compiled
`vanilla-main.css` from the watcher. It lives inside the watched theme
directory but is an *output* of the SCSS compilation — without the ignore,
every Sass run would itself trigger another rebuild.

## Related commands

- `make rebuild` — clean build; use it to reset a stale build, after
  dependency changes, or to refresh sidebars after shared-toctree edits.
- `make vanilla-main` — recompile the CSS manually (the preview does this
  automatically when SCSS or other theme sources change).
- `make vanilla-main-debug` — readable, unpruned CSS with a source map, for
  debugging only (written to `node_modules/.cache/ulwazi/debug/`).
