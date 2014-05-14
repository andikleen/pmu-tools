#
# Silvermont top level model
# Can be collected without multiplexing
# Please see http://ark.intel.com for more details on these CPUs.
#

# Instructions Per Cycle
def IPC(EV, level):
    return EV("INST_RETIRED.ANY", level) / EV("CPU_CLK_UNHALTED.THREAD", 1)

# Average Frequency Utilization relative nominal frequency
def TurboUtilization(EV, level):
    return EV("CPU_CLK_UNHALTED.THREAD", level) / EV("CPU_CLK_UNHALTED.REF_TSC", level)

class FrontendBound:
    name = "Frontend Bound"
    domain = ""
    desc = """
This category reflects slots where the Frontend of the processor undersupplies
its Backend."""
    level = 1
    def compute(self, EV):
         try:
             self.val = EV("NO_ALLOC_CYCLES.NOT_DELIVERED", 1) / EV("CPU_CLK_UNHALTED.CORE", 1)
             self.thresh = self.val > 0.0
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
             self.val = (EV("UOPS_RETIRED.ALL", 1) * 0.5)/ EV("CPU_CLK_UNHALTED.CORE", 1)
             self.thresh = self.val > 0.0
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

        o["FrontendBound"].sample = []
        o["BackendOrBadSpeculation"].sample = []
        o["Retiring"].sample = []

        # user visible metrics

        n = Metric_IPC() ; r.metric(n)
        n = Metric_TurboUtilization() ; r.metric(n)
