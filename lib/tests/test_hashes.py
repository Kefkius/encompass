import unittest
import coinhash

from lib.bitcoin import rev_hex
from lib import chainparams

chainparams.init_chains()

class Test_hashes(unittest.TestCase):

    def test_sha256d(self):
        # bitcoin block 100000
        block_header = '0100000050120119172a610421a6c3011dd330d9df07b63616c2cc1f1cd00200000000006657a9252aacd5c0b2940996ecff952228c3067cc38d4885efb5a4ac4247e9f337221b4d4c86041b0f2b5710'
        actual_pow_hash = '000000000003ba27aa200b1cecaad478d2b00432346c3f1f3986da1afd33e506'
        chain = chainparams.get_chain_instance('BTC')

        self.assertEqual(actual_pow_hash, chain.hash_header( chain.header_from_string(block_header.decode('hex')) ))

    def test_scrypt(self):
        # litecoin block 20000
        block_header = '010000006bce902b61adcac03429993a51deaaff5229d21453af96d5a1425ba956edeebec3c4551556f8340cfd54292411a8f2c1d6a4f2444651619fcad4708aefc0c020c6f4a94e678a041d81590000'
        actual_pow_hash = '000000010f3a68cae10585dea46116e5298a83458bd05ab2169829a84ff3ef1e'
        chain = chainparams.get_chain_instance('LTC')

        self.assertEqual(actual_pow_hash, chain.pow_hash_header( chain.header_from_string(block_header.decode('hex')) ))

    def test_x11(self):
        # dash block 200000
        block_header = '020000007e3aab137b7d64096f20613289197414631bad462e139f445edb030000000000efc89e19be378dc9d2e6f00048611a405acf76f78334cb8504ce119fbade8420ce36af54e4bc181bfcdef446'
        actual_pow_hash = '000000000004d0615ff622ec78457ca211dc63fc9c62cca9d9d9af7206be721b'
        chain = chainparams.get_chain_instance('DASH')

        self.assertEqual(actual_pow_hash, chain.hash_header( chain.header_from_string(block_header.decode('hex')) ))

