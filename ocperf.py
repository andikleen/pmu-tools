#!/usr/bin/env python3
# Copyright (c) 2011-2025, Intel Corporation
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
# OCVERBOSE=1 print which files are opened
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
if sys.version_info.major == 2:
    from pipes import quote
else:
    from shlex import quote
import itertools
import glob
from pmudef import EVENTSEL_ANY, EVENTSEL_INV, EVMASK, extra_flags, EVENTSEL_UMASK2
if sys.version_info.major == 3:
    import typing # noqa
    from typing import Set, List, Dict, Any, Tuple, DefaultDict # noqa

import msr as msrmod
import latego
import event_download

force_download = False
experimental = False
ocverbose = os.getenv("OCVERBOSE") is not None

exists_cache = dict() # type: Dict[str,bool]

emap_list = [] # type: List[EmapNativeJSON]

topology = None # type: None | Set[str]

def file_exists(s):
    if s in exists_cache:
        return exists_cache[s]
    global topology
    if topology is None:
        top = os.getenv("TOPOLOGY")
        topology = set()
        if top:
            try:
                topology = {x.strip()
                             .replace("/sys/devices", "/sys/bus/event_source/devices")
                            for x in open(top).readlines()}
            except OSError:
                print("Cannot open topology", top, file=sys.stderr)
    if s in topology:
        return True
    found = os.path.exists(s)
    exists_cache[s] = found
    return found

def has_format(s, pmu):
    return file_exists("/sys/bus/event_source/devices/%s/format/%s" % (pmu, s))

def has_format_any(f, pmu):
    return has_format(f, pmu) or has_format(f, pmu + "_0")

cached_vals = dict()

def cached_read(fn):
    if fn not in cached_vals:
        try:
            with open(fn) as f:
                cached_vals[fn] = f.read()
        except (OSError, IOError):
            cached_vals[fn] = "?"
    return cached_vals[fn]

warned = set()

def warn_once(s):
    if s not in warned:
        print(s, file=sys.stderr)
        warned.add(s)

class PerfVersion(object):
    def __init__(self):
        minor = 0
        perf = os.getenv("PERF")
        if not perf:
            perf = "perf"
        try:
            version = subprocess.Popen([perf, "--version"],
                    stdout=subprocess.PIPE).communicate()[0]
        except OSError:
            print("Cannot run", perf)
            version = ""
        if not isinstance(version, str):
            version = version.decode('utf-8')
        m = re.match(r"perf version (\d+)\.(\d+)\.", version)
        version = 412 # assume that no match is new enough
        if m:
            major = int(m.group(1))
            minor = int(m.group(2))
            version = major * 100 + minor

        pmu = "cpu_core" if os.path.exists("/sys/bus/event_source/devices/cpu_core") else "cpu"

        self.direct = os.getenv("DIRECT_MSR") or version < 400
        self.offcore = has_format("offcore_rsp", pmu) and not self.direct
        self.ldlat = has_format("ldlat", pmu) and not self.direct
        self.has_name = version >= 304
        self.has_uncore_expansion = version >= 412

version = PerfVersion()

class MSR(object):
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
    ("usr=yes", "", 0, "u"),
    ("usr=no", "", 0, "k"),
    ("os=yes", "", 0, "k"),
    ("os=no", "", 0, "u"),
    ("anythr=yes", "any=1", 0, ""),
    ("anythr=no", "any=0", 0, ""),
    ("pdir", "", 0, "ppp"),
    ("precise=yes", "", 0, "pp"),
    ("cp", "in_tx_cp=1", 0, ""))

number = "(0x[0-9a-fA-F]+|[0-9]+)"

qualval_map = (
    (r"event_select=" + number, "event=%#x", 0),
    (r"u" + number, "umask=%#x", 0),
    (r"c(?:mask=)?" + number, "cmask=%d", 24),
    (r"e(?:dge=)?" + number, "edge=%d", 18),
    (r"ocr_msr_val=" + number, "config1=%#x", 0),
    (r"(?:sa|sample-after|period)=" + number, "period=%d", 0))

