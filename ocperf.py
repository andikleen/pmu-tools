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
# Features:
# - map intel events to raw perf events
# - enable disable workarounds for specific events
# - handle offcore event on older kernels
# For the later must run as root and only as a single instance per machine 
# Normal events (mainly not OFFCORE) can be handled unprivileged 
# For events you can specify additional intel names from the list
# env variables:
# PERF=... perf binary to use (default "perf")
# EVENTMAP=... eventmap file (default: location of script based on CPU)
# the script looks for the spreadsheets in the same directory as the
# binary is
import sys
import glob
import os, os.path
import struct
import subprocess
import csv
import re
import shlex
import copy
import textwrap
from pmudef import *

import msr as msrmod
import latego

exedir = os.path.dirname(sys.argv[0])

# some mismapped to similar systems (HEDT->EP etc.)
cpu_mapping = {
    42: "snb-client.csv", # sandy bridge
    26: "nhm-ep.csv",  # bloomfield
    30: "nhm-ep.csv",  # lynnfield
    46: "nhm-ex.csv",  # beckton
    37: "wsm-sp.csv",  # clarkdale
    44: "wsm-dp.csv",  # gulftown
    45: "snb-ep.csv",  # sandybridge ep
    47: "wsm-dp.csv",  # westmere-EX
    58: "ivb-client.csv", # ivy bridge client
    60: "hsw.csv", 62: "hsw.csv", 70: "hsw.csv", 71: "hsw.csv",  # Haswell
    69: "hsw.csv", 
    28: "bnl.csv", 38: "bnl.csv", 39: "bnl.csv", 53: "bnl.csv", 54: "bnl.csv",
    62: "ivt.csv"      # ivybridge-ep
}

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

def resolve_symlink(p):
    l = p
    while os.path.islink(p):
        p = os.readlink(p)
        if os.path.isabs(p):
            return p
    return os.path.join(os.path.dirname(l), p)
        
def getconfig(name):
    return os.path.join(exedir, name)

class CPU:
    def cpumap(self):
        f = open("/proc/cpuinfo", "r")
        if not f:
            return False
        for i in f:
            n = i.split()
            if n[0] == "vendor_id" and n[2] != "GenuineIntel":
                return False
            if n[0] == "cpu" and n[1] == "family" and n[3] != "6":
                return False
            if n[0] == "model":
                model = int(n[2])
                self.model = model
                if model in cpu_mapping:
                    return cpu_mapping[model]
                print "Unknown CPU model %d" % (model,)
                return False
        f.close()
        print "Cannot identify CPU"
        return False

    def getmap(self):
        t = os.getenv('EVENTMAP')
        if t:
            # XXX
            if t.find("snb-ep") >= 0:
                self.model = 58
            else:
                self.model = 0
            return t
        t = self.cpumap()
        if t:
            return getconfig(t)
        return False

class Event:
    def __init__(self, name, val, desc):
        self.val = val
        self.name = name
        self.extra = ""
        self.msr = 0
        self.msrvalue = 0
        self.desc = desc

    def output_newstyle(self, newextra=""):
        val = self.val
        extra = self.newextra + newextra
        if extra:
            extra = "," + extra
        e = "event=0x%x,umask=0x%x%s" % (val & 0xff, (val >> 8) & 0xff, extra)
        if version.has_name:
            e += ",name=%s" % (self.name.replace(".", "_"),)
        return e

    def output(self, use_raw=False, flags=""):
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
    if flag == 0:
        print "bad flag"
        return -1
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

