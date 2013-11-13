#!/usr/bin/python
# Import perf.data into a pandas DataFrame
import pandas as pd
import numpy as np
import perfdata
from collections import defaultdict, Counter
import bisect
import elf

#
# TBD 
# fix all types
# extra table for threads
# flatten callchains and branch_stack
# expand registers, stack
# represent other metadata
# s/w trace points
# 

ignored = ('type', 'start', 'end', '__recursion_lock__', 'ext_reserved',
           'header_end', 'end_event', 'offset')

def lookup(m, ip):
    i = bisect.bisect_left(m, (ip,))
    if i < len(m) and m[i][0] == ip:
        mr = m[i]
    elif i == 0:
        return None, 0
    else:
        mr = m[i - 1]
    return mr, ip - mr[0] 

def resolve(maps, pid, ip):
    if not maps[pid]:
        # xxx kernel
        return None, 0
    m, offset = lookup(maps[pid], ip)
    if not m or offset >= m[1]:
        # look up kernel
        m, offset = lookup(maps[-1], ip)
        if offset >= m[1]:
            return None, 0
    assert ip >= m[0] and ip < m[0] + m[1]
    return m[2], offset

def do_add(d, u, k, i):
    d[k].append(i)
    u[k] += 1

def samples_to_df(h):
    ev = perfdata.get_events(h)
    index = []
    data = defaultdict(list)
    procs = dict()

    maps = defaultdict(list)
    pnames = defaultdict(str)
    used = Counter()

    # comm do not necessarily appear in order
    # first build queue of comm in order
    updates = []
    for j in ev:
        # no time stamp: assume it's synthesized and kernel
        if j.type == 'MMAP' and j.pid == -1 and j.tid == 0:
            bisect.insort(maps[j.pid], (j.addr, j.len, j.filename))
        elif j.type in ('COMM','MMAP'):
            bisect.insort(updates, (j.time2, j))

    for j in ev:
        add = lambda k, i: do_add(data, used, k, i)

        if j.type != "SAMPLE":
            continue

        # process pending updates
        while len(updates) > 0 and j.time >= updates[0][0]:
            u = updates[0][1]
            del updates[0]
            if u.type == 'MMAP':
                pid = u.pid
                bisect.insort(maps[pid], (u.addr, u.len, u.filename))
            elif u.type == 'COMM':
                maps[u.pid] = []
                pnames[u.pid] = u.comm
    
        filename, offset = resolve(maps, j.pid, j.ip)        
        add('filename', filename)
        add('foffset', offset)
        sym = None
        offset = None
        line = None
        srcfile = None
        if filename and filename.startswith("/"):
            sym, offset, line = elf.resolve_addr(filename, j.ip)
        add('symbol', sym)
        add('soffset', offset)
        add('line', line)
        for name in j:
            if name not in ignored:
                if j[name]:
                    used[name] += 1
                data[name].append(j[name])
        # XXX assumes time exists
        index.append(pd.Timestamp(j["time"]))
    for j in data.keys():
        if used[j] == 0:
            del data[j]
    return pd.DataFrame(data, index=index, dtype=np.uint64)

def read_samples(fn):
    with open(fn, "rb") as f:
        h = perfdata.perf_file.parse_stream(f)
        df = samples_to_df(h)
        return df

if __name__ == '__main__':
    import sys
    df = read_samples(sys.argv[1])
    print df
    print df['filename'].value_counts()
    print df['symbol'].value_counts()
    print df['line'].value_counts()
