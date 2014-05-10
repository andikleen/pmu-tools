#!/usr/bin/env python
# Copyright (c) 2011-2013, Intel Corporation
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
# - handle offcore event on older kernels
# For the later must run as root and only as a single instance per machine 
# Normal events (mainly not OFFCORE) can be handled unprivileged 
# For events you can specify additional intel names from the list
#
# env variables:
# PERF=... perf binary to use (default "perf")
# EVENTMAP=eventmap
# When eventmap is not specified, look in ~/.events
# The eventmap is automatically downloaded there
#
import sys
import os
import struct
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

fixed_counters = {
    "32": "instructions",
    "33": "cycles",
    "34": "ref-cycles",
    "FIXED COUNTER 1": "instructions",
    "FIXED COUNTER 2": "cycles",
    "FIXED COUNTER 3": "ref-cycles"
}

def has_format(s):
    return os.path.isfile("/sys/devices/cpu/format/" + s)

class PerfVersion:
    def __init__(self):
        minor = 0
        version = subprocess.Popen(["perf","--version"], stdout=subprocess.PIPE).communicate()[0]
        m = re.match(r"perf version (\d+)\.(\d+)\.", version)
        if m:
            major = m.group(1)
            minor = m.group(2)
            if re.match("[0-9]+", minor):
                minor = int(minor, 16)
            if re.match("[0-9]+", major) and int(major) > 3:
                minor = 100 # infinity

        self.direct = os.getenv("DIRECT_MSR") or minor < 4
        self.offcore = has_format("offcore_rsp") and not self.direct
        self.ldlat = has_format("ldlat") and not self.direct
        self.has_name = minor >= 4

version = PerfVersion()

class MSR:
    reg = {}

    def writemsr(self, msrnum, val, print_only = False):
        print "msr %x = %x" % (msrnum, val, )
        if print_only:
            return
        msrmod.writemsr(msrnum, val)

    def checked_writemsr(self, msr, val, print_only = False):
        if msr in self.reg:
            sys.exit("Multiple events use same register")
        self.writemsr(msr, val, print_only)
        self.reg[msr] = 1

class Event:
    def __init__(self, name, val, desc):
        self.val = val
        self.name = name
        self.extra = ""
        self.msr = 0
        self.msrval = 0
        self.desc = desc

    def output_newstyle(self, newextra=""):
        """Format an perf event for output and return as perf event string.
           Always uses new style (cpu/.../)."""
        val = self.val
        extra = self.newextra
        if newextra:
            extra += "," + newextra
        e = "event=0x%x,umask=0x%x%s" % (val & 0xff, (val >> 8) & 0xff, extra)
        if version.has_name:
            e += ",name=%s" % (self.name.replace(".", "_"),)
        return e

    def output(self, use_raw=False, flags=""):
        """Format an event for output and return as perf event string.
           use_raw when true return old style perf string (rXXX).
           Otherwise chose between old and new style based on the 
           capabilities of the installed perf executable.
           flags when set add perf flags (e.g. u for user, p for pebs)."""
        val = self.val
        newe = ""
        extra = "".join(merge_extra(extra_set(self.extra), extra_set(flags)))
        m = re.search(r"c(mask=)?([0-9]+)", extra)
        if m:
            extra = re.sub(r"c(mask=)?[0-9]+", "", extra)
            val |= int(m.group(2)) << 24
            newe += "cmask=%x" % (int(m.group(2)))

        if version.direct or use_raw:
            ename = "r%x" % (val,) 
            if extra:
                ename += ":" + extra
        else:
            ename = "cpu/%s/" % (self.output_newstyle(newextra=newe)) + extra
        return ename

def ffs(flag):
    assert flag != 0
    m = 1
    j = 0
    while (flag & m) == 0:
        m = m << 1
        j += 1
    return j

def extra_set(e):
    return set(map(lambda x: x[0],
                   re.findall(r"((p+)|[ukHG]|(c(mask=)?\d+))", e)))

def merge_extra(a, b):
    m = a | b
    if 'ppp' in m:
        m = m - set(['p', 'pp'])
    if 'pp' in m:
        m = m - set(['p'])
    return m

