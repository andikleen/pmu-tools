
#
# auto generated description IVB
#


# Constants

PipelineWidth = 4
MEM_L3_WEIGHT = 7
MEM_STLB_HIT_COST = 7
MEM_SFB_COST = 13
MEM_4KALIAS_COST = 5
MEM_XSNP_HITM_COST = 60
MEM_XSNP_HIT_COST = 43
MEM_XSNP_NONE_COST = 29

# Aux. formulas

def BackendBoundAtEXE_stalls(EV):
    return ( EV("CYCLE_ACTIVITY.CYCLES_NO_EXECUTE") + EV("UOPS_EXECUTED.CYCLES_GE_1_UOP_EXEC") - EV("UOPS_EXECUTED.CYCLES_GE_3_UOPS_EXEC") - EV("RS_EVENTS.EMPTY_CYCLES") )
def BackendBoundAtEXE(EV):
    return BackendBoundAtEXE_stalls(EV) / CLKS(EV)
def MemBoundFraction(EV):
    return ( EV("CYCLE_ACTIVITY.STALLS_LDM_PENDING") + EV("RESOURCE_STALLS.SB") ) / ( BackendBoundAtEXE_stalls(EV) + EV("RESOURCE_STALLS.SB") )
def MemL3HitFraction(EV):
    return EV("MEM_LOAD_UOPS_RETIRED.LLC_HIT_PS") / ( EV("MEM_LOAD_UOPS_RETIRED.LLC_HIT_PS") + MEM_L3_WEIGHT * EV("MEM_LOAD_UOPS_RETIRED.LLC_MISS_PS") )
def AvgFillBufferLatency(EV):
    return EV("L1D_PEND_MISS.PENDING") / EV("MEM_LOAD_UOPS_RETIRED.L1_MISS")
def MispredClearsFraction(EV):
    return EV("BR_MISP_RETIRED.ALL_BRANCHES_PS") / ( EV("BR_MISP_RETIRED.ALL_BRANCHES_PS") + EV("MACHINE_CLEARS.COUNT") )
def AvgRsEmptyPeriodClears(EV):
    return ( EV("RS_EVENTS.EMPTY_CYCLES") - EV("ICACHE.IFETCH_STALL") ) / EV("RS_EVENTS.EMPTY_END")
def RetireUopFraction(EV):
    return EV("UOPS_RETIRED.RETIRE_SLOTS") / EV("UOPS_ISSUED.ANY")
def CLKS(EV):
    return EV("CPU_CLK_UNHALTED.THREAD")
def SLOTS(EV):
    return PipelineWidth * CLKS(EV)
def IPC(EV):
    return EV("INST_RETIRED.ANY") / CLKS(EV)
def TurboUtilization(EV):
    return CLKS(EV) / EV("CPU_CLK_UNHALTED.REF_TSC")
def UPI(EV):
    return EV("UOPS_RETIRED.RETIRE_SLOTS") / EV("INST_RETIRED.ANY")

# Event groups

class FrontendBound:
    name = "Frontend Bound"
    domain = "Slots"
    area = "FE"
    desc = """
This category reflects slots where the Frontend of the processor undersupplies
its Backend."""
    level = 1
    def compute(self, EV):
         try:
             self.val = EV("IDQ_UOPS_NOT_DELIVERED.CORE") / SLOTS(EV)
             self.thresh = self.val > 0.2
         except ZeroDivisionError:
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
             self.val = PipelineWidth * EV("IDQ_UOPS_NOT_DELIVERED.CYCLES_0_UOPS_DELIV.CORE") / SLOTS(EV)
             self.thresh = self.val > 0.2 and self.parent.thresh
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class ICacheMisses:
    name = "ICache Misses"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents cycles fraction CPU was stalled due to instruction
