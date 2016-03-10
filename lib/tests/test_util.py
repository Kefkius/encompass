import unittest
from lib.util import format_satoshis, parse_URI
from lib import chainparams

bitcoin_chain = None

def setupModule():
    global bitcoin_chain
    chainparams.init_chains()
    chainparams.set_active_chain('BTC')
    bitcoin_chain = chainparams.get_chain_instance('BTC')


class TestUtil(unittest.TestCase):

    def test_format_satoshis(self):
        result = format_satoshis(1234)
        expected = "0.00001234"
        self.assertEqual(expected, result)

    def test_format_satoshis_diff_positive(self):
        result = format_satoshis(1234, is_diff=True)
        expected = "+0.00001234"
        self.assertEqual(expected, result)

    def test_format_satoshis_diff_negative(self):
        result = format_satoshis(-1234, is_diff=True)
        expected = "-0.00001234"
        self.assertEqual(expected, result)

    def _do_test_parse_URI(self, uri, expected, chain='BTC'):
        result = parse_URI(uri, chainparams.get_chain_instance(chain))
        self.assertEqual(expected, result)

    def test_parse_URI_address(self):
        self._do_test_parse_URI('bitcoin:15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma',
                                {'address': '15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma'})
        self._do_test_parse_URI('litecoin:LPzGaoLUtXFkmNo3u1chDxGxDnSaBQTTxm',
                                {'address': 'LPzGaoLUtXFkmNo3u1chDxGxDnSaBQTTxm'}, chain='LTC')

    def test_parse_URI_only_address(self):
        self._do_test_parse_URI('15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma',
                                {'address': '15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma'})


    def test_parse_URI_address_label(self):
        self._do_test_parse_URI('bitcoin:15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma?label=electrum%20test',
                                {'address': '15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma', 'label': 'electrum test'})

    def test_parse_URI_address_message(self):
        self._do_test_parse_URI('bitcoin:15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma?message=electrum%20test',
                                {'address': '15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma', 'message': 'electrum test', 'memo': 'electrum test'})

    def test_parse_URI_address_amount(self):
        self._do_test_parse_URI('bitcoin:15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma?amount=0.0003',
                                {'address': '15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma', 'amount': 30000})

    def test_parse_URI_address_request_url(self):
        self._do_test_parse_URI('bitcoin:15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma?r=http://domain.tld/page?h%3D2a8628fc2fbe',
                                {'address': '15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma', 'r': 'http://domain.tld/page?h=2a8628fc2fbe'})

    def test_parse_URI_ignore_args(self):
        self._do_test_parse_URI('bitcoin:15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma?test=test',
                                {'address': '15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma', 'test': 'test'})

    def test_parse_URI_multiple_args(self):
        self._do_test_parse_URI('bitcoin:15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma?amount=0.00004&label=electrum-test&message=electrum%20test&test=none&r=http://domain.tld/page',
                                {'address': '15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma', 'amount': 4000, 'label': 'electrum-test', 'message': u'electrum test', 'memo': u'electrum test', 'r': 'http://domain.tld/page', 'test': 'none'})

    def test_parse_URI_no_address_request_url(self):
        self._do_test_parse_URI('bitcoin:?r=http://domain.tld/page?h%3D2a8628fc2fbe',
                                {'r': 'http://domain.tld/page?h=2a8628fc2fbe'})

    def test_parse_URI_invalid_address(self):
        self.assertRaises(AssertionError, parse_URI, 'bitcoin:invalidaddress', bitcoin_chain)

    def test_parse_URI_invalid(self):
        self.assertRaises(AssertionError, parse_URI, 'notbitcoin:15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma', bitcoin_chain)

    def test_parse_URI_parameter_polution(self):
        self.assertRaises(Exception, parse_URI, 'bitcoin:15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma?amount=0.0003&label=test&amount=30.0', bitcoin_chain)

