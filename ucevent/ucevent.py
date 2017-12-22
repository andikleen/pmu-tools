#!/usr/bin/env python
# Copyright (c) 2013, Intel Corporation
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
# run perf with uncore events and output data in a vmstat/turbostat like running
# normalized format.
#
# requires a perf driver for the uncore (recent Intel server CPUs) and may
# need some kernel patches (see documentation)
# 
# ucevent event .. -- perf arguments
# e.g. ucevent event
# no event => list
# ucevent -h to show other arguments
import argparse
import sys
import textwrap
import os
import re
import subprocess
import pty
import locale
import exceptions
import copy
import fnmatch
import glob
from collections import defaultdict

import ucexpr
import ucmsg

dbg = ucmsg.debug_msg

cpu_mapping = {
    45: "jkt",
    62: "ivt",
    63: "hsx",
    86: "bdxde",
    79: "bdx",
    85: "skx",
}

args = None
per_socket = False

class CPU:
    """Query CPU information."""
    def cpumap(self):
        if (self.vendor == "GenuineIntel" and
            self.family == 6 and
            self.model in cpu_mapping):
            return cpu_mapping[self.model]
        print >>sys.stderr, "Cannot identify CPU model %d" % (self.model)
        return None

    # assumes that physical ids, nodes are all in the same name space
    def __init__(self):
        self.socket = dict()
        f = open("/proc/cpuinfo", "r")
        for l in f:
            n = l.split()
            if len(n) == 0:
                continue
            if n[0] == "processor":
                cpu = int(n[2])
            elif n[0] == "physical" and n[1] == "id":
                s = int(n[3])
                if s not in self.socket:
                    self.socket[s] = cpu
            elif n[0] == "vendor_id":
                self.vendor = n[2]
            elif n[0] == "cpu" and n[1] == "family":
                self.family = int(n[3])
            elif n[0] == "model" and n[1] == ":":
                self.model = int(n[2])
        f.close()

    def max_node(self):
        return max(self.socket)

    def socket_to_cpu(self, s):
        if s in self.socket:
            return self.socket[s]
        sys.exit("Invalid socket %d" % s)
        
cpu = CPU()
cputype = os.getenv("FORCECPU")
if not cputype:
    cputype = cpu.cpumap()
if not cputype:
    sys.exit(1)

code = """
import CPU_uc
events = CPU_uc.events
aliases = CPU_uc.aliases
derived = CPU_uc.derived
categories = CPU_uc.categories
import CPU_extra
extra_derived = CPU_extra.extra_derived
""".replace("CPU", cputype)
try:
    sys.path.append("nda")
    exec code
except ImportError:
    print >>sys.stderr, "Unknown CPU", cputype
    sys.exit(1)
import aux
cpu_aux = aux.Aux()

def lookup_event(name):
    if name in events:
        return events[name]
    if name in derived:
        return derived[name]
    return None

def print_list(f, ls, c, description, equation, ehdr):
    count = 0
    if description:
        wrap = textwrap.TextWrapper(initial_indent="     ",
                                    subsequent_indent="     ")
    for i in sorted(ls.keys()):
        ev = ls[i]
        if ev["Category"] == c:
            count += 1
            
            desc = "?"
            if "Desc" in ev:
                desc = ev["Desc"]
            derived = ""
            if "Broken" in ev and not args.broken:
                continue
            if "Equation" in ev:
                if args.unsupported:
                    derived = " (Derived)"
                elif "Obscure" in ev:
                    continue
            elif not args.unsupported:
                continue
            if args.name_only:
                print >>f, i
                continue
            ehdr.out()
            print >>f, "  %-30s %-40s" % (i, desc + derived)
            if description:
                defn = ""
                if "Defn" in ev:
                    defn = ev["Defn"]
                if "Notes" in ev:
                    defn += " Notes: " + ev["Notes"]
                if "MaxIncCyc" in ev and ev["MaxIncCyc"] > 1:
                    defn += (" May increase upto %d units per cycle." %
                                (ev["MaxIncCyc"]))                    
                print >>f, wrap.fill(defn)
                if "Equation" in ev:
                    eql, equations = convert_equation(ev, dict(), True, True)
                    q = set()
                    for eq in eql:
                        if eq not in ['[',']']:
                            q |= get_qualifiers(perf_box(eq))
                else:
                    q = get_qualifiers(format_box(ev))
                if q:
                    print >>f, wrap.fill("Qualifiers: " + " ".join(q))
                if "Filter" in ev:
                    print >>f, wrap.fill("Filter: " + show_filter(ev["Filter"]))
            if equation:
                if "Equation" in ev:
                    print >>f, "     Equation: ", ev["Equation"]
    return count

