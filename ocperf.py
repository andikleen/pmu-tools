#!/usr/bin/env python2
# Copyright (c) 2011-2015, Intel Corporation
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
# wrapper for perf for using named events and events with additional MSRs.
# syntax is like perf, except Intel events are listed and can be specified
#
# or library for other python program to convert intel event names to
# perf/raw format
#
# Features:
# - map intel events to raw perf events
# - enable disable workarounds for specific events
# - resolve uncore events
# - handle offcore event on older kernels
# For the later must run as root and only as a single instance per machine
# Normal events (mainly not OFFCORE) can be handled unprivileged
# For events you can specify additional intel names from the list
#
# env variables:
# PERF=... perf binary to use (default "perf")
# EVENTMAP=eventmap
# EVENTMAP2=eventmap
# EVENTMAP3=eventmap
# OFFCORE=eventmap
# UNCORE=eventmap
# UNCORE2=eventmap
# eventmap is a path name to a json file. can contain wildcards.
# When eventmap is not specified, look in ~/.cache/pmu-events/
# The eventmap is automatically downloaded there
# eventmap can be also a CPU identifer (GenuineIntel-FAMILY-MODEL, like GenuineIntel-06-37)
# (Note that the numbers are in upper case hex)
#
# TOPOLOGY=topologyfile
# topologyfile is a dump of the sysfs of another system (find /sys > file)
# Needed for uncore units. This is useful to generate perf command lines for other systems.
#
# OCVERBOSE=1 print while files are opened
#
# Special arguments:
# --no-period   Never add a period
# --print       only print
# --force-download Force event list download
# --experimental Support experimental events
# --noexplode  Don't list all sub pmus for uncore events. Rely on perf stat to merge.
from __future__ import print_function
import sys
import os
import subprocess
import json
import re
import copy
import textwrap
import pipes
import itertools
from pmudef import *

import msr as msrmod
import latego
import event_download

force_download = False
pebs_enable = "p"
experimental = False
ocverbose = os.getenv("OCVERBOSE") is not None

exists_cache = dict()

topology = None

def file_exists(s):
    if s in exists_cache:
        return exists_cache[s]
    global topology
    if topology is None:
        top = os.getenv("TOPOLOGY")
        topology = set()
        if top:
            try:
                topology = set([x.strip() for x in open(top).readlines()])
            except OSError:
                print("Cannot open", top, file=sys.stderr)
    if s in topology:
        return True
    found = os.path.exists(s)
    exists_cache[s] = found
    return found

def has_format(s, pmu="cpu"):
    return file_exists("/sys/devices/%s/format/%s" % (pmu, s))

def has_format_any(f, u):
    return has_format(f, u) or has_format(f, u + "_0")

warned = set()

def warn_once(s):
    if s not in warned:
        print(s, file=sys.stderr)
        warned.add(s)

class PerfVersion:
    def __init__(self):
        minor = 0
        perf = os.getenv("PERF")
        if not perf:
            perf = "perf"
        try:
            version = subprocess.Popen([perf, "--version"], stdout=subprocess.PIPE).communicate()[0]
        except OSError:
            print("Cannot run", perf)
            version = ""
        m = re.match(r"perf version (\d+)\.(\d+)\.", version.decode('utf-8'))
        if m:
            major = m.group(1)
            minor = m.group(2)
            if re.match("[0-9]+", minor):
                minor = int(minor, 10)
            if re.match("[0-9]+", major) and int(major) > 3:
                minor = 100 # infinity

        self.direct = os.getenv("DIRECT_MSR") or minor < 4
        self.offcore = has_format("offcore_rsp") and not self.direct
        self.ldlat = has_format("ldlat") and not self.direct
        self.has_name = minor >= 4

version = PerfVersion()

class MSR:
    def __init__(self):
        self.reg = {}

    def writemsr(self, msrnum, val, print_only = False):
        print("msr %x = %x" % (msrnum, val, ))
        if print_only:
            return
        msrmod.writemsr(msrnum, val)

    def checked_writemsr(self, msr, val, print_only = False):
        if msr in self.reg:
            sys.exit("Multiple events use same register")
        self.writemsr(msr, val, print_only)
        self.reg[msr] = 1

qual_map = (
    ("amt1", "any=1", EVENTSEL_ANY, ""),
    ("percore", "percore=1", 0, ""),
    ("perf_metrics", "", 0, ""),
    ("i1", "inv=1", EVENTSEL_INV, ""),
    ("e1", "edge=1", 0, ""),
    ("e0", "edge=0", 0, ""),
    ("tx", "in_tx=1", 0, ""),
    ("sup", "", 0, "k"),
    ("SUP", "", 0, "k"),
    ("usr=yes", "", 0, "u"),
    ("usr=no", "", 0, "k"),
    ("anythr=yes", "any=1", 0, ""),
    ("cp", "in_tx_cp=1", 0, ""))

