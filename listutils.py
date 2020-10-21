# generic utilities for lists

from itertools import chain

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