def show_one_filter(f):
    if f in cpu_aux.qual_display_alias:
        return cpu_aux.qual_display_alias[f]
    q, v = ucexpr.convert_qual(f, "0")
    return q

def show_filter(f):
    return " ".join(map(show_one_filter, f.split(",")))

qual_cache = dict()

def get_qualifiers(box):
    if not box:
        return set()
    obox = box
    if box in qual_cache:
        return qual_cache[box]
    if not box_exists(box):
        box += "_0"
        if not box_exists(box):
            return set()
    d = os.listdir("/sys/devices/uncore_%s/format" % (box))
    q = set()
    for j in d:
        if j not in ["event", "umask"]:
            q.add(j)
    qual_cache[obox] = q
    return q

def expand_acronyms(n):
    for j in cpu_aux.acronyms:
        n = n.replace(j, j + " (" + cpu_aux.acronyms[j] + ")")
    return n

class EventsHeader:
    def __init__(self, name, f):
        self.printed = False
        self.name = name
        self.f = f

    def out(self):
        if not self.printed and not args.name_only:
            n = expand_acronyms(self.name)
            print >>self.f
            print >>self.f, n
            self.printed = True

def cmp_cat(a, b):
    # XXX move interesting ones first
    return cmp(a.lower(), b.lower())

def get_pager():
    if args.no_pager:
	return sys.stdout, None
    f = sys.stdout
    if f.isatty():
        try:
            sp = subprocess.Popen(["less", "-F"], stdin=subprocess.PIPE)
            return sp.stdin, sp
        except OSError:
            f = sys.stdout
    return f, None

def print_events(cat, desc, equation):
    f, proc = get_pager()
    ecount = 0
    dcount = 0
    if (args.unsupported or args.broken) and not args.name_only:
        print >>f, "\nNot all of these events have been tested and they may be broken"
        print >>f, "USE AT YOUR OWN RISK!"
    for c in sorted(categories, cmp_cat):
        if cat and expand_acronyms(c).lower().find(cat.lower()) < 0:
            continue
        ehdr = EventsHeader(c, f)
        ecount += print_list(f, events, c, desc, equation, ehdr)
        dcount += print_list(f, derived, c, desc, equation, ehdr)
    if proc:
        f.close()
        proc.wait()

def format_equation(ev, qual, quiet=False):
    e = ucexpr.parse(ev["Equation"], ev["Box"], quiet or args.quiet, "UserEq" in ev, qual)
    return e

def format_umask(u):
    u = u[1:]   # drop b
    u = u.replace("x", "0")
    return int(u, 2)

box_dir_cache = []

def find_boxes(prefix):
    if prefix.startswith("uncore_"):
        prefix = prefix[6:]
    global box_dir_cache
    if len(box_dir_cache) == 0:
        box_dir_cache += [x for x in os.listdir("/sys/devices/") if x.startswith("uncore")]
    l = [x.replace("uncore_", "") for x in box_dir_cache if x.startswith("uncore_" + prefix)]
    return sorted(l)

box_cache = dict()

def box_exists(box):
    n = "/sys/devices/uncore_%s" % (box)
    if n not in box_cache:
        box_cache[n] = os.path.exists(n)
    return box_cache[n]

def format_event(ev):
    if "Equation" in ev:
        return format_equation(ev, None)
    return format_reg_event(ev, dict())

