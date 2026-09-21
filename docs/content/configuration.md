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

For a fully worked example with explanatory comments, see
[`docs/default-conf.py`](https://github.com/canonical/ulwazi/blob/main/docs/default-conf.py)
in the repository -- it's the "simple way" starter template most projects
copy from.

## Top-level `conf.py` values

These are set directly in `conf.py`.

| Setting              | Default if unset       | Purpose                                                                                                                                                                        |
| -------------------- | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `localtoc_max_depth` | `-1` (unlimited depth) | Limits how many nested heading levels show in the page's local table of contents. Set to a positive integer (e.g. `3`) to truncate at that depth, or `-1` to show every level. |

## `html_context` values with a built-in default

Set these inside the `html_context` dictionary in `conf.py`, for example:

```python
html_context = {
    "repo_branch": "main",
    "repo_folder": "docs",
}
```

If you don't set them, Ulwazi uses the defaults below.

| Setting                    | Default if unset                 | Purpose                                                                                                                                                                                                                                                      |
| -------------------------- | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `repo_branch`              | `"main"`                         | Branch containing the doc source, used to build "edit this page" / "view source" links.                                                                                                                                                                      |
| `repo_folder`              | `"docs"`                         | Folder containing the doc source, used to build "edit this page" / "view source" links.                                                                                                                                                                      |
| `default_source_extension` | `".rst"`                         | Source file extension used to build "edit this page" / "view source" links, and as a fallback on pages (like `genindex`) that don't have a source suffix of their own. Set to `".md"` if your docs are written in MyST Markdown instead of reStructuredText. |
| `discourse`                | `"https://discourse.ubuntu.com"` | Base URL for the Discourse link shown in the header's community-links menu (only shown if this is set to a non-empty value).                                                                                                                                 |
| `product_tag`              | `"_static/tag.png"`              | Reserved for a product tag/logo image path. **Not currently read by any Ulwazi template** -- setting it has no visible effect yet.                                                                                                                           |
| `github_issues`            | `"enabled"`                      | Reserved for toggling the GitHub issues integration. **Not currently read by any Ulwazi template** -- setting it has no visible effect yet.                                                                                                                  |
| `sequential_nav`           | `"none"`                         | Reserved for controlling previous/next page navigation (documented values: `none`, `prev`, `next`, `both`). **Not currently read by any Ulwazi template** -- setting it has no visible effect yet.                                                           |
| `display_contributors`     | `True`                           | Reserved for toggling a contributors list (`True`/`False`). **Not currently read by any Ulwazi template** -- setting it has no visible effect yet.                                                                                                           |
| `path`                     | `"/docs"`                        | Reserved/legacy value. **Not currently read by any Ulwazi template** -- setting it has no visible effect yet.                                                                                                                                                |

## `html_context` values with no built-in default

These have no fallback value. Most are simply optional, and, if unset, the
feature they control doesn't render, and nothing breaks. A few are used without
setting a value, so an incomplete setup can produce a broken link.

| Setting                                 | If unset                                                                                                                                                               | Purpose                                                                                                                                    |
| --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `feedback`                              | Feedback/edit/view icons don't render.                                                                                                                                 | Set to `True` (or leave unset/`False`) to show or hide the feedback button and the "edit this page" / "view source" icons.                 |
| `github_url`                            | If `feedback` is `True` but `github_url` is unset, the feedback button still renders with a broken/incomplete link (`href="/issues/new?..."` with no host).            | Documentation repository URL, used for the feedback button and to build edit/view links. Required for `feedback` to work correctly.        |
| `default_edit_url` / `default_view_url` | Used as-is when `github_url` or the current page name isn't available (e.g. on `genindex`). If unset in that situation, the edit/view icons render with an empty link. | Fallback "edit this page" / "view source" URLs for pages that can't build one from `github_url` + page name.                               |
| `mattermost`                            | Link doesn't render.                                                                                                                                                   | Adds a Mattermost link to the header's community-links menu.                                                                               |
| `matrix`                                | Link doesn't render.                                                                                                                                                   | Adds a Matrix link to the header's community-links menu.                                                                                   |
| `product_page`                          | If unset, the project link in the header renders as `href="https://"`.                                                                                                 | Product website hostname shown in the header navigation, next to the project name.                                                         |
| `add_product_menu`                      | Product menu doesn't render.                                                                                                                                           | Set to `True` (or leave unset/`False`) to include or hide Canonical's generated product menu at the top of every page.                     |
| `footer`                                | Footer product/license/custom-entries section doesn't render.                                                                                                          | Dictionary controlling what appears in the page footer; see sub-keys below.                                                                |
| `footer.product`                        | Product name isn't shown in the footer.                                                                                                                                | Set to `True` (or leave unset/`False`) to show or hide the product name as the footer's first entry.                                       |
| `footer.license`                        | License isn't shown in the footer.                                                                                                                                     | Set to `True` (or leave unset/`False`) to show or hide license info as the footer's second entry (requires `license.name` to also be set). |
| `footer.entries`                        | No custom footer entries.                                                                                                                                              | A list of raw HTML snippets appended to the footer.                                                                                        |
| `license`                               | No license shown (even if `footer.license` is `True`).                                                                                                                 | Dict with a `name` (e.g. an SPDX identifier like `"LGPL-3.0-only"`) and optional `url`, shown in the footer.                               |
| `logo_link_URL`                         | If unset, the header logo links to an empty href.                                                                                                                      | Destination URL for the logo in the header navigation.                                                                                     |
| `logo_img_URL`                          | If unset, the header logo `<img>` has an empty `src`.                                                                                                                  | Image URL for the logo in the header navigation.                                                                                           |
| `logo_title`                            | If unset, the text label next to the header logo is empty.                                                                                                             | Text label shown beside the logo in the header navigation.                                                                                 |

## Deprecated aliases

These older setting names (from the previous, Furo-based `canonical-sphinx`
theme) are still honoured for backwards compatibility. If you set an old
name without also setting its replacement, Ulwazi copies the value across
and logs a deprecation warning at build time:

| Deprecated name  | Use instead   |
| ---------------- | ------------- |
| `github_version` | `repo_branch` |
| `github_folder`  | `repo_folder` |

If both the old and new names are set, the new name wins and no warning is
shown.
