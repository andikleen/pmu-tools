#!/usr/bin/python
# Copyright (c) 2012-2013, Intel Corporation
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
# Do cycle decomposition on a workload: estimate on which part of the
# CPU pipeline it bottlenecks.
#
# must find ocperf in python module path. add to paths below if needed.
#
# Handles a variety of perf versions, but older ones have various limitations.
#
# - cannot handle programs that exit with an error code (wrap in shell)

import sys, os, re, itertools, textwrap, types, platform
#sys.path.append("../pmu-tools")
import ocperf

extra_events = "cycles|instructions|faults|cs|migrations|cpu-clock|task-clock|" + \
               "page-faults|context-switches|CPU-migrations"
extra_events_l = set(extra_events.split("|"))
ingroup_events = set(["cycles", "instructions", "ref-cycles"])

def usage():
    print >>sys.stderr, """
Do cycle decomposition on a workload: estimate on which part of the
CPU pipeline it bottlenecks. The bottlenecks are expressed as a tree
with different levels (max 4).

Requires an Intel Sandy, Ivy Bridge, Haswell CPU.
It works best on Ivy Bridge currently, the others only support
a basic (but reliable) model.

Usage:
./toplev.py [-lX] [-v] [-d] [-o logfile] program
measure program
./toplev.py [-lX] [-v] [-d] [-o logfile] -a sleep X
measure whole system for X seconds
./toplev.py [-lX] [-v] [-d] [-o logfile] -p PID
measure pid PID

-o set output file
-v print everything
-d use detailed model if available (only Ivy Bridge currently)
-lLEVEL only use events upto max level (max 4)
-x, CSV mode with separator ,

Other perf arguments allowed (see the perf documentation)
After -- perf arguments conflicting with toplevel can be used.

Some caveats:
The lower levels of the measurement tree are much less reliable
than the higher levels.  They also rely on counter multi-plexing
and cannot use groups, which can cause larger measurement errors
with non steady state workloads.
(If you don't understand this terminology; it means measurements
are much less accurate and it works best with programs that primarily
do the same thing over and over)

In this case it's recommended to measure the program only after
the startup phase by profiling globally or attaching later.
level 1 or running without -d is generally the most reliable.

One of the events (even used by level 1) requires a recent enough
kernel that understands its counter constraints.  3.10+ is safe.

The tool cannot distinguish perf failing from the program failing.
If the program returns an error code, and you still want to measure
it wrap it with a sh -c.
"""
    sys.exit(1)

def works(x):
    return os.system(x + " >/dev/null 2>/dev/null") == 0

class PerfFeatures:
    group_support = False
    def __init__(self):
        self.output_supported = works("perf stat --output /dev/null true")
        if not self.output_supported:
            self.logfd_supported = works("perf stat --log-fd 3 --output /dev/null true")
        # some broken perf versions log on stdin
        if not self.output_supported and not self.logfd_supported:
            self.output_on_stdin = works("perf stat true 0>&1 | grep -q Performance")
        if self.output_supported:
            self.group_support = works("perf stat --output /dev/null -e '{cycles,branches}' true")

    def perf_output(self, plog):
        if self.output_supported:
            return "--output %s " % (plog,)
        elif self.logfd_supported:
            return "--log-fd 3 3>%s " % (plog,)
        elif self.output_on_stdin:
            return ">%s 0>&1 " % (plog,)
        else:
            # gets confused by other errors
            return "2>%s " % (plog,)

    def event_group(self, evlist, max_counters):
        el = filter(lambda e: e not in extra_events_l or e in ingroup_events, evlist)
	e = ",".join(el)
        # when the group has to be multiplexed anyways don't use a group
        # perf doesn't support groups that need to be multiplexed internally too
        if len(el) <= max_counters and self.group_support:
            e = "{%s}" % (e,)
        extra = filter(lambda e: e in extra_events_l and e not in ingroup_events, evlist)
        if extra:
            if e:
                e += ","
            e += ",".join(extra)
        return e
 
