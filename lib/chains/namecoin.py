"""Chain-specific Namecoin code."""
from cryptocur import *

def get_class():
    return Namecoin

class Namecoin(CryptoCur):
    PoW = False
    chain_index = 7
    coin_name = 'Namecoin'
    code = 'NMC'
    p2pkh_version = 52
    p2sh_version = 13
    wif_version = 180
    ext_pub_version = '0488b21e'
    ext_priv_version = '0488ade4'
    message_magic = 'Bitcoin Signed Message:\n'

    DUST_THRESHOLD = 5430
    MIN_RELAY_TX_FEE = 100000
    RECOMMENDED_FEE = 500000
    COINBASE_MATURITY = 100

    block_explorers = [
        ('Namecoin.info', 'https://explorer.namecoin.info',
                    {'tx': '/tx/%', 'addr': '/a/%'}),
        ('Namecha.in', 'https://namecha.in',
                    {'tx': '/tx/%', 'addr': '/address/%'}),
        ('Coinplorer.com', 'https://coinplorer.com/NMC',
                    {'tx': '/Transactions/%', 'addr': '/Addresses/%'})
    ]

    DEFAULT_PORTS = {'t':'50001', 's':'50002', 'h':'8081', 'g':'8082'}

    DEFAULT_SERVERS = {
        'e-nmc.us-west-2.maza.club': DEFAULT_PORTS,
    }

