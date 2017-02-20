
def split_in_size_n(l, n):
    return [l[i:i + n] for i in range(0, len(l), n)]
