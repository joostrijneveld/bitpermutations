from bitpermutations.data import (ONE, ZERO,
                                  Register, Mask, IndicesMask, MaskRegister,
                                  AllocationError)
import bitpermutations.instructions as x86
from bitpermutations.printing import print_reg_to_memfunc, print_memfunc
from bitpermutations.utils import reg_to_memfunc, split_in_size_n
import argparse
import functools
from collections import OrderedDict


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
            raise Exception("Sequence did not fit in registers; "
                            "{} elements remaining".format(len(seq)))


def registers_to_sequence(registers):
    result = sum((x.value for x in registers), [])
    while result[-1] is ZERO:
        result.pop()
        if not result:
            break
    return result


def square_1_701(out_data, in_data):
    """ Operates on MemoryFragments containing the polynomials """

    r = Register()

    r_out = [Register() for _ in range(3)]
    r_out_b = [Register() for _ in range(3)]
    r_out_c = [Register() for _ in range(3)]
    result = [Register() for _ in range(3)]

    t1 = Register()
    t2 = Register()
    shifted = t3 = Register()

    for i in range(2, -1, -1):
        x86.vmovdqu(r, in_data[i])
        for j in range(0, 8):
            x86.macro_v256rol(shifted, r, j, t1, t2)
            if i == 0:
                if j < 4:
                    if j == 0:
                        mask = '00000001' * 32
                    if j == 1:
                        mask = '00000100' * 32
                    if j == 2:
                        mask = '00010000' * 32
                    if j == 3:
                        mask = '01000000' * 32

                    if j == 0:
                        x86.vpand(r_out[i], shifted, Mask(mask))
                    else:
                        x86.vpand(t1, shifted, Mask(mask))
                        x86.vpxor(r_out[i], r_out[i], t1)
                elif 4 <= j < 8:
                    if j == 4:
                        mask = '00000001' * 32
                    if j == 5:
                        mask = '00000100' * 32
                    if j == 6:
                        mask = '00010000' * 32
                    if j == 7:
                        mask = '01000000' * 32

                    if j == 4:
                        x86.vpand(r_out_b[i], shifted, Mask(mask))
                    else:
                        x86.vpand(t1, shifted, Mask(mask))
                        x86.vpxor(r_out_b[i], r_out_b[i], t1)
            if i == 1:
                if j < 4:
                    if j == 0:
                        mask = '00100000' * 19 + '00100000' + '00000001' * 12
                    if j == 1:
                        mask = '10000000' * 19 + '10000000' + '00000100' * 12
                    if j == 2:
                        mask = '00000000' * 19 + '00000000' + '00010000' * 12
                    if j == 3:
                        mask = '00000000' * 19 + '00000000' + '01000000' * 12

                    if j == 0:
                        x86.vpand(r_out[i], shifted, Mask(mask))
                    else:
                        x86.vpand(t1, shifted, Mask(mask))
                        x86.vpxor(r_out[i], r_out[i], t1)
                if 2 <= j < 6:
                    if j == 2:
                        mask = '00000010' * 19 + '00000010' + '00000000' * 11 + '00000010'  # noqa: E501
                    if j == 3:
                        mask = '00001000' * 19 + '00001000' + '00000000' * 12
                    if j == 4:
                        mask = '00100000' * 19 + '00100000' + '00000000' * 12
                    if j == 5:
                        mask = '10000000' * 19 + '10000000' + '00000000' * 12

                    if j == 2:
                        x86.vpand(r_out_b[i], shifted, Mask(mask))
                    else:
                        x86.vpand(t1, shifted, Mask(mask))
                        x86.vpxor(r_out_b[i], r_out_b[i], t1)
                if 4 <= j < 8:
                    if j == 4:
                        mask = '00000000' * 19 + '00000001' + '00000001' * 11 + '00000000'  # noqa: E501
                    if j == 5:
                        mask = '00000000' * 19 + '00000100' + '00000100' * 11 + '00000000'  # noqa: E501
                    if j == 6:
                        mask = '00000010' * 19 + '00010000' + '00010000' * 11 + '00000010'  # noqa: E501
                    if j == 7:
                        mask = '00001000' * 19 + '00000000' + '01000000' * 11 + '00001000'  # noqa: E501

                    if j == 4:
                        x86.vpand(r_out_c[i], shifted, Mask(mask))
                    else:
                        x86.vpand(t1, shifted, Mask(mask))
                        x86.vpxor(r_out_c[i], r_out_c[i], t1)

            if i == 2:
                if j < 2:
                    if j == 0:
                        mask = '00100000' * 32
                    if j == 1:
                        mask = '10000000' * 32

                    if j == 0:
                        x86.vpand(r_out[i], shifted, Mask(mask))
                    else:
                        x86.vpand(t1, shifted, Mask(mask))
                        x86.vpxor(r_out[i], r_out[i], t1)
                if 2 <= j < 6:
                    if j == 2:
                        mask = '00000010' * 32
                    if j == 3:
                        mask = '00001000' * 32
                    if j == 4:
                        mask = '00100000' * 32
                    if j == 5:
                        mask = '10000000' * 32

                    if j == 2:
                        x86.vpand(r_out_b[i], shifted, Mask(mask))
                    else:
                        x86.vpand(t1, shifted, Mask(mask))
                        x86.vpxor(r_out_b[i], r_out_b[i], t1)
                if 6 <= j < 8:
                    if j == 6:
                        mask = '00000010' * 32
                    if j == 7:
                        mask = '00001000' * 32

                    if j == 6:
                        x86.vpand(r_out_c[i], shifted, Mask(mask))
                    else:
                        x86.vpand(t1, shifted, Mask(mask))
                        x86.vpxor(r_out_c[i], r_out_c[i], t1)

    # move bit 511 to r_out_b[2]
    x86.vpand(t1, r_out_b[1], Mask('0001'))
    x86.vpxor(r_out_b[2], r_out_b[2], t1)

    highbyte_mask = Mask(2 * ('1' + '0' * 15))
    highbyte_nmask = Mask(2 * ('0' + '1' * 15))

    mask = IndicesMask(2*sum(zip(range(8), [None] * 8), ()))
    x86.vpshufb(result[0], r_out[0], mask)

    mask = IndicesMask(2*sum(zip([None] * 8, range(1, 9)), ()))
    x86.vpshufb(t1, r_out_b[0], mask)
    x86.vpxor(result[0], t1, result[0])

    x86.vextracti128(result[1], result[0], 1)
    mask = IndicesMask(2*sum(zip(range(8, 16), [None] * 8), ()))
    x86.vpshufb(result[2], r_out[0], mask)

    mask = IndicesMask(2*(sum(zip([None] * 8, range(9, 16)), ()) + (None, 0)))
    x86.vpshufb(t1, r_out_b[0], mask)
    x86.vpand(t2, t1, highbyte_mask)
    x86.vpand(t1, t1, highbyte_nmask)
    x86.vpermq(t2, t2, '01001100')
    x86.vpxor(t1, t1, t2)
    x86.vpxor(result[2], t1, result[2])

    x86.vinserti128(result[0], result[0], result[2], 1)
    x86.vextracti128(t1, result[2], 1)
    x86.vinserti128(result[1], result[1], t1, 1)

    # ---

    mask = IndicesMask(sum(zip(range(8), [None] * 8), ()) +
                       sum(zip([None] * 8, range(8), ), ()))
    x86.vpshufb(result[2], r_out[1], mask)

    mask = IndicesMask(2*sum(zip([None] * 8, range(1, 9)), ()))
    x86.vpshufb(t1, r_out_c[1], mask)
    x86.vpxor(result[2], t1, result[2])

    mask = IndicesMask((None,)*16+sum(zip(range(8), [None] * 8), ()))
    x86.vpshufb(t1, r_out_b[1], mask)
    x86.vpxor(result[2], t1, result[2])

    x86.vextracti128(t2, result[2], 1)
    x86.vpermq(t2, t2, '11010011')
    x86.vpxor(result[0], t2, result[0])

    mask = IndicesMask(sum(zip(range(8, 12), [None] * 8), ()) +
                       sum(zip([None] * 8, range(12, 16)), ()) +
                       sum(zip([None] * 8, range(8, 16), ), ()))
    x86.vpshufb(t1, r_out[1], mask)

    mask = IndicesMask(2*(sum(zip([None] * 7, range(9, 16)), ()) + (None, 0)))
    x86.vpshufb(t2, r_out_c[1], mask)
    x86.vpand(t3, t2, highbyte_mask)
    x86.vpand(t2, t2, highbyte_nmask)
    x86.vpermq(t3, t3, '01001100')
    x86.vpxor(t2, t3, t2)
    x86.vpxor(t1, t1, t2)

    mask = IndicesMask(2*sum(zip(range(8, 16), [None] * 8), ()))
    x86.vpshufb(t2, r_out_b[1], mask)
    x86.vpxor(t2, t2, t1)
    x86.vpand(t3, t2, Mask('0001'))
    x86.vinserti128(result[2], result[2], t3, 1)
    # complete first 0-350

    x86.vpand(t1, t2, Mask('0110'))
    x86.vpermq(t1, t1, '10000001')
    x86.vpxor(result[0], result[0], t1)

    x86.vpand(t1, t2, Mask('1000'))
    x86.vpermq(t1, t1, '00000011')
    x86.vpxor(result[1], t1, result[1])

    mask = IndicesMask(2*sum(zip(range(8), [None] * 8), ()))
    x86.vpshufb(t1, r_out_b[2], mask)

    mask = IndicesMask(2*sum(zip([None] * 8, range(1, 9)), ()))
    x86.vpshufb(t2, r_out_c[2], mask)
    x86.vpxor(t1, t1, t2)

    mask = IndicesMask(2*sum(zip([None] * 8, range(8)), ()))
    x86.vpshufb(t2, r_out[2], mask)
    x86.vpxor(t1, t1, t2)

    x86.vinserti128(t3, t3, t1, 0)
    x86.vpermq(t3, t3, '11010011')
    x86.vpxor(result[1], t3, result[1])

    x86.vextracti128(t3, t1, 1)
    x86.vpermq(t3, t3, '11010011')
    x86.vpxor(result[2], t3, result[2])

    mask = IndicesMask(2*sum(zip(range(8, 16), [None] * 8), ()))
    x86.vpshufb(t1, r_out_b[2], mask)

    mask = IndicesMask(2*sum(zip([None] * 8, range(8, 16)), ()))
    x86.vpshufb(t2, r_out[2], mask)
    x86.vpxor(t1, t1, t2)

    mask = IndicesMask(2*(sum(zip([None] * 7, range(9, 16)), ()) + (None, 0)))
    x86.vpshufb(t2, r_out_c[2], mask)
    x86.vpand(t3, t2, highbyte_mask)
    x86.vpand(t2, t2, highbyte_nmask)
    x86.vpermq(t3, t3, '01001100')
    x86.vpxor(t2, t3, t2)
    x86.vpxor(t1, t2, t1)

    x86.vpermq(t2, t1, '00111111')
    x86.vpxor(result[1], result[1], t2)

    x86.vpermq(t3, t1, '11111101')
    x86.vpxor(result[2], result[2], t3)

    for i in range(3):
        x86.vmovdqu(out_data[i], result[i])