cache misses."""
    level = 3
    def compute(self, EV):
         try:
             self.val = ( EV("ICACHE.IFETCH_STALL") - EV("ITLB_MISSES.WALK_DURATION") ) / CLKS(EV)
             self.thresh = self.val > 0.05 and self.parent.thresh
         except ZeroDivisionError:
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
             self.val = EV("ITLB_MISSES.WALK_DURATION") / CLKS(EV)
             self.thresh = self.val > 0.05 and self.parent.thresh
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class BranchResteers:
    name = "Branch Resteers"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents cycles fraction CPU was stalled due to Branch Resteers."""
    level = 3
    def compute(self, EV):
         try:
             self.val = ( EV("BR_MISP_RETIRED.ALL_BRANCHES_PS") + EV("MACHINE_CLEARS.COUNT") + EV("BACLEARS.ANY") ) * AvgRsEmptyPeriodClears(EV) / CLKS(EV)
             self.thresh = self.val > 0.05 and self.parent.thresh
         except ZeroDivisionError:
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
             self.val = EV("DSB2MITE_SWITCHES.PENALTY_CYCLES") / CLKS(EV)
             self.thresh = self.val > 0.05 and self.parent.thresh
         except ZeroDivisionError:
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
             self.val = EV("ILD_STALL.LCP") / CLKS(EV)
             self.thresh = self.val > 0.05 and self.parent.thresh
         except ZeroDivisionError:
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
             self.thresh = self.val > 0.2 and (IPC(EV) > 2.0) and self.parent.thresh
         except ZeroDivisionError:
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
             self.val = EV("IDQ.ALL_MITE_CYCLES_ANY_UOPS") - EV("IDQ.ALL_MITE_CYCLES_4_UOPS")
             self.thresh = self.val > 0.1 and self.parent.thresh
         except ZeroDivisionError:
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
             self.val = EV("IDQ.ALL_DSB_CYCLES_ANY_UOPS") - EV("IDQ.ALL_DSB_CYCLES_4_UOPS")
             self.thresh = self.val > 0.3 and self.parent.thresh
         except ZeroDivisionError:
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
             self.val = ( EV("LSD.CYCLES_ACTIVE") - EV("LSD.CYCLES_4_UOPS") ) / CLKS(EV)
             self.thresh = self.val > 0.1 and self.parent.thresh
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class BadSpeculation:
    name = "Bad Speculation"
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
             self.val = ( EV("UOPS_ISSUED.ANY") - EV("UOPS_RETIRED.RETIRE_SLOTS") + PipelineWidth * EV("INT_MISC.RECOVERY_CYCLES") ) / SLOTS(EV)
             self.thresh = self.val > 0.1
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class BranchMispredicts:
    name = "Branch Mispredicts"
    domain = "Slots"
    area = "BAD"
    desc = """
This metric represents slots fraction CPU was impacted by Branch
Missprediction."""
    level = 2
    def compute(self, EV):
         try:
             self.val = MispredClearsFraction(EV) * self.BadSpeculation.compute(EV)
             self.thresh = self.val > 0.05 and self.parent.thresh
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class MachineClears:
    name = "Machine Clears"
    domain = "Slots"
    area = "BAD"
    desc = """
This metric represents slots fraction CPU was impacted by Machine Clears."""
    level = 2
    def compute(self, EV):
         try:
             self.val = self.BadSpeculation.compute(EV) - self.BranchMispredicts.compute(EV)
             self.thresh = self.val > 0.05 and self.parent.thresh
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class BackendBound:
    name = "Backend Bound"
    domain = "Slots"
    area = "BE"
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

