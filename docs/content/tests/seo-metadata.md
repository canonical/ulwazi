---
og:title: "Testing metadata and SEO overrides"
og:description: "Custom Open Graph description set on this page to test the override mechanism."
og:image: "https://assets.ubuntu.com/v1/253da317-image-document-ubuntudocs.svg"
myst:
  html_meta:
    description: "Custom meta description set on this page to test the SEO override mechanism."
---

(testing-metadata)=

# SEO and metadata tests

The SEO and metadata tests verify that page `<title>`, description, Open Graph
tags, canonical link, and favicon are all present and correctly formed on
built pages.

This implements the "Asset and structural validation" and "Extension
compatibility" test categories from the
[testing strategy](https://github.com/canonical/ulwazi/pull/124).

## What is tested

For each checked page, the test verifies:

- `<title>` includes the site-name suffix, not just the page heading.
- `<meta name="description">` is present and non-empty.
- `rel="canonical"` link is present and is an absolute URL.
- A favicon `<link>` tag is present.
- All required Open Graph tags (`og:title`, `og:type`, `og:url`, `og:site_name`,
  `og:description`, `og:image`) are present, and always use `property=`, never
  `name=`.

The test also checks that per-page `og:*` and description overrides work. The
fixture page for this check is this very page -- its front matter sets manual
`og:title`, `og:description`, `og:image`, and description overrides, so the
test can confirm the override syntax documented in
{doc}`the contribution guide <../contribute>` actually works, not just that
the auto-generated defaults are present.

## What is not tested

The test doesn't re-check Sphinx or `sphinxext-opengraph` internals (for
example, how descriptions are truncated) -- only that Ulwazi's own templates
and configuration wire the extension up correctly.

## How it's tested

The test parses the HTML files Sphinx already builds under `docs/_build/`
using [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) -- no
browser needed, since none of these checks depend on rendered appearance.

```shell
make docs
uv run pytest tests/test_seo_metadata.py
```

All checks are grouped into a single `test_seo_metadata` test, so the pytest
summary stays one line when everything passes. If a check fails, the
assertion message lists every specific problem found, tagged by page, for
example:

```text
- [index] missing favicon <link> tag
- [testing_metadata] og:title override did not take effect: 'Testing metadata and SEO' (expected 'Testing metadata and SEO overrides')
```

See {doc}`the contribution guide <../contribute>` for the default metadata
behaviour and override syntax that this test verifies.