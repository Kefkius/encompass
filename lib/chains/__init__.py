import pkgutil
import importlib

import cryptocur

import bitcoin_chainkey
import blackcoin
import clam
import dash
import dogecoin
import feathercoin
import litecoin
import mazacoin
import namecoin
import peercoin
import startcoin
import viacoin

not_chainkey_modules = ['cryptocur']
"""These modules should not be loaded as chainkey modules."""

