# Theme feature and regression tests

`tests/test_features.py` checks Ulwazi's page-processing results and a short
browser journey. The fixtures include **both** the MyST and RST syntax cheat
sheets, the code-heading page, and the two admonition example pages.

## Fast: generated markup

One grouped fast case, `test_features_fast`, checks document heading classes
and inline code, plain-text global navigation titles, Vanilla body-list and
local-TOC markup,
the configured TOC depth, and notification type mappings. It also checks that
named admonition targets survive, each converted tab set has reciprocal
button/panel references and one initially selected panel, and a highlighted
code block and copy script are wired in. The search page must include a
breadcrumb-map entry for the code-heading page. The same case also checks the
inline-code example and the first rendered header and data row of each grid,
list, and CSV table in both cheat sheets.

This verifies Ulwazi's conversions, not Sphinx's parsing and highlighting
algorithms or the details of `sphinx-design` and other extensions.

## Slow: user interactions

One grouped `slow` Playwright case, `test_features_slow`, opens the **fresh**
site through a local HTTP server. In a new browser context it checks that the
cookie-consent notification appears on first visit, closes after **Accept
all** and saves the consent cookie, stays closed on another page in the same
browser context, and reopens from the footer's **Manage your tracker
settings** link. It then expands and collapses the global navigation,
selects tabs by click and arrow key, checks that dark mode persists between
pages, clicks a code-block copy button and verifies the clipboard text, and
submits a search and follows a result with the correct breadcrumb.
Chromium is installed on demand; the case needs browser dependencies, so it
is not run by the fast PR workflow.

The consent dialog is provided by the external Canonical cookie bundle; the
sample docs configure that bundle and Ulwazi renders the footer link. This
check covers their integration, not the bundle's full preference-management
workflow. It requires the bundle to load in the browser and may fail during a
remote outage; the separate {doc}`slow asset availability check
<assets-structure>` reports CDN failures as advisory warnings instead.

Search and browser checks assert the theme's wiring, not Sphinx ranking,
cross-tab-set synchronization, pixel colours or cross-browser layout. The
separate SEO, styling, PDF, structured-TOC and extension-compatibility suites
retain their own scopes.

## Running and reporting

`make test` runs the fast case; `make test-slow` runs the slow case along with
the other slow tests. To select only these cases without Make's older
`docs/_build` prerequisite, run
`uv run --group docs pytest -m 'not slow' tests/test_features.py` or
`uv run --group docs pytest -m slow tests/test_features.py`.

Each tier contributes **one pytest result** for this module. The passing
recap names the pair explicitly:

```text
PASSED tests/test_features.py::test_features_fast
PASSED tests/test_features.py::test_features_slow
```

On failure, the test name identifies the category and tier; the assertion
heading and page or browser-journey labels identify the failed checks. For
example, the fast case can report:

```text
Features [fast] checks failed:
- [content/test7_admonitionsMD] admonitions: note-reference target/link lost
- [search] breadcrumb map: code-heading page must have 'This is a test' ancestor
```

The project-wide pytest `-rA` setting still prints its normal pass recap;
these tests do not change output from other suites. A shared Sphinx build
failure instead appears as a fixture setup error with captured build warnings,
not as a failed feature check.