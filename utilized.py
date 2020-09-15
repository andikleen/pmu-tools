#!/usr/bin/python
# extract utilized CPUs out of toplev CSV output
# toplev ... -I 1000 --node +CPU_Utilization -x, -o x.csv ...
# utilized.py < x.csv
# note it duplicates the core output
from __future__ import print_function
import argparse
import csv
import sys
import re
import collections

ap = argparse.ArgumentParser()
ap.add_argument('--min-util', default=10., type=float)
ap.add_argument('file', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
ap.add_argument('--output', '-o', type=argparse.FileType('w'), default=sys.stdout)
args = ap.parse_args()

key = None

c = csv.reader(args.file)
wr = csv.writer(args.output)

fields = collections.OrderedDict()
util = collections.defaultdict(list)

for t in c:
    if len(t) < 3 or t[0].startswith("#"):
        continue
    if t[0] == "Timestamp":
        wr.writerow(t)
    key = t[1] # XXX handle no -I
    if key in fields:
        fields[key].append(t)
    else:
        fields[key] = [t]
    if t[2] == "CPU_Utilization":
        util[key].append(float(t[3]))

final = []
skipped = []
for j in fields.keys():
    if "-T" not in j and not j.startswith("CPU"):
        if "S" in j:
            final.append(j)
        continue
    core = re.sub(r'-T\d+', '', j)
    utilization = 100
    if len(util[j]) > 0:
        utilization = (sum(util[j]) / len(util[j])) * 100.
    if utilization >= float(args.min_util):
        for k in fields[core] + fields[j]:
            wr.writerow(k)
    else:
        skipped.append(j)
for j in final:
    for k in fields[j]:
        wr.writerow(k)
print("skipped", " ".join(skipped), file=sys.stderr)