uncore_map = (
    (r'e(\d)', 'edge='),
    (r't=(\d+)', "thresh="),
    (r'match=(0x[0-9a-fA-F]+)', "filter_occ="),
    (r'filter1=(0x[0-9a-fA-F]+)', "config1=", 32),
    (r"nc=(\d+)", "filter_nc="),
    (r'filter=(0x[0-9a-fA-F]+)', "config1="),
    (r'one_unit', '', ),
    (r"u" + number, "umask="),
    (r"opc=?" + number, "filter_opc="),
    (r"tid=?" + number, "filter_tid="),
    (r"state=?" + number, "filter_state="))

uncore_map_thresh = (
    (r"c(?:mask=)?" + number, "thresh="),)

uncore_map_cmask = (
    (r"c(?:mask=)?" + number, "cmask="),)

# newe gets modified
def convert_extra(extra, val, newe):
    nextra = ""
    while extra:
        if extra[0] == ":":
            extra = extra[1:]
            continue
        found = False
        for j in qualval_map:
            m = re.match(j[0], extra, re.I)
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
            if extra.lower().startswith(j[0]):
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

class Event(object):
    def __init__(self, name, val, desc):
        self.val = val
        self.name = name
        self.extra = ""
        self.userextra = ""
        self.msr = 0
        self.msrval = 0
        self.desc = desc
        self.precise = 0
        self.collectpebs = 0
        self.newextra = ""
        self.overflow = None
        self.errata = None
        self.counter = ""
        self.period = 0
        self.pname = None

    # XXX return with pmu to be consistent with Uncore and fix callers
    def output_newstyle(self, extra="", noname=False, period=False, name="", noexplode=False):
        """Format an perf event for output and return as perf event string.
           Always uses new style (cpu/.../)."""
        val = self.val
        if extra:
            extra = self.newextra + "," + extra
        else:
            extra = self.newextra
        if self.pname:
            e = self.pname
        else:
            e = "event=0x%x,umask=0x%x" % (val & 0xff,
                                           ((val >> 8) & 0xff) | (((val >> 40) & 0xff) << 8))
        e += extra
        if version.has_name:
            if name:
                e += ",name=" + name
            elif not noname:
                e += ",name=%s" % (gen_name(self.name, "sup" in (self.extra + extra)))
        if period and self.period and ",period=" not in e:
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
        extra = "".join(sorted(merge_extra(extra_set(self.extra), extra_set(flags))))
        extra, val = convert_extra(":" + extra, val, newe)
        if version.direct or use_raw:
            if self.pname:
                ename = self.pname
            else:
                ename = "r%x" % (val,)
            if extra:
                ename += ":" + extra
            # XXX should error for extras that don't fit into raw
        else:
            p = self.output_newstyle(extra=",".join(newe),
                    noname=noname, period=period, name=name)
            ename = "%s/%s/" % (self.pmu, p) + extra
        return ename

    def filter_qual(self):
        if cached_read("/sys/bus/event_source/devices/%s/format/umask") == "config:8-15":
            self.val &= ~EVENTSEL_UMASK2

        def check_qual(q):
            if q == "":
                return True
            if "=" in q:
                q, _ = q.split("=")
            if has_format_any(q, self.pmu):
                return True
            warn_once("%s: format %s not supported. Filtering out" % (self. pmu, q))
            return False
        self.newextra = ",".join(filter(check_qual, self.newextra.split(",")))

box_to_perf = {
    "cbo": "cbox",
    "qpi_ll": "qpi",
    "sbo": "sbox",
}

def box_exists(box):
    return file_exists("/sys/bus/event_source/devices/uncore_%s" % (box))

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
            m = re.match(match, flags, re.I)
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

