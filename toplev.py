#!/usr/bin/env python3
# Copyright (c) 2012-2025, Intel Corporation
# Author: Andi Kleen
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# Measure a workload using the topdown performance model:
# estimate on which part of the CPU pipeline it bottlenecks.
#
# Must find ocperf in python module path.
# Handles a variety of perf and kernel versions, but older ones have various
# limitations.

# Environment variables for overrides (see also tl_cpu/ocperf):
# TOPOLOGY=file     Read sysfs topology from file. Also --force-topology
# PERF=exe          Force perf binary to run
# FORCE_NMI_WATCHDOG=1  Force NMI watchdog mode
# KERNEL_VERSION=...    Force kernel version (e.g. 5.0)
# FORCEMETRICS=1    Force fixed metrics and slots
# TLSEED=n          Set seed for --subset sample: sampling
# DURATION_TIME=0   Force not using duration_time

from __future__ import print_function, division
import sys
import os
import re
import textwrap
import platform
import pty
import subprocess
import argparse
import time
import types
import csv
import bisect
import random
import json
import io
import glob
from dummyarith import DummyArith
from copy import copy
from fnmatch import fnmatch
from math import isnan
from collections import defaultdict, Counter, OrderedDict
from itertools import compress, groupby, chain
from listutils import cat_unique, dedup, filternot, not_list, append_dict, \
        zip_longest, flatten, findprefix, dummy_dict
from objutils import has, safe_ref, map_fields, ref_or

from tl_stat import ComputeStat, ValStat, combine_valstat
import tl_cpu
import tl_output
import ocperf
import event_download
from tl_uval import UVal
from tl_io import flex_open_r, flex_open_w, popentext, warn, warn_once, \
        warn_once_no_assert, print_once,                                \
        obj_debug_print, debug_print, warn_no_assert,                   \
        set_args as io_set_args
if sys.version_info.major == 3:
    import typing # noqa
    from typing import Set, List, Dict, Any, Tuple, DefaultDict # noqa

known_cpus = (
    ("snb", (42, )),
    ("jkt", (45, )),
    ("ivb", (58, )),
    ("ivt", (62, )),
    ("hsw", (60, 70, 69 )),
    ("hsx", (63, )),
    ("slm", (55, 77, 76, )),
    ("bdw", (61, 71, )),
    ("bdx", (79, 86, )),
    ("simple", ()),
    ("skl", (94, 78, 142, 158, 165, 166, )),
    ("knl", (87, )),
    ("skx", ((85, 4,), )),
    ("clx", ((85, 5,), (85, 6,), (85, 7,), (85, 8,), (85, 9,), (85, 10,), )),
    ("icl", (126, 125, 157,
             167, )), # RKL as ICL for now
    ("tgl", (140, 141, )),
    ("icx", (106, 108, )),
    ("adl", (154, 151,
             183, 186, 191, )), # RPL as ADL
    ("adl-glc", (154, )),
    ("adl-grt", (154, )),
    ("spr", (143, 
             207, )), # EMR as SPR
    ("ehl", (150, )),
    ("srf", (175, 206 )),
    ("sprmax", ()),
    ("gnr", (173, 174)),
    ("lnl", (189, )),
    ("lnl-lnc", (189, )),
    ("lnl-skt", (189, )),
    ("arl", (198, )),
    ("mtl", (170, 186, )),
    ("mtl-cmt", (170, 186, )),
    ("mtl-rwc", (170, 186, )),
)

eventlist_alias = {
} # type: Dict[str,str]

tsx_cpus = ("hsw", "hsx", "bdw", "skl", "skx", "clx", "icl", "icx",
            "spr", "sprmax", "gnr")

hybrid_cpus = ("adl", "mtl", "lnl", "arl")
atom_hybrid_cpus = ("adl-grt", "mtl-cmt", "lnl-skt", "arl-skt")

non_json_events = set(("dummy", "duration_time"))

tma_mgroups = set() # type: Set[str]

# tunables (tunable with --tune)

DEDUP_AREA = "Bottleneck"
DEDUP_NODE = ""
BOTTLENECK_LEVEL_INC = 1
IDLE_MARKER_THRESHOLD = 0.05
SIB_THRESH = 0.05
PERF_SKIP_WINDOW = 15
KEEP_UNREF = False
INAME = False
FUZZYINPUT = False

# handle kernels that don't support all events
unsup_pebs = (
    ("BR_MISP_RETIRED.ALL_BRANCHES:pp", (("hsw",), (3, 18), None)),
    ("MEM_LOAD_UOPS_L3_HIT_RETIRED.XSNP_HITM:pp", (("hsw",), (3, 18), None)),
    ("MEM_LOAD_UOPS_RETIRED.L3_MISS:pp", (("hsw",), (3, 18), None)),
)

ivb_ht_39 = (("ivb", "ivt"), (4, 1), (3, 9))
# uncomment if you removed commit 741a698f420c3 from kernel
#ivb_ht_39 = ((), None, None)

# both kernel bugs and first time a core was supported
# disable events if the kernel does not support them properly
# this does not handle backports (override with --force-events)
unsup_events = (
    # commit 36bbb2f2988a29
    ("OFFCORE_RESPONSE.DEMAND_RFO.L3_HIT.HITM_OTHER_CORE", (("hsw", "hsx"), (3, 18), None)),
    # commit 741a698f420c3 broke it, commit e979121b1b and later fixed it
    ("MEM_LOAD_UOPS_L*_HIT_RETIRED.*", ivb_ht_39),
    ("MEM_LOAD_UOPS_RETIRED.*", ivb_ht_39),
    ("MEM_LOAD_UOPS_L*_MISS_RETIRED.*", ivb_ht_39),
    ("MEM_UOPS_RETIRED.*", ivb_ht_39),
    # commit 5e176213a6b2bc
    # the event works, but it cannot put into the same group as
    # any other CYCLE_ACTIVITY.* event. For now black list, but
    # could also special case this in the group scheduler.
    ("CYCLE_ACTIVITY.STALLS_TOTAL", (("bdw", (4, 4), None))),
    # commit 91f1b70582c62576
    ("CYCLE_ACTIVITY.*", (("bdw"), (4, 1), None)),
    ("L1D_PEND_MISS.PENDING", (("bdw"), (4, 1), None)),
    # commit 6113af14c8
    ("CYCLE_ACTIVITY:CYCLES_LDM_PENDING", (("ivb", "ivt"), (3, 12), None)),
    # commit f8378f52596477
    ("CYCLE_ACTIVITY.*", (("snb", "jkt"), (3, 9), None)),
    # commit 0499bd867bd17c (ULT) or commit 3a632cb229bfb18 (other)
    # technically most haswells are 3.10, but ULT is 3.11
    ("L1D_PEND_MISS.PENDING", (("hsw",), (3, 11), None)),
    ("L1D_PEND_MISS.PENDING", (("hsx"), (3, 10), None)),
    # commit c420f19b9cdc
    ("CYCLE_ACTIVITY.*_L1D_PENDING", (("hsw", "hsx"), (4, 1), None)),
    ("CYCLE_ACTIVITY.CYCLES_NO_EXECUTE", (("hsw", "hsx"), (4, 1), None)),
    # commit 3a632cb229b
    ("CYCLE_ACTIVITY.*", (("hsw", "hsx"), (3, 11), None)))

FIXED_BASE = 50
METRICS_BASE = 100
SPECIAL_END = 130

limited_counters_base = {
    "instructions": FIXED_BASE + 0,
    "cycles": FIXED_BASE + 1,
    "ref-cycles": FIXED_BASE + 2,
    "slots": FIXED_BASE + 3,
    "cpu/slots/": FIXED_BASE + 3,
    "cpu_core/slots/": FIXED_BASE + 3,
    "topdown.slots": FIXED_BASE + 3,
    "cpu_core/topdown-fe-bound/": METRICS_BASE + 0,
    "cpu/topdown-fe-bound/": METRICS_BASE + 0,
    "cpu_core/topdown-be-bound/": METRICS_BASE + 1,
    "cpu/topdown-be-bound/": METRICS_BASE + 1,
    "cpu_core/topdown-bad-spec/": METRICS_BASE + 2,
    "cpu/topdown-bad-spec/": METRICS_BASE + 2,
    "cpu_core/topdown-retiring/": METRICS_BASE + 3,
    "cpu/topdown-retiring/": METRICS_BASE + 3,
    "cpu_core/topdown-heavy-ops/": METRICS_BASE + 4,
    "cpu/topdown-heavy-ops/": METRICS_BASE + 4,
    "cpu/topdown-br-mispredict/": METRICS_BASE + 5,
    "cpu_core/topdown-br-mispredict/": METRICS_BASE + 5,
    "cpu_core/topdown-mem-bound/": METRICS_BASE + 6,
    "cpu/topdown-mem-bound/": METRICS_BASE + 6,
    "cpu/topdown-fetch-lat/": METRICS_BASE + 7,
    "cpu_core/topdown-fetch-lat/": METRICS_BASE + 7,
    "cpu/cycles-ct/": 2,
    "cpu_core/cycles-ct/": 2,
}

promotable_limited = set((
    "instructions",
    "cycles",
    "slots",
    "cpu/slots/",
    "cpu_core/slots/")
)

Undef = UVal("undef", 0)

# should clean those up, but they're all read-only after initialization anyways
global smt_mode
global output_numcpus
global metrics_own_group
global run_l1_parallel

class EventContextBase(object):
    def __init__(self):
        self.constraint_fixes = {}
        self.constraint_patterns = []
        self.errata_whitelist = []
        self.outgroup_events = set()
        self.sched_ignore_events = set()
        self.require_pebs_events = set()
        self.core_domains = set()
        self.limited_counters = {}
        self.limited_set = set()
        self.fixed_events = set()
        self.errata_events = {}
        self.errata_warn_events = {}
        self.limit4_events = set()
        self.notfound_cache = {}
        self.rmap_cache = {}
        self.slots_available = False
        self.standard_counters = tuple("") # type: Tuple[str, ...]
        self.counters = 0
        self.limit4_counters = ""
        self.force_metrics = False
        self.metrics_override = False

    def init_emap(self, emap):
        self.emap = emap

class EventContext(EventContextBase):
    """Event related context for a given target CPU."""
    def __init__(self, pmu):
        EventContextBase.__init__(self)
        self.outgroup_events = set(["dummy", "duration_time", "msr/tsc/"])
        self.core_domains = set(["Slots", "CoreClocks", "CoreMetric",
            "Core_Execution", "Core_Clocks", "Core_Metric"])
        self.limited_counters = dict(limited_counters_base)
        self.limited_set = set(self.limited_counters.keys())
        self.fixed_events = set([x for x in self.limited_counters
                                 if FIXED_BASE <= self.limited_counters[x] <= SPECIAL_END])
        if (pmu is None
                or pmu not in cpu.counters
                or pmu not in cpu.standard_counters
                or pmu not in cpu.limit4_counters):
            pmu = "cpu"
        self.standard_counters = cpu.standard_counters[pmu]
        self.counters = cpu.counters[pmu]
        self.limit4_counters = cpu.limit4_counters[pmu]

smt_mode = False

def works(x):
    return os.system(x + " >/dev/null 2>/dev/null") == 0

exists_cache = {} # type: Dict[str,bool]

def cached_exists(fn):
    if fn in exists_cache:
        return exists_cache[fn]
    found = os.path.exists(fn)
    exists_cache[fn] = found
    return found

def safe_int(x):
    try:
        return int(x)
    except ValueError:
        return 0

def event_nocheck():
    return args.import_ or args.no_check

