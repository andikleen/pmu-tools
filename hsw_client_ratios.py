
#
# auto generated TopDown description for Intel 4th gen Core (code named Haswell)
# Please see http://ark.intel.com for more details on these CPUs.
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

def BackendBoundAtEXE_stalls(EV, level):
    return ( EV("CYCLE_ACTIVITY.CYCLES_NO_EXECUTE", level) + EV("UOPS_EXECUTED.CYCLES_GE_1_UOPS_EXEC", level) - EV("UOPS_EXECUTED.CYCLES_GE_3_UOPS_EXEC", level) - EV("RS_EVENTS.EMPTY_CYCLES", level) )
def BackendBoundAtEXE(EV, level):
    return BackendBoundAtEXE_stalls(EV, level) / CLKS(EV, level)
def MemBoundFraction(EV, level):
    return ( EV("CYCLE_ACTIVITY.STALLS_LDM_PENDING", level) + EV("RESOURCE_STALLS.SB", level) ) / ( BackendBoundAtEXE_stalls(EV, level) + EV("RESOURCE_STALLS.SB", level) )
def MemL3HitFraction(EV, level):
    return EV("MEM_LOAD_UOPS_RETIRED.L3_HIT", level) / ( EV("MEM_LOAD_UOPS_RETIRED.L3_HIT", level) + MEM_L3_WEIGHT * EV("MEM_LOAD_UOPS_RETIRED.L3_MISS", level) )
def AvgFillBufferLatency(EV, level):
    return EV("L1D_PEND_MISS.PENDING", level) / EV("MEM_LOAD_UOPS_RETIRED.L1_MISS", level)
def MispredClearsFraction(EV, level):
    return EV("BR_MISP_RETIRED.ALL_BRANCHES", level) / ( EV("BR_MISP_RETIRED.ALL_BRANCHES", level) + EV("MACHINE_CLEARS.COUNT", level) )
def RetireUopFraction(EV, level):
    return EV("UOPS_RETIRED.RETIRE_SLOTS", level) / EV("UOPS_ISSUED.ANY", level)
def CLKS(EV, level):
    return EV("CPU_CLK_UNHALTED.THREAD", level)
def SLOTS(EV, level):
    return PipelineWidth * CLKS(EV, level)
def IPC(EV, level):
    return EV("INST_RETIRED.ANY", level) / CLKS(EV, level)
def TurboUtilization(EV, level):
    return CLKS(EV, level) / EV("CPU_CLK_UNHALTED.REF_TSC", level)