class UncoreEvent(object):
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
            e.unit = "clock" if box_exists("clock") else "cbox"
            e.umask = 0
            e.code = 0xff
        # xxx subctr
        if e.unit in box_to_perf:
            e.unit = box_to_perf[e.unit]
        e.msr = None
        e.overflow = 0
        e.counter = "1"  # dummy for toplev
        e.newextra = ""
        if 'Errata' in row:
            e.errata = row['Errata']
        else:
            e.errata = None
        self.extra = ''
        self.userextra = ''

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
                name = gen_name(e.name, False)
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

perf_qual = "kuhGHSD"  # without pebs

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

def print_event(name, desc, f, human, wrap, pmu=""):
    desc = "".join([y for y in desc if y < chr(127)])
    print("  %-42s" % (name,), end='', file=f)
    if pmu:
        print(" [%s]" % pmu, end='', file=f)
    if human:
        print("\n%s" % (wrap.fill(desc),), file=f)
    else:
        print(" [%s]" % (desc,), file=f)

def uncore_exists(box, postfix=""):
    if file_exists("/sys/bus/event_source/devices/uncore_" + box + postfix):
        return True
    if file_exists("/sys/bus/event_source/devices/uncore_" + box + "_0" + postfix):
        return True
    return False

missing_boxes = set()

def check_uncore_event(e, extramsg):
    if uncore_exists(e.unit):
        if e.cmask and not uncore_exists(e.unit, "/format/cmask"):
            warn_once("Uncore unit " + e.unit + " missing cmask for " + e.name)
            extramsg.append("not supported due to missing cmask in PMU")
            return None
        if e.umask and not uncore_exists(e.unit, "/format/umask"):
            warn_once("Uncore unit " + e.unit + " missing umask for " + e.name)
            extramsg.append("not supported due to missing umask in PMU")
            return None
        return e
    if e.unit not in missing_boxes:
        warn_once("Uncore unit " + e.unit + " missing")
        missing_boxes.add(e.unit)
    extramsg.append("not supported due to missing PMU")
    return None

fixed_counters = {
    "inst_retired.any": (0xc0, 0, 0),
    "cpu_clk_unhalted.thread": (0x3c, 0, 0),
    "cpu_clk_unhalted.thread_any": (0x3c, 0, 1),
    "cpu_clk_unhalted.core": (0x3c, 0, 1),
}

def update_ename(ev, name):
    if ev:
        ev = copy.deepcopy(ev)
        ev.name = name
    return ev

def json_open(name):
    if ocverbose:
        print("open", name, file=sys.stderr)
    d = open(name, "rb").read()
    if not isinstance(d, str):
        d = d.decode('utf-8')

    json_data = json.loads(d)
    if isinstance(json_data, dict) and 'Events' in json_data:
        json_data = json_data['Events']

    return json_data

