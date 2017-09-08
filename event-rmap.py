#!/usr/bin/env python
# print currently running events on cpu (default 0)
# event-rmap [cpu-num]
# xxx no pebs, no extra modi for now, racy with multi plexing
import sys
import msr
import ocperf
from pmudef import *

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
except:
    pebs_enable = 0
for i in range(0, 8):
    try:
        evsel = msr.readmsr(MSR_EVNTSEL + i, cpu)
    except OSError:
        break
    found += 1
    if evsel & EVENTSEL_ENABLE:
        print "%d: %016x: " % (i, evsel),
        evsel &= EVMASK
        if evsel in emap.codes:
            ev = emap.codes[evsel]
            if ev.msr:
                try:
                    extra = msr.readmsr(ev.msr)
                except OSError:
                    print "Cannot read extra MSR %x for %s" % (ev.msr, ev.name)
                    continue
                for j in emap.codes.keys():
                    if j == evsel and extra == emap.codes[j].msrvalue:
                        print j.name, "msr:%x" % (extra),
                else:
                    print "no exact match for %s, msr %x value %x" % (ev.name,
                                                                      ev.msr, ev.msrvalue),
            else:
                print ev.name,
        else:
            name = ""
            for j in emap.codes.keys():
                if j & 0xff == evsel & 0xff:
                    name += "%s[%x] " % (emap.codes[j].name, j)
            if name:
                print "[no exact match] " + name,
            else:
                print "r%x" % (evsel),
        if evsel & EVENTSEL_CMASK:
            print "cmask=%x" % (evsel >> 24),
        if evsel & EVENTSEL_EDGE:
            print "edge=1",
        if evsel & EVENTSEL_ANY:
            print "any=1",
        if evsel & EVENTSEL_INV:
            print "inv=1",
        if evsel & EVENTSEL_PC:
            print "pc=1",
        if pebs_enable & (1 << i):
            print "precise=1",
        print
if found == 0:
    print "Cannot read any MSRs"

try:
    fixed = msr.readmsr(MSR_IA32_FIXED_CTR_CTRL)
except OSError:
    print "Cannot read fixed counter MSR"
    fixed = 0
for i in range(0, 2):
    if fixed & (1 << (i*4)):
        print "fixed %d: %s" % (i, fixednames[i])
        