# format an event's attributes
def format_attrs(ev, box):
    evsel = ev["EvSel"]
    if "Umask" in ev and ev["Umask"] and box == "pcu":
        evsel |= format_umask(ev["Umask"])
    if "ExtSel" in ev and ev["ExtSel"] != "":
        evsel |= (ev["ExtSel"] << 21)
    attrs = "event=%#x" % (evsel)
    if "Umask" in ev and ev["Umask"] and box != "pcu":
        attrs += ",umask=%#x" % (format_umask(ev["Umask"]))
    if box == "pcu":
        if "SubCtr" in ev and int(ev["SubCtr"]) > 0:
            attrs += ",occ_sel=%d" % (ev["SubCtr"])
    return attrs

box_to_perf = {
    "cbo": "cbox",
    "qpi_ll": "qpi",
    "upi_ll": "upi",
    "sbo": "sbox",
}

def format_box(ev):
    box = ev["Box"].lower()
    if box in box_to_perf:
        box = box_to_perf[box]
    return box

# format a single event for perf
def format_reg_event(ev, qual):
    box = format_box(ev)
    attrs = format_attrs(ev, box)
    if qual:
        attrs += "," + qual
    if not box_exists(box):
        ret = ["uncore_%s/%s/" % (j, attrs) for j in find_boxes(box)]
        if ret:
            return ret
    return ["uncore_%s/%s/" % (box, attrs)]

HEADER_INTERVAL = 50

def is_pct(s):
    return s.find("_PCT") >= 0 or s.find("PCT_") >= 0

nonecount = 0

def get_box(s):
    m = re.match(r"([^.]+)\.(.*)", s)
    if m:
        return re.sub(r"[0-9]+$", "", m.group(1)), m.group(2)
    global nonecount
    nonecount += 1
    return "%d" % (nonecount)

def sum_event(a, b):
    if args.no_sum or a.find("iMC") >= 0 or a.find("QPI_LL") >= 0:
        return False
    return get_box(a) == get_box(b)

def is_str(x):
    return isinstance(x, basestring)

def scale_val(val):
    if args.scale and not is_str(val):
        val = val / units[args.scale]
    return val

PCT_FIELDLEN = 7
OVER_THRESHOLD = 3

units = { "GB": 1024**3, "MB": 1024**2, "KB": 1024 }

class Output:
    """Output data in human readable columns. This also merges boxes
       and implements adaptive column widths."""

    def __init__(self, fieldlen=14, adaptive=False):
        self.headers = []
        self.vals = []
        self.num_output = 0
        locale.setlocale(locale.LC_ALL, '')
        self.FIELDLEN = fieldlen
        self.over = 0
        self.columns = dict()
        self.adaptive = adaptive
        self.timestamp = None

    def out(self, name, r, timestamp):
        if self.vals and sum_event(self.headers[-1], name):
            if is_str(self.vals[-1]) or is_str(r):
                self.vals[-1] = str(self.vals[-1]) + str(r)
            else:
                self.vals[-1] += r    
            self.headers[-1] = self.headers[-1].replace("0.", ".", 1) 
        else:
            self.headers.append(name)
            self.vals.append(r)
        self.timestamp = timestamp

    def fieldlen(self, hdr):
        if self.columns and hdr in self.columns:
            return self.columns[hdr]
        elif is_pct(hdr):
            return PCT_FIELDLEN
        else:
            return self.FIELDLEN

    def update_column(self, hdr, l):
        if not self.adaptive:
            return
        if hdr in self.columns:
            old = self.columns[hdr]
            if l > old:
                self.over += 1
            if self.over >= OVER_THRESHOLD:
                self.columns[hdr] = l
                self.num_output = -1 # force redisplay
        else:
            self.columns[hdr] = l

    def format_field(self, j, h, fieldlen):
        if isinstance(j, float):
            if is_pct(h):
                j *= 100.0
            fmt = "%.2f"
            j = scale_val(j)
        elif is_str(j):
            fmt = "%s"
        else:
            fmt = "%d"
            j = scale_val(j)
        num = locale.format(fmt, j, grouping=True)
        if len(num) >= fieldlen:
            num += " "
        return num

    def print_header(self):
        pre = ""
        for v, j in zip(self.vals, self.headers):
            l = self.fieldlen(j)
            l = max(len(self.format_field(v, j, l)), l)
            print >>args.output, pre + j
            pre += "|" + " "*(l - 1)
            self.columns[j] = l

    def flush(self):
        if (self.num_output % HEADER_INTERVAL) == 0:
            self.print_header()
            self.over = 0 
        out = ""
        for j, h in zip(self.vals, self.headers):
            fieldlen = self.fieldlen(h)
            num = self.format_field(j, h, fieldlen)
            out += "%-*s" % (fieldlen, num)
            self.update_column(h, len(num))
        print >>args.output, out
        self.vals = []
        self.headers = []
        self.num_output += 1

