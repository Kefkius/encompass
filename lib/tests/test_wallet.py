import shutil
import tempfile
import sys
import unittest
import os
import json

from StringIO import StringIO
from lib.wallet import WalletStorage, BIP44_Wallet, NewWallet
from lib import chainparams

def setUpModule():
    chainparams.init_chains()


class FakeSynchronizer(object):

    def __init__(self):
        self.store = []

    def add(self, address):
        self.store.append(address)


class WalletTestCase(unittest.TestCase):

    def setUp(self):
        super(WalletTestCase, self).setUp()
        chainparams.set_active_chain('BTC')
        self.user_dir = tempfile.mkdtemp()

        self.wallet_path = os.path.join(self.user_dir, "somewallet")

        self._saved_stdout = sys.stdout
        self._stdout_buffer = StringIO()
        sys.stdout = self._stdout_buffer

    def tearDown(self):
        super(WalletTestCase, self).tearDown()
        shutil.rmtree(self.user_dir)
        # Restore the "real" stdout
        sys.stdout = self._saved_stdout


class TestWalletStorage(WalletTestCase):

    def test_read_dictionnary_from_file(self):

        some_dict = {"BTC": {"a":"b", "c":"d"}}
        contents = repr(some_dict)
        with open(self.wallet_path, "w") as f:
            contents = f.write(contents)

        storage = WalletStorage(self.wallet_path)
        self.assertEqual("b", storage.get("a"))
        self.assertEqual("d", storage.get("c"))

    def test_write_dictionnary_to_file(self):

        storage = WalletStorage(self.wallet_path)

        some_dict = {"a":"b", "c":"d"}
        expected_config = {"BTC": some_dict}

        for key, value in some_dict.items():
            storage.put(key, value)
        storage.write()

        contents = ""
        with open(self.wallet_path, "r") as f:
            contents = f.read()
        self.assertEqual(expected_config, json.loads(contents))


