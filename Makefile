PROJECT=ulwazi
UV_TEST_GROUPS := "--group=dev"
UV_LINT_GROUPS := "--group=lint" "--group=types"
UV_DOCS_GROUPS := "--group=docs"

include common.mk

.PHONY: format
format: format-ruff format-codespell format-prettier  ## Run all automatic formatters

.PHONY: lint
lint: lint-ruff lint-codespell lint-mypy lint-prettier lint-pyright lint-shellcheck lint-twine  ## Run all linters

.PHONY: pack
pack: pack-pip  ## Build all packages

.PHONY: publish
publish: publish-pypi  ## Publish packages

.PHONY: publish-pypi
publish-pypi: clean package-pip lint-twine  ## Publish Python packages to pypi
	uv tool run twine upload dist/*

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
install-build-deps: install-lint-build-deps
ifeq ($(APT_PACKAGES),)
else ifeq ($(shell which apt-get),)
	$(warning Cannot install build dependencies without apt.)
	$(warning Please ensure the equivalents to these packages are installed: $(APT_PACKAGES))
else
	sudo $(APT) install $(APT_PACKAGES)
endif

# If additional build dependencies need installing in order to build the linting env.
.PHONY: install-lint-build-deps
install-lint-build-deps:

# Overrides specific to Ulwazi
vanilla-main: install-npm
	npm install
	echo "Compiling SCSS to CSS..."

	@echo "Using local sass..."
	@./node_modules/.bin/sass \
		--load-path=node_modules \
		ulwazi/theme/ulwazi/assets/main.scss \
		ulwazi/theme/ulwazi/static/css/vanilla-main.css

	@echo "SCSS compilation complete!"

.PHONY: product-menu
product-menu:
	@echo "Updating the product menu..."
	python3 ulwazi/product_menu_gen.py

# Override tests to build HTML and PDF output as a prerequisite.
# These should be removed when the docs are built programmatically in the tests.
.PHONY: test
test: docs-html docs-pdf-prep-force docs-pdf
	uv run pytest

.PHONY: test-fast
test-fast: docs-html
	uv run pytest -m 'not slow'

.PHONY: test-slow
test-slow: docs-html docs-pdf-prep-force docs-pdf
	uv run pytest -m 'slow'

.PHONY: test-coverage
test-coverage: docs-html docs-pdf ## Generate coverage report
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

.PHONY: rebuild
rebuild: clean docs
