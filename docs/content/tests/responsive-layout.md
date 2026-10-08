# Responsive layout tests

`tests/test_responsive.py` covers part of the {doc}`responsive layout and
cross-browser testing goal <../testing-strategy>`. Its five `slow` pytest
cases use Playwright with Chromium and the **pre-built sample home page** at
`docs/_build/index.html`. The two small-screen tests each run at 375px
(mobile) and 768px (tablet); the desktop test runs at 1280px.

## Screen classes

The {doc}`testing strategy <../testing-strategy>` defines the broad mobile,
tablet, desktop and optional large-desktop width ranges. This suite samples
only 375px, 768px and 1280px. It does **not** test the optional 1920px width
or the boundaries between classes. The ranges are not an exhaustive list of
component breakpoints: for example, the side drawer changes maximum width
at 460px, and Ulwazi's custom full-width grid starts at
`calc(1036px + 15rem)` (1276px at a 16px root font size). Neither transition
is tested at its boundary here.

## What is checked

| Test case | Viewport | Checks |
| --- | --- | --- |
| `test_desktop_layout` | 1280px | The outer side navigation, main content, on-page TOC, and top-bar links are visible; the mobile top-bar Menu and side-navigation opener are hidden; the three columns start in left-to-right order. |
| `test_small_screen_layout[mobile-375]` | 375px | Main content is visible, the document does not scroll horizontally, the top-bar links start hidden, Menu opens them and Close menu hides them, and the side-navigation opener is visible. |
| `test_small_screen_layout[tablet-768]` | 768px | The same layout and top-bar checks at tablet width. |
| `test_small_screen_side_navigation[mobile-375]` | 375px | The side-navigation drawer panel starts hidden, opens when its hamburger button is clicked, receives the `is-drawer-expanded` class, and is hidden again with the in-drawer button; the expanded class is removed. |
| `test_small_screen_side_navigation[tablet-768]` | 768px | The same drawer interaction at tablet width. |

These are five pytest results from three test functions. They check the
**home page**, not every built page. In particular, visibility of the outer
side navigation at desktop width does not assert visibility of every link
inside it, and the small-screen horizontal-scroll check happens before any
menu is opened.

## Running and scope

Build the docs first with `make docs`, then run
`uv run --group dev --group docs pytest -q tests/test_responsive.py` to select
just these tests. `make test-all` includes them; `make test-slow` includes
them after building HTML and PDF. The scheduled/on-demand slow-test workflow
runs `make test-slow`. The regular PR workflow runs `make test` (fast tests
only), so these five cases are **not required PR checks**. `make test-coverage`
does not select this file either.

These checks do **not** test search-page or no-feedback opener placement,
feedback-row geometry, drawer bounds, focus and keyboard behavior, backdrop
dismissal, resizing across breakpoints, 320px layouts, other pages, Firefox,
or pixel-level appearance. A separate slow browser journey in
`tests/test_features.py` checks some drawer keyboard interactions at 768px,
and `tests/test_layout_smoke.py` checks all built pages for overflow at a
1440px desktop width. The broader testing strategy describes goals, not
claims of implemented coverage.
