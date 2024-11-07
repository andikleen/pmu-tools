# -*- coding: latin-1 -*-
#
# auto generated TopDown/TMA 5.01-full-perf description for Intel 4rd gen Core (code named Haswell)
# Please see http://ark.intel.com for more details on these CPUs.
#
# References:
# http://bit.ly/tma-ispass14
# http://halobates.de/blog/p/262
# https://sites.google.com/site/analysismethods/yasin-pubs
# https://download.01.org/perfmon/
# https://github.com/andikleen/pmu-tools/wiki/toplev-manual
#

# Helpers

print_error = lambda msg: False
smt_enabled = False
ebs_mode = False
version = "5.01-full-perf"
base_frequency = -1.0
Memory = 0
Average_Frequency = 0.0
num_cores = 1
num_threads = 1
num_sockets = 1


def handle_error(obj, msg):
    print_error(msg)
    obj.errcount += 1
    obj.val = 0
    obj.thresh = False

def handle_error_metric(obj, msg):
    print_error(msg)
    obj.errcount += 1
    obj.val = 0



# Constants

Exe_Ports = 8
Mem_L2_Store_Cost = 9
Mem_L3_Weight = 7
Mem_STLB_Hit_Cost = 8
BAClear_Cost = 12
MS_Switches_Cost = 2
Avg_Assist_Cost = 66
Pipeline_Width = 4
DSB_Width = 4
OneMillion = 1000000
OneBillion = 1000000000
Energy_Unit = 61
EBS_Mode = 0
DS = 0

# Aux. formulas


def Backend_Bound_Cycles(self, EV, level):
    return (STALLS_TOTAL(self, EV, level) + (EV("UOPS_EXECUTED.CORE:c1", level) - Few_Uops_Executed_Threshold(self, EV, level)) / 2 - Frontend_RS_Empty_Cycles(self, EV, level) + EV("RESOURCE_STALLS.SB", level)) if smt_enabled else(STALLS_TOTAL(self, EV, level) + EV("UOPS_EXECUTED.CORE:c1", level) - Few_Uops_Executed_Threshold(self, EV, level) - Frontend_RS_Empty_Cycles(self, EV, level) + EV("RESOURCE_STALLS.SB", level))

def Cycles_0_Ports_Utilized(self, EV, level):
    return (EV("UOPS_EXECUTED.CORE:i1:c1", level)) / 2 if smt_enabled else(STALLS_TOTAL(self, EV, level) - Frontend_RS_Empty_Cycles(self, EV, level))

def Cycles_1_Port_Utilized(self, EV, level):
    return (EV("UOPS_EXECUTED.CORE:c1", level) - EV("UOPS_EXECUTED.CORE:c2", level)) / 2 if smt_enabled else(EV("UOPS_EXECUTED.CORE:c1", level) - EV("UOPS_EXECUTED.CORE:c2", level))

def Cycles_2_Ports_Utilized(self, EV, level):
    return (EV("UOPS_EXECUTED.CORE:c2", level) - EV("UOPS_EXECUTED.CORE:c3", level)) / 2 if smt_enabled else(EV("UOPS_EXECUTED.CORE:c2", level) - EV("UOPS_EXECUTED.CORE:c3", level))

def Cycles_3m_Ports_Utilized(self, EV, level):
    return (EV("UOPS_EXECUTED.CORE:c3", level) / 2) if smt_enabled else EV("UOPS_EXECUTED.CORE:c3", level)

def DurationTimeInSeconds(self, EV, level):
    return EV("interval-ms", 0) / 1000

def Execute_Cycles(self, EV, level):
    return (EV("UOPS_EXECUTED.CORE:c1", level) / 2) if smt_enabled else EV("UOPS_EXECUTED.CORE:c1", level)

def Fetched_Uops(self, EV, level):
    return (EV("IDQ.DSB_UOPS", level) + EV("LSD.UOPS", level) + EV("IDQ.MITE_UOPS", level) + EV("IDQ.MS_UOPS", level))

def Few_Uops_Executed_Threshold(self, EV, level):
    EV("UOPS_EXECUTED.CORE:c2", level)
    EV("UOPS_EXECUTED.CORE:c3", level)
    return EV("UOPS_EXECUTED.CORE:c3", level) if (IPC(self, EV, level)> 1.8) else EV("UOPS_EXECUTED.CORE:c2", level)

def Frontend_RS_Empty_Cycles(self, EV, level):
    EV("RS_EVENTS.EMPTY_CYCLES", level)
    return EV("RS_EVENTS.EMPTY_CYCLES", level) if (self.Fetch_Latency.compute(EV)> 0.1) else 0

def Frontend_Latency_Cycles(self, EV, level):
    return EV(lambda EV , level : min(EV("CPU_CLK_UNHALTED.THREAD", level) , EV("IDQ_UOPS_NOT_DELIVERED.CYCLES_0_UOPS_DELIV.CORE", level)) , level )

def HighIPC(self, EV, level):
    val = IPC(self, EV, level) / Pipeline_Width
    return val

def ITLB_Miss_Cycles(self, EV, level):
    return (14 * EV("ITLB_MISSES.STLB_HIT", level) + EV("ITLB_MISSES.WALK_DURATION", level))

def LOAD_L1_MISS(self, EV, level):
    return EV("MEM_LOAD_UOPS_RETIRED.L2_HIT", level) + EV("MEM_LOAD_UOPS_RETIRED.L3_HIT", level) + EV("MEM_LOAD_UOPS_L3_HIT_RETIRED.XSNP_HIT", level) + EV("MEM_LOAD_UOPS_L3_HIT_RETIRED.XSNP_HITM", level) + EV("MEM_LOAD_UOPS_L3_HIT_RETIRED.XSNP_MISS", level)

def LOAD_L1_MISS_NET(self, EV, level):
    return LOAD_L1_MISS(self, EV, level) + EV("MEM_LOAD_UOPS_RETIRED.L3_MISS", level)

def LOAD_L3_HIT(self, EV, level):
    return EV("MEM_LOAD_UOPS_RETIRED.L3_HIT", level) * (1 + EV("MEM_LOAD_UOPS_RETIRED.HIT_LFB", level) / LOAD_L1_MISS_NET(self, EV, level))

def LOAD_XSNP_HIT(self, EV, level):
    return EV("MEM_LOAD_UOPS_L3_HIT_RETIRED.XSNP_HIT", level) * (1 + EV("MEM_LOAD_UOPS_RETIRED.HIT_LFB", level) / LOAD_L1_MISS_NET(self, EV, level))

def LOAD_XSNP_HITM(self, EV, level):
    return EV("MEM_LOAD_UOPS_L3_HIT_RETIRED.XSNP_HITM", level) * (1 + EV("MEM_LOAD_UOPS_RETIRED.HIT_LFB", level) / LOAD_L1_MISS_NET(self, EV, level))

def LOAD_XSNP_MISS(self, EV, level):
    return EV("MEM_LOAD_UOPS_L3_HIT_RETIRED.XSNP_MISS", level) * (1 + EV("MEM_LOAD_UOPS_RETIRED.HIT_LFB", level) / LOAD_L1_MISS_NET(self, EV, level))

def Mem_L3_Hit_Fraction(self, EV, level):
    return EV("MEM_LOAD_UOPS_RETIRED.L3_HIT", level) / (EV("MEM_LOAD_UOPS_RETIRED.L3_HIT", level) + Mem_L3_Weight * EV("MEM_LOAD_UOPS_RETIRED.L3_MISS", level))

def Mem_Lock_St_Fraction(self, EV, level):
    return EV("MEM_UOPS_RETIRED.LOCK_LOADS", level) / EV("MEM_UOPS_RETIRED.ALL_STORES", level)

def Memory_Bound_Fraction(self, EV, level):
    return (STALLS_MEM_ANY(self, EV, level) + EV("RESOURCE_STALLS.SB", level)) / Backend_Bound_Cycles(self, EV, level)

def Mispred_Clears_Fraction(self, EV, level):
    return EV("BR_MISP_RETIRED.ALL_BRANCHES", level) / (EV("BR_MISP_RETIRED.ALL_BRANCHES", level) + EV("MACHINE_CLEARS.COUNT", level))

def ORO_Demand_RFO_C1(self, EV, level):
    return EV(lambda EV , level : min(EV("CPU_CLK_UNHALTED.THREAD", level) , EV("OFFCORE_REQUESTS_OUTSTANDING.CYCLES_WITH_DEMAND_RFO", level)) , level )

def ORO_DRD_Any_Cycles(self, EV, level):
    return EV(lambda EV , level : min(EV("CPU_CLK_UNHALTED.THREAD", level) , EV("OFFCORE_REQUESTS_OUTSTANDING.CYCLES_WITH_DATA_RD", level)) , level )

def ORO_DRD_BW_Cycles(self, EV, level):
    return EV(lambda EV , level : min(EV("CPU_CLK_UNHALTED.THREAD", level) , EV("OFFCORE_REQUESTS_OUTSTANDING.ALL_DATA_RD:c6", level)) , level )

def SQ_Full_Cycles(self, EV, level):
    return (EV("OFFCORE_REQUESTS_BUFFER.SQ_FULL", level) / 2) if smt_enabled else EV("OFFCORE_REQUESTS_BUFFER.SQ_FULL", level)

def STALLS_MEM_ANY(self, EV, level):
    return EV(lambda EV , level : min(EV("CPU_CLK_UNHALTED.THREAD", level) , EV("CYCLE_ACTIVITY.STALLS_LDM_PENDING", level)) , level )

def STALLS_TOTAL(self, EV, level):
    return EV(lambda EV , level : min(EV("CPU_CLK_UNHALTED.THREAD", level) , EV("CYCLE_ACTIVITY.CYCLES_NO_EXECUTE", level)) , level )

def Store_L2_Hit_Cycles(self, EV, level):
    return EV("L2_RQSTS.RFO_HIT", level) * Mem_L2_Store_Cost *(1 - Mem_Lock_St_Fraction(self, EV, level))

def Mem_XSNP_HitM_Cost(self, EV, level):
    return 60

def Mem_XSNP_Hit_Cost(self, EV, level):
    return 43

def Mem_XSNP_None_Cost(self, EV, level):
    return 29

def Recovery_Cycles(self, EV, level):
    return (EV("INT_MISC.RECOVERY_CYCLES_ANY", level) / 2) if smt_enabled else EV("INT_MISC.RECOVERY_CYCLES", level)

def Retire_Fraction(self, EV, level):
    return Retired_Slots(self, EV, level) / EV("UOPS_ISSUED.ANY", level)

def Retired_Slots(self, EV, level):
    return EV("UOPS_RETIRED.RETIRE_SLOTS", level)

# Number of logical processors (enabled or online) on the target system
def Num_CPUs(self, EV, level):
    return 8 if smt_enabled else 4

# Instructions Per Cycle (per Logical Processor)
def IPC(self, EV, level):
    return EV("INST_RETIRED.ANY", level) / CLKS(self, EV, level)

# Uops Per Instruction
def UopPI(self, EV, level):
    val = Retired_Slots(self, EV, level) / EV("INST_RETIRED.ANY", level)
    self.thresh = (val > 1.05)
    return val

# Uops per taken branch
def UpTB(self, EV, level):
    val = Retired_Slots(self, EV, level) / EV("BR_INST_RETIRED.NEAR_TAKEN", level)
    self.thresh = val < Pipeline_Width * 1.5
    return val

# Cycles Per Instruction (per Logical Processor)
def CPI(self, EV, level):
    return 1 / IPC(self, EV, level)

# Per-Logical Processor actual clocks when the Logical Processor is active.
def CLKS(self, EV, level):
    return EV("CPU_CLK_UNHALTED.THREAD", level)

# Total issue-pipeline slots (per-Physical Core till ICL; per-Logical Processor ICL onward)
def SLOTS(self, EV, level):
    return Pipeline_Width * CORE_CLKS(self, EV, level)

# Instructions Per Cycle across hyper-threads (per physical core)
def CoreIPC(self, EV, level):
    return EV("INST_RETIRED.ANY", level) / CORE_CLKS(self, EV, level)

# Instruction-Level-Parallelism (average number of uops executed when there is execution) per thread (logical-processor)
def ILP(self, EV, level):
    return (EV("UOPS_EXECUTED.CORE", level) / 2 / Execute_Cycles(self, EV, level)) if smt_enabled else EV("UOPS_EXECUTED.CORE", level) / Execute_Cycles(self, EV, level)

# Core actual clocks when any Logical Processor is active on the Physical Core
def CORE_CLKS(self, EV, level):
    return ((EV("CPU_CLK_UNHALTED.THREAD", level) / 2) * (1 + EV("CPU_CLK_UNHALTED.ONE_THREAD_ACTIVE", level) / EV("CPU_CLK_UNHALTED.REF_XCLK", level))) if ebs_mode else(EV("CPU_CLK_UNHALTED.THREAD_ANY", level) / 2) if smt_enabled else CLKS(self, EV, level)

# Instructions per Load (lower number means higher occurrence rate). Tip: reduce memory accesses. #Link Opt Guide section: Minimize Register Spills
def IpLoad(self, EV, level):
    val = EV("INST_RETIRED.ANY", level) / EV("MEM_UOPS_RETIRED.ALL_LOADS", level)
    self.thresh = (val < 3)
    return val

# Instructions per Store (lower number means higher occurrence rate). Tip: reduce memory accesses. #Link Opt Guide section: Minimize Register Spills
def IpStore(self, EV, level):
    val = EV("INST_RETIRED.ANY", level) / EV("MEM_UOPS_RETIRED.ALL_STORES", level)
    self.thresh = (val < 8)
    return val

