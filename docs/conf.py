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
    'product_menu_enabled': True,  # Enable Product menu
}

html_favicon = '_static/favicon.png'

# import product_menu as p_menu

# p_menu.save2file(p_menu.get_nav_menu(p_menu.fetch_and_parse(p_menu.PRODUCT_MENU_PARSING_URL)))

# def update_product_menu():
#     """Fetches, parses, and saves the product navigation menu."""
#     try:
#         # Fetch a page with the menu from the URL
#         raw_page= p_menu.fetch_and_parse(p_menu.PRODUCT_MENU_PARSING_URL)

#         # Crop the menu
#         nav_menu = p_menu.get_nav_menu(raw_page)

#         # Save it to a file
#         p_menu.save2file(nav_menu)

#         print("Product menu updated successfully.")

#     except Exception as e:
#         print(f"Failed to update product menu: {e}")

# # Execute the update
# update_product_menu()
