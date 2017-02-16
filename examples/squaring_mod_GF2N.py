from bitpermutations.data import Register, ONE, ZERO, Mask, IndicesMask
import bitpermutations.instructions as x86


def gen_sequence(e, N):
    def interleave(seq):
        if len(seq) % 2 == 0:
            return [x for t in zip(seq[:len(seq) // 2],
                                   seq[len(seq) // 2:]) for x in t]
        else:
            return ([x for t in zip(seq[:len(seq) // 2],
                                    seq[len(seq) // 2 + 1:]) for x in t] +
                    [seq[len(seq) // 2]])
    seq = list(range(N))
    for i in range(e):
        seq = interleave(seq)
    return seq


def sequence_to_registers(dst, seq):
    seq = list(seq)
    for i, reg in enumerate(dst):
        if len(seq) >= reg.size:
            reg.value, seq = seq[:reg.size], seq[reg.size:]
        else:
            reg.value = seq + [ZERO] * (reg.size - len(seq))
            break
    else:
        if len(seq) > 0:
            print(seq)
            raise Exception("Sequence did not fit in registers; "
                            "{} elements remaining".format(len(seq)))


def registers_to_sequence(registers):
    result = sum((x.value for x in registers), [])
    while result[-1] is ZERO:
        result.pop()
        if not result:
            break
    return result


def square(dst, src):
    """ Expects three 256-bit registers containing the polynomial """
    pass


def square_350_701(dst, src):
    """ Requires source and destination registers to be disjunct. """
    r = src
    r_out = dst

    lowbitmask = Mask('0'*255 + '1')
    lowbitreg = Register()
    x86.vpand(lowbitreg, r[0], lowbitmask)

    x86.vpandn(r[0], r[0], lowbitmask)

    rest = Register()
    twobits = Register()
    nexttwobits = Register()
    mask0001 = Mask('0001')

    for i in range(2, -1, -1):
        x86.vpsllq(rest, r[i], 2)
        x86.vpsrlq(twobits, r[i], 62)
        x86.vpermq(twobits, twobits, '10010011')
        x86.vpand(nexttwobits, twobits, mask0001)
        x86.vpandn(twobits, twobits, mask0001)
        x86.vpxor(r[i], rest, twobits)
        if i + 1 < 3:
            x86.vpxor(r[i+1], r[i+1], nexttwobits)

    mask_bit_in_byte = [Mask(32 * ([ZERO]*i + [ONE] + [ZERO]*(7-i)))
                        for i in range(8)]
    bits = Register()
    accum = Register()

    for i in range(2, -1, -1):
        for j in range(8):
            x86.vpand(bits, r[i], mask_bit_in_byte[j])
            if j == 0:
                x86.vpshlq(accum, bits, 7 - 2*j)
            else:
                x86.vpshlq(bits, bits, 7 - 2*j)
                if j == 7:
                    x86.vpxor(r[i], accum, bits)
                else:
                    x86.vpxor(accum, accum, bits)

    x86.vpermq(lowbitreg, lowbitreg, '11001111')
    x86.vpshlq(lowbitreg, lowbitreg, 56)
    x86.vpxor(r[2], lowbitreg, r[2])

    indices = IndicesMask(list(range(15, -1, -1)) +
                          [None] * 8 + list(range(7, -1, -1)))
    x86.vpshufb(r_out[2], r[0], indices)
    x86.vpermq(r_out[2], r_out[2], '10010011')

    t1 = Register()

    for i in range(2):
        indices = IndicesMask([None] * 24 + list(range(15, 7, -1)))
        x86.vpshufb(r_out[1-i], r[i], indices)
        indices = IndicesMask(list(range(15, -1, -1)) +
                              list(range(7, -1, -1)) + [None] * 8)
        x86.vpshufb(t1, r[i+1], indices)
        x86.vpxor(r_out[1-i], t1, r_out[1-i])
        x86.vpermq(r_out[1-i], r_out[1-i], '11010010')


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
