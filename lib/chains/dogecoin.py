'''Chain-specific Dogecoin code'''
from cryptocur import *
import os

from coinhash import SHA256dHash, ScryptHash

def get_class():
    return Dogecoin

class Dogecoin(CryptoCur):
    PoW = False
    chain_index = 3
    coin_name = 'Dogecoin'
    code = 'DOGE'
    p2pkh_version = 30
    p2sh_version = 22
    wif_version = 158
    message_magic = 'Dogecoin Signed Message:\n'

    # can't find solid data on the constants below
    DUST_THRESHOLD = 1000000
#    MIN_RELAY_TX_FEE = 100000000
    MIN_RELAY_TX_FEE = DUST_THRESHOLD
    RECOMMENDED_FEE = MIN_RELAY_TX_FEE
    COINBASE_MATURITY = 240

    block_explorers = [
        ('Dogechain.info', 'https://dogechain.info',
                    {'tx': '/tx/%', 'addr': '/address/%'}),
        ('Coinplorer.com', 'https://coinplorer.com/DOGE',
                    {'tx': '/Transactions/%', 'addr': '/Addresses/%'})
    ]

    base_units = {
        'KDOGE': 11,
        'DOGE': 8
    }

    DEFAULT_PORTS = {'t':'50001', 's':'50002', 'h':'8081', 'g':'8082'}

    DEFAULT_SERVERS = {
        'doge-cce-1.coinomi.net':{'t':'5003', 's':'5003', 'h':'8081', 'g':'8082'},
        'doge-cce-2.coinomi.net':{'t':'5003', 's':'5003', 'h':'8081', 'g':'8082'}
    }

