# Tests

This section documents the Ulwazi theme test suite. See the list of tests
implemented in Ulwazi below.

Basic tests:

- **Site validation** (`tests/test_site_validation.py`) — verifies the built HTML has no broken assets (missing CSS, JS, images).
- **SCSS propagation** (`tests/test_scss_propagation.py`) — checks that custom SCSS classes reach the rendered HTML with the expected computed styles.
- **PDF generation** (`tests/test_pdf_generation.py`) — verifies PDF generation produces the expected output file. *(slow)*

More advanced tests:

```{toctree}
:maxdepth: 1

SEO and metadata <seo-metadata>
Structured TOC <structured-toc>
Python versions <python-versions>
```

(test-output-convention)=
## Test output convention

Tests are grouped so that their pytest output stays minimal when everything
passes, but pinpoints every problem when something fails:

- **When green:** all checks of a test run inside a single pytest test case,
  so a passing run reports one `PASSED` line per test. A test file with both
  a fast and a slow test reports one line per tier it runs in (two lines in
  `make test-all`).
- **When red:** the test collects every failed check it can safely run --
  across all checked pages and parts -- and lists them all in one failure
  message, each tagged by page and checked part. A failure on one page or
  part does not hide problems found elsewhere.

For example, a failing structured-TOC run reports which of the RST or MyST
fixture pages broke and which check failed on it:

```text
structured-TOC slow checks failed:
  - [rst] slice items are not rendered inline (y positions: [11031, 11051])
  - [rst] domain-aria-target span not found
```

The exception is tests that are parametrized on purpose, such as the
{ref}`Python version tests <python-version-tests>`, where each parameter
value is an independently reported result.
