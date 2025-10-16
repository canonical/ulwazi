:orphan:
.. |br| raw:: html
  
   <br />

.. vale off

.. _cheat-sheet:

ReStructuredText cheat sheet
============================

.. vale on

This file contains the syntax for commonly used reST markup.
Open it in your text editor to quickly copy and paste the markup you need.

.. See the :ref:`reStructuredText style guide <style-guide>` for detailed information and conventions.

Also see the `Sphinx reStructuredText Primer <https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html>`_ for more details on reST, and the `Canonical Documentation Style Guide <https://docs.ubuntu.com/styleguide/en>`_ for general style conventions.

H2 heading
----------

:h2:`H2 heading without TOC entry`

H3 heading
~~~~~~~~~~

H4 heading
^^^^^^^^^^

H5 heading
..........

Inline formatting
-----------------

- :guilabel:`UI element`
- ``code``
- :file:`file path`
- :command:`command`
- :kbd:`Key`
- *Italic*
- **Bold**

Code blocks
-----------

Start a code block::

     code:
       - example: true

.. code:: text

     # Demonstrate a code block
     code:
       - example: true

.. code-block:: yaml

     # Demonstrate a code block
     code:
       - example: true

Syntax highlighting
~~~~~~~~~~~~~~~~~~~

YAML:

.. code-block:: yaml

   # Required
   version: 2

   # Set the version of Python and other tools you might need
   build:
     os: ubuntu-22.04
     tools:
       python: "3.11"
     jobs:
       post_create_environment:
       - pip install sphinx build
       - python -m build
       - pip install dist/ulwazi-0.1.tar.gz
       post_checkout:
       - git fetch --unshallow || true

   # Build documentation in the docs/ directory with Sphinx
   sphinx:
     builder: dirhtml
     configuration: docs/conf.py
     fail_on_warning: true

   # If using Sphinx, optionally build your docs in additional formats such as PDF
   formats:
   - pdf

   # Optionally declare the Python requirements required to build your docs
   python:
     install:
     - requirements: requirements.txt

Shell:

.. code-block:: shell

   # Create and activate a virtual environment
   python3 -m venv .venv && source .venv/bin/activate

   # Install Sphinx and the RTD theme
   pip install sphinx sphinx-rtd-theme

   # Build HTML docs from the "docs" folder
   sphinx-build -b html docs/ _build/html

Python:

.. code-block:: python

   import datetime
   import os
   import yaml

   copyright = "%s CC-BY-SA, %s" % (datetime.date.today().year, author)

   if "READTHEDOCS_VERSION" in os.environ:
       version = os.environ["READTHEDOCS_VERSION"]
       sitemap_url_scheme = "{version}{link}"
   else:
       sitemap_url_scheme = "MANUAL/{link}"

   if os.path.exists("./reuse/substitutions.yaml"):
       with open("./reuse/substitutions.yaml", "r") as fd:
           myst_substitutions = yaml.safe_load(fd.read())

.. _a_section_target:

Links
-----

- `Canonical website <https://canonical.com/>`_
- `Canonical website`_ (defined in ``reuse/links.txt`` or at the bottom of the page)
- https:\ //canonical.com/
- :ref:`a_section_target`
- :ref:`Link text <a_section_target>`
- :doc:`../../index`
- :doc:`Link text <../../index>`


Navigation
----------

Use the following syntax::

  .. toctree::
     :hidden:

     sub-page1
     sub-page2


Lists
-----

1. Step 1

   - Item 1

     * Sub-item
   - Item 2

     i. Sub-step 1
     #. Sub-step 2
#. Step 2

   a. Sub-step 1

      - Item
   #. Sub-step 2

Term 1:
  Definition
Term 2:
  Definition

Tables
------

rST supports four table implementations: grid, list, CSV, and simple. Grid and simple tables can also use 
the table directive or the  rst-class directive to provide more options.

Grid tables
~~~~~~~~~~~

Small grid table, default aligned (no alignment options):

+------------------------------------+----------+
| Header 1                           | Header 2 |
+====================================+==========+
| [1,1] |br| Second paragraph        |  [1,2]   |
+------------------------------------+----------+
| [2,1]                              |  [2,2]   |
+------------------------------------+----------+

Wide grid table, default aligned (no alignment options):

+----------------------+------------+---------------+-----------+------------+-------------+-----------+-----------+------------+
| Header 1             | Header 2   |     Header 3  | Header 4  | Header 5   | Header 6    | Header 7  | Header 8  | Header 9   |
+======================+============+===============+===========+============+=============+===========+===========+============+
| [1,1]                | [1,2]      |   [1,3]       | [1,4]     | [1,5]      | [1,6]       | [1,7]     | [1,8]     | [1,9]      |
|                      |            |               |           |            |             |           |           |            |
| Second paragraph     |            |               |           |            |             |           |           |            |
+----------------------+------------+---------------+-----------+------------+-------------+-----------+-----------+------------+
| [2,1]                | [2,2]      |   [2,3]       | [2,4]     | [2,5]      | [2,6]       | [2,7]     | [2,8]     | [2,9]      |
+----------------------+------------+---------------+-----------+------------+-------------+-----------+-----------+------------+

Grid table with table directive, default aligned:

.. table::

  +----------------------+------------------+
  | Header 1             | Header 2         |
  +======================+==================+
  | [1,1]                | [1,2]            |
  |                      |                  |
  | Second paragraph     |                  |
  +----------------------+------------------+
  | [2,1]                | [2,2]            |
  +----------------------+------------------+