qualval_map = (
    (r"u(0x[0-9a-f]+)", "umask=%#x", 0),
    (r"c(?:mask=)?(0x[0-9a-f]+|[0-9]+)", "cmask=%d", 24),
    (r"e(?:dge=)?(0x[0-9a-f]+|[0-9]+)", "edge=%d", 18),
    (r"(?:sa|sample-after|period)=([0-9]+)", "period=%d", 0))

uncore_map = (
    (r'e(\d)', 'edge='),
    (r't=(\d+)', "thresh="),
    (r'[Mm]atch=(0x[0-9a-fA-F]+)', "filter_occ="),
    (r'filter1=(0x[0-9a-fA-F]+)', "config1=", 32),
    ("nc=(\d+)", "filter_nc="),
    (r'filter=(0x[0-9a-fA-F]+)', "config1="),
    (r'one_unit', '', ),
    (r"u(0x[0-9a-fA-F]+)", "umask="),
    (r"opc=?(0x[0-9a-fA-F]+)", "filter_opc="),
    (r"tid=?(0x[0-9a-fA-F]+)", "filter_tid="),
    (r"state=?(0x[0-9a-fA-F]+)", "filter_state="))

uncore_map_thresh = (
    (r"c(?:mask=)?([0-9a-fA-Fx]+)", "thresh="),)

uncore_map_cmask = (
    (r"c(?:mask=)?(0x[0-9a-fA-F]+|[0-9]+)", "cmask="),)

# newe gets modified
def convert_extra(extra, val, newe):
    nextra = ""
    while extra:
        if extra[0] == ":":
            extra = extra[1:]
            continue
        found = False
        for j in qualval_map:
            m = re.match(j[0], extra)
            if m:
                if j[2]:
                    val |= int(m.group(1), 0) << j[2]
                newe.append(j[1] % (int(m.group(1), 0)))
                extra = extra[len(m.group(0)):]
                found = True
                break
        if found:
            continue
        found = False
        for j in qual_map:
            if extra.startswith(j[0]):
                val |= j[2]
                newe.append(j[1])
                extra = extra[len(j[0]):]
                nextra += j[3]
                found = True
                break
        if found:
            continue
        if not extra:
            break
        if extra[0] in perf_qual + "p":
            nextra += extra[0]
            extra = extra[1:]
            continue
        print("bad event qualifier", extra, file=sys.stderr)
        break
    return nextra, val

def gen_name(n, sup):
    n = n.replace(".", "_").replace(":", "_").replace("=", "_")
    if sup:
        n += "_k"
    return n

class Event:
    def __init__(self, name, val, desc):
        self.val = val
        self.name = name
        self.extra = ""
        self.msr = 0
        self.msrval = 0
        self.desc = desc
        self.pebs = 0
        self.newextra = ""
        self.overflow = None
        self.errata = None
        self.counter = ""
        self.period = 0

    # XXX return with pmu to be consistent with Uncore and fix callers
    def output_newstyle(self, extra="", noname=False, period=False, name="", noexplode=False):
        """Format an perf event for output and return as perf event string.
           Always uses new style (cpu/.../)."""
        val = self.val
        if extra:
            extra = self.newextra + "," + extra
        else:
            extra = self.newextra
        e = "event=0x%x,umask=0x%x%s" % (val & 0xff, (val >> 8) & 0xff, extra)
        if version.has_name:
            if name:
                e += ",name=" + name
            elif not noname:
                e += ",name=%s" % (gen_name(self.name, "sup" in (self.extra + extra)))
        if period and self.period and not ",period=" in e:
            e += ",period=%d" % self.period
        return e

    def output(self, use_raw=False, flags="", noname=False, period=False, name="", noexplode=False):
        """Format an event for output and return as perf event string.
           use_raw when true return old style perf string (rXXX).
           Otherwise chose between old and new style based on the
           capabilities of the installed perf executable.
           flags when set add perf flags (e.g. u for user, p for pebs)."""
        val = self.val
        newe = []
        extra = "".join(merge_extra(extra_set(self.extra), extra_set(flags)))
        extra, val = convert_extra(":" + extra, val, newe)
        if version.direct or use_raw:
            ename = "r%x" % (val,)
            if extra:
                ename += ":" + extra
            # XXX should error for extras that don't fit into raw
        else:
            ename = "cpu/%s/" % (self.output_newstyle(extra=",".join(newe), noname=noname, period=period, name=name)) + extra
        return ename

    def filter_qual(self):
        def check_qual(q):
            if q == "":
                return True
            if "=" in q:
                q, _ = q.split("=")
            if has_format_any(q, "cpu"):
                return True
            warn_once("cpu: format %s not supported. Filtering out" % q)
            return False
        self.newextra = ",".join(filter(check_qual, self.newextra.split(",")))

