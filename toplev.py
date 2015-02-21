#!/usr/bin/python
# Copyright (c) 2012-2015, Intel Corporation
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
# must find ocperf in python module path. add to paths below if needed.
# Handles a variety of perf versions, but older ones have various limitations.

import sys, os, re, itertools, textwrap, platform, pty, subprocess
import exceptions, argparse, time, types
from collections import defaultdict, Counter
#sys.path.append("../pmu-tools")
import ocperf

known_cpus = (
    ("snb", (42, )),
    ("jkt", (45, )),
    ("ivb", (58, )),
    ("ivt", (62, )),
    ("hsw", (60, 70, 69 )),
    ("hsx", (63, )),
    ("slm", (55, 77)),
    ("bdw", (61, )),
)

tsx_cpus = ("hsw", "hsx", "bdw")

fixed_to_num = {
    "instructions" : 0,
    "cycles" : 1,
    "cpu/event=0x3c,umask=0x00,any=1/": 1,
    "cpu/event=0x3c,umask=0x0,any=1/": 1,
    "ref-cycles" : 2,
    "cpu/event=0x0,umask=0x3,any=1/" : 2,
}

ingroup_events = frozenset(fixed_to_num.keys())

outgroup_events = set()

nonperf_events = {"interval-ns"}

valid_events = [r"cpu/.*?/", "ref-cycles", r"r[0-9a-fA-F]+", "cycles", "instructions"]

# workaround for broken event files for now
event_fixes = {
    "UOPS_EXECUTED.CYCLES_GE_1_UOPS_EXEC": "UOPS_EXECUTED.CYCLES_GE_1_UOP_EXEC",
    "UOPS_EXECUTED.CYCLES_GE_1_UOP_EXEC": "UOPS_EXECUTED.CYCLES_GE_1_UOPS_EXEC"
}

smt_domains = ("Slots", "CoreClocks", "CoreMetric")

smt_mode = False

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

def needed_fixed(evlist):
    fixed_only = set(evlist) & ingroup_events
    return sum(Counter([fixed_to_num[x] for x in fixed_only]).values())

MAX_FIXED = 3

def needed_counters(evlist):
    num_generic = len(set(evlist) - ingroup_events)
    # If we need more than 3 fixed counters (happens with any vs no any)
    # promote those to generic counters
    num_fixed = needed_fixed(evlist)
    #print "num_generic", num_generic, "num_fixed", num_fixed, "evlist", evlist
    if num_fixed > MAX_FIXED:
        num_generic += num_fixed - MAX_FIXED
    return num_generic

def event_group(evlist):
    e = ",".join(add_filter(evlist))
    if not args.no_group and 1 < needed_counters(evlist) <= cpu.counters:
        e = "{%s}" % (e,)
    return e

feat = PerfFeatures()
emap = ocperf.find_emap()
if not emap:
    sys.exit("Unknown CPU or CPU event map not found.")