class EmapNativeJSON(object):
    """Read an event table."""

    def __init__(self, name, pmu):
        self.events = {}
        self.perf_events = {}
        self.codes = {}
        self.desc = {}
        self.pevents = {}
        self.latego = False
        self.uncore_events = {}
        self.error = False
        self.pmu = pmu
        self.name = name
        self.read_events(name)

    def add_event(self, e):
        self.events[e.name] = e
        self.perf_events[e.name.replace('.', '_')] = e  # workaround for perf-style naming
        if e.pname:
            self.pevents[e.pname] = e
        self.codes[e.val] = e
        self.desc[e.name] = e.desc
        e.pmu = self.pmu

    def read_table(self, r):
        for row in r:
            def get(x):
                if isinstance(row[x], bool):
                    return "1" if row[x] else "0"
                return row[x]
            def gethex(x):
                return int(get(x).split(",")[0], 16)
            def getdec(x):
                return int(get(x), 10)

            name = get(u'EventName').lower().rstrip()
            try:
                code = gethex(u'EventCode')
                umask = gethex(u'UMask')
                if 'UMaskExt' in row:
                    umask |= gethex(u'UMaskExt') << (40 - 8)
            except ValueError:
                if ocverbose:
                    print("cannot parse event", name)
                continue
            anyf = 0
            if name in fixed_counters:
                code, umask, anyf = fixed_counters[name]
            if u'Other' in row:
                other = gethex(u'Other') << 16
            else:
                other = 0
            other |= gethex(u'EdgeDetect') << 18
            if u'AnyThread' in row:
                other |= (gethex(u'AnyThread') | anyf) << 21
            if u'CounterMask' in row:
                other |= getdec(u'CounterMask') << 24
            elif u'CMask' in row:
                other |= getdec(u'CMask') << 24
            other |= gethex(u'Invert') << 23
            val = code | (umask << 8) | other
            val &= EVMASK
            d = get(u'PublicDescription')
            if d is None:
                d = ''
            d = d.strip()
            e = Event(name, val, d)
            e.newextra = ""
            if other & ((1 << 16)|(1 << 17)):
                if other & (1<<16):
                    e.extra += "u"
                if other & (1 << 17):
                    e.extra += "k"
            e.perfqual = None
            if u'MSRIndex' in row and get(u'MSRIndex') and get(u'MSRValue'):
                msrnum = gethex(u'MSRIndex')
                msrval = gethex(u'MSRValue')
                if version.offcore and msrnum in (0x1a6, 0x1a7):
                    e.newextra = ",offcore_rsp=0x%x" % (msrval, )
                    e.perfqual = "offcore_rsp"
                elif version.ldlat and msrnum in (0x3f6,):
                    e.newextra = ",ldlat=0x%x" % (msrval, )
                    e.perfqual = "ldlat"
                elif msrnum == 0x3f7:
                    e.newextra = ",frontend=%#x" % (msrval, )
                    e.perfqual = "frontend"
                # add new msr here
                else:
                    e.msrval = msrval
                    e.msr = msrnum
            if u'SampleAfterValue' in row:
                e.overflow = get(u'SampleAfterValue')
            e.counter = get(u'Counter')
            e.precise = getdec(u'Precise') if u'Precise' in row else 0
            e.collectpebs = getdec(u'CollectPEBS') if u'CollectPEBS' in row else 0
            e.pebs = getdec(u'PEBS') if u'PEBS' in row else 0
            if e.collectpebs > 1 or e.pebs >= 2:
                e.extra += "pp"
                if len(e.counter.split(",")) == 1:
                    e.extra += "p"
            try:
                if get(u'Errata') != "null":
                    try:
                        d += " Errata: "
                        d += get(u'Errata')
                        e.errata = get(u'Errata')
                    except UnicodeDecodeError:
                        pass
            except KeyError:
                pass
            e.desc = d
            for (flag, name) in extra_flags:
                if val & flag:
                    e.newextra += ",%s=%d" % (name, (val & flag) >> ffs(flag), )
            e.period = int(get(u'SampleAfterValue')) if u'SampleAfterValue' in row else 0
            self.add_event(e)

    def getevent(self, e, nocheck=False, extramsg=[]):
        """Retrieve an event with name e. Return Event object or None.
           When nocheck is set don't check against current system."""
        e = e.lower()
        extra = ""
        edelim = ""
        m = re.match(r'([^:]+):request=([^:]+):response=([^:]+)', e)
        if m:
            ename = m.group(1) + "." + m.group(2) + "." + m.group(3)
            return update_ename(self.getevent(ename, nocheck=nocheck, extramsg=extramsg), e)
        m = re.match(r'(.*?):(.*)', e)
        if m:
            extra = m.group(2)
            edelim = ":"
            e = m.group(1)
        if e in self.events:
            # hack for now. Avoid ambiguity with :p
            # Should handle qualmap properly here
            extra = extra.replace("period=", "sample-after=")
            userextra = extra
            extra = extra_set(extra)
            ev = self.events[e]
            ev_extra = extra_set(ev.extra)
            if extra and merge_extra(ev_extra, extra) > ev_extra:
                ev = copy.deepcopy(self.events[e])
                ev.userextra = userextra
                ev.extra = "".join(sorted(merge_extra(ev_extra, extra)))
                return ev
            return self.events[e]
        elif e.endswith("_ps"):
            return update_ename(self.getevent(e[:-3] + ":p" + extra), e)
        elif e.startswith("offcore") and (e + "_0") in self.events:
            return update_ename(self.getevent(e + "_0" + edelim + extra), e)
        elif e in self.uncore_events:
            ev = self.uncore_events[e]
            if ev and not nocheck:
                ev = check_uncore_event(ev, extramsg)
            if ev and extra:
                ev = copy.deepcopy(ev)
                ev.newextra = extra
            return ev
        elif e in self.perf_events:
            return self.perf_events[e]
        elif e in self.pevents:
            return self.pevents[e]

        extramsg.append("event not found for %s for %s" % (self.pmu, self.name))
        return None

    # XXX need to handle exploded events
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
            e = self.pevents[p]
            n = e.name
            if e.userextra:
                n += ":" + e.userextra
            return n
        return p

    def dumpevents(self, f=sys.stdout, human=True, uncore=True):
        """Print all events with descriptions to the file descriptor f.
           When human is true word wrap all the descriptions."""
        wrap = None
        if human:
            wrap = textwrap.TextWrapper(initial_indent="     ",
                                        subsequent_indent="     ")
        for k in sorted(self.events.keys()):
            print_event(k, self.desc[k], f, human, wrap, self.pmu)
        if uncore:
            for k in sorted(self.uncore_events.keys()):
                print_event(k, self.uncore_events[k].desc, f, human, wrap)

    def read_events(self, name):
        """Read JSON normal events table."""
        if name.find("JKT") >= 0 or name.find("Jaketown") >= 0:
            self.latego = True
        try:
            data = json_open(name)
        except ValueError as e:
            print("Cannot parse", name + ":", e.message, file=sys.stderr)
            self.error = True
            return
        self.read_table(data)
        if "topdown.slots" in self.events:
            self.add_topdown()

    def add_offcore(self, name):
        """Read offcore table."""
        data = json_open(name)
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
        data = json_open(name)
        for row in data:
            name = row['EventName'].lower()
            try:
                self.uncore_events[name] = UncoreEvent(name, row)
            except UnicodeEncodeError:
                pass

    def add_topdown(self):
        def td_event(name, pname, desc, counter):
            e = Event(name, 0, desc)
            e.counter = counter
            e.pname = pname
            self.add_event(e)
        td_event("perf_metrics.retiring", "topdown-retiring", "Number of slots the pipeline was frontend bound.", "32")
        td_event("perf_metrics.bad_speculation", "topdown-bad-spec", "Number of slots the pipeline was doing bad speculation.", "33")
        td_event("perf_metrics.frontend_bound", "topdown-fe-bound", "Number of slots the pipeline was frontend bound.", "34")
        td_event("perf_metrics.backend_bound", "topdown-be-bound", "Number of slots the pipeline was backend bound.", "35")
        td_event("topdown.slots", "slots", "Number of slots", "36")

        if "topdown.memory_bound_slots" in self.events:
            td_event("perf_metrics.heavy_operations", "topdown-heavy-ops", "Number of slots pipeline retired microcode instructions with >2 uops", "36")
            td_event("perf_metrics.branch_mispredicts", "topdown-br-mispredict", "Number of slots frontend was bound by branch mispredictions", "37")
            td_event("perf_metrics.memory_bound", "topdown-mem-bound", "Number of slots backend was bound by memory", "38")
            td_event("perf_metrics.fetch_latency", "topdown-fetch-lat", "Number of slots frontend was bound by memory fetch latency", "39")

