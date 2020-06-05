#!/usr/bin/env python
# trace kernel PMU status changes for other programs
# perf record -a -e msr:* -o pmu.data perf .. (or other tool like toplev)
# pmutrace pmu.data
#
from __future__ import print_function
import os
import argparse
from pmudef import MSR_EVNTSEL, EVENTSEL_ENABLE, MSR_FIXED_CTR_CTL, EVMASK, MSR_GLOBAL_CTRL
import ocperf
import collections
import sys

ap = argparse.ArgumentParser(description='Decode PMU state in MSR trace')
ap.add_argument('pmudata')
args = ap.parse_args()

emap = ocperf.find_emap()
if not emap:
    sys.exit("Unknown CPU or cannot find CPU event table")

msrs = collections.defaultdict(int)

def enabled(cpu, i):
    if i < 32:
        return msrs[(cpu, MSR_EVNTSEL + i)] & EVENTSEL_ENABLE
    return msrs[(cpu, MSR_FIXED_CTR_CTL)] & (1 << (i - 32))

fixednames = (
       "inst_retired.any",
       "cpu_clk_unhalted.thread",
       "cpu_clk_unhalted.ref_tsc"
)

def resolve(cpu, i):
    if i < 32:
        event = msrs[(cpu, i + MSR_EVNTSEL)] & EVMASK
        if event in emap.codes:
            ev = emap.codes[event]
            name = ev.name
            # add extra
            # fuzzy resolve
            return name
    return fixednames[i - 32] # XX add extra

inf = os.popen("perf script -F -comm,-tid -i '%s'" % args.pmudata)
for l in inf:
    # [001] 3766869.481796: msr:write_msr: 6e0, value 5470f8ef7ff0cc
    n = l.split()
    cpu, ts, cmd, msr, val = int(n[0].strip("[]")), n[1], n[2].strip(":"), int(n[3].strip(","), 16), int(n[5], 16)

    if cmd == "msr:write_msr":
        # we assume global_ctrl is the final write to enable
        if MSR_GLOBAL_CTRL == msr:
            old = msrs[(cpu, MSR_GLOBAL_CTRL)]
            new = val ^ old
            print(ts, "%x" % new,end=" ")
            ind = 0
            while new:
                if (new & 1) and enabled(cpu, ind):
                    print("%d: ", resolve(cpu, ind), end=" ")
                new >>= 1
                ind += 1
            print
        msrs[cpu] = val
