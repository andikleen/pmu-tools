
#
# auto generated TopDown description for Ivy Bridge
# Please see http://ark.intel.com for more details on these CPUs.
#

smt_enabled = False

# Constants

Pipeline_Width = 4
Mem_L3_Weight = 7
Mem_STLB_Hit_Cost = 7
Mem_SFB_Cost = 13
Mem_4K_Alias_Cost = 7
Mem_XSNP_HitM_Cost = 60
MEM_XSNP_Hit_Cost = 43
MEM_XSNP_None_Cost = 29
MS_Switches_Cost = 3
OneMillion = 1000000

# Aux. formulas

# Floating Point Operations Count
def FLOP_Count(EV, level):
    return ( 1 *(EV("FP_COMP_OPS_EXE.SSE_SCALAR_SINGLE", level) + EV("FP_COMP_OPS_EXE.SSE_SCALAR_DOUBLE", level))+ 2 * EV("FP_COMP_OPS_EXE.SSE_PACKED_DOUBLE", level) + 4 *(EV("FP_COMP_OPS_EXE.SSE_PACKED_SINGLE", level) + EV("SIMD_FP_256.PACKED_DOUBLE", level))+ 8 * EV("SIMD_FP_256.PACKED_SINGLE", level) )
def Recovery_Cycles(EV, level):
    return ( EV("INT_MISC.RECOVERY_CYCLES:amt1", level) / 2)if smt_enabled else EV("INT_MISC.RECOVERY_CYCLES", level)
def Execute_Cycles(EV, level):
    return ( EV("UOPS_EXECUTED.CORE:c1", level) / 2)if smt_enabled else EV("UOPS_EXECUTED.CYCLES_GE_1_UOP_EXEC", level)
def L1D_Miss_Cycles(EV, level):
    return ( EV("L1D_PEND_MISS.PENDING_CYCLES:amt1", level) / 2)if smt_enabled else EV("L1D_PEND_MISS.PENDING_CYCLES", level)
def ITLB_Miss_Cycles(EV, level):
    return ( Mem_STLB_Hit_Cost * EV("ITLB_MISSES.STLB_HIT", level) + EV("ITLB_MISSES.WALK_DURATION", level) )
def Cycles_0_Ports_Utilized(EV, level):
    return ( EV("UOPS_EXECUTED.CORE:i1", level))/ 2 if smt_enabled else(STALLS_TOTAL(EV, level) - EV("RS_EVENTS.EMPTY_CYCLES", level) - EV("ARITH.FPU_DIV_ACTIVE", level) )
def Cycles_1_Port_Utilized(EV, level):
    return ( EV("UOPS_EXECUTED.CORE:c1", level) - EV("UOPS_EXECUTED.CORE:c2", level))/ 2 if smt_enabled else(EV("UOPS_EXECUTED.CYCLES_GE_1_UOP_EXEC", level) - EV("UOPS_EXECUTED.CYCLES_GE_2_UOPS_EXEC", level) )
def Cycles_2_Ports_Utilized(EV, level):
    return ( EV("UOPS_EXECUTED.CORE:c2", level) - EV("UOPS_EXECUTED.CORE:c3", level))/ 2 if smt_enabled else(EV("UOPS_EXECUTED.CYCLES_GE_2_UOPS_EXEC", level) - EV("UOPS_EXECUTED.CYCLES_GE_3_UOPS_EXEC", level) )
def Cycles_3m_Ports_Utilized(EV, level):
    return ( EV("UOPS_EXECUTED.CORE:c3", level) / 2)if smt_enabled else EV("UOPS_EXECUTED.CYCLES_GE_3_UOPS_EXEC", level)
def STALLS_MEM_ANY(EV, level):
    return min(EV("CPU_CLK_UNHALTED.THREAD", level) , EV("CYCLE_ACTIVITY.STALLS_LDM_PENDING", level) )
def STALLS_TOTAL(EV, level):
    return min(EV("CPU_CLK_UNHALTED.THREAD", level) , EV("CYCLE_ACTIVITY.CYCLES_NO_EXECUTE", level) )
def ORO_Demand_DRD_C1(EV, level):
    return min(EV("CPU_CLK_UNHALTED.THREAD", level) , EV("OFFCORE_REQUESTS_OUTSTANDING.CYCLES_WITH_DEMAND_DATA_RD", level) )
def ORO_Demand_DRD_C6(EV, level):
    return min(EV("CPU_CLK_UNHALTED.THREAD", level) , EV("OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD:c6", level) )
def Few_Uops_Executed_Threshold(EV, level):
    return EV("UOPS_EXECUTED.CYCLES_GE_3_UOPS_EXEC", level) if(IPC(EV, level) > 1.25)else EV("UOPS_EXECUTED.CYCLES_GE_2_UOPS_EXEC", level)
def Backend_Bound_At_EXE(EV, level):
    return ( STALLS_TOTAL(EV, level) + EV("UOPS_EXECUTED.CYCLES_GE_1_UOP_EXEC", level) - Few_Uops_Executed_Threshold(EV, level) - EV("RS_EVENTS.EMPTY_CYCLES", level) + EV("RESOURCE_STALLS.SB", level))/ CLKS(EV, level)
def Mem_L3_Hit_Fraction(EV, level):
    return EV("MEM_LOAD_UOPS_RETIRED.LLC_HIT", level) /(EV("MEM_LOAD_UOPS_RETIRED.LLC_HIT", level) + Mem_L3_Weight * EV("MEM_LOAD_UOPS_RETIRED.LLC_MISS", level) )
def Mispred_Clears_Fraction(EV, level):
    return EV("BR_MISP_RETIRED.ALL_BRANCHES", level) /(EV("BR_MISP_RETIRED.ALL_BRANCHES", level) + EV("MACHINE_CLEARS.COUNT", level) )
def Avg_RS_Empty_Period_Clears(EV, level):
    return ( EV("RS_EVENTS.EMPTY_CYCLES", level) - EV("ICACHE.IFETCH_STALL", level))/ EV("RS_EVENTS.EMPTY_END", level)
def Retire_Uop_Fraction(EV, level):
    return EV("UOPS_RETIRED.RETIRE_SLOTS", level) / EV("UOPS_ISSUED.ANY", level)
def SLOTS(EV, level):
    return Pipeline_Width * CLKS1(EV, level)
# Instructions Per Cycle (per physical core)
def IPC(EV, level):
    return EV("INST_RETIRED.ANY", level) / CLKS1(EV, level)
def CPI(EV, level):
    return 1 / IPC(EV, level)
# Uops Per Instruction
def UPI(EV, level):
    return EV("UOPS_RETIRED.RETIRE_SLOTS", level) / EV("INST_RETIRED.ANY", level)
