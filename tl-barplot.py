#!/usr/bin/env python
# plot toplev -I... -x, -o ...csv output as bar plot
#
import matplotlib.pyplot as plt
import argparse
import math
from collections import defaultdict
import gen_level
import tldata
import re

def parse_args():
    p = argparse.ArgumentParser(usage='plot toplev -I...  -x, output as bar plot')
    p.add_argument('file', help='CSV file to plot')
    p.add_argument('--output', '-o', help='Save figure to file (.pdf/.png/etc). Otherwise show.',
                      nargs='?')
    p.add_argument('--verbose', '-v', help='Plot all data values even if below threshold', action='store_true')
    p.add_argument('--xkcd', help='Enable XKCD mode (with new matplotlib). Please install Humor Sans.', action='store_true')
    p.add_argument('--title', help='Set title of plot', nargs='?')
    p.add_argument('--quiet', help='Be quiet', action='store_true')
    p.add_argument('--cpu', help='CPU to plot (by default first)') # XXX
    return p.parse_args()

args = parse_args()

try:
    import brewer2mpl
except ImportError:
    if not args.quiet:
        print "pip install brewer2mpl for better colors"

if args.xkcd:
    plt.xkcd()

data = tldata.TLData(args.file, args.verbose)
data.update()

levels = data.levels
timestamps = data.times
ratios = defaultdict(list)
# XXX plot multiple cpus instead
if args.cpu:
    cpu = args.cpu
elif len(data.cpus) > 0:
    cpu = sorted(sorted(data.cpus), key=len, reverse=True)[0]
else:
    cpu = None

def cpumatch(x, match, base):
    return x.startswith(cpu) or x == base

if cpu:
    base = None
    m = re.match(r'C\d+', cpu)
    if m:
        base = m.group(0)
    aliases = [x for x in data.cpus if cpumatch(x, cpu, base)]
    print "plotting cpus:", " ".join(sorted(aliases))
else:
    aliases = []
if len(aliases) == 0:
    aliases = [None]

for h in data.headers:
    def findval(d):
        for c in aliases:
            if (h, c) in d:
                return d[(h, c)]
        return float('nan')

    ratios[h] = map(findval, data.vals)

def valid_row(r):
    s = sum(r)
    #if sum([0 if math.isnan(x) else 1 for x in r]) < len(r)/80.:
    #    return False
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
        ax.set_title(t, { 'fontsize': 6 }, loc='right')
    except AttributeError:
        ax.set_title(t)

def suffix(x):
    dot = x.rfind('.')
    if dot >= 0:
        return x[dot+1:]
    return x

n = 0
numplots = len(levels.keys())
ax = None
yset = False
max_legend = 0
xaxis = None
legend_bbox = (0., 0., -0.07, -0.03)
legend_loc = 2

for l in tldata.level_order(data):
    non_null = [x for x in  levels[l] if valid_row(ratios[x])]
    if not non_null:
        n += 1
        continue
    all_colors = get_colors(non_null)
    ax = plt.subplot2grid((numplots, 1), (n, 0), sharex=xaxis)
    plt.tight_layout()
    set_title(ax, l)
    r = [[y if y == y else 0.0 for y in ratios[x]] for x in non_null]

    if gen_level.is_metric(non_null[0]):
        for j, name in zip(r, non_null):
            stack = ax.plot(timestamps, j, label=name)
        leg = plt.legend(ncol=6,
                         loc=legend_loc,
                         bbox_to_anchor=legend_bbox,
                         prop={'size':6})
        low = min([min(ratios[x]) for x in non_null])
        high = max([max(ratios[x]) for x in non_null])
        if not math.isnan(low) and not math.isnan(high):
            ax.yaxis.set_ticks([low, math.trunc(((high - low)/2.0)/100.)*100., high])
    else:
        stack = ax.stackplot(timestamps, *r, colors=all_colors)
        ax.set_ylim(0, 100)
        ax.yaxis.set_ticks([0., 50., 100.])
        p = [plt.Rectangle((0, 0), 1, 1, fc=pc.get_facecolor()[0]) for pc in stack]
        leg = plt.legend(p, map(suffix, non_null),
                ncol=6,
                bbox_to_anchor=legend_bbox,
                loc=legend_loc,
                prop={'size':6})
    leg.get_frame().set_alpha(0.5)
    for j in ax.get_xticklabels() + ax.get_yticklabels():
        j.set_fontsize(6)
    if not xaxis:
        xaxis = ax
    #if n >= 2 and not yset and l != -1:
    #    ax.set_ylabel('(% of execution time)')
    #    yset = True
    if n != numplots:
        max_legend = max(len(non_null), max_legend)
    #ax.margins(0, 0)
    n += 1

if len(timestamps) == 1:
    plt.gca().axes.get_xaxis().set_visible(False)

plt.subplots_adjust(hspace=1.5 if max_legend > 6 else 0.9, bottom=0.20,
                    top=0.95)

if args.title:
    #plt.subplot(numplots, 1, 1)
    plt.title(args.title)

if args.output:
    plt.savefig(args.output)
else:
    plt.show()
