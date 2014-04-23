
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

def CLKS(EV, level):
    return EV("CPU_CLK_UNHALTED.THREAD", level)
# Floating Point Operations Count
def FLOP_count(EV, level):
    return ( 1 *(EV("FP_COMP_OPS_EXE.SSE_SCALAR_SINGLE", level) + EV("FP_COMP_OPS_EXE.SSE_SCALAR_DOUBLE", level))+ 2 * EV("FP_COMP_OPS_EXE.SSE_PACKED_DOUBLE", level) + 4 *(EV("FP_COMP_OPS_EXE.SSE_PACKED_SINGLE", level) + EV("SIMD_FP_256.PACKED_DOUBLE", level))+ 8 * EV("SIMD_FP_256.PACKED_SINGLE", level) )
def RetireUopFraction(EV, level):
    return EV("UOPS_RETIRED.RETIRE_SLOTS", level) / EV("UOPS_ISSUED.ANY", level)
def SLOTS(EV, level):
    return PipelineWidth * CLKS(EV, level)
# Instructions Per Cycle
def IPC(EV, level):
    return EV("INST_RETIRED.ANY", level) / CLKS(EV, level)
# Uops Per Instruction
def UPI(EV, level):
    return EV("UOPS_RETIRED.RETIRE_SLOTS", level) / EV("INST_RETIRED.ANY", level)
# Instruction per taken branch
def InstPerTakenBranch(EV, level):
    return EV("INST_RETIRED.ANY", level) / EV("BR_INST_RETIRED.NEAR_TAKEN", level)
# Fraction of Uops delivered by the DSB (decoded instructions cache)
def DSBCoverage(EV, level):
    return ( EV("IDQ.DSB_UOPS", level) + EV("LSD.UOPS", level))/(EV("IDQ.DSB_UOPS", level) + EV("LSD.UOPS", level) + EV("IDQ.MITE_UOPS", level) + EV("IDQ.MS_UOPS", level) )
# Memory-Level-Parallelism (avg L1 miss demand load when there is at least 1 such miss)
def MLP(EV, level):
    return EV("L1D_PEND_MISS.PENDING", level) / EV("L1D_PEND_MISS.PENDING_CYCLES", level)
# Average Frequency Utilization relative nominal frequency
def TurboUtilization(EV, level):
    return CLKS(EV, level) / EV("CPU_CLK_UNHALTED.REF_TSC", level)

# Event groups


class FrontendBound:
    name = "FrontendBound"
    domain = "Slots"
    area = "FE"
    desc = """
This category reflects slots where the Frontend of the processor undersupplies
its Backend. Frontend denotes the first portion of pipeline responsible to
fetch micro-ops which the Backend can execute. Within the Frontend, a branch
predictor predicts the next address to fetch, cache-lines are fetched from
memory, parsed into instructions, and lastly decoded into micro-ops. The
purpose of the Frontend cluster is to deliver uops to Backend whenever the
latter can accept them. For example, stalls due to instruction-cache misses
would be categorized under Frontend Bound."""
    level = 1
    def compute(self, EV):
        try:
            self.val = EV("IDQ_UOPS_NOT_DELIVERED.CORE", 1)/ SLOTS(EV, 1 )
            self.thresh = (self.val > 0.2)
        except ZeroDivisionError:
            #print "FrontendBound zero division"
            self.val = 0
            self.thresh = False
        return self.val

class FrontendLatency:
    name = "Frontend Latency"
    domain = "Slots"
    area = "FE"
    desc = """
This metric represents slots fraction CPU was stalled due to Frontend latency
issues.  For example, instruction-cache misses, iTLB misses or fetch stalls
after a branch missprediction are categorized under Frontend Latency. In such
cases the Frontend eventually delivers no uops for some period."""
    level = 2
    def compute(self, EV):
        try:
            self.val = PipelineWidth * EV("IDQ_UOPS_NOT_DELIVERED.CYCLES_0_UOPS_DELIV.CORE", 2)/ SLOTS(EV, 2 )
            self.thresh = (self.val > 0.15) and self.parent.thresh
        except ZeroDivisionError:
            #print "FrontendLatency zero division"
            self.val = 0
            self.thresh = False
        return self.val