feat = PerfFeatures()

logfile = None
multiplex = False
print_all = False
detailed_model = False
max_level = 2
csv_mode = None

first = 1
while first < len(sys.argv):
    if sys.argv[first] == '-o':
        first += 1
        if first >= len(sys.argv):
            usage()
        logfile = sys.argv[first]
    elif sys.argv[first] == '-v':
        print_all = True
    elif sys.argv[first] == '-d':
        detailed_model = True
    elif sys.argv[first].startswith("-l"):
        max_level = int(sys.argv[first][2:])
    elif sys.argv[first].startswith("-x"):
        csv_mode = sys.argv[first][2:]
    elif sys.argv[first] == '--':
        first += 1
        break
    else:
        break
    first += 1

if len(sys.argv) - first <= 0:
    usage()

class Output:
    def __init__(self, logfile, csv):
        self.csv = csv
        if logfile:
            self.logf = open(logfile, "w")
            self.terminal = False
        else:
            self.logf = sys.stderr
            self.terminal = self.logf.isatty()

    def s(self, hdr, s):
        if self.csv:
            print >>self.logf,"%s%s%s" % (hdr, self.csv, s)
        else:
            print >>self.logf, "%-35s\t%s" % (hdr + ":", s)

    def p(self, name, l):
	if l:
	    if l >= -0.05 and l < 1.05:
	        self.s(name, "%5s%%"  % ("%2.2f" % (100.0 * l)))
	    else:
		self.s(name, "mismeasured")
        else:
            self.s(name, "not available")

    def nopercent(self, name, num):
        if num:
            self.s(name, "%5s"  % ("%2.2f" % (num)))
        else:
            self.s(name, "not available")

    def int(self, name, num):
        self.s(name, "%5s"  % ("%d" % (num)))

    def bold(self, s):
        if (not self.terminal) or self.csv:
            return s
        return '\033[1m' + s + '\033[0m'

    def desc(self, d):
        if not self.csv:
            print >>self.logf, "\t%s" % (d)

    def warning(self, s):
        if not self.csv:
            print >>sys.stderr, self.bold("warning:") + " " + s


known_cpus = (
    ("snb", (42, 45)),
    ("ivb", (58, )),
    ("ivt", (62, )),
    ("hsw", (60, 63, 70, 71))
)

class CPU:
    counters = 0

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
        if self.cpu == None:
            print "Unknown FORCECPU ",force
        return True
       
    def force_counters(self):
        cnt = os.getenv("FORCECOUNTERS")
        if cnt:
            self.counters = int(cnt)

    def __init__(self):
        self.model = 0
        self.threads = 0 
        self.cpu = None
        self.ht = False
        forced_cpu = self.force_cpu()
        self.force_counters()
        cores = {}
        with open("/proc/cpuinfo", "r") as f:
            ok = 0
            for l in f:
                n = l.split()
                if len(n) < 3:
                    continue
                if (n[0], n[2]) == ("vendor_id", "GenuineIntel") and ok == 0:
                    ok += 1
                elif (len(n) > 3 and 
                        (n[0], n[1], n[3]) == ("cpu", "family", "6") and 
                        ok == 1):
                    ok += 1
                elif (n[0], n[1]) == ("model", ":") and ok == 2:
                    ok += 1
                    self.model = int(n[2])
                elif n[0] == "processor":
                    self.threads += 1
                elif (n[0], n[1]) == ("physical", "id"):
                    physid = int(n[3])
                elif (n[0], n[1]) == ("core", "id"):
                    key = (physid, int(n[3]),)
                    if key in cores:
                        cores[key] += 1
                    else:
                        cores[key] = 1
                    if cores[key] > 1:
                        self.ht = True
        if ok >= 3 and not forced_cpu:
            for i in known_cpus:
                if self.model in i[1]:
                    self.cpu = i[0]
                    break
        if self.counters == 0:
            if self.ht:
                self.counters = 4
            else:
                self.counters = 8

