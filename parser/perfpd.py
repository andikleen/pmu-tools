#!/usr/bin/python
# Import perf.data into a pandas DataFrame
import pandas as pd
import numpy as np
import perfdata
from collections import defaultdict, Counter
import bisect
import elf
import mmap

#
# TBD 
# fix all types
# extra table for threads
# flatten callchains and branch_stack
# expand registers, stack
# represent other metadata
# s/w trace points
# handle shlibs
# fix callchain
# resolve branch
# 

ignored = ('type', 'start', 'end', '__recursion_lock__', 'ext_reserved',
           'header_end', 'end_event', 'offset', 'callchain', 'branch_stack')

def resolve_chain(cc, j, mm):
    if cc:
        j.callchain_func = []
        j.callchain_src = []
        for ip in cc.caller:
            fn, _ = mm.resolve(j.pid, ip)
            print ip, fn
            sym, offset, line = None, None, None
            if fn and fn.startswith("/"):
                sym, offset, line = elf.resolve_addr(fn, ip)
            print sym, offset, line
            j.callchain_func.append((sym, offset))
            j.callchain_src.append((fn, line))

def do_add(d, u, k, i):
    d[k].append(i)
    u[k] += 1

def samples_to_df(h):
    ev = perfdata.get_events(h)
    index = []
    data = defaultdict(list)

    used = Counter()
    mm = mmap.MmapTracker()

    for n in range(0, len(ev)):
        mm.lookahead_mmap(ev, n)

        j = ev[n]
        if j.type != "SAMPLE":
            continue

        mm.update_sample(j)
        add = lambda k, i: do_add(data, used, k, i)

        filename, offset = mm.resolve(j.pid, j.ip)        
        add('filename', filename)
        add('foffset', offset)
        sym, offset, line = None, None, None
        if filename and filename.startswith("/"):
            sym, offset, line = elf.resolve_addr(filename, j.ip)
        add('symbol', sym)
        add('soffset', offset)
        add('line', line)
        #if 'callchain' in j:
        #    resolve_chain(j['callchain'], j, mmap)
        for name in j:
            if name not in ignored:
                if j[name]:
                    used[name] += 1
                data[name].append(j[name])
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
