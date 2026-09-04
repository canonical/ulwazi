PROJECT=ulwazi
UV_TEST_GROUPS := "--group=dev"
UV_DOCS_GROUPS := "--group=docs"
UV_LINT_GROUPS := "--group=lint" "--group=types" $(UV_DOCS_GROUPS)
UV_TICS_GROUPS := "--group=tics"

include common.mk

.PHONY: format
format: format-ruff format-codespell format-prettier format-pre-commit  ## Run all automatic formatters

.PHONY: lint
lint: lint-ruff lint-codespell lint-mypy lint-prettier lint-pyright lint-shellcheck lint-twine  ## Run all linters

.PHONY: pack
pack: pack-pip  ## Build all packages

# Find dependencies that need installing
APT_PACKAGES :=
ifeq ($(wildcard /usr/include/libxml2/libxml/xpath.h),)
APT_PACKAGES += libxml2-dev
endif
ifeq ($(wildcard /usr/include/libxslt/xslt.h),)
APT_PACKAGES += libxslt1-dev
endif
ifeq ($(wildcard /usr/share/doc/python3-venv/copyright),)
APT_PACKAGES += python3-venv
endif

# Used for installing build dependencies in CI.
.PHONY: install-build-deps
install-build-deps:
ifeq ($(APT_PACKAGES),)
else ifeq ($(shell which apt-get),)
	$(warning Cannot install build dependencies without apt.)
	$(warning Please ensure the equivalents to these packages are installed: $(APT_PACKAGES))
else
	sudo $(APT) install $(APT_PACKAGES)
endif

# Ulwazi-specific targets
vanilla-main: install-npm  ## Install Vanilla and compile CSS
	npm install --no-audit --no-fund
	echo "Compiling SCSS to CSS..."

	@echo "Using local sass..."
	@./node_modules/.bin/sass \
		--load-path=node_modules \
		ulwazi/theme/ulwazi/assets/main.scss \
		ulwazi/theme/ulwazi/static/css/vanilla-main.css

	@echo "SCSS compilation complete!"

.PHONY: product-menu
product-menu:  ## Update the product menu
	@echo "Updating the product menu..."
	python3 ulwazi/product_menu_gen.py

.PHONY: pygments-css
pygments-css:  ## Regenerate the syntax highlighting stylesheets (pygments-light/dark.css)
	@echo "Regenerating Pygments stylesheets..."
	uv run python ulwazi/theme/ulwazi/static/css/generate_pygments_css.py
	@echo "Done. Rebuild the docs (make docs-clean && make docs) to pick up the changes."

.PHONY: rebuild
rebuild: clean docs  ## Clean the environment and rebuild the docs

.PHONY: run
run:  ## Launch an interactive preview of the docs
	$(MAKE) -C docs run

# Override tests to build HTML and PDF output as a prerequisite.
# These should be removed when the docs are built programmatically in the tests.
.PHONY: test
test: docs-html  ## Run fast tests only (excluding slow tests)
	uv run pytest -m 'not slow'

.PHONY: test-fast
test-fast: docs-html  ##- Run fast tests only (same as 'make test')
	uv run pytest -m 'not slow'

.PHONY: test-slow
test-slow: docs-html docs-pdf-prep docs-pdf   ##- Run slow tests only (PDF builds, browser checks)
	uv run pytest -m 'slow'

.PHONY: test-all
test-all: docs-html docs-pdf-prep docs-pdf  ##- Run all tests (fast and slow)
	uv run pytest

# Build the theme and sample docs on every supported Python version.
#
# This is a slow test (PR #124 testing-strategy category #7). For each
# version it provisions a throwaway uv venv, installs the theme plus the
# ``docs`` dependency group, and builds the sample docs with
# ``--fail-on-warning``. The developer's ``.venv`` is never touched and the
# source tree stays clean (build output lives under pytest's ``tmp_path``).
#
# The version list is defined once in ``tests/test_python_versions.py``
# (``SUPPORTED_PYTHON_VERSIONS``); pytest expands it via parametrize, so this
# target does not repeat the list.
#
# ``-n auto`` runs the parametrized versions concurrently via pytest-xdist,
# which is the local parallelism we want. To run a single version instead:
#
#     uv run pytest -m slow tests/test_python_versions.py -k 3.11
#
# In CI the monthly workflow (``.github/workflows/test-python-versions.yaml``)
# uses a GitHub Actions matrix instead of pytest-xdist.
.PHONY: test-python-versions
test-python-versions:  ##- Build the theme and docs on every supported Python version (slow)
	uv run pytest -n auto -m slow tests/test_python_versions.py

.PHONY: test-coverage
test-coverage: docs-html docs-pdf ##- Run tests and generate coverage report
ifeq ($(COVERAGE_SOURCE),)
	uv run coverage run --source $(PROJECT),tests -m pytest
else
	uv run coverage run --source $(COVERAGE_SOURCE),tests -m pytest
endif
	uv run coverage xml -o results/coverage.xml
	# for backwards compatibility
	# https://github.com/canonical/starflow/blob/3447d302cb7883cbb966ce0ec7e5b3dfd4bb3019/.github/workflows/test-python.yaml#L109
	cp results/coverage.xml coverage.xml
	uv run coverage report -m
	uv run coverage html