# Instruction per taken branch
def IPTB(EV, level):
    return EV("INST_RETIRED.ANY", level) / EV("BR_INST_RETIRED.NEAR_TAKEN", level)
# Fraction of Uops delivered by the DSB (decoded instructions cache)
def DSB_Coverage(EV, level):
    return ( EV("IDQ.DSB_UOPS", level) + EV("LSD.UOPS", level))/(EV("IDQ.DSB_UOPS", level) + EV("LSD.UOPS", level) + EV("IDQ.MITE_UOPS", level) + EV("IDQ.MS_UOPS", level) )
# Instruction-Level-Parallelism (average number of uops executed when there is at least 1 uop executed)
def ILP(EV, level):
    return EV("UOPS_EXECUTED.THREAD", level) / Execute_Cycles(EV, level)
# Memory-Level-Parallelism (average number of L1 miss demand load when there is at least 1 such miss)
def MLP(EV, level):
    return EV("L1D_PEND_MISS.PENDING", level) / L1D_Miss_Cycles(EV, level)
# Actual Average Latency for L1 data-cache miss demand loads
def Load_Miss_Real_Latency(EV, level):
    return EV("L1D_PEND_MISS.PENDING", level) /(EV("MEM_LOAD_UOPS_RETIRED.L1_MISS", level) + EV("MEM_LOAD_UOPS_RETIRED.HIT_LFB", level) )
# Average Frequency Utilization relative nominal frequency
def Turbo_Utilization(EV, level):
    return CLKS(EV, level) / EV("CPU_CLK_UNHALTED.REF_TSC", level)
# Fraction of cycles where the core's Page Walker is busy serving iTLB/Load/Store
def Page_Walks_Use(EV, level):
    return ( EV("ITLB_MISSES.WALK_DURATION", level) + EV("DTLB_LOAD_MISSES.WALK_DURATION", level) + EV("DTLB_STORE_MISSES.WALK_DURATION", level))/ CLKS1(EV, level)
# Per-thread actual clocks
def CLKS(EV, level):
    return EV("CPU_CLK_UNHALTED.THREAD", level)
# Core actual clocks
def CLKS1(EV, level):
    return ( EV("CPU_CLK_UNHALTED.THREAD:amt1", level) / 2)if smt_enabled else CLKS(EV, level)

# Event groups


class Frontend_Bound:
    name = "Frontend_Bound"
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
            #print "Frontend_Bound zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Frontend_Latency:
    name = "Frontend_Latency"
    domain = "Slots"
    area = "FE"
    desc = """
This metric represents slots fraction CPU was stalled due to Frontend latency
issues.  For example, instruction-cache misses, iTLB misses or fetch stalls
after a branch misprediction are categorized under Frontend Latency. In such
cases the Frontend eventually delivers no uops for some period."""
    level = 2
    def compute(self, EV):
        try:
            self.val = Pipeline_Width * EV("IDQ_UOPS_NOT_DELIVERED.CYCLES_0_UOPS_DELIV.CORE", 2)/ SLOTS(EV, 2 )
            self.thresh = (self.val > 0.15) and self.parent.thresh
        except ZeroDivisionError:
            #print "Frontend_Latency zero division"
            self.val = 0
            self.thresh = False
        return self.val

class ICache_Misses:
    name = "ICache_Misses"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents cycles fraction CPU was stalled due to instruction
cache misses. Using compiler's Profile-Guided Optimization (PGO) can reduce
i-cache misses through improved hot code layout."""
    level = 3
    def compute(self, EV):
        try:
            self.val = EV("ICACHE.IFETCH_STALL", 3)/ CLKS(EV, 3)- self.ITLB_Misses.compute(EV )
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            #print "ICache_Misses zero division"
            self.val = 0
            self.thresh = False
        return self.val

class ITLB_Misses:
    name = "ITLB_Misses"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents cycles fraction CPU was stalled due to instruction TLB
misses. Using large code pages may be considered here."""
    level = 3
    def compute(self, EV):
        try:
            self.val = ITLB_Miss_Cycles(EV, 3)/ CLKS(EV, 3 )
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            #print "ITLB_Misses zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Branch_Resteers:
    name = "Branch_Resteers"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents cycles fraction CPU was stalled due to Branch Resteers.
Following all sorts of miss-predicted branches, this measure the delays of
fetch instructions from corrected path caused by the Frontend of the machine.
For example, branchy code with lots of (taken) branches and/or branch miss-
predictions might get categorized under Branch Resteers."""
    level = 3
    def compute(self, EV):
        try:
            self.val = Avg_RS_Empty_Period_Clears(EV, 3)*(EV("BR_MISP_RETIRED.ALL_BRANCHES", 3)+ EV("MACHINE_CLEARS.COUNT", 3)+ EV("BACLEARS.ANY", 3)) / CLKS(EV, 3 )
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            #print "Branch_Resteers zero division"
            self.val = 0
            self.thresh = False
        return self.val

class DSB_Switches:
    name = "DSB_Switches"
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
            #print "DSB_Switches zero division"
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

class MS_Switches:
    name = "MS_Switches"
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
            self.val = MS_Switches_Cost * EV("IDQ.MS_SWITCHES", 3)/ CLKS(EV, 3 )
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            #print "MS_Switches zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Frontend_Bandwidth:
    name = "Frontend_Bandwidth"
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
            self.val = self.Frontend_Bound.compute(EV)- self.Frontend_Latency.compute(EV )
            self.thresh = (self.val > 0.1) & (IPC(EV, 2) > 2.0) and self.parent.thresh
        except ZeroDivisionError:
            #print "Frontend_Bandwidth zero division"
            self.val = 0
            self.thresh = False
        return self.val

class MITE:
    name = "MITE"
    domain = "CClocks"
    area = "FE"
    desc = """
This metric represents cycles fraction in which CPU was likely limited due to
the MITE fetch pipeline.  For example, inefficiencies in the instruction
decoders are categorized here."""
    level = 3
    def compute(self, EV):
        try:
            self.val = ( EV("IDQ.ALL_MITE_CYCLES_ANY_UOPS", 3)- EV("IDQ.ALL_MITE_CYCLES_4_UOPS", 3)) / CLKS1(EV, 3 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "MITE zero division"
            self.val = 0
            self.thresh = False
        return self.val

class DSB:
    name = "DSB"
    domain = "CClocks"
    area = "FE"
    desc = """
