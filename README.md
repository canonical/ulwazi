# Ulwazi

Ulwazi, Xhosa for infomration, is a work-in-progress Sphinx theme based on [Vanilla design](https://github.com/canonical/vanilla-framework).

Layout and functionality is derived from [sphinx-basic-ng](https://github.com/pradyunsg/sphinx-basic-ng), developed by [praduimsg](https://github.com/pradyunsg), and [Alabaster](https://github.com/sphinx-doc/alabaster).

The theme will default to a generic Vanilla Framework style, but will have options for Canonical specific theming to support the org's documentation needs. 

## Testing

A Makefile is included with some basic functionality to run and rebuild the test content. To build documentation using the theme, clone the repository and run:

```
make run
```

Once built, any changes to the source of the theme will require a new package to be built and installed. To do this, run:

```
make rebuild
```
