import datetime
from pathlib import Path

import yaml

# Configuration for the Sphinx documentation builder.
# All configuration specific to your project should be done in this file.
#
# If you're new to Sphinx and don't want any advanced or custom features,
# just go through the items marked 'TODO'.
#
# A complete list of built-in Sphinx configuration values:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
#
# Our starter pack uses the custom Canonical Sphinx extension
# to keep all documentation based on it consistent and on brand:
# https://github.com/canonical/canonical-sphinx


#######################
# Project information #
#######################

# Project name
#
# TODO: Update with the official name of your project or product

project = "The Ulwazi theme sample - some very long phrase here to test the wrapping of the title in the header"
author = "Canonical Ltd."


# Sidebar documentation title; best kept reasonably short
#
# TODO: To include a version number, add it here (hardcoded or automated).
version = "beta"


# TODO: To disable the title, set to an empty string.

html_title = project + " documentation"


# Copyright string; shown at the bottom of the page
#
# Now, the starter pack uses CC-BY-SA as the license
# and the current year as the copyright year.
#
# TODO: If your docs need another license, specify it instead of 'CC-BY-SA'.
#
# TODO: If your documentation is a part of the code repository of your project,
#       it inherits the code license instead; specify it instead of 'CC-BY-SA'.
#
# NOTE: For static works, it is common to provide the first publication year.
#       Another option is to provide both the first year of publication
#       and the current year, especially for docs that frequently change,
#       e.g. 2022–2023 (note the en-dash).
#
#       A way to check a repo's creation date is to get a classic GitHub token
#       with 'repo' permissions; see https://github.com/settings/tokens
#       Next, use 'curl' and 'jq' to extract the date from the API's output:
#
#       curl -H 'Authorization: token <TOKEN>' \
#         -H 'Accept: application/vnd.github.v3.raw' \
#         https://api.github.com/repos/canonical/<REPO> | jq '.created_at'

copyright = f"{datetime.date.today().year}"

# Documentation website URL
#
# TODO: Update with the official URL of your docs or leave empty if unsure.
#
# NOTE: The Open Graph Protocol (OGP) enhances page display in a social graph
#       and is used by social media platforms; see https://ogp.me/

ogp_site_url = "https://canonical-ulwazi.readthedocs-hosted.com/"


# Preview name of the documentation website
#
# TODO: To use a different name for the project in previews, update as needed.

ogp_site_name = project


# Preview image URL
#
# TODO: To customise the preview image, update as needed.

ogp_image = "https://assets.ubuntu.com/v1/253da317-image-document-ubuntudocs.svg"


# Product favicon; shown in bookmarks, browser tabs, etc.

# TODO: To customise the favicon, uncomment and update as needed.

# html_favicon = ".sphinx/_static/favicon.png"


# Dictionary of values to pass into the Sphinx context for all pages:
# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-html_context

