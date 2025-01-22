# Ulwazi

Ulwazi, Xhosa for information, is a work-in-progress Sphinx theme based on [Vanilla design](https://github.com/canonical/vanilla-framework).

[Demo website](https://canonical-ulwazi.readthedocs-hosted.com/)

Layout and functionality is derived from [sphinx-basic-ng](https://github.com/pradyunsg/sphinx-basic-ng), developed by [praduimsg](https://github.com/pradyunsg) and [Alabaster](https://github.com/sphinx-doc/alabaster).

The theme will default to a generic Vanilla Framework style but will have options for the specific Canonical theming to support the org's documentation needs. 

## Testing

A Makefile includes some basic functionality to build the theme and then build and run the test content with the theme.

To build documentation using the theme, run:

```
make run
```

Once built, any changes to the theme will require a new package to be built and installed. To do this, run:

```
make rebuild
```
