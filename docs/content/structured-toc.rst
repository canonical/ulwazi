.. _structured-toc:

Structured tables of contents
=============================

This page demonstrates the ``sphinx-structured-toc`` extension, which builds
compact, accessible tables of contents with the ``domain`` and ``slice``
directives.

A structured table of contents is *independent* of Sphinx's ``toctree``
(see :doc:`the tests section <tests/index>` for the difference): a
``toctree`` builds the site's page tree, while this extension displays a
thematic table of contents whose context is exposed to screen reader users
through ARIA attributes.

The examples below link to pages in this sample documentation. The same link
text is deliberately repeated in different slices: visually the context is
obvious, and thanks to the ARIA attributes a screen reader announces the
accessible name (for example, *Reference, Models, Model layer*) instead of
just the visible text.

Domain named after a section heading
------------------------------------

When the ``domain`` directive has no argument, its name is derived from the
nearest enclosing section heading:

.. domain::

   .. slice:: Content

      :doc:`Home <../index>`
      :doc:`Contribution guide <contribute>`

   .. slice:: Tests

      :doc:`Test content <test>`
      :doc:`Tests overview <tests/index>`

Explicit domain name
--------------------

A ``domain`` can also take an explicit name, which overrides the section
heading. Items can carry the trailing ``slice`` and ``domain`` keywords to
have the slice and domain names added to their accessible names:

.. domain:: Ulwazi sample documentation
   :suppress-warnings:

   .. slice:: Reference

      :doc:`RST cheat sheet <rst-cheat-sheet>` slice
      :doc:`MyST cheat sheet <myst-cheat-sheet>` slice

   .. slice:: Meta

      :doc:`Testing strategy <testing-strategy>` domain
      :doc:`Roadmap <roadmap>` domain

.. note::

   The ``:suppress-warnings:`` flag silences the extension's ambiguity
   warnings for every item in the domain. It is used here because the sample
   pages above are not part of any ``toctree``, which would otherwise make
   the build fail on warnings.

The MyST version of this page is available at
:doc:`structured-toc-myst`.