class ITLBmisses:
    name = "ITLB misses"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents cycles fraction CPU was stalled due to instruction TLB
misses. Using large code pages may be considered here."""
    level = 3
    def compute(self, EV):
        try:
            self.val = EV("ITLB_MISSES.WALK_DURATION", 3)/ CLKS(EV, 3 )
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            #print "ITLBmisses zero division"
            self.val = 0
            self.thresh = False
        return self.val

class DSBswitches:
    name = "DSB switches"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents cycles fraction CPU was stalled due to switches from
DSB to MITE pipelines. Optimizing for better DSB hit rate may be considered."""
    level = 3
    def compute(self, EV):
        try:
            self.val = EV("DSB2MITE_SWITCHES.PENALTY_CYCLES", 3)/ CLKS(EV, 3 )
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            #print "DSBswitches zero division"
            self.val = 0
            self.thresh = False
        return self.val

class LCP:
    name = "LCP"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents cycles fraction CPU was stalled due to Length Changing
Prefixes (LCPs). Using proper compiler flags or Intel Compiler by default will
certainly avoid this."""
    level = 3
    def compute(self, EV):
        try:
            self.val = EV("ILD_STALL.LCP", 3)/ CLKS(EV, 3 )
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            #print "LCP zero division"
            self.val = 0
            self.thresh = False
        return self.val

class MSswitches:
    name = "MS switches"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents cycles fraction CPU was stalled due to switches of uop
delivery to the Microcode Sequencer (MS). Commonly used instructions are
optimized for delivery by the DSB or MITE pipelines. The MS is designated to
deliver long uop flows required by CISC instructions like CPUID, or uncommon
conditions like Floating Point Assists when dealing with Denormals."""
    level = 3
    def compute(self, EV):
        try:
            self.val = MS_SWITCHES_COST * EV("IDQ.MS_SWITCHES", 3)/ CLKS(EV, 3 )
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            #print "MSswitches zero division"
            self.val = 0
            self.thresh = False
        return self.val

class FrontendBandwidth:
    name = "Frontend Bandwidth"
    domain = "Slots"
    area = "FE"
    desc = """
This metric represents slots fraction CPU was stalled due to Frontend
bandwidth issues.  For example, inefficiencies at the instruction decoders, or
code restrictions for caching in the DSB (decoded uops cache) are categorized
under Frontend Bandwidth. In such cases, the Frontend typically delivers non-
optimal amount of uops to the Backend."""
    level = 2
    def compute(self, EV):
        try:
            self.val = self.FrontendBound.compute(EV)- self.FrontendLatency.compute(EV )
            self.thresh = (self.val > 0.1) & (IPC(EV, 2) > 2.0) and self.parent.thresh
        except ZeroDivisionError:
            #print "FrontendBandwidth zero division"
            self.val = 0
            self.thresh = False
        return self.val

class MITE:
    name = "MITE"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents cycles fraction in which CPU was likely limited due to
the MITE fetch pipeline.  For example, inefficiencies in the instruction
decoders are categorized here."""
    level = 3
    def compute(self, EV):
        try:
            self.val = ( EV("IDQ.ALL_MITE_CYCLES_ANY_UOPS", 3)- EV("IDQ.ALL_MITE_CYCLES_4_UOPS", 3)) / CLKS(EV, 3 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "MITE zero division"
            self.val = 0
            self.thresh = False
        return self.val

class DSB:
    name = "DSB"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents cycles fraction in which CPU was likely limited due to
DSB (decoded uop cache) fetch pipeline.  For example, inefficient utlilization
of the DSB cache structure or bank conflict when reading from it, are
categorized here."""
    level = 3
    def compute(self, EV):
        try:
            self.val = ( EV("IDQ.ALL_DSB_CYCLES_ANY_UOPS", 3)- EV("IDQ.ALL_DSB_CYCLES_4_UOPS", 3)) / CLKS(EV, 3 )
            self.thresh = (self.val > 0.3) and self.parent.thresh
        except ZeroDivisionError:
            #print "DSB zero division"
            self.val = 0
            self.thresh = False
        return self.val

