"""Base CryptoCurrency."""
import os, hashlib

import coinhash

def rev_hex(s):
    """Reverses the bytes of a hex string."""
    return s.decode('hex')[::-1].encode('hex')

def int_to_hex(i, length=1):
    """Encodes an integer as a little-endian hex string of the given length."""
    s = hex(i)[2:].rstrip('L')
    s = "0"*(2*length - len(s)) + s
    return rev_hex(s)

def var_int(i):
    # https://en.bitcoin.it/wiki/Protocol_specification#Variable_length_integer
    if i<0xfd:
        return int_to_hex(i)
    elif i<=0xffff:
        return "fd"+int_to_hex(i,2)
    elif i<=0xffffffff:
        return "fe"+int_to_hex(i,4)
    else:
        return "ff"+int_to_hex(i,8)

def op_push(i):
    if i<0x4c:
        return int_to_hex(i)
    elif i<0xff:
        return '4c' + int_to_hex(i)
    elif i<0xffff:
        return '4d' + int_to_hex(i,2)
    else:
        return '4e' + int_to_hex(i,4)

hash_encode = lambda x: x[::-1].encode('hex')
hash_decode = lambda x: x.decode('hex')[::-1]

def bits_to_target(bits):
    """Convert a compact representation to a hex target."""
    MM = 256*256*256
    a = bits%MM
    if a < 0x8000:
        a *= 256
    target = (a) * pow(2, 8 * (bits/MM - 3))
    return target

def target_to_bits(target):
    """Convert a target to compact representation."""
    MM = 256*256*256
    c = ("%064X"%target)[2:]
    i = 31
    while c[0:2]=="00":
        c = c[2:]
        i -= 1

    c = int('0x'+c[0:6],16)
    if c >= 0x800000:
        c /= 256
        i += 1

    new_bits = c + MM * i
    return new_bits