class MemoryBound:
    name = "Memory Bound"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric represents how much Memory subsystem was a bottleneck."""
    level = 2
    def compute(self, EV):
         try:
             self.val = MemBoundFraction(EV) * BackendBoundAtEXE(EV)
             self.thresh = self.val > 0.2 and self.parent.thresh
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class L1Bound:
    name = "L1 Bound"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric represents how often CPU was stalled without missing the L1 data
cache."""
    level = 3
    def compute(self, EV):
         try:
             self.val = ( EV("CYCLE_ACTIVITY.STALLS_LDM_PENDING") - EV("CYCLE_ACTIVITY.STALLS_L1D_PENDING") ) / CLKS(EV)
             self.thresh = (self.val > 0.07 and self.parent.thresh) or (self.DTLBOverhead.compute(EV) > 0)
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class DTLBOverhead:
    name = "DTLB Overhead"
    domain = "Clocks"
    area = "BE/Mem"
    desc = ""
    level = 4
    def compute(self, EV):
         try:
             self.val = ( MEM_STLB_HIT_COST * EV("DTLB_LOAD_MISSES.STLB_HIT") + EV("DTLB_LOAD_MISSES.WALK_DURATION") ) / CLKS(EV)
             self.thresh = self.val > 0.0 and self.parent.thresh
         except ZeroDivisionError:
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
             self.val = MEM_SFB_COST * EV("LD_BLOCKS.STORE_FORWARD") / CLKS(EV)
             self.thresh = self.val > 0.0 and self.parent.thresh
         except ZeroDivisionError:
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
             self.val = AvgFillBufferLatency(EV) * EV("LD_BLOCKS.NO_SR") / CLKS(EV)
             self.thresh = self.val > 0.0 and self.parent.thresh
         except ZeroDivisionError:
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
             self.val = MEM_4KALIAS_COST * EV("LD_BLOCKS_PARTIAL.ADDRESS_ALIAS")
             self.thresh = self.val > 0.0 and self.parent.thresh
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class L2Bound:
    name = "L2 Bound"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric represents how often CPU was stalled on L2 cache."""
    level = 3
    def compute(self, EV):
         try:
             self.val = ( EV("CYCLE_ACTIVITY.STALLS_L1D_PENDING") - EV("CYCLE_ACTIVITY.STALLS_L2_PENDING") ) / CLKS(EV)
             self.thresh = self.val > 0.03 and self.parent.thresh
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class L3Bound:
    name = "L3 Bound"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric represents how often CPU was stalled on L3 cache or contended with
a sibling Core."""
    level = 3
    def compute(self, EV):
         try:
             self.val = MemL3HitFraction(EV) * EV("CYCLE_ACTIVITY.STALLS_L2_PENDING") / CLKS(EV)
             self.thresh = self.val > 0.1 and self.parent.thresh
         except ZeroDivisionError:
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
             self.val = MEM_XSNP_HITM_COST * ( EV("MEM_LOAD_UOPS_LLC_HIT_RETIRED.XSNP_HITM_PS") + EV("MEM_LOAD_UOPS_LLC_HIT_RETIRED.XSNP_MISS_PS") ) / CLKS(EV)
             self.thresh = self.val > 0.0 and self.parent.thresh
         except ZeroDivisionError:
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
             self.val = MEM_XSNP_HIT_COST * EV("MEM_LOAD_UOPS_LLC_HIT_RETIRED.XSNP_HIT_PS") / CLKS(EV)
             self.thresh = self.val > 0.0 and self.parent.thresh
         except ZeroDivisionError:
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
with a sibiling core."""
    level = 4
    def compute(self, EV):
         try:
             self.val = MEM_XSNP_NONE_COST * EV("MEM_LOAD_UOPS_RETIRED.LLC_HIT_PS") / CLKS(EV)
             self.thresh = self.val > 0.1 and self.parent.thresh
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class StoresBound:
    name = "Stores Bound"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric represents how often CPU was stalled on due to store operations."""
    level = 3
    def compute(self, EV):
         try:
             self.val = self.MemoryBound.compute(EV) - ( EV("CYCLE_ACTIVITY.STALLS_LDM_PENDING") / CLKS(EV) )
             self.thresh = self.val > 0.2 and self.parent.thresh
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class FalseSharing:
    name = "False Sharing"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric represents how often CPU was stalled on due to store operations."""
    level = 4
    def compute(self, EV):
         try:
             self.val = MEM_XSNP_HITM_COST * ( EV("MEM_LOAD_UOPS_LLC_HIT_RETIRED.XSNP_HITM_PS") + EV("OFFCORE_RESPONSE.DEMAND_RFO.LLC_HIT.HITM_OTHER_CORE") ) / CLKS(EV)
             self.thresh = self.val > 0.2 and self.parent.thresh
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class SplitStores:
    name = "Split Stores"
    domain = "Stores"
    area = "BE/Mem"
    desc = """
