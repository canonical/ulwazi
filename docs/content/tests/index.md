# Tests

This section documents the Ulwazi theme test suite. See the list of tests
implemented in Ulwazi below.

Basic tests:

- **Site validation** (`tests/test_site_validation.py`) — verifies the built HTML has no broken assets (missing CSS, JS, images).
- **SCSS propagation** (`tests/test_scss_propagation.py`) — checks that custom SCSS classes reach the rendered HTML with the expected computed styles.
- **Layout smoke** (`tests/test_layout_smoke.py`) — checks every built page: the article renders inside the main docs column, and, in a browser at 1440px, no page is wider than the viewport and no element (like an unsized icon) spills out of the main column. *(browser check is slow)*
- **PDF generation** (`tests/test_pdf_generation.py`) — verifies PDF generation produces the expected output file. *(slow)*

More advanced tests:

```{toctree}
:maxdepth: 1

SEO and metadata <seo-metadata>
Python versions <python-versions>
Extension compatibility <extension-compatibility>
```
