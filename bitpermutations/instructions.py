from .data import (ZERO, ONE,
                   Register, MemoryFragment, DataFragment,
                   Mask, IndicesMask, MaskRegister)
from .utils import split_in_size_n

# This list collects asm of executed instructions
INSTRUCTIONS = []


def validate(*options):
    def wrapper(f):
        def decorated(*args, **kwargs):
            attempts = []
            for opt in options:
                xmms = set()
                try:
                    for i, (arg, (atype, size)) in enumerate(zip(args, opt)):
                        if not isinstance(arg, atype):
                            raise Exception(
                                "Operand {} was of type '{}' "
                                "instead of expected '{}'."
                                .format(i, type(arg), atype))
                        if type(arg) is Register and arg.size != size:
                            if arg.size == 256 and size == 128:
                                xmms.add(i)
                        if type(arg) is int and arg.bit_length() > size:
                            raise Exception(
                                "Operand {} was an {}-bit immediate "
                                "instead of expected max of {}-bit."
                                .format(i, arg.bit_length(), size))
                        if type(arg) is str and len(arg) != size:
                            raise Exception(
                                "Operand {} was an {}-bit immediate "
                                "instead of expected {} bits."
                                .format(i, len(arg), size))
                except Exception as e:
                    attempts.append(e)
            if len(attempts) == len(options):
                if len(attempts) > 1:
                    error_text = ["No options matched. Exceptions:"]
                    for e in attempts:
                        error_text += [str(e)]
                    raise Exception('\n'.join(error_text))
                elif len(attempts) == 1:
                    raise attempts[0]
            for i in xmms:
                # We have an ymm register, but have to pass xmm;
                args[i] = Register.xmm_from_ymm(args[i])
            return f(*args, **kwargs)
        return decorated
    return wrapper


def instruction(f):
    """ Decorator for instructions, to make selectively exporting possible. """
    f._instruction = True
    return f


@instruction
@validate(((DataFragment, 256), (Register, 256)),
          ((Register, 256), (DataFragment, 256)))
def vmovdqa(dest, source):
    dest.value = source.value
    INSTRUCTIONS.append(
        "vmovdqa {}, {}".format(source, dest)
    )


@instruction
@validate(((Register, 256), (Register, 256), (int, 8)))
def vpsllq(dest, source, n):
    """Shift Packed Data Left Logical, split on quadwords"""
    quads = split_in_size_n(source, 64)
    dest.value = sum(([ZERO] * n + x[:64-n] for x in quads), [])
    INSTRUCTIONS.append(
        "vpsllq ${}, {}, {}".format(n, source, dest)
    )


@instruction
@validate(((Register, 256), (Register, 256), (int, 8)))
def vpsrlq(dest, source, n):
    quads = split_in_size_n(source, 64)
    dest.value = sum((x[n:] + [ZERO] * n for x in quads), [])
    INSTRUCTIONS.append(
        "vpsrlq ${}, {}, {}".format(n, source, dest)
    )


@instruction
def vpshlq(dest, source, n):
    """ This generalization of vpsllq and vpsrlq supports negative shifts. """
    if n > 0:
        vpsllq(dest, source, n)
    elif n < 0:
        vpsrlq(dest, source, -1*n)


def _xor(r1, r2):
    r = []
    for i, (a, b) in enumerate(zip(r1, r2)):
        if a == b:
            r.append(ZERO)
        elif a != ZERO and b != ZERO:
            raise Exception(
                "bit {}: xoring two nonzero bits {} {}!".format(i, a, b))
        elif a != ZERO:
            r.append(a)
        else:
            r.append(b)
    return r


def mask(mask, register):
    return [x if i == ONE else ZERO for i, x in zip(mask, register)]


@instruction
@validate(((Register, 256), (Register, 256), (DataFragment, 256)))
def vpxor(dest, source1, source2):
    dest.value = _xor(source1, source2)
    INSTRUCTIONS.append(
        "vpxor {}, {}, {}".format(source2, source1, dest)
    )