def UPI(EV, level):
    return EV("UOPS_RETIRED.RETIRE_SLOTS", level) / EV("INST_RETIRED.ANY", level)

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
             self.val = EV("IDQ_UOPS_NOT_DELIVERED.CORE", 1) / SLOTS(EV, 1)
             self.thresh = (self.val > 0.2)
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
             self.val = PipelineWidth * EV("IDQ_UOPS_NOT_DELIVERED.CYCLES_0_UOPS_DELIV.CORE", 2) / SLOTS(EV, 2)
             self.thresh = (self.val > 0.2) and self.parent.thresh
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
             self.val = EV("ITLB_MISSES.WALK_DURATION", 3) / CLKS(EV, 3)
             self.thresh = (self.val > 0.05) and self.parent.thresh
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
             self.val = EV("DSB2MITE_SWITCHES.PENALTY_CYCLES", 3) / CLKS(EV, 3)
             self.thresh = (self.val > 0.05) and self.parent.thresh
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
             self.val = EV("ILD_STALL.LCP", 3) / CLKS(EV, 3)
             self.thresh = (self.val > 0.05) and self.parent.thresh
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
             self.thresh = (self.val > 0.2) & (IPC(EV, 2) > 2.0) and self.parent.thresh
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
             self.val = EV("IDQ.ALL_MITE_CYCLES_ANY_UOPS", 3) - EV("IDQ.ALL_MITE_CYCLES_4_UOPS", 3)
             self.thresh = (self.val > 0.1) and self.parent.thresh
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
             self.val = EV("IDQ.ALL_DSB_CYCLES_ANY_UOPS", 3) - EV("IDQ.ALL_DSB_CYCLES_4_UOPS", 3)
             self.thresh = (self.val > 0.3) and self.parent.thresh
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
             self.val = ( EV("UOPS_ISSUED.ANY", 1) - EV("UOPS_RETIRED.RETIRE_SLOTS", 1) + PipelineWidth * EV("INT_MISC.RECOVERY_CYCLES", 1) ) / SLOTS(EV, 1)
             self.thresh = (self.val > 0.1)
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
             self.val = MispredClearsFraction(EV, 2) * self.BadSpeculation.compute(EV)
             self.thresh = (self.val > 0.05) and self.parent.thresh
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
             self.thresh = (self.val > 0.05) and self.parent.thresh
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
             self.thresh = (self.val > 0.2)
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
             self.val = MemBoundFraction(EV, 2) * BackendBoundAtEXE(EV, 2)
             self.thresh = (self.val > 0.2) and self.parent.thresh
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
             self.val = ( EV("CYCLE_ACTIVITY.STALLS_LDM_PENDING", 3) - EV("CYCLE_ACTIVITY.STALLS_L1D_PENDING", 3) ) / CLKS(EV, 3)
             self.thresh = ((self.val > 0.07) and self.parent.thresh) | (self.DTLBOverhead.thresh > 0)
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
             self.val = ( MEM_STLB_HIT_COST * EV("DTLB_LOAD_MISSES.STLB_HIT", 4) + EV("DTLB_LOAD_MISSES.WALK_DURATION", 4) ) / CLKS(EV, 4)
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
             self.val = MEM_SFB_COST * EV("LD_BLOCKS.STORE_FORWARD", 4) / CLKS(EV, 4)
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
             self.val = AvgFillBufferLatency(EV, 4) * EV("LD_BLOCKS.NO_SR", 4) / CLKS(EV, 4)
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
             self.val = MEM_4KALIAS_COST * EV("LD_BLOCKS_PARTIAL.ADDRESS_ALIAS", 4)
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
             self.val = ( EV("CYCLE_ACTIVITY.STALLS_L1D_PENDING", 3) - EV("CYCLE_ACTIVITY.STALLS_L2_PENDING", 3) ) / CLKS(EV, 3)
             self.thresh = (self.val > 0.03) and self.parent.thresh
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
             self.val = MemL3HitFraction(EV, 3) * EV("CYCLE_ACTIVITY.STALLS_L2_PENDING", 3) / CLKS(EV, 3)
             self.thresh = (self.val > 0.1) and self.parent.thresh
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
             self.val = MEM_XSNP_HITM_COST * ( EV("MEM_LOAD_UOPS_L3_HIT_RETIRED.XSNP_HITM", 4) + EV("MEM_LOAD_UOPS_L3_HIT_RETIRED.XSNP_MISS", 4) ) / CLKS(EV, 4)
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
             self.val = MEM_XSNP_HIT_COST * EV("MEM_LOAD_UOPS_L3_HIT_RETIRED.XSNP_HIT", 4) / CLKS(EV, 4)
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
             self.val = MEM_XSNP_NONE_COST * EV("MEM_LOAD_UOPS_RETIRED.L3_HIT", 4) / CLKS(EV, 4)
             self.thresh = (self.val > 0.1) and self.parent.thresh
         except ZeroDivisionError:
             self.val = 0
             self.thresh = False
         return self.val