class OutputCSV(Output):
    """CSV version of Output."""

    def __init__(self, csv):
        Output.__init__(self)
        self.csv = csv

    def flush(self):
        if self.num_output == 0:
            print >>args.output, self.csv.join(["timestamp"] + self.headers)
        scaled_vals = map(scale_val, [self.timestamp] + self.vals)
        print >>args.output, self.csv.join(map(str, scaled_vals))
        self.vals = []
        self.headers = []
        self.num_output += 1

groupings = ('[', ']', '{', '}', '[[', ']]')

out = None

class PerfRun:
    """Control a perf process"""
    def __init__(self):
        self.perf = None

    # for testing purposes
    def mock(self, logfile, evl):
        f = open(logfile, "w")
        for t in range(0, 5):
            num = 10000 + t
            for i in evl:
                if i in groupings:
                    continue
                i = i.replace("{","").replace("}","")
                o = "%s,%s" % (num, i)
                to = "%d," % (t)
                print >>f,to + "S0,1,"+o
                print >>f,to + "S1,1,"+o
                num += 10000
        f.close()

    def execute(self, s, logfile, evl):
        if not args.quiet:
            l = map(lambda x: "'" + x + "'" if x.find("{") >= 0 else x,  s)
            i = l.index('--log-fd')
            del l[i:i+2]
            print >>args.output, " ".join(l)
        if args.mock:
            self.mock(logfile, evl)
            self.perf = None
        else:
            self.perf = subprocess.Popen(s, close_fds=False)

def perf_box(x):
    m = re.match(r"uncore_([^/]+)(_\d+)?/", x)
    if not m:
        return None
    return m.group(1)

def available_counters(box):
    if box in cpu_aux.limited_counters:
        return cpu_aux.limited_counters[box]
    return cpu_aux.DEFAULT_COUNTERS

def count_filter(ev):
    return sum(map(lambda x: ev.count("," + x), cpu_aux.filters))

def is_fixed(x):
    return x.find("/clockticks/") >= 0

# determine if equation can run in a group
def supports_group(evl, nl):
    evl = filter(lambda x: not is_fixed(x), evl)
    boxes = defaultdict(list)
    bnames = defaultdict(list)
    for j, n in zip(evl, nl):
        box = perf_box(j)
        if not box:
            continue
        boxes[box].append(j)
        bnames[box].append(n)
    for box in boxes:
        # some events have too complicated counter constraints for 
        # this pear brain scheduler to decide if groups work or not. Just do
        # not do groups for them.
        for n in bnames[box]:
            ev = lookup_event(n)
            if complicated_counters(ev):
                return False
        evl = boxes[box]
        filters = sum(map(count_filter, evl))
        if len(evl) > available_counters(box) or filters > 1:
            return False
    return True

def count_box(box):
    return len(find_boxes(box))

# run a equation
def evaluate(eq, EV):
    SAMPLE_INTERVAL = float(args.interval)*1000000
    ROUND = lambda x: round(x)
    KB = 1024
    MB = 1024*KB
    GB = 1024*MB
    KILO = 1000
    MEGA = 1000*KILO
    GIGA = 1000*MEGA
    NUM_R3QPI = count_box("r3qpi") # XXX add generic function
    dbg("evaluate", eq)
    try:
        return eval(eq)
    except NameError:
        return "#EVAL"
    except ZeroDivisionError:
        return 0.0

def is_error(x):
    return is_str(x) and x.startswith("#")

