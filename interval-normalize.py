#!/usr/bin/python
# convert perf stat -Ixxx -x, / toplev -Ixxx -x, output to normalized output
# t1,ev1,num1
# t1,ev2,num1
# t2,ev1,num3
# ->
# timestamp,ev1,ev2
# t1,num1,num2
# t2,num3,,
import sys
import csv

if len(sys.argv) > 1:
    inf = open(sys.argv[1], "r")
else:
    inf = sys.stdin

printed_header = False
timestamp = None

events = dict()
rc = csv.reader(inf)
for row in rc:
    if len(row) < 3:
        continue
    ts, val, ev = row
    ev = ev.strip()
    if ts != timestamp:
        if timestamp:
            if not printed_header:
                print ",".join(["Timestamp"] + events.keys())
                printed_header = True
            print timestamp + "," + ",".join(map(lambda x: events[x], events.keys()))
            events = dict()
        timestamp = ts
    events[ev] = val

