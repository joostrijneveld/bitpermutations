## Bit Permutations

The purpose of this project is to make it easier to write x86 assembly code that deals with complex bit permutations. When performing permutations on sequences of bits, it is hard to interpret the results and verify correctness (or spot errors).

Here, we do not look at the value of the bits, but instead keep track of their original location, making it much easier to follow progress.

Currently this also implies that bit values cannot be combined meaningfully; we focus purely on permutations, and do not support operations such as xoring two potentially non-zero values.
