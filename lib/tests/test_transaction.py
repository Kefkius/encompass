import unittest
from lib import transaction
from lib import chainparams
from lib.bitcoin import TYPE_ADDRESS, TYPE_PUBKEY, TYPE_SCRIPT

import pprint

unsigned_blob = '01000000012a5c9a94fcde98f5581cd00162c60a13936ceb75389ea65bf38633b424eb4031000000005701ff4c53ff0488b21e03ef2afea18000000089689bff23e1e7fb2f161daa37270a97a3d8c2e537584b2d304ecb47b86d21fc021b010d3bd425f8cf2e04824bfdf1f1f5ff1d51fadd9a41f9e3fb8dd3403b1bfe00000000ffffffff0140420f00000000001976a914230ac37834073a42146f11ef8414ae929feaafc388ac00000000'
signed_blob = '01000000012a5c9a94fcde98f5581cd00162c60a13936ceb75389ea65bf38633b424eb4031000000006c493046022100a82bbc57a0136751e5433f41cf000b3f1a99c6744775e76ec764fb78c54ee100022100f9e80b7de89de861dc6fb0c1429d5da72c2b6b2ee2406bc9bfb1beedd729d985012102e61d176da16edd1d258a200ad9759ef63adf8e14cd97f53227bae35cdb84d2f6ffffffff0140420f00000000001976a914230ac37834073a42146f11ef8414ae929feaafc388ac00000000'

def setUpModule():
    chainparams.init_chains()

