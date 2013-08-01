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
# Handles a variety of perf versions, but older ones have various limitations.

import sys, os, re, itertools, textwrap, types, platform, pty, subprocess
import exceptions, pprint
#sys.path.append("../pmu-tools")
import ocperf

ingroup_events = frozenset(["cycles", "instructions", "ref-cycles"])

def usage():
    print >>sys.stderr, """
Do cycle decomposition on a workload: estimate on which part of the
CPU pipeline it bottlenecks. The bottlenecks are expressed as a tree
with different levels (max 4).

Requires an Intel Sandy, Ivy Bridge, Haswell CPU.
It works best on Ivy Bridge currently.

Usage:
./toplev.py [-lX] [-v] [-d] [-o logfile] program
measure program
./toplev.py [-lX] [-v] [-d] [-o logfile] -a sleep X
measure whole system for X seconds
./toplev.py [-lX] [-v] [-d] [-o logfile] -p PID
measure pid PID

-o set output file
-v print everything
-d use detailed model if available
-lLEVEL only use events upto max level (max 4)
-x, CSV mode with separator ,
-Inum  Enable interval mode, printing output every num ms
--kernel Measure kernel code only
--user   Measure user code only

Other perf arguments allowed (see the perf documentation)
After -- perf arguments conflicting with toplevel can be used.

Some caveats:
The lower levels of the measurement tree are less reliable
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
"""
    sys.exit(1)

def works(x):
    return os.system(x + " >/dev/null 2>/dev/null") == 0

class PerfFeatures:
    "Adapt to the quirks of various perf versions."
    group_support = False
    def __init__(self):
        self.output_supported = works("perf stat --output /dev/null true")
        self.logfd_supported = works("perf stat --log-fd 3 3>/dev/null true")
        # some broken perf versions log on stdin
        if not self.output_supported and not self.logfd_supported:
	    print "perf binary is too old. please upgrade"
	    sys.exit(1)
        if self.output_supported:
            self.group_support = works("perf stat --output /dev/null -e '{cycles,branches}' true")

    def perf_output(self, plog):
        if self.logfd_supported:
            return "--log-fd X"
        elif self.output_supported:
            return "--output %s " % (plog,)

    def event_group(self, evlist):
        need_counters = set(evlist) - ingroup_events
	e = ",".join(evlist)
        # when the group has to be multiplexed anyways don't use a group
        # perf doesn't support groups that need to be multiplexed internally too
        if (len(need_counters) <= cpu.counters and self.group_support
                and len(need_counters) > 1):
            e = "{%s}" % (e,)
        return e
 
feat = PerfFeatures()
emap = ocperf.find_emap()

logfile = None
print_all = False
detailed_model = False
max_level = 2
csv_mode = None
interval_mode = None
force = False
ring_filter = None

first = 1
while first < len(sys.argv):
    if sys.argv[first] == '-o':
        first += 1
        if first >= len(sys.argv):
            usage()
        logfile = sys.argv[first]
    elif sys.argv[first] == '-v':
        print_all = True
    elif sys.argv[first] == '--force':
        force = True
    elif sys.argv[first] in ('--kernel', '--user'):
        ring_filter = sys.argv[first][2:]
    elif sys.argv[first] == '-d':
        detailed_model = True
    elif sys.argv[first].startswith("-l"):
        max_level = int(sys.argv[first][2:])
    elif sys.argv[first].startswith("-x"):
        csv_mode = sys.argv[first][2:]
    elif sys.argv[first].startswith("-I"):
        interval_mode = sys.argv[first]
    elif sys.argv[first] == '--':
        first += 1
        break
    else:
        break
    first += 1

if len(sys.argv) - first <= 0:
    usage()

MAX_ERROR = 0.05

def check_ratio(l):
    if print_all:
        return True
    return 0 - MAX_ERROR < l < 1 + MAX_ERROR

class Output:
    "Generate output human readable or as CSV."
    def __init__(self, logfile, csv):
        self.csv = csv
        if logfile:
            self.logf = open(logfile, "w")
            self.terminal = False
        else:
            self.logf = sys.stderr
            self.terminal = self.logf.isatty()

    def s(self, area, hdr, s):
        if self.csv:
            print >>self.logf,"%s%s%s" % (hdr, self.csv, s)
        else:
            if area:
                hdr = "%-7s %s" % (area, hdr)
            print >>self.logf, "%-42s\t%s" % (hdr + ":", s)

    def p(self, area, name, l, timestamp):
        if timestamp:
            sep = " "
            if self.csv:
                sep = self.csv
            print >>self.logf,"%6.9f%s" % (timestamp, sep),
	if l:
            if check_ratio(l):
	        self.s(area, name, "%5s%%"  % ("%2.2f" % (100.0 * l)))
	    else:
		self.s(area, name, "mismeasured")
        else:
            self.s(area, name, "not available")

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
    ("snb", (42, )),
    ("jkt", (45, )),
    ("ivb", (58, )),
    ("ivt", (62, )),
    ("hsw", (60, 70, 71, 69 )),
    ("hsx", (63, )),
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