p = argparse.ArgumentParser(usage='toplev [options] perf-arguments',
description='''
Estimate on which part of the CPU pipeline a workload bottlenecks using the TopDown model.
The bottlenecks are expressed as a tree with different levels.

Requires an Intel Sandy, Ivy Bridge, Haswell CPU.
It works best on Ivy Bridge currently.
On Sandy Bridge Server use Sandy Bridge (FORCECPU=snb)

Examples:

./toplev.py -l2 program
measure program in level 2

./toplev.py -a sleep X
measure whole system for X seconds

./toplev.py -o logfile.csv -x, -p PID
measure pid PID, outputting in CSV format
''', epilog='''
Other perf arguments allowed (see the perf documentation)
After -- perf arguments conflicting with toplev can be used.

Some caveats:

The lower levels of the measurement tree are less reliable
than the higher levels.  They also rely on counter multi-plexing,
and can not run each equation in a single group, which can cause larger
measurement errors with non steady state workloads

(If you don't understand this terminology; it means measurements
in higher levels are less accurate and it works best with programs that primarily
do the same thing over and over)

In this case it's recommended to measure the program only after
the startup phase by profiling globally or attaching later.
level 1 or running without -d is generally the most reliable.

If the program is very reproducible -- such as a simple kernel --
it is also possible to use --no-multiplex. In this case the
workload is rerun multiple times until all data is collected.
Do not use together with sleep.

One of the events (even used by level 1) requires a recent enough
kernel that understands its counter constraints.  3.10+ is safe.

Various older kernels (such as 2.6.32) can not schedule all groups
used by toplev correctly. In this case use --no-group (may cause
additional measurement errors)

In Hyper Threading mode toplev defaults to measuring the whole
system.

Recent kernels do not allow all events needed by level 3 or larger
in Hyper Threading mode due to a bug workaround. If that is needed
please see the github site for a kernel patch.

Other CPUs can be forced with FORCECPU=name
Valid CPU names: ''' + " ".join([x[0] for x in known_cpus]),
formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument('--verbose', '-v', help='Print all results even when below threshold',
               action='store_true')
p.add_argument('--force', help='Force potentially broken configurations',
               action='store_true')
p.add_argument('--kernel', help='Only measure kernel code', action='store_true')
p.add_argument('--user', help='Only measure user code', action='store_true')
p.add_argument('--print-group', '-g', help='Print event group assignments',
               action='store_true')
p.add_argument('--no-desc', help='Don\'t print event descriptions', action='store_true')
p.add_argument('--csv', '-x', help='Enable CSV mode with specified delimeter')
p.add_argument('--interval', '-I', help='Enable interval mode with ms interval',
               type=int)
p.add_argument('--output', '-o', help='Set output file', default=sys.stderr,
               type=argparse.FileType('w'))
p.add_argument('--graph', help='Automatically graph interval output with tl-barplot.py',
               action='store_true')
p.add_argument('--title', help='Set title of graph')
p.add_argument('--xkcd', help='Use xkcd plotting mode for graph', action='store_true')
p.add_argument('--level', '-l', help='Measure upto level N (max 5)',
               type=int, default=1)
p.add_argument('--detailed', '-d', help=argparse.SUPPRESS, action='store_true')
p.add_argument('--metrics', '-m', help="Print extra metrics", action='store_true')
p.add_argument('--raw', help="Print raw values", action='store_true')
p.add_argument('--sw', help="Measure perf Linux metrics", action='store_true')
p.add_argument('--cpu', '-C', help=argparse.SUPPRESS)
p.add_argument('--tsx', help="Measure TSX metrics", action='store_true')
p.add_argument('--all', help="Measure everything available", action='store_true')
p.add_argument('--frequency', help="Measure frequency", action='store_true')
p.add_argument('--no-group', help='Dont use groups', action='store_true')
p.add_argument('--no-multiplex',
               help='Do not multiplex, but run the workload multiple times as needed. Requires reproducible workloads.',
               action='store_true')
p.add_argument('--power', help='Display power metrics', action='store_true')
p.add_argument('--version', help=argparse.SUPPRESS, action='store_true')
args, rest = p.parse_known_args()

if args.version:
    print "toplev"
    sys.exit(0)

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
        extra += '--title "' + args.title + '" '
    if args.xkcd:
        extra += '--xkcd '
    if args.output != sys.stderr:
        extra += '--output "' + args.output.name + '" '
    args.csv = ','
    cmd = "PATH=$PATH:. ; tl-barplot.py " + extra + "/dev/stdin"
    args.output = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE).stdin

print_all = args.verbose # or args.csv
dont_hide = args.verbose
detailed_model = (args.level > 1) or args.detailed
csv_mode = args.csv
interval_mode = args.interval
force = args.force
ring_filter = ""
if args.kernel:
    ring_filter = 'k'
if args.user:
    ring_filter = 'u'
if args.user and args.kernel:
    ring_filter = None
print_group = args.print_group
if args.cpu:
    rest = ["--cpu", args.cpu] + rest

MAX_ERROR = 0.05

def check_ratio(l):
    if print_all:
        return True
    return 0 - MAX_ERROR < l < 1 + MAX_ERROR

