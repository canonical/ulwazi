Contribution guide
==================

Thank you for your interest in contributing to the Ulwazi Sphinx theme!
This guide covers the basic workflow for changing the theme, its sample
documentation, and its tests.

If you only want to use Ulwazi in another documentation project, start with
the :doc:`home page <../index>` and the :doc:`configuration reference
<configuration>`.

Before you start
----------------

You need:

- Git and ``make``
- Python 3.10 or later (3.11 is recommended)
- `uv <https://docs.astral.sh/uv/>`_ -- the Make targets install it if it is
  missing
- Node.js and npm only when compiling SCSS -- ``make vanilla-main`` tries to
  install Node.js if ``npm`` is missing

The setup targets may use ``snap``, Homebrew, or the uv installer to install
missing tools. Install them yourself first if you prefer not to grant
``sudo`` access during setup.

Alternatively, use the optional Workshop environment described in the
`README <https://github.com/canonical/ulwazi/blob/main/README.md#optional-workshop-development-environment>`_.

Build and preview
-----------------

Clone the repository and run the commands from its root directory:

.. code-block:: shell

   git clone https://github.com/canonical/ulwazi.git
   cd ulwazi
   make docs

``make docs`` creates the ``.venv`` virtual environment, installs the theme and
documentation dependencies, and builds the sample site with warnings treated
as errors.

To preview the site while you edit it:

.. code-block:: shell

   make run

The preview runs at ``http://127.0.0.1:8000``. To use a different address,
run, for example, ``make run SPHINX_HOST=0.0.0.0 SPHINX_PORT=8080``. Stop the
preview with :kbd:`Ctrl+C` when you finish.

The preview rebuilds after content, theme, and SCSS changes. See
:doc:`preview-workflow` for how it detects them. If shared navigation appears
stale, or after changing dependencies in ``pyproject.toml``, rebuild from
scratch:

.. code-block:: shell

   make rebuild

``make rebuild`` runs ``make clean``, which removes build output and the
``.venv`` virtual environment, and then runs ``make docs``.

Make a change
-------------

Use this table to find the files and checks that usually apply:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Change
     - What to update and check
   * - Python hooks or templates
     - Edit ``ulwazi/`` or ``ulwazi/theme/ulwazi/``. Run ``make test`` and
       inspect the affected pages in ``make run``.
   * - SCSS
     - Edit ``ulwazi/theme/ulwazi/assets/``. The preview compiles changed SCSS;
       run ``make vanilla-main`` to compile it explicitly. Commit
       ``ulwazi/theme/ulwazi/static/css/vanilla-main.css`` and its map.
   * - Rendered markup or theme features
     - Update both :ref:`reST <rst_ref>` and :ref:`MyST <myst-ref>` cheat sheets
       when equivalent syntax exists. Add a test assertion and follow
       :doc:`tests/coverage` to map the feature.
   * - Configuration values
     - Update :doc:`configuration` and, for recommended starter settings,
       ``docs/default-conf.py``. Add a configuration test where possible.
   * - Tests
     - Follow :ref:`the test checklist <test-addition-checklist>` and update the
       :ref:`test inventory <test-inventory>` when collected cases change.
   * - Documentation only
     - Run ``make docs`` and check the changed pages in the preview.

Run checks
----------

Before opening a pull request, run the checks that match your change:

.. code-block:: shell

   make test              # Fast tests; run for every code or docs change
   make lint              # Linters used by CI
   make test-slow         # Browser and PDF tests; needs extra dependencies
   make test-coverage     # Coverage metrics; run after feature mappings change

``make test`` builds the sample HTML first. See the :doc:`test overview
<tests/index>` for every suite, :doc:`tests/code-quality` for linter tool
requirements, and :doc:`tests/coverage` for the three coverage metrics.

Open a pull request
-------------------

Keep each pull request focused, explain the user-visible effect, and list the
checks you ran. Update documentation in the same pull request when you change
behavior or configuration. For visual changes, include before-and-after
screenshots or point reviewers to representative pages in the preview.

Pull requests run automated tests, linters, and the coverage comparison.
Recent pull request titles commonly start with a type such as ``feat:``,
``fix:``, ``test:``, or ``chore:``.

Theme files layout
------------------

The following list contains some of the most important files and folders to focus on
when contributing to this theme:

- ``ulwazi/__init__.py``  -- Theme initialization and core hooks
- ``ulwazi/navigation.py``  -- Manages the global TOC navigation tree
- ``ulwazi/tabs.py``        -- Converts ``sphinx-design`` tabs to Vanilla markup
- ``ulwazi/theme/ulwazi/`` -- Contains all theme files:

  - ``theme.toml``         -- Theme configuration
  - ``assets/``            -- SCSS sources compiled into ``static/css/vanilla-main.css``
  - ``components/`` and ``sections/`` -- Reusable Jinja template fragments
  - ``static/``            -- Static assets (CSS, JS, fonts, images)
  - HTML files             -- Jinja templates used by Sphinx

Other files of interest for development:

- ``ulwazi/product_menu_gen.py`` -- Product menu generation logic
- ``docs/conf.py``                 -- Configuration for this sample site
- ``docs/default-conf.py``         -- Starter configuration for adopters
- ``tests/``                       -- Automated tests for the theme

To modify the HTML of pages generated by Sphinx before the theme templates use
it, see the ``_html_page_context`` function in ``ulwazi/__init__.py``.

To upgrade the Vanilla Framework, follow the
`README upgrade steps <https://github.com/canonical/ulwazi/blob/main/README.md#upgrade-the-vanilla-framework>`_.

Page metadata and SEO
----------------------

**You don't need to add metadata to sample pages.** In this sample site,
every page gets a working ``<title>``, description, Open Graph tags,
canonical link, and favicon from Sphinx, Ulwazi's templates, and the
``sphinxext-opengraph`` settings in ``docs/conf.py``. Another project needs
equivalent extension and ``conf.py`` settings. The table below shows where
each default comes from if you add nothing:

.. list-table::
   :header-rows: 1

   * - Tag
     - Default source
   * - ``<title>``
     - Page heading + site title suffix
   * - ``og:title``
     - Page heading
   * - ``<meta name="description">`` and ``og:description``
     - First ~200 characters of the page's own text (generated
       *independently* for each -- see the description override below)
   * - ``og:image``
     - The ``ogp_image`` setting in ``conf.py``
   * - ``rel="canonical"``, favicon
     - ``html_baseurl`` / ``html_favicon`` in ``conf.py``

Only override these if the defaults don't fit a specific page -- for example,
a landing page you want to promote on social media with custom text.

Overriding Open Graph tags (``og:title``, ``og:description``, ``og:image``)
*****************************************************************************

Add plain ``og:*`` fields at the very start of the file, before the title.
``sphinxext-opengraph`` reads these directly and always renders the correct
``<meta property="og:...">`` form -- no special syntax needed:

.. tab-set::

   .. tab-item:: reST

      .. code-block:: rst

         :og:title: Custom title for social media previews
         :og:description: Custom description for social media previews
         :og:image: https://example.com/preview-image.png

         Page title
         ==========

   .. tab-item:: MyST

      .. code-block:: markdown

         ---
         og:title: "Custom title for social media previews"
         og:description: "Custom description for social media previews"
         og:image: "https://example.com/preview-image.png"
         ---

         # Page title

Overriding the page description
********************************

The plain page description (``<meta name="description">``) is unrelated to
``og:description`` -- setting one does not affect the other. Set it with a
``.. meta::`` directive (reST) or nested under ``myst.html_meta`` (MyST):

.. tab-set::

   .. tab-item:: reST

      .. code-block:: rst

         .. meta::
            :description: A one- or two-sentence summary of this page.

   .. tab-item:: MyST

      .. code-block:: markdown

         ---
         myst:
           html_meta:
             description: "A one- or two-sentence summary of this page."
         ---

See the :ref:`reST cheat sheet <rst_ref>` and :ref:`MyST cheat sheet <myst-ref>`
for full working examples. See the :doc:`Tests documentation <tests/index>` for
how these defaults and overrides are automatically tested.

Further resources
-----------------

- `Ulwazi theme README <https://github.com/canonical/ulwazi/blob/main/README.md>`_
- `Vanilla Design Framework <https://github.com/canonical/vanilla-framework>`_
- `sphinx-basic-ng reference <https://github.com/pradyunsg/sphinx-basic-ng>`_
- `Furo theme <https://pradyunsg.me/furo/>`_ (`source <https://github.com/pradyunsg/furo>`_)

All contributions are welcome: bug reports, feature requests, and pull requests.

.. toctree::
   :hidden:

   syntax-highlighting.md
   roadmap.md
   testing-strategy.md
