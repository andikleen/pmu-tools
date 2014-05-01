#!/usr/bin/python
# plot toplev -v -lX -x, output as bar plot
#
import matplotlib.pyplot as plt
import csv
import argparse
import math
import re
from collections import defaultdict
import gen_level

def parse_args():
    p = argparse.ArgumentParser(usage='plot toplev -v -lN -x, output as bar plot') 
    p.add_argument('file', help='CSV file to plot')
    p.add_argument('--output', '-o', help='Save figure to file (.pdf/.png/etc). Otherwise show.',
                      nargs='?')
    p.add_argument('--verbose', '-v', help='Print data values', action='store_true')
    p.add_argument('--xkcd', help='Enable XKCD mode (with new matplotlib). Please install Humor Sans.', action='store_true')
    p.add_argument('--title', help='Set title of plot', nargs='?')
    p.add_argument('--quiet', help='Be quiet', action='store_true')
    return p.parse_args()

args = parse_args()

try:
    import brewer2mpl
except ImportError:
    if not args.quiet:
        print "pip install brewer2mpl for better colors"

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

METRIC_LEVEL = 99

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
    if r[3] == "metric":
        l = METRIC_LEVEL # put at end
    else:
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

def get_colors(non_null):
    if 'brewer2mpl' in globals():
        num_color = max(min(len(non_null), 11), 3)
        all_colors = brewer2mpl.get_map('Spectral', 'Diverging', num_color).hex_colors
    else:
        all_colors = None
    return all_colors

def set_title(ax, t):
    try:
        ax.set_title(t, loc='right')
    except AttributeError:
        ax.set_title(t)

n = 1
numplots = len(levels.keys())
fig = plt.figure()
ax = None
yset = False
max_legend = 0
print levels.keys()
for l in sorted(levels.keys()):
    non_null = filter(lambda x: valid_row(ratios[x]), levels[l])
    if not non_null:
        #print "nothing in level", l
        n += 1
        continue
    all_colors = get_colors(non_null)
    ax = fig.add_subplot(numplots, 1, n)
    r = [ratios[x] for x in non_null]
    if l == METRIC_LEVEL:
        for j, name in zip(r, non_null):
            stack = ax.plot(timestamps, j, label=name)
        set_title(ax, "Metrics")
        leg = plt.legend(ncol=3, loc=2, bbox_to_anchor=(0., 0., -0.07, -0.07), prop={'size':8})
    else:
        stack = ax.stackplot(timestamps, colors=all_colors, *r)
        ax.set_ylim(0, 100)
        ax.yaxis.set_ticks([0., 50., 100.])
        set_title(ax, "Level %d" % (l))
        p = [plt.Rectangle((0, 0), 1, 1, fc=pc.get_facecolor()[0]) for pc in stack]
        leg = plt.legend(p, non_null, ncol=3 if len(non_null) > 4 else 2,
                bbox_to_anchor=(0., 0., -0.07, -0.07),
                loc=2, prop={'size':8})
    leg.get_frame().set_alpha(0.5)
    for j in ax.get_xticklabels() + ax.get_yticklabels():
        j.set_fontsize(6)
    if n >= 2 and not yset and l != -1:
        ax.set_ylabel('(% of execution time)')
        yset = True
    if n != numplots:
        max_legend = max(len(non_null), max_legend)
    ax.margins(0, 0)
    n += 1

if len(timestamps) == 1:
    plt.gca().axes.get_xaxis().set_visible(False)

plt.subplots_adjust(hspace=1.5 if max_legend > 6 else 0.9, bottom=0.20,
                    top=0.95)

if args.title:
    plt.subplot(numplots, 1, 1)
    plt.title(args.title)

if args.output:
    plt.savefig(args.output)
else:
    plt.show()
