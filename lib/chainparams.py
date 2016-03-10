"""Chain inspection and switching."""
import imp
import importlib
import pkgutil
from collections import namedtuple

import chains

active_chain = None

ChainParams = namedtuple('ChainParams', ('chain_index', 'coin_name', 'code', 'cls'))
"""Named tuple holding data about a supported blockchain.

Attributes:
    chain_index (int): BIP-0044 chain index of the blockchain. This is just for organization.
    coin_name (str): Full name of the blockchain.
    code (str): Abbreviated name of the blockchain.
    cls: Class that represents the chain.

"""

known_chains = []
known_chain_dict = {}
known_chain_codes = []

subscriptions = []
"""Callbacks for when the active chain changes."""

def init_chains():
    global known_chains, known_chain_dict, known_chain_codes

    for loader, module_name, is_pkg in pkgutil.walk_packages(chains.__path__):
        if module_name in chains.not_chainkey_modules:
            continue

        # For unit tests, the statement in "try:" will throw an error.
        try:
            m = importlib.import_module('.' + module_name, 'encompass.chains')
        except ImportError:
            m = importlib.import_module('.' + module_name, 'chains')
        cls = m.get_class()

        # Assign URI scheme if not specified.
        if not cls.uri_scheme:
            cls.uri_scheme = cls.coin_name.lower()

        params = ChainParams(cls.chain_index, cls.coin_name, cls.code, cls)
        known_chains.append(params)

    known_chain_dict = dict((i.code, i) for i in known_chains)
    known_chain_codes = [i.code for i in known_chains]
    set_active_chain('BTC')

def get_active_chain():
    global active_chain
    return active_chain

def set_active_chain(chaincode):
    global active_chain
    active_chain = get_chain_instance(chaincode)
    for func in subscriptions:
        try:
            func(active_chain)
        except Exception:
            pass

def param(attr, chaincode=None):
    """Get an attribute of a chain."""
    if chaincode is None:
        chain = get_active_chain()
        return getattr(chain, attr)
    return getattr(get_chain_instance(chaincode), attr)

def get_chain_instance(chaincode):
    active_chain = get_active_chain()
    if active_chain and active_chain.code == chaincode:
        return active_chain

    chain = known_chain_dict.get(chaincode)
    if not chain:
        return
    return chain.cls()

def is_known_chain(chaincode):
    return chaincode in known_chain_codes

def subscribe(callback):
    """Subscribe to changes of the active chain.

    Args:
        callback (function): Function that accepts the new
        active chain as an argument.

    Returns:
        Whether or not the subscription was successful.
    """
    if hasattr(callback, '__call__'):
        subscriptions.append(callback)
        return True
    return False

def unsubscribe(callback):
    """Unsubscribe to changes of the active chain."""
    if callback in subscriptions:
        subscriptions.remove(callback)
