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

def init_chains():
    global known_chains, known_chain_dict, known_chain_codes

    for loader, module_name, is_pkg in pkgutil.walk_packages(chains.__path__):
        if module_name in chains.not_chainkey_modules:
            continue

        m = importlib.import_module('.' + module_name, 'encompass.chains')
        cls = m.get_class()
        params = ChainParams(cls.chain_index, cls.coin_name, cls.code, cls)
        known_chains.append(params)

    known_chain_dict = dict((i.code, i) for i in known_chains)
    known_chain_codes = [i.code for i in known_chains]

def get_active_chain():
    global active_chain
    return active_chain

def set_active_chain(chaincode):
    global active_chain
    active_chain = get_chain_instance(chaincode)


def get_chain_instance(chaincode):
    chain = known_chain_dict.get(chaincode)
    if not chain:
        return
    return chain.cls()

def is_known_chain(chaincode):
    return chaincode in known_chain_codes
