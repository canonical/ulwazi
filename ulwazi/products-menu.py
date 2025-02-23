import requests
from bs4 import BeautifulSoup

URL = "https://canonical.com/"


def fetch_and_parse(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None

if __name__ == "__main__":
    address = URL
    parsed_html = fetch_and_parse(address)
    navigation_menu = parsed_html.find("header", id="navigation")

    if navigation_menu:
        # print("Found the NavMenu: \n", navigation_menu.prettify())
        num_lines = len(navigation_menu.prettify().splitlines())
        print(f"Parsed the NavMenu spanning {num_lines} lines.")
    else:
        print("NavMenu not found.")