class Output:
    """Generate human readable output."""
    def __init__(self, logfile):
        self.csv = False
        self.sep = " "
        self.logf = logfile
        self.printed_descs = set()
        self.hdrlen = 46

    # pass all possible hdrs in advance to compute suitable padding
    def set_hdr(self, hdr):
        self.hdrlen = max(len(hdr) + 1, self.hdrlen)

    def s(self, area, hdr, s, remark, desc, sample):
        if area:
            hdr = "%-7s %s" % (area, hdr)
        if remark == "above":
            remark = ""
        print >>self.logf, "%-*s %s %s" % (self.hdrlen, hdr + ":", s, remark)
        if desc and not args.no_desc:
            print >>self.logf, "\t" + desc
        if desc and sample:
            print >>self.logf, "\t" + "Sampling events: ", sample

    def item(self, area, name, l, timestamp, remark, desc, title, fmtnum, check, sample):
        if timestamp:
            self.logf.write("%6.9f%s" % (timestamp, self.sep))
        if title:
            if self.csv:
                self.logf.write(title + self.csv)
            else:
                self.logf.write("%-6s" % (title))
        if not check or check_ratio(l):
            if desc in self.printed_descs:
                desc = ""
            else:
                self.printed_descs.add(desc)
            self.s(area, name, fmtnum(l), remark, desc, sample)
        else:
            self.s(area, name, fmtnum(0), "mismeasured", "", sample)

    def p(self, area, name, l, timestamp, remark, desc, title, sample):
        self.item(area, name, l, timestamp, remark, desc, title,
                  lambda l: "%5s%%" % ("%2.2f" % (100.0 * l)), True, sample)

    def metric(self, area, name, l, timestamp, desc, title, unit):
        self.item(area, name, l, timestamp, unit, desc, title,
                  lambda l: "%5s" % ("%3.2f" % (l)), False, "")

class OutputCSV(Output):
    def __init__(self, logfile, csv):
        Output.__init__(self, logfile)
        self.csv = csv
        self.sep = self.csv

    def s(self, area, hdr, s, remark, desc, sample):
        remark = self.csv + remark
        if args.no_desc:
            desc = ""
        if desc and sample:
            desc += " Sampling events: " + sample
        desc = self.csv + '"' + desc + '"'
        desc = re.sub(r"\s+", " ", desc)
        print >>self.logf, '%s%s%s%s%s%s%s' % (hdr, self.csv, s.strip(), remark, desc, self.csv, sample)

class CPU:
    # overrides for easy regression tests
    def force_cpu(self):
        force = os.getenv("FORCECPU")
        if not force:
            return False
        self.cpu = None
        for i in known_cpus:
            if force == i[0]:
                self.cpu = i[0]
                break
        if self.cpu is None:
            print "Unknown FORCECPU ",force
        return True

    def force_counters(self):
        cnt = os.getenv("FORCECOUNTERS")
        if cnt:
            self.counters = int(cnt)

    def force_ht(self):
        ht = os.getenv("FORCEHT")
        if ht:
            self.ht = int(ht)
            return True
        return False

    def __init__(self):
        self.model = 0
        self.cpu = None
        self.ht = False
        self.counters = 0
        self.has_tsx = False
        self.freq = 0.0
        self.siblings = {}
        self.threads = 0
        forced_cpu = self.force_cpu()
        forced_ht = self.force_ht()
        self.force_counters()
        cores = Counter()
        sockets = Counter()
        self.coreids = defaultdict(list)
        self.cputocore = {}
        self.cputothread = {}
        with open("/proc/cpuinfo", "r") as f:
            ok = 0
            for l in f:
                n = l.split()
                if len(n) < 3:
                    continue
                if n[0] == 'processor':
                    ok += 1
                    cpunum = int(n[2])
                elif (n[0], n[2]) == ("vendor_id", "GenuineIntel") and ok == 0:
                    ok += 1
                elif (len(n) > 3 and
                        (n[0], n[1], n[3]) == ("cpu", "family", "6") and
                        ok == 1):
                    ok += 1
                elif (n[0], n[1]) == ("model", ":") and ok == 2:
                    ok += 1
                    self.model = int(n[2])
                elif (n[0], n[1]) == ("model", "name"):
                    ok += 1
                    m = re.search(r"@ (\d+\.\d+)Ghz", l)
                    if m:
                        self.freq = float(m.group(1))
                elif (n[0], n[1]) == ("physical", "id"):
                    physid = int(n[3])
                    sockets[physid] += 1
                elif (n[0], n[1]) == ("core", "id"):
                    coreid = int(n[3])
                    key = (physid, coreid,)
                    cores[key] += 1
                    self.threads = max(self.threads, cores[key])
                    if self.threads > 1 and not forced_ht:
                        self.ht = True
                    self.coreids[key].append(cpunum)
                    self.cputocore[cpunum] = key
                    self.cputothread[cpunum] = self.coreids[key].index(cpunum)
                elif n[0] == "flags":
                    ok += 1
                    self.has_tsx = "rtm" in n
        if ok >= 6 and not forced_cpu:
            for i in known_cpus:
                if self.model in i[1]:
                    self.cpu = i[0]
                    break
        if self.counters == 0:
            if self.cpu == "slm":
                self.counters = 2
            elif self.ht:
                self.counters = 4
            else:
                self.counters = 8
        self.sockets = len(sockets.keys())