# Instructions per Branch (lower number means higher occurrence rate)
def IpBranch(self, EV, level):
    val = EV("INST_RETIRED.ANY", level) / EV("BR_INST_RETIRED.ALL_BRANCHES", level)
    self.thresh = (val < 8)
    return val

# Instructions per (near) call (lower number means higher occurrence rate)
def IpCall(self, EV, level):
    val = EV("INST_RETIRED.ANY", level) / EV("BR_INST_RETIRED.NEAR_CALL", level)
    self.thresh = (val < 200)
    return val

# Instructions per taken branch
def IpTB(self, EV, level):
    val = EV("INST_RETIRED.ANY", level) / EV("BR_INST_RETIRED.NEAR_TAKEN", level)
    self.thresh = val < Pipeline_Width * 2 + 1
    return val

# Branch instructions per taken branch. . Can be used to approximate PGO-likelihood for non-loopy codes.
def BpTkBranch(self, EV, level):
    return EV("BR_INST_RETIRED.ALL_BRANCHES", level) / EV("BR_INST_RETIRED.NEAR_TAKEN", level)

# Total number of retired Instructions
def Instructions(self, EV, level):
    return EV("INST_RETIRED.ANY", level)

# Average number of Uops retired in cycles where at least one uop has retired.
def Retire(self, EV, level):
    return Retired_Slots(self, EV, level) / EV("UOPS_RETIRED.RETIRE_SLOTS:c1", level)

# Fraction of Uops delivered by the DSB (aka Decoded ICache; or Uop Cache). See section 'Decoded ICache' in Optimization Manual. http://www.intel.com/content/www/us/en/architecture-and-technology/64-ia-32-architectures-optimization-manual.html
def DSB_Coverage(self, EV, level):
    val = EV("IDQ.DSB_UOPS", level) / Fetched_Uops(self, EV, level)
    self.thresh = (val < 0.7) and HighIPC(self, EV, 1)
    return val

# Taken Branches retired Per Cycle
def TBpC(self, EV, level):
    return EV("BR_INST_RETIRED.NEAR_TAKEN", level) / CLKS(self, EV, level)

# Instructions per speculative Unknown Branch Misprediction (BAClear) (lower number means higher occurrence rate)
def IpUnknown_Branch(self, EV, level):
    return Instructions(self, EV, level) / EV("BACLEARS.ANY", level)

# Number of Instructions per non-speculative Branch Misprediction (JEClear) (lower number means higher occurrence rate)
def IpMispredict(self, EV, level):
    val = EV("INST_RETIRED.ANY", level) / EV("BR_MISP_RETIRED.ALL_BRANCHES", level)
    self.thresh = (val < 200)
    return val

# Instructions per retired Mispredicts for indirect CALL or JMP branches (lower number means higher occurrence rate).
def IpMisp_Indirect(self, EV, level):
    val = Instructions(self, EV, level) / (Retire_Fraction(self, EV, level) * EV("BR_MISP_EXEC.INDIRECT", level))
    self.thresh = (val < 1000)
    return val

# Actual Average Latency for L1 data-cache miss demand load operations (in core cycles)
def Load_Miss_Real_Latency(self, EV, level):
    return EV("L1D_PEND_MISS.PENDING", level) / (EV("MEM_LOAD_UOPS_RETIRED.L1_MISS", level) + EV("MEM_LOAD_UOPS_RETIRED.HIT_LFB", level))

# Memory-Level-Parallelism (average number of L1 miss demand load when there is at least one such miss. Per-Logical Processor)
def MLP(self, EV, level):
    return EV("L1D_PEND_MISS.PENDING", level) / EV("L1D_PEND_MISS.PENDING_CYCLES", level)

# L1 cache true misses per kilo instruction for retired demand loads
def L1MPKI(self, EV, level):
    return 1000 * EV("MEM_LOAD_UOPS_RETIRED.L1_MISS", level) / EV("INST_RETIRED.ANY", level)

# L2 cache true misses per kilo instruction for retired demand loads
def L2MPKI(self, EV, level):
    return 1000 * EV("MEM_LOAD_UOPS_RETIRED.L2_MISS", level) / EV("INST_RETIRED.ANY", level)

# Offcore requests (L2 cache miss) per kilo instruction for demand RFOs
def L2MPKI_RFO(self, EV, level):
    return 1000 * EV("OFFCORE_REQUESTS.DEMAND_RFO", level) / EV("INST_RETIRED.ANY", level)

# L3 cache true misses per kilo instruction for retired demand loads
def L3MPKI(self, EV, level):
    return 1000 * EV("MEM_LOAD_UOPS_RETIRED.L3_MISS", level) / EV("INST_RETIRED.ANY", level)

# Average per-thread data fill bandwidth to the L1 data cache [GB / sec]
def L1D_Cache_Fill_BW(self, EV, level):
    return 64 * EV("L1D.REPLACEMENT", level) / OneBillion / Time(self, EV, level)

# Average per-thread data fill bandwidth to the L2 cache [GB / sec]
def L2_Cache_Fill_BW(self, EV, level):
    return 64 * EV("L2_LINES_IN.ALL", level) / OneBillion / Time(self, EV, level)

# Average per-thread data fill bandwidth to the L3 cache [GB / sec]
def L3_Cache_Fill_BW(self, EV, level):
    return 64 * EV("LONGEST_LAT_CACHE.MISS", level) / OneBillion / Time(self, EV, level)

# Utilization of the core's Page Walker(s) serving STLB misses triggered by instruction/Load/Store accesses
def Page_Walks_Utilization(self, EV, level):
    val = (EV("ITLB_MISSES.WALK_DURATION", level) + EV("DTLB_LOAD_MISSES.WALK_DURATION", level) + EV("DTLB_STORE_MISSES.WALK_DURATION", level)) / CORE_CLKS(self, EV, level)
    self.thresh = (val > 0.5)
    return val

# Average per-core data fill bandwidth to the L1 data cache [GB / sec]
def L1D_Cache_Fill_BW_2T(self, EV, level):
    return L1D_Cache_Fill_BW(self, EV, level)

# Average per-core data fill bandwidth to the L2 cache [GB / sec]
def L2_Cache_Fill_BW_2T(self, EV, level):
    return L2_Cache_Fill_BW(self, EV, level)

# Average per-core data fill bandwidth to the L3 cache [GB / sec]
def L3_Cache_Fill_BW_2T(self, EV, level):
    return L3_Cache_Fill_BW(self, EV, level)

# Average Latency for L2 cache miss demand Loads
def Load_L2_Miss_Latency(self, EV, level):
    return EV("OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD", level) / EV("OFFCORE_REQUESTS.DEMAND_DATA_RD", level)

# Average Parallel L2 cache miss demand Loads
def Load_L2_MLP(self, EV, level):
    return EV("OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD", level) / EV("OFFCORE_REQUESTS_OUTSTANDING.CYCLES_WITH_DEMAND_DATA_RD", level)

# Average Parallel L2 cache miss data reads
def Data_L2_MLP(self, EV, level):
    return EV("OFFCORE_REQUESTS_OUTSTANDING.ALL_DATA_RD", level) / EV("OFFCORE_REQUESTS_OUTSTANDING.CYCLES_WITH_DATA_RD", level)

# Average CPU Utilization (percentage)
def CPU_Utilization(self, EV, level):
    return CPUs_Utilized(self, EV, level) / Num_CPUs(self, EV, level)

# Average number of utilized CPUs
def CPUs_Utilized(self, EV, level):
    return EV("CPU_CLK_UNHALTED.REF_TSC", level) / EV("msr/tsc/", 0)

# Measured Average Core Frequency for unhalted processors [GHz]
def Core_Frequency(self, EV, level):
    return Turbo_Utilization(self, EV, level) * EV("msr/tsc/", 0) / OneBillion / Time(self, EV, level)

# Average Frequency Utilization relative nominal frequency
def Turbo_Utilization(self, EV, level):
    return CLKS(self, EV, level) / EV("CPU_CLK_UNHALTED.REF_TSC", level)

# Fraction of cycles where both hardware Logical Processors were active
def SMT_2T_Utilization(self, EV, level):
    return 1 - EV("CPU_CLK_UNHALTED.ONE_THREAD_ACTIVE", level) / (EV("CPU_CLK_UNHALTED.REF_XCLK_ANY", level) / 2) if smt_enabled else 0

# Fraction of cycles spent in the Operating System (OS) Kernel mode
def Kernel_Utilization(self, EV, level):
    val = EV("CPU_CLK_UNHALTED.THREAD_P:SUP", level) / EV("CPU_CLK_UNHALTED.THREAD", level)
    self.thresh = (val > 0.05)
    return val

# Cycles Per Instruction for the Operating System (OS) Kernel mode
def Kernel_CPI(self, EV, level):
    return EV("CPU_CLK_UNHALTED.THREAD_P:SUP", level) / EV("INST_RETIRED.ANY_P:SUP", level)

# Average external Memory Bandwidth Use for reads and writes [GB / sec]
def DRAM_BW_Use(self, EV, level):
    return 64 *(EV("UNC_ARB_TRK_REQUESTS.ALL", level) + EV("UNC_ARB_COH_TRK_REQUESTS.ALL", level)) / OneMillion / Time(self, EV, level) / 1000

# Total package Power in Watts
def Power(self, EV, level):
    return EV("UNC_PKG_ENERGY_STATUS", level) * Energy_Unit /(Time(self, EV, level) * OneMillion )

# Run duration time in seconds
def Time(self, EV, level):
    val = EV("interval-s", 0)
    self.thresh = (val < 1)
    return val

# Socket actual clocks when any core is active on that socket
def Socket_CLKS(self, EV, level):
    return EV("UNC_CLOCK.SOCKET", level)

# Instructions per Far Branch ( Far Branches apply upon transition from application to operating system, handling interrupts, exceptions) [lower number means higher occurrence rate]
def IpFarBranch(self, EV, level):
    val = EV("INST_RETIRED.ANY", level) / EV("BR_INST_RETIRED.FAR_BRANCH:USER", level)
    self.thresh = (val < 1000000)
    return val

# Event groups


class Frontend_Bound:
    name = "Frontend_Bound"
    domain = "Slots"
    area = "FE"
    level = 1
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvFB', 'BvIO', 'TmaL1', 'PGO'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("IDQ_UOPS_NOT_DELIVERED.CORE", 1) / SLOTS(self, EV, 1)
            self.thresh = (self.val > 0.15)
        except ZeroDivisionError:
            handle_error(self, "Frontend_Bound zero division")
        return self.val
    desc = """
This category represents fraction of slots where the
processor's Frontend undersupplies its Backend. Frontend
denotes the first part of the processor core responsible to
fetch operations that are executed later on by the Backend
part. Within the Frontend; a branch predictor predicts the
next address to fetch; cache-lines are fetched from the
memory subsystem; parsed into instructions; and lastly
decoded into micro-operations (uops). Ideally the Frontend
can issue Pipeline_Width uops every cycle to the Backend.
Frontend Bound denotes unutilized issue-slots when there is
no Backend stall; i.e. bubbles where Frontend delivered no
uops while Backend could have accepted them. For example;
stalls due to instruction-cache misses would be categorized
under Frontend Bound."""


