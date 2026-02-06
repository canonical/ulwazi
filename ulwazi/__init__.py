import importlib.util
from os import path
from pathlib import Path
from typing import Any, Dict

import sphinx.application
from bs4 import BeautifulSoup

from .navigation import get_navigation_tree
from .tabs import convert_tabs

THEME_PATH = (Path(__file__).parent / "theme" / "ulwazi").resolve()

# See http://www.sphinx-doc.org/en/stable/theming.html#distribute-your-theme-as-a-python-package
def setup(app):
    app.add_html_theme('ulwazi', str(THEME_PATH))

    app.add_config_value("localtoc_max_depth", None, "html")

    app.connect(  # pyright: ignore [reportUnknownMemberType]
        "config-inited",
        config_inited,
    )
    app.connect("html-page-context", _html_page_context)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

def config_inited(app, config):  # noqa: ANN401
    """Read user-provided values and setup defaults."""

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
        # "js/scripts.js",
        "js/header-nav.js",
        "js/dropdown.js",
        # "js/main.js"
        "js/product_menu.js",
        "js/vanilla-tabs.js",
        "js/nav-toggle.js",
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

def _compute_navigation_tree(context: Dict[str, Any]) -> str:
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

    HEADING_STYLES = {
        "h1": "p-heading--1",
        "h2": "p-heading--2",
        "h3": "p-heading--3",
        "h4": "p-heading--4",
        "h5": "p-heading--5",
        "h6": "p-heading--6",
    }

    soup = BeautifulSoup(body_html, "html.parser")

    for tag_name, class_name in HEADING_STYLES.items():
        for tag in soup.find_all(tag_name):
            existing_classes = tag.get("class", [])
            if class_name not in existing_classes:
                existing_classes.append(class_name)
            tag["class"] = existing_classes

    return str(soup)

def apply_list_classes(body_html: str) -> str:
    """Add custom CSS classes to list items in the generated body HTML."""
    if not body_html:
        return body_html

    LIST_STYLES = {
        "ul": "p-list--unordered",
        "ol": "p-list--ordered",
        "li": "p-list__item",
        "ul.simple": "p-list--unordered p-list--simple",
        "ol.simple": "p-list--ordered p-list--simple",

    }

    soup = BeautifulSoup(body_html, "html.parser")
    for tag_name, class_name in LIST_STYLES.items():
        for tag in soup.find_all(tag_name):
            existing_classes = tag.get("class", [])
            if class_name not in existing_classes:
                existing_classes.append(class_name)
            tag["class"] = existing_classes

    return str(soup)

def apply_admonition_classes(body_html:str) -> str:
    """Convert admonition classes to notifications in the generated body HTML"""
    if not body_html:
        return body_html

    soup = BeautifulSoup(body_html, "html.parser")

    admonitions = soup.find_all(class_="admonition")
    generic = soup.find_all(class_="admonition-generic-admonition")

    for admonition in admonitions:
        print("Full admonition !!")
        print(admonition)
        child_tags = admonition.find_all(recursive=False)
        div_tag = soup.new_tag('div')
        title = 0
        message = soup.new_tag("div",attrs={"class":"p-notification__message"})
        div_id = admonition.get('id')
        for child in child_tags:
            if child.get("class") == ["admonition-title"]:
                match child.text:
                        case 'Attention':
                            div_tag = soup.new_tag("div", attrs={"class":"p-notification--caution","id":div_id})
                            title = soup.new_tag("h5",attrs={"class":"p-notification__title"})
                            title.string = child.string
                        case 'Caution':
                            div_tag = soup.new_tag("div", attrs={"class":"p-notification--caution","id":div_id})
                            title = soup.new_tag("h5",attrs={"class":"p-notification__title"})
                            title.string = child.string
                        case 'Danger':
                            div_tag = soup.new_tag("div", attrs={"class":"p-notification--caution","id":div_id})
                            title = soup.new_tag("h5",attrs={"class":"p-notification__title"})
                            title.string = child.string
                        case 'Error':
                            div_tag = soup.new_tag("div", attrs={"class":"p-notification--negative","id":div_id})
                            title = soup.new_tag("h5",attrs={"class":"p-notification__title"})
                            title.string = child.string
                        case 'Hint':
                            div_tag = soup.new_tag("div", attrs={"class":"p-notification--positive","id":div_id})
                            title = soup.new_tag("h5",attrs={"class":"p-notification__title"})
                            title.string = child.string
                        case 'Important':
                            div_tag = soup.new_tag("div", attrs={"class":"p-notification--information","id":div_id})
                            title = soup.new_tag("h5",attrs={"class":"p-notification__title"})
                            title.string = child.string
                        case 'Note':
                            div_tag = soup.new_tag("div", attrs={"class":"p-notification--information","id":div_id})
                            title = soup.new_tag("h5",attrs={"class":"p-notification__title"})
                            title.string = child.string
                        case 'Tip':
                            div_tag = soup.new_tag("div", attrs={"class":"p-notification--positive","id":div_id})
                            title = soup.new_tag("h5",attrs={"class":"p-notification__title"})
                            title.string = child.string
                        case 'Warning':
                            div_tag = soup.new_tag("div", attrs={"class":"p-notification--caution","id":div_id})
                            title = soup.new_tag("h5",attrs={"class":"p-notification__title"})
                            title.string = child.string
                        case _:
                            div_tag = soup.new_tag("div", attrs={"class":"p-notification--information","id":div_id})
                            title = soup.new_tag("h5",attrs={"class":"p-notification__title"})
                            title.string = child.string

            else:
                message.append(child)
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
        child_text = []
        for child in child_tags:
            child_text.append(child.string)
            child.decompose()

        code.string = " ".join(child_text)
        if "class" in code.attrs:
            del code["class"]

    return str(soup)

def modify_local_toc(toc:str) -> str:
    """Modify localtoc to apply Vanilla Framework styles"""
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
        li["class"] = ["p-table-of-contents__item"]
        a = li.find("a", recursive=False)
        if a:
            a["class"] = ["p-table-of-contents__link"]
    
    # Add Back to top button at the end
    back_to_top = BeautifulSoup(
                    '<div class="p-top"><a href="#" class="p-top__link">Back to top</a></div>',
                    "html.parser"
                    )
    toc_html.append(back_to_top)

    return str(toc_html)

def truncate_local_toc(toc: str, max_depth: int = None) -> str:
    """Limit the number of nested levels if localtoc_max_depth is set in conf.py."""
    if not toc:
        return toc

    toc_html = BeautifulSoup(toc, "html.parser")

    if max_depth is not None:
        def trim_ul(ul, depth=1):
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

def _html_page_context(
    app: sphinx.application.Sphinx,
    pagename: str,
    templatename: str,
    context: Dict[str, Any],
    doctree: Any,
) -> None:
    # Values computed from page-level context.
    context["expandable_navigation_tree"] = _compute_navigation_tree(context)

    if "toc" in context:
        context["toc"] = modify_local_toc(context["toc"])
        context["toc"] = truncate_local_toc(
            context["toc"],
            getattr(app.config, "localtoc_max_depth", None)
        )
    
    # Modify the body of the content
    if "body" in context:
        context["body"] = apply_heading_classes(context["body"])
        context["body"] = apply_list_classes(context["body"])
        context["body"] = apply_admonition_classes(context["body"])
        context["body"] = modify_inline_code(context["body"])
        context["body"] = convert_tabs(context["body"])