cpu = CPU()

class PerfRun:
    def execute(self, r):
        outp, inp = pty.openpty()
        n = r.index("--log-fd")
        r[n + 1] = "%d" % (inp)
        l = ["'" + x + "'" if x.find("{") >= 0 else x for x in r]
        i = l.index('--log-fd')
        del l[i:i+2]
        print " ".join(l)
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
}

fixed_set = frozenset(fixed_counters.keys())

def separator(x):
    if x.startswith("cpu"):
        return ""
    return ":"

def add_filter(s):
    if ring_filter:
        s = [x + separator(x) + ring_filter for x in s]
    return s

def raw_event(i):
    if i.count(".") > 0:
        if i in fixed_counters:
            return fixed_counters[i]
        e = emap.getevent(i)
        if e is None:
            if i in event_fixes:
                e = emap.getevent(event_fixes[i])
        if e is None:
            print >>sys.stderr, "%s not found" % (i,)
            if not force:
                sys.exit(1)
            return "cycles" # XXX
        i = e.output(noname=True)
        emap.update_event(e.output(noname=True), e)
    return i

# generate list of converted raw events from events string
def raw_events(evlist):
    return map(raw_event, evlist)

def mark_fixed(s):
    r = raw_event(s)
    if r in ingroup_events:
        return "%s[F]" % s
    return s

def pwrap(s, linelen=60, indent=""):
    print indent + ("\n" + indent).join(textwrap.wrap(s, linelen))

def has(obj, name):
    return name in obj.__class__.__dict__

def print_header(work, evlist):
    evnames0 = [obj.evlist for obj in work]
    evnames = set(itertools.chain(*evnames0))
    names = ["%s[%d]" % (obj.__class__.__name__, obj.__class__.level if has(obj, 'level') else 0) for obj in work]
    pwrap(" ".join(names) + ":", 78)
    pwrap(" ".join(map(mark_fixed, evnames)).lower() +
          " [%d_counters]" % (len(evnames - fixed_set)), 75, "  ")

def setup_perf(evstr, rest):
    prun = PerfRun()
    add = []
    if interval_mode:
        add += ['-I', str(interval_mode)]
    inf = prun.execute([perf, "stat", "-x,", "--log-fd", "X", "-e", evstr]  + add + rest)
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
            print_not(a, a.errors[e], e, j)
            total[e] += 1
    if sum(total.values()) > 0:
        print >>sys.stderr, ", ".join(["%d %s" % (num, e) for e, num in total.iteritems()])

def event_regexp():
    return "|".join(valid_events)

def is_event(l, n):
    if len(l) <= n:
        return False
    return re.match(event_regexp(), l[n])

def set_interval(env, d):
    env['interval-ns'] = d * 1E+3
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

