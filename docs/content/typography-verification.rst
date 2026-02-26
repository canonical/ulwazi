:orphan:

.. vale off

Typography Verification
========================

.. vale on

This document verifies that all RST components follow the typography specifications defined in ``_vanilla-settings.scss``:

- **H1**: weight 500, size 2rem (32px), line-height 2.5rem (40px)
- **H2**: weight 300, size 2rem (32px), line-height 2.5rem (40px)
- **H3**: weight 500, size 1.5rem (24px), line-height 2rem (32px)
- **H4**: weight 300, size 1.5rem (24px), line-height 2rem (32px)
- **H5**: weight 600, size 1.125rem (18px), line-height 1.5rem (24px)
- **H6**: weight 400, size 1.125rem (18px), line-height 1.5rem (24px)
- **P**: weight 400, size 0.875rem (14px), line-height 1.25rem (20px)

H1 Heading Level
================

This is paragraph text under H1. Font should be: weight 400, size 0.875rem (14px), line-height 1.25rem (20px).

H2 Heading Level
----------------

This is paragraph text under H2. Font should be: weight 400, size 0.875rem (14px), line-height 1.25rem (20px).

H3 Heading Level
~~~~~~~~~~~~~~~~

This is paragraph text under H3. Font should be: weight 400, size 0.875rem (14px), line-height 1.25rem (20px).

H4 Heading Level
^^^^^^^^^^^^^^^^

This is paragraph text under H4. Font should be: weight 400, size 0.875rem (14px), line-height 1.25rem (20px).

H5 Heading Level
................

This is paragraph text under H5. Font should be: weight 400, size 0.875rem (14px), line-height 1.25rem (20px).

H2 with H2 Variant
------------------

:h2:`This is H2 heading without TOC entry`

This paragraph follows an H2 variant.

Inline Formatting Verification
-------------------------------

Typography should remain consistent with inline formatting:

- :guilabel:`UI element` in paragraph text
- ``code`` in paragraph text
- :file:`file path` in paragraph text
- :command:`command` in paragraph text
- :kbd:`Key` in paragraph text
- *Italic* in paragraph text
- **Bold** in paragraph text

All the above should maintain the base paragraph typography of weight 400, size 0.875rem (14px), line-height 1.25rem (20px).

Code Blocks Typography
----------------------

Code blocks should use monospace font: ``"Ubuntu Mono", Consolas, Monaco, Courier, monospace``

.. code-block:: python

   # Code block example
   def example():
       return "Typography test"

Terminal Block Typography
-------------------------

Terminal blocks should also use monospace font:

.. terminal::
  :user: ubuntu
  :host: test

  make run

Lists Typography
----------------

List items should use paragraph typography (weight 400, size 0.875rem, line-height 1.25rem):

1. First item with paragraph text
2. Second item with paragraph text

   - Nested item A
   - Nested item B

3. Third item with paragraph text

Definition Lists Typography
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Definition lists should maintain proper typography:

Term 1:
  Definition text should use paragraph typography (weight 400, size 0.875rem, line-height 1.25rem).

Term 2:
  Another definition maintaining the same typography.

Table Typography
----------------

Table content should use paragraph typography:

.. list-table::
   :header-rows: 1

   * - Header Column 1
     - Header Column 2
   * - Cell content with paragraph text
     - Cell content with paragraph text
   * - More cell content
     - More cell content

Grid Table Typography
~~~~~~~~~~~~~~~~~~~~~

+----------------------+------------------+
| Header 1             | Header 2         |
+======================+==================+
| Cell content         | Cell content     |
|                      |                  |
| Second paragraph     | in cell          |
+----------------------+------------------+
| More cells           | More content     |
+----------------------+------------------+

Notes and Admonitions Typography
---------------------------------

.. note::
   Note content should use paragraph typography (weight 400, size 0.875rem, line-height 1.25rem).

.. tip::
   Tip content should use paragraph typography (weight 400, size 0.875rem, line-height 1.25rem).

.. important::
   Important content should use paragraph typography (weight 400, size 0.875rem, line-height 1.25rem).

.. caution::
   Caution content should use paragraph typography (weight 400, size 0.875rem, line-height 1.25rem).

Links Typography
----------------

Links should maintain paragraph typography:

- `External link <https://canonical.com/>`_
- :ref:`Internal reference <typography_section>`
- :doc:`Document link <rst-cheat-sheet>`

.. _typography_section:

Tabs Typography
---------------

Tab content should use paragraph typography:

.. tab-set::

    .. tab-item:: Tab 1

        Content in tab 1 with paragraph text maintaining weight 400, size 0.875rem, line-height 1.25rem.

    .. tab-item:: Tab 2

        Content in tab 2 with paragraph text maintaining weight 400, size 0.875rem, line-height 1.25rem.

Glossary Typography
-------------------

.. glossary::

   test term
     Glossary definition should use paragraph typography (weight 400, size 0.875rem, line-height 1.25rem).

   another term
     Another definition maintaining the same typography.

Reference to :term:`test term` in paragraph text.

Multi-level Heading Hierarchy Test
-----------------------------------

H3 Level Test
~~~~~~~~~~~~~

Paragraph under H3.

H4 Level Test
^^^^^^^^^^^^^

Paragraph under H4.

H5 Level Test
.............

Paragraph under H5.

Verification Checklist
----------------------

When reviewing this page in the browser:

1. **Inspect H1** - Should be weight 500, size 32px, line-height 40px
2. **Inspect H2** - Should be weight 300, size 32px, line-height 40px
3. **Inspect H3** - Should be weight 500, size 24px, line-height 32px
4. **Inspect H4** - Should be weight 300, size 24px, line-height 32px
5. **Inspect H5** - Should be weight 600, size 18px, line-height 24px
6. **Inspect H6** - Should be weight 400, size 18px, line-height 24px
7. **Inspect paragraphs** - Should be weight 400, size 14px, line-height 20px
8. **Inspect code blocks** - Should use Ubuntu Mono font family
9. **Inspect inline code** - Should use Ubuntu Mono font family
10. **Inspect all admonitions** - Paragraph text should maintain base typography
11. **Inspect table cells** - Should maintain paragraph typography
12. **Inspect list items** - Should maintain paragraph typography
13. **Inspect definition lists** - Should maintain paragraph typography
14. **Inspect tab content** - Should maintain paragraph typography