box_to_perf = {
    "cbo": "cbox",
    "qpi_ll": "qpi",
    "sbo": "sbox",
}

def box_exists(box):
    return file_exists("/sys/devices/uncore_%s" % (box))

def int_or_zero(row, name):
    if name in row:
        if row[name] == 'False':
            return 0
        if row[name] == 'True':
            return 1
        return int(row[name])
    return 0

uncore_units = {
    "imph-u": "arb",
    "kti ll": "upi",
    "m3kti": "m3upi",
    "upi ll": "upi",
}

def convert_uncore(flags, extra_map):
    o = ""
    while flags:
        for j in uncore_map + extra_map:
            if flags[0] == ",":
                flags = flags[1:]
            match, repl = j[0], j[1]
            m = re.match(match, flags)
            if m:
                if repl == "":
                    pass
                elif len(j) > 2:
                    o += "," + repl + ("%#x" % (int(m.group(1), 0) << j[2]))
                else:
                    o += "," + repl + m.group(1)
                flags = flags[m.end():]
            if flags == "":
                break
            if flags[0:1] == ":":
                flags = flags[1:]
        else:
            if flags != "":
                if len(extra_map) > 0:
                    print("Uncore cannot parse", flags, file=sys.stderr)
                break
    return o

class UncoreEvent:
    def __init__(self, name, row):
        self.name = name
        e = self
        if 'PublicDescription' in row:
            e.desc = row['PublicDescription'].strip()
        elif 'BriefDescription' in row:
            e.desc = row['BriefDescription'].strip()
        else:
            e.desc = row['Description'].strip()
        e.code = int(row['EventCode'], 16)
        if 'Internal' in row and int(row['Internal']) != 0:
            e.code |= int(row['Internal']) << 21
        e.umask = int(row['UMask'], 16)
        e.cmask = int_or_zero(row, 'CounterMask')
        e.inv = int_or_zero(row, 'Invert')
        e.edge = int_or_zero(row, 'EdgeDetect')
        e.unit = row['Unit'].lower()
        if e.unit in uncore_units:
            e.unit = uncore_units[e.unit]
        if e.unit == "ncu":
            e.unit = "cbox_0"
            e.umask = 0
            e.code = 0xff
        # xxx subctr
        if e.unit in box_to_perf:
            e.unit = box_to_perf[e.unit]
        e.msr = None
        e.overflow = 0
        e.counter = "1" # dummy for toplev
        e.newextra = ""
        if 'Errata' in row:
            e.errata = row['Errata']
        else:
            e.errata = None

    #  {
    # "Unit": "CBO",
    # "EventCode": "0x22",
    # "UMask": "0x21",
    # "EventName": "UNC_CBO_XSNP_RESPONSE.MISS_EXTERNAL",
    # "Description": "An external snoop misses in some processor core.",
    # "Counter": "0,1",
    # "CounterMask": "0",
    # "Invert": "0",
    # "EdgeDetect": "0"
    # },
    # XXX cannot separate sockets
    # extra: perf flags
    # flags: emon flags
    def output_newstyle(self, newextra="", noname=False, period=False, name="", flags="", noexplode=False):
        e = self
        o = "/event=%#x" % e.code
        if e.umask:
            o += ",umask=%#x" % e.umask
        if e.cmask:
            o += ",cmask=%#x" % e.cmask
        if e.edge:
            o += ",edge=1"
        if e.inv:
            o += ",inv=1"

        if e.newextra:
            if flags:
                flags += ","
            flags += e.newextra

        one_unit = "one_unit" in flags

        if has_format_any("cmask", "uncore_" + e.unit):
            extra_map = uncore_map_cmask
        else:
            extra_map = uncore_map_thresh

        o += convert_uncore(flags, extra_map)

        # xxx subctr, occ_sel, filters
        if version.has_name and not noname:
            if name == "":
                name = e.name.replace(".", "_")
            o += ",name=" + name + "_NUM"
        if newextra:
            o += "," + ",".join(newextra)
        o += "/"

        # explode boxes if needed
        def box_name(n):
            return "%s_%d" % (e.unit, n)
        def box_n_exists(n):
            if one_unit and n > 0:
                return False
            return box_exists(box_name(n))
        if not noexplode and not box_exists(e.unit) and box_n_exists(0):
            return ",".join(["uncore_" + box_name(x) + o.replace("_NUM", "_%d" % (x)) for x in
                             itertools.takewhile(box_n_exists, itertools.count())])
        return "uncore_%s%s" % (e.unit, o.replace("_NUM", ""))

    def filter_qual(self):
        def check_qual(q):
            if q == "":
                return False
            if q == "one_unit":
                return True
            if "=" in q:
                q, _ = q.split("=")
            if has_format_any(q, "uncore_" + self.unit):
                return True
            warn_once("%s: format %s not supported. Filtering out" % (self.unit, q))
            return False

        self.newextra = ",".join(filter(check_qual, convert_uncore(self.newextra, ()).split(",")))


    output = output_newstyle