# read perf output and output results
def gen_res(evl, res, evp, equations, evnames, timestamp):
    dbg("evl", evl)
    dbg("res", res)
    dbg("evp", evp)
    dbg("equations", equations)
    cur_eq = None
    eql = equations
    for j in evl:
        if j == '[' or j == '[[':
            cur_eq = eql[0]
            eq_events = dict()
        elif j == ']' or j == ']]':
            r = None
            for x in eq_events:
                if is_error(eq_events[x]):
                    r = eq_events[x]
                    break
            if r is None:
                if '/' in equations[0]:
                    EV = lambda x, n: float(eq_events[x])
                else:
                    EV = lambda x, n: long(eq_events[x])
                r = evaluate(equations[0], EV)
                dbg("result", r)
            out.out(evnames[0], r, timestamp)
            equations = equations[1:]
            cur_eq = None
            evnames = evnames[1:]
        elif cur_eq:
            assert evp[0] == j
            eq_events[evp[0]] = res[0]
            res = res[1:]
            evp = evp[1:]
        elif j in ('{', '}'):
            continue
        else:
            assert evp[0] == j
            if re.match(r"[0-9]+", res[0]):
                r = int(res[0])
            else:
                r = res[0]
            out.out(evnames[0], r, timestamp)
            evnames = evnames[1:]
            res = res[1:]
            evp = evp[1:]
    out.flush()
    assert len(res) == 0
    assert len(evp) == 0

# replace internal [] equation groups with perf format
def gen_events(evl):
    e = ""
    prev = ""
    for j in evl:
        if j == '[' or j == ']':
            continue
        if j == '[[':
            j = '{'
        elif j == ']]':
            j = '}'
        sep = ""
        if prev:
            match = [prev in groupings, j in groupings]
            if match == [True, True] or match == [False, False]:
                sep = ","
            if prev in ['[', '{'] and match[1] == False:
                sep = ""
            if prev in [']', '}']:
                sep = ","
            if match[0] == False and j in ['[', '{']:
                sep = ","
        e += sep + j
        prev = j
    return e

def concat(d):
    x = []
    for j in sorted(d.keys()):
        x += d[j]
    return x

def gennames(names, sockets):
    x = []
    for s in sorted(sockets):
        if s != "":
            s += "-"
        for n in names:
            x.append(s + n)
    return x

def check_per_socket(s, warned):
    if (not warned and
            sorted(map(lambda x: int(x[1:]), s)) != range(0, len(s))):
        ucmsg.warning("perf --per-socket appears broken. Please update perf.")
        ucmsg.warning("Data on socket > 0 will be likely incorrect.")
        return True
    return warned

perf_errors = {
    "<not supported>": "#NS",
    "<not counted>": "#NC",
}

# run perf and output results
def measure(evl, argl, equations, evnames):
    warned = False
    all_events = gen_events(evl)
    ## use a pty because perf doesn't do enough fflush() otherwise
    outp, inp = pty.openpty()
    logfile = "ulog.%d" % (os.getpid())
    run = PerfRun()
    run.execute([perf, "stat", "--log-fd", "%d" % (inp), "-e", all_events] + argl, logfile, evl)
    prev_timestamp = None
    evp = defaultdict(list)
    res = defaultdict(list)
    socket = ""
    try:
        if args.mock:
            f = open(logfile, 'r')
        else:
            f = os.fdopen(outp, 'r')
            os.close(inp)
        while True:
            try:
                # force line-by-line buffering
                l = f.readline()
                if not l:
                    break
            except (KeyboardInterrupt, exceptions.IOError):
                break
            l = l.strip()
            dbg("perf", l)
            if l.startswith('#') or l == "":
                continue
            if per_socket:
                ts, socket, _, rest = l.split(",", 3)
                l = ts + "," + rest
            # uncore// contains commas!
            m = re.match(r"([0-9.]+),([0-9]+|<.*>),?,(.*)$", l)
            if not m:
                print "PERF-UNREADABLE", l,
                continue
            timestamp = m.group(1)
            if timestamp != prev_timestamp:
                if per_socket and not args.quiet:
                    warned = check_per_socket(res.keys(), warned)
                if evp:
                    num = len(res)
                    gen_res(evl*num, concat(res), concat(evp),
                            equations*num, gennames(evnames, res.keys()), timestamp)
                res = defaultdict(list)
                evp = defaultdict(list)
            prev_timestamp = timestamp
            r = m.group(2)
            if r.startswith("<"):
                if r in perf_errors:
                    r = perf_errors[r]
                else:
                    r = "#NA"
            res[socket].append(r)
            p = m.group(3)
	    if p.find("/,") >= 0:
                p = re.sub(r"/,.*", "", p) + "/"
            if p.startswith(","):
                p = p[1:]
            evp[socket].append(p)
        f.close()
        if args.mock:
            os.remove(logfile)
    except exceptions.IOError:
        # ptys always seem to end with EIO
        #print "Error talking to perf", e
        pass
    if evp:
        num = len(res)
        gen_res(evl*num, concat(res), concat(evp), equations*num,
                gennames(evnames, res.keys()), timestamp)
    if run.perf:
        run.perf.wait()

