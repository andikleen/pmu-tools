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
# For the later must run as root and only as a single instance per machine 
# Normal events (mainly not OFFCORE) can be handled unprivileged 
# For events you can specify additional intel names from the list
# In browser mode the raw events cannot be decoded back.
# The :cXXX notation cannot be decoded back
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

import msr as msrmod
import latego

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
    60: "hsw.csv", 70: "hsw.csv", 71: "hsw.csv",  # Haswell
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

        self.offcore = (minor >= 4 and
                        os.path.isfile("/sys/devices/cpu/format/offcore_rsp") and
                        not os.getenv("DIRECT_MSR"))

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
    if hasattr(sys, 'frozen'):
        p = sys.executable
    else:
        p = __file__
    p = resolve_symlink(p)
    dir = os.path.dirname(p)
    return os.path.join(dir, name)

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

    def output(self, use_raw=False):
        val = self.val
        extra = self.extra
        m = re.search(r"(c[0-9]+)", extra)
        if m:
            extra = re.sub(r"c[0-9]+", "", extra)
            val |= int(m.group(1)[1:]) << 24

        if version.offcore:
            self.ename = "cpu/event=0x%x,umask=0x%x%s/" % (val & 0xff, (val >> 8) & 0xff,
                                                           self.newextra, )
        else:
            self.ename = "r%x" % (val,)
            if extra:
                self.ename += ":" + extra

        if self.ename and not use_raw:
            e = self.ename + extra
        else:
            e = self.ename
            if ev.extra != "":
                e += ":" + extra
        return e

EVENTSEL_EVENT = 0x00ff
EVENTSEL_UMASK = 0xff00
EVENTSEL_EDGE  = 1<<18
EVENTSEL_PC    = 1<<19
EVENTSEL_ANY   = 1<<21
EVENTSEL_INV   = 1<<23
EVENTSEL_CMASK = 0xff000000

EVMASK = (EVENTSEL_EVENT|EVENTSEL_UMASK|EVENTSEL_EDGE|EVENTSEL_PC|EVENTSEL_ANY|
          EVENTSEL_INV|EVENTSEL_CMASK)

extra_flags = (
        (EVENTSEL_EDGE, "edge"),
        (EVENTSEL_PC,   "pc"),
        (EVENTSEL_ANY,  "any"),
        (EVENTSEL_INV,  "inv"),
        (EVENTSEL_CMASK, "cmask"))

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

class Emap:
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
            other = 0
            if 'other' in m and m['other'] in index and get('other'):
                other = gethex('other') << 16
            if 'edge' in m and m['edge'] in index:
                other |= gethex('edge') << 18
            if 'any' in m and m['any'] in index:
                other |= gethex('any') << 21
            if 'cmask' in m and m['cmask'] in index:
                other |= gethex('cmask') << 24
            if 'invert' in m and m['invert'] in index:
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
                else:
                    e.msrval = msrval
                    e.msr = msrnum
            self.events[name] = e
            self.codes[val] = e
            e.pebs = get('pebs')
            if e.pebs and int(e.pebs):
                if name.endswith("_PS"):
                    e.extra += "p"
                else:
                    self.desc[name] += " (Supports PEBS)"
            for (flag, name) in extra_flags:
                if val & flag:
                    e.newextra += ",%s=%d" % (name, (val & flag) >> ffs(flag), )

    def getevent_worker(self, e):
        e = e.lower()
        extra = ""
        m = re.match(r'(.*):(.*)', e)
        if m:
            extra = m.group(2)
            e = m.group(1)
        if e in self.events:
            if extra:
                ev = copy.deepcopy(self.events[e])
                ev.extra += extra
                ev.output()
                return ev
            return self.events[e]
        elif e.endswith("_ps"):
            return self.getevent(e[:-3] + ":p" + extra)
        elif e.endswith("_0") or e.endswith("_1"):
            return self.getevent(e.replace("_0","").replace("_1","") + ":" + extra)
        return None

    def getevent(self, e):
        ev = self.getevent_worker(e)
        e = ev.output()
        if e not in self.pevents:
            self.pevents[e] = ev
        return ev

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

    def dumpevents(self):
        for k in sorted(self.desc.keys()):
            print "  %-42s [%s]" % (k, self.desc[k],)

#
# Handle the immense creativity of Event spreadsheet creators
# 

