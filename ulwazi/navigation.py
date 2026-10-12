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

"""Generate the navigation tree from the Sphinx toctree function."""

import functools
from typing import Any, cast
from urllib.parse import urlsplit

from bs4 import BeautifulSoup, Tag
from bs4.element import AttributeValueList, PageElement
from sphinx.util import logging as sphinx_logging

logger = sphinx_logging.getLogger(__name__)


def _strip_code_tags_from_element(element: Tag) -> None:
    """Remove code-related tags from an element, keeping only their text content."""
    for tag_name in ["code", "pre", "kbd", "samp"]:
        for tag in element.find_all(tag_name):
            tag.unwrap()

    # Also remove span tags with code-related classes
    for span in element.find_all(
        "span", class_=["pre", "docutils", "literal", "notranslate"]
    ):
        span.unwrap()


def _get_navigation_expand_image(soup: BeautifulSoup) -> Tag:
    icon_down = soup.new_tag("i", attrs={"class": "p-icon--chevron-down"})
    icon_up = soup.new_tag("i", attrs={"class": "p-icon--chevron-up"})
    container = soup.new_tag("span")
    container.append(icon_down)
    container.append(icon_up)
    return container


def _mark_current_link(element: Tag) -> None:
    """Mark the current page link the way Vanilla Framework expects.

    Adds the `is-active` class and the `aria-current="page"` attribute to
    the element's first <a>. Vanilla's CSS uses these to draw the active
    background and the left highlight bar.
    """
    current_link = element.find("a")
    if current_link is None:
        return
    link_classes = (
        cast(AttributeValueList, current_link.get("class"))
        if current_link.get("class") is not None
        else AttributeValueList()
    )
    link_classes.append("is-active")
    current_link["class"] = link_classes
    current_link["aria-current"] = "page"


@functools.cache
def get_navigation_tree(toctree_html: str) -> str:
    """Modify the given navigation tree, with furo-specific elements.

    Adds a checkbox + corresponding label to <li>s that contain a <ul> tag, to enable
    the I-spent-too-much-time-making-this-CSS-only collapsing sidebar tree.
    """
    if not toctree_html:
        return toctree_html

    soup = BeautifulSoup(toctree_html, "html.parser")

    # We add a proper style for each <ul> in the globaltoc
    for element in soup.find_all("ul", recursive=True):
        element["class"] = "p-side-navigation__list"

    # We add a proper style for each <li> in the globaltoc
    for element in soup.find_all("li", recursive=True):
        cast(AttributeValueList, element["class"]).append("p-side-navigation__item")

    # We add a proper style and strip code-related tags for each <a> in the globaltoc
    for element in soup.find_all("a", recursive=True):
        cast(AttributeValueList, element["class"]).append("p-side-navigation__link")
        _strip_code_tags_from_element(element)

    toctree_checkbox_count = 0
    last_element_with_current = None

    for element in soup.find_all("li", recursive=True):
        classes = (
            cast(AttributeValueList, element.get("class"))
            if element.get("class") is not None
            else AttributeValueList()
        )
        last_element_with_current = (
            element if "current" in classes else last_element_with_current
        )

        if bool(element.find("ul")):
            classes.append("has-children")
            element["class"] = classes

            toctree_checkbox_count += 1
            checkbox_name = f"toctree-checkbox-{toctree_checkbox_count}"

            checkbox = soup.new_tag(
                "input",
                attrs={
                    "type": "checkbox",
                    "class": "toctree-checkbox",
                    "id": checkbox_name,
                    "name": checkbox_name,
                    "role": "switch",
                },
            )
            checkbox.attrs.update({"checked": ""} if "current" in classes else {})

            a_item: Tag | None = element.find("a")

            label = soup.new_tag("label")
            label.attrs["for"] = checkbox_name
            label.append(_get_navigation_expand_image(soup))

            # Create nav-item div and append a, label, checkbox
            nav_item_div = soup.new_tag(
                "div", attrs={"class": "nav-item", "data-checkbox": checkbox_name}
            )
            nav_item_div.append(cast(PageElement, a_item))
            nav_item_div.append(checkbox)  # <-- checkbox before label
            nav_item_div.append(label)

            # Remove a_item, label, checkbox from their previous positions
            element.contents[:] = [
                tag for tag in element.contents if tag not in (a_item, label, checkbox)
            ]
            element.insert(0, nav_item_div)

            # Hide children unless this li is "current"
            children_ul = element.find("ul")
            if children_ul and "current" not in classes:
                for child_li in children_ul.find_all("li", recursive=False):
                    child_li_classes = (
                        cast(AttributeValueList, child_li.get("class"))
                        if child_li.get("class") is not None
                        else AttributeValueList()
                    )
                    child_li_classes.append("hidden")
                    child_li["class"] = child_li_classes
        else:
            # For leaf li, wrap the <a> in .nav-item
            a_item = element.find("a")
            if a_item:
                nav_item_div = soup.new_tag("div", attrs={"class": "nav-item"})
                nav_item_div.append(a_item)
                if a_item in element.contents:
                    element.contents.remove(a_item)
                element.insert(0, nav_item_div)

    if last_element_with_current is not None:
        cast(AttributeValueList, last_element_with_current["class"]).append(
            "current-page"
        )
        _mark_current_link(last_element_with_current)

    return str(soup)


