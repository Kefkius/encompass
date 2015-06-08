'''Chain-specific Digibyte code'''
from cryptocur import CryptoCur, hash_encode, hash_decode, rev_hex, int_to_hex, sha256, Hash, bits_to_target, target_to_bits
import os
import hashlib
import sqlite3

from ltc_scrypt import getPoWHash as getPoWScryptHash
from groestl_hash import getPoWHash as getPoWGroestlHash
from skeinhash import getPoWHash as getPoWSkeinHash
from qubit_hash import getPoWHash as getPoWQubitHash
from groestlcoin_hash import getHash as getPoWGroestlHash

multi_algo_diff_change_height = 145000
always_update_diff_change_height = 400000
num_algos = 5

class Digibyte(CryptoCur):
    PoW = True
    chain_index = 20
    coin_name = 'Digibyte'
    code = 'DGB'
    p2pkh_version = 30
    p2sh_version = 5
    wif_version = 158
    ext_pub_version = '0488b21e'
    ext_priv_version = '0488ade4'

    DUST_THRESHOLD = 0
    MIN_RELAY_TX_FEE = 100000
    RECOMMENDED_FEE = 100000
    COINBASE_MATURITY = 100

    block_explorers = {
        'DigiExplorer': 'https://digiexplorer.info/tx/'
    }

    base_units = {
        'DGB': 8
    }

    chunk_size = 2016

    DEFAULT_PORTS = {'t':'50001', 's':'50002', 'h':'8081', 'g':'8082'}

    DEFAULT_SERVERS = {
        'digibytewiki.com':DEFAULT_PORTS,
        'dgb-cce-1.coinomi.net':{'t':'5023', 's':'5023', 'h':'8081', 'g':'8082'},
        'dgb-cce-2.coinomi.net':{'t':'5023', 's':'5023', 'h':'8081', 'g':'8082'}
    }


    # overriden to setup up the sqlite db
    def set_headers_path(self, path):
        self.headers_path = path
        path_folder = os.path.split(path)[0]
        self.db_file_path = os.path.join(path_folder, 'blockchain_db_dgb.db')
        self.init_db_file()

    def init_db_file(self):
        header_db_file = sqlite3.connect(self.db_path())
        header_db = header_db_file.cursor()
        try:
            first_header = header_db.execute('SELECT * FROM headers WHERE height = 0')
        except Exception:
            header_db.execute('CREATE TABLE headers (header, algo, height int UNIQUE)')
        header_db_file.commit()
        header_db_file.close()

    def db_path(self):
        return self.db_file_path

    def verify_chain(self, chain):

        first_header = chain[0]
        prev_header = self.read_header(first_header.get('block_height') -1)

        for header in chain:

            height = header.get('block_height')

            prev_hash = self.hash_header(prev_header)
            bits, target = self.get_target(height, chain)
            version = header.get('version')
            if version == 1:
                _hash = self.pow_hash_scrypt_header(header)
            elif version == 2:
                _hash = self.pow_hash_sha_header(header)
            elif version == 514:
                _hash = self.pow_hash_scrypt_header(header)
            elif version == 1026:
                _hash = self.pow_hash_groestl_header(header)
            elif version == 1538:
                _hash = self.pow_hash_skein_header(header)
            elif version == 2050:
                _hash = self.pow_hash_qubit_header(header)
            else:
                print( "error unknown block version")
            try:
                assert prev_hash == header.get('prev_block_hash')
                assert bits == header.get('bits')
                assert int('0x'+_hash,16) < target
            except Exception:
                return False

            prev_header = header

        return True

    def verify_chunk(self, index, hexdata):
        data = hexdata.decode('hex')
        height = index*2016
        num = len(data)/80

        if index == 0:  
            previous_hash = ("0"*64)
        else:
            prev_header = self.read_header(height-1)
            if prev_header is None: raise
            previous_hash = self.hash_header(prev_header)

        for i in range(num):
            height = index*2016 + i
            raw_header = data[i*80:(i+1)*80]
            header = self.header_from_string(raw_header)
            version = header.get('version')
            if height >= always_update_diff_change_height:
                bits, target = self.get_target(height, data=data)
            if version == 1:
                _hash = self.pow_hash_scrypt_header(header)
            elif version == 2:
                _hash = self.pow_hash_sha_header(header)
            elif version == 514:
                _hash = self.pow_hash_scrypt_header(header)
            elif version == 1026:
                _hash = self.pow_hash_groestl_header(header)
            elif version == 1538:
                _hash = self.pow_hash_skein_header(header)
            elif version == 2050:
                _hash = self.pow_hash_qubit_header(header)
            else:
                print( "error unknown block version {}".format(version))
            assert previous_hash == header.get('prev_block_hash')
            if height >= always_update_diff_change_height:
                assert bits == header.get('bits')
                assert int('0x'+_hash,16) < target

            previous_header = header
            previous_hash = self.hash_header(header)

        self.save_chunk(index, data)

    def hash_header(self, header):
        return rev_hex(Hash(self.header_to_string(header).decode('hex')).encode('hex'))

    def pow_hash_scrypt_header(self, header):
        return rev_hex(getPoWScryptHash(self.header_to_string(header).decode('hex')).encode('hex'))

    def pow_hash_sha_header(self,header):
        return self.hash_header(header)

    def pow_hash_skein_header(self,header):
        return rev_hex(getPoWSkeinHash(self.header_to_string(header).decode('hex')).encode('hex'))

    def pow_hash_groestl_header(self,header):
        return rev_hex(getPoWGroestlHash(self.header_to_string(header).decode('hex')).encode('hex'))

    def pow_hash_qubit_header(self,header):
        return rev_hex(getPoWQubitHash(self.header_to_string(header).decode('hex')).encode('hex'))

    def get_target_v3(self, height, chain=None, data=None):
        target_timespan = 0.10 * 24 * 60 * 60 # 2.4 hours
        target_spacing = 60 # 1 minute
        interval = target_timespan / target_spacing
        target_timespan_re = 1 * 60
        target_spacing_re = 1 * 60
        interval_re = target_timespan_re / target_spacing_re # 1 block
        # multi algo updates
        multi_algo_target_timespan = 150 # 2.5 minutes (num_algos * 30 seconds)
        multi_algo_target_spacing = 150 # 2.5 minutes (num_algos * 30 seconds)
        multi_algo_interval = 1 # every block

        averaging_interval = 10 # 10 blocks
        averaging_target_timespan = averaging_interval * multi_algo_target_spacing

        max_adjust_down = 40
        max_adjust_up = 20

        max_adjust_down_v3 = 16
        max_adjust_up_v3 = 8
        local_difficulty_adjustment = 4
        target_timespan_adj_down = multi_algo_target_timespan * (160 + max_adjust_down) / 100

        max_target = 0x00000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF

        last = self.read_header(height-1)
        if last is None:
            for h in chain:
                if h.get('block_height') == height-1:
                    last = h
        first = self.read_header((height-1) - (num_algos * averaging_interval))
        if first is None:
            for h in chain:
                if h.get('block_height') == (height-1) - (num_algos * averaging_interval):
                    first = h

        header_db_file = sqlite3.connect(self.db_path())
        header_db = header_db_file.cursor()

        # TODO select header from db where algo is the same as last's
        # and height is the highest of that algo
        # https://github.com/digibyte/digibyte/blob/master/src/main.cpp#L1495
        prev_algo_index = header_db.execute('''SELECT header FROM headers WHERE ...''')

    def get_target(self, height, chain=None, data=None):
        if chain is None:
            chain = []  # Do not use mutables as default values!

        header_db_file = sqlite3.connect(self.db_path())
        header_db = header_db_file.cursor()
        max_target = 0x00000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        if height == 0 and data: 
            header_db.execute('''INSERT OR REPLACE INTO headers VALUES ('%s', '%s', '%s')''' % (data[0:80].encode('hex'), str(2), str(0)))
            header_db_file.commit()
            header_db_file.close()
        if height == 0: return 0x1e0ffff0, 0x00000FFFF0000000000000000000000000000000000000000000000000000000

        
        # None of this is valid. Variables are undefined, etc.
#        # Myriadcoin
#        bits = last.get('bits') 
#        target = bits_to_target(bits)
#
#        # new target
#        new_target = min( max_target, (target * nActualTimespan)/nAvgInterval )
#        new_bits = target_to_bits(new_target)

        header_db_file.commit()
        header_db_file.close()
        return new_bits, new_target

Currency = Digibyte