dummy_count = 1000

def ev_append(ovl, x, nl, n):
    if x not in ovl:
        ovl.append(x)
    if n not in nl:
        nl.append(n)
    global dummy_count
    dummy_count += 1
    return dummy_count # dummy value to avoid division by zero

class WarnOnce:
    def __init__(self):
        self.warned = False
    def warn(self, msg):
        if not self.warned:
            ucmsg.warning(msg)
            self.warned = True

def add_group(x, nl, in_group, mw):
    if len(x) == 0:
        return x
    if len(x) > 1 and not in_group:
        if supports_group(x, nl):
            return ['[['] + x + [']]']
        mw.warn("Equation will multiplex and may produce inaccurate results (see manual)")
    return ['['] + x + [']']

# convert a equation to perf form
def convert_equation(ev, qual, in_group, quiet=False):
    mw = WarnOnce()
    nnl = []
    evl = []
    equations = []
    eql = format_equation(ev, qual, quiet)
    for p in eql:
        ovl = []
        nl = []
        # run equation to collect events
        r = evaluate(p, lambda x, n: ev_append(ovl, x, nl, n))
        if is_error(r) and not args.quiet:
            print >>sys.stderr, "Cannot evaluate equation", ev["Equation"]
        nnl.append(nl)
        evl.append(ovl)
        equations.append(p)
    flat_eql = []
    for j, nl in zip(evl, nnl):
        flat_eql += add_group(j, nl, in_group, mw)
    return flat_eql, equations

standard_events = ("cycles", "ref-cycles", "instructions")

# convert a single event to perf form
def convert_one(evn, evl, evnames, equations, qual, in_group):
    ev = lookup_event(evn)
    if not ev:
        print >>sys.stderr, "unknown event", evn
        sys.exit(1)
    if "Equation" in ev:
        nvl, neql = convert_equation(ev, qual, in_group)
        equations += neql
        num = len(neql)
    else:
        nvl = format_reg_event(ev, qual)
        # should run this in a group XXX
        num = len(nvl)
    evl += nvl
    # add index numbers to names
    if num > 1:
        evnames += map(lambda x, y: x.replace(".", "%d." % (y),1),
                       [evn] * num, range(0, num))
    else:
        evnames.append(evn)
    return evl, evnames, equations

# equation on command line
def user_equation(evn, in_group):
    # XXX no qualifiers for now, as the the , conflicts with "with:"
    ev = dict()
    ev["Equation"] = evn
    ev["Box"] = ""
    ev["UserEq"] = True
    return convert_equation(ev, dict(), in_group)

# convert command line events to perf form
def convert_events(arg_events):
    print_events = []
    equations = []
    evnames = []
    evl = []
    j = 0
    in_group = 0
    for evn in arg_events:
        if evn == "--":
            j += 1
            break
        if evn in standard_events:
            evnames.append(evn)
            evl.append(evn)
            j += 1
            continue
        if evn in ['{', '}']:
            if evn == '{':
                in_group += 1
            else:
                in_group -= 1
            evl += evn
            j += 1
            continue
        if evn.count(".") == 0:
            break
        print_events.append(evn)
        # not checking for * here, as it conflicts with wildcards
        if re.search(r"[ /()+-]", evn):
            nvl, neql = user_equation(evn, in_group)
            equations += neql
            evl += nvl
            evnames += [evn] * len(nvl)
            j += 1
            continue
        qual = ""
        n = evn.split(",", 1)
        if len(n) > 1:
            evn = n[0]
            qual = n[1]
        if re.search(r"[[*?]", evn):
            for me in sorted(events.keys() + derived.keys()):
                if fnmatch.fnmatch(me, evn):
                    evl, evnames, equations = convert_one(me, evl, evnames,
                                                          equations, qual, in_group)
        else:
            evl, evnames, equations = convert_one(evn, evl, evnames, equations,
                                                  qual, in_group)
        j += 1
    if not args.quiet:
        print >>args.output, "Events:", " ".join(print_events)
    return evl, equations, evnames, args.events[j:]