pmu_to_type = {
    "cpu_core": ("hybridcore", "Core"),
    "cpu_atom": ("hybridcore", "Atom"),
    "cpu": ("core", None),
}

def json_with_extra(el, eventmap_is_file, pmu, typ_key):
    typ = pmu_to_type[pmu]
    if typ_key:
        typ = (typ[0], typ_key)
    name = event_download.eventlist_name(el, key=typ[0], hybridkey=typ[1])
    if not os.path.exists(name):
        name = event_download.eventlist_name(el, "hybridcore", hybridkey=typ[1])
    emap = EmapNativeJSON(name, pmu)
    if not emap or emap.error:
        print("parsing", name, "failed", file=sys.stderr)
        return None
    if experimental:
        try:
            emap.read_events(event_download.eventlist_name(el, "core experimental"))
        except IOError:
            pass
    add_extra_env(emap, el, eventmap_is_file)
    return emap

def add_extra_env(emap, el, eventmap_is_file):
    try:
        oc = os.getenv("OFFCORE")
        if oc:
            oc = canon_emapvar(oc, "matrix")
            oc = event_download.eventlist_name(el, "offcore")
            emap.add_offcore(oc)
        elif not eventmap_is_file:
            oc = event_download.eventlist_name(el, "offcore")
            if os.path.exists(oc) and el != oc:
                emap.add_offcore(oc)
            if experimental:
                oc = event_download.eventlist_name(el, "offcore experimental")
                if os.path.exists(oc) and oc != el:
                    emap.add_offcore(oc)
    except IOError:
        print("Cannot open offcore", oc, file=sys.stderr)
    try:
        uc = os.getenv("UNCORE")
        if uc:
            uc = canon_emapvar(uc, "uncore")
            uc = event_download.eventlist_name(uc, "uncore")
            emap.add_uncore(uc)
        elif not eventmap_is_file:
            uc = event_download.eventlist_name(el, "uncore")
            if os.path.exists(uc) and uc != el:
                emap.add_uncore(uc)
            if experimental:
                uc = event_download.eventlist_name(el, "uncore experimental")
                if os.path.exists(uc) and uc != el:
                    emap.add_uncore(uc)
    except IOError:
        print("Cannot open uncore", uc, file=sys.stderr)
    def read_map(env, typ, r):
        try:
            e2 = os.getenv(env)
            if e2:
                e2 = canon_emapvar(e2, typ)
                r(e2)
                # don't try to download for now
        except IOError:
            print("Cannot open " + env, e2, file=sys.stderr)
    read_map("EVENTMAP2", "core", emap.read_events)
    read_map("EVENTMAP3", "core", emap.read_events)
    read_map("UNCORE2", "uncore", emap.add_uncore)

