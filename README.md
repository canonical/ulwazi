# Ulwazi

This is a proof of concept for a Sphinx theme based on [Vanilla design](https://github.com/canonical/vanilla-framework).

Layout and functionality is derived from [sphinx-basic-ng](https://github.com/pradyunsg/sphinx-basic-ng), developed by [praduimsg](https://github.com/pradyunsg), and [Alabaster](https://github.com/sphinx-doc/alabaster).

## Testing

A Makefile is included with some basic functionality to run and rebuild the test content. To build documentation using the theme, clone the repository and run:

```
make run
```

Once built, any changes to the source of the theme will require a new package to be built and installed. To do this, run:

```
make rebuild
```