#
# Simple 5 event top level model
#

print_error = lambda msg: False
version = "1.0"

# Constants

PipelineWidth = 4

def CLKS(EV):
    return EV("CPU_CLK_UNHALTED.THREAD", 1)

def SLOTS(EV):
    return PipelineWidth * CLKS(EV)

# Instructions Per Cycle
def IPC(EV, level):
    return EV("INST_RETIRED.ANY", level) / CLKS(EV)

# Uops Per Instruction
def UPI(EV, level):
    return EV("UOPS_RETIRED.RETIRE_SLOTS", level) / EV("INST_RETIRED.ANY", level)

# Average Frequency Utilization relative nominal frequency
def TurboUtilization(EV, level):
    return CLKS(EV) / EV("CPU_CLK_UNHALTED.REF_TSC", level)

class FrontendBound:
    name = "Frontend Bound"
    domain = "Slots"
    desc = """
This category reflects slots where the Frontend of the processor undersupplies
its Backend."""
    level = 1
    def compute(self, EV):
         try:
             self.val = EV("IDQ_UOPS_NOT_DELIVERED.CORE", 1) / SLOTS(EV)
             self.thresh = self.val > 0.2
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class BadSpeculation:
    name = "Bad Speculation"
    domain = "Slots"
    desc = """
This category reflects slots wasted due to incorrect speculations, which
include slots used to allocate uops that do not eventually get retired and
slots for which allocation was blocked due to recovery from earlier incorrect
speculation. For example, wasted work due to miss-predicted branches is
categorized under the Bad Speculation category"""
    level = 1
    def compute(self, EV):
         try:
             self.val = ( EV("UOPS_ISSUED.ANY", 1) - EV("UOPS_RETIRED.RETIRE_SLOTS", 1) + PipelineWidth * EV("INT_MISC.RECOVERY_CYCLES", 1) ) / SLOTS(EV)
             self.thresh = self.val > 0.1
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class BackendBound:
    name = "Backend Bound"
    domain = "Slots"
    desc = """
This category reflects slots where no uops are being delivered due to a lack
of required resources for accepting more uops in the Backend of the pipeline."""
    level = 1
    def compute(self, EV):
         try:
             self.val = 1 - ( self.FrontendBound.compute(EV) + self.BadSpeculation.compute(EV) + self.Retiring.compute(EV) )
             self.thresh = self.val > 0.2
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class Retiring:
    name = "Retiring"
    domain = "Slots"
    desc = """
This category reflects slots utilized by good uops i.e. allocated uops that
eventually get retired."""
    level = 1
    def compute(self, EV):
         try:
             self.val = EV("UOPS_RETIRED.RETIRE_SLOTS", 1) / SLOTS(EV)
             self.thresh = self.val > 0.7
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class Metric_IPC:
    name = "IPC"
    desc = """
Instructions Per Cycle"""
    errcount = 0

    def compute(self, EV):
        try:
            self.val = IPC(EV, 0)
        except ZeroDivisionError:
            print_error("IPC zero division")
            self.errcount += 1
            self.val = 0

class Metric_UPI:
    name = "UPI"
    desc = """
Uops Per Instruction"""
    errcount = 0

    def compute(self, EV):
        try:
            self.val = UPI(EV, 0)
        except ZeroDivisionError:
            print_error("UPI zero division")
            self.errcount += 1
            self.val = 0

class Metric_TurboUtilization:
    name = "TurboUtilization"
    desc = """
Average Frequency Utilization relative nominal frequency"""
    errcount = 0

    def compute(self, EV):
        try:
            self.val = TurboUtilization(EV, 0)
        except ZeroDivisionError:
            print_error("TurboUtilization zero division")
            self.errcount += 1
            self.val = 0

class Setup:
    def __init__(self, r):
        prev = None
        o = dict()
        n = FrontendBound() ; r.run(n)
        o["FrontendBound"] = n
        n = BadSpeculation() ; r.run(n)
        o["BadSpeculation"] = n
        n = BackendBound() ; r.run(n)
        o["BackendBound"] = n
        n = Retiring() ; r.run(n)
        o["Retiring"] = n

        o["FrontendBound"].parent = None
        o["BadSpeculation"].parent = None
        o["BackendBound"].parent = None
        o["Retiring"].parent = None
        
        o["BackendBound"].FrontendBound = o["FrontendBound"]
        o["BackendBound"].BadSpeculation = o["BadSpeculation"]
        o["BackendBound"].Retiring = o["Retiring"]

        o["FrontendBound"].sibling = None
        o["BadSpeculation"].sibling = None
        o["BackendBound"].sibling = None
        o["Retiring"].sibling = None

        o["FrontendBound"].sample = []
        o["BadSpeculation"].sample = []
        o["BackendBound"].sample = []
        o["Retiring"].sample = []

        # user visible metrics

        n = Metric_IPC() ; r.metric(n)
        n = Metric_UPI() ; r.metric(n)
        n = Metric_TurboUtilization() ; r.metric(n)