class Fetch_Latency:
    name = "Fetch_Latency"
    domain = "Slots"
    area = "FE"
    level = 2
    htoff = False
    sample = ['RS_EVENTS.EMPTY_END']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['Frontend', 'TmaL2'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = Pipeline_Width * Frontend_Latency_Cycles(self, EV, 2) / SLOTS(self, EV, 2)
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Fetch_Latency zero division")
        return self.val
    desc = """
This metric represents fraction of slots the CPU was stalled
due to Frontend latency issues.  For example; instruction-
cache misses; iTLB misses or fetch stalls after a branch
misprediction are categorized under Frontend Latency. In
such cases; the Frontend eventually delivers no uops for
some period."""


class ICache_Misses:
    name = "ICache_Misses"
    domain = "Clocks"
    area = "FE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BigFootprint', 'BvBC', 'FetchLat', 'IcMiss'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("ICACHE.IFDATA_STALL", 3) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "ICache_Misses zero division")
        return self.val
    desc = """
This metric represents fraction of cycles the CPU was
stalled due to instruction cache misses.. Using compiler's
Profile-Guided Optimization (PGO) can reduce i-cache misses
through improved hot code layout."""


class ITLB_Misses:
    name = "ITLB_Misses"
    domain = "Clocks"
    area = "FE"
    level = 3
    htoff = False
    sample = ['ITLB_MISSES.WALK_COMPLETED']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BigFootprint', 'BvBC', 'FetchLat', 'MemoryTLB'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = ITLB_Miss_Cycles(self, EV, 3) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "ITLB_Misses zero division")
        return self.val
    desc = """
This metric represents fraction of cycles the CPU was
stalled due to Instruction TLB (ITLB) misses.. Consider
large 2M pages for code (selectively prefer hot large-size
function, due to limited 2M entries). Linux options:
standard binaries use libhugetlbfs; Hfsort.. https://github.
com/libhugetlbfs/libhugetlbfs;https://research.fb.com/public
ations/optimizing-function-placement-for-large-scale-data-
center-applications-2/"""


class Branch_Resteers:
    name = "Branch_Resteers"
    domain = "Clocks"
    area = "FE"
    level = 3
    htoff = False
    sample = ['BR_MISP_RETIRED.ALL_BRANCHES']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['FetchLat'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = BAClear_Cost *(EV("BR_MISP_RETIRED.ALL_BRANCHES", 3) + EV("MACHINE_CLEARS.COUNT", 3) + EV("BACLEARS.ANY", 3)) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Branch_Resteers zero division")
        return self.val
    desc = """
This metric represents fraction of cycles the CPU was
stalled due to Branch Resteers. Branch Resteers estimates
the Frontend delay in fetching operations from corrected
path; following all sorts of miss-predicted branches. For
example; branchy code with lots of miss-predictions might
get categorized under Branch Resteers. Note the value of
this node may overlap with its siblings."""


class MS_Switches:
    name = "MS_Switches"
    domain = "Clocks_Estimated"
    area = "FE"
    level = 3
    htoff = False
    sample = ['IDQ.MS_SWITCHES']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['FetchLat', 'MicroSeq'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = MS_Switches_Cost * EV("IDQ.MS_SWITCHES", 3) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "MS_Switches zero division")
        return self.val
    desc = """
This metric estimates the fraction of cycles when the CPU
was stalled due to switches of uop delivery to the Microcode
Sequencer (MS). Commonly used instructions are optimized for
delivery by the DSB (decoded i-cache) or MITE (legacy
instruction decode) pipelines. Certain operations cannot be
handled natively by the execution pipeline; and must be
performed by microcode (small programs injected into the
execution stream). Switching to the MS too often can
negatively impact performance. The MS is designated to
deliver long uop flows required by CISC instructions like
CPUID; or uncommon conditions like Floating Point Assists
when dealing with Denormals."""


class LCP:
    name = "LCP"
    domain = "Clocks"
    area = "FE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['FetchLat'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("ILD_STALL.LCP", 3) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "LCP zero division")
        return self.val
    desc = """
This metric represents fraction of cycles CPU was stalled
due to Length Changing Prefixes (LCPs). Using proper
compiler flags or Intel Compiler by default will certainly
avoid this."""


class DSB_Switches:
    name = "DSB_Switches"
    domain = "Clocks"
    area = "FE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['DSBmiss', 'FetchLat'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("DSB2MITE_SWITCHES.PENALTY_CYCLES", 3) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "DSB_Switches zero division")
        return self.val
    desc = """
This metric represents fraction of cycles the CPU was
stalled due to switches from DSB to MITE pipelines. The DSB
(decoded i-cache) is a Uop Cache where the front-end
directly delivers Uops (micro operations) avoiding heavy x86
decoding. The DSB pipeline has shorter latency and delivered
higher bandwidth than the MITE (legacy instruction decode
pipeline). Switching between the two pipelines can cause
penalties hence this metric measures the exposed penalty..
See section 'Optimization for Decoded Icache' in
Optimization Manual:.
http://www.intel.com/content/www/us/en/architecture-and-
technology/64-ia-32-architectures-optimization-manual.html"""


class Fetch_Bandwidth:
    name = "Fetch_Bandwidth"
    domain = "Slots"
    area = "FE"
    level = 2
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['FetchBW', 'Frontend', 'TmaL2'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = self.Frontend_Bound.compute(EV) - self.Fetch_Latency.compute(EV)
            self.thresh = (self.val > 0.2)
        except ZeroDivisionError:
            handle_error(self, "Fetch_Bandwidth zero division")
        return self.val
    desc = """
This metric represents fraction of slots the CPU was stalled
due to Frontend bandwidth issues.  For example;
inefficiencies at the instruction decoders; or restrictions
for caching in the DSB (decoded uops cache) are categorized
under Fetch Bandwidth. In such cases; the Frontend typically
delivers suboptimal amount of uops to the Backend."""


class MITE:
    name = "MITE"
    domain = "Slots_Estimated"
    area = "FE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['DSBmiss', 'FetchBW'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = (EV("IDQ.ALL_MITE_CYCLES_ANY_UOPS", 3) - EV("IDQ.ALL_MITE_CYCLES_4_UOPS", 3)) / CORE_CLKS(self, EV, 3) / 2
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "MITE zero division")
        return self.val
    desc = """
This metric represents Core fraction of cycles in which CPU
was likely limited due to the MITE pipeline (the legacy
decode pipeline). This pipeline is used for code that was
not pre-cached in the DSB or LSD. For example;
inefficiencies due to asymmetric decoders; use of long
immediate or LCP can manifest as MITE fetch bandwidth
bottleneck.. Consider tuning codegen of 'small hotspots'
that can fit in DSB. Read about 'Decoded ICache' in
Optimization Manual:.
http://www.intel.com/content/www/us/en/architecture-and-
technology/64-ia-32-architectures-optimization-manual.html"""


class DSB:
    name = "DSB"
    domain = "Slots_Estimated"
    area = "FE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['DSB', 'FetchBW'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = (EV("IDQ.ALL_DSB_CYCLES_ANY_UOPS", 3) - EV("IDQ.ALL_DSB_CYCLES_4_UOPS", 3)) / CORE_CLKS(self, EV, 3) / 2
            self.thresh = (self.val > 0.15) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "DSB zero division")
        return self.val
    desc = """
This metric represents Core fraction of cycles in which CPU
was likely limited due to DSB (decoded uop cache) fetch
pipeline.  For example; inefficient utilization of the DSB
cache structure or bank conflict when reading from it; are
categorized here."""


class Bad_Speculation:
    name = "Bad_Speculation"
    domain = "Slots"
    area = "BAD"
    level = 1
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['TmaL1'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = (EV("UOPS_ISSUED.ANY", 1) - Retired_Slots(self, EV, 1) + Pipeline_Width * Recovery_Cycles(self, EV, 1)) / SLOTS(self, EV, 1)
            self.thresh = (self.val > 0.15)
        except ZeroDivisionError:
            handle_error(self, "Bad_Speculation zero division")
        return self.val
    desc = """
This category represents fraction of slots wasted due to
incorrect speculations. This include slots used to issue
uops that do not eventually get retired and slots for which
the issue-pipeline was blocked due to recovery from earlier
incorrect speculation. For example; wasted work due to miss-
predicted branches are categorized under Bad Speculation
category. Incorrect data speculation followed by Memory
Ordering Nukes is another example."""


class Branch_Mispredicts:
    name = "Branch_Mispredicts"
    domain = "Slots"
    area = "BAD"
    level = 2
    htoff = False
    sample = ['BR_MISP_RETIRED.ALL_BRANCHES:pp']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BadSpec', 'BrMispredicts', 'BvMP', 'TmaL2'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = Mispred_Clears_Fraction(self, EV, 2) * self.Bad_Speculation.compute(EV)
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Branch_Mispredicts zero division")
        return self.val
    desc = """
This metric represents fraction of slots the CPU has wasted
due to Branch Misprediction.  These slots are either wasted
by uops fetched from an incorrectly speculated program path;
or stalls when the out-of-order part of the machine needs to
recover its state from a speculative path.. Using profile
feedback in the compiler may help. Please see the
Optimization Manual for general strategies for addressing
branch misprediction issues..
http://www.intel.com/content/www/us/en/architecture-and-
technology/64-ia-32-architectures-optimization-manual.html"""


class Machine_Clears:
    name = "Machine_Clears"
    domain = "Slots"
    area = "BAD"
    level = 2
    htoff = False
    sample = ['MACHINE_CLEARS.COUNT']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BadSpec', 'BvMS', 'MachineClears', 'TmaL2'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = self.Bad_Speculation.compute(EV) - self.Branch_Mispredicts.compute(EV)
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Machine_Clears zero division")
        return self.val
    desc = """
This metric represents fraction of slots the CPU has wasted
due to Machine Clears.  These slots are either wasted by
uops fetched prior to the clear; or stalls the out-of-order
portion of the machine needs to recover its state after the
clear. For example; this can happen due to memory ordering
Nukes (e.g. Memory Disambiguation) or Self-Modifying-Code
(SMC) nukes.. See \"Memory Disambiguation\" in Optimization
Manual and:. https://software.intel.com/sites/default/files/
m/d/4/1/d/8/sma.pdf"""


class Backend_Bound:
    name = "Backend_Bound"
    domain = "Slots"
    area = "BE"
    level = 1
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvOB', 'TmaL1'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = 1 -(self.Frontend_Bound.compute(EV) + self.Bad_Speculation.compute(EV) + self.Retiring.compute(EV))
            self.thresh = (self.val > 0.2)
        except ZeroDivisionError:
            handle_error(self, "Backend_Bound zero division")
        return self.val
    desc = """
This category represents fraction of slots where no uops are
being delivered due to a lack of required resources for
accepting new uops in the Backend. Backend is the portion of
the processor core where the out-of-order scheduler
dispatches ready uops into their respective execution units;
and once completed these uops get retired according to
program order. For example; stalls due to data-cache misses
or stalls due to the divider unit being overloaded are both
categorized under Backend Bound. Backend Bound is further
divided into two main categories: Memory Bound and Core
Bound."""


class Memory_Bound:
    name = "Memory_Bound"
    domain = "Slots"
    area = "BE/Mem"
    level = 2
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['Backend', 'TmaL2'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = Memory_Bound_Fraction(self, EV, 2) * self.Backend_Bound.compute(EV)
            self.thresh = (self.val > 0.2) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Memory_Bound zero division")
        return self.val
    desc = """
This metric represents fraction of slots the Memory
subsystem within the Backend was a bottleneck.  Memory Bound
estimates fraction of slots where pipeline is likely stalled
due to demand load or store instructions. This accounts
mainly for (1) non-completed in-flight memory demand loads
which coincides with execution units starvation; in addition
to (2) cases where stores could impose backpressure on the
pipeline when many of them get buffered at the same time
(less common out of the two)."""


class L1_Bound:
    name = "L1_Bound"
    domain = "Stalls"
    area = "BE/Mem"
    level = 3
    htoff = False
    sample = ['MEM_LOAD_UOPS_RETIRED.L1_HIT:pp']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['CacheHits', 'MemoryBound', 'TmaL3mem'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = max((STALLS_MEM_ANY(self, EV, 3) - EV("CYCLE_ACTIVITY.STALLS_L1D_PENDING", 3)) / CLKS(self, EV, 3) , 0 )
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "L1_Bound zero division")
        return self.val
    desc = """
This metric estimates how often the CPU was stalled without
loads missing the L1 Data (L1D) cache.  The L1D cache
typically has the shortest latency.  However; in certain
cases like loads blocked on older stores; a load might
suffer due to high latency even though it is being satisfied
by the L1D. Another example is loads who miss in the TLB.
These cases are characterized by execution unit stalls;
while some non-completed demand load lives in the machine
without having that demand load missing the L1 cache."""


class DTLB_Load:
    name = "DTLB_Load"
    domain = "Clocks_Estimated"
    area = "BE/Mem"
    level = 4
    htoff = False
    sample = ['MEM_UOPS_RETIRED.STLB_MISS_LOADS:pp']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvMT', 'MemoryTLB'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = (Mem_STLB_Hit_Cost * EV("DTLB_LOAD_MISSES.STLB_HIT", 4) + EV("DTLB_LOAD_MISSES.WALK_DURATION", 4)) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "DTLB_Load zero division")
        return self.val
    desc = """
This metric roughly estimates the fraction of cycles where
the Data TLB (DTLB) was missed by load accesses. TLBs
(Translation Look-aside Buffers) are processor caches for
recently used entries out of the Page Tables that are used
to map virtual- to physical-addresses by the operating
system. This metric approximates the potential delay of
demand loads missing the first-level data TLB (assuming
worst case scenario with back to back misses to different
pages). This includes hitting in the second-level TLB (STLB)
as well as performing a hardware page walk on an STLB miss.."""


class Store_Fwd_Blk:
    name = "Store_Fwd_Blk"
    domain = "Clocks_Estimated"
    area = "BE/Mem"
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = 13 * EV("LD_BLOCKS.STORE_FORWARD", 4) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Store_Fwd_Blk zero division")
        return self.val
    desc = """
This metric roughly estimates fraction of cycles when the
memory subsystem had loads blocked since they could not
forward data from earlier (in program order) overlapping
stores. To streamline memory operations in the pipeline; a
load can avoid waiting for memory if a prior in-flight store
is writing the data that the load wants to read (store
forwarding process). However; in some cases the load may be
blocked for a significant time pending the store forward.
For example; when the prior store is writing a smaller
region than the load is reading."""


class Lock_Latency:
    name = "Lock_Latency"
    domain = "Clocks"
    area = "BE/Mem"
    level = 4
    htoff = False
    sample = ['MEM_UOPS_RETIRED.LOCK_LOADS:pp']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['LockCont', 'Offcore'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = Mem_Lock_St_Fraction(self, EV, 4) * ORO_Demand_RFO_C1(self, EV, 4) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.2) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Lock_Latency zero division")
        return self.val
    desc = """
This metric represents fraction of cycles the CPU spent
handling cache misses due to lock operations. Due to the
microarchitecture handling of locks; they are classified as
L1_Bound regardless of what memory source satisfied them."""


class Split_Loads:
    name = "Split_Loads"
    domain = "Clocks_Calculated"
    area = "BE/Mem"
    level = 4
    htoff = False
    sample = ['MEM_UOPS_RETIRED.SPLIT_LOADS:pp']
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = Load_Miss_Real_Latency(self, EV, 4) * EV("LD_BLOCKS.NO_SR", 4) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.3)
        except ZeroDivisionError:
            handle_error(self, "Split_Loads zero division")
        return self.val
    desc = """
This metric estimates fraction of cycles handling memory
load split accesses - load that cross 64-byte cache line
boundary. . Consider aligning data or hot structure fields.
See the Optimization Manual for more details"""


class G4K_Aliasing:
    name = "4K_Aliasing"
    domain = "Clocks_Estimated"
    area = "BE/Mem"
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("LD_BLOCKS_PARTIAL.ADDRESS_ALIAS", 4) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.2) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "G4K_Aliasing zero division")
        return self.val
    desc = """
This metric estimates how often memory load accesses were
aliased by preceding stores (in program order) with a 4K
address offset. False match is possible; which incur a few
cycles load re-issue. However; the short re-issue duration
is often hidden by the out-of-order core and HW
optimizations; hence a user may safely ignore a high value
of this metric unless it manages to propagate up into parent
nodes of the hierarchy (e.g. to L1_Bound).. Consider
reducing independent loads/stores accesses with 4K offsets.
See the Optimization Manual for more details"""


