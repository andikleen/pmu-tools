
#
# auto generated TopDown description for Intel 2nd gen Core (code named SandyBridge)
# Please see http://ark.intel.com for more details on these CPUs.
#


# Constants

PipelineWidth = 4
MEM_L3_WEIGHT = 7
MEM_STLB_HIT_COST = 7
MEM_SFB_COST = 13
MEM_4KALIAS_COST = 7
MEM_XSNP_HITM_COST = 60
MEM_XSNP_HIT_COST = 43
MEM_XSNP_NONE_COST = 29
MS_SWITCHES_COST = 3

# Aux. formulas

def FLOP_count(EV, level):
    return ( 1 *(EV("FP_COMP_OPS_EXE.SSE_SCALAR_SINGLE", level) + EV("FP_COMP_OPS_EXE.SSE_SCALAR_DOUBLE", level))+ 2 * EV("FP_COMP_OPS_EXE.SSE_PACKED_DOUBLE", level) + 4 *(EV("FP_COMP_OPS_EXE.SSE_PACKED_SINGLE", level) + EV("SIMD_FP_256.PACKED_DOUBLE", level))+ 8 * EV("SIMD_FP_256.PACKED_SINGLE", level) )
def RetireUopFraction(EV, level):
    return EV("UOPS_RETIRED.RETIRE_SLOTS", level) / EV("UOPS_ISSUED.ANY", level)
def SLOTS(EV, level):
    return PipelineWidth * CLKS(EV, level)
def IPC(EV, level):
    return EV("INST_RETIRED.ANY", level) / CLKS(EV, level)
def UPI(EV, level):
    return EV("UOPS_RETIRED.RETIRE_SLOTS", level) / EV("INST_RETIRED.ANY", level)
def InstPerTakenBranch(EV, level):
    return EV("INST_RETIRED.ANY", level) / EV("BR_INST_RETIRED.NEAR_TAKEN", level)
def DSBCoverage(EV, level):
    return ( EV("IDQ.DSB_UOPS", level) + EV("LSD.UOPS", level))/(EV("IDQ.DSB_UOPS", level) + EV("LSD.UOPS", level) + EV("IDQ.MITE_UOPS", level) + EV("IDQ.MS_UOPS", level) )
def MLP(EV, level):
    return EV("L1D_PEND_MISS.PENDING", level) / EV("L1D_PEND_MISS.PENDING_CYCLES", level)
def CPUUtilization(EV, level):
    return EV("CPU_CLK_UNHALTED.REF_TSC", level) / XXX
def TurboUtilization(EV, level):
    return CLKS(EV, level) / EV("CPU_CLK_UNHALTED.REF_TSC", level)
def GFLOPs(EV, level):
    return FLOP_count(EV, level) / 1e9 / XXX
def CLKS(EV, level):
    return EV("CPU_CLK_UNHALTED.THREAD", level)

# Event groups


class FrontendBound:
    name = "FrontendBound"
    domain = "Slots"
    area = "FE"
    desc = """
This category reflects slots where the Frontend of the processor undersupplies
its Backend."""
    level = 1
    def compute(self, EV):
        try:
            self.val = EV("IDQ_UOPS_NOT_DELIVERED.CORE", 1) / SLOTS(EV, 1)
            self.thresh = (self.val > 0.2)
        except ZeroDivisionError:
            print "FrontendBound zero division"
            self.val = 0
            self.thresh = False
        return self.val

class FrontendLatency:
    name = "Frontend Latency"
    domain = "Slots"
    area = "FE"
    desc = """
This metric represents slots fraction CPU was stalled due to Frontend latency
issues."""
    level = 2
    def compute(self, EV):
        try:
            self.val = PipelineWidth * EV("IDQ_UOPS_NOT_DELIVERED.CYCLES_0_UOPS_DELIV.CORE", 2) / SLOTS(EV, 2)
            self.thresh = (self.val > 0.15) and self.parent.thresh
        except ZeroDivisionError:
            print "FrontendLatency zero division"
            self.val = 0
            self.thresh = False
        return self.val

class ITLBmisses:
    name = "ITLB misses"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents cycles fraction CPU was stalled due to instruction TLB