def canon_emapvar(el, typ):
    if ("*" in el or "." in el or "_" in el) and "/" not in el and not file_exists(el):
        el = "%s/%s" % (event_download.getdir(), el)
    if '*' in el:
        l = glob.glob(el)
        if l:
            if len(l) > 1:
                l = [x for x in l if x.find(typ) >= 0]
            if l:
                el = l[0]
    return el

def find_emap(eventvar="EVENTMAP", pmu="cpu", typ=None):
    """Search and read a perfmon event map.
       When the EVENTMAP environment variable is set read that, otherwise
       read the map for the current CPU. EVENTMAP can be a CPU specifier
       in the map file or a path name.
       Dito for the OFFCORE and UNCORE environment variables.

       Optionally pass the name of the EVENTMAP variable, and the cpu pmu name,
       and the cpu hybrid type in the map file.

       Return an emap object that contains the events and can be queried
       or None if nothing is found or the current CPU is unknown."""
    el = os.getenv(eventvar)
    if not el:
        eventmap_is_file = False
        el = event_download.get_cpustr()
    else:
        eventmap_is_file = "/" in el
    el = canon_emapvar(el, "core")
    if "/" in el:
        try:
            emap = EmapNativeJSON(el, pmu)
            if not emap or emap.error:
                return None
            add_extra_env(emap, el, eventmap_is_file)
            return emap
        except IOError:
            return None
    try:
        if not force_download:
            return json_with_extra(el, eventmap_is_file, pmu, typ)
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
        return json_with_extra(el, eventmap_is_file, pmu, typ)
    except IOError:
        pass
    return None

