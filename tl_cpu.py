# Copyright (c) 2012-2020, Intel Corporation
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
# toplev CPU detection

#
# Environment variables to override (mainly for testing):
# FORCECPU=cpu     Force CPU type (e.g. skl). Also --force-cpu
# FORCECOUNTERS=n  Force number of generic counters
# FORCEHT=0/1      Force SMT mode
# HYPERVISOR=0/1   Force hypervisor mode (also --force-hypervisor)
# CPUINFO=file     Read cpu information from file instead of /proc/cpuinfo. Also --force-cpuinfo
# REDUCED_COUNTERS=n Reduce counters by n
#

from collections import defaultdict, Counter
import os
import re
import glob
import sys
if sys.version_info.major == 3:
    import typing # noqa
    from typing import Set, List, Dict, Tuple # noqa

modelid_map = {
    (0x8e, ): "KBLR",
    (0x9e, ): "CFL",
}

cpus_8gpc = set(["icl", "tgl", "icx", "spr", "sprmax", "srf", "lnl", "arl", "gnr"])

def num_offline_cpus():
    cpus = glob.glob("/sys/devices/system/cpu/cpu[0-9]*/online")
    offline = 0
    for fn in cpus:
        with open(fn, "r") as f:
            if int(f.read()) == 0:
                offline += 1
    return offline

def reduced_counters():
    rc = os.getenv("REDUCED_COUNTERS")
    if rc:
        return int(rc)
    val = 1
    fn = "/sys/bus/event_source/devices/cpu/allow_tsx_force_abort"
    if os.path.exists(fn):
        with open(fn, "r") as f:
            val = int(f.read())
    return 1 if val == 0 else 0

class Env(object):
    def __init__(self):
        self.forcecpu = os.getenv("FORCECPU")
        self.forcecounters = os.getenv("FORCECOUNTERS")
        self.forceht = os.getenv("FORCEHT")
        self.hypervisor = os.getenv("HYPERVISOR")
        self.cpuinfo = os.getenv("CPUINFO")