class LSD:
    name = "LSD"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents cycles fraction in which CPU was likely limited due to
LSD (Loop Stream Detector) unit.  LSD typically does well sustaining Uop
supply. However, in some rare cases, optimal uop-delivery could not be reached
for small loops whose size (in terms of number of uops) does not suit well the
LSD structure."""
    level = 3
    def compute(self, EV):
        try:
            self.val = ( EV("LSD.CYCLES_ACTIVE", 3)- EV("LSD.CYCLES_4_UOPS", 3)) / CLKS(EV, 3 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "LSD zero division"
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
speculation. For example, wasted work due to miss-predicted branches are
categorized under Bad Speculation category"""
    level = 1
    def compute(self, EV):
        try:
            self.val = ( EV("UOPS_ISSUED.ANY", 1)- EV("UOPS_RETIRED.RETIRE_SLOTS", 1)+ PipelineWidth * EV("INT_MISC.RECOVERY_CYCLES", 1)) / SLOTS(EV, 1 )
            self.thresh = (self.val > 0.1)
        except ZeroDivisionError:
            #print "BadSpeculation zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Backend_Bound:
    name = "Backend_Bound"
    domain = "Slots"
    area = "BE"
    desc = """
This category reflects slots where no uops are being delivered due to a lack
of required resources for accepting more uops in the Backend of the pipeline.
Backend describes the portion of the pipeline where the out-of-order scheduler
dispatches ready uops into their respective execution units, and once
completed these uops get retired according to program order. For example,
stalls due to data-cache misses or stalls due to the divider unit being
overloaded are both categorized under Backend Bound."""
    level = 1
    def compute(self, EV):
        try:
            self.val = 1 -(self.FrontendBound.compute(EV)+ self.BadSpeculation.compute(EV)+ self.Retiring.compute(EV))
            self.thresh = (self.val > 0.2)
        except ZeroDivisionError:
            #print "Backend_Bound zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Retiring:
    name = "Retiring"
    domain = "Slots"
    area = "RET"
    desc = """
This category reflects slots utilized by useful work i.e. allocated uops that
eventually get retired. Ideally, all pipeline slots would be attributed to the
Retiring category.  Retiring of 100% would indicate the maximum 4 uops retired
per cycle has been achieved.  Maximizing Retiring typically increases the
Instruction-Per-Cycle metric. Note that a high Retiring value does not
necessary mean there is no room for more performance.  For example, Microcode
assists are categorized under Retiring. They hurt performance and can often be
avoided.  A high Retiring value for non-vectorized code may be a good hint for
programmer to consider vectorizing his code.  Doing so essentially lets more
computations be done without significantly increasing number of instructions
thus improving the performance."""
    level = 1
    def compute(self, EV):
        try:
            self.val = EV("UOPS_RETIRED.RETIRE_SLOTS", 1)/ SLOTS(EV, 1 )
            self.thresh = (self.val > 0.7) | self.MicroSequencer.thresh
        except ZeroDivisionError:
            #print "Retiring zero division"
            self.val = 0
            self.thresh = False
        return self.val

class BASE:
    name = "BASE"
    domain = "Slots"
    area = "RET"
    desc = """
This metric represents slots fraction CPU was retiring uops not originated
from the microcode-sequencer. This correlates with total number of
instructions used by the program. A uops-per-instruction ratio of 1 should be
expected. A high Retiring value for non-vectorized code is typically a good
hint for programmer to pursue vectorizing his code, which can reduce
instructions hence this bucket."""
    level = 2
    def compute(self, EV):
        try:
            self.val = self.Retiring.compute(EV)- self.MicroSequencer.compute(EV )
            self.thresh = (self.val > 0.6) and self.parent.thresh
        except ZeroDivisionError:
            #print "BASE zero division"
            self.val = 0
            self.thresh = False
        return self.val