def print_keys(runner, res, rev, out, interval, env):
    referenced = set()
    if smt_mode:
        # collect counts from all threads of cores as lists
        # this way the model can access all threads individually
        # print the SMT aware nodes
        core_keys = sorted(res.keys(), key = key_to_coreid)
        for core, citer in itertools.groupby(core_keys, key_to_coreid):
            cpus = list(citer)
            r = list(itertools.izip(*[res[j] for j in cpus]))
            runner.print_res(r, rev[cpus[0]], out, interval, core_fmt(core), env, Runner.SMT_yes,
                             referenced)

        # print the non SMT nodes
        for j in sorted(res.keys()):
            runner.print_res(res[j], rev[j], out, interval, thread_fmt(j), env, Runner.SMT_no,
                             referenced)
    else:
        for j in sorted(res.keys()):
            runner.print_res(res[j], rev[j], out, interval, j, env, Runner.SMT_dontcare,
                             referenced)

    # sanity check: did we reference all results?
    r = res[res.keys()[0]]
    if len(referenced) != len(r):
        print "warning: %d results not referenced:" % (len(r) - len(referenced)),
        print " ".join(sorted(["%d" % x for x in set(range(len(r))) - referenced]))

def execute_no_multiplex(runner, out, rest):
    if args.interval: # XXX
        sys.exit('--no-multiplex is not supported with interval mode')
    groups = runner.evgroups
    n = 1
    res = defaultdict(list)
    rev = defaultdict(list)
    env = dict()
    for g in groups:
        if len(g) == 0:
            continue
        print "RUN #%d of %d" % (n, len(groups))
        ret, res, rev, interval = do_execute(runner, g, out, rest, res, rev, env)
        n += 1
    print_keys(runner, res, rev, out, interval, env)
    return ret

def execute(runner, out, rest):
    env = dict()
    ret, res, rev, interval = do_execute(runner, ",".join(filter(lambda x: len(x) > 0, runner.evgroups)),
                                         out, rest,
                                         defaultdict(list),
                                         defaultdict(list),
                                         env)
    print_keys(runner, res, rev, out, interval, env)
    return ret

perf_fields = [
    r"[0-9.]+",
    r"<.*?>",
    r"S\d+-C\d+?",
    r"S\d+",
    r"raw 0x[0-9a-f]+",
    r"Joules",
    ""]

def do_execute(runner, evstr, out, rest, res, rev, env):
    account = defaultdict(Stat)
    inf, prun = setup_perf(evstr, rest)
    prev_interval = 0.0
    interval = None
    start = time.time()
    while True:
        try:
            l = inf.readline()
            if not l:
                break
        except exceptions.IOError:
             # handle pty EIO
             break
        except KeyboardInterrupt:
            continue
        if interval_mode:
            m = re.match(r"\s*([0-9.]+),(.*)", l)
            if m:
                interval = float(m.group(1))
                l = m.group(2)
                if interval != prev_interval:
                    if res:
                        set_interval(env, interval - prev_interval)
                        print_keys(runner, res, rev, out, prev_interval, env)
                        res = defaultdict(list)
                        rev = defaultdict(list)
                    prev_interval = interval
        # cannot just split on commas, as they are inside cpu/..../
        # code later relies on the regex stripping ku flags
        fields = "(" + "|".join(valid_events + perf_fields) + "),?"
        n = re.findall(fields, l)
        # filter out the empty unit field added by 3.14
        n = filter(lambda x: x != "" and x != "Joules", n)

        # timestamp is already removed
        # -a --per-socket socket,numcpus,count,event,...
        # -a --per-core core,numcpus,count,event,...
        # -a -A cpu,count,event,...
        # count,event,...
        if is_event(n, 1):
            title, count, event = "", n[0], n[1]
        elif is_event(n, 3):
            title, count, event = n[0], n[2], n[3]
        elif is_event(n, 2):
            title, count, event = n[0], n[1], n[2]
        else:
            print "unparseable perf output"
            sys.stdout.write(l)
            continue
        event = event.rstrip()
        if re.match(r"[0-9]+", count):
            val = float(count)
        elif count.startswith("<"):
            account[event].errors[count.replace("<","").replace(">","")] += 1
            val = 0
        else:
            print "unparseable perf count"
            sys.stdout.write(l)
            continue
        account[event].total += 1
        res[title].append(val)
        rev[title].append(event)
        if args.raw:
            print "raw",title,"event",event,"val",val
    inf.close()
    if 'interval-ns' not in env:
            set_interval(env, (time.time() - start) * 1E+9)
    ret = prun.wait()
    print_account(account)
    return ret, res, rev, interval