def ffs(flag):
    assert flag != 0
    m = 1
    j = 0
    while (flag & m) == 0:
        m = m << 1
        j += 1
    return j

perf_qual = "kuhGHSD" # without pebs

def extra_set(e):
    return set(map(lambda x: x[0],
        re.findall(r"(" + "|".join([x[0] for x in qual_map + qualval_map + uncore_map]) + "|[" + perf_qual + "]|p+)", e)))

def merge_extra(a, b):
    m = a | b
    if 'ppp' in m:
        m = m - set(['p', 'pp'])
    if 'pp' in m:
        m = m - set(['p'])
    m = m - set([':'])
    return m

def print_event(name, desc, f, human, wrap):
    desc = "".join([y for y in desc if y < chr(127)])
    print("  %-42s" % (name,), end='', file=f)
    if human:
        print("\n%s" % (wrap.fill(desc),), file=f)
    else:
        print(" [%s]" % (desc,), file=f)

def uncore_exists(box, postfix=""):
    if file_exists("/sys/devices/uncore_" + box + postfix):
        return True
    if file_exists("/sys/devices/uncore_" + box + "_0" + postfix):
        return True
    return False

missing_boxes = set()

def check_uncore_event(e):
    if uncore_exists(e.unit):
        if e.cmask and not uncore_exists(e.unit, "/format/cmask"):
            warn_once("Uncore unit " + e.unit + " missing cmask for " + e.name)
            return None
        if e.umask and not uncore_exists(e.unit, "/format/umask"):
            warn_once("Uncore unit " + e.unit + " missing umask for " + e.name)
            return None
        return e
    if e.unit not in missing_boxes:
        warn_once("Uncore unit " + e.unit + " missing")
        missing_boxes.add(e.unit)
    return None

fixed_counters = {
    "inst_retired.any": (0xc0, 0, 0),
    "cpu_clk_unhalted.thread": (0x3c, 0, 0),
    "cpu_clk_unhalted.thread_any": (0x3c, 0, 1),
    "topdown.slots": (0x00, 0x04, 0),
}

def update_ename(ev, name):
    if ev:
        ev = copy.deepcopy(ev)
        ev.name = name
    return ev

