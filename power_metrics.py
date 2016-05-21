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
    domain = "Package"
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
    domain = "Package"
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
    domain = "Package"
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
    domain = "Package"
    def compute(self, EV):
        self.val = EV("power/energy-gpu/", 1)
        self.thresh = self.val > 1

class Setup:
    def __init__(self, r):
        r.metric(EnergyCores())
        r.metric(EnergyPackage())
        if os.path.exists("/sys/devices/power/events/energy-ram"):
            r.metric(EnergyRAM())
        if os.path.exists("/sys/devices/power/events/energy-gpu"):
            r.metric(EnergyGPU())