class MicroSequencer:
    name = "MicroSequencer"
    domain = "Slots"
    area = "RET"
    desc = """
This metric represents slots fraction CPU was retiring uops fetched by the
Microcode Sequencer (MS) ROM.  The MS is used for CISC instructions not fully
decoded by the default decoders (like repeat move strings), or by microcode
assists used to address some operation modes (like in Floating Point assists)."""
    level = 2
    def compute(self, EV):
        try:
            self.val = RetireUopFraction(EV, 2)* EV("IDQ.MS_UOPS", 2)/ SLOTS(EV, 2 )
            self.thresh = (self.val > 0.05)
        except ZeroDivisionError:
            #print "MicroSequencer zero division"
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

class Metric_UPI:
    name = "UPI"
    desc = """
Uops Per Instruction"""

    def compute(self, EV):
        try:
            self.val = UPI(EV, 0)
        except ZeroDivisionError:
            print "UPI zero division"
            self.val = 0

class Metric_InstPerTakenBranch:
    name = "InstPerTakenBranch"
    desc = """
Instruction per taken branch"""

    def compute(self, EV):
        try:
            self.val = InstPerTakenBranch(EV, 0)
        except ZeroDivisionError:
            print "InstPerTakenBranch zero division"
            self.val = 0

class Metric_DSBCoverage:
    name = "DSBCoverage"
    desc = """
Fraction of Uops delivered by the DSB (decoded instructions cache)"""

    def compute(self, EV):
        try:
            self.val = DSBCoverage(EV, 0)
        except ZeroDivisionError:
            print "DSBCoverage zero division"
            self.val = 0

class Metric_MLP:
    name = "MLP"
    desc = """
Memory-Level-Parallelism (avg L1 miss demand load when there is at least 1
such miss)"""

    def compute(self, EV):
        try:
            self.val = MLP(EV, 0)
        except ZeroDivisionError:
            print "MLP zero division"
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
        o["Retiring"].MicroSequencer = o["MicroSequencer"]
        o["BASE"].Retiring = o["Retiring"]
        o["BASE"].MicroSequencer = o["MicroSequencer"]

        # siblings cross-tree

        o["FrontendBound"].sibling = None
        o["FrontendLatency"].sibling = None
        o["ITLBmisses"].sibling = None
        o["DSBswitches"].sibling = None
        o["LCP"].sibling = None
        o["MSswitches"].sibling = o["MicroSequencer"]
        o["FrontendBandwidth"].sibling = None
        o["MITE"].sibling = None
        o["DSB"].sibling = None
        o["LSD"].sibling = None
        o["BadSpeculation"].sibling = o["BranchResteers"]
        o["Backend_Bound"].sibling = None
        o["Retiring"].sibling = None
        o["BASE"].sibling = None
        o["MicroSequencer"].sibling = o["MSswitches"]

        # sampling events (experimential)

        o["FrontendBound"].sample = []
        o["FrontendLatency"].sample = []
        o["ITLBmisses"].sample = []
        o["DSBswitches"].sample = []
        o["LCP"].sample = []
        o["MSswitches"].sample = []
        o["FrontendBandwidth"].sample = []
        o["MITE"].sample = []
        o["DSB"].sample = []
        o["LSD"].sample = []
        o["BadSpeculation"].sample = []
        o["Backend_Bound"].sample = []
        o["Retiring"].sample = []
        o["BASE"].sample = []
        o["MicroSequencer"].sample = []

        # user visible metrics

        n = Metric_IPC() ; r.metric(n)
        n = Metric_UPI() ; r.metric(n)
        n = Metric_InstPerTakenBranch() ; r.metric(n)
        n = Metric_DSBCoverage() ; r.metric(n)
        n = Metric_MLP() ; r.metric(n)
        n = Metric_TurboUtilization() ; r.metric(n)