class EmapNativeJSON(object):
    """Read an event table."""

    def __init__(self, name):
        self.events = {}
        self.perf_events = {}
        self.codes = {}
        self.desc = {}
        self.pevents = {}
        self.latego = False
        self.uncore_events = {}
        self.error = False
        self.read_events(name)

    def add_event(self, e):
        self.events[e.name] = e
        self.perf_events[e.name.replace('.', '_')] = e # workaround for perf-style naming
        self.codes[e.val] = e
        self.desc[e.name] = e.desc

    def read_table(self, r, m):
        for row in r:
            get = lambda x: row[m[x]]
            gethex = lambda x: int(get(x).split(",")[0], 16)
            getdec = lambda x: int(get(x), 10)

            name = get('name').lower().rstrip()
            code = gethex('code')
            umask = gethex('umask')
            anyf = 0
            if name in fixed_counters:
                code, umask, anyf = fixed_counters[name]
            if m['other'] in row:
                other = gethex('other') << 16
            else:
                other = 0
            other |= gethex('edge') << 18
            if m['any'] in row:
                other |= (gethex('any') | anyf) << 21
            other |= getdec('cmask') << 24
            other |= gethex('invert') << 23
            val = code | (umask << 8) | other
            val &= EVMASK
            d = get('desc')
            if d is None:
                d = ''
            d = d.strip()
            e = Event(name, val, d)
            counter = get('counter')
            e.newextra = ""
            if other & ((1<<16)|(1<<17)):
                if other & (1<<16):
                    e.extra += "u"
                if other & (1<<17):
                    e.extra += "k"
            if (m['msr_index'] in row and get('msr_index') and get('msr_value')):
                msrnum = gethex('msr_index')
                msrval = gethex('msr_value')
                if version.offcore and msrnum in (0x1a6, 0x1a7):
                    e.newextra = ",offcore_rsp=0x%x" % (msrval, )
                elif version.ldlat and msrnum in (0x3f6,):
                    e.newextra = ",ldlat=0x%x" % (msrval, )
                elif msrnum == 0x3f7:
                    e.newextra = ",frontend=%#x" % (msrval, )
                # add new msr here
                else:
                    e.msrval = msrval
                    e.msr = msrnum
            if m['overflow'] in row:
                e.overflow = get('overflow')
            e.pebs = get('pebs')
            if e.pebs and int(e.pebs):
                if name.endswith("_ps") or int(e.pebs) == 2:
                    e.extra += pebs_enable
                    d += " (Uses PEBS)"
                else:
                    d = d.replace("(Precise Event)","") + " (Supports PEBS)"
            try:
                if get('errata') != "null":
                    try:
                        d += " Errata: "
                        d += get('errata')
                        e.errata = get('errata')
                    except UnicodeDecodeError:
                        pass
            except KeyError:
                pass
            e.desc = d
            e.counter = get('counter')
            for (flag, name) in extra_flags:
                if val & flag:
                    e.newextra += ",%s=%d" % (name, (val & flag) >> ffs(flag), )
            e.period = int(get('sav')) if m['sav'] in row else 0
            self.add_event(e)

    def getevent(self, e, nocheck=False):
        """Retrieve an event with name e. Return Event object or None.
           When nocheck is set don't check against current system."""
        e = e.lower()
        extra = ""
        edelim = ""
        m = re.match(r'([^:]+):request=([^:]+):response=([^:]+)', e)
        if m:
            ename = m.group(1) + "." + m.group(2) + "." + m.group(3)
            return update_ename(self.getevent(ename), e)
        m = re.match(r'(.*?):(.*)', e)
        if m:
            extra = m.group(2)
            edelim = ":"
            e = m.group(1)
        if e in self.events:
            # hack for now. Avoid ambiguity with :p
            # Should handle qualmap properly here
            extra = extra.replace("period=", "sample-after=")
            extra = extra_set(extra)
            ev = self.events[e]
            ev_extra = extra_set(ev.extra)
            if extra and merge_extra(ev_extra, extra) > ev_extra:
                ev = copy.deepcopy(self.events[e])
                ev.extra = "".join(merge_extra(ev_extra, extra))
                return ev
            return self.events[e]
        elif e.endswith("_ps"):
            return update_ename(self.getevent(e[:-3] + ":p" + extra), e)
        elif e.endswith("_0") or e.endswith("_1"):
            return update_ename(self.getevent(e.replace("_0","").replace("_1","") + edelim + extra), e)
        elif e.startswith("offcore") and (e + "_0") in self.events:
            return update_ename(self.getevent(e + "_0" + edelim + extra), e)
        elif e in self.uncore_events:
            ev = self.uncore_events[e]
            if ev and not nocheck:
                ev = check_uncore_event(ev)
            if ev and extra:
                ev = copy.deepcopy(ev)
                ev.newextra = extra
            return ev
        elif e in self.perf_events:
            return self.perf_events[e]
        return None

    def update_event(self, e, ev):
        if e not in self.pevents:
            self.pevents[e] = ev

    def getraw(self, r):
        e = "r%x" % (r)
        if e in self.pevents:
            ev = self.pevents[e]
            s = ev.name
            if ev.extra:
                s += ":" + ev.extra
            return s
        return "!Raw 0x%x" % (r,)

    def getperf(self, p):
        if p in self.pevents:
            return self.pevents[p].name
        return p

    def dumpevents(self, f=sys.stdout, human=True):
        """Print all events with descriptions to the file descriptor f.
           When human is true word wrap all the descriptions."""
        wrap = None
        if human:
            wrap = textwrap.TextWrapper(initial_indent="     ",
                                        subsequent_indent="     ")
        for k in sorted(self.events.keys()):
            print_event(k, self.desc[k], f, human, wrap)
        for k in sorted(self.uncore_events.keys()):
            print_event(k, self.uncore_events[k].desc, f, human, wrap)

    def read_events(self, name):
        """Read JSON normal events table."""
        mapping = {
            'name': u'EventName',
            'code': u'EventCode',
            'umask': u'UMask',
            'msr_index': u'MSRIndex',
            'msr_value': u'MSRValue',
            'cmask': u'CounterMask',
            'invert': u'Invert',
            'any': u'AnyThread',
            'edge': u'EdgeDetect',
            'desc': u'PublicDescription',
            'pebs': u'PEBS',
            'counter': u'Counter',
            'overflow': u'SampleAfterValue',
            'errata': u'Errata',
            'sav': u'SampleAfterValue',
            'other': u'Other',
        }
        if name.find("JKT") >= 0 or name.find("Jaketown") >= 0:
            self.latego = True
        try:
            if ocverbose:
                print("open", name)
            data = json.load(open(name, 'rb'))
        except ValueError as e:
            print("Cannot open", name + ":", e.message, file=sys.stderr)
            self.error = True
            return
        if u'PublicDescription' not in data[0]:
            mapping['desc'] = u'BriefDescription'
        self.read_table(data, mapping)
        if "topdown.slots" in self.events:
            self.add_topdown()

    def add_offcore(self, name):
        """Read offcore table."""
        if ocverbose:
            print("open", name)
        data = json.load(open(name, 'rb'))
        #   {
        #    "MATRIX_REQUEST": "DEMAND_DATA_RD",
        #    "MATRIX_RESPONSE": "NULL",
        #    "MATRIX_VALUE": "0x0000000001",
        #    "MATRIX_REGISTER": "0,1",
        #    "DESCRIPTION": "Counts demand data reads that"
        #   },

        offcore_response = self.getevent("OFFCORE_RESPONSE")
        if not offcore_response:
            return
        requests = []
        responses = []

        for row in data:
            if row[u"MATRIX_REQUEST"].upper() != "NULL":
                requests.append((row[u"MATRIX_REQUEST"], row[u"MATRIX_VALUE"], row[u"DESCRIPTION"]))
            if row[u"MATRIX_RESPONSE"].upper() != "NULL":
                responses.append((row[u"MATRIX_RESPONSE"], row[u"MATRIX_VALUE"], row[u"DESCRIPTION"]))

        def create_event(req_name, req_val, req_desc, res_name, res_val, res_desc):
            oe = copy.deepcopy(offcore_response)
            oe.name = ("OFFCORE_RESPONSE.%s.%s" % (req_name, res_name)).lower()
            if oe.name.lower() in self.events:
                return
            oe.msrval = int(req_val, 16) | (int(res_val, 16) << 16)
            oe.desc = req_desc + " " + res_desc
            if version.offcore:
                oe.newextra = ",offcore_rsp=0x%x" % (oe.msrval, )
            else:
                oe.msr = 0x1a6
            self.add_event(oe)

        for a, b in itertools.product(requests, responses):
            create_event(*(a + b))

    def add_uncore(self, name, force=False):
        if ocverbose:
            print("open", name)
        data = json.load(open(name, "rb"))
        for row in data:
            name = row['EventName'].lower()
            try:
                self.uncore_events[name] = UncoreEvent(name, row)
            except UnicodeEncodeError:
                pass

    def add_topdown(self):
        def td_event(name, umask, desc, counter):
            e = Event(name, umask, desc)
            e.counter = counter
            self.add_event(e)
        td_event("perf_metrics.retiring", 0x1000, "Number of slots the pipeline was frontend bound.", "32")
        td_event("perf_metrics.bad_speculation", 0x1100, "Number of slots the pipeline was doing bad speculation.", "33")
        td_event("perf_metrics.frontend_bound", 0x1200, "Number of slots the pipeline was frontend bound.", "34")
        td_event("perf_metrics.backend_bound", 0x1300, "Number of slots the pipeline was backend bound.", "35")

