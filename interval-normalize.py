#!/usr/bin/python
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

ap = argparse.ArgumentParser(description=
'Normalize CSV data from perf or toplev. All values are printed on a single line.')
ap.add_argument('inputfile', type=argparse.FileType('r'), default=sys.stdin, nargs='?')
ap.add_argument('--output', '-o', type=argparse.FileType('w'), default=sys.stdout, nargs='?')
ap.add_argument('--cpu', nargs='?', help='Only output for this cpu')
ap.add_argument('--na', nargs='?', help='Value to use if data is not available', default="")
args = ap.parse_args()

printed_header = False
timestamp = None

def is_number(n):
    return re.match(r'[0-9.]+%?', n) != None

def is_cpu(n):
    return re.match(r'(CPU)|(S\d+(-C\d+)?)', row[1]) != None

events = dict()
out = []
times = []
cpus = []
rc = csv.reader(args.inputfile)
res = []
writer = csv.writer(args.output)
lastcpu = None
for row in rc:
    # 1.354075473,0,cpu-migrations                                  old perf w/o cpu
    # 1.354075473,CPU0,0,cpu-migrations                             old perf w/ cpu
    # 0.799553738,137765150,,branches                               new perf with unit
    # 0.799553738,CPU1,137765150,,branches                        new perf with unit and cpu
    # 0.100879059,402.603109,,task-clock,402596410,100.00         new perf with unit without cpu and stats
    # 0.200584389,FrontendBound.Branch Resteers,15.87%,above,"",    toplev single thread
    # 0.200584389,0,FrontendBound.Branch Resteers,15.87%,above,"",  toplev w/ cpu
    if len(row) == 0:
        continue
    ts = row[0].strip()
    if len(row) == 3: # old perf
        cpu, ev, val = None, row[2], row[1]
    elif len(row) == 4: # new perf w/ unit or old perf w/ CPU
        if is_cpu(row[1]):  # old
            cpu, ev, val = row[1], row[3], row[2]
        else: # new
            cpu, ev, val = None, row[3], row[1]
    elif len(row) == 5: # new perf w/ CPU
        cpu, ev, val = row[1], row[4], row[2]
    elif len(row) > 5: # toplev or new perf
        if is_number(row[1]) and is_number(row[4]):     # new perf w/o CPU
            cpu, ev, val = None, row[3], row[1]
        elif is_cpu(row[1]) and is_number(row[2]) and is_number(row[5]):
            CPU, EV, val = row[1], row[4], row[2]
        elif "." in row[2] and is_number(row[2]):
            cpu, ev, val = None, row[1], row[2].replace("%", "")
        else:
            cpu, ev, val = row[1], row[2], row[3].replace("%", "")
    elif row[0].startswith("#"):    # comment
        continue
    else:
        print "PARSE-ERROR", row
        continue

    ev = ev.strip()
    if ts != timestamp or cpu != lastcpu:
        if timestamp:
            if args.cpu and cpu != args.cpu:
                continue
            # delay in case we didn't see all headers
            # only need to do that for toplev, directly output for perf?
            # could limit buffering to save memory?
            out.append(res)
            times.append(ts)
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

def resolve(row, ind):
    if ind >= len(row):
        return args.na
    v = row[ind]
    if v is None:
        return args.na
    return v

keys = sorted(events.keys())
writer.writerow(["Timestamp"] + (["CPU"] if cpu is not None else []) + keys)
for row, ts, cpunum in zip(out, times, cpus):
    writer.writerow([ts] +
                ([cpunum] if cpu is not None else []) +
                ([resolve(row, events[x]) for x in keys]))

