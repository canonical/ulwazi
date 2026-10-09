# Smoke tests

The fast `tests/test_smoke.py` case answers a simple question: did the Ulwazi
page shell render a usable home page? It uses the freshly built sample site,
not old files left in `docs/_build/`.

## What is tested

- The main article contains the expected welcome heading and preview text.
- The header, global side navigation and footer are present.
- The skip link targets the main content, and Home is marked as the current
  navigation link.
- No unrendered Jinja delimiters appear in visible, non-example text.

This check is intentionally shallow: see {doc}`assets-structure` for asset
resolution and {doc}`features` for page transformations and interactions.
SEO, styling, external fonts and Sphinx build warnings are checked elsewhere.

## How it is tested

One grouped fast case, `test_smoke_fast`, inspects the home page with
Beautiful Soup. The shared fixture builds the docs using Sphinx's Python API,
so theme hooks are included in test coverage. Run it with `make test` or,
without the Makefile's legacy build step, with
`uv run --group docs pytest tests/test_smoke.py`.

The category recap identifies a passing smoke case as
`2. Smoke: Fast(1/1): PASSED`; use `-vv` to see its pytest ID.
On failure, the same case
lists each broken contract beneath its category and tier, for example:

```text
Smoke [fast] checks failed:
- [home] accessibility: skip link must target main#content
- [home] navigation: Home must be the active current-page link
```