class Emap:
    "Read a event spreadsheet."
    events = {}
    codes = {}
    desc = {}
    pevents = {}
    latego = False

    def read_spreadsheet(self, name, dialect, m):
        index = None
        r = csv.reader(open(name, 'rb'), dialect=dialect)
        for row in r:
            if index == None:
                index = dict(zip(row, xrange(len(row))))
                continue

            get = lambda (x): row[index[m[x]]]
            gethex = lambda (x): int(get(x).split(",")[0], 16)

            name = get('name').lower().rstrip()
            code = gethex('code')
            umask = gethex('umask')
            if 'other' in m and m['other'] in index:
                other = gethex('other') << 16
            else:
                other = gethex('edge') << 18
                other |= gethex('any') << 21
                other |= gethex('cmask') << 24
                other |= gethex('invert') << 23
            val = code | (umask << 8) | other
            val &= EVMASK
            d = get('desc').strip()
            self.desc[name] = d
            e = Event(name, val, d)
            counter = get('counter')
            e.pname = "r%x" % (val,)
            if counter in fixed_counters:
                e.pname = fixed_counters[counter]
            e.newextra = ""
            if ('msr_index' in m and m['msr_index'] in index
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
            if 'overflow' in m:
                e.overflow = get('overflow')
            else:
                e.overflow = None
            self.events[name] = e
            self.codes[val] = e
            e.pebs = get('pebs')
            if e.pebs and int(e.pebs):
                if name.endswith("_ps"):
                    e.extra += "p"
                    self.desc[name] += " (Uses PEBS)"
                else:
                    self.desc[name] = self.desc[name].replace("(Precise Event)","") + " (Supports PEBS)"
            for (flag, name) in extra_flags:
                if val & flag:
                    e.newextra += ",%s=%d" % (name, (val & flag) >> ffs(flag), )

    def getevent_worker(self, e):
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

    def getevent(self, e):
        ev = self.getevent_worker(e)
        if ev == None:
            return None
        return ev

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

    def dumpevents(self, f, human):
        if human:
            wrap = textwrap.TextWrapper(initial_indent="     ",
                                        subsequent_indent="     ")            
        for k in sorted(self.desc.keys()):
            print >>f,"  %-42s" % (k,),
            if human:
                print >>f, "\n%s" % (wrap.fill(self.desc[k]),)
            else:
                print >>f, " [%s]" % (self.desc[k],)

#
# Handle the immense creativity of Event spreadsheet creators
# 

class EmapBNL(Emap):
    # Event_Name,Code,UMask,Counter,Description,Counter_Mask,Invert,AnyThread,Edge_Detect,PEBS
    def __init__(self, name, model):
        spreadsheet = {
            'name': 'Event_Name',
            'code': 'Code',
            'umask': 'UMask',
            'cmask': 'Counter_Mask',
            'invert': 'Invert',
            'any': 'AnyThread',
            'edge': 'Edge_Detect',
            'desc': 'Description',
            'pebs': 'PEBS',
            'counter': 'Counter'
        }
        return self.read_spreadsheet(name, 'excel', spreadsheet)

class EmapNHM(Emap):
    def __init__(self, name, model):
        nhm_spreadsheet = {
            'name': 'NAME',
            'code': 'Event ID',
            'umask': 'UMASK',
            'other': 'OTHER',
            'msr_index': 'MSR_INDEX',
            'msr_value': 'MSR_VALUE',
            'desc': 'DESCRIPTION',
            'pebs': 'PRECISE_EVENT',
            'counter': 'COUNTER',
            'overflow': 'OVERFLOW',
        }
        return self.read_spreadsheet(name, 'excel-tab', nhm_spreadsheet)

class EmapJSON(Emap):
    # EventCode,UMask,EventName,Description,Counter,OverFlow,MSRIndex,MSRValue,PreciseEvent,Invert,AnyThread,EdgeDetect,CounterMask
    def __init__(self, name, model):
        spreadsheet = {
            'name': 'EventName',
            'code': 'EventCode',
            'umask': 'UMask',
            'msr_index': 'MSRIndex',
            'msr_value': 'MSRValue',
            'cmask': 'CounterMask',
            'invert': 'Invert',
            'any': 'AnyThread',
            'edge': 'EdgeDetect',
            'desc': 'Description',
            'pebs': 'PreciseEvent',
            'counter': 'Counter',
            'overflow': 'OverFlow',
        }
        if model == 45:
            self.latego = True
        return self.read_spreadsheet(name, 'excel', spreadsheet)

readers = (
    ("snb-ep", EmapJSON),
    ("snb", EmapJSON),
    ("ivb", EmapJSON),
    ("hsw", EmapJSON),
    ("nhm", EmapNHM),
    ("wsm", EmapNHM),
    ("bnl", EmapBNL),
    ("ivt", EmapJSON)
)

def find_emap():
    cpu = CPU()
    t = cpu.getmap()
    if t:
        try:
            for i in readers:
                if os.path.basename(t).startswith(i[0]):
                    emap = i[1](t, cpu.model)
                    return emap
        except IOError:
            print "Cannot read %s" % (t,)
            sys.exit(1)
    print "Unknown CPU"
    sys.exit(1)

def addarg(s, add):
    s += " "
    if add.count(" ") > 0:
        return s + "\"" + add + "\""
    return s + add

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
        cmd = addarg(cmd, sys.argv[i])
        i += 1
        arg = ""
        if len(sys.argv) > i:
            arg = sys.argv[i]
        prefix = ""
    else:
        arg = sys.argv[i][2:]
        prefix = sys.argv[i][:2]
    return arg, i, cmd, prefix

def process_args():
    cmd = os.getenv("PERF")
    if not cmd:
        cmd = "perf"
    cmd += " "

    overflow = None
    print_only = False
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--print":
            print_only = True
            i += 1
        elif sys.argv[i][0:2] == '-e':
            event, i, cmd, prefix = getarg(i, cmd)
            event, overflow = process_events(event, print_only)
            cmd = addarg(cmd, prefix + event)
        elif sys.argv[i][0:2] == '-c':
            oarg, i, cmd, prefix = getarg(i, cmd)
            if oarg == "default":
                if overflow == None:
                    print >>sys.stderr,"""
Specify the -e events before -c default or event has no overflow field."""
                    sys.exit(1)
                cmd = addarg(cmd, prefix + overflow) 
            else:
                cmd = addarg(cmd, prefix + oarg)
        else:        
            cmd = addarg(cmd, sys.argv[i])
        i += 1
    print cmd
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
        l = subprocess.Popen(cmd, shell=True, stdout=pager)
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
            p = subprocess.Popen(shlex.split(cmd))
            ret = os.waitpid(p.pid, 0)[1]
            latego.cleanup()
            sys.exit(ret)
        pipe = subprocess.Popen(shlex.split(cmd), 
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
        p = subprocess.Popen(shlex.split(cmd))
        ret = os.waitpid(p.pid, 0)[1]
        sys.exit(ret)

if __name__ == '__main__':
    emap = find_emap()
    msr = MSR()
    cmd = process_args()
    perf_cmd(cmd)