def ev_append(ev, level, obj):
    if isinstance(ev, types.LambdaType):
        return ev(lambda ev, level: ev_append(ev, level, obj), level)
    if ev in nonperf_events:
        return 99
    if not (ev, level) in obj.evlevels:
        obj.evlevels.append((ev, level, obj.name))
    if 'nogroup' in obj.__class__.__dict__ and obj.nogroup:
        outgroup_events.add(ev)
    if re.match(r'^[a-z]', ev):
        valid_events.append(ev)
    return 99

def canon_event(e):
    m = re.match(r"(.*?):(.*)", e)
    if m and m.group(2) != "amt1":
        e = m.group(1)
    if e in fixed_counters:
        return fixed_counters[e]
    if m:
        e = m.group(1)
    if e.endswith("_0"):
        e = e[:-2]
    return e.lower()

fixes = dict(zip(event_fixes.values(), event_fixes.keys()))

def event_rmap(e):
    n = canon_event(emap.getperf(e))
    if emap.getevent(n):
        return n
    if n.upper() in fixes:
        n = fixes[n.upper()].lower()
    return n

def lookup_res(res, rev, ev, obj, env, level, referenced, cpuoff = -1):
    if ev in env:
        return env[ev]
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
                       lookup_res(res, rev, ev, obj, env, level, referenced, off), level)
                       for off in range(cpu.threads)])

    index = obj.res_map[(ev, level, obj.name)]
    referenced.add(index)
    #print (ev, level, obj.name), "->", index
    rev = event_rmap(rev[index])
    assert (rev == canon_event(ev) or
                (ev in event_fixes and canon_event(event_fixes[ev]) == rev))

    if isinstance(res[index], types.TupleType):
        if cpuoff == -1:
            return sum(res[index])
        else:
            return res[index][cpuoff]
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

def sample_event(e):
    ev = emap.getevent(e.replace("_PS", ""))
    if not ev:
        raise BadEvent(e)
    return ev.name + ":pp"

def sample_desc(s):
    try:
        return ",".join([sample_event(x) for x in s])
    except BadEvent as e:
        #return "Unknown sample event %s" % (e.event)
        return ""

def get_levels(evlev):
    return [x[1] for x in evlev]

def get_names(evlev):
    return [x[0] for x in evlev]

def num_non_fixed(l):
    n = cpu.counters
    while len(set(l[:n]) - fixed_set) < cpu.counters and n < len(l):
        n += 1
    return n

def full_name(obj):
    name = obj.name
    while 'parent' in obj.__dict__ and obj.parent:
        obj = obj.parent
        name = obj.name + "." + name
    return name

def smt_node(obj):
    return 'domain' in obj.__class__.__dict__ and obj.domain in smt_domains

def count(f, l):
    return len(filter(f, l))