def handle_io_error(f, name, warn=False):
    try:
        f(name)
    except IOError:
        if warn:
            print("Cannot open", name, file=sys.stderr)

def json_with_extra(el):
    name = event_download.eventlist_name(el, "core")
    emap = EmapNativeJSON(name)
    if not emap or emap.error:
        print("parsing", name, "failed", file=sys.stderr)
        return None
    if experimental:
        try:
            emap.read_events(event_download.eventlist_name(el, "core experimental"))
        except IOError:
            pass
    add_extra_env(emap, el)
    return emap

def add_extra_env(emap, el):
    try:
        oc = os.getenv("OFFCORE")
        if oc:
            oc = canon_emapvar(oc, "matrix")
            oc = event_download.eventlist_name(el, "offcore")
            emap.add_offcore(oc)
        else:
            oc = event_download.eventlist_name(el, "offcore")
            if os.path.exists(oc):
                emap.add_offcore(oc)
            if experimental:
                oc = event_download.eventlist_name(el, "offcore experimental")
                if os.path.exists(oc):
                    emap.add_offcore(oc)
    except IOError:
        print("Cannot open", oc, file=sys.stderr)
    try:
        uc = os.getenv("UNCORE")
        if uc:
            uc = canon_emapvar(uc, "uncore")
            uc = event_download.eventlist_name(uc, "uncore")
            emap.add_uncore(uc)
        else:
            uc = event_download.eventlist_name(el, "uncore")
            if os.path.exists(uc):
                emap.add_uncore(uc)
            if experimental:
                uc = event_download.eventlist_name(el, "uncore experimental")
                if os.path.exists(uc):
                    emap.add_uncore(uc)
    except IOError:
        print("Cannot open", uc, file=sys.stderr)
    def read_map(env, typ, r):
        try:
            e2 = os.getenv(env)
            if e2:
                e2 = canon_emapvar(e2, typ)
                r(e2)
                # don't try to download for now
        except IOError:
            print("Cannot open", e2, file=sys.stderr)
    read_map("EVENTMAP2", "core", lambda r: emap.read_events(r))
    read_map("EVENTMAP3", "core", lambda r: emap.read_events(r))
    read_map("UNCORE2", "uncore", lambda r: emap.add_uncore(r))

