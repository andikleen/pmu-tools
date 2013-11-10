#!/usr/bin/python
# Import perf.data into a pandas DataFrame
# May need substantial memory for large input files.
import pandas as pd
import numpy as np
import perfdata
from collections import defaultdict

#
# TBD 
# resolve ips
# extra table for threads
# good data model for callchains and branch_stack
# expand registers, stack
# represent other metadata
# s/w trace points
# 

def samples_to_df(h):
    ev = perfdata.get_events(h)
    index = []
    data = defaultdict(list)
    for j in ev:
        if j.type != "SAMPLE":
            continue
        for name in j:
            if name.startswith("__"):
                continue
            data[name].append(j[name])
        # XXX assumes time exists
        index.append(j["time"])
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
