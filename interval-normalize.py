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
import sys
import csv
import re
import copy
import argparse
import csv_formats
import collections

ap = argparse.ArgumentParser(description=
'Normalize CSV data from perf or toplev. All values are printed on a single line.')
ap.add_argument('inputfile', type=argparse.FileType('r'), default=sys.stdin, nargs='?')
ap.add_argument('--output', '-o', type=argparse.FileType('w'), default=sys.stdout, nargs='?')
ap.add_argument('--cpu', nargs='?', help='Only output for this cpu')
ap.add_argument('--na', nargs='?', help='Value to use if data is not available', default="")
args = ap.parse_args()

printed_header = False
timestamp = None

events = collections.OrderedDict()
out = []
times = []
cpus = []
rc = csv.reader(args.inputfile)
res = []
writer = csv.writer(args.output)
lastcpu = None
for row in rc:
    r = csv_formats.parse_csv_row(row)
    if r is None:
        continue
    ts, cpu, ev, val = r.ts, r.cpu, r.ev, r.val

    if ts != timestamp or cpu != lastcpu:
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

    # use a list for row storage to keep memory requirements down
    if ev not in events:
        events[ev] = len(res)
    ind = events[ev]
    if ind >= len(res):
        res += [None] * ((ind + 1) - len(res))
    res[ind] = val
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

keys = events.keys()
writer.writerow(["Timestamp"] + (["CPU"] if cpu is not None else []) + keys)
for row, ts, cpunum in zip(out, times, cpus):
    writer.writerow([ts] +
                ([cpunum] if cpu is not None else []) +
                ([resolve(row, events[x]) for x in keys]))

