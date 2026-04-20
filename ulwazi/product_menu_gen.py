import logging
import os

import requests
from bs4 import BeautifulSoup

PRODUCT_MENU_PARSING_URL = "https://canonical.com/data"
PRODUCT_MENU_FILENAME = "product_menu_copy.html"
PRODUCT_MENU_DIRECTORY = "ulwazi/theme/ulwazi/components/"

logging.basicConfig(
    level=logging.INFO
)  # change to logging.DEBUG to enable debug messages
logger = logging.getLogger(__name__)


def fetch_and_parse(url: str) -> BeautifulSoup:
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)
        return BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching the URL: {e}")
        return None


def apply_grid_alignment(header, page: BeautifulSoup) -> None:
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
        if hasattr(child, "name") and child.name == "div":
            # Found a div child, check if it contains our elements
            if banner in child.descendants and nav in child.descendants:
                container = child
                break

    if not container:
        logger.warning(
            "Could not find container div - attempting transformation anyway"
        )

    # Create the new grid structure
    subgrid_div = page.new_tag("div", **{"class": "l-docs__subgrid"})
    sidebar_div = page.new_tag("div", **{"class": "l-docs__sidebar"})
    main_div = page.new_tag("div", **{"class": "l-docs__main"})

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
        "header", id="product-menu-header", **{"class": "product-menu"}
    )
    wrapper.append(header)

    return wrapper.prettify()


def save2file(content: str) -> None:
    filename = PRODUCT_MENU_DIRECTORY.strip("/") + "/" + PRODUCT_MENU_FILENAME
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)


def prefix_local_links(soup, base_url="https://canonical.com") -> BeautifulSoup:
    """Updates all local links/resources in a BeautifulSoup object by
    prepending them with the given base URL.
    """
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
            if element.has_attr(attr) and element[attr].startswith("/"):
                element[attr] = base_url + element[attr]
    return soup


if __name__ == "__main__":
    address = PRODUCT_MENU_PARSING_URL
    parsed_html = fetch_and_parse(address)
    navigation_menu = get_nav_menu(prefix_local_links(parsed_html))
    num_lines = len(navigation_menu.splitlines())
    if num_lines > 100:
        logger.debug(f"The parsed the NavMenu has {num_lines} lines.")
    else:
        logger.error("NavMenu not found.")
        exit(1)

    logger.debug("First 1000 symbols of the NavMenu: \n" + navigation_menu[:1000])
    save2file(navigation_menu)
    logger.info(
        f"Saved product menu as {PRODUCT_MENU_DIRECTORY.strip('/')}/{PRODUCT_MENU_FILENAME}"
    )
