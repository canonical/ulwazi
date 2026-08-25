# Extension compatibility tests

The extension compatibility tests verify that the Ulwazi theme works with
every extension that the
[Sphinx Stack](https://documentation.ubuntu.com/sphinx-stack/latest/reference/default-extensions/)
enables by default, plus additional extensions we choose to support.

This implements the "Extension compatibility" test category from the
testing strategy.

All extensions are enabled simultaneously in `docs/conf.py`, and the
sample sections on this very page exercise each of them. The test then
checks the built HTML and build artifacts for each extension's expected
output.

## What is tested

| Extension | Check |
|---|---|
| `notfound.extension` | `404.html` is built with the Ulwazi stylesheet |
| `sphinx_design` | Cards, grid items, and badges render with `sd-*` classes |
| `sphinx_reredirects` | Redirect stub page with a meta refresh is generated |
| `sphinx_rerediraffe` | Redirect stub page is generated from `redirects.txt` |
| `sphinxcontrib.jquery` | jQuery is loaded on the page |
| `sphinxext.opengraph` | Open Graph meta tags are present |
| `sphinx.ext.intersphinx` | External reference resolves to a link |
| `sphinx_config_options` | Config option renders with its fields table |
| `sphinx_contributor_listing` | Build succeeds with the extension active (see known gaps) |
| `sphinx_filtered_toctree` | Filtered toctree renders its entries |
| `sphinx_last_updated_by_git` | Build succeeds with the extension active (see known gaps) |
| `sphinx_llm.txt` | `llms.txt` is generated in the build output |
| `sphinx_related_links` | Build succeeds with the extension active (see known gaps) |
| `sphinx_roles` | Custom roles (`spellexception`, `literalref`) render |
| `sphinx_sitemap` | `sitemap.xml` is generated with page entries |
| `sphinx_structured_toc` | Structured TOC renders as a `nav` with slices |
| `sphinx_terminal` | Terminal block renders with terminal classes |
| `sphinx_ubuntu_images` | Image list renders for the given filters |
| `sphinx_youtube_links` | YouTube link renders with the play icon |
| `sphinxcontrib.cairosvgconverter` | PDF build succeeds *(slow)* |

## What is excluded

`canonical_sphinx` is intentionally **not** tested: it is a Sphinx theme
(the Furo-based Canonical theme) and cannot coexist with Ulwazi. Its
sub-extensions (`notfound.extension`, `sphinx_design`, `sphinx_reredirects`,
`sphinxcontrib.jquery`, `sphinxext.opengraph`) are enabled and tested
individually instead.

`sphinx_tabs.tabs` is also **not** tested: the theme standardises on
`sphinx_design` tab sets (`tab-set` / `tab-item`), which cover the same
use cases. The extension is therefore not enabled in `docs/conf.py`.

## Known gaps

The Ulwazi theme does not yet consume the output of every extension, so
some checks only assert that the build succeeds with the extension
active. These extensions are still enabled and built with — regressions
in the build are caught — but their rendered output is not asserted.
Supporting them in the theme is tracked as follow-up work:

- `sphinx_contributor_listing` exposes a `get_contributors_for_file`
  context function, but no Ulwazi template calls it yet.
- `sphinx_related_links` exposes related-links context functions, but no
  Ulwazi template renders them yet.
- `sphinx_last_updated_by_git` populates the `last_updated` page context
  and (with `git_last_updated_metatags`, on by default) an
  `article:modified_time` meta tag. The meta tag is currently not
  emitted: `canonical_sphinx_config` sets `html_last_updated_fmt` to an
  empty string, which makes the extension's page-context hook return
  early. No Ulwazi template renders `last_updated` either.

## How it's tested

The test parses the HTML that Sphinx already builds under `docs/_build/`
using [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) —
no browser needed, since these checks don't depend on rendered appearance.
Each extension has its own parametrized test case, so the pytest output
shows one line per extension.

```shell
make docs
uv run pytest tests/test_extension_compatibility.py
```

The `sphinxcontrib.cairosvgconverter` check is marked `slow` because it
requires the PDF build; run it with `make test-slow`.

## Sample content

The sections below exercise each extension on this page. They double as
living examples of the extension syntax and as fixtures for the tests.

### Cards, grids, and badges (sphinx_design)

```{card} A card title
A card body with some text.
```

````{grid} 1 1 2 2
:gutter: 2

```{grid-item-card} Grid item 1
Some text in the first grid item.
```

```{grid-item-card} Grid item 2
Some text in the second grid item.
```
````

A badge: {bdg-primary}`some badge`

### Tabs (sphinx_design)

Tab sets from `sphinx_design` (`tab-set` / `tab-item`):

`````{tab-set}

````{tab-item} Tab one
Content of the first tab.
````

````{tab-item} Tab two
Content of the second tab.
````

`````

### Terminal output (sphinx_terminal)

```{terminal}
:user: root
:host: vampyr
:dir: /root

sudo apt update

Hit:1 https://example.com/ubuntu stable InRelease
Reading package lists... Done
```

### YouTube embeds (sphinx_youtube_links)

```{youtube} https://www.youtube.com/watch?v=iMLiK1fX4I0
:title: Ubuntu desktop tour
```

### Configuration options (sphinx_config_options)

```{eval-rst}
.. config:option:: example-option
   :shortdesc: An example configuration option
   :type: string
   :default: ``"default-value"``
   :scope: global

   A longer description of the example option, explaining what it does
   and when to set it.
```

### Filtered toctree (sphinx_filtered_toctree)

The filtered toctree below includes the cheatsheets only when the
`show-cheatsheets` filter is not excluded via `toc_filter_exclude`:

```{eval-rst}
.. filtered-toctree::
   :maxdepth: 1

   MyST cheat sheet <../myst-cheat-sheet>
   RST cheat sheet <../rst-cheat-sheet>
```

### Structured TOC (sphinx_structured_toc)

The structured TOC below groups links into domains and slices with ARIA
labels for accessibility. It is HTML-only output, so it is wrapped in an
`only:: html` directive to keep LaTeX (PDF) builds working:

```{eval-rst}
.. only:: html

    ..  domain:: Theme areas

        ..  slice:: Content

            :doc:`MyST cheat sheet <../myst-cheat-sheet>`
            :doc:`RST cheat sheet <../rst-cheat-sheet>`

        ..  slice:: Meta

            :doc:`Testing strategy <../testing-strategy>`
            :doc:`Contributing <../contribute>`
```

### Related links (sphinx_related_links)

Related links and Discourse topics are declared as page metadata and
rendered by the theme's templates:

```{eval-rst}
.. meta::
   :relatedlinks: https://github.com/canonical/ulwazi
```

### Custom roles (sphinx_roles)

A spelling exception: :spellexception:`PurposelyWrong`.

A literal reference: :literalref:`some literal text`.

### Ubuntu images (sphinx_ubuntu_images)

```{eval-rst}
.. ubuntu-images::
   :releases: noble
   :lts-only:
   :image-types: live-server
   :archs: arm64
   :empty: No matching images found.
```

### Contributor listing (sphinx_contributor_listing)

Contributors are listed automatically from the repository's git history
when `display_contributors` is enabled in `html_context`. The extension
exposes a `get_contributors_for_file` context function that templates
can call; the Ulwazi theme does not consume it yet (known gap).

### Intersphinx (sphinx.ext.intersphinx)

A link to the [Python glossary](inv:python:std:label#glossary), resolved
through intersphinx.

### Last updated by git (sphinx_last_updated_by_git)

The last-updated timestamp for this page is read from git commit metadata
and exposed to the page context.

### Sitemap (sphinx_sitemap)

A `sitemap.xml` file is generated for the whole site; see the build output.

### Open Graph (sphinxext.opengraph)

Open Graph metadata is generated for every page; see the page `<head>`.

### jQuery (sphinxcontrib.jquery)

jQuery is loaded for extensions that require it.

### Redirects (sphinx_reredirects and sphinx_rerediraffe)

Redirect stub pages are generated from the `redirects` dictionary in
`conf.py` (sphinx_reredirects) and the `redirects.txt` file
(sphinx_rerediraffe).

### Not-found page (notfound.extension)

A custom 404 page is rendered with the theme's styling.

### SVG to PDF conversion (sphinxcontrib.cairosvgconverter)

SVG images are converted to PDF during LaTeX builds. This only affects
PDF output; see the PDF build test.

### LLM artifacts (sphinx_llm.txt)

An `llms.txt` file and Markdown artifacts are generated for LLM
consumption; see the build output.
