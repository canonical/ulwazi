# Testing strategy

This page describes the vision for testing the Ulwazi Sphinx theme.
It defines **what** we test, **why** we test it, and **how** the tests are
organised -- so that every contributor understands the goals and can help move
towards them.

This is a target to aim for, not a detailed implementation plan.
Some of the tests described here already exist; others are planned work that
aligns with the goals in the [roadmap](roadmap.md).

## Guiding principles

- **Confidence over coverage.** A test is valuable if it catches real
  regressions that a user would notice, not if it inflates a coverage number.
- **Fast feedback by default.** Every change should be validated by a fast,
  automatic test suite. Expensive checks run on a schedule or on demand.
- **Readable for non-engineers.** Tests are written and documented so that
  Technical Authors and designers can understand what is being checked and why.
- **Layered checks.** We combine build-time checks, structural HTML validation,
  visual regression, and browser-level testing so that problems are caught at
  the earliest stage where they can be detected.

## Technology stack

The testing stack builds on the same tools that the project already uses for
development:

| Tool | Role |
| --- | --- |
| [uv](https://docs.astral.sh/uv/) | Manages the Python virtual environment, dependencies, and test groups. All test commands run through `uv run`. |
| [pytest](https://docs.pytest.org/) | The test runner. Tests live in the `tests/` directory and are discovered automatically. |
| [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) | Parses built HTML so we can assert on structure and content without a browser. |
| [Playwright](https://playwright.dev/python/) | Launches a real browser to check rendered appearance, computed styles, and responsive behaviour. |
| [coverage.py](https://coverage.readthedocs.io/) | Measures which parts of the theme's Python code are exercised by the tests. To track the theme functions that Sphinx calls during a build, tests invoke Sphinx through its Python API rather than relying on a pre-built output directory. |
| GitHub Actions | Runs the automatic test suite on every push and pull request. |

Tests are split into two tiers using pytest markers:

- **Fast tests** (`not slow`) -- run on every change. They build HTML and check
  structure, assets, and Python logic.
- **Slow tests** (`slow`) -- run regularly or on demand. They include PDF
  generation and browser-based visual checks that need extra system
  dependencies or take longer to complete.

## Test categories

The tests are organised into the following categories, ordered from the
earliest stage at which a problem can be detected to the most comprehensive
checks:

1. **Build process tests** -- verify the build pipeline completes successfully.
2. **Smoke tests** -- quick high-level checks for obvious breakage.
3. **Asset and structural validation** -- ensure all referenced assets exist and
   the HTML structure is sound.
4. **Feature and regression tests** -- verify every major theme feature renders
   correctly.
5. **Extension compatibility tests** -- ensure the theme works with all default
   Sphinx Stack extensions.
6. **Responsive and cross-browser tests** -- verify layout across screen sizes
   and browsers.
7. **Python version and environment compatibility** -- ensure the theme works
   across supported environments.
8. **Accessibility checks** -- ensure the theme meets accessibility standards.

### 1. Build process tests

**Goal:** Ensure the theme and the sample documentation build successfully and
reproducibly.

These tests verify that the build pipeline -- SCSS compilation, theme package
installation, and Sphinx invocation -- completes without errors and produces the
expected output files.

What to check:

- `make vanilla-main` compiles SCSS to CSS without errors.
- `make docs` builds the HTML output and produces `docs/_build/index.html`.
- `make docs-pdf` (slow) produces the expected PDF file.
- Sphinx builds with `--fail-on-warning` so that warnings are treated as errors.
- The build works from a clean environment (`make rebuild`).

### 2. Smoke tests

**Goal:** Catch obvious breakage quickly before deeper checks run.

Smoke tests are fast, high-level checks that confirm the most important things
are present and working. If a smoke test fails, there is no point running more
detailed tests.

What to check:

- The built `index.html` exists and contains expected content.
- Core theme assets (CSS, JS, fonts) are present and linked correctly.
- The navigation menu, header, and footer render on the home page.
- No unstyled or raw template markup leaks into the output.

### 3. Asset and structural validation

**Goal:** Ensure every referenced asset exists and the HTML structure is sound.

These tests parse the built HTML with Beautiful Soup and verify that all
internal links, stylesheets, scripts, and images resolve to real files.

What to check:

- Every `<link>`, `<script>`, and `<img>` tag points to an existing asset.
- Internal navigation links are not broken.
- The sitemap is generated and contains the expected URLs.
- No empty or duplicate `id` attributes on critical elements.

### 4. Feature and regression tests

**Goal:** Verify that every major theme feature renders correctly and continues
to do so after changes.

The sample documentation in `docs/content/` doubles as a test fixture. Each
feature has a dedicated page that exercises the relevant markup. Tests then
check the built HTML for the expected structure and classes.

Main features to cover:

- **Admonitions** -- every admonition type maps to the correct Vanilla
  notification class.
- **Code blocks** -- syntax highlighting, copy buttons, and inline code styling.
- **Headings** -- heading levels, heading classes, and headings that contain
  inline code.
- **Tables of contents** -- global navigation tree, local (on-page) TOC, and TOC
  depth truncation.
- **Tabs** -- `sphinx-tabs` rendering and synced tabs.
- **Typography** -- paragraph text, headings, lists, and blockquotes match the
  Vanilla Framework design tokens.
- **Breadcrumbs** -- breadcrumb navigation reflects the page hierarchy.
- **Search** -- the search page loads and returns results.
- **404 page** -- the not-found page renders with theme styling.
- **SCSS propagation** -- custom SCSS classes reach the rendered HTML with the
  expected computed styles.

### 5. Extension compatibility tests

**Goal:** Ensure the theme works with every extension that the
[Sphinx Stack](https://documentation.ubuntu.com/sphinx-stack/latest/reference/default-extensions/)
enables by default.

Because documentation projects rely on these extensions, a theme change must not
break their output. Each extension should have at least one sample page and a
test that checks the rendered result.

For the current list of extensions that the Sphinx Stack enables by default,
see the
[Sphinx Stack documentation](https://documentation.ubuntu.com/sphinx-stack/latest/reference/default-extensions/).

### 6. Responsive and cross-browser tests

**Goal:** Verify the theme looks and works correctly across screen sizes and
browsers.

These tests use Playwright to load the built site in a real browser and check
layout, computed styles, and interactive behaviour.

What to check:

- **Mobile** (375 px width) -- navigation collapses, content reflows, no
  horizontal scroll.
- **Tablet** (768 px) -- layout adjusts correctly, side navigation behaves.
- **Desktop** (1280 px) -- full layout with side navigation and local TOC.
- **Large desktop** (1920 px) -- typography and spacing match the design
  specification.
- **Theme toggle** -- light/dark mode toggle works and persists.
- **Keyboard navigation** -- focus styles are visible and logical.
- **Cross-browser** -- run key visual checks in Chromium and Firefox.

### 7. Python version and environment compatibility

**Goal:** Ensure the theme works across the supported Python versions and
common build environments.

The theme declares `requires-python = ">=3.10"`. Tests should verify that the
build and test suite pass on every supported Python version.

What to check:

- Build and test on all supported Python versions (currently 3.10 through
  3.13).
- Build on Ubuntu (the primary CI platform) and macOS (for local development).
- Verify that the `uv.lock` file is in sync with `pyproject.toml`
  (`make lint-uv-lockfile`).
- Confirm the theme installs cleanly into a fresh virtual environment.

### 8. Accessibility checks

**Goal:** Ensure the theme meets accessibility standards so that documentation is
usable by everyone.

This aligns with the roadmap goal of adding accessibility checks.

What to check:

- Run automated accessibility scans (for example, with
  [pa11y](https://pa11y.org/)) on key pages.
- Check colour contrast ratios for text and interactive elements in both light
  and dark modes.
- Verify that all interactive elements (navigation toggles, tabs, search) are
  operable with a keyboard.
- Ensure heading hierarchy is logical and landmarks are present.

## Running the tests

Tests can be run at three levels, depending on what you need to check:

- **Automatic tests** -- fast checks that run on every change.
- **Full test suite** -- includes slow tests like PDF generation and browser
  checks.
- **Manual visual review** -- a local preview for hands-on inspection.

### Automatic tests (on every change)

Fast tests run automatically on every push and pull request through GitHub
Actions. They build the HTML output and run all non-slow pytest tests.

```shell
make test
```

The `make test-fast` command is an explicit alias for `make test`.

These tests are designed to complete in under a few minutes and require no
extra system dependencies beyond the standard uv environment.

### Full test suite (regular or on-demand)

The full suite includes slow tests: PDF generation and browser-based visual
checks. These require additional system packages (LaTeX, Playwright browsers).

To run only the slow tests:

```shell
make test-slow
```

To run all tests (fast and slow) together with a coverage report:

```shell
make test-coverage
```

The coverage report is written to `results/coverage.xml` and an HTML version is
generated in `htmlcov/`.

### Manual visual review

Automated tests catch regressions, but a manual review is still valuable for
visual polish. Use the local preview server to inspect changes:

```shell
make run
```

Then open `http://127.0.0.1:8000` in a browser and check the sample pages,
especially the [MyST cheat sheet](myst-cheat-sheet.md) and the
[RST cheat sheet](rst-cheat-sheet.rst), which exercise the full range of
supported syntax.