Grid table with table directive, right aligned:

.. table::
  :align: right

  +----------------------+------------------+
  | Header 1             | Header 2         |
  +======================+==================+
  | [1,1]                | [1,2]            |
  |                      |                  |
  | Second paragraph     |                  |
  +----------------------+------------------+
  | [2,1]                | [2,2]            |
  +----------------------+------------------+

Grid table with rst-class directive, default aligned:

.. rst-class:: align-default

  +----------------------+------------------+
  | Header 1             | Header 2         |
  +======================+==================+
  | [1,1]                | [1,2]            |
  |                      |                  |
  | Second paragraph     |                  |
  +----------------------+------------------+
  | [2,1]                | [2,2]            |
  +----------------------+------------------+

Grid table with rst-class directive, right aligned:

.. rst-class:: align-right

  +----------------------+------------------+
  | Header 1             | Header 2         |
  +======================+==================+
  | [1,1]                | [1,2]            |
  |                      |                  |
  | Second paragraph     |                  |
  +----------------------+------------------+
  | [2,1]                | [2,2]            |
  +----------------------+------------------+


List tables
~~~~~~~~~~~

List table, default aligned:

.. list-table::
   :header-rows: 1

   * - Header 1
     - Header 2
   * - [1,1]

       Second paragraph
     - [1,2]
   * - [2,1]
     - [2,2]

List table, right aligned:

.. list-table::
   :header-rows: 1
   :align: right

   * - Header 1
     - Header 2
   * - [1,1]

       Second paragraph
     - [1,2]
   * - [2,1]
     - [2,2]

CSV tables
~~~~~~~~~~
     
CSV table, default aligned:

.. csv-table::
  :header: "Header 1", "Header 2"
  :widths: 15, 15

  "[1,1]", "[1,2]"
  "[2,1]", "[2,2]"

CSV table, right aligned:

.. csv-table::
  :header: "Header 1", "Header 2"
  :widths: 15, 15
  :align: right

  "[1,1]", "[1,2]"
  "[2,1]", "[2,2]"

Simple tables
~~~~~~~~~~~~~

Simple table, default aligned (no alignment options):

======== ========
Header 1 Header 2
======== ========
[1,1]    [1,2]   
[1,2]    [2,2] 
======== ========

Simple with table directive, default aligned:

.. table::
  :widths: auto

  ======== ========
  Header 1 Header 2
  ======== ========
  [1,1]    [1,2]   
  [1,2]    [2,2] 
  ======== ========

Simple with table directive, right aligned:

.. table::
  :widths: auto
  :align: right

  ======== ========
  Header 1 Header 2
  ======== ========
  [1,1]    [1,2]   
  [1,2]    [2,2] 
  ======== ========

Simple table with rst-class directive, default aligned:

.. rst-class:: align-default
  
  ======== ========
  Header 1 Header 2
  ======== ========
  [1,1]    [1,2]   
  [1,2]    [2,2] 
  ======== ========

Simple table with rst-class directive, right aligned:

.. rst-class:: align-right
  
  ======== ========
  Header 1 Header 2
  ======== ========
  [1,1]    [1,2]   
  [1,2]    [2,2] 
  ======== ========


Notes
-----

.. note::
   A note.

.. tip::
   A tip.

.. important::
   Important information

.. caution::
   This might damage your hardware!

Images
------
Use ``.. image::`` for simple images without captions.

.. image:: https://assets.ubuntu.com/v1/b3b72cb2-canonical-logo-166.png

Use ``.. figure::`` to include a caption, and to reference the image in text.

.. figure:: https://assets.ubuntu.com/v1/b3b72cb2-canonical-logo-166.png
   :width: 100px
   :alt: Alt text

   Figure caption

Images can be inserted in-line |logo| via a substitution. 

.. |logo| image:: https://assets.ubuntu.com/v1/b3b72cb2-canonical-logo-166.png
   :width: 16px


Reuse
-----

.. |reuse_key| replace:: This is **included** text.

|reuse_key|

.. include:: include.txt
   :start-after: [include_start]
   :end-before: [include_end]

.. Tabs
.. ----

.. .. tab-set::

..    .. tab-item:: Tab 1

..       Content Tab 1

..    .. tab-item:: Tab 2

..       Content Tab 2


Glossary
--------

.. glossary::

   example term
     Definition of the example term.

:term:`example term`

More useful markup
------------------

- .. versionadded:: X.Y
- | Line 1
  | Line 2
  | Line 3
- .. This is a comment
- :abbr:`API (Application Programming Interface)`

----

.. Custom extensions
.. -----------------

.. Related links at the top of the page::

..   :relatedlinks: https://github.com/canonical/lxd-sphinx-extensions, [RTFM](https://www.google.com)
..   :discourse: 12345

.. Terms that should not be checked by the spelling checker: :spellexception:`PurposelyWrong`

.. A single-line terminal view that separates input from output:

.. .. terminal::
..    :input: command
..    :user: root
..    :host: vampyr
..    :dir: /home/user/directory/

..    the output

.. A multi-line version of the same:

.. .. terminal::
..    :user: root
..    :host: vampyr
..    :dir: /home/user/directory/

..    :input: command 1
..    output 1
..    :input: command 2
..    output 2

.. A link to a YouTube video:

.. .. youtube:: https://www.youtube.com/watch?v=iMLiK1fX4I0
..           :title: Demo



.. LINKS
.. _Canonical website: https://canonical.com/