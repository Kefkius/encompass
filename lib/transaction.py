#!/usr/bin/env python
#
# Electrum - lightweight Bitcoin client
# Copyright (C) 2011 thomasv@gitorious
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


# Note: The deserialization code originally comes from ABE.


import bitcoin
from bitcoin import *
from util import print_error
from script import *
import time
import sys
import struct

import chainparams

NO_SIGNATURE = 'ff'

def parse_sig(x_sig):
    s = []
    for sig in x_sig:
        if sig[-2:] == '01':
            s.append(sig[:-2])
        else:
            assert sig == NO_SIGNATURE
            s.append(None)
    return s

def is_extended_pubkey(x_pubkey):
    return x_pubkey[0:2] in ['fe', 'ff']

def x_to_xpub(x_pubkey):
    if x_pubkey[0:2] == 'ff':
        from account import BIP32_Account
        xpub, s = BIP32_Account.parse_xpubkey(x_pubkey)
        return xpub


def parse_xpub(x_pubkey):
    if x_pubkey[0:2] in ['02','03','04']:
        pubkey = x_pubkey
    elif x_pubkey[0:2] == 'ff':
        from account import BIP32_Account
        xpub, s = BIP32_Account.parse_xpubkey(x_pubkey)
        pubkey = BIP32_Account.derive_pubkey_from_xpub(xpub, s[0], s[1])
    elif x_pubkey[0:2] == 'fe':
        from account import OldAccount
        mpk, s = OldAccount.parse_xpubkey(x_pubkey)
        pubkey = OldAccount.get_pubkey_from_mpk(mpk.decode('hex'), s[0], s[1])
    elif x_pubkey[0:2] == 'fd':
        addrtype = ord(x_pubkey[2:4].decode('hex'))
        hash160 = x_pubkey[4:].decode('hex')
        pubkey = None
        address = hash_160_to_bc_address(hash160, addrtype)
    else:
        raise BaseException("Cannnot parse pubkey")
    if pubkey:
        address = public_key_to_bc_address(pubkey.decode('hex'))
    return pubkey, address


def parse_scriptSig(d, bytes):
    try:
        decoded = [ x for x in script_GetOp(bytes) ]
    except Exception:
        # coinbase transactions raise an exception
        print_error("cannot find address in input script", bytes.encode('hex'))
        return

    # payto_pubkey
    match = [ opcodes.OP_PUSHDATA4 ]
    if match_decoded(decoded, match):
        sig = decoded[0][1].encode('hex')
        d['address'] = "(pubkey)"
        d['signatures'] = [sig]
        d['num_sig'] = 1
        d['x_pubkeys'] = ["(pubkey)"]
        d['pubkeys'] = ["(pubkey)"]
        return

    # non-generated TxIn transactions push a signature
    # (seventy-something bytes) and then their public key
    # (65 bytes) onto the stack:
    match = [ opcodes.OP_PUSHDATA4, opcodes.OP_PUSHDATA4 ]
    if match_decoded(decoded, match):
        sig = decoded[0][1].encode('hex')
        x_pubkey = decoded[1][1].encode('hex')
        try:
            signatures = parse_sig([sig])
            pubkey, address = parse_xpub(x_pubkey)
        except:
            import traceback
            traceback.print_exc(file=sys.stdout)
            print_error("cannot find address in input script", bytes.encode('hex'))
            return
        d['signatures'] = signatures
        d['x_pubkeys'] = [x_pubkey]
        d['num_sig'] = 1
        d['pubkeys'] = [pubkey]
        d['address'] = address
        return

    # p2sh transaction, m of n
    match = [ opcodes.OP_0 ] + [ opcodes.OP_PUSHDATA4 ] * (len(decoded) - 1)
    if not match_decoded(decoded, match):
        print_error("cannot find address in input script", bytes.encode('hex'))
        return
    x_sig = [x[1].encode('hex') for x in decoded[1:-1]]
    dec2 = [ x for x in script_GetOp(decoded[-1][1]) ]
    m = dec2[0][0] - opcodes.OP_1 + 1
    n = dec2[-2][0] - opcodes.OP_1 + 1
    op_m = opcodes.OP_1 + m - 1
    op_n = opcodes.OP_1 + n - 1
    match_multisig = [ op_m ] + [opcodes.OP_PUSHDATA4]*n + [ op_n, opcodes.OP_CHECKMULTISIG ]
    if not match_decoded(dec2, match_multisig):
        print_error("cannot find address in input script", bytes.encode('hex'))
        return
    x_pubkeys = map(lambda x: x[1].encode('hex'), dec2[1:-2])
    pubkeys = [parse_xpub(x)[0] for x in x_pubkeys]     # xpub, addr = parse_xpub()
    redeemScript = Transaction.multisig_script(pubkeys, m)
    # write result in d
    d['num_sig'] = m
    d['signatures'] = parse_sig(x_sig)
    d['x_pubkeys'] = x_pubkeys
    d['pubkeys'] = pubkeys
    d['redeemScript'] = redeemScript
    d['address'] = hash_160_to_bc_address(hash_160(redeemScript.decode('hex')), 5)




