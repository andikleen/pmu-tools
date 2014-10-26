#!/usr/bin/python
# convert perf stat -Ixxx -x, / toplev -Ixxx -x, output to normalized output
# this version buffers all data in memory
# t1,ev1,num1
# t1,ev2,num1
# t2,ev1,num3
# ->
# timestamp,ev1,ev2
# t1,num1,num2
# t2,num3,,
import sys
import csv
import re
import copy

if len(sys.argv) > 1:
    inf = open(sys.argv[1], "r")
else:
    inf = sys.stdin

printed_header = False
timestamp = None

def is_number(n):
    return re.match(r'[0-9.%]+', n)

events = dict()
out = []
times = []
rc = csv.reader(inf)
for row in rc:
    if len(row) < 3:
        continue
    # formats:
    # 1.354075473,0,cpu-migrations                                  old perf
    # 0.799553738,137765150,,branches                               new perf with unit
    # 0.200584389,FrontendBound.Branch Resteers,15.87%,above,"",    toplev
    ts = row[0].strip()
    if is_number(row[2]):
        ev, val = row[1], row[2]
    elif is_number(row[1]):
        if len(row) > 3:
            val, ev = row[1], row[3]
        else:
            val, ev = row[1], row[2]
    ev = ev.strip()
    if ts != timestamp:
        if timestamp:
            # delay in case we didn't see all headers
            # only need to do that for toplev, directly output for perf?
            # could limit buffering to save memory?
            out.append(copy.deepcopy(events))
            times.append(ts)
            for j in events.keys():
                events[j] = ""
        timestamp = ts
    events[ev] = val


print ",".join(["Timestamp"] + events.keys())
for row, ts in zip(out, times):
    print ts + "," + ",".join([row[x] if x in row else "" for x in events.keys()])
