#!/usr/bin/env python
# Copyright (c) 2012-2020, Intel Corporation
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

from __future__ import print_function
import sys, os, re, textwrap, platform, pty, subprocess
import argparse, time, types, csv, copy
import bisect
from fnmatch import fnmatch
from collections import defaultdict, Counter
from itertools import compress, groupby, chain
import itertools
from listutils import cat_unique, dedup, filternot, not_list, append_dict
from objutils import has, safe_ref, map_fields

from tl_stat import ComputeStat, ValStat, deprecated_combine_valstat
import tl_cpu
import tl_output
import ocperf
import event_download
from tl_uval import UVal
from tl_io import flex_open_r, flex_open_w, popentext

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
    ("skl", (94, 78, 142, 158, )),
    ("knl", (87, )),
    ("skx", ((85, 4,), )),
    ("clx", ((85, 5,), (85, 6,), (85, 7,), )),
    ("icl", (126, )),
    ("tgl", (140, )),
)

tsx_cpus = ("hsw", "hsx", "bdw", "skl", "skx", "clx", "icl", "tgl")

non_json_events = set(("dummy",))

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

constraint_fixes = dict()

event_nocheck = False
import_mode = False

errata_whitelist = []

outgroup_events = set(["dummy"])

sched_ignore_events = set([])

nonperf_events = set(["interval-ns", "interval-s", "interval-ms", "mux"])

require_pebs_events = set([])

event_fixes = {
}

core_domains = set(["Slots", "CoreClocks", "CoreMetric"])

FIXED_BASE = 50
METRICS_BASE = 100
SPECIAL_END = 130

limited_counters = {
    "instructions": FIXED_BASE + 0,
    "cycles": FIXED_BASE + 1,
    "ref-cycles": FIXED_BASE + 2,
    "slots": FIXED_BASE + 3,
    "topdown.slots": FIXED_BASE + 3,
    "topdown-fe-bound": METRICS_BASE + 0,
    "topdown-be-bound": METRICS_BASE + 1,
    "topdown-bad-spec": METRICS_BASE + 2,
    "topdown-retiring": METRICS_BASE + 3,
    "cpu/cycles-ct/": 2,
}
limited_set = set(limited_counters.keys())
fixed_events = set([x for x in limited_counters if FIXED_BASE <= limited_counters[x] <= SPECIAL_END])

smt_mode = False

errata_events = dict()
errata_warn_events = dict()

test_mode = os.getenv("TL_TESTER")

perf = os.getenv("PERF")
if not perf:
    perf = "perf"

warned = set()

def warn_once(msg):
    if msg not in warned:
        print(msg, file=sys.stderr)
        warned.add(msg)
    if test_mode:
        assert 0

def debug_print(x):
    if args.debug:
        print(x, file=sys.stderr)

def test_debug_print(x):
    if args.debug or test_mode:
        print(x, file=sys.stderr)

def works(x):
    return os.system(x + " >/dev/null 2>/dev/null") == 0

class PerfFeatures:
    """Adapt to the quirks of various perf versions."""
    def __init__(self, args):
        self.logfd_supported = works(perf + " stat --log-fd 3 3>/dev/null true")
        if not self.logfd_supported:
            sys.exit("perf binary is too old or perf is disabled in /proc/sys/kernel/perf_event_paranoid")
        self.supports_power = (
                not args.no_uncore
                and not args.force_hypervisor
                and works(perf + " stat -e power/energy-cores/ -a true"))
        self.supports_percore = works(perf + " stat --percore-show-thread true")
        # guests don't support offcore response
        if event_nocheck:
            self.supports_ocr = True
            self.has_max_precise = True
            self.max_precise = 3
        else:
            self.supports_ocr = works(perf +
                    " stat -e '{cpu/event=0xb7,umask=1,offcore_rsp=0x123/,instructions}' true")
            self.has_max_precise = os.path.exists("/sys/devices/cpu/caps/max_precise")
            if self.has_max_precise:
                self.max_precise = int(open("/sys/devices/cpu/caps/max_precise").read())

def kv_to_key(v):
    return v[0] * 100 + v[1]

def unsup_event(e, table, min_kernel=None):
    if ":" in e:
        e = e[:e.find(":")]
    for j in table:
        if fnmatch(e, j[0]) and cpu.realcpu in j[1][0]:
            break
    else:
        return False
    v = j[1]
    if v[1] and kv_to_key(kernel_version) < kv_to_key(v[1]):
        if min_kernel:
            min_kernel.append(v[1])
        return True
    if v[2] and kv_to_key(kernel_version) >= kv_to_key(v[2]):
        return False
    return False

def remove_qual(ev):
    return re.sub(r':[ku]', '', re.sub(r'/[ku+]', '/', ev))

def limited_overflow(evlist):
    assigned = Counter([limited_counters[x] for x in evlist if x in limited_counters]).values()
    return any([x > 1 for x in assigned])

limit4_events = set()

# limited to first four counters on ICL+
def limit4_overflow(evlist):
    return sum([x in limit4_events for x in evlist]) > 4

def ismetric(x):
    return x.startswith("topdown-")

resources = ("frontend=", "offcore_rsp=", "ldlat=", "in_tx_cp=", "cycles-ct")

def event_to_resource(ev):
    for j in resources:
        if j in ev:
            return j
    return ""

def resource_split(evlist):
    r = Counter(map(event_to_resource, evlist))
    for j in r.keys():
        if j == "":
            continue
        if j == "offcore_rsp=":
            if r[j] > 2:
                return True
        elif r[j] > 1:
            return True
    return False

def num_generic_counters(evset):
    return len(evset - fixed_events - outgroup_events - sched_ignore_events)

FORCE_SPLIT = 100

# Force metrics into own group
metrics_own_group = True

def needed_counters(evlist):
    evset = set(evlist)
    num = num_generic_counters(evset)

    evlist = list(map(remove_qual, evlist))

    metrics = [ismetric(x) for x in evlist]

    if any(metrics):
        # slots must be first if metrics are present
        if "slots" in evlist and evlist[0] != "slots":
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
    # some fixed could be promoted to generic, but that doesn't work
    # with ref-cycles.
    if limited_overflow(evlist):
        debug_print("split for limited overflow %s " % evlist)
        return FORCE_SPLIT

    if limit4_overflow(evlist):
        debug_print("split for limit4 overflow %s" % evlist)
        return FORCE_SPLIT

    return num

def event_group(evlist):
    evlist = add_filter(evlist)
    l = []
    for is_og, g in groupby(evlist, lambda x: x in outgroup_events):
        if is_og or args.no_group:
            l += g
        else:
            g = list(g)
            e = ",".join(g)
            if needed_counters(g) <= cpu.counters:
                e = "{%s}" % e
                if args.pinned and all([ismetric(x) or x == "slots" for x in g]):
                    e += ":D"
            else:
                # the scheduler should have avoided that
                print("group", e, " does not fit in pmu", file=sys.stderr)
            l.append(e)
    return ",".join(l)

def exe_dir():
    d = os.path.realpath(sys.argv[0])
    d = os.path.dirname(d)
    if d:
        return d
    return "."

