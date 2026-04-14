# This file is part of Ulwazi.
#
# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3, as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranties of MERCHANTABILITY, SATISFACTORY
# QUALITY, or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
# License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

"""Connect the extension to Sphinx and shim some Vanilla styling."""

import importlib.util
from pathlib import Path
from typing import Any, cast

from bs4 import BeautifulSoup, Tag
from bs4.element import AttributeValueList
from docutils import nodes
from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.util.typing import ExtensionMetadata

from ulwazi.navigation import get_navigation_tree
from ulwazi.tabs import convert_tabs

THEME_PATH = (Path(__file__).parent / "theme" / "ulwazi").resolve()

# Uncomment when we add build tooling
# try:
#     from ._version import __version__
# except ImportError:
#     from importlib.metadata import PackageNotFoundError, version

#     try:
#         __version__ = version("ulwazi")
#     except PackageNotFoundError:
#         __version__ = "dev"


def setup(app: Sphinx) -> ExtensionMetadata:
    """Connect the extension's core components to Sphinx.

    :param app: The Sphinx application instance

    :returns: The extension's metadata
    """
    app.add_html_theme("ulwazi", str(Path(__file__).parent / "theme/ulwazi"))
    app.add_config_value("localtoc_max_depth", None, "html")
    app.connect(  # pyright: ignore [reportUnknownMemberType]
        "config-inited",
        config_inited,
    )
    app.connect("html-page-context", _html_page_context)  # pyright: ignore [reportUnknownMemberType]

    return {
        "version": "0.4",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


def config_inited(app: Sphinx, config: Config) -> None:
    """Read user-provided values and set up defaults.

    :param app: The Sphinx application instance
    :param config: The Sphinx build configuration
    """
    html_context = config.html_context

    required_packages = [
        "sphinxcontrib.jquery",
    ]

    for package in required_packages:
        try:
            if importlib.util.find_spec(package) is not None:
                app.setup_extension(package)
            else:
                print(f"{package} not found.\n{package} will not be configured.")
        except ModuleNotFoundError:  # noqa: PERF203
            print(f"{package} not found.\n{package} will not be configured.")

    extra_js = [
        "js/header-nav.js",
        "js/dropdown.js",
        "js/product_menu.js",
        "js/vanilla-tabs.js",
        "js/nav-toggle.js",
        "js/search.js",
        "js/search-breadcrumbs.js",
    ]

    values_and_defaults = [
        ("product_tag", "_static/tag.png"),
        ("github_version", "main"),
        ("github_folder", "docs"),
        ("github_issues", "enabled"),
        ("discourse", "https://discourse.ubuntu.com"),
        ("sequential_nav", "none"),
        ("display_contributors", True),
        ("path", "/docs"),
    ]

    for value, default in values_and_defaults:
        html_context.setdefault(value, default)

    for item in extra_js:
        app.add_js_file(item)


def _compute_navigation_tree(context: dict[str, Any]) -> str:
    # The globaltoc tree by Sphinx
    if "toctree" in context:
        toctree = context["toctree"]
        toctree_html = toctree(
            collapse=False,
            titles_only=True,
            includehidden=True,
        )
    else:
        toctree_html = ""

    return get_navigation_tree(toctree_html)


def apply_heading_classes(body_html: str) -> str:
    """Add custom CSS classes to headings in the generated body HTML."""
    if not body_html:
        return body_html

    heading_classes = {
        "h1": "p-heading--1",
        "h2": "p-heading--2",
        "h3": "p-heading--3",
        "h4": "p-heading--4",
        "h5": "p-heading--5",
        "h6": "p-heading--6",
    }

    soup = BeautifulSoup(body_html, "html.parser")

    for tag_name, class_name in heading_classes.items():
        for tag in soup.find_all(tag_name):
            existing_classes = (
                cast(AttributeValueList, tag.get("class"))
                if tag.get("class") is not None
                else AttributeValueList()
            )
            if class_name not in existing_classes:
                existing_classes.append(class_name)
            tag["class"] = existing_classes

    return str(soup)


def apply_list_classes(body_html: str) -> str:
    """Add custom CSS classes to list items in the generated body HTML."""
    if not body_html:
        return body_html

    list_classes = {
        "ul": "p-list--unordered",
        "ol": "p-list--ordered",
        "li": "p-list__item",
        "ul.simple": "p-list--unordered p-list--simple",
        "ol.simple": "p-list--ordered p-list--simple",
    }

    soup = BeautifulSoup(body_html, "html.parser")
    for tag_name, class_name in list_classes.items():
        for tag in soup.find_all(tag_name):
            existing_classes = (
                cast(AttributeValueList, tag.get("class"))
                if tag.get("class") is not None
                else AttributeValueList()
            )
            if class_name not in existing_classes:
                existing_classes.append(class_name)
            tag["class"] = existing_classes

    return str(soup)


def apply_admonition_classes(body_html: str) -> str:
    """Convert admonition classes to notifications in the generated body HTML."""
    if not body_html:
        return body_html

    soup = BeautifulSoup(body_html, "html.parser")

    admonitions = soup.find_all(class_="admonition")

    admonition_classes = {
        "Attention": "caution",
        "Caution": "caution",
        "Danger": "caution",
        "Error": "negative",
        "Hint": "positive",
        "Important": "information",
        "Note": "information",
        "Tip": "positive",
        "Warning": "caution",
    }

    for admonition in admonitions:
        child_tags = admonition.find_all(recursive=False)
        div_tag = soup.new_tag("div")
        message = soup.new_tag("div", attrs={"class": "p-notification__message"})
        div_id: str = cast(str, admonition.get("id", ""))
        title: Tag | None = None

        for child in child_tags:
            if child.get("class") == ["admonition-title"]:
                # Default to 'information' class notification
                div_tag = soup.new_tag(
                    "div", attrs={"class": "p-notification--information", "id": div_id}
                )
                title = soup.new_tag("h5", attrs={"class": "p-notification__title"})
                title.string = child.string if child.string else ""

                # Apply notification class defined in `admonition_classes'
                if child.text in admonition_classes:
                    div_tag = soup.new_tag(
                        "div",
                        attrs={
                            "class": f"p-notification--{admonition_classes[child.text]}",
                            "id": div_id,
                        },
                    )
                    title = soup.new_tag("h5", attrs={"class": "p-notification__title"})
                    title.string = child.string if child.string is not None else ""
            else:
                message.append(child)

        if title:
            div_tag.append(title)
        div_tag.append(message)
        admonition.replace_with(div_tag)

    return str(soup)


def modify_inline_code(body_html: str) -> str:
    """Modify inline code elements in the HTML."""
    if not body_html:
        return body_html

    soup = BeautifulSoup(body_html, "html.parser")

    for code in soup.find_all("code", class_="docutils literal notranslate"):
        child_tags = code.findChildren()
        child_text: list[str] = []
        for child in child_tags:
            child_text.append(child.string)
            child.decompose()

        code.string = " ".join(child_text)
        if "class" in code.attrs:
            del code["class"]

    return str(soup)


def modify_local_toc(toc: str) -> str:
    """Modify localtoc to apply Vanilla Framework styles."""
    if not toc:
        return toc

    toc_html = BeautifulSoup(toc, "html.parser")

    # Remove a redundant <ul>
    top_ul = toc_html.find("ul")
    if top_ul:
        top_ul.unwrap()

    # Remove the page title <li>
    top_li = toc_html.find("li")
    if top_li:
        top_li.unwrap()

    # Remove the link to the page title <a>
    top_a = toc_html.find("a")
    if top_a:
        top_a.decompose()

    # Remove a redundant margin for headings
    top_ul = toc_html.find("ul")
    if top_ul:
        top_ul.unwrap()

    # Assign classes from Vanilla Framework
    for li in toc_html.find_all("li"):
        li["class"] = "p-table-of-contents__item"
        a = li.find("a", recursive=False)
        if a:
            a["class"] = "p-table-of-contents__link"

    # Add Back to top button at the end
    back_to_top = BeautifulSoup(
        '<div class="p-top"><a href="#" class="p-top__link">Back to top</a></div>',
        "html.parser",
    )
    toc_html.append(back_to_top)

    return str(toc_html)


def truncate_local_toc(toc: str, max_depth: int = -1) -> str:
    """Limit the number of nested levels if localtoc_max_depth is set in conf.py."""
    if not toc:
        return toc

    toc_html = BeautifulSoup(toc, "html.parser")

    if max_depth != -1:

        def trim_ul(ul: Tag, depth: int = 1) -> None:
            if depth >= max_depth:
                # delete all nested <ul> inside <li>
                for li in ul.find_all("li", recursive=False):
                    nested = li.find("ul", recursive=False)
                    if nested:
                        nested.decompose()
            else:
                # recurse into each li's nested ul
                for li in ul.find_all("li", recursive=False):
                    nested = li.find("ul", recursive=False)
                    if nested:
                        trim_ul(nested, depth + 1)

        trim_ul(toc_html, 1)

    return str(toc_html)


def _build_breadcrumb_map(app: Sphinx, context: dict[str, Any]) -> str:
    """Build a mapping of docnames to their navigation breadcrumb paths."""
    import json

    breadcrumb_map = {}

    def process_list_items(items, parent_path=None):
        """Recursively process list items to extract navigation hierarchy."""
        if parent_path is None:
            parent_path = []

        for li in items:
            # Find the link in this list item
            link = li.find("a", class_="reference internal")
            if link:
                href = link.get("href", "")
                title = link.get_text(strip=True)

                # Check if this is a section link (contains #)
                is_section_link = "#" in href

                # Extract docname from href (handle dirhtml format)
                # First remove leading ../
                docname = href
                while docname.startswith("../"):
                    docname = docname[3:]
                # Remove trailing / or .html
                if docname.endswith("/"):
                    docname = docname[:-1]
                if docname.endswith(".html"):
                    docname = docname[:-5]

                # For section links, strip the anchor to get the base page
                if is_section_link and "#" in docname:
                    docname = docname.split("#")[0]

                # Only store breadcrumbs for actual pages (not section links)
                if docname and not is_section_link:
                    # Store the breadcrumb path for this doc (not including itself)
                    breadcrumb_map[docname] = list(parent_path)

                # Check for nested items
                nested_ul = li.find("ul")
                if nested_ul:
                    nested_items = nested_ul.find_all("li", recursive=False)
                    if nested_items:
                        # Only add to path if it's a page link (not a section)
                        if is_section_link:
                            # For section links, continue with the same parent path
                            # (don't add sections to breadcrumb trail)
                            process_list_items(nested_items, parent_path)
                        else:
                            # For page links, add to the path for children
                            new_path = parent_path + [{"title": title, "link": href}]
                            process_list_items(nested_items, new_path)

    # Get the global toctree
    if "toctree" in context:
        try:
            toctree = context["toctree"]
            toctree_html = toctree(
                collapse=False,
                titles_only=False,
                includehidden=True,
                maxdepth=-1,
            )

            if toctree_html:
                soup = BeautifulSoup(toctree_html, "html.parser")
                # Find all top-level list items
                top_level_ul = soup.find("ul")
                if top_level_ul:
                    top_items = top_level_ul.find_all("li", recursive=False)
                    process_list_items(top_items)
        except Exception as e:
            # If toctree generation fails, return empty map
            pass

    return json.dumps(breadcrumb_map)


def _html_page_context(
    app: Sphinx,
    pagename: str,
    _templatename: str,
    context: dict[str, Any],
    _doctree: nodes.document | None,
) -> None:
    # Values computed from page-level context.
    context["expandable_navigation_tree"] = _compute_navigation_tree(context)

    if "toc" in context:
        context["toc"] = modify_local_toc(context["toc"])
        context["toc"] = truncate_local_toc(
            context["toc"], getattr(app.config, "localtoc_max_depth", -1)
        )

    # Build navigation breadcrumb mapping for search
    if pagename == "search":
        context["search_breadcrumb_map"] = _build_breadcrumb_map(app, context)

    # Modify the body of the content
    if "body" in context:
        context["body"] = apply_heading_classes(context["body"])
        context["body"] = apply_list_classes(context["body"])
        context["body"] = apply_admonition_classes(context["body"])
        context["body"] = modify_inline_code(context["body"])
        context["body"] = convert_tabs(context["body"])
