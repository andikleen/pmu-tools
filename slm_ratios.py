#
# Silvermont top level model
# Can be collected without multiplexing
# Please see http://ark.intel.com for more details on these CPUs.
#

print_error = lambda msg: False
version = "1.0"

# Instructions Per Cycle
def IPC(EV, level):
    return EV("INST_RETIRED.ANY", level) / EV("cycles", 1)

# Average Frequency Utilization relative nominal frequency
def TurboUtilization(EV, level):
    return EV("cycles", level) / EV("CPU_CLK_UNHALTED.REF_TSC", level)

def DurationTimeInSeconds(EV, level):
    return EV("interval-ns", 0) / 1e+06 / 1000

# Run duration time in seconds
def Time(EV, level):
    return DurationTimeInSeconds(EV, level)

# Per-thread actual clocks
def CLKS(EV, level):
    return EV("CPU_CLK_UNHALTED.THREAD", level)

# Cycles Per Instruction (threaded)
def CPI(EV, level):
    return 1 / IPC(EV, level)

class FrontendBound:
    name = "Frontend Bound"
    domain = ""
    desc = """
This category reflects slots where the Frontend of the processor undersupplies
its Backend."""
    level = 1
    def compute(self, EV):
         try:
             self.val = EV("NO_ALLOC_CYCLES.NOT_DELIVERED", 1) / EV("cycles", 1)
             self.thresh = self.val > 0
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class BackendOrBadSpeculation:
    name = "Backend or Bad Speculation"
    domain = "Slots"
    desc = """
This category reflects slots wasted due to incorrect speculations, or
slots where no uops are being delivered due to a lack
of required resources for accepting more uops in the Backend of the pipeline.  """
    level = 1
    def compute(self, EV):
         try:
             EV("cycles", 1) # hack to force evaluation
             self.val = 1. - self.FrontendBound.val - self.Retiring.val
             self.thresh = self.val > 0.0
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class Retiring:
    name = "Retiring"
    domain = ""
    desc = """
This category reflects slots utilized by good uops i.e. allocated uops that
eventually get retired."""
    level = 1
    def compute(self, EV):
         try:
             self.val = (EV("UOPS_RETIRED.ALL", 1) * 0.5)/ EV("cycles", 1)
             self.thresh = self.val > 0
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class Metric_IPC:
    name = "IPC"
    desc = """
Instructions Per Cycle"""

    def compute(self, EV):
        try:
            self.val = IPC(EV, 0)
        except ZeroDivisionError:
            print "IPC zero division"
            self.val = 0

class Metric_TurboUtilization:
    name = "TurboUtilization"
    desc = """
Average Frequency Utilization relative nominal frequency"""

    def compute(self, EV):
        try:
            self.val = TurboUtilization(EV, 0)
        except ZeroDivisionError:
            print "TurboUtilization zero division"
            self.val = 0

class Metric_CLKS:
    name = "CLKS"
    desc = """
Per-thread actual clocks"""
    domain = "Count"
    maxval = 0
    errcount = 0

    def compute(self, EV):
        try:
            self.val = CLKS(EV, 0)
        except ZeroDivisionError:
            print_error("CLKS zero division")
            self.errcount += 1
            self.val = 0

class Metric_Time:
    name = "Time"
    desc = """
Run duration time in seconds"""
    domain = "Count"
    maxval = 0
    errcount = 0

    def compute(self, EV):
        try:
            self.val = Time(EV, 0)
        except ZeroDivisionError:
            print_error("Time zero division")
            self.errcount += 1
            self.val = 0

class Metric_CPI:
    name = "CPI"
    desc = """
Cycles Per Instruction (threaded)"""
    domain = "Metric"
    maxval = 0
    errcount = 0

    def compute(self, EV):
        try:
            self.val = CPI(EV, 0)
        except ZeroDivisionError:
            print_error("CPI zero division")
            self.errcount += 1
            self.val = 0

class Setup:
    def __init__(self, r):
        prev = None
        o = dict()
        n = FrontendBound() ; r.run(n) ; n.parent = prev ; prev = n
        o["FrontendBound"] = n
        n = Retiring() ; r.run(n) ; n.parent = prev ; prev = n
        o["Retiring"] = n
        n = BackendOrBadSpeculation() ; r.run(n) ; n.parent = prev ; prev = n
        o["BackendOrBadSpeculation"] = n

        o["BackendOrBadSpeculation"].FrontendBound = o["FrontendBound"]
        o["BackendOrBadSpeculation"].Retiring = o["Retiring"]

        o["FrontendBound"].sibling = None
        o["BackendOrBadSpeculation"].sibling = None
        o["Retiring"].sibling = None

        o["FrontendBound"].sample = []
        o["BackendOrBadSpeculation"].sample = []
        o["Retiring"].sample = []

        # user visible metrics

        n = Metric_IPC() ; r.metric(n)
        n = Metric_CPI() ; r.metric(n)
        n = Metric_TurboUtilization() ; r.metric(n)
        n = Metric_CLKS() ; r.metric(n)
        n = Metric_Time() ; r.metric(n)
