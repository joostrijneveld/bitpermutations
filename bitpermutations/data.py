
UNKNOWN = '?'
ZERO = '-'
ONE = '#'

tokens = [UNKNOWN, ZERO, ONE]


class DataFragmentMeta(type):

    def __str__(self):
        return "register or memory fragment"


class RegisterMeta(DataFragmentMeta):

    def __str__(self):
        return "register"


class MemoryFragmentMeta(DataFragmentMeta):

    def __str__(self):
        return "memory fragment"


class MaskMeta(DataFragmentMeta):

    def __str__(self):
        return "mask"


class DataFragment(metaclass=DataFragmentMeta):

    def __init__(self, size):
        self.size = size
        self._value = [UNKNOWN] * size

    def __iter__(self):
        yield from self._value

    def __len__(self):
        return self.size

    def __getitem__(self, i):
        return self._value[i]

    def __str__(self):
        return str(self._value)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        # TODO validation goes here
        if len(val) != self.size:
            raise Exception("Setting {} bits, but is of size {}"
                            .format(len(val), self.size))
        for x in val:
            if type(x) is not int and x not in tokens:
                raise Exception("Value contained unrecognized {}".format(x))
        self._value = [x for x in val]

    def printable(self, n=64):
        result = ""
        x = list(reversed(self._value))
        offset = 256 - len(x) % 256
        for i, a in enumerate(x):
            i += offset
            result += '{:^4}'.format(a)
            if i % 8 == 7:
                result += '|'
            if i % n == n-1:
                result += '\n'
        return result


class Register(DataFragment, metaclass=RegisterMeta):

    def __init__(self, size=256):
        super().__init__(size)


class MemoryFragment(DataFragment, metaclass=MemoryFragmentMeta):

    def __init__(self, size, value=None):
        super().__init__(size, size)
        if value:
            self._value = value
        else:
            self._value = [UNKNOWN] * size
        self.size = size


class Mask(DataFragment, metaclass=MaskMeta):

    def __init__(self, value, size=256):
        super().__init__(size)
        if size % len(value) != 0:
            raise Exception("Length of mask must divide its size")
        wsize = size // len(value)
        if type(value) is str:
            if any(x not in '01' for x in value):
                raise ValueError("Mask must consist of 0s and 1s")
            self.value = sum(([(ONE if x == '1' else ZERO)] * wsize
                              for x in reversed(value)), [])
        elif type(value) is list:
            if any(x not in [ONE, ZERO] for x in value):
                raise ValueError("Mask must consist of ONEs and ZEROs")
            self.value = sum(([x] * wsize for x in value), [])
        else:
            raise TypeError("Mask must be either string or list of bits")


class IndicesMask(Mask, metaclass=MaskMeta):

    def __init__(self, indices, size=256):
        if len(indices) is not size // 8:
            raise NotImplementedError("IndicesMask only supports byte indices")
        if any(type(x) is not int and x is not None for x in indices):
            raise TypeError("IndicesMask must contain indices or None-value")
        if any(x is not None and not 0 <= int(x) < size // 8 for x in indices):
            raise ValueError("Indices must be between 0 and number of bytes")
        self.size = size
        self.indices = indices

    def __getitem__(self, i):
        return self.indices[i]

    def __iter__(self):
        yield from self.indices

    def __len__(self):
        return self.size // 8