class CPU(object):
    """Detect the CPU."""
    # overrides for easy regression tests
    def force_cpu(self, known_cpus):
        force = self.env.forcecpu
        if not force:
            return False
        self.cpu = ""
        for i in known_cpus:
            if force == i[0]:
                self.cpu = i[0]
                break
        if self.cpu is None:
            print("Unknown FORCECPU ",force)
        return True

    def force_ht(self):
        ht = self.env.forceht
        if ht:
            self.ht = True if int(ht) else False
            return True
        return False

    def __init__(self, known_cpus=(), nocheck=False, env=Env()):
        self.vendor = ""
        self.env = env
        self.model = 0
        self.cpu = ""
        self.realcpu = "simple"
        self.ht = False
        self.counters = {} # type: Dict[str,int]
        self.has_tsx = False
        self.hypervisor = False
        self.force_hypervisor = False
        if self.env.hypervisor:
            self.hypervisor = True
            self.force_hypervisor = True
        self.freq = 0.0
        self.threads = 0
        forced_cpu = self.force_cpu(known_cpus)
        forced_ht = self.force_ht()
        cores = Counter() # type: typing.Counter[Tuple[int,int]]
        sockets = Counter() # type: typing.Counter[int]
        self.coreids = defaultdict(list)
        self.cputocore = {}
        self.cputothread = {}
        self.sockettocpus = defaultdict(list)
        self.cputosocket = {}
        self.allcpus = []
        self.step = 0
        self.name = ""
        cpuinfo = self.env.cpuinfo
        if cpuinfo is None:
            cpuinfo = "/proc/cpuinfo"
        with open(cpuinfo, "r") as f:
            seen = set()
            for l in f:
                n = l.split()
                if len(n) < 3:
                    continue
                if n[0] == 'processor':
                    seen.add("processor")
                    cpunum = int(n[2])
                    self.allcpus.append(cpunum)
                elif (n[0], n[2]) == ("vendor_id", "GenuineIntel"):
                    self.vendor = n[2]
                    seen.add("vendor_id")
                elif (len(n) > 3 and
                        (n[0], n[1], n[3]) == ("cpu", "family", "6")):
                    seen.add("cpu family")
                elif (n[0], n[1]) == ("model", ":"):
                    seen.add("model")
                    self.model = int(n[2])
                elif (n[0], n[1]) == ("model", "name"):
                    seen.add("model name")
                    m = re.search(r"@ (\d+\.\d+)GHz", l)
                    if m:
                        self.freq = float(m.group(1))
                    self.name = " ".join(n[3:])
                elif (n[0], n[1]) == ("physical", "id"):
                    physid = int(n[3])
                    sockets[physid] += 1
                    self.sockettocpus[physid].append(cpunum)
                    self.cputosocket[cpunum] = physid
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
                    seen.add("flags")
                    self.has_tsx = "rtm" in n
                    if "hypervisor" in n:
                        self.hypervisor = True
                elif n[0] == "stepping":
                    seen.add("stepping")
                    self.step = int(n[2])
        if len(seen) >= 7:
            for i in known_cpus:
                if self.model in i[1] or (self.model, self.step) in i[1]:
                    self.realcpu = i[0]
                    if not forced_cpu:
                        self.cpu = i[0]
                    break
        self.force_counters()
        self.limit4_counters = { "cpu": "none" }
        self.standard_counters = { "cpu": tuple(("0,1,2,3",)) }
        if self.cpu.startswith("lnl"):
            newcounters = {
                "cpu_core": 10,
                "cpu": 10,
                "cpu_atom": 8,
            }
            self.standard_counters = {
                "cpu_core": ("0,1,2,3,4,5,6,7,8,9", ),
                "cpu": ("0,1,2,3,4,5,6,7,8,9", "0,1,2,3,4,5,6,7" ),
                "cpu_atom": ("0,1,2,3,4,5,6,7", )
            }
            self.limit4_counters = { "cpu_core": "0,1,2,3", "cpu_atom": "none",
                                     "cpu": "0,1,2,3" }
        elif self.cpu.startswith("adl") or self.cpu.startswith("mtl"):
            atom_counters = 6 if self.cpu.startswith("adl") else 8
            newcounters = {
                "cpu_core": 8,
                "cpu": 4,
                "cpu_atom": atom_counters,
            }
            self.standard_counters = {
                "cpu_core": ("0,1,2,3,4,5,6,7", "0,1,2,3", ),
                "cpu": ("0,1,2,3,4,5,6,7", "0,1,2,3", "0,1,2,3,4,5" ),
                "cpu_atom": ("0,1,2,3,4,5", ) if atom_counters == 6 else ("0,1,2,3,4,5,6,7,", )
            }
            self.limit4_counters = { "cpu_core": "0,1,2,3", "cpu_atom": "none",
                                     "cpu": "0,1,2,3" }
        elif self.cpu == "slm":
            newcounters = { "cpu": 2 }
            self.standard_counters = { "cpu": ("0,1",) }
        # when running in a hypervisor always assume worst case HT in on
        # also when CPUs are offline assume SMT is on
        elif self.ht or self.hypervisor or (num_offline_cpus() > 0 and not nocheck) or self.cpu in cpus_8gpc:
            if self.cpu in cpus_8gpc or (self.cpu == "simple" and self.realcpu in cpus_8gpc):
                newcounters = {"cpu": 8 }
                self.standard_counters = { "cpu": ("0,1,2,3,4,5,6,7", "0,1,2,3", ) }
                self.limit4_counters = { "cpu": "0,1,2,3" }
            else:
                newcounters = { "cpu": 4 }
        elif self.cpu == "ehl":
            newcounters = { "cpu": 4 }
        else:
            newcounters = { "cpu": 8 }
        if not self.counters:
            self.counters = newcounters
        if not nocheck and not self.env.forcecounters:
            for j in ("cpu", "cpu_core", "cpu_atom"):
                if j in self.counters:
                    self.counters[j] -= reduced_counters()
        if self.cpu in cpus_8gpc:
            self.standard_counters = { "cpu": ("0,1,2,3,4,5,6,7", "0,1,2,3",
                                               "0,1,2,3,4,5,6,7", "0,1,2,3,4,5,6,7,8,9") }
            self.limit4_counters = { "cpu": "0,1,2,3" }

        if self.cpu == "spr" and "Max" in self.name:
            self.cpu = "sprmax"

        try:
            self.pmu_name = open("/sys/bus/event_source/devices/cpu/caps/pmu_name").read().strip()
        except IOError:
            self.pmu_name = ""

        self.sockets = len(sockets.keys())
        self.modelid = None
        mid = (self.model,)
        self.true_name = self.cpu
        if mid in modelid_map:
            self.modelid = modelid_map[mid]
            self.true_name = self.modelid.lower()
        # XXX match steppings here too

    def force_counters(self):
        cnt = self.env.forcecounters
        if cnt:
            cntn = int(cnt)
            if self.realcpu in ("adl", "mtl", "lnl"):
                self.counters = {
                    "cpu_core": cntn,
                    "cpu_atom": cntn,
                    "cpu": cntn }
            else:
                self.counters = { "cpu": cntn }
