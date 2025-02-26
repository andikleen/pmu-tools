#!/usr/bin/env python3
# query cpu topology and print all matching cpu numbers
# cputop "query" ["format"]
# query is a python expression, using variables:
# socket, core, thread, type, cpu
# or "offline" to query all offline cpus
# or "atom" or "core" to select core types
# type can be "atom" or "core"
# cpu is the cpu number
# format is a printf format with %d
# %d will be replaced with the cpu number
# format can be offline to offline the cpu or online to online
# Author: Andi Kleen
from __future__ import print_function
import sys
import os
import re
import argparse
import glob

def numfile(fn):
    f = open(fn, "r")
    v = int(f.read())
    f.close()
    return v

outstr = ""

def output(p, fmt):
    if fmt:
        if fmt == "taskset":
            global outstr
            if outstr:
                outstr += ","
            else:
                outstr += "taskset -c "
            outstr += "%d" % p
        else:
            print(fmt % (p,))
    else:
        print(p)

ap = argparse.ArgumentParser(description='''
query cpu topology and print all matching cpu numbers
cputop "query" ["format"]
query is a python expression, using variables:
socket, core, thread, type, cpu
type is "core" or "atom" on a hybrid system
cpu is the cpu number
or "offline" to query all offline cpus
format is a printf format with %d
%d will be replaced with the cpu number, or online/offline
to generate online/offline commands, or taskset to generate taskset command line''',
epilog='''
Examples:
print all cores on socket 0
cputop "socket == 0"

print all first threads in each core on socket 0
cputop "thread == 0 and socket == 0"

disable all second threads (disable hyper threading)
cputop "thread == 1" offline

reenable all offlined cpus
cputop offline online

print all online cpus
cputop True ''', formatter_class=argparse.RawTextHelpFormatter)
ap.add_argument('expr', help='python expression with socket/core/thread')
ap.add_argument('fmt', help='Output format string with %%d, or online/offline', nargs='?')
args = ap.parse_args()

if args.expr == "atom":
    args.expr = 'type == "atom"'
if args.expr == "core":
    args.expr = 'type == "core"'

special = {
    "offline": "echo 0 > /sys/devices/system/cpu/cpu%d/online",
    "online": "echo 1 > /sys/devices/system/cpu/cpu%d/online",
}

if args.fmt in special:
    args.fmt = special[args.fmt]

types = dict()
for fn in glob.glob("/sys/bus/event_source/devices/cpu_*/cpus"):
    typ = os.path.basename(fn.replace("/cpus", "")).replace("cpu_","")
    cpus = open(fn).read()
    for j in cpus.split(","):
        m = re.match(r'(\d+)(-\d+)?', j)
        if m is None:
            continue
        if m.group(2):
            for k in range(int(m.group(1)), int(m.group(2)[1:])+1):
                types[k] = typ
        else:
            types[int(m.group(1))] = typ

base = "/sys/devices/system/cpu/"
p = {}
l = os.listdir(base)
for d in l:
    m = re.match(r"cpu([0-9]+)", d)
    if not m:
        continue
    proc = int(m.group(1))
    top = base + d + "/topology"
    if not os.path.exists(top):
        if args.expr == "offline":
            output(proc, args.fmt)
        continue
    socket = numfile(top + "/physical_package_id")
    core = numfile(top + "/core_id")
    n = 0
    while (socket, core, n) in p:
        n += 1
    p[(socket, core, n)] = proc

if args.expr == "offline":
    sys.exit(0)

for j in sorted(p.keys()):
    socket, core, thread = j
    cpu = p[j]
    type = "any"
    if cpu in types:
        type = types[cpu]
    if eval(args.expr):
        output(p[j], args.fmt)

if outstr:
    print(outstr)