p = argparse.ArgumentParser(usage='toplev [options] perf-arguments',
description='''
Estimate on which part of the CPU pipeline a workload bottlenecks using the TopDown model.
The bottlenecks are expressed as a tree with different levels.
Requires a modern Intel CPU.

Examples:
toplev.py -l2 program
measure whole system in level 2 while program is running

toplev.py -l1 --single-thread program
measure single threaded program. system must be idle.

toplev.py -l3 --no-desc -I 100 -x, sleep X
measure whole system for X seconds every 100ms, outputting in CSV format.

toplev.py --all --core C0 taskset -c 0,1 program
Measure program running on core 0 with all nodes and metrics enables
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
g.add_argument('--gen-script', help='Generate script to collect perfmon information for --import later',
               action='store_true')
g.add_argument('--drilldown', help='Automatically rerun to get more details on bottleneck', action='store_true')

g = p.add_argument_group('Measurement filtering')
g.add_argument('--kernel', help='Only measure kernel code', action='store_true')
g.add_argument('--user', help='Only measure user code', action='store_true')
g.add_argument('--cpu', '-C', help=argparse.SUPPRESS)
g.add_argument('--pid', '-p', help=argparse.SUPPRESS)
g.add_argument('--core', help='Limit output to cores. Comma list of Sx-Cx-Tx. All parts optional.')
g.add_argument('--no-aggr', '-A', help='Measure every CPU', action='store_true')

g = p.add_argument_group('Select events')
g.add_argument('--level', '-l', help='Measure upto level N (max 6)',
               type=int, default=1)
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
g.add_argument('--reduced', help='Use reduced server subset of nodes/metrics', action='store_true')
g.add_argument('--metric-group', help='Add (+) or remove (-|^) metric groups of metrics, '
               'comma separated list from --list-metric-groups.', default=None)
g.add_argument('--pinned', help='Run topdown metrics (on ICL+) pinned', action='store_true')

g = p.add_argument_group('Query nodes')
g.add_argument('--list-metrics', help='List all metrics. Can be followed by prefixes to limit',
            action='store_true')
g.add_argument('--list-nodes', help='List all nodes. Can be followed by prefixes to limit',
            action='store_true')
g.add_argument('--list-metric-groups', help='List metric groups.', action='store_true')
g.add_argument('--list-all', help='List every supported node/metric/metricgroup. Can be followed by prefixes to limit',
            action='store_true')
g.add_argument('--describe', help='Print full descriptions for listed node prefixes', action='store_true')

g = p.add_argument_group('Workarounds')
g.add_argument('--no-group', help='Dont use groups', action='store_true')
g.add_argument('--force-events', help='Assume kernel supports all events. May give wrong results.',
               action='store_true')
g.add_argument('--ignore-errata', help='Do not disable events with errata', action='store_true', default=True)
g.add_argument('--handle-errata', help='Disable events with errata', action='store_true')

g = p.add_argument_group('Output')
g.add_argument('--per-core', help='Aggregate output per core', action='store_true')
g.add_argument('--per-socket', help='Aggregate output per socket', action='store_true')
g.add_argument('--per-thread', help='Aggregate output per CPU thread', action='store_true')
g.add_argument('--global', help='Aggregate output for all CPUs', action='store_true', dest='global_')
g.add_argument('--no-desc', help='Do not print event descriptions', action='store_true')
g.add_argument('--desc', help='Force event descriptions', action='store_true')
g.add_argument('--verbose', '-v', help='Print all results even when below threshold or exceeding boundaries. '
               'Note this can result in bogus values, as the TopDown methodology relies on thresholds '
               'to correctly characterize workloads. Values not crossing threshold are marked with <.',
               action='store_true')
g.add_argument('--csv', '-x', help='Enable CSV mode with specified delimeter')
g.add_argument('--output', '-o', help='Set output file')
g.add_argument('--split-output', help='Generate multiple output files, one for each specified '
               'aggregation option (with -o)',
               action='store_true')
g.add_argument('--graph', help='Automatically graph interval output with tl-barplot.py',
               action='store_true')
g.add_argument("--graph-cpu", help="CPU to graph using --graph")
g.add_argument('--title', help='Set title of graph')
g.add_argument('--quiet', help='Avoid unnecessary status output', action='store_true')
g.add_argument('--long-desc', help='Print long descriptions instead of abbreviated ones.',
                action='store_true')
g.add_argument('--columns', help='Print CPU output in multiple columns for each node', action='store_true')
g.add_argument('--summary', help='Print summary at the end. Only useful with -I', action='store_true')
g.add_argument('--no-area', help='Hide area column', action='store_true')
g.add_argument('--perf-output', help='Save perf stat output in specified file')
g.add_argument('--no-perf', help=argparse.SUPPRESS, action='store_true') # noop, for compatibility
g.add_argument('--perf', help='Print perf command line', action='store_true')
g.add_argument('--print', help="Only print perf command line. Don't run", action='store_true')
g.add_argument('--idle-threshold', help="Hide idle CPUs (default <5%% of busiest if not CSV, specify percent)",
               default=None, type=float)

g = p.add_argument_group('Environment')
g.add_argument('--force-cpu', help='Force CPU type', choices=[x[0] for x in known_cpus])
g.add_argument('--force-topology', metavar='findsysoutput', help='Use specified topology file (find /sys/devices)')
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
g.add_argument('--xnormalize', help='Add extra sheets with normalized data in xlsx files', action='store_true')
g.add_argument('--xchart', help='Chart data in xlsx files', action='store_true')
g.add_argument('--xkeep', help='Keep temporary CSV files', action='store_true')

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
p.add_argument('--repl', action='store_true', help=argparse.SUPPRESS) # start python repl after initialization
p.add_argument('--filterquals', help=argparse.SUPPRESS, action='store_true') # remove events not supported by perf
p.add_argument('--tune', nargs='+', help=argparse.SUPPRESS) # override global variables with python expression
p.add_argument('--force-bn', action='append', help=argparse.SUPPRESS) # force bottleneck for testing
args, rest = p.parse_known_args()

if args.idle_threshold:
    idle_threshold = args.idle_threshold / 100.
elif args.csv or args.xlsx: # not for args.graph
    idle_threshold = 0  # avoid breaking programs that rely on the CSV output
else:
    idle_threshold = 0.05

import_mode = args.import_ is not None
event_nocheck = import_mode or args.no_check

feat = PerfFeatures(args)
pversion = ocperf.PerfVersion()

def gen_cpu_name(cpu):
    if cpu == "simple":
        return event_download.get_cpustr()
    for j in known_cpus:
        if cpu == j[0]:
            if isinstance(j[1][0], tuple):
                return "GenuineIntel-6-%02X-%d" % j[1][0]
            else:
                return "GenuineIntel-6-%02X" % j[1][0]
    assert False
    return None

if args.tune:
    for t in args.tune:
        exec(t)

env = tl_cpu.Env()

if args.force_cpu:
    env.forcecpu = args.force_cpu
    cpu = gen_cpu_name(args.force_cpu)
    if not os.getenv("EVENTMAP"):
        os.environ["EVENTMAP"] = cpu
    if not os.getenv("UNCORE"):
        os.environ["UNCORE"] = cpu
if args.force_topology:
    if not os.getenv("TOPOLOGY"):
        os.environ["TOPOLOGY"] = args.force_topology
        ocperf.topology = None # force reread
if args.force_cpuinfo:
    env.cpuinfo = args.force_cpuinfo
if args.force_hypervisor:
    env.hypervisor = True

emap = ocperf.find_emap()
if not emap:
    sys.exit("Unknown CPU or CPU event map not found.")

rest = [x for x in rest if x != "--"]

if args.version:
    print("toplev")
    sys.exit(0)

if args.cpu:
    rest = ["--cpu", args.cpu] + rest
if args.pid:
    rest = ["--pid", args.pid] + rest
if args.csv and len(args.csv) != 1:
    sys.exit("--csv/-x argument can be only a single character")

forced_per_socket = False
forced_per_core = False
if args.xchart:
    args.xnormalize = True
    args.verbose = True
if args.xlsx:
    if args.output:
        sys.exit("-o / --output not allowed with --xlsx")
    if args.valcsv:
        sys.exit("--valcsv not allowed with --xlsx")
    if args.perf_output:
        sys.exit("--perf-output not allowed with --xlsx")
    if args.csv:
        sys.exit("-c / --csv not allowed with --xlsx")
    if not args.xlsx.endswith(".xlsx"):
        sys.exit("--xlsx must end in .xlsx")
    if not args.interval:
        args.interval = 1000
    args.csv = ','
    xlsx_base = re.sub(r'\.xlsx$', '.csv', args.xlsx)
    args.valcsv = re.sub(r'\.csv$', '-valcsv.csv', xlsx_base)
    args.output = xlsx_base
    args.summary = True
    args.perf_output = re.sub(r'\.csv$', '-perf.csv', xlsx_base)
    if not args.single_thread:
        args.per_thread = True
        args.split_output = True
        if args.per_socket:
            forced_per_socket = True
        if args.per_core:
            forced_per_core = True
        args.per_socket = True
        args.per_core = True
        args.no_aggr = True
        args.global_ = True

if args.no_aggr:
    rest = ["-A"] + rest

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

if args.all:
    args.tsx = True
    args.power = True
    args.sw = True
    args.metrics = True
    args.frequency = True
    args.level = 6

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
    graphp = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, **popentext)
    args.output = graphp.stdin

if args.sample_repeat:
    args.run_sample = True

if args.handle_errata:
    args.ignore_errata = False

ring_filter = ""
if args.kernel:
    ring_filter = 'k'
if args.user:
    ring_filter = 'u'
if args.user and args.kernel:
    ring_filter = None

MAX_ERROR = 0.05

def check_ratio(l):
    if args.verbose:
        return True
    return 0 - MAX_ERROR < l < 1 + MAX_ERROR

cpu = tl_cpu.CPU(known_cpus, nocheck=event_nocheck, env=env)

if cpu.pmu_name and cpu.pmu_name.startswith("generic") and not args.quiet:
    print("warning: kernel is in architectural mode and might mismeasure events", file=sys.stderr)
    print("Consider a kernel update. See https://github.com/andikleen/pmu-tools/wiki/toplev-kernel-support", file=sys.stderr)

if args.xlsx and not forced_per_socket and cpu.sockets == 1:
    args.per_socket = False
if args.xlsx and not forced_per_core and cpu.threads == 1:
    args.per_core = False

if cpu.hypervisor:
    feat.max_precise = 0
    feat.has_max_precise = True
    feat.supports_ocr = False

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
    print(" ".join(l))
    sys.stdout.flush()

def gen_script(r):
    print("#!/bin/sh")
    print("# Generated from 'toplev " + " ".join(sys.argv) + " for CPU " + cpu.cpu)
    print("# Show output with toplev.py " +
          " ".join([x for x in sys.argv if x != "--gen-script"]) +
          " --import toplev_perf.csv --force-cpuinfo toplev_cpuinfo --force-topology toplev_topology --force-cpu " +
          cpu.cpu)
    print("# print until Ctrl-C or run with command on command line (e.g. -a -I 1000 sleep 10)")
    print("# override output file names with OUT=... script (default toplev_...)")
    print("# enable compression with POSTFIX=.xz script")
    print("OUT=${OUT:-toplev}")
    print("find /sys/devices > ${OUT}_topology")
    print("cat /proc/cpuinfo > ${OUT}_cpuinfo")
    i = r.index('--log-fd')
    r[i] = "-o"
    r[i + 1] = "${OUT}_perf.csv${POSTFIX}"
    i = r.index('-x;')
    r[i] = '-x\\;'
    i = r.index('-e')
    r[i+1] = "'" + r[i+1] + "'"
    print(" ".join(r + ['"$@"']))

class PerfRun:
    """Control a perf subprocess."""
    def execute(self, r):
        if import_mode:
            self.perf = None
            return flex_open_r(args.import_)

        if args.gen_script:
            gen_script(r)
            sys.exit(0)

        outp, inp = pty.openpty()
        if 'set_inheritable' in os.__dict__:
            os.set_inheritable(inp, 1)
        n = r.index("--log-fd")
        r[n + 1] = "%d" % (inp)
        print_perf(r)
        if args.print:
            sys.exit(0)
        self.perf = subprocess.Popen(r, close_fds=False)
        os.close(inp)
        return os.fdopen(outp, 'r')

    def wait(self):
        ret = 0
        if self.perf:
            ret = self.perf.wait()
        return ret

def separator(x):
    if x.startswith("cpu"):
        return ""
    return ":"

def add_filter_event(e):
    if "/" in e and not e.startswith("cpu"):
        return e
    if ":" in e:
        s = ""
    else:
        s = separator(e)
    if not e.endswith(s + ring_filter):
        return e + s + ring_filter
    return e

def add_filter(s):
    if ring_filter:
        s = list(map(add_filter_event, s))
    return s

def initialize_event(name, i, e):
    if "." in name or "_" in name:
        emap.update_event(e.output(noname=True), e)
        if (e.counter not in cpu.standard_counters and not name.startswith("UNC_")):
            if e.counter.startswith("Fixed"):
                limited_counters[i] = int(e.counter.split()[2]) + FIXED_BASE
                fixed_events.add(i)
            else:
                # for now use the first counter only to simplify
                # the assignment. This is sufficient for current
                # CPUs
                limited_counters[i] = int(e.counter.split(",")[0])
            limited_set.add(i)
        if e.name.upper() in constraint_fixes:
            e.counter = constraint_fixes[e.name.upper()]
        if e.counter == cpu.limit4_counters:
            limit4_events.add(i)
        if e.errata:
            if e.errata not in errata_whitelist:
                errata_events[name] = e.errata
            else:
                errata_warn_events[name] = e.errata
        if ('pebs' in e.__dict__ and e.pebs == 2) or name.startswith("FRONTEND_"):
            require_pebs_events.add(name)
    else:
        non_json_events.add(i)
    if not i.startswith("cpu/") and i not in fixed_events:
        if not i.startswith("uncore"):
            valid_events.add_event(i)
        if i.startswith("msr/"):
            sched_ignore_events.add(i)
        else:
            outgroup_events.add(add_filter_event(i))

notfound_cache = dict()

def raw_event(i, name="", period=False, nopebs=True, initialize=False):
    e = None
    orig_i = i
    if "." in i or "_" in i:
        if re.match(r'^(OCR|OFFCORE_RESPONSE).*', i) and not feat.supports_ocr:
            if not args.quiet:
                print("%s not supported in guest" % i, file=sys.stderr)
            return "dummy"
        if not cpu.ht:
            i = i.replace(":percore", "")
        extramsg = []
        e = emap.getevent(i, nocheck=event_nocheck, extramsg=extramsg)
        if e is None:
            if i in event_fixes:
                e = emap.getevent(event_fixes[i], nocheck=event_nocheck)
        if e is None:
            if i not in notfound_cache:
                notfound_cache[i] = extramsg[0]
                print("%s %s" % (i, extramsg[0]), file=sys.stderr)
            return "dummy"
        if re.match("^[0-9]", name):
            name = "T" + name
        if args.filterquals:
            e.filter_qual()
        if nopebs and 'extra' in e.__dict__:
            e.extra = e.extra.replace("p", "")
        i = e.output(noname=True, name=name, period=period, noexplode=True)
    if initialize:
        initialize_event(orig_i, i, e)
    return i

# generate list of converted raw events from events string
def raw_events(evlist, initialize=False):
    return [raw_event(x, initialize=initialize) for x in evlist]

def mark_fixed(s):
    r = raw_event(s)
    if r in fixed_events:
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
    return [perf, "stat", "-x;", "--log-fd", "X"] + add + ["-e", evstr] + rest

def setup_perf(evstr, rest):
    prun = PerfRun()
    inf = prun.execute(perf_args(evstr, rest))
    return inf, prun

class Stat:
    def __init__(self):
        self.total = 0
        self.errors = Counter()

def print_not(a, count, msg, j):
    print(("%s %s %s %.2f%% in %d measurements"
                % (emap.getperf(j), j, msg,
                    100.0 * (float(count) / float(a.total)),
                    a.total)),
                file=sys.stderr)

# XXX need to get real ratios from perf
def print_account(ad):
    total = Counter()
    for j in ad:
        a = ad[j]
        for e in a.errors:
            if args.stats:
                print_not(a, a.errors[e], e, j)
            total[e] += 1
    if sum(total.values()) > 0 and not args.quiet:
        print(", ".join(["%d events %s" % (num, e) for e, num in total.items()]),
                file=sys.stderr)

class ValidEvents:
    def update(self):
        self.string = "|".join(self.valid_events)

    def __init__(self):
        self.valid_events = [r"cpu/.*?/", "uncore.*?/.*?/", "ref-cycles", "power.*",
                             r"msr.*", "emulation-faults",
                             r"r[0-9a-fA-F]+", "cycles", "instructions", "dummy",
                             "slots", r"topdown-(fe-bound|be-bound|retiring|bad-spec)"]
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
    return re.match(valid_events.string, l[n])

def is_number(n):
    return re.match(r'\d+', n) is not None

def set_interval(env, d):
    env['interval-ns'] = d * 1e9
    env['interval-ms'] = d * 1e3
    env['interval-s'] = d

def key_to_coreid(k):
    x = cpu.cputocore[int(k)]
    return x[0] * 1000 + x[1]

def key_to_socketid(k):
    return cpu.cputocore[int(k)][0]

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
        if not m:
            sys.exit("Bad core match %s" % match)

        def matching(name, mapping):
            return mapping[cpunum] == int(m.group(name)[1:])
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

def display_keys(runner, keys, mode):
    if mode == OUTPUT_GLOBAL:
        return ("",)
    if len(keys) > 1 and smt_mode:
        if mode == OUTPUT_SOCKET:
            all_cpus = list(set(map(socket_fmt, runner.allowed_threads)))
        else:
            cores = [key_to_coreid(x) for x in keys if int(x) in runner.allowed_threads]
            if mode != OUTPUT_CORE:
                threads = list(map(thread_fmt, runner.allowed_threads))
            else:
                threads = []
            all_cpus = list(set(map(core_fmt, cores))) + threads
    else:
        all_cpus = list(keys)
    if any(map(package_node, runner.olist)):
        all_cpus += ["S%d" % x for x in range(cpu.sockets)]
    return all_cpus

def verify_rev(rev, cpus):
    for k in cpus:
        for ind, o in enumerate(rev[k]):
            assert o == rev[cpus[0]][ind]
        assert len(rev[k]) == len(rev[cpus[0]])

IDLE_MARKER_THRESHOLD = 0.05

def find_idle_keys(res, rev, idle_thresh):
    cycles = { k: max([0] + [val for val, ev in zip(res[k], rev[k])
                    if ev in ("cycles", "cpu/event=0x3c,umask=0x0,any=1/")])
               for k in res.keys() }
    if not cycles:
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

def print_keys(runner, res, rev, valstats, out, interval, env, mode):
    def filtered(j):
        return j != "" and is_number(j) and int(j) not in runner.allowed_threads

    idle_keys = find_idle_keys(res, rev, runner.idle_threshold)
    idle_mark_keys = find_idle_keys(res, rev, IDLE_MARKER_THRESHOLD)
    hidden_keys = set()
    stat = runner.stat
    keys = sorted(res.keys(), key=num_key)
    out.set_cpus(display_keys(runner, keys, mode))
    runner.numprint = 0
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
            combined_st = [deprecated_combine_valstat(z)
                  for z in zip(*[valstats[x] for x in cpus])]
            env['num_merged'] = len(cpus)

            if mode in (OUTPUT_CORE,OUTPUT_SOCKET,OUTPUT_GLOBAL):
                merged_res = combined_res
                merged_st = combined_st
            else:
                merged_res = res[j]
                merged_st = valstats[j]

            # may need to repeat to get stable threshold values
            # in case of mutual dependencies between SMT and non SMT
            # but don't loop forever (?)
            used_stat = stat
            for _ in range(3):
                changed = runner.compute(merged_res, rev[j], merged_st, env, thread_node, used_stat)
                if core not in printed_cores:
                    verify_rev(rev, cpus)
                    changed += runner.compute(combined_res, rev[cpus[0]], combined_st, env, core_node, used_stat)
                if changed == 0:
                    break
                used_stat = None

            # find bottleneck
            bn = find_bn(runner.olist, not_package_node)

            if mode == OUTPUT_GLOBAL:
                runner.print_res(out, interval, "", not_package_node, bn)
                break
            if mode == OUTPUT_SOCKET:
                runner.print_res(out, interval, socket_fmt(int(j)), not_package_node, bn,
                                 idle_socket(sid, idle_mark_keys))
                printed_sockets.add(sid)
                continue
            if mode == OUTPUT_THREAD:
                runner.compute(res[j], rev[j], valstats[j], env, package_node, stat)
                runner.print_res(out, interval, thread_fmt(int(j)), any_node, bn, j in idle_mark_keys)
                continue

            # per core or mixed core/thread mode

            # print the SMT aware nodes
            if core not in printed_cores:
                runner.print_res(out, interval, core_fmt(core), core_node, bn,
                        idle_core(core, idle_mark_keys))
                printed_cores.add(core)

            # print the non SMT nodes
            if mode == OUTPUT_CORE:
                fmt = core_fmt(core)
                idle = idle_core(core, idle_mark_keys)
            else:
                fmt = thread_fmt(int(j))
                idle = j in idle_mark_keys
            runner.print_res(out, interval, fmt, thread_node, bn, idle)
    elif mode != OUTPUT_GLOBAL:
        env['num_merged'] = 1
        for j in keys:
            if filtered(j):
                continue
            if j in idle_keys:
                hidden_keys.add(j)
                continue
            runner.reset_thresh()
            runner.compute(res[j], rev[j], valstats[j], env, not_package_node, stat)
            bn = find_bn(runner.olist, not_package_node)
            runner.print_res(out, interval, j, not_package_node, bn, j in idle_mark_keys)
    if mode == OUTPUT_GLOBAL:
        env['num_merged'] = 1
        cpus = [x for x in keys if not filtered(x)]
        if cpus:
            combined_res = [sum([res[j][i] for j in cpus])
                            for i in range(len(res[cpus[0]]))]
            combined_st = [deprecated_combine_valstat([valstats[j][i] for j in cpus])
                           for i in range(len(valstats[cpus[0]]))]
            if smt_mode:
                nodeselect = package_node
            else:
                nodeselect = any_node
            runner.reset_thresh()
            runner.compute(combined_res, rev[cpus[0]] if len(cpus) > 0 else [],
                           combined_st, env, nodeselect, stat)
            runner.print_res(out, interval, "all", nodeselect, None, False)
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
            runner.compute(res[j], rev[j], valstats[j], env, package_node, stat)
            runner.print_res(out, interval, jname, package_node, None, j in idle_mark_keys)
    # no bottlenecks from package nodes for now
    out.flush()
    stat.referenced_check(res, runner.sched.evnum)
    stat.compute_errors()
    runner.idle_keys |= hidden_keys
    if runner.numprint == 0 and not args.quiet and runner.olist:
        print("No node crossed threshold", file=sys.stderr)

def print_and_split_keys(runner, res, rev, valstats, out, interval, env):
    if args.per_core + args.per_thread + args.per_socket + args.global_ > 1:
        if args.per_thread:
            out.remark("Per thread")
            out.reset("thread")
            print_keys(runner, res, rev, valstats, out, interval, env, OUTPUT_THREAD)
        if args.per_core:
            out.remark("Per core")
            out.reset("core")
            print_keys(runner, res, rev, valstats, out, interval, env, OUTPUT_CORE)
        if args.per_socket:
            out.remark("Per socket")
            out.reset("socket")
            print_keys(runner, res, rev, valstats, out, interval, env, OUTPUT_SOCKET)
        if args.global_:
            out.remark("Global")
            out.reset("global")
            print_keys(runner, res, rev, valstats, out, interval, env, OUTPUT_GLOBAL)
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
        print_keys(runner, res, rev, valstats, out, interval, env, mode)

def print_and_sum_keys(runner, res, rev, valstats, out, interval, env):
    if args.interval and interval is None:
        interval = float('nan')
    if runner.summary:
        runner.summary.add(res, rev, valstats, env)
    print_and_split_keys(runner, res, rev, valstats, out, interval, env)

def print_summary(runner, out):
    if not args.summary:
        return
    print_and_split_keys(runner, runner.summary.res, runner.summary.rev,
                         runner.summary.valstats, out,
                         float('nan'), runner.summary.env)

def is_outgroup(x):
    return set(x) - outgroup_events == set()

class SaveContext:
    """Save (some) environment context, in this case stdin seek offset to make < file work
       when we reexecute the workload multiple times."""
    def __init__(self):
        try:
            self.startoffset = sys.stdin.tell()
        except OSError:
            self.startoffset = None
        except IOError:
            self.startoffset = None

    def restore(self):
        if self.startoffset is not None:
            sys.stdin.seek(self.startoffset)

def execute_no_multiplex(runner, out, rest):
    results = []
    groups = [g.evnum for g in runner.sched.evgroups]
    num_runs = len(groups) - sum([g.outgroup for g in runner.sched.evgroups])
    outg = []
    n = 0
    ctx = SaveContext()
    # runs could be further reduced by tweaking
    # the scheduler to avoid any duplicated events
    for g, gg in zip(groups, runner.sched.evgroups):
        if gg.outgroup:
            outg.append(g)
            continue
        print("RUN #%d of %d: %s" % (n, num_runs, " ".join([quote(o.name) for o in gg.objl])))
        lresults = results if n == 0 else []
        for ret, res, rev, interval, valstats, env in do_execute(runner, outg + [g], out, rest):
            lresults.append([ret, res, rev, interval, valstats, env])
        if n > 0:
            for r, lr in zip(results, lresults):
                r[0] = lr[0]
                # use interval of first
                for j in (1, 2, 4, 5):
                    append_dict(r[j], lr[j])
        ctx.restore()
        outg = []
        n += 1
    assert num_runs == n
    for ret, res, rev, interval, valstats, env in results:
        print_and_sum_keys(runner, res, rev, valstats, out, interval, env)
    return ret

def execute(runner, out, rest):
    events = [x.evnum for x in runner.sched.evgroups if len(x.evnum) > 0]
    ctx = SaveContext()
    for ret, res, rev, interval, valstats, env in do_execute(runner, events, out, rest):
        print_and_sum_keys(runner, res, rev, valstats, out, interval, env)
    ctx.restore()
    return ret

def find_group(num):
    groups = runner.sched.evgroups
    g = groups[bisect.bisect_right(groups, GroupCmp(num)) - 1]
    assert g.base <= num < g.base + len(g.evnum)
    return g

def dump_raw(interval, title, event, val, index, stddev, multiplex):
    ename = event_rmap(event)
    g = find_group(index)
    nodes = " ".join([o.name.replace(" ", "_") for o in g.objl if event in o.evnum])
    if args.raw:
        print("raw", title, "event", event, "val", val, "ename", ename, "index",
                index, "group", g.num, "nodes", nodes)
    if args.valcsv:
        runner.valcsv.writerow((interval, title, g.num, ename, val, event, index,
                                stddev, multiplex, nodes))
perf_fields = [
    r"[0-9.]+",
    r"<.*?>",
    r"S\d+-C\d+?",
    r"S\d+",
    r"raw 0x[0-9a-f]+",
    r"Joules",
    ""]

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

def do_execute(runner, events, out, rest):
    res = defaultdict(list)
    rev = defaultdict(list)
    valstats = defaultdict(list)
    env = dict()
    evstr = group_join(events)
    account = defaultdict(Stat)
    inf, prun = setup_perf(evstr, rest)
    prev_interval = 0.0
    interval = None
    start = time.time()
    init_res = copy.deepcopy(res)
    while True:
        try:
            l = inf.readline()
            if not l:
                break
            if args.perf_output:
                args.perf_output.write(l)

            # some perf versions break CSV output lines incorrectly for power events
            if l.endswith("Joules"):
                l2 = inf.readline()
                l = l + l2.strip()
            if l.startswith("#") or len(l) == 0:
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
            continue
        if args.interval:
            m = re.match(r"\s+([0-9.]{9,});(.*)", l)
            if m:
                interval = float(m.group(1))
                l = m.group(2)
                if interval != prev_interval:
                    if res:
                        set_interval(env, interval - prev_interval)
                        yield 0, res, rev, interval, valstats, env
                        res = defaultdict(list)
                        rev = defaultdict(list)
                        valstats = defaultdict(list)
                        env = dict()
                    prev_interval = interval
            elif not l[:1].isspace():
                # these are likely bogus summary lines printed by v5.8 perf stat
                # just ignore
                continue

        n = l.split(";")

        # filter out the empty unit field added by 3.14
        n = list(filter(lambda x: x not in ('', 'Joules'), n))

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
            print("unparseable perf output", file=sys.stderr)
            sys.stdout.write(l)
            continue

        # dummy event used as separator to avoid merging problems
        if event == "emulation-faults":
            continue

        title = title.replace("CPU", "")
        # code later relies on stripping ku flags
        event = event.replace("/k", "/").replace("/u", "/")

        multiplex = float('nan')
        event = event.rstrip()
        if re.match(r"\s*[0-9.]+", count):
            val = float(count)
        elif re.match(r"\s*<", count):
            account[event].errors[count.replace("<","").replace(">","")] += 1
            multiplex = 0.
            val = 0
        else:
            print("unparseable perf count", file=sys.stderr)
            sys.stdout.write(l)
            continue

        # post fixes:
        # ,xxx%    -> -rXXX stddev
        stddev = 0.
        if len(n) > off and n[off].endswith("%"):
            stddev = (float(n[off].replace("%", "").replace(",", ".")) / 100.) * val
            off += 1

        # ,xxx,yyy -> multiplexing in newer perf
        if len(n) > off + 1:
            multiplex = float(n[off + 1].replace(",", "."))
            off += 2

        st = ValStat(stddev=stddev, multiplex=multiplex)

        account[event].total += 1

        def dup_val(l, val, event, st):
            for j in l:
                res["%d" % (j)].append(val)
                rev["%d" % (j)].append(event)
                valstats["%d" % (j)].append(st)

        # power/uncore events are only output once for every socket. duplicate them
        # to all cpus in the socket to make the result lists match
        # unless we use -A ??
        # also -C xxx causes them to be duplicated too, unless single thread
        if (re.match(r'power|uncore', event) and
                title != "" and is_number(title) and
                (not (args.core and not args.single_thread))):
            cpunum = int(title)
            socket = cpu.cputosocket[cpunum]
            dup_val(cpu.sockettocpus[socket], val, event, st)
        # per core events are only output once. duplicate them.
        elif re.match(r'(S\d+-)?(D\d+-)?C\d+', title) and not args.single_thread:
            m = re.match(r'(?:S(\d+)-)?(?:D(\d+)-)?C(\d+)', title)
            # ignore die for now (XXX)
            socket, core = int(m.group(1)), int(m.group(3))
            dup_val(cpu.coreids[(socket, core)], val, event, st)
        else:
            res[title].append(val)
            rev[title].append(event)
            valstats[title].append(st)

        if args.raw or args.valcsv:
            dump_raw(interval if args.interval else "",
                     title,
                     event,
                     val,
                     len(res[title]) - len(init_res[title]) - 1,
                     stddev, multiplex)
    inf.close()
    if 'interval-s' not in env:
        set_interval(env, time.time() - start)
    ret = prun.wait()
    print_account(account)
    yield ret, res, rev, interval, valstats, env

# dummy arithmetic type without any errors, for collecting
# the events from the model. Otherwise divisions by zero cause
# early exits
class DummyArith:
    def __sub__(self, o):
        return self
    def __add__(self, o):
        return self
    def __mul__(self, o):
        return self
    def __div__(self, o):
        return self
    def __truediv__(self, o):
        return self
    def __rsub__(self, o):
        return self
    def __radd__(self, o):
        return self
    def __rmul__(self, o):
        return self
    def __rdiv__(self, o):
        return self
    def __rtruediv__(self, o):
        return self
    def __lt__(self, o):
        return True
    def __eq__(self, o):
        return True
    def __ne__(self, o):
        return True
    def __ge__(self, o):
        return True
    def __gt__(self, o):
        return True
    def __or__(self, o):
        return self
    def __and__(self, o):
        return self
    def __min__(self, o):
        return self
    def __max__(self, o):
        return self

run_l1_parallel = False # disabled for now until we can fix the perf scheduler
slots_available = False

def adjust_ev(ev, level):
    # use the programmable slots for non L1 so that level 1
    # can (mostly) run in parallel with other groups.
    # this also helps for old or non ICL kernels
    if ev == "TOPDOWN.SLOTS" and ((run_l1_parallel and level != 1) or not slots_available):
        ev = "TOPDOWN.SLOTS_P"
    return ev

def ev_append(ev, level, obj):
    if isinstance(ev, types.LambdaType):
        return ev(lambda ev, level: ev_append(ev, level, obj), level)
    if ev in nonperf_events:
        return DummyArith()
    ev = adjust_ev(ev, level)

    key = (ev, level, obj.name)
    if key not in obj.evlevels:
        if ev == "TOPDOWN.SLOTS" or ev.startswith("PERF_METRICS."):
            ind = [x[1] == level for x in obj.evlevels]
            ins = ind.index(True) if any(ind) else 0
            obj.evlevels.insert(ins + (0 if ev == "TOPDOWN.SLOTS" else 1), key)
        else:
            obj.evlevels.append(key)
        if safe_ref(obj, 'nogroup'):
            outgroup_events.add(ev.lower())
    return DummyArith()

def canon_event(e):
    m = re.match(r"(.*?):(.*)", e)
    if m:
        e = m.group(1)
    return e.lower()

fixes = dict(zip(event_fixes.values(), event_fixes.keys()))

def do_event_rmap(e):
    n = canon_event(emap.getperf(e))
    if emap.getevent(n, nocheck=event_nocheck):
        return n
    if n.upper() in fixes:
        n = fixes[n.upper()].lower()
        if n:
            return n
    if e in non_json_events:
        return e
    debug_print("rmap: cannot find %s, using dummy" % e)
    return "dummy"

rmap_cache = dict()

def event_rmap(e):
    if e in rmap_cache:
        return rmap_cache[e]
    n = do_event_rmap(e)
    rmap_cache[e] = n
    return n

# compare events to handle name aliases
def compare_event(aname, bname):
    a = emap.getevent(aname, nocheck=event_nocheck)
    if a is None:
        return False
    b = emap.getevent(bname, nocheck=event_nocheck)
    if b is None:
        return False
    fields = ('val','event','cmask','edge','inv')
    return map_fields(a, fields) == map_fields(b, fields)

def lookup_res(res, rev, ev, obj, env, level, referenced, cpuoff, st):
    """get measurement result and wrap in UVal"""

    ev = adjust_ev(ev, level)

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
                  lookup_res(res, rev, ev, obj, env, level, referenced, off, st), level)
                  for off in range(env['num_merged'])])

    index = obj.res_map[(ev, level, obj.name)]
    referenced.add(index)
    #print((ev, level, obj.name), "->", index)
    if not args.fast:
        try:
            r = rev[index]
        except IndexError:
            warn_once("Not enough lines in perf output for rev (%d vs %d for %s)" %
                    (index, len(rev), obj.name))
            return 0
        rmap_ev = event_rmap(r).lower()
        ev = ev.lower()
        assert (rmap_ev == canon_event(ev).replace("/k", "/") or
                compare_event(rmap_ev, ev) or
                (ev in event_fixes and canon_event(event_fixes[ev]) == rmap_ev) or
                rmap_ev == "dummy")

    try:
        vv = res[index]
    except IndexError:
        warn_once("Not enough lines in perf output for res (%d vs %d for %s)" %
                (index, len(res), obj.name))
        return 0.0
    if isinstance(vv, tuple):
        if cpuoff == -1:
            vv = sum(vv)
        else:
            try:
                vv = vv[cpuoff]
            except IndexError:
                warn_once("warning: Partial CPU thread data from perf for %s" %
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
def sample_event(e):
    ev = emap.getevent(e, nocheck=event_nocheck)
    if not ev:
        raise BadEvent(e)
    postfix = ring_filter
    if ev.pebs and int(ev.pebs):
        postfix = "pp"
    if postfix:
        postfix = ":" + postfix
    return ev.name + postfix

def sample_desc(s):
    try:
        return " ".join([sample_event(x) for x in s])
    except BadEvent:
        #return "Unknown sample event %s" % (e.event)
        return ""

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
    return safe_ref(obj, 'domain') in core_domains

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

# only check direct children, the rest are handled recursively
def children_over(l, obj):
    n = [o.thresh for o in l if 'parent' in o.__dict__ and o.parent == obj]
    return any(n)

def obj_desc_runtime(obj, rest, sep="\n\t"):
    # hide description if children are also printed
    if children_over(rest, obj):
        desc = ""
    else:
        desc = obj_desc(obj)
    if 'htoff' in obj.__dict__ and obj.htoff and obj.thresh and cpu.ht and not args.single_thread:
        desc += """
Warning: Hyper Threading may lead to incorrect measurements for this node.
Suggest to re-measure with HT off (run cputop.py "thread == 1" offline | sh)."""
    return desc

def node_filter(obj, default, sibmatch):
    if args.nodes:
        fname = full_name(obj)
        name = obj.name

        def _match(m):
            return (fnmatch(name, m) or
                    fnmatch(fname, m) or
                    fnmatch(fname, "*" + m))

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

        nodes = args.nodes
        if nodes[0] == '!':
            default = False
            nodes = nodes[1:]

        for j in nodes.split(","):
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
                return True
            if has_siblings(j, obj):
                for sib in obj.sibling:
                    fname = full_name(sib)
                    name = sib.name
                    if match(j[i:], False):
                        sibmatch.add(obj)
                        return True
    return default

SIB_THRESH = 0.05

def _find_bn(bn, level):
    siblings = sorted([x for x in bn if x.level - 1 == level], key=lambda x: x.val, reverse=True)
    if len(siblings) == 0:
        return None
    # ambigious
    if level > 0 and len(siblings) > 1 and siblings[0].val - siblings[1].val <= SIB_THRESH:
        return None
    n = _find_bn([x for x in bn if full_name(x).startswith(full_name(siblings[0]))], level + 1)
    if n is None:
        return siblings[0]
    return n

def find_bn(olist, match):
    bn = [o for o in olist if match(o) and not o.metric]
    if args.force_bn:
        bn = sorted([o for o in olist if o.name in args.force_bn], key=lambda x: x.level, reverse=True)
        if bn:
            return bn[0]
    bn = [o for o in olist if o.thresh]
    if not bn:
        return None
    return _find_bn(bn, 0)

pmu_does_not_exist = set()

# XXX check if PMU can be accessed from current user
def missing_pmu(e):
    if event_nocheck:
        return False
    m = re.match(r"([a-z0-9_]+)/", e)
    if m:
        pmu = m.group(1)
        if pmu in pmu_does_not_exist:
            return True
        if not os.path.isdir("/sys/devices/%s" % pmu):
            pmu_does_not_exist.add(pmu)
            return True
    return False

def query_errata(obj, errata_events, errata_nodes, errata_names):
    errata = [errata_events[x] for x in obj.evlist if x in errata_events]
    if any(errata):
        errata_nodes.add(obj)
        errata_names |= set(errata)

def olist_by_metricgroup(l, mg):
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
            for g in obj.metricgroup:
                for j in mg[g]:
                    if j in valid:
                        add(j)
        add(obj)
    return ml

def node_unit(obj):
    return (" " + obj_domain(obj)) if has(obj, 'domain') else ""

def node_below(obj):
    return not obj.thresh

class Summary:
    """Accumulate counts for summary."""
    def __init__(self):
        self.res = defaultdict(list)
        self.rev = defaultdict(list)
        self.env = Counter()
        self.valstats = defaultdict(list)

    def add(self, res, rev, valstats, env):
        # assume perf always outputs the same
        if self.rev:
            assert rev == self.rev
        for j in res.keys():
            if len(self.res[j]) == 0:
                self.res[j] = res[j]
            else:
                self.res[j] = [a+b for a, b in zip(self.res[j], res[j])]
        self.rev = rev
        for j in valstats.keys():
            self.valstats[j] = self.valstats[j] + valstats[j]
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

class Group:
    def __init__(self, evnum, objl, outgroup=False):
        self.evnum = evnum
        self.base = -1
        self.objl = set(objl)
        self.outgroup = outgroup
        self.num = -1

class GroupCmp:
    def __init__(self, v):
        self.v = v
    def __lt__(self, g):
        return self.v < g.base

# Control whether even unrelated groups can be merged
any_merge = True

# Interleave uncore events between CPU groups
distribute_uncore = False

def grab_group(l):
    if needed_counters(l) <= cpu.counters:
        return len(l)
    n = 1
    while needed_counters(l[:n]) < cpu.counters and n < len(l):
        n += 1
    if needed_counters(l[:n]) > cpu.counters and n > 0:
        n -= 1
        assert needed_counters(l[:n]) <= cpu.counters
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
    z_l = itertools.zip_longest if sys.version_info.major == 3 else itertools.izip_longest
    return [x for x in chain(*z_l(cg, og)) if x is not None]

def gen_res_map(solist):
    for obj in solist:
        for k in obj.group_map.keys():
            gr = obj.group_map[k]
            obj.res_map[k] = gr[0].base + gr[1]

def print_group(g):
    evkeys = [k for o in g.objl for k in o.group_map.keys() if o.group_map[k][0] == g]
    objnames = {("%s" % quote(x[2])) + ("[%d]" % x[1] if x[1] else "") for x in evkeys}
    evnames = {mark_fixed(x[0]) for x in evkeys}
    pwrap(" ".join(objnames) + ":", 78)
    pwrap(" ".join(evnames).lower() +
          (" [%d counters]" % needed_counters(g.evnum)) +
          (" [%d]" % g.base if args.debug else ""), 75, "  ")

class Scheduler:
    """Schedule events into groups."""

    def __init__(self):
        self.evnum = [] # flat global list
        self.evgroups = [] # of Group
        self.og_groups = dict()
        # list of groups that still have generic counters, for faster
        # duplicate checks
        self.evgroups_nf = []

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
                        test_debug_print("unreferenced %s  [%d]" % (g.evnum[i], i))
                        g.evnum[i] = "dummy"

    def split_groups(self, obj, evlev):
        levels = set(get_levels(evlev))
        if len(levels) == 1:
            # when there is only a single left just fill groups
            evnum = list(map(raw_event, get_names(evlev)))
            while evlev:
                n = grab_group(evnum)
                self.add(obj, evnum[:n], None)
                evlev = evlev[n:]
                evnum = evnum[n:]
        else:
            for l in sorted(levels):
                evl = [x for x in evlev if x[1] == l]
                # don't filter objects, the lower level functions
                # have to handle missing entries
                if evl:
                    self.add(obj, raw_events(get_names(evl)), evl)

    def add_duplicate(self, evnum, obj):
        evset = set(evnum)
        num_gen = num_generic_counters(evset)
        full = set()

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
                  needed_counters(cat_unique(g.evnum, evnum)) <= cpu.counters):
                debug_print("add_duplicate %s %s in %s obj %s" % (
                    evnum,
                    list(map(event_rmap, evnum)),
                    g.evnum,
                    obj.name))
                for k in evnum:
                    if k not in g.evnum:
                        g.evnum.append(k)
                g.objl.add(obj)
                update_group_map(g.evnum, obj, g)
                return True

            # memorize already full groups
            elif num_generic_counters(set(g.evnum)) >= cpu.counters:
                full.add(g)
        if full:
            self.evgroups_nf = [g for g in self.evgroups_nf if g not in full]

        return False

    def add(self, obj, evnum, evlev):
        # does not fit into a group.
        if needed_counters(evnum) > cpu.counters:
            self.split_groups(obj, evlev)
            return
        evnum = dedup(evnum)
        if not self.add_duplicate(evnum, obj):
            debug_print("add %s %s" % (evnum, list(map(event_rmap, evnum))))
            g = Group(evnum, [obj])
            self.evgroups.append(g)
            self.evgroups_nf.append(g)
            update_group_map(evnum, obj, g)

    def add_outgroup(self, obj, evnum):
        debug_print("add_outgroup %s" % evnum)
        for ev in evnum:
            if ev in self.og_groups:
                g = self.og_groups[ev]
                g.objl.add(obj)
            else:
                g = Group([ev], [obj], True)
                self.og_groups[ev] = g
                self.evgroups.append(g)
                self.evgroups_nf.append(g)
            update_group_map([ev], obj, g)

    def allocate_bases(self):
        base = 0
        for i, g in enumerate(self.evgroups):
            g.base = base
            g.num = i
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
            debug_print("schedule %s " % obj.name)
            evnum = obj.evnum
            evlevels = obj.evlevels
            oe = [e in outgroup_events for e in obj.evnum]
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

        self.dummy_unreferenced(olist)
        self.allocate_bases()

        if args.print_group:
            for g in self.evgroups:
                print_group(g)

        gen_res_map(olist)
        if args.print_group:
            self.print_group_summary(olist)

def should_print_obj(obj, match):
    assert not isinstance(obj.val, DummyArith)
    if obj.val is None:
        return False
    if obj.thresh or args.verbose:
        if not match(obj):
            pass
        elif obj.metric:
            if args.verbose or obj.val != 0:
                return True
        elif check_ratio(obj.val):
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

class Runner:
    """Handle measurements of event groups. Map events to groups."""

    def reset(self):
        self.stat = ComputeStat(args.quiet)
        self.sample_obj = set()
        self.olist = []
        self.bottlenecks = set()
        self.idle_keys = set()
        self.summary = None
        if args.summary:
            self.summary = Summary()
        self.sched = Scheduler()

    def __init__(self, max_level, idle_threshold):
        self.reset()
        self.odict = dict()
        self.max_level = max_level
        self.max_node_level = 0
        self.idle_threshold = idle_threshold
        # always needs to be filtered by olist:
        self.metricgroups = defaultdict(list)
        self.numprint = 0
        if args.valcsv:
            self.valcsv = csv.writer(args.valcsv, lineterminator='\n')
            self.valcsv.writerow(("Timestamp", "CPU", "Group", "Event", "Value",
                                  "Perf-event", "Index", "STDDEV", "MULTI", "Nodes"))

    def do_run(self, obj):
        obj.res = None
        obj.res_map = dict()
        obj.group_map = dict()
        self.olist.append(obj)
        self.odict[obj.name] = obj
        if has(obj, 'metricgroup'):
            for j in obj.metricgroup:
                self.metricgroups[j].append(obj)
        self.max_node_level = max(self.max_node_level, obj.level)

    # remove unwanted nodes after their parent relationship has been set up
    def filter_nodes(self):
        self.full_olist = list(self.olist)

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

        self.sibmatch = set()

        def want_node(obj):
            if args.reduced and has(obj, 'server') and not obj.server:
                return False
            if args.no_uncore and safe_ref(obj, 'area') == "Info.System":
                return False
            want = ((obj.metric and args.metrics) or
                    (('force_metric' in obj.__dict__) and obj.force_metric) or
                    obj.name in add_met or
                    obj in parents) and obj.name not in remove_met
            if not obj.metric and obj.level <= self.max_level:
                want = True
            return node_filter(obj, want, self.sibmatch)

        # this updates sibmatch
        fmatch = list(map(want_node, self.olist))
        # now keep what is both in fmatch and sibmatch
        self.olist = [obj for obj, fil in zip(self.olist, fmatch) if fil or obj in self.sibmatch]
        if len(self.olist) == 0:
            sys.exit("All nodes disabled")

    def setup_children(self):
        for obj in self.olist:
            if not obj.metric and 'parent' in obj.__dict__ and obj.parent:
                obj.parent.children.append(obj)

    # check nodes argument for typos
    def check_nodes(self, nodesarg):

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
            if s in self.odict:
                return True
            for k in self.olist:
                if fnmatch(k.name, s) or fnmatch(full_name(k), s):
                    return True
            return False
        valid = map(valid_node, options)
        if not all(valid):
            sys.exit("Unknown node(s) in --nodes: " +
                     " ".join([o for o, v in zip(options, valid) if not v]))

    def reset_thresh(self):
        for obj in self.olist:
            if not obj.metric:
                obj.thresh = False

    def run(self, obj):
        obj.thresh = False
        obj.metric = False
        obj.children = []
        self.do_run(obj)

    def metric(self, obj):
        obj.thresh = True
        obj.metric = True
        obj.level = 0
        obj.sibling = None
        self.do_run(obj)

    def force_metric(self, obj):
        obj.force_metric = True
        self.metric(obj)

    # collect the events by pre-computing the equation
    def collect(self):
        bad_nodes = set()
        bad_events = set()
        unsup_nodes = set()
        errata_nodes = set()
        errata_warn_nodes = set()
        errata_names = set()
        errata_warn_names = set()
        min_kernel = []
        for obj in self.olist:
            obj.evlevels = []
            obj.compute(lambda ev, level: ev_append(ev, level, obj))
            obj.val = None
            obj.evlist = [x[0] for x in obj.evlevels]
            obj.evnum = raw_events(obj.evlist, initialize=True)
            obj.nc = needed_counters(set(obj.evnum))

            # work arounds for lots of different problems
            unsup = [x for x in obj.evlist if unsup_event(x, unsup_events, min_kernel)]
            if any(unsup):
                bad_nodes.add(obj)
                bad_events |= set(unsup)
            unsup = [x for x in obj.evlist if missing_pmu(x)]
            if any(unsup):
                unsup_nodes.add(obj)
            query_errata(obj, errata_events, errata_nodes, errata_names)
            query_errata(obj, errata_warn_events, errata_warn_nodes, errata_warn_names)
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
                        print("Fixed in kernel %d.%d" % (sorted(min_kernel, key=kv_to_key, reverse=True)[0]),
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
        if len(self.olist) == 0:
            sys.exit("No usable events found")

    def propagate_siblings(self):
        changed = [0]

        def propagate(k, changed):
            if not k.thresh:
                k.thresh = True
                changed[0] += 1

        for obj in self.olist:
            if obj in self.sibmatch:
                propagate(obj, changed)
            if obj.thresh and obj.sibling:
                if isinstance(obj.sibling, (list, tuple)):
                    for k in obj.sibling:
                        propagate(k, changed)
                else:
                    propagate(obj.sibling, changed)
        return changed[0]

    def compute(self, res, rev, valstats, env, match, stat):
        if len(res) == 0:
            print("Nothing measured?", file=sys.stderr)
            return False

        changed = 0

        # step 1: compute
        for obj in self.olist:
            obj.errcount = 0

            if not match(obj):
                continue
            ref = set()
            oldthresh = obj.thresh
            if 'parent' in obj.__dict__ and obj.parent and obj.parent not in self.olist:
                obj.parent.thresh = True
            obj.compute(lambda e, level:
                            lookup_res(res, rev, e, obj, env, level, ref, -1, valstats))
            if args.force_bn and obj.name in args.force_bn:
                obj.thresh = True
            if obj.thresh != oldthresh:
                changed += 1
            if stat:
                stat.referenced |= ref
            if not obj.res_map and not all([x in env for x in obj.evnum]):
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
        return changed

    def print_res(self, out, timestamp, title, match, bn, idlemark=False):
        if bn:
            self.bottlenecks.add(bn)

        if safe_ref(out, 'logf') == sys.stderr:
            out.logf.flush()

        # determine all objects to print
        olist = [o for o in self.olist if should_print_obj(o, match)]

        # sort by metric group
        olist = olist_by_metricgroup(olist, self.metricgroups)

        compute_column_lengths(olist, out)

        # step 3: print
        for i, obj in enumerate(olist):
            val = get_uval(obj)
            desc = obj_desc_runtime(obj, olist[i + 1:])
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
                        sample_desc(obj.sample) if has(obj, 'sample') else None,
                        "<==" if obj == bn else "",
                        node_below(obj),
                        idlemark)
                if obj.thresh or args.verbose:
                    self.sample_obj.add(obj)
            self.numprint += 1

    def list_metric_groups(self):
        print("MetricGroups:")
        mg = sorted(self.metricgroups.keys())
        if args.csv:
            print("\n".join(mg))
        else:
            pwrap(" ".join(mg), indent="        ")

    def list_nodes(self, title, filt, rest):
        def match(rest, n, fn):
            return not rest or any([n.startswith(x) or fn.startswith(x) if
                                    not x.endswith("^") else
                                    n == x[:-1] or fn == x[:-1]
                                    for x in rest])

        if title:
            print("%s:" % title)
        for obj in self.olist:
            fn = full_name(obj)
            sep = args.csv if args.csv else "\n\t"
            if filt(obj) and match(rest, obj.name, fn):
                print(fn, end=sep)
                if not args.no_desc:
                    print(obj_desc(obj, sep=sep))

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

def do_sample(sample_obj, rest, count, ret):
    samples = [("cycles:pp", "Precise cycles", )]

    for obj in sample_obj:
        for s in obj.sample:
            samples.append((s, obj.name))

    # first dedup
    samples = [k for k, g in groupby(sorted(samples))]

    # now merge objects with the same sample event into one
    def sample_event(x):
        return x[0]
    samples = sorted(samples, key=sample_event)
    samples = [(k, "_".join([x[1] for x in g])) for k, g in groupby(samples, key=sample_event)]

    # find unsupported events
    nsamp = [x for x in samples if not unsup_event(x[0], unsup_events)]
    nsamp = [(remove_pp(x[0]), x[1])
             if unsup_event(x[0], unsup_pebs) else x
             for x in nsamp]
    if nsamp != samples:
        missing = [x[0] for x in set(samples) - set(nsamp)]
        if not args.quiet:
            print("warning: update kernel to handle sample events:", file=sys.stderr)
            print("\n".join(missing), file=sys.stderr)

    def force_pebs(ev):
        return ev in require_pebs_events

    no_pebs = not supports_pebs()
    if no_pebs:
        for j in nsamp:
            # initialize require_pebs_events
            raw_event(j[0], nopebs=False, initialize=True)
        nnopebs = {x[0] for x in nsamp if force_pebs(x[0])}
        if nnopebs and not args.quiet:
            for j in nnopebs:
                print("sample event %s not (currently) supported in virtualization" % j, file=sys.stderr)
        nsamp = [x for x in nsamp if x[0] not in nnopebs]

    sl = [raw_event(s[0], s[1] + "_" + clean_event(s[0]), period=True, nopebs=False) for s in nsamp]
    sl = add_filter(sl)
    sample = ",".join([x for x in sl if x])
    if no_pebs:
        sample = re.sub(r'/p+', '/', sample)
        sample = re.sub(r':p+', '', sample)
    print("Sampling:")
    extra_args = args.sample_args.replace("+", "-").split()
    perf_data = args.sample_basename
    if count is not None:
        perf_data += ".%d" % count
    sperf = ([perf, "record"] +
             extra_args +
             ["-e", sample, "-o", perf_data] +
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
            print("Run `" + perf + " report%s%s' to show the sampling results" % (
                (" -i %s" % perf_data) if perf_data != "perf.data" else "",
                " --no-branch-history" if "-b" in extra_args else ""))

BOTTLENECK_LEVEL_INC = 1

def suggest_bottlenecks(runner):
    def gen_bn(o):
        if o.children:
            return "+%s*/%d" % (o.name, o.level + BOTTLENECK_LEVEL_INC)
        if 'sibling' in o.__dict__ and o.sibling:
            return "+%s^" % full_name(o)
        return None
    children = [gen_bn(o) for o in runner.bottlenecks]
    children = list(filter(None, children))
    if children and args.nodes:
        children = [x for x in children if x[:-1] not in args.nodes]
    if children:
        mux = ",+MUX" if not (args.metrics or args.all) and (args.nodes is None or "MUX" not in args.nodes) else ""
        if not args.quiet:
            print("Add%s --nodes '!%s%s' for breakdown on the bottleneck%s." % (
                    "ing" if args.drilldown else "",
                    ",".join(children),
                    mux,
                    "s" if len(children) > 1 else ""))
        if args.drilldown:
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
    print("Run toplev --describe %s to get more information on bottleneck%s" % (
        " ".join([full_name(x) + "^" if nummatch(x.name) > 1 else x.name + "^" for x in runner.bottlenecks]),
        "s" if len(runner.bottlenecks) > 1 else ""), file=sys.stderr)

def do_xlsx():
    cmd = "%s %s/tl-xlsx.py --valcsv '%s' --perf '%s' --cpuinfo '%s' " % (
        sys.executable,
        exe_dir(),
        args.valcsv.name,
        args.perf_output.name,
        env.cpuinfo if env.cpuinfo else "/proc/cpuinfo")
    if args.single_thread:
        names = ["program"]
        files = [out.logf.name]
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
                print("interval-normalize failed: %d" % ret, file=sys.stderr)
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
    if not args.xkeep:
        for fn in files + extrafiles:
            os.remove(fn)
    return ret

def sysctl(name):
    try:
        with open("/proc/sys/" + name.replace(".","/"), "r") as f:
            val = int(f.readline())
    except IOError:
        return 0
    return val

# check nmi watchdog
if sysctl("kernel.nmi_watchdog") != 0 or os.getenv("FORCE_NMI_WATCHDOG"):
    cpu.counters -= 1
    print("Consider disabling nmi watchdog to minimize multiplexing", file=sys.stderr)
    print("(echo 0 > /proc/sys/kernel/nmi_watchdog as root)", file=sys.stderr)

if cpu.cpu is None:
    sys.exit("Unsupported CPU model %d" % (cpu.model,))

kv = os.getenv("KERNEL_VERSION")
if not kv:
    kv = platform.release()
kernel_version = list(map(int, kv.split(".")[:2]))

def ht_warning():
    if cpu.ht and not args.quiet:
        print("WARNING: HT enabled", file=sys.stderr)
        print("Measuring multiple processes/threads on the same core may is not reliable.",
                file=sys.stderr)

def add_args(rest, *args):
    a = [x for x in args if x not in rest]
    return a + rest

def setup_metrics(model):
    force_metrics = os.getenv("FORCEMETRICS") is not None
    model.topdown_use_fixed = force_metrics or os.path.exists(
            "/sys/devices/cpu/events/topdown-fe-bound")
    global core_domains
    core_domains = set(["CoreClocks", "CoreMetric"])
    global slots_available
    slots_available = force_metrics or os.path.exists("/sys/devices/cpu/events/slots")

runner = Runner(args.level, idle_threshold)

pe = lambda x: None
if args.debug:
    printed_error = set()
    def print_err(x):
        if x not in printed_error:
            print(x)
            printed_error.add(x)
    pe = lambda e: print_err(e)

if args.single_thread:
    cpu.ht = False

if args.quiet:
    if not args.desc:
        args.no_desc = True
    args.no_util = True

if cpu.cpu == "ivb":
    import ivb_client_ratios
    ivb_client_ratios.smt_enabled = cpu.ht
    smt_mode = cpu.ht
    model = ivb_client_ratios
elif cpu.cpu == "ivt":
    import ivb_server_ratios
    ivb_server_ratios.smt_enabled = cpu.ht
    smt_mode = cpu.ht
    model = ivb_server_ratios
elif cpu.cpu == "snb":
    import snb_client_ratios
    snb_client_ratios.smt_enabled = cpu.ht
    smt_mode = cpu.ht
    model = snb_client_ratios
elif cpu.cpu == "jkt":
    import jkt_server_ratios
    jkt_server_ratios.smt_enabled = cpu.ht
    smt_mode = cpu.ht
    model = jkt_server_ratios
elif cpu.cpu == "hsw":
    import hsw_client_ratios
    hsw_client_ratios.smt_enabled = cpu.ht
    smt_mode = cpu.ht
    model = hsw_client_ratios
elif cpu.cpu == "hsx":
    import hsx_server_ratios
    hsx_server_ratios.smt_enabled = cpu.ht
    smt_mode = cpu.ht
    model = hsx_server_ratios
elif cpu.cpu == "bdw":
    import bdw_client_ratios
    bdw_client_ratios.smt_enabled = cpu.ht
    smt_mode = cpu.ht
    model = bdw_client_ratios
elif cpu.cpu == "bdx":
    import bdx_server_ratios
    bdx_server_ratios.smt_enabled = cpu.ht
    smt_mode = cpu.ht
    model = bdx_server_ratios
elif cpu.cpu == "skl":
    import skl_client_ratios
    skl_client_ratios.smt_enabled = cpu.ht
    smt_mode = cpu.ht
    model = skl_client_ratios
elif cpu.cpu == "skx":
    import skx_server_ratios
    skx_server_ratios.smt_enabled = cpu.ht
    smt_mode = cpu.ht
    model = skx_server_ratios
elif cpu.cpu == "clx":
    import clx_server_ratios
    clx_server_ratios.smt_enabled = cpu.ht
    smt_mode = cpu.ht
    model = clx_server_ratios
elif cpu.cpu == "icl":
    import icl_client_ratios
    icl_client_ratios.smt_enabled = cpu.ht
    model = icl_client_ratios
    setup_metrics(model)
    # work around kernel constraint table bug in some kernel versions
    constraint_fixes["CYCLE_ACTIVITY.STALLS_MEM_ANY"] = "0,1,2,3"
elif cpu.cpu == "tgl":
    # FIXME use the icl model for now until we have a full TGL model
    import icl_client_ratios
    icl_client_ratios.smt_enabled = cpu.ht
    model = icl_client_ratios
    setup_metrics(model)
    # work around kernel constraint table bug in some kernel versions
    constraint_fixes["CYCLE_ACTIVITY.STALLS_MEM_ANY"] = "0,1,2,3"
elif cpu.cpu == "slm":
    import slm_ratios
    model = slm_ratios
elif cpu.cpu == "knl":
    import knl_ratios
    knl_ratios.smt_enabled = smt_mode = cpu.ht
    model = knl_ratios
else:
    ht_warning()
    import simple_ratios
    model = simple_ratios

version = model.version
model.print_error = pe
model.check_event = lambda ev: emap.getevent(ev) is not None
model.Setup(runner)

if args.gen_script:
    args.quiet = True

if "Errata_Whitelist" in model.__dict__:
    errata_whitelist += model.Errata_Whitelist.split(";")

if "base_frequency" in model.__dict__:
    model.base_frequency = cpu.freq * 1000

if "model" in model.__dict__:
    model.model = cpu.modelid

if args.describe:
    args.long_desc = True
    if not rest:
        sys.exit("No nodes to describe")
    runner.list_nodes(None, any_node, rest)
if args.list_metrics or args.list_all:
    runner.list_nodes("Metrics", lambda obj: obj.metric, rest)
if args.list_nodes or args.list_all:
    runner.list_nodes("Nodes", lambda obj: not obj.metric, rest)
if args.list_metric_groups or args.list_all:
    runner.list_metric_groups()
if args.list_metric_groups or args.list_metrics or args.list_nodes or args.list_all or args.describe:
    if any([x.startswith("-") for x in rest]):
        sys.exit("Unknown arguments for --list*/--describe")
    sys.exit(0)

def check_root():
    if not (os.geteuid() == 0 or sysctl("kernel.perf_event_paranoid") == -1) and not args.quiet:
        print("Warning: Needs root or echo -1 > /proc/sys/kernel/perf_event_paranoid",
                file=sys.stderr)

if not args.no_util:
    import perf_metrics
    perf_metrics.Setup(runner)

if args.power and feat.supports_power:
    import power_metrics
    power_metrics.Setup(runner)
    if not args.quiet and not import_mode and not args.print:
        print("Running with --power. Will measure complete system.")
    if args.single_thread:
        print("--single-thread conflicts with --power")
    check_root()
    rest = add_args(rest, "-a")

if args.sw:
    import linux_metrics
    linux_metrics.Setup(runner)

if args.tsx and cpu.has_tsx and cpu.cpu in tsx_cpus:
    import tsx_metrics
    tsx_metrics.Setup(runner)

if args.frequency:
    import frequency
    frequency.SetupCPU(runner, cpu)

if args.nodes:
    runner.check_nodes(args.nodes)
runner.setup_children()
runner.filter_nodes()

if smt_mode and not os.getenv('FORCEHT'):
    # do not need SMT mode if no objects have Core scope
    if not any(map(core_node, runner.olist)):
        smt_mode = False

if not smt_mode and not args.single_thread and "-A" not in rest:
    multi = args.per_socket + args.per_core + args.per_thread + args.global_
    if multi > 0:
        rest = add_args(rest, "-a")
    if multi > 1 or args.per_thread:
        rest = add_args(rest, "-A")
    if args.per_socket and multi == 1:
        rest = add_args(rest, "--per-socket")
    if args.per_core and multi == 1:
        rest = add_args(rest, "--per-core")

full_system = False
if not args.single_thread and smt_mode:
    if not args.quiet and not import_mode:
        print("Will measure complete system.")
    if smt_mode:
        if args.cpu:
            print("Warning: --cpu/-C mode with HyperThread must specify all core thread pairs!",
                  file=sys.stderr)
        if args.pid:
            sys.exit("-p/--pid mode not compatible with SMT. Use sleep in global mode.")
    check_root()
    rest = add_args(rest, "-a", "-A")
    full_system = True
else:
    full_system = "-A" in rest or "--per-core" in rest or "--per-socket" in rest

if ("Slots" not in core_domains and
        cpu.ht and
        not args.single_thread and
        any(map(core_node, runner.olist))):
    if not feat.supports_percore:
        runner.olist = filternot(core_node, runner.olist)
    else:
        rest = ["--percore-show-thread"] + rest

if args.perf_output:
    ph = []
    if args.interval:
        ph.append("Timestamp")
    if full_system:
        ph.append("Location")
        if ("--per-socket" in rest or "--per-core" in rest) and "-A" not in rest:
            ph.append("Num-CPUs")
    ph += ["Value", "Unit", "Event", "Run-Time", "Enabled"]
    args.perf_output.write(";".join(ph) + "\n")

if args.core:
    runner.allowed_threads = [x for x in cpu.allcpus if display_core(x, False)]
    allowed_cores = [x for x in cpu.allcpus if display_core(x, True)]
    rest = ["-C", ",".join(["%d" % x for x in allowed_cores])] + rest
else:
    runner.allowed_threads = cpu.allcpus

if not args.quiet and not args.print:
    print("Using level %d." % (args.level), end='')
    if not args.level and cpu.cpu != "slm":
        print("Change level with -lX")
    print()
    sys.stdout.flush()

if args.pinned:
    run_l1_parallel = True

if args.repl:
    import code
    code.interact(banner='toplev repl', local=locals())
    sys.exit(0)

runner.collect()
if args.csv:
    if args.columns:
        out = tl_output.OutputColumnsCSV(args.output, args.csv, args, version, cpu)
    else:
        out = tl_output.OutputCSV(args.output, args.csv, args, version, cpu)
elif args.columns:
    out = tl_output.OutputColumns(args.output, args, version, cpu)
else:
    out = tl_output.OutputHuman(args.output, args, version, cpu)
runner.sched.schedule(runner.olist)

def measure_and_sample(count):
    while True:
        try:
            if args.no_multiplex:
                ret = execute_no_multiplex(runner, out, rest)
            else:
                ret = execute(runner, out, rest)
        except KeyboardInterrupt:
            ret = 1
        print_summary(runner, out)
        runner.stat.compute_errors()
        if runner.bottlenecks and not args.quiet:
            suggest_desc(runner)
        repeat = False
        if args.level < runner.max_node_level and runner.bottlenecks:
            repeat = suggest_bottlenecks(runner)
        if (args.show_sample or args.run_sample) and ret == 0:
            do_sample(runner.sample_obj, rest, count, ret)
        if 100 <= ret <= 200 and repeat:
            print("Perf or workload appears to have failed with error %d. Not drilling down" % ret,
                  file=sys.stderr)
            break
        if count is not None:
            count += 1
        if repeat:
            if not args.quiet:
                print("Rerunning workload", file=sys.stderr)
            runner.reset()
            runner.olist = runner.full_olist
            for o in runner.olist:
                o.group_map = dict()
                o.res_map = dict()
            runner.filter_nodes()
            runner.collect()
            runner.sched.schedule(runner.olist)
        else:
            break
    return ret, count

if args.sample_repeat:
    cnt = 1
    for j in range(args.sample_repeat):
        ret, cnt = measure_and_sample(cnt)
        if ret:
            break
else:
    ret, count = measure_and_sample(0 if args.drilldown else None)

out.print_footer()
out.flushfiles()

if args.xlsx and ret == 0:
    ret = do_xlsx()

if runner.idle_keys and not args.quiet:
    print("Idle CPUs %s may have been hidden. Override with --idle-threshold 100" %
            (",".join(runner.idle_keys)), file=sys.stderr)

if notfound_cache and any(["not supported" not in x for x in notfound_cache.values()]) and not args.quiet:
    print("Some events not found. Consider running event_download to update event lists", file=sys.stderr)

if args.graph:
    args.output.close()
    graphp.wait()
sys.exit(ret)