def validate_help_links(help_links: Any) -> dict[str, Any] | None:  # noqa: ANN401, PLR0911
    """Normalise the conf.py ``html_context["help_links"]`` value.

    ``None``, ``False``, or an empty mapping mean the block is off. A
    configured value must be a mapping with a non-empty string ``title`` and
    a non-empty list of ``links``; each link needs non-empty string ``text``
    and an absolute ``http(s)`` URL. Any malformed value is rejected as a
    whole (never partially rendered) with a specific warning naming the
    offending key or index.

    :param help_links: The raw ``html_context`` value from conf.py

    :returns: A fresh normalised ``{"title": str, "links": [...]}`` mapping,
        or ``None`` when the block is off or the value is invalid
    """
    if not help_links or help_links is True:
        return None

    if not isinstance(help_links, dict):
        _warn_help_links(f"expected a mapping, got {type(help_links).__name__}")
        return None

    help_links_typed = cast("dict[str, Any]", help_links)
    title = help_links_typed.get("title")
    if not isinstance(title, str) or not title.strip():
        _warn_help_links("'title' must be a non-empty string")
        return None

    raw_links = help_links_typed.get("links")
    if not isinstance(raw_links, list) or not raw_links:
        _warn_help_links("'links' must be a non-empty list")
        return None

    links = cast("list[Any]", raw_links)  # type: ignore[redundant-cast]
    normalised_links: list[dict[str, str]] = []
    for index, link in enumerate(links):
        if not isinstance(link, dict):
            _warn_help_links(f"links[{index}] must be a mapping")
            return None
        link_typed = cast("dict[str, Any]", link)
        text = link_typed.get("text")
        if not isinstance(text, str) or not text.strip():
            _warn_help_links(f"links[{index}]['text'] must be a non-empty string")
            return None
        url = link_typed.get("url")
        if not isinstance(url, str) or not url.strip():
            _warn_help_links(f"links[{index}]['url'] must be a non-empty string")
            return None
        if not _is_safe_url(url):
            _warn_help_links(
                f"links[{index}]['url'] must be an absolute http(s) URL, got {url!r}"
            )
            return None
        normalised_links.append({"text": text, "url": url})

    return {"title": title, "links": normalised_links}


def _is_safe_url(url: str) -> bool:
    """Accept only absolute http/https URLs with a hostname."""
    parts = urlsplit(url.strip())
    return parts.scheme in ("http", "https") and bool(parts.netloc)


def _warn_help_links(message: str) -> None:
    """Emit one actionable build warning for an invalid help_links value."""
    logger.warning(
        f"html_context['help_links'] is invalid and will be ignored: {message}. "
        "See the 'Get help links' section of the Ulwazi configuration docs "
        "for the expected shape.",
    )


def add_help_links(navigation_html: str, help_links: dict[str, Any] | None) -> str:
    """Append the conf.py-configured "Get help" links after the navigation tree.

    Built directly here, rather than as toctree entries, so the links keep their
    own p-link--soft styling instead of picking up the p-side-navigation__link
    styling get_navigation_tree() gives every real toctree entry above.
    """
    if not help_links:
        return navigation_html

    soup = BeautifulSoup(navigation_html, "html.parser")

    container = soup.new_tag("div", attrs={"class": "p-help-links"})

    # Mirror the markup Sphinx emits for a toctree :caption: so the heading picks
    # up the theme's own .caption styling instead of restating it here.
    heading = soup.new_tag("p", attrs={"class": "caption", "role": "heading"})
    icon = soup.new_tag(
        "i", attrs={"class": "p-icon--help p-help-links__icon", "aria-hidden": "true"}
    )
    heading.append(icon)
    caption_text = soup.new_tag("span", attrs={"class": "caption-text"})
    caption_text.string = help_links["title"]
    heading.append(caption_text)
    container.append(heading)

    link_list = soup.new_tag("ul", attrs={"class": "p-help-links__list"})
    for link in help_links["links"]:
        item = soup.new_tag("li", attrs={"class": "p-help-links__item"})
        anchor = soup.new_tag(
            "a",
            attrs={
                "class": "p-help-links__link",
                "href": link["url"],
            },
        )
        anchor.string = link["text"]
        item.append(anchor)
        link_list.append(item)
    container.append(link_list)

    soup.append(container)

    return str(soup)
