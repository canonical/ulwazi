PROJECT=ulwazi
UV_TEST_GROUPS := "--group=dev"
UV_LINT_GROUPS := "--group=lint" "--group=types"

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

.PHONY: product-menu
product-menu:
	@echo "Updating the product menu..."
	python3 ulwazi/product_menu_gen.py

.PHONY: npm-install
npm-install:
	@command -v npm >/dev/null 2>&1 || { echo >&2 "Error: 'npm' not found. Please install it."; exit 1; }
	@npm install

.PHONY: vanilla-main
vanilla-main: npm-install
	@./node_modules/.bin/sass \
		--load-path=node_modules \
		ulwazi/theme/ulwazi/assets/main.scss \
		ulwazi/theme/ulwazi/static/css/vanilla-main.css

.PHONY: test
test: vanilla-main
	uv run pytest
