'''Chain-specific Dash code'''
from cryptocur import *
import os

import coinhash

def get_class():
    return Dash

class Dash(CryptoCur):
    PoW = False
    chain_index = 5
    coin_name = 'Dash'
    code = 'DASH'
    p2pkh_version = 76
    p2sh_version = 16
    wif_version = 204
    ext_pub_version = '02fe52f8'
    ext_priv_version = '02fe52cc'
    message_magic = 'DarkCoin Signed Message:\n'

    DUST_THRESHOLD = 5430
    MIN_RELAY_TX_FEE = 1000
    RECOMMENDED_FEE = 50000
    COINBASE_MATURITY = 100

    header_hash = coinhash.X11Hash

    block_explorers = [
        ('CryptoID', 'https://chainz.cryptoid.info/dash',
                    {'tx': '/tx.dws?%', 'addr': '/address.dws?%'}),
        ('CoinPlorer', 'https://coinplorer.com/DRK',
                    {'tx': '/Transactions/%', 'addr': '/Addresses/%'})
    ]

    base_units = {
        'DASH': 8,
        'mDASH': 5,
        'uDASH': 2,
    }

    chunk_size = 2016

    # Network
    DEFAULT_PORTS = {'t':'50001', 's':'50002', 'h':'8081', 'g':'8082'}

    DEFAULT_SERVERS = {
        'electrum.darkcointalk.org':DEFAULT_PORTS, # propulsion
        'drk1.electrum-servers.us':DEFAULT_PORTS,  # elm4ever
        'electrum.drk.siampm.com':DEFAULT_PORTS,   # thelazier
        'electrum-drk.club':DEFAULT_PORTS,         # duffman
    }

