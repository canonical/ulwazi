"""Ulwazi-specific settings from docs/default-conf.py, with non-default values.

Keep this Sphinx project self-contained: unrelated starter-pack extensions,
static paths, and RTD environment variables are not needed for theme tests.
"""

extensions = ["ulwazi"]
html_theme = "ulwazi"
project = "Maximum configuration example"
author = "Example authors"
version = "2.0"

# The documented default is 3; depth 4 includes H5 but not H6 in the local TOC.
localtoc_max_depth = 4

html_context = {
    # Repository settings and community links (based on docs/default-conf.py).
    "repo_branch": "release/2.0",
    "repo_folder": "/guides/",
    "default_source_extension": ".md",
    "discourse": "https://forum.example.com/maximum",
    "feedback": True,
    "github_url": "https://github.com/example/maximum-docs",
    "default_edit_url": "https://github.com/example/maximum-docs/edit/main/README.md",
    "default_view_url": "https://github.com/example/maximum-docs/blob/main/README.md",
    "mattermost": "https://chat.example.com/maximum",
    "matrix": "https://matrix.to/#/#maximum:example.com",
    "product_page": "example.com/maximum",
    "add_product_menu": True,
    "logo_link_URL": "https://example.com/maximum-home",
    "logo_img_URL": "https://example.com/assets/maximum-logo.svg",
    "logo_title": "Maximum docs",
    "license": {
        "name": "CC-BY-4.0",
        "url": "https://example.com/maximum-license",
    },
    "footer": {
        "product": True,
        "license": True,
        "entries": ['<a href="https://example.com/support">Maximum support</a>'],
    },
    # Reserved/legacy values: Ulwazi preserves these, but does not render them.
    "product_tag": "_static/maximum-tag.svg",
    "github_issues": "disabled",
    "sequential_nav": "both",
    "display_contributors": False,
    "path": "/maximum-docs",
}
