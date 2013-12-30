#!/usr/bin/python
# plot toplev -l1 -v -x, output as bar plot
# works best with -v and -l1
import matplotlib.pyplot as plt
import csv
import argparse
import math
from collections import defaultdict

try:
    import brewer2mpl
    all_colors = brewer2mpl.get_map('Spectral', 'Diverging', 4).hex_colors
except ImportError:
    print "pip install brewer2mpl for better colors"
    all_colors = ('red','green','blue','yellow','black')

ratios = defaultdict(list)
timestamps = []

args = argparse.ArgumentParser(usage='plot toplev -l1 -v -x, output as bar plot') 
args.add_argument('file', help='CSV file to plot')
p = args.parse_args()

rc = csv.reader(open(p.file, "r"))
ts = None
for r in rc:
    if len(r) < 4:
        continue
    t = math.trunc(float(r[0]) * 100) / 100.0
    print t,r[1]
    if t != ts:
        timestamps.append(t)
        ts = t
    ratios[r[1]].append(float(r[2].replace("%","")))
    
bars = []
prev = [0] * len(ratios[ratios.keys()[0]])
col = all_colors
for j in ratios:
    print j,ratios[j],prev
    bars.append(plt.bar(timestamps, ratios[j], color=col[0], bottom=prev))
    prev = [x+y for x,y in zip(prev, ratios[j])]
    col = col[1:]
    if not col:
        col = all_colors
              
plt.xlabel('Time')
plt.ylabel('Percent bottleneck')
plt.legend(map(lambda x: x[0], bars), ratios.keys())
plt.margins(0, 0)
plt.show()
