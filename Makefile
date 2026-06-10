PROJECT=starcraft
# Define when more than the main package tree requires coverage
# like is the case for snapcraft (snapcraft and snapcraft_legacy):
# COVERAGE_SOURCE="starcraft"
UV_TEST_GROUPS := "--group=dev"
UV_DOCS_GROUPS := "--group=docs"
UV_LINT_GROUPS := "--group=lint" "--group=types" $(UV_DOCS_GROUPS)
UV_TICS_GROUPS := "--group=tics"

# If you have dev dependencies that depend on your distro version, uncomment these:
# ifneq ($(wildcard /etc/os-release),)
# include /etc/os-release
# endif
# ifdef VERSION_CODENAME
# UV_TEST_GROUPS += "--group=dev-$(VERSION_CODENAME)"
# UV_DOCS_GROUPS += "--group=dev-$(VERSION_CODENAME)"
# UV_LINT_GROUPS += "--group=dev-$(VERSION_CODENAME)"
# UV_TICS_GROUPS += "--group=dev-$(VERSION_CODENAME)"
# endif

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
install-build-deps: install-lint-build-deps
ifeq ($(APT_PACKAGES),)
else ifeq ($(shell which apt-get),)
	$(warning Cannot install build dependencies without apt.)
	$(warning Please ensure the equivalents to these packages are installed: $(APT_PACKAGES))
else
	sudo $(APT) install $(APT_PACKAGES)
endif

vanilla-main: npm-install
	echo "Compiling SCSS to CSS..."

	@echo "Using local sass..."
	@./node_modules/.bin/sass \
		--load-path=node_modules \
		ulwazi/theme/ulwazi/assets/main.scss \
		ulwazi/theme/ulwazi/static/css/vanilla-main.css

	@echo "SCSS compilation complete!"

rebuild: docs-clean docs-run

product-menu:
	@echo "Updating the product menu..."
	python3 ulwazi/product_menu_gen.py
