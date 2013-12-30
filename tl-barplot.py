#!/usr/bin/python
# plot toplev -l1 -v -x, output as bar plot
# works best with -v and -l1
import matplotlib.pyplot as plt
import csv
import argparse
import math
import re
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
    if not re.match(r"\d+(\.\d*)", r[0]):
        r = ["0.0"] + r
    t = math.trunc(float(r[0]) * 100) / 100.0
    if t != ts:
        timestamps.append(t)
        ts = t
    ratios[r[1]].append(float(r[2].replace("%","")))

print "time", len(timestamps), timestamps
for j in ratios.keys():
    print j, ratios[j]
    
fig = plt.figure()
ax = fig.add_subplot('111')
stack =  ax.stackplot(timestamps, colors=all_colors, *(ratios.values()))
ax.set_xlabel('Time (s)')
ax.set_ylabel('Bottleneck (% of execution time)')

p = [plt.Rectangle((0, 0), 1, 1, fc=pc.get_facecolor()[0]) for pc in stack]
plt.legend(p, ratios.keys())
ax.margins(0, 0)
if len(timestamps) == 1:
    plt.gca().axes.get_xaxis().set_visible(False)
plt.show()
