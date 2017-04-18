#!/usr/bin/env python
# Copyright (c) 2012-2016, Intel Corporation
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
# Must find ocperf in python module path. add to paths below if needed.
# Handles a variety of perf and kernel versions, but older ones have various
# limitations.

import sys, os, re, itertools, textwrap, platform, pty, subprocess
import exceptions, argparse, time, types, fnmatch, csv, copy
from collections import defaultdict, Counter

from tl_stat import combine_valstat, ComputeStat, ValStat
from tl_cpu import CPU
import tl_output
import ocperf

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
)

tsx_cpus = ("hsw", "hsx", "bdw", "skl")

fixed_to_num = {
    "instructions" : 0,
    "cycles" : 1,
    "cpu/event=0x3c,umask=0x00,any=1/": 1,
    "cpu/event=0x3c,umask=0x0,any=1/": 1,
    "ref-cycles" : 2,
    "cpu/event=0x0,umask=0x3,any=1/" : 2,
}

# handle kernels that don't support all events
unsup_pebs = (
    ("BR_MISP_RETIRED.ALL_BRANCHES:pp", (("hsw",), (3, 18), None)),
    ("MEM_LOAD_UOPS_L3_HIT_RETIRED.XSNP_HITM:pp", (("hsw",), (3, 18), None)),
    ("MEM_LOAD_UOPS_RETIRED.L3_MISS:pp", (("hsw",), (3, 18), None)),
)

ivb_ht_39 = (("ivb", "ivt"), (4, 1), (3, 9))
# uncomment if you removed commit 741a698f420c3
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

errata_whitelist = {
    "BDE69", "BDE70",
}

ingroup_events = frozenset(fixed_to_num.keys())

outgroup_events = set(["dummy"])

nonperf_events = set(["interval-ns", "mux"])

# workaround for broken event files for now
event_fixes = {
    "UOPS_EXECUTED.CYCLES_GE_1_UOPS_EXEC": "UOPS_EXECUTED.CYCLES_GE_1_UOP_EXEC",
    "UOPS_EXECUTED.CYCLES_GE_1_UOP_EXEC": "UOPS_EXECUTED.CYCLES_GE_1_UOPS_EXEC"
}

smt_domains = ("Slots", "CoreClocks", "CoreMetric")

limited_counters = {
    "cpu/cycles-ct/": 2,
}
limited_set = set(limited_counters.keys())

smt_mode = False

errata_events = dict()
errata_warn_events = dict()

perf = os.getenv("PERF")
if not perf:
    perf = "perf"

def works(x):
    return os.system(x + " >/dev/null 2>/dev/null") == 0

class PerfFeatures:
    """Adapt to the quirks of various perf versions."""
    def __init__(self):
        self.logfd_supported = works(perf + " stat --log-fd 3 3>/dev/null true")
        if not self.logfd_supported:
            sys.exit("perf binary is too old. please upgrade")
        self.supports_power = works(perf + " list  | grep -q power/")

def kv_to_key(v):
    return v[0] * 100 + v[1]

def unsup_event(e, table, min_kernel=None):
    if ":" in e:
        e = e[:e.find(":")]
    for j in table:
        if fnmatch.fnmatch(e, j[0]) and cpu.realcpu in j[1][0]:
            break
    else:
        return False
    v = j[1]
    if v[1] and kv_to_key(kernel_version) < kv_to_key(v[1]):
        if min_kernel:
            min_kernel.append(v[1])
        return True
    if v[2] and kv_to_key(kernel_version) >= kv_to_key(v[2]) :
        return True
    return False

def needed_limited_counter(evlist, limit_table, limit_set):
    limited_only = set(evlist) & set(limit_set)
    assigned = Counter([limit_table[x] for x in limited_only]).values()
    # 0..1 counter is ok
    # >1   counter is over subscribed
    return sum([x - 1 for x in assigned if x > 1])

def fixed_overflow(evlist):
    return needed_limited_counter(evlist, fixed_to_num, ingroup_events)

def limit_overflow(evlist):
    return needed_limited_counter(evlist, limited_counters, limited_set)

def needed_counters(evlist):
    evset = set(evlist)
    num_generic = len(evset - ingroup_events - limited_set)

    # If we need more than 3 fixed counters (happens with any vs no any)
    # promote those to generic counters
    num = num_generic + fixed_overflow(evlist)

    # account events that only schedule on one of the generic counters

    # first allocate the limited counters that are not oversubscribed
    num_limit = limit_overflow(evlist)
    num += len(evset & limited_set) - num_limit

    # if we need more than one of a limited counter make it look
    # like it fills the group to limit first before adding them to force
    # a split
    if num_limit > 0:
        num = max(num, cpu.counters) + num_limit
    return num

def event_group(evlist):
    e = ",".join(add_filter(evlist))
    if not args.no_group and 1 < needed_counters(evlist) <= cpu.counters:
        e = "{%s}" % (e,)
    return e

def exe_dir():
    d = os.path.dirname(sys.argv[0])
    if d:
        return d
    return "."

feat = PerfFeatures()
emap = ocperf.find_emap()
if not emap:
    sys.exit("Unknown CPU or CPU event map not found.")

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
can also be used.

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
Do not use together with sleep.

toplev needs a new enough perf tool and has specific requirements on
the kernel. See http://github.com/andikleen/pmu-tools/wiki/toplev-kernel-support