misses."""
    level = 3
    def compute(self, EV):
        try:
            self.val = EV("ITLB_MISSES.WALK_DURATION", 3) / CLKS(EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            print "ITLBmisses zero division"
            self.val = 0
            self.thresh = False
        return self.val

class DSBswitches:
    name = "DSB switches"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents cycles fraction CPU was stalled due to switches from
DSB to MITE pipelines."""
    level = 3
    def compute(self, EV):
        try:
            self.val = EV("DSB2MITE_SWITCHES.PENALTY_CYCLES", 3) / CLKS(EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            print "DSBswitches zero division"
            self.val = 0
            self.thresh = False
        return self.val

class LCP:
    name = "LCP"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents cycles fraction CPU was stalled due to Length Changing
Prefixes (LCPs)."""
    level = 3
    def compute(self, EV):
        try:
            self.val = EV("ILD_STALL.LCP", 3) / CLKS(EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            print "LCP zero division"
            self.val = 0
            self.thresh = False
        return self.val

class MSswitches:
    name = "MS switches"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents cycles fraction CPU was stalled due to switches of uop
delivery to the Microcode Sequencer (MS)."""
    level = 3
    def compute(self, EV):
        try:
            self.val = MS_SWITCHES_COST * EV("IDQ.MS_SWITCHES", 3) / CLKS(EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            print "MSswitches zero division"
            self.val = 0
            self.thresh = False
        return self.val

class FrontendBandwidth:
    name = "Frontend Bandwidth"
    domain = "Slots"
    area = "FE"
    desc = """
This metric represents slots fraction CPU was stalled due to Frontend
bandwidth issues."""
    level = 2
    def compute(self, EV):
        try:
            self.val = self.FrontendBound.compute(EV) - self.FrontendLatency.compute(EV)
            self.thresh = (self.val > 0.1) & (IPC(EV, 2) > 2.0) and self.parent.thresh
        except ZeroDivisionError:
            print "FrontendBandwidth zero division"
            self.val = 0
            self.thresh = False
        return self.val

class MITE:
    name = "MITE"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents cycles fraction in which CPU was likely limited due to
the MITE fetch pipeline."""
    level = 3
    def compute(self, EV):
        try:
            self.val = ( EV("IDQ.ALL_MITE_CYCLES_ANY_UOPS", 3) - EV("IDQ.ALL_MITE_CYCLES_4_UOPS", 3))/ CLKS(EV, 3)
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            print "MITE zero division"
            self.val = 0
            self.thresh = False
        return self.val

class DSB:
    name = "DSB"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents cycles fraction in which CPU was likely limited due to
DSB (decoded uop cache) fetch pipeline."""
    level = 3
    def compute(self, EV):
        try:
            self.val = ( EV("IDQ.ALL_DSB_CYCLES_ANY_UOPS", 3) - EV("IDQ.ALL_DSB_CYCLES_4_UOPS", 3))/ CLKS(EV, 3)
            self.thresh = (self.val > 0.3) and self.parent.thresh
        except ZeroDivisionError:
            print "DSB zero division"
            self.val = 0
            self.thresh = False
        return self.val

class LSD:
    name = "LSD"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents cycles fraction in which CPU was likely limited due to
LSD (Loop Stream Detector) unit."""
    level = 3
    def compute(self, EV):
        try:
            self.val = ( EV("LSD.CYCLES_ACTIVE", 3) - EV("LSD.CYCLES_4_UOPS", 3))/ CLKS(EV, 3)
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            print "LSD zero division"
            self.val = 0
            self.thresh = False
        return self.val

class BadSpeculation:
    name = "BadSpeculation"
    domain = "Slots"
    area = "BAD"
    desc = """
This category reflects slots wasted due to incorrect speculations, which
include slots used to allocate uops that do not eventually get retired and
slots for which allocation was blocked due to recovery from earlier incorrect
speculation."""
    level = 1
    def compute(self, EV):
        try:
            self.val = ( EV("UOPS_ISSUED.ANY", 1) - EV("UOPS_RETIRED.RETIRE_SLOTS", 1) + PipelineWidth * EV("INT_MISC.RECOVERY_CYCLES", 1))/ SLOTS(EV, 1)
            self.thresh = (self.val > 0.1)
        except ZeroDivisionError:
            print "BadSpeculation zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Backend_Bound:
    name = "Backend_Bound"
    domain = "Slots"
    area = "BE"
    desc = """
This category reflects slots where no uops are being delivered due to a lack
of required resources for accepting more uops in the Backend of the pipeline."""
    level = 1
    def compute(self, EV):
        try:
            self.val = 1 -(self.FrontendBound.compute(EV) + self.BadSpeculation.compute(EV) + self.Retiring.compute(EV) )
            self.thresh = (self.val > 0.2)
        except ZeroDivisionError:
            print "Backend_Bound zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Retiring:
    name = "Retiring"
    domain = "Slots"
    area = "RET"
    desc = """
This category reflects slots utilized by useful work i. Note that a high
Retiring value does not necessary mean there is no room for more performance.
A high Retiring value for non-vectorized code may be a good hint for
programmer to consider vectorizing his code."""
    level = 1
    def compute(self, EV):
        try:
            self.val = EV("UOPS_RETIRED.RETIRE_SLOTS", 1) / SLOTS(EV, 1)
            self.thresh = (self.val > 0.7)
        except ZeroDivisionError:
            print "Retiring zero division"
            self.val = 0
            self.thresh = False
        return self.val

class BASE:
    name = "BASE"
    domain = "Slots"
    area = "RET"
    desc = """
This metric represents slots fraction CPU was retiring uops not originated
from the microcode-sequencer."""
    level = 2
    def compute(self, EV):
        try:
            self.val = self.Retiring.compute(EV) - self.MicroSequencer.compute(EV)
            self.thresh = (self.val > 0.6) and self.parent.thresh
        except ZeroDivisionError:
            print "BASE zero division"
            self.val = 0
            self.thresh = False
        return self.val

class MicroSequencer:
    name = "MicroSequencer"
    domain = "Slots"
    area = "RET"
    desc = """
This metric represents slots fraction CPU was retiring uops fetched by the
Microcode Sequencer (MS) ROM."""
    level = 2
    def compute(self, EV):
        try:
            self.val = RetireUopFraction(EV, 2) * EV("IDQ.MS_UOPS", 2) / SLOTS(EV, 2)
            self.thresh = (self.val > 0.05)
        except ZeroDivisionError:
            print "MicroSequencer zero division"
            self.val = 0
            self.thresh = False
        return self.val

# Schedule


class Setup:
    def __init__(self, r):
        o = dict()
        n = FrontendBound() ; r.run(n) ; o["FrontendBound"] = n
        n = FrontendLatency() ; r.run(n) ; o["FrontendLatency"] = n
        n = ITLBmisses() ; r.run(n) ; o["ITLBmisses"] = n
        n = DSBswitches() ; r.run(n) ; o["DSBswitches"] = n
        n = LCP() ; r.run(n) ; o["LCP"] = n
        n = MSswitches() ; r.run(n) ; o["MSswitches"] = n
        n = FrontendBandwidth() ; r.run(n) ; o["FrontendBandwidth"] = n
        n = MITE() ; r.run(n) ; o["MITE"] = n
        n = DSB() ; r.run(n) ; o["DSB"] = n
        n = LSD() ; r.run(n) ; o["LSD"] = n
        n = BadSpeculation() ; r.run(n) ; o["BadSpeculation"] = n
        n = Backend_Bound() ; r.run(n) ; o["Backend_Bound"] = n
        n = Retiring() ; r.run(n) ; o["Retiring"] = n
        n = BASE() ; r.run(n) ; o["BASE"] = n
        n = MicroSequencer() ; r.run(n) ; o["MicroSequencer"] = n

        # parents
        o["FrontendLatency"].parent = o["FrontendBound"]
        o["ITLBmisses"].parent = o["FrontendLatency"]
        o["DSBswitches"].parent = o["FrontendLatency"]
        o["LCP"].parent = o["FrontendLatency"]
        o["MSswitches"].parent = o["FrontendLatency"]
        o["FrontendBandwidth"].parent = o["FrontendBound"]
        o["MITE"].parent = o["FrontendBandwidth"]
        o["DSB"].parent = o["FrontendBandwidth"]
        o["LSD"].parent = o["FrontendBandwidth"]
        o["BASE"].parent = o["Retiring"]
        o["MicroSequencer"].parent = o["Retiring"]

        # references between groups

        o["FrontendBandwidth"].FrontendBound = o["FrontendBound"]
        o["FrontendBandwidth"].FrontendLatency = o["FrontendLatency"]
        o["Backend_Bound"].FrontendBound = o["FrontendBound"]
        o["Backend_Bound"].BadSpeculation = o["BadSpeculation"]
        o["Backend_Bound"].Retiring = o["Retiring"]
        o["BASE"].Retiring = o["Retiring"]
        o["BASE"].MicroSequencer = o["MicroSequencer"]