def fix_field(nev, key, old, num):
    nev[key] = nev[key].replace(old, old.replace("x", str(num)))

# expand a single event
def expand_ev(table, name, num):
    ev = table[name]
    for n in range(0, num):
        nev = copy.deepcopy(ev)
        fix_field(nev, "Equation", ",x", n)
        fix_field(nev, "Equation", "=x", n)
        fix_field(nev, "Equation", "RANKx", n)
        fix_field(nev, "Equation", "NODEx", n)
        fix_field(nev, "Desc", "Rank x", n)
        fix_field(nev, "Desc", "Node x", n)
        fix_field(nev, "Defn", "(x)", n)
        table[name.replace("x", str(n))] = nev
    del table[name]

def maybe_expand_ev(table, name, max_node):
    if name.find("NODEx") >= 0:
        expand_ev(table, name, max_node)
    elif name.find("RANKx") >= 0:
        expand_ev(table, name, cpu_aux.MAX_RANK)

# XXX should do this at generation time
def expand_events():
    max_node = cpu.max_node() + 1
    for j in derived.keys():
        maybe_expand_ev(derived, j, max_node)
    for j in events.keys():
        maybe_expand_ev(events, j, max_node)
    for j in extra_derived:
        derived[j] = extra_derived[j]
    
def get_counter(c):
    m = re.match(r"(\d+)-(\d+)", c)
    if m:
        start = int(m.group(1))
        return start, int(m.group(2))
    return int(c), int(c)

# index=0 start of ranges, index=1 end of ranges
def counter_list(counters, index):
    return map(lambda x: get_counter(x)[index], str(counters).split(","))

# check for complicated counters our simple scheduler cannot handle
def complicated_counters(ev):
    counters = ev["Counters"]
    return (max(counter_list(counters, 1)) < available_counters(format_box(ev)) - 1 or
                max(counter_list(counters, 0)) > 0)

def check_events():
    ae = dict()
    for j in sorted(events.keys()):
        ev = events[j]
        box = j[:j.index(".")]
        if "EvSel" not in ev:
            print j,"has no evsel"
        umask = ""
        extsel = 0
        if "Umask" in ev:
            umask = ev['Umask']
        if "ExtSel" in ev:
            extsel = ev['ExtSel']
            if extsel == "":
                extsel = 0
        key = box, ev['EvSel'], extsel, umask
        if key in ae:
            print ae[key],"duplicated with",j,key
        else:
            ae[key] = j
        if complicated_counters(ev):
            print "event %s has complicated counters:  %s" % (j, ev["Counters"])

def check_multiplex():
    if args.quiet:
        return
    found = False
    for j in glob.iglob("/sys/devices/uncore_*/perf_event_mux_interval_ms"):
        found = True
        break
    if not found:
        ucmsg.warning("No hrtimer multiplexing support in kernel.")
        ucmsg.warning("Multiplexed events will be incorrect when not fully busy.")

def event_dummy(e, n):
    global dummy_count
    dummy_count += 1
    return dummy_count

def parse_all():
    errors = 0
    empty = 0
    for name in derived.keys():
        print "---",name,": "
        el = format_event(derived[name])
        for e in el:
            print e
            r = evaluate(e, event_dummy)
            print "result:", r
            if is_error(r):
                errors += 1
        if not el:
            print "empty list"
            empty += 1
    print "%d errors, %d empties" % (errors, empty)

perf = os.getenv("PERF")
if not perf:
    perf = "perf"

