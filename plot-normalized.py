#!/usr/bin/env python
# plot already normalized data
# first column is time stamp
import csv
import matplotlib.pyplot as plt
import sys
import argparse

ap = argparse.ArgumentParser(usage='Plot already normalized CSV data')
ap.add_argument('--output', '-o', help='Output to file. Otherwise show.',
                nargs='?')
ap.add_argument('inf', nargs='?', default=sys.stdin, type=argparse.FileType('r'),
                help='input CSV file')
args = ap.parse_args()

inf = args.inf

rc = csv.reader(inf)

num = 0
timestamps = []
columns = dict()
for r in rc:
    num += 1
    if num == 1:
        for j in r[1:]:
            columns[j] = []
        continue
    timestamps.append(r[0])
    c = 1
    for j in columns:
        try:
            columns[j].append(float(r[c]))
        except ValueError:
            columns[j].append(float('nan'))
        c += 1

for j in columns:
    plt.plot(timestamps, columns[j], label=j)
leg = plt.legend()
leg.get_frame().set_alpha(0.5)
if args.output:
    plt.savefig(args.output)
else:
    plt.show()
