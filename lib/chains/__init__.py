import pkgutil
import importlib

import cryptocur

import bitcoin_chainkey
import clam
import dash
import litecoin
import mazacoin
import peercoin

not_chainkey_modules = ['cryptocur']
"""These modules should not be loaded as chainkey modules."""

