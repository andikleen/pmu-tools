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
# fix all types?
# extra table for threads?
# stream_id
# flatten callchains and branch_stack
# expand registers, stack
# represent other metadata
# s/w trace points
# fix callchain
# resolve branch
# debuginfo / buildid
# instructions / basic blocks
# 

ignored = {'type', 'start', 'end', '__recursion_lock__', 'ext_reserved',
           'header_end', 'end_event', 'offset', 'callchain', 'branch', 'branch_stack',
           # skip attr for now, as it is too complex
           # XXX simple representation
           'attr'}

def resolve_ip(filename, foffset, ip, need_line):
    sym, soffset, line = None, 0, None
    if filename and filename.startswith("/"):
        sym, soffset = elf.resolve_sym(filename, foffset)
        if not sym:
            sym, soffset = elf.resolve_sym(filename, ip)
        if need_line:
            line = elf.resolve_line(filename, ip)
    return sym, soffset, line

def resolve_chain(cc, j, mm, need_line):
    if not cc:
        return
    j.callchain_sym = []
    j.callchain_offset = []
    if need_line:
        j.callchain_src = []
    for ip in cc.caller:
        filename, mmap_base, foffset = mm.resolve(j.pid, ip)
        sym, soffset, line = resolve_ip(filename, foffset, ip, need_line)
        j.callchain_sym.append(sym)
        j.callchain_offset.append(soffset)
        if need_line:
            j.callchain_src.append(line)

def do_add(d, u, k, i):
    d[k].append(i)
    u[k] += 1

def samples_to_df(h, need_line):
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

        filename, mmap_base, foffset = mm.resolve(j.pid, j.ip)
        add('filename', filename)
        add('foffset', foffset)
        sym, soffset, line = resolve_ip(filename, foffset, j.ip, need_line)
        add('symbol', sym)
        add('line', line)
        add('soffset', soffset)
        if 'callchain' in j:
            resolve_chain(j['callchain'], j, mm, need_line)
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

def read_samples(fn, need_line=True):
    with open(fn, "rb") as f:
        h = perfdata.perf_file.parse_stream(f)
        df = samples_to_df(h, need_line)
        return df, h.attrs.perf_file_attr.f_attr, h.features

if __name__ == '__main__':
    import argparse

    args = argparse.ArgumentParser()
    args.add_argument('file', nargs='?', help='perf.data file to read', 
                          default='perf.data')
    args.add_argument('--repl', action='store_true',
                             help='start python shell with data')
    p = args.parse_args()
    df, _, _ = read_samples(p.file)
    if p.repl:
        import code
        print df
        code.interact(banner='perf.data is in df', local=locals())
        sys.exit(0)

    print df
    print df['filename'].value_counts()
    print df['symbol'].value_counts()
    print df['line'].value_counts()