def square_350_701(dst, src):
    """ Requires source and destination registers to be disjunct. """
    r = src
    r_out = dst

    maskreg = MaskRegister()
    lowbitmask = Mask('0'*255 + '1')
    x86.vmovdqa(maskreg, lowbitmask)

    lowbitreg = Register()
    x86.vpand(lowbitreg, maskreg, r[0])
    x86.vpandn(r[0], maskreg, r[0])

    rest = Register()
    twobits = Register()
    nexttwobits = Register()
    mask0001 = Mask('0001')
    x86.vmovdqa(maskreg, mask0001)

    for i in range(2, -1, -1):
        x86.vpsllq(rest, r[i], 2)
        x86.vpsrlq(twobits, r[i], 62)
        x86.vpermq(twobits, twobits, '10010011')
        x86.vpand(nexttwobits, maskreg, twobits)
        x86.vpandn(twobits, maskreg, twobits)
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


def square_701_patience(out_data, in_data, n):
    x = list(range(701)) + 3*[ZERO]

    regs = split_in_size_n(x, 64)

    seq = gen_sequence(n, 701) + 3*[ZERO]
    seq_r = split_in_size_n(seq, 64)

    moved = [False] * len(seq_r)

    r = Register(64)
    t1 = Register(64)

    maskcache = OrderedDict()

    def mask_to_register(mask):
        mask = Mask.as_immediate(mask)
        if mask in maskcache:
            maskcache.move_to_end(mask)
            return maskcache[mask]
        try:
            maskreg = MaskRegister(64, mask)
        except AllocationError:
            _, maskreg = maskcache.popitem(False)
        x86.mov(maskreg, mask)
        maskcache[mask] = maskreg
        return maskreg

    for j, inreg in enumerate(regs):
        x86.mov(r, in_data[j])
        for i, seqreg in enumerate(seq_r):
            piledict = {}
            for rotation in range(64):
                ror_seqreg = seqreg[rotation:] + seqreg[:rotation]
                piles = []
                overlap = [x for x in ror_seqreg if x in inreg and x != ZERO]
                for x in overlap:
                    for pile in piles:
                        try:
                            if pile[-1] <= x:
                                pile.append(x)
                                break
                        except IndexError:  # pile is empty
                            pass
                    else:  # doesn't fit on any existing pile: start a new pile
                        piles.append([x])
                piledict[rotation] = piles
            min_pile_key = min(piledict, key=lambda x: len(piledict.get(x)))
            if len(piledict[0]) == len(piledict[min_pile_key]):
                min_pile_key = 0
            if min_pile_key > 0:
                ror_seqreg = seqreg[min_pile_key:] + seqreg[:min_pile_key]
            else:
                ror_seqreg = seqreg

            for pile in piledict[min_pile_key]:
                emask = [ZERO] * 64
                for bit in pile:
                    emask[inreg.index(bit)] = ONE
                dmask = [ZERO] * 64
                for bit in pile:
                    dmask[ror_seqreg.index(bit)] = ONE

                # For consecutive bits, we do not even need pext/pdep
                if (Mask.consec(dmask) and Mask.consec(emask) and
                    (Mask.degree(emask) <= 31 or Mask.degree(dmask) <= 31)):
                    delta = (Mask.degree(dmask) - Mask.degree(emask)) % 64
                    x86.mov(t1, r)
                    if Mask.degree(emask) <= 31:
                        x86.iand(t1, Mask.as_immediate(emask))
                        x86.rol(t1, delta + min_pile_key)
                        min_pile_key = 0  # to avoid two rols
                    else:
                        x86.rol(t1, delta)
                        x86.iand(t1, Mask.as_immediate(dmask))
                else:
                    # if we can extract using AND instead..
                    if Mask.consec(emask, True) and Mask.degree(emask) <= 31:
                        x86.mov(t1, r)
                        x86.iand(t1, Mask.as_immediate(emask))
                    else:
                        x86.pext(t1, r, mask_to_register(emask))
                    x86.pdep(t1, t1, mask_to_register(dmask))

                if min_pile_key > 0:
                    x86.rol(t1, min_pile_key)
                if moved[i]:  # stored per i, as it's not the outer loop
                    x86.xor(out_data[i], t1)
                else:
                    x86.mov(out_data[i], t1)
                    moved[i] = True
    x86.movq(out_data[11], 0)  # to fill up all 768 bits


if __name__ == '__main__':
    permutations = {
        1: square_1_701,
        350: reg_to_memfunc(square_350_701, 3, 3),
    }

    parser = argparse.ArgumentParser(description='Output squaring routines.')
    parser.add_argument('no_of_squarings', type=int,
                        help='the number of repeated squarings')
    parser.add_argument('--patience', dest='patience', action='store_true',
                        help='always use the patience-sort method')
    parser.set_defaults(patience=False)

    args = parser.parse_args()
    if args.no_of_squarings in permutations and not args.patience:
        f = permutations[args.no_of_squarings]
        print_memfunc(f, 3, 3)
    else:
        f = functools.partial(square_701_patience, n=args.no_of_squarings)
        f.__name__ = "square_{}_701_patience".format(args.no_of_squarings)
        print_memfunc(f, 12, 12, per_reg=64)
