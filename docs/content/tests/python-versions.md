(python-version-tests)=
# Python version compatibility tests

The Python version compatibility tests verify that the Ulwazi theme can be
installed into a fresh virtual environment and that the sample documentation
builds successfully on every supported Python version.

This implements the "Python version and environment compatibility" test
category (category #7) from the testing strategy.

## What is tested

For each supported Python version, the test:

1. Provisions a throwaway virtual environment using `uv`.
2. Installs the Ulwazi theme plus the `docs` dependency group into that
   environment.
3. Builds the sample documentation with `--fail-on-warning`.
4. Verifies that the built `index.html` references the Ulwazi stylesheet
   (`vanilla-main.css`), proving the theme was actually applied.

The test does **not** run PDF generation or browser-based visual checks per
version; those remain in the regular slow test suite. The goal here is to
catch environment-level regressions — a dependency that drops support for an
older Python, a theme change that accidentally uses syntax unsupported by the
declared minimum version, or a broken install path.

## Supported Python versions

The theme declares `requires-python = ">=3.10"` in `pyproject.toml`. The
currently tested versions are:

- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13
- Python 3.14

The authoritative list lives in `SUPPORTED_PYTHON_VERSIONS` in
`tests/test_python_versions.py`. The fast
{doc}`code quality check <code-quality>` `test_python_versions_in_sync` fails
if the list disagrees with the GitHub Actions matrix in
`.github/workflows/test-python-versions.yaml`, the `requires-python` floor,
the Python classifiers, or the ruff, mypy and pyright target versions in
`pyproject.toml`.

```{note}
The supported range is defined by `requires-python` in `pyproject.toml`.
Only versions within that range are tested; older versions are not
supported because `uv` will not install the package outside its
declared `requires-python` range.
```

## MyST runtime installation test

A separate slow test, `test_myst_runtime_installation`, validates the
theme's *runtime* dependency chain rather than a Python version: it stages
the packaging inputs outside the checkout, installs the packaged theme
(non-editably) into a fresh `pip` venv with **only** its runtime
dependencies, and then adds plain `myst-parser~=4.0` -- no `linkify` extra,
no manual `linkify-it-py` install. It verifies that:

1. A reST-only build works without MyST installed or activated.
2. The installed `ulwazi` distribution declares `linkify-it-py~=2.0`
   (the dependency that makes the restored MyST `linkify` default work).
3. A MyST fixture with **no** `myst_enable_extensions` assignment renders
   all three restored defaults: substitution, definition lists, and
   bare-URL linkification.

This is the acceptance test for the MyST compatibility defaults restored
from `canonical-sphinx`; see the "MyST syntax defaults" section of
{doc}`../configuration`. It runs on the current
interpreter and does not multiply the Python-version matrix.

## Running the tests locally

The test is marked `slow`, so it is excluded from `make test` and
`make test-fast`. It is included in `make test-all` (which runs all tests
with no marker filter) and `make test-slow`.

To run only this particular test:

```shell
make test-python-versions
```

This runs all supported Python versions concurrently using
[pytest-xdist](https://pytest-xdist.readthedocs.io/) (`-n auto`). Each
version gets its own throwaway virtual environment under pytest's temporary
directory, so your development `.venv` is never touched and the source tree
stays clean.

To run a single Python version (for faster feedback while debugging):

```shell
uv run pytest -m slow tests/test_python_versions.py -k 3.11
```

Replace `3.11` with the version you want to test.

## Running in CI

The tests run automatically on the 15th of every month at 03:00 UTC via the
`Python version compatibility` GitHub Actions workflow
(`.github/workflows/test-python-versions.yaml`).

The workflow uses a GitHub Actions matrix to run each Python version on a
separate runner, which gives clean, isolated logs and free parallelism in
CI. You can also trigger the workflow manually using the `workflow_dispatch`
event — useful when validating a pull request that changes
`requires-python` or the dependency groups.

## Why monthly

Each test job provisions a Python interpreter, installs the full `docs`
dependency group, and builds the sample documentation. That is slow and
expensive compared to the fast test suite, so it runs on a schedule rather
than on every push. The fast tests (`make test`) continue to run on every
change and provide quick feedback.