class PerfRun:
    def execute(self, logfile, r):
	# XXX handle non logfd
	self.logfile = None
	if "--log-fd" in r:
	    outp, inp = pty.openpty()
	    n = r.index("--log-fd")
	    r[n + 1] = "%d" % (inp)
        l = map(lambda x: "'" + x + "'" if x.find("{") >= 0 else x,  r)
        if "--log-fd" in r:
            i = l.index('--log-fd')
            del l[i:i+2]
        print " ".join(l)
	self.perf = subprocess.Popen(r)
	if "--log-fd" not in r:
	     self.perf.wait()
	     self.perf = None
	     self.logfile = logfile
	     return open(logfile, "r")
        else:
	     os.close(inp)
             return os.fdopen(outp, 'r')

    def wait(self):
	if self.perf:
	    self.perf.wait()
        if self.logfile:	
            os.remove(self.logfile)

filter_to_perf = {
    "kernel": "k",
    "user": "u",
}

fixed_counters = {
    "CPU_CLK_UNHALTED.THREAD": "cycles",
    "INST_RETIRED.ANY": "instructions",
    "CPU_CLK_UNHALTED.REF_TSC": "ref-cycles"
}

def filter_string():
    if ring_filter:
        return filter_to_perf[ring_filter]
    return ""

def raw_event(i):
    if i.count(".") > 0:
	if i in fixed_counters:
	    return fixed_counters[i]
        e = emap.getevent(i)
        if e == None:
            print "%s not found" % (i,)
            if not force:
                sys.exit(1)
            return "cycles" # XXX 
        i = e.output(True, filter_string())
    return i

# generate list of converted raw events from events string
def raw_events(evlist):
    return map(lambda x: raw_event(x), evlist)

def pwrap(s):
    print "\n".join(textwrap.wrap(s, 60))

def print_header(work, evlist):
    evnames0 = map(lambda obj: obj.evlist, work)
    evnames = set(itertools.chain(*evnames0))
    names = map(lambda obj: obj.__class__.__name__, work)
    pwrap(" ".join(names) + ": " + " ".join(evnames).lower() + 
            " [%d_counters]" % (len(evnames - set(fixed_counters.keys()))))

def base_event(event):
    event = event.rstrip()
    m = re.match(r"(.*):.*", event)
    if m:
        event = m.group(1)
    return event

def setup_perf(events, evstr):
    plog = "plog.%d" % (os.getpid(),)
    rest = ["-x,", "-e", evstr]
    if interval_mode:
        rest += [interval_mode]
    rest += sys.argv[first:]
    prun = PerfRun()
    #try:
    inf = prun.execute(plog, ["perf", "stat"]  + feat.perf_output(plog).split(" ") + rest)
    #except IOError:
    #    print "Cannot open result file %s" % (plog)
    #    return
    return inf, prun

# execute perf: list of event-groups -> list of results-for-group
# and print result
def execute(events, runner, out):
    inf, prun = setup_perf(events, runner.evstr)
    res = []
    rev = []
    prev_interval = 0.0
    interval = None
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
                        runner.print_res(res, rev, out, prev_interval)
                        res = []
                        rev = []
                    prev_interval = interval
        if l.find(",") < 0:
            print "unparseable perf output"
            print l,
            continue
        count, event = l.split(",", 1) 
        event = base_event(event)
        if re.match(r"[0-9]+,", l):
            val = float(count)
        elif count == "<not counted>":
            print "warning: event %s not counted" % (event)
            val = 0
        elif count == "<not supported>":
            print "warning: event %s not supported" % (event)
            val = 0
        else:
            print "unparseable perf output"
            print l,
            continue
        res.append(val)
        rev.append(event)
    inf.close()
    prun.wait()
    runner.print_res(res, rev, out, interval)

def ev_append(ev, level, obj):
    if not (ev, level) in obj.evlevels:
        obj.evlevels.append((ev, level))
    return 1

def canon_event(e):
    if e.upper() in fixed_counters:
        return fixed_counters[e.upper()]
    if e.endswith("_0"):
        e = e[:-2]
    return e.lower()

def lookup_res(res, rev, ev, index):
    assert canon_event(emap.getperf(rev[index])) == canon_event(ev)
    return res[index]

# dedup a and keep b uptodate
def dedup2(a, b):
    s = sorted(a)
    for j in range(0, len(s) - 1):
        if s[j] == s[j+1]:
            i = a.index(s[j], a.index(s[j]) + 1)
            del a[i]
            del b[i]
    return a, b

def cmp_obj(a, b):
    if a.level == b.level:
        return a.nc - b.nc
    return a.level - b.level

def update_res_map(evlev, objl, base):
    for lev, i in zip(evlev, range(0, len(evlev))):
        for obj in objl:
            if lev in obj.evlevels:
                obj.res_map[lev] = base + i

def get_levels(evlev):
    return map(lambda x: x[1], evlev)