class PerfFeatures(object):
    """Adapt to the quirks of various perf versions."""
    def __init__(self, args):
        pmu = "cpu"
        if os.path.exists("/sys/bus/event_source/devices/cpu_core"):
            pmu = "cpu_core"
        p = os.getenv("PERF")
        self.perf = p if p else "perf"
        ret = os.system(self.perf + " stat --log-fd 3 3>/dev/null true")
        if ret:
            # work around the insane perf setup on Debian derivates
            # it fails if the perf isn't the same as the kernel
            # look for the underlying perf installs, if any
            # perf is compatible, so just pick the newest
            if ret == 512:
                l = sorted(glob.glob("/usr/lib/linux-tools*/perf"),
                          key=lambda x: [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', x)])
                if len(l) > 0:
                    self.perf = l[0]
                    ret = os.system(self.perf + " stat --log-fd 3 3>/dev/null true")
                if ret:
                    sys.exit("perf binary is too old/not installed or perf is disabled in /proc/sys/kernel/perf_event_paranoid")
        self.logfd_supported = ret == 0
        self.supports_power = (
                not args.no_uncore
                and not args.force_hypervisor
                and os.path.exists("/sys/bus/event_source/devices/power/events/energy-cores"))
        with os.popen(self.perf + " --version") as f:
            v = f.readline().split()
            perf_version = tuple(map(safe_int, v[2].split(".")[:2])) if len(v) >= 3 else (0,0)

        self.supports_percore = (perf_version >= (5,7) or
                                 works(self.perf + " stat --percore-show-thread true"))
        dt = os.getenv("DURATION_TIME")
        if dt:
            self.supports_duration_time = int(dt)
        else:
            self.supports_duration_time = (perf_version >= (5,2) or
                    works(self.perf + " stat -e duration_time true"))
        # guests don't support offcore response
        if event_nocheck():
            self.has_max_precise = True
            self.max_precise = 3
        else:
            self.has_max_precise = os.path.exists("/sys/bus/event_source/devices/%s/caps/max_precise" % pmu)
            if self.has_max_precise:
                self.max_precise = int(open("/sys/bus/event_source/devices/%s/caps/max_precise" % pmu).read())
        if args.exclusive and not args.print and not (perf_version >= (5,10) or works(self.perf + " stat -e '{branches,branches,branches,branches}:e' true")):
            sys.exit("perf binary does not support :e exclusive modifier")

def kv_to_key(v):
    return v[0] * 100 + v[1]

def unsup_event(e, table, kernel_version, min_kernel=None):
    if ":" in e:
        e = e[:e.find(":")]
    for j in table:
        if fnmatch(e, j[0]) and cpu.realcpu in j[1][0]:
            break
    else:
        return False
    v = j[1]
    if v[1] and kernel_version < kv_to_key(v[1]):
        if min_kernel:
            min_kernel.append(v[1])
        return True
    if v[2] and kernel_version >= kv_to_key(v[2]):
        return False
    return False

def remove_qual(ev):
    def get_group(prefix, m):
        if m.group(1):
            return prefix + m.group(1)
        return prefix

    return re.sub(r':(p?)[kuhgHeD]+$', lambda m: get_group("", m), re.sub(r'/(p?)[kuhgHeD]+$', lambda m: get_group("/", m), ev))

def limited_overflow(evlist, num):
    class GenericCounters:
        def __init__(self):
            self.num = 0

    def gen_overflow(c, gc, inc):
        if c in promotable_limited:
            gc.num += inc - 1
            return False
        return True

    assigned = Counter([ectx.limited_counters[remove_qual(x)] for x in evlist if remove_qual(x) in ectx.limited_counters])
    gc = GenericCounters()
    return any([x > 1 and gen_overflow(k, gc, x) for k, x in assigned.items()]), gc.num

# we limit to 3 events because one could be taken up by the nmi watchdog
# and also there's some kernel issue that sometimes only 3 fit on ICL
LIMIT4_MAX_EVENTS = 3

# limited to first four counters on ICL+
def limit4_overflow(evlist):
    return sum([remove_qual(x) in ectx.limit4_events for x in evlist]) > LIMIT4_MAX_EVENTS

def ismetric(x):
    return x.startswith(("topdown-", "cpu_core/topdown-", "cpu/topdown-"))

resources = ("frontend=", "offcore_rsp=", "ldlat=", "in_tx_cp=", "cycles-ct")

def event_to_resource(ev):
    for j in resources:
        if remove_qual(j) in ev:
            return j
    return ""

def resource_split(evlist):
    r = Counter(map(event_to_resource, evlist))
    for j in sorted(r.keys()):
        if j == "":
            continue
        if j == "offcore_rsp=":
            if r[j] > 2:
                return True
        elif r[j] > 1:
            return True
    return False

def num_generic_counters(evset):
    # XXX does not handle formulas having different u/k qualifiers, but we would need to fix the
    # callers to be consistent to handle that
    return len(evset - set(add_filter(ectx.fixed_events)) - ectx.fixed_events - ectx.outgroup_events - ectx.sched_ignore_events)

FORCE_SPLIT = 100
FORCE_SPLIT_LIMIT4 = 101

# Force metrics into own group
metrics_own_group = True

def is_slots(x):
    return re.match(r'(cpu/|cpu_core/)?slots[,/]', x) is not None

def needed_counters(evlist):
    evset = set(evlist)
    num = num_generic_counters(evset)

    metrics = [ismetric(x) for x in evlist]
    slots = [is_slots(x) for x in evlist]

    if any(metrics) or any(slots):
        # slots must be first if metrics are present
        if any(map(is_slots, evlist)) and not is_slots(evlist[0]):
            debug_print("split for slots %s" % evlist)
            return FORCE_SPLIT
        # force split if there are other events.
        if metrics_own_group and len(evlist) > sum(metrics) + 1:
            debug_print("split for other events in topdown %s" % evlist)
            return FORCE_SPLIT

    # split if any resource is oversubscribed
    if resource_split(evlist):
        debug_print("resource split %s" % evlist)
        return FORCE_SPLIT

    evlist = list(compress(evlist, not_list(metrics)))

    # force split if we overflow fixed or limited
    l_over, numg = limited_overflow(evlist, num)
    if l_over:
        debug_print("split for limited overflow %s " % evlist)
        return FORCE_SPLIT

    if limit4_overflow(evlist):
        debug_print("split for limit4 overflow %s" % evlist)
        return FORCE_SPLIT_LIMIT4

    return num + numg

def event_group(evlist):
    evlist = add_filter(evlist)
    l = [] # type: List[str]
    pgroup = False
    for is_og, g in groupby(evlist, lambda x: x in ectx.outgroup_events):
        gl = list(g)
        slots_or_metric = [ismetric(x) or is_slots(x) for x in gl]
        # keep the groups for slots or metric because of some kernel
        # requirements and also some perf versions reorder slots with no group.
        if is_og or (args.no_group and not any(slots_or_metric)):
            l += gl
        else:
            e = ",".join(gl)
            e = "{%s}" % e
            if args.exclusive or args.pinned or args.weak or args.host or args.guest:
                e += ":"
            if args.weak:
                e += "W"
            if args.exclusive:
                e += "e"
            if args.guest:
                e += "G"
            if args.host:
                e += "H"
            elif args.pinned:
                if all(slots_or_metric):
                    e += "D"
                    assert pgroup is False
                    assert is_slots(gl[0])
                    pgroup = True
                else:
                    assert not any(slots_or_metric)

            l.append(e)
    return ",".join(l)

def exe_dir():
    d = os.path.realpath(sys.argv[0])
    d = os.path.dirname(d)
    if d:
        return d
    return "."

def add_args(rest, *args):
    a = [x for x in args if x not in rest]
    return a + rest

def update_arg(arg, flag, sep, newval):
    i = findprefix(arg, flag, "--")
    if i >= 0:
        if arg[i] == flag:
            arg[i+1] = newval
        else:
            arg[i] = flag + sep + newval
        return True
    return False

def del_arg_val(arg, flag):
    i = findprefix(arg, flag, "--")
    del arg[i:i+2 if arg[i] == flag else i+1]

def init_args():
    p = argparse.ArgumentParser(usage='toplev [options] perf-arguments',
    description='''
Estimate on which part of the CPU pipeline a workload bottlenecks using the TopDown model.
The bottlenecks are expressed as a tree with different levels.
Requires a modern Intel CPU.

Examples:


toplev -l1 --single-thread program
measure single threaded program. On hyper threaded systems with
Skylake or older the system should be idle.

toplev -NB program
Measure program showing consolidated bottleneck view and extra
information associated with bottlenecks. Note this will multiplex
performance counters, so there may be measuring errors.

toplev -NB --run-sample program
Measure programing showing bottlenecks and extra nodes, and
automatically sample for the location of bottlenecks in a second
pass.

toplev --drilldown --only-bottleneck program
Rerun workload with minimal multiplexing until critical bottleneck
is found. Only print critical bottleneck

toplev -l3 --no-desc -I 100 -x, sleep X
measure whole system for X seconds every 100ms, outputting in CSV format.

toplev --all --core C0 taskset -c 0,1 program
Measure program running on core 0 with all nodes and metrics enables

toplev --all --xlsx x.xlsx -a sleep 10
Generate spreadsheet with full system measurement for 10 seconds
''', epilog='''
Other perf arguments allowed (see the perf documentation)
After -- perf arguments conflicting with toplev can be used.

Some caveats:

toplev defaults to measuring the full system and show data
for all CPUs. Use taskset to limit the workload to known CPUs if needed.
In some cases (idle system, single threaded workload) --single-thread
can also be used to get less output.

The lower levels of the measurement tree are less reliable
than the higher levels.  They also rely on counter multi-plexing,
and can not run each equation in a single group, which can cause larger
measurement errors with non steady state workloads

(If you don't understand this terminology; it means measurements
in higher levels are less accurate and it works best with programs that primarily
do the same thing over and over)

If the program is very reproducible -- such as a simple kernel --
it is also possible to use --no-multiplex. In this case the
workload is rerun multiple times until all data is collected.

Only use with sleep if the workload is running in a steady state.

With the --drilldown option toplev can automatically remeasure the workload
with only the nodes needed to measure the particular bottlenecks
This also requires a reproducible or steady-state workload.

toplev needs a new enough perf tool and has specific requirements on
the kernel. See http://github.com/andikleen/pmu-tools/wiki/toplev-kernel-support.''',
    formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_argument_group('General operation')
    g.add_argument('--interval', '-I', help='Measure every ms instead of only once',
                   type=int)
    g.add_argument('--no-multiplex',
                   help='Do not multiplex, but run the workload multiple times as needed. '
                   'Requires reproducible workloads.',
                   action='store_true')
    g.add_argument('--single-thread', '-S', help='Measure workload as single thread. Workload must run single threaded. '
                   'In SMT mode other thread must be idle.', action='store_true')
    g.add_argument('--fast', '-F', help='Skip sanity checks to optimize CPU consumption', action='store_true')
    g.add_argument('--import', help='Import specified perf stat output file instead of running perf. '
                   'Must be for same cpu, same arguments, same /proc/cpuinfo, same topology, unless overriden',
                    dest='import_')
    g.add_argument('--subset', help="Process only a subset of the input file with --import. "
            "Valid syntax: a-b. Process from seek offset a to b. b is optional. "
            "x/n%% process x'th n percent slice. Starts counting at 0. Add - to process to end of input. "
            "sample:n%% Sample each time stamp in input with n%% (0-100%%) probability. "
            "toplev will automatically round to the next time stamp boundary.")
    g.add_argument('--parallel',
            help="Run toplev --import in parallel in N processes, or the system's number of CPUs if 0 is specified",
            action='store_true')
    g.add_argument('--pjobs', type=int, default=0,
            help='Number of threads to run with parallel. Default is number of CPUs.')
    g.add_argument('--gen-script', help='Generate script to collect perfmon information for --import later',
                   action='store_true')
    g.add_argument('--script-record', help='Use perf stat record in script for faster recording or '
                   'import generated perf.data (requires new perf)', action='store_true')
    g.add_argument('--drilldown', help='Automatically rerun to get more details on bottleneck', action='store_true')
    g.add_argument('--show-cpu', help='Print current CPU type and exit',
                action='store_true')

    g = p.add_argument_group('Measurement filtering')
    g.add_argument('--kernel', help='Only measure kernel code', action='store_true')
    g.add_argument('--user', help='Only measure user code', action='store_true')
    g.add_argument('--cpu', '-C', help=argparse.SUPPRESS)
    g.add_argument('--pid', '-p', help=argparse.SUPPRESS)
    g.add_argument('--core', help='Limit output to cores. Comma list of Sx-Cx-Tx. All parts optional.')
    g.add_argument('--no-aggr', '-A', help='Measure every CPU', action='store_true')
    g.add_argument('--cputype', help='Limit to hybrid cpu type (atom or core)', choices=['atom', 'core'])

    g = p.add_argument_group('Select events')
    g.add_argument('--level', '-l', help='Measure upto level N (max 6)',
                   type=int, default=-1)
    g.add_argument('--metrics', '-m', help="Print extra metrics", action='store_true')
    g.add_argument('--sw', help="Measure perf Linux metrics", action='store_true')
    g.add_argument('--no-util', help="Do not measure CPU utilization", action='store_true')
    g.add_argument('--tsx', help="Measure TSX metrics", action='store_true')
    g.add_argument('--all', help="Measure everything available", action='store_true')
    g.add_argument('--frequency', help="Measure frequency", action='store_true')
    g.add_argument('--power', help='Display power metrics', action='store_true')
    g.add_argument('--nodes', help='Include or exclude nodes (with + to add, -|^ to remove, '
                   'comma separated list, wildcards allowed, add * to include all children/siblings, '
                   'add /level to specify highest level node to match, '
                   'add ^ to match related siblings and metrics, '
                   'start with ! to only include specified nodes)')
    g.add_argument('--metric-group', help='Add (+) or remove (-|^) metric groups of metrics, '
                   'comma separated list from --list-metric-groups.', default=None)
    g.add_argument('--areas', help='Add specific areas. Comma separate list, wildcards allowed')
    g.add_argument('--pinned', help='Run topdown metrics (on ICL+) pinned', action='store_true')
    g.add_argument('--exclusive', help='Use exclusive groups. Requires new kernel and new perf', action='store_true')
    g.add_argument('--host', action='store_true', help="Count host only")
    g.add_argument('--guest', action='store_true', help="Count guest only")
    g.add_argument('--weak', action='store_true', help="Use weak groups to work around scheduling problems")
    g.add_argument('--thread',
            help="Enable per thread SMT measurements for pre-ICL, at the cost of more multiplexing.",
            action='store_true')
    g.add_argument('--aux', help='Enable auxilliary hierarchy nodes on some models. '
                                 'Auxiliary nodes offer alternate views of the same bottleneck component, which can impact observed bottleneck percentage totals',
                action='store_true')
    g.add_argument('--node-metrics', '-N', help='Add metrics related to selected nodes, but hide when node is not crossing threshold',
                    action='store_true')
    g.add_argument('--bottlenecks', '-B', help='Show bottlenecks view of Bottleneck metrics. Use -l0 to disable standard topdown view.', action='store_true')

    g = p.add_argument_group('Model tunables')
    g.add_argument('--fp16', help='Enable FP16 support in some models', action='store_true')
    g.add_argument('--hbm-only', help='Enable HBM only mode in some models', action='store_true')
    g.add_argument('--ret-latency', help='Read JSON file with Retire latencies. Can specify path inside JSON file with :, for example foo.json:6-cores:MEAN')

    g = p.add_argument_group('Query nodes')
    g.add_argument('--list-metrics', help='List all metrics. Can be followed by prefixes to limit, ^ for full match',
                action='store_true')
    g.add_argument('--list-nodes', help='List all nodes. Can be followed by prefixes to limit, ^ for full match',
                action='store_true')
    g.add_argument('--list-metric-groups', help='List metric groups.', action='store_true')
    g.add_argument('--list-all', help='List every supported node/metric/metricgroup. Can be followed by prefixes to limit, ^ for full match.',
                action='store_true')
    g.add_argument('--describe', help='Print full descriptions for listed node prefixes. Add ^ to require full match.', action='store_true')

    g = p.add_argument_group('Workarounds')
    g.add_argument('--no-group', help='Dont use groups', action='store_true')
    g.add_argument('--force-events', help='Assume kernel supports all events. May give wrong results.',
                   action='store_true')
    g.add_argument('--ignore-errata', help='Do not disable events with errata', action='store_true', default=True)
    g.add_argument('--handle-errata', help='Disable events with errata', action='store_true')
    g.add_argument('--reserved-counters', default=0, help='Assume N generic counters are used elsewhere', type=int)

    g = p.add_argument_group('Filtering output')
    g.add_argument('--only-bottleneck', help='Only print topdown tree bottleneck and associated metrics (unless overriden with other options like --nodes or --bottleneck)', action='store_true')
    g.add_argument('--verbose', '-v', help='Print all results even when below threshold or exceeding boundaries. '
                   'Note this can result in bogus values, as the TopDown methodology relies on thresholds '
                   'to correctly characterize workloads. Values not crossing threshold are marked with <.',
                   action='store_true')

    g = p.add_argument_group('Output format')
    g.add_argument('--per-core', help='Aggregate output per core', action='store_true')
    g.add_argument('--per-socket', help='Aggregate output per socket', action='store_true')
    g.add_argument('--per-thread', help='Aggregate output per CPU thread', action='store_true')
    g.add_argument('--global', help='Aggregate output for all CPUs', action='store_true', dest='global_')
    g.add_argument('--no-desc', help='Do not print event descriptions', action='store_true')
    g.add_argument('--desc', help='Force event descriptions', action='store_true')
    g.add_argument('--csv', '-x', help='Enable CSV mode with specified delimeter')
    g.add_argument('--output', '-o', help='Set output file')
    g.add_argument('--split-output', help='Generate multiple output files, one for each specified '
                   'aggregation option (with -o)',
                   action='store_true')
    g.add_argument('--graph', help='Automatically graph interval output with tl-barplot.py',
                   action='store_true')
    g.add_argument("--graph-cpu", help="CPU to graph using --graph")
    g.add_argument('--title', help='Set title of graph')
    g.add_argument('-q', '--quiet', help='Avoid unnecessary status output', action='store_true')
    g.add_argument('--long-desc', help='Print long descriptions instead of abbreviated ones.',
                    action='store_true')
    g.add_argument('--columns', help='Print CPU output in multiple columns for each node', action='store_true')
    g.add_argument('--json', help='Print output in JSON format for Chrome about://tracing', action='store_true')
    g.add_argument('--summary', help='Print summary at the end. Only useful with -I', action='store_true')
    g.add_argument('--no-area', help='Hide area column', action='store_true')
    g.add_argument('--perf-output', help='Save perf stat output in specified file')
    g.add_argument('--perf-summary', help='Save summarized perf stat output in specified file')
    g.add_argument('--no-perf', help=argparse.SUPPRESS, action='store_true') # noop, for compatibility
    g.add_argument('--perf', help='Print perf command line', action='store_true')
    g.add_argument('--print', help="Only print perf command line. Don't run", action='store_true')
    g.add_argument('--idle-threshold', help="Hide idle CPUs (default <5%% of busiest if not CSV, specify percent)",
                   default=None, type=float)
    g.add_argument('--no-output', help="Don't print computed output. Does not affect --summary.", action='store_true')
    g.add_argument('--no-mux', help="Don't print mux statistics", action="store_true")
    g.add_argument('--abbrev', help="Abbreviate node names in output", action="store_true")
    g.add_argument('--no-sort', help="Don't sort output by Metric group", action="store_true")

    g = p.add_argument_group('Environment')
    g.add_argument('--force-cpu', help='Force CPU type', choices=[x[0] for x in known_cpus])
    g.add_argument('--force-topology', metavar='findsysoutput', help='Use specified topology file (find /sys/bus/event_source/devices/)')
    g.add_argument('--force-cpuinfo', metavar='cpuinfo', help='Use specified cpuinfo file (/proc/cpuinfo)')
    g.add_argument('--force-hypervisor', help='Assume running under hypervisor (no uncore, no offcore, no PEBS)',
                   action='store_true')
    g.add_argument('--no-uncore', help='Disable uncore events', action='store_true')
    g.add_argument('--no-check', help='Do not check that PMU units exist', action='store_true')

    g = p.add_argument_group('Additional information')
    g.add_argument('--print-group', '-g', help='Print event group assignments',
                   action='store_true')
    g.add_argument('--raw', help="Print raw values", action='store_true')
    g.add_argument('--valcsv', '-V', help='Write raw counter values into CSV file')
    g.add_argument('--stats', help='Show statistics on what events counted', action='store_true')

    g = p.add_argument_group('xlsx output')
    g.add_argument('--xlsx', help='Generate xlsx spreadsheet output with data for '
                   'socket/global/thread/core/summary/raw views with 1s interval. '
                   'Add --single-thread to only get program output.')
    g.add_argument('--set-xlsx', help=argparse.SUPPRESS, action='store_true') # set arguments for xlsx only
    g.add_argument('--xnormalize', help='Add extra sheets with normalized data in xlsx files', action='store_true')
    g.add_argument('--xchart', help='Chart data in xlsx files', action='store_true')
    g.add_argument('--keep', help='Keep temporary files', action='store_true')
    g.add_argument('--xkeep', dest='keep', action='store_true', help=argparse.SUPPRESS)

    g = p.add_argument_group('Sampling')
    g.add_argument('--show-sample', help='Show command line to rerun workload with sampling', action='store_true')
    g.add_argument('--run-sample', help='Automatically rerun workload with sampling', action='store_true')
    g.add_argument('--sample-args', help='Extra arguments to pass to perf record for sampling. Use + to specify -',
                   default='-g')
    g.add_argument('--sample-repeat',
                   help='Repeat measurement and sampling N times. This interleaves counting and sampling. '
                   'Useful for background collection with -a sleep X.', type=int)
    g.add_argument('--sample-basename', help='Base name of sample perf.data files', default="perf.data")

    g.add_argument('-d', help=argparse.SUPPRESS, action='help') # prevent passing this to perf

    p.add_argument('--version', help=argparse.SUPPRESS, action='store_true')
    p.add_argument('--debug', help=argparse.SUPPRESS, action='store_true') # enable scheduler debugging
    p.add_argument('--dfilter', help=argparse.SUPPRESS, action='append')
    p.add_argument('--repl', action='store_true', help=argparse.SUPPRESS) # start python repl after initialization
    p.add_argument('--filterquals', help=argparse.SUPPRESS, action='store_true') # remove events not supported by perf
    p.add_argument('--setvar', help=argparse.SUPPRESS, action='append') # set env variable (for test suite iterating options)
    p.add_argument('--tune', nargs='+', help=argparse.SUPPRESS) # override global variables with python expression
    p.add_argument('--tune-model', nargs='+', help=argparse.SUPPRESS) # override global variables late with python expression
    p.add_argument('--force-bn', action='append', help=argparse.SUPPRESS) # force bottleneck for testing
    p.add_argument('--no-json-header', action='store_true', help=argparse.SUPPRESS) # no [ for json
    p.add_argument('--no-json-footer', action='store_true', help=argparse.SUPPRESS) # no ] for json
    p.add_argument('--no-csv-header', action='store_true', help=argparse.SUPPRESS) # no header/version for CSV
    p.add_argument('--no-csv-footer', action='store_true', help=argparse.SUPPRESS) # no version for CSV
    p.add_argument('--no-version', action='store_true', help="Don't print version")
    args, rest = p.parse_known_args()
    io_set_args(args)
    if args.setvar:
        for j in args.setvar:
            l = j.split("=")
            os.environ[l[0]] = l[1]
    return args, rest

def output_count():
    return args.per_core + args.global_ + args.per_thread + args.per_socket

def multi_output():
    return output_count() > 1

def open_output_files(args):
    if args.valcsv:
        try:
            args.valcsv = flex_open_w(args.valcsv)
        except IOError as e:
            sys.exit("Cannot open valcsv file %s: %s" % (args.valcsv, e))

    if args.perf_output:
        try:
            args.perf_output = flex_open_w(args.perf_output)
        except IOError as e:
            sys.exit("Cannot open perf output file %s: %s" % (args.perf_output, e))

def init_xlsx(args):
    args.set_xlsx = True
    if args.output:
        sys.exit("-o / --output not allowed with --xlsx")
    if args.valcsv:
        sys.exit("--valcsv not allowed with --xlsx")
    if args.perf_output:
        sys.exit("--perf-output not allowed with --xlsx")
    if args.csv:
        sys.exit("-c / --csv not allowed with --xlsx")
    if args.thread:
        sys.exit("--thread not supported with --xlsx") # XXX
    if not args.xlsx.endswith(".xlsx"):
        sys.exit("--xlsx must end in .xlsx")
    xlsx_base = re.sub(r'\.xlsx$', '.csv', args.xlsx)
    args.valcsv = re.sub(r'\.csv$', '-valcsv.csv', xlsx_base)
    args.perf_output = re.sub(r'\.csv$', '-perf.csv', xlsx_base)
    args.output = xlsx_base
    if args.xchart:
        args.xnormalize = True
        args.verbose = True

forced_per_socket = False
forced_per_core = False

def set_xlsx(args):
    if not args.interval:
        args.interval = 1000
    args.csv = ','
    if args.xlsx:
        args.summary = True
    if not args.single_thread:
        args.per_thread = True
        args.split_output = True
        global forced_per_socket
        if args.per_socket:
            forced_per_socket = True
        global forced_per_core
        if args.per_core:
            forced_per_core = True
        args.per_socket = True
        args.per_core = True
        args.no_aggr = True
        args.global_ = True

def do_xlsx(env, args):
    cmd = "%s %s/tl-xlsx.py --valcsv '%s' --perf '%s' --cpuinfo '%s' " % (
        sys.executable,
        exe_dir(),
        args.valcsv.name,
        args.perf_output.name,
        env.cpuinfo if env.cpuinfo else "/proc/cpuinfo")
    if args.single_thread:
        names = ["program"]
        files = [args.output if args.output else "program"]
    else:
        names = ((["socket"] if args.per_socket else []) +
                 (["core"] if args.per_core else []) +
                 ["global", "thread"])
        files = [tl_output.output_name(args.output, p) for p in names]

    extrafiles = []
    extranames = []
    charts = []
    if args.xnormalize:
        for j, n in zip(files, names):
            nname = j.replace(".csv", "-norm.csv")
            ncmd = "%s %s/interval-normalize.py --normalize-cpu --error-exit < '%s' > '%s'" % (
                    sys.executable,
                    exe_dir(),
                    j,
                    nname)
            if not args.quiet:
                print(ncmd)
            ret = os.system(ncmd)
            if ret:
                warn("interval-normalize failed: %d" % ret)
                return ret
            extrafiles.append(nname)
            extranames.append("n" + n)
            if args.xchart:
                charts.append("n" + n)

    cmd += " ".join(["--%s '%s'" % (n, f) for n, f in zip(names, files)])
    cmd += " " + " ".join(["--add '%s' '%s'" % (f, n) for n, f in zip(extranames, extrafiles)])
    cmd += " " + " ".join(["--chart '%s'" % f for f in charts])
    cmd += " '%s'" % args.xlsx
    if not args.quiet:
        print(cmd)
    ret = os.system(cmd)
    if not args.keep:
        for fn in files + extrafiles:
            os.remove(fn)
    return ret

def gentmp(o, cpu):
    o = re.sub(r'\.(xz|gz)', '', o)
    if o.endswith(".csv"):
        return o.replace(".csv", "-cpu%d.csv" % cpu)
    return o + "-cpu%d" % cpu

def output_to_tmp(arg, outfn, args):
    if not args.output or args.xlsx:
        arg.insert(1, "-o" + outfn)
    elif update_arg(arg, "--output", "=", outfn):
        pass
    elif update_arg(arg, "-o", "", outfn):
        pass
    else:
        # does not handle -o combined with other one letter options
        sys.exit("Use plain -o / --output argument with --parallel")

def merge_files(files, outf, args):
    for j in files:
        tl_output.catrmfile(j, outf, args.keep)

# run multiple subset toplevs in parallel and merge the results
def run_parallel(args, env):
    procs = []
    pofns = []
    valfns = []
    sums = []
    targ = copy(sys.argv)
    del targ[targ.index("--parallel")]
    ichunk = os.path.getsize(args.import_) / args.pjobs
    fileoff = 0
    for cpu in range(args.pjobs):
        arg = copy(targ)
        if args.xlsx:
            del_arg_val(arg, "--xlsx")
            arg = [arg[0], "--set-xlsx", "--perf-output=X", "--valcsv=X"] + arg[1:]
        outfn = gentmp(args.output if args.output else "toplevo%d" % os.getpid(), cpu)
        output_to_tmp(arg, outfn, args)
        if args.perf_output or args.xlsx:
            pofn = gentmp(args.perf_output if args.perf_output else "toplevp", cpu)
            update_arg(arg, "--perf-output", "=", pofn)
            pofns.append(pofn)
        if args.valcsv or args.xlsx:
            valfn = gentmp(args.valcsv if args.valcsv else "toplevv", cpu)
            update_arg(arg, "--valcsv", "=", valfn)
            valfns.append(valfn)
        end = ""
        if cpu < args.pjobs-1:
            end = "%d" % (fileoff + ichunk)
        arg.insert(1, ("--subset=%d-" % fileoff) + end)
        fileoff += ichunk
        if args.json and args.pjobs > 1:
            if cpu > 0:
                arg.insert(1, "--no-json-header")
            if cpu < args.pjobs - 1 or args.summary:
                arg.insert(1, "--no-json-footer")
        sumfn = None
        if args.summary:
            del arg[arg.index("--summary")]
            sumfn = gentmp("toplevs%d" % os.getpid(), cpu)
            arg.insert(1, "--perf-summary=" + sumfn)
            sums.append(sumfn)
        if args.pjobs > 1:
            if cpu > 0:
                arg.insert(1, "--no-csv-header")
            if cpu < args.pjobs - 1 or args.summary:
                arg.insert(1, "--no-csv-footer")
        if not args.quiet:
            print(" ".join(arg))
        pp = subprocess.Popen(arg, stdout=subprocess.PIPE, **popentext) # type: ignore
        procs.append((pp, outfn))
    if args.xlsx:
        init_xlsx(args)
        set_xlsx(args)
    logfiles, logf = tl_output.open_all_logfiles(args, args.output)
    for p in procs:
        ret = p[0].wait()
        if ret:
            sys.exit("Subprocess toplev failed %d" % ret)
        tl_output.catrmoutput(p[1], logf, logfiles, args.keep)
    ret = 0
    if sums:
        cmd = [sys.executable, exe_dir() + "/interval-merge.py"] + sums
        if not args.quiet:
            print(" ".join(cmd))
        inp = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        outfn = "toplevm%d" % os.getpid()
        output_to_tmp(targ, outfn, args)
        if args.xlsx:
            del_arg_val(targ, "--xlsx")
            targ.insert(1, "--set-xlsx")
        if args.perf_output:
            del_arg_val(targ, "--perf-output")
        if args.valcsv:
            del_arg_val(targ, "--valcsv")
        update_arg(targ, "--import", "=", "/dev/stdin")
        targ.insert(1, "--no-output")
        if args.json:
            targ.insert(1, "--no-json-header")
        else:
            targ.insert(1, "--no-csv-header")
        if not args.quiet:
            print(" ".join(targ))
        outp = subprocess.Popen(targ, stdin=inp.stdout)
        ret = inp.wait()
        if ret:
            sys.exit("interval-merge failed")
        ret = outp.wait()
        if ret:
            sys.exit("summary toplev failed")
        tl_output.catrmoutput(outfn, logf, logfiles, args.keep)
        if not args.keep:
            for j in sums:
                os.remove(j)
    open_output_files(args)
    merge_files(valfns, args.valcsv, args)
    merge_files(pofns, args.perf_output, args)
    if args.xlsx:
        ret = do_xlsx(env, args)
    # XXX graph
    return ret

def init_idle_threshold(args):
    if args.idle_threshold:
        idle_threshold = args.idle_threshold / 100.
    elif args.csv or args.xlsx or args.set_xlsx: # not for args.graph
        idle_threshold = 0  # avoid breaking programs that rely on the CSV output
    else:
        idle_threshold = 0.05
    return idle_threshold

ret_latency = None

def setup_retlatency(args):
    global ret_latency
    if args.ret_latency:
        try:
            l = args.ret_latency.split(":")
            ret_latency = json.load(open(l[0]))["Data"]
        except IOError:
            sys.exit("Cannot open %s" % l[0])
        except KeyError:
            sys.exit("retlat file has unparseable format")
    else:
        load_default_retlat()

def lookup_retlat(event):
    if ret_latency is None:
        warn_once("No --ret-latency for %s" % event)
        return 1.0
    try:
        l = args.ret_latency.split(":") if args.ret_latency else ()
        o = ret_latency[event]
        return o["MEAN"]

        for k in l[1:]:
            if k in o[0] or k.upper() in o[0]:
                o = o[0][k]
                # XXX check for remaining arguments
                break
            if k not in o[1] and k.upper() in o[1]:
                k = k.upper()
                o = o[1][k]
        if type(o) is list:
            o = o[0]["MEAN"]
        return o
    except KeyError as e:
        warn_once("bad ret latency key %s" % e)
        return 1.0 # XXX

def gen_cpu_name(cpu):
    if cpu == "simple":
        c = event_download.get_cpustr()
        if not c.startswith("GenuineIntel"): # fix github runner
            c = "GenuineIntel-6-4E"
        return c
    if cpu == "sprmax":
        cpu = "spr"
    for j in known_cpus:
        if cpu == j[0]:
            if len(j[1]) > 0 and isinstance(j[1][0], tuple):
                return "GenuineIntel-6-%02X-%d" % j[1][0]
            else:
                if len(j[1]) == 0:
                    sys.exit("Cannot generate cpu name for %s" % cpu)
                if j[1][0] in eventlist_alias:
                    return eventlist_alias[j[1][0]] # type: ignore
                return "GenuineIntel-6-%02X" % j[1][0]  # type: ignore
    sys.exit("Unknown cpu %s" % cpu)
    return None

def update_args(args, env):
    if args.force_cpu:
        env.forcecpu = args.force_cpu
        cpuname = gen_cpu_name(args.force_cpu)
        if not os.getenv("EVENTMAP"):
            os.environ["EVENTMAP"] = cpuname
        if not os.getenv("UNCORE"):
            os.environ["UNCORE"] = cpuname
    if args.force_topology:
        if not os.getenv("TOPOLOGY"):
            os.environ["TOPOLOGY"] = args.force_topology
            ocperf.topology = None # force reread
    if args.force_cpuinfo:
        env.cpuinfo = args.force_cpuinfo
    if args.force_hypervisor:
        env.hypervisor = True
    if args.sample_repeat:
        args.run_sample = True
    if args.handle_errata:
        args.ignore_errata = False
    if args.exclusive and args.pinned:
        sys.exit("--exclusive and --pinned cannot be combined")

def handle_parallel(args, env):
    if args.parallel:
        if not args.import_:
            sys.exit("--parallel requires --import")
        if args.import_.endswith(".xz") or args.import_.endswith(".gz"):
            sys.exit("Uncompress input file first") # XXX
        if args.perf_summary:
            sys.exit("--parallel does not support --perf-summary") # XXX
        if args.subset:
            # XXX support sample
            sys.exit("--parallel does not support --subset")
        if args.json and multi_output() and not args.split_output:
            sys.exit("--parallel does not support multi-output --json without --split-output")
        if args.graph:
            sys.exit("--parallel does not support --graph") # XXX
        if args.pjobs == 0:
            import multiprocessing
            args.pjobs = multiprocessing.cpu_count()
        sys.exit(run_parallel(args, env))

def handle_rest(args, rest):
    if rest[:1] == ["--"]:
        rest = rest[1:]
    if args.cpu:
        rest = ["--cpu", args.cpu] + rest
    if args.pid:
        rest = ["--pid", args.pid] + rest
    if args.csv and len(args.csv) != 1:
        sys.exit("--csv/-x argument can be only a single character")

    if args.xlsx:
        init_xlsx(args)
    if args.set_xlsx:
        set_xlsx(args)
    return rest

def update_args2(args):
    if args.perf_summary:
        try:
            args.perf_summary = flex_open_w(args.perf_summary)
        except IOError as e:
            sys.exit("Cannot open perf summary file %s: %s" % (args.perf_summary, e))
        # XXX force no_uncore because the resulting file cannot be imported otherwise?

    if args.all:
        args.tsx = True
        args.power = True
        args.sw = True
        args.metrics = True
        args.frequency = True
        args.level = 6

    if args.only_bottleneck:
        args.quiet = True
        args.no_version = True

def handle_graph(args):
    graphp = None
    if args.graph:
        if not args.interval:
            args.interval = 100
        extra = ""
        if args.title:
            title = args.title
        else:
            title = "cpu %s" % (args.graph_cpu if args.graph_cpu else 0)
        extra += '--title "' + title + '" '
        if args.split_output:
            sys.exit("--split-output not allowed with --graph")
        if args.output:
            extra += '--output "' + args.output + '" '
        if args.graph_cpu:
            extra += "--cpu " + args.graph_cpu + " "
        args.csv = ','
        cmd = "%s %s/tl-barplot.py %s /dev/stdin" % (sys.executable, exe_dir(), extra)
        if not args.quiet:
            print(cmd)
        graphp = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, **popentext) # type: ignore
        args.output = graphp.stdin
    return graphp

def init_ring_filter(args):
    ring_filter = ""
    if args.kernel and not args.user:
        ring_filter = 'k'
    if args.user and not args.kernel:
        ring_filter = 'u'
    return ring_filter

MAX_ERROR = 0.05

def check_ratio(l):
    if args.verbose:
        return True
    return 0 - MAX_ERROR < l < 1 + MAX_ERROR

def update_args_cpu(args, pversion):
    if args.level < 0:
        if args.bottlenecks:
            args.level = 4
        else:
            args.level = 2 if any([x >= 8 for x in cpu.counters.values()]) else 1
    if args.show_cpu:
        print("%s %s %s" % (cpu.true_name, cpu.pmu_name, cpu.name))
        sys.exit(0)
    desired_cpu = args.force_cpu if args.force_cpu else cpu.model # type: ignore
    if desired_cpu in eventlist_alias:
        r = eventlist_alias[desired_cpu] # type: ignore
        if not os.getenv("EVENTMAP"):
            os.environ["EVENTMAP"] = r
        if not os.getenv("UNCORE"):
            os.environ["UNCORE"] = r

    if cpu.pmu_name and cpu.pmu_name.startswith("generic") and not args.quiet:
        print("warning: kernel is in architectural mode and might mismeasure events", file=sys.stderr)
        print("Consider a kernel update. See https://github.com/andikleen/pmu-tools/wiki/toplev-kernel-support", file=sys.stderr)
        if cpu.cpu in hybrid_cpus:
            sys.exit("Hybrid %s not supported in architectural mode" % cpu.cpu)

    if args.xlsx and not forced_per_socket and cpu.sockets == 1:
        args.per_socket = False
    if args.xlsx and not forced_per_core and cpu.threads == 1:
        args.per_core = False

    if cpu.hypervisor:
        feat.max_precise = 0
        feat.has_max_precise = True

    if not pversion.has_uncore_expansion:
        # XXX reenable power
        args.no_uncore = True

    if cpu.hypervisor or args.no_uncore:
        feat.supports_power = False

def print_perf(r):
    if not (args.perf or args.print):
        return
    l = ["'" + x + "'" if x.find("{") >= 0 else x for x in r]
    l = [x.replace(";", "\\;") for x in l]
    i = l.index('--log-fd')
    del l[i:i+2]
    s = " ".join(l)
    print(s)
    sys.stdout.flush()

def gen_script(r):
    print("#!/bin/sh")
    print("# Generated from 'toplev " + " ".join(sys.argv) + " for CPU " + cpu.cpu)
    print("# Show output with toplev.py " +
          " ".join([x for x in sys.argv if x != "--gen-script"]) +
          " --import toplev_perf%s --force-cpuinfo toplev_cpuinfo --force-topology toplev_topology --force-cpu " % (
                ".data" if args.script_record else ".csv") + cpu.cpu)
    print("# print until Ctrl-C or run with command on command line (e.g. -a -I 1000 sleep 10)")
    print("# override output file names with OUT=... script (default toplev_...)")
    if not args.script_record:
        print("# enable compression with POSTFIX=.xz script")
    print("OUT=${OUT:-toplev}")
    print("PERF=${PERF:-perf}")
    print("find /sys/bus/event_source/devices/ > ${OUT}_topology")
    print("cat /proc/cpuinfo > ${OUT}_cpuinfo")
    r[0] = "$PERF"
    i = r.index('--log-fd')
    r[i] = "-o"
    if args.script_record:
        r[i + 1] = "${OUT}_perf.data"
        i = r.index("stat")
        r[i] = "stat record --quiet"
    else:
        r[i + 1] = "${OUT}_perf.csv${POSTFIX}"
    i = r.index('-x;')
    if args.script_record:
        del r[i]
    else:
        r[i] = '-x\\;'
    i = r.index('-e')
    r[i+1] = "'" + r[i+1] + "'"
    print(" ".join(r + ['"$@"']))

class PerfRun(object):
    """Control a perf subprocess."""
    def __init__(self):
        self.skip_to_next_ts = False
        self.end_seek_offset = None
        self.sample_prob = None
        self.skip_line = False
        self.perf = None
        self.offset = None

    def handle_inputsubset(self, f, iss):
        m = re.match(r'(\d+)-?(\d+)?$', iss)
        if m:
            off = int(m.group(1))
            f.seek(off)
            if m.group(2):
                self.end_seek_offset = int(m.group(2)) + 1
            if off:
                self.skip_to_next_ts = True
                self.skip_line = True
            return
        m = re.match(r'(\d+)/([0-9.]+)%(-)?$', iss)
        if m:
            f.seek(0, 2)
            size = f.tell()
            chunk = int(size * (float(m.group(2)) / 100.))
            nth = int(m.group(1))
            if (nth+1)*chunk > size:
                sys.exit("--subset %s out of range" % iss)
            f.seek(chunk * nth)
            if m.group(3) is None:
                self.end_seek_offset = chunk * (1+nth) + 1
            if chunk * nth != 0:
                self.skip_to_next_ts = True
                self.skip_line = True
            return
        m = re.match('sample:([0-9.]+)%?$', iss)
        if m:
            self.sample_prob = float(m.group(1)) / 100.
            self.random = random.Random()
            s = os.getenv("TLSEED")
            if s:
                self.random.seed(int(s))
            self.sampling = False
            return
        sys.exit("Unparseable --subset %s" % iss)

    def skip_input(self):
        if self.skip_to_next_ts:
            return True
        if self.sample_prob:
            return not self.sampling
        return False

    # must be stored before reading the line
    def store_offset(self):
        if self.end_seek_offset:
            self.offset = self.inputf.tell() # type: ignore

    def skip_first_line(self):
        if self.skip_line:
            self.skip_line = False
            return True
        return False

    def next_timestamp(self):
        if self.end_seek_offset:
            if self.end_seek_offset <= self.offset:
                return True
        self.skip_to_next_ts = False
        if self.sample_prob:
            r = self.random.random()
            self.sampling = r < self.sample_prob
        return False

    def execute(self, r):
        if args.import_:
            print_perf(r)
            if args.script_record:
                self.perf = subprocess.Popen([feat.perf, "stat", "report", "-x;", "-i", args.import_], stderr=subprocess.PIPE, **popentext) # type: ignore
                return self.perf.stderr
            self.perf = None
            try:
                f = flex_open_r(args.import_)
            except IOError as e:
                sys.exit("Cannot open file %s: %s" % (args.import_, e))
            if args.subset:
                try:
                    self.handle_inputsubset(f, args.subset)
                except OSError:
                    sys.exit("--subset not supported on compressed or unseekable files.")
                except io.UnsupportedOperation:
                    sys.exit("--subset not supported on compressed or unseekable files.")
            self.inputf = f
            return f

        if args.gen_script:
            gen_script(r)
            sys.exit(0)

        outp, inp = pty.openpty()
        if 'set_inheritable' in os.__dict__:
            os.set_inheritable(inp, True)
        n = r.index("--log-fd")
        r[n + 1] = "%d" % (inp)
        print_perf(r)
        if args.print:
            sys.exit(0)
        self.perf = subprocess.Popen(r, close_fds=False) # type: ignore
        os.close(inp)
        return os.fdopen(outp, 'r')

    def wait(self):
        ret = 0
        if self.perf:
            ret = self.perf.wait()
            self.perf = None
        return ret

    def __del__(self):
        if self.perf:
            self.perf.kill()

def separator(x):
    if ":" in x:
        return ""
    if x.startswith("cpu"):
        return ""
    return ":"

def add_filter_event(e):
    if "/" in e and not e.startswith("cpu"):
        return e
    if e == "dummy" or e == "emulation-faults" or e == "duration_time":
        return e
    s = separator(e)
    if not e.endswith(s + args.ring_filter):
        return e + s + args.ring_filter
    return e

def add_filter(s):
    if args.ring_filter:
        s = list(map(add_filter_event, s))
    return s

def is_cpu_event(s):
    return re.match(r'cpu(_atom|_core)?/', s) is not None

def initialize_event(name, i, e):
    if "." in name or "_" in name and name not in non_json_events:
        eo = e.output(noname=not INAME, noexplode=True)
        ectx.emap.update_event(eo, e)
        ectx.emap.update_event(remove_qual(eo), e) # XXX
        if (e.counter not in ectx.standard_counters and not name.startswith("UNC_")):
            if e.counter.startswith("Fixed"):
                ectx.limited_counters[i] = int(e.counter.split()[2]) + FIXED_BASE
                ectx.fixed_events.add(i)
            elif is_number(e.counter) and int(e.counter) >= 32:
                ectx.limited_counters[i] = int(e.counter) - 32 + FIXED_BASE
                ectx.fixed_events.add(i)
            else:
                # for now use the first counter only to simplify
                # the assignment. This is sufficient for current
                # CPUs
                ectx.limited_counters[i] = int(e.counter.split(",")[0])
            ectx.limited_set.add(i)
        nameu = e.name.upper()
        if nameu in ectx.constraint_fixes:
            e.counter = ectx.constraint_fixes[nameu]
        for k, v in ectx.constraint_patterns:
            if nameu.startswith(k):
                e.counter = v
        if e.counter == ectx.limit4_counters or eo.endswith("/p"):
            ectx.limit4_events.add(i)
        if e.errata and e.errata != "0" and e.errata != "null":
            if e.errata not in ectx.errata_whitelist:
                ectx.errata_events[name] = e.errata
            else:
                ectx.errata_warn_events[name] = e.errata
        if ('pebs' in e.__dict__ and e.pebs == 2) or name.startswith("FRONTEND_"):
            ectx.require_pebs_events.add(name)
    else:
        non_json_events.add(i)
    valid_events.add_event(i)
    if INAME:
        valid_events.add_event(ocperf.gen_name(re.sub(r':.*','', name), False))  # XXX sup, handle :... uniquely
    if not is_cpu_event(i) and i not in ectx.fixed_events:
        if not i.startswith("uncore"):
            valid_events.add_event(i)
        if i.startswith("msr/"):
            ectx.sched_ignore_events.add(i)
        else:
            ectx.outgroup_events.add(add_filter_event(i))

def raw_event(i, name="", period=False, initialize=False):
    e = None
    orig_i = i
    if i == "cycles" and (cpu.cpu in hybrid_cpus or cached_exists("/sys/bus/event_source/devices/cpu_core")):
        i = "cpu_clk_unhalted.thread"
    if "." in i or "_" in i and i not in non_json_events:
        if not cpu.ht:
            i = i.replace(":percore", "")
        extramsg = [] # type: List[str]
        e = ectx.emap.getevent(i, nocheck=event_nocheck(), extramsg=extramsg)
        if e is None:
            if i not in ectx.notfound_cache:
                ectx.notfound_cache[i] = extramsg[0]
                if not args.quiet:
                    print("%s %s" % (i, extramsg[0]), file=sys.stderr)
            return "dummy"
        if has(e, 'perfqual') and not cached_exists("/sys/bus/event_source/devices/%s/format/%s"  % (ectx.emap.pmu, e.perfqual)):
            if not args.quiet:
                print("%s event not supported in hypervisor or architectural mode" % i, file=sys.stderr)
            return "dummy"

        if re.match("^[0-9]", name):
            name = "T" + name
        if args.filterquals:
            e.filter_qual()
        i = e.output(noname=not INAME, name=name, period=period, noexplode=True)
        if not ectx.force_metrics:
            m = re.search(r'(topdown-[a-z-]+)', i)
            if m and not cached_exists("/sys/bus/event_source/devices/%s/events/%s" % (ectx.emap.pmu, m.group(1))):
                if not args.quiet:
                    print("%s event not supported in sysfs" % m.group(1))
                i = "dummy"
    if initialize:
        initialize_event(orig_i, i, e)
    return i

# generate list of converted raw events from events string
def raw_events(evlist, initialize=False):
    return [raw_event(x, initialize=initialize) for x in evlist]

def mark_fixed(s):
    r = raw_event(s)
    if r in ectx.fixed_events:
        return "%s[F]" % s
    return s

def pwrap(s, linelen=70, indent=""):
    print(indent +
          ("\n" + indent).join(
              textwrap.wrap(s, linelen, break_long_words=False)),
          file=sys.stderr)

def pwrap_not_quiet(s, linelen=70, indent=""):
    if not args.quiet:
        pwrap(s, linelen, indent)

def perf_args(evstr, rest):
    add = []
    if args.interval:
        add += ['-I', str(args.interval)]
    return [feat.perf, "stat", "-x;", "--log-fd", "X"] + add + ["-e", evstr] + rest

def setup_perf(evstr, rest):
    prun = PerfRun()
    inf = prun.execute(perf_args(evstr, rest))
    return inf, prun

class Stat(object):
    def __init__(self):
        self.total = 0
        self.errors = Counter() # type: typing.Counter[str]

def print_not(a, count, msg, j):
    print(("%s %s %s %.2f%% in %d measurements"
                % (j, j, msg, # XXX rmap again with ectx
                    100.0 * (float(count) / float(a.total)),
                    a.total)),
                file=sys.stderr)

# XXX need to get real ratios from perf
def print_account(ad):
    total = Counter() # type: typing.Counter[str]
    for j in ad:
        a = ad[j]
        for e in a.errors:
            if args.stats:
                print_not(a, a.errors[e], e, j)
            total[e] += 1
    if sum(total.values()) > 0 and not args.quiet:
        print(", ".join(["%d events %s" % (num, e) for e, num in total.items()]),
                file=sys.stderr)

class ValidEvents(object):
    def update(self):
        self.string = "|".join(self.valid_events)

    def __init__(self):
        self.valid_events = [r"cpu(_core|_atom)?/.*?/", "uncore.*?/.*?/", "ref-cycles", "power.*", "tool/.*",
                             r"msr.*", "emulation-faults",
                             r"r[0-9a-fA-F]+", "cycles", "instructions", "dummy",
                             "slots", r"topdown-(fe-bound|be-bound|retiring|bad-spec|heavy-ops|br-mispredict|fetch-lat|mem-bound)"]
        self.update()

    def add_event(self, ev):
        if re.match(self.string, ev):
            return
        # add first to overwrite more generic regexprs list r...
        self.valid_events.insert(0, ev)
        self.update()

valid_events = ValidEvents()

def is_event(l, n):
    if len(l) <= n:
        return False
    # use static string to make regexpr caching work
    return re.match(valid_events.string, l[n], re.I)

def is_number(n):
    return re.match(r'\d+$', n) is not None

def set_interval(env, d, interval):
    env['interval-ns'] = d * 1e9
    env['interval-ms'] = d * 1e3
    env['interval-s'] = d
    env['interval'] = interval

def key_to_coreid(k):
    try:
        x = cpu.cputocore[int(k)]
        return x[0] * 1000 + x[1]
    except ValueError:
        return 0

def key_to_socketid(k):
    try:
        return cpu.cputocore[int(k)][0]
    except ValueError:
        return 0

def core_fmt(core):
    if cpu.sockets > 1:
        return "S%d-C%d" % (core / 1000, core % 1000,)
    return "C%d" % (core % 1000,)

def socket_fmt(j):
    return "S%d" % cpu.cputocore[j][0]

def thread_fmt(j):
    return core_fmt(key_to_coreid(j)) + ("-T%d" % cpu.cputothread[int(j)])

def display_core(cpunum, ignore_thread=False):
    for match in args.core.split(","):
        m = re.match(r'(?P<socket>S\d+)?-?(?P<core>C\d+)?-?(?P<thread>T\d+)?', match, re.I)
        if not m or not any((m.group('core'), m.group('socket'),)):
            sys.exit("Bad core match %s" % match)

        def matching(name, mapping):
            return mapping[cpunum] == int(m.group(name)[1:]) # type: ignore
        if m.group('socket') and not matching('socket', cpu.cputosocket):
            continue
        if m.group('core') and cpu.cputocore[cpunum][1] != int(m.group('core')[1:]):
            continue
        if not ignore_thread and m.group('thread') and not matching('thread', cpu.cputothread):
            continue
        return True
    return False

OUTPUT_CORE_THREAD = 0
OUTPUT_CORE = 1
OUTPUT_THREAD = 2
OUTPUT_SOCKET = 3
OUTPUT_GLOBAL = 4

def display_keys(runner, keys, mode, post=""):
    allowed_threads = runner.cpu_list
    if mode == OUTPUT_GLOBAL:
        return ("",)
    if len(keys) > 1 and smt_mode:
        if mode == OUTPUT_SOCKET:
            all_cpus = dedup(map(socket_fmt, allowed_threads))
        else:
            cores = [key_to_coreid(x) for x in keys if int(x) in allowed_threads]
            if mode != OUTPUT_CORE:
                threads = [thread_fmt(x) + post for x in allowed_threads]
            else:
                threads = []
            all_cpus = [core_fmt(x)+post for x in cores] + threads
    else:
        all_cpus = [x + post for x in keys]
    if any(map(package_node, runner.olist)):
        all_cpus += ["S%d" % x for x in range(cpu.sockets)]
    return all_cpus

def verify_rev(rev, cpus):
    for k in cpus:
        for ind, o in enumerate(rev[k]):
            assert o == rev[cpus[0]][ind]
        assert len(rev[k]) == len(rev[cpus[0]])

def is_cycles(ev):
    return re.match(r'cycles|slots|r20003c|cpu(_atom|_core)?/slots|cpu(_atom|_core)?/event=0x(3c|a4),umask=0x(0|1)', ev) is not None

def find_cycles(rev):
    for l in rev.values():
        for idle_ev in l:
            if is_cycles(idle_ev):
                return idle_ev
    return ""

def find_idle_keys(res, rev, idle_thresh):
    if sum([len(res[k]) for k in res.keys()]) == 0:
        return set()
    if len(res.keys()) == 1:
        return set()
    idle_ev = find_cycles(rev)
    if idle_ev == "":
        warn_once("no idle detection because no cycle event found")
        return set()
    cycles = { k: max([0] + [val for val, ev in zip(res[k], rev[k]) if ev == idle_ev])
               for k in res.keys() }
    if sum(cycles.values()) == 0 and not args.quiet:
        print_once("no idle detection because cycles counts are zero")
        return set()
    max_cycles = max(cycles.values())
    return {k for k in cycles.keys() if cycles[k] < max_cycles * idle_thresh}

def is_idle(cpus, idle_keys):
    return all([("%d" % c) in idle_keys for c in cpus])

def idle_core(core, idle_keys):
    return is_idle(cpu.coreids[core], idle_keys)

def idle_socket(socket, idle_keys):
    return is_idle(cpu.sockettocpus[socket], idle_keys)

# from https://stackoverflow.com/questions/4836710/does-python-have-a-built-in-function-for-string-natural-sort
def num_key(s):
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', s)]

def invalid_res(res, key, nothing):
    if len(res) == 0:
        if isinstance(key, list):
            for j in key:
                nothing.add(j)
        else:
            nothing.add(key)
        return True
    return False

def runner_name(r):
    if r.pmu is None:
        return "cpu"
    return r.pmu.replace("cpu_", "")

default_compute_iter = 3
# override how often to recompute to converge all the thresholds
COMPUTE_ITER = None

def print_keys(runner, res, rev, valstats, out, interval, env, mode, runner_list):
    nothing = set() # type: Set[str]
    allowed_threads = runner.cpu_list
    def filtered(j):
        return j != "" and is_number(j) and int(j) not in allowed_threads
    core_node = lambda obj: safe_ref(obj, 'domain') in runner.ectx.core_domains
    thread_node = lambda obj: not (core_node(obj) or package_node(obj))

    idle_keys = find_idle_keys(res, rev, runner.idle_threshold)
    idle_mark_keys = find_idle_keys(res, rev, IDLE_MARKER_THRESHOLD)
    printer = runner.printer
    hidden_keys = set()
    stat = runner.stat
    keys = sorted(res.keys(), key=num_key)
    post = ""
    if runner.pmu != "cpu":
        if len(res.keys()) > 1:
            post += "-"
        post += runner_name(runner)
    out.set_cpus(display_keys(runner, keys, mode, post))
    runner.printer.numprint = 0
    if smt_mode:
        printed_cores = set()
        printed_sockets = set()
        for j in list(keys):
            if j != "" and int(j) not in cpu.cputocore:
                warn_once("Warning: input cpu %s not in cpuinfo." % j)
                del res[j]
        keys = sorted(res.keys(), key=num_key)
        for j in keys:
            if filtered(j):
                continue
            sid = key_to_socketid(j)
            core = key_to_coreid(j)
            if mode == OUTPUT_CORE and core in printed_cores:
                continue
            if mode == OUTPUT_SOCKET and sid in printed_sockets:
                continue
            if j in idle_keys:
                hidden_keys.add(j)
                continue

            runner.reset_thresh()

            if mode == OUTPUT_GLOBAL:
                cpus = keys
            elif mode == OUTPUT_SOCKET:
                cpus = [x for x in keys if key_to_socketid(x) == sid and not filtered(x)]
            else:
                cpus = [x for x in keys if key_to_coreid(x) == core and not filtered(x)]
            combined_res = list(zip(*[res[x] for x in cpus]))
            combined_st = [combine_valstat(z)
                  for z in zip(*[valstats[x] for x in cpus])]
            env['num_merged'] = len(cpus)

            if mode in (OUTPUT_CORE,OUTPUT_SOCKET,OUTPUT_GLOBAL):
                merged_res = combined_res
                merged_st = combined_st
            else:
                merged_res = res[j]
                merged_st = valstats[j]

            if invalid_res(merged_res, cpus, nothing):
                continue

            # may need to repeat to get stable threshold values
            # in case of mutual dependencies between SMT and non SMT
            # but don't loop forever (?)
            used_stat = stat
            onemore = False
            iterations = COMPUTE_ITER if COMPUTE_ITER else default_compute_iter
            for _ in range(iterations):
                env['num_merged'] = 1
                changed = runner.compute(merged_res, rev[j], merged_st, env, thread_node, used_stat, runner_list)
                verify_rev(rev, cpus)
                env['num_merged'] = len(cpus)
                changed += runner.compute(combined_res, rev[cpus[0]], combined_st, env, core_node, used_stat, runner_list)
                if changed == 0 and COMPUTE_ITER is None:
                    # do always one more so that any thresholds depending on a later node are caught
                    if not onemore:
                        onemore = True
                        continue
                    break
                used_stat = None

            # find bottleneck
            bn = find_bn(runner.olist, not_package_node)

            if mode == OUTPUT_GLOBAL:
                printer.print_res(runner.olist, out, interval, "", not_package_node, bn)
                break
            if mode == OUTPUT_SOCKET:
                printer.print_res(runner.olist, out, interval, socket_fmt(int(j)),
                                  not_package_node, bn, idle_socket(sid, idle_mark_keys))
                printed_sockets.add(sid)
                continue
            if mode == OUTPUT_THREAD:
                runner.compute(res[j], rev[j], valstats[j], env, package_node, stat, runner_list)
                printer.print_res(runner.olist, out, interval, thread_fmt(int(j))+post, any_node,
                                  bn, j in idle_mark_keys)
                continue

            # per core or mixed core/thread mode

            # print the SMT aware nodes
            if core not in printed_cores:
                printer.print_res(runner.olist, out, interval, core_fmt(core)+post, core_node, bn,
                        idle_core(core, idle_mark_keys))
                printed_cores.add(core)

            # print the non SMT nodes
            if mode == OUTPUT_CORE:
                fmt = core_fmt(core)
                idle = idle_core(core, idle_mark_keys)
            else:
                fmt = thread_fmt(int(j))
                idle = j in idle_mark_keys
            printer.print_res(runner.olist, out, interval, fmt+post, thread_node, bn, idle)
    elif mode != OUTPUT_GLOBAL:
        env['num_merged'] = 1
        for j in keys:
            if filtered(j):
                continue
            if j in idle_keys:
                hidden_keys.add(j)
                continue
            if invalid_res(res[j], j, nothing):
                continue
            runner.reset_thresh()
            runner.compute(res[j], rev[j], valstats[j], env, not_package_node, stat, runner_list)
            bn = find_bn(runner.olist, not_package_node)
            printer.print_res(runner.olist, out, interval, j+post, not_package_node, bn, j in idle_mark_keys)
    if mode == OUTPUT_GLOBAL:
        env['num_merged'] = 1
        cpus = [x for x in keys if not filtered(x)]
        if cpus:
            combined_res = [sum([res[j][i] for j in cpus])
                            for i in range(len(res[cpus[0]]))]
            combined_st = [combine_valstat([valstats[j][i] for j in cpus])
                           for i in range(len(valstats[cpus[0]]))]
            if smt_mode:
                nodeselect = package_node
            else:
                nodeselect = any_node
            if not invalid_res(combined_res, cpus, nothing):
                runner.reset_thresh()
                runner.compute(combined_res, rev[cpus[0]] if len(cpus) > 0 else [],
                               combined_st, env, nodeselect, stat, runner_list)
                bn = find_bn(runner.olist, lambda x: True)
                printer.print_res(runner.olist, out, interval, "", nodeselect, bn, False)
    elif mode != OUTPUT_THREAD:
        packages = set()
        for j in keys:
            if j == "":
                continue
            if is_number(j):
                if filtered(j):
                    continue
                p_id = cpu.cputosocket[int(j)]
                if p_id in packages:
                    continue
                packages.add(p_id)
                jname = "S%d" % p_id
            else:
                jname = j
            if j in idle_keys:
                hidden_keys.add(j)
                continue
            runner.reset_thresh()
            if invalid_res(res[j], j, nothing):
                continue
            runner.compute(res[j], rev[j], valstats[j], env, package_node, stat, runner_list)
            printer.print_res(runner.olist, out, interval, jname, package_node, None, j in idle_mark_keys)
    # no bottlenecks from package nodes for now
    out.flush()
    if not FUZZYINPUT:
        stat.referenced_check(res, runner.sched.evnum)
    stat.compute_errors()
    runner.idle_keys |= hidden_keys
    if nothing and not args.quiet:
        print("%s: Nothing measured%s" % (runner.pmu, " for " if len(nothing) > 0 and "" not in nothing else ""), " ".join(sorted(nothing)), file=sys.stderr)
    if runner.printer.numprint == 0 and not args.quiet and runner.olist:
        print("No node %scrossed threshold" % (
                "for %s " % runner_name(runner) if runner.pmu != "cpu" else ""), file=sys.stderr)

def print_and_split_keys(runner, res, rev, valstats, out, interval, env, rlist):
    if multi_output():
        if args.per_thread:
            out.remark("Per thread")
            out.reset("thread")
            print_keys(runner, res, rev, valstats, out, interval, env, OUTPUT_THREAD, rlist)
        if args.per_core:
            out.remark("Per core")
            out.reset("core")
            print_keys(runner, res, rev, valstats, out, interval, env, OUTPUT_CORE, rlist)
        if args.per_socket:
            out.remark("Per socket")
            out.reset("socket")
            print_keys(runner, res, rev, valstats, out, interval, env, OUTPUT_SOCKET, rlist)
        if args.global_:
            out.remark("Global")
            out.reset("global")
            print_keys(runner, res, rev, valstats, out, interval, env, OUTPUT_GLOBAL, rlist)
    else:
        if args.split_output:
            sys.exit("--split-output needs --per-thread / --global / --per-socket / --per-core")
        mode = OUTPUT_CORE_THREAD
        if args.per_thread:
            mode = OUTPUT_THREAD
        elif args.per_core:
            mode = OUTPUT_CORE
        elif args.per_socket:
            mode = OUTPUT_SOCKET
        elif args.global_:
            mode = OUTPUT_GLOBAL
        print_keys(runner, res, rev, valstats, out, interval, env, mode, rlist)

def print_check_keys(runner, res, rev, valstats, out, interval, env, rlist):
    if res and all([sum(res[k]) == 0.0 and len(res[k]) > 0 for k in res.keys()]) and cpu.cpu == cpu.realcpu:
        if args.subset:
            return
        if runner.pmu == "cpu":
            sys.exit("All measured values 0. perf broken?")
        else:
            if not args.quiet:
                print("Measured values for %s all 0" % runner_name(runner), file=sys.stderr)
            return
    if args.interval and interval is None:
        interval = float('nan')
    if not args.no_output:
        print_and_split_keys(runner, res, rev, valstats, out, interval, env, rlist)

def print_summary(summary, out, runner_list, full_system):
    if args.perf_summary:
        p = summary.summary_perf
        for sv in zip_longest(*p.values()):
            for ind, title in enumerate(p.keys()):
                r = sv[ind]
                l = []
                if args.interval:
                    l.append("\tSUMMARY")
                if full_system:
                    l.append(("CPU" + title) if re.match(r'\d+$', title) else title)
                if output_numcpus:
                    l.append("0") # XXX
                if r is None:
                    continue
                if is_number(title):
                    cpunum = int(title)
                    if (r[2].startswith("uncore") or r[2].startswith("power")) and (
                            cpunum != cpu.sockettocpus[cpu.cputosocket[cpunum]][0]):
                        continue
                    if r[2].startswith("duration_time") and cpunum != 0 and not args.cpu and not args.core:
                        continue
                args.perf_summary.write(";".join(l + ["%f" % r[0], r[1],
                                                      r[2], "%f" % r[3],
                                                      "%.2f" % r[4], "", ""]) + "\n")

    if not args.summary:
        return
    for runner, res, rev in runner_split(runner_list, summary.res, summary.rev):
        print_and_split_keys(runner, res, rev,
                         summary.valstats, out,
                             float('nan'), summary.env, runner_list)

class SaveContext(object):
    """Save (some) environment context, in this case stdin seek offset to make < file work
       when we reexecute the workload multiple times."""
    def __init__(self):
        try:
            self.startoffset = sys.stdin.tell() # type: int | None
        except OSError:
            self.startoffset = None
        except IOError:
            self.startoffset = None

    def restore(self):
        if self.startoffset is not None:
            sys.stdin.seek(self.startoffset)

def execute_no_multiplex(runner_list, out, rest, summary):
    results = [] # type: List[Any]
    groups = []
    num_outg = 0
    for runner in runner_list:
        groups += [g.evnum for g in runner.sched.evgroups]
        num_outg += sum([g.outgroup for g in runner.sched.evgroups])
    num_runs = len(groups) - num_outg
    outg = []
    n = 0
    ctx = SaveContext()
    resoff = Counter() # type: typing.Counter[str]
    RES, REV, INTERVAL, VALSTATS, ENV = range(5)
    ret = 0
    # runs could be further reduced by tweaking
    # the scheduler to avoid any duplicated events
    for runner in runner_list:
        groups = [g.evnum for g in runner.sched.evgroups]
        for g, gg in zip(groups, runner.sched.evgroups):
            if gg.outgroup:
                outg.append(g)
                continue
            print("RUN #%d of %d%s: %s" % (n + 1, num_runs,
                " for %s" % runner_name(runner) if len(runner_list) > 1 else "",
                " ".join([quote(o.name) for o in gg.objl])))
            # becomes results for first iteration
            lresults = results if n == 0 else []
            res = None
            events = outg + [g]
            runner.set_ectx()
            evstr = group_join(events)
            flat_events = flatten(events)
            flat_rmap = [event_rmap(e, runner_list) for e in flat_events]
            runner.clear_ectx()
            for nret, res, rev, interval, valstats, env in do_execute(
                    [runner],
                    summary, evstr, flat_rmap,
                    out, rest, resoff, flat_events):
                ret = max(ret, nret)
                lresults.append([res, rev, interval, valstats, env])
            if res:
                for t in res.keys():
                    resoff[t] += len(res[t])
            if n > 0:
                if len(lresults) != len(results):
                    if not args.quiet:
                        print("Original run had %d intervals, this run has %d. "
                              "Workload run time not stable?" %
                            (len(lresults), len(results)), file=sys.stderr)
                    if len(lresults) > len(results):
                        # throw away excessive intervals
                        lresults = lresults[:len(results)]
                    else:
                        # fill the missing intervals with dummy data
                        v = lresults[0]
                        for ind, _ in enumerate(results):
                            if ind >= len(lresults):
                                lresults.append([dummy_dict(v[RES]),
                                                 v[REV],
                                                 v[INTERVAL],
                                                 dummy_dict(v[RES], ValStat(0,0)),
                                                 v[ENV]])
                    assert len(lresults) == len(results)
                i = 0
                for r, lr in zip(results, lresults):
                    for j in (RES, REV, VALSTATS):
                        append_dict(r[j], lr[j])
                    i += 1
            ctx.restore()
            outg = []
            n += 1
    assert num_runs == n
    for res, rev, interval, valstats, env in results:
        if summary:
            summary.add(res, rev, valstats, env)
        for runner, res, rev in runner_split(runner_list, res, rev):
            print_check_keys(runner, res, rev, valstats, out, interval, env, runner_list)
    return ret

def runner_split(runner_list, res, rev):
    for r in runner_list:
        if len(res.keys()) == 1 and "" in res:
            off = r.sched.offset
            end = off + len(r.sched.evnum)
            yield r, { "": res[""][off:end]}, { "": rev[""][off:end] }
        elif r.cpu_list:
            d = defaultdict(list) # type: DefaultDict[str,list]
            d.update({ "%d" % k: res["%d" % k] for k in r.cpu_list })
            yield r, d, rev
        else:
            yield r, res, rev

def execute(runner_list, out, rest, summary):
    evstr, flat_events, flat_rmap = "", [], []
    for runner in runner_list:
        new_events = [x.evnum for x in runner.sched.evgroups if len(x.evnum) > 0]
        if len(new_events) == 0:
            continue
        runner.set_ectx()
        if evstr:
            evstr += ","
        evstr += group_join(new_events)
        new_flat_events = flatten(new_events)
        flat_events += new_flat_events
        flat_rmap += [event_rmap(e, runner_list) for e in new_flat_events]
        runner.clear_ectx()
    ctx = SaveContext()
    for ret, res, rev, interval, valstats, env in do_execute(
            runner_list, summary,
            evstr, flat_rmap, out, rest, Counter(), None):
        if summary:
            summary.add(res, rev, valstats, env)
        for runner, res, rev in runner_split(runner_list, res, rev):
            print_check_keys(runner, res, rev, valstats, out, interval, env, runner_list)
    ctx.restore()
    return ret

def find_group(num, runner_list):
    offset = 0
    for runner in runner_list:
        if num - offset < len(runner.sched.evnum):
            break
        offset += len(runner.sched.evnum)
    num -= offset
    groups = runner.sched.evgroups
    g = groups[bisect.bisect_right(groups, GroupCmp(num)) - 1]
    if g.base <= num < g.base + len(g.evnum):
        return g
    warn("group for event %d not found" % num)
    return None

def dump_raw(valcsv, interval, title, event, ename, val, index, stddev, multiplex, runner_list):
    if index < 0:
        return
    g = find_group(index, runner_list)
    if g is None:
        return
    nodes = " ".join(sorted([o.name.replace(" ", "_") for o in g.objl if event in o.evnum]))
    if args.raw:
        print("raw", title, "event", event, "val", val, "ename", ename, "index",
                index, "group", g.num, "nodes", nodes)
    if args.valcsv:
        valcsv.writerow((interval, title, g.num, ename, val, event, index,
                                stddev, multiplex, nodes))
def group_join(events):
    e = ""
    last = None
    sep = ""
    for j in events:
        e += sep
        # add dummy event to separate identical events to avoid merging
        # in perf stat
        if last == j[0] and sep:
            e += "emulation-faults,"
        e += event_group(j)
        sep = ","
        last = j[-1]
    return e

def update_perf_summary(summary, off, title, val, event, unit, multiplex):
    if title not in summary.summary_perf:
        summary.summary_perf[title] = []
    if len(summary.summary_perf[title]) <= off:
        summary.summary_perf[title].append([val, unit, event, 0, multiplex])
    else:
        r = summary.summary_perf[title][off]
        r[0] += val
        assert r[1] == unit
        assert r[2] == event or event == "dummy"
        r[3] = min(r[3], multiplex)

def find_runner(rlist, off, title, event):
    if len(rlist) == 1 and rlist[0].pmu == "cpu":
        return rlist[0], off
    for r in rlist:
        if title == "":
            if r.sched.offset <= off < r.sched.offset+len(r.sched.evnum):
                return r, off - r.sched.offset
        elif r.cpu_list:
            # in the per cpu case each hybrid cpu has its own line, so no offsets for the runners
            # but need to handle leaks below
            if int(title) in r.cpu_list:
                # For hybrid, non cpu events like msr/tsc/ get expanded over all CPUs.
                # and leak into the other runner who doesn't know anything about them.
                # XXX check does not handle dups
                if not event.startswith("cpu") and (off >= len(r.sched.evnum) or event != r.sched.evnum[off]):
                    return None, 0
                return r, off
        else:
            return r, off
    return None, 0

def perf_name(e):
    m = re.search(r'name=([^,/]+)', e)
    if m:
        return m.group(1)
    return None

FINE = 0
SKIP = 1
FUZZY = 2

def check_event(rlist, event, off, title, prev_interval, l, revnum, linenum, last_linenum):
    r, off = find_runner(rlist, off, title, event)
    if r is None:
        return r, FINE, event
    # likely event expanded over all CPUs
    if event.startswith("cpu") and not event.startswith(r.pmu):
        if args.debug:
            print("event wrong pmu", event, title, r.pmu)
        return None, FINE, event
    # cannot check because it's an event that needs to be expanded first
    if not event.startswith("cpu") and is_number(title) and int(title) not in r.cpu_list:
        return r, FINE, event
    if revnum is None:
        revnum = r.sched.evnum
    if event.startswith("uncore"):
        event = re.sub(r'_[0-9]+', '', event)
        event = re.sub(r'/uncore_[a-z]+,', '/', event)
    try:
        expected_ev = remove_qual(revnum[off])
    except IndexError:
        if FUZZYINPUT:
            expected_ev = event
        else:
            sys.exit("Out of range event %s offset %d (len %d). %s" % (event, off, len(revnum),
                     "Mismatch in toplev arguments from recording?" if args.import_ else ""))
    if event != expected_ev:
        en = perf_name(expected_ev)
        if en == event:
            return r, FINE, expected_ev
        # work around perf bug that incorrectly expands uncore events in some versions
        if off > 0 and event == remove_qual(revnum[off - 1]):
            return None, FINE, expected_ev
        if FUZZYINPUT:
            return r, FUZZY, expected_ev
        # some perf version don't output <not counted/supported due to dd15480a3d67
        # if the event is expected within a small window assume it's not counted
        # and reuse the value for the next
        near = revnum[off:off+PERF_SKIP_WINDOW]
        for j in near:
            if event == remove_qual(j):
                if args.debug:
                    print("skipping, expected", expected_ev, "got", event,
                          "off", off, "title", title,
                          "context", revnum[off:off+PERF_SKIP_WINDOW])
                if linenum == last_linenum[0]: # avoid endless loop
                    return r, FINE, expected_ev
                last_linenum[0] = linenum
                return r, SKIP, expected_ev
        print("Event in input does not match schedule (%s vs expected %s [pmu:%s/ind:%d/tit:%s/int:%f+%d])." % (
                event, expected_ev, r.pmu, off, title, prev_interval, linenum),
                file=sys.stderr)
        sys.stdout.write(l)
        if args.import_:
            sys.exit("Different arguments than original toplev?")
        sys.exit("Input corruption")
    return r, FINE, event

def update_missing(res, rev, valstats, fallback):
    for k in rev.keys():
        for ind, event in enumerate(rev[k]):
            if not isnan(res[k][ind]):
                continue
            key = (k, event)
            if key in fallback:
                if args.debug:
                    print("updating fuzzy event", k, event, fallback[key][0])
                res[k][ind] = fallback[key][0]
                valstats[k][ind] = fallback[key][1]
                continue
            pn = perf_name(event)
            if pn:
                key = (k, pn)
                if key in fallback:
                    res[k][ind] = fallback[key][0]
                    valstats[k][ind] = fallback[key][1]
                    if args.debug:
                        print("updating", k, rev[k][ind])
                    continue
            if not args.quiet:
                print("Cannot find value for", k, rev[k][ind], pn, "in input")
            res[k][ind] = float("nan")
        assert not any([x is None for x in res[k]])

def do_execute(rlist, summary, evstr, flat_rmap, out, rest, resoff, revnum):
    res = defaultdict(list) # type: DefaultDict[str,List[float]]
    rev = defaultdict(list) # type: DefaultDict[str, List[str]]
    valstats = defaultdict(list) # type: DefaultDict[str,List[ValStat]]
    env = {} # type: Dict[str,str]
    account = defaultdict(Stat) # type: DefaultDict[str,Stat]
    inf, prun = setup_perf(evstr, rest)
    prev_interval = 0.0
    interval = None
    interval_dur = 0.0
    linenum = 1
    skip = False
    last_linenum = [0]
    fallback = {} # type: Dict[Tuple[str,str], Tuple[float, ValStat]]
    need_fallback = False
    if not args.import_ and not args.interval:
        start = time.time()
    while True:
        if skip:
            # when skipping reuse line from last iteration
            pass
        else:
            try:
                prun.store_offset()
                l = inf.readline()
                origl = l
                if not l:
                    break

                # some perf versions break CSV output lines incorrectly for power events
                if l.endswith("Joules"):
                    l2 = inf.readline()
                    l = l + l2.strip()
                if l.startswith("#") or l.strip() == "":
                    linenum += 1
                    skip = False
                    continue
            except OSError:
                # handle pty EIO
                break
            except IOError:
                break
            except KeyboardInterrupt:
                continue
        if re.match(r'^(Timestamp|Value|Location)', l):
            # header generated by toplev in import mode. ignore.
            linenum += 1
            skip = False
            continue
        if prun.skip_first_line():
            skip = False
            continue
        origl = l
        if args.interval:
            m = re.match(r"\s*([0-9.]{9,}|SUMMARY);(.*)", l)
            if m:
                interval = float(m.group(1)) if m.group(1) != "SUMMARY" else 0.0
                l = m.group(2)
                if interval != prev_interval:
                    linenum = 1
                    # skip the first because we can't tell when it started
                    if prev_interval != 0.0 and prun.next_timestamp():
                        interval_dur = interval - prev_interval
                        interval = prev_interval
                        break
                    if res:
                        interval_dur = interval - prev_interval
                        set_interval(env, interval_dur, prev_interval)
                        if need_fallback:
                            update_missing(res, rev, valstats, fallback)
                        fallback = {}
                        need_fallback = False
                        yield 0, res, rev, prev_interval, valstats, env
                        res = defaultdict(list)
                        rev = defaultdict(list)
                        valstats = defaultdict(list)
                    prev_interval = interval
                    start = interval
            elif not l[:1].isspace():
                # these are likely bogus summary lines printed by v5.8 perf stat
                # just ignore
                skip = False
                continue

        if prun.skip_input():
            continue
        if args.perf_output:
            args.perf_output.write(origl.rstrip() + "\n")

        n = l.split(";")

        # filter out the empty unit field added by 3.14
        n = [x for x in n if x not in ('', 'Joules', 'ns')]

        # timestamp is already removed
        # -a --per-socket socket,numcpus,count,event,...
        # -a --per-core core,numcpus,count,event,...
        # -a -A cpu,count,event,...
        # count,event,...
        if is_event(n, 1):
            title, count, event, off = "", n[0], n[1], 2
        elif is_event(n, 3):
            title, count, event, off = n[0], n[2], n[3], 4
        elif is_event(n, 2):
            title, count, event, off = n[0], n[1], n[2], 3
        else:
            if not FUZZYINPUT:
                warn("unparseable perf output\n%s" % origl.rstrip())
            linenum += 1
            skip = False
            continue

        # dummy event used as separator to avoid merging problems
        if event.startswith("emulation-faults"):
            linenum += 1
            skip = False
            continue

        title = title.replace("CPU", "")

        # code later relies on stripping ku flags
        event = re.sub(r'\s+\[.*\]', '', event)
        event = remove_qual(event)
        m = re.match(r'(cpu_core|cpu_atom|cpu|tool)/(cycles|duration_time)/', event)
        if m:
            event = m.group(2)

        # duplicated duration_time in perf ~6.5. was already added from the first.
        if event == "duration_time" and count == "<not counted>":
            linenum += 1
            skip = False
            continue

        skip = False
        origevent = event
        runner, action, event = check_event(rlist, event, len(res[title]),
                                   title, prev_interval, origl, revnum, linenum, last_linenum)
        if runner is None:
            linenum += 1
            continue
        if action == SKIP:
            l = origl
            skip = True
        if action == FUZZY:
            need_fallback = True

        multiplex = float('nan')
        event = event.rstrip()
        if re.match(r"\s*[0-9.]+", count):
            val = float(count.replace(",", "."))
        elif re.match(r"\s*<", count):
            account[event].errors[count.replace("<","").replace(">","")] += 1
            multiplex = 0.
            val = 0
        else:
            warn("unparseable perf count\n%s" % l.rstrip())
            linenum += 1
            continue

        # post fixes:
        # ,xxx%    -> -rXXX stddev
        stddev = 0.
        if len(n) > off and n[off].endswith("%") and not skip:
            stddev = (float(n[off].replace("%", "").replace(",", ".")) / 100.) * val
            off += 1

        # ,xxx,yyy -> multiplexing in newer perf
        if len(n) > off + 1 and not skip:
            multiplex = float(n[off + 1].replace(",", "."))
            off += 2

        st = ValStat(stddev=stddev, multiplex=multiplex)

        account[event].total += 1

        def ignored_cpu(num):
            return num not in runner.cpu_list and (num not in cpu.cputocore or not any(
                    [k in runner.cpu_list for k in cpu.coreids[cpu.cputocore[num]]]))

        def add(t):
            if runner.cpu_list and is_number(t) and ignored_cpu(int(t)):
                return

            if skip:
                res[t].append(0.0)
            elif action == FUZZY:
                res[t].append(float("nan"))
            else:
                res[t].append(val)
            fallback[(t, origevent)] = (val, st)
            rev[t].append(event)
            valstats[t].append(st)
            if args.perf_summary:
                # XXX add unit, enabled, num-cpus
                assert len(res[t]) == len(rev[t])
                update_perf_summary(summary, resoff[t] + len(res[t]) - 1, t, val, event, "", multiplex)

        def dup_val(l):
            for j in l:
                if j in runner.cpu_list:
                    add("%d" % j)

        def uncore_event(event):
            return re.match(r'power|uncore', event)

        # power/uncore events are only output once for every socket
        if ((uncore_event(event) or uncore_event(origevent)) and
                is_number(title) and
                (not ((args.core or args.cpu) and not args.single_thread))):
            cpunum = int(title)
            socket = cpu.cputosocket[cpunum]
            dup_val(cpu.sockettocpus[socket])
        elif re.match(r'(S\d+-)?(D\d+-)?C\d+', title) and (smt_mode or args.no_aggr):
            m = re.match(r'(?:S(\d+)-)?(?:D(\d+)-)?C(\d+)', title)
            assert m is not None
            if m.group(2): # XXX
                warn_once("die topology not supported currently")
            socket, core = int(m.group(1)), int(m.group(3))
            dup_val(cpu.coreids[(socket, core)])
        # duration time is only output once, except with --cpu/-C (???)
        # except perf 6.2+ outputs it with -A on all cpus, but not counting except the first
        elif ((event.startswith("duration_time") or origevent.startswith("duration_time"))
                and is_number(title) and not args.cpu and not args.core):
            dup_val(runner.cpu_list)
        else:
            add(title)

        if skip:
            continue

        linenum += 1

        if args.raw or args.valcsv:
            dump_raw(out.valcsv,
                     interval if args.interval else "",
                     title,
                     event,
                     event_rmap(event, rlist),
                     val if val or not re.match(r"\s*<", count) else count,
                     len(res[title]) - 1,
                     stddev, multiplex, rlist)

    inf.close()
    if not args.import_ and not args.interval:
        set_interval(env, time.time() - start, start)
    elif args.interval:
        set_interval(env, interval_dur if interval_dur else args.interval/1000.,
                     interval if interval else float('NaN'))
    else:
        warn_no_assert("cannot determine time duration. Per second metrics may be wrong. Use -Ixxx.")
        set_interval(env, 0, 0)
    ret = prun.wait()
    print_account(account)
    if need_fallback:
        update_missing(res, rev, valstats, fallback)
    yield ret, res, rev, interval, valstats, env

run_l1_parallel = False # disabled for now until we can fix the perf scheduler

def adjust_ev(ev, level):
    # use the programmable slots for non L1 so that level 1
    # can (mostly) run in parallel with other groups.
    # this also helps for old or non ICL kernels
    # XXX this creates groups without slots leader
    if isinstance(ev, str) and ev.startswith("TOPDOWN.SLOTS") and ((run_l1_parallel and level != 1) or not ectx.slots_available) and not ev.startswith("TOPDOWN.SLOTS_P"):
        ev = ev.replace("TOPDOWN.SLOTS", "TOPDOWN.SLOTS_P")
    return ev

def ev_collect(ev, level, obj):
    if isinstance(ev, types.LambdaType):
        return ev(lambda ev, level: ev_collect(ev, level, obj), level)
    if ev == "mux":
        return DummyArith()
    if ev.startswith("interval-"):
        if not feat.supports_duration_time:
            return DummyArith()
        ev = "duration_time"

    ev = adjust_ev(ev, level)

    if level == 999:
        if ret_latency is None:
            setup_retlatency(args)
        return DummyArith()

    key = (ev, level, obj.name)
    if key not in obj.evlevels:
        if ev.startswith(("TOPDOWN.SLOTS", "PERF_METRICS.")):
            ind = [x[1] == level for x in obj.evlevels]
            ins = ind.index(True) if any(ind) else 0
            obj.evlevels.insert(ins + (0 if ev.startswith("TOPDOWN.SLOTS") else 1), key)
        else:
            obj.evlevels.append(key)
        if safe_ref(obj, 'nogroup') or ev == "duration_time":
            ectx.outgroup_events.add(ev.lower())
    return DummyArith()

def canon_event(e):
    m = re.match(r"(.*?):(.*)", e)
    if m:
        e = m.group(1)
    return e.lower()

def find_runner_by_pmu(pmu, runner_list):
    for r in runner_list:
        if r.pmu == pmu:
            return r
    return None

def event_pmu(ev):
    m = re.match(r'(.*?)/', ev)
    if m:
        return m.group(1)
    return None

def event_ectx(ev, runner_list):
    pmu = event_pmu(ev)
    if pmu and pmu.startswith("cpu"):
        r = find_runner_by_pmu(pmu, runner_list)
        if r:
            return r.ectx
    # this works for now because the atom model doesn't use any uncore events
    # may need to fix later once it does
    return ectx if ectx else runner_list[0].ectx

def do_event_rmap(e, ectx_):
    n = ectx_.emap.getperf(e)
    if ectx_.emap.getevent(n, nocheck=event_nocheck()):
        return n
    if e in non_json_events:
        return e
    if e.startswith("uncore"):
        warn_no_assert("rmap: cannot find %s, using dummy" % e)
    else:
        warn("rmap: cannot find %s, using dummy" % e)
    return "dummy"

def event_rmap(e, runner_list):
    ectx_ = event_ectx(e, runner_list)
    if e in ectx_.rmap_cache:
        return ectx_.rmap_cache[e]
    n = do_event_rmap(e, ectx_)
    ectx_.rmap_cache[e] = n
    return n

cycles_aliases = frozenset(("cycles", "cpu_clk_unhalted.thread", "cpu_clk_unhalted.core",
                            "cpu_core/event=0x3c,umask=0x0/", "cpu_atom/event=0x3c,umask=0x0/",
                            "cpu/event=0x3c,umask=0x0/"))

# compare events to handle name aliases
def compare_event(aname, bname):
    # XXX this should be handled in ocperf
    if aname in cycles_aliases and bname in cycles_aliases:
        return True
    a = ectx.emap.getevent(aname, nocheck=event_nocheck())
    if a is None:
        return False
    b = ectx.emap.getevent(bname, nocheck=event_nocheck())
    if b is None:
        return False
    fields = ('val','event','cmask','edge','inv')
    return map_fields(a, fields) == map_fields(b, fields)

# XXX check does not match the function name
def is_hybrid():
    return ocperf.file_exists("/sys/bus/event_source/devices/cpu/format/any")

def lookup_res(res, rev, ev, obj, env, level, referenced, cpuoff, st, runner_list):
    """get measurement result, possibly wrapping in UVal"""

    if level == 999:
        return lookup_retlat(ev)

    ev = adjust_ev(ev, level)

    if isinstance(ev, str) and ev.startswith("interval") and feat.supports_duration_time:
        scale = { "interval-s":  1e9,
                  "interval-ns": 1,
                  "interval-ms": 1e6 }[ev]
        return lookup_res(res, rev, "duration_time", obj, env, level, referenced, cpuoff, st, runner_list)/scale

    if ev in env:
        return env[ev]
    if ev == "mux":
        return min([s.multiplex for s in st])
    #
    # when the model passed in a lambda run the function for each logical cpu
    # (by resolving its EVs to only that CPU)
    # and then sum up. This is needed for the workarounds to make various
    # per thread counters at least as big as unhalted cycles.
    #
    # otherwise we always sum up.
    #
    if isinstance(ev, types.LambdaType):
        return sum([ev(lambda ev, level:
                  lookup_res(res, rev, ev, obj, env, level, referenced, off, st, runner_list), level)
                  for off in range(env['num_merged'])])

    index = obj.res_map[(ev, level, obj.name)]
    referenced.add(index)
    #print((ev, level, obj.name), "->", index)
    if not args.fast:
        try:
            r = rev[index]
        except IndexError:
            warn_once_no_assert("Not enough lines in perf output for rev (%d vs %d for %s) at %s, event %s" %
                    (index, len(rev), obj.name, env['interval'], ev))
            return 0
        rmap_ev = event_rmap(r, runner_list).lower()
        ev = ev.lower()
        assert (rmap_ev == canon_event(ev).replace("/k", "/") or
                compare_event(rmap_ev, ev) or
                rmap_ev == "dummy" or
                (rmap_ev.endswith("_any") and not is_hybrid())), "event rmap mismatch %s vs %s" % (rmap_ev, ev)

    try:
        vv = res[index]
    except IndexError:
        warn_once("Not enough lines in perf output for res (%d vs %d for %s) at %s" %
                (index, len(res), obj.name, env['interval']))
        return 0.0
    if isinstance(vv, tuple):
        if cpuoff == -1:
            vv = sum(vv)
        else:
            try:
                vv = vv[cpuoff]
            except IndexError:
                warn_once("Partial CPU thread data from perf for %s" %
                        obj.name)
                return 0.0
    if st[index].stddev or st[index].multiplex != 100.0:
        return UVal(name=ev, value=vv, stddev=st[index].stddev, mux=st[index].multiplex)
    return vv

class BadEvent(Exception):
    def __init__(self, name):
        super(Exception, self).__init__()
        self.event = name

# XXX check for errata
def sample_event(e, emap):
    ev = emap.getevent(e, nocheck=event_nocheck())
    if not ev:
        raise BadEvent(e)
    postfix = args.ring_filter
    if postfix:
        postfix = ":" + postfix
    return ev.name + postfix

def sample_desc(s, emap):
    try:
        return " ".join([sample_event(x, emap) for x in s])
    except BadEvent as e:
        warn_once_no_assert("Unknown sample event %s" % (e.event))
        return ""

def get_level(x):
    return x[1]

def get_levels(evlev):
    return [x[1] for x in evlev]

def get_names(evlev):
    return [x[0] for x in evlev]

def full_name(obj):
    name = obj.name
    while 'parent' in obj.__dict__ and obj.parent:
        obj = obj.parent
        name = obj.name + "." + name
    return name

def package_node(obj):
    return safe_ref(obj, 'domain') in ("Package", "SystemMetric")

def not_package_node(obj):
    return not package_node(obj)

def core_node(obj):
    return safe_ref(obj, 'domain') in ectx.core_domains

def thread_node(obj):
    if package_node(obj):
        return False
    if core_node(obj):
        return False
    return True

def any_node(obj):
    return True

def obj_domain(obj):
    return obj.domain.replace("Estimated", "est").replace("Calculated", "calc")

def metric_unit(obj):
    if has(obj, 'unit'):
        return obj.unit
    if has(obj, 'domain'):
        return obj_domain(obj).replace("SystemMetric", "SysMetric")
    return "Metric"

def obj_desc(obj, sep="\n\t"):
    desc = obj.desc[1:].replace("\n", sep)

    # by default limit to first sentence
    if not args.long_desc and "." in desc:
        desc = desc[:desc.find(".") + 1] + ".."

    return desc

def get_mg(obj):
    return ref_or(obj, 'metricgroup', frozenset([]))

# only check direct children, the rest are handled recursively
def children_over(l, obj):
    n = [o.thresh for o in l if 'parent' in o.__dict__ and o.parent == obj]
    return any(n)

def bottleneck_related(obj, bn):
    if obj == bn:
        return True
    if (get_mg(bn) & get_mg(obj)) - tma_mgroups:
        return True
    return False

def obj_desc_runtime(obj, rest, bn):
    # hide description if children are also printed
    if children_over(rest, obj) or (not args.desc and not bottleneck_related(obj, bn)):
        desc = ""
    else:
        desc = obj_desc(obj)
    if 'htoff' in obj.__dict__ and obj.htoff and obj.thresh and cpu.ht and not args.single_thread:
        desc += """
Warning: Hyper Threading may lead to incorrect measurements for this node.
Suggest to re-measure with HT off (run cputop.py "thread == 1" offline | sh)."""
    return desc

def node_filter(obj, default, sibmatch, mgroups):
    if args.nodes:
        fname = full_name(obj)
        name = obj.name

        def _match(m):
            return (fnmatch(name, m) or
                    fnmatch(fname, m) or
                    fnmatch(fname, "*." + m))

        def match(m, checklevel=True):
            if m.endswith("^"):
                m = m[:-1]
            r = re.match("(.*)/([0-9]+)", m)
            if r:
                level = int(r.group(2))
                if checklevel and obj.level > level:
                    return False
                m = r.group(1)
            return _match(m)

        def has_siblings(j, obj):
            return j.endswith("^") and 'sibling' in obj.__dict__ and obj.sibling

        def has_mg(j, obj):
            return j.endswith("^") and get_mg(obj)

        nodes = args.nodes
        if nodes[0] == '!':
            default = False
            nodes = nodes[1:]

        for j in nodes.split(","):
            j = j.strip()
            if j == "":
                continue
            i = 0
            if j[0] == '^' or j[0] == '-':
                if match(j[1:]):
                    return False
                continue
            elif j[0] == '+':
                i += 1

            if match(j[i:], True):
                if has_siblings(j, obj):
                    sibmatch |= set(obj.sibling)
                if has_mg(j, obj):
                    mgroups |= obj.metricgroup
                obj.forced = True
                return True
            if has_siblings(j, obj):
                for sib in obj.sibling:
                    fname = full_name(sib)
                    name = sib.name
                    if match(j[i:], False):
                        sibmatch.add(obj)
                        return True
    return default

def _find_bn(bn, level):
    siblings = sorted([x for x in bn if x.level - 1 == level], key=lambda x: x.val, reverse=True)
    if len(siblings) == 0:
        return None
    # remove overlap nodes
    siblings = [x for x in siblings if not (has(x, 'overlap') and x.overlap)]
    # ambigious
    if level > 0 and len(siblings) > 1 and siblings[0].val - siblings[1].val <= SIB_THRESH:
        return None
    n = _find_bn([x for x in bn if full_name(x).startswith(full_name(siblings[0]))], level + 1)
    if n is None:
        return siblings[0]
    return n

def find_bn(olist, match):
    if args.force_bn:
        bn = sorted([o for o in olist if o.name in args.force_bn], key=lambda x: x.level, reverse=True)
        if bn:
            return bn[0]
    bn = [o for o in olist if match(o) and not o.metric and o.thresh]
    if not bn:
        return None
    return _find_bn(bn, 0)

pmu_does_not_exist = set()

# XXX check if PMU can be accessed from current user
def missing_pmu(e):
    if event_nocheck():
        return False
    m = re.match(r"([a-z0-9_]+)/", e)
    if m:
        pmu = m.group(1)
        if pmu in pmu_does_not_exist:
            return True
        if not os.path.isdir("/sys/bus/event_source/devices/%s" % pmu):
            pmu_does_not_exist.add(pmu)
            return True
    return False

def query_errata(obj, errata_events, errata_nodes, errata_names):
    errata = [errata_events[x] for x in obj.evlist if x in errata_events]
    if any(errata):
        errata_nodes.add(obj)
        errata_names |= set(errata)

def olist_by_metricgroup(l, mg):
    if args.no_sort:
        return l
    valid = set(l)
    visited = set()
    ml = []
    for obj in l:
        if obj in visited:
            continue

        def add(obj):
            if obj not in visited:
                ml.append(obj)
                visited.add(obj)

        if has(obj, 'metricgroup'):
            for g in sorted(obj.metricgroup):
                for j in mg[g]:
                    if j in valid:
                        add(j)
        add(obj)
    return ml

def node_unit(obj):
    return (" " + obj_domain(obj)) if has(obj, 'domain') else ""

def node_below(obj):
    return not obj.thresh

class Summary(object):
    """Accumulate counts for summary."""
    def __init__(self):
        self.res = defaultdict(list)
        self.rev = defaultdict(list)
        self.env = Counter() # type: typing.Counter[str]
        self.valstats = defaultdict(list)
        self.summary_perf = OrderedDict()

    def add(self, res, rev, valstats, env):
        for j in sorted(res.keys()):
            for ind, val in enumerate(res[j]):
                if ind < len(self.res[j]):
                    self.res[j][ind] += val
                    self.valstats[j][ind] = combine_valstat([self.valstats[j][ind], valstats[j][ind]])
                else:
                    self.res[j].append(val)
                    self.valstats[j].append(valstats[j][ind])
        if len(rev.keys()) == 1:
            append_dict(self.rev, rev)
        else:
            self.rev.update(rev)
        for j in env.keys():
            self.env[j] += env[j]

def parse_metric_group(l, mg):
    if l is None:
        return [], []

    add, rem = [], []
    for n in l.split(","):
        if n[0:1] == '-' or n[0:1] == '^':
            if n[1:] not in mg:
                print("metric group", n[1:], "not found", file=sys.stderr)
                continue
            rem += [x.name for x in mg[n[1:]]]
            continue
        if n[0:1] == '+':
            n = n[1:]
        if n not in mg:
            print("metric group", n, "not found", file=sys.stderr)
            continue
        add += [x.name for x in mg[n]]
    return add, rem

def obj_area(obj):
    return obj.area if has(obj, 'area') and not args.no_area else None

def get_parents(obj):
    def get_par(obj):
        return obj.parent if 'parent' in obj.__dict__ else None
    p = get_par(obj)
    l = []
    while p:
        l.append(p)
        p = get_par(p)
    return l

def quote(s):
    if " " in s:
        return '"' + s + '"'
    return s

class Group(object):
    def __init__(self, evnum, objl, num, outgroup=False):
        self.evnum = evnum
        self.base = -1
        self.objl = set(objl)
        self.outgroup = outgroup
        self.num = num

class GroupCmp(object):
    def __init__(self, v):
        self.v = v
    def __lt__(self, g):
        return self.v < g.base

# Control whether even unrelated groups can be merged
any_merge = True

# Interleave uncore events between CPU groups
distribute_uncore = False

def grab_group(l):
    if needed_counters(l) <= ectx.counters:
        return len(l)
    n = 1
    while needed_counters(l[:n]) <= ectx.counters and n < len(l):
        n += 1
    if needed_counters(l[:n]) > ectx.counters and n > 0:
        n -= 1
        assert needed_counters(l[:n]) <= ectx.counters
    return n

def update_group_map(evnum, obj, group):
    for lev in obj.evlevels:
        r = raw_event(lev[0])
        # can happen during splitting
        # the update of the other level will fix it
        if r in evnum and lev not in obj.group_map:
            obj.group_map[lev] = (group, evnum.index(r))

def do_distribute_uncore(evgroups):
    cg = [g for g in evgroups if not g.outgroup]
    og = [g for g in evgroups if g.outgroup]
    return [x for x in chain(*zip_longest(cg, og)) if x is not None]

def gen_res_map(solist):
    for obj in solist:
        for k in obj.group_map.keys():
            gr = obj.group_map[k]
            obj.res_map[k] = gr[0].base + gr[1]

def print_group(g):
    evkeys = [k for o in g.objl for k in o.group_map.keys() if o.group_map[k][0] == g]
    objnames = {("%s" % quote(x[2])) + ("[%d]" % x[1] if x[1] else "") for x in evkeys}
    if len(objnames) == 0:
        return
    evnames = {mark_fixed(x[0]) for x in evkeys}
    pwrap(" ".join(objnames) + ":", 78)
    pwrap(" ".join(evnames).lower() +
          (" [%d counters]" % needed_counters(g.evnum)) +
          (" [%d]" % g.base if args.debug else ""), 75, "  ")

def match_patlist(l, s):
    for x in l.split(","):
        if fnmatch(s, x):
            return True
    return False

class Scheduler(object):
    """Schedule events into groups."""

    def __init__(self):
        self.evnum = [] # flat global list
        self.evgroups = [] # of Group
        self.og_groups = {}
        # list of groups that still have generic counters, for faster
        # duplicate checks
        self.evgroups_nf = []
        self.nextgnum = 0
        self.event_to_group = {}

    # should avoid adding those in the first place instead
    def dummy_unreferenced(self, olist):
        refs = defaultdict(set)
        for o in olist:
            for g, ind in o.group_map.values():
                refs[g].add(ind)
        for g in self.evgroups:
            ref = refs[g]
            if len(ref) < len(g.evnum):
                for i in range(len(g.evnum)):
                    if i not in ref:
                        debug_print("unreferenced %s [%d] %s" % (g.evnum[i],
                                         i,
                                         " ".join([o.name for o in g.objl])))
                        g.evnum[i] = "dummy"

    def split_groups(self, obj, evlev):
        for lev, evl in groupby(sorted(evlev, key=get_level), get_level):
            evlev = list(evl)
            evnum = [raw_event(x[0]) for x in evlev]
            while evlev:
                n = grab_group(evnum)
                self.add(obj, evnum[:n], None)
                evlev = evlev[n:]
                evnum = evnum[n:]

    # may modify evnum
    def add_duplicate(self, evnum, obj):
        evset = set(evnum)
        num_gen = num_generic_counters(evset)
        full = set()

        if ((has(obj, 'area') and match_patlist(DEDUP_AREA, obj.area)) or
                match_patlist(DEDUP_NODE, obj.name)):
            # reuse any previous event independent of group subsets
            # for bottleneck nodes which are too large for the usual
            # heuristics

            duped = []
            for ind, e in enumerate(evnum):
                if ismetric(e) or is_slots(e):
                    continue
                if e in self.event_to_group:
                    g = self.event_to_group[e]
                    debug_print("dedup %s %s to %s" % (obj.name, e, " ".join([x.name for x in g.objl])))
                    g.objl.add(obj)
                    update_group_map(g.evnum, obj, g)
                    duped.append(ind)
            # need to remove in place so that caller sees it
            # remove backwards so that indexes stay valid
            for ind in reversed(duped):
                del evnum[ind]
            if len(evnum) == 0:
                debug_print("%s fully deduped" % obj.name)
                return True

        for g in reversed(self.evgroups_nf if num_gen else self.evgroups):
            if g.outgroup:
                continue

            #
            # In principle we should only merge if there is any overlap,
            # otherwise completely unrelated nodes get merged. But the perf
            # scheduler isn't very good at handling smaller groups, and
            # with eventual exclusive use we would like as big groups as
            # possible. Still keep it as a --tune option to play around.
            if ((any_merge or not evset.isdisjoint(g.evnum)) and
                  needed_counters(cat_unique(g.evnum, evnum)) <= ectx.counters):
                obj_debug_print(obj, "add_duplicate %s in %s obj %s to group %d" % (
                    " ".join(evnum),
                    " ".join(g.evnum),
                    obj.name,
                    g.num))
                for k in evnum:
                    if k not in g.evnum:
                        g.evnum.append(k)
                    if k not in self.event_to_group:
                        self.event_to_group[k] = g
                g.objl.add(obj)
                update_group_map(g.evnum, obj, g)
                return True

            # memorize already full groups
            elif num_generic_counters(set(g.evnum)) >= ectx.counters:
                full.add(g)
        if full:
            self.evgroups_nf = [g for g in self.evgroups_nf if g not in full]

        return False

    def add(self, obj, evnum, evlev):
        # does not fit into a group.
        if needed_counters(evnum) > ectx.counters:
            self.split_groups(obj, evlev)
            return
        evnum = dedup(evnum)
        if not self.add_duplicate(evnum, obj):
            g = Group(evnum, [obj], self.nextgnum)
            obj_debug_print(obj, "add %s to group %d" % (evnum, g.num))
            for k in evnum:
                if k not in self.event_to_group:
                    self.event_to_group[k] = g
            self.nextgnum += 1
            self.evgroups.append(g)
            self.evgroups_nf.append(g)
            update_group_map(evnum, obj, g)

    def add_outgroup(self, obj, evnum):
        obj_debug_print(obj, "add_outgroup %s" % evnum)
        for ev in evnum:
            if ev in self.og_groups:
                g = self.og_groups[ev]
                g.objl.add(obj)
            else:
                g = Group([ev], [obj], self.nextgnum, True)
                self.nextgnum += 1
                self.og_groups[ev] = g
                self.evgroups.append(g)
                self.evgroups_nf.append(g)
            update_group_map([ev], obj, g)

    def allocate_bases(self):
        base = 0
        for g in self.evgroups:
            g.base = base
            self.evnum += g.evnum
            base += len(g.evnum)

    def print_group_summary(self, olist):
        num_groups = len([g for g in self.evgroups if not g.outgroup])
        print("%d cpu groups, %d outgroups with %d events total (%d unique) for %d objects, %d dummies" % (
            num_groups,
            len(self.evgroups) - num_groups,
            len(self.evnum),
            len(set(self.evnum)),
            len(olist),
            self.evnum.count("dummy")),
              file=sys.stderr)

    # fit events into available counters
    def schedule(self, olist):
        # sort objects by level and inside each level by num-counters
        solist = sorted(olist, key=lambda x: (x.level, x.nc))
        # try to fit each objects events into groups
        # that fit into the available CPU counters
        for obj in solist:
            obj_debug_print(obj, "schedule %s " % obj.name)
            evnum = obj.evnum
            evlevels = obj.evlevels
            oe = [e in ectx.outgroup_events for e in obj.evnum]
            if any(oe):
                # add events outside group separately
                og_evnum = list(compress(obj.evnum, oe))
                self.add_outgroup(obj, og_evnum)
                if all(oe):
                    continue

                # keep other events
                ie = not_list(oe)
                evlevels = list(compress(obj.evlevels, ie))
                evnum = list(compress(obj.evnum, ie))

            self.add(obj, evnum, evlevels)

        if args.no_multiplex or distribute_uncore:
            self.evgroups = do_distribute_uncore(self.evgroups)

        if not KEEP_UNREF:
            self.dummy_unreferenced(olist)
        self.allocate_bases()

        if args.print_group:
            for g in self.evgroups:
                print_group(g)

        gen_res_map(olist)
        if args.print_group:
            self.print_group_summary(olist)

def should_print_obj(obj, match, thresh_mg, bn):
    assert not isinstance(obj.val, DummyArith)
    if obj.val is None:
        return False
    if obj.thresh or obj.metric or args.verbose:
        if not match(obj):
            return False
        elif args.only_bottleneck and obj != bn:
            if args.node_metrics and 'group_select' in obj.__dict__ and get_mg(obj) & get_mg(bn):
                return True
            if args.bottlenecks and 'area' in obj.__dict__ and obj.area == "Bottleneck":
                return True
            # XXX handle more explicit options like metrics?
            if 'forced' in obj.__dict__ and obj.forced:
                return True
        elif obj.metric:
            if args.node_metrics and 'group_select' in obj.__dict__ and not (get_mg(obj) & thresh_mg):
                return False
            if args.verbose or (obj.metric and obj.thresh and obj.val != 0.0):
                return True
        elif check_ratio(obj.val): # somewhat redundant
            thresh_mg |= get_mg(obj) - tma_mgroups
            return True
    return False

def get_uval(ob):
    u = ob.val if isinstance(ob.val, UVal) else UVal(ob.name, ob.val)
    u.name = ob.name
    return u

# pre compute column lengths
def compute_column_lengths(olist, out):
    for obj in olist:
        out.set_hdr(full_name(obj), obj_area(obj))
        if obj.metric:
            out.set_unit(metric_unit(obj))
        else:
            out.set_unit(node_unit(obj))
        out.set_below(node_below(obj))

class Printer(object):
    """Print measurements while accumulating some metadata."""
    def __init__(self, metricgroups):
        self.sample_obj = set()
        self.bottlenecks = set()
        self.numprint = 0
        self.metricgroups = metricgroups

    def print_res(self, olist, out, timestamp, title, match, bn, idlemark=False):
        if bn:
            self.bottlenecks.add(bn)

        out.logf.flush()

        # determine all objects to print
        thresh_mg = set() # type: Set[str]
        olist = [o for o in olist if should_print_obj(o, match, thresh_mg, bn)]

        # sort by metric group
        olist = olist_by_metricgroup(olist, self.metricgroups)

        compute_column_lengths(olist, out)

        # step 3: print
        for i, obj in enumerate(olist):
            val = get_uval(obj)
            if has(obj, 'maxval') and obj.maxval is not None and obj.maxval != 0:
                maxval = UVal(obj.name, obj.maxval)
                val = min(val, maxval)
            desc = obj_desc_runtime(obj, olist[i + 1:], bn)
            if obj.metric:
                out.metric(obj_area(obj), obj.name, val, timestamp,
                        desc,
                        title,
                        metric_unit(obj),
                        idlemark)
            else:
                out.ratio(obj_area(obj),
                        full_name(obj), val, timestamp,
                        "%" + node_unit(obj),
                        desc,
                        title,
                        sample_desc(obj.sample, self.emap) if has(obj, 'sample') else None,
                        "<==" if obj == bn else "",
                        node_below(obj),
                        idlemark)
                if obj.thresh or args.verbose:
                    self.sample_obj.add(obj)
            self.numprint += 1

    def init_emap(self, emap):
        self.emap = emap

# check nodes argument for typos
def check_nodes(runner_list, nodesarg):
    def opt_obj_name(s):
        if s[:1] in ('+', '^', '-'):
            s = s[1:]
        if "/" in s:
            s = s[:s.index("/")]
        if s.endswith("^"):
            s = s[:-1]
        return s

    if nodesarg[:1] == "!":
        nodesarg = nodesarg[1:]
    options = [opt_obj_name(s) for s in nodesarg.split(",")]
    def valid_node(s):
        if s == "":
            return True
        for r in runner_list:
            if s in r.odict:
                return True
            for k in r.olist:
                if fnmatch(k.name, s) or fnmatch(full_name(k), s):
                    return True
        return False

    valid = list(map(valid_node, options))
    if not all(valid):
        sys.exit("Unknown node(s) in --nodes: " +
                 " ".join([o for o, v in zip(options, valid) if not v]))

class Runner(object):
    """Handle measurements of event groups. Map events to groups."""

    def reset(self):
        self.stat = ComputeStat(args.quiet)
        self.olist = []
        self.idle_keys = set()
        self.sched = Scheduler()
        self.printer = Printer(self.metricgroups)

    def __init__(self, max_level, idle_threshold, kernel_version, pmu=None):
        # always needs to be filtered by olist:
        self.metricgroups = defaultdict(list)
        self.reset()
        self.odict = {}
        self.max_level = max_level
        self.max_node_level = 0
        self.idle_threshold = idle_threshold
        self.ectx = EventContext(pmu)
        self.pmu = pmu
        self.full_olist = []
        self.cpu_list = [] # type: List[int]
        self.kernel_version = kernel_version

    def set_ectx(self):
        global ectx
        ectx = self.ectx

    def clear_ectx(self):
        # confuses the type checker
        #global ectx
        #ectx = None
        pass

    def do_run(self, obj):
        obj.res = None
        obj.res_map = {}
        obj.group_map = {}
        self.olist.append(obj)
        self.full_olist.append(obj)
        self.odict[obj.name] = obj
        if has(obj, 'metricgroup'):
            for j in sorted(obj.metricgroup):
                self.metricgroups[j].append(obj)
        self.max_node_level = max(self.max_node_level, obj.level)

    # remove unwanted nodes after their parent relationship has been set up
    def filter_nodes(self):
        add_met, remove_met = parse_metric_group(args.metric_group, self.metricgroups)

        add_obj = {self.odict[x] for x in add_met}
        parents = [get_parents(x) for x in add_obj]
        if add_obj:
            for o in self.olist:
                if safe_ref(o, 'sibling') is None:
                    continue
                m = set(o.sibling) & add_obj
                for s in m:
                    parents.append(s)
                    parents += get_parents(s)

        self.sibmatch = set() # type: Set[Any]
        mgroups = set() # type: Set[str]

        def want_node(obj, mgroups, tma_mgroups):
            mg = safe_ref(obj, 'metricgroup')
            if args.no_uncore and mg and "SoC" in mg:
                return False
            area = safe_ref(obj, 'area')
            if args.areas and area and any([fnmatch(area, p) for p in args.areas.split(",")]):
                return True
            if args.bottlenecks and area == "Bottleneck":
                return True

            want = ((obj.metric and args.metrics) or
                    (('force_metric' in obj.__dict__) and obj.force_metric) or
                    obj.name in add_met or
                    obj in parents) and obj.name not in remove_met
            if not obj.metric and obj.level <= self.max_level:
                want = True
            want = node_filter(obj, want, self.sibmatch, mgroups)
            mg = get_mg(obj)
            tma_mgroups |= set([x for x in mg if x.startswith("Tma")])
            if args.node_metrics and want and not obj.metric:
                mgroups |= set(mg) - tma_mgroups
            return want

        for x in self.olist:
            if 'forced' in x.__dict__:
                x.forced = False

        # this updates sibmatch
        fmatch = [want_node(x, mgroups, tma_mgroups) for x in self.olist]

        def select_node(obj):
            if obj in self.sibmatch:
                return True
            if get_mg(obj) & mgroups:
                obj.group_select = True
                return True
            return False

        # now keep what is both in fmatch and sibmatch and mgroups
        # assume that mgroups matches do not need propagation
        self.olist = [obj for obj, fil in zip(self.olist, fmatch) if fil or select_node(obj)]

    def setup_children(self):
        for obj in self.olist:
            if not obj.metric and 'parent' in obj.__dict__ and obj.parent:
                obj.parent.children.append(obj)

    def reset_thresh(self):
        for obj in self.olist:
            obj.thresh = Undef

    def run(self, obj):
        obj.thresh = False
        obj.metric = False
        obj.children = []
        self.do_run(obj)

    def metric(self, obj):
        obj.thresh = Undef
        obj.metric = True
        obj.level = 0
        obj.sibling = None
        self.do_run(obj)

    def force_metric(self, obj):
        obj.force_metric = True
        self.metric(obj)

    # collect the events by pre-computing the equation
    def collect(self):
        self.set_ectx()
        bad_nodes = set()
        bad_events = set()
        unsup_nodes = set()
        errata_nodes = set() # type: Set[Any]
        errata_warn_nodes = set() # type: Set[Any]
        errata_names = set() # type: Set[str]
        errata_warn_names = set() # type: Set[str]
        min_kernel = [] # type: List[int]
        for obj in self.olist:
            obj.evlevels = []
            obj.compute(lambda ev, level: ev_collect(ev, level, obj))
            obj.val = None
            obj.evlist = [x[0] for x in obj.evlevels]
            obj.evnum = raw_events(obj.evlist, initialize=True)
            obj.nc = needed_counters(dedup(obj.evnum))

            # work arounds for lots of different problems
            unsup = [x for x in obj.evlist if unsup_event(x, unsup_events, self.kernel_version, min_kernel)]
            if any(unsup):
                bad_nodes.add(obj)
                bad_events |= set(unsup)
            unsup = [x for x in obj.evlist if missing_pmu(x)]
            if any(unsup):
                unsup_nodes.add(obj)
            query_errata(obj, ectx.errata_events, errata_nodes, errata_names)
            query_errata(obj, ectx.errata_warn_events, errata_warn_nodes, errata_warn_names)
        if bad_nodes:
            if args.force_events:
                pwrap_not_quiet("warning: Using --force-events. Nodes: " +
                        " ".join([x.name for x in bad_nodes]) + " may be unreliable")
            else:
                if not args.quiet:
                    pwrap("warning: removing " +
                       " ".join([x.name for x in bad_nodes]) +
                       " due to unsupported events in kernel: " +
                       " ".join(sorted(bad_events)), 80, "")
                    if min_kernel:
                        print("Fixed in kernel %d" % (sorted(min_kernel, key=kv_to_key, reverse=True)[0]),
                                file=sys.stderr)
                    print("Use --force-events to override (may result in wrong measurements)",
                            file=sys.stderr)
                self.olist = [x for x in self.olist if x not in bad_nodes]
        if unsup_nodes:
            pwrap_not_quiet("Nodes " + " ".join(x.name for x in unsup_nodes) + " has unsupported PMUs")
            self.olist = [x for x in self.olist if x not in unsup_nodes]
        if errata_nodes and not args.ignore_errata:
            pwrap_not_quiet("Nodes " + " ".join(x.name for x in errata_nodes) + " have errata " +
                        " ".join(errata_names) + " and were disabled. " +
                        "Override with --ignore-errata")
            self.olist = [x for x in self.olist if x in errata_nodes]
        if errata_warn_nodes and not args.ignore_errata:
            pwrap_not_quiet("Nodes " + " ".join(x.name for x in errata_warn_nodes) + " have errata " +
                        " ".join(errata_warn_names))
        self.clear_ectx()

    def propagate_siblings(self):
        changed = [0]

        def propagate(k, changed, srco):
            if args.debug:
                print("propagate", srco.name, "->", k.name)
            if not k.thresh:
                k.thresh = True
                changed[0] += 1

        for obj in self.olist:
            if obj in self.sibmatch:
                propagate(obj, changed, obj)
            if obj.thresh and obj.sibling:
                if isinstance(obj.sibling, (list, tuple)):
                    for k in obj.sibling:
                        propagate(k, changed, obj)
                else:
                    propagate(obj.sibling, changed, obj)
        return changed[0]

    def compute(self, res, rev, valstats, env, match, stat, runner_list):
        self.set_ectx()
        changed = 0

        # step 1: compute
        for obj in self.olist:
            obj.errcount = 0

            if not match(obj):
                continue
            ref = set() # type: Set[int]
            oldthresh = obj.thresh
            if 'parent' in obj.__dict__ and obj.parent and obj.parent not in self.olist:
                obj.parent.thresh = True
            obj.compute(lambda e, level:
                            lookup_res(res, rev, e, obj, env, level, ref, -1, valstats, runner_list))
            # compatibility for models that don't set thresh for metrics
            if isinstance(obj.thresh, UVal) and obj.name == "Undef":
                obj.thresh = True
            if args.force_bn and obj.name in args.force_bn:
                obj.thresh = True
            if obj.thresh != oldthresh and oldthresh != Undef:
                changed += 1
            if stat:
                stat.referenced |= ref
            if not obj.res_map and not all([x in env for x in obj.evnum]) and not args.quiet:
                print("%s not measured" % (obj.__class__.__name__,), file=sys.stderr)
            if not obj.metric and not check_ratio(obj.val):
                obj.thresh = False
                if stat:
                    stat.mismeasured.add(obj.name)
            if stat and has(obj, 'errcount') and obj.errcount > 0:
                if obj.name not in stat.errors:
                    stat.errcount += obj.errcount
                stat.errors.add(obj.name)
                stat.referenced |= set(obj.res_map.values())

        # step 2: propagate siblings
        changed += self.propagate_siblings()
        self.clear_ectx()
        return changed

    def list_metric_groups(self):
        if not args.quiet:
            print("MetricGroups:")
        mg = sorted(self.metricgroups.keys())
        if args.quiet or args.csv:
            pre = ""
        else:
            pre = "\t"
        for j in mg:
            print(pre + j)

    def list_nodes(self, title, filt, rest):
        def match(rest, n, fn):
            return not rest or any([n.startswith(x) or fn.startswith(x) if
                                    not x.endswith("^") else
                                    n == x[:-1] or fn == x[:-1]
                                    for x in rest])

        if title and not args.quiet:
            print("%s:" % title)
        for obj in self.olist:
            fn = full_name(obj)
            if args.csv:
                pre, sep, dsep = "", "\n", ""
            elif args.quiet:
                pre, sep, dsep = "", "\n", "\n"
            else:
                pre, sep, dsep = "\t", "\n", "\n\t"
            if filt(obj) and match(rest, obj.name, fn):
                print(fn, end=sep)
                if not args.no_desc:
                    print(pre + obj_desc(obj, sep=dsep))

    def filter_per_core(self, single_thread, rest):
        if ("Slots" not in self.ectx.core_domains and
                cpu.ht and
                not single_thread and has_core_node(self)):
            if not feat.supports_percore:
                self.olist = filternot(lambda obj:
                        safe_ref(obj, 'domain') in self.ectx.core_domains,
                        self.olist)
            else:
                rest = add_args(rest, "--percore-show-thread")
        return rest

def runner_restart(runner, offset):
    emap = runner.printer.emap
    runner.reset()
    runner.printer.emap = emap
    runner.olist = list(runner.full_olist)
    for o in runner.olist:
        o.group_map = {}
        o.res_map = {}
    runner.filter_nodes()
    runner.collect()
    runner.set_ectx()
    runner.sched.schedule(runner.olist)
    runner.clear_ectx()
    runner.sched.offset = offset
    offset += len(runner.sched.evnum)
    return offset

def runner_init(runner):
    runner.setup_children()
    runner.filter_nodes()
    runner.collect()

def supports_pebs():
    if feat.has_max_precise:
        return feat.max_precise > 0
    return not cpu.hypervisor

def remove_pp(s):
    if s.endswith(":pp"):
        return s[:-3]
    return s

def clean_event(e):
    return remove_pp(e).replace(".", "_").replace(":", "_").replace('=','')

def sample_groups(sl):
    s = ""
    while sl:
        # may generate inefficient groups depending on order
        n = grab_group(sl)
        if s:
            s += ","
        g = ",".join(add_filter(sl[:n]))
        if n > 1:
            g = "{%s}" % g
        s += g
        sl = sl[n:]
    return s

def do_sample(sample_obj, rest, count, ret, kernel_version):
    samples = [("cycles:pp", "Precise cycles", )]

    for obj in sample_obj:
        for s in obj.sample:
            samples.append((s, obj.name))

    # first dedup
    samples = dedup(samples)

    # now merge objects with the same sample event into one
    def sample_event(x):
        return x[0]
    samples = sorted(samples, key=sample_event)
    samples = [(k, "_".join([x[1] for x in g])) for k, g in groupby(samples, key=sample_event)]

    # find unsupported events
    nsamp = [x for x in samples if not unsup_event(x[0], unsup_events, kernel_version)]
    nsamp = [(remove_pp(x[0]), x[1])
             if unsup_event(x[0], unsup_pebs, kernel_version) else x
             for x in nsamp]
    if nsamp != samples:
        missing = [x[0] for x in set(samples) - set(nsamp)]
        warn("Update kernel to handle sample events:" + "\n".join(missing))

    def force_pebs(ev):
        return ev in ectx.require_pebs_events

    no_pebs = not supports_pebs()
    if no_pebs:
        for j in nsamp:
            # initialize ectx.require_pebs_events
            raw_event(j[0], initialize=True)
        nnopebs = {x[0] for x in nsamp if force_pebs(x[0])}
        if nnopebs and not args.quiet:
            for o in nnopebs:
                warn_no_assert("sample event %s not (currently) supported in virtualization" % o)
        nsamp = [x for x in nsamp if x[0] not in nnopebs]

    sl = [raw_event(s[0], s[1] + "_" + clean_event(s[0]), period=True) for s in nsamp]
    sample = sample_groups(sl)
    if no_pebs:
        sample = re.sub(r'/p+', '/', sample)
        sample = re.sub(r':p+', '', sample)
    if not args.quiet:
        print("Sampling:")
    extra_args = args.sample_args.replace("+", "-").split()
    perf_data = args.sample_basename
    if count is not None:
        perf_data += ".%d" % count
    sperf = ([feat.perf, "record"] +
             extra_args +
             ["-e", "'" + sample + "'", "-o", perf_data] +
             [x for x in rest if x not in ("-A", "--percore-show-thread")])
    cmd = " ".join(sperf)
    if not (args.run_sample and args.quiet):
        print(cmd)
    if args.run_sample and ret == 0:
        ret = os.system(cmd)
        if ret:
            print("Sampling failed")
            sys.exit(1)
        if not args.quiet:
            print("Run `" + feat.perf + " report%s%s' to show the sampling results" % (
                (" -i %s" % perf_data) if perf_data != "perf.data" else "",
                " --no-branch-history" if "-b" in extra_args else ""))

def suggest_bottlenecks(runner):
    def gen_bn(o):
        if o.children:
            return "+%s*/%d" % (o.name, o.level + BOTTLENECK_LEVEL_INC)
        if 'sibling' in o.__dict__ and o.sibling:
            return "+%s^" % full_name(o)
        return None
    printer = runner.printer
    children = [gen_bn(o) for o in printer.bottlenecks]
    measured = set([x.name for x in runner.olist])
    children = [x for x in children if x and x not in measured]
    parents = []
    for b in printer.bottlenecks:
        parents += ["+" + full_name(o) for o in get_parents(b) if o.name not in measured]
    if args.nodes:
        children = [x for x in children if x[1:-1] not in args.nodes]
        parents = [x for x in parents if x[1:] not in args.nodes]
    if children:
        mux = ",+MUX" if not (args.metrics or args.all) and (args.nodes is None or "MUX" not in args.nodes) else ""
        if not args.quiet:
            print("Add%s --nodes '!%s%s' for breakdown." % (
                    "ing" if args.drilldown else "",
                    ",".join(children + parents),
                    mux))
        if args.drilldown:
            if runner.pmu != "cpu" and not args.quiet:
                print("Please make sure workload does not move between core types for drilldown", file=sys.stderr)
            if args.nodes:
                args.nodes += ","
            else:
                args.nodes = ""
            if args.nodes == "" or args.nodes[0] != '!':
                args.nodes = "!" + args.nodes
            args.nodes += ",".join(children) + mux
            return True
    return False

def suggest_desc(runner):
    def nummatch(n):
        return sum([x.name.startswith(n) for x in runner.olist])
    printer = runner.printer
    print("Run toplev --describe %s to get more information on bottleneck%s%s" % (
        " ".join([full_name(x) + "^" if nummatch(x.name) > 1 else x.name + "^" for x in printer.bottlenecks]),
        "s" if len(printer.bottlenecks) > 1 else "",
        (" for " + runner.pmu.replace("cpu_", "")) if runner.pmu and runner.pmu != "cpu" else ""),
        file=sys.stderr)
    if not args.run_sample:
        print_once("Add --run-sample to find locations")

def sysctl(name):
    try:
        with open("/proc/sys/" + name.replace(".","/"), "r") as f:
            val = int(f.readline())
    except IOError:
        return 0
    return val

def update_cpu(args, cpu):
    # check nmi watchdog
    # XXX need to get this state from CSV import
    if sysctl("kernel.nmi_watchdog") != 0 or os.getenv("FORCE_NMI_WATCHDOG"):
        # XXX should probe if nmi watchdog runs on fixed or generic counter
        for j in cpu.counters.keys():
            cpu.counters[j] -= 1 # FIXME
        if not args.quiet and not args.import_:
            print("Consider disabling nmi watchdog to minimize multiplexing", file=sys.stderr)
            print("(echo 0 | sudo tee /proc/sys/kernel/nmi_watchdog or\n echo kernel.nmi_watchdog=0 >> /etc/sysctl.conf ; sysctl -p as root)", file=sys.stderr)

    for j in cpu.counters.keys():
        cpu.counters[j] -= args.reserved_counters

    if cpu.cpu is None:
        sys.exit("Unsupported CPU model %s %d" % (cpu.vendor, cpu.model,))

def get_kernel():
    kv = os.getenv("KERNEL_VERSION")
    if not kv:
        kv = platform.release()
    return kv_to_key(list(map(int, kv.split(".")[:2])))

def check_exclusive(args, kernel_version):
    if args.exclusive:
        if kernel_version < 510:
            sys.exit("--exclusive needs kernel 5.10+")
        global metrics_own_group
        metrics_own_group = False
        global run_l1_parallel
        run_l1_parallel = False

def ht_warning():
    if cpu.ht and not args.quiet:
        print("WARNING: HT enabled", file=sys.stderr)
        print("Measuring multiple processes/threads on the same core may is not reliable.",
                file=sys.stderr)

def setup_metrics(model, pmu):
    fmenv = os.getenv("FORCEMETRICS")
    ectx.force_metrics = fmenv is not None
    if ectx.force_metrics:
        try:
            ectx.metrics_override = True if int(fmenv if fmenv else "0") else False
        except ValueError:
            ectx.metrics_override = False
    if ectx.force_metrics:
        model.topdown_use_fixed = ectx.metrics_override
    else:
        model.topdown_use_fixed = os.path.exists("/sys/bus/event_source/devices/%s/events/topdown-fe-bound" % pmu)
    if args.no_group:
        model.topdown_use_fixed = False
    ectx.core_domains = ectx.core_domains - set(["Slots"])
    if ectx.force_metrics:
        ectx.slots_available = ectx.metrics_override
    else:
        ectx.slots_available = os.path.exists("/sys/bus/event_source/devices/%s/events/slots" % pmu)

def parse_cpu_list(s):
    l = []
    for j in s.split(","):
        m = re.match(r'(\d+)(-\d+)?', j)
        if m is None:
            continue
        if m.group(2):
            for k in range(int(m.group(1)), int(m.group(2)[1:])+1):
                l.append(k)
        else:
            l.append(int(m.group(1)))
    return l

def read_cpus(base):
    with open(base + "/cpus") as cpus:
        return parse_cpu_list(cpus.readline())
    return []

def use_cpu(cpu):
    if args.core:
        return display_core(cpu, True)
    if args.cpu:
        return cpu in parse_cpu_list(args.cpu)
    return True

def get_cpu_list(fn):
    return [k for k in read_cpus(fn) if use_cpu(k)]

def init_runner_list(kernel_version):
    idle_threshold = init_idle_threshold(args)
    runner_list = []
    hybrid_pmus = []
    hybrid_pmus = glob.glob("/sys/bus/event_source/devices/cpu_*")
    if args.force_cpu and args.force_cpu not in hybrid_cpus:
        hybrid_pmus = hybrid_pmus[:1]
    # real hybrid
    if hybrid_pmus and cpu.cpu in hybrid_cpus:
        for j in hybrid_pmus:
            pmuname = os.path.basename(j).replace("cpu_", "")
            if args.cputype and pmuname != args.cputype:
                continue
            cpu_list = get_cpu_list(j)
            if len(cpu_list) == 0:
                continue
            r = Runner(args.level, idle_threshold, kernel_version, pmu=os.path.basename(j))
            runner_list.append(r)
            r.cpu_list = cpu_list
    # hybrid, but faking non hybrid cpu
    elif hybrid_pmus:
        runner_list = [Runner(args.level, idle_threshold, kernel_version,
            pmu= "cpu_atom" if cpu.cpu in atom_hybrid_cpus else "cpu_core")]
        runner_list[0].cpu_list = get_cpu_list("/sys/bus/event_source/devices/cpu_core")
        if len(runner_list[0].cpu_list) == 0:
            sys.exit("cpu_core fallback has no cpus")
    # no hybrid
    else:
        r = Runner(args.level, idle_threshold, kernel_version, pmu="cpu")
        r.cpu_list = []
        runner_list = [r]

    if args.all:
        assert all([ru.max_level <= args.level for ru in runner_list])

    return runner_list

def handle_more_options(args):
    if args.single_thread:
        cpu.ht = False

    if args.quiet:
        if not args.desc:
            args.no_desc = True
        args.no_util = True

def tune_model(model):
    if args.tune_model:
        for t in args.tune_model:
            exec(t)

def init_model(model, runner, pe):
    version = model.version
    model.print_error = pe
    model.check_event = lambda ev: ectx.emap.getevent(ev) is not None
    model.Setup(runner)
    model.num_cores = len(cpu.coreids) # includes sockets
    if cpu.ht:
        model.num_threads = 2

    if "Errata_Whitelist" in model.__dict__:
        ectx.errata_whitelist += model.Errata_Whitelist.split(";")

    if "base_frequency" in model.__dict__:
        model.base_frequency = cpu.freq * 1000

    if "model" in model.__dict__:
        model.model = cpu.modelid

    if "Num_CPUs" in model.__dict__:
        model.Num_CPUs = lambda a, b, c: len(cpu.allcpus)

    if args.fp16:
        if "FP16" in model.__dict__:
            model.FP16 = lambda a, b, c: True
        else:
            sys.exit("--fp16 option but no support in model")

    if args.hbm_only:
        if "HBM_Only" in model.__dict__:
            model.HBM_Only = lambda a, b, c: True
        else:
            sys.exit("--hbm-only option but no support in model")

    tune_model(model)

    return version

def legacy_smt_setup(model):
    global smt_mode
    if args.thread:
        model.ebs_mode = cpu.ht
        return
    model.smt_enabled = cpu.ht
    smt_mode |= cpu.ht

def load_default_retlat():
    global ret_latency
    if ret_latency is None:
        name = cpu.cpu.split("-")[0]
        fn = os.path.dirname(os.path.realpath(__file__)) + ("/%s-retlat.json" % name)
        try:
            ret_latency = json.load(open(fn))["Data"]
        except IOError:
            sys.exit("Cannot find default ret latency file %s\n" % fn +
                     "Please generate with representative workload using genretlat -o %s workload" % fn)

def model_setup(runner, cpuname, pe, kernel_version):
    global smt_mode
    atom_pmu = runner.pmu == "cpu_atom"
    core_pmu = not atom_pmu
    if cpuname == "ivb":
        import ivb_client_ratios
        model = ivb_client_ratios
        legacy_smt_setup(model)
    elif cpuname == "ivt":
        import ivb_server_ratios
        model = ivb_server_ratios
        legacy_smt_setup(model)
    elif cpuname == "snb":
        import snb_client_ratios
        model = snb_client_ratios
        legacy_smt_setup(model)
    elif cpuname == "jkt":
        import jkt_server_ratios
        model = jkt_server_ratios
        legacy_smt_setup(model)
    elif cpuname == "hsw":
        import hsw_client_ratios
        model = hsw_client_ratios
        legacy_smt_setup(model)
    elif cpuname == "hsx":
        import hsx_server_ratios
        model = hsx_server_ratios
        legacy_smt_setup(model)
    elif cpuname == "bdw":
        import bdw_client_ratios
        model = bdw_client_ratios
        legacy_smt_setup(model)
    elif cpuname == "bdx":
        import bdx_server_ratios
        model = bdx_server_ratios
        legacy_smt_setup(model)
    elif cpuname == "skl":
        import skl_client_ratios
        model = skl_client_ratios
        legacy_smt_setup(model)
    elif cpuname == "skx":
        import skx_server_ratios
        model = skx_server_ratios
        legacy_smt_setup(model)
    elif cpuname == "clx":
        import clx_server_ratios
        model = clx_server_ratios
        legacy_smt_setup(model)
    elif cpuname == "icx":
        import icx_server_ratios
        icx_server_ratios.smt_enabled = cpu.ht
        model = icx_server_ratios
        setup_metrics(model, runner.pmu)
        # work around kernel constraint table bug in some kernel versions
        if kernel_version < 510:
            ectx.constraint_fixes["CYCLE_ACTIVITY.STALLS_MEM_ANY"] = "0,1,2,3"
        smt_mode = cpu.ht
    elif cpu.cpu == "spr":
        import spr_server_ratios
        spr_server_ratios.smt_enabled = cpu.ht
        model = spr_server_ratios
        setup_metrics(model, runner.pmu)
        smt_mode = cpu.ht
        if kernel_version < 670: # expect to be fixed in 6.7
            # kernel incorrectly schedules ocr on 0-3 only
            ectx.constraint_patterns.append(("OCR.", "0,1,2,3", ))
    elif cpu.cpu == "sprmax":
        import spr_max_server_ratios
        spr_max_server_ratios.smt_enabled = cpu.ht
        model = spr_max_server_ratios
        setup_metrics(model, runner.pmu)
        smt_mode = cpu.ht
        if kernel_version < 670: # expect to be fixed in 6.7
            # kernel incorrectly schedules ocr on 0-3 only
            ectx.constraint_patterns.append(("OCR.", "0,1,2,3", ))
    elif cpu.cpu == "gnr":
        import gnr_server_ratios
        model = gnr_server_ratios
        setup_metrics(model, runner.pmu)
    elif cpuname == "icl":
        import icl_client_ratios
        icl_client_ratios.smt_enabled = cpu.ht
        model = icl_client_ratios
        setup_metrics(model, runner.pmu)
        # work around kernel constraint table bug in some kernel versions
        if kernel_version < 510:
            ectx.constraint_fixes["CYCLE_ACTIVITY.STALLS_MEM_ANY"] = "0,1,2,3"
        smt_mode = cpu.ht
    elif cpuname == "tgl":
        import icl_client_ratios
        icl_client_ratios.smt_enabled = cpu.ht
        model = icl_client_ratios
        setup_metrics(model, runner.pmu)
        if kernel_version < 510:
            ectx.constraint_fixes["CYCLE_ACTIVITY.STALLS_MEM_ANY"] = "0,1,2,3"
        smt_mode = cpu.ht
    elif (cpuname == "adl" and core_pmu) or cpuname == "adl-glc":
        import adl_glc_ratios
        setup_metrics(adl_glc_ratios, runner.pmu)
        adl_glc_ratios.smt_enabled = cpu.ht
        model = adl_glc_ratios
        smt_mode = cpu.ht
        if kernel_version < 670: # expect to be fixed in 6.7
            # kernel incorrectly schedules ocr on 0-3 only
            ectx.constraint_patterns.append(("OCR.", "0,1,2,3", ))
    elif (cpuname == "adl" and atom_pmu) or cpuname == "adl-grt":
        import adl_grt_ratios
        model = adl_grt_ratios
        model.use_aux = args.aux
    elif (cpuname == "mtl" and core_pmu) or cpuname == "mtl-rwc":
        import mtl_rwc_ratios
        setup_metrics(mtl_rwc_ratios, runner.pmu)
        mtl_rwc_ratios.smt_enabled = cpu.ht
        model = mtl_rwc_ratios
        ectx.constraint_patterns.append(("OCR.", "0,1,2,3", ))
    elif (cpuname == "mtl" and atom_pmu) or cpuname == "mtl-cmt":
        import mtl_cmt_ratios
        model = mtl_cmt_ratios
        model.use_aux = args.aux
    elif cpuname == "srf":
        import srf_ratios
        model = srf_ratios
    # ARL uses LNL models, but own retlat file.
    elif (cpuname in ("lnl", "arl") and core_pmu) or cpuname == "lnl-lnc":
        import lnl_lnc_ratios
        model = lnl_lnc_ratios
        setup_metrics(model, runner.pmu)
    elif (cpuname in ("lnl", "arl") and atom_pmu) or cpuname == "lnl-skt":
        import lnl_skt_ratios
        model = lnl_skt_ratios
        setup_metrics(model, runner.pmu)
    elif cpuname == "slm":
        import slm_ratios
        model = slm_ratios
    elif cpuname == "knl":
        import knl_ratios
        knl_ratios.smt_enabled = smt_mode = cpu.ht
        model = knl_ratios
    elif cpuname == "ehl":
        import ehl_ratios
        model = ehl_ratios
    else:
        if not args.quiet:
            print("Warning: Unknown CPU model number, falling back to simple model")
        ht_warning()
        import simple_ratios
        model = simple_ratios

    return init_model(model, runner, pe)

def runner_emaps(pe, runner_list):
    version = ""
    for runner in runner_list:
        runner.set_ectx()
        if cpu.cpu in atom_hybrid_cpus:
            typ = "Atom"
        elif cpu.cpu in hybrid_cpus and runner.pmu in ("cpu", None):
            typ = "Core"
        else:
            typ = None
        emap = ocperf.find_emap(pmu=runner.pmu if runner.pmu else "cpu", typ=typ)
        if not emap:
            ocperf.ocverbose = True
            ocperf.find_emap()
            sys.exit("Unknown CPU or CPU event map not found (EVENTMAP:%s, model:%d, cpu:%s, typ:%s)" %
                     (os.environ["EVENTMAP"] if "EVENTMAP" in os.environ else "?", cpu.model, cpu.cpu, typ))
        runner.ectx.init_emap(emap)
        runner.printer.init_emap(emap)
        if version:
            version += ", "
        version += model_setup(runner, cpu.cpu, pe, runner.kernel_version)
        runner.clear_ectx()
    return version

def setup_pe():
    pe = lambda x: None
    if args.debug:
        printed_error = set()
        def print_err(x):
            if x not in printed_error:
                print(x)
                printed_error.add(x)
        pe = lambda e: print_err(e)
    return pe

def handle_misc_options(args, version):
    if args.version:
        print("toplev, CPU: %s, TMA version: %s" % (cpu.cpu, version))
        sys.exit(0)

    if args.gen_script:
        args.quiet = True

    if args.subset:
        if not args.import_:
            sys.exit("--subset requires --import mode")
        if args.script_record:
            sys.exit("--subset cannot be used with --script-record. Generate temp file with perf stat report -x\\;")

def handle_cmd(args, runner_list, rest):
    if args.describe:
        args.long_desc = True
        if not rest:
            sys.exit("No nodes to describe")
        for r in runner_list:
            r.list_nodes(None, any_node, rest)
    if args.list_metrics or args.list_all:
        for r in runner_list:
            r.list_nodes("Metrics", lambda obj: obj.metric, rest)
    if args.list_nodes or args.list_all:
        for r in runner_list:
            r.list_nodes("Nodes", lambda obj: not obj.metric, rest)
    if args.list_metric_groups or args.list_all:
        for r in runner_list:
            r.list_metric_groups()
    if args.list_metric_groups or args.list_metrics or args.list_nodes or args.list_all or args.describe:
        if any([x.startswith("-") for x in rest]):
            sys.exit("Unknown arguments for --list*/--describe")
        sys.exit(0)

def has_core_node(runner):
    res = False
    runner.set_ectx()
    for o in runner.olist:
        if core_node(o):
            res = True
            break
    runner.clear_ectx()
    return res

def any_core_node(runner_list):
    for r in runner_list:
        if has_core_node(r):
            return True
    return False

def check_root():
    if not (os.geteuid() == 0 or sysctl("kernel.perf_event_paranoid") == -1) and not args.quiet:
        print("Warning: Needs root or echo -1 > /proc/sys/kernel/perf_event_paranoid",
                file=sys.stderr)

def extra_setup_once(runner, rest):
    if not args.no_util:
        import perf_metrics
        perf_metrics.Setup(runner)

    if args.power and feat.supports_power:
        import power_metrics
        power_metrics.Setup(runner)

    if args.sw:
        import linux_metrics
        linux_metrics.Setup(runner)

    if args.power and feat.supports_power:
        if not args.quiet and not args.import_ and not args.print:
            print("Running with --power. Will measure complete system.")
        if args.single_thread:
            print("--single-thread conflicts with --power")
        check_root()
        rest = add_args(rest, "-a")

    return rest

def extra_setup(runner):
    if args.tsx and cpu.has_tsx and cpu.cpu in tsx_cpus and runner.pmu in ("cpu", "cpu_core"):
        import tsx_metrics
        tsx_metrics.Setup(runner)

    if args.frequency:
        import frequency
        frequency.SetupCPU(runner, cpu)

def runner_extra_init(args, rest, runner_list):
    rest = extra_setup_once(runner_list[0], rest)
    for r in runner_list:
        extra_setup(r)

    if args.nodes:
        check_nodes(runner_list, args.nodes)

    for r in runner_list:
        r.setup_children()

    return rest

def runner_filter(args, rest, runner_list):
    for r in runner_list:
        rest = r.filter_per_core(args.single_thread, rest)
    return rest

def update_smt(args, rest):
    if not smt_mode and not args.single_thread and not args.no_aggr:
        hybrid = cpu.cpu in hybrid_cpus
        multi = output_count()
        if multi > 0:
            rest = add_args(rest, "-a")
        if (multi > 1 or args.per_thread) and not hybrid:
            args.no_aggr = True
        if args.per_socket and multi == 1 and not hybrid:
            rest = add_args(rest, "--per-socket")
        if args.per_core and multi == 1 and not hybrid:
            rest = add_args(rest, "--per-core")
    return rest

def runner_node_filter(runner_list):
    for r in runner_list:
        r.filter_nodes()

def update_smt_mode(runner_list):
    if smt_mode and not os.getenv('FORCEHT'):
        # do not need SMT mode if no objects have Core scope
        if not any_core_node(runner_list):
            return False
    return smt_mode

def check_full_system(args, rest):
    full_system = False
    if not args.single_thread and smt_mode:
        if not args.quiet and not args.import_:
            print("Will measure complete system.")
        if smt_mode:
            if args.cpu:
                print("Warning: --cpu/-C mode with HyperThread must specify all core thread pairs!",
                      file=sys.stderr)
            if args.pid:
                sys.exit("-p/--pid mode not compatible with SMT. Use sleep in global mode.")
        check_root()
        rest = add_args(rest, "-a")
        args.no_aggr = True
        full_system = True
    else:
        full_system = args.no_aggr or "--per-core" in rest or "--per-socket" in rest
    if args.no_aggr:
        rest = add_args(rest, "-A")
    return full_system, rest

output_numcpus = False

def init_perf_output(args, rest, full_system):
    if (args.perf_output or args.perf_summary) and not args.no_csv_header:
        ph = []
        if args.interval:
            ph.append("Timestamp")
        if full_system:
            ph.append("Location")
            if ("--per-socket" in rest or "--per-core" in rest) and not args.no_aggr:
                ph.append("Num-CPUs")
                global output_numcpus
                output_numcpus = True
        ph += ["Value", "Unit", "Event", "Run-Time", "Enabled", "", ""]
        if args.perf_output:
            args.perf_output.write(";".join(ph) + "\n")
        if args.perf_summary:
            args.perf_summary.write(";".join(ph) + "\n")

def setup_cpus(args, rest, cpu, runner_list):
    if args.cpu:
        allcpus = parse_cpu_list(args.cpu)
    else:
        allcpus = cpu.allcpus
    if args.core:
        allowed_threads = [x for x in allcpus if display_core(x, False)]
        allowed_cores = [x for x in allcpus if display_core(x, True)]
        rest = ["-C", ",".join(["%d" % x for x in allowed_cores])] + rest
    else:
        allowed_threads = allcpus

    if len(runner_list) > 1 and args.no_aggr and not runner_list[0].cpu_list: # XXX
        cores = list(sorted(cpu.coreids.keys()))
        part = len(cores)//len(runner_list)
        start = 0
        for r in runner_list:
            r.cpu_list = sorted(flatten([cpu.coreids[x] for x in cores[start:start+part]]))
            start += part
    else:
        for r in runner_list:
            if r.cpu_list:
                r.cpu_list = sorted(list(set(r.cpu_list) & set(allowed_threads)))
            else:
                r.cpu_list = list(allowed_threads)
    return rest

def init_output(args, version):
    if args.json:
        if args.csv:
            sys.exit("Cannot combine --csv with --json")
        if args.columns:
            sys.exit("Cannot combine --columns with --json")
        out = tl_output.OutputJSON(args.output, args.csv, args, version, cpu) # type: tl_output.Output
    elif args.csv:
        if args.columns:
            out = tl_output.OutputColumnsCSV(args.output, args.csv, args, version, cpu)
        else:
            out = tl_output.OutputCSV(args.output, args.csv, args, version, cpu)
    elif args.columns:
        out = tl_output.OutputColumns(args.output, args, version, cpu)
    else:
        out = tl_output.OutputHuman(args.output, args, version, cpu)
    return out

def init_valcsv(out, args):
    if args.valcsv:
        out.valcsv = csv.writer(args.valcsv, lineterminator='\n', delimiter=';')
        if not args.no_csv_header:
            out.valcsv.writerow(("Timestamp", "CPU", "Group", "Event", "Value",
                                 "Perf-event", "Index", "STDDEV", "MULTI", "Nodes"))

# XXX use runner_restart
def runner_first_init(args, runner_list):
    nnodes = 0
    for r in runner_list:
        runner_init(r)
        nnodes += len(r.olist)
    if nnodes == 0:
        sys.exit("No nodes enabled")

    if args.nodes:
        check_nodes(runner_list, args.nodes)

    offset = 0
    for r in runner_list:
        r.set_ectx()
        r.sched.schedule(r.olist)
        r.sched.offset = offset
        offset += len(r.sched.evnum)
        r.clear_ectx()

def suggest(runner):
    printer = runner.printer
    if printer.bottlenecks and not args.quiet:
        suggest_desc(runner)
    if args.level < runner.max_node_level and printer.bottlenecks:
        return suggest_bottlenecks(runner)
    return False

def measure_and_sample(runner_list, count, out, orig_smt_mode, rest, full_system):
    rrest = rest
    while True:
        summary = Summary()
        try:
            if args.no_multiplex and not args.import_:
                ret = execute_no_multiplex(runner_list, out, rrest, summary)
            else:
                ret = execute(runner_list, out, rrest, summary)
        except KeyboardInterrupt:
            ret = 1
        print_summary(summary, out, runner_list, full_system)
        repeat = False
        for runner in runner_list:
            runner.stat.compute_errors()
            repeat |= suggest(runner)
        if (args.show_sample or args.run_sample) and ret == 0:
            for runner in runner_list:
                runner.set_ectx()
                do_sample(runner.printer.sample_obj, rest, count, ret, runner.kernel_version)
                runner.clear_ectx()
        if 100 <= ret <= 200 and repeat:
            print("Perf or workload appears to have failed with error %d. Not drilling down" % ret,
                  file=sys.stderr)
            break
        if count is not None:
            count += 1
        if repeat:
            if not args.quiet:
                print("Rerunning workload", file=sys.stderr)
            offset = 0
            nnodes = 0
            for r in runner_list:
                offset = runner_restart(r, offset)
                nnodes += len(r.olist)
            global smt_mode
            smt_mode = orig_smt_mode
            if smt_mode and not os.getenv('FORCEHT'):
                if not any_core_node(runner_list):
                    smt_mode = False
            # XXX do all checks for incompatible arguments like top level
            if smt_mode and not args.single_thread:
                check_root()
                rrest = add_args(rrest, "-a")
                rrest = add_args(rrest, "-A")
                full_system = True
            if nnodes == 0:
                sys.exit("No nodes enabled")
        else:
            break
    return ret, count, full_system

def report_idle(runner_list):
    ik = set()
    for r in runner_list:
        ik |= r.idle_keys
    if ik and not args.quiet:
        print("Idle CPUs %s may have been hidden. Override with --idle-threshold 100" %
                idle_range_list(ik), file=sys.stderr)

def report_not_supported(runner_list):
    notfound_caches = {}
    for r in runner_list:
        notfound_caches.update(r.ectx.notfound_cache)
    if notfound_caches and any(["not supported" not in x for x in notfound_caches.values()]) and not args.quiet:
        print("Some events not found. Consider running event_download to update event lists", file=sys.stderr)

def measure(out, orig_smt_mode, rest, runner_list, full_system):
    if args.sample_repeat:
        cnt = 1
        for j in range(args.sample_repeat):
            ret, cnt, full_system = measure_and_sample(runner_list, cnt, out, orig_smt_mode,
                                                       rest, full_system)
            if ret:
                break
    else:
        ret, count, full_system = measure_and_sample(runner_list, 0 if args.drilldown else None, out,
                                                     orig_smt_mode, rest, full_system)
    return ret

def idle_range_list(l):
    if all([x.isdigit() for x in l]):
        # adapted from https://stackoverflow.com/questions/2154249/identify-groups-of-continuous-numbers-in-a-list
        def get_range(g):
            group = [x[1] for x in g]
            if len(group) == 1:
                return "%d" % group[0]
            return "%d-%d" % (group[0], group[-1])
        l = [get_range(g) for k, g in groupby(enumerate(sorted([int(x) for x in l])), lambda x: x[0] - x[1])]
    return ",".join(l)

def finish_graph(graphp):
    if args.graph:
        args.output.close()
        graphp.wait()

def main(args, rest, feat, env, cpu):
    pversion = ocperf.PerfVersion()
    handle_parallel(args, env)
    rest = handle_rest(args, rest)
    open_output_files(args)
    update_args2(args)
    graphp = handle_graph(args)
    args.ring_filter = init_ring_filter(args)
    update_args_cpu(args, pversion)
    update_cpu(args, cpu)
    kernel_version = get_kernel()
    check_exclusive(args, kernel_version)
    runner_list = init_runner_list(kernel_version)
    if len(runner_list) == 0:
        sys.exit("No PMUs with matching CPUs found")
    global KEEP_UNREF
    if len(runner_list) > 1 and isinstance(KEEP_UNREF, bool):
        KEEP_UNREF = True # for now -- dummy can get assigned to wrong runner
    if len(runner_list) > 1 and (INAME or FUZZYINPUT):
        sys.exit("INAME and FUZZYINPUT do not support hybrid")
    handle_more_options(args)
    version = runner_emaps(setup_pe(), runner_list)
    handle_misc_options(args, version)
    handle_cmd(args, runner_list, rest)
    rest = runner_extra_init(args, rest, runner_list)
    rest = runner_filter(args, rest, runner_list)
    rest = update_smt(args, rest)
    runner_node_filter(runner_list)
    global smt_mode
    orig_smt_mode = smt_mode
    smt_mode = update_smt_mode(runner_list)
    full_system, rest = check_full_system(args, rest)
    init_perf_output(args, rest, full_system)
    rest = setup_cpus(args, rest, cpu, runner_list)
    if args.pinned:
        run_l1_parallel = True
    out = init_output(args, version)
    init_valcsv(out, args)
    runner_first_init(args, runner_list)
    if args.repl:
        import code
        code.interact(banner='toplev repl', local=locals())
        sys.exit(0)
    ret = measure(out, orig_smt_mode, rest, runner_list, full_system)
    out.print_footer()
    out.flushfiles()
    if args.xlsx and ret == 0:
        ret = do_xlsx(env, args)
    report_idle(runner_list)
    report_not_supported(runner_list)
    finish_graph(graphp)
    sys.exit(ret)

if __name__ == '__main__':
    # these are top level to avoid globals, which break the type checker
    # alternative would be to pass them everywhere, but that would be tedious
    args, rest_ = init_args()
    feat = PerfFeatures(args)
    ectx = EventContextBase() # only for type checker
    # allow tune to override toplevel without global
    if args.tune:
        for t in args.tune:
            exec(t)
    env_ = tl_cpu.Env()
    update_args(args, env_)
    # XXX move into ectx
    cpu = tl_cpu.CPU(known_cpus, nocheck=event_nocheck(), env=env_)
    main(args, rest_, feat, env_, cpu)