def get_address_from_output_script(bytes, active_chain=None):
    if active_chain is None:
        active_chain = chainparams.get_active_chain()
    decoded = [ x for x in script_GetOp(bytes) ]

    # The Genesis Block, self-payments, and pay-by-IP-address payments look like:
    # 65 BYTES:... CHECKSIG
    match = [ opcodes.OP_PUSHDATA4, opcodes.OP_CHECKSIG ]
    if match_decoded(decoded, match):
        return 'pubkey', decoded[0][1].encode('hex')

    # Pay-by-Bitcoin-address TxOuts look like:
    # DUP HASH160 20 BYTES:... EQUALVERIFY CHECKSIG
    match = [ opcodes.OP_DUP, opcodes.OP_HASH160, opcodes.OP_PUSHDATA4, opcodes.OP_EQUALVERIFY, opcodes.OP_CHECKSIG ]
    if match_decoded(decoded, match):
        return 'address', hash_160_to_bc_address(decoded[2][1], active_chain.p2pkh_version)

    # p2sh
    match = [ opcodes.OP_HASH160, opcodes.OP_PUSHDATA4, opcodes.OP_EQUAL ]
    if match_decoded(decoded, match):
        return 'address', hash_160_to_bc_address(decoded[1][1], active_chain.p2sh_version)

    return 'script', bytes





def parse_input(vds):
    d = {}
    prevout_hash = hash_encode(vds.read_bytes(32))
    prevout_n = vds.read_uint32()
    scriptSig = vds.read_bytes(vds.read_compact_size())
    d['scriptSig'] = scriptSig.encode('hex')
    sequence = vds.read_uint32()
    if prevout_hash == '00'*32:
        d['is_coinbase'] = True
    else:
        d['is_coinbase'] = False
        d['prevout_hash'] = prevout_hash
        d['prevout_n'] = prevout_n
        d['sequence'] = sequence
        d['pubkeys'] = []
        d['signatures'] = {}
        d['address'] = None
        if scriptSig:
            parse_scriptSig(d, scriptSig)
    return d


def parse_output(vds, i, active_chain=None):
    if active_chain is None:
        active_chain = chainparams.get_active_chain()
    d = {}
    d['value'] = vds.read_int64()
    scriptPubKey = vds.read_bytes(vds.read_compact_size())
    d['type'], d['address'] = get_address_from_output_script(scriptPubKey, active_chain)
    d['scriptPubKey'] = scriptPubKey.encode('hex')
    d['prevout_n'] = i
    return d


def deserialize(raw, active_chain=None):
    if active_chain is None:
        active_chain = chainparams.get_active_chain()
    vds = BCDataStream()
    vds.write(raw.decode('hex'))
    d = {}
    start = vds.read_cursor
    d['version'] = vds.read_int32()
    n_vin = vds.read_compact_size()
    d['inputs'] = list(parse_input(vds) for i in xrange(n_vin))
    n_vout = vds.read_compact_size()
    d['outputs'] = list(parse_output(vds,i, active_chain) for i in xrange(n_vout))
    d['lockTime'] = vds.read_uint32()
    return d


