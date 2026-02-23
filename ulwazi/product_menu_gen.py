import requests
from bs4 import BeautifulSoup
import os
import logging

PRODUCT_MENU_PARSING_URL = "https://canonical.com/data"
PRODUCT_MENU_FILENAME = "product_menu_copy.html"
PRODUCT_MENU_DIRECTORY = "ulwazi/theme/ulwazi/components/"

logging.basicConfig(level=logging.INFO)  # change to logging.DEBUG to enable debug messages
logger = logging.getLogger(__name__)

def fetch_and_parse(url: str) -> BeautifulSoup:
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)
        return BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching the URL: {e}")
        return None

def get_nav_menu(page: BeautifulSoup) -> str:
    header = page.find("header", id="navigation")
    # Change the id to avoid conflicts with the theme's main navigation
    if header:
        header["id"] = "product-navigation"
    return header.prettify()

def save2file(content:str) -> None:
    filename = PRODUCT_MENU_DIRECTORY.strip("/") + "/" + PRODUCT_MENU_FILENAME
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)

def prefix_local_links(soup, base_url="https://canonical.com") -> BeautifulSoup:
    """
    Updates all local links/resources in a BeautifulSoup object by
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
    logger.info(f"Saved product menu as {PRODUCT_MENU_DIRECTORY.strip("/")}/{PRODUCT_MENU_FILENAME}")
