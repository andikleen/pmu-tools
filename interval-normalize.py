#!/usr/bin/env python
# convert perf stat -Ixxx -x, / toplev -Ixxx -x, output to normalized output
# this version buffers all data in memory, so it can use a lot of memory.
# t1,ev1,num1
# t1,ev2,num1
# t2,ev1,num3
# ->
# timestamp,ev1,ev2
# t1,num1,num2
# t2,num3,,
# when the input has CPU generate separate lines for each CPU (may need post filtering)
from __future__ import print_function
import sys
import csv
import argparse
import collections
import csv_formats

ap = argparse.ArgumentParser(description=
'Normalize CSV data from perf or toplev. All values are printed on a single line.')
ap.add_argument('inputfile', type=argparse.FileType('r'), default=sys.stdin, nargs='?')
ap.add_argument('--output', '-o', type=argparse.FileType('w'), default=sys.stdout, nargs='?')
ap.add_argument('--cpu', nargs='?', help='Only output for this cpu')
ap.add_argument('--na', nargs='?', help='Value to use if data is not available', default="")
ap.add_argument('--error-exit', action='store_true', help='Force error exit on parse error')
ap.add_argument('--normalize-cpu', action='store_true', help='Normalize CPUs into unique columns too')
args = ap.parse_args()

printed_header = False
timestamp = None

events = collections.OrderedDict()
out = []
times = []
cpus = []
rc = csv.reader(args.inputfile)
res = []
writer = csv.writer(args.output, lineterminator='\n')
lastcpu = None
cpu = None
lineno = 1
for row in rc:
    if len(row) > 0 and (row[0] == "Timestamp" or row[0].startswith("#")):
        lineno += 1
        continue
    r = csv_formats.parse_csv_row(row, error_exit=args.error_exit)
    if r is None:
        print("at line %d" % lineno, file=sys.stderr)
        lineno += 1
        continue
    ts, cpu, ev, val = r.ts, r.cpu, r.ev, r.val

    if ts != timestamp or (cpu != lastcpu and not args.normalize_cpu):
        if timestamp:
            if args.cpu and cpu != args.cpu:
                continue
            # delay in case we didn't see all headers
            # only need to do that for toplev, directly output for perf?
            # could limit buffering to save memory?
            out.append(res)
            times.append(timestamp)
            cpus.append(cpu)
            res = []
        timestamp = ts
        lastcpu = cpu

    if cpu is not None and args.normalize_cpu:
        ev = cpu + " " + ev

    # use a list for row storage to keep memory requirements down
    if ev not in events:
        events[ev] = len(res)
    ind = events[ev]
    if ind >= len(res):
        res += [None] * ((ind + 1) - len(res))
    res[ind] = val
    lineno += 1
if res and not (args.cpu and cpu != args.cpu):
    out.append(res)
    times.append(timestamp)
    cpus.append(cpu)

def resolve(row, ind):
    if ind >= len(row):
        return args.na
    v = row[ind]
    if v is None:
        return args.na
    return v

def cpulist():
    if args.normalize_cpu:
        return []
    if cpu is not None:
        return ["CPU"]
    return []

keys = events.keys()
writer.writerow(["Timestamp"] + cpulist() + list(keys))
for row, ts, cpunum in zip(out, times, cpus):
    writer.writerow([ts] +
                ([cpunum] if (cpu is not None and not args.normalize_cpu) else []) +
                ([resolve(row, events[x]) for x in keys]))
