# Use Ulwazi in your documentation

This guide explains how to migrate an existing Sphinx documentation set to use the Ulwazi theme.
It assumes your project is based on the [Canonical Sphinx starter pack](https://github.com/canonical/sphinx-docs-starter-pack).

For a real-world example of this migration, see the [Charmed Apache Kafka documentation PR](https://github.com/canonical/kafka-operator/pull/444/files).

## Prerequisites

- An existing Sphinx documentation set
- Python 3.8 or later
- A `requirements.txt` file for your docs dependencies
- A `conf.py` Sphinx configuration file

## 1. Update `requirements.txt`

Replace `canonical-sphinx[full]` with the individual packages that your documentation and Ulwazi require.
Your `requirements.txt` should include at minimum:

```text
sphinx
build
sphinx-autobuild
canonical-sphinx-config @ git+https://github.com/Canonical/canonical-sphinx-config.git@main
myst-parser~=4.0
sphinx-basic-ng
sphinxcontrib-jquery
beautifulsoup4
packaging
sphinxcontrib-svg2pdfconverter[CairoSVG]
sphinx-last-updated-by-git
sphinx-sitemap
ulwazi
```

The key addition is the last line: `ulwazi`. This installs the theme from PyPI.

## 2. Update `conf.py`

This is the most significant part of the migration. Follow the steps below.

### Set the theme

Add or update the `html_theme` setting:

```python
html_theme = "ulwazi"
```

### Remove the `canonical_sphinx` extension

In the `extensions` list, replace `"canonical_sphinx"` with the individual extensions that Ulwazi
and its companion packages need:

```python
extensions = [
    "sphinx_terminal",
    "sphinxcontrib.cairosvgconverter",
    "sphinx_last_updated_by_git",
    "sphinx.ext.intersphinx",
    "sphinx_sitemap",
    "ulwazi",
    "canonical_sphinx_config",
    "myst_parser",
    "sphinxcontrib.jquery",
]
```

Feel free to add any other extensions that your documentation might need.
Sometimes, the best way to figure out what they are is to build the docs and
see the error message for something missing.

### Extract top-level variables for `html_context`

Before the `html_context` dictionary, add three new top-level variables.
These are referenced inside `html_context` and make it easier for users to configure
the most commonly changed values in one place.

Add the following block immediately before `html_context = {`:

```python
# TODO: Adjust to point to the repository where your documentation source files
# are stored.

github_repo = "https://github.com/your-org/your-repo"

# TODO: Select the default syntax for docs source files.
# This is for a fallback view/edit source code buttons.

default_source_extension = ".md"

# TODO: Change to your product website URL,
#       dropping the 'https://' prefix, e.g. 'ubuntu.com/lxd'.
#       If there is no such website - set to '/' or remove the {{ product_page }}
#       link from the page header template.

product_page = "your-product.example.com"
```

Replace the placeholder values with your actual repository URL,
file extension (`.md` or `.rst`), and product page URL.

### Update `html_context`

The `html_context` dictionary needs several additions and updates.
For the full diff of a real migration, see the
[Charmed Apache Kafka PR](https://github.com/canonical/kafka-operator/pull/444/files#diff-85933aa74a2d66c3e4dcdf7a9ad8397f5a7971080d34ef1108296a7c6b69e7e3).

All changes in this section are added inside the `html_context` dictionary:

```{code-block} python
:caption: html_context dictionary

html_context = {

}
```

#### Use the new variables

Replace the hardcoded strings with the variables you defined in step 3.3:

```python
    "product_page": product_page,      # was: "your-product.example.com"
    "github_url": github_repo,         # was: "https://github.com/your-org/your-repo"
    "license": {
        "name": "Apache-2.0",          # TODO: set your license
        "url": github_repo + "/blob/main/LICENSE",
    },
```

#### Add `project` and `author` inheritance

Update these entries so the theme can reuse the existing `project` and `author` values already defined in `conf.py`.

```python
    "project": project,
    "author": author,
```

#### Add feedback, source extension, and default URL entries

Adjust the feedback and source code parameters:

```python
    "feedback": True,
    "github_issues": "enabled",
    "default_source_extension": default_source_extension,
    "default_edit_url": github_repo + "/edit/main/docs/index" + default_source_extension,
    "default_view_url": github_repo + "/blob/main/docs/index" + default_source_extension,
```

`default_edit_url` and `default_view_url` serve as fallback URLs for the view/edit source buttons on pages that do not have a specific source file path set.

#### Add navigation menu entries

Add the horizontal navigation menu configuration:

```python
    # Horizontal Nav Menu
    "company": "Canonical",
    # "link1_URL": "https://example.com/",
    # "link1_name": "First optional link",
    # "link2_URL": "https://example.com/",
    # "link2_name": "Second optional link",
```

Uncomment and fill in `link1` and `link2` if you want links in the top navigation bar.

#### Add product menu and logo entries

Add the product menu (uncomment if you want the top thin line product menu) and main logo:

```python
    # Canonical Product menu
    # Uncomment if you need a product menu added on the top of every page
    # "add_product_menu": True,

    "logo_link_URL": "https://documentation.ubuntu.com",
    "logo_img_URL": "https://assets.ubuntu.com/v1/82818827-CoF_white.svg",
    "logo_title": "Canonical",
```

#### Add footer configuration

Add footer parameters:

```python
    # TODO: Customize the footer.
    "footer": {
        # Whether to add the product name as the first entry.
        "product": True,
        # Whether to add the license as the second entry.
        "license": True,
        # List your footer entries. Accepts HTML tags.
        "entries": [
            '<a class="js-revoke-cookie-manager" href="#tracker-settings">Manage your tracker settings</a>',
        ]
    }
```

### Add syntax highlighting settings

```{warning}
This and following parameters are no longer key-values inside `html_context`.
```

Add these settings after the extensions list:

```python
highlight_language = "none"  # default
pygments_style = "autumn"    # see https://pygments.org/styles for more
```

### Add sitemap settings

Add the `sitemap_show_lastmod` setting to your sitemap section:

```python
sitemap_show_lastmod = True
```

### Configure PDF generation

If you need a PDF version of your docs, add the following at the end of `conf.py`:

```python
set_modern_pdf_config = True
```

Don't forget to add an extension for PDF generation, for example: `sphinx_modern_pdf_style`.

### Update the `copyright` format

The Ulwazi theme expects a plain year string rather than the older `CC-BY-SA` format:

```python
copyright = f"{datetime.date.today().year}"
```

The license information is now conveyed through the `"license"` key in `html_context`.

## The default `conf.py`

A reference `conf.py` with all the required configuration and TODO markers is provided
in the Ulwazi repository as
[`default-conf.py`](https://github.com/canonical/ulwazi/blob/main/docs/default-conf.py).
Copy it as the starting point for a new documentation set,
or use it as a checklist when migrating an existing one.

## Migration example

For a real-world example of this migration, see the
[Charmed Apache Kafka documentation PR](https://github.com/canonical/kafka-operator/pull/444/files).
