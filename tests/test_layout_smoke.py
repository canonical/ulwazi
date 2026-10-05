"""Layout smoke tests.

Cheap, page-agnostic checks over every built HTML page to catch layout
breakage that page-specific tests miss: oversized icons or images, wide
content, and templates that render outside the docs grid.

- test_article_inside_docs_main: the page article must sit inside
  ``main.l-docs__main`` so it lands in the grid's content column. Parses
  HTML only (fast).
- test_no_layout_overflow: renders every page in Chromium at a desktop
  width (slow) and checks that:

  - the page is no wider than the viewport, and
  - no visible element spills out of the main content column. This catches
    oversized items that the side columns absorb without widening the
    page (for example, an unsized SVG icon). Content inside a scrolling or
    clipping container (code blocks, wide tables) doesn't count.
"""

import subprocess
import sys
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from playwright.sync_api import ViewportSize, sync_playwright

BUILD_DIR = Path("docs/_build")
VIEWPORT: ViewportSize = {"width": 1440, "height": 900}
MAIN_SELECTOR = "main.l-docs__main"
# Sub-pixel rounding can report 1px of overflow on otherwise fine pages.
TOLERANCE_PX = 1

# Measures page overflow and main-column spill. Both report the deepest
# offending elements, to point at the culprit rather than at every container
# that inherits its size.
_LAYOUT_JS = """([mainSelector, tol]) => {
  const de = document.documentElement;
  const vw = de.clientWidth;
  const name = (e) => e.tagName.toLowerCase() +
    (typeof e.className === 'string' && e.className.trim()
      ? '.' + e.className.trim().split(/\\s+/).join('.') : '');
  const deepest = (test, root) => [...root.querySelectorAll('*')]
    .filter((e) => test(e) && ![...e.children].some(test))
    .slice(0, 3).map(name);

  const pageOut = (e) => e.getBoundingClientRect().right > vw + tol;
  const result = {overflow: de.scrollWidth - vw, overflowCulprits: [],
                  spill: []};
  if (result.overflow > tol) {
    result.overflowCulprits = deepest(pageOut, document.body);
  }

  const main = document.querySelector(mainSelector);
  if (!main) return result;
  const m = main.getBoundingClientRect();
  // Content inside a scrolling/clipping container is contained by design.
  const clipped = (e) => {
    for (let a = e.parentElement; a && a !== main; a = a.parentElement) {
      if (getComputedStyle(a).overflowX !== 'visible') return true;
    }
    return false;
  };
  const spills = (e) => {
    const r = e.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && !clipped(e) &&
      (r.right > m.right + tol || r.left < m.left - tol);
  };
  result.spill = deepest(spills, main);
  return result;
}"""


def _built_pages() -> list[Path]:
    """Return every built HTML page, skipping Sphinx asset directories."""
    assert BUILD_DIR.exists(), f"{BUILD_DIR} not found -- run 'make docs' first"
    return sorted(
        page
        for page in BUILD_DIR.rglob("*.html")
        if not any(part.startswith("_") for part in page.relative_to(BUILD_DIR).parts)
    )


def test_article_inside_docs_main():
    """Every page article renders inside the docs grid's main column."""
    failures = []
    for page in _built_pages():
        with page.open(encoding="utf-8") as f:
            soup = BeautifulSoup(f, "lxml")
        article = soup.select_one('article[role="main"]')
        if article is None:
            # Redirect stubs and similar pages have no article to place.
            continue
        if article.find_parent("main", class_="l-docs__main") is None:
            failures.append(str(page.relative_to(BUILD_DIR)))

    assert not failures, (
        "Article rendered outside .l-docs__main (check the template's "
        "content block):\n  " + "\n  ".join(failures)
    )


@pytest.mark.slow
def test_no_layout_overflow():
    """No page overflows the viewport or spills out of the main column."""
    pages = _built_pages()
    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=True,
    )
    failures = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT)
        for path in pages:
            page.goto(f"file://{path.resolve()}")
            result = page.evaluate(_LAYOUT_JS, [MAIN_SELECTOR, TOLERANCE_PX])
            name = path.relative_to(BUILD_DIR)
            if result["overflow"] > TOLERANCE_PX:
                culprits = ", ".join(result["overflowCulprits"]) or "unknown"
                failures.append(
                    f"{name}: page {result['overflow']}px wider than the "
                    f"viewport (culprits: {culprits})"
                )
            if result["spill"]:
                failures.append(
                    f"{name}: content spills out of the main column "
                    f"({', '.join(result['spill'])})"
                )
        browser.close()

    assert not failures, (
        f"Layout overflow at {VIEWPORT['width']}px viewport:\n  "
        + "\n  ".join(failures)
    )
