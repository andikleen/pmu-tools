#!/usr/bin/python
# plot toplev -l1 -v -x, output as bar plot
# works best with -v and -l1
import matplotlib.pyplot as plt
import csv
import sys
from collections import defaultdict

all_colors = ('red','green','blue','yellow','black')

ratios = defaultdict(list)
timestamps = []

rc = csv.reader(open(sys.argv[1], "r"))
ts = None
for r in rc:
    if len(r) < 4:
        continue
    if r[0] != ts:
        timestamps.append(float(r[0]))
        ts = r[0]
    ratios[r[1]].append(float(r[2].replace("%","")))
    
bars = []
prev = None
col = all_colors
for j in ratios:
    print j,ratios[j]
    bars.append(plt.bar(timestamps, ratios[j], color=col[0], bottom=prev))
    prev = ratios[j]
    col = col[1:]
    if not col:
        col = all_colors
                
plt.legend(map(lambda x: x[0], bars), ratios.keys())
plt.show()
