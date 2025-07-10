# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Test'
copyright = '2024'
author = 'Canonical'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "ulwazi",
    "myst_parser"
]

myst_enable_extensions = [
    "colon_fence"
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "ulwazi"
html_static_path = ['_static']


# -- Theme customisation  ----------------------------------------------------

html_context = {
    'company': 'Canonical',
    'link1_URL': 'https://snapcraft.io/',
    'link1_name': 'Snapcraft',
}

html_favicon = '_static/favicon.png'

rst_prolog = """
.. role:: center
   :class: align-center
.. role:: h2
    :class: hclass2
.. role:: woke-ignore
    :class: woke-ignore
.. role:: vale-ignore
    :class: vale-ignore
"""
