#!/usr/bin/python
# plot interval CSV output from perf/toplev
# perf stat -I1000 -x, -o file ...
# toplev -I1000 -x, -o file ... 
# interval-plot.py file (or stdin)
# delimeter must be ,
# this is for data that is not normalized
# TODO: move legend somewhere else where it doesn't overlap?
# better and more colors
import csv
import sys
import matplotlib.pyplot as plt
import collections

import gen_level

all_colors = ('silver','grey','black','orange','brown','maroon',
	      'green','olive','purple','red', '#6960EC', '#F0FFFF',
              '#728C00', '#827B60', '#F87217', '#E55451', # 16
              '#F88017', '#C11B17', '#17BFC2', '#C48793') # 20
cur_colors = collections.defaultdict(lambda: all_colors)
assigned = dict()

if len(sys.argv) > 1:
    inf = open(sys.argv[1], "r")
else:
    inf = sys.stdin

rc = csv.reader(inf)
timestamps = dict()
value = dict()

for r in rc:
    # timestamp,event,value
    if len(r) < 3:
        continue
    event = r[1]
    if event not in assigned:
        level = gen_level.get_level(event)
        print level, event
        assigned[event] = cur_colors[level][0]
        cur_colors[level] = cur_colors[level][1:]
        if len(cur_colors[level]) == 0:
            cur_colors[level] = all_colors
        value[event] = []
        timestamps[event] = []
    timestamps[event].append(r[0])
    try:
        value[event].append(float(r[2].replace("%","")))
    except ValueError:
        value[event].append(0.0)

levels = dict()
for j in assigned.keys():
    levels[gen_level.get_level(j)] = True

n = 1
for l in levels.keys():
    ax = plt.subplot(len(levels), 1, n)
    ax.set_ylim(0, 100)
    t = []
    for j in assigned.keys():
        if gen_level.get_level(j) == l:
            t.append(j)
            ax.plot(timestamps[j], value[j], assigned[j])
    leg = ax.legend(t, loc='upper left')
    leg.get_frame().set_alpha(0.5)
    n += 1
plt.show()
