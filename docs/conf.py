import os
import sys

sys.path.insert(0, os.path.abspath('../sdks/python-sdk/src'))
sys.path.insert(0, os.path.abspath('../sdks/agent-sdk/src'))

project = 'xmtp-py'
author = 'XMTP Python Contributors'
release = '0.0.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx_autodoc_typehints',
]

autosummary_generate = True

autodoc_typehints = 'description'
napoleon_google_docstring = True
napoleon_numpy_docstring = False

templates_path = ['_templates']
exclude_patterns = ['_build']

html_theme = 'alabaster'