def get_names(evlev):
    return map(lambda x: x[0], evlev)

def num_non_fixed(l):
    n = cpu.counters
    fixed_set = frozenset(fixed_counters.keys())
    while len(set(l[:n]) - fixed_set) < cpu.counters and n < len(l):
        n += 1
    return n

class Runner:
    "Schedule measurements of event groups. Try to run multiple in parallel."
    def __init__(self, max_level):
        self.evnum = [] # flat global list
        self.evstr = ""
        self.olist = []
        self.max_level = max_level

    def run(self, obj):
	obj.thresh = 0.0
        if obj.level > self.max_level:
            return
        obj.res = None
        obj.res_map = dict()
        self.olist.append(obj)

    def split_groups(self, objl, evlev):
        if len(set(get_levels(evlev))) == 1:
            # split again
            while evlev:
                n = num_non_fixed(get_names(evlev))
		l = evlev[:n]
                self.add(objl, raw_events(get_names(l)), l)
                evlev = evlev[n:]
        else:
            # resubmit each level
            max_level = max(get_levels(evlev))
            for l in range(1, max_level + 1):
                evl = filter(lambda x: x[1] == l, evlev)
                if evl:
                    self.add(objl, raw_events(get_names(evl)), evl)

    def add(self, objl, evnum, evlev):
        assert evlev
        # does not fit into a group. 
        if len(set(evnum) - ingroup_events) > cpu.counters:
            self.split_groups(objl, evlev)
            return
        base = len(self.evnum)
        evlev, evnum = dedup2(evlev, evnum)
        update_res_map(evlev, objl, base)

        self.evnum += evnum
        if self.evstr:
            self.evstr += ","
        self.evstr += feat.event_group(evnum)
        print_header(objl, get_names(evlev))

    # collect the events by pre-computing the equation
    def collect(self):
        self.objects = {}
        for obj in self.olist:
            self.objects[obj.name] = obj
        for obj in self.olist:
            obj.evlevels = []
            obj.compute(lambda ev, level: ev_append(ev, level, obj))
            obj.evlist = map(lambda x: x[0], obj.evlevels)
            obj.evnum = raw_events(obj.evlist)
            obj.nc = len(set(obj.evnum) - ingroup_events)

    # fit events into available counters
    # simple first fit algorithm
    def schedule(self, out):
        curobj = []
        curev = []
        curlev = []
        # pass 0:
        # sort objects by level and the by num-counters
        solist = sorted(self.olist, cmp=cmp_obj)
        # pass 1: try to fit each objects events into groups
        # that fit into the available CPU counters
        for obj in solist:
            newev = curev + obj.evnum
            newlev = curlev + obj.evlevels
            needed = len(set(newev) - ingroup_events)
            # when the current group doesn't have enough free slots
            # or is already too large
            # start a new group
            if cpu.counters < needed and curobj:
                self.add(curobj, curev, curlev)
                curobj = []
                curev = []
                curlev = []
                newev = obj.evnum
                newlev = obj.evlevels
            curobj.append(obj)
            curev = newev
            curlev = newlev
        if not curobj:
            return
        self.add(curobj, curev, curlev)

    def print_res(self, res, rev, out, timestamp):
        if len(res) == 0:
            print "Nothing measured?"
            return
        for obj in self.olist:
            if obj.res_map:
                obj.compute(lambda e, level:
                            lookup_res(res, rev, e, obj.res_map[(e, level)]))
                if obj.thresh or print_all:
                    out.p(obj.area if 'area' in obj.__class__.__dict__ else None,
                          obj.name, obj.val, timestamp)
                if obj.thresh and check_ratio(obj.val):
                    out.desc(obj.desc[1:].replace("\n","\n\t"))
                else:
                    obj.thresh = 0 # hide children too
            else:
                out.warning("%s not measured" % (obj.__class__.__name__,))

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

version = map(int, platform.release().split(".")[:2])
if version[0] < 3 or (version[0] == 3 and version[1] < 10):
    print >>sys.stderr, "Older kernel than 3.10. Events may not be correctly scheduled."

if cpu.cpu == None:
    print >>sys.stderr, "Unsupported CPU model %d" % (cpu.model,)
    sys.exit(1)
    
runner = Runner(max_level)

if cpu.cpu == "ivb" and detailed_model:
    import ivb_client_ratios
    ev = ivb_client_ratios.Setup(runner)
elif cpu.cpu == "ivt" and detailed_model:
    import ivb_server_ratios
    ev = ivb_server_ratios.Setup(runner)
elif cpu.cpu == "snb" and detailed_model:
    import snb_client_ratios
    ev = snb_client_ratios.Setup(runner)
elif cpu.cpu == "hsw" and detailed_model:
    import hsw_client_ratios
    ev = hsw_client_ratios.Setup(runner)
else:
    import simple_ratios
    ev = simple_ratios.Setup(runner)

runner.collect()
out = Output(logfile, csv_mode)
runner.schedule(out)
execute(runner.evnum, runner, out)
