"""Generate the navigation tree from Sphinx's toctree function's output."""

import functools
import copy

from bs4 import BeautifulSoup, Tag


def _get_navigation_expand_image(soup: BeautifulSoup, is_active: bool = False) -> Tag:
    # Render both icons, CSS will toggle visibility
    icon_down = soup.new_tag("i", attrs={"class": "p-icon--chevron-down"})
    icon_up = soup.new_tag("i", attrs={"class": "p-icon--chevron-up"})
    container = soup.new_tag("span")
    container.append(icon_down)
    container.append(icon_up)
    return container


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
        classes = element.get("class", [])
        if "current" in classes:
            last_element_with_current = element

        has_children = bool(element.find("ul"))

        if has_children:
            element["class"] = classes + ["has-children"]

            toctree_checkbox_count += 1
            checkbox_name = f"toctree-checkbox-{toctree_checkbox_count}"

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
            if "current" in classes:
                checkbox.attrs["checked"] = ""

            a_item = element.find("a")

            # Pass is_active to icon generator
            icon = _get_navigation_expand_image(soup, is_active="current" in classes)

            label = soup.new_tag("label")
            label.attrs["for"] = checkbox_name
            label.append(_get_navigation_expand_image(soup, is_active="current" in classes))

            # Create nav-item div and append a, label, checkbox
            nav_item_div = soup.new_tag("div", attrs={
                "class": "nav-item",
                "data-checkbox": checkbox_name
            })
            nav_item_div.append(a_item)
            nav_item_div.append(checkbox)  # <-- checkbox before label
            nav_item_div.append(label)

            # Remove a_item, label, checkbox from their previous positions
            for tag in [a_item, label, checkbox]:
                if tag in element.contents:
                    element.contents.remove(tag)
            element.insert(0, nav_item_div)

            # Hide children unless this li is "current"
            children_ul = element.find("ul")
            if children_ul and "current" not in classes:
                for child_li in children_ul.find_all("li", recursive=False):
                    child_li["class"] = child_li.get("class", []) + ["hidden"]

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
        last_element_with_current["class"].append("current-page")
        last_element_with_current["class"].append('aria-current="page"')

    return str(soup)