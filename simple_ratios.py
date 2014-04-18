#
# Simple 5 event top level model
#

# Constants

PipelineWidth = 4

def CLKS(EV):
    return EV("CPU_CLK_UNHALTED.THREAD", 1)

def SLOTS(EV):
    return PipelineWidth * CLKS(EV)

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

class Setup:
    def __init__(self, r):
        prev = None
        o = dict()
        n = FrontendBound() ; r.run(n) ; n.parent = prev ; prev = n
        o["FrontendBound"] = n
        n = BadSpeculation() ; r.run(n) ; n.parent = prev ; prev = n
        o["BadSpeculation"] = n
        n = BackendBound() ; r.run(n) ; n.parent = prev ; prev = n
        o["BackendBound"] = n
        n = Retiring() ; r.run(n) ; n.parent = prev ; prev = n
        o["Retiring"] = n
        
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