def canon_emapvar(el, typ):
    if ("*" in el or "." in el or "_" in el) and not "/" in el and not file_exists(el):
        el = "%s/%s" % (event_download.getdir(), el)
    if '*' in el:
        import glob
        l = glob.glob(el)
        if l:
            if len(l) > 1:
                l = [x for x in l if x.find(typ) >= 0]
            el = l[0]
    return el

def find_emap():
    """Search and read a perfmon event map.
       When the EVENTMAP environment variable is set read that, otherwise
       read the map for the current CPU. EVENTMAP can be a CPU specifier
       in the map file or a path name.
       Dito for the OFFCORE and UNCORE environment variables.

       Return an emap object that contains the events and can be queried
       or None if nothing is found or the current CPU is unknown."""
    el = os.getenv("EVENTMAP")
    if not el:
        el = event_download.get_cpustr()
    el = canon_emapvar(el, "core")
    if "/" in el:
        try:
            emap = EmapNativeJSON(el)
            if not emap or emap.error:
                return None
            add_extra_env(emap, el)
            return emap
        except IOError:
            return None
    try:
        if not force_download:
            emap = json_with_extra(el)
            if emap:
                add_extra_env(emap, el)
                return emap
    except IOError:
        pass
    try:
        toget = ["core"]
        if not os.getenv("OFFCORE"):
            toget.append("offcore")
        if not os.getenv("UNCORE"):
            toget.append("uncore")
        if experimental:
            toget += [x + " experimental" for x in toget]
        event_download.download(el, toget)
        emap = json_with_extra(el)
        if emap:
            add_extra_env(emap, el)
            return emap
    except IOError:
        pass
    return None

def process_events(event, print_only, period, noexplode):
    if emap is None:
        return event, False
    overflow = None
    # replace inner commas so we can split events
    event = re.sub(r"([a-z][a-z0-9]+/)([^/]+)/",
            lambda m: m.group(1) + m.group(2).replace(",", "#") + "/",
            event)
    el = event.split(",")
    nl = []
    group_index = 0
    for i in el:
        group_start = ""
        group_end = ""
        start = ""
        end = ""
        if i.startswith('{'):
            group_start = "{"
            i = i[1:]
            group_index = len(nl)
        m = re.match(r'(.*)(\}(:.*)?)', i)
        if m:
            group_end = m.group(2)
            i = m.group(1)
        i = i.strip()
        m = re.match(r'(cpu|uncore_.*?)/([^#]+)(#?.*?)/(.*)', i)
        if m:
            start = m.group(1) + "/"
            ev = emap.getevent(m.group(2))
            end = m.group(3) + "/"
            if ev:
                qual = "".join(merge_extra(extra_set(ev.extra), extra_set(m.group(4))))
                end += qual
                i = ev.output_newstyle(period=period, noexplode=noexplode)
            else:
                start = ""
                end = ""
        else:
            ev = emap.getevent(i)
            if ev:
                i = ev.output(period=period, noexplode=noexplode)
        if ev:
            if ev.msr:
                msr.checked_writemsr(ev.msr, ev.msrval, print_only)
            if emap.latego and (ev.val & 0xffff) in latego.latego_events:
                latego.setup_event(ev.val & 0xffff, 1)
            overflow = ev.overflow
        event = (group_start + start + i + end + group_end).replace("#", ",")
        nl.append(event)
        if ev:
            emap.update_event(event, ev)
        if "S" in group_end:
            for j in range(group_index + 1, len(nl)):
                nl[j] = re.sub(r',period=\d+', '', nl[j])

    return str.join(',', nl), overflow

