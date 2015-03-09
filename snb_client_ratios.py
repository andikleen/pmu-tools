
#
# auto generated TopDown 2.9 description for Intel 2nd gen Core (code named SandyBridge)
# Please see http://ark.intel.com for more details on these CPUs.
#
# References:
# http://halobates.de/blog/p/262
# https://sites.google.com/site/analysismethods/yasin-pubs
#

# Helpers

print_error = lambda msg: False

smt_enabled = False

# Constants

Pipeline_Width = 4
L2_Store_Latency = 9
Mem_L3_Weight = 7
Mem_STLB_Hit_Cost = 7
Mem_SFB_Cost = 13
Mem_4K_Alias_Cost = 7
Mem_XSNP_HitM_Cost = 60
MEM_XSNP_Hit_Cost = 43
MEM_XSNP_None_Cost = 29
Mem_Local_DRAM_Cost = 200
Mem_Remote_DRAM_Cost = 310
Mem_Remote_HitM_Cost = 200
Mem_Remote_Fwd_Cost = 180
MS_Switches_Cost = 3
OneMillion = 1000000
Energy_Unit = 15.6

# Aux. formulas


# Floating Point Operations Count
def FLOP_Count(EV, level):
    return (1 *(EV("FP_COMP_OPS_EXE.X87", level) + EV("FP_COMP_OPS_EXE.SSE_SCALAR_SINGLE", level) + EV("FP_COMP_OPS_EXE.SSE_SCALAR_DOUBLE", level)) + 2 * EV("FP_COMP_OPS_EXE.SSE_PACKED_DOUBLE", level) + 4 *(EV("FP_COMP_OPS_EXE.SSE_PACKED_SINGLE", level) + EV("SIMD_FP_256.PACKED_DOUBLE", level)) + 8 * EV("SIMD_FP_256.PACKED_SINGLE", level))

def Recovery_Cycles(EV, level):
    return (EV("INT_MISC.RECOVERY_CYCLES:amt1", level) / 2) if smt_enabled else EV("INT_MISC.RECOVERY_CYCLES", level)

def L1D_Miss_Cycles(EV, level):
    return (EV("L1D_PEND_MISS.PENDING_CYCLES:amt1", level) / 2) if smt_enabled else EV("L1D_PEND_MISS.PENDING_CYCLES", level)

def SQ_Full_Cycles(EV, level):
    return (EV("OFFCORE_REQUESTS_BUFFER.SQ_FULL", level) / 2) if smt_enabled else EV("OFFCORE_REQUESTS_BUFFER.SQ_FULL", level)

def ITLB_Miss_Cycles(EV, level):
    return (Mem_STLB_Hit_Cost * EV("ITLB_MISSES.STLB_HIT", level) + EV("ITLB_MISSES.WALK_DURATION", level))

def ORO_Demand_DRD_C1(EV, level):
    return EV(lambda EV , level : min(EV("CPU_CLK_UNHALTED.THREAD", level) , EV("OFFCORE_REQUESTS_OUTSTANDING.CYCLES_WITH_DEMAND_DATA_RD", level)) , level )

def ORO_Demand_DRD_C6(EV, level):
    return EV(lambda EV , level : min(EV("CPU_CLK_UNHALTED.THREAD", level) , EV("OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD:c6", level)) , level )

def ORO_Demand_RFO_C1(EV, level):
    return EV(lambda EV , level : min(EV("CPU_CLK_UNHALTED.THREAD", level) , EV("OFFCORE_REQUESTS_OUTSTANDING.CYCLES_WITH_DEMAND_RFO", level)) , level )

def Store_L2_Hit_Cycles(EV, level):
    return 0

def Cycles_False_Sharing_Client(EV, level):
    return Mem_XSNP_HitM_Cost *(EV("MEM_LOAD_UOPS_LLC_HIT_RETIRED.XSNP_HITM", level) + EV("OFFCORE_RESPONSE.DEMAND_RFO.LLC_HIT.HITM_OTHER_CORE", level))

