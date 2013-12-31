#!/usr/bin/python
# plot toplev -v -lX -x, output as bar plot
#
# TODO:
# y label
import matplotlib.pyplot as plt
import csv
import argparse
import math
import re
from collections import defaultdict
import gen_level

try:
    import brewer2mpl
except ImportError:
    print "pip install brewer2mpl for better colors"
    all_colors = ('red','green','blue','yellow','black')

p = argparse.ArgumentParser(usage='plot toplev -v -lN -x, output as bar plot') 
p.add_argument('file', help='CSV file to plot')
p.add_argument('--output', '-o', help='Save figure to file (.pdf/.png/etc). Otherwise show.',
                  nargs='?')
p.add_argument('--verbose', '-v', help='Print data values', action='store_true')
p.add_argument('--xkcd', help='Enable XKCD mode (with new matplotlib). Please install Humor Sans.', action='store_true')
args = p.parse_args()

if args.xkcd:
    plt.xkcd()

def flush_vals(ratios, vals):
    if not vals:
        return
    k = ratios.keys()
    if not k:
        k = vals.keys()
    for j in k:
        if j in vals and -5 <= vals[j] <= 105:
            ratios[j].append(vals[j])
        else:
            ratios[j].append(float('nan'))

ratios = defaultdict(list)
timestamps = []
rc = csv.reader(open(args.file, "r"))
ts = None
levels = defaultdict(list)
vals = None
for r in rc:
    if len(r) < 4:
        continue
    if not re.match(r"\d+(\.\d*)", r[0]):
        r = ["0.0"] + r
    l = gen_level.get_level(r[1])
    if r[1] not in levels[l]:
        levels[l].append(r[1])
    t = math.trunc(float(r[0]) * 100) / 100.0
    if t != ts:
        timestamps.append(t)
        ts = t
        flush_vals(ratios, vals)
        vals = dict()
    vals[r[1]] = float(r[2].replace("%",""))
flush_vals(ratios, vals)

if args.verbose:
    print "time", len(timestamps), timestamps
    for j in ratios.keys():
        print j, ratios[j]

def valid_row(r):
    s = sum(r)
    return s != 0.0 and s != float('nan')
    
n = 1
numplots = len(levels.keys())
fig = plt.figure()
ax = None
yset = False
for l in levels.keys():
    non_null = filter(lambda x: valid_row(ratios[x]), levels[l])
    if not non_null:
        print "nothing in level", l
        n += 1
        continue
    if 'brewer2mpl' in globals():
        num_color = max(min(len(non_null), 11), 3)
        all_colors = brewer2mpl.get_map('Spectral', 'Diverging', num_color).hex_colors
    ax = fig.add_subplot(numplots, 1, n)
    r = map(lambda x: ratios[x], non_null)
    stack = ax.stackplot(timestamps, colors=all_colors, *r)
    ax.set_ylim(0, 100)
    ax.set_title('Level %d' % (l))
    ax.get_xaxis().set_visible(False)
    #box = ax.get_position()
    #ax.set_position([box.x0, box.y0, box.width, box.height * 0.8])

    p = [plt.Rectangle((0, 0), 1, 1, fc=pc.get_facecolor()[0]) for pc in stack]
    leg = plt.legend(p, non_null, ncol=2, bbox_to_anchor=(0., 0., 1., 0.0), loc=2)
    leg.get_frame().set_alpha(0.5)
    ax.margins(0, 0)
    n += 1

if ax:
    ax.set_xlabel('Time (s)')
    ax.get_xaxis().set_visible(True)

if len(timestamps) == 1:
    plt.gca().axes.get_xaxis().set_visible(False)

plt.subplots_adjust(hspace=1.0)

plt.ylabel('(% of execution time)')
if args.output:
    plt.savefig(args.output)
else:
    plt.show()
