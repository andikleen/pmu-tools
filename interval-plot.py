#!/usr/bin/env python
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
import re
import csv_formats

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
p.add_argument('file', help='CSV file to plot (or stdin)', nargs='?')
p.add_argument('--output', '-o', help='Output to file. Otherwise show.', 
               nargs='?')
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

def isnum(x):
    return re.match(r'[0-9.]+', x)

val = ""
for row in rc:
    r = csv_formats.parse_csv_row(row)
    if r is None:
        continue
    ts, cpu, event, val = r.ts, r.cpu, r.ev, r.val
    if event not in assigned:
        level = gen_level.get_level(event)
        assigned[event] = cur_colors[level][0]
        cur_colors[level] = cur_colors[level][1:]
        if len(cur_colors[level]) == 0:
            cur_colors[level] = all_colors
        value[event] = []
        timestamps[event] = []
    timestamps[event].append(float(ts))
    try:
        value[event].append(float(val.replace("%","")))
    except ValueError:
        value[event].append(0.0)

levels = set(map(gen_level.get_level, assigned.keys()))

if args.xkcd:
    try:
        plt.xkcd()
    except NameError:
        print "Please update matplotlib. Cannot enable xkcd mode."

n = 1
for l in levels:
    ax = plt.subplot(len(levels), 1, n)
    if val.find('%') >= 0:
        ax.set_ylim(0, 100)
    t = []
    for j in assigned.keys():
        print j, gen_level.get_level(j), l
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
if val.find('%') >= 0:
    plt.ylabel('Bottleneck %')
else:
    plt.ylabel("Counter value")
if args.output:
    plt.savefig(args.output)
else:
    plt.show()