def Mem_Lock_St_Fraction(EV, level):
    return EV("MEM_UOPS_RETIRED.LOCK_LOADS", level) / EV("MEM_UOPS_RETIRED.ALL_STORES", level)

def Retire_Uop_Fraction(EV, level):
    return EV("UOPS_RETIRED.RETIRE_SLOTS", level) / EV("UOPS_ISSUED.ANY", level)

def SLOTS(EV, level):
    return Pipeline_Width * CORE_CLKS(EV, level)

def DurationTimeInSeconds(EV, level):
    return 0 if 0 > 0 else(EV("interval-ns", 0) / 1e+09 / 1000 )

# Instructions Per Cycle (per logical thread)
def IPC(EV, level):
    return EV("INST_RETIRED.ANY", level) / CLKS(EV, level)

# Cycles Per Instruction (threaded)
def CPI(EV, level):
    return 1 / IPC(EV, level)

# Instructions Per Cycle (per physical core)
def CoreIPC(EV, level):
    return EV("INST_RETIRED.ANY", level) / CORE_CLKS(EV, level)

# Uops Per Instruction
def UPI(EV, level):
    return EV("UOPS_RETIRED.RETIRE_SLOTS", level) / EV("INST_RETIRED.ANY", level)

# Instruction per taken branch
def IPTB(EV, level):
    return EV("INST_RETIRED.ANY", level) / EV("BR_INST_RETIRED.NEAR_TAKEN", level)

# Branch instructions per taken branch. Can be used to approximate PGO-likelihood for non-loopy codes.
def BPTB(EV, level):
    return EV("BR_INST_RETIRED.ALL_BRANCHES", level) / EV("BR_INST_RETIRED.NEAR_TAKEN", level)

# Fraction of Uops delivered by the DSB (decoded instructions cache)
def DSB_Coverage(EV, level):
    return (EV("IDQ.DSB_UOPS", level) + EV("LSD.UOPS", level)) /(EV("IDQ.DSB_UOPS", level) + EV("LSD.UOPS", level) + EV("IDQ.MITE_UOPS", level) + EV("IDQ.MS_UOPS", level))

# Memory-Level-Parallelism (average number of L1 miss demand load when there is at least 1 such miss)
def MLP(EV, level):
    return EV("L1D_PEND_MISS.PENDING", level) / L1D_Miss_Cycles(EV, level)

# Giga Floating Point Operations Per Second
def GFLOPs(EV, level):
    return FLOP_Count(EV, level) / OneMillion / DurationTimeInSeconds(EV, level) / 1000

# Average Frequency Utilization relative nominal frequency
def Turbo_Utilization(EV, level):
    return CLKS(EV, level) / EV("CPU_CLK_UNHALTED.REF_TSC", level)

# Fraction of cycles where the core's Page Walker is busy serving iTLB/Load/Store
def Page_Walks_Use(EV, level):
    return (EV("ITLB_MISSES.WALK_DURATION", level) + EV("DTLB_LOAD_MISSES.WALK_DURATION", level) + EV("DTLB_STORE_MISSES.WALK_DURATION", level)) / CORE_CLKS(EV, level)

# PerfMon Event Multiplexing accuracy indicator
def MUX(EV, level):
    return EV("CPU_CLK_UNHALTED.THREAD_P", level) / EV("CPU_CLK_UNHALTED.THREAD", level)

# Per-thread actual clocks
def CLKS(EV, level):
    return EV("CPU_CLK_UNHALTED.THREAD", level)

# Core actual clocks
def CORE_CLKS(EV, level):
    return (EV("CPU_CLK_UNHALTED.THREAD:amt1", level) / 2) if smt_enabled else CLKS(EV, level)

# Run duration time in seconds
def Time(EV, level):
    return DurationTimeInSeconds(EV, level)

# Event groups


