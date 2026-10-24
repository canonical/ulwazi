# Troubleshooting

This page collects problems commonly seen when adopting Ulwazi, especially
when migrating a project from the previous, Furo-based Canonical Sphinx
Stack (v2.x and earlier). Each entry explains the symptom, the cause, and a
workaround until the theme fixes it.

If your problem is not listed here, check the
[configuration reference](configuration.md) first, then
[open an issue](https://github.com/canonical/ulwazi/issues).

## The root page `<title>` repeats the site title

**Symptom:** the root page's browser tab or search-engine result reads like:

```text
Charmed Apache Kafka documentation — Charmed Apache Kafka documentation
```

**Cause:** Ulwazi renders `<title>{{ page heading }} — {{ html_title }}</title>`
on every page. On the root page the page heading (the H1 title) commonly
equals `html_title`, because projects following the Sphinx Stack guide set
`project = "X documentation"` and use the same words for the index H1.

**Workaround:** none in the theme yet. Until it is fixed, set the root page's
H1 to something other than the site title (for example, "Welcome" or a
product-specific landing title).

**Tracked in** [ulwazi#202](https://github.com/canonical/ulwazi/issues/202).

## The feedback button pre-fills "documentation" twice

**Symptom:** clicking **Give feedback** opens a GitHub issue whose body reads:

```text
*Please describe the question or issue you're facing with X documentation documentation.*
```

**Cause:** the feedback template appends a hard-coded `" documentation"`
after the project name. With `project = "X documentation"` (the recommended
setting), the word is duplicated.

**Workaround:** none in the theme yet; the string is fixed in the template.
Setting `html_title` or other title values does not affect it.

**Tracked in** [ulwazi#203](https://github.com/canonical/ulwazi/issues/203).

## Legacy `_templates/header.html` and `footer.html` overrides do nothing

**Symptom:** after migrating, custom analytics snippets, header menus, or
footer blocks that worked with the Furo-based stack silently disappear. The
build succeeds without warnings.

**Cause:** Ulwazi does not call the `header.html` / `footer.html` template
names that the previous stack's how-tos recommended overriding. Its page
shell includes `sections/header.html` and `sections/footer.html` instead.
Sphinx resolves templates from `templates_path` first, so an override placed
at `_templates/sections/header.html` **does** take effect; a file named
`_templates/header.html` is simply never loaded.

**Workaround:** port each override to the Ulwazi template path or to a
configuration value:

- Google Tag Manager / Google Analytics: set your own container ID in
  `html_context["tag_id"]` instead of injecting a script via `header.html`.
  Ulwazi includes the GTM snippet on every HTML page; without a custom
  `tag_id` it uses Canonical's default container, which silently replaces
  your project's analytics.
- Header menus and footer links: use the `html_context` keys documented in
  the [configuration reference](configuration.md) (`link1_name`/`link1_URL`,
  `footer`, `help_links`, and related settings).
- Any markup that has no configuration equivalent: copy the relevant
  section template from `ulwazi/theme/ulwazi/sections/` into
  `_templates/sections/` in your project and edit it there.

**Tracked in** [ulwazi#204](https://github.com/canonical/ulwazi/issues/204).

## `repo_default_branch` is ignored; edit links point at the wrong branch

**Symptom:** "edit this page" and "view source" links point at `main` even
though the project's documentation branch is different.

**Cause:** `repo_default_branch` was the `html_context` key used by the
previous stack. Ulwazi reads `repo_branch` and only maps the older
`github_version` alias, so a migrated `repo_default_branch` value is
silently ignored.

**Workaround:** rename the key:

```python
html_context = {
    "repo_branch": "my-default-branch",
}
```

**Tracked in** [ulwazi#195](https://github.com/canonical/ulwazi/issues/195).

## Previous/next page navigation buttons are gone

**Symptom:** the previous/next buttons that the Furo-based theme rendered at
the bottom of pages (some projects added them via a custom footer template)
no longer appear, and setting `sequential_nav` in `html_context` has no
effect.

**Cause:** sequential navigation is not implemented in Ulwazi yet. The
`sequential_nav` key is accepted but no template reads it.

**Workaround:** none yet. If your tutorial flow depends on the buttons,
track progress in [ulwazi#196](https://github.com/canonical/ulwazi/issues/196),
which covers re-implementing the footer features dropped from
canonical-sphinx (sequential nav, contributors, last updated).

## `display_contributors`, `github_issues`, and `product_tag` have no effect

**Symptom:** setting these `html_context` keys changes nothing in the
rendered pages.

**Cause:** these legacy keys are not read by any Ulwazi template yet. They
are listed (with their defaults) under
{ref}`"Not currently supported" <not-currently-supported>` in the
configuration reference.

**Workaround:** none yet; the planned footer work in
[ulwazi#196](https://github.com/canonical/ulwazi/issues/196) is expected to
activate `display_contributors`.

## PDF builds lose the Canonical branding, or fail with an extension-order warning

**Symptom:** with `sphinx_modern_pdf_style` enabled, the build warns:

```text
List "ulwazi" before "sphinx_modern_pdf_style" in extensions, otherwise the
Canonical PDF branding defaults are ignored.
```

and the generated PDF is unbranded (no Canonical logo or footer). With
`fail_on_warning = true` (the Sphinx Stack default), the build fails
outright.

**Cause:** Sphinx fires `config-inited` handlers in extension-registration
order, and `sphinx_modern_pdf_style` reads the `modern_pdf_options` defaults
that Ulwazi injects in its own handler. If `"sphinx_modern_pdf_style"`
appears before `"ulwazi"` in `extensions`, Ulwazi's defaults arrive too late.

**Workaround:** keep the required order in `conf.py`:

```python
extensions = [
    "ulwazi",                 # must come first
    "sphinx_modern_pdf_style",
    # ... other extensions
]
```

## Edit/view icons on generated pages fabricate dead links

**Symptom:** the edit and view icons on generated pages such as `genindex`
link to a nonexistent source file (for example `genindex.rst`).

**Cause:** generated pages have no source file. Ulwazi builds their
edit/view links from `default_source_extension` (default `".rst"`), which
cannot produce a working link for any project.

**Workaround:** none per-page yet. Setting `default_source_extension` to
`".md"` only makes the fabricated URL look plausible for MyST projects; it
still does not exist. To hide the edit/view icons (and the feedback button)
on all pages, set `feedback` to `False` in `html_context`.

## Analytics: the GTM container is not yours

**Symptom:** after migrating, page views show up under Canonical's default
GTM container instead of the project's own.

**Cause:** Ulwazi always includes a Google Tag Manager snippet, using
`html_context["tag_id"]` (default `GTM-N384JMX2`). Projects that injected
their own GTM via a legacy `header.html` override lose it silently (see
above), and the default container takes over.

**Workaround:** set your container ID in `conf.py`:

```python
html_context = {
    "tag_id": "GTM-XXXXXXX",
}
```

## MyST linkify or substitutions stopped working

**Symptom:** bare URLs are no longer auto-linked, or `{{ key }}`
substitutions no longer resolve, after migrating.

**Cause:** the previous stack set the MyST defaults via
canonical-sphinx. Ulwazi restores them (`substitution`, `deflist`, `linkify`)
only when `"myst_parser"` is in `extensions` **and**
`myst_enable_extensions` is unset in `conf.py` and on the command line. An
explicit setting (including an explicitly empty one) always wins and is not
merged.

**Workaround:** check that `"myst_parser"` is listed in `extensions`, and
that `myst_enable_extensions` is either unset (to get the defaults) or
explicitly includes what you need:

```python
myst_enable_extensions = ["substitution", "deflist", "linkify"]
```

The `linkify` extension needs the `linkify-it-py` package, which a normal
Ulwazi installation supplies as a direct dependency.

## 404 page links are broken or missing

**Symptom:** the 404 page renders, but its links are relative and break, or
the page does not render at all.

**Cause:** Ulwazi bundles `sphinx-notfound-page` and activates it
automatically, computing the URL prefix from the Read the Docs canonical URL
and the `slug` config value. Explicit `notfound_urls_prefix` and
`notfound_template` settings take precedence over the theme defaults, and
`notfound_enabled = False` opts out entirely.

**Workaround:** check that `slug` matches the path segment your docs are
served under (for example `"ulwazi"` for `documentation.ubuntu.com/ulwazi/`),
and that no explicit `notfound_*` settings from the previous stack override
the defaults. See the [configuration reference](configuration.md) for the
exact precedence rules.