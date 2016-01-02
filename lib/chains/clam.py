'''Chain-specific Clam code'''
from cryptocur import *
import os
import time

from coinhash import SHA256dHash

def get_class():
    return Clam

TX_VERSION_CLAMSPEECH = 2

class Clam(CryptoCur):
    PoW = False
    chain_index = 23
    coin_name = 'Clam'
    code = 'CLAMS'
    p2pkh_version = 137
    p2sh_version = 13
    wif_version = 133
    ext_pub_version = '0488b21e'
    ext_priv_version = '0488ade4'
    message_magic = 'Clam Signed Message:\n'

    DUST_THRESHOLD = 5430
    MIN_RELAY_TX_FEE = 10000
    RECOMMENDED_FEE = 50000
    COINBASE_MATURITY = 500

    block_explorers = [
        ('Clamsight.com', 'https://clamsight.com',
                    {'tx': '/tx/%', 'addr': '/address/%'})
    ]

    base_units = {
        'CLAMS': 8
    }

    chunk_size = 2016

    DEFAULT_PORTS = {'t':'50001', 's':'50002', 'h':'8081', 'g':'8082'}

    DEFAULT_SERVERS = {
        'scallop.us-west-2.maza.club':DEFAULT_PORTS
    }

    def deserialize_tx_fields(self, vds, fields, d):
        timestamp = ('timestamp', vds.read_int32)
        fields.insert(1, timestamp)
        clamspeech = ('clamspeech', vds.read_string)
        fields.append(clamspeech)

    def serialize_tx_fields(self, tx, for_sig, fields):
        unix_time = getattr(tx, 'timestamp', None)
        if unix_time is None:
            unix_time = int(time.time())
        timestamp = ('timestamp', [int_to_hex(unix_time, 4)])
        fields.insert(1, timestamp)

        tx_version = getattr(tx, 'version', 1)
        if tx_version < TX_VERSION_CLAMSPEECH:
            return

        speech_str = getattr(tx, 'clamspeech', '').encode('hex')
        speech = ('clamspeech', [speech_str])
        speech_len = ('clamspeech_len', [var_int(len(speech_str)/2)])
        fields.insert(-1,  speech_len)
        fields.insert(-1,  speech)