def getarg(i, cmd):
    if sys.argv[i][2:] == '' or sys.argv[i][:2] == '--':
        cmd.append(sys.argv[i])
        i += 1
        arg = ""
        if len(sys.argv) > i:
            arg = sys.argv[i]
        prefix = ""
    else:
        arg = sys.argv[i][2:]
        prefix = sys.argv[i][:2]
    return arg, i, prefix

def process_args():
    perf = os.getenv("PERF")
    if not perf:
        perf = "perf"
    cmd = [perf]

    noexplode = False
    overflow = None
    print_only = False
    never, no, yes = range(3)
    record = no
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--print":
            print_only = True
        elif sys.argv[i] == "--force-download":
           pass
        elif sys.argv[i] == "--experimental":
            pass
        elif sys.argv[i] == "--no-period":
            record = never
        elif sys.argv[i] == "--noexplode":
            noexplode = True
        elif sys.argv[i] == "record" and record == no:
            cmd.append(sys.argv[i])
            record = yes
        elif sys.argv[i][0:2] == '-e' or sys.argv[i] == '--event':
            event, i, prefix = getarg(i, cmd)
            event, overflow = process_events(event, print_only,
                                             True if record == yes else False,
                                             noexplode)
            cmd.append(prefix + event)
        elif record and (sys.argv[i][0:2] == '-c' or sys.argv[i] == '--count'):
            oarg, i, prefix = getarg(i, cmd)
            if oarg == "default":
                if overflow is None:
                    print("""
Specify the -e events before -c default or event has no overflow field.""", file=sys.stderr)
                    sys.exit(1)
                cmd.append(prefix + overflow)
            else:
                cmd.append(prefix + oarg)
        else:
            cmd.append(sys.argv[i])
        i += 1
    print(" ".join(map(pipes.quote, cmd)))
    if print_only:
        sys.exit(0)
    return cmd

def get_pager():
    f = sys.stdout
    if f.isatty():
        try:
            sp = subprocess.Popen(["less", "-F"], stdin=subprocess.PIPE)
            return sp.stdin, sp
        except OSError:
            f = sys.stdout
    return f, None

def perf_cmd(cmd):
    if emap is None:
        sys.exit(subprocess.call(cmd))
    elif len(sys.argv) >= 2 and sys.argv[1] == "list":
        pager, proc = get_pager()
        try:
            l = subprocess.Popen(cmd, stdout=pager)
            l.wait()
            print(file=pager)
            emap.dumpevents(pager, proc is not None)
            if proc:
                pager.close()
                proc.wait()
        except IOError:
            pass
    elif len(sys.argv) >= 2 and (sys.argv[1] == "report" or sys.argv[1] == "stat"):
        direct = version.has_name
        if not direct:
            for w in sys.argv:
                if w == "--tui":
                    direct = True
                    break
        if direct:
            ret = subprocess.call(cmd)
            latego.cleanup()
            sys.exit(ret)
        try:
            pipe = subprocess.Popen(cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT).stdout
            raw = lambda e: " " + emap.getraw(int(e.group(1), 16))
            for i in pipe:
                i = re.sub("[rR]aw 0x([0-9a-f]{4,})", raw, i)
                i = re.sub("r([0-9a-f]{4,})", raw, i)
                i = re.sub("(cpu/.*?/)", lambda e: emap.getperf(e.group(1)), i)
                print(i, end='')
        except IOError:
            pass
        pipe.close()
        latego.cleanup()
    else:
        sys.exit(subprocess.call(cmd))

if __name__ == '__main__':
    for j in sys.argv:
        if j == "--force-download":
            force_download = True
        if j == "--experimental":
            experimental = True
        if j == "--noexplode":
            noexplode = True
    emap = find_emap()
    if not emap:
        print("Do not recognize CPU or cannot find CPU map file.", file=sys.stderr)
    msr = MSR()
    cmd = process_args()
    try:
        perf_cmd(cmd)
    except KeyboardInterrupt:
        pass
