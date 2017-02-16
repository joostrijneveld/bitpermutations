import unittest
import squaring_mod_GF2N as sqGF2N
from bitpermutations.data import Register, ZERO


class TestSquaringModGF2N(unittest.TestCase):

    def test_square_350_701(self):
        src = [Register(256) for _ in range(3)]
        dst = [Register(256) for _ in range(3)]
        seq = sqGF2N.gen_sequence(350, 701)
        sqGF2N.sequence_to_registers(src, range(0, 701))

        sqGF2N.square_350_701(dst, src)
        result = sqGF2N.registers_to_sequence(dst)

        self.assertEqual(result, seq)

if __name__ == '__main__':
    unittest.main()
