# generic utilities for lists

from itertools import chain

def flatten(x):
    return list(chain(*x))

def filternot(p, l):
    return filter(lambda x: not p(x), l)

# add items from b to a if not already in a
def cat_unique(a, b):
    aset = set(a)
    add = [x for x in b if x not in aset]
    return a + add

# dedup a and keep b uptodate
def dedup2(a, b):
    aset = set()
    al = []
    bl = []
    for ai, bi in zip(a, b):
        if ai not in aset:
            al.append(ai)
            bl.append(bi)
            aset.add(ai)
    return al, bl

def not_list(l):
    return [not x for x in l]