class Emap(object):
    """Read an event table."""

    def __init__(self):
        self.events = {}
        self.codes = {}
        self.desc = {}
        self.pevents = {}
        self.latego = False

    def add_event(self, e):
        self.events[e.name] = e
        self.codes[e.val] = e
        self.desc[e.name] = e.desc

    def read_table(self, r, m):
        for row in r:
            get = lambda (x): row[m[x]]
            gethex = lambda (x): int(get(x).split(",")[0], 16)
            getdec = lambda (x): int(get(x), 10)

            name = get('name').lower().rstrip()
            code = gethex('code')
            umask = gethex('umask')
            if 'other' in m and m['other'] in row:
                other = gethex('other') << 16
            else:
                other = gethex('edge') << 18
                other |= gethex('any') << 21
                other |= getdec('cmask') << 24
                other |= gethex('invert') << 23
            val = code | (umask << 8) | other
            val &= EVMASK
            d = get('desc').strip()
            try:
                d = d.encode('utf-8')
            except UnicodeDecodeError:
                pass
            e = Event(name, val, d)
            counter = get('counter')
            e.pname = "r%x" % (val,)
            if counter in fixed_counters:
                e.pname = fixed_counters[counter]
            e.newextra = ""
            if ('msr_index' in m and m['msr_index'] in row
                    and get('msr_index') and get('msr_value')):
                msrnum = gethex('msr_index')
                msrval = gethex('msr_value')
                if version.offcore and msrnum in (0x1a6, 0x1a7):
                    e.newextra = ",offcore_rsp=0x%x" % (msrval, )
                elif version.ldlat and msrnum in (0x3f6,):
                    e.newextra = ",ldlat=0x%x" % (msrval, )
                # add new msr here
                else:
                    e.msrval = msrval
                    e.msr = msrnum
            if 'overflow' in m and m['overflow'] in row:
                e.overflow = get('overflow')
                #if e.overflow == "0":
                #    print >>sys.stderr, "Warning: %s has no overflow value" % (name,)
            else:
                e.overflow = None
            e.pebs = get('pebs')
            if e.pebs and int(e.pebs):
                if name.endswith("_ps"):
                    e.extra += "p"
                    d += " (Uses PEBS)"
                else:
                    d = d.replace("(Precise Event)","") + " (Supports PEBS)"
            if get('errata') != "null":
                d += " Errata: " + get('errata')
            e.desc = d
            for (flag, name) in extra_flags:
                if val & flag:
                    e.newextra += ",%s=%d" % (name, (val & flag) >> ffs(flag), )
            self.add_event(e)

    def getevent(self, e):
        """Retrieve an event with name e. Return Event object or None."""
        e = e.lower()
        extra = ""
        edelim = ""
        m = re.match(r'(.*):(.*)', e)
        if m:
            extra = m.group(2)
            edelim = ":"
            e = m.group(1)
        if e in self.events:
            extra = extra_set(extra)
            ev = self.events[e]
            ev_extra = extra_set(ev.extra)
            if extra and merge_extra(ev_extra, extra) > ev_extra:
                ev = copy.deepcopy(self.events[e])
                ev.extra = "".join(merge_extra(ev_extra, extra))
                return ev
            return self.events[e]
        elif e.endswith("_ps"):
            return self.getevent(e[:-3] + ":p" + extra)
        elif e.endswith("_0") or e.endswith("_1"):
            return self.getevent(e.replace("_0","").replace("_1","") + edelim + extra)
        elif e.startswith("offcore") and (e + "_0") in self.events:
            return self.getevent(e + "_0" + edelim + extra)
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
        if human:
            wrap = textwrap.TextWrapper(initial_indent="     ",
                                        subsequent_indent="     ")            
        for k in sorted(self.desc.keys()):
            print >>f,"  %-42s" % (k,),
            if human:
                print >>f, "\n%s" % (wrap.fill(self.desc[k]),)
            else:
                print >>f, " [%s]" % (self.desc[k],)

# XXX handle TakenAlone, DataLA
class EmapNativeJSON(Emap):
    def __init__(self, name):
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
        }
        super(EmapNativeJSON, self).__init__()
        if name.find("JKT") >= 0:
            self.latego = True
        data = json.load(open(name, 'rb'))
        if u'PublicDescription' not in data[0]:
            mapping['desc'] = u'BriefDescription'
        return self.read_table(data, mapping)

    def add_offcore(self, name):
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
            if row[u"MATRIX_REQUEST"] != "NULL":
                requests.append((row[u"MATRIX_REQUEST"], row[u"MATRIX_VALUE"], row[u"DESCRIPTION"]))
            if row[u"MATRIX_RESPONSE"] != "NULL":
                responses.append((row[u"MATRIX_RESPONSE"], row[u"MATRIX_VALUE"], row[u"DESCRIPTION"]))

        def create_event(req_name, req_val, req_desc, res_name, res_val, res_desc):
            oe = copy.deepcopy(offcore_response)
            oe.name = ("OFFCORE_RESPONSE.%s.%s" % (req_name, res_name)).lower()
            oe.msrval = int(req_val, 16) | int(res_val, 16)
            oe.desc = req_desc + " " + res_desc
            if version.offcore:
                oe.newextra = ",offcore_rsp=0x%x" % (oe.msrval, )
            self.add_event(oe)

        for a, b in itertools.product(requests, responses):
            create_event(*(a + b))

