"""Utility functions involving coins."""
import hashlib
from collections import namedtuple

import chainparams
from chains import cryptocur

COIN = 100000000

def sha256(x):
    return hashlib.sha256(x).digest()

def Hash(x):
    """SHA256d."""
    if type(x) is unicode: x=x.encode('utf-8')
    return hashlib.sha256( hashlib.sha256(x).digest() ).digest()


hash_encode = lambda x: cryptocur.hash_encode(x)
hash_decode = lambda x: cryptocur.hash_decode(x)
rev_hex = lambda s: cryptocur.rev_hex(s)
int_to_hex = lambda i, length=1: cryptocur.int_to_hex(i, length)
var_int = lambda i: cryptocur.var_int(i)
op_push = lambda i: cryptocur.op_push(i)
bits_to_target = lambda bits: cryptocur.bits_to_target(bits)
target_to_bits = lambda target: cryptocur.target_to_bits(target)


class BlockExplorer(object):
    """Block explorer.

    Attributes:
        name (str): Identifying string.
        base_url (str): Base URL for retrieving data.
        routes (dict): Dict of routes for retrieving data.
            The string '%' will be replaced by the item (e.g. tx hash).
    """
    def __init__(self, name='', base_url='', routes=None):
        if routes is None: routes = {}
        self.name = name
        self.base_url = base_url
        self.routes = routes

    def get_url(self, kind, item):
        """Construct URL retrieving data.

        Args:
            kind (str): Kind of data (e.g. 'tx').
            item (str): Identifier (e.g. tx hash).
        """
        if not self.routes.get(kind): return
        route = self.routes[kind].replace('%', item)
        url = ''.join([self.base_url, route])
        return url

    def serialize(self):
        return (self.name, self.base_url, self.routes)

def block_explorer(config):
    options = config.get_above_chain(config.get_active_chain_code())
    name = options.get('block_explorer', chainparams.param('block_explorers')[0][0])
    return name

def block_explorer_info():
    explorers = [BlockExplorer(*i) for i in chainparams.param('block_explorers')]
    return dict((i.name, i) for i in explorers)

def block_explorer_instance(config):
    return block_explorer_info().get(block_explorer(config))

def block_explorer_URL(config, kind, item):
    be = block_explorer_instance(config)
    if not be:
        return

    return be.get_url(kind, item)

