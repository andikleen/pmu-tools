#!/usr/bin/python
# Import perf.data into a pandas DataFrame
# May need substantial memory for large input files.
import pandas as pd
import numpy as np
import perfdata
from collections import defaultdict, Counter
import bisect
import pprint

#
# TBD 
# fix all types
# drop unused columns
# extra table for threads
# flatten callchains and branch_stack
# expand registers, stack
# represent other metadata
# s/w trace points
# fix time
# 

ignored = ('type', 'start', 'end', '__recursion_lock__', 'ext_reserved',
           'mmap_data')

def lookup(m, ip):
    mr = m[bisect.bisect_left(m, (ip,)) - 1]
    return mr, ip - mr[0] 

def resolve(maps, pid, ip):
    m, offset = lookup(maps[pid], ip)
    if offset >= m[1]:
        # look up kernel
        m, offset = lookup(maps[-1], ip)
        if offset >= m[1]:
            return None, 0
    return m[2], offset

def samples_to_df(h):
    ev = perfdata.get_events(h)
    index = []
    data = defaultdict(list)
    maps = defaultdict(list)
    pnames = defaultdict(str)
    for j in ev:
        if j.type == 'MMAP':
            pid = j.pid
            bisect.insort(maps[pid], (j.addr, j.len, j.filename))
            if pid != -1:
                print "maps",pid,pnames[pid], maps[pid]
        elif j.type == 'COMM':
            print "comm", j.pid, j.comm
            maps[j.pid] = []
            pnames[j.pid] = j.comm
        if j.type != "SAMPLE":
            continue
        filename, offset = resolve(maps, j.pid, j.ip)
        data['filename'].append(filename)
        data['offset'].append(offset)
        for name in j:
            if name not in ignored:
                data[name].append(j[name])
        # XXX assumes time exists
        index.append(pd.Timestamp(j["time"]))
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
