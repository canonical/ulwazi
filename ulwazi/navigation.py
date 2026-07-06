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
from typing import cast

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
        cast(AttributeValueList, last_element_with_current["class"]).extend(
            ["current-page", 'aria-current="page"']
        )

    return str(soup)
