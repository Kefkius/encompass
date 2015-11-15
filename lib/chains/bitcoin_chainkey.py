import cryptocur
from cryptocur import *
import os

from coinhash import SHA256dHash

def get_class():
    return Bitcoin


DEFAULT_PORTS = {'t':'50001', 's':'50002', 'h':'8081', 'g':'8082'}

class Bitcoin(CryptoCur):
    PoW = True
    chain_index = 0
    coin_name = 'Bitcoin'
    code = 'BTC'
    p2pkh_version = 0
    p2sh_version = 5
    wif_version = 128
    ext_pub_version = '0488b21e'
    ext_priv_version = '0488ade4'

    DUST_THRESHOLD = 5430
    MIN_RELAY_TX_FEE = 1000
    RECOMMENDED_FEE = 50000
    COINBASE_MATURITY = 100

    block_explorers = [
        ('Insight.is', 'https://insight.bitpay.com',
                    {'tx': '/tx/%', 'addr': '/address/%'}),
        ('Blockchain.info', 'https://blockchain.info',
                    {'tx': '/tx/%', 'addr': '/address/%'})
    ]

    base_units = {
        'BTC': 8,
        'mBTC': 5,
        'bits': 2,
    }

    headers_url = 'http://headers.electrum.org/blockchain_headers'

    DEFAULT_SERVERS = {
        'electrum.be':{'t':'50001', 's':'50002'},
        'electrum.drollette.com':{'t':'50001', 's':'50002'},
        'erbium1.sytes.net':{'t':'50001', 's':'50002'},
        'ecdsa.net':{'t':'50001', 's':'110'},
        'electrum0.electricnewyear.net':{'t':'50001', 's':'50002'},
        'kirsche.emzy.de':DEFAULT_PORTS,
        'VPS.hsmiths.com':{'t':'50001', 's':'50002'},
        'ELECTRUM.jdubya.info':{'t':'50001', 's':'50002'},
        'electrum.no-ip.org':{'t':'50001', 's':'50002', 'g':'443'},
        'electrum.thwg.org':DEFAULT_PORTS,
        'us.electrum.be':{'t':'50001', 's':'50002'},
    }



