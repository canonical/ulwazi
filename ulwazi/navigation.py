"""Generate the navigation tree from Sphinx's toctree function's output."""

import functools
import copy

from bs4 import BeautifulSoup, Tag


def _get_navigation_expand_image(soup: BeautifulSoup) -> Tag:
    retval = soup.new_tag("i", attrs={"class": "icon"})

    svg_element = soup.new_tag("svg")
    svg_use_element = soup.new_tag("use", href="#svg-arrow-right")
    svg_element.append(svg_use_element)

    retval.append(svg_element)
    return retval


@functools.lru_cache(maxsize=None)
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
        # classes = element.get("class", [])
        # element["class"] = classes + ["p-side-navigation__list"]
        element["class"] = "p-side-navigation__list"
    
    # We add a proper style for each <li> in the globaltoc
    for element in soup.find_all("li", recursive=True):
        # element["class"] = "p-side-navigation__item"
        element["class"].append("p-side-navigation__item")

    # We add a proper style for each <a> in the globaltoc
    for element in soup.find_all("a", recursive=True):
        element["class"].append("p-side-navigation__link")

    toctree_checkbox_count = 0
    last_element_with_current = None

    for element in soup.find_all("li", recursive=True):
        # We check all "li" elements, to add a "current-page" to the correct li.
        classes = element.get("class", [])
        if "current" in classes:
            last_element_with_current = element

        # Nothing more to do, unless this has "children"
        if not element.find("ul"):
            continue

        # Add a class to indicate that this has children.
        element["class"] = classes + ["has-children"]

        toctree_checkbox_count += 1
        checkbox_name = f"toctree-checkbox-{toctree_checkbox_count}" 
        # We're gonna add a checkbox.
        checkbox = soup.new_tag(
            "input",
            attrs={
                "type": "checkbox",
                "class": ["toctree-checkbox"],
                "id": checkbox_name,
                "name": checkbox_name,
                "role": "switch",
            },
        )
        # if this has a "current" class, be expanded by default (by checking the checkbox)
        if "current" in classes:
            checkbox.attrs["checked"] = ""

        # Identify the title of the li item
        a_item = element.find("a")

        # Add the arrow to indicat t has childrem and can be expanded
        icon = _get_navigation_expand_image(soup)
        # check if the current page is the one being expanded and rotate the arrow
        if "current" in classes:
            icon["class"] = icon["class"] + ["current"]

        # Add label for clickability of the arrow icon
        label = soup.new_tag("label", attrs={"for": f"toctree-checkbox-{toctree_checkbox_count}"})
        label.append(icon)
        a_item.insert_after(label)

        # Add the checkbox that's used to store expanded/collapsed state.
        a_item.insert_after(checkbox)

        if "current" not in classes:
            children = element.find("ul")

            for child in children.find_all("li"):
                child["class"] = child.get("class", []) + ["hidden"]
                # Add a class to indicate

    if last_element_with_current is not None:
        last_element_with_current["class"].append("current-page")
        last_element_with_current["class"].append('aria-current="page"')

    return str(soup)