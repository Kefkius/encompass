'''Chain-specific Blackcoin code'''
from cryptocur import *
import os
import time

from coinhash import SHA256dHash, ScryptHash

def get_class():
    return Blackcoin

class Blackcoin(CryptoCur):
    PoW = False
    chain_index = 10
    coin_name = 'Blackcoin'
    code = 'BLK'
    p2pkh_version = 25
    p2sh_version = 85
    wif_version = 153
    ext_pub_version = '0488b21e'
    ext_priv_version = '0488ade4'
    message_magic = 'BlackCoin Signed Message:\n'

    DUST_THRESHOLD = 5430
    MIN_RELAY_TX_FEE = 10000
    RECOMMENDED_FEE = 50000
    COINBASE_MATURITY = 500

    block_explorers = [
        ('Coinplorer.com', 'https://coinplorer.com/BC',
                    {'tx': '/Transactions/%', 'addr': '/Addresses/%'}),
        ('Bchain.info', 'https://bchain.info/BC',
                    {'tx': '/tx/%', 'addr': '/addr/%'})
    ]

    chunk_size = 2016

    # Network
    DEFAULT_PORTS = {'t':'50001', 's':'50002', 'h':'8081', 'g':'8082'}

    DEFAULT_SERVERS = {
        'blk-cce-1.coinomi.net':{'t':'5015','s':'5015','h':'8081','g':'8082'},
        'blk-cce-2.coinomi.net':{'t':'5015','s':'5015','h':'8081','g':'8082'}
    }

    def hash_header(self, header):
        if header.get('version', 0) > 6:
            return rev_hex(SHA256dHash(self.header_to_string(header).decode('hex')).encode('hex'))
        else:
            return rev_hex(ScryptHash(self.header_to_string(header).decode('hex')).encode('hex'))

    def deserialize_tx_fields(self, vds, fields, d):
        timestamp = ('timestamp', vds.read_int32)
        fields.insert(1, timestamp)

    def serialize_tx_fields(self, tx, for_sig, fields):
        unix_time = getattr(tx, 'timestamp', None)
        if unix_time is None:
            unix_time = int(time.time())
        timestamp = ('timestamp', [int_to_hex(unix_time, 4)])
        fields.insert(1, timestamp)

