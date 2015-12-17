import unittest
from lib import script

import pprint

class TestBCDataStream(unittest.TestCase):

    def test_compact_size(self):
        s = script.BCDataStream()
        values = [0, 1, 252, 253, 2**16-1, 2**16, 2**32-1, 2**32, 2**64-1]
        for v in values:
            s.write_compact_size(v)

        with self.assertRaises(script.SerializationError):
            s.write_compact_size(-1)

        self.assertEquals(s.input.encode('hex'),
                          '0001fcfdfd00fdfffffe00000100feffffffffff0000000001000000ffffffffffffffffff')
        for v in values:
            self.assertEquals(s.read_compact_size(), v)

        with self.assertRaises(IndexError):
            s.read_compact_size()

    def test_string(self):
        s = script.BCDataStream()
        with self.assertRaises(script.SerializationError):
            s.read_string()

        msgs = ['Hello', ' ', 'World', '', '!']
        for msg in msgs:
            s.write_string(msg)
        for msg in msgs:
            self.assertEquals(s.read_string(), msg)

        with self.assertRaises(script.SerializationError):
            s.read_string()

    def test_bytes(self):
        s = script.BCDataStream()
        s.write('foobar')
        self.assertEquals(s.read_bytes(3), 'foo')
        self.assertEquals(s.read_bytes(2), 'ba')
        self.assertEquals(s.read_bytes(4), 'r')
        self.assertEquals(s.read_bytes(1), '')

    def test_vector(self):
        s = script.BCDataStream()
        # Four int32 values
        raw = '04000000000100000005000000f4010000'
        expected = [0, 1, 5, 500]
        s.write(raw.decode('hex'))
        # Test deserialization

        def parse_item(vds):
            return vds.read_int32()

        self.assertEquals(s.read_vector(parse_item), expected)

        # Test serialization
        s.clear()

        def write_item(item, vds):
            vds.write_int32(item)

        s.write_vector(expected, write_item)
        self.assertEquals(s.input.encode('hex'), raw)
