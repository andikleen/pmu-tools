#!/usr/bin/env python
# print currently running events on cpu (default 0)
# event-rmap [cpu-num]
# xxx no pebs, no extra modi for now
import sys
import msr
import ocperf
from pmudef import *

MSR_EVNTSEL = 0x186 
MSR_IA32_FIXED_CTR_CTRL = 0x38d

fixednames = (
       "inst_retired.any",
       "cpu_clk_unhalted.thread",
       "cpu_clk_unhalted.ref_tsc"
)

cpu = 0
if len(sys.argv) > 1:
    cpu = int(sys.argv[1])

emap = ocperf.find_emap()
for i in range(0, 8):
    try:
        evsel = msr.readmsr(MSR_EVNTSEL + i, cpu)
    except OSError:
        break
    if evsel & EVENTSEL_ENABLE:
        print "%d: %016x: " % (i, evsel),
        evsel &= EVMASK
        if evsel in emap.codes:
            print emap.codes[evsel].name
        else:
            name = ""
            for j in emap.codes.keys():
                if j & 0xff == evsel & 0xff:
                    name += "%s " % (emap.codes[j].name)
            if name:
                print "[no exact match] " + name
            else:
                print "r%x" % (evsel)
if i == 0:
    print "Cannot read any MSRs"

try:
    fixed = msr.readmsr(MSR_IA32_FIXED_CTR_CTRL)
except OSError:
    print "Cannot read fixed counter MSR"
    fixed = 0
for i in range(0, 2):
    if fixed & (1 << (i*4)):
        print "fixed %d: %s" % (i, fixednames[i])
        
