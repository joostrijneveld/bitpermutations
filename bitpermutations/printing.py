from .data import Register, MemoryFragment
import bitpermutations.instructions as instructions
import bitpermutations.data as data
from .instructions import vmovdqu


def print_reg_to_memfunc(f, in_size, out_size, per_reg=256):
    """Wraps a function that operates on registers in .data and .text sections,
    and makes it operate on memory fragments instead."""

    in_data = [MemoryFragment(per_reg, '{}(%rsi)'.format(per_reg*i // 8))
               for i in range(in_size)]
    out_data = [MemoryFragment(per_reg, '{}(%rdi)'.format(per_reg*i // 8))
                for i in range(in_size)]
    src = [Register(per_reg) for _ in range(in_size)]
    dst = [Register(per_reg) for _ in range(out_size)]

    instructions.INSTRUCTIONS = []
    data.DATASECTION = []

    for reg, mem in zip(src, in_data):
        vmovdqu(reg, mem)
    f(dst, src)
    for mem, reg in zip(out_data, dst):
        vmovdqu(mem, reg)

    print(".data")
    print(".align 32")
    for mask in data.DATASECTION:
        print(mask.data())

    print(".text")
    print(".att_syntax prefix")
    print(".global {}".format(f.__name__))

    print("{}:".format(f.__name__))
    for ins in instructions.INSTRUCTIONS:
        print(ins)

    print("ret")
