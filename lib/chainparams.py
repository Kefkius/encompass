from collections import namedtuple
from util import print_error
import importlib
import traceback, sys
import chains
import chains.cryptocur

active_chain = None

ChainParams = namedtuple('ChainParams', ('chain_index', 'coin_name', 'code', 'module_name'))
"""Named tuple holding data about a supported blockchain.

Attributes:
    chain_index (int): BIP-0044 chain index of the blockchain. This is just for organization.
    coin_name (str): Full name of the blockchain.
    code (str): Abbreviated name of the blockchain.
    module_name (str): Name of the module in lib/chains/ where the relevant class is defined.

"""

_known_chains = (
    # Bitcoin
    ChainParams(0, 'Bitcoin', 'BTC', 'bitcoin'),

    # Litecoin
    ChainParams(2, 'Litecoin', 'LTC', 'litecoin'),

    # Dogecoin
    ChainParams(3, 'Dogecoin', 'DOGE', 'dogecoin'),

    # Dash
    ChainParams(5, 'Dash', 'DASH', 'dash'),

    # Peercoin
    ChainParams(6, 'Peercoin', 'PPC', 'peercoin'),

    # Feathercoin
    ChainParams(8, 'Feathercoin', 'FTC', 'feathercoin'),

    # Blackcoin
    ChainParams(10, 'Blackcoin', 'BLK', 'blackcoin'),
    
    # Mazacoin
    ChainParams(13, 'Mazacoin', 'MZC', 'mazacoin'),

    # Viacoin
    ChainParams(14, 'Viacoin', 'VIA', 'viacoin'),

    # Digibyte
    ChainParams(20, 'Digibyte', 'DGB', 'digibyte'),
)

_known_chain_dict = dict((i.code, i) for i in _known_chains)

_known_chain_codes = [i.code for i in _known_chains]

def get_active_chain():
    global active_chain
    return active_chain

def set_active_chain(chaincode):
    global active_chain
    active_chain = get_chain_instance(chaincode)

def is_known_chain(code):
    code = code.upper()
    if code in _known_chain_codes:
        return True
    return False

def get_params(code):
    code = code.upper()
    if code in _known_chain_codes:
        return _known_chain_dict[code]
    return None

def get_chainparam(code, property):
    code = code.upper()
    chain = _known_chain_dict.get(code)
    if chain:
        return getattr(chain, property)
    return None

def get_chain_index(code):
    return get_chainparam(code, 'chain_index')

def get_code_from_index(index):
    for chain in _known_chains:
        if chain.chain_index == index:
            return chain.code
    return None

def get_server_trust(code):
    instance = get_chain_instance(code)
    if instance is None: return None
    # Proof of work
    is_pow = instance.PoW
    # servers used
    servers = len(instance.DEFAULT_SERVERS)
    # criterion -> [value, info]
    return {
        'pow': is_pow,
        'servers': servers,
    }

def get_chain_instance(code):
    """Gets an instance of the given chain's class.

    Args:
        code (str): ChainParams code of the blockchain.

    Returns:
        An instance of the blockchain's class. All blockchain
        classes derive from CryptoCur, the base class defined
        in lib/chains/cryptocur.py

    """
    code = code.upper()
    if not is_known_chain(code): return None
    params = get_params(code)
    module_name = params.module_name
    # If importing fails, try with a different path.
    try:
        classmodule = importlib.import_module(''.join(['chainkey.chains.', module_name]))
        classInst = getattr(classmodule, 'Currency')
    except (AttributeError, ImportError):
        classmodule = importlib.import_module(''.join(['lib.chains.', module_name]))
    classInst = getattr(classmodule, 'Currency')
    return classInst()

def run_chainhook(name, *args):
    """Runs any chainhooks that the active chain has."""
    results = []
    f_list = chains.cryptocur.chainhooks.get(name,[])
    active_chain = get_active_chain()
    # if the chain's class matches the active chain's class, call the hook
    for cls in f_list:
        if not cls == active_chain.__class__:
            continue
        try:
            f = getattr(active_chain, name)
            r = f(*args)
        except Exception:
            print_error("Chainhook error")
            traceback.print_exc(file=sys.stdout)
            r = False
        if r:
            results.append(r)

    if results:
        assert len(results) == 1, results
        return results[0]
