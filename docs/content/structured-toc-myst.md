(structured-toc-myst)=

# Structured tables of contents (MyST)

This page is the MyST Markdown counterpart of
{doc}`structured-toc`, demonstrating the `sphinx-structured-toc`
extension's `domain` and `slice` directives in MyST syntax.

The directives are parsed through MyST's `colon_fence` extension, with `{doc}`
roles as slice items. The slice and domain names match the RST page so both
rendering paths can be verified identically.

```{note}
Colon fences do not nest at the same colon count: the outer `domain` fence
must use more colons (`:::::`) than the inner `slice` fences (`:::`), otherwise
the outer fence closes at the first inner `:::` line.
```

## Domain named after a section heading

When the `domain` directive has no argument, its name is derived from the
nearest enclosing section heading:

:::::{domain}

:::{slice} Content

{doc}`Home <../index>`
{doc}`Contribution guide <contribute>`

:::

:::{slice} Tests

{doc}`Test content <test>`
{doc}`Tests overview <tests/index>`

:::

:::::

## Explicit domain name

A `domain` can also take an explicit name, which overrides the section
heading. Items can carry the trailing `slice` and `domain` keywords to have
the slice and domain names added to their accessible names:

:::::{domain} Ulwazi sample documentation
:suppress-warnings:

:::{slice} Reference

{doc}`RST cheat sheet <rst-cheat-sheet>` slice
{doc}`MyST cheat sheet <myst-cheat-sheet>` slice

:::

:::{slice} Meta

{doc}`Testing strategy <testing-strategy>` domain
{doc}`Roadmap <roadmap>` domain

:::

:::::

```{note}
The `:suppress-warnings:` flag silences the extension's ambiguity warnings
for every item in the domain. It is used here because the sample pages above
are not part of any `toctree`, which would otherwise make the build fail on
warnings.
```