Other CPUs can be forced with FORCECPU=name
This usually requires setting the correct event map with EVENTMAP=...
Valid CPU names: ''' + " ".join([x[0] for x in known_cpus]),
formatter_class=argparse.RawDescriptionHelpFormatter)
g = p.add_argument_group('General operation')
g.add_argument('--interval', '-I', help='Measure every ms instead of only once',
               type=int)
g.add_argument('--no-multiplex',
               help='Do not multiplex, but run the workload multiple times as needed. Requires reproducible workloads.',
               action='store_true')
g.add_argument('--single-thread', '-S', help='Measure workload as single thread. Workload must run single threaded. In SMT mode other thread must be idle.', action='store_true')

g = p.add_argument_group('Measurement filtering')
g.add_argument('--kernel', help='Only measure kernel code', action='store_true')
g.add_argument('--user', help='Only measure user code', action='store_true')
g.add_argument('--cpu', '-C', help=argparse.SUPPRESS)
g.add_argument('--pid', '-p', help=argparse.SUPPRESS)
g.add_argument('--core', help='Limit output to cores. Comma list of Sx-Cx-Tx. All parts optional.')

g = p.add_argument_group('Select events')
g.add_argument('--level', '-l', help='Measure upto level N (max 5)',
               type=int, default=1)
g.add_argument('--metrics', '-m', help="Print extra metrics", action='store_true')
g.add_argument('--sw', help="Measure perf Linux metrics", action='store_true')
g.add_argument('--no-util', help="Do not measure CPU utilization", action='store_true')
g.add_argument('--tsx', help="Measure TSX metrics", action='store_true')
g.add_argument('--all', help="Measure everything available", action='store_true')
g.add_argument('--frequency', help="Measure frequency", action='store_true')
g.add_argument('--power', help='Display power metrics', action='store_true')
g.add_argument('--nodes', help='Include or exclude nodes (with + to add, ^ to remove, comma separated list, wildcards allowed)')
g.add_argument('--reduced', help='Use reduced server subset of nodes/metrics', action='store_true')

g = p.add_argument_group('Workarounds')
g.add_argument('--no-group', help='Dont use groups', action='store_true')
g.add_argument('--force-events', help='Assume kernel supports all events. May give wrong results.', action='store_true')
g.add_argument('--ignore-errata', help='Do not disable events with errata', action='store_true')

g = p.add_argument_group('Output')
g.add_argument('--no-desc', help='Do not print event descriptions', action='store_true')
g.add_argument('--desc', help='Force event descriptions', action='store_true')
g.add_argument('--verbose', '-v', help='Print all results even when below threshold or exceeding boundaries. Note this can result in bogus values, as the TopDown methodology relies on thresholds to correctly characterize workloads.',
               action='store_true')
g.add_argument('--csv', '-x', help='Enable CSV mode with specified delimeter')
g.add_argument('--output', '-o', help='Set output file', default=sys.stderr,
               type=argparse.FileType('w'))
g.add_argument('--graph', help='Automatically graph interval output with tl-barplot.py',
               action='store_true')
g.add_argument("--graph-cpu", help="CPU to graph using --graph")
g.add_argument('--title', help='Set title of graph')
g.add_argument('--quiet', help='Avoid unnecessary status output', action='store_true')
g.add_argument('--long-desc', help='Print long descriptions instead of abbreviated ones.',
                action='store_true')
g.add_argument('--columns', help='Print CPU output in multiple columns', action='store_true')
g.add_argument('--summary', help='Print summary at the end. Only useful with -I', action='store_true')

g = p.add_argument_group('Additional information')
g.add_argument('--print-group', '-g', help='Print event group assignments',
               action='store_true')
g.add_argument('--raw', help="Print raw values", action='store_true')
g.add_argument('--valcsv', '-V', help='Write raw counter values into CSV file', type=argparse.FileType('w'))
g.add_argument('--stats', help='Show statistics on what events counted', action='store_true')
g.add_argument('--detailed', '-d', help=argparse.SUPPRESS, action='store_true')

g = p.add_argument_group('Sampling')
g.add_argument('--show-sample', help='Show command line to rerun workload with sampling', action='store_true')
g.add_argument('--run-sample', help='Automatically rerun workload with sampling', action='store_true')
g.add_argument('--sample-args', help='Extra rguments to pass to perf record for sampling. Use + to specify -', default='-g')
g.add_argument('--sample-repeat', help='Repeat measurement and sampling N times. This interleaves counting and sampling', type=int)
g.add_argument('--sample-basename', help='Base name of sample perf.data files', default="perf.data")

p.add_argument('--version', help=argparse.SUPPRESS, action='store_true')
p.add_argument('--debug', help=argparse.SUPPRESS, action='store_true')
p.add_argument('--repl', action='store_true', help=argparse.SUPPRESS)
args, rest = p.parse_known_args()

rest = [x for x in rest if x != "--"]

if args.version:
    print "toplev"
    sys.exit(0)

if args.cpu:
    rest = ["--cpu", args.cpu] + rest
if args.pid:
    rest = ["--pid", args.pid] + rest

if len(rest) == 0:
    p.print_help()
    sys.exit(0)

if args.all:
    args.tsx = True
    args.power = True
    args.sw = True
    args.metrics = True
    args.frequency = True
    args.level = 5

if args.graph:
    if not args.interval:
        args.interval = 100
    extra = ""
    if args.title:
        title = args.title
    else:
        title = "cpu %s" % (args.graph_cpu if args.graph_cpu else 0)
    extra += '--title "' + title + '" '
    if args.output != sys.stderr:
        extra += '--output "' + args.output.name + '" '
    if args.graph_cpu:
        extra += "--cpu " + args.graph_cpu + " "
    args.csv = ','
    cmd = "PATH=$PATH:%s ; tl-barplot.py %s /dev/stdin" % (exe_dir(), extra)
    if not args.quiet:
        print cmd
    args.output = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE).stdin

if args.sample_repeat:
    args.run_sample = True

print_all = args.verbose # or args.csv
dont_hide = args.verbose
detailed_model = (args.level > 1) or args.detailed
csv_mode = args.csv
interval_mode = args.interval
ring_filter = ""
if args.kernel:
    ring_filter = 'k'
if args.user:
    ring_filter = 'u'
if args.user and args.kernel:
    ring_filter = None
print_group = args.print_group

MAX_ERROR = 0.05

def check_ratio(l):
    if print_all:
        return True
    return 0 - MAX_ERROR < l < 1 + MAX_ERROR

cpu = CPU(known_cpus)

def print_perf(r):
    if args.quiet:
        return
    l = ["'" + x + "'" if x.find("{") >= 0 else x for x in r]
    l = [x.replace(";", "\;") for x in l]
    i = l.index('--log-fd')
    del l[i:i+2]
    print " ".join(l)
    sys.stdout.flush()

class PerfRun:
    """Control a perf subprocess."""
    def execute(self, r):
        outp, inp = pty.openpty()
        n = r.index("--log-fd")
        r[n + 1] = "%d" % (inp)
        print_perf(r)
        self.perf = subprocess.Popen(r)
        os.close(inp)
        return os.fdopen(outp, 'r')

    def wait(self):
        ret = 0
        if self.perf:
            ret = self.perf.wait()
        return ret

fixed_counters = {
    "CPU_CLK_UNHALTED.THREAD": "cycles",
    "CPU_CLK_UNHALTED.THREAD:amt1": "cpu/event=0x3c,umask=0x0,any=1/",
    "INST_RETIRED.ANY": "instructions",
    "CPU_CLK_UNHALTED.REF_TSC": "ref-cycles",
    "CPU_CLK_UNHALTED.REF_TSC:amt1": "cpu/event=0x0,umask=0x3,any=1/",
    "CPU_CLK_UNHALTED.REF_TSC:sup": "cpu/event=0x0,umask=0x3/k",
    "CPU_CLK_UNHALTED.REF_TSC:SUP": "cpu/event=0x0,umask=0x3/k",
}

fixed_set = frozenset(fixed_counters.keys())
fixed_to_name = dict(zip(fixed_counters.values(), fixed_counters.keys()))

def separator(x):
    if x.startswith("cpu"):
        return ""
    return ":"

def add_filter_event(e):
    if "/" in e and not e.startswith("cpu"):
        return e
    s = separator(e)
    if not e.endswith(s + ring_filter):
        return e + s + ring_filter
    return e

def add_filter(s):
    if ring_filter:
        s = map(add_filter_event, s)
    return s

notfound_cache = set()

def raw_event(i, name="", period=False):
    orig_i = i
    if i.count(".") > 0:
        if i in fixed_counters:
            return fixed_counters[i]
        e = emap.getevent(i)
        if e is None:
            if i in event_fixes:
                e = emap.getevent(event_fixes[i])
        if e is None:
            if i not in notfound_cache:
                notfound_cache.add(i)
                print >>sys.stderr, "%s not found" % (i,)
            return "dummy"
        oi = i
        i = e.output(noname=True, name=name, period=period)
        if len(re.findall(r'[a-z0-9_]+/.*?/[a-z]*', i)) > 1:
            print "Event", oi, "maps to multiple units. Ignored."
            return "dummy" # FIXME
        emap.update_event(e.output(noname=True), e)
        # next three things should be moved somewhere else
        if i.startswith("uncore"):
            outgroup_events.add(i)
        if e.counter != cpu.standard_counters and not e.counter.startswith("Fixed"):
            # for now use the first counter only to simplify
            # the assignment. This is sufficient for current
            # CPUs
            limited_counters[i] = int(e.counter.split(",")[0])
            limited_set.add(i)
        if e.errata:
            if e.errata in errata_whitelist:
                errata_events[orig_i] = e.errata
            else:
                errata_warn_events[orig_i] = e.errata
    return i

# generate list of converted raw events from events string
def raw_events(evlist):
    return map(raw_event, evlist)

def mark_fixed(s):
    r = raw_event(s)
    if r in ingroup_events:
        return "%s[F]" % s
    return s

def pwrap(s, linelen=70, indent=""):
    print indent + ("\n" + indent).join(textwrap.wrap(s, linelen, break_long_words=False))

def pwrap_not_quiet(s, linelen=70, indent=""):
    if not args.quiet:
        pwrap(s, linelen, indent)

def has(obj, name):
    return name in obj.__class__.__dict__

def flatten(x):
    return itertools.chain(*x)

def print_header(work, evlist):
    evnames0 = [obj.evlist for obj in work]
    evnames = set(flatten(evnames0))
    names = ["%s[%d]" % (obj.__class__.__name__, obj.__class__.level if has(obj, 'level') else 0) for obj in work]
    pwrap(" ".join(names) + ":", 78)
    pwrap(" ".join(map(mark_fixed, evnames)).lower() +
          " [%d counters]" % (needed_counters(raw_events(evnames))), 75, "  ")

def perf_args(evstr, rest):
    add = []
    if interval_mode:
        add += ['-I', str(interval_mode)]
    return [perf, "stat", "-x;", "--log-fd", "X", "-e", evstr]  + add + rest

def setup_perf(evstr, rest):
    prun = PerfRun()
    inf = prun.execute(perf_args(evstr, rest))
    return inf, prun

class Stat:
    def __init__(self):
        self.total = 0
        self.errors = Counter()

def print_not(a, count , msg, j):
     print >>sys.stderr, ("%s %s %s %.2f%% in %d measurements"
                % (emap.getperf(j), j, msg, 100.0 * (float(count) / float(a.total)), a.total))

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
        print >>sys.stderr, ", ".join(["%d events %s" % (num, e) for e, num in total.iteritems()])

class ValidEvents:
    def update(self):
        self.string = "|".join(self.valid_events)

    def __init__(self):
        self.valid_events = [r"cpu/.*?/", "uncore.*?/.*?/", "ref-cycles",
                             r"r[0-9a-fA-F]+", "cycles", "instructions", "dummy"]
        self.update()

    def add_event(self, ev):
        # add first to overwrite more generic regexprs list r...
        self.valid_events.insert(0, ev)
        self.update()

valid_events = ValidEvents()

def is_event(l, n):
    if len(l) <= n:
        return False
    # use static string to make regexpr caching work
    return re.match(valid_events.string, l[n])

def set_interval(env, d):
    env['interval-ns'] = d * 1e9
    if args.raw:
        print "interval-ns val", env['interval-ns']

def key_to_coreid(k):
    x = cpu.cputocore[int(k)]
    return x[0] * 1000 + x[1]

def core_fmt(core):
    if cpu.sockets > 1:
        return "S%d-C%d" % (core / 1000, core % 1000,)
    return "C%d" % (core % 1000,)

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

def display_keys(runner, keys):
    if len(keys) > 1 and smt_mode:
        cores = [key_to_coreid(x) for x in keys if int(x) in runner.allowed_threads]
        threads = map(thread_fmt, runner.allowed_threads)
        all_cpus = list(set(map(core_fmt, cores) + threads))
    else:
        all_cpus = keys
    if any(map(package_node, runner.olist)):
        all_cpus += ["S%d" % x for x in range(cpu.sockets)]
    return all_cpus

def print_keys(runner, res, rev, valstats, out, interval, env):
    stat = runner.stat
    out.set_cpus(display_keys(runner, res.keys()))
    if smt_mode:
        printed_cores = set()
        for j in sorted(res.keys()):
            if j != "" and int(j) not in runner.allowed_threads:
                continue

            runner.reset_thresh()

            # collect counts from all threads of cores as lists
            # this way the model can access all threads individually
            core = key_to_coreid(j)
            cpus = [x for x in res.keys() if key_to_coreid(x) == core]
            combined_res = zip(*[res[x] for x in cpus])
            st = [combine_valstat(z) for z in itertools.izip(*[valstats[x] for x in cpus])]

            # repeat a few times to get stable threshold values
            # in case of mutual dependencies between SMT and non SMT
            # XXX use better algorithm
            used_stat = stat
            for _ in range(3):
                runner.compute(res[j], rev[j], valstats[j], env, thread_node, used_stat)
                runner.compute(combined_res, rev[cpus[0]], st, env, core_node, used_stat)
                used_stat = None

            # find bottleneck
            bn = find_bn(runner.olist, not_package_node)

            # print the SMT aware nodes
            if core not in printed_cores:
                runner.print_res(out, interval, core_fmt(core), core_node, bn)
                printed_cores.add(core)

            # print the non SMT nodes
            # recompute the nodes so we get up-to-date values
            runner.print_res(out, interval, thread_fmt(j), thread_node, bn)
    else:
        for j in sorted(res.keys()):
            if j != "" and int(j) not in runner.allowed_threads:
                continue
            runner.compute(res[j], rev[j], valstats[j], env, not_package_node, stat)
            bn = find_bn(runner.olist, not_package_node)
            runner.print_res(out, interval, j, not_package_node, bn)
    packages = set()
    for j in sorted(res.keys()):
        if j == "":
            continue
        if int(j) not in runner.allowed_threads:
            continue
        p_id = cpu.cputosocket[int(j)]
        if p_id in packages:
            continue
        packages.add(p_id)
        runner.compute(res[j], rev[j], valstats[j], env, package_node, stat)
        runner.print_res(out, interval, "S%d" % p_id, package_node, None)
        # no bottlenecks from package nodes for now
    out.flush()
    stat.referenced_check(res)
    stat.compute_errors()

def print_and_sum_keys(runner, res, rev, valstats, out, interval, env):
    if runner.summary:
	runner.summary.add(res, rev, valstats, env);
    print_keys(runner, res, rev, valstats, out, interval, env)

def print_summary(runner, out):
    if not args.summary:
	return
    print_keys(runner, runner.summary.res, runner.summary.rev,
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
        except exceptions.IOError:
            self.startoffset = None

    def restore(self):
        if self.startoffset is not None:
            sys.stdin.seek(self.startoffset)

def execute_no_multiplex(runner, out, rest):
    if args.interval: # XXX
        sys.exit('--no-multiplex is not supported with interval mode')
    res = defaultdict(list)
    rev = defaultdict(list)
    valstats = defaultdict(list)
    env = dict()
    groups = [x for x in runner.evgroups if len(x) > 0]
    num_runs = len(groups) - count(is_outgroup, groups)
    outg = []
    n = 0
    ctx = SaveContext()
    # runs could be further reduced by tweaking
    # the scheduler to avoid any duplicated events
    for g in groups:
        if is_outgroup(g):
            outg.append(g)
            continue
        n += 1
        print "RUN #%d of %d" % (n, num_runs)
        ret, res, rev, interval, valstats = do_execute(runner, outg + [g], out, rest,
                                                 res, rev, valstats, env)
        ctx.restore()
        outg = []
    assert num_runs == n
    print_and_sum_keys(runner, res, rev, valstats, out, interval, env)
    return ret

def execute(runner, out, rest):
    env = dict()
    events = filter(lambda x: len(x) > 0, runner.evgroups)
    ctx = SaveContext()
    ret, res, rev, interval, valstats = do_execute(runner, events,
                                         out, rest,
                                         defaultdict(list),
                                         defaultdict(list),
                                         defaultdict(list),
                                         env)
    ctx.restore()
    print_and_sum_keys(runner, res, rev, valstats, out, interval, env)
    return ret

def group_number(num, events):
    gnum = itertools.count(1)
    def group_nums(group):
        if all([x in outgroup_events for x in group]):
            idx = 0
        else:
            idx = gnum.next()
        return [idx] * len(group)

    gnums = map(group_nums, events)
    return list(flatten(gnums))[num]

def dump_raw(interval, title, event, val, index, events, stddev, multiplex):
    if event in fixed_to_name:
        ename = fixed_to_name[event].lower()
    else:
        ename = event_rmap(event)
    gnum = group_number(index, events)
    if args.raw:
        print "raw", title, "event", event, "val", val, "ename", ename, "index", index, "group", gnum
    if args.valcsv:
        runner.valcsv.writerow((interval, title, gnum, ename, val, event, index, stddev, multiplex))

perf_fields = [
    r"[0-9.]+",
    r"<.*?>",
    r"S\d+-C\d+?",
    r"S\d+",
    r"raw 0x[0-9a-f]+",
    r"Joules",
    ""]

def do_execute(runner, events, out, rest, res, rev, valstats, env):
    evstr = ",".join(map(event_group, events))
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
            l = l.strip()

            # some perf versions break CSV output lines incorrectly for power events
            if l.endswith("Joules"):
                l2 = inf.readline()
                l = l + l2.strip()
        except exceptions.IOError:
             # handle pty EIO
             break
        except KeyboardInterrupt:
            continue
        if interval_mode:
            m = re.match(r"\s*([0-9.]+);(.*)", l)
            if m:
                interval = float(m.group(1))
                l = m.group(2)
                if interval != prev_interval:
                    if res:
                        set_interval(env, interval - prev_interval)
			print_and_sum_keys(runner, res, rev, valstats, out, prev_interval, env)
                        res = defaultdict(list)
                        rev = defaultdict(list)
                        valstats = defaultdict(list)
                    prev_interval = interval

        n = l.split(";")

        # filter out the empty unit field added by 3.14
        n = filter(lambda x: x != "" and x != "Joules", n)

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
            print "unparseable perf output"
            sys.stdout.write(l)
            continue
        title = title.replace("CPU", "")
        # code later relies on stripping ku flags
        event = event.replace("/k", "/").replace("/u", "/")

        multiplex = float('nan')
        event = event.rstrip()
        if re.match(r"[0-9.]+", count):
            val = float(count)
        elif count.startswith("<"):
            account[event].errors[count.replace("<","").replace(">","")] += 1
            multiplex = 0.
            val = 0
        else:
            print "unparseable perf count"
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

        # power/uncore events are only output once for every socket. duplicate them
        # to all cpus in the socket to make the result lists match
        # unless we use -A ??
        # also -C xxx causes them to be duplicated too, unless single thread
        if ((event.startswith("power") or event.startswith("uncore")) and
                title != "" and (not (args.core and not args.single_thread))):
            cpunum = int(title)
            socket = cpu.cputosocket[cpunum]
            for j in cpu.sockettocpus[socket]:
                if not args.core or display_core(j, True):
                    res["%d" % (j)].append(val)
                    rev["%d" % (j)].append(event)
                    valstats["%d" % (j)].append(st)
        else:
            res[title].append(val)
            rev[title].append(event)
            valstats[title].append(st)

        if args.raw or args.valcsv:
            dump_raw(interval if interval_mode else "",
                     title,
                     event,
                     val,
                     len(res[title]) - len(init_res[title]) - 1,
                     events, stddev, multiplex)
    inf.close()
    if 'interval-ns' not in env:
            set_interval(env, time.time() - start)
    ret = prun.wait()
    print_account(account)
    return ret, res, rev, interval, valstats

def ev_append(ev, level, obj):
    if isinstance(ev, types.LambdaType):
        return ev(lambda ev, level: ev_append(ev, level, obj), level)
    if ev in nonperf_events:
        return 99
    if not (ev, level, obj.name) in obj.evlevels:
        obj.evlevels.append((ev, level, obj.name))
    if has(obj, 'nogroup') and obj.nogroup:
        outgroup_events.add(ev.lower())
    if not ev.startswith("cpu"):
        valid_events.add_event(ev)
    return 99

def canon_event(e):
    m = re.match(r"(.*?):(.*)", e)
    if m and m.group(2) != "amt1" and m.group(2) not in ("sup", "SUP"):
        e = m.group(1)
    if e in fixed_counters:
        return fixed_counters[e]
    if m:
        e = m.group(1)
    if e.endswith("_0"):
        e = e[:-2]
    return e.lower()

fixes = dict(zip(event_fixes.values(), event_fixes.keys()))

def do_event_rmap(e):
    n = canon_event(emap.getperf(e))
    if emap.getevent(n):
        return n
    if n.upper() in fixes:
        n = fixes[n.upper()].lower()
        if n:
            return n
    return "dummy"

rmap_cache = dict()

def event_rmap(e):
    if e in rmap_cache:
        return rmap_cache[e]
    n = do_event_rmap(e)
    rmap_cache[e] = n
    return n

def lookup_res(res, rev, ev, obj, env, level, referenced, cpuoff, st):
    if ev in env:
        return env[ev]
    if ev == "mux":
        return combine_valstat(st).multiplex
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
                       for off in range(cpu.threads)])

    index = obj.res_map[(ev, level, obj.name)]
    referenced.add(index)
    #print (ev, level, obj.name), "->", index
    rmap_ev = event_rmap(rev[index]).lower()
    assert (rmap_ev == canon_event(ev).replace("/k", "/") or
                (ev in event_fixes and canon_event(event_fixes[ev]) == rmap_ev) or
                rmap_ev == "dummy")

    if isinstance(res[index], types.TupleType):
        if cpuoff == -1:
            return sum(res[index])
        else:
            try:
                return res[index][cpuoff]
            except IndexError:
                print >>sys.stderr, "warning: Partial CPU thread data from perf"
                return 0
    return res[index]

def add_key(k, x, y):
    k[x] = y

# dedup a and keep b uptodate
def dedup2(a, b):
    k = dict()
    map(lambda x, y: add_key(k, x, y), a, b)
    return k.keys(), map(lambda x: k[x], k.keys())

def cmp_obj(a, b):
    if a.level == b.level:
        return a.nc - b.nc
    return a.level - b.level

def update_res_map(evnum, objl, base):
    for obj in objl:
        for lev in obj.evlevels:
            r = raw_event(lev[0])
            if r in evnum:
                obj.res_map[lev] = base + evnum.index(r)

class BadEvent:
    def __init__(self, name):
        self.event = name

# XXX check for errata
def sample_event(e):
    ev = emap.getevent(e.replace("_PS", ""))
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
    except BadEvent as e:
        #return "Unknown sample event %s" % (e.event)
        return ""

def get_levels(evlev):
    return [x[1] for x in evlev]

def get_names(evlev):
    return [x[0] for x in evlev]

def grab_group(l):
    n = 1
    while needed_counters(l[:n]) < cpu.counters and n < len(l):
        n += 1
    if needed_counters(l[:n]) > cpu.counters and n > 0:
        n -= 1
    return n

def full_name(obj):
    name = obj.name
    while 'parent' in obj.__dict__ and obj.parent:
        obj = obj.parent
        name = obj.name + "." + name
    return name

def package_node(obj):
    return has(obj, 'domain') and obj.domain == "Package"

def not_package_node(obj):
    return not package_node(obj)

def core_node(obj):
    return has(obj, 'domain') and obj.domain in smt_domains

def thread_node(obj):
    if package_node(obj):
        return False
    if obj.metric and not (has(obj, 'domain') and obj.domain == "CoreMetric"):
        return True
    return not core_node(obj)

def count(f, l):
    return len(filter(f, l))

def metric_unit(obj):
    if has(obj, 'unit'):
        return obj.unit
    if has(obj, 'domain'):
        return obj.domain
    return "Metric"

# only check direct children, the rest are handled recursively
def children_over(l, obj):
    n = [o.thresh for o in l if 'parent' in o.__dict__ and o.parent == obj]
    return any(n)

def obj_desc(obj, rest):
    # hide description if children are also printed
    if not args.long_desc and children_over(rest, obj):
        desc = ""
    else:
        desc = obj.desc[1:].replace("\n", "\n\t")

    # by default limit to first sentence
    if not args.long_desc and "." in desc:
        desc = desc[:desc.find(".") + 1] + ".."

    if 'htoff' in obj.__dict__ and obj.htoff and obj.thresh and cpu.ht and not args.single_thread:
        desc += """
Warning: Hyper Threading may lead to incorrect measurements for this node.
Suggest to re-measure with HT off (run cputop.py "thread == 1" offline | sh)."""
    return desc

def node_filter(obj, test):
    if args.nodes:
        fname = full_name(obj)
        name = obj.name

        def match(m):
            return fnmatch.fnmatch(name, m) or fnmatch.fnmatch(fname, m)

        for j in args.nodes.split(","):
            i = 0
            if j[0] == '^':
                if match(j[1:]):
                    return False
                continue
            elif j[0] == '+':
                i += 1
            if match(j[i:]):
                return True
    return test()

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
    bn = [o for o in olist if match(o) and o.thresh and not o.metric]
    if len(bn) == 0:
        return None
    return _find_bn(bn, 0)

pmu_does_not_exist = set()

def missing_pmu(e):
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
        if has(obj, 'metricgroup'):
            for g in obj.metricgroup:
                for j in mg[g]:
                    if j not in visited and j in valid:
                        ml.append(j)
                        visited.add(j)
        else:
            ml.append(obj)
    return ml

def node_unit(obj):
    return (((" " + obj.domain) if has(obj, 'domain') else "") +
             (" below" if not obj.thresh else ""))

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

class Runner:
    """Schedule measurements of event groups. Map events to groups."""

    def __init__(self, max_level):
        self.evnum = [] # flat global list
        self.evgroups = list()
        self.evbases = list()
        self.olist = []
        self.max_level = max_level
        self.missed = 0
        self.sample_obj = set()
        self.stat = ComputeStat(args.quiet)
        # always needs to be filtered by olist:
        self.metricgroups = defaultdict(list)
        if args.valcsv:
            self.valcsv = csv.writer(args.valcsv)
            self.valcsv.writerow(("Timestamp", "CPU" ,"Group", "Event", "Value",
                                  "Perf-event", "Index", "STDEV", "MULTI"))
	self.summary = None
	if args.summary:
	    self.summary = Summary()

    def do_run(self, obj):
        obj.res = None
        obj.res_map = dict()
        self.olist.append(obj)
        if has(obj, 'metricgroup'):
            for j in obj.metricgroup:
                self.metricgroups[j].append(obj)

    # remove unwanted nodes after their parent relation ship has been set up
    def filter_nodes(self):
        def want_node(obj):
            if args.reduced and has(obj, 'server') and not obj.server:
                return False
            if not obj.metric:
                return node_filter(obj, lambda: obj.level <= self.max_level)
            else:
                return node_filter(obj, lambda: args.metrics)

        self.olist = filter(want_node, self.olist)

    def reset_thresh(self):
        for obj in self.olist:
            if not obj.metric:
                obj.thresh = False

    def run(self, obj):
        obj.thresh = False
        obj.metric = False
        self.do_run(obj)

    def metric(self, obj):
        obj.thresh = True
        obj.metric = True
        obj.level = 0
        obj.sibling = None
        self.do_run(obj)

    def split_groups(self, objl, evlev):
        if len(set(get_levels(evlev))) == 1:
            # when there is only a single left just fill groups
            while evlev:
                n = grab_group(map(raw_event, get_names(evlev)))
                l = evlev[:n]
                self.add(objl, raw_events(get_names(l)), l, True)
                evlev = evlev[n:]
        else:
            # resubmit groups for each level
            max_level = max(get_levels(evlev))
            for l in range(1, max_level + 1):
                # FIXME: filter objl by level too
                evl = filter(lambda x: x[1] == l, evlev)
                if evl:
                    self.add(objl, raw_events(get_names(evl)), evl)

    def add_duplicate(self, evnum, objl):
        evset = set(evnum)
        for j, base in zip(self.evgroups, self.evbases):
            # cannot add super sets, as that would need patching
            # up all indexes inbetween.
            if evset <= set(j):
                if args.debug:
                    print "add_duplicate", evnum, base, map(event_rmap, evnum), "in", j
                update_res_map(j, objl, base)
                return True
            # for now...
            elif needed_counters(set(evnum) | set(j)) <= cpu.counters:
                self.missed += 1
        return False

    def add(self, objl, evnum, evlev, force=False):
        # does not fit into a group.
        if needed_counters(evnum) > cpu.counters and not force:
            self.split_groups(objl, evlev)
            return
        evnum, evlev = dedup2(evnum, evlev)
        if not self.add_duplicate(evnum, objl):
            base = len(self.evnum)
            if args.debug:
                print "add", evnum, base, map(event_rmap, evnum)
            update_res_map(evnum, objl, base)
            self.evnum += evnum
            self.evgroups.append(evnum)
            self.evbases.append(base)
            if print_group:
                print_header(objl, get_names(evlev))

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
            obj.evlist = [x[0] for x in obj.evlevels]
            obj.evnum = raw_events(obj.evlist)
            obj.nc = needed_counters(obj.evnum)

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
                        print "Fixed in kernel %d.%d" % (sorted(min_kernel, key=kv_to_key, reverse=True)[0])
                    print "Use --force-events to override (may result in wrong measurements)"
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

    # fit events into available counters
    # simple first fit algorithm
    def schedule(self):
        curobj = []
        curev = []
        curlev = []
        # sort objects by level and inside each level by num-counters
        solist = sorted(self.olist, cmp=cmp_obj)
        # try to fit each objects events into groups
        # that fit into the available CPU counters
        for obj in solist:
            if not (set(obj.evnum) - outgroup_events):
                self.add([obj], obj.evnum, obj.evlevels)
                continue
            # try adding another object to the current group
            newev = curev + obj.evnum
            newlev = curlev + obj.evlevels
            needed = needed_counters(newev)
            # when the current group doesn't have enough free slots
            # or is already too large
            # start a new group
            if cpu.counters < needed and curobj:
                self.add(curobj, curev, curlev)
                # restart new group
                curobj = []
                curev = []
                curlev = []
                newev = obj.evnum
                newlev = obj.evlevels
            # commit the object to the group
            curobj.append(obj)
            curev = newev
            curlev = newlev
        if curobj:
            self.add(curobj, curev, curlev)
        if print_group:
            num_groups = len([x for x in self.evgroups if needed_counters(x) <= cpu.counters])
            print "%d groups, %d non-groups with %d events total (%d unique) for %d objects, missed %d merges" % (
                num_groups,
                len(self.evgroups) - num_groups, 
                len(self.evnum),
                len(set(self.evnum)),
                len(self.olist),
                self.missed)

    def propagate_siblings(self):
        for obj in self.olist:
            if obj.thresh and obj.sibling:
                if isinstance(obj.sibling, (list, tuple)):
                    for k in obj.sibling:
                        k.thresh = True
                else:
                    obj.sibling.thresh = True

    def compute(self, res, rev, valstats, env, match, stat):
        if len(res) == 0:
            print "Nothing measured?"
            return

        # step 1: compute
        for obj in self.olist:
            obj.errcount = 0

            if not match(obj):
                continue
            ref = set()
            obj.compute(lambda e, level:
                            lookup_res(res, rev, e, obj, env, level, ref, -1, valstats))
            if stat:
                stat.referenced |= ref
            obj.valstat = combine_valstat([valstats[i] for i in ref])
            if not obj.res_map and not all([x in env for x in obj.evnum]):
                print >>sys.stderr, "%s not measured" % (obj.__class__.__name__,)
            if not obj.metric and not check_ratio(obj.val):
                obj.thresh = False
                if stat:
                    stat.mismeasured.add(obj.name)
            if stat and has(obj, 'errcount') and obj.errcount > 0:
                if obj.name not in stat.errors:
                    stat.errcount += obj.errcount
                stat.errors.add(obj.name)

        # step 2: propagate siblings
        self.propagate_siblings()

    def print_res(self, out, timestamp, title, match, bn):
        out.logf.flush()

        # determine all objects to print
        olist = []
        for obj in self.olist:
            if obj.thresh or print_all:
                if not match(obj):
                    pass
                elif obj.metric:
                    if print_all or obj.val != 0:
                        olist.append(obj)
                elif check_ratio(obj.val):
                    olist.append(obj)

        # sort by metric group
        olist = olist_by_metricgroup(olist, self.metricgroups)

        # pre compute column lengths
        for obj in olist:
            out.set_hdr(full_name(obj), obj.area if has(obj, 'area') else None)
            if obj.metric:
                out.set_unit(metric_unit(obj))
            else:
                out.set_unit(node_unit(obj))

        # step 3: print
        for i, obj in enumerate(olist):
            val = obj.val
            desc = obj_desc(obj, olist[i + 1:])
            if obj.metric:
                out.metric(obj.area if has(obj, 'area') else None,
                        obj.name, val, timestamp,
                        desc,
                        title,
                        metric_unit(obj),
                        obj.valstat)
            elif check_ratio(val):
                out.ratio(obj.area if has(obj, 'area') else None,
                        full_name(obj), val, timestamp,
                        node_unit(obj),
                        desc,
                        title,
                        sample_desc(obj.sample) if has(obj, 'sample') else None,
                        obj.valstat,
                        "BN" if obj == bn else "")
                if obj.thresh or args.verbose:
                    self.sample_obj.add(obj)

def remove_pp(s):
    if s.endswith(":pp"):
        return s[:-3]
    return s

def clean_event(e):
    return remove_pp(e).replace(".", "_").replace(":", "_").replace('=','')

def do_sample(sample_obj, rest, count):
    # XXX use :ppp if available
    samples = [("cycles:pp", "Precise cycles", )]
    for obj in sample_obj:
        for s in obj.sample:
            samples.append((s, obj.name))
    nsamp = [x for x in samples if not unsup_event(x[0], unsup_events)]
    nsamp = [(remove_pp(x[0]), x[1]) if unsup_event(x[0], unsup_pebs) else x
                for x in nsamp]
    if cmp(nsamp, samples):
        missing = [x[0] for x in set(samples) - set(nsamp)]
        if not args.quiet:
            print >>sys.stderr, "warning: update kernel to handle sample events:"
            print >>sys.stderr, "\n".join(missing)
    sl = [raw_event(s[0], s[1] + "_" + clean_event(s[0]), period=True) for s in nsamp]
    sl = add_filter(sl)
    sample = ",".join([x for x in sl if x])
    print "Sampling:"
    extra_args = args.sample_args.replace("+", "-").split()
    perf_data = args.sample_basename
    if count:
        perf_data += ".%d" % count
    sperf = [perf, "record" ] + extra_args + ["-e", sample, "-o", perf_data] + [x for x in rest if x != "-A"]
    print " ".join(sperf)
    if args.run_sample:
        ret = os.system(" ".join(sperf))
        if ret:
            print "Sampling failed"
            sys.exit(1)
        if not args.quiet:
            print "Run `" + perf + " report %s%s' to show the sampling results" % (
                ("-i %s" % perf_data) if perf_data != "perf_data" else "",
                " --no-branch-history"  if "-b" in extra_args else "")

def sysctl(name):
    try:
        with open("/proc/sys/" + name.replace(".","/"), "r") as f:
            val = int(f.readline())
    except IOError:
        return 0
    return val

# check nmi watchdog
if sysctl("kernel.nmi_watchdog") != 0:
    sys.exit("Please disable the NMI watchdog as it permanently consumes one "
             "hw-PMU counter.\n"
             "(echo 0 > /proc/sys/kernel/nmi_watchdog)")

if cpu.cpu is None:
    sys.exit("Unsupported CPU model %d" % (cpu.model,))

kv = os.getenv("KERNEL_VERSION")
if not kv:
    kv = platform.release()
kernel_version = map(int, kv.split(".")[:2])

def ht_warning():
    if cpu.ht and not args.quiet:
        print >>sys.stderr, "WARNING: HT enabled"
        print >>sys.stderr, "Measuring multiple processes/threads on the same core may is not reliable."

runner = Runner(args.level)

pe = lambda x: None
if args.debug:
    pe = lambda x: sys.stdout.write(x + "\n")

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
elif cpu.cpu == "slm":
    import slm_ratios
    model = slm_ratios
else:
    ht_warning()
    if detailed_model and not args.quiet:
        print >>sys.stderr, "Sorry, no detailed model for your CPU. Only Level 1 supported."
    import simple_ratios
    model = simple_ratios

version = model.version
model.print_error = pe
model.Setup(runner)

def setup_with_metrics(p, runner):
    old_metrics = args.metrics
    args.metrics = True
    p.Setup(runner)
    args.metrics = old_metrics

def check_root():
    if not (os.geteuid() == 0 or sysctl("kernel.perf_event_paranoid") == -1) and not args.quiet:
        print >>sys.stderr, "Warning: Needs root or echo -1 > /proc/sys/kernel/perf_event_paranoid"

runner.filter_nodes()

if not args.no_util:
    import perf_metrics
    setup_with_metrics(perf_metrics, runner)

if args.power and feat.supports_power:
    import power_metrics
    setup_with_metrics(power_metrics, runner)
    if not args.quiet:
        print "Running with --power. Will measure complete system."
    check_root()
    if "-a" not in rest:
        rest = ["-a"] + rest

if args.sw:
    import linux_metrics
    setup_with_metrics(linux_metrics, runner)

if args.tsx and cpu.has_tsx and cpu.cpu in tsx_cpus:
    import tsx_metrics
    setup_with_metrics(tsx_metrics, runner)

if args.frequency:
    import frequency
    old_metrics = args.metrics
    args.metrics = True
    frequency.SetupCPU(runner, cpu)
    args.metrics = old_metrics

if "--per-socket" in rest:
    sys.exit("toplev not compatible with --per-socket")
if "--per-core" in rest:
    sys.exit("toplev not compatible with --per-core")

if not args.single_thread and cpu.ht:
    if not args.quiet:
        print "Will measure complete system."
    if smt_mode:
        if args.cpu:
            print >>sys.stderr, "Warning: --cpu/-C mode with HyperThread must specify all core thread pairs!"
        if args.pid:
            sys.exit("-p/--pid mode not compatible with SMT. Use sleep in global mode.")
    check_root()
    if "-a" not in rest:
        rest = ["-a"] + rest
    if "-A" not in rest:
        rest = ["-A"] + rest

if args.core:
    runner.allowed_threads = [x for x in cpu.allcpus if display_core(x, False)]
    allowed_cores = [x for x in cpu.allcpus if display_core(x, True)]
    rest = ["-C", ",".join(["%d" % x for x in allowed_cores])] + rest
else:
    runner.allowed_threads = cpu.allcpus

if not args.quiet:
    print "Using level %d." % (args.level),
    if not args.level and cpu.cpu != "slm":
        print "Change level with -lX"
    print

if args.repl:
    import code
    code.interact(banner='toplev repl', local=locals())
    sys.exit(0)

runner.collect()
if csv_mode:
    if args.columns:
        out = tl_output.OutputColumnsCSV(args.output, csv_mode, args, version, cpu)
    else:
        out = tl_output.OutputCSV(args.output, csv_mode, args, version, cpu)
elif args.columns:
    out = tl_output.OutputColumns(args.output, args, version)
else:
    out = tl_output.OutputHuman(args.output, args, version)
runner.schedule()

def measure_and_sample(count):
    try:
        if args.no_multiplex:
            ret = execute_no_multiplex(runner, out, rest)
        else:
            ret = execute(runner, out, rest)
    except KeyboardInterrupt:
	print_summary(runner, out)
        sys.exit(1)
    print_summary(runner, out)
    runner.stat.compute_errors()
    if args.show_sample or args.run_sample:
        do_sample(runner.sample_obj, rest, count)
    return ret

if args.sample_repeat:
    for j in range(args.sample_repeat):
        ret = measure_and_sample(j + 1)
        if ret:
            break
else:
    ret = measure_and_sample(None)

sys.exit(ret)
