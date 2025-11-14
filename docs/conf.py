# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------
# Make the project importable by Sphinx (important for autodoc)

import os
import sys

# Adjust depending on your project structure:
# Here we assume:
#   AeroMAPS/
#     aeromaps/    <-- your package
#     docs/

sys.path.insert(0, os.path.abspath(".."))


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "AeroMAPS"
copyright = "2025, AeroMAPS Research Team"
author = "AeroMAPS Research Team"
release = "v0.9.0-beta"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# Autosummary: generate stub files automatically
autosummary_generate = True

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
]

napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_private_with_doc = False
napoleon_use_param = True
napoleon_use_rtype = True

# Render `None` as “None” instead of type NoneType
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}

# Show type hints in the description, not in the function signature
set_type_checking_flag = True
typehints_fully_qualified = False


templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# Use the Read the Docs theme (cleaner and more standard for Sphinx projects)
html_theme = "sphinx_rtd_theme"

html_static_path = ["_static"]
