from .data import (ZERO, ONE,
                   Register, MemoryFragment, DataFragment, IndicesMask)


def split_in_size_n(l, n):
    return [l[i:i + n] for i in range(0, len(l), n)]


def validate_operands(*operands):
    def wrapper(f):
        def decorated(*args, **kwargs):
            xmms = set()
            for i, (arg, (argtype, size)) in enumerate(zip(args, operands)):
                if not isinstance(arg, argtype):
                    raise Exception("Operand {} was of type '{}'"
                                    "instead of expected '{}'."
                                    .format(i, type(arg), argtype))
                if type(arg) is Register and arg.size != size:
                    if arg.size == 256 and size == 128:
                        xmms.add(i)
                if type(arg) is int and arg.bit_length() > size:
                    raise Exception("Operand {} was an {}-bit immediate"
                                    "instead of expected maximum of {}-bit."
                                    .format(i, arg.bit_length(), size))
                if type(arg) is str and len(arg) != size:
                    raise Exception("Operand {} was an {}-bit immediate"
                                    "instead of expected {} bits."
                                    .format(i, len(arg), size))
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
@validate_operands((Register, 256), (Register, 256), (int, 8))
def vpsllq(dest, source, n):
    """Shift Packed Data Left Logical, split on quadwords"""
    quads = split_in_size_n(source, 64)
    dest.value = sum(([ZERO] * n + x[:64-n] for x in quads), [])


@instruction
@validate_operands((Register, 256), (Register, 256), (int, 8))
def vpsrlq(dest, source, n):
    quads = split_in_size_n(source, 64)
    dest.value = sum((x[n:] + [ZERO] * n for x in quads), [])


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


def mask(r, m):
    return [x if i == ONE else ZERO for x, i in zip(r, m)]


@instruction
@validate_operands((Register, 256), (Register, 256), (DataFragment, 256))
def vpxor(dest, source1, source2):
    dest.value = _xor(source1, source2)


@instruction
@validate_operands((Register, 256), (Register, 256), (DataFragment, 256))
def vpand(dest, source1, source2):
    dest.value = mask(source1, source2)


@instruction
@validate_operands((Register, 256), (Register, 256), (DataFragment, 256))
def vpandn(dest, source1, source2):
    dest.value = mask(source1, [ONE if x is ZERO else ZERO for x in source2])


@instruction
@validate_operands((DataFragment, 64), (DataFragment, 64))
def xor(dest, source):
    if type(dest) is MemoryFragment and type(dest) is type(source):
        raise Exception("At least source or dest of xor must be a register.")
    dest.value = _xor(dest, source)


@instruction
@validate_operands((DataFragment, 64), (DataFragment, 64))
def iand(dest, source):
    """ Computes the and of two 64-bit data fragments """
    if type(dest) is MemoryFragment and type(dest) is type(source):
        raise Exception("At least source or dest of and must be a register.")
    dest.value = mask(dest, source)


@instruction
@validate_operands((Register, 256), (Register, 256), (str, 8))
def vpermq(dest, source, imm):
    quads = split_in_size_n(source, 64)
    indices = reversed(split_in_size_n(imm, 2))
    dest.value = sum([quads[int(i, 2)] for i in indices], [])


@instruction
@validate_operands((DataFragment, 128), (Register, 256), (int, 8))
def vextracti128(dest, source, imm):
    dest.value = (source[128:] if imm else source[:128]) + [ZERO]*128


@instruction
@validate_operands((Register, 256),
                   (Register, 256), (DataFragment, 128), (int, 8))
def vinserti128(dest, source1, source2, imm):
    if imm:
        dest.value = source2[:128] + source1[:128]
    else:
        dest.value = source1[:128] + source2[128:]


@instruction
@validate_operands((Register, 256), (Register, 256), (IndicesMask, 256))
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


@instruction
@validate_operands((Register, 256), (Register, 256), (int, 8),
                   (Register, 256), (Register, 256))
def macro_v256rol(dest, source, n, t0, t1):
    vpsrlq(t1, source, 64-n)
    vpsllq(t0, source, n)
    vpermq(dest, t1, '10010011')
    vpxor(dest, dest, t0)


__all__ = [name for name, f in locals().items() if hasattr(f, '_instruction')]
