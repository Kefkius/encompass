import pkgutil
import importlib

import cryptocur

not_chainkey_modules = ['cryptocur']
"""These modules should not be loaded as chainkey modules."""