This metric represents cycles fraction in which CPU was likely limited due to
DSB (decoded uop cache) fetch pipeline.  For example, inefficient utilization
of the DSB cache structure or bank conflict when reading from it, are
categorized here."""
    level = 3
    def compute(self, EV):
        try:
            self.val = ( EV("IDQ.ALL_DSB_CYCLES_ANY_UOPS", 3)- EV("IDQ.ALL_DSB_CYCLES_4_UOPS", 3)) / CLKS1(EV, 3 )
            self.thresh = (self.val > 0.3) and self.parent.thresh
        except ZeroDivisionError:
            #print "DSB zero division"
            self.val = 0
            self.thresh = False
        return self.val

class LSD:
    name = "LSD"
    domain = "CClocks"
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
            self.val = ( EV("LSD.CYCLES_ACTIVE", 3)- EV("LSD.CYCLES_4_UOPS", 3)) / CLKS1(EV, 3 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "LSD zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Bad_Speculation:
    name = "Bad_Speculation"
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
            self.val = ( EV("UOPS_ISSUED.ANY", 1)- EV("UOPS_RETIRED.RETIRE_SLOTS", 1)+ Pipeline_Width * Recovery_Cycles(EV, 1)) / SLOTS(EV, 1 )
            self.thresh = (self.val > 0.1)
        except ZeroDivisionError:
            #print "Bad_Speculation zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Branch_Mispredicts:
    name = "Branch_Mispredicts"
    domain = "Slots"
    area = "BAD"
    desc = """
This metric represents slots fraction CPU was impacted by Branch
Misprediction.  These slots are either wasted by uops fetched from an
incorrectly speculated program path, or stalls the Backend of the machine
needs to recover its state from a speculative path."""
    level = 2
    def compute(self, EV):
        try:
            self.val = Mispred_Clears_Fraction(EV, 2)* self.Bad_Speculation.compute(EV )
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            #print "Branch_Mispredicts zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Machine_Clears:
    name = "Machine_Clears"
    domain = "Slots"
    area = "BAD"
    desc = """
This metric represents slots fraction CPU was impacted by Machine Clears.
These slots are either wasted by uops fetched prior to the clear, or stalls
the Backend of the machine needs to recover its state after the clear. For
example, this can happen due to memory ordering Nukes (e.g. Memory
Disambiguation) or Self-Modifying-Code (SMC) nukes."""
    level = 2
    def compute(self, EV):
        try:
            self.val = self.Bad_Speculation.compute(EV)- self.Branch_Mispredicts.compute(EV )
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            #print "Machine_Clears zero division"
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
            self.val = 1 -(self.Frontend_Bound.compute(EV)+ self.Bad_Speculation.compute(EV)+ self.Retiring.compute(EV))
            self.thresh = (self.val > 0.2)
        except ZeroDivisionError:
            #print "Backend_Bound zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Memory_Bound:
    name = "Memory_Bound"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric represents how much Memory subsystem was a bottleneck.  Memory
Bound measures cycle fraction where pipeline is likely stalled due to demand
load or store instructions. This accounts mainly for non-completed in-flight
memory demand loads which coincides with execution starvation. in addition to
less common cases where stores could imply backpressure on the pipeline."""
    level = 2
    def compute(self, EV):
        try:
            self.val = ( STALLS_MEM_ANY(EV, 2)+ EV("RESOURCE_STALLS.SB", 2)) / CLKS(EV, 2 )
            self.thresh = (self.val > 0.2) and self.parent.thresh
        except ZeroDivisionError:
            #print "Memory_Bound zero division"
            self.val = 0
            self.thresh = False
        return self.val

class L1_Bound:
    name = "L1_Bound"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric represents how often CPU was stalled without missing the L1 data
cache.  The L1 cache typically has the shortest latency.  However, in certain
cases like loads blocked on older stores, a load might suffer a high latency
even though it is being satisfied by the L1. There are no fill-buffers
allocated for L1 hits so instead we use the load matrix (LDM) stalls sub-event
as it accounts for any non-completed load."""
    level = 3
    def compute(self, EV):
        try:
            self.val = ( STALLS_MEM_ANY(EV, 3)- EV("CYCLE_ACTIVITY.STALLS_L1D_PENDING", 3)) / CLKS(EV, 3 )
            self.thresh = ((self.val > 0.07) and self.parent.thresh) | self.DTLB_Load.thresh
        except ZeroDivisionError:
            #print "L1_Bound zero division"
            self.val = 0
            self.thresh = False
        return self.val

class DTLB_Load:
    name = "DTLB_Load"
    domain = "Clocks"
    area = "BE/Mem"
    desc = ""
    level = 4
    def compute(self, EV):
        try:
            self.val = ( Mem_STLB_Hit_Cost * EV("DTLB_LOAD_MISSES.STLB_HIT", 4)+ EV("DTLB_LOAD_MISSES.WALK_DURATION", 4)) / CLKS(EV, 4 )
            self.thresh = self.val > 0.0 and self.parent.thresh
        except ZeroDivisionError:
            #print "DTLB_Load zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Store_Fwd_Blk:
    name = "Store_Fwd_Blk"
    domain = "Clocks"
    area = "BE/Mem"
    desc = ""
    level = 4
    def compute(self, EV):
        try:
            self.val = Mem_SFB_Cost * EV("LD_BLOCKS.STORE_FORWARD", 4)/ CLKS(EV, 4 )
            self.thresh = self.val > 0.0 and self.parent.thresh
        except ZeroDivisionError:
            #print "Store_Fwd_Blk zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Split_Loads:
    name = "Split_Loads"
    domain = "Clocks"
    area = "BE/Mem"
    desc = ""
    level = 4
    def compute(self, EV):
        try:
            self.val = Load_Miss_Real_Latency(EV, 4)* EV("LD_BLOCKS.NO_SR", 4)/ CLKS(EV, 4 )
            self.thresh = self.val > 0.0 and self.parent.thresh
        except ZeroDivisionError:
            #print "Split_Loads zero division"
            self.val = 0
            self.thresh = False
        return self.val

class G4K_Aliasing:
    name = "4K_Aliasing"
    domain = "Clocks"
    area = "BE/Mem"
    desc = ""
    level = 4
    def compute(self, EV):
        try:
            self.val = Mem_4K_Alias_Cost * EV("LD_BLOCKS_PARTIAL.ADDRESS_ALIAS", 4)/ CLKS(EV, 4 )
            self.thresh = self.val > 0.0 and self.parent.thresh
        except ZeroDivisionError:
            #print "G4K_Aliasing zero division"
            self.val = 0
            self.thresh = False
        return self.val

class L2_Bound:
    name = "L2_Bound"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric represents how often CPU was stalled on L2 cache.  Avoiding cache
misses (i.e. L1 misses/L2 hits) will improve the latency and increase
performance."""
    level = 3
    def compute(self, EV):
        try:
            self.val = ( EV("CYCLE_ACTIVITY.STALLS_L1D_PENDING", 3)- EV("CYCLE_ACTIVITY.STALLS_L2_PENDING", 3)) / CLKS(EV, 3 )
            self.thresh = (self.val > 0.03) and self.parent.thresh
        except ZeroDivisionError:
            #print "L2_Bound zero division"
            self.val = 0
            self.thresh = False
        return self.val