class Frontend_Bound:
    name = "Frontend_Bound"
    domain = "Slots"
    area = "FE"
    desc = """
This category reflects slots where the Frontend of the
processor undersupplies its Backend. Frontend denotes the
first portion of pipeline responsible to fetch micro-ops
which the Backend can execute. Within the Frontend, a branch
predictor predicts the next address to fetch, cache-lines
are fetched from memory, parsed into instructions, and
lastly decoded into micro-ops. The purpose of the Frontend
cluster is to deliver uops to Backend whenever the latter
can accept them. For example, stalls due to instruction-
cache misses would be categorized under Frontend Bound."""
    level = 1
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    def compute(self, EV):
        try:
            self.val = EV("IDQ_UOPS_NOT_DELIVERED.CORE", 1) / SLOTS(EV, 1 )
            self.thresh = (self.val > 0.2)
        except ZeroDivisionError:
            print_error("Frontend_Bound zero division")
            self.errcount += 1
            self.val = 0
            self.thresh = False
        return self.val

class Frontend_Latency:
    name = "Frontend_Latency"
    domain = "Slots"
    area = "FE"
    desc = """
This metric represents slots fraction CPU was stalled due to
Frontend latency issues.  For example, instruction-cache
misses, iTLB misses or fetch stalls after a branch
misprediction are categorized under Frontend Latency. In
such cases the Frontend eventually delivers no uops for some
period."""
    level = 2
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    def compute(self, EV):
        try:
            self.val = Pipeline_Width * EV("IDQ_UOPS_NOT_DELIVERED.CYCLES_0_UOPS_DELIV.CORE", 2) / SLOTS(EV, 2 )
            self.thresh = (self.val > 0.15) and self.parent.thresh
        except ZeroDivisionError:
            print_error("Frontend_Latency zero division")
            self.errcount += 1
            self.val = 0
            self.thresh = False
        return self.val

class ITLB_Misses:
    name = "ITLB_Misses"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents cycles fraction CPU was stalled due
to instruction TLB misses. Using large code pages may be
considered here."""
    level = 3
    htoff = False
    sample = ['ITLB_MISSES.WALK_COMPLETED']
    errcount = 0
    sibling = None
    def compute(self, EV):
        try:
            self.val = ITLB_Miss_Cycles(EV, 3) / CLKS(EV, 3 )
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            print_error("ITLB_Misses zero division")
            self.errcount += 1
            self.val = 0
            self.thresh = False
        return self.val

class DSB_Switches:
    name = "DSB_Switches"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents cycles fraction CPU was stalled due
to switches from DSB to MITE pipelines. Optimizing for
better DSB hit rate may be considered."""
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    def compute(self, EV):
        try:
            self.val = EV("DSB2MITE_SWITCHES.PENALTY_CYCLES", 3) / CLKS(EV, 3 )
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            print_error("DSB_Switches zero division")
            self.errcount += 1
            self.val = 0
            self.thresh = False
        return self.val

class LCP:
    name = "LCP"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents cycles fraction CPU was stalled due
to Length Changing Prefixes (LCPs). Using proper compiler
flags or Intel Compiler by default will certainly avoid
this."""
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    def compute(self, EV):
        try:
            self.val = EV("ILD_STALL.LCP", 3) / CLKS(EV, 3 )
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            print_error("LCP zero division")
            self.errcount += 1
            self.val = 0
            self.thresh = False
        return self.val

class MS_Switches:
    name = "MS_Switches"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents cycles fraction CPU was stalled due
to switches of uop delivery to the Microcode Sequencer (MS).
Commonly used instructions are optimized for delivery by the
DSB or MITE pipelines. The MS is designated to deliver long
uop flows required by CISC instructions like CPUID, or
uncommon conditions like Floating Point Assists when dealing
with Denormals."""
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    def compute(self, EV):
        try:
            self.val = MS_Switches_Cost * EV("IDQ.MS_SWITCHES", 3) / CLKS(EV, 3 )
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            print_error("MS_Switches zero division")
            self.errcount += 1
            self.val = 0
            self.thresh = False
        return self.val

