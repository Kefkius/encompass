import unittest

from lib.util_coin import rev_hex, Hash
import ltc_scrypt
import neoscrypt

HashScrypt = lambda x: ltc_scrypt.getPoWHash(x)
HashNeoscrypt = lambda x: neoscrypt.getPoWHash(x)

class Test_hashes(unittest.TestCase):

    def test_neoscrypt(self):
        # feathercoin block 732700
        raw_block = '0200000082ad0f32d0dca2438ec33dd5eabd612fee6cd28559a37c34cc17a0d813f8b01ff2e7b7179c2b869dde5b5fa516e86187d599a15b05cda223b5407ec2b1ca802a8a946c55ad623f1cca6115000301000000010000000000000000000000000000000000000000000000000000000000000000ffffffff2d031c2e0b062f503253482f048a946c55086800169235000000132f474956452d4d452d434f494e532e636f6d2f0000000001a0d6d7dc010000001976a914cfd4166bf463109717ef6bda95a01c40e0ab9ba288ac000000000100000001e920ef6dd0f2395d6cb829f3b2a99dc067ede1bffbf57bb58622b65c9b1dd5f8000000006c493046022100b8b2cd44ae056b84bf9c3a887347af64d6974dba25e181f68a1db74a451c67bb0221008c8bcc2b001faf3c23fcd6064368afc1ca91000959e8759d26a701aced7cf6d40121038c3c33640db4a025f3ebefe5f3b705708236f5104b29d4a1eb60971d58d931c3ffffffff036dcf2719010000001976a914b6dabc407e13cfb474713c9c96e13a2f6c7d1b2888ac8379ce3d000000001976a91484b09afa67a69fc5ffa90e27359acde0b7309cb988ac1007e085000000001976a9145cbe3c20de96194fef74df5b5d9da6b5643b92cb88ac000000000100000001df8fed0c1602f3e57ef586a491f673bbd124c3751bd783effb9f2a3259b98f43010000006b4830450220375b6508a97f2d080b8bd380830565216e54d05f2e89fda96beb22e9624c2811022100e836367122271516dc43f34e88a4e1a2e14cc6263ba144ee83abf5bb7ec0d20f012102e355f533557054cd9df7465e762c9bb71ec85febe844acf12d83db4caf4f9408ffffffff021295e437000000001976a914545b159ee0c7593a4ccd79714caf08fe1b58cee388ac1c7a0f00000000001976a914a4af10954d9fd6556ed7e6d3d8b927bcac1cce4688ac00000000'
        actual_pow_hash = '00000000194b59f845a26aa4be535d6f645c502999b932faf62e9d4300c14bf5'

        self.assertEqual(actual_pow_hash, rev_hex(HashNeoscrypt(raw_block.decode('hex')).encode('hex')))
