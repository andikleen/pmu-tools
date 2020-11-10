# generic utilities for lists
import sys
from itertools import chain

if sys.version_info.major == 3:
    from itertools import zip_longest
else:
    from itertools import izip_longest
    zip_longest = izip_longest

def flatten(x):
    return list(chain(*x))

def filternot(p, l):
    return list(filter(lambda x: not p(x), l))

# add items from b to a if not already in a
def cat_unique(a, b):
    aset = set(a)
    add = [x for x in b if x not in aset]
    return a + add

# remove duplicates without reordering
def dedup(a):
    l = []
    prev = set()
    for j in a:
        if j not in prev:
            l.append(j)
            prev.add(j)
    return l

def not_list(l):
    return [not x for x in l]

# merge two dicts with appending lists
def append_dict(a, b):
    for k in b:
        if k in a:
            a[k] += b[k]
        else:
            a[k] = b[k]

def padlist(l, length, val=0.0):
    if len(l) < length:
        return l + [val]*(length-len(l))
    return l

def findprefix(l, prefix, stop=None):
    for i, v in enumerate(l):
        if v == stop:
            break
        if v.startswith(prefix):
            return i
    return -1