cpu = CPU()

def execute(r):
    print r
    if os.system(r) != 0:
        print >>sys.stderr, "perf failed"
        return False
    return True

def num_counters(ev):
    counter = 0
    for i in ev:
        if re.match(r'r[0-9a-f](:p)?', i):
            counter += 1
    return counter

fixed_counters = {
	"CPU_CLK_UNHALTED.THREAD": "cycles",
	"INST_RETIRED.ANY": "instructions",
	"CPU_CLK_UNHALTED.REF_TSC": "ref-cycles"
}

def raw_event(i, emap):
    if i.count(".") > 0:
	if i in fixed_counters:
	    return fixed_counters[i]
        e = emap.getevent(i)
        if e == None:
            print "%s not found" % (i,)
            return "cycles" # XXX 
        i = emap.getevent(i).output(True)
    return i

# generate list of converted raw events from events string
def raw_events(evlist):
    emap = ocperf.find_emap()
    return map(lambda x: raw_event(x, emap), evlist)

def pwrap(s):
    print "\n".join(textwrap.wrap(s, 80))

def print_header(work, evlist):
    evnames0 = map(lambda obj: obj.evlist, work)
    evnames = set(itertools.chain(*evnames0))
    names = map(lambda obj: obj.__class__.__name__, work)
    pwrap(" ".join(names) + ": " + " ".join(evnames).lower())

# map the flat results back to the original groups
# this assumes perf always outputs them in the original order
# also check if we got the right events
def flat_to_group(res, events, rev):
    resg = []
    i = 0
    for egroup in events:
        g = []
        for j in egroup:
            if rev[i] != j:
                print "--- got event %s expected %s" % (rev[i], j, )
            g.append(res[i])
            i += 1
        resg.append(g)
    return resg

def shell_arg(a):
    if re.search(r"[\t \[\]()|$&{};<>?*\"']", a):
        return "'%s'" % (a,)
    return a

# execute perf: list of event-groups -> list of results-for-group
def measure(events):
    plog = "plog.%d" % (os.getpid(),)
    rest = " -x, -e '" + ",".join(map(lambda e: feat.event_group(e, cpu.counters), events)) + "' "
    rest += " ".join(map(shell_arg, sys.argv[first:]))
    if not execute("perf stat " + feat.perf_output(plog) + rest):
        print >>sys.stderr, "not measured because perf failed"
        return
    inf = open(plog, "r")
    res = []
    rev = []
    for l in inf:
        reg = r"[0-9.]+,(" + extra_events + "|(r|raw )[0-9a-fx]+|cpu/[^/]+/)"
        if re.match(reg, l):
            count, event = l.split(",", 1) 
            res.append(float(count))
            rev.append(event.rstrip())
        elif l.startswith("<not counted>"):
            res.append(0)
            rev.append(l.split(",")[1].rstrip())
        elif l.startswith("<not supported>"):
            print "warning: event %s not supported" % (l.split(",")[1].rstrip())
            res.append(0)
            rev.append(l.split(",")[1].rstrip())
        else:
            print l,
    inf.close()
    r = flat_to_group(res, events, rev)
    os.remove(plog)
    return r

# map events to their values
def finish(work, res, evlist):
    values = {}
    for r, ev in zip(res, evlist):
        values[ev] = r
    for obj in work:
        obj.res = map(lambda x: values[x], obj.evnum)

def ev_append(ev, obj):
    #print "got", ev
    if not ev in obj.evlist:
        obj.evlist.append(ev)
    return 1

