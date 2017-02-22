from functools import wraps


def split_in_size_n(l, n):
    return [l[i:i + n] for i in range(0, len(l), n)]


def reg_to_memfunc(f, in_size, out_size, per_reg=256):
    """ Makes a function that operates on registers use memory instead. """

    # To prevent circular imports
    from .instructions import vmovdqu
    from .data import Register

    @wraps(f)
    def memfunc(out_data, in_data):
        src = [Register(per_reg) for _ in range(in_size)]
        dst = [Register(per_reg) for _ in range(out_size)]

        for reg, mem in zip(src, in_data):
            vmovdqu(reg, mem)
        f(dst, src)
        for mem, reg in zip(out_data, dst):
            vmovdqu(mem, reg)
    return memfunc
