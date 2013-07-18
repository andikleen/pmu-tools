#!/usr/bin/python
# plot already normalized data
# first column is time stamp
import csv
import matplotlib.pyplot as plt
import sys

if len(sys.argv) > 1:
    inf = open(sys.argv[1], "r")
else:
    inf = sys.stdin

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
        columns[j].append(float(r[c]))
        c += 1

for j in columns:
    plt.plot(timestamps, columns[j], label=j)
leg = plt.legend()
leg.get_frame().set_alpha(0.5)
plt.show()