html_context = {
    # Product page URL; can be different from product docs URL
    #
    # TODO: Change to your product website URL,
    #       dropping the 'https://' prefix, e.g. 'ubuntu.com/lxd'.
    #
    # TODO: If there's no such website,
    #       remove the {{ product_page }} link from the page header template
    #       (usually .sphinx/_templates/header.html; also, see README.rst).
    "product_page": "pypi.org/project/ulwazi/",
    # Product tag image; the orange part of your logo, shown in the page header
    #
    # TODO: To add a tag image, uncomment and update as needed.
    # 'product_tag': '_static/tag.png',
    #
    # Inherit project name
    "project": project,
    # Inherit the author value
    "author": author,
    # Licensing information
    #
    # TODO: Change your product's license name and a link to its file.
    # For the name, we recommend using the standard shorthand identifier from
    # https://spdx.org/licenses
    # For the URL, link directly to the product's license statement, typically found on
    # the product's home page or in its GitHub project.
    "license": {
        "name": "LGPL-3.0-only",
        "url": "https://github.com/canonical/ulwazi/blob/main/LICENSE",
    },
    # Your Discourse instance URL
    #
    # TODO: Change to your Discourse instance URL or leave empty.
    #
    # NOTE: If set, adding ':discourse: 123' to an .rst file
    #       will add a link to Discourse topic 123 at the bottom of the page.
    "discourse": "https://discourse.ubuntu.com",
    # Your Mattermost channel URL
    #
    # TODO: Change to your Mattermost channel URL or leave empty.
    "mattermost": "https://chat.canonical.com/canonical/channels/documentation",
    # Your Matrix channel URL
    #
    # TODO: Change to your Matrix channel URL or leave empty.
    "matrix": "https://matrix.to/#/#documentation:ubuntu.com",
    # Your documentation GitHub repository URL
    #
    # TODO: Change to your documentation GitHub repository URL or leave empty.
    #
    # NOTE: If set, links for viewing the documentation source files
    #       and creating GitHub issues are added at the bottom of each page.
    "github_url": "https://github.com/canonical/ulwazi",
    # Docs branch in the repo; used in links for viewing the source files
    #
    # TODO: To customise the branch, uncomment and update as needed.
    "repo_default_branch": "main",
    # Docs location in the repo; used in links for viewing the source files
    #
    # TODO: To customise the directory, uncomment and update as needed.
    "repo_folder": "/docs/",
    # TODO: To enable or disable the Previous / Next buttons at the bottom of pages
    # Valid options: none, prev, next, both
    # "sequential_nav": "both",
    # TODO: To enable listing contributors on individual pages, set to True
    "display_contributors": False,
    # Required for feedback button
    "feedback": True,
    "github_issues": "enabled",
    "default_source_extension": ".md",
    "default_edit_url": "https://github.com/canonical/ulwazi/edit/main/docs/index.rst",
    "default_view_url": "https://github.com/canonical/ulwazi/blob/main/docs/index.rst",
    # Horizontal Nav Menu
    "company": "Canonical",
    "link1_URL": "https://snapcraft.io/",
    "link1_name": "First optional link",
    "link2_URL": "https://snapcraft.io/",
    "link2_name": "Second optional link",
    # Canonical Product menu
    # Uncomment if you need a product menu added on the top of every page
    "add_product_menu": True,
    # Main Horizontal menu
    # "is_docs": False, # Purpose unknown
    "logo_link_URL": "/",
    "logo_img_URL": "https://assets.ubuntu.com/v1/82818827-CoF_white.svg",
    "logo_title": "Canonical",
    # TODO: Customize the footer.
    "footer": {
        # Whether to add the product name as the first entry.
        "product": True,
        # Whether to add the license as the second entry.
        "license": True,
        # List your footer entries. Accepts HTML tags.
        "entries": [
            '<a class="js-revoke-cookie-manager" href="#tracker-settings">Manage your tracker settings</a>',
        ],
    },
}

# TODO: To enable the edit button on pages, uncomment and change the link to a
# public repository on GitHub or Launchpad. Any of the following link domains
# are accepted:
# - https://github.com/example-org/example"
# - https://launchpad.net/example
# - https://git.launchpad.net/example
#
# html_theme_options = {
# 'source_edit_link': 'https://github.com/canonical/sphinx-docs-starter-pack',
# }

# Limit the number of levels for Table of contents
localtoc_max_depth = 3

#######################
# Sitemap configuration: https://sphinx-sitemap.readthedocs.io/
#######################

# Base URL of RTD hosted project

html_baseurl = "https://canonical-starter-pack.readthedocs-hosted.com/"

# URL scheme. Add language and version scheme elements.
# When configured with RTD variables, check for RTD environment so manual runs succeed:

#######################
# Template and asset locations
#######################

html_theme = "ulwazi"

myst_enable_extensions = {"colon_fence", "deflist", "substitution", "tasklist"}

extensions = [
    "ulwazi",
    "canonical_sphinx_config",
    "sphinxcontrib.jquery",
    "sphinx_modern_pdf_style",
    "sphinx_terminal",
    "myst_parser",
    "sphinx_tabs.tabs",
    "sphinx_design",
]

# Excludes files or directories from processing

exclude_patterns = ["doc-cheat-sheet*", "_build", "Thumbs.db", ".DS_Store"]

# Syntax highlighting settings

highlight_language = "none"  # default
pygments_style = "autumn"  # see https://pygments.org/styles for more

# Specifies a reST snippet to be appended to each .rst file

rst_epilog = """
"""

rst_prolog = """
.. role:: center
   :class: align-center
.. role:: h2
    :class: hclass2
.. role:: woke-ignore
    :class: woke-ignore
.. role:: vale-ignore
    :class: vale-ignore
"""

# Workaround for https://github.com/canonical/canonical-sphinx/issues/34

if "discourse_prefix" not in html_context and "discourse" in html_context:
    html_context["discourse_prefix"] = f"{html_context['discourse']}/t/"

# Workaround for substitutions.yaml

if Path("./reuse/substitutions.yaml").exists():
    with Path("./reuse/substitutions.yaml").open() as fd:
        myst_substitutions = yaml.safe_load(fd.read())

# PDF
set_modern_pdf_config = True
