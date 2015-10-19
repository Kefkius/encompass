import unittest
import imp

imp.load_module('encompass', *imp.find_module('lib'))
from encompass import chainparams

chainparams.init_chains()

class TestChainparams(unittest.TestCase):
    def test_chains_exist(self):
        self.assertGreater(len(chainparams.known_chains), 0)

    def test_known_chains(self):
        for chain in chainparams.known_chains:
            cls = chain.cls
            self.assertEqual(chain.chain_index, cls.chain_index)
            self.assertEqual(chain.coin_name, cls.coin_name)
            self.assertEqual(chain.code, cls.code)
            self.assertEqual(chain.cls, cls)

            self.assertIn(chain.code, chainparams.known_chain_codes)
            self.assertEqual(chain, chainparams.known_chain_dict[cls.code])

    def test_is_known_chain(self):
        self.assertTrue(chainparams.is_known_chain('BTC'))
        self.assertFalse(chainparams.is_known_chain('EncompassTestCode'))
