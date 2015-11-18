import cryptocur
from cryptocur import *
import os

from coinhash import SHA256dHash

def get_class():
    return Bitcoin

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

    DEFAULT_PORTS = {'t':'50001', 's':'50002', 'h':'8081', 'g':'8082'}

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


    def get_target(self, height, chain=None):
        if chain is None:
            chain = []  # Do not use mutables as default values!
        index = height/2016

        max_target = 0x00000000FFFF0000000000000000000000000000000000000000000000000000
        if index == 0: return 0x1d00ffff, max_target

        first = self.read_header((index-1)*2016)
        last = self.read_header(index*2016-1)
        if last is None:
            for h in chain:
                if h.get('block_height') == index*2016-1:
                    last = h

        nActualTimespan = last.get('timestamp') - first.get('timestamp')
        nTargetTimespan = 14*24*60*60
        nActualTimespan = max(nActualTimespan, nTargetTimespan/4)
        nActualTimespan = min(nActualTimespan, nTargetTimespan*4)

        bits = last.get('bits')
        # convert to bignum
        MM = 256*256*256
        a = bits%MM
        if a < 0x8000:
            a *= 256
        target = (a) * pow(2, 8 * (bits/MM - 3))

        # new target
        new_target = min( max_target, (target * nActualTimespan)/nTargetTimespan )

        # convert it to bits
        c = ("%064X"%new_target)[2:]
        i = 31
        while c[0:2]=="00":
            c = c[2:]
            i -= 1

        c = int('0x'+c[0:6],16)
        if c >= 0x800000:
            c /= 256
            i += 1

        new_bits = c + MM * i
        return new_bits, new_target


