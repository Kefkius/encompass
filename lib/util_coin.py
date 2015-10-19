"""Utility functions involving coins."""
import hashlib
from collections import namedtuple

COIN = 100000000

def sha256(x):
    return hashlib.sha256(x).digest()

def Hash(x):
    """SHA256d."""
    if type(x) is unicode: x=x.encode('utf-8')
    return hashlib.sha256( hashlib.sha256(x).digest() ).digest()

def rev_hex(s):
    """Reverses the bytes of a hex string."""
    return s.decode('hex')[::-1].encode('hex')

def int_to_hex(i, length=1):
    """Encodes an integer as a little-endian hex string of the given length."""
    s = hex(i)[2:].rstrip('L')
    s = "0"*(2*length - len(s)) + s
    return rev_hex(s)

def var_int(i):
    # https://en.bitcoin.it/wiki/Protocol_specification#Variable_length_integer
    if i<0xfd:
        return int_to_hex(i)
    elif i<=0xffff:
        return "fd"+int_to_hex(i,2)
    elif i<=0xffffffff:
        return "fe"+int_to_hex(i,4)
    else:
        return "ff"+int_to_hex(i,8)

def op_push(i):
    if i<0x4c:
        return int_to_hex(i)
    elif i<0xff:
        return '4c' + int_to_hex(i)
    elif i<0xffff:
        return '4d' + int_to_hex(i,2)
    else:
        return '4e' + int_to_hex(i,4)

hash_encode = lambda x: x[::-1].encode('hex')
hash_decode = lambda x: x.decode('hex')[::-1]

def bits_to_target(bits):
    """Convert a compact representation to a hex target."""
    MM = 256*256*256
    a = bits%MM
    if a < 0x8000:
        a *= 256
    target = (a) * pow(2, 8 * (bits/MM - 3))
    return target

def target_to_bits(target):
    """Convert a target to compact representation."""
    MM = 256*256*256
    c = ("%064X"%target)[2:]
    i = 31
    while c[0:2]=="00":
        c = c[2:]
        i -= 1

    c = int('0x'+c[0:6],16)
    if c >= 0x800000:
        c /= 256
        i += 1

    new_bits = c + MM * i
    return new_bits

BlockExplorer = namedtuple('BlockExplorer', ('name', 'base_url', 'routes'))
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
        url = ''.join(self.base_url, route)
        return url