class TestTransaction(unittest.TestCase):

    def test_tx_unsigned(self):
        chainparams.set_active_chain('BTC')
        expected = {
            'inputs': [{
                'address': '1446oU3z268EeFgfcwJv6X2VBXHfoYxfuD',
                'is_coinbase': False,
                'num_sig': 1,
                'prevout_hash': '3140eb24b43386f35ba69e3875eb6c93130ac66201d01c58f598defc949a5c2a',
                'prevout_n': 0,
                'pubkeys': ['02e61d176da16edd1d258a200ad9759ef63adf8e14cd97f53227bae35cdb84d2f6'],
                'scriptSig': '01ff4c53ff0488b21e03ef2afea18000000089689bff23e1e7fb2f161daa37270a97a3d8c2e537584b2d304ecb47b86d21fc021b010d3bd425f8cf2e04824bfdf1f1f5ff1d51fadd9a41f9e3fb8dd3403b1bfe00000000',
                'sequence': 4294967295,
                'signatures': [None],
                'x_pubkeys': ['ff0488b21e03ef2afea18000000089689bff23e1e7fb2f161daa37270a97a3d8c2e537584b2d304ecb47b86d21fc021b010d3bd425f8cf2e04824bfdf1f1f5ff1d51fadd9a41f9e3fb8dd3403b1bfe00000000']}],
            'locktime': 0,
            'outputs': [{
                'address': '14CHYaaByjJZpx4oHBpfDMdqhTyXnZ3kVs',
                'prevout_n': 0,
                'scriptPubKey': '76a914230ac37834073a42146f11ef8414ae929feaafc388ac',
                'type': TYPE_ADDRESS,
                'value': 1000000}],
                'version': 1
        }
        tx = transaction.Transaction(unsigned_blob)
        self.assertEquals(tx.deserialize(), expected)
        self.assertEquals(tx.deserialize(), None)

        self.assertEquals(tx.as_dict(), {'hex': unsigned_blob, 'complete': False})
        self.assertEquals(tx.get_outputs(), [('14CHYaaByjJZpx4oHBpfDMdqhTyXnZ3kVs', 1000000)])
        self.assertEquals(tx.get_output_addresses(), ['14CHYaaByjJZpx4oHBpfDMdqhTyXnZ3kVs'])

        self.assertTrue(tx.has_address('14CHYaaByjJZpx4oHBpfDMdqhTyXnZ3kVs'))
        self.assertTrue(tx.has_address('1446oU3z268EeFgfcwJv6X2VBXHfoYxfuD'))
        self.assertFalse(tx.has_address('1CQj15y1N7LDHp7wTt28eoD1QhHgFgxECH'))

        self.assertEquals(tx.inputs_to_sign(), set(x_pubkey for i in expected['inputs'] for x_pubkey in i['x_pubkeys']))
        self.assertEquals(tx.serialize(), unsigned_blob)

        tx.update_signatures(signed_blob)
        self.assertEquals(tx.raw, signed_blob)

        tx.update(unsigned_blob)
        tx.raw = None
        blob = str(tx)
        self.assertEquals(transaction.deserialize(blob), expected)

    def test_tx_signed(self):
        chainparams.set_active_chain('BTC')
        expected = {
            'inputs': [{
                'address': '1446oU3z268EeFgfcwJv6X2VBXHfoYxfuD',
                'is_coinbase': False,
                'num_sig': 1,
                'prevout_hash': '3140eb24b43386f35ba69e3875eb6c93130ac66201d01c58f598defc949a5c2a',
                'prevout_n': 0,
                'pubkeys': ['02e61d176da16edd1d258a200ad9759ef63adf8e14cd97f53227bae35cdb84d2f6'],
                'scriptSig': '493046022100a82bbc57a0136751e5433f41cf000b3f1a99c6744775e76ec764fb78c54ee100022100f9e80b7de89de861dc6fb0c1429d5da72c2b6b2ee2406bc9bfb1beedd729d985012102e61d176da16edd1d258a200ad9759ef63adf8e14cd97f53227bae35cdb84d2f6',
                'sequence': 4294967295,
                'signatures': ['3046022100a82bbc57a0136751e5433f41cf000b3f1a99c6744775e76ec764fb78c54ee100022100f9e80b7de89de861dc6fb0c1429d5da72c2b6b2ee2406bc9bfb1beedd729d985'],
                'x_pubkeys': ['02e61d176da16edd1d258a200ad9759ef63adf8e14cd97f53227bae35cdb84d2f6']}],
            'locktime': 0,
            'outputs': [{
                'address': '14CHYaaByjJZpx4oHBpfDMdqhTyXnZ3kVs',
                'prevout_n': 0,
                'scriptPubKey': '76a914230ac37834073a42146f11ef8414ae929feaafc388ac',
                'type': TYPE_ADDRESS,
                'value': 1000000}],
            'version': 1
        }
        tx = transaction.Transaction(signed_blob)
        self.assertEquals(tx.deserialize(), expected)
        self.assertEquals(tx.deserialize(), None)
        self.assertEquals(tx.as_dict(), {'hex': signed_blob, 'complete': True})

        self.assertEquals(tx.inputs_to_sign(), set())
        self.assertEquals(tx.serialize(), signed_blob)

        tx.update_signatures(signed_blob)

    def test_errors(self):
        with self.assertRaises(TypeError):
            transaction.Transaction.pay_script(output_type=None, addr='')

        with self.assertRaises(BaseException):
            transaction.parse_xpub('')

    def test_parse_xpub(self):
        chainparams.set_active_chain('BTC')
        res = transaction.parse_xpub('fe4e13b0f311a55b8a5db9a32e959da9f011b131019d4cebe6141b9e2c93edcbfc0954c358b062a9f94111548e50bde5847a3096b8b7872dcffadb0e9579b9017b01000200')
        self.assertEquals(res, ('04ee98d63800824486a1cf5b4376f2f574d86e0a3009a6448105703453f3368e8e1d8d090aaecdd626a45cc49876709a3bbb6dc96a4311b3cac03e225df5f63dfc', '19h943e4diLc68GXW7G75QNe2KWuMu7BaJ'))

        res = transaction.parse_xpub('fd007d260305ef27224bbcf6cf5238d2b3638b5a78d5')
        self.assertEquals(res, (None, '1CQj15y1N7LDHp7wTt28eoD1QhHgFgxECH'))

    def test_peercoin_deserialize_and_serialize(self):
        chainparams.set_active_chain('PPC')
        rawtx = '0100000058e4615501a367e883a383167e64c84e9c068ba5c091672e434784982f877eede589cb7e53000000006a473044022043b9aee9187effd7e6c7bc444b09162570f17e36b4a9c02cf722126cc0efa3d502200b3ba14c809fa9a6f7f835cbdbbb70f2f43f6b30beaf91eec6b8b5981c80cea50121025edf500f18f9f2b3f175f823fa996fbb2ec52982a9aeb1dc2e388a651054fb0fffffffff0257be0100000000001976a91495efca2c6a6f0e0f0ce9530219b48607a962e77788ac45702000000000001976a914f28abfb465126d6772dcb4403b9e1ad2ea28a03488ac00000000'
        tx = transaction.Transaction(rawtx)
        d = tx.deserialize()
        self.assertEqual(d['version'], 1)
        self.assertEqual(len(d['inputs']), 1)
        self.assertEqual(len(d['outputs']), 2)
        self.assertEqual(d['locktime'], 0)
        self.assertEqual(d['timestamp'], 1432478808)

        self.assertEqual(tx.serialize(), rawtx)

    def test_clams_deserialize_and_serialize(self):
        chainparams.set_active_chain('CLAM')
        rawtx = '02000000704d4a5501faaac09e923eb154c4a1692a69f40c6c7570ee508c5cef1d85325a5caeabd8f74a0100008a47304402205b628da48fe51c0d33fdb496b942690b1c0a6f8b295c431fe80c296b4e19af8702203e33521e4b3cb36e0f82f75930c8eeb5cd28d5189ac10a9b119e967f8cee0d53014104be46fb68e65df4b60ccf5503eed8ccbd0939543205f0ecaaf2343fd2301e4ef7bce423461bee2912f438466a95d125bd43d4b55bf809bd3efb9614bac9fe7b25ffffffff0200000000000000000040e1a65500000000434104be46fb68e65df4b60ccf5503eed8ccbd0939543205f0ecaaf2343fd2301e4ef7bce423461bee2912f438466a95d125bd43d4b55bf809bd3efb9614bac9fe7b25ac000000001568747470733a2f2f4a7573742d446963652e636f6d'
        tx = transaction.Transaction(rawtx)
        d = tx.deserialize()

        self.assertEqual(d['version'], 2)
        self.assertEqual(len(d['inputs']), 1)
        self.assertEqual(len(d['outputs']), 2)
        self.assertEqual(d['locktime'], 0)
        self.assertEqual(d['timestamp'], 1430932848)
        self.assertEqual(d['clamspeech'], 'https://Just-Dice.com')

        self.assertEqual(tx.serialize(), rawtx)


class NetworkMock(object):

    def __init__(self, unspent):
        self.unspent = unspent

    def synchronous_get(self, arg):
        return self.unspent