class DRAMBound:
    name = "DRAM Bound"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric represents how often CPU was stalled on main memory (DRAM)."""
    level = 3
    def compute(self, EV):
         try:
             self.val = ( 1 - MemL3HitFraction(EV, 3) ) * EV("CYCLE_ACTIVITY.STALLS_L2_PENDING", 3) / CLKS(EV, 3)
             self.thresh = (self.val > 0.1) and self.parent.thresh
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
             self.val = self.MemoryBound.compute(EV) - ( EV("CYCLE_ACTIVITY.STALLS_LDM_PENDING", 3) / CLKS(EV, 3) )
             self.thresh = (self.val > 0.2) and self.parent.thresh
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
             self.val = MEM_XSNP_HITM_COST * ( EV("MEM_LOAD_UOPS_L3_HIT_RETIRED.XSNP_HITM", 4) + EV("OFFCORE_RESPONSE.DEMAND_RFO.L3_HIT.HITM_OTHER_CORE", 4) ) / CLKS(EV, 4)
             self.thresh = (self.val > 0.2) and self.parent.thresh
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
             self.val = EV("MEM_UOPS_RETIRED.SPLIT_STORES", 4) / EV("MEM_UOPS_RETIRED.ALL_STORES", 4)
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
             self.val = ( MEM_STLB_HIT_COST * EV("DTLB_STORE_MISSES.STLB_HIT", 4) + EV("DTLB_STORE_MISSES.WALK_DURATION", 4) ) / CLKS(EV, 4)
             self.thresh = (self.val > 0.05) and self.parent.thresh
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
             self.val = BackendBoundAtEXE(EV, 2) - self.MemoryBound.compute(EV)
             self.thresh = (self.val > 0.1) and self.parent.thresh
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
             self.val = EV("UOPS_RETIRED.RETIRE_SLOTS", 1) / SLOTS(EV, 1)
             self.thresh = (self.val > 0.6)
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
             self.thresh = ((self.val > 0.7) | (self.MicroSequencer.thresh > 0))
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
             self.val = RetireUopFraction(EV, 2) * EV("IDQ.MS_UOPS", 2) / SLOTS(EV, 2)
             self.thresh = (self.val > 0.05)
         except ZeroDivisionError:
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
        n = FrontendBandwidth() ; r.run(n) ; o["FrontendBandwidth"] = n
        n = MITE() ; r.run(n) ; o["MITE"] = n
        n = DSB() ; r.run(n) ; o["DSB"] = n
        n = BadSpeculation() ; r.run(n) ; o["BadSpeculation"] = n
        n = BranchMispredicts() ; r.run(n) ; o["BranchMispredicts"] = n
        n = MachineClears() ; r.run(n) ; o["MachineClears"] = n
        n = BackendBound() ; r.run(n) ; o["BackendBound"] = n
        n = MemoryBound() ; r.run(n) ; o["MemoryBound"] = n
        n = L1Bound() ; r.run(n) ; o["L1Bound"] = n
        n = DTLBOverhead() ; r.run(n) ; o["DTLBOverhead"] = n
        n = LoadsBlockedbyStoreForwarding() ; r.run(n) ; o["LoadsBlockedbyStoreForwarding"] = n
        n = SplitLoads() ; r.run(n) ; o["SplitLoads"] = n
        n = G4KAliasing() ; r.run(n) ; o["G4KAliasing"] = n
        n = L2Bound() ; r.run(n) ; o["L2Bound"] = n
        n = L3Bound() ; r.run(n) ; o["L3Bound"] = n
        n = ContestedAccesses() ; r.run(n) ; o["ContestedAccesses"] = n
        n = DataSharing() ; r.run(n) ; o["DataSharing"] = n
        n = L3Latency() ; r.run(n) ; o["L3Latency"] = n
        n = DRAMBound() ; r.run(n) ; o["DRAMBound"] = n
        n = StoresBound() ; r.run(n) ; o["StoresBound"] = n
        n = FalseSharing() ; r.run(n) ; o["FalseSharing"] = n
        n = SplitStores() ; r.run(n) ; o["SplitStores"] = n
        n = DTLBStoreOverhead() ; r.run(n) ; o["DTLBStoreOverhead"] = n
        n = CoreBound() ; r.run(n) ; o["CoreBound"] = n
        n = Retiring() ; r.run(n) ; o["Retiring"] = n
        n = BASE() ; r.run(n) ; o["BASE"] = n
        n = MicroSequencer() ; r.run(n) ; o["MicroSequencer"] = n

        # parents
        o["FrontendLatency"].parent = o["FrontendBound"]
        o["ITLBmisses"].parent = o["FrontendLatency"]
        o["DSBswitches"].parent = o["FrontendLatency"]
        o["LCP"].parent = o["FrontendLatency"]
        o["FrontendBandwidth"].parent = o["FrontendBound"]
        o["MITE"].parent = o["FrontendBandwidth"]
        o["DSB"].parent = o["FrontendBandwidth"]
        o["BranchMispredicts"].parent = o["BadSpeculation"]
        o["MachineClears"].parent = o["BadSpeculation"]
        o["MemoryBound"].parent = o["BackendBound"]
        o["L1Bound"].parent = o["MemoryBound"]
        o["DTLBOverhead"].parent = o["L1Bound"]
        o["LoadsBlockedbyStoreForwarding"].parent = o["L1Bound"]
        o["SplitLoads"].parent = o["L1Bound"]
        o["G4KAliasing"].parent = o["L1Bound"]
        o["L2Bound"].parent = o["MemoryBound"]
        o["L3Bound"].parent = o["MemoryBound"]
        o["ContestedAccesses"].parent = o["L3Bound"]
        o["DataSharing"].parent = o["L3Bound"]
        o["L3Latency"].parent = o["L3Bound"]
        o["DRAMBound"].parent = o["MemoryBound"]
        o["StoresBound"].parent = o["MemoryBound"]
        o["FalseSharing"].parent = o["StoresBound"]
        o["SplitStores"].parent = o["StoresBound"]
        o["DTLBStoreOverhead"].parent = o["StoresBound"]
        o["CoreBound"].parent = o["BackendBound"]
        o["BASE"].parent = o["Retiring"]
        o["MicroSequencer"].parent = o["Retiring"]

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
        o["BASE"].Retiring = o["Retiring"]
        o["BASE"].MicroSequencer = o["MicroSequencer"]
