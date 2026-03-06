Usage guide
===========

Ulwazi Sphinx theme is what defines the representation of our documentation content for end users.

Once it's released, it will be available as a Python package.
For now, it can be built manually and used as a file.

Build
*****

To build the theme as a package:

.. code-block:: shell

   make html

After a successful build the Ulwazi Sphinx theme is stored in the
``dist`` directory.
Look for the ``ulwazi-x.tar.gz`` file, where ``x`` is the version.

The Ulwazi Sphinx theme can be later used to build documentation with Sphinx,
both locally or with the ReadtheDocs platform.
Make sure to implement necessary changes to the Sphinx configuration,
including the ``conf.py`` configuration file, which needs to contain required parameters and values.
