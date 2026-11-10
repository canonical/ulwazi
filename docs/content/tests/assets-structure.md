# Asset and structural tests

`tests/test_assets_structure.py` checks rendered assets and theme controls
that Sphinx does not validate. It has three fast offline checks and a slow,
advisory check of external resources. The rendered-site checks use
representative pages, not a whole-site crawl.

## Fast: compiled Vanilla Framework CSS

The `test_vanilla_css_size_and_pruning` case reads the committed
`ulwazi/theme/ulwazi/static/css/vanilla-main.css`, without building the site
or running Sass. It fails if:

- the file is 200,000 bytes or larger (`VANILLA_CSS_BUDGET`): Read the Docs
  truncates larger static files;
- a theme source names a bare Vanilla Framework namespace prefix such as `p-`, which
  would stop the build from pruning that namespace;
- pruning the file again for the current theme sources would change it, so
  the CSS is stale: compiled without `make vanilla-main`, or not rebuilt
  after a template, script or Python hook changed its Vanilla classes;
- the file styles a Vanilla Framework class that no theme source uses.

It doesn't check how the remaining rules render; the browser tests do that.
See {ref}`contribute-compiled-css` for how the build prunes the CSS.

### Removed-classes manifest

The pruner also writes `vanilla-main.css.removed-classes.json`, the list of
Vanilla Framework classes whose styles were removed. The theme reads it to
warn about pages that use those classes (see
{ref}`pruned-vanilla-stylesheet`). The `test_removed_classes_manifest` case
fails if:

- the manifest is missing, not valid JSON, or its `classes` list is unsorted;
- the pruner's vocabulary scan reads the manifest (it would then keep every
  listed class on the next run);
- the manifest differs from what pruning the unpruned CSS removes, so it is
  stale: run `make vanilla-main`;
- it lists a class the shipped CSS still styles.

The staleness comparison needs the Sass output in `node_modules/.cache/ulwazi/`.
The case is skipped, not failed, when that cache is absent (fresh clone or
cleaned `node_modules`); run `make vanilla-main` to enable it.

### Build-time warning and summary

Three cases in `tests/test_config_robustness.py` build tiny generated sites
with raw HTML and check what the theme reports:

| Case | Page content | Expected |
| --- | --- | --- |
| `test_warn_removed_classes` | `p-card` (pruned) and `p-notification--positive` (shipped) | A warning naming the page and `p-card` only, plus the red `Fail!` summary |
| `test_removed_classes_all_clear` | `p-notification--positive` only | No warnings and the green `Pass!` summary |
| `test_warn_removed_classes_opt_out` | `p-card` with `ulwazi_warn_removed_classes = False` | No warning and no summary line |

The assertions match the page name, class names and the `Pass!`/`Fail!`
markers, not the full message text, so rewording the advice doesn't break
them. Run them with
`uv run pytest tests/test_config_robustness.py -k removed_classes`.

## Fast: local assets and structure

- Local linked stylesheets, scripts and images resolve to files relative to
  each generated page. The home page, both syntax cheat sheets, a nested
  code-heading page and search are representative fixtures.
- Core Ulwazi CSS and JS are linked; no page loads the same stylesheet or
  script twice. Search loads its breadcrumb script exactly once, and other
  pages do not load it.
- Side-navigation expanders' checkbox IDs match their labels and theme data
  attributes. Local-TOC fragments target the same page's article.
- Theme tab/control IDs are unique, and notifications do not have empty IDs.

The `test_assets_structure_fast` case checks these contracts without network
access. It also uses mocked responses to check the slow probe's URL discovery,
retry, redirect safety, and warning messages. It does not re-check Sphinx's
source-reference warnings, sitemap/SEO, or extension-specific output such as
structured-TOC navigation.

## Slow: remote availability

The `test_assets_structure_slow` case checks statically referenced external
assets on the same pages: stylesheets, scripts, images (including `srcset`),
Open Graph preview images, and remote fonts and backgrounds referenced by
linked local CSS. It probes each distinct URL once, with bounded timeouts and
at most one retry for transient problems. The current sample assets use
`assets.ubuntu.com`; probes are restricted to reviewed public asset hosts.

If a resource cannot be confirmed available, the case **passes with a pytest
warning** listing the URL, HTTP reason, and the originating source file and
line number when the URL occurs literally in `docs/conf.py`, a sampled MyST
or RST source page, or a checked-in theme stylesheet. A URL emitted by a
template or third-party extension without an identifiable source is reported
as `rendered <page>/index.html:<line>` instead. For example:

```text
tests/test_assets_structure.py: RemoteAssetWarning: Assets and structure [slow]:
  remote availability is advisory; fallback not verified:
  - https://assets.ubuntu.com/v1/example.png (HTTP 404; referenced by docs/content/myst-cheat-sheet.md:439 img[src])
```

Read the warnings summary even when pytest reports `PASSED`: a green result
means the check ran, not that every remote asset was healthy. The slow tier is
scheduled and can also be run manually. Ordinary hyperlinks, resources loaded
only by runtime JavaScript (such as analytics), disabled optional menus, and
resources imported by *remote* stylesheets are outside this check. It is a
snapshot of availability, not uptime monitoring or a rendering test.

No CDN-to-local asset failover is currently configured. System-font choices
and path-based search breadcrumbs are not evidence that a replacement asset
loaded. The slow check therefore reports an unavailable primary with
"fallback not verified"; it never claims a fallback was used. If an asset
failover is added, it needs a separate browser test that blocks the primary
and observes the secondary loading successfully.

## How it is tested

The checks parse a fresh `dirhtml` build with Beautiful Soup. Run the fast
case with `make test`, or the slow advisory with `make test-slow` (which also
runs other slow tests). To run either case alone, use
`uv run --group docs pytest -m 'not slow' tests/test_assets_structure.py` or
`uv run --group docs pytest -m slow tests/test_assets_structure.py`.

The fast assertion collects every broken local resource or control under
`Assets and structure [fast] checks failed`, for example:

```text
Assets and structure [fast] checks failed:
- [content/myst-cheat-sheet] script[src] '../../_static/js/nav-toggle.js': missing /tmp/.../html/_static/js/nav-toggle.js
- [search] breadcrumb script: expected 1, got 2
```

When green, the category recap groups these tests with other asset/structure
checks on one line, with separate fast and slow statuses. Use `-vv` to see
individual test IDs.