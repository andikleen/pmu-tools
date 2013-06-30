#!/usr/bin/python
# plot interval CSV output from perf/toplev
# perf stat -I1000 -x, -o file ...
# toplev -I1000 -x, -o file ... 
# interval-plot.py file (or stdin)
# delimeter must be ,
# TODO: move legend somewhere else where it doesn't overlap?
# better and more colors
import csv
import sys
import matplotlib.pyplot as plt

# currently need 39 colors max. we reuse after 20 XXX
all_colors = ('silver','grey','black','orange','brown','maroon',
	      'green','olive','purple','red', '#6960EC', '#F0FFFF',
              '#728C00', '#827B60', '#F87217', '#E55451', # 16
              '#F88017', '#C11B17', '#17BFC2', '#C48793') # 20
cur_color = all_colors
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
        assigned[event] = cur_color[0]		
        cur_color = cur_color[1:]
        if len(cur_color) == 0:
            cur_color = all_colors
        value[event] = []
        timestamps[event] = []
    timestamps[event].append(r[0])
    try:
        value[event].append(float(r[2].replace("%","")))
    except ValueError:
        value[event].append(0.0)

fig, ax = plt.subplots(1)
ax.set_ylim(0, 100)
t = []
for j in assigned.keys():
    t.append(j)
    ax.plot(timestamps[j], value[j], assigned[j])
leg = ax.legend(t, loc='upper left')
leg.get_frame().set_alpha(0.5)
plt.show()

