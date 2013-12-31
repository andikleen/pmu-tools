#!/usr/bin/python
# plot toplev -lX -v -x, output as bar plot
#
# TODO:
# fill in dummy values
# move legend out
# y label
# two column legend
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

ratios = defaultdict(list)
timestamps = []

args = argparse.ArgumentParser(usage='plot toplev -lN -v -x, output as bar plot') 
args.add_argument('file', help='CSV file to plot')
args.add_argument('--output', '-o', help='Save figure to file (.pdf/.png/etc). Otherwise show.',
                  nargs='?')
args.add_argument('--xkcd', help='Enable XKCD mode (with new matplotlib). Please install Humor Sans.', action='store_true')
arg = args.parse_args()

if arg.xkcd:
    plt.xkcd()

rc = csv.reader(open(arg.file, "r"))
ts = None
levels = defaultdict(list)
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
    # xxx fill in dummy values if not using -v
    ratios[r[1]].append(float(r[2].replace("%","")))

print "time", len(timestamps), timestamps
for j in ratios.keys():
    print j, ratios[j]
    
n = 1
numplots = len(levels.keys())
fig = plt.figure()
ax = None
for l in levels.keys():
    non_null = filter(lambda x: sum(ratios[x]) != 0.0, levels[l])
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
    ax.set_title('Level %d' % (l), loc='left')
    ax.get_xaxis().set_visible(False)
    ax.xaxis.tick_top()

    p = [plt.Rectangle((0, 0), 1, 1, fc=pc.get_facecolor()[0]) for pc in stack]
    leg = plt.legend(p, non_null, ncol=2, bbox_to_anchor=(0., 0., 1., .102), loc=2)
    leg.get_frame().set_alpha(0.5)
    ax.margins(0, 0)
    n += 1

if ax:
    ax.set_xlabel('Time (s)')
    ax.get_xaxis().set_visible(True)

if len(timestamps) == 1:
    plt.gca().axes.get_xaxis().set_visible(False)

plt.subplots_adjust(hspace=1.0)

# xxx put in wrong place
#plt.ylabel('Bottleneck (% of execution time)')
if arg.output:
    plt.savefig(arg.output)
else:
    plt.show()
