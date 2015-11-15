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

    def test_subscribe_to_changes(self):
        test_list = []
        def on_active_chain_changed(new_chain):
            test_list.append(new_chain.code)
        self.assertTrue(chainparams.subscribe(on_active_chain_changed))
        # Change the active chain
        chainparams.set_active_chain('BTC')
        self.assertEqual(len(test_list), 1)
        self.assertEqual('BTC', test_list[0])

        chainparams.unsubscribe(on_active_chain_changed)
        chainparams.set_active_chain('BTC')
        self.assertEqual(len(test_list), 1)
        self.assertEqual('BTC', test_list[0])