expand_events()

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='''
Intel Xeon uncore performance counter events frontend for perf. The uncore is the 
part of the CPU that is not core. This tool allows to monitor a variety of
metrics in the uncore, including memory, QPI, PCI-E bandwidth, cache hit
rates, power management statistics and various others.''')
    p.add_argument('--cat',
                   help='Only print events from categories containing this in list')
    p.add_argument('--unsupported', action='store_true',
                   help='''
Print all events, including unsupported and potentially broken ones.
Use at your own risk.''')
    p.add_argument('--broken', action='store_true', help=argparse.SUPPRESS)
    p.add_argument('--desc', help='Print detailed descriptions in list',
                   action='store_true')
    p.add_argument('--name-only', help='Only print event name in list',
                   action='store_true')
    p.add_argument('--equation', help='Print equations for derived events in list',
                    action='store_true')
    p.add_argument('--attr', help='Print attributes', action='store_true')
    p.add_argument('--parse-all', help=argparse.SUPPRESS,
                   action='store_true')
    p.add_argument('--mock', action='store_true', help=argparse.SUPPRESS)
    p.add_argument('--scale', help='Scale numbers to unit (GB,MB,KB)', choices=units)
    p.add_argument('--csv', '-x',
                   help='Enable CSV mode and use argument to separate fields')
    p.add_argument('events', nargs='*', help="""
List of events to be converted. May have a comma separate list of name=val
qualifiers after comma for each event (see --desc output for valid qualifiers).
Can use { and } (each as own argument and quoted) to define groups.
Valid to use shell-style wildcards (quoted) to match multiple events.
It is also valid to specify a equation (quoted, containing space).
After -- a perf argument line can be specified (e.g. sleep NUM or a
workload to run). Please note that ucevent measurements are always
global to the specified socket(s) unlike normal perf stat.""")
    p.add_argument('--interval', '-I', default=1000, type=int,
                   help='Measurement interval in ms')
    p.add_argument('--socket', '-S', help='Measure only socket (default all)',
                   type=int)
    p.add_argument('--cpu', '-C',
                   help='''
Measure socket associated with CPU, 
or use that CPU for the (very few) events that use core events''', type=int)
    p.add_argument('--fieldlen', default=6, help='Set output field length',
                   type=int)
    p.add_argument('--verbose', '-v', help='More verbose output', action='store_true',
                   default=False)
    p.add_argument('--quiet', help=argparse.SUPPRESS, default=True)
    p.add_argument('--no-sum', help='Don\'t sum up multiple instances of units', action='store_true')
    p.add_argument('--check-events', help=argparse.SUPPRESS, action='store_true')
    p.add_argument('--output', '-o', help='Set output file', default=sys.stdout,
                   type=argparse.FileType('w'))
    p.add_argument('--resolve', action='store_true',
                   help='Only print resolved event names. Do not run perf.')
    p.add_argument("--no-pager", action='store_true',
		   help='Do not use a pager')
    p.add_argument('--debug', help=argparse.SUPPRESS)
    args = p.parse_args()

    if args.verbose:
        args.quiet = False

    ucmsg.quiet = args.quiet
    ucmsg.debug = args.debug

    if args.check_events:
        check_events()
        sys.exit(0)

    if args.csv:
        out = OutputCSV(args.csv)
    else:
        out = Output(args.fieldlen, True)

    if args.parse_all:
        parse_all()
    elif not args.events:
        print_events(args.cat, args.desc, args.equation)
    else:
        if not args.mock:
            check_multiplex()

        argl = ['-I%s' % (args.interval), '-x,']
        if args.cpu is not None:
            argl.append('-C%d' % (args.cpu))
        elif args.socket is not None:
            argl.append('-C%d' % (cpu.socket_to_cpu(args.socket)))
        else:
            argl.append('-a')
            argl.append('--per-socket')
            per_socket = True

        evl, equations, evnames, rest = convert_events(args.events)
        if len(rest) == 0:
            rest = ["sleep", "999999"]
        if len(evl) == 0:
            print >>sys.stderr, "no events to measure"
            sys.exit(1)
        if args.resolve:
            for ev, evname in zip(evl, evnames):
                print evname,"\t",ev
            sys.exit(0)
        try:
            measure(evl, argl + rest, equations, evnames)       
        except OSError as e:
            print "perf failed to run:", e
            sys.exit(1)
