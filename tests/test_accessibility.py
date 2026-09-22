"""Accessibility checks: colour contrast (test category 9, testing-strategy.md).

Scope follows the "Accessibility checks" category of the Ulwazi testing
strategy (see docs/content/testing-strategy.md), which names pa11y as the
example automated scanner: "Run automated accessibility scans (for example,
with pa11y) on key pages." Both pa11y and this test are built on axe-core,
the same WCAG 2.1 engine (also used by Lighthouse and browser DevTools) --
this test drives axe-core directly through the Playwright browser already
used elsewhere in this suite (see test_scss_propagation.py) via
`axe-playwright-python`, rather than adding pa11y's own npm/Puppeteer
toolchain (a second, separate browser-automation stack) as a dependency.

Only axe's `color-contrast` *violations* are asserted on -- not its
`incomplete` results (cases axe can't automatically confirm, such as
deliberately transparent, hover-revealed text; axe flags these for manual
review rather than as failures, and this test follows that distinction).

This is a first, focused slice of the "Accessibility checks" category --
contrast only. Automated scans of other WCAG rules, keyboard operability,
and heading/landmark structure are separate follow-up work.
"""

import subprocess
import sys
from pathlib import Path

import pytest
from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import sync_playwright

# Key pages to scan: the home page (header/footer/feedback button) and the
# two cheat sheets, which exercise the widest range of theme components
# (admonitions, tables, code blocks, tabs) per docs/content/testing-strategy.md.
PAGES = {
    "index": Path("docs/_build/index.html"),
    "rst_cheat_sheet": Path("docs/_build/content/rst-cheat-sheet/index.html"),
    "myst_cheat_sheet": Path("docs/_build/content/myst-cheat-sheet/index.html"),
}

# Theme name -> whether the real theme toggle button needs clicking first.
# The default page load is already the light theme (see
# ulwazi/theme/ulwazi/static/js/theme-toggle.js: with no saved preference,
# it falls back to "is-light"), so dark mode is reached by clicking the
# real toggle, exactly as a reader would.
THEMES = {"is-light": False, "is-dark": True}

CONTRAST_RULE = "color-contrast"
AXE_OPTIONS = {
    "runOnly": {"type": "rule", "values": [CONTRAST_RULE]},
    "resultTypes": ["violations"],
}


class ContrastFailure(dict[str, str]):
    """A single axe `color-contrast` violation node, tagged by page and theme."""


def _group_by_root_cause(failures: list[ContrastFailure]) -> list[str]:
    """Collapse per-element violations sharing a (page, theme, colour pair).

    Pygments wraps every syntax-highlighted token in its own <span>, so a
    single low-contrast colour pair (e.g. one pygments token style) can
    produce dozens of individual axe violation nodes -- one per <span> --
    even though there's really only one root-cause colour combination to
    fix. `failureSummary` already encodes the foreground/background/ratio,
    so grouping on (page, theme, summary) collapses those duplicates back
    down to one line per distinct issue, with an example selector and an
    affected-element count.
    """
    grouped: dict[tuple[str, str, str], list[str]] = {}
    for f in failures:
        key = (f["page"], f["theme"], f["summary"])
        grouped.setdefault(key, []).append(f["target"])

    return [
        f"  [{page}/{theme}] {len(targets)} element(s), e.g. {targets[0]}\n    {summary}"
        for (page, theme, summary), targets in grouped.items()
    ]


@pytest.mark.slow
def test_color_contrast_meets_wcag_aa():
    """Scan key pages, in both themes, for axe `color-contrast` violations."""
    for path in PAGES.values():
        assert path.exists(), f"Built page not found: {path}. Run `make docs` first."
    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=True,
    )

    axe = Axe()
    failures: list[ContrastFailure] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for page_name, path in PAGES.items():
            for theme, needs_toggle in THEMES.items():
                page = browser.new_page()
                page.goto(f"file://{path.resolve()}")
                if needs_toggle:
                    page.click(".theme-toggle")
                results = axe.run(page, options=AXE_OPTIONS)
                failures.extend(
                    ContrastFailure(
                        page=page_name,
                        theme=theme,
                        target=", ".join(node["target"]),
                        summary=node.get("failureSummary", violation["help"]),
                    )
                    for violation in results.response["violations"]
                    for node in violation["nodes"]
                )
                page.close()
        browser.close()

    if failures:
        pytest.fail(
            "WCAG AA colour contrast violations found:\n"
            + "\n".join(_group_by_root_cause(failures))
        )
