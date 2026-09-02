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

from bs4 import BeautifulSoup, Tag
from bs4.element import AttributeValueList, PageElement


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

    # Sphinx renders a toctree's :caption: as a <p class="caption" role="heading">
    # rather than a real heading tag, to avoid clashing with the document's own
    # heading hierarchy. We promote it to a real <h2>, matching the "On this page"
    # heading style, since this is the top-level globaltoc rather than page content.
    for element in soup.find_all("p", class_="caption"):
        element.name = "h2"
        element["class"] = ["p-text--x-small-capitalised", "globaltoc-caption"]
        del element["role"]
        caption_text = element.find("span", class_="caption-text")
        if caption_text:
            caption_text.unwrap()

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


def add_help_links(navigation_html: str, help_links: dict[str, Any] | None) -> str:
    """Append the conf.py-configured "Get help" links after the navigation tree.

    Built directly here, rather than as toctree entries, so the links keep their
    own p-link--soft styling instead of picking up the p-side-navigation__link
    styling get_navigation_tree() gives every real toctree entry above.
    """
    if not help_links:
        return navigation_html

    soup = BeautifulSoup(navigation_html, "html.parser")

    container = soup.new_tag(
        "div", attrs={"class": "p-help-links p-help-links--match-globaltoc"}
    )

    heading = soup.new_tag("h2", attrs={"class": "p-text--x-small-capitalised"})
    icon = soup.new_tag(
        "i", attrs={"class": "p-icon--help p-help-links__icon", "aria-hidden": "true"}
    )
    heading.append(icon)
    heading.append(help_links["title"])
    container.append(heading)

    link_list = soup.new_tag("ul", attrs={"class": "p-list"})
    for link in help_links["links"]:
        item = soup.new_tag("li", attrs={"class": "p-list__item"})
        anchor = soup.new_tag(
            "a",
            attrs={
                "class": "p-link--soft p-text--small u-no-margin--bottom",
                "href": link["url"],
            },
        )
        anchor.string = link["text"]
        item.append(anchor)
        link_list.append(item)
    container.append(link_list)

    aside = soup.new_tag("aside")
    aside.append(container)
    soup.append(aside)

    return str(soup)