class Frontend_Bandwidth:
    name = "Frontend_Bandwidth"
    domain = "Slots"
    area = "FE"
    desc = """
This metric represents slots fraction CPU was stalled due to
Frontend bandwidth issues.  For example, inefficiencies at
the instruction decoders, or code restrictions for caching
in the DSB (decoded uops cache) are categorized under
Frontend Bandwidth. In such cases, the Frontend typically
delivers non-optimal amount of uops to the Backend."""
    level = 2
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    def compute(self, EV):
        try:
            self.val = self.Frontend_Bound.compute(EV) - self.Frontend_Latency.compute(EV )
            self.thresh = (self.val > 0.1) & (IPC(EV, 2) > 2.0) and self.parent.thresh
        except ZeroDivisionError:
            print_error("Frontend_Bandwidth zero division")
            self.errcount += 1
            self.val = 0
            self.thresh = False
        return self.val

class MITE:
    name = "MITE"
    domain = "CoreClocks"
    area = "FE"
    desc = """
This metric represents Core cycles fraction in which CPU was
likely limited due to the MITE fetch pipeline.  For example,
inefficiencies in the instruction decoders are categorized
here."""
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    def compute(self, EV):
        try:
            self.val = (EV("IDQ.ALL_MITE_CYCLES_ANY_UOPS", 3) - EV("IDQ.ALL_MITE_CYCLES_4_UOPS", 3)) / CORE_CLKS(EV, 3 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            print_error("MITE zero division")
            self.errcount += 1
            self.val = 0
            self.thresh = False
        return self.val

class DSB:
    name = "DSB"
    domain = "CoreClocks"
    area = "FE"
    desc = """
This metric represents Core cycles fraction in which CPU was
likely limited due to DSB (decoded uop cache) fetch
pipeline.  For example, inefficient utilization of the DSB
cache structure or bank conflict when reading from it, are
categorized here."""
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    def compute(self, EV):
        try:
            self.val = (EV("IDQ.ALL_DSB_CYCLES_ANY_UOPS", 3) - EV("IDQ.ALL_DSB_CYCLES_4_UOPS", 3)) / CORE_CLKS(EV, 3 )
            self.thresh = (self.val > 0.3) and self.parent.thresh
        except ZeroDivisionError:
            print_error("DSB zero division")
            self.errcount += 1
            self.val = 0
            self.thresh = False
        return self.val

class LSD:
    name = "LSD"
    domain = "CoreClocks"
    area = "FE"
    desc = """
This metric represents Core cycles fraction in which CPU was
likely limited due to LSD (Loop Stream Detector) unit.  LSD
typically does well sustaining Uop supply. However, in some
rare cases, optimal uop-delivery could not be reached for
small loops whose size (in terms of number of uops) does not
suit well the LSD structure."""
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    def compute(self, EV):
        try:
            self.val = (EV("LSD.CYCLES_ACTIVE", 3) - EV("LSD.CYCLES_4_UOPS", 3)) / CORE_CLKS(EV, 3 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            print_error("LSD zero division")
            self.errcount += 1
            self.val = 0
            self.thresh = False
        return self.val

class Bad_Speculation:
    name = "Bad_Speculation"
    domain = "Slots"
    area = "BAD"
    desc = """
This category reflects slots wasted due to incorrect
speculations, which include slots used to allocate uops that
do not eventually get retired and slots for which allocation
was blocked due to recovery from earlier incorrect
speculation. For example, wasted work due to miss-predicted
branches are categorized under Bad Speculation category"""
    level = 1
    htoff = False
    sample = ['INT_MISC.RECOVERY_CYCLES']
    errcount = 0
    sibling = None
    def compute(self, EV):
        try:
            self.val = (EV("UOPS_ISSUED.ANY", 1) - EV("UOPS_RETIRED.RETIRE_SLOTS", 1) + Pipeline_Width * Recovery_Cycles(EV, 1)) / SLOTS(EV, 1 )
            self.thresh = (self.val > 0.1)
        except ZeroDivisionError:
            print_error("Bad_Speculation zero division")
            self.errcount += 1
            self.val = 0
            self.thresh = False
        return self.val

class Backend_Bound:
    name = "Backend_Bound"
    domain = "Slots"
    area = "BE"
    desc = """
This category reflects slots where no uops are being
delivered due to a lack of required resources for accepting
more uops in the Backend of the pipeline. Backend describes
the portion of the pipeline where the out-of-order scheduler
dispatches ready uops into their respective execution units,
and once completed these uops get retired according to
program order. For example, stalls due to data-cache misses
or stalls due to the divider unit being overloaded are both
categorized under Backend Bound."""
    level = 1
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    def compute(self, EV):
        try:
            self.val = 1 -(self.Frontend_Bound.compute(EV) + self.Bad_Speculation.compute(EV) + self.Retiring.compute(EV))
            self.thresh = (self.val > 0.2)
        except ZeroDivisionError:
            print_error("Backend_Bound zero division")
            self.errcount += 1
            self.val = 0
            self.thresh = False
        return self.val

class Retiring:
    name = "Retiring"
    domain = "Slots"
    area = "RET"
    desc = """
This category reflects slots utilized by useful work i.e.
allocated uops that eventually get retired. Ideally, all
pipeline slots would be attributed to the Retiring category.
Retiring of 100% would indicate the maximum 4 uops retired
per cycle has been achieved.  Maximizing Retiring typically
increases the Instruction-Per-Cycle metric. Note that a high
Retiring value does not necessary mean there is no room for
more performance.  For example, Microcode assists are
categorized under Retiring. They hurt performance and can
often be avoided.  A high Retiring value for non-vectorized
code may be a good hint for programmer to consider
vectorizing his code.  Doing so essentially lets more
computations be done without significantly increasing number
of instructions thus improving the performance."""
    level = 1
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    def compute(self, EV):
        try:
            self.val = EV("UOPS_RETIRED.RETIRE_SLOTS", 1) / SLOTS(EV, 1 )
            self.thresh = (self.val > 0.7) | self.Microcode_Sequencer.thresh
        except ZeroDivisionError:
            print_error("Retiring zero division")
            self.errcount += 1
            self.val = 0
            self.thresh = False
        return self.val

class Base:
    name = "Base"
    domain = "Slots"
    area = "RET"
    desc = """
This metric represents slots fraction where the CPU was
retiring uops not originated from the microcode-sequencer.
This correlates with total number of instructions used by
the program. A uops-per-instruction ratio of 1 should be
expected. While this is the most desirable of the top 4
categories, high values may still indicate areas for
improvement. If possible focus on techniques that reduce
instruction count or result in more efficient instructions
generation such as vectorization."""
    level = 2
    htoff = False
    sample = ['INST_RETIRED.PREC_DIST']
    errcount = 0
    sibling = None
    def compute(self, EV):
        try:
            self.val = self.Retiring.compute(EV) - self.Microcode_Sequencer.compute(EV )
            self.thresh = (self.val > 0.6) and self.parent.thresh
        except ZeroDivisionError:
            print_error("Base zero division")
            self.errcount += 1
            self.val = 0
            self.thresh = False
        return self.val

class Microcode_Sequencer:
    name = "Microcode_Sequencer"
    domain = "Slots"
    area = "RET"
    desc = """
This metric represents slots fraction CPU was retiring uops
fetched by the Microcode Sequencer (MS) ROM.  The MS is used
for CISC instructions not fully decoded by the default
decoders (like repeat move strings), or by microcode assists
used to address some operation modes (like in Floating Point
assists)."""
    level = 2
    htoff = False
    sample = ['IDQ.MS_UOPS']
    errcount = 0
    sibling = None
    def compute(self, EV):
        try:
            self.val = Retire_Uop_Fraction(EV, 2)* EV("IDQ.MS_UOPS", 2) / SLOTS(EV, 2 )
            self.thresh = (self.val > 0.05)
        except ZeroDivisionError:
            print_error("Microcode_Sequencer zero division")
            self.errcount += 1
            self.val = 0
            self.thresh = False
        return self.val

class Metric_IPC:
    name = "IPC"
    desc = """
Instructions Per Cycle (per logical thread)"""
    domain = "Metric"
    maxval = 5
    errcount = 0

    def compute(self, EV):
        try:
            self.val = IPC(EV, 0)
        except ZeroDivisionError:
            print_error("IPC zero division")
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

class Metric_CoreIPC:
    name = "CoreIPC"
    desc = """
Instructions Per Cycle (per physical core)"""
    domain = "CoreMetric"
    maxval = 2
    errcount = 0

    def compute(self, EV):
        try:
            self.val = CoreIPC(EV, 0)
        except ZeroDivisionError:
            print_error("CoreIPC zero division")
            self.errcount += 1
            self.val = 0

class Metric_UPI:
    name = "UPI"
    desc = """
Uops Per Instruction"""
    domain = "Metric"
    maxval = 2
    errcount = 0

    def compute(self, EV):
        try:
            self.val = UPI(EV, 0)
        except ZeroDivisionError:
            print_error("UPI zero division")
            self.errcount += 1
            self.val = 0

class Metric_IPTB:
    name = "IPTB"
    desc = """
Instruction per taken branch"""
    domain = "Metric"
    maxval = 0
    errcount = 0

    def compute(self, EV):
        try:
            self.val = IPTB(EV, 0)
        except ZeroDivisionError:
            print_error("IPTB zero division")
            self.errcount += 1
            self.val = 0

class Metric_BPTB:
    name = "BPTB"
    desc = """
Branch instructions per taken branch. Can be used to
approximate PGO-likelihood for non-loopy codes."""
    domain = "Metric"
    maxval = 0
    errcount = 0

    def compute(self, EV):
        try:
            self.val = BPTB(EV, 0)
        except ZeroDivisionError:
            print_error("BPTB zero division")
            self.errcount += 1
            self.val = 0

class Metric_DSB_Coverage:
    name = "DSB_Coverage"
    desc = """
Fraction of Uops delivered by the DSB (decoded instructions
cache)"""
    domain = "Metric"
    maxval = 1
    errcount = 0

    def compute(self, EV):
        try:
            self.val = DSB_Coverage(EV, 0)
        except ZeroDivisionError:
            print_error("DSB_Coverage zero division")
            self.errcount += 1
            self.val = 0

class Metric_MLP:
    name = "MLP"
    desc = """
Memory-Level-Parallelism (average number of L1 miss demand
load when there is at least 1 such miss)"""
    domain = "Metric"
    maxval = 10
    errcount = 0

    def compute(self, EV):
        try:
            self.val = MLP(EV, 0)
        except ZeroDivisionError:
            print_error("MLP zero division")
            self.errcount += 1
            self.val = 0

class Metric_GFLOPs:
    name = "GFLOPs"
    desc = """
Giga Floating Point Operations Per Second"""
    domain = "Metric"
    maxval = 100
    errcount = 0

    def compute(self, EV):
        try:
            self.val = GFLOPs(EV, 0)
        except ZeroDivisionError:
            print_error("GFLOPs zero division")
            self.errcount += 1
            self.val = 0

class Metric_Turbo_Utilization:
    name = "Turbo_Utilization"
    desc = """
Average Frequency Utilization relative nominal frequency"""
    domain = "Metric"
    maxval = 10
    errcount = 0

    def compute(self, EV):
        try:
            self.val = Turbo_Utilization(EV, 0)
        except ZeroDivisionError:
            print_error("Turbo_Utilization zero division")
            self.errcount += 1
            self.val = 0

class Metric_Page_Walks_Use:
    name = "Page_Walks_Use"
    desc = """
Fraction of cycles where the core's Page Walker is busy
serving iTLB/Load/Store"""
    domain = "CoreClocks"
    maxval = 0
    errcount = 0

    def compute(self, EV):
        try:
            self.val = Page_Walks_Use(EV, 0)
        except ZeroDivisionError:
            print_error("Page_Walks_Use zero division")
            self.errcount += 1
            self.val = 0

class Metric_MUX:
    name = "MUX"
    desc = """
PerfMon Event Multiplexing accuracy indicator"""
    domain = "Clocks"
    maxval = 0
    errcount = 0

    def compute(self, EV):
        try:
            self.val = MUX(EV, 0)
        except ZeroDivisionError:
            print_error("MUX zero division")
            self.errcount += 1
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

class Metric_CORE_CLKS:
    name = "CORE_CLKS"
    desc = """
Core actual clocks"""
    domain = "CoreClocks"
    maxval = 0
    errcount = 0

    def compute(self, EV):
        try:
            self.val = CORE_CLKS(EV, 0)
        except ZeroDivisionError:
            print_error("CORE_CLKS zero division")
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

# Schedule


class Setup:
    def __init__(self, r):
        o = dict()
        n = Frontend_Bound() ; r.run(n) ; o["Frontend_Bound"] = n
        n = Frontend_Latency() ; r.run(n) ; o["Frontend_Latency"] = n
        n = ITLB_Misses() ; r.run(n) ; o["ITLB_Misses"] = n
        n = DSB_Switches() ; r.run(n) ; o["DSB_Switches"] = n
        n = LCP() ; r.run(n) ; o["LCP"] = n
        n = MS_Switches() ; r.run(n) ; o["MS_Switches"] = n
        n = Frontend_Bandwidth() ; r.run(n) ; o["Frontend_Bandwidth"] = n
        n = MITE() ; r.run(n) ; o["MITE"] = n
        n = DSB() ; r.run(n) ; o["DSB"] = n
        n = LSD() ; r.run(n) ; o["LSD"] = n
        n = Bad_Speculation() ; r.run(n) ; o["Bad_Speculation"] = n
        n = Backend_Bound() ; r.run(n) ; o["Backend_Bound"] = n
        n = Retiring() ; r.run(n) ; o["Retiring"] = n
        n = Base() ; r.run(n) ; o["Base"] = n
        n = Microcode_Sequencer() ; r.run(n) ; o["Microcode_Sequencer"] = n

        # parents

        o["Frontend_Latency"].parent = o["Frontend_Bound"]
        o["ITLB_Misses"].parent = o["Frontend_Latency"]
        o["DSB_Switches"].parent = o["Frontend_Latency"]
        o["LCP"].parent = o["Frontend_Latency"]
        o["MS_Switches"].parent = o["Frontend_Latency"]
        o["Frontend_Bandwidth"].parent = o["Frontend_Bound"]
        o["MITE"].parent = o["Frontend_Bandwidth"]
        o["DSB"].parent = o["Frontend_Bandwidth"]
        o["LSD"].parent = o["Frontend_Bandwidth"]
        o["Base"].parent = o["Retiring"]
        o["Microcode_Sequencer"].parent = o["Retiring"]

        # references between groups

        o["Frontend_Bandwidth"].Frontend_Bound = o["Frontend_Bound"]
        o["Frontend_Bandwidth"].Frontend_Latency = o["Frontend_Latency"]
        o["Backend_Bound"].Frontend_Bound = o["Frontend_Bound"]
        o["Backend_Bound"].Bad_Speculation = o["Bad_Speculation"]
        o["Backend_Bound"].Retiring = o["Retiring"]
        o["Retiring"].Microcode_Sequencer = o["Microcode_Sequencer"]
        o["Base"].Retiring = o["Retiring"]
        o["Base"].Microcode_Sequencer = o["Microcode_Sequencer"]

        # siblings cross-tree

	o["MS_Switches"].sibling = o["Microcode_Sequencer"]
	o["Microcode_Sequencer"].sibling = o["MS_Switches"]

        # user visible metrics

        n = Metric_IPC() ; r.metric(n)
        n = Metric_CPI() ; r.metric(n)
        n = Metric_CoreIPC() ; r.metric(n)
        n = Metric_UPI() ; r.metric(n)
        n = Metric_IPTB() ; r.metric(n)
        n = Metric_BPTB() ; r.metric(n)
        n = Metric_DSB_Coverage() ; r.metric(n)
        n = Metric_MLP() ; r.metric(n)
        n = Metric_GFLOPs() ; r.metric(n)
        n = Metric_Turbo_Utilization() ; r.metric(n)
        n = Metric_Page_Walks_Use() ; r.metric(n)
        n = Metric_MUX() ; r.metric(n)
        n = Metric_CLKS() ; r.metric(n)
        n = Metric_CORE_CLKS() ; r.metric(n)
        n = Metric_Time() ; r.metric(n)
