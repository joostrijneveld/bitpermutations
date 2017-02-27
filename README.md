## Bit Permutations [![Build Status](https://travis-ci.org/joostrijneveld/bitpermutations.svg?branch=master)](https://travis-ci.org/joostrijneveld/bitpermutations)

The purpose of this project is to make it easier to write x86 assembly code that deals with complex bit permutations. When performing permutations on sequences of bits, it is hard to interpret the results and verify correctness (or spot errors).

We do not look at the value of the bits, but instead keep track of their original location, making it much easier to follow progress. Currently this also implies that bit values cannot be combined meaningfully; we focus purely on permutations, and do not support operations such as xoring two potentially non-zero values.

Functions written using the instructions provided by this package output assembly code that behaves identically -- there should be no need for manual instruction translation or register assignment.

### Applications

The reason for writing this package was to make it easier to write assembly code that performs multisquare operations on polynomials over GF2 modulo `X^701 - 1`, but the resulting code can be trivially modified to perform squarings in other fields with similar structure. The simple command-line interface makes it possible to generate the required assembly files from a Makefile. The code is included in the `applications` directory, and could also serve as an 'example of usage' for this package.

### Notes on usage

The use of this package is twofold: it simulates x86 assembly operations, and outputs the matching assembly code. It includes a set of instructions that operate on data types as `Register` and `MemoryFragment`. By performing such an instruction, its assembly representation is added to a list of instructions that can be printed, and the value in the respective data structure also modified accordingly. As these instructions are Python functions, however, there is room for all sorts of control logic before they are actually performed -- that's the interesting part!

In general, the data structures consist of two types: bit sequences (such as `Register`) and bit masks such as (`Mask`). Bit sequences contain integers arrays, while masks contain valuations (`ONE`, `ZERO` and `UNKNOWN`). Strict validation decorators prevent user-induced bugs by ensuring that instructions can only be called in meaningful ways, and will not allow operating on the 'wrong' data type. Note that, by design, this makes instruction signatures more restrictive than the standard instruction set.

When instantiating `Register` objects, they are allocated to an available register. This register is made available again when the last reference to the object is destroyed (e.g. when it is only used in limited function scope) or when it is explicitly freed using the `free()` method.

Assigning values to data structures can be done by setting a list to their `.value` attribute, typically done during initialization. The `utils.sequence_to_values` method provides an abstraction for this. While bits can be accessed by indexing the object, they cannot be dynamically set -- doing so would interfere with simulation. As one might expect, iteration over a data structure implicitly iterates over its value.

Naturally, the instruction set is far from complete. Whereas some instructions are semantically difficult to simulate when operating on labeled bits (rather than on values), others (or variants of existing instructions) are simply omitted because there was no immediate need to include them. Compatible extensions are always welcome.

### Wish-list

- It would be great to support rolling back instructions, as sometimes the most natural way to explore alternative routines is by walking down multiple paths, backtracking and comparing results. Currently this can be achieved by modifying the `INSTRUCTIONS` list directly, but this obviously breaks simulatability.
- Currently register allocation is still largely a manual process. While register name assignment is taken care of, the user still needs to manually ensure (and potentially hint, by means of `free()`) that sufficient free registers are available. Liveness analysis would be a considerable improvement (but is non-trivial, especially in combination with rollbacks).
