# Structured TOC tests

The structured TOC tests verify that the
[sphinx-structured-toc](https://github.com/canonical/sphinx-structured-toc)
extension works with the Ulwazi theme, that its `domain` and `slice` directives
render correctly in both RST and MyST source syntax, with the accessibility
markup they produce surviving Ulwazi's HTML post-processing.

Throughout this page, *domain* means a named group of related documentation
links and *slice* means one subsection of that group. See the
[extension's README](https://github.com/canonical/sphinx-structured-toc)
for details.

This implements the "Extension compatibility" test category from the
{doc}`testing strategy <../testing-strategy>`.

## What is tested

The fixtures are the "Structured tables of contents" sections of the
{doc}`RST cheat sheet <../rst-cheat-sheet>` and the
{doc}`MyST cheat sheet <../myst-cheat-sheet>`. There are no dedicated sample
pages for this feature: the cheat sheets already serve as the theme's
rendering reference, and reusing them keeps the example and its test in the
place contributors look first. Both use the same slice and domain names, so
both rendering paths can be verified identically.

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
  context disambiguates them for users of screen readers.
- The extension's `domain-list.css` is linked on the page.

Fast tests run with `make test`.

The slow test (marked `slow`, run with
`make test-slow`) additionally verifies the rendered appearance in a real
browser with Playwright:

- Slice items flow inline (one line per slice), as `domain-list.css`
  intends.
- The explicit domain name span (`span.domain-aria-target`) is present in
  the DOM but visually hidden, so screen readers announce the domain while
  sighted users see the compact list.

The same slow test builds LaTeX in a temporary directory and confirms that
**both** cheat sheets contribute bold slice names and linked list items to the
PDF source. The extension supports PDF output starting with version 0.2.0;
PDF links remain usable, but ARIA attributes are specific to HTML. The LaTeX
and browser checks run independently, so a LaTeX build failure does not hide
browser problems, and vice versa.

## What is not tested

The test doesn't re-test the extension's internals (directive parsing, id
generation, ambiguity warnings), only that Ulwazi's build wires the
extension up correctly and that its output stays intact and legible under
the theme.

## How it's tested

The fast test parses the HTML files that Sphinx already builds under
`docs/_build/` using
[Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/). The slow
test loads the built pages in Chromium with
[Playwright](https://playwright.dev/) and inspects element geometry, then
runs Sphinx separately with warnings treated as errors and checks the
generated `.tex` before the PDF target removes intermediate files.

```shell
make docs
uv run pytest tests/test_structured_toc.py
```

The checks are grouped into two tests -- `test_structured_toc_markup` for
everything that only needs the built HTML, and `test_structured_toc_slow`
for the LaTeX and browser checks -- so each pytest run reports a single
line per tier it selects: `make test` and `make test-slow` each report one
result, and a full run (`make test-all`) reports both. If a check fails, the
failure message lists every specific problem found, tagged by page and
checked part.

The cheat-sheet examples use native `domain`/`slice` directives without
HTML-only wrappers. When combined into one LaTeX document, identical
unmarked links from the two cheat sheets trigger the extension's ambiguity
warnings; their domains use `:suppress-warnings:` to keep the build clean.