class CryptoCur(object):
    '''Abstract class containing cryptocurrency-specific code'''
    ### Chain parameters ###

    # Whether this chain verifies Proof-of-Work
    PoW = False

    # index used in child key derivation
    chain_index = 0
    # Full name (e.g. Bitcoin)
    coin_name = ''
    # Abbreviation (e.g. BTC)
    code = ''
    # Address base58 prefix
    p2pkh_version = 0
    # Script hash base58 prefix
    p2sh_version = 0
    # Private key base58 prefix
    wif_version = 0
    # Extended pubkey base58 prefix
    ext_pub_version = ''
    # Extended privkey base58 prefix
    ext_priv_version = ''
    # "Magic" bytes for signing/verifying
    message_magic = ''

    ### Constants ###

    DUST_THRESHOLD = 5430
    MIN_RELAY_TX_FEE = 1000
    RECOMMENDED_FEE = 50000
    COINBASE_MATURITY = 100

    ### Hash Algorithms ###
    base58_hash = coinhash.SHA256dHash
    header_hash = coinhash.SHA256dHash
    transaction_hash = coinhash.SHA256dHash

    # Block explorers.
    block_explorers = None

    # Currency units {name : decimal point}
    base_units = None

    # URL where a header bootstrap can be downloaded
    headers_url = ''

    # Default electrum servers.
    DEFAULT_SERVERS = None

    # Number of headers in one chunk
    chunk_size = 2016

    def __init__(self):
        # Default mutables.
        for attr, data_type in [('block_explorers', list),
                                ('base_units', dict),
                                ('DEFAULT_SERVERS', dict)]:
            if getattr(self, attr) is None:
                setattr(self, attr, data_type())
        if not self.base_units:
            self.base_units = {self.code: 8}

    def block_explorer(self, config):
        """Get preferred block explorer from config."""
        return config.get('block_explorer', self.block_explorers[0])

    def block_explorer_info(self):
        """Get a dict of this chain's block explorers."""
        return dict((i.name, i) for i in self.block_explorers)



    # Called on chain reorg. Go back by COINBASE_MATURITY.
    def reorg_handler(self, local_height):
        name = self.path()
        if os.path.exists(name):
            f = open(name, 'rb+')
            f.seek((local_height*80) - (self.COINBASE_MATURITY*80))
            f.truncate()
            f.close()

    # Tell us where our blockchain_headers file is
    def set_headers_path(self, path):
        self.headers_path = path

    def path(self):
        return self.headers_path

    # Called from blockchain.py when a chain of headers (arbitrary number of headers that's less than a chunk) needs verification.
    def verify_chain(self, chain):
        """Returns whether a chain of headers is valid."""
        first_header = chain[0]
        prev_header = self.read_header(first_header.get('block_height') - 1)
        # if we don't verify PoW, just check that headers connect by previous_hash
        for header in chain:
            height = header.get('block_height')

            prev_hash = self.hash_header(prev_header)
            if self.PoW:
                bits, target = self.get_target(height, chain)
            _hash = self.hash_header(header)
            try:
                assert prev_hash == header.get('prev_block_hash')
                if self.PoW:
                    assert bits == header.get('bits')
                    assert int('0x'+_hash,16) < target
            except Exception:
                return False

            prev_header = header

        return True

    # Called from blockchain.py when a chunk of headers needs verification.
    def verify_chunk(self, index, hexdata):
        """Attempts to verify a chunk of headers.

        Does not return a value. This either succeeds
        or throws an error."""
        data = hexdata.decode('hex')
        height = index*self.chunk_size
        num = len(data)/80
        # we form a chain of headers so we don't need to save individual headers
        # in cases where a chain uses recent headers in difficulty calculation.
        chain = []

        if index == 0:
            previous_hash = ("0"*64)
        else:
            prev_header = self.read_header(index*self.chunk_size-1)
            if prev_header is None: raise
            previous_hash = self.hash_header(prev_header)

        # if we don't verify PoW, just check that headers connect by previous_hash
        for i in range(num):
            height = index*self.chunk_size + i
            raw_header = data[i*80:(i+1)*80]
            header = self.header_from_string(raw_header)
            _hash = self.hash_header(header)

            if self.PoW:
                header['block_height'] = height
                chain.append(header)
                bits, target = self.get_target(height, chain)

            assert previous_hash == header.get('prev_block_hash')
            if self.PoW:
                assert bits == header.get('bits')
                assert int('0x'+_hash,16) < target

            previous_header = header
            previous_hash = _hash

        self.save_chunk(index, data)

    # Most common header format. Reimplement in a derived class if header format differs.
    def header_to_string(self, res):
        """Create a serialized string from a header dict."""
        s = []
        s.append(int_to_hex(res.get('version'),4))
        s.append(rev_hex(res.get('prev_block_hash')))
        s.append(rev_hex(res.get('merkle_root')))
        s.append(int_to_hex(int(res.get('timestamp')),4))
        s.append(int_to_hex(int(res.get('bits')),4))
        s.append(int_to_hex(int(res.get('nonce')),4))
        return ''.join(s)

    # Most common header format. Reimplement in a derived class if header format differs.
    def header_from_string(self, s):
        """Create a header dict from a serialized string."""
        hex_to_int = lambda s: int('0x' + s[::-1].encode('hex'), 16)
        h = {}
        h['version'] = hex_to_int(s[0:4])
        h['prev_block_hash'] = hash_encode(s[4:36])
        h['merkle_root'] = hash_encode(s[36:68])
        h['timestamp'] = hex_to_int(s[68:72])
        h['bits'] = hex_to_int(s[72:76])
        h['nonce'] = hex_to_int(s[76:80])
        return h

    def hash_header(self, header):
        return rev_hex(( getattr(coinhash, self.header_hash.__name__)(self.header_to_string(header).decode('hex')) ).encode('hex'))

    # save a chunk of headers to the binary file. Should not need to be reimplemented but can be.
    def save_chunk(self, index, chunk):
        filename = self.path()
        f = open(filename,'rb+')
        f.seek(index * self.chunk_size * 80)
        h = f.write(chunk)
        f.close()

    # save a single header to the binary file. Should not need to be reimplemented but can be.
    def save_header(self, header):
        data = self.header_to_string(header).decode('hex')
        assert len(data) == 80
        height = header.get('block_height')
        filename = self.path()
        f = open(filename,'rb+')
        f.seek(height*80)
        h = f.write(data)
        f.close()

    # read a header from the binary file. Should not need to be reimplemented but can be.
    def read_header(self, block_height):
        name = self.path()
        if os.path.exists(name):
            f = open(name,'rb')
            f.seek(block_height*80)
            h = f.read(80)
            f.close()
            if len(h) == 80:
                h = self.header_from_string(h)
                return h

    # Calculate the difficulty target
    def get_target(self, height, chain=None):
        pass

    def deserialize_tx_fields(self, vds, fields, d):
        """This method provides a way for chains to modify the deserialization process.

        Args:
            vds (BCDataStream): Data stream.
            fields (list): List of 2-tuples of the form (name, action), where:
                - name (str): Attribute name.
                - action: Function to call that returns the value. Usually a BCDataStream method.
            d (dict): Dict used to hold deserialized values.
        """
        pass

    def serialize_tx_fields(self, tx, for_sig, fields):
        """This method provides a way for chains to modify the serialization process.

        Args:
            tx (Transaction): Transaction instance.
            for_sig: Serialization purpose. Can be any of the following:
                - -1: Do not sign, estimate length.
                - i >= 0: Serialized tx for signing input i.
                - None: Add all known signatures.
            fields (list): List of 2-tuples of the form (name, data), where:
                - name (str): Attribute name.
                - data (list): Empty list containing the data for that field. If data is added to
                    this list, the Transaction instance will use that data instead of supplying its own.
        """
        pass