class Runner:
    """Schedule measurements of event groups. Try to run multiple in parallel."""

    SMT_yes, SMT_no, SMT_dontcare = range(3)

    def __init__(self, max_level):
        self.evnum = [] # flat global list
        self.evgroups = list()
        self.olist = []
        self.max_level = max_level

    def do_run(self, obj):
        obj.res = None
        obj.res_map = dict()
        self.olist.append(obj)

    def run(self, obj):
        obj.thresh = False
        obj.metric = False
        if obj.level > self.max_level:
            return
        self.do_run(obj)

    def metric(self, obj):
        obj.thresh = True
        obj.metric = True
        obj.level = 0
        obj.sibling = None
        if not args.metrics:
            return
        self.do_run(obj)

    def split_groups(self, objl, evlev):
        if len(set(get_levels(evlev))) == 1:
            # when there is only a single left just fill groups
            while evlev:
                n = num_non_fixed(get_names(evlev))
                l = evlev[:n]
                self.add(objl, raw_events(get_names(l)), l)
                evlev = evlev[n:]
        else:
            # resubmit groups for each level
            max_level = max(get_levels(evlev))
            for l in range(1, max_level + 1):
                evl = filter(lambda x: x[1] == l, evlev)
                if evl:
                    self.add(objl, raw_events(get_names(evl)), evl)

    def add(self, objl, evnum, evlev):
        # does not fit into a group.
        if needed_counters(evnum) > cpu.counters:
            self.split_groups(objl, evlev)
            return
        base = len(self.evnum)
        evnum, evlev = dedup2(evnum, evlev)
        update_res_map(evnum, objl, base)
        self.evnum += evnum
        self.evgroups.append(event_group(evnum))
        if print_group:
            print_header(objl, get_names(evlev))

    # collect the events by pre-computing the equation
    def collect(self):
        self.objects = {}
        for obj in self.olist:
            self.objects[obj.name] = obj
        for obj in self.olist:
            obj.evlevels = []
            obj.compute(lambda ev, level: ev_append(ev, level, obj))
            obj.evlist = [x[0] for x in obj.evlevels]
            obj.evnum = raw_events(obj.evlist)
            obj.nc = needed_counters(obj.evnum)

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
            print "%d groups, %d non-groups with %d events total (%d unique) for %d objects" % (
                count(lambda x: x.startswith("{"), self.evgroups),
                count(lambda x: not x.startswith("{"), self.evgroups),
                len(self.evnum),
                len(set(self.evnum)),
                len(self.olist))

    def print_res(self, res, rev, out, timestamp, title, env, smt, referenced):
        if len(res) == 0:
            print "Nothing measured?"
            return

        # step 1: compute
        for obj in self.olist:
            out.set_hdr(full_name(obj))
            if obj.res_map:
                obj.compute(lambda e, level:
                            lookup_res(res, rev, e, obj, env, level, referenced))
            else:
                print >>sys.stderr, "%s not measured" % (obj.__class__.__name__,)
        out.logf.flush()

        # step 2: propagate siblings
        for obj in self.olist:
            if obj.thresh and obj.sibling:
                obj.sibling.thresh = True

        # step 3: print
        for obj in self.olist:
            if obj.thresh or print_all:
                val = obj.val
                if not obj.thresh and not dont_hide:
                    val = 0.0
                if obj.name == "Time": # XXX hack
                    continue
                if (smt != Runner.SMT_dontcare and
                        (Runner.SMT_yes if smt_node(obj) else Runner.SMT_no) != smt):
                    continue
                disclaimer = ""
                if 'htoff' in obj.__dict__ and obj.htoff and obj.thresh and cpu.ht:
                    disclaimer = """
Warning: Hyper Threading may lead to incorrect measurements for this node.
Suggest to re-measure with HT off (run cputop.py "thread == 1" offline | sh)."""
                desc = obj.desc[1:].replace("\n", "\n\t")
                if obj.metric:
                    out.metric(obj.area if 'area' in obj.__class__.__dict__ else None,
                            obj.name, val, timestamp,
                            desc + disclaimer,
                            title,
                            obj.unit if 'unit' in obj.__class__.__dict__ else "metric")
                else:
                    out.p(obj.area if 'area' in obj.__class__.__dict__ else None,
                        full_name(obj), val, timestamp,
                        "below" if not obj.thresh else "above",
                        desc + disclaimer,
                        title,
                        sample_desc(obj.sample) if obj.sample else "")

def sysctl(name):
    try:
        with open("/proc/sys/" + name.replace(".","/"), "r") as f:
            val = int(f.readline())
    except IOError:
        return 0
    return val

# check nmi watchdog
if sysctl("kernel.nmi_watchdog") != 0:
    sys.exit("Please disable nmi watchdog (echo 0 > /proc/sys/kernel/nmi_watchdog)")

if cpu.cpu is None:
    sys.exit("Unsupported CPU model %d" % (cpu.model,))

kernel_version = map(int, platform.release().split(".")[:2])
if detailed_model:
    if kernel_version[0] < 3 or (kernel_version[0] == 3 and kernel_version[1] < 10):
        print >>sys.stderr, "Older kernel than 3.10. Events may not be correctly scheduled."