class EmapSNB(Emap):
    def __init__(self, name, model):
        snb_spreadsheet = {
            'name': 'NAME',
            'code': 'CODE',
            'umask': 'UMASK',
            'other': 'OTHER',
            'msr_index': 'MSR_INDEX',
            'msr_value': 'MSR_VALUE',
            'desc': 'Description',
            'pebs': 'PRECISE_EVENT',
            'counter': 'COUNTER'
        }
        return self.read_spreadsheet(name, 'excel', snb_spreadsheet)

class EmapBNL(Emap):
    # Event_Name,Code,UMask,Counter,Description,Counter_Mask,Invert,AnyThread,Edge_Detect,PEBS
    def __init__(self, name, model):
        ivb_spreadsheet = {
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
        return self.read_spreadsheet(name, 'excel', ivb_spreadsheet)

class EmapNEW(Emap):
    # new format 
    # Event_Name,Code,UMask,Counter,Counter_HT_Off,Description,MSR_Index,MSR_Value,Taken_Alone,Counter_Mask,Invert,AnyThread,Edge_Detect,PEBS
    def __init__(self, name, model):
        ivb_spreadsheet = {
            'name': 'Event_Name',
            'code': 'Code',
            'umask': 'UMask',
            'msr_index': 'MSR_Index',
            'msr_value': 'MSR_Value',
            'cmask': 'Counter_Mask',
            'invert': 'Invert',
            'any': 'AnyThread',
            'edge': 'Edge_Detect',
            'desc': 'Description',
            'pebs': 'PEBS',
            'counter': 'Counter'
        }
        if model == 58:
            self.latego = True
        return self.read_spreadsheet(name, 'excel', ivb_spreadsheet)

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
            'counter': 'COUNTER'
        }
        return self.read_spreadsheet(name, 'excel-tab', nhm_spreadsheet)

class EmapHSW(Emap):
    def __init__(self, name, model):
        hsw_spreadsheet = {
            'name': 'EventName',
            'code': 'EventCode',
            'umask': 'UMask',
            'other': 'Other',
            'msr_index': 'MSRIndex',
            'msr_value': 'MSRValue',
            'desc': 'Description',
            'pebs': 'PreciseEvent',
            'counter': 'Counter'
        }
        return self.read_spreadsheet(name, 'excel', hsw_spreadsheet)

readers = (
    ("snb-ep", EmapNEW),
    ("snb", EmapSNB),
    ("ivb", EmapNEW),
    ("hsw", EmapNEW),
    ("nhm", EmapNHM),
    ("wsm", EmapNHM),
    ("bnl", EmapBNL),
    ("ivt", EmapNEW)
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
    # ignore anything with new style args (cpu/a,b/) so far
    # because we get confused by the inner commas
    # need a proper parser
    if event.find("/") >= 0:
        return event
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
        e = emap.getevent(i)
        if e:
            i = e.output()
            if e.msr:
                msr.checked_writemsr(e.msr, e.msrval, print_only)
            if emap.latego:
                print "setting up latego %x" % (e.val & 0xffff)
                latego.setup_event(e.val & 0xffff, 1)
        nl.append(start + i + end)
    return str.join(',', nl)

def process_args():
    cmd = os.getenv("PERF")
    if not cmd:
        cmd = "perf"
    cmd += " "

    print_only = False
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--print":
            print_only = True
            i += 1
        if sys.argv[i][0:2] == '-e':
            if sys.argv[i][2:] == '':
                cmd = addarg(cmd, sys.argv[i])
                i += 1
                event = ""
                if len(sys.argv) > i:
                    event = sys.argv[i]
            else:
                event = sys.argv[i][2:]
            event = process_events(event, print_only)
            cmd = addarg(cmd, event)
        else:        
            cmd = addarg(cmd, sys.argv[i])
        i += 1
    print cmd
    if print_only:
        sys.exit(0)
    return cmd

def perf_cmd(cmd):
    if len(sys.argv) >= 2 and sys.argv[1] == "list":
        os.system(cmd + "| cat")
        print
        emap.dumpevents()
    elif len(sys.argv) >= 2 and (sys.argv[1] == "report" or sys.argv[1] == "stat"):
        for w in sys.argv:
            if w == "--tui":
                os.system(cmd)
                latego.cleanup()
                sys.exit(0)
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
        os.system(cmd)

if __name__ == '__main__':
    emap = find_emap()
    msr = MSR()
    cmd = process_args()
    perf_cmd(cmd)
