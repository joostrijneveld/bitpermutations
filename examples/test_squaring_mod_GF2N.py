import unittest
import squaring_mod_GF2N as sqGF2N
from bitpermutations.data import Register, MemoryFragment


class TestSquaringModGF2N_patience(unittest.TestCase):

    def test_square_701_patience(self):
        src = [MemoryFragment(64, '{}(%rsi)'.format(i*8))for i in range(12)]
        dst = [MemoryFragment(64, '{}(%rdi)'.format(i*8)) for i in range(12)]
        for n in range(10):
            seq = sqGF2N.gen_sequence(n, 701)
            sqGF2N.sequence_to_registers(src, range(0, 701))

            sqGF2N.square_701_patience(dst, src, n)
            result = sqGF2N.registers_to_sequence(dst)

            if self.assertEqual(result, seq):
                break

    def test_square_701_patience_callee_save(self):
        src = [MemoryFragment(64, '{}(%rsi)'.format(i*8))for i in range(12)]
        dst = [MemoryFragment(64, '{}(%rdi)'.format(i*8)) for i in range(12)]
        seq = sqGF2N.gen_sequence(5, 701)
        sqGF2N.sequence_to_registers(src, range(0, 701))

        sqGF2N.square_701_patience(dst, src, 5, 5)
        result = sqGF2N.registers_to_sequence(dst)

        self.assertEqual(result, seq)


class TestSquaringModGF2N_permutations(unittest.TestCase):

    def test_square_1_701(self):
        src = [MemoryFragment(256, '{}(%rsi)'.format(i*32)) for i in range(3)]
        dst = [MemoryFragment(256, '{}(%rdi)'.format(i*32)) for i in range(3)]
        seq = sqGF2N.gen_sequence(1, 701)
        sqGF2N.sequence_to_registers(src, range(0, 701))

        sqGF2N.square_1_701(dst, src)
        result = sqGF2N.registers_to_sequence(dst)

        self.assertEqual(result, seq)

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
