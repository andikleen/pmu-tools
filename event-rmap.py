#!/usr/bin/env python
# print currently running events on cpu (default 0)
# event-rmap [cpu-num]
# xxx no extra modi for now, racy with multi plexing
from __future__ import print_function
import sys
import msr
import ocperf
from pmudef import (MSR_PEBS_ENABLE, MSR_EVNTSEL, EVENTSEL_ENABLE, EVMASK,
                    EVENTSEL_CMASK,
                    EVENTSEL_EDGE, EVENTSEL_ANY, EVENTSEL_INV, EVENTSEL_PC,
                    MSR_IA32_FIXED_CTR_CTRL)

fixednames = (
    "inst_retired.any",
    "cpu_clk_unhalted.thread",
    "cpu_clk_unhalted.ref_tsc"
)

cpu = 0
if len(sys.argv) > 1:
    cpu = int(sys.argv[1])

emap = ocperf.find_emap()
if not emap:
    sys.exit("Unknown CPU or cannot find CPU event table")
found = 0
try:
    pebs_enable = msr.readmsr(MSR_PEBS_ENABLE, cpu)
except OSError:
    pebs_enable = 0
for i in range(0, 8):
    try:
        evsel = msr.readmsr(MSR_EVNTSEL + i, cpu)
    except OSError:
        break
    found += 1
    if evsel & EVENTSEL_ENABLE:
        print("%d: %016x: " % (i, evsel), end="")
        evsel &= EVMASK
        if evsel in emap.codes:
            ev = emap.codes[evsel]
            if ev.msr:
                try:
                    extra = msr.readmsr(ev.msr)
                except OSError:
                    print("Cannot read extra MSR %x for %s" % (ev.msr, ev.name))
                    continue
                for j in emap.codes.keys():
                    if j == evsel and extra == emap.codes[j].msrvalue:
                        print(j.name, "msr:%x" % (extra), end="")
                        break
                else:
                    print("no exact match for %s, msr %x value %x" % (ev.name,
                                                                      ev.msr, ev.msrvalue), end="")
            else:
                print(ev.name, end="")
        else:
            name = ""
            for j in emap.codes.keys():
                if j & 0xff == evsel & 0xff:
                    name += "%s[%x] " % (emap.codes[j].name, j)
            if name:
                print("[no exact match] " + name, end=" ")
            else:
                print("r%x" % (evsel), end=" ")
        if evsel & EVENTSEL_CMASK:
            print("cmask=%x" % (evsel >> 24), end=" ")
        if evsel & EVENTSEL_EDGE:
            print("edge=1", end=" ")
        if evsel & EVENTSEL_ANY:
            print("any=1", end=" ")
        if evsel & EVENTSEL_INV:
            print("inv=1", end=" ")
        if evsel & EVENTSEL_PC:
            print("pc=1", end=" ")
        if pebs_enable & (1 << i):
            print("precise=1", end=" ")
        print()
if found == 0:
    print("Cannot read any MSRs")

try:
    fixed = msr.readmsr(MSR_IA32_FIXED_CTR_CTRL)
except OSError:
    print("Cannot read fixed counter MSR")
    fixed = 0
for i in range(0, 2):
    if fixed & (1 << (i*4)):
        print("fixed %d: %s" % (i, fixednames[i]))