@instruction
@validate(((Register, 256), (MaskRegister, 256), (DataFragment, 256)),
          ((Register, 256), (Register, 256), (Mask, 256)))
def vpand(dest, source1, source2):
    dest.value = mask(source1, source2)
    INSTRUCTIONS.append(
        "vpand {}, {}, {}".format(source2, source1, dest)
    )


@instruction
@validate(((Register, 256), (MaskRegister, 256), (DataFragment, 256)),
          ((Register, 256), (Register, 256), (Mask, 256)))
def vpandn(dest, source1, source2):
    dest.value = mask([ONE if x is ZERO else ZERO for x in source1], source2)
    INSTRUCTIONS.append(
        "vpandn {}, {}, {}".format(source2, source1, dest)
    )


@instruction
@validate(((DataFragment, 64), (DataFragment, 64)))
def xor(dest, source):
    if type(dest) is MemoryFragment and type(dest) is type(source):
        raise Exception("At least source or dest of xor must be a register.")
    dest.value = _xor(dest, source)


@instruction
@validate(((DataFragment, 64), (DataFragment, 64)))
def iand(dest, source):
    """ Computes the and of two 64-bit data fragments """
    if type(dest) is MemoryFragment and type(dest) is type(source):
        raise Exception("At least source or dest of and must be a register.")
    dest.value = mask(dest, source)


@instruction
@validate(((Register, 256), (Register, 256), (str, 8)))
def vpermq(dest, source, imm):
    quads = split_in_size_n(source, 64)
    indices = reversed(split_in_size_n(imm, 2))
    dest.value = sum([quads[int(i, 2)] for i in indices], [])
    INSTRUCTIONS.append(
        "vpermq ${}, {}, {}".format(int(imm, 2), source, dest)
    )


@instruction
@validate(((DataFragment, 128), (Register, 256), (int, 8)))
def vextracti128(dest, source, imm):
    dest.value = (source[128:] if imm else source[:128]) + [ZERO]*128
    INSTRUCTIONS.append(
        "vextracti128 ${}, {}, {}".format(imm, source, dest)
    )


@instruction
@validate(((Register, 256), (Register, 256), (DataFragment, 128), (int, 8)))
def vinserti128(dest, source1, source2, imm):
    if imm:
        dest.value = source2[:128] + source1[:128]
    else:
        dest.value = source1[:128] + source2[128:]
    INSTRUCTIONS.append(
        "vinserti128 ${}, {}, {}, {}".format(imm, source2, source1, dest)
    )


@instruction
@validate(((Register, 256), (Register, 256), (IndicesMask, 256)))
def vpshufb(dest, source, indices):
    xmms = split_in_size_n(source, 128)
    xmm_bytes = [split_in_size_n(x, 8) for x in xmms]
    r_out = [[None] * 16, [None] * 16]
    index_bytes = split_in_size_n(indices, 16)
    for i, indices_xmm in enumerate(index_bytes):
        for j, index in enumerate(indices_xmm):
            if index is None:
                r_out[i][j] = [ZERO] * 8
            elif 0 <= index < 16:
                r_out[i][j] = xmm_bytes[i][index]
            else:
                raise ValueError("Can only access bytes between 0 to 16")
    dest.value = sum(sum(r_out, []), [])
    INSTRUCTIONS.append(
        "vpshufb {}, {}, {}".format(indices, source, dest)
    )


@instruction
@validate(((Register, 256), (Register, 256), (int, 8),
           (Register, 256), (Register, 256)))
def macro_v256rol(dest, source, n, t0, t1):
    vpsrlq(t1, source, 64-n)
    vpsllq(t0, source, n)
    vpermq(dest, t1, '10010011')
    vpxor(dest, dest, t0)


__all__ = [name for name, f in locals().items() if hasattr(f, '_instruction')]
