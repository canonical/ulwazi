Typography verification
========================

This is paragraph text under H1. Font should be: weight 400, size 0.875rem (14px), line-height 1.25rem (20px).

Testing Setup
-------------

**Important**: This typography verification should be tested at 1K screen resolution (1920x1080 pixels).

To set your browser viewport to 1K resolution using Developer Tools:

**Chrome**:

1. Press ``F12`` or ``Ctrl+Shift+I`` (``Cmd+Option+I`` on Mac) to open DevTools
2. Click the **Toggle device toolbar** icon (or press ``Ctrl+Shift+M`` / ``Cmd+Shift+M``)
3. In the device toolbar, select **Responsive** from the dropdown
4. Set dimensions to **1920 x 1080**
5. Ensure zoom is set to **100%**

**Firefox**:

1. Press ``F12`` or ``Ctrl+Shift+I`` (``Cmd+Option+I`` on Mac) to open DevTools
2. Click the **Responsive Design Mode** icon (or press ``Ctrl+Shift+M`` / ``Cmd+Option+M``)
3. Set dimensions to **1920 x 1080**
4. Ensure zoom is set to **100%**


Typography Specifications
--------------------------

This document verifies that all RST components follow the typography specifications defined in ``_vanilla-settings.scss``:

- **H1**: weight 500, size 2rem (32px), line-height 2.5rem (40px)
- **H2**: weight 300, size 2rem (32px), line-height 2.5rem (40px)
- **H3**: weight 500, size 1.5rem (24px), line-height 2rem (32px)
- **H4**: weight 300, size 1.5rem (24px), line-height 2rem (32px)
- **H5**: weight 600, size 1.125rem (18px), line-height 1.5rem (24px)
- **H6**: weight 400, size 1.125rem (18px), line-height 1.5rem (24px)
- **P**: weight 400, size 0.875rem (14px), line-height 1.25rem (20px)


H2 Heading Level
----------------

This is paragraph text under H2. Font should be: weight 300, size 2rem (32px), line-height 2.5rem (40px).

H3 Heading Level
~~~~~~~~~~~~~~~~

This is paragraph text under H3. Font should be: weight 500, size 1.5rem (24px), line-height 2rem (32px).

H4 Heading Level
^^^^^^^^^^^^^^^^

This is paragraph text under H4. Font should be: weight 300, size 1.5rem (24px), line-height 2rem (32px).

H5 Heading Level
................

This is paragraph text under H5. Font should be: weight 600, size 1.125rem (18px), line-height 1.5rem (24px).


Inline Formatting Verification
-------------------------------

Typography should remain consistent with inline formatting:

- :guilabel:`UI element` in paragraph text
- ``code`` in paragraph text
- :file:`file path` in paragraph text
- :command:`sudo apt update` in paragraph text
- :kbd:`Ctrl+C` in paragraph text
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

.. raw:: html

   <ul style="list-style-type: none; padding-left: 0;">
     <li><input type="checkbox"> <strong>Inspect H1</strong> - Should be weight 500, size 32px, line-height 40px</li>
     <li><input type="checkbox"> <strong>Inspect H2</strong> - Should be weight 300, size 32px, line-height 40px</li>
     <li><input type="checkbox"> <strong>Inspect H3</strong> - Should be weight 500, size 24px, line-height 32px</li>
     <li><input type="checkbox"> <strong>Inspect H4</strong> - Should be weight 300, size 24px, line-height 32px</li>
     <li><input type="checkbox"> <strong>Inspect H5</strong> - Should be weight 600, size 18px, line-height 24px</li>
     <li><input type="checkbox"> <strong>Inspect H6</strong> - Should be weight 400, size 18px, line-height 24px</li>
     <li><input type="checkbox"> <strong>Inspect paragraphs</strong> - Should be weight 400, size 14px, line-height 20px</li>
     <li><input type="checkbox"> <strong>Inspect code blocks</strong> - Should use Ubuntu Mono font family</li>
     <li><input type="checkbox"> <strong>Inspect inline code</strong> - Should use Ubuntu Mono font family</li>
     <li><input type="checkbox"> <strong>Inspect all admonitions</strong> - Paragraph text should maintain base typography</li>
     <li><input type="checkbox"> <strong>Inspect table cells</strong> - Should maintain paragraph typography</li>
     <li><input type="checkbox"> <strong>Inspect list items</strong> - Should maintain paragraph typography</li>
     <li><input type="checkbox"> <strong>Inspect definition lists</strong> - Should maintain paragraph typography</li>
     <li><input type="checkbox"> <strong>Inspect tab content</strong> - Should maintain paragraph typography</li>
   </ul>