class FB_Full:
    name = "FB_Full"
    domain = "Clocks_Calculated"
    area = "BE/Mem"
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvMB', 'MemoryBW'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = Load_Miss_Real_Latency(self, EV, 4) * EV("L1D_PEND_MISS.REQUEST_FB_FULL:c1", 4) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.3)
        except ZeroDivisionError:
            handle_error(self, "FB_Full zero division")
        return self.val
    desc = """
This metric does a *rough estimation* of how often L1D Fill
Buffer unavailability limited additional L1D miss memory
access requests to proceed. The higher the metric value; the
deeper the memory hierarchy level the misses are satisfied
from (metric values >1 are valid). Often it hints on
approaching bandwidth limits (to L2 cache; L3 cache or
external memory).. See $issueBW and $issueSL hints. Avoid
software prefetches if indeed memory BW limited."""


class L2_Bound:
    name = "L2_Bound"
    domain = "Stalls"
    area = "BE/Mem"
    level = 3
    htoff = False
    sample = ['MEM_LOAD_UOPS_RETIRED.L2_HIT:pp']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvML', 'CacheHits', 'MemoryBound', 'TmaL3mem'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = (EV("CYCLE_ACTIVITY.STALLS_L1D_PENDING", 3) - EV("CYCLE_ACTIVITY.STALLS_L2_PENDING", 3)) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "L2_Bound zero division")
        return self.val
    desc = """
This metric estimates how often the CPU was stalled due to
L2 cache accesses by loads.  Avoiding cache misses (i.e. L1
misses/L2 hits) can improve the latency and increase
performance."""


class L3_Bound:
    name = "L3_Bound"
    domain = "Stalls"
    area = "BE/Mem"
    level = 3
    htoff = False
    sample = ['MEM_LOAD_UOPS_RETIRED.L3_HIT:pp']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['CacheHits', 'MemoryBound', 'TmaL3mem'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = Mem_L3_Hit_Fraction(self, EV, 3) * EV("CYCLE_ACTIVITY.STALLS_L2_PENDING", 3) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "L3_Bound zero division")
        return self.val
    desc = """
This metric estimates how often the CPU was stalled due to
loads accesses to L3 cache or contended with a sibling Core.
Avoiding cache misses (i.e. L2 misses/L3 hits) can improve
the latency and increase performance."""


class Contested_Accesses:
    name = "Contested_Accesses"
    domain = "Clocks_Estimated"
    area = "BE/Mem"
    level = 4
    htoff = False
    sample = ['MEM_LOAD_UOPS_L3_HIT_RETIRED.XSNP_HITM:pp', 'MEM_LOAD_UOPS_L3_HIT_RETIRED.XSNP_MISS:pp']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvMS', 'DataSharing', 'LockCont', 'Offcore', 'Snoop'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = (Mem_XSNP_HitM_Cost(self, EV, 4) * LOAD_XSNP_HITM(self, EV, 4) + Mem_XSNP_Hit_Cost(self, EV, 4) * LOAD_XSNP_MISS(self, EV, 4)) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Contested_Accesses zero division")
        return self.val
    desc = """
This metric estimates fraction of cycles while the memory
subsystem was handling synchronizations due to contested
accesses. Contested accesses occur when data written by one
Logical Processor are read by another Logical Processor on a
different Physical Core. Examples of contested accesses
include synchronizations such as locks; true data sharing
such as modified locked variables; and false sharing."""


class Data_Sharing:
    name = "Data_Sharing"
    domain = "Clocks_Estimated"
    area = "BE/Mem"
    level = 4
    htoff = False
    sample = ['MEM_LOAD_UOPS_L3_HIT_RETIRED.XSNP_HIT:pp']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvMS', 'Offcore', 'Snoop'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = Mem_XSNP_Hit_Cost(self, EV, 4) * LOAD_XSNP_HIT(self, EV, 4) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Data_Sharing zero division")
        return self.val
    desc = """
This metric estimates fraction of cycles while the memory
subsystem was handling synchronizations due to data-sharing
accesses. Data shared by multiple Logical Processors (even
just read shared) may cause increased access latency due to
cache coherency. Excessive data sharing can drastically harm
multithreaded performance."""


class L3_Hit_Latency:
    name = "L3_Hit_Latency"
    domain = "Clocks_Estimated"
    area = "BE/Mem"
    level = 4
    htoff = False
    sample = ['MEM_LOAD_UOPS_RETIRED.L3_HIT:pp']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvML', 'MemoryLat'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = Mem_XSNP_None_Cost(self, EV, 4) * LOAD_L3_HIT(self, EV, 4) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "L3_Hit_Latency zero division")
        return self.val
    desc = """
This metric estimates fraction of cycles with demand load
accesses that hit the L3 cache under unloaded scenarios
(possibly L3 latency limited).  Avoiding private cache
misses (i.e. L2 misses/L3 hits) will improve the latency;
reduce contention with sibling physical cores and increase
performance.  Note the value of this node may overlap with
its siblings."""


class SQ_Full:
    name = "SQ_Full"
    domain = "Clocks"
    area = "BE/Mem"
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvMB', 'MemoryBW', 'Offcore'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = SQ_Full_Cycles(self, EV, 4) / CORE_CLKS(self, EV, 4)
            self.thresh = (self.val > 0.3) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "SQ_Full zero division")
        return self.val
    desc = """
This metric measures fraction of cycles where the Super
Queue (SQ) was full taking into account all request-types
and both hardware SMT threads (Logical Processors)."""


class DRAM_Bound:
    name = "DRAM_Bound"
    domain = "Stalls"
    area = "BE/Mem"
    level = 3
    htoff = False
    sample = ['MEM_LOAD_UOPS_RETIRED.L3_MISS:pp']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['MemoryBound', 'TmaL3mem'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = (1 - Mem_L3_Hit_Fraction(self, EV, 3)) * EV("CYCLE_ACTIVITY.STALLS_L2_PENDING", 3) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "DRAM_Bound zero division")
        return self.val
    desc = """
This metric estimates how often the CPU was stalled on
accesses to external memory (DRAM) by loads. Better caching
can improve the latency and increase performance."""


class MEM_Bandwidth:
    name = "MEM_Bandwidth"
    domain = "Clocks"
    area = "BE/Mem"
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvMB', 'MemoryBW', 'Offcore'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = ORO_DRD_BW_Cycles(self, EV, 4) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.2) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "MEM_Bandwidth zero division")
        return self.val
    desc = """
This metric estimates fraction of cycles where the core's
performance was likely hurt due to approaching bandwidth
limits of external memory - DRAM ([SPR-HBM] and/or HBM).
The underlying heuristic assumes that a similar off-core
traffic is generated by all IA cores. This metric does not
aggregate non-data-read requests by this logical processor;
requests from other IA Logical Processors/Physical
Cores/sockets; or other non-IA devices like GPU; hence the
maximum external memory bandwidth limits may or may not be
approached when this metric is flagged (see Uncore counters
for that).. Improve data accesses to reduce cacheline
transfers from/to memory. Examples: 1) Consume all bytes of
a each cacheline before it is evicted (e.g. reorder
structure elements and split non-hot ones), 2) merge
computed-limited with BW-limited loops, 3) NUMA
optimizations in multi-socket system. Note: software
prefetches will not help BW-limited application.."""


class MEM_Latency:
    name = "MEM_Latency"
    domain = "Clocks"
    area = "BE/Mem"
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvML', 'MemoryLat', 'Offcore'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = ORO_DRD_Any_Cycles(self, EV, 4) / CLKS(self, EV, 4) - self.MEM_Bandwidth.compute(EV)
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "MEM_Latency zero division")
        return self.val
    desc = """
This metric estimates fraction of cycles where the
performance was likely hurt due to latency from external
memory - DRAM ([SPR-HBM] and/or HBM).  This metric does not
aggregate requests from other Logical Processors/Physical
Cores/sockets (see Uncore counters for that).. Improve data
accesses or interleave them with compute. Examples: 1) Data
layout re-structuring, 2) Software Prefetches (also through
the compiler).."""


class Store_Bound:
    name = "Store_Bound"
    domain = "Stalls"
    area = "BE/Mem"
    level = 3
    htoff = False
    sample = ['MEM_UOPS_RETIRED.ALL_STORES:pp']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['MemoryBound', 'TmaL3mem'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("RESOURCE_STALLS.SB", 3) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.2) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Store_Bound zero division")
        return self.val
    desc = """
This metric estimates how often CPU was stalled  due to RFO
store memory accesses; RFO store issue a read-for-ownership
request before the write. Even though store accesses do not
typically stall out-of-order CPUs; there are few cases where
stores can lead to actual stalls. This metric will be
flagged should RFO stores be a bottleneck."""


class Store_Latency:
    name = "Store_Latency"
    domain = "Clocks_Estimated"
    area = "BE/Mem"
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvML', 'LockCont', 'MemoryLat', 'Offcore'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = (Store_L2_Hit_Cycles(self, EV, 4) + (1 - Mem_Lock_St_Fraction(self, EV, 4)) * ORO_Demand_RFO_C1(self, EV, 4)) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Store_Latency zero division")
        return self.val
    desc = """
This metric estimates fraction of cycles the CPU spent
handling L1D store misses. Store accesses usually less
impact out-of-order core performance; however; holding
resources for longer time can lead into undesired
implications (e.g. contention on L1D fill-buffer entries -
see FB_Full). Consider to avoid/reduce unnecessary (or
easily load-able/computable) memory store."""


class False_Sharing:
    name = "False_Sharing"
    domain = "Clocks_Estimated"
    area = "BE/Mem"
    level = 4
    htoff = False
    sample = ['MEM_LOAD_UOPS_L3_HIT_RETIRED.XSNP_HITM:pp', 'OFFCORE_RESPONSE.DEMAND_RFO.L3_HIT.HITM_OTHER_CORE']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvMS', 'DataSharing', 'LockCont', 'Offcore', 'Snoop'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = Mem_XSNP_HitM_Cost(self, EV, 4) * EV("OFFCORE_RESPONSE.DEMAND_RFO.L3_HIT.HITM_OTHER_CORE", 4) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "False_Sharing zero division")
        return self.val
    desc = """
This metric roughly estimates how often CPU was handling
synchronizations due to False Sharing. False Sharing is a
multithreading hiccup; where multiple Logical Processors
contend on different data-elements mapped into the same
cache line. . False Sharing can be easily avoided by padding
to make Logical Processors access different lines."""


class Split_Stores:
    name = "Split_Stores"
    domain = "Core_Utilization"
    area = "BE/Mem"
    level = 4
    htoff = False
    sample = ['MEM_UOPS_RETIRED.SPLIT_STORES:pp']
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = 2 * EV("MEM_UOPS_RETIRED.SPLIT_STORES", 4) / CORE_CLKS(self, EV, 4)
            self.thresh = (self.val > 0.2) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Split_Stores zero division")
        return self.val
    desc = """
This metric represents rate of split store accesses.
Consider aligning your data to the 64-byte cache line
granularity."""


class DTLB_Store:
    name = "DTLB_Store"
    domain = "Clocks_Estimated"
    area = "BE/Mem"
    level = 4
    htoff = False
    sample = ['MEM_UOPS_RETIRED.STLB_MISS_STORES:pp']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvMT', 'MemoryTLB'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = (Mem_STLB_Hit_Cost * EV("DTLB_STORE_MISSES.STLB_HIT", 4) + EV("DTLB_STORE_MISSES.WALK_DURATION", 4)) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "DTLB_Store zero division")
        return self.val
    desc = """
This metric roughly estimates the fraction of cycles spent
handling first-level data TLB store misses.  As with
ordinary data caching; focus on improving data locality and
reducing working-set size to reduce DTLB overhead.
Additionally; consider using profile-guided optimization
(PGO) to collocate frequently-used data on the same page.
Try using larger page sizes for large amounts of frequently-
used data."""


