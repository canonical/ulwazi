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

"""Utilities for building the navigation menu."""

import logging
import sys
from pathlib import Path
from typing import cast

import requests
from bs4 import BeautifulSoup, Tag

PRODUCT_MENU_PARSING_URL = "https://canonical.com/data"
PRODUCT_MENU_DIRECTORY = "ulwazi/theme/ulwazi/components/"
PRODUCT_MENU_FILENAME = "product_menu_copy.html"
NAVMENU_LINE_THRESHOLD = 100

logging.basicConfig(
    level=logging.INFO
)  # change to logging.DEBUG to enable debug messages
logger = logging.getLogger(__name__)


def fetch_and_parse(url: str) -> BeautifulSoup | None:
    """Fetch and parse markup from a given URL.

    :param url: The remote source to pull the markup from.

    :returns: The parsed markup on success. Else, none.

    :raises RequestException: For bad responses from the URL request.
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)
        return BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.RequestException:
        logger.exception(f"Error fetching the URL")
        return None


def apply_grid_alignment(header: Tag, page: BeautifulSoup) -> None:
    """Transform the navigation structure to use l-docs grid layout.

    Converts from p-navigation__row--25-75 to l-docs__subgrid with
    l-docs__sidebar and l-docs__main for proper alignment.

    This is resilient to changes as it relies on stable class names
    (p-navigation__banner and p-navigation__nav) rather than exact structure.
    """
    # Find the banner and nav elements (these are the stable elements we need)
    banner = header.find("div", class_="p-navigation__banner")
    nav = header.find("nav", class_="p-navigation__nav")

    if not banner:
        logger.warning(
            "Could not find banner element (p-navigation__banner) - skipping grid transformation"
        )
        return

    if not nav:
        logger.warning(
            "Could not find nav element (p-navigation__nav) - skipping grid transformation"
        )
        return

    # Find the parent container - look for a div that's a direct child of header
    # This is typically p-navigation__row--25-75 or similar
    container = None
    for child in header.children:
        child = cast(Tag, child)  # We don't need to worry about NavigableStrings here
        if (
            hasattr(child, "name")
            and child.name == "div"
            and banner in child.descendants
            and nav in child.descendants
        ):
            container = child
            break

    if not container:
        logger.warning(
            "Could not find container div - attempting transformation anyway"
        )

    # Create the new grid structure
    subgrid_div = page.new_tag("div", attrs={"class": "l-docs__subgrid"})
    sidebar_div = page.new_tag("div", attrs={"class": "l-docs__sidebar"})
    main_div = page.new_tag("div", attrs={"class": "l-docs__main"})

    # Move banner into sidebar (extract removes it from its current location)
    banner.extract()
    sidebar_div.append(banner)

    # Move nav into main
    nav.extract()
    main_div.append(nav)

    # Assemble the grid structure
    subgrid_div.append(sidebar_div)
    subgrid_div.append(main_div)

    # Replace the old container with the new grid structure
    if container:
        container.replace_with(subgrid_div)
    else:
        # No container found, append directly to header
        header.append(subgrid_div)

    logger.debug("Successfully applied grid alignment transformation")


def get_nav_menu(page: BeautifulSoup) -> str:
    """Extract and process a page's navigation menu.

    :param page: The page to extract the nav menu from.

    :returns: The page navigation, wrapped in a custom header tag.
    """
    header = page.find("header", id="navigation")

    if not header:
        logger.error("Could not find header with id='navigation'")
        return ""

    # Change the id to avoid conflicts with the theme's main navigation
    header["id"] = "product-navigation"

    # Apply grid alignment transformation
    apply_grid_alignment(header, page)

    # Wrap in outer header with id="product-menu-header" and class="product-menu"
    wrapper = page.new_tag(
        "header", id="product-menu-header", attrs={"class": "product-menu"}
    )
    wrapper.append(header)

    return wrapper.prettify()


def save2file(content: str) -> None:
    """Write the product menu HTML to a file.

    :param content: The string to write to write to the product menu copy.
    """
    filename = f"{PRODUCT_MENU_DIRECTORY.strip('/')}/{PRODUCT_MENU_FILENAME}"
    Path.mkdir(Path(filename).parent, exist_ok=True, parents=True)
    with Path(filename).open("w", encoding="utf-8") as file:
        file.write(content)


def prefix_local_links(
    soup: BeautifulSoup, base_url: str = "https://canonical.com"
) -> BeautifulSoup:
    """Prepend all links in 'soup' with the given 'base_url'."""
    # Tags and attributes to check for local references
    link_attributes = {
        "a": "href",
        "link": "href",
        "script": "src",
        "img": "src",
        "iframe": "src",
        "source": "src",
        "form": "action",
    }

    for tag, attr in link_attributes.items():
        for element in soup.find_all(tag):
            if element.has_attr(attr) and str(element[attr]).startswith("/"):
                element[attr] = f"{base_url}{element[attr]}"
    return soup


if __name__ == "__main__":
    address = PRODUCT_MENU_PARSING_URL
    parsed_html = fetch_and_parse(address)
    navigation_menu = (
        get_nav_menu(prefix_local_links(parsed_html)) if parsed_html else ""
    )
    num_lines = len(navigation_menu.splitlines()) if navigation_menu else 0
    if num_lines > NAVMENU_LINE_THRESHOLD:
        logger.debug(f"The parsed the NavMenu has {num_lines} lines.")
    else:
        logger.error("NavMenu not found.")
        sys.exit(1)

    save2file(str(navigation_menu))
    logger.info(
        f"Saved product menu as {PRODUCT_MENU_DIRECTORY.strip('/')}/{PRODUCT_MENU_FILENAME}"
    )
