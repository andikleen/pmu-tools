#!/usr/bin/env python3
# plot interval CSV output from perf/toplev
# perf stat -I1000 -x, -o file ...
# toplev -I1000 -x, -o file ...
# interval-plot.py file (or stdin)
# delimeter must be ,
# this is for data that is not normalized
# TODO: move legend somewhere else where it doesn't overlap?
from __future__ import print_function
import os
import csv
import sys
import collections
import argparse
import re
import matplotlib
if os.getenv("DISPLAY") is None:
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
import csv_formats
import gen_level
import tl_io

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
p.add_argument('-l', '--level', type=int, help='max level to plot', default=2)
p.add_argument('-m', '--metric', action='store_true', help='show metrics')
p.add_argument('-a', '--add', help='add extra plot with metrics (comma separated)', default="")
p.add_argument('file', help='CSV file to plot (otherwise using stdin). Can be .gz,.xz,.zstd', nargs='?')
p.add_argument('--output', '-o', help='Output to file. Otherwise show.',
               nargs='?')
args = p.parse_args()

adds = set(args.add.split(","))

if args.style:
    try:
        from mpltools import style
        style.use(args.style)
    except ImportError:
        print("Need mpltools for setting styles (pip install mpltools)")

try:
    import brewer2mpl
    all_colors = brewer2mpl.get_map('Paired', 'Qualitative', 12).hex_colors
except ImportError:
    print("Install brewer2mpl for better colors (pip install brewer2mpl)")
    all_colors = ('green','orange','red','blue',
              'black','olive','purple','#6960EC', '#F0FFFF',
              '#728C00', '#827B60', '#F87217', '#E55451',  # 16
              '#F88017', '#C11B17', '#17BFC2', '#C48793')  # 20

cur_colors = collections.defaultdict(lambda: all_colors)
assigned = {}

if args.file:
    inf = tl_io.flex_open_r(args.file)
else:
    inf = sys.stdin

rc = csv.reader(inf)
timestamps = {}
value = {}

def isnum(x):
    return re.match(r'[0-9.]+', x)

def skip_event(event, unit):
    # heuristic to figure out nodes. should enhance CSV to add area
    is_node = unit and (re.match(r'(% )?Slots( <)?', unit) or "." in event)
    level = event.count(".") + 1
    #print(event, "level", level, "unit", unit)
    if args.add and event in adds:
        return False
    if args.level and is_node and level > args.level:
        return True
    if args.metric is False and not is_node:
        return True
    return False

val = ""
for row in rc:
    r = csv_formats.parse_csv_row(row)
    if r is None:
        continue
    ts, cpu, event, val = r.ts, r.cpu, r.ev, r.val
    if ts == "SUMMARY" or skip_event(event, r.unit):
        continue
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

k = set(assigned.keys()) - adds
levels = set(map(gen_level.get_level, k)) | adds

if args.xkcd:
    try:
        plt.xkcd()
    except NameError:
        print("Please update matplotlib. Cannot enable xkcd mode.")

n = 1
for l in levels:
    ax = plt.subplot(len(levels), 1, n)
    if val.find('%') >= 0:
        ax.set_ylim(0, 100)
    t = []
    for j in assigned.keys():
        print(j, gen_level.get_level(j), l)
        if gen_level.get_level(j) == l or j == l:
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