def json_with_offcore(el, need_oc):
    emap = EmapNativeJSON(event_download.eventlist_name(el, "core"))
    if not emap:
        return None
    oc = event_download.eventlist_name(el, "offcore")
    if os.path.exists(oc):
        emap.add_offcore(oc)
    elif need_oc:
        return None
    return emap

def find_emap():
    """Search and read a perfmon event map.
       When the EVENTMAP environment variable is set read that, otherwise
       read the map for the current CPU. EVENTMAP can be a CPU specifier 
       in the map file or a path name.
       Dito for the OFFCORE environment variable.

       Return an emap object that contains the events and can be queried
       or None if nothing is found or the current CPU is unknown."""
    el = os.getenv("EVENTMAP")
    if el and el.find("/") >= 0:
        try:
            emap = EmapNativeJSON(el)
            oc = os.getenv("OFFCORE")
            if oc:
                emap.add_offcore(oc)
            return emap
        except IOError:
            return None
    if not el:
        el = event_download.get_cpustr()
    try:
        # FIXME: always downloads when no offcore file
        emap = json_with_offcore(el, True)
        if emap:
            return emap
    except IOError:
        pass
    try:
        event_download.download(el, ["core", "offcore"])
        return json_with_offcore(el, False)
    except IOError:
        pass
    return None

def process_events(event, print_only):
    overflow = None
    # replace inner commas so we can split events
    event = re.sub(r"([a-z][a-z0-9]+/)([^/]+)/",
            lambda m: m.group(1) + m.group(2).replace(",", "#") + "/",
            event)
    el = event.split(",")
    nl = []
    for i in el:
        start = ""
        end = ""
        if i.startswith('{'):
            start = "{"
            i = i[1:]
        if i.endswith('}'):
            end = "}"
            i = i[:-1]
        m = re.match(r"(cpu/)([^/#]+)([^/]+/)([^,]*)", i)
        if m:
            start += m.group(1)
            ev = emap.getevent(m.group(2))
            end += m.group(3)
            if ev:
                end += "".join(merge_extra(extra_set(ev.extra), extra_set(m.group(4))))
            i = ev.output_newstyle()
        else:
            extra = ""
            m = re.match("([^:]*):(.*)", i)
            if m:
                extra = m.group(2)
                i = m.group(1)
            ev = emap.getevent(i)
            if ev:
                i = ev.output(flags=extra)
        if ev:
            if ev.msr:
                msr.checked_writemsr(ev.msr, ev.msrval, print_only)
	    if emap.latego and (ev.val & 0xffff) in latego.latego_events:
                latego.setup_event(ev.val & 0xffff, 1)
            overflow = ev.overflow
        event = (start + i + end).replace("#", ",")
        nl.append(event)
        if ev:
            emap.update_event(event, ev)

    return str.join(',', nl), overflow

def getarg(i, cmd):
    if sys.argv[i][2:] == '':
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

    overflow = None
    print_only = False
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--print":
            print_only = True
        elif sys.argv[i][0:2] == '-e':
            event, i, prefix = getarg(i, cmd)
            event, overflow = process_events(event, print_only)
            cmd.append(prefix + event)
        elif sys.argv[i][0:2] == '-c':
            oarg, i, prefix = getarg(i, cmd)
            if oarg == "default":
                if overflow == None:
                    print >>sys.stderr,"""
Specify the -e events before -c default or event has no overflow field."""
                    sys.exit(1)
                cmd.append(prefix + overflow)
            else:
                cmd.append(prefix + oarg)
        else:        
            cmd.append(sys.argv[i])
        i += 1
    print " ".join(map(pipes.quote, cmd))
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
    if len(sys.argv) >= 2 and sys.argv[1] == "list":
        pager, proc = get_pager()
        l = subprocess.Popen(cmd, stdout=pager)
        l.wait()
        print >>pager
        emap.dumpevents(pager, proc != None)
        if proc:
            pager.close()
            proc.wait()
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
        pipe = subprocess.Popen(cmd, 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.STDOUT).stdout
        raw = lambda e: " " + emap.getraw(int(e.group(1), 16))
        for i in pipe:
            i = re.sub("[rR]aw 0x([0-9a-f]{4,})", raw, i)
            i = re.sub("r([0-9a-f]{4,})", raw, i)
            i = re.sub("(cpu/.*?/)", lambda e: emap.getperf(e.group(1)), i)
            print i,
        pipe.close()
        latego.cleanup()
    else:
        sys.exit(subprocess.call(cmd))

if __name__ == '__main__':
    emap = find_emap()
    if not emap:
        sys.exit("Do not recognize CPU or cannot find CPU map file")
    msr = MSR()
    cmd = process_args()
    perf_cmd(cmd)