class TestBIP44Wallet(WalletTestCase):
    seed_text = "travel nowhere air position hill peace suffer parent beautiful rise blood power home crumble teach"
    password = "secret"

    def _open_wallet(self, chaincode='BTC'):
        active_chain = chainparams.get_chain_instance(chaincode)
        self.storage = WalletStorage(self.wallet_path, active_chain)
        self.wallet = BIP44_Wallet(self.storage)

    def _make_wallet(self, chaincode='BTC'):
        self._open_wallet(chaincode)
        self.wallet.add_seed(self.seed_text, self.password)
        self._setup_chain()

    def _setup_chain(self):
        self.wallet.create_master_keys(self.password)
        self.wallet.create_hd_account(self.password)

    def test_account_derivation(self):
        self._make_wallet()
        key = self.wallet.master_public_keys[self.wallet.root_name]
        # m/44'/0'
        self.assertEqual('xpub6Ar6Cfm9Ww2RJbvXDD6Xk4a5eztRTg1do1SKEDYgmd21mtmYYgeYbAp7uCKYMgVfezCLTpM2rn25Ma5Vhm5pRktzM1cspx9MQwMJNs21Tjm', key)
        self.assertEqual(2, len(self.wallet.accounts))
        self.wallet.create_next_account(self.password)
        self.assertEqual(3, len(self.wallet.accounts))

        account_keys = [
            ('0', 'xpub6C9nDygdSEeKU4g8wyEqeCWSRcBj4SdrHbXjvAaqJQbSLkvuTVA1G2sSzDfU64jQLWk1rb5jhajxdY1m5MCPqXSofx6VyPP1U5zEjSS3zmE'), # m/44'/0'/0'
            ('1', 'xpub6C9nDygdSEeKWUeFzqxD34LZ12R1RJQ3uzRi5sVVRDY2F5yiZR5wJ6iMJNh3wFhSyxJQNupsqiVv6dExobVwDE2gHsjnxTiHMVuNvs8WcEV'), # m/44'/0'/1'
            ('2', 'xpub6C9nDygdSEeKZnGtRYGykLPo8Djpv7qd8KXgoXhqiuoeorKfAHyH4rxwstTfi8cXUd32WanrkkTU9JT6Sn5tDrtpywBi7dBmKv5imKoQVvG'), # m/44'/0'/2'
        ]
        for acc, xpub in account_keys:
            self.assertEqual(xpub, self.wallet.accounts[acc].xpub)

        # Switch chains.
        self._open_wallet('MAZA')
        self._setup_chain()


        key = self.wallet.master_public_keys[self.wallet.root_name]
        # m/44'/13'
        self.assertEqual('xpub6Ar6Cfm9Ww2RrLB9i4ZJGcTtpyVxjocRcWUsmTjgukCWKDeC9pHisW6hjxEL3wSacTFHUkrxWtcAosu82dy1rMT8czZ6fE8oYTWqRbM8xng', key)
        self.assertEqual(2, len(self.wallet.accounts))
        self.wallet.create_next_account(self.password)
        self.assertEqual(3, len(self.wallet.accounts))

        account_keys = [
            ('0', 'xpub6DSVctpka27jHAYzzBAwvooCYY1TbKu1eopXrKJJsp8p3A8H6YPcxdSU2nUtJa12vkHPsauGmTEqLmESeg8rMvbxVUeEsJZe4yBS8qWad8J'), # m/44'/13'/0'
            ('1', 'xpub6DSVctpka27jMDufiQuVzPwk58gdAyWHMxyPB4jrGprW8r7hsKZK6uov4UM8h3mkdaARF5rw2ANemZbJXHjti9wiW7XxRaKhnjoLDtKSyBQ'), # m/44'/13'/1'
            ('2', 'xpub6DSVctpka27jPq7HtBubwzwdw6WeWQFkRHGUniCoJsqUUNeez2FCd7E7Gh6MZwhpQtGQu4M8NdkEE4zW8bGcAe9mjBaLkWWdqspQMmjr8iG'), # m/44'/13'/2'
        ]
        for acc, xpub in account_keys:
            self.assertEqual(xpub, self.wallet.accounts[acc].xpub)


        # Ensure the BTC section still exists.
        privkeys = self.wallet.storage.get_for_chain('BTC', 'master_public_keys')
        self.assertEqual('xpub6Ar6Cfm9Ww2RJbvXDD6Xk4a5eztRTg1do1SKEDYgmd21mtmYYgeYbAp7uCKYMgVfezCLTpM2rn25Ma5Vhm5pRktzM1cspx9MQwMJNs21Tjm', privkeys['x/'])

    def test_address_derivation(self):
        self._make_wallet()

        btc_keys = [
            ('0', ('1MSv1TDyqXnWj3symY2GPfA3znrkg6gSdE', '0220faa22f8c79d46eae54c7ab3047efc5da6201b8ca824339e99044339cb5c99f')),
            ('1', ('1JXC9JY5ADFawGcw6468sDq5CEEj4r9X2y', '02deeae5f964965749ccfc4acc32ceb3e66f65420d49f4a86c3742feb974662a5b')),
        ]
        for acc, expected in btc_keys:
            self.assertEqual(expected, self.wallet.accounts[acc].first_address())

        # Switch chains.
        self._open_wallet('MAZA')
        self._setup_chain()

        maza_keys = [
            ('0', ('MC6MWHWchmszHEeMEcqUDiPPYDBi9j8BgE', '03138a486f59642ad66eb221a0574e46857156aa130cb2a7b375c2a26046bb1bc5')),
            ('1', ('MF8hvu7NQNeK5mtxQERGoMx6JGx9GrZRiu', '029164d44867fb028b8300e7afb8dcd8c81bc8405a10d86a8a568b92fb2980646a')),
        ]
        for acc, expected in maza_keys:
            self.assertEqual(expected, self.wallet.accounts[acc].first_address())

class TestNewWallet(WalletTestCase):

    seed_text = "travel nowhere air position hill peace suffer parent beautiful rise blood power home crumble teach"
    password = "secret"

    first_account_name = "account1"

    import_private_key = "L52XzL2cMkHxqxBXRyEpnPQZGUs3uKiL3R11XbAdHigRzDozKZeW"
    import_key_address = "15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma"

    def setUp(self):
        super(TestNewWallet, self).setUp()
        self.storage = WalletStorage(self.wallet_path)
        self.wallet = NewWallet(self.storage)
        # This cannot be constructed by electrum at random, it should be safe
        # from eventual collisions.
        self.wallet.add_seed(self.seed_text, self.password)
        self.wallet.create_master_keys(self.password)
        self.wallet.create_hd_account(self.password)

    def test_wallet_with_seed_is_not_watching_only(self):
        self.assertFalse(self.wallet.is_watching_only())

    def test_wallet_without_seed_is_watching_only(self):
        # We need a new storage , since the default storage was already seeded
        # in setUp()
        new_dir = tempfile.mkdtemp()
        storage = WalletStorage(os.path.join(new_dir, "somewallet"))
        wallet = NewWallet(storage)
        self.assertTrue(wallet.is_watching_only())
        shutil.rmtree(new_dir)  # Don't leave useless stuff in /tmp

    def test_new_wallet_is_deterministic(self):
        self.assertTrue(self.wallet.is_deterministic())

    def test_get_seed_returns_correct_seed(self):
        self.assertEqual(self.wallet.get_seed(self.password), self.seed_text)

    def test_update_password(self):
        new_password = "secret2"
        self.wallet.update_password(self.password, new_password)
        self.wallet.get_seed(new_password)
