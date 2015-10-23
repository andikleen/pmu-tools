import os
import gen_level
from collections import defaultdict
import csv
import re

class TLData:
    """Read a toplev output CSV file.

   Exported:
    times[n] All time stamps
    vals[n]  All values, as dicts mapping (name, cpu)->float
    levels{name} All levels (includes metrics), name->list of fields
    headers(set) All headers (including metrics)
    metrics(set) All metrics
    helptxt[col] All help texts.
    cpus(set)    All CPUs
    """

    def __init__(self, fn, verbose=False):
        self.times = []
        self.vals = []
        self.fn = fn
        self.levels = defaultdict(set)
        self.metrics = set()
        self.headers = set()
        self.mtime = None
        self.helptxt = dict()
        self.cpus = set()
        self.verbose = verbose

    def update(self):
        mtime = os.path.getmtime(self.fn)
        if self.mtime == mtime:
            return
        self.mtime = mtime
        csvf = csv.reader(open(self.fn, 'r'))
        prevts = None
        val = dict()
        for r in csvf:
            if r[0].strip().startswith("#"):
                continue
            if re.match(r'[CS]\d+.*', r[1]):
                ts, cpu, name, pct, state, helptxt = r[0], r[1], r[2], r[3], r[4], r[5]
            else:
                ts, name, pct, state, helptxt = r[0], r[1], r[2], r[3], r[4]
                cpu = None
            key = (name, cpu)
            ts, pct = float(ts), float(pct.replace("%", ""))
            if name not in self.helptxt or self.helptxt[name] == "":
                self.helptxt[name] = helptxt
            if state == "below" and not self.verbose:
                continue
            if prevts and ts != prevts:
                self.times.append(prevts)
                self.vals.append(val)
                val = dict()
            val[key] = pct
            n = gen_level.level_name(name)
            if cpu:
                self.cpus.add(cpu)
            self.headers.add(name)
            if gen_level.is_metric(name):
                self.metrics.add(n)
            self.levels[n].add(name)
            prevts = ts

early_plots = ["TopLevel", "CPU utilization", "Power", "Frequency", "CPU-METRIC"]

def sort_pos(i, data):
    if i in early_plots:
        return early_plots.index(i)
    if i in data.metrics:
        return 30
    return 20

def cmp_level(a, b, data):
    ap, bp = sort_pos(a, data), sort_pos(b, data)
    if ap != bp:
        return ap - bp
    return cmp(a, b)

def level_order(data):
    """Return plot order of all levels."""
    return sorted(data.levels.keys(), cmp=lambda a, b: cmp_level(a, b, data))