This metric represents rate of split store accesses."""
    level = 4
    def compute(self, EV):
         try:
             self.val = EV("MEM_UOPS_RETIRED.SPLIT_STORES_PS") / EV("MEM_UOPS_RETIRED.ALL_STORES_PS")
             self.thresh = self.val > 0.0 and self.parent.thresh
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class DTLBStoreOverhead:
    name = "DTLB Store Overhead"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric represents cycles fraction spent handling first-level data TLB
store misses."""
    level = 4
    def compute(self, EV):
         try:
             self.val = ( MEM_STLB_HIT_COST * EV("DTLB_STORE_MISSES.STLB_HIT") + EV("DTLB_STORE_MISSES.WALK_DURATION") ) / CLKS(EV)
             self.thresh = self.val > 0.05 and self.parent.thresh
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class CoreBound:
    name = "Core Bound"
    domain = "Clocks"
    area = "BE/Core"
    desc = """
This metric represents how much Core non-memory issues were a bottleneck."""
    level = 2
    def compute(self, EV):
         try:
             self.val = BackendBoundAtEXE(EV) - self.MemoryBound.compute(EV)
             self.thresh = self.val > 0.1 and self.parent.thresh
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class DividerActive:
    name = "Divider Active"
    domain = "Clocks"
    area = "BE/Core"
    desc = ""
    level = 3
    def compute(self, EV):
         try:
             self.val = EV("ARITH.FPU_DIV_ACTIVE") / CLKS(EV)
             self.thresh = self.val > 0.0 and self.parent.thresh
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class PortsUtilization:
    name = "Ports Utilization"
    domain = "Clocks"
    area = "BE/Core"
    desc = """
This metric represents cycles fraction application was stalled due to Core
non-divider-related issues."""
    level = 3
    def compute(self, EV):
         try:
             self.val = self.CoreBound.compute(EV) - self.DividerActive.compute(EV)
             self.thresh = self.val > 0.1 and self.parent.thresh
         except ZeroDivisionError:
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
             self.val = ( EV("CYCLE_ACTIVITY.CYCLES_NO_EXECUTE") - EV("RS_EVENTS.EMPTY_CYCLES") ) / CLKS(EV)
             self.thresh = self.val > 0.1 and self.parent.thresh
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class G1_Port:
    name = "1_Port"
    domain = "Clocks"
    area = "BE/Core"
    desc = """
This metric represents cycles fraction CPU executed total of 1 uop per cycle
on all execution ports."""
    level = 4
    def compute(self, EV):
         try:
             self.val = ( EV("UOPS_EXECUTED.CYCLES_GE_1_UOP_EXEC") - EV("UOPS_EXECUTED.CYCLES_GE_2_UOPS_EXEC") ) / CLKS(EV)
             self.thresh = self.val > 0.1 and self.parent.thresh
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class G2_Ports:
    name = "2_Ports"
    domain = "Clocks"
    area = "BE/Core"
    desc = """
This metric represents cycles fraction CPU executed total of 2 uops per cycle
on all execution ports."""
    level = 4
    def compute(self, EV):
         try:
             self.val = ( EV("UOPS_EXECUTED.CYCLES_GE_2_UOPS_EXEC") - EV("UOPS_EXECUTED.CYCLES_GE_3_UOPS_EXEC") ) / CLKS(EV)
             self.thresh = self.val > 0.1 and self.parent.thresh
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class G3m_Ports:
    name = "3m_Ports"
    domain = "Clocks"
    area = "BE/Core"
    desc = """
This metric represents cycles fraction CPU executed total of 3 or more uops
per cycle on all execution ports."""
    level = 4
    def compute(self, EV):
         try:
             self.val = EV("UOPS_EXECUTED.CYCLES_GE_3_UOPS_EXEC") / CLKS(EV)
             self.thresh = self.val > 0.1 and self.parent.thresh
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class Retiring:
    name = "Retiring"
    domain = "Slots"
    area = "RET"
    desc = """
This category reflects slots utilized by good uops i. Note that a high
Retiring value does not necessary mean there is no room for better
performance. A high Retiring value for non-vectorized code may be a good hint
for programmer to consider vectorizing his code."""
    level = 1
    def compute(self, EV):
         try:
             self.val = EV("UOPS_RETIRED.RETIRE_SLOTS") / SLOTS(EV)
             self.thresh = self.val > 0.6
         except ZeroDivisionError:
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
             self.thresh = (self.val > 0.7 or self.MicroSequencer.compute(EV))
         except ZeroDivisionError:
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
             self.val = self.FP_x87.compute(EV) + self.FP_Scalar.compute(EV) + self.FP_Vector.compute(EV)
             self.thresh = self.val > 0.2 and self.parent.thresh
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class FP_x87:
    name = "FP_x87"
    domain = "Uops"
    area = "RET"
    desc = """
This metric represents floating-point (FP) x87 uops fraction the CPU has
executed."""
    level = 4
    def compute(self, EV):
         try:
             self.val = EV("FP_COMP_OPS_EXE.X87") / EV("UOPS_EXECUTED.THREAD")
             self.thresh = self.val > 0.1 and self.parent.thresh
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class FP_Scalar:
    name = "FP_Scalar"
    domain = "Uops"
    area = "RET"
    desc = """
This metric represents arithmetic floating-point (FP) scalar uops fraction the
CPU has executed."""
    level = 4
    def compute(self, EV):
         try:
             self.val = ( EV("FP_COMP_OPS_EXE.SSE_SCALAR_SINGLE") + EV("FP_COMP_OPS_EXE.SSE_SCALAR_DOUBLE") ) / EV("UOPS_EXECUTED.THREAD")
             self.thresh = self.val > 0.1 and self.parent.thresh
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class FP_Vector:
    name = "FP_Vector"
    domain = "Uops"
    area = "RET"
    desc = """
This metric represents arithmetic floating-point (FP) vector uops fraction the
CPU has executed."""
    level = 4
    def compute(self, EV):
         try:
             self.val = ( EV("FP_COMP_OPS_EXE.SSE_PACKED_DOUBLE") + EV("FP_COMP_OPS_EXE.SSE_PACKED_SINGLE") + EV("SIMD_FP_256.PACKED_SINGLE") + EV("SIMD_FP_256.PACKED_DOUBLE") ) / EV("UOPS_EXECUTED.THREAD")
             self.thresh = self.val > 0.2 and self.parent.thresh
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class OTHER:
    name = "OTHER"
    domain = "Uops"
    area = "RET"
    desc = """
This metric represents non-floating-point (FP) uop fraction the CPU has
executed."""
    level = 3
    def compute(self, EV):
         try:
             self.val = 1 - self.FP_Arith.compute(EV) - EV("IDQ.MS_UOPS") / EV("UOPS_EXECUTED.THREAD")
             self.thresh = self.val > 0.3 and self.parent.thresh
         except ZeroDivisionError:
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
             self.val = RetireUopFraction(EV) * EV("IDQ.MS_UOPS") / SLOTS(EV)
             self.thresh = self.val > 0.05
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val


