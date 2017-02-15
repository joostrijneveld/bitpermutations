from bitpermutations.data import Register, ONE, ZERO, Mask
from bitpermutations.instructions import *


def gen_sequence(n):
    def interleave(seq):
        if len(seq) % 2 == 0:
            return [x for t in zip(seq[:len(seq) // 2],
                                   seq[len(seq) // 2:]) for x in t]
        else:
            return ([x for t in zip(seq[:len(seq) // 2],
                                    seq[len(seq) // 2 + 1:]) for x in t] +
                    [seq[len(seq) // 2]])
    seq = list(range(N))
    for i in range(n):
        seq = interleave(seq)
    return seq


def square(dst, src):
    """ Expects three 256-bit registers containing the polynomial """
    pass


def square_350_701(dst, src):
    """ Requires source and destination registers to be disjunct. """
    r = src
    r_out = dst

    lowbitmask = Mask('0'*255 + '1')
    lowbitreg = Register()
    vpand(lowbitreg, r[0], lowbitmask)

    vpandn(r[0], r[0], lowbitmask)

    rest = Register()
    twobits = Register()
    nexttwobits = Register()
    mask0001 = Mask('0001')

    for i in range(2, -1, -1):
        vpsllq(rest, r[i], 2)
        vpsrlq(twobits, r[i], 62)
        vpermq(twobits, twobits, '10010011')
        vpand(nexttwobits, twobits, mask0001)
        vpandn(twobits, twobits, mask0001)
        vpxor(r[i], rest, twobits)
        if i + 1 < 3:
            vpxor(r[i+1], r[i+1], nexttwobits)

    mask_bit_in_byte = [Mask(32 * ([ZERO]*i + [ONE] + [ZERO]*(7-i)))
                             for i in range(8)]
    bits = Register()
    accum = Register()

    for i in range(2, -1, -1):
        for j in range(8):
            vpand(bits, r[i], mask_bit_in_byte[j])
            if j == 0:
                vpshlq(accum, bits, 7 - 2*j)
            else:
                vpshlq(bits, bits, 7 - 2*j)
                if j == 7:
                    vpxor(r[i], accum, bits)
                else:
                    vpxor(accum, accum, bits)

    vpermq(lowbitreg, lowbitreg, '11001111')
    vpshlq(lowbitreg, lowbitreg, 56)
    vpxor(r[2], lowbitreg, r[2])

    indices = list(range(15, -1, -1)) + [None] * 8 + list(range(7, -1, -1))
    vpshufb(r_out[2], r[0], indices)
    vpermq(r_out[2], r_out[2], '10010011')

    t1 = Register()

    for i in range(2):
        indices = [None] * 24 + list(range(15, 7, -1))
        vpshufb(r_out[1-i], r[i], indices)
        mask = list(range(15, -1, -1)) + list(range(7, -1, -1)) + [None] * 8
        vpshufb(t1, r[i+1], mask)
        vpxor(r_out[1-i], t1, r_out[1-i])
        vpermq(r_out[1-i], r_out[1-i], '11010010')


if __name__ == '__main__':
    # TODO initialize from MemoryFragments instead
    src = [Register(256) for _ in range(3)]
    src[0].value = list(range(0, 256))
    src[1].value = list(range(256, 512))
    src[2].value = list(range(512, 701)) + [ZERO] * 67

    dst = [Register(256) for _ in range(3)]

    square_350_701(dst, src)

    for x in reversed(dst):
        print(x.printable(64))