def push_script(x):
    return op_push(len(x)/2) + x


class Transaction:

    def __str__(self):
        if self.raw is None:
            self.raw = self.serialize()
        return self.raw

    def __init__(self, raw, active_chain=None):
        self.raw = raw.strip() if raw else None
        self.inputs = None
        if active_chain is None:
            active_chain = chainparams.get_active_chain()
        self.active_chain = active_chain

    def update(self, raw):
        self.raw = raw
        self.inputs = None
        self.deserialize()

    def update_signatures(self, raw):
        """Add new signatures to a transaction"""
        d = deserialize(raw)
        for i, txin in enumerate(self.inputs):
            sigs1 = txin.get('signatures')
            sigs2 = d['inputs'][i].get('signatures')
            for sig in sigs2:
                if sig in sigs1:
                    continue
                for_sig = Hash(self.tx_for_sig(i).decode('hex'))
                # der to string
                order = ecdsa.ecdsa.generator_secp256k1.order()
                r, s = ecdsa.util.sigdecode_der(sig.decode('hex'), order)
                sig_string = ecdsa.util.sigencode_string(r, s, order)
                pubkeys = txin.get('pubkeys')
                compressed = True
                for recid in range(4):
                    public_key = MyVerifyingKey.from_signature(sig_string, recid, for_sig, curve = SECP256k1)
                    pubkey = point_to_ser(public_key.pubkey.point, compressed).encode('hex')
                    if pubkey in pubkeys:
                        public_key.verify_digest(sig_string, for_sig, sigdecode = ecdsa.util.sigdecode_string)
                        j = pubkeys.index(pubkey)
                        print_error("adding sig", i, j, pubkey, sig)
                        self.inputs[i]['signatures'][j] = sig
                        self.inputs[i]['x_pubkeys'][j] = pubkey
                        break
        # redo raw
        self.raw = self.serialize()


    def deserialize(self):
        if self.raw is None:
            self.raw = self.serialize()
        if self.inputs is not None:
            return
        d = deserialize(self.raw, self.active_chain)
        self.inputs = d['inputs']
        self.outputs = [(x['type'], x['address'], x['value']) for x in d['outputs']]
        self.locktime = d['lockTime']
        return d

    @classmethod
    def from_io(klass, inputs, outputs, locktime=0):
        self = klass(None)
        self.inputs = inputs
        self.outputs = outputs
        self.locktime = locktime
        return self

    @classmethod
    def sweep(klass, privkeys, network, to_address, fee):
        inputs = []
        keypairs = {}
        for privkey in privkeys:
            pubkey = public_key_from_private_key(privkey)
            address = address_from_private_key(privkey)
            u = network.synchronous_get(('blockchain.address.listunspent',[address]))
            pay_script = klass.pay_script('address', address)
            for item in u:
                item['scriptPubKey'] = pay_script
                item['redeemPubkey'] = pubkey
                item['address'] = address
                item['prevout_hash'] = item['tx_hash']
                item['prevout_n'] = item['tx_pos']
                item['pubkeys'] = [pubkey]
                item['x_pubkeys'] = [pubkey]
                item['signatures'] = [None]
                item['num_sig'] = 1
            inputs += u
            keypairs[pubkey] = privkey

        if not inputs:
            return

        total = sum(i.get('value') for i in inputs) - fee
        outputs = [('address', to_address, total)]
        self = klass.from_io(inputs, outputs)
        self.sign(keypairs)
        return self

    @classmethod
    def multisig_script(klass, public_keys, m):
        n = len(public_keys)
        assert n <= 15
        assert m <= n
        op_m = format(opcodes.OP_1 + m - 1, 'x')
        op_n = format(opcodes.OP_1 + n - 1, 'x')
        keylist = [op_push(len(k)/2) + k for k in public_keys]
        return op_m + ''.join(keylist) + op_n + 'ae'

    @classmethod
    def pay_script(self, output_type, addr):
        if output_type == 'script':
            return addr.encode('hex')
        elif output_type == 'address':
            addrtype, hash_160 = bc_address_to_hash_160(addr)
            if addrtype == 0:
                script = '76a9'                                      # op_dup, op_hash_160
                script += push_script(hash_160.encode('hex'))
                script += '88ac'                                     # op_equalverify, op_checksig
            elif addrtype == 5:
                script = 'a9'                                        # op_hash_160
                script += push_script(hash_160.encode('hex'))
                script += '87'                                       # op_equal
            else:
                raise
        else:
            raise
        return script

    def input_script(self, txin, i, for_sig):
        # for_sig:
        #   -1   : do not sign, estimate length
        #   i>=0 : serialized tx for signing input i
        #   None : add all known signatures

        p2sh = txin.get('redeemScript') is not None
        num_sig = txin['num_sig'] if p2sh else 1
        address = txin['address']

        x_signatures = txin['signatures']
        signatures = filter(None, x_signatures)
        is_complete = len(signatures) == num_sig

        if for_sig in [-1, None]:
            # if we have enough signatures, we use the actual pubkeys
            # use extended pubkeys (with bip32 derivation)
            if for_sig == -1:
                # we assume that signature will be 0x48 bytes long
                pubkeys = txin['pubkeys']
                sig_list = [ "00" * 0x48 ] * num_sig
            elif is_complete:
                pubkeys = txin['pubkeys']
                sig_list = ((sig + '01') for sig in signatures)
            else:
                pubkeys = txin['x_pubkeys']
                sig_list = ((sig + '01') if sig else NO_SIGNATURE for sig in x_signatures)
            script = ''.join(push_script(x) for x in sig_list)
            if not p2sh:
                x_pubkey = pubkeys[0]
                if x_pubkey is None:
                    addrtype, h160 = bc_address_to_hash_160(txin['address'])
                    x_pubkey = 'fd' + (chr(addrtype) + h160).encode('hex')
                script += push_script(x_pubkey)
            else:
                script = '00' + script          # put op_0 in front of script
                redeem_script = self.multisig_script(pubkeys, num_sig)
                script += push_script(redeem_script)

        elif for_sig==i:
            script = txin['redeemScript'] if p2sh else self.pay_script('address', address)
        else:
            script = ''

        return script

    def BIP_LI01_sort(self):
        # See https://github.com/kristovatlas/rfc/blob/master/bips/bip-li01.mediawiki
        self.inputs.sort(key = lambda i: (i['prevout_hash'], i['prevout_n']))
        self.outputs.sort(key = lambda o: (o[2], self.pay_script(o[0], o[1])))

    def serialize(self, for_sig=None):
        inputs = self.inputs
        outputs = self.outputs
        s  = int_to_hex(1,4)                                         # version
        s += var_int( len(inputs) )                                  # number of inputs
        for i, txin in enumerate(inputs):
            s += txin['prevout_hash'].decode('hex')[::-1].encode('hex')   # prev hash
            s += int_to_hex(txin['prevout_n'], 4)                         # prev index
            script = self.input_script(txin, i, for_sig)
            s += var_int( len(script)/2 )                            # script length
            s += script
            s += "ffffffff"                                          # sequence
        s += var_int( len(outputs) )                                 # number of outputs
        for output in outputs:
            output_type, addr, amount = output
            s += int_to_hex( amount, 8)                              # amount
            script = self.pay_script(output_type, addr)
            s += var_int( len(script)/2 )                           #  script length
            s += script                                             #  script
        s += int_to_hex(0,4)                                        #  lock time
        if for_sig is not None and for_sig != -1:
            s += int_to_hex(1, 4)                                   #  hash type
        return s

    def tx_for_sig(self,i):
        return self.serialize(for_sig = i)

    def hash(self):
        return Hash(self.raw.decode('hex') )[::-1].encode('hex')

    def add_input(self, input):
        self.inputs.append(input)
        self.raw = None

    def input_value(self):
        return sum(x['value'] for x in self.inputs)

    def output_value(self):
        return sum( val for tp,addr,val in self.outputs)

    def get_fee(self):
        return self.input_value() - self.output_value()

    def signature_count(self):
        r = 0
        s = 0
        for txin in self.inputs:
            if txin.get('is_coinbase'):
                continue
            signatures = filter(None, txin.get('signatures',[]))
            s += len(signatures)
            r += txin.get('num_sig',-1)
        return s, r

    def is_complete(self):
        s, r = self.signature_count()
        return r == s

    def inputs_without_script(self):
        out = set()
        for i, txin in enumerate(self.inputs):
            if txin.get('scriptSig') == '':
                out.add(i)
        return out

    def inputs_to_sign(self):
        out = set()
        for txin in self.inputs:
            num_sig = txin.get('num_sig')
            if num_sig is None:
                continue
            x_signatures = txin['signatures']
            signatures = filter(None, x_signatures)
            if len(signatures) == num_sig:
                # input is complete
                continue
            for k, x_pubkey in enumerate(txin['x_pubkeys']):
                if x_signatures[k] is not None:
                    # this pubkey already signed
                    continue
                out.add(x_pubkey)
        return out

    def sign(self, keypairs):
        for i, txin in enumerate(self.inputs):
            num = txin['num_sig']
            for x_pubkey in txin['x_pubkeys']:
                signatures = filter(None, txin['signatures'])
                if len(signatures) == num:
                    # txin is complete
                    break
                if x_pubkey in keypairs.keys():
                    print_error("adding signature for", x_pubkey)
                    # add pubkey to txin
                    txin = self.inputs[i]
                    x_pubkeys = txin['x_pubkeys']
                    ii = x_pubkeys.index(x_pubkey)
                    sec = keypairs[x_pubkey]
                    pubkey = public_key_from_private_key(sec)
                    txin['x_pubkeys'][ii] = pubkey
                    txin['pubkeys'][ii] = pubkey
                    self.inputs[i] = txin
                    # add signature
                    for_sig = Hash(self.tx_for_sig(i).decode('hex'))
                    pkey = regenerate_key(sec)
                    secexp = pkey.secret
                    private_key = bitcoin.MySigningKey.from_secret_exponent( secexp, curve = SECP256k1 )
                    public_key = private_key.get_verifying_key()
                    sig = private_key.sign_digest_deterministic( for_sig, hashfunc=hashlib.sha256, sigencode = ecdsa.util.sigencode_der )
                    assert public_key.verify_digest( sig, for_sig, sigdecode = ecdsa.util.sigdecode_der)
                    txin['signatures'][ii] = sig.encode('hex')
                    self.inputs[i] = txin
        print_error("is_complete", self.is_complete())
        self.raw = self.serialize()


    def get_outputs(self):
        """convert pubkeys to addresses"""
        o = []
        for type, x, v in self.outputs:
            if type == 'address':
                addr = x
            elif type == 'pubkey':
                addr = public_key_to_bc_address(x.decode('hex'))
            else:
                addr = 'SCRIPT ' + x.encode('hex')
            o.append((addr,v))      # consider using yield (addr, v)
        return o

    def get_output_addresses(self):
        return [addr for addr, val in self.get_outputs()]


    def has_address(self, addr):
        return (addr in self.get_output_addresses()) or (addr in (tx.get("address") for tx in self.inputs))

    def as_dict(self):
        if self.raw is None:
            self.raw = self.serialize()
        self.deserialize()
        out = {
            'hex': self.raw,
            'complete': self.is_complete()
        }
        return out


    def requires_fee(self, wallet):
        # see https://en.bitcoin.it/wiki/Transaction_fees
        #
        # size must be smaller than 1 kbyte for free tx
        size = len(self.serialize(-1))/2
        if size >= 10000:
            return True
        # all outputs must be 0.01 BTC or larger for free tx
        for addr, value in self.get_outputs():
            if value < 1000000:
                return True
        # priority must be large enough for free tx
        threshold = 57600000
        weight = 0
        for txin in self.inputs:
            age = wallet.get_confirmations(txin["prevout_hash"])[0]
            weight += txin["value"] * age
        priority = weight / size
        print_error(priority, threshold)

        return priority < threshold