class Core_Bound:
    name = "Core_Bound"
    domain = "Slots"
    area = "BE/Core"
    level = 2
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['Backend', 'TmaL2', 'Compute'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = self.Backend_Bound.compute(EV) - self.Memory_Bound.compute(EV)
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Core_Bound zero division")
        return self.val
    desc = """
This metric represents fraction of slots where Core non-
memory issues were of a bottleneck.  Shortage in hardware
compute resources; or dependencies in software's
instructions are both categorized under Core Bound. Hence it
may indicate the machine ran out of an out-of-order
resource; certain execution units are overloaded or
dependencies in program's data- or instruction-flow are
limiting the performance (e.g. FP-chained long-latency
arithmetic operations).. Tip: consider Port Saturation
analysis as next step."""


class Divider:
    name = "Divider"
    domain = "Clocks"
    area = "BE/Core"
    level = 3
    htoff = False
    sample = ['ARITH.DIVIDER_UOPS']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvCB'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = 10 * EV("ARITH.DIVIDER_UOPS", 3) / CORE_CLKS(self, EV, 3)
            self.thresh = (self.val > 0.2) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Divider zero division")
        return self.val
    desc = """
This metric represents fraction of cycles where the Divider
unit was active. Divide and square root instructions are
performed by the Divider unit and can take considerably
longer latency than integer or Floating Point addition;
subtraction; or multiplication."""


class Ports_Utilization:
    name = "Ports_Utilization"
    domain = "Clocks"
    area = "BE/Core"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['PortsUtil'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = (Backend_Bound_Cycles(self, EV, 3) - EV("RESOURCE_STALLS.SB", 3) - STALLS_MEM_ANY(self, EV, 3)) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.15) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Ports_Utilization zero division")
        return self.val
    desc = """
This metric estimates fraction of cycles the CPU performance
was potentially limited due to Core computation issues (non
divider-related).  Two distinct categories can be attributed
into this metric: (1) heavy data-dependency among contiguous
instructions would manifest in this metric - such cases are
often referred to as low Instruction Level Parallelism
(ILP). (2) Contention on some hardware execution unit other
than Divider. For example; when there are too many multiply
operations.. Loop Vectorization -most compilers feature
auto-Vectorization options today- reduces pressure on the
execution ports as multiple elements are calculated with
same uop."""


class Ports_Utilized_0:
    name = "Ports_Utilized_0"
    domain = "Clocks"
    area = "BE/Core"
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['PortsUtil'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = Cycles_0_Ports_Utilized(self, EV, 4) / CORE_CLKS(self, EV, 4)
            self.thresh = (self.val > 0.2) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Ports_Utilized_0 zero division")
        return self.val
    desc = """
This metric represents fraction of cycles CPU executed no
uops on any execution port (Logical Processor cycles since
ICL, Physical Core cycles otherwise). Long-latency
instructions like divides may contribute to this metric..
Check assembly view and Appendix C in Optimization Manual to
find out instructions with say 5 or more cycles latency..
http://www.intel.com/content/www/us/en/architecture-and-
technology/64-ia-32-architectures-optimization-manual.html"""


class Ports_Utilized_1:
    name = "Ports_Utilized_1"
    domain = "Clocks"
    area = "BE/Core"
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['PortsUtil'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = Cycles_1_Port_Utilized(self, EV, 4) / CORE_CLKS(self, EV, 4)
            self.thresh = (self.val > 0.2) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Ports_Utilized_1 zero division")
        return self.val
    desc = """
This metric represents fraction of cycles where the CPU
executed total of 1 uop per cycle on all execution ports
(Logical Processor cycles since ICL, Physical Core cycles
otherwise). This can be due to heavy data-dependency among
software instructions; or over oversubscribing a particular
hardware resource. In some other cases with high
1_Port_Utilized and L1_Bound; this metric can point to L1
data-cache latency bottleneck that may not necessarily
manifest with complete execution starvation (due to the
short L1 latency e.g. walking a linked list) - looking at
the assembly can be helpful."""


class Ports_Utilized_2:
    name = "Ports_Utilized_2"
    domain = "Clocks"
    area = "BE/Core"
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['PortsUtil'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = Cycles_2_Ports_Utilized(self, EV, 4) / CORE_CLKS(self, EV, 4)
            self.thresh = (self.val > 0.15) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Ports_Utilized_2 zero division")
        return self.val
    desc = """
This metric represents fraction of cycles CPU executed total
of 2 uops per cycle on all execution ports (Logical
Processor cycles since ICL, Physical Core cycles otherwise).
Loop Vectorization -most compilers feature auto-
Vectorization options today- reduces pressure on the
execution ports as multiple elements are calculated with
same uop."""


class Ports_Utilized_3m:
    name = "Ports_Utilized_3m"
    domain = "Clocks"
    area = "BE/Core"
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvCB', 'PortsUtil'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = Cycles_3m_Ports_Utilized(self, EV, 4) / CORE_CLKS(self, EV, 4)
            self.thresh = (self.val > 0.4) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Ports_Utilized_3m zero division")
        return self.val
    desc = """
This metric represents fraction of cycles CPU executed total
of 3 or more uops per cycle on all execution ports (Logical
Processor cycles since ICL, Physical Core cycles otherwise)."""


class ALU_Op_Utilization:
    name = "ALU_Op_Utilization"
    domain = "Core_Execution"
    area = "BE/Core"
    level = 5
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = (EV("UOPS_DISPATCHED_PORT.PORT_0", 5) + EV("UOPS_DISPATCHED_PORT.PORT_1", 5) + EV("UOPS_DISPATCHED_PORT.PORT_5", 5) + EV("UOPS_DISPATCHED_PORT.PORT_6", 5)) / (4 * CORE_CLKS(self, EV, 5))
            self.thresh = (self.val > 0.4)
        except ZeroDivisionError:
            handle_error(self, "ALU_Op_Utilization zero division")
        return self.val
    desc = """
This metric represents Core fraction of cycles CPU
dispatched uops on execution ports for ALU operations."""


class Port_0:
    name = "Port_0"
    domain = "Core_Clocks"
    area = "BE/Core"
    level = 6
    htoff = False
    sample = ['UOPS_DISPATCHED_PORT.PORT_0']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['Compute'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("UOPS_DISPATCHED_PORT.PORT_0", 6) / CORE_CLKS(self, EV, 6)
            self.thresh = (self.val > 0.6)
        except ZeroDivisionError:
            handle_error(self, "Port_0 zero division")
        return self.val
    desc = """
This metric represents Core fraction of cycles CPU
dispatched uops on execution port 0  ALU and 2nd branch"""


class Port_1:
    name = "Port_1"
    domain = "Core_Clocks"
    area = "BE/Core"
    level = 6
    htoff = False
    sample = ['UOPS_DISPATCHED_PORT.PORT_1']
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("UOPS_DISPATCHED_PORT.PORT_1", 6) / CORE_CLKS(self, EV, 6)
            self.thresh = (self.val > 0.6)
        except ZeroDivisionError:
            handle_error(self, "Port_1 zero division")
        return self.val
    desc = """
This metric represents Core fraction of cycles CPU
dispatched uops on execution port 1 (ALU)"""


class Port_5:
    name = "Port_5"
    domain = "Core_Clocks"
    area = "BE/Core"
    level = 6
    htoff = False
    sample = ['UOPS_DISPATCHED_PORT.PORT_5']
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("UOPS_DISPATCHED_PORT.PORT_5", 6) / CORE_CLKS(self, EV, 6)
            self.thresh = (self.val > 0.6)
        except ZeroDivisionError:
            handle_error(self, "Port_5 zero division")
        return self.val
    desc = """
This metric represents Core fraction of cycles CPU
dispatched uops on execution port 5  ALU. See section
'Handling Port 5 Pressure' in Optimization Manual:.
http://www.intel.com/content/www/us/en/architecture-and-
technology/64-ia-32-architectures-optimization-manual.html"""


class Port_6:
    name = "Port_6"
    domain = "Core_Clocks"
    area = "BE/Core"
    level = 6
    htoff = False
    sample = ['UOPS_DISPATCHED_PORT.PORT_1']
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("UOPS_DISPATCHED_PORT.PORT_6", 6) / CORE_CLKS(self, EV, 6)
            self.thresh = (self.val > 0.6)
        except ZeroDivisionError:
            handle_error(self, "Port_6 zero division")
        return self.val
    desc = """
This metric represents Core fraction of cycles CPU
dispatched uops on execution port 6  Primary Branch and
simple ALU"""


class Load_Op_Utilization:
    name = "Load_Op_Utilization"
    domain = "Core_Execution"
    area = "BE/Core"
    level = 5
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = (EV("UOPS_DISPATCHED_PORT.PORT_2", 5) + EV("UOPS_DISPATCHED_PORT.PORT_3", 5) + EV("UOPS_DISPATCHED_PORT.PORT_7", 5) - EV("UOPS_DISPATCHED_PORT.PORT_4", 5)) / (2 * CORE_CLKS(self, EV, 5))
            self.thresh = (self.val > 0.6)
        except ZeroDivisionError:
            handle_error(self, "Load_Op_Utilization zero division")
        return self.val
    desc = """
This metric represents Core fraction of cycles CPU
dispatched uops on execution port for Load operations"""


class Port_2:
    name = "Port_2"
    domain = "Core_Clocks"
    area = "BE/Core"
    level = 6
    htoff = False
    sample = ['UOPS_DISPATCHED_PORT.PORT_2']
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("UOPS_DISPATCHED_PORT.PORT_2", 6) / CORE_CLKS(self, EV, 6)
            self.thresh = (self.val > 0.6)
        except ZeroDivisionError:
            handle_error(self, "Port_2 zero division")
        return self.val
    desc = """
This metric represents Core fraction of cycles CPU
dispatched uops on execution port 2 Loads and Store-address"""


class Port_3:
    name = "Port_3"
    domain = "Core_Clocks"
    area = "BE/Core"
    level = 6
    htoff = False
    sample = ['UOPS_DISPATCHED_PORT.PORT_3']
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("UOPS_DISPATCHED_PORT.PORT_3", 6) / CORE_CLKS(self, EV, 6)
            self.thresh = (self.val > 0.6)
        except ZeroDivisionError:
            handle_error(self, "Port_3 zero division")
        return self.val
    desc = """
This metric represents Core fraction of cycles CPU
dispatched uops on execution port 3 Loads and Store-address"""


class Store_Op_Utilization:
    name = "Store_Op_Utilization"
    domain = "Core_Execution"
    area = "BE/Core"
    level = 5
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("UOPS_DISPATCHED_PORT.PORT_4", 5) / CORE_CLKS(self, EV, 5)
            self.thresh = (self.val > 0.6)
        except ZeroDivisionError:
            handle_error(self, "Store_Op_Utilization zero division")
        return self.val
    desc = """
This metric represents Core fraction of cycles CPU
dispatched uops on execution port for Store operations"""


class Port_4:
    name = "Port_4"
    domain = "Core_Clocks"
    area = "BE/Core"
    level = 6
    htoff = False
    sample = ['UOPS_DISPATCHED_PORT.PORT_4']
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("UOPS_DISPATCHED_PORT.PORT_4", 6) / CORE_CLKS(self, EV, 6)
            self.thresh = (self.val > 0.6)
        except ZeroDivisionError:
            handle_error(self, "Port_4 zero division")
        return self.val
    desc = """
This metric represents Core fraction of cycles CPU
dispatched uops on execution port 4 (Store-data)"""


class Port_7:
    name = "Port_7"
    domain = "Core_Clocks"
    area = "BE/Core"
    level = 6
    htoff = False
    sample = ['UOPS_DISPATCHED_PORT.PORT_7']
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("UOPS_DISPATCHED_PORT.PORT_7", 6) / CORE_CLKS(self, EV, 6)
            self.thresh = (self.val > 0.6)
        except ZeroDivisionError:
            handle_error(self, "Port_7 zero division")
        return self.val
    desc = """
This metric represents Core fraction of cycles CPU
dispatched uops on execution port 7 simple Store-address"""


class Retiring:
    name = "Retiring"
    domain = "Slots"
    area = "RET"
    level = 1
    htoff = False
    sample = ['UOPS_RETIRED.RETIRE_SLOTS']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvUW', 'TmaL1'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = Retired_Slots(self, EV, 1) / SLOTS(self, EV, 1)
            self.thresh = (self.val > 0.7) or self.Heavy_Operations.thresh
        except ZeroDivisionError:
            handle_error(self, "Retiring zero division")
        return self.val
    desc = """
This category represents fraction of slots utilized by
useful work i.e. issued uops that eventually get retired.
Ideally; all pipeline slots would be attributed to the
Retiring category.  Retiring of 100% would indicate the
maximum Pipeline_Width throughput was achieved.  Maximizing
Retiring typically increases the Instructions-per-cycle (see
IPC metric). Note that a high Retiring value does not
necessary mean there is no room for more performance.  For
example; Heavy-operations or Microcode Assists are
categorized under Retiring. They often indicate suboptimal
performance and can often be optimized or avoided. . A high
Retiring value for non-vectorized code may be a good hint
for programmer to consider vectorizing his code.  Doing so
essentially lets more computations be done without
significantly increasing number of instructions thus
improving the performance."""


class Light_Operations:
    name = "Light_Operations"
    domain = "Slots"
    area = "RET"
    level = 2
    htoff = False
    sample = ['INST_RETIRED.PREC_DIST']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['Retire', 'TmaL2'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = self.Retiring.compute(EV) - self.Heavy_Operations.compute(EV)
            self.thresh = (self.val > 0.6)
        except ZeroDivisionError:
            handle_error(self, "Light_Operations zero division")
        return self.val
    desc = """
This metric represents fraction of slots where the CPU was
retiring light-weight operations -- instructions that
require no more than one uop (micro-operation). This
correlates with total number of instructions used by the
program. A uops-per-instruction (see UopPI metric) ratio of
1 or less should be expected for decently optimized code
running on Intel Core/Xeon products. While this often
indicates efficient X86 instructions were executed; high
value does not necessarily mean better performance cannot be
achieved. . Focus on techniques that reduce instruction
count or result in more efficient instructions generation
such as vectorization."""


class Heavy_Operations:
    name = "Heavy_Operations"
    domain = "Slots"
    area = "RET"
    level = 2
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['Retire', 'TmaL2'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = self.Microcode_Sequencer.compute(EV)
            self.thresh = (self.val > 0.1)
        except ZeroDivisionError:
            handle_error(self, "Heavy_Operations zero division")
        return self.val
    desc = """
This metric represents fraction of slots where the CPU was
retiring heavy-weight operations -- instructions that
require two or more uops or micro-coded sequences. This
highly-correlates with the uop length of these
instructions/sequences."""


class Microcode_Sequencer:
    name = "Microcode_Sequencer"
    domain = "Slots"
    area = "RET"
    level = 3
    htoff = False
    sample = ['IDQ.MS_UOPS']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['MicroSeq'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = Retire_Fraction(self, EV, 3) * EV("IDQ.MS_UOPS", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Microcode_Sequencer zero division")
        return self.val
    desc = """
This metric represents fraction of slots the CPU was
retiring uops fetched by the Microcode Sequencer (MS) unit.
The MS is used for CISC instructions not supported by the
default decoders (like repeat move strings; or CPUID); or by
microcode assists used to address some operation modes (like
in Floating Point assists). These cases can often be
avoided.."""


class Assists:
    name = "Assists"
    domain = "Slots_Estimated"
    area = "RET"
    level = 4
    htoff = False
    sample = ['OTHER_ASSISTS.ANY_WB_ASSIST']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvIO'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = Avg_Assist_Cost * EV("OTHER_ASSISTS.ANY_WB_ASSIST", 4) / SLOTS(self, EV, 4)
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Assists zero division")
        return self.val
    desc = """
This metric estimates fraction of slots the CPU retired uops
delivered by the Microcode_Sequencer as a result of Assists.
Assists are long sequences of uops that are required in
certain corner-cases for operations that cannot be handled
natively by the execution pipeline. For example; when
working with very small floating point values (so-called
Denormals); the FP units are not set up to perform these
operations natively. Instead; a sequence of instructions to
perform the computation on the Denormals is injected into
the pipeline. Since these microcode sequences might be
dozens of uops long; Assists can be extremely deleterious to
performance and they can be avoided in many cases."""


class CISC:
    name = "CISC"
    domain = "Slots"
    area = "RET"
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = max(0 , self.Microcode_Sequencer.compute(EV) - self.Assists.compute(EV))
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "CISC zero division")
        return self.val
    desc = """
This metric estimates fraction of cycles the CPU retired
uops originated from CISC (complex instruction set computer)
instruction. A CISC instruction has multiple uops that are
required to perform the instruction's functionality as in
the case of read-modify-write as an example. Since these
instructions require multiple uops they may or may not imply
sub-optimal use of machine resources."""


class Metric_IPC:
    name = "IPC"
    domain = "Metric"
    maxval = Pipeline_Width + 2
    errcount = 0
    area = "Info.Thread"
    metricgroup = frozenset(['Ret', 'Summary'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IPC(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "IPC zero division")
    desc = """
Instructions Per Cycle (per Logical Processor)"""


class Metric_UopPI:
    name = "UopPI"
    domain = "Metric"
    maxval = 2
    errcount = 0
    area = "Info.Thread"
    metricgroup = frozenset(['Pipeline', 'Ret', 'Retire'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = UopPI(self, EV, 0)
            self.thresh = (self.val > 1.05)
        except ZeroDivisionError:
            handle_error_metric(self, "UopPI zero division")
    desc = """
Uops Per Instruction"""


class Metric_UpTB:
    name = "UpTB"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Thread"
    metricgroup = frozenset(['Branches', 'Fed', 'FetchBW'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = UpTB(self, EV, 0)
            self.thresh = self.val < Pipeline_Width * 1.5
        except ZeroDivisionError:
            handle_error_metric(self, "UpTB zero division")
    desc = """
Uops per taken branch"""


class Metric_CPI:
    name = "CPI"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Thread"
    metricgroup = frozenset(['Pipeline', 'Mem'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = CPI(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "CPI zero division")
    desc = """
Cycles Per Instruction (per Logical Processor)"""


class Metric_CLKS:
    name = "CLKS"
    domain = "Count"
    maxval = 0
    errcount = 0
    area = "Info.Thread"
    metricgroup = frozenset(['Pipeline'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = CLKS(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "CLKS zero division")
    desc = """
Per-Logical Processor actual clocks when the Logical
Processor is active."""


class Metric_SLOTS:
    name = "SLOTS"
    domain = "Count"
    maxval = 0
    errcount = 0
    area = "Info.Thread"
    metricgroup = frozenset(['TmaL1'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = SLOTS(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "SLOTS zero division")
    desc = """
Total issue-pipeline slots (per-Physical Core till ICL; per-
Logical Processor ICL onward)"""


class Metric_CoreIPC:
    name = "CoreIPC"
    domain = "Core_Metric"
    maxval = Pipeline_Width + 2
    errcount = 0
    area = "Info.Core"
    metricgroup = frozenset(['Ret', 'SMT', 'TmaL1'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = CoreIPC(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "CoreIPC zero division")
    desc = """
Instructions Per Cycle across hyper-threads (per physical
core)"""


class Metric_ILP:
    name = "ILP"
    domain = "Metric"
    maxval = Exe_Ports
    errcount = 0
    area = "Info.Core"
    metricgroup = frozenset(['Backend', 'Cor', 'Pipeline', 'PortsUtil'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = ILP(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "ILP zero division")
    desc = """
Instruction-Level-Parallelism (average number of uops
executed when there is execution) per thread (logical-
processor)"""


class Metric_CORE_CLKS:
    name = "CORE_CLKS"
    domain = "Count"
    maxval = 0
    errcount = 0
    area = "Info.Core"
    metricgroup = frozenset(['SMT'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = CORE_CLKS(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "CORE_CLKS zero division")
    desc = """
Core actual clocks when any Logical Processor is active on
the Physical Core"""


class Metric_IpLoad:
    name = "IpLoad"
    domain = "Inst_Metric"
    maxval = 0
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = frozenset(['InsType'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpLoad(self, EV, 0)
            self.thresh = (self.val < 3)
        except ZeroDivisionError:
            handle_error_metric(self, "IpLoad zero division")
    desc = """
Instructions per Load (lower number means higher occurrence
rate). Tip: reduce memory accesses."""


class Metric_IpStore:
    name = "IpStore"
    domain = "Inst_Metric"
    maxval = 0
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = frozenset(['InsType'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpStore(self, EV, 0)
            self.thresh = (self.val < 8)
        except ZeroDivisionError:
            handle_error_metric(self, "IpStore zero division")
    desc = """
Instructions per Store (lower number means higher occurrence
rate). Tip: reduce memory accesses."""


class Metric_IpBranch:
    name = "IpBranch"
    domain = "Inst_Metric"
    maxval = 0
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = frozenset(['Branches', 'Fed', 'InsType'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpBranch(self, EV, 0)
            self.thresh = (self.val < 8)
        except ZeroDivisionError:
            handle_error_metric(self, "IpBranch zero division")
    desc = """
Instructions per Branch (lower number means higher
occurrence rate)"""


class Metric_IpCall:
    name = "IpCall"
    domain = "Inst_Metric"
    maxval = 0
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = frozenset(['Branches', 'Fed', 'PGO'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpCall(self, EV, 0)
            self.thresh = (self.val < 200)
        except ZeroDivisionError:
            handle_error_metric(self, "IpCall zero division")
    desc = """
Instructions per (near) call (lower number means higher
occurrence rate)"""


class Metric_IpTB:
    name = "IpTB"
    domain = "Inst_Metric"
    maxval = 0
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = frozenset(['Branches', 'Fed', 'FetchBW', 'Frontend', 'PGO'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpTB(self, EV, 0)
            self.thresh = self.val < Pipeline_Width * 2 + 1
        except ZeroDivisionError:
            handle_error_metric(self, "IpTB zero division")
    desc = """
Instructions per taken branch"""


class Metric_BpTkBranch:
    name = "BpTkBranch"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = frozenset(['Branches', 'Fed', 'PGO'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = BpTkBranch(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "BpTkBranch zero division")
    desc = """
Branch instructions per taken branch. . Can be used to
approximate PGO-likelihood for non-loopy codes."""


class Metric_Instructions:
    name = "Instructions"
    domain = "Count"
    maxval = 0
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = frozenset(['Summary', 'TmaL1'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Instructions(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Instructions zero division")
    desc = """
Total number of retired Instructions"""


class Metric_Retire:
    name = "Retire"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Pipeline"
    metricgroup = frozenset(['Pipeline', 'Ret'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Retire(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Retire zero division")
    desc = """
Average number of Uops retired in cycles where at least one
uop has retired."""


class Metric_DSB_Coverage:
    name = "DSB_Coverage"
    domain = "Metric"
    maxval = 1
    errcount = 0
    area = "Info.Frontend"
    metricgroup = frozenset(['DSB', 'Fed', 'FetchBW'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = DSB_Coverage(self, EV, 0)
            self.thresh = (self.val < 0.7) and HighIPC(self, EV, 1)
        except ZeroDivisionError:
            handle_error_metric(self, "DSB_Coverage zero division")
    desc = """
Fraction of Uops delivered by the DSB (aka Decoded ICache;
or Uop Cache). See section 'Decoded ICache' in Optimization
Manual. http://www.intel.com/content/www/us/en/architecture-
and-technology/64-ia-32-architectures-optimization-
manual.html"""


class Metric_TBpC:
    name = "TBpC"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Frontend"
    metricgroup = frozenset(['Branches', 'FetchBW'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = TBpC(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "TBpC zero division")
    desc = """
Taken Branches retired Per Cycle"""


class Metric_IpUnknown_Branch:
    name = "IpUnknown_Branch"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Frontend"
    metricgroup = frozenset(['Fed'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpUnknown_Branch(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "IpUnknown_Branch zero division")
    desc = """
Instructions per speculative Unknown Branch Misprediction
(BAClear) (lower number means higher occurrence rate)"""


class Metric_IpMispredict:
    name = "IpMispredict"
    domain = "Inst_Metric"
    maxval = 0
    errcount = 0
    area = "Info.Bad_Spec"
    metricgroup = frozenset(['Bad', 'BadSpec', 'BrMispredicts'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpMispredict(self, EV, 0)
            self.thresh = (self.val < 200)
        except ZeroDivisionError:
            handle_error_metric(self, "IpMispredict zero division")
    desc = """
Number of Instructions per non-speculative Branch
Misprediction (JEClear) (lower number means higher
occurrence rate)"""


class Metric_IpMisp_Indirect:
    name = "IpMisp_Indirect"
    domain = "Inst_Metric"
    maxval = 0
    errcount = 0
    area = "Info.Bad_Spec"
    metricgroup = frozenset(['Bad', 'BrMispredicts'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpMisp_Indirect(self, EV, 0)
            self.thresh = (self.val < 1000)
        except ZeroDivisionError:
            handle_error_metric(self, "IpMisp_Indirect zero division")
    desc = """
Instructions per retired Mispredicts for indirect CALL or
JMP branches (lower number means higher occurrence rate)."""


class Metric_Load_Miss_Real_Latency:
    name = "Load_Miss_Real_Latency"
    domain = "Clocks_Latency"
    maxval = 1000
    errcount = 0
    area = "Info.Memory"
    metricgroup = frozenset(['Mem', 'MemoryBound', 'MemoryLat'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Load_Miss_Real_Latency(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Load_Miss_Real_Latency zero division")
    desc = """
Actual Average Latency for L1 data-cache miss demand load
operations (in core cycles)"""


class Metric_MLP:
    name = "MLP"
    domain = "Metric"
    maxval = 10
    errcount = 0
    area = "Info.Memory"
    metricgroup = frozenset(['Mem', 'MemoryBound', 'MemoryBW'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = MLP(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "MLP zero division")
    desc = """
Memory-Level-Parallelism (average number of L1 miss demand
load when there is at least one such miss. Per-Logical
Processor)"""


class Metric_L1MPKI:
    name = "L1MPKI"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Memory"
    metricgroup = frozenset(['CacheHits', 'Mem'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = L1MPKI(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "L1MPKI zero division")
    desc = """
L1 cache true misses per kilo instruction for retired demand
loads"""


class Metric_L2MPKI:
    name = "L2MPKI"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Memory"
    metricgroup = frozenset(['Mem', 'Backend', 'CacheHits'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = L2MPKI(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "L2MPKI zero division")
    desc = """
L2 cache true misses per kilo instruction for retired demand
loads"""


class Metric_L2MPKI_RFO:
    name = "L2MPKI_RFO"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Memory"
    metricgroup = frozenset(['CacheMisses', 'Offcore'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = L2MPKI_RFO(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "L2MPKI_RFO zero division")
    desc = """
Offcore requests (L2 cache miss) per kilo instruction for
demand RFOs"""


class Metric_L3MPKI:
    name = "L3MPKI"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Memory"
    metricgroup = frozenset(['Mem'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = L3MPKI(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "L3MPKI zero division")
    desc = """
L3 cache true misses per kilo instruction for retired demand
loads"""


class Metric_L1D_Cache_Fill_BW:
    name = "L1D_Cache_Fill_BW"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Memory"
    metricgroup = frozenset(['Mem', 'MemoryBW'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = L1D_Cache_Fill_BW(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "L1D_Cache_Fill_BW zero division")
    desc = """
Average per-thread data fill bandwidth to the L1 data cache
[GB / sec]"""


class Metric_L2_Cache_Fill_BW:
    name = "L2_Cache_Fill_BW"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Memory"
    metricgroup = frozenset(['Mem', 'MemoryBW'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = L2_Cache_Fill_BW(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "L2_Cache_Fill_BW zero division")
    desc = """
Average per-thread data fill bandwidth to the L2 cache [GB /
sec]"""


class Metric_L3_Cache_Fill_BW:
    name = "L3_Cache_Fill_BW"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Memory"
    metricgroup = frozenset(['Mem', 'MemoryBW'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = L3_Cache_Fill_BW(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "L3_Cache_Fill_BW zero division")
    desc = """
Average per-thread data fill bandwidth to the L3 cache [GB /
sec]"""


class Metric_Page_Walks_Utilization:
    name = "Page_Walks_Utilization"
    domain = "Core_Metric"
    maxval = 1
    errcount = 0
    area = "Info.Memory.TLB"
    metricgroup = frozenset(['Mem', 'MemoryTLB'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Page_Walks_Utilization(self, EV, 0)
            self.thresh = (self.val > 0.5)
        except ZeroDivisionError:
            handle_error_metric(self, "Page_Walks_Utilization zero division")
    desc = """
Utilization of the core's Page Walker(s) serving STLB misses
triggered by instruction/Load/Store accesses"""


class Metric_L1D_Cache_Fill_BW_2T:
    name = "L1D_Cache_Fill_BW_2T"
    domain = "Core_Metric"
    maxval = 0
    errcount = 0
    area = "Info.Memory.Core"
    metricgroup = frozenset(['Mem', 'MemoryBW'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = L1D_Cache_Fill_BW_2T(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "L1D_Cache_Fill_BW_2T zero division")
    desc = """
Average per-core data fill bandwidth to the L1 data cache
[GB / sec]"""


class Metric_L2_Cache_Fill_BW_2T:
    name = "L2_Cache_Fill_BW_2T"
    domain = "Core_Metric"
    maxval = 0
    errcount = 0
    area = "Info.Memory.Core"
    metricgroup = frozenset(['Mem', 'MemoryBW'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = L2_Cache_Fill_BW_2T(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "L2_Cache_Fill_BW_2T zero division")
    desc = """
Average per-core data fill bandwidth to the L2 cache [GB /
sec]"""


class Metric_L3_Cache_Fill_BW_2T:
    name = "L3_Cache_Fill_BW_2T"
    domain = "Core_Metric"
    maxval = 0
    errcount = 0
    area = "Info.Memory.Core"
    metricgroup = frozenset(['Mem', 'MemoryBW'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = L3_Cache_Fill_BW_2T(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "L3_Cache_Fill_BW_2T zero division")
    desc = """
Average per-core data fill bandwidth to the L3 cache [GB /
sec]"""


class Metric_Load_L2_Miss_Latency:
    name = "Load_L2_Miss_Latency"
    domain = "Clocks_Latency"
    maxval = 1000
    errcount = 0
    area = "Info.Memory.Latency"
    metricgroup = frozenset(['LockCont', 'Memory_Lat', 'Offcore'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Load_L2_Miss_Latency(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Load_L2_Miss_Latency zero division")
    desc = """
Average Latency for L2 cache miss demand Loads"""


class Metric_Load_L2_MLP:
    name = "Load_L2_MLP"
    domain = "Metric"
    maxval = 100
    errcount = 0
    area = "Info.Memory.Latency"
    metricgroup = frozenset(['Memory_BW', 'Offcore'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Load_L2_MLP(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Load_L2_MLP zero division")
    desc = """
Average Parallel L2 cache miss demand Loads"""


class Metric_Data_L2_MLP:
    name = "Data_L2_MLP"
    domain = "Metric"
    maxval = 100
    errcount = 0
    area = "Info.Memory.Latency"
    metricgroup = frozenset(['Memory_BW', 'Offcore'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Data_L2_MLP(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Data_L2_MLP zero division")
    desc = """
Average Parallel L2 cache miss data reads"""


class Metric_CPU_Utilization:
    name = "CPU_Utilization"
    domain = "Metric"
    maxval = 1
    errcount = 0
    area = "Info.System"
    metricgroup = frozenset(['HPC', 'Summary'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = CPU_Utilization(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "CPU_Utilization zero division")
    desc = """
Average CPU Utilization (percentage)"""


class Metric_CPUs_Utilized:
    name = "CPUs_Utilized"
    domain = "Metric"
    maxval = 300
    errcount = 0
    area = "Info.System"
    metricgroup = frozenset(['Summary'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = CPUs_Utilized(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "CPUs_Utilized zero division")
    desc = """
Average number of utilized CPUs"""


class Metric_Core_Frequency:
    name = "Core_Frequency"
    domain = "System_Metric"
    maxval = 0
    errcount = 0
    area = "Info.System"
    metricgroup = frozenset(['Summary', 'Power'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Core_Frequency(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Core_Frequency zero division")
    desc = """
Measured Average Core Frequency for unhalted processors
[GHz]"""


class Metric_Turbo_Utilization:
    name = "Turbo_Utilization"
    domain = "Core_Metric"
    maxval = 10
    errcount = 0
    area = "Info.System"
    metricgroup = frozenset(['Power'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Turbo_Utilization(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Turbo_Utilization zero division")
    desc = """
Average Frequency Utilization relative nominal frequency"""


class Metric_SMT_2T_Utilization:
    name = "SMT_2T_Utilization"
    domain = "Core_Metric"
    maxval = 1
    errcount = 0
    area = "Info.System"
    metricgroup = frozenset(['SMT'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = SMT_2T_Utilization(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "SMT_2T_Utilization zero division")
    desc = """
Fraction of cycles where both hardware Logical Processors
were active"""


class Metric_Kernel_Utilization:
    name = "Kernel_Utilization"
    domain = "Metric"
    maxval = 1
    errcount = 0
    area = "Info.System"
    metricgroup = frozenset(['OS'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Kernel_Utilization(self, EV, 0)
            self.thresh = (self.val > 0.05)
        except ZeroDivisionError:
            handle_error_metric(self, "Kernel_Utilization zero division")
    desc = """
Fraction of cycles spent in the Operating System (OS) Kernel
mode"""


class Metric_Kernel_CPI:
    name = "Kernel_CPI"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.System"
    metricgroup = frozenset(['OS'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Kernel_CPI(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Kernel_CPI zero division")
    desc = """
Cycles Per Instruction for the Operating System (OS) Kernel
mode"""


class Metric_DRAM_BW_Use:
    name = "DRAM_BW_Use"
    domain = "GB/sec"
    maxval = 200
    errcount = 0
    area = "Info.System"
    metricgroup = frozenset(['HPC', 'MemOffcore', 'MemoryBW', 'SoC'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = DRAM_BW_Use(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "DRAM_BW_Use zero division")
    desc = """
Average external Memory Bandwidth Use for reads and writes
[GB / sec]"""


class Metric_Power:
    name = "Power"
    domain = "System_Metric"
    maxval = 200
    errcount = 0
    area = "Info.System"
    metricgroup = frozenset(['Power', 'SoC'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Power(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Power zero division")
    desc = """
Total package Power in Watts"""


class Metric_Time:
    name = "Time"
    domain = "Seconds"
    maxval = 0
    errcount = 0
    area = "Info.System"
    metricgroup = frozenset(['Summary'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Time(self, EV, 0)
            self.thresh = (self.val < 1)
        except ZeroDivisionError:
            handle_error_metric(self, "Time zero division")
    desc = """
Run duration time in seconds"""


class Metric_Socket_CLKS:
    name = "Socket_CLKS"
    domain = "Count"
    maxval = 0
    errcount = 0
    area = "Info.System"
    metricgroup = frozenset(['SoC'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Socket_CLKS(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Socket_CLKS zero division")
    desc = """
Socket actual clocks when any core is active on that socket"""


class Metric_IpFarBranch:
    name = "IpFarBranch"
    domain = "Inst_Metric"
    maxval = 0
    errcount = 0
    area = "Info.System"
    metricgroup = frozenset(['Branches', 'OS'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpFarBranch(self, EV, 0)
            self.thresh = (self.val < 1000000)
        except ZeroDivisionError:
            handle_error_metric(self, "IpFarBranch zero division")
    desc = """
Instructions per Far Branch ( Far Branches apply upon
transition from application to operating system, handling
interrupts, exceptions) [lower number means higher
occurrence rate]"""


# Schedule



class Setup:
    def __init__(self, r):
        o = dict()
        n = Frontend_Bound() ; r.run(n) ; o["Frontend_Bound"] = n
        n = Fetch_Latency() ; r.run(n) ; o["Fetch_Latency"] = n
        n = ICache_Misses() ; r.run(n) ; o["ICache_Misses"] = n
        n = ITLB_Misses() ; r.run(n) ; o["ITLB_Misses"] = n
        n = Branch_Resteers() ; r.run(n) ; o["Branch_Resteers"] = n
        n = MS_Switches() ; r.run(n) ; o["MS_Switches"] = n
        n = LCP() ; r.run(n) ; o["LCP"] = n
        n = DSB_Switches() ; r.run(n) ; o["DSB_Switches"] = n
        n = Fetch_Bandwidth() ; r.run(n) ; o["Fetch_Bandwidth"] = n
        n = MITE() ; r.run(n) ; o["MITE"] = n
        n = DSB() ; r.run(n) ; o["DSB"] = n
        n = Bad_Speculation() ; r.run(n) ; o["Bad_Speculation"] = n
        n = Branch_Mispredicts() ; r.run(n) ; o["Branch_Mispredicts"] = n
        n = Machine_Clears() ; r.run(n) ; o["Machine_Clears"] = n
        n = Backend_Bound() ; r.run(n) ; o["Backend_Bound"] = n
        n = Memory_Bound() ; r.run(n) ; o["Memory_Bound"] = n
        n = L1_Bound() ; r.run(n) ; o["L1_Bound"] = n
        n = DTLB_Load() ; r.run(n) ; o["DTLB_Load"] = n
        n = Store_Fwd_Blk() ; r.run(n) ; o["Store_Fwd_Blk"] = n
        n = Lock_Latency() ; r.run(n) ; o["Lock_Latency"] = n
        n = Split_Loads() ; r.run(n) ; o["Split_Loads"] = n
        n = G4K_Aliasing() ; r.run(n) ; o["G4K_Aliasing"] = n
        n = FB_Full() ; r.run(n) ; o["FB_Full"] = n
        n = L2_Bound() ; r.run(n) ; o["L2_Bound"] = n
        n = L3_Bound() ; r.run(n) ; o["L3_Bound"] = n
        n = Contested_Accesses() ; r.run(n) ; o["Contested_Accesses"] = n
        n = Data_Sharing() ; r.run(n) ; o["Data_Sharing"] = n
        n = L3_Hit_Latency() ; r.run(n) ; o["L3_Hit_Latency"] = n
        n = SQ_Full() ; r.run(n) ; o["SQ_Full"] = n
        n = DRAM_Bound() ; r.run(n) ; o["DRAM_Bound"] = n
        n = MEM_Bandwidth() ; r.run(n) ; o["MEM_Bandwidth"] = n
        n = MEM_Latency() ; r.run(n) ; o["MEM_Latency"] = n
        n = Store_Bound() ; r.run(n) ; o["Store_Bound"] = n
        n = Store_Latency() ; r.run(n) ; o["Store_Latency"] = n
        n = False_Sharing() ; r.run(n) ; o["False_Sharing"] = n
        n = Split_Stores() ; r.run(n) ; o["Split_Stores"] = n
        n = DTLB_Store() ; r.run(n) ; o["DTLB_Store"] = n
        n = Core_Bound() ; r.run(n) ; o["Core_Bound"] = n
        n = Divider() ; r.run(n) ; o["Divider"] = n
        n = Ports_Utilization() ; r.run(n) ; o["Ports_Utilization"] = n
        n = Ports_Utilized_0() ; r.run(n) ; o["Ports_Utilized_0"] = n
        n = Ports_Utilized_1() ; r.run(n) ; o["Ports_Utilized_1"] = n
        n = Ports_Utilized_2() ; r.run(n) ; o["Ports_Utilized_2"] = n
        n = Ports_Utilized_3m() ; r.run(n) ; o["Ports_Utilized_3m"] = n
        n = ALU_Op_Utilization() ; r.run(n) ; o["ALU_Op_Utilization"] = n
        n = Port_0() ; r.run(n) ; o["Port_0"] = n
        n = Port_1() ; r.run(n) ; o["Port_1"] = n
        n = Port_5() ; r.run(n) ; o["Port_5"] = n
        n = Port_6() ; r.run(n) ; o["Port_6"] = n
        n = Load_Op_Utilization() ; r.run(n) ; o["Load_Op_Utilization"] = n
        n = Port_2() ; r.run(n) ; o["Port_2"] = n
        n = Port_3() ; r.run(n) ; o["Port_3"] = n
        n = Store_Op_Utilization() ; r.run(n) ; o["Store_Op_Utilization"] = n
        n = Port_4() ; r.run(n) ; o["Port_4"] = n
        n = Port_7() ; r.run(n) ; o["Port_7"] = n
        n = Retiring() ; r.run(n) ; o["Retiring"] = n
        n = Light_Operations() ; r.run(n) ; o["Light_Operations"] = n
        n = Heavy_Operations() ; r.run(n) ; o["Heavy_Operations"] = n
        n = Microcode_Sequencer() ; r.run(n) ; o["Microcode_Sequencer"] = n
        n = Assists() ; r.run(n) ; o["Assists"] = n
        n = CISC() ; r.run(n) ; o["CISC"] = n

        # parents

        o["Fetch_Latency"].parent = o["Frontend_Bound"]
        o["ICache_Misses"].parent = o["Fetch_Latency"]
        o["ITLB_Misses"].parent = o["Fetch_Latency"]
        o["Branch_Resteers"].parent = o["Fetch_Latency"]
        o["MS_Switches"].parent = o["Fetch_Latency"]
        o["LCP"].parent = o["Fetch_Latency"]
        o["DSB_Switches"].parent = o["Fetch_Latency"]
        o["Fetch_Bandwidth"].parent = o["Frontend_Bound"]
        o["MITE"].parent = o["Fetch_Bandwidth"]
        o["DSB"].parent = o["Fetch_Bandwidth"]
        o["Branch_Mispredicts"].parent = o["Bad_Speculation"]
        o["Machine_Clears"].parent = o["Bad_Speculation"]
        o["Memory_Bound"].parent = o["Backend_Bound"]
        o["L1_Bound"].parent = o["Memory_Bound"]
        o["DTLB_Load"].parent = o["L1_Bound"]
        o["Store_Fwd_Blk"].parent = o["L1_Bound"]
        o["Lock_Latency"].parent = o["L1_Bound"]
        o["Split_Loads"].parent = o["L1_Bound"]
        o["G4K_Aliasing"].parent = o["L1_Bound"]
        o["FB_Full"].parent = o["L1_Bound"]
        o["L2_Bound"].parent = o["Memory_Bound"]
        o["L3_Bound"].parent = o["Memory_Bound"]
        o["Contested_Accesses"].parent = o["L3_Bound"]
        o["Data_Sharing"].parent = o["L3_Bound"]
        o["L3_Hit_Latency"].parent = o["L3_Bound"]
        o["SQ_Full"].parent = o["L3_Bound"]
        o["DRAM_Bound"].parent = o["Memory_Bound"]
        o["MEM_Bandwidth"].parent = o["DRAM_Bound"]
        o["MEM_Latency"].parent = o["DRAM_Bound"]
        o["Store_Bound"].parent = o["Memory_Bound"]
        o["Store_Latency"].parent = o["Store_Bound"]
        o["False_Sharing"].parent = o["Store_Bound"]
        o["Split_Stores"].parent = o["Store_Bound"]
        o["DTLB_Store"].parent = o["Store_Bound"]
        o["Core_Bound"].parent = o["Backend_Bound"]
        o["Divider"].parent = o["Core_Bound"]
        o["Ports_Utilization"].parent = o["Core_Bound"]
        o["Ports_Utilized_0"].parent = o["Ports_Utilization"]
        o["Ports_Utilized_1"].parent = o["Ports_Utilization"]
        o["Ports_Utilized_2"].parent = o["Ports_Utilization"]
        o["Ports_Utilized_3m"].parent = o["Ports_Utilization"]
        o["ALU_Op_Utilization"].parent = o["Ports_Utilized_3m"]
        o["Port_0"].parent = o["ALU_Op_Utilization"]
        o["Port_1"].parent = o["ALU_Op_Utilization"]
        o["Port_5"].parent = o["ALU_Op_Utilization"]
        o["Port_6"].parent = o["ALU_Op_Utilization"]
        o["Load_Op_Utilization"].parent = o["Ports_Utilized_3m"]
        o["Port_2"].parent = o["Load_Op_Utilization"]
        o["Port_3"].parent = o["Load_Op_Utilization"]
        o["Store_Op_Utilization"].parent = o["Ports_Utilized_3m"]
        o["Port_4"].parent = o["Store_Op_Utilization"]
        o["Port_7"].parent = o["Store_Op_Utilization"]
        o["Light_Operations"].parent = o["Retiring"]
        o["Heavy_Operations"].parent = o["Retiring"]
        o["Microcode_Sequencer"].parent = o["Heavy_Operations"]
        o["Assists"].parent = o["Microcode_Sequencer"]
        o["CISC"].parent = o["Microcode_Sequencer"]

        # user visible metrics

        n = Metric_IPC() ; r.metric(n) ; o["IPC"] = n
        n = Metric_UopPI() ; r.metric(n) ; o["UopPI"] = n
        n = Metric_UpTB() ; r.metric(n) ; o["UpTB"] = n
        n = Metric_CPI() ; r.metric(n) ; o["CPI"] = n
        n = Metric_CLKS() ; r.metric(n) ; o["CLKS"] = n
        n = Metric_SLOTS() ; r.metric(n) ; o["SLOTS"] = n
        n = Metric_CoreIPC() ; r.metric(n) ; o["CoreIPC"] = n
        n = Metric_ILP() ; r.metric(n) ; o["ILP"] = n
        n = Metric_CORE_CLKS() ; r.metric(n) ; o["CORE_CLKS"] = n
        n = Metric_IpLoad() ; r.metric(n) ; o["IpLoad"] = n
        n = Metric_IpStore() ; r.metric(n) ; o["IpStore"] = n
        n = Metric_IpBranch() ; r.metric(n) ; o["IpBranch"] = n
        n = Metric_IpCall() ; r.metric(n) ; o["IpCall"] = n
        n = Metric_IpTB() ; r.metric(n) ; o["IpTB"] = n
        n = Metric_BpTkBranch() ; r.metric(n) ; o["BpTkBranch"] = n
        n = Metric_Instructions() ; r.metric(n) ; o["Instructions"] = n
        n = Metric_Retire() ; r.metric(n) ; o["Retire"] = n
        n = Metric_DSB_Coverage() ; r.metric(n) ; o["DSB_Coverage"] = n
        n = Metric_TBpC() ; r.metric(n) ; o["TBpC"] = n
        n = Metric_IpUnknown_Branch() ; r.metric(n) ; o["IpUnknown_Branch"] = n
        n = Metric_IpMispredict() ; r.metric(n) ; o["IpMispredict"] = n
        n = Metric_IpMisp_Indirect() ; r.metric(n) ; o["IpMisp_Indirect"] = n
        n = Metric_Load_Miss_Real_Latency() ; r.metric(n) ; o["Load_Miss_Real_Latency"] = n
        n = Metric_MLP() ; r.metric(n) ; o["MLP"] = n
        n = Metric_L1MPKI() ; r.metric(n) ; o["L1MPKI"] = n
        n = Metric_L2MPKI() ; r.metric(n) ; o["L2MPKI"] = n
        n = Metric_L2MPKI_RFO() ; r.metric(n) ; o["L2MPKI_RFO"] = n
        n = Metric_L3MPKI() ; r.metric(n) ; o["L3MPKI"] = n
        n = Metric_L1D_Cache_Fill_BW() ; r.metric(n) ; o["L1D_Cache_Fill_BW"] = n
        n = Metric_L2_Cache_Fill_BW() ; r.metric(n) ; o["L2_Cache_Fill_BW"] = n
        n = Metric_L3_Cache_Fill_BW() ; r.metric(n) ; o["L3_Cache_Fill_BW"] = n
        n = Metric_Page_Walks_Utilization() ; r.metric(n) ; o["Page_Walks_Utilization"] = n
        n = Metric_L1D_Cache_Fill_BW_2T() ; r.metric(n) ; o["L1D_Cache_Fill_BW_2T"] = n
        n = Metric_L2_Cache_Fill_BW_2T() ; r.metric(n) ; o["L2_Cache_Fill_BW_2T"] = n
        n = Metric_L3_Cache_Fill_BW_2T() ; r.metric(n) ; o["L3_Cache_Fill_BW_2T"] = n
        n = Metric_Load_L2_Miss_Latency() ; r.metric(n) ; o["Load_L2_Miss_Latency"] = n
        n = Metric_Load_L2_MLP() ; r.metric(n) ; o["Load_L2_MLP"] = n
        n = Metric_Data_L2_MLP() ; r.metric(n) ; o["Data_L2_MLP"] = n
        n = Metric_CPU_Utilization() ; r.metric(n) ; o["CPU_Utilization"] = n
        n = Metric_CPUs_Utilized() ; r.metric(n) ; o["CPUs_Utilized"] = n
        n = Metric_Core_Frequency() ; r.metric(n) ; o["Core_Frequency"] = n
        n = Metric_Turbo_Utilization() ; r.metric(n) ; o["Turbo_Utilization"] = n
        n = Metric_SMT_2T_Utilization() ; r.metric(n) ; o["SMT_2T_Utilization"] = n
        n = Metric_Kernel_Utilization() ; r.metric(n) ; o["Kernel_Utilization"] = n
        n = Metric_Kernel_CPI() ; r.metric(n) ; o["Kernel_CPI"] = n
        n = Metric_DRAM_BW_Use() ; r.metric(n) ; o["DRAM_BW_Use"] = n
        n = Metric_Power() ; r.metric(n) ; o["Power"] = n
        n = Metric_Time() ; r.metric(n) ; o["Time"] = n
        n = Metric_Socket_CLKS() ; r.metric(n) ; o["Socket_CLKS"] = n
        n = Metric_IpFarBranch() ; r.metric(n) ; o["IpFarBranch"] = n

        # references between groups

        o["Fetch_Bandwidth"].Frontend_Bound = o["Frontend_Bound"]
        o["Fetch_Bandwidth"].Fetch_Latency = o["Fetch_Latency"]
        o["Branch_Mispredicts"].Bad_Speculation = o["Bad_Speculation"]
        o["Machine_Clears"].Branch_Mispredicts = o["Branch_Mispredicts"]
        o["Machine_Clears"].Bad_Speculation = o["Bad_Speculation"]
        o["Backend_Bound"].Frontend_Bound = o["Frontend_Bound"]
        o["Backend_Bound"].Retiring = o["Retiring"]
        o["Backend_Bound"].Bad_Speculation = o["Bad_Speculation"]
        o["Memory_Bound"].Fetch_Latency = o["Fetch_Latency"]
        o["Memory_Bound"].Backend_Bound = o["Backend_Bound"]
        o["Memory_Bound"].Retiring = o["Retiring"]
        o["Memory_Bound"].Bad_Speculation = o["Bad_Speculation"]
        o["Memory_Bound"].Frontend_Bound = o["Frontend_Bound"]
        o["MEM_Latency"].MEM_Bandwidth = o["MEM_Bandwidth"]
        o["Core_Bound"].Backend_Bound = o["Backend_Bound"]
        o["Core_Bound"].Memory_Bound = o["Memory_Bound"]
        o["Core_Bound"].Frontend_Bound = o["Frontend_Bound"]
        o["Core_Bound"].Fetch_Latency = o["Fetch_Latency"]
        o["Core_Bound"].Retiring = o["Retiring"]
        o["Core_Bound"].Bad_Speculation = o["Bad_Speculation"]
        o["Ports_Utilization"].Fetch_Latency = o["Fetch_Latency"]
        o["Ports_Utilized_0"].Fetch_Latency = o["Fetch_Latency"]
        o["Retiring"].Heavy_Operations = o["Heavy_Operations"]
        o["Light_Operations"].Microcode_Sequencer = o["Microcode_Sequencer"]
        o["Light_Operations"].Retiring = o["Retiring"]
        o["Light_Operations"].Heavy_Operations = o["Heavy_Operations"]
        o["Heavy_Operations"].Microcode_Sequencer = o["Microcode_Sequencer"]
        o["CISC"].Microcode_Sequencer = o["Microcode_Sequencer"]
        o["CISC"].Assists = o["Assists"]

        # siblings cross-tree

        o["MS_Switches"].sibling = (o["Machine_Clears"], o["L1_Bound"], o["Microcode_Sequencer"],)
        o["LCP"].sibling = (o["DSB_Switches"], o["Fetch_Bandwidth"],)
        o["DSB_Switches"].sibling = (o["LCP"], o["Fetch_Bandwidth"],)
        o["Fetch_Bandwidth"].sibling = (o["LCP"], o["DSB_Switches"],)
        o["Machine_Clears"].sibling = (o["MS_Switches"], o["L1_Bound"], o["Contested_Accesses"], o["Data_Sharing"], o["False_Sharing"], o["Microcode_Sequencer"],)
        o["L1_Bound"].sibling = (o["MS_Switches"], o["Machine_Clears"], o["Ports_Utilized_1"], o["Microcode_Sequencer"],)
        o["DTLB_Load"].sibling = (o["DTLB_Store"],)
        o["Lock_Latency"].sibling = (o["Store_Latency"],)
        o["FB_Full"].sibling = (o["SQ_Full"], o["MEM_Bandwidth"], o["Store_Latency"],)
        o["Contested_Accesses"].sibling = (o["Machine_Clears"], o["Data_Sharing"], o["False_Sharing"],)
        o["Data_Sharing"].sibling = (o["Machine_Clears"], o["Contested_Accesses"], o["False_Sharing"],)
        o["L3_Hit_Latency"].sibling = (o["MEM_Latency"],)
        o["L3_Hit_Latency"].overlap = True
        o["SQ_Full"].sibling = (o["FB_Full"], o["MEM_Bandwidth"],)
        o["MEM_Bandwidth"].sibling = (o["FB_Full"], o["SQ_Full"],)
        o["MEM_Latency"].sibling = (o["L3_Hit_Latency"],)
        o["Store_Latency"].sibling = (o["Lock_Latency"], o["FB_Full"],)
        o["Store_Latency"].overlap = True
        o["False_Sharing"].sibling = (o["Machine_Clears"], o["Contested_Accesses"], o["Data_Sharing"],)
        o["Split_Stores"].sibling = (o["Port_4"],)
        o["DTLB_Store"].sibling = (o["DTLB_Load"],)
        o["Ports_Utilized_1"].sibling = (o["L1_Bound"],)
        o["Ports_Utilized_2"].sibling = (o["Port_0"], o["Port_1"], o["Port_5"], o["Port_6"],)
        o["Port_0"].sibling = (o["Ports_Utilized_2"], o["Port_1"], o["Port_5"], o["Port_6"],)
        o["Port_1"].sibling = (o["Ports_Utilized_2"], o["Port_0"], o["Port_5"], o["Port_6"],)
        o["Port_5"].sibling = (o["Ports_Utilized_2"], o["Port_0"], o["Port_1"], o["Port_6"],)
        o["Port_6"].sibling = (o["Ports_Utilized_2"], o["Port_0"], o["Port_1"], o["Port_5"],)
        o["Port_4"].sibling = (o["Split_Stores"],)
        o["Microcode_Sequencer"].sibling = (o["MS_Switches"], o["Machine_Clears"], o["L1_Bound"],)
        o["IpTB"].sibling = (o["LCP"], o["DSB_Switches"], o["Fetch_Bandwidth"],)
        o["DSB_Coverage"].sibling = (o["LCP"], o["DSB_Switches"], o["Fetch_Bandwidth"],)
        o["DRAM_BW_Use"].sibling = (o["FB_Full"], o["SQ_Full"], o["MEM_Bandwidth"],)