class L3_Bound:
    name = "L3_Bound"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric represents how often CPU was stalled on L3 cache or contended with
a sibling Core.  Avoiding cache misses (i.e. L2 misses/L3 hits) will improve
the latency and increase performance."""
    level = 3
    def compute(self, EV):
        try:
            self.val = Mem_L3_Hit_Fraction(EV, 3)* EV("CYCLE_ACTIVITY.STALLS_L2_PENDING", 3)/ CLKS(EV, 3 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "L3_Bound zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Contested_Accesses:
    name = "Contested_Accesses"
    domain = "Clocks"
    area = "BE/Mem"
    desc = ""
    level = 4
    def compute(self, EV):
        try:
            self.val = Mem_XSNP_HitM_Cost *(EV("MEM_LOAD_UOPS_LLC_HIT_RETIRED.XSNP_HITM", 4)+ EV("MEM_LOAD_UOPS_LLC_HIT_RETIRED.XSNP_MISS", 4)) / CLKS(EV, 4 )
            self.thresh = self.val > 0.0 and self.parent.thresh
        except ZeroDivisionError:
            #print "Contested_Accesses zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Data_Sharing:
    name = "Data_Sharing"
    domain = "Clocks"
    area = "BE/Mem"
    desc = ""
    level = 4
    def compute(self, EV):
        try:
            self.val = MEM_XSNP_Hit_Cost * EV("MEM_LOAD_UOPS_LLC_HIT_RETIRED.XSNP_HIT", 4)/ CLKS(EV, 4 )
            self.thresh = self.val > 0.0 and self.parent.thresh
        except ZeroDivisionError:
            #print "Data_Sharing zero division"
            self.val = 0
            self.thresh = False
        return self.val

class L3_Latency:
    name = "L3_Latency"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric is a rough aggregate estimate of cycles fraction where CPU
accessed L3 cache for all load requests, while there was no contention/sharing
with a sibling core.  Avoiding cache misses (i.e. L2 misses/L3 hits) will
improve the latency and increase performance."""
    level = 4
    def compute(self, EV):
        try:
            self.val = MEM_XSNP_None_Cost * EV("MEM_LOAD_UOPS_RETIRED.LLC_HIT", 4)/ CLKS(EV, 4 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "L3_Latency zero division"
            self.val = 0
            self.thresh = False
        return self.val

class MEM_Bound:
    name = "MEM_Bound"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric represents how often CPU was stalled on main memory (DRAM).
Caching will improve the latency and increase performance."""
    level = 3
    def compute(self, EV):
        try:
            self.val = ( 1 - Mem_L3_Hit_Fraction(EV, 3)) * EV("CYCLE_ACTIVITY.STALLS_L2_PENDING", 3)/ CLKS(EV, 3 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "MEM_Bound zero division"
            self.val = 0
            self.thresh = False
        return self.val

class MEM_Bandwidth:
    name = "MEM_Bandwidth"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric represents how often CPU was likely stalled due to approaching
bandwidth limits of main memory (DRAM).  NUMA in multi-socket system may be
considered in such case."""
    level = 4
    def compute(self, EV):
        try:
            self.val = ORO_Demand_DRD_C6(EV, 4)/ CLKS(EV, 4 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "MEM_Bandwidth zero division"
            self.val = 0
            self.thresh = False
        return self.val

class MEM_Latency:
    name = "MEM_Latency"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric represents how often CPU was likely stalled due to latency from
main memory (DRAM).  Data layout re-structuring or using Software Prefetches
(also through the compiler) may be considered in such case."""
    level = 4
    def compute(self, EV):
        try:
            self.val = ( ORO_Demand_DRD_C1(EV, 4)- ORO_Demand_DRD_C6(EV, 4)) / CLKS(EV, 4 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "MEM_Latency zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Stores_Bound:
    name = "Stores_Bound"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric represents how often CPU was stalled on due to store operations.
Tip: consider False Sharing analysis as next step"""
    level = 3
    def compute(self, EV):
        try:
            self.val = self.Memory_Bound.compute(EV)- STALLS_MEM_ANY(EV, 3)/ CLKS(EV, 3 )
            self.thresh = (self.val > 0.2) and self.parent.thresh
        except ZeroDivisionError:
            #print "Stores_Bound zero division"
            self.val = 0
            self.thresh = False
        return self.val

class False_Sharing:
    name = "False_Sharing"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric represents how often CPU was stalled on due to store operations.
Tip: consider False Sharing analysis as next step"""
    level = 4
    def compute(self, EV):
        try:
            self.val = Mem_XSNP_HitM_Cost *(EV("MEM_LOAD_UOPS_LLC_HIT_RETIRED.XSNP_HITM", 4)+ EV("OFFCORE_RESPONSE.DEMAND_RFO.LLC_HIT.HITM_Other_CORE", 4)) / CLKS(EV, 4 )
            self.thresh = (self.val > 0.2) and self.parent.thresh
        except ZeroDivisionError:
            #print "False_Sharing zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Split_Stores:
    name = "Split_Stores"
    domain = "Stores"
    area = "BE/Mem"
    desc = """
This metric represents rate of split store accesses.  Consider aligning your
data to the 64-byte cache line granularity."""
    level = 4
    def compute(self, EV):
        try:
            self.val = EV("MEM_UOPS_RETIRED.SPLIT_STORES", 4)/ EV("MEM_UOPS_RETIRED.ALL_STORES", 4 )
            self.thresh = self.val > 0.0 and self.parent.thresh
        except ZeroDivisionError:
            #print "Split_Stores zero division"
            self.val = 0
            self.thresh = False
        return self.val

class DTLB_Store:
    name = "DTLB_Store"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric represents cycles fraction spent handling first-level data TLB
store misses.  As with ordinary data caching, focus on improving data locality
and reducing working-set size to reduce DTLB overhead.  Additionally, consider
using profile-guided optimization (PGO) to collocate frequently-used data on
the same page.  Try using larger page sizes for large amounts of frequently-
used data."""
    level = 4
    def compute(self, EV):
        try:
            self.val = ( Mem_STLB_Hit_Cost * EV("DTLB_STORE_MISSES.STLB_HIT", 4)+ EV("DTLB_STORE_MISSES.WALK_DURATION", 4)) / CLKS(EV, 4 )
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            #print "DTLB_Store zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Core_Bound:
    name = "Core_Bound"
    domain = "Clocks"
    area = "BE/Core"
    desc = """
This metric represents how much Core non-memory issues were of a bottleneck.
Shortage in hardware compute resources, or dependencies software's
instructions are both categorized under Core Bound. Hence it may indicate the
machine ran out of an OOO resources, certain execution units are overloaded or
dependencies in program's data- or instruction-flow are limiting the
performance (e.g. FP-chained long-latency arithmetic operations). Tip:
consider Port Saturation analysis as next step."""
    level = 2
    def compute(self, EV):
        try:
            self.val = Backend_Bound_At_EXE(EV, 2)- self.Memory_Bound.compute(EV )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "Core_Bound zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Divider:
    name = "Divider"
    domain = "CClocks"
    area = "BE/Core"
    desc = ""
    level = 3
    def compute(self, EV):
        try:
            self.val = EV("ARITH.FPU_DIV_ACTIVE", 3)/ CLKS1(EV, 3 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "Divider zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Ports_Utilization:
    name = "Ports_Utilization"
    domain = "Clocks"
    area = "BE/Core"
    desc = """
This metric represents cycles fraction application was stalled due to Core
computation issues (non divider-related).  For example, heavy data-dependency
between nearby instructions will manifest in this category. Ditto if
instruction-mix used by the application overloads specific hardware execution
unit. Hint: Loop Vectorization -most compilers feature auto-Vectorization
options today- reduces pressure on the execution ports as multiple elements
are calculated with same uop."""
    level = 3
    def compute(self, EV):
        try:
            self.val = self.Core_Bound.compute(EV)- self.Divider.compute(EV )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "Ports_Utilization zero division"
            self.val = 0
            self.thresh = False
        return self.val

class G0_Ports_Utilized:
    name = "0_Ports_Utilized"
    domain = "CClocks"
    area = "BE/Core"
    desc = """
This metric represents cycles fraction CPU executed no uops on any execution
port."""
    level = 4
    def compute(self, EV):
        try:
            self.val = Cycles_0_Ports_Utilized(EV, 4)/ CLKS1(EV, 4 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "G0_Ports_Utilized zero division"
            self.val = 0
            self.thresh = False
        return self.val

class G1_Port_Utilized:
    name = "1_Port_Utilized"
    domain = "CClocks"
    area = "BE/Core"
    desc = """
This metric represents cycles fraction CPU executed total of 1 uop per cycle
on all execution ports. This can be due to heavy data-dependency among
instructions. In some cases with high 1_Port_Utilized and L1_Bound it can
point to L1 data-cache latency bottleneck that may not necessarily manifest
with complete execution starvation (due to the short L1 latency e.g. walking
linked list) - looking at the assembly can be helpful. Tip: consider 'Core
Port Saturation' analysis-type as next step."""
    level = 4
    def compute(self, EV):
        try:
            self.val = Cycles_1_Port_Utilized(EV, 4)/ CLKS1(EV, 4 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "G1_Port_Utilized zero division"
            self.val = 0
            self.thresh = False
        return self.val

class G2_Ports_Utilized:
    name = "2_Ports_Utilized"
    domain = "CClocks"
    area = "BE/Core"
    desc = """
This metric represents cycles fraction CPU executed total of 2 uops per cycle
on all execution ports. Tip: consider 'Core Port Saturation' analysis-type as
next step. Loop Vectorization -most compilers feature auto-Vectorization
options today- reduces pressure on the execution ports as multiple elements
are calculated with same uop."""
    level = 4
    def compute(self, EV):
        try:
            self.val = Cycles_2_Ports_Utilized(EV, 4)/ CLKS1(EV, 4 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "G2_Ports_Utilized zero division"
            self.val = 0
            self.thresh = False
        return self.val

class G3m_Ports_Utilized:
    name = "3m_Ports_Utilized"
    domain = "CClocks"
    area = "BE/Core"
    desc = """
This metric represents cycles fraction CPU executed total of 3 or more uops
per cycle on all execution ports. Tip: consider 'Core Port Saturation'
analysis-type as next step"""
    level = 4
    def compute(self, EV):
        try:
            self.val = Cycles_3m_Ports_Utilized(EV, 4)/ CLKS1(EV, 4 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "G3m_Ports_Utilized zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Port_0:
    name = "Port_0"
    domain = "CClocks"
    area = "BE/Core"
    desc = """
This metric represents Core cycles fraction CPU dispatched uops on execution
port 0 (ALU)"""
    level = 5
    def compute(self, EV):
        try:
            self.val = EV("UOPS_DISPATCHED_PORT.PORT_0", 5)/ CLKS1(EV, 5 )
            self.thresh = self.val > 0.0 and self.parent.thresh
        except ZeroDivisionError:
            #print "Port_0 zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Port_1:
    name = "Port_1"
    domain = "CClocks"
    area = "BE/Core"
    desc = """
This metric represents Core cycles fraction CPU dispatched uops on execution
port 1 (ALU)"""
    level = 5
    def compute(self, EV):
        try:
            self.val = EV("UOPS_DISPATCHED_PORT.PORT_1", 5)/ CLKS1(EV, 5 )
            self.thresh = self.val > 0.0 and self.parent.thresh
        except ZeroDivisionError:
            #print "Port_1 zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Port_2:
    name = "Port_2"
    domain = "CClocks"
    area = "BE/Core"
    desc = """
This metric represents Core cycles fraction CPU dispatched uops on execution
port 2 (Loads and Store-address)"""
    level = 5
    def compute(self, EV):
        try:
            self.val = EV("UOPS_DISPATCHED_PORT.PORT_2", 5)/ CLKS1(EV, 5 )
            self.thresh = self.val > 0.0 and self.parent.thresh
        except ZeroDivisionError:
            #print "Port_2 zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Port_3:
    name = "Port_3"
    domain = "CClocks"
    area = "BE/Core"
    desc = """
This metric represents Core cycles fraction CPU dispatched uops on execution
port 3 (Loads and Store-address)"""
    level = 5
    def compute(self, EV):
        try:
            self.val = EV("UOPS_DISPATCHED_PORT.PORT_3", 5)/ CLKS1(EV, 5 )
            self.thresh = self.val > 0.0 and self.parent.thresh
        except ZeroDivisionError:
            #print "Port_3 zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Port_4:
    name = "Port_4"
    domain = "CClocks"
    area = "BE/Core"
    desc = """
This metric represents Core cycles fraction CPU dispatched uops on execution
port 4 (Store-data)"""
    level = 5
    def compute(self, EV):
        try:
            self.val = EV("UOPS_DISPATCHED_PORT.PORT_4", 5)/ CLKS1(EV, 5 )
            self.thresh = self.val > 0.0 and self.parent.thresh
        except ZeroDivisionError:
            #print "Port_4 zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Port_5:
    name = "Port_5"
    domain = "CClocks"
    area = "BE/Core"
    desc = """
This metric represents Core cycles fraction CPU dispatched uops on execution
port 5 (Branches and ALU)"""
    level = 5
    def compute(self, EV):
        try:
            self.val = EV("UOPS_DISPATCHED_PORT.PORT_5", 5)/ CLKS1(EV, 5 )
            self.thresh = self.val > 0.0 and self.parent.thresh
        except ZeroDivisionError:
            #print "Port_5 zero division"
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
            self.thresh = (self.val > 0.7) | self.Microcode_Sequencer.thresh
        except ZeroDivisionError:
            #print "Retiring zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Base:
    name = "Base"
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
            self.val = self.Retiring.compute(EV)- self.Microcode_Sequencer.compute(EV )
            self.thresh = (self.val > 0.6) and self.parent.thresh
        except ZeroDivisionError:
            #print "Base zero division"
            self.val = 0
            self.thresh = False
        return self.val

class FP_x87:
    name = "FP_x87"
    domain = "Uops"
    area = "RET"
    desc = """
This metric represents floating-point (FP) x87 uops fraction the CPU has
executed. Tip: consider compiler flags to generate newer AVX (or SSE)
instruction sets, which typically perform better and feature vectors."""
    level = 4
    def compute(self, EV):
        try:
            self.val = EV("FP_COMP_OPS_EXE.X87", 4)/ EV("UOPS_EXECUTED.THREAD", 4 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "FP_x87 zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Microcode_Sequencer:
    name = "Microcode_Sequencer"
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
            self.val = Retire_Uop_Fraction(EV, 2)* EV("IDQ.MS_UOPS", 2)/ SLOTS(EV, 2 )
            self.thresh = (self.val > 0.05)
        except ZeroDivisionError:
            #print "Microcode_Sequencer zero division"
            self.val = 0
            self.thresh = False
        return self.val

class Metric_IPC:
    name = "IPC"
    desc = """
Instructions Per Cycle (per physical core)"""

    def compute(self, EV):
        try:
            self.val = IPC(EV, 0)
        except ZeroDivisionError:
            print "IPC zero division"
            self.val = 0

class Metric_CPI:
    name = "CPI"
    desc = """
"""

    def compute(self, EV):
        try:
            self.val = CPI(EV, 0)
        except ZeroDivisionError:
            print "CPI zero division"
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

class Metric_IPTB:
    name = "IPTB"
    desc = """
Instruction per taken branch"""

    def compute(self, EV):
        try:
            self.val = IPTB(EV, 0)
        except ZeroDivisionError:
            print "IPTB zero division"
            self.val = 0

class Metric_DSB_Coverage:
    name = "DSB_Coverage"
    desc = """
Fraction of Uops delivered by the DSB (decoded instructions cache)"""

    def compute(self, EV):
        try:
            self.val = DSB_Coverage(EV, 0)
        except ZeroDivisionError:
            print "DSB_Coverage zero division"
            self.val = 0

class Metric_ILP:
    name = "ILP"
    desc = """
Instruction-Level-Parallelism (average number of uops executed when there is
at least 1 uop executed)"""

    def compute(self, EV):
        try:
            self.val = ILP(EV, 0)
        except ZeroDivisionError:
            print "ILP zero division"
            self.val = 0

class Metric_MLP:
    name = "MLP"
    desc = """
Memory-Level-Parallelism (average number of L1 miss demand load when there is
at least 1 such miss)"""

    def compute(self, EV):
        try:
            self.val = MLP(EV, 0)
        except ZeroDivisionError:
            print "MLP zero division"
            self.val = 0

class Metric_Load_Miss_Real_Latency:
    name = "Load_Miss_Real_Latency"
    desc = """
Actual Average Latency for L1 data-cache miss demand loads"""

    def compute(self, EV):
        try:
            self.val = Load_Miss_Real_Latency(EV, 0)
        except ZeroDivisionError:
            print "Load_Miss_Real_Latency zero division"
            self.val = 0

class Metric_Turbo_Utilization:
    name = "Turbo_Utilization"
    desc = """
Average Frequency Utilization relative nominal frequency"""

    def compute(self, EV):
        try:
            self.val = Turbo_Utilization(EV, 0)
        except ZeroDivisionError:
            print "Turbo_Utilization zero division"
            self.val = 0

class Metric_Page_Walks_Use:
    name = "Page_Walks_Use"
    desc = """
Fraction of cycles where the core's Page Walker is busy serving
iTLB/Load/Store"""

    def compute(self, EV):
        try:
            self.val = Page_Walks_Use(EV, 0)
        except ZeroDivisionError:
            print "Page_Walks_Use zero division"
            self.val = 0

class Metric_CLKS:
    name = "CLKS"
    desc = """
Per-thread actual clocks"""

    def compute(self, EV):
        try:
            self.val = CLKS(EV, 0)
        except ZeroDivisionError:
            print "CLKS zero division"
            self.val = 0

class Metric_CLKS1:
    name = "CLKS1"
    desc = """
Core actual clocks"""

    def compute(self, EV):
        try:
            self.val = CLKS1(EV, 0)
        except ZeroDivisionError:
            print "CLKS1 zero division"
            self.val = 0

# Schedule


class Setup:
    def __init__(self, r):
        o = dict()
        n = Frontend_Bound() ; r.run(n) ; o["Frontend_Bound"] = n
        n = Frontend_Latency() ; r.run(n) ; o["Frontend_Latency"] = n
        n = ICache_Misses() ; r.run(n) ; o["ICache_Misses"] = n
        n = ITLB_Misses() ; r.run(n) ; o["ITLB_Misses"] = n
        n = Branch_Resteers() ; r.run(n) ; o["Branch_Resteers"] = n
        n = DSB_Switches() ; r.run(n) ; o["DSB_Switches"] = n
        n = LCP() ; r.run(n) ; o["LCP"] = n
        n = MS_Switches() ; r.run(n) ; o["MS_Switches"] = n
        n = Frontend_Bandwidth() ; r.run(n) ; o["Frontend_Bandwidth"] = n
        n = MITE() ; r.run(n) ; o["MITE"] = n
        n = DSB() ; r.run(n) ; o["DSB"] = n
        n = LSD() ; r.run(n) ; o["LSD"] = n
        n = Bad_Speculation() ; r.run(n) ; o["Bad_Speculation"] = n
        n = Branch_Mispredicts() ; r.run(n) ; o["Branch_Mispredicts"] = n
        n = Machine_Clears() ; r.run(n) ; o["Machine_Clears"] = n
        n = Backend_Bound() ; r.run(n) ; o["Backend_Bound"] = n
        n = Memory_Bound() ; r.run(n) ; o["Memory_Bound"] = n
        n = L1_Bound() ; r.run(n) ; o["L1_Bound"] = n
        n = DTLB_Load() ; r.run(n) ; o["DTLB_Load"] = n
        n = Store_Fwd_Blk() ; r.run(n) ; o["Store_Fwd_Blk"] = n
        n = Split_Loads() ; r.run(n) ; o["Split_Loads"] = n
        n = G4K_Aliasing() ; r.run(n) ; o["G4K_Aliasing"] = n
        n = L2_Bound() ; r.run(n) ; o["L2_Bound"] = n
        n = L3_Bound() ; r.run(n) ; o["L3_Bound"] = n
        n = Contested_Accesses() ; r.run(n) ; o["Contested_Accesses"] = n
        n = Data_Sharing() ; r.run(n) ; o["Data_Sharing"] = n
        n = L3_Latency() ; r.run(n) ; o["L3_Latency"] = n
        n = MEM_Bound() ; r.run(n) ; o["MEM_Bound"] = n
        n = MEM_Bandwidth() ; r.run(n) ; o["MEM_Bandwidth"] = n
        n = MEM_Latency() ; r.run(n) ; o["MEM_Latency"] = n
        n = Stores_Bound() ; r.run(n) ; o["Stores_Bound"] = n
        n = False_Sharing() ; r.run(n) ; o["False_Sharing"] = n
        n = Split_Stores() ; r.run(n) ; o["Split_Stores"] = n
        n = DTLB_Store() ; r.run(n) ; o["DTLB_Store"] = n
        n = Core_Bound() ; r.run(n) ; o["Core_Bound"] = n
        n = Divider() ; r.run(n) ; o["Divider"] = n
        n = Ports_Utilization() ; r.run(n) ; o["Ports_Utilization"] = n
        n = G0_Ports_Utilized() ; r.run(n) ; o["G0_Ports_Utilized"] = n
        n = G1_Port_Utilized() ; r.run(n) ; o["G1_Port_Utilized"] = n
        n = G2_Ports_Utilized() ; r.run(n) ; o["G2_Ports_Utilized"] = n
        n = G3m_Ports_Utilized() ; r.run(n) ; o["G3m_Ports_Utilized"] = n
        n = Port_0() ; r.run(n) ; o["Port_0"] = n
        n = Port_1() ; r.run(n) ; o["Port_1"] = n
        n = Port_2() ; r.run(n) ; o["Port_2"] = n
        n = Port_3() ; r.run(n) ; o["Port_3"] = n
        n = Port_4() ; r.run(n) ; o["Port_4"] = n
        n = Port_5() ; r.run(n) ; o["Port_5"] = n
        n = Retiring() ; r.run(n) ; o["Retiring"] = n
        n = Base() ; r.run(n) ; o["Base"] = n
        n = FP_x87() ; r.run(n) ; o["FP_x87"] = n
        n = Microcode_Sequencer() ; r.run(n) ; o["Microcode_Sequencer"] = n

        # parents

        o["Frontend_Latency"].parent = o["Frontend_Bound"]
        o["ICache_Misses"].parent = o["Frontend_Latency"]
        o["ITLB_Misses"].parent = o["Frontend_Latency"]
        o["Branch_Resteers"].parent = o["Frontend_Latency"]
        o["DSB_Switches"].parent = o["Frontend_Latency"]
        o["LCP"].parent = o["Frontend_Latency"]
        o["MS_Switches"].parent = o["Frontend_Latency"]
        o["Frontend_Bandwidth"].parent = o["Frontend_Bound"]
        o["MITE"].parent = o["Frontend_Bandwidth"]
        o["DSB"].parent = o["Frontend_Bandwidth"]
        o["LSD"].parent = o["Frontend_Bandwidth"]
        o["Branch_Mispredicts"].parent = o["Bad_Speculation"]
        o["Machine_Clears"].parent = o["Bad_Speculation"]
        o["Memory_Bound"].parent = o["Backend_Bound"]
        o["L1_Bound"].parent = o["Memory_Bound"]
        o["DTLB_Load"].parent = o["L1_Bound"]
        o["Store_Fwd_Blk"].parent = o["L1_Bound"]
        o["Split_Loads"].parent = o["L1_Bound"]
        o["G4K_Aliasing"].parent = o["L1_Bound"]
        o["L2_Bound"].parent = o["Memory_Bound"]
        o["L3_Bound"].parent = o["Memory_Bound"]
        o["Contested_Accesses"].parent = o["L3_Bound"]
        o["Data_Sharing"].parent = o["L3_Bound"]
        o["L3_Latency"].parent = o["L3_Bound"]
        o["MEM_Bound"].parent = o["Memory_Bound"]
        o["MEM_Bandwidth"].parent = o["MEM_Bound"]
        o["MEM_Latency"].parent = o["MEM_Bound"]
        o["Stores_Bound"].parent = o["Memory_Bound"]
        o["False_Sharing"].parent = o["Stores_Bound"]
        o["Split_Stores"].parent = o["Stores_Bound"]
        o["DTLB_Store"].parent = o["Stores_Bound"]
        o["Core_Bound"].parent = o["Backend_Bound"]
        o["Divider"].parent = o["Core_Bound"]
        o["Ports_Utilization"].parent = o["Core_Bound"]
        o["G0_Ports_Utilized"].parent = o["Ports_Utilization"]
        o["G1_Port_Utilized"].parent = o["Ports_Utilization"]
        o["G2_Ports_Utilized"].parent = o["Ports_Utilization"]
        o["G3m_Ports_Utilized"].parent = o["Ports_Utilization"]
        o["Port_0"].parent = o["G3m_Ports_Utilized"]
        o["Port_1"].parent = o["G3m_Ports_Utilized"]
        o["Port_2"].parent = o["G3m_Ports_Utilized"]
        o["Port_3"].parent = o["G3m_Ports_Utilized"]
        o["Port_4"].parent = o["G3m_Ports_Utilized"]
        o["Port_5"].parent = o["G3m_Ports_Utilized"]
        o["Base"].parent = o["Retiring"]
        o["FP_x87"].parent = o["Base"]
        o["Microcode_Sequencer"].parent = o["Retiring"]

        # references between groups

        o["ICache_Misses"].ITLB_Misses = o["ITLB_Misses"]
        o["Frontend_Bandwidth"].Frontend_Bound = o["Frontend_Bound"]
        o["Frontend_Bandwidth"].Frontend_Latency = o["Frontend_Latency"]
        o["Branch_Mispredicts"].Bad_Speculation = o["Bad_Speculation"]
        o["Machine_Clears"].Bad_Speculation = o["Bad_Speculation"]
        o["Machine_Clears"].Branch_Mispredicts = o["Branch_Mispredicts"]
        o["Backend_Bound"].Frontend_Bound = o["Frontend_Bound"]
        o["Backend_Bound"].Bad_Speculation = o["Bad_Speculation"]
        o["Backend_Bound"].Retiring = o["Retiring"]
        o["L1_Bound"].DTLB_Load = o["DTLB_Load"]
        o["Stores_Bound"].Memory_Bound = o["Memory_Bound"]
        o["Core_Bound"].Memory_Bound = o["Memory_Bound"]
        o["Ports_Utilization"].Core_Bound = o["Core_Bound"]
        o["Ports_Utilization"].Divider = o["Divider"]
        o["Retiring"].Microcode_Sequencer = o["Microcode_Sequencer"]
        o["Base"].Retiring = o["Retiring"]
        o["Base"].Microcode_Sequencer = o["Microcode_Sequencer"]

        # siblings cross-tree

        o["Frontend_Bound"].sibling = None
        o["Frontend_Latency"].sibling = None
        o["ICache_Misses"].sibling = None
        o["ITLB_Misses"].sibling = None
        o["Branch_Resteers"].sibling = o["Bad_Speculation"]
        o["DSB_Switches"].sibling = None
        o["LCP"].sibling = None
        o["MS_Switches"].sibling = o["Microcode_Sequencer"]
        o["Frontend_Bandwidth"].sibling = None
        o["MITE"].sibling = None
        o["DSB"].sibling = None
        o["LSD"].sibling = None
        o["Bad_Speculation"].sibling = o["Branch_Resteers"]
        o["Branch_Mispredicts"].sibling = None
        o["Machine_Clears"].sibling = None
        o["Backend_Bound"].sibling = None
        o["Memory_Bound"].sibling = None
        o["L1_Bound"].sibling = None
        o["DTLB_Load"].sibling = None
        o["Store_Fwd_Blk"].sibling = None
        o["Split_Loads"].sibling = None
        o["G4K_Aliasing"].sibling = None
        o["L2_Bound"].sibling = None
        o["L3_Bound"].sibling = None
        o["Contested_Accesses"].sibling = None
        o["Data_Sharing"].sibling = None
        o["L3_Latency"].sibling = None
        o["MEM_Bound"].sibling = None
        o["MEM_Bandwidth"].sibling = None
        o["MEM_Latency"].sibling = None
        o["Stores_Bound"].sibling = None
        o["False_Sharing"].sibling = None
        o["Split_Stores"].sibling = None
        o["DTLB_Store"].sibling = None
        o["Core_Bound"].sibling = None
        o["Divider"].sibling = None
        o["Ports_Utilization"].sibling = None
        o["G0_Ports_Utilized"].sibling = None
        o["G1_Port_Utilized"].sibling = None
        o["G2_Ports_Utilized"].sibling = None
        o["G3m_Ports_Utilized"].sibling = None
        o["Port_0"].sibling = None
        o["Port_1"].sibling = None
        o["Port_2"].sibling = None
        o["Port_3"].sibling = None
        o["Port_4"].sibling = None
        o["Port_5"].sibling = None
        o["Retiring"].sibling = None
        o["Base"].sibling = None
        o["FP_x87"].sibling = None
        o["Microcode_Sequencer"].sibling = o["MS_Switches"]

        # sampling events (experimental)

        o["Frontend_Bound"].sample = []
        o["Frontend_Latency"].sample = []
        o["ICache_Misses"].sample = []
        o["ITLB_Misses"].sample = []
        o["Branch_Resteers"].sample = ['BR_MISP_RETIRED.ALL_BRANCHES_PS']
        o["DSB_Switches"].sample = []
        o["LCP"].sample = []
        o["MS_Switches"].sample = []
        o["Frontend_Bandwidth"].sample = []
        o["MITE"].sample = []
        o["DSB"].sample = []
        o["LSD"].sample = []
        o["Bad_Speculation"].sample = []
        o["Branch_Mispredicts"].sample = []
        o["Machine_Clears"].sample = []
        o["Backend_Bound"].sample = []
        o["Memory_Bound"].sample = []
        o["L1_Bound"].sample = []
        o["DTLB_Load"].sample = []
        o["Store_Fwd_Blk"].sample = []
        o["Split_Loads"].sample = []
        o["G4K_Aliasing"].sample = []
        o["L2_Bound"].sample = []
        o["L3_Bound"].sample = []
        o["Contested_Accesses"].sample = ['MEM_LOAD_UOPS_LLC_HIT_RETIRED.XSNP_HITM_PS', 'MEM_LOAD_UOPS_LLC_HIT_RETIRED.XSNP_MISS_PS']
        o["Data_Sharing"].sample = ['MEM_LOAD_UOPS_LLC_HIT_RETIRED.XSNP_HIT_PS']
        o["L3_Latency"].sample = ['MEM_LOAD_UOPS_RETIRED.LLC_HIT_PS']
        o["MEM_Bound"].sample = []
        o["MEM_Bandwidth"].sample = []
        o["MEM_Latency"].sample = []
        o["Stores_Bound"].sample = []
        o["False_Sharing"].sample = ['MEM_LOAD_UOPS_LLC_HIT_RETIRED.XSNP_HITM_PS']
        o["Split_Stores"].sample = ['MEM_UOPS_RETIRED.SPLIT_STORES_PS', 'MEM_UOPS_RETIRED.ALL_STORES_PS']
        o["DTLB_Store"].sample = []
        o["Core_Bound"].sample = []
        o["Divider"].sample = []
        o["Ports_Utilization"].sample = []
        o["G0_Ports_Utilized"].sample = []
        o["G1_Port_Utilized"].sample = []
        o["G2_Ports_Utilized"].sample = []
        o["G3m_Ports_Utilized"].sample = []
        o["Port_0"].sample = []
        o["Port_1"].sample = []
        o["Port_2"].sample = []
        o["Port_3"].sample = []
        o["Port_4"].sample = []
        o["Port_5"].sample = []
        o["Retiring"].sample = []
        o["Base"].sample = []
        o["FP_x87"].sample = []
        o["Microcode_Sequencer"].sample = []

        # user visible metrics

        n = Metric_IPC() ; r.metric(n)
        n = Metric_CPI() ; r.metric(n)
        n = Metric_UPI() ; r.metric(n)
        n = Metric_IPTB() ; r.metric(n)
        n = Metric_DSB_Coverage() ; r.metric(n)
        n = Metric_ILP() ; r.metric(n)
        n = Metric_MLP() ; r.metric(n)
        n = Metric_Load_Miss_Real_Latency() ; r.metric(n)
        n = Metric_Turbo_Utilization() ; r.metric(n)
        n = Metric_Page_Walks_Use() ; r.metric(n)
        n = Metric_CLKS() ; r.metric(n)
        n = Metric_CLKS1() ; r.metric(n)