def ht_warning():
    if cpu.ht:
        print >>sys.stderr, "WARNING: HT enabled"
        print >>sys.stderr, "Measuring multiple processes/threads on the same core may is not reliable."

runner = Runner(args.level)

if cpu.cpu == "ivb":
    import ivb_client_ratios
    ivb_client_ratios.smt_enabled = cpu.ht
    smt_mode = cpu.ht
    ivb_client_ratios.Setup(runner)
elif cpu.cpu == "ivt":
    import ivb_server_ratios
    ivb_server_ratios.smt_enabled = cpu.ht
    smt_mode = cpu.ht
    ivb_server_ratios.Setup(runner)
elif cpu.cpu == "snb":
    import snb_client_ratios
    snb_client_ratios.Setup(runner)
elif cpu.cpu == "jkt":
    import jkt_server_ratios
    jkt_server_ratios.Setup(runner)
elif cpu.cpu == "hsw":
    import hsw_client_ratios
    hsw_client_ratios.smt_enabled = cpu.ht
    smt_mode = cpu.ht
    hsw_client_ratios.Setup(runner)
elif cpu.cpu == "hsx":
    import hsx_server_ratios
    hsx_server_ratios.smt_enabled = cpu.ht
    smt_mode = cpu.ht
    hsx_server_ratios.Setup(runner)
elif cpu.cpu == "bdw":
    import bdw_client_ratios
    bdw_client_ratios.smt_enabled = cpu.ht
    smt_mode = cpu.ht
    bdw_client_ratios.Setup(runner)
elif cpu.cpu == "slm":
    import slm_ratios
    slm_ratios.Setup(runner)
else:
    ht_warning()
    if detailed_model:
        print >>sys.stderr, "Sorry, no detailed model for your CPU. Only Level 1 supported."
    import simple_ratios
    simple_ratios.Setup(runner)

def setup_with_metrics(p, runner):
    old_metrics = args.metrics
    args.metrics = True
    p.Setup(runner)
    args.metrics = old_metrics

if args.power and feat.supports_power:
    import power_metrics
    setup_with_metrics(power_metrics, runner)
    print >>sys.stderr, "Running with --power. Will measure complete system."
    if "-a" not in rest:
        rest = ["-a"] + rest

if args.sw:
    import linux_metrics
    setup_with_metrics(linux_metrics, runner)

if args.tsx and cpu.has_tsx and cpu.cpu in tsx_cpus:
    import tsx_metrics
    setup_with_metrics(tsx_metrics, runner)

if (args.level > 2 or not smt_mode) or args.frequency:
    import frequency
    old_metrics = args.metrics
    args.metrics = True
    frequency.SetupCPU(runner, cpu)
    args.metrics = old_metrics

if smt_mode:
    print "Running in HyperThreading mode. Will measure complete system."
    if "--per-socket" in rest:
        sys.exit("Hyper Threading more not compatible with --per-socket")
    if "--per-core" in rest:
        sys.exit("Hyper Threading more not compatible with --per-core")
    if args.cpu:
        print >>sys.stderr, "Warning: --cpu/-C mode with HyperThread must specify all core thread pairs!"
    if not (os.geteuid() == 0 or sysctl("kernel.perf_event_paranoid") == -1):
        print >>sys.stderr, "Warning: Needs root or echo -1 > /proc/sys/kernel/perf_event_paranoid"
    if kernel_version[0] == 3 and kernel_version[1] >= 10 and args.level >= 3:
        print >>sys.stderr, "Warning: kernel may need to be patched to schedule all events with level %d in HT mode" % (args.level)
    if "-a" not in rest:
        rest = ["-a"] + rest
    if "-A" not in rest:
        rest = ["-A"] + rest

print "Using level %d." % (args.level),
if not args.level and cpu.cpu != "slm":
    print "Change level with -lX"
print

runner.collect()
if csv_mode:
    out = OutputCSV(args.output, csv_mode)
else:
    out = Output(args.output)
runner.schedule()
if args.no_multiplex:
    ret = execute_no_multiplex(runner, out, rest)
else:
    ret = execute(runner, out, rest)
sys.exit(ret)