class Runner:
    "Schedule measurements of event groups. Try to run multiple in parallel."
    workll = []
    evll = []
    olist = []

    def run(self, obj):
	obj.thresh = 0.0
        if obj.level > self.max_level:
            return
        obj.res = None
        obj.evlist = []
        self.olist.append(obj)

    # xxx fix the input files
    def fix_parents(self):
	for obj in self.olist:
	    if not obj.parent:
	        continue
	    if obj.level == 1:
                obj.parent = None
	    elif obj.parent.level >= obj.level:
                my_list = self.olist[:self.olist.index(obj)]
		all_parents = filter(lambda x: x.level < obj.level, my_list)
		obj.parent = all_parents[-1]
	        assert obj.parent.level < obj.level

    def add(self, work, evlist):
        self.workll.append(work)
        self.evll.append(evlist)

    def execute(self):
        for work, evlist in zip(self.workll, self.evll):
            print_header(work, evlist)
            res = measure([evlist])
            if res:
                finish(work, res[0], evlist)

    # collect the events by pre-computing the equation
    # we disable the output, so it happens silently
    def collect(self):
        self.objects = {}
        for obj in self.olist:
            self.objects[obj.name] = obj
        for obj in self.olist:
            obj.evlist = []
            obj.compute(lambda ev: ev_append(ev, obj))
            # for now until we sample
            obj.evlist = map(lambda x: x.replace("_PS",""), obj.evlist)
            obj.evnum = raw_events(obj.evlist)
            obj.nc = num_counters(obj.evnum)

    # fit events into available counters
    # simple first fit algorithm
    def schedule(self, out):
        work = []
        evlist = set()
        # XXX sort by evnums too
        solist = sorted(self.olist, key=lambda k: k.nc)
        for obj in solist:
            objev = obj.evnum
            newev = set(list(evlist) + objev)
            needed = len(filter(lambda x: x not in extra_events_l, newev))
            if cpu.counters < needed and work:
                self.add(work, evlist)
                work = []
                evlist = []
                newev = set(objev)
            work.append(obj)
            evlist = newev
        if work:
            self.add(work, evlist)
        self.execute()
        for obj in self.olist:
            if obj.res:
                obj.compute(lambda e: obj.res[obj.evlist.index(e.replace("_PS",""))])
                if obj.thresh or print_all:
                    out.p(obj.name, obj.val)
                if obj.thresh:
                    out.desc(obj.desc[1:].replace("\n","\n\t"))
            else:
                out.warning("%s not measured" % (obj.__class__.__name__,))

class RunnerMultiplex(Runner):
    "Version of Runner that multiplexes all event groups for only a single run."
    def execute(self):
        for work, evlist in zip(self.workll, self.evll):
            print_header(work, evlist)
        glist = []
        for e in self.evll:
            glist.append(e)
        res = measure(glist)
        if res:
            for work, evll, r in zip(self.workll, self.evll, res):
                finish(work, r, evll)

def sysctl(name):
    try:
        f = open("/proc/sys/" + name.replace(".","/"), "r")
        val = int(f.readline())
        f.close()
    except IOError:
        return 0
    return val

# check nmi watchdog
if sysctl("kernel.nmi_watchdog") != 0:
    print >>sys.stderr,"Please disable nmi watchdog (echo 0 > /proc/sys/kernel/nmi_watchdog)"
    sys.exit(1)

version = platform.release().split(".")
if int(version[0]) < 3 or (int(version[0]) == 3 and int(version[1]) < 10):
    print >>sys.stderr, "Older kernel than 3.10. Events may not be correctly scheduled."

if cpu.cpu == None:
    print >>sys.stderr, "Unsupported CPU model %d" % (cpu.model,)
    sys.exit(1)
    
if cpu.cpu == "ivb" and detailed_model and max_level > 1:
    multiplex = True 

if multiplex:
    runner = RunnerMultiplex()
else:
    runner = Runner()

runner.max_level = max_level
if cpu.cpu == "ivb" and detailed_model:
    import ivb_client_ratios
    ev = ivb_client_ratios.Setup(runner)
else:
    import simple_ratios
    ev = simple_ratios.Setup(runner)

runner.fix_parents()
runner.collect()
out = Output(logfile, csv_mode)
runner.schedule(out)
