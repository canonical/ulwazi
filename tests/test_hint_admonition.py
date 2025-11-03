"""Test that hint admonitions have custom star icon styling."""
import os
from bs4 import BeautifulSoup

INDEX_PATH = "docs/_build/content/test6_admonitions.html"
COMPILED_CSS_PATH = "ulwazi/theme/ulwazi/static/css/vanilla-main.css"


def test_hint_has_custom_class():
    """Verify that hint admonitions include the p-notification--hint class."""
    # Skip test if build doesn't exist yet
    if not os.path.exists(INDEX_PATH):
        return
    
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "lxml")
    
    # Find hint admonition - it should have both p-notification--positive and p-notification--hint
    hint_divs = soup.find_all("div", class_="p-notification--hint")
    assert len(hint_divs) > 0, "No elements found with class 'p-notification--hint'"
    
    # Verify it also has p-notification--positive
    for hint_div in hint_divs:
        classes = hint_div.get("class", [])
        assert "p-notification--positive" in classes, \
            "Hint notification should have p-notification--positive class"
        assert "p-notification--hint" in classes, \
            "Hint notification should have p-notification--hint class"


def test_css_contains_hint_rule():
    """Verify that compiled CSS contains the custom rule for hint notifications."""
    assert os.path.exists(COMPILED_CSS_PATH), \
        f"Compiled CSS not found at {COMPILED_CSS_PATH}"
    
    with open(COMPILED_CSS_PATH, "r", encoding="utf-8") as f:
        css_content = f.read()
    
    # Check that the custom CSS rule exists
    assert ".p-notification--hint" in css_content, \
        "CSS should contain .p-notification--hint selector"
    assert "background-image:" in css_content, \
        "CSS should contain background-image property"
    # Check for the star SVG (simplified check for key parts)
    assert "M8 0l2.4 5.2 5.6.8-4 4 1 5.6L8 13l-5 2.6 1-5.6-4-4 5.6-.8L8 0z" in css_content, \
        "CSS should contain star icon SVG path"


def test_tip_does_not_have_hint_class():
    """Verify that tip admonitions do not have the p-notification--hint class."""
    # Skip test if build doesn't exist yet
    if not os.path.exists(INDEX_PATH):
        return
    
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "lxml")
    
    # Find all p-notification--positive divs
    positive_divs = soup.find_all("div", class_="p-notification--positive")
    
    # Filter to find tips (those without hint class but with positive class)
    # We need to check the title to distinguish between hint and tip
    for div in positive_divs:
        title_elem = div.find("h5", class_="p-notification__title")
        if title_elem and "Tip" in title_elem.get_text():
            classes = div.get("class", [])
            assert "p-notification--hint" not in classes, \
                "Tip notification should not have p-notification--hint class"
