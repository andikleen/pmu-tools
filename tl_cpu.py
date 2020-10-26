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

modelid_map = {
    (0x8e, ): "KBLR",
    (0x9e, ): "CFL",
}

cpus_8gpc = set(["icl", "tgl"])

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
    fn = "/sys/devices/cpu/allow_tsx_force_abort"
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
        self.cpu = None
        for i in known_cpus:
            if force == i[0]:
                self.cpu = i[0]
                break
        if self.cpu is None:
            print("Unknown FORCECPU ",force)
        return True

    def force_counters(self):
        cnt = self.env.forcecounters
        if cnt:
            self.counters = int(cnt)

    def force_ht(self):
        ht = self.env.forceht
        if ht:
            self.ht = int(ht)
            return True
        return False

    def __init__(self, known_cpus, nocheck, env):
        self.env = env
        self.model = 0
        self.cpu = None
        self.realcpu = "simple"
        self.ht = False
        self.counters = 0
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
        self.force_counters()
        cores = Counter()
        sockets = Counter()
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
        self.limit4_counters = "none"
        self.standard_counters = ("0,1,2,3",)
        if self.counters == 0:
            if self.cpu == "slm":
                self.counters = 2
                self.standard_counters = ("0,1",)
            # when running in a hypervisor always assume worst case HT in on
            # also when CPUs are offline assume SMT is on
            elif self.ht or self.hypervisor or (num_offline_cpus() > 0 and not nocheck) or self.cpu in cpus_8gpc:
                if self.cpu in cpus_8gpc or (self.cpu == "simple" and self.realcpu in cpus_8gpc):
                    self.counters = 8
                    self.standard_counters = ("0,1,2,3,4,5,6,7", "0,1,2,3", )
                    self.limit4_counters = "0,1,2,3"
                else:
                    self.counters = 4
            else:
                self.counters = 8
            if not nocheck:
                self.counters -= reduced_counters()
        elif self.cpu in cpus_8gpc:
            self.standard_counters = ("0,1,2,3,4,5,6,7", "0,1,2,3", )
            self.limit4_counters = "0,1,2,3"

        try:
            self.pmu_name = open("/sys/devices/cpu/caps/pmu_name").read().strip()
        except IOError:
            self.pmu_name = None

        self.sockets = len(sockets.keys())
        self.modelid = None
        mid = (self.model,)
        self.true_name = self.cpu
        if mid in modelid_map:
            self.modelid = modelid_map[mid]
            self.true_name = self.modelid.lower()
        # XXX match steppings here too
