# Structured TOC tests

The structured TOC tests verify that the
[sphinx-structured-toc](https://github.com/canonical/sphinx-structured-toc)
extension works with the Ulwazi theme: its `domain` and `slice` directives
render correctly in both RST and MyST source syntax, and the accessibility
markup they produce survives Ulwazi's HTML post-processing.

This implements the "Extension compatibility" test category from the
{doc}`testing strategy <../testing-strategy>`.

## What is tested

The fixture pages are {doc}`structured-toc <../structured-toc>` (RST) and
{doc}`structured-toc-myst <../structured-toc-myst>` (MyST). They use the same
slice and domain names so both rendering paths can be verified identically.

For each fixture page, the fast test verifies:

- Both `domain` directives render as `<nav class="domain-list">` elements.
- Every `aria-labelledby` value resolves to an element `id` on the same page
  -- this is the core accessibility contract that ties the nav landmark,
  slice labels, and marked links together.
- Each slice renders a `<span class="domain-list-label">` with the expected
  name.
- Items marked with the trailing `slice`/`domain` keywords carry both `id`
  and `aria-labelledby` on their `<a>` tag; unmarked items carry neither.
- Duplicate visible link texts have distinct accessible names -- the ARIA
  context disambiguates them for screen reader users.
- The extension's `domain-list.css` is linked on the page.

The slow test (marked `slow`, run with `make test-slow`) additionally
verifies the rendered appearance in a real browser with Playwright:

- Slice items flow inline (one line per slice), as `domain-list.css`
  intends.
- The explicit domain name span (`span.domain-aria-target`) is present in
  the DOM but visually hidden, so screen readers announce the domain while
  sighted users see the compact list.

## What is not tested

The test doesn't re-test the extension's internals (directive parsing, id
generation, ambiguity warnings) -- only that Ulwazi's build wires the
extension up correctly and that its output stays intact and legible under
the theme.

## How it's tested

The fast test parses the HTML files Sphinx already builds under
`docs/_build/` using
[Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/). The slow
test loads the built pages in Chromium via
[Playwright](https://playwright.dev/) and inspects element geometry.

```shell
make docs
uv run pytest tests/test_structured_toc.py
```

All structural checks are grouped into a single `test_structured_toc_markup`
test, so the pytest summary stays one line when everything passes. If a
check fails, the assertion message lists every specific problem found,
tagged by page.

```{note}
The extension registers HTML visitors only, so the LaTeX (PDF) builder
would fail on its nodes. `docs/conf.py` registers no-op LaTeX visitors for
them, which keeps the structured tables of contents out of the PDF while
the surrounding prose still appears.
```