def process_events(event, print_only, period, noexplode):
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
        m = re.match(r'([^/]+)/([^#]+)(#?.*?)/(.*)', i)
        if m:
            start = m.group(1) + "/"
            for emap in emap_list:
                if emap.pmu == m.group(1):
                    ev = emap.getevent(m.group(2))
                    break
            else:
                ev = emap_list[0].getevent(m.group(2))
            end = m.group(3) + "/"
            if ev:
                qual = "".join(sorted(merge_extra(extra_set(ev.extra), extra_set(m.group(4)))))
                end += qual
                i = ev.output_newstyle(period=period, noexplode=noexplode)
                if i.count("/") > 2: # was it exploded?
                    start = ""
                    end = ""
            else:
                start = ""
                end = ""
        else:
            ev = None
            res = [x.getevent(i) for x in emap_list]
            res = [x for x in res if x]
            if res:
                if len(res) > 1 and not i.lower().startswith("unc_"):
                    print("Event %s is not unique on hybrid CPUs. Add cpu_*// prefixes" % i, file=sys.stderr)
                ev = res[0]
                i = ev.output(period=period, noexplode=noexplode)
        if ev:
            if ev.msr:
                msr.checked_writemsr(ev.msr, ev.msrval, print_only)
            for emap in emap_list:
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
                                             record == yes,
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
    print(" ".join(map(quote, cmd)))
    if print_only:
        sys.exit(0)
    return cmd

if sys.version_info.major == 3:
    popentext = dict(text=True)
else:
    popentext = {}

def get_pager():
    f = sys.stdout
    if f.isatty():
        try:
            sp = subprocess.Popen(["less", "-F"], stdin=subprocess.PIPE, **popentext) # type: ignore
            return sp.stdin, sp
        except OSError:
            f = sys.stdout
    return f, None

def perf_cmd(cmd):
    if len(emap_list) == 0:
        sys.exit(subprocess.call(cmd))
    elif len(sys.argv) >= 2 and sys.argv[1] == "list":
        pager, proc = get_pager()
        try:
            l = subprocess.Popen(cmd, stdout=pager)
            l.wait()
            print(file=pager)
            uncore = True
            for emap in emap_list:
                if len(emap_list) > 1:
                    print("%s:\n" % emap.pmu, file=pager)
                emap.dumpevents(pager, proc is not None, uncore)
                uncore = False
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
                i = re.sub("(cpu(_core|_atom)?/.*?/)", lambda e: emap.getperf(e.group(1)), i)
                print(i, end='')
        except IOError:
            pass
        pipe.close()
        latego.cleanup()
    else:
        sys.exit(subprocess.call(cmd))

def find_pmus():
    g = glob.glob("/sys/bus/event_source/devices/cpu*")
    if len(g) == 0:
        g = ["/sys/bus/event_source/devices/cpu"]
    return [i.replace("/sys/bus/event_source/devices/", "") for i in g]


def main():
    global force_download, experimental, noexplode
    global msr
    for j in sys.argv:
        if j == "--force-download":
            force_download = True
        if j == "--experimental":
            experimental = True
        if j == "--noexplode":
            noexplode = True
    msr = MSR()
    pmus = find_pmus()
    for pmu in pmus:
        emap = find_emap(pmu=pmu)
        if not emap:
            print("Do not recognize CPU or cannot find CPU map file.", file=sys.stderr)
        else:
            emap_list.append(emap)
    cmd = process_args()
    try:
        perf_cmd(cmd)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()