# Schedule

class Setup:
    def __init__(self, r):
        prev = None
        o = dict()
        n = FrontendBound() ; r.run(n) ; n.parent = prev ; prev = n
        o["FrontendBound"] = n
        n = FrontendLatency() ; r.run(n) ; n.parent = prev ; prev = n
        o["FrontendLatency"] = n
        n = ICacheMisses() ; r.run(n) ; n.parent = prev ; prev = n
        o["ICacheMisses"] = n
        n = ITLBmisses() ; r.run(n) ; n.parent = prev ; prev = n
        o["ITLBmisses"] = n
        n = BranchResteers() ; r.run(n) ; n.parent = prev ; prev = n
        o["BranchResteers"] = n
        n = DSBswitches() ; r.run(n) ; n.parent = prev ; prev = n
        o["DSBswitches"] = n
        n = LCP() ; r.run(n) ; n.parent = prev ; prev = n
        o["LCP"] = n
        n = FrontendBandwidth() ; r.run(n) ; n.parent = prev ; prev = n
        o["FrontendBandwidth"] = n
        n = MITE() ; r.run(n) ; n.parent = prev ; prev = n
        o["MITE"] = n
        n = DSB() ; r.run(n) ; n.parent = prev ; prev = n
        o["DSB"] = n
        n = LSD() ; r.run(n) ; n.parent = prev ; prev = n
        o["LSD"] = n
        n = BadSpeculation() ; r.run(n) ; n.parent = prev ; prev = n
        o["BadSpeculation"] = n
        n = BranchMispredicts() ; r.run(n) ; n.parent = prev ; prev = n
        o["BranchMispredicts"] = n
        n = MachineClears() ; r.run(n) ; n.parent = prev ; prev = n
        o["MachineClears"] = n
        n = BackendBound() ; r.run(n) ; n.parent = prev ; prev = n
        o["BackendBound"] = n
        n = MemoryBound() ; r.run(n) ; n.parent = prev ; prev = n
        o["MemoryBound"] = n
        n = L1Bound() ; r.run(n) ; n.parent = prev ; prev = n
        o["L1Bound"] = n
        n = DTLBOverhead() ; r.run(n) ; n.parent = prev ; prev = n
        o["DTLBOverhead"] = n
        n = LoadsBlockedbyStoreForwarding() ; r.run(n) ; n.parent = prev ; prev = n
        o["LoadsBlockedbyStoreForwarding"] = n
        n = SplitLoads() ; r.run(n) ; n.parent = prev ; prev = n
        o["SplitLoads"] = n
        n = G4KAliasing() ; r.run(n) ; n.parent = prev ; prev = n
        o["G4KAliasing"] = n
        n = L2Bound() ; r.run(n) ; n.parent = prev ; prev = n
        o["L2Bound"] = n
        n = L3Bound() ; r.run(n) ; n.parent = prev ; prev = n
        o["L3Bound"] = n
        n = ContestedAccesses() ; r.run(n) ; n.parent = prev ; prev = n
        o["ContestedAccesses"] = n
        n = DataSharing() ; r.run(n) ; n.parent = prev ; prev = n
        o["DataSharing"] = n
        n = L3Latency() ; r.run(n) ; n.parent = prev ; prev = n
        o["L3Latency"] = n
        n = StoresBound() ; r.run(n) ; n.parent = prev ; prev = n
        o["StoresBound"] = n
        n = FalseSharing() ; r.run(n) ; n.parent = prev ; prev = n
        o["FalseSharing"] = n
        n = SplitStores() ; r.run(n) ; n.parent = prev ; prev = n
        o["SplitStores"] = n
        n = DTLBStoreOverhead() ; r.run(n) ; n.parent = prev ; prev = n
        o["DTLBStoreOverhead"] = n
        n = CoreBound() ; r.run(n) ; n.parent = prev ; prev = n
        o["CoreBound"] = n
        n = DividerActive() ; r.run(n) ; n.parent = prev ; prev = n
        o["DividerActive"] = n
        n = PortsUtilization() ; r.run(n) ; n.parent = prev ; prev = n
        o["PortsUtilization"] = n
        n = G0_Ports() ; r.run(n) ; n.parent = prev ; prev = n
        o["G0_Ports"] = n
        n = G1_Port() ; r.run(n) ; n.parent = prev ; prev = n
        o["G1_Port"] = n
        n = G2_Ports() ; r.run(n) ; n.parent = prev ; prev = n
        o["G2_Ports"] = n
        n = G3m_Ports() ; r.run(n) ; n.parent = prev ; prev = n
        o["G3m_Ports"] = n
        n = Retiring() ; r.run(n) ; n.parent = prev ; prev = n
        o["Retiring"] = n
        n = BASE() ; r.run(n) ; n.parent = prev ; prev = n
        o["BASE"] = n
        n = FP_Arith() ; r.run(n) ; n.parent = prev ; prev = n
        o["FP_Arith"] = n
        n = FP_x87() ; r.run(n) ; n.parent = prev ; prev = n
        o["FP_x87"] = n
        n = FP_Scalar() ; r.run(n) ; n.parent = prev ; prev = n
        o["FP_Scalar"] = n
        n = FP_Vector() ; r.run(n) ; n.parent = prev ; prev = n
        o["FP_Vector"] = n
        n = OTHER() ; r.run(n) ; n.parent = prev ; prev = n
        o["OTHER"] = n
        n = MicroSequencer() ; r.run(n) ; n.parent = prev ; prev = n
        o["MicroSequencer"] = n

        # references between groups

        o["FrontendBandwidth"].FrontendBound = o["FrontendBound"]
        o["FrontendBandwidth"].FrontendLatency = o["FrontendLatency"]
        o["BranchMispredicts"].BadSpeculation = o["BadSpeculation"]
        o["MachineClears"].BadSpeculation = o["BadSpeculation"]
        o["MachineClears"].BranchMispredicts = o["BranchMispredicts"]
        o["BackendBound"].FrontendBound = o["FrontendBound"]
        o["BackendBound"].BadSpeculation = o["BadSpeculation"]
        o["BackendBound"].Retiring = o["Retiring"]
        o["L1Bound"].DTLBOverhead = o["DTLBOverhead"]
        o["StoresBound"].MemoryBound = o["MemoryBound"]
        o["CoreBound"].MemoryBound = o["MemoryBound"]
        o["PortsUtilization"].CoreBound = o["CoreBound"]
        o["PortsUtilization"].DividerActive = o["DividerActive"]
        o["BASE"].Retiring = o["Retiring"]
        o["BASE"].MicroSequencer = o["MicroSequencer"]
        o["FP_Arith"].FP_x87 = o["FP_x87"]
        o["FP_Arith"].FP_Scalar = o["FP_Scalar"]
        o["FP_Arith"].FP_Vector = o["FP_Vector"]
        o["OTHER"].FP_Arith = o["FP_Arith"]
