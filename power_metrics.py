#
# perf power metrics for toplev
#

import os

class EnergyPackage:
    name = "Package Energy"
    desc = """
Package Energy over measurement period in Joules"""
    unit = "Joules"
    nogroup = True
    subplot = "Power"
    def compute(self, EV):
        self.val = EV("power/energy-pkg/", 1)
        self.thresh = self.val > 0

class EnergyCores:
    name = "Cores Energy"
    desc = """
Cores Energy over measurement period in Joules"""
    unit = "Joules"
    nogroup = True
    subplot = "Power"
    def compute(self, EV):
        self.val = EV("power/energy-cores/", 1)
        self.thresh = self.val > 0

class EnergyRAM:
    name = "RAM Energy"
    desc = """
RAM Energy over measurement period in Joules"""
    unit = "Joules"
    nogroup = True
    subplot = "Power"
    def compute(self, EV):
        self.val = EV("power/energy-ram/", 1)
        self.thresh = self.val > 0

class EnergyGPU:
    name = "GPU Energy"
    desc = """
GPU Energy over measurement period in Joules"""
    unit = "Joules"
    nogroup = True
    subplot = "Power"
    def compute(self, EV):
        self.val = EV("power/energy-gpu/", 1)
        self.thresh = self.val > 1

class Setup:
    def __init__(self, r):
        r.metric(EnergyCores())
        r.metric(EnergyPackage())
        perf = os.getenv("PERF")
        if not perf:
            perf = "perf"
        if os.system(perf + " stat -e power/energy-ram/ >/dev/null 2>/dev/null true") == 0:
            r.metric(EnergyRAM())
        if os.system(perf + " stat -e power/energy-gpu/ >/dev/null 2>/dev/null true") == 0:
            r.metric(EnergyGPU())
