'''Chain-specific Peercoin code'''
from cryptocur import *
import os
import time

def get_class():
    return Peercoin

class Peercoin(CryptoCur):
    PoW = False
    chain_index = 6
    coin_name = 'Peercoin'
    code = 'PPC'
    p2pkh_version = 55
    p2sh_version = 117
    wif_version = 128
    ext_pub_version = '0488b21e'
    ext_priv_version = '0488ade4'
    message_magic = 'PPCoin Signed Message:\n'

    DUST_THRESHOLD = 5430
    MIN_RELAY_TX_FEE = 10000
    RECOMMENDED_FEE = 50000
    COINBASE_MATURITY = 500

    block_explorers = [
        ('PeercoinExplorer.info', 'https://peercoinexplorer.info',
                    {'tx': '/tx/%', 'addr': '/address/%'})
    ]

    base_units = {
        'HPPC': 8,
        'PPC': 6,
        'mPPC': 3
    }

    chunk_size = 2016

    # Network
    DEFAULT_PORTS = {'t':'5004', 's':'5004', 'h':'8081', 'g':'8082'}

    DEFAULT_SERVERS = {
        'ppc-cce-1.coinomi.net':DEFAULT_PORTS
    }

    def deserialize_tx_fields(self, vds, fields, d):
        timestamp = ('timestamp', vds.read_int32)
        fields.insert(1, timestamp)

    def serialize_tx_fields(self, tx, for_sig, fields):
        unix_time = getattr(tx, 'timestamp', None)
        if unix_time is None:
            unix_time = int(time.time())
        timestamp = ('timestamp', [int_to_hex(unix_time, 4)])
        fields.insert(1, timestamp)

