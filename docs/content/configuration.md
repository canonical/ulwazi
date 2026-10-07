# Configuration reference

Ulwazi works with a minimal `conf.py`:

```python
extensions = ["ulwazi"]
html_theme = "ulwazi"
```

Everything else on this page is optional. If you don't set a value, Ulwazi
either falls back to a hard-coded default (so your build still works), or
simply doesn't render the feature that value controls. This page lists
every Ulwazi-specific setting so you know what's available and what
happens if you skip it.

```{note}
For a baseline example with explanatory comments, see
[`docs/default-conf.py`](https://github.com/canonical/ulwazi/blob/main/docs/default-conf.py)
in the repository -- this is easiest way to start using Ulwazi.
```

## Top-level configuration values

These are set directly in `conf.py`.

```{list-table}
:header-rows: 1

*
    - Setting
    - Default if unset
    - Purpose
*
    - `localtoc_max_depth`
    - `3`
    - Limits the local table of contents to H2–H4 on a page with an H1 title. Set to `-1` or `None` to show every heading level.
*
    - `slug`
    - `""`
    - Path segment for the project's hosted documentation, used to prefix links on the bundled 404 page. For example, use `"ulwazi"` for `documentation.ubuntu.com/ulwazi/`.
*
    - `notfound_enabled`
    - `True`
    - Set to `False` to opt out of Ulwazi's automatic `sphinx-notfound-page` activation and 404 defaults. If `notfound.extension` is also explicitly listed, it remains active.
```

Ulwazi also supplies a `404.html` template and chooses the 404 URL prefix from
the Read the Docs canonical URL when available. Explicit `notfound_template`
and `notfound_urls_prefix` settings take precedence. List `"ulwazi"` before
`"sphinx_modern_pdf_style"` in `extensions` to enable Canonical PDF branding;
Ulwazi stages the logo in the LaTeX output directory.

## HTML context

Sphinx makes values in the `html_context` dictionary available to HTML
templates. Define this dictionary in `conf.py`; unlike top-level settings such
as `localtoc_max_depth`, its values are grouped under `html_context`. Ulwazi
uses them for theme elements such as navigation, feedback, and source links.

### With defaults

Set these inside the `html_context` dictionary in `conf.py`, for example:

```python
html_context = {
    "repo_branch": "main",
    "repo_folder": "/docs/",
}
```

If you don't set them, Ulwazi uses the defaults below.

```{list-table}
:header-rows: 1

*
    - Setting
    - Default if unset
    - Purpose
*
    - `repo_branch`
    - `"main"`
    - Branch containing the doc source, used to build "edit this page" / "view source" links.
*
    - `repo_folder`
    - `"/docs/"`
    - Folder containing the doc source, used to build "edit this page" / "view source" links. Include the leading and trailing slashes when setting a custom folder.
*
    - `default_source_extension`
    - `".rst"`
    - Source file extension used to build "edit this page" / "view source" links on generated pages (such as `genindex`) without a source suffix. Set to `".md"` if your docs are written in MyST Markdown instead of reStructuredText.
*
    - `discourse`
    - `"https://discourse.ubuntu.com"`
    - Base URL for the Discourse link shown in the header's community-links menu (only shown if this is set to a non-empty value).
```

### Without defaults

These have no fallback value. Most are simply optional, and, if unset, the
feature they control doesn't render, and nothing breaks. A few are used without
setting a value, so an incomplete setup can produce a broken link.

```{list-table}
:header-rows: 1

*
    - Setting
    - If unset
    - Purpose
*
    - `feedback`
    - Feedback/edit/view icons don't render.
    - Set to `True` (or leave unset/`False`) to show or hide the feedback button and the "edit this page" / "view source" icons.
*
    - `github_url`
    - If `feedback` is `True` but `github_url` is unset, the feedback button still renders with a broken/incomplete link (`href="/issues/new?..."` with no host).
    - Documentation repository URL, used for the feedback button and to build edit/view links. Required for `feedback` to work correctly.
*
    - `default_edit_url` / `default_view_url`
    - Used as-is when `github_url` or the current page name isn't available. If unset in that situation, the edit/view icons render with an empty link.
    - Fallback "edit this page" / "view source" URLs for pages that can't build one from `github_url` + page name.
*
    - `mattermost`
    - Link doesn't render.
    - Adds a Mattermost link to the header's community-links menu.
*
    - `matrix`
    - Link doesn't render.
    - Adds a Matrix link to the header's community-links menu.
*
    - `product_page`
    - If unset, the project link in the header renders as `href="https://"`.
    - Product website hostname shown in the header navigation, next to the project name.
*
    - `add_product_menu`
    - Product menu doesn't render.
    - Set to `True` (or leave unset/`False`) to include or hide Canonical's generated product menu at the top of every page.
*
    - `footer`
    - Footer product/license/custom-entries section doesn't render.
    - Dictionary controlling what appears in the page footer; see sub-keys below.
*
    - `footer.product`
    - Product name isn't shown in the footer.
    - Set to `True` (or leave unset/`False`) to show or hide the product name as the footer's first entry.
*
    - `footer.license`
    - License isn't shown in the footer.
    - Set to `True` (or leave unset/`False`) to show or hide license info as the footer's second entry (requires `license.name` to also be set).
*
    - `footer.entries`
    - No custom footer entries.
    - A list of raw HTML snippets appended to the footer.
*
    - `license`
    - No license shown (even if `footer.license` is `True`).
    - Dict with a `name` (e.g. an SPDX identifier like `"LGPL-3.0-only"`) and optional `url`, shown in the footer.
*
    - `logo_link_URL`
    - If unset, the header logo links to an empty href.
    - Destination URL for the logo in the header navigation.
*
    - `logo_img_URL`
    - If unset, the header logo `<img>` has an empty `src`.
    - Image URL for the logo in the header navigation.
*
    - `logo_title`
    - If unset, the text label next to the header logo is empty.
    - Text label shown beside the logo in the header navigation.
```

### Not currently supported

Ulwazi supplies defaults for these `html_context` values, but no Ulwazi
template reads them yet. Setting them has no visible effect on the theme;
the purposes below describe their intended or legacy use.

```{list-table}
:header-rows: 1

*
    - Setting
    - Default if unset
    - Intended purpose
*
    - `product_tag`
    - `"_static/tag.png"`
    - Product tag/logo image path.
*
    - `github_issues`
    - `"enabled"`
    - Toggle the GitHub issues integration.
*
    - `sequential_nav`
    - `"none"`
    - Control previous/next page navigation (documented values: `none`, `prev`, `next`, `both`).
*
    - `display_contributors`
    - `True`
    - Toggle a contributors list (`True`/`False`).
*
    - `path`
    - `"/docs"`
    - Reserved/legacy value.
```

## Deprecated aliases

These older setting names (from the previous, Furo-based `canonical-sphinx`
theme) are still honoured for backwards compatibility. If you set an old
name without also setting its replacement, Ulwazi copies the value across
and logs a deprecation warning at build time:

| Deprecated name  | Use instead   |
| ---------------- | ------------- |
| `github_version` | `repo_branch` |
| `github_folder`  | `repo_folder` |

If both the old and new names are set, the new name takes precedence and no
warning is shown.
