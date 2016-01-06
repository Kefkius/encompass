'''Chain-specific Viacoin code'''

############################################
# Code here is taken from Vialectrum       #
# https://github.com/vialectrum/vialectrum #
############################################

from cryptocur import *
import os

from coinhash import SHA256dHash, ScryptHash

def get_class():
    return Viacoin

class Viacoin(CryptoCur):
    PoW = False
    chain_index = 14
    coin_name='Viacoin'
    code = 'VIA'
    p2pkh_version = 71
    p2sh_version = 33
    wif_version = 199
    ext_pub_version = '0488b21e'
    ext_priv_version = '0488ade4'
    message_magic = 'Viacoin Signed Message:\n'

    DUST_THRESHOLD = 0
    MIN_RELAY_TX_FEE = 100000
    RECOMMENDED_FEE = MIN_RELAY_TX_FEE
    COINBASE_MATURITY = 3600

    block_explorers = [
        ('bchain.info', 'https://bchain.info/VIA',
                    {'tx': '/tx/%', 'addr': '/addr/%'})
    ]

    base_units = {
        'VIA': 8,
        'mVIA': 5,
        'bits': 2
    }

    chunk_size = 2016

    headers_url = 'http://headers.vialectrum.org/blockchain_headers'

    DEFAULT_PORTS = {'t':'50001', 's':'50002', 'h':'8081', 'g':'8082'}

    DEFAULT_SERVERS = {
        'server.vialectrum.org': DEFAULT_PORTS,
        'vialectrum.viacoin.net': DEFAULT_PORTS,
    }

