import requests
from bs4 import BeautifulSoup

PRODUCT_MENU_PARSING_URL = "https://canonical.com/"
PRODUCT_MENU_FILENAME = "product_menu_copy.html"
PRODUCT_MENU_DIRECTORY = "docs/_static"

def fetch_and_parse(url: str) -> BeautifulSoup:
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)
        return BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None

def get_nav_menu(page: BeautifulSoup) -> str:
    return page.find("header", id="navigation").prettify()

def save2file(content:str) -> None:
    filename = PRODUCT_MENU_DIRECTORY.strip("/") + "/" + PRODUCT_MENU_FILENAME
    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)

if __name__ == "__main__":
    address = PRODUCT_MENU_PARSING_URL
    parsed_html = fetch_and_parse(address)
    navigation_menu = get_nav_menu(parsed_html)
    num_lines = len(navigation_menu.splitlines())
    if num_lines > 100:
        print(f"The parsed the NavMenu has {num_lines} lines.")
    else:
        print("NavMenu not found.")
        exit(1)

    print("First 1000 symbols of the NavMenu: \n" + navigation_menu[:1000])
    save2file(navigation_menu)
    print(f"Saved product menu as {PRODUCT_MENU_DIRECTORY.strip("/")}/{PRODUCT_MENU_FILENAME}")
    