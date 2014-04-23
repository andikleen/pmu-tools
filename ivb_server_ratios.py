
#
# auto generated TopDown description for Intel Xeon E5 v2 (code named IvyBridge EP)
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
MEM_LOCAL_DRAM_COST = 200
MEM_REMOTE_DRAM_COST = 310
MEM_REMOTE_HITM_COST = 200
MEM_REMOTE_FWD_COST = 180
MS_SWITCHES_COST = 3

# Aux. formulas

def CLKS(EV, level):
    return EV("CPU_CLK_UNHALTED.THREAD", level)
# Floating Point Operations Count
def FLOP_count(EV, level):
    return ( 1 *(EV("FP_COMP_OPS_EXE.SSE_SCALAR_SINGLE", level) + EV("FP_COMP_OPS_EXE.SSE_SCALAR_DOUBLE", level))+ 2 * EV("FP_COMP_OPS_EXE.SSE_PACKED_DOUBLE", level) + 4 *(EV("FP_COMP_OPS_EXE.SSE_PACKED_SINGLE", level) + EV("SIMD_FP_256.PACKED_DOUBLE", level))+ 8 * EV("SIMD_FP_256.PACKED_SINGLE", level) )
def FewUopsExecutedThreshold(EV, level):
    EV("UOPS_EXECUTED.CYCLES_GE_3_UOPS_EXEC", level); EV("UOPS_EXECUTED.CYCLES_GE_2_UOPS_EXEC", level)
    return EV("UOPS_EXECUTED.CYCLES_GE_3_UOPS_EXEC", level) if(IPC(EV, level) > 1.25)else EV("UOPS_EXECUTED.CYCLES_GE_2_UOPS_EXEC", level)
def BackendBoundAtEXE_stalls(EV, level):
    return ( EV("CYCLE_ACTIVITY.CYCLES_NO_EXECUTE", level) + EV("UOPS_EXECUTED.CYCLES_GE_1_UOP_EXEC", level) - FewUopsExecutedThreshold(EV, level) - EV("RS_EVENTS.EMPTY_CYCLES", level) + EV("RESOURCE_STALLS.SB", level) )
def BackendBoundAtEXE(EV, level):
    return BackendBoundAtEXE_stalls(EV, level) / CLKS(EV, level)
def MemL3HitFraction(EV, level):
    return EV("MEM_LOAD_UOPS_RETIRED.LLC_HIT", level) /(EV("MEM_LOAD_UOPS_RETIRED.LLC_HIT", level) + MEM_L3_WEIGHT * EV("MEM_LOAD_UOPS_RETIRED.LLC_MISS", level) )
def MispredClearsFraction(EV, level):
    return EV("BR_MISP_RETIRED.ALL_BRANCHES", level) /(EV("BR_MISP_RETIRED.ALL_BRANCHES", level) + EV("MACHINE_CLEARS.COUNT", level) )
def AvgRsEmptyPeriodClears(EV, level):
    return ( EV("RS_EVENTS.EMPTY_CYCLES", level) - EV("ICACHE.IFETCH_STALL", level))/ EV("RS_EVENTS.EMPTY_END", level)
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
# Instruction-Level-Parallelism (avg uops executed when there is at least 1 uop executed)
def ILP(EV, level):
    return EV("UOPS_EXECUTED.THREAD", level) / EV("UOPS_EXECUTED.CYCLES_GE_1_UOP_EXEC", level)
# Memory-Level-Parallelism (avg L1 miss demand load when there is at least 1 such miss)
def MLP(EV, level):
    return EV("L1D_PEND_MISS.PENDING", level) / EV("L1D_PEND_MISS.PENDING_CYCLES", level)
# Average L1 miss demand load latency
def L1dMissLatency(EV, level):
    return EV("L1D_PEND_MISS.PENDING", level) / EV("MEM_LOAD_UOPS_RETIRED.L1_MISS", level)
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

class ICacheMisses:
    name = "ICache Misses"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents cycles fraction CPU was stalled due to instruction
cache misses. Using compiler's Profile-Guided Optimization (PGO) can reduce
i-cache misses through improved hot code layout."""
    level = 3
    def compute(self, EV):
        try:
            self.val = ( EV("ICACHE.IFETCH_STALL", 3)- EV("ITLB_MISSES.WALK_DURATION", 3)) / CLKS(EV, 3 )
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            #print "ICacheMisses zero division"
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

class BranchResteers:
    name = "Branch Resteers"
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
            self.val = ( EV("BR_MISP_RETIRED.ALL_BRANCHES", 3)+ EV("MACHINE_CLEARS.COUNT", 3)+ EV("BACLEARS.ANY", 3)) * AvgRsEmptyPeriodClears(EV, 3)/ CLKS(EV, 3 )
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            #print "BranchResteers zero division"
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

class BranchMispredicts:
    name = "Branch Mispredicts"
    domain = "Slots"
    area = "BAD"
    desc = """
This metric represents slots fraction CPU was impacted by Branch
Missprediction.  These slots are either wasted by uops fetched from an
incorrectly speculated program path, or stalls the Backend of the machine
needs to recover its state from a speculative path."""
    level = 2
    def compute(self, EV):
        try:
            self.val = MispredClearsFraction(EV, 2)* self.BadSpeculation.compute(EV )
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            #print "BranchMispredicts zero division"
            self.val = 0
            self.thresh = False
        return self.val

class MachineClears:
    name = "Machine Clears"
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
            self.val = self.BadSpeculation.compute(EV)- self.BranchMispredicts.compute(EV )
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            #print "MachineClears zero division"
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

class MemoryBound:
    name = "MemoryBound"
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
            self.val = ( EV("CYCLE_ACTIVITY.STALLS_LDM_PENDING", 2)+ EV("RESOURCE_STALLS.SB", 2)) / CLKS(EV, 2 )
            self.thresh = (self.val > 0.2) and self.parent.thresh
        except ZeroDivisionError:
            #print "MemoryBound zero division"
            self.val = 0
            self.thresh = False
        return self.val

class L1Bound:
    name = "L1 Bound"
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
            self.val = ( EV("CYCLE_ACTIVITY.STALLS_LDM_PENDING", 3)- EV("CYCLE_ACTIVITY.STALLS_L1D_PENDING", 3)) / CLKS(EV, 3 )
            self.thresh = ((self.val > 0.07) and self.parent.thresh) | self.DTLB_Overhead.thresh
        except ZeroDivisionError:
            #print "L1Bound zero division"
            self.val = 0
            self.thresh = False
        return self.val

class DTLB_Overhead:
    name = "DTLB_Overhead"
    domain = "Clocks"
    area = "BE/Mem"
    desc = ""
    level = 4
    def compute(self, EV):
        try:
            self.val = ( MEM_STLB_HIT_COST * EV("DTLB_LOAD_MISSES.STLB_HIT", 4)+ EV("DTLB_LOAD_MISSES.WALK_DURATION", 4)) / CLKS(EV, 4 )
            self.thresh = self.val > 0.0 and self.parent.thresh
        except ZeroDivisionError:
            #print "DTLB_Overhead zero division"
            self.val = 0
            self.thresh = False
        return self.val

class LoadsBlockedbyStoreForwarding:
    name = "Loads Blocked by Store Forwarding"
    domain = "Clocks"
    area = "BE/Mem"
    desc = ""
    level = 4
    def compute(self, EV):
        try:
            self.val = MEM_SFB_COST * EV("LD_BLOCKS.STORE_FORWARD", 4)/ CLKS(EV, 4 )
            self.thresh = self.val > 0.0 and self.parent.thresh
        except ZeroDivisionError:
            #print "LoadsBlockedbyStoreForwarding zero division"
            self.val = 0
            self.thresh = False
        return self.val

class SplitLoads:
    name = "Split Loads"
    domain = "Clocks"
    area = "BE/Mem"
    desc = ""
    level = 4
    def compute(self, EV):
        try:
            self.val = L1dMissLatency(EV, 4)* EV("LD_BLOCKS.NO_SR", 4)/ CLKS(EV, 4 )
            self.thresh = self.val > 0.0 and self.parent.thresh
        except ZeroDivisionError:
            #print "SplitLoads zero division"
            self.val = 0
            self.thresh = False
        return self.val

class G4KAliasing:
    name = "4K Aliasing"
    domain = "Clocks"
    area = "BE/Mem"
    desc = ""
    level = 4
    def compute(self, EV):
        try:
            self.val = MEM_4KALIAS_COST * EV("LD_BLOCKS_PARTIAL.ADDRESS_ALIAS", 4)/ CLKS(EV, 4 )
            self.thresh = self.val > 0.0 and self.parent.thresh
        except ZeroDivisionError:
            #print "G4KAliasing zero division"
            self.val = 0
            self.thresh = False
        return self.val

class L2Bound:
    name = "L2 Bound"
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
            #print "L2Bound zero division"
            self.val = 0
            self.thresh = False
        return self.val

class L3Bound:
    name = "L3 Bound"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric represents how often CPU was stalled on L3 cache or contended with
a sibling Core.  Avoiding cache misses (i.e. L2 misses/L3 hits) will improve
the latency and increase performance."""
    level = 3
    def compute(self, EV):
        try:
            self.val = MemL3HitFraction(EV, 3)* EV("CYCLE_ACTIVITY.STALLS_L2_PENDING", 3)/ CLKS(EV, 3 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "L3Bound zero division"
            self.val = 0
            self.thresh = False
        return self.val

class ContestedAccesses:
    name = "Contested Accesses"
    domain = "Clocks"
    area = "BE/Mem"
    desc = ""
    level = 4
    def compute(self, EV):
        try:
            self.val = MEM_XSNP_HITM_COST *(EV("MEM_LOAD_UOPS_LLC_HIT_RETIRED.XSNP_HITM", 4)+ EV("MEM_LOAD_UOPS_LLC_HIT_RETIRED.XSNP_MISS", 4)) / CLKS(EV, 4 )
            self.thresh = self.val > 0.0 and self.parent.thresh
        except ZeroDivisionError:
            #print "ContestedAccesses zero division"
            self.val = 0
            self.thresh = False
        return self.val

class DataSharing:
    name = "Data Sharing"
    domain = "Clocks"
    area = "BE/Mem"
    desc = ""
    level = 4
    def compute(self, EV):
        try:
            self.val = MEM_XSNP_HIT_COST * EV("MEM_LOAD_UOPS_LLC_HIT_RETIRED.XSNP_HIT", 4)/ CLKS(EV, 4 )
            self.thresh = self.val > 0.0 and self.parent.thresh
        except ZeroDivisionError:
            #print "DataSharing zero division"
            self.val = 0
            self.thresh = False
        return self.val

class L3Latency:
    name = "L3 Latency"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric is a rough aggregate estimate of cycles fraction where CPU
accessed L3 cache for all load requests, while there was no contention/sharing
with a sibiling core.  Avoiding cache misses (i.e. L2 misses/L3 hits) will
improve the latency and increase performance."""
    level = 4
    def compute(self, EV):
        try:
            self.val = MEM_XSNP_NONE_COST * EV("MEM_LOAD_UOPS_RETIRED.LLC_HIT", 4)/ CLKS(EV, 4 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "L3Latency zero division"
            self.val = 0
            self.thresh = False
        return self.val

class DRAMBound:
    name = "DRAM Bound"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric represents how often CPU was stalled on main memory (DRAM).
Caching will improve the latency and increase performance."""
    level = 3
    def compute(self, EV):
        try:
            self.val = ( 1 - MemL3HitFraction(EV, 3)) * EV("CYCLE_ACTIVITY.STALLS_L2_PENDING", 3)/ CLKS(EV, 3 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "DRAMBound zero division"
            self.val = 0
            self.thresh = False
        return self.val

class MEMBandwidth:
    name = "MEM Bandwidth"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric represents how often CPU was likely stalled due to approaching
bandwidth limits of main memory (DRAM).  NUMA in multi-socket system may be
considered in such case."""
    level = 4
    def compute(self, EV):
        try:
            self.val = EV("OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD:cmask=6", 4)/ CLKS(EV, 4 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "MEMBandwidth zero division"
            self.val = 0
            self.thresh = False
        return self.val

class MEMLatency:
    name = "MEM Latency"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric represents how often CPU was likely stalled due to latency from
main memory (DRAM).  Data layout restructing or using Software Prefetches
(also through the compiler) may be considered in such case."""
    level = 4
    def compute(self, EV):
        try:
            self.val = ( EV("OFFCORE_REQUESTS_OUTSTANDING.CYCLES_WITH_DEMAND_DATA_RD", 4)- EV("OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD:cmask=6", 4)) / CLKS(EV, 4 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "MEMLatency zero division"
            self.val = 0
            self.thresh = False
        return self.val

class LocalDRAM:
    name = "Local DRAM"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric represents how often CPU was likely stalled due to loads from
local memory. Caching will improve the latency and increase performance."""
    level = 5
    def compute(self, EV):
        try:
            self.val = MEM_LOCAL_DRAM_COST * EV("MEM_LOAD_UOPS_LLC_MISS_RETIRED.LOCAL_DRAM", 5)/ CLKS(EV, 5 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "LocalDRAM zero division"
            self.val = 0
            self.thresh = False
        return self.val

class RemoteDRAM:
    name = "Remote DRAM"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric represents how often CPU was likely stalled due to loads from
remote memory. This is caused often due to non-optimal NUMA allocations."""
    level = 5
    def compute(self, EV):
        try:
            self.val = MEM_REMOTE_DRAM_COST * EV("MEM_LOAD_UOPS_LLC_MISS_RETIRED.REMOTE_DRAM", 5)/ CLKS(EV, 5 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "RemoteDRAM zero division"
            self.val = 0
            self.thresh = False
        return self.val

class RemoteCache:
    name = "Remote Cache"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric represents how often CPU was likely stalled due to loads from
remote cache in other sockets. This is caused often due to non-optimal NUMA
allocations."""
    level = 5
    def compute(self, EV):
        try:
            self.val = ( MEM_REMOTE_HITM_COST * EV("MEM_LOAD_UOPS_LLC_MISS_RETIRED.REMOTE_HITM", 5)+ MEM_REMOTE_FWD_COST * EV("MEM_LOAD_UOPS_LLC_MISS_RETIRED.REMOTE_FWD", 5)) / CLKS(EV, 5 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "RemoteCache zero division"
            self.val = 0
            self.thresh = False
        return self.val

class StoresBound:
    name = "Stores Bound"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric represents how often CPU was stalled on due to store operations.
Tip: consider False Sharing analysis as next step"""
    level = 3
    def compute(self, EV):
        try:
            self.val = self.MemoryBound.compute(EV)-(EV("CYCLE_ACTIVITY.STALLS_LDM_PENDING", 3)/ CLKS(EV, 3))
            self.thresh = (self.val > 0.2) and self.parent.thresh
        except ZeroDivisionError:
            #print "StoresBound zero division"
            self.val = 0
            self.thresh = False
        return self.val

class FalseSharing:
    name = "False Sharing"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric represents how often CPU was stalled on due to store operations.
Tip: consider False Sharing analysis as next step"""
    level = 4
    def compute(self, EV):
        try:
            self.val = MEM_XSNP_HITM_COST *(EV("MEM_LOAD_UOPS_LLC_HIT_RETIRED.XSNP_HITM", 4)+ EV("OFFCORE_RESPONSE.DEMAND_RFO.LLC_HIT.HITM_OTHER_CORE", 4)) / CLKS(EV, 4 )
            self.thresh = (self.val > 0.2) and self.parent.thresh
        except ZeroDivisionError:
            #print "FalseSharing zero division"
            self.val = 0
            self.thresh = False
        return self.val

class SplitStores:
    name = "Split Stores"
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
            #print "SplitStores zero division"
            self.val = 0
            self.thresh = False
        return self.val

class DTLBStoreOverhead:
    name = "DTLB Store Overhead"
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
            self.val = ( MEM_STLB_HIT_COST * EV("DTLB_STORE_MISSES.STLB_HIT", 4)+ EV("DTLB_STORE_MISSES.WALK_DURATION", 4)) / CLKS(EV, 4 )
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            #print "DTLBStoreOverhead zero division"
            self.val = 0
            self.thresh = False
        return self.val

class CoreBound:
    name = "CoreBound"
    domain = "Clocks"
    area = "BE/Core"
    desc = """
This metric represents how much Core non-memory issues were a bottleneck.
This may indicate that we ran out of OOO resources or are saturating certain
execution units (e.g. the use of FP-chained long-latency arithmetic
operations) which can limit performance. Tip: consider Port Saturation
analysis as next step"""
    level = 2
    def compute(self, EV):
        try:
            self.val = BackendBoundAtEXE(EV, 2)- self.MemoryBound.compute(EV )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "CoreBound zero division"
            self.val = 0
            self.thresh = False
        return self.val

class DividerActive:
    name = "DividerActive"
    domain = "Clocks"
    area = "BE/Core"
    desc = ""
    level = 3
    def compute(self, EV):
        try:
            self.val = EV("ARITH.FPU_DIV_ACTIVE", 3)/ CLKS(EV, 3 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "DividerActive zero division"
            self.val = 0
            self.thresh = False
        return self.val

class PortsUtilization:
    name = "Ports Utilization"
    domain = "Clocks"
    area = "BE/Core"
    desc = """
This metric represents cycles fraction application was stalled due to Core
computatio issues (non divider-related).  For example, heavy data-dependency
between nearby instructions will manifest in this category. Ditto if
instruction-mix used by the application overloads specific hardware execution
unit. Loop Vectorization -most compilers feature auto-vectorization options
today- reduces pressure on the execution ports as multiple elements are
calculated with same uop."""
    level = 3
    def compute(self, EV):
        try:
            self.val = self.CoreBound.compute(EV)- self.DividerActive.compute(EV )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "PortsUtilization zero division"
            self.val = 0
            self.thresh = False
        return self.val

class G0_Ports:
    name = "0_Ports"
    domain = "Clocks"
    area = "BE/Core"
    desc = """
This metric represents cycles fraction CPU executed no uops on any execution
port."""
    level = 4
    def compute(self, EV):
        try:
            self.val = ( EV("CYCLE_ACTIVITY.CYCLES_NO_EXECUTE", 4)- EV("RS_EVENTS.EMPTY_CYCLES", 4)) / CLKS(EV, 4 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "G0_Ports zero division"
            self.val = 0
            self.thresh = False
        return self.val

class G1_Port:
    name = "1_Port"
    domain = "Clocks"
    area = "BE/Core"
    desc = """
This metric represents cycles fraction CPU executed total of 1 uop per cycle
on all execution ports. Tip: consider 'Core Port Saturation' analysis-type as
next step"""
    level = 4
    def compute(self, EV):
        try:
            self.val = ( EV("UOPS_EXECUTED.CYCLES_GE_1_UOP_EXEC", 4)- EV("UOPS_EXECUTED.CYCLES_GE_2_UOPS_EXEC", 4)) / CLKS(EV, 4 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "G1_Port zero division"
            self.val = 0
            self.thresh = False
        return self.val

class G2_Ports:
    name = "2_Ports"
    domain = "Clocks"
    area = "BE/Core"
    desc = """
This metric represents cycles fraction CPU executed total of 2 uops per cycle
on all execution ports. Tip: consider 'Core Port Saturation' analysis-type as
next step. Loop Vectorization -most compilers feature auto-vectorization
options today- reduces pressure on the execution ports as multiple elements
are calculated with same uop."""
    level = 4
    def compute(self, EV):
        try:
            self.val = ( EV("UOPS_EXECUTED.CYCLES_GE_2_UOPS_EXEC", 4)- EV("UOPS_EXECUTED.CYCLES_GE_3_UOPS_EXEC", 4)) / CLKS(EV, 4 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "G2_Ports zero division"
            self.val = 0
            self.thresh = False
        return self.val

class G3m_Ports:
    name = "3m_Ports"
    domain = "Clocks"
    area = "BE/Core"
    desc = """
This metric represents cycles fraction CPU executed total of 3 or more uops
per cycle on all execution ports. Tip: consider 'Core Port Saturation'
analysis-type as next step"""
    level = 4
    def compute(self, EV):
        try:
            self.val = EV("UOPS_EXECUTED.CYCLES_GE_3_UOPS_EXEC", 4)/ CLKS(EV, 4 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "G3m_Ports zero division"
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

class FP_Arith:
    name = "FP_Arith"
    domain = "Uops"
    area = "RET"
    desc = """
This metric represents overall arithmetic floating-point (FP) uops fraction
the CPU has executed."""
    level = 3
    def compute(self, EV):
        try:
            self.val = self.FP_x87.compute(EV)+ self.FP_Scalar.compute(EV)+ self.FP_Vector.compute(EV )
            self.thresh = (self.val > 0.2) and self.parent.thresh
        except ZeroDivisionError:
            #print "FP_Arith zero division"
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

class FP_Scalar:
    name = "FP_Scalar"
    domain = "Uops"
    area = "RET"
    desc = """
This metric represents arithmetic floating-point (FP) scalar uops fraction the
CPU has executed. Tip: investigate what limits (compiler) generation of vector
code."""
    level = 4
    def compute(self, EV):
        try:
            self.val = ( EV("FP_COMP_OPS_EXE.SSE_SCALAR_SINGLE", 4)+ EV("FP_COMP_OPS_EXE.SSE_SCALAR_DOUBLE", 4)) / EV("UOPS_EXECUTED.THREAD", 4 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            #print "FP_Scalar zero division"
            self.val = 0
            self.thresh = False
        return self.val

class FP_Vector:
    name = "FP_Vector"
    domain = "Uops"
    area = "RET"
    desc = """
This metric represents arithmetic floating-point (FP) vector uops fraction the
CPU has executed. Tip: check if vector width is expected"""
    level = 4
    def compute(self, EV):
        try:
            self.val = ( EV("FP_COMP_OPS_EXE.SSE_PACKED_DOUBLE", 4)+ EV("FP_COMP_OPS_EXE.SSE_PACKED_SINGLE", 4)+ EV("SIMD_FP_256.PACKED_SINGLE", 4)+ EV("SIMD_FP_256.PACKED_DOUBLE", 4)) / EV("UOPS_EXECUTED.THREAD", 4 )
            self.thresh = (self.val > 0.2) and self.parent.thresh
        except ZeroDivisionError:
            #print "FP_Vector zero division"
            self.val = 0
            self.thresh = False
        return self.val

class OTHER:
    name = "OTHER"
    domain = "Uops"
    area = "RET"
    desc = """
This metric represents non-floating-point (FP) uop fraction the CPU has
executed. If you application has no FP operations, this will likely be biggest
fraction."""
    level = 3
    def compute(self, EV):
        try:
            self.val = self.BASE.compute(EV)- self.FP_Arith.compute(EV )
            self.thresh = (self.val > 0.3) and self.parent.thresh
        except ZeroDivisionError:
            #print "OTHER zero division"
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

class Metric_ILP:
    name = "ILP"
    desc = """
Instruction-Level-Parallelism (avg uops executed when there is at least 1 uop
executed)"""

    def compute(self, EV):
        try:
            self.val = ILP(EV, 0)
        except ZeroDivisionError:
            print "ILP zero division"
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

class Metric_L1dMissLatency:
    name = "L1dMissLatency"
    desc = """
Average L1 miss demand load latency"""

    def compute(self, EV):
        try:
            self.val = L1dMissLatency(EV, 0)
        except ZeroDivisionError:
            print "L1dMissLatency zero division"
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
        n = ICacheMisses() ; r.run(n) ; o["ICacheMisses"] = n
        n = ITLBmisses() ; r.run(n) ; o["ITLBmisses"] = n
        n = BranchResteers() ; r.run(n) ; o["BranchResteers"] = n
        n = DSBswitches() ; r.run(n) ; o["DSBswitches"] = n
        n = LCP() ; r.run(n) ; o["LCP"] = n
        n = MSswitches() ; r.run(n) ; o["MSswitches"] = n
        n = FrontendBandwidth() ; r.run(n) ; o["FrontendBandwidth"] = n
        n = MITE() ; r.run(n) ; o["MITE"] = n
        n = DSB() ; r.run(n) ; o["DSB"] = n
        n = LSD() ; r.run(n) ; o["LSD"] = n
        n = BadSpeculation() ; r.run(n) ; o["BadSpeculation"] = n
        n = BranchMispredicts() ; r.run(n) ; o["BranchMispredicts"] = n
        n = MachineClears() ; r.run(n) ; o["MachineClears"] = n
        n = Backend_Bound() ; r.run(n) ; o["Backend_Bound"] = n
        n = MemoryBound() ; r.run(n) ; o["MemoryBound"] = n
        n = L1Bound() ; r.run(n) ; o["L1Bound"] = n
        n = DTLB_Overhead() ; r.run(n) ; o["DTLB_Overhead"] = n
        n = LoadsBlockedbyStoreForwarding() ; r.run(n) ; o["LoadsBlockedbyStoreForwarding"] = n
        n = SplitLoads() ; r.run(n) ; o["SplitLoads"] = n
        n = G4KAliasing() ; r.run(n) ; o["G4KAliasing"] = n
        n = L2Bound() ; r.run(n) ; o["L2Bound"] = n
        n = L3Bound() ; r.run(n) ; o["L3Bound"] = n
        n = ContestedAccesses() ; r.run(n) ; o["ContestedAccesses"] = n
        n = DataSharing() ; r.run(n) ; o["DataSharing"] = n
        n = L3Latency() ; r.run(n) ; o["L3Latency"] = n
        n = DRAMBound() ; r.run(n) ; o["DRAMBound"] = n
        n = MEMBandwidth() ; r.run(n) ; o["MEMBandwidth"] = n
        n = MEMLatency() ; r.run(n) ; o["MEMLatency"] = n
        n = LocalDRAM() ; r.run(n) ; o["LocalDRAM"] = n
        n = RemoteDRAM() ; r.run(n) ; o["RemoteDRAM"] = n
        n = RemoteCache() ; r.run(n) ; o["RemoteCache"] = n
        n = StoresBound() ; r.run(n) ; o["StoresBound"] = n
        n = FalseSharing() ; r.run(n) ; o["FalseSharing"] = n
        n = SplitStores() ; r.run(n) ; o["SplitStores"] = n
        n = DTLBStoreOverhead() ; r.run(n) ; o["DTLBStoreOverhead"] = n
        n = CoreBound() ; r.run(n) ; o["CoreBound"] = n
        n = DividerActive() ; r.run(n) ; o["DividerActive"] = n
        n = PortsUtilization() ; r.run(n) ; o["PortsUtilization"] = n
        n = G0_Ports() ; r.run(n) ; o["G0_Ports"] = n
        n = G1_Port() ; r.run(n) ; o["G1_Port"] = n
        n = G2_Ports() ; r.run(n) ; o["G2_Ports"] = n
        n = G3m_Ports() ; r.run(n) ; o["G3m_Ports"] = n
        n = Retiring() ; r.run(n) ; o["Retiring"] = n
        n = BASE() ; r.run(n) ; o["BASE"] = n
        n = FP_Arith() ; r.run(n) ; o["FP_Arith"] = n
        n = FP_x87() ; r.run(n) ; o["FP_x87"] = n
        n = FP_Scalar() ; r.run(n) ; o["FP_Scalar"] = n
        n = FP_Vector() ; r.run(n) ; o["FP_Vector"] = n
        n = OTHER() ; r.run(n) ; o["OTHER"] = n
        n = MicroSequencer() ; r.run(n) ; o["MicroSequencer"] = n

        # parents

        o["FrontendLatency"].parent = o["FrontendBound"]
        o["ICacheMisses"].parent = o["FrontendLatency"]
        o["ITLBmisses"].parent = o["FrontendLatency"]
        o["BranchResteers"].parent = o["FrontendLatency"]
        o["DSBswitches"].parent = o["FrontendLatency"]
        o["LCP"].parent = o["FrontendLatency"]
        o["MSswitches"].parent = o["FrontendLatency"]
        o["FrontendBandwidth"].parent = o["FrontendBound"]
        o["MITE"].parent = o["FrontendBandwidth"]
        o["DSB"].parent = o["FrontendBandwidth"]
        o["LSD"].parent = o["FrontendBandwidth"]
        o["BranchMispredicts"].parent = o["BadSpeculation"]
        o["MachineClears"].parent = o["BadSpeculation"]
        o["MemoryBound"].parent = o["Backend_Bound"]
        o["L1Bound"].parent = o["MemoryBound"]
        o["DTLB_Overhead"].parent = o["L1Bound"]
        o["LoadsBlockedbyStoreForwarding"].parent = o["L1Bound"]
        o["SplitLoads"].parent = o["L1Bound"]
        o["G4KAliasing"].parent = o["L1Bound"]
        o["L2Bound"].parent = o["MemoryBound"]
        o["L3Bound"].parent = o["MemoryBound"]
        o["ContestedAccesses"].parent = o["L3Bound"]
        o["DataSharing"].parent = o["L3Bound"]
        o["L3Latency"].parent = o["L3Bound"]
        o["DRAMBound"].parent = o["MemoryBound"]
        o["MEMBandwidth"].parent = o["DRAMBound"]
        o["MEMLatency"].parent = o["DRAMBound"]
        o["LocalDRAM"].parent = o["MEMLatency"]
        o["RemoteDRAM"].parent = o["MEMLatency"]
        o["RemoteCache"].parent = o["MEMLatency"]
        o["StoresBound"].parent = o["MemoryBound"]
        o["FalseSharing"].parent = o["StoresBound"]
        o["SplitStores"].parent = o["StoresBound"]
        o["DTLBStoreOverhead"].parent = o["StoresBound"]
        o["CoreBound"].parent = o["Backend_Bound"]
        o["DividerActive"].parent = o["CoreBound"]
        o["PortsUtilization"].parent = o["CoreBound"]
        o["G0_Ports"].parent = o["PortsUtilization"]
        o["G1_Port"].parent = o["PortsUtilization"]
        o["G2_Ports"].parent = o["PortsUtilization"]
        o["G3m_Ports"].parent = o["PortsUtilization"]
        o["BASE"].parent = o["Retiring"]
        o["FP_Arith"].parent = o["BASE"]
        o["FP_x87"].parent = o["FP_Arith"]
        o["FP_Scalar"].parent = o["FP_Arith"]
        o["FP_Vector"].parent = o["FP_Arith"]
        o["OTHER"].parent = o["BASE"]
        o["MicroSequencer"].parent = o["Retiring"]

        # references between groups

        o["FrontendBandwidth"].FrontendBound = o["FrontendBound"]
        o["FrontendBandwidth"].FrontendLatency = o["FrontendLatency"]
        o["BranchMispredicts"].BadSpeculation = o["BadSpeculation"]
        o["MachineClears"].BadSpeculation = o["BadSpeculation"]
        o["MachineClears"].BranchMispredicts = o["BranchMispredicts"]
        o["Backend_Bound"].FrontendBound = o["FrontendBound"]
        o["Backend_Bound"].BadSpeculation = o["BadSpeculation"]
        o["Backend_Bound"].Retiring = o["Retiring"]
        o["L1Bound"].DTLB_Overhead = o["DTLB_Overhead"]
        o["StoresBound"].MemoryBound = o["MemoryBound"]
        o["CoreBound"].MemoryBound = o["MemoryBound"]
        o["PortsUtilization"].CoreBound = o["CoreBound"]
        o["PortsUtilization"].DividerActive = o["DividerActive"]
        o["Retiring"].MicroSequencer = o["MicroSequencer"]
        o["BASE"].Retiring = o["Retiring"]
        o["BASE"].MicroSequencer = o["MicroSequencer"]
        o["FP_Arith"].FP_x87 = o["FP_x87"]
        o["FP_Arith"].FP_Scalar = o["FP_Scalar"]
        o["FP_Arith"].FP_Vector = o["FP_Vector"]
        o["OTHER"].BASE = o["BASE"]
        o["OTHER"].FP_Arith = o["FP_Arith"]

        # siblings cross-tree

        o["FrontendBound"].sibling = None
        o["FrontendLatency"].sibling = None
        o["ICacheMisses"].sibling = None
        o["ITLBmisses"].sibling = None
        o["BranchResteers"].sibling = o["BadSpeculation"]
        o["DSBswitches"].sibling = None
        o["LCP"].sibling = None
        o["MSswitches"].sibling = o["MicroSequencer"]
        o["FrontendBandwidth"].sibling = None
        o["MITE"].sibling = None
        o["DSB"].sibling = None
        o["LSD"].sibling = None
        o["BadSpeculation"].sibling = o["BranchResteers"]
        o["BranchMispredicts"].sibling = None
        o["MachineClears"].sibling = None
        o["Backend_Bound"].sibling = None
        o["MemoryBound"].sibling = None
        o["L1Bound"].sibling = None
        o["DTLB_Overhead"].sibling = None
        o["LoadsBlockedbyStoreForwarding"].sibling = None
        o["SplitLoads"].sibling = None
        o["G4KAliasing"].sibling = None
        o["L2Bound"].sibling = None
        o["L3Bound"].sibling = None
        o["ContestedAccesses"].sibling = None
        o["DataSharing"].sibling = None
        o["L3Latency"].sibling = None
        o["DRAMBound"].sibling = None
        o["MEMBandwidth"].sibling = None
        o["MEMLatency"].sibling = None
        o["LocalDRAM"].sibling = None
        o["RemoteDRAM"].sibling = None
        o["RemoteCache"].sibling = None
        o["StoresBound"].sibling = None
        o["FalseSharing"].sibling = None
        o["SplitStores"].sibling = None
        o["DTLBStoreOverhead"].sibling = None
        o["CoreBound"].sibling = None
        o["DividerActive"].sibling = None
        o["PortsUtilization"].sibling = None
        o["G0_Ports"].sibling = None
        o["G1_Port"].sibling = None
        o["G2_Ports"].sibling = None
        o["G3m_Ports"].sibling = None
        o["Retiring"].sibling = None
        o["BASE"].sibling = None
        o["FP_Arith"].sibling = None
        o["FP_x87"].sibling = None
        o["FP_Scalar"].sibling = None
        o["FP_Vector"].sibling = None
        o["OTHER"].sibling = None
        o["MicroSequencer"].sibling = o["MSswitches"]

        # sampling events (experimential)

        o["FrontendBound"].sample = []
        o["FrontendLatency"].sample = []
        o["ICacheMisses"].sample = []
        o["ITLBmisses"].sample = []
        o["BranchResteers"].sample = ['BR_MISP_RETIRED.ALL_BRANCHES_PS']
        o["DSBswitches"].sample = []
        o["LCP"].sample = []
        o["MSswitches"].sample = []
        o["FrontendBandwidth"].sample = []
        o["MITE"].sample = []
        o["DSB"].sample = []
        o["LSD"].sample = []
        o["BadSpeculation"].sample = []
        o["BranchMispredicts"].sample = []
        o["MachineClears"].sample = []
        o["Backend_Bound"].sample = []
        o["MemoryBound"].sample = []
        o["L1Bound"].sample = []
        o["DTLB_Overhead"].sample = []
        o["LoadsBlockedbyStoreForwarding"].sample = []
        o["SplitLoads"].sample = []
        o["G4KAliasing"].sample = []
        o["L2Bound"].sample = []
        o["L3Bound"].sample = []
        o["ContestedAccesses"].sample = ['MEM_LOAD_UOPS_LLC_HIT_RETIRED.XSNP_HITM_PS', 'MEM_LOAD_UOPS_LLC_HIT_RETIRED.XSNP_MISS_PS']
        o["DataSharing"].sample = ['MEM_LOAD_UOPS_LLC_HIT_RETIRED.XSNP_HIT_PS']
        o["L3Latency"].sample = ['MEM_LOAD_UOPS_RETIRED.LLC_HIT_PS']
        o["DRAMBound"].sample = []
        o["MEMBandwidth"].sample = []
        o["MEMLatency"].sample = []
        o["LocalDRAM"].sample = []
        o["RemoteDRAM"].sample = []
        o["RemoteCache"].sample = []
        o["StoresBound"].sample = []
        o["FalseSharing"].sample = ['MEM_LOAD_UOPS_LLC_HIT_RETIRED.XSNP_HITM_PS']
        o["SplitStores"].sample = ['MEM_UOPS_RETIRED.SPLIT_STORES_PS', 'MEM_UOPS_RETIRED.ALL_STORES_PS']
        o["DTLBStoreOverhead"].sample = []
        o["CoreBound"].sample = []
        o["DividerActive"].sample = []
        o["PortsUtilization"].sample = []
        o["G0_Ports"].sample = []
        o["G1_Port"].sample = []
        o["G2_Ports"].sample = []
        o["G3m_Ports"].sample = []
        o["Retiring"].sample = []
        o["BASE"].sample = []
        o["FP_Arith"].sample = []
        o["FP_x87"].sample = []
        o["FP_Scalar"].sample = []
        o["FP_Vector"].sample = []
        o["OTHER"].sample = []
        o["MicroSequencer"].sample = []

        # user visible metrics

        n = Metric_IPC() ; r.metric(n)
        n = Metric_UPI() ; r.metric(n)
        n = Metric_InstPerTakenBranch() ; r.metric(n)
        n = Metric_DSBCoverage() ; r.metric(n)
        n = Metric_ILP() ; r.metric(n)
        n = Metric_MLP() ; r.metric(n)
        n = Metric_L1dMissLatency() ; r.metric(n)
        n = Metric_TurboUtilization() ; r.metric(n)
