#!/usr/bin/python
# plot interval CSV output from perf/toplev
# perf stat -I1000 -x, -o file ...
# toplev -I1000 -x, -o file ... 
# interval-plot.py file (or stdin)
# delimeter must be ,
# this is for data that is not normalized
# TODO: move legend somewhere else where it doesn't overlap?
import csv
import sys
import matplotlib.pyplot as plt
import collections
import argparse

p = argparse.ArgumentParser(
        usage='plot interval CSV output from perf stat/toplev',
        description='''
perf stat -I1000 -x, -o file ...
toplev -I1000 -x, -o file ... 
interval-plot.py file (or stdin)
delimeter must be ,
this is for data that is not normalized.''')
p.add_argument('--xkcd', action='store_true', help='enable xkcd mode')
p.add_argument('--style', help='set mpltools style (e.g. ggplot)')
p.add_argument('file', help='CSV file to plot (or stdin)')
args = p.parse_args()

if args.style:
    try:
        from mpltools import style
        style.use(args.style)
    except ImportError:
        print "Need mpltools for setting styles (pip install mpltools)"

import gen_level

try:
    import brewer2mpl
    all_colors = brewer2mpl.get_map('Paired', 'Qualitative', 12).hex_colors
except ImportError:
    print "Install brewer2mpl for better colors (pip install brewer2mpl)"
    all_colors = ('green','orange','red','blue',
    	      'black','olive','purple','#6960EC', '#F0FFFF',
              '#728C00', '#827B60', '#F87217', '#E55451', # 16
              '#F88017', '#C11B17', '#17BFC2', '#C48793') # 20

cur_colors = collections.defaultdict(lambda: all_colors)
assigned = dict()

if args.file:
    inf = open(args.file, "r")
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

if args.xkcd:
    try:
        plt.xkcd()
    except NameError:
        print "Please update matplotlib. Cannot enable xkcd mode."

n = 1
for l in levels.keys():
    ax = plt.subplot(len(levels), 1, n)
    ax.set_ylim(0, 100)
    t = []
    for j in assigned.keys():
        if gen_level.get_level(j) == l:
            t.append(j)
            if 'style' not in globals():
                ax.plot(timestamps[j], value[j], assigned[j])
            else:
                ax.plot(timestamps[j], value[j])
    leg = ax.legend(t, loc='upper left')
    leg.get_frame().set_alpha(0.5)
    n += 1

plt.xlabel('Time')
plt.ylabel('Bottleneck %')
plt.show()
