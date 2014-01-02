# utility functions

import bisect

def find_le(f, key):
    pos = bisect.bisect_left(f, (key,))
    if pos < len(f) and f[pos][0] == key:
        return f[pos]
    if pos == 0:
        return None
    return f[pos - 1]
