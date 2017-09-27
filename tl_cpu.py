# Copyright (c) 2012-2015, Intel Corporation
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
from collections import defaultdict, Counter
import os
import re
import glob

def num_offline_cpus():
    cpus = glob.glob("/sys/devices/system/cpu/cpu[0-9]*/online")
    offline = 0
    for fn in cpus:
        with open(fn, "r") as f:
            if int(f.read()) == 0:
                offline += 1
    return offline

class CPU:
    """Detect the CPU."""
    # overrides for easy regression tests
    def force_cpu(self, known_cpus):
        force = os.getenv("FORCECPU")
        if not force:
            return False
        self.cpu = None
        for i in known_cpus:
            if force == i[0]:
                self.cpu = i[0]
                break
        if self.cpu is None:
            print "Unknown FORCECPU ",force
        return True

    def force_counters(self):
        cnt = os.getenv("FORCECOUNTERS")
        if cnt:
            self.counters = int(cnt)

    def force_ht(self):
        ht = os.getenv("FORCEHT")
        if ht:
            self.ht = int(ht)
            return True
        return False

    def __init__(self, known_cpus):
        self.model = 0
        self.cpu = None
        self.realcpu = "simple"
        self.ht = False
        self.counters = 0
        self.has_tsx = False
        self.hypervisor = False
        self.freq = 0.0
        self.siblings = {}
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
        self.name = ""
	cpuinfo = os.getenv("CPUINFO")
	if cpuinfo is None:
	    cpuinfo = "/proc/cpuinfo"
	with open(cpuinfo, "r") as f:
            ok = 0
            for l in f:
                n = l.split()
                if len(n) < 3:
                    continue
                if n[0] == 'processor':
                    ok += 1
                    cpunum = int(n[2])
                    self.allcpus.append(cpunum)
                elif (n[0], n[2]) == ("vendor_id", "GenuineIntel") and ok == 0:
                    ok += 1
                elif (len(n) > 3 and
                        (n[0], n[1], n[3]) == ("cpu", "family", "6") and
                        ok == 1):
                    ok += 1
                elif (n[0], n[1]) == ("model", ":") and ok == 2:
                    ok += 1
                    self.model = int(n[2])
                elif (n[0], n[1]) == ("model", "name"):
                    ok += 1
                    m = re.search(r"@ (\d+\.\d+)Ghz", l)
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
                    ok += 1
                    self.has_tsx = "rtm" in n
                    self.hypervisor = "hypervisor" in n
        if ok >= 6:
            for i in known_cpus:
                if self.model in i[1]:
                    self.realcpu = i[0]
                    if not forced_cpu:
                        self.cpu = i[0]
                    break
        if self.counters == 0:
            self.standard_counters = "0,1,2,3"
            if self.cpu == "slm":
                self.counters = 2
                self.standard_counters = "0,1"
            # when running in a hypervisor always assume worst case HT in on
            # also when CPUs are offline assume SMT is on
            elif self.ht or self.hypervisor or num_offline_cpus() > 0:
                self.counters = 4
            else:
                self.counters = 8
            # chicken bit to override if we get it wrong
            counters = os.getenv("TLCOUNTERS")
            if counters:
                self.counters = int(counters)
        self.sockets = len(sockets.keys())
