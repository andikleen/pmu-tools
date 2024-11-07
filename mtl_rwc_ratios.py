# -*- coding: latin-1 -*-
#
# auto generated TopDown/TMA 5.01-full-perf description for Intel 14th gen Core (code name Meteor Lake) with Redwood Cove
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
topdown_use_fixed = False

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

Exe_Ports = 12
Mem_L2_Store_Cost = 10
Mem_STLB_Hit_Cost = 7
MS_Switches_Cost = 3
Avg_Assist_Cost = ( 99 *3 + 63 + 30 ) / 5
Pipeline_Width = 6
DSB_Width = 8
MITE_Width = 6
Decode_Width = 6
MS_Width = 4
Retire_Width = 8
OneMillion = 1000000
OneBillion = 1000000000
Energy_Unit = 61
PERF_METRICS_MSR = 1
DS = 0

# Aux. formulas


def Br_DoI_Jumps(self, EV, level):
    return EV("BR_INST_RETIRED.NEAR_TAKEN", level) - EV("BR_INST_RETIRED.COND_TAKEN", level) - 2 * EV("BR_INST_RETIRED.NEAR_CALL", level)

def Branching_Retired(self, EV, level):
    return (EV("BR_INST_RETIRED.ALL_BRANCHES", level) + 2 * EV("BR_INST_RETIRED.NEAR_CALL", level) + EV("INST_RETIRED.NOP", level)) / SLOTS(self, EV, level)

def Serialize_Core(self, EV, level):
    return self.Core_Bound.compute(EV) * (self.Serializing_Operation.compute(EV) + EV("RS.EMPTY_RESOURCE", level) / CLKS(self, EV, level) * self.Ports_Utilized_0.compute(EV)) / (self.Divider.compute(EV) + self.Ports_Utilization.compute(EV) + self.Serializing_Operation.compute(EV))

def Umisp(self, EV, level):
    return 10 * self.Microcode_Sequencer.compute(EV) * self.Other_Mispredicts.compute(EV) / self.Branch_Mispredicts.compute(EV)

def Assist(self, EV, level):
    return (self.Microcode_Sequencer.compute(EV) / (self.Few_Uops_Instructions.compute(EV) + self.Microcode_Sequencer.compute(EV))) * (self.Assists.compute(EV) / self.Microcode_Sequencer.compute(EV))

def Assist_Frontend(self, EV, level):
    return (1 - EV("INST_RETIRED.REP_ITERATION", level) / EV("UOPS_RETIRED.MS:c1", level)) * (self.Fetch_Latency.compute(EV) * (self.MS_Switches.compute(EV) + self.Branch_Resteers.compute(EV) * (self.Clears_Resteers.compute(EV) + self.Mispredicts_Resteers.compute(EV) * self.Other_Mispredicts.compute(EV) / self.Branch_Mispredicts.compute(EV)) / (self.Mispredicts_Resteers.compute(EV) + self.Unknown_Branches.compute(EV) + self.Clears_Resteers.compute(EV))) / (self.ITLB_Misses.compute(EV) + self.Branch_Resteers.compute(EV) + self.DSB_Switches.compute(EV) + self.LCP.compute(EV) + self.ICache_Misses.compute(EV) + self.MS_Switches.compute(EV)) + self.Fetch_Bandwidth.compute(EV) * self.MS.compute(EV) / (self.MITE.compute(EV) + self.DSB.compute(EV) + self.MS.compute(EV) + self.LSD.compute(EV)))

def Assist_Retired(self, EV, level):
    return Assist(self, EV, level) * self.Heavy_Operations.compute(EV)

def Core_Bound_Cycles(self, EV, level):
    return self.Ports_Utilized_0.compute(EV) * CLKS(self, EV, level) + Few_Uops_Executed_Threshold(self, EV, level)

def DurationTimeInSeconds(self, EV, level):
    return EV("interval-ms", 0) / 1000

def Execute_Cycles(self, EV, level):
    return (EV("UOPS_EXECUTED.CORE_CYCLES_GE_1", level) / 2) if smt_enabled else EV("UOPS_EXECUTED.THREAD:c1", level)

# factor used for metrics associating fixed costs for FB Hits - according to probability theory if all FB Hits come at a random rate in original L1_Miss cost interval then the average cost for each one is 0.5 of the fixed cost
def FB_Factor(self, EV, level):
    return 1 + FBHit_per_L1Miss(self, EV, level) / 2

def FBHit_per_L1Miss(self, EV, level):
    return EV("MEM_LOAD_RETIRED.FB_HIT", level) / EV("MEM_LOAD_RETIRED.L1_MISS", level)

def Fetched_Uops(self, EV, level):
    return EV("UOPS_ISSUED.ANY", level)

def Few_Uops_Executed_Threshold(self, EV, level):
    return EV("EXE_ACTIVITY.1_PORTS_UTIL", level) + self.Retiring.compute(EV) * EV("EXE_ACTIVITY.2_3_PORTS_UTIL", level)

# Floating Point computational (arithmetic) Operations Count
def FLOP_Count(self, EV, level):
    return EV("FP_ARITH_INST_RETIRED.SCALAR", level) + 2 * EV("FP_ARITH_INST_RETIRED.128B_PACKED_DOUBLE", level) + 4 * EV("FP_ARITH_INST_RETIRED.4_FLOPS", level) + 8 * EV("FP_ARITH_INST_RETIRED.256B_PACKED_SINGLE", level)

def FP_Arith_Scalar(self, EV, level):
    return EV("FP_ARITH_INST_RETIRED.SCALAR", level)

def FP_Arith_Vector(self, EV, level):
    return EV("FP_ARITH_INST_RETIRED.VECTOR", level)

def HighIPC(self, EV, level):
    val = IPC(self, EV, level) / Pipeline_Width
    return val

def Light_Ops_Sum(self, EV, level):
    return self.FP_Arith.compute(EV) + self.Int_Operations.compute(EV) + self.Memory_Operations.compute(EV) + self.Fused_Instructions.compute(EV) + self.Non_Fused_Branches.compute(EV)

def MEM_Bound_Ratio(self, EV, level):
    return EV("MEMORY_ACTIVITY.STALLS_L3_MISS", level) / CLKS(self, EV, level)

def Mem_Lock_St_Fraction(self, EV, level):
    return EV("MEM_INST_RETIRED.LOCK_LOADS", level) / EV("MEM_INST_RETIRED.ALL_STORES", level)

def Mispred_Clears_Fraction(self, EV, level):
    return self.Branch_Mispredicts.compute(EV) / self.Bad_Speculation.compute(EV)

def ORO_Demand_RFO_C1(self, EV, level):
    return EV(lambda EV , level : min(EV("CPU_CLK_UNHALTED.THREAD", level) , EV("OFFCORE_REQUESTS_OUTSTANDING.CYCLES_WITH_DEMAND_RFO", level)) , level )

def ORO_DRD_Any_Cycles(self, EV, level):
    return EV(lambda EV , level : min(EV("CPU_CLK_UNHALTED.THREAD", level) , EV("OFFCORE_REQUESTS_OUTSTANDING.CYCLES_WITH_DATA_RD", level)) , level )

def ORO_DRD_BW_Cycles(self, EV, level):
    return EV(lambda EV , level : min(EV("CPU_CLK_UNHALTED.THREAD", level) , EV("OFFCORE_REQUESTS_OUTSTANDING.DATA_RD:c4", level)) , level )

def Store_L2_Hit_Cycles(self, EV, level):
    return EV("MEM_STORE_RETIRED.L2_HIT", level) * Mem_L2_Store_Cost *(1 - Mem_Lock_St_Fraction(self, EV, level))

def True_XSNP_HitM_Fraction(self, EV, level):
    return EV("OCR.DEMAND_DATA_RD.L3_HIT.SNOOP_HITM", level) / (EV("OCR.DEMAND_DATA_RD.L3_HIT.SNOOP_HITM", level) + EV("OCR.DEMAND_DATA_RD.L3_HIT.SNOOP_HIT_WITH_FWD", level))

def Mem_XSNP_HitM_Cost(self, EV, level):
    return 28 * Core_Frequency(self, EV, level)

def Mem_XSNP_Hit_Cost(self, EV, level):
    return 27 * Core_Frequency(self, EV, level)

def Mem_XSNP_None_Cost(self, EV, level):
    return 12 * Core_Frequency(self, EV, level)

def Mem_L2_Hit_Cost(self, EV, level):
    return 3 * Core_Frequency(self, EV, level)

def PERF_METRICS_SUM(self, EV, level):
    return (EV("PERF_METRICS.FRONTEND_BOUND", level) / EV("TOPDOWN.SLOTS", level)) + (EV("PERF_METRICS.BAD_SPECULATION", level) / EV("TOPDOWN.SLOTS", level)) + (EV("PERF_METRICS.RETIRING", level) / EV("TOPDOWN.SLOTS", level)) + (EV("PERF_METRICS.BACKEND_BOUND", level) / EV("TOPDOWN.SLOTS", level))

def Retire_Fraction(self, EV, level):
    return EV("UOPS_RETIRED.SLOTS", level) / EV("UOPS_ISSUED.ANY", level)

def Retired_Slots(self, EV, level):
    return self.Retiring.compute(EV) * SLOTS(self, EV, level)

# Number of logical processors (enabled or online) on the target system
def Num_CPUs(self, EV, level):
    return num_cores * num_threads if num_cores else(8 + 16 /(2 - smt_enabled))

# A system parameter for dependent-loads (pointer chasing like access pattern) of the workload. An integer fraction in range from 0 (no dependent loads) to 100 (all loads are dependent loads)
def Dependent_Loads_Weight(self, EV, level):
    return 20

# Total pipeline cost of Branch Misprediction related bottlenecks
def Mispredictions(self, EV, level):
    val = 100 *(1 - Umisp(self, EV, level)) * (self.Branch_Mispredicts.compute(EV) + self.Fetch_Latency.compute(EV) * self.Mispredicts_Resteers.compute(EV) / (self.ITLB_Misses.compute(EV) + self.Branch_Resteers.compute(EV) + self.DSB_Switches.compute(EV) + self.LCP.compute(EV) + self.ICache_Misses.compute(EV) + self.MS_Switches.compute(EV)))
    self.thresh = (val > 20)
    return val

# Total pipeline cost of instruction fetch related bottlenecks by large code footprint programs (i-side cache; TLB and BTB misses)
def Big_Code(self, EV, level):
    val = 100 * self.Fetch_Latency.compute(EV) * (self.ITLB_Misses.compute(EV) + self.ICache_Misses.compute(EV) + self.Unknown_Branches.compute(EV)) / (self.ITLB_Misses.compute(EV) + self.Branch_Resteers.compute(EV) + self.DSB_Switches.compute(EV) + self.LCP.compute(EV) + self.ICache_Misses.compute(EV) + self.MS_Switches.compute(EV))
    self.thresh = (val > 20)
    return val

# Total pipeline cost of instruction fetch bandwidth related bottlenecks (when the front-end could not sustain operations delivery to the back-end)
def Instruction_Fetch_BW(self, EV, level):
    val = 100 *(self.Frontend_Bound.compute(EV) - (1 - Umisp(self, EV, level)) * self.Fetch_Latency.compute(EV) * self.Mispredicts_Resteers.compute(EV) / (self.ITLB_Misses.compute(EV) + self.Branch_Resteers.compute(EV) + self.DSB_Switches.compute(EV) + self.LCP.compute(EV) + self.ICache_Misses.compute(EV) + self.MS_Switches.compute(EV)) - Assist_Frontend(self, EV, level)) - Big_Code(self, EV, level)
    self.thresh = (val > 20)
    return val

# Total pipeline cost of external Memory- or Cache-Bandwidth related bottlenecks
def Cache_Memory_Bandwidth(self, EV, level):
    val = 100 *((self.Memory_Bound.compute(EV) * (self.DRAM_Bound.compute(EV) / (self.L1_Bound.compute(EV) + self.DRAM_Bound.compute(EV) + self.Store_Bound.compute(EV) + self.L2_Bound.compute(EV) + self.L3_Bound.compute(EV))) * (self.MEM_Bandwidth.compute(EV) / (self.MEM_Bandwidth.compute(EV) + self.MEM_Latency.compute(EV)))) + (self.Memory_Bound.compute(EV) * (self.L3_Bound.compute(EV) / (self.L1_Bound.compute(EV) + self.DRAM_Bound.compute(EV) + self.Store_Bound.compute(EV) + self.L2_Bound.compute(EV) + self.L3_Bound.compute(EV))) * (self.SQ_Full.compute(EV) / (self.Contested_Accesses.compute(EV) + self.Data_Sharing.compute(EV) + self.SQ_Full.compute(EV) + self.L3_Hit_Latency.compute(EV)))) + (self.Memory_Bound.compute(EV) * (self.L1_Bound.compute(EV) / (self.L1_Bound.compute(EV) + self.DRAM_Bound.compute(EV) + self.Store_Bound.compute(EV) + self.L2_Bound.compute(EV) + self.L3_Bound.compute(EV))) * (self.FB_Full.compute(EV) / (self.DTLB_Load.compute(EV) + self.Split_Loads.compute(EV) + self.FB_Full.compute(EV) + self.Lock_Latency.compute(EV) + self.L1_Latency_Dependency.compute(EV) + self.Store_Fwd_Blk.compute(EV)))))
    self.thresh = (val > 20)
    return val

# Total pipeline cost of external Memory- or Cache-Latency related bottlenecks
def Cache_Memory_Latency(self, EV, level):
    val = 100 *((self.Memory_Bound.compute(EV) * (self.DRAM_Bound.compute(EV) / (self.L1_Bound.compute(EV) + self.DRAM_Bound.compute(EV) + self.Store_Bound.compute(EV) + self.L2_Bound.compute(EV) + self.L3_Bound.compute(EV))) * (self.MEM_Latency.compute(EV) / (self.MEM_Bandwidth.compute(EV) + self.MEM_Latency.compute(EV)))) + (self.Memory_Bound.compute(EV) * (self.L3_Bound.compute(EV) / (self.L1_Bound.compute(EV) + self.DRAM_Bound.compute(EV) + self.Store_Bound.compute(EV) + self.L2_Bound.compute(EV) + self.L3_Bound.compute(EV))) * (self.L3_Hit_Latency.compute(EV) / (self.Contested_Accesses.compute(EV) + self.Data_Sharing.compute(EV) + self.SQ_Full.compute(EV) + self.L3_Hit_Latency.compute(EV)))) + (self.Memory_Bound.compute(EV) * self.L2_Bound.compute(EV) / (self.L1_Bound.compute(EV) + self.DRAM_Bound.compute(EV) + self.Store_Bound.compute(EV) + self.L2_Bound.compute(EV) + self.L3_Bound.compute(EV))) + (self.Memory_Bound.compute(EV) * (self.L1_Bound.compute(EV) / (self.L1_Bound.compute(EV) + self.DRAM_Bound.compute(EV) + self.Store_Bound.compute(EV) + self.L2_Bound.compute(EV) + self.L3_Bound.compute(EV))) * (self.L1_Latency_Dependency.compute(EV) / (self.DTLB_Load.compute(EV) + self.Split_Loads.compute(EV) + self.FB_Full.compute(EV) + self.Lock_Latency.compute(EV) + self.L1_Latency_Dependency.compute(EV) + self.Store_Fwd_Blk.compute(EV)))) + (self.Memory_Bound.compute(EV) * (self.L1_Bound.compute(EV) / (self.L1_Bound.compute(EV) + self.DRAM_Bound.compute(EV) + self.Store_Bound.compute(EV) + self.L2_Bound.compute(EV) + self.L3_Bound.compute(EV))) * (self.Lock_Latency.compute(EV) / (self.DTLB_Load.compute(EV) + self.Split_Loads.compute(EV) + self.FB_Full.compute(EV) + self.Lock_Latency.compute(EV) + self.L1_Latency_Dependency.compute(EV) + self.Store_Fwd_Blk.compute(EV)))) + (self.Memory_Bound.compute(EV) * (self.L1_Bound.compute(EV) / (self.L1_Bound.compute(EV) + self.DRAM_Bound.compute(EV) + self.Store_Bound.compute(EV) + self.L2_Bound.compute(EV) + self.L3_Bound.compute(EV))) * (self.Split_Loads.compute(EV) / (self.DTLB_Load.compute(EV) + self.Split_Loads.compute(EV) + self.FB_Full.compute(EV) + self.Lock_Latency.compute(EV) + self.L1_Latency_Dependency.compute(EV) + self.Store_Fwd_Blk.compute(EV)))) + (self.Memory_Bound.compute(EV) * (self.Store_Bound.compute(EV) / (self.L1_Bound.compute(EV) + self.DRAM_Bound.compute(EV) + self.Store_Bound.compute(EV) + self.L2_Bound.compute(EV) + self.L3_Bound.compute(EV))) * (self.Split_Stores.compute(EV) / (self.DTLB_Store.compute(EV) + self.Split_Stores.compute(EV) + self.Store_Latency.compute(EV) + self.False_Sharing.compute(EV) + self.Streaming_Stores.compute(EV)))) + (self.Memory_Bound.compute(EV) * (self.Store_Bound.compute(EV) / (self.L1_Bound.compute(EV) + self.DRAM_Bound.compute(EV) + self.Store_Bound.compute(EV) + self.L2_Bound.compute(EV) + self.L3_Bound.compute(EV))) * (self.Store_Latency.compute(EV) / (self.DTLB_Store.compute(EV) + self.Split_Stores.compute(EV) + self.Store_Latency.compute(EV) + self.False_Sharing.compute(EV) + self.Streaming_Stores.compute(EV)))))
    self.thresh = (val > 20)
    return val

# Total pipeline cost of Memory Address Translation related bottlenecks (data-side TLBs)
def Memory_Data_TLBs(self, EV, level):
    val = 100 *((self.Memory_Bound.compute(EV) * (self.L1_Bound.compute(EV) / (self.L1_Bound.compute(EV) + self.DRAM_Bound.compute(EV) + self.Store_Bound.compute(EV) + self.L2_Bound.compute(EV) + self.L3_Bound.compute(EV))) * (self.DTLB_Load.compute(EV) / (self.DTLB_Load.compute(EV) + self.Split_Loads.compute(EV) + self.FB_Full.compute(EV) + self.Lock_Latency.compute(EV) + self.L1_Latency_Dependency.compute(EV) + self.Store_Fwd_Blk.compute(EV)))) + (self.Memory_Bound.compute(EV) * (self.Store_Bound.compute(EV) / (self.L1_Bound.compute(EV) + self.DRAM_Bound.compute(EV) + self.Store_Bound.compute(EV) + self.L2_Bound.compute(EV) + self.L3_Bound.compute(EV))) * (self.DTLB_Store.compute(EV) / (self.DTLB_Store.compute(EV) + self.Split_Stores.compute(EV) + self.Store_Latency.compute(EV) + self.False_Sharing.compute(EV) + self.Streaming_Stores.compute(EV)))))
    self.thresh = (val > 20)
    return val

# Total pipeline cost of Memory Synchronization related bottlenecks (data transfers and coherency updates across processors)
def Memory_Synchronization(self, EV, level):
    val = 100 *(self.Memory_Bound.compute(EV) * ((self.L3_Bound.compute(EV) / (self.L1_Bound.compute(EV) + self.DRAM_Bound.compute(EV) + self.Store_Bound.compute(EV) + self.L2_Bound.compute(EV) + self.L3_Bound.compute(EV))) * (self.Contested_Accesses.compute(EV) + self.Data_Sharing.compute(EV)) / (self.Contested_Accesses.compute(EV) + self.Data_Sharing.compute(EV) + self.SQ_Full.compute(EV) + self.L3_Hit_Latency.compute(EV)) + (self.Store_Bound.compute(EV) / (self.L1_Bound.compute(EV) + self.DRAM_Bound.compute(EV) + self.Store_Bound.compute(EV) + self.L2_Bound.compute(EV) + self.L3_Bound.compute(EV))) * self.False_Sharing.compute(EV) / ((self.DTLB_Store.compute(EV) + self.Split_Stores.compute(EV) + self.Store_Latency.compute(EV) + self.False_Sharing.compute(EV) + self.Streaming_Stores.compute(EV)) - self.Store_Latency.compute(EV))) + self.Machine_Clears.compute(EV) * (1 - self.Other_Nukes.compute(EV) / (self.Other_Nukes.compute(EV))))
    self.thresh = (val > 10)
    return val

# Total pipeline cost when the execution is compute-bound - an estimation. Covers Core Bound when High ILP as well as when long-latency execution units are busy.
def Compute_Bound_Est(self, EV, level):
    val = 100 *((self.Core_Bound.compute(EV) * self.Divider.compute(EV) / (self.Divider.compute(EV) + self.Ports_Utilization.compute(EV) + self.Serializing_Operation.compute(EV))) + (self.Core_Bound.compute(EV) * (self.Ports_Utilization.compute(EV) / (self.Divider.compute(EV) + self.Ports_Utilization.compute(EV) + self.Serializing_Operation.compute(EV))) * (self.Ports_Utilized_3m.compute(EV) / (self.Ports_Utilized_2.compute(EV) + self.Ports_Utilized_3m.compute(EV) + self.Ports_Utilized_1.compute(EV) + self.Ports_Utilized_0.compute(EV)))))
    self.thresh = (val > 20)
    return val

# Total pipeline cost of irregular execution (e.g. FP-assists in HPC, Wait time with work imbalance multithreaded workloads, overhead in system services or virtualized environments)
def Irregular_Overhead(self, EV, level):
    val = 100 *(Assist_Frontend(self, EV, level) + Umisp(self, EV, level) * self.Branch_Mispredicts.compute(EV) + (self.Machine_Clears.compute(EV) * self.Other_Nukes.compute(EV) / (self.Other_Nukes.compute(EV))) + Serialize_Core(self, EV, level) + Assist_Retired(self, EV, level))
    self.thresh = (val > 10)
    return val

# Total pipeline cost of remaining bottlenecks in the back-end. Examples include data-dependencies (Core Bound when Low ILP) and other unlisted memory-related stalls.
def Other_Bottlenecks(self, EV, level):
    val = 100 -(Big_Code(self, EV, level) + Instruction_Fetch_BW(self, EV, level) + Mispredictions(self, EV, level) + Cache_Memory_Bandwidth(self, EV, level) + Cache_Memory_Latency(self, EV, level) + Memory_Data_TLBs(self, EV, level) + Memory_Synchronization(self, EV, level) + Compute_Bound_Est(self, EV, level) + Irregular_Overhead(self, EV, level) + Branching_Overhead(self, EV, level) + Useful_Work(self, EV, level))
    self.thresh = (val > 20)
    return val

# Total pipeline cost of instructions used for program control-flow - a subset of the Retiring category in TMA. Examples include function calls; loops and alignments. (A lower bound). Consider Loop Unrolling or function inlining optimizations
def Branching_Overhead(self, EV, level):
    val = 100 * Branching_Retired(self, EV, level)
    self.thresh = (val > 5)
    return val

# Total pipeline cost of "useful operations" - the portion of Retiring category not covered by Branching_Overhead nor Irregular_Overhead.
def Useful_Work(self, EV, level):
    val = 100 *(self.Retiring.compute(EV) - Branching_Retired(self, EV, level) - Assist_Retired(self, EV, level))
    self.thresh = (val > 20)
    return val

# Probability of Core Bound bottleneck hidden by SMT-profiling artifacts. Tip: consider analysis with SMT disabled
def Core_Bound_Likely(self, EV, level):
    val = 100 *(1 - self.Core_Bound.compute(EV) / self.Ports_Utilization.compute(EV) if self.Core_Bound.compute(EV)< self.Ports_Utilization.compute(EV) else 1) if SMT_2T_Utilization(self, EV, level)> 0.5 else 0
    self.thresh = (val > 0.5)
    return val

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
    return EV("TOPDOWN.SLOTS", level) if topdown_use_fixed else EV("TOPDOWN.SLOTS", level)

# Fraction of Physical Core issue-slots utilized by this Logical Processor
def Slots_Utilization(self, EV, level):
    return SLOTS(self, EV, level) / (EV("TOPDOWN.SLOTS:percore", level) / 2) if smt_enabled else 1

# The ratio of Executed- by Issued-Uops. Ratio > 1 suggests high rate of uop micro-fusions. Ratio < 1 suggest high rate of "execute" at rename stage.
def Execute_per_Issue(self, EV, level):
    return EV("UOPS_EXECUTED.THREAD", level) / EV("UOPS_ISSUED.ANY", level)

# Instructions Per Cycle across hyper-threads (per physical core)
def CoreIPC(self, EV, level):
    return EV("INST_RETIRED.ANY", level) / CORE_CLKS(self, EV, level)

# Floating Point Operations Per Cycle
def FLOPc(self, EV, level):
    return FLOP_Count(self, EV, level) / CORE_CLKS(self, EV, level)

# Actual per-core usage of the Floating Point non-X87 execution units (regardless of precision or vector-width). Values > 1 are possible due to  Fused-Multiply Add  use all of ADD/MUL/FMA in Scalar or 128/256-bit vectors - less common.
def FP_Arith_Utilization(self, EV, level):
    return (EV("FP_ARITH_DISPATCHED.PORT_0", level) + EV("FP_ARITH_DISPATCHED.PORT_1", level) + EV("FP_ARITH_DISPATCHED.PORT_5", level)) / (2 * CORE_CLKS(self, EV, level))

# Instruction-Level-Parallelism (average number of uops executed when there is execution) per thread (logical-processor)
def ILP(self, EV, level):
    return EV("UOPS_EXECUTED.THREAD", level) / EV("UOPS_EXECUTED.THREAD:c1", level)

# uops Executed per Cycle
def EPC(self, EV, level):
    return EV("UOPS_EXECUTED.THREAD", level) / CLKS(self, EV, level)

# Core actual clocks when any Logical Processor is active on the Physical Core
def CORE_CLKS(self, EV, level):
    return EV("CPU_CLK_UNHALTED.DISTRIBUTED", level) if smt_enabled else CLKS(self, EV, level)

# Instructions per Load (lower number means higher occurrence rate). Tip: reduce memory accesses. #Link Opt Guide section: Minimize Register Spills
def IpLoad(self, EV, level):
    val = EV("INST_RETIRED.ANY", level) / EV("MEM_INST_RETIRED.ALL_LOADS", level)
    self.thresh = (val < 3)
    return val

# Instructions per Store (lower number means higher occurrence rate). Tip: reduce memory accesses. #Link Opt Guide section: Minimize Register Spills
def IpStore(self, EV, level):
    val = EV("INST_RETIRED.ANY", level) / EV("MEM_INST_RETIRED.ALL_STORES", level)
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

# Instructions per Floating Point (FP) Operation (lower number means higher occurrence rate). Reference: Tuning Performance via Metrics with Expectations. https://doi.org/10.1109/LCA.2019.2916408
def IpFLOP(self, EV, level):
    val = EV("INST_RETIRED.ANY", level) / FLOP_Count(self, EV, level)
    self.thresh = (val < 10)
    return val

# Instructions per FP Arithmetic instruction (lower number means higher occurrence rate). Values < 1 are possible due to intentional FMA double counting. Approximated prior to BDW.
def IpArith(self, EV, level):
    val = EV("INST_RETIRED.ANY", level) / (FP_Arith_Scalar(self, EV, level) + FP_Arith_Vector(self, EV, level))
    self.thresh = (val < 10)
    return val

# Instructions per FP Arithmetic Scalar Single-Precision instruction (lower number means higher occurrence rate). Values < 1 are possible due to intentional FMA double counting.
def IpArith_Scalar_SP(self, EV, level):
    val = EV("INST_RETIRED.ANY", level) / EV("FP_ARITH_INST_RETIRED.SCALAR_SINGLE", level)
    self.thresh = (val < 10)
    return val

# Instructions per FP Arithmetic Scalar Double-Precision instruction (lower number means higher occurrence rate). Values < 1 are possible due to intentional FMA double counting.
def IpArith_Scalar_DP(self, EV, level):
    val = EV("INST_RETIRED.ANY", level) / EV("FP_ARITH_INST_RETIRED.SCALAR_DOUBLE", level)
    self.thresh = (val < 10)
    return val

# Instructions per FP Arithmetic AVX/SSE 128-bit instruction (lower number means higher occurrence rate). Values < 1 are possible due to intentional FMA double counting.
def IpArith_AVX128(self, EV, level):
    val = EV("INST_RETIRED.ANY", level) / (EV("FP_ARITH_INST_RETIRED.128B_PACKED_DOUBLE", level) + EV("FP_ARITH_INST_RETIRED.128B_PACKED_SINGLE", level))
    self.thresh = (val < 10)
    return val

# Instructions per FP Arithmetic AVX* 256-bit instruction (lower number means higher occurrence rate). Values < 1 are possible due to intentional FMA double counting.
def IpArith_AVX256(self, EV, level):
    val = EV("INST_RETIRED.ANY", level) / (EV("FP_ARITH_INST_RETIRED.256B_PACKED_DOUBLE", level) + EV("FP_ARITH_INST_RETIRED.256B_PACKED_SINGLE", level))
    self.thresh = (val < 10)
    return val

# Instructions per PAUSE (lower number means higher occurrence rate)
def IpPause(self, EV, level):
    return Instructions(self, EV, level) / EV("CPU_CLK_UNHALTED.PAUSE_INST", level)

# Instructions per Software prefetch instruction (of any type: NTA/T0/T1/T2/Prefetch) (lower number means higher occurrence rate)
def IpSWPF(self, EV, level):
    val = EV("INST_RETIRED.ANY", level) / EV("SW_PREFETCH_ACCESS.ANY", level)
    self.thresh = (val < 100)
    return val

# Total number of retired Instructions
def Instructions(self, EV, level):
    return EV("INST_RETIRED.ANY", level)

# Average number of Uops retired in cycles where at least one uop has retired.
def Retire(self, EV, level):
    return Retired_Slots(self, EV, level) / EV("UOPS_RETIRED.SLOTS:c1", level)

# Estimated fraction of retirement-cycles dealing with repeat instructions
def Strings_Cycles(self, EV, level):
    val = EV("INST_RETIRED.REP_ITERATION", level) / EV("UOPS_RETIRED.SLOTS:c1", level)
    self.thresh = (val > 0.1)
    return val

# Instructions per a microcode Assist invocation. See Assists tree node for details (lower number means higher occurrence rate)
def IpAssist(self, EV, level):
    val = EV("INST_RETIRED.ANY", level) / EV("ASSISTS.ANY", level)
    self.thresh = (val < 100000)
    return val

# Instruction-Level-Parallelism (average number of uops executed when there is execution) per physical core
def Execute(self, EV, level):
    return EV("UOPS_EXECUTED.THREAD", level) / Execute_Cycles(self, EV, level)

# Average number of uops fetched from LSD per cycle
def Fetch_LSD(self, EV, level):
    return EV("LSD.UOPS", level) / EV("LSD.CYCLES_ACTIVE", level)

# Average number of uops fetched from DSB per cycle
def Fetch_DSB(self, EV, level):
    return EV("IDQ.DSB_UOPS", level) / EV("IDQ.DSB_CYCLES_ANY", level)

# Average number of uops fetched from MITE per cycle
def Fetch_MITE(self, EV, level):
    return EV("IDQ.MITE_UOPS", level) / EV("IDQ.MITE_CYCLES_ANY", level)

# Average number of Uops issued by front-end when it issued something
def Fetch_UpC(self, EV, level):
    return EV("UOPS_ISSUED.ANY", level) / EV("UOPS_ISSUED.ANY:c1", level)

# Fraction of Uops delivered by the LSD (Loop Stream Detector; aka Loop Cache)
def LSD_Coverage(self, EV, level):
    return EV("LSD.UOPS", level) / Fetched_Uops(self, EV, level)

# Fraction of Uops delivered by the DSB (aka Decoded ICache; or Uop Cache). See section 'Decoded ICache' in Optimization Manual. http://www.intel.com/content/www/us/en/architecture-and-technology/64-ia-32-architectures-optimization-manual.html
def DSB_Coverage(self, EV, level):
    val = EV("IDQ.DSB_UOPS", level) / Fetched_Uops(self, EV, level)
    self.thresh = (val < 0.7) and HighIPC(self, EV, 1)
    return val

# Average number of cycles the front-end was delayed due to an Unknown Branch detection. See Unknown_Branches node.
def Unknown_Branch_Cost(self, EV, level):
    return EV("INT_MISC.UNKNOWN_BRANCH_CYCLES", level) / EV("INT_MISC.UNKNOWN_BRANCH_CYCLES:c1:e1", level)

# Average number of cycles of a switch from the DSB fetch-unit to MITE fetch unit - see DSB_Switches tree node for details.
def DSB_Switch_Cost(self, EV, level):
    return EV("DSB2MITE_SWITCHES.PENALTY_CYCLES", level) / EV("DSB2MITE_SWITCHES.PENALTY_CYCLES:c1:e1", level)

# Taken Branches retired Per Cycle
def TBpC(self, EV, level):
    return EV("BR_INST_RETIRED.NEAR_TAKEN", level) / CLKS(self, EV, level)

# Total pipeline cost of DSB (uop cache) misses - subset of the Instruction_Fetch_BW Bottleneck.
def DSB_Misses(self, EV, level):
    val = 100 *(self.Fetch_Latency.compute(EV) * self.DSB_Switches.compute(EV) / (self.ITLB_Misses.compute(EV) + self.Branch_Resteers.compute(EV) + self.DSB_Switches.compute(EV) + self.LCP.compute(EV) + self.ICache_Misses.compute(EV) + self.MS_Switches.compute(EV)) + self.Fetch_Bandwidth.compute(EV) * self.MITE.compute(EV) / (self.MITE.compute(EV) + self.DSB.compute(EV) + self.MS.compute(EV) + self.LSD.compute(EV)))
    self.thresh = (val > 10)
    return val

# Total pipeline cost of DSB (uop cache) hits - subset of the Instruction_Fetch_BW Bottleneck.
def DSB_Bandwidth(self, EV, level):
    val = 100 *(self.Frontend_Bound.compute(EV) * (self.Fetch_Bandwidth.compute(EV) / (self.Fetch_Latency.compute(EV) + self.Fetch_Bandwidth.compute(EV))) * (self.DSB.compute(EV) / (self.MITE.compute(EV) + self.DSB.compute(EV) + self.MS.compute(EV) + self.LSD.compute(EV))))
    self.thresh = (val > 10)
    return val

# This metric represents fraction of cycles the CPU retirement was stalled likely due to retired DSB misses
def DSB_Switches_Ret(self, EV, level):
    val = EV("FRONTEND_RETIRED.ANY_DSB_MISS", level) * EV("FRONTEND_RETIRED.ANY_DSB_MISS", 999) / CLKS(self, EV, level)
    self.thresh = (val > 0.05)
    return val

# This metric represents fraction of cycles the CPU retirement was stalled likely due to retired operations that invoke the Microcode Sequencer
def MS_Latency_Ret(self, EV, level):
    val = EV("FRONTEND_RETIRED.MS_FLOWS", level) * EV("FRONTEND_RETIRED.MS_FLOWS", 999) / CLKS(self, EV, level)
    self.thresh = (val > 0.05)
    return val

# This metric represents fraction of cycles the CPU retirement was stalled likely due to retired branches who got branch address clears
def Unknown_Branches_Ret(self, EV, level):
    return EV("FRONTEND_RETIRED.UNKNOWN_BRANCH", level) * EV("FRONTEND_RETIRED.UNKNOWN_BRANCH", 999) / CLKS(self, EV, level)

# Average Latency for L1 instruction cache misses
def ICache_Miss_Latency(self, EV, level):
    return EV("ICACHE_DATA.STALLS", level) / EV("ICACHE_DATA.STALL_PERIODS", level)

# Total pipeline cost of Instruction Cache misses - subset of the Big_Code Bottleneck.
def IC_Misses(self, EV, level):
    val = 100 *(self.Fetch_Latency.compute(EV) * self.ICache_Misses.compute(EV) / (self.ITLB_Misses.compute(EV) + self.Branch_Resteers.compute(EV) + self.DSB_Switches.compute(EV) + self.LCP.compute(EV) + self.ICache_Misses.compute(EV) + self.MS_Switches.compute(EV)))
    self.thresh = (val > 5)
    return val

# Instructions per non-speculative DSB miss (lower number means higher occurrence rate)
def IpDSB_Miss_Ret(self, EV, level):
    val = EV("INST_RETIRED.ANY", level) / EV("FRONTEND_RETIRED.ANY_DSB_MISS", level)
    self.thresh = (val < 50)
    return val

# Instructions per speculative Unknown Branch Misprediction (BAClear) (lower number means higher occurrence rate)
def IpUnknown_Branch(self, EV, level):
    return Instructions(self, EV, level) / EV("BACLEARS.ANY", level)

# L2 cache true code cacheline misses per kilo instruction 
def L2MPKI_Code(self, EV, level):
    return 1000 * EV("FRONTEND_RETIRED.L2_MISS", level) / EV("INST_RETIRED.ANY", level)

# L2 cache speculative code cacheline misses per kilo instruction 
def L2MPKI_Code_All(self, EV, level):
    return 1000 * EV("L2_RQSTS.CODE_RD_MISS", level) / EV("INST_RETIRED.ANY", level)

# Number of Instructions per non-speculative Branch Misprediction (JEClear) (lower number means higher occurrence rate)
def IpMispredict(self, EV, level):
    val = EV("INST_RETIRED.ANY", level) / EV("BR_MISP_RETIRED.ALL_BRANCHES", level)
    self.thresh = (val < 200)
    return val

# Instructions per retired Mispredicts for conditional non-taken branches (lower number means higher occurrence rate).
def IpMisp_Cond_Ntaken(self, EV, level):
    val = EV("INST_RETIRED.ANY", level) / EV("BR_MISP_RETIRED.COND_NTAKEN", level)
    self.thresh = (val < 200)
    return val

# Instructions per retired Mispredicts for conditional taken branches (lower number means higher occurrence rate).
def IpMisp_Cond_Taken(self, EV, level):
    val = EV("INST_RETIRED.ANY", level) / EV("BR_MISP_RETIRED.COND_TAKEN", level)
    self.thresh = (val < 200)
    return val

# Instructions per retired Mispredicts for return branches (lower number means higher occurrence rate).
def IpMisp_Ret(self, EV, level):
    val = EV("INST_RETIRED.ANY", level) / EV("BR_MISP_RETIRED.RET", level)
    self.thresh = (val < 500)
    return val

# Instructions per retired Mispredicts for indirect CALL or JMP branches (lower number means higher occurrence rate).
def IpMisp_Indirect(self, EV, level):
    val = EV("INST_RETIRED.ANY", level) / EV("BR_MISP_RETIRED.INDIRECT", level)
    self.thresh = (val < 1000)
    return val

# Branch Misprediction Cost: Cycles representing fraction of TMA slots wasted per non-speculative branch misprediction (retired JEClear)
def Branch_Misprediction_Cost(self, EV, level):
    return Mispredictions(self, EV, level) * SLOTS(self, EV, level) / Pipeline_Width / EV("BR_MISP_RETIRED.ALL_BRANCHES", level) / 100

# Speculative to Retired ratio of all clears (covering Mispredicts and nukes)
def Spec_Clears_Ratio(self, EV, level):
    return EV("INT_MISC.CLEARS_COUNT", level) / (EV("BR_MISP_RETIRED.ALL_BRANCHES", level) + EV("MACHINE_CLEARS.COUNT", level))

# Fraction of branches that are non-taken conditionals
def Cond_NT(self, EV, level):
    return EV("BR_INST_RETIRED.COND_NTAKEN", level) / EV("BR_INST_RETIRED.ALL_BRANCHES", level)

# Fraction of branches that are taken conditionals
def Cond_TK(self, EV, level):
    return EV("BR_INST_RETIRED.COND_TAKEN", level) / EV("BR_INST_RETIRED.ALL_BRANCHES", level)

# Fraction of branches that are CALL or RET
def CallRet(self, EV, level):
    return (EV("BR_INST_RETIRED.NEAR_CALL", level) + EV("BR_INST_RETIRED.NEAR_RETURN", level)) / EV("BR_INST_RETIRED.ALL_BRANCHES", level)

# Fraction of branches that are unconditional (direct or indirect) jumps
def Jump(self, EV, level):
    return Br_DoI_Jumps(self, EV, level) / EV("BR_INST_RETIRED.ALL_BRANCHES", level)

# Fraction of branches of other types (not individually covered by other metrics in Info.Branches group)
def Other_Branches(self, EV, level):
    return 1 -(Cond_NT(self, EV, level) + Cond_TK(self, EV, level) + CallRet(self, EV, level) + Jump(self, EV, level))

# Actual Average Latency for L1 data-cache miss demand load operations (in core cycles)
def Load_Miss_Real_Latency(self, EV, level):
    return EV("L1D_PEND_MISS.PENDING", level) / EV("MEM_LOAD_COMPLETED.L1_MISS_ANY", level)

# Memory-Level-Parallelism (average number of L1 miss demand load when there is at least one such miss. Per-Logical Processor)
def MLP(self, EV, level):
    return EV("L1D_PEND_MISS.PENDING", level) / EV("L1D_PEND_MISS.PENDING_CYCLES", level)

# L1 cache true misses per kilo instruction for retired demand loads
def L1MPKI(self, EV, level):
    return 1000 * EV("MEM_LOAD_RETIRED.L1_MISS", level) / EV("INST_RETIRED.ANY", level)

# L1 cache true misses per kilo instruction for all demand loads (including speculative)
def L1MPKI_Load(self, EV, level):
    return 1000 * EV("L2_RQSTS.ALL_DEMAND_DATA_RD", level) / EV("INST_RETIRED.ANY", level)

# L2 cache true misses per kilo instruction for retired demand loads
def L2MPKI(self, EV, level):
    return 1000 * EV("MEM_LOAD_RETIRED.L2_MISS", level) / EV("INST_RETIRED.ANY", level)

# L2 cache  true misses per kilo instruction for all request types (including speculative)
def L2MPKI_All(self, EV, level):
    return 1000 * EV("L2_RQSTS.MISS", level) / EV("INST_RETIRED.ANY", level)

# L2 cache  true misses per kilo instruction for all demand loads  (including speculative)
def L2MPKI_Load(self, EV, level):
    return 1000 * EV("L2_RQSTS.DEMAND_DATA_RD_MISS", level) / EV("INST_RETIRED.ANY", level)

# Offcore requests (L2 cache miss) per kilo instruction for demand RFOs
def L2MPKI_RFO(self, EV, level):
    return 1000 * EV("L2_RQSTS.RFO_MISS", level) / EV("INST_RETIRED.ANY", level)

# L2 cache hits per kilo instruction for all request types (including speculative)
def L2HPKI_All(self, EV, level):
    return 1000 *(EV("L2_RQSTS.REFERENCES", level) - EV("L2_RQSTS.MISS", level)) / EV("INST_RETIRED.ANY", level)

# L2 cache hits per kilo instruction for all demand loads  (including speculative)
def L2HPKI_Load(self, EV, level):
    return 1000 * EV("L2_RQSTS.DEMAND_DATA_RD_HIT", level) / EV("INST_RETIRED.ANY", level)

# L3 cache true misses per kilo instruction for retired demand loads
def L3MPKI(self, EV, level):
    return 1000 * EV("MEM_LOAD_RETIRED.L3_MISS", level) / EV("INST_RETIRED.ANY", level)

# Fill Buffer (FB) hits per kilo instructions for retired demand loads (L1D misses that merge into ongoing miss-handling entries)
def FB_HPKI(self, EV, level):
    return 1000 * EV("MEM_LOAD_RETIRED.FB_HIT", level) / EV("INST_RETIRED.ANY", level)

# Average per-thread data fill bandwidth to the L1 data cache [GB / sec]
def L1D_Cache_Fill_BW(self, EV, level):
    return 64 * EV("L1D.REPLACEMENT", level) / OneBillion / Time(self, EV, level)

# Average per-thread data fill bandwidth to the L2 cache [GB / sec]
def L2_Cache_Fill_BW(self, EV, level):
    return 64 * EV("L2_LINES_IN.ALL", level) / OneBillion / Time(self, EV, level)

# Average per-thread data fill bandwidth to the L3 cache [GB / sec]
def L3_Cache_Fill_BW(self, EV, level):
    return 64 * EV("LONGEST_LAT_CACHE.MISS", level) / OneBillion / Time(self, EV, level)

# Average per-thread data access bandwidth to the L3 cache [GB / sec]
def L3_Cache_Access_BW(self, EV, level):
    return 64 * EV("OFFCORE_REQUESTS.ALL_REQUESTS", level) / OneBillion / Time(self, EV, level)

# Utilization of the core's Page Walker(s) serving STLB misses triggered by instruction/Load/Store accesses
def Page_Walks_Utilization(self, EV, level):
    val = (EV("ITLB_MISSES.WALK_PENDING", level) + EV("DTLB_LOAD_MISSES.WALK_PENDING", level) + EV("DTLB_STORE_MISSES.WALK_PENDING", level)) / (4 * CORE_CLKS(self, EV, level))
    self.thresh = (val > 0.5)
    return val

# STLB (2nd level TLB) code speculative misses per kilo instruction (misses of any page-size that complete the page walk)
def Code_STLB_MPKI(self, EV, level):
    return 1000 * EV("ITLB_MISSES.WALK_COMPLETED", level) / EV("INST_RETIRED.ANY", level)

# STLB (2nd level TLB) data load speculative misses per kilo instruction (misses of any page-size that complete the page walk)
def Load_STLB_MPKI(self, EV, level):
    return 1000 * EV("DTLB_LOAD_MISSES.WALK_COMPLETED", level) / EV("INST_RETIRED.ANY", level)

# STLB (2nd level TLB) data store speculative misses per kilo instruction (misses of any page-size that complete the page walk)
def Store_STLB_MPKI(self, EV, level):
    return 1000 * EV("DTLB_STORE_MISSES.WALK_COMPLETED", level) / EV("INST_RETIRED.ANY", level)

# This metric represents fraction of cycles the CPU retirement was stalled likely due to STLB misses by demand loads
def Load_STLB_Miss_Ret(self, EV, level):
    val = EV("MEM_INST_RETIRED.STLB_MISS_LOADS", level) * EV("MEM_INST_RETIRED.STLB_MISS_LOADS", 999) / CLKS(self, EV, level)
    self.thresh = (val > 0.05)
    return val

# This metric represents fraction of cycles the CPU retirement was stalled likely due to STLB misses by demand stores
def Store_STLB_Miss_Ret(self, EV, level):
    val = EV("MEM_INST_RETIRED.STLB_MISS_STORES", level) * EV("MEM_INST_RETIRED.STLB_MISS_STORES", 999) / CLKS(self, EV, level)
    self.thresh = (val > 0.05)
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

# Average per-core data access bandwidth to the L3 cache [GB / sec]
def L3_Cache_Access_BW_2T(self, EV, level):
    return L3_Cache_Access_BW(self, EV, level)

# Rate of L2 HW prefetched lines that were not used by demand accesses
def Useless_HWPF(self, EV, level):
    val = EV("L2_LINES_OUT.USELESS_HWPF", level) / (EV("L2_LINES_OUT.SILENT", level) + EV("L2_LINES_OUT.NON_SILENT", level))
    self.thresh = (val > 0.15)
    return val

# Average Latency for L2 cache miss demand Loads
def Load_L2_Miss_Latency(self, EV, level):
    return EV("OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD", level) / EV("OFFCORE_REQUESTS.DEMAND_DATA_RD", level)

# Average Latency for L3 cache miss demand Loads
def Load_L3_Miss_Latency(self, EV, level):
    return EV("OFFCORE_REQUESTS_OUTSTANDING.L3_MISS_DEMAND_DATA_RD", level) / EV("OFFCORE_REQUESTS.L3_MISS_DEMAND_DATA_RD", level)

# Average Parallel L2 cache miss demand Loads
def Load_L2_MLP(self, EV, level):
    return EV("OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD", level) / EV("OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD:c1", level)

# Average Parallel L2 cache miss data reads
def Data_L2_MLP(self, EV, level):
    return EV("OFFCORE_REQUESTS_OUTSTANDING.DATA_RD", level) / EV("OFFCORE_REQUESTS_OUTSTANDING.CYCLES_WITH_DATA_RD", level)

# Un-cacheable retired load per kilo instruction
def UC_Load_PKI(self, EV, level):
    return 1000 * EV("MEM_LOAD_MISC_RETIRED.UC", level) / EV("INST_RETIRED.ANY", level)

# "Bus lock" per kilo instruction
def Bus_Lock_PKI(self, EV, level):
    return 1000 * EV("SQ_MISC.BUS_LOCK", level) / EV("INST_RETIRED.ANY", level)

# Average CPU Utilization (percentage)
def CPU_Utilization(self, EV, level):
    return CPUs_Utilized(self, EV, level) / Num_CPUs(self, EV, level)

# Average number of utilized CPUs
def CPUs_Utilized(self, EV, level):
    return EV("CPU_CLK_UNHALTED.REF_TSC", level) / EV("msr/tsc/", 0)

# Measured Average Core Frequency for unhalted processors [GHz]
def Core_Frequency(self, EV, level):
    return Turbo_Utilization(self, EV, level) * EV("msr/tsc/", 0) / OneBillion / Time(self, EV, level)

# Giga Floating Point Operations Per Second. Aggregate across all supported options of: FP precisions, scalar and vector instructions, vector-width
def GFLOPs(self, EV, level):
    return (FLOP_Count(self, EV, level) / OneBillion) / Time(self, EV, level)

# Average Frequency Utilization relative nominal frequency
def Turbo_Utilization(self, EV, level):
    return CLKS(self, EV, level) / EV("CPU_CLK_UNHALTED.REF_TSC", level)

# Fraction of cycles where both hardware Logical Processors were active
def SMT_2T_Utilization(self, EV, level):
    return 1 - EV("CPU_CLK_UNHALTED.ONE_THREAD_ACTIVE", level) / EV("CPU_CLK_UNHALTED.REF_DISTRIBUTED", level) if smt_enabled else 0

# Fraction of cycles spent in the Operating System (OS) Kernel mode
def Kernel_Utilization(self, EV, level):
    val = EV("CPU_CLK_UNHALTED.THREAD_P:SUP", level) / EV("CPU_CLK_UNHALTED.THREAD", level)
    self.thresh = (val > 0.05)
    return val

# Cycles Per Instruction for the Operating System (OS) Kernel mode
def Kernel_CPI(self, EV, level):
    return EV("CPU_CLK_UNHALTED.THREAD_P:SUP", level) / EV("INST_RETIRED.ANY_P:SUP", level)

# Fraction of cycles the processor is waiting yet unhalted; covering legacy PAUSE instruction, as well as C0.1 / C0.2 power-performance optimized states. Sample code of TPAUSE: https://github.com/torvalds/linux/blob/master/arch/x86/lib/delay.c#L105. If running on Linux, please check the power control interface: https://github.com/torvalds/linux/blob/master/arch/x86/kernel/cpu/umwait.c and https://github.com/torvalds/linux/blob/master/Documentation/ABI/testing/sysfs-devices-system-cpu#L587
def C0_Wait(self, EV, level):
    val = EV("CPU_CLK_UNHALTED.C0_WAIT", level) / CLKS(self, EV, level)
    self.thresh = (val > 0.05)
    return val

# Average external Memory Bandwidth Use for reads and writes [GB / sec]
def DRAM_BW_Use(self, EV, level):
    return 64 *(EV("UNC_HAC_ARB_TRK_REQUESTS.ALL", level) + EV("UNC_HAC_ARB_COH_TRK_REQUESTS.ALL", level)) / OneBillion / Time(self, EV, level)

# Average number of parallel data read requests to external memory. Accounts for demand loads and L1/L2 prefetches
def MEM_Parallel_Reads(self, EV, level):
    return EV("UNC_ARB_DAT_OCCUPANCY.RD", level) / EV("UNC_ARB_DAT_OCCUPANCY.RD:c1", level)

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
    sample = ['FRONTEND_RETIRED.LATENCY_GE_4:pp']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvFB', 'BvIO', 'TmaL1', 'PGO'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = (EV("PERF_METRICS.FRONTEND_BOUND", 1) / EV("TOPDOWN.SLOTS", 1)) / PERF_METRICS_SUM(self, EV, 1) - EV("INT_MISC.UOP_DROPPING", 1) / SLOTS(self, EV, 1) if topdown_use_fixed else(EV("IDQ_BUBBLES.CORE", 1) - EV("INT_MISC.UOP_DROPPING", 1)) / SLOTS(self, EV, 1)
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
    sample = ['FRONTEND_RETIRED.LATENCY_GE_16:pp', 'FRONTEND_RETIRED.LATENCY_GE_8:pp']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['Frontend', 'TmaL2'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = ((EV("PERF_METRICS.FETCH_LATENCY", 2) / EV("TOPDOWN.SLOTS", 2)) / PERF_METRICS_SUM(self, EV, 2) - EV("INT_MISC.UOP_DROPPING", 2) / SLOTS(self, EV, 2)) if topdown_use_fixed else(EV("IDQ_BUBBLES.CYCLES_0_UOPS_DELIV.CORE", 2) * Pipeline_Width - EV("INT_MISC.UOP_DROPPING", 2)) / SLOTS(self, EV, 2)
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
    sample = ['FRONTEND_RETIRED.L2_MISS:pp', 'FRONTEND_RETIRED.L1I_MISS:pp']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BigFootprint', 'BvBC', 'FetchLat', 'IcMiss'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("ICACHE_DATA.STALLS", 3) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "ICache_Misses zero division")
        return self.val
    desc = """
This metric represents fraction of cycles the CPU was
stalled due to instruction cache misses.. Using compiler's
Profile-Guided Optimization (PGO) can reduce i-cache misses
through improved hot code layout."""


class Code_L2_Hit:
    name = "Code_L2_Hit"
    domain = "Clocks_Retired"
    area = "FE"
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['IcMiss', 'FetchLat', 'Offcore'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = max(0 , EV("FRONTEND_RETIRED.L1I_MISS", 4) * EV("FRONTEND_RETIRED.L1I_MISS", 999) / CLKS(self, EV, 4) - self.Code_L2_Miss.compute(EV))
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Code_L2_Hit zero division")
        return self.val
    desc = """
This metric estimates fraction of cycles the CPU was stalled
due to instruction cache misses that hit in the L2 cache."""


class Code_L2_Miss:
    name = "Code_L2_Miss"
    domain = "Clocks_Retired"
    area = "FE"
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['IcMiss', 'FetchLat', 'Offcore'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("FRONTEND_RETIRED.L2_MISS", 4) * EV("FRONTEND_RETIRED.L2_MISS", 999) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Code_L2_Miss zero division")
        return self.val
    desc = """
This metric estimates fraction of cycles the CPU was stalled
due to instruction cache misses that miss in the L2 cache."""


class ITLB_Misses:
    name = "ITLB_Misses"
    domain = "Clocks"
    area = "FE"
    level = 3
    htoff = False
    sample = ['FRONTEND_RETIRED.STLB_MISS:pp', 'FRONTEND_RETIRED.ITLB_MISS:pp']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BigFootprint', 'BvBC', 'FetchLat', 'MemoryTLB'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("ICACHE_TAG.STALLS", 3) / CLKS(self, EV, 3)
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


class Code_STLB_Hit:
    name = "Code_STLB_Hit"
    domain = "Clocks_Retired"
    area = "FE"
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['FetchLat', 'MemoryTLB'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = max(0 , EV("FRONTEND_RETIRED.ITLB_MISS", 4) * EV("FRONTEND_RETIRED.ITLB_MISS", 999) / CLKS(self, EV, 4) - self.Code_STLB_Miss.compute(EV))
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Code_STLB_Hit zero division")
        return self.val
    desc = """
This metric roughly estimates the fraction of cycles where
the (first level) ITLB was missed by instructions fetches,
that later on hit in second-level TLB (STLB)"""


class Code_STLB_Miss:
    name = "Code_STLB_Miss"
    domain = "Clocks_Retired"
    area = "FE"
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['FetchLat', 'MemoryTLB'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = EV("FRONTEND_RETIRED.STLB_MISS", 4) * EV("FRONTEND_RETIRED.STLB_MISS", 999) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Code_STLB_Miss zero division")
        return self.val
    desc = """
This metric estimates the fraction of cycles where the
Second-level TLB (STLB) was missed by instruction fetches,
performing a hardware page walk"""


class Code_STLB_Miss_4K:
    name = "Code_STLB_Miss_4K"
    domain = "Clocks_Estimated"
    area = "FE"
    level = 5
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['FetchLat', 'MemoryTLB'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("ITLB_MISSES.WALK_ACTIVE", 5) / CLKS(self, EV, 5) * EV("ITLB_MISSES.WALK_COMPLETED_4K", 5) / (EV("ITLB_MISSES.WALK_COMPLETED_4K", 5) + EV("ITLB_MISSES.WALK_COMPLETED_2M_4M", 5))
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Code_STLB_Miss_4K zero division")
        return self.val
    desc = """
This metric estimates the fraction of cycles to walk the
memory paging structures to cache translation of 4 KB pages
for (instruction) code accesses."""


class Code_STLB_Miss_2M:
    name = "Code_STLB_Miss_2M"
    domain = "Clocks_Estimated"
    area = "FE"
    level = 5
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['FetchLat', 'MemoryTLB'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("ITLB_MISSES.WALK_ACTIVE", 5) / CLKS(self, EV, 5) * EV("ITLB_MISSES.WALK_COMPLETED_2M_4M", 5) / (EV("ITLB_MISSES.WALK_COMPLETED_4K", 5) + EV("ITLB_MISSES.WALK_COMPLETED_2M_4M", 5))
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Code_STLB_Miss_2M zero division")
        return self.val
    desc = """
This metric estimates the fraction of cycles to walk the
memory paging structures to cache translation of 2 or 4 MB
pages for (instruction) code accesses."""


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
            self.val = EV("INT_MISC.CLEAR_RESTEER_CYCLES", 3) / CLKS(self, EV, 3) + self.Unknown_Branches.compute(EV)
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


class Mispredicts_Resteers:
    name = "Mispredicts_Resteers"
    domain = "Clocks"
    area = "FE"
    level = 4
    htoff = False
    sample = ['INT_MISC.CLEAR_RESTEER_CYCLES']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BadSpec', 'BrMispredicts', 'BvMP'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = Mispred_Clears_Fraction(self, EV, 4) * EV("INT_MISC.CLEAR_RESTEER_CYCLES", 4) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Mispredicts_Resteers zero division")
        return self.val
    desc = """
This metric represents fraction of cycles the CPU was
stalled due to Branch Resteers as a result of Branch
Misprediction at execution stage."""


class Clears_Resteers:
    name = "Clears_Resteers"
    domain = "Clocks"
    area = "FE"
    level = 4
    htoff = False
    sample = ['INT_MISC.CLEAR_RESTEER_CYCLES']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BadSpec', 'MachineClears'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = (1 - Mispred_Clears_Fraction(self, EV, 4)) * EV("INT_MISC.CLEAR_RESTEER_CYCLES", 4) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Clears_Resteers zero division")
        return self.val
    desc = """
This metric represents fraction of cycles the CPU was
stalled due to Branch Resteers as a result of Machine
Clears."""


class Unknown_Branches:
    name = "Unknown_Branches"
    domain = "Clocks"
    area = "FE"
    level = 4
    htoff = False
    sample = ['FRONTEND_RETIRED.UNKNOWN_BRANCH']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BigFootprint', 'BvBC', 'FetchLat'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("INT_MISC.UNKNOWN_BRANCH_CYCLES", 4) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Unknown_Branches zero division")
        return self.val
    desc = """
This metric represents fraction of cycles the CPU was
stalled due to new branch address clears. These are fetched
branches the Branch Prediction Unit was unable to recognize
(e.g. first time the branch is fetched or hitting BTB
capacity limit) hence called Unknown Branches"""


class MS_Switches:
    name = "MS_Switches"
    domain = "Clocks_Estimated"
    area = "FE"
    level = 3
    htoff = False
    sample = ['FRONTEND_RETIRED.MS_FLOWS']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['FetchLat', 'MicroSeq'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = MS_Switches_Cost * EV("UOPS_RETIRED.MS:c1:e1", 3) / Retire_Fraction(self, EV, 3) / CLKS(self, EV, 3)
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
            self.val = EV("DECODE.LCP", 3) / CLKS(self, EV, 3)
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
    sample = ['FRONTEND_RETIRED.DSB_MISS:pp']
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
    sample = ['FRONTEND_RETIRED.LATENCY_GE_2_BUBBLES_GE_1', 'FRONTEND_RETIRED.LATENCY_GE_1', 'FRONTEND_RETIRED.LATENCY_GE_2']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['FetchBW', 'Frontend', 'TmaL2'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = max(0 , self.Frontend_Bound.compute(EV) - self.Fetch_Latency.compute(EV))
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
    sample = ['FRONTEND_RETIRED.ANY_DSB_MISS']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['DSBmiss', 'FetchBW'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = (EV("IDQ.MITE_CYCLES_ANY", 3) - EV("IDQ.MITE_CYCLES_OK", 3)) / CORE_CLKS(self, EV, 3) / 2
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


class Decoder0_Alone:
    name = "Decoder0_Alone"
    domain = "Slots_Estimated"
    area = "FE"
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['DSBmiss', 'FetchBW'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = (EV("INST_DECODED.DECODERS:c1", 4) - EV("INST_DECODED.DECODERS:c2", 4)) / CORE_CLKS(self, EV, 4) / 2
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Decoder0_Alone zero division")
        return self.val
    desc = """
This metric represents fraction of cycles where decoder-0
was the only active decoder"""


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
            self.val = (EV("IDQ.DSB_CYCLES_ANY", 3) - EV("IDQ.DSB_CYCLES_OK", 3)) / CORE_CLKS(self, EV, 3) / 2
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


class LSD:
    name = "LSD"
    domain = "Slots_Estimated"
    area = "FE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['FetchBW', 'LSD'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = (EV("LSD.CYCLES_ACTIVE", 3) - EV("LSD.CYCLES_OK", 3)) / CORE_CLKS(self, EV, 3) / 2
            self.thresh = (self.val > 0.15) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "LSD zero division")
        return self.val
    desc = """
This metric represents Core fraction of cycles in which CPU
was likely limited due to LSD (Loop Stream Detector) unit.
LSD typically does well sustaining Uop supply. However; in
some rare cases; optimal uop-delivery could not be reached
for small loops whose size (in terms of number of uops) does
not suit well the LSD structure."""


class MS:
    name = "MS"
    domain = "Slots_Estimated"
    area = "FE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['MicroSeq'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = max(EV("IDQ.MS_CYCLES_ANY", 3) , EV("UOPS_RETIRED.MS:c1", 3) / Retire_Fraction(self, EV, 3)) / CORE_CLKS(self, EV, 3) / 2
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "MS zero division")
        return self.val
    desc = """
This metric represents Core fraction of cycles in which CPU
was likely limited due to the Microcode Sequencer (MS) unit
- see Microcode_Sequencer node for details."""


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
            self.val = max(1 -(self.Frontend_Bound.compute(EV) + self.Backend_Bound.compute(EV) + self.Retiring.compute(EV)) , 0 )
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
    sample = ['TOPDOWN.BR_MISPREDICT_SLOTS']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BadSpec', 'BrMispredicts', 'BvMP', 'TmaL2'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = (EV("PERF_METRICS.BRANCH_MISPREDICTS", 2) / EV("TOPDOWN.SLOTS", 2)) / PERF_METRICS_SUM(self, EV, 2) if topdown_use_fixed else EV("TOPDOWN.BR_MISPREDICT_SLOTS", 2) / SLOTS(self, EV, 2)
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


class Cond_NT_Mispredicts:
    name = "Cond_NT_Mispredicts"
    domain = "Clocks_Retired"
    area = "BAD"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BrMispredicts'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("BR_MISP_RETIRED.COND_NTAKEN_COST", 3) * EV("BR_MISP_RETIRED.COND_NTAKEN_COST", 999) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Cond_NT_Mispredicts zero division")
        return self.val
    desc = """
This metric represents fraction of cycles the CPU was
stalled due to retired misprediction by non-taken
conditional branches."""


class Cond_TK_Mispredicts:
    name = "Cond_TK_Mispredicts"
    domain = "Clocks_Retired"
    area = "BAD"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BrMispredicts'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("BR_MISP_RETIRED.COND_TAKEN_COST", 3) * EV("BR_MISP_RETIRED.COND_TAKEN_COST", 999) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Cond_TK_Mispredicts zero division")
        return self.val
    desc = """
This metric represents fraction of cycles the CPU was
stalled due to misprediction by taken conditional branches."""


class Ind_Call_Mispredicts:
    name = "Ind_Call_Mispredicts"
    domain = "Clocks_Retired"
    area = "BAD"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BrMispredicts'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("BR_MISP_RETIRED.INDIRECT_CALL_COST", 3) * EV("BR_MISP_RETIRED.INDIRECT_CALL_COST", 999) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Ind_Call_Mispredicts zero division")
        return self.val
    desc = """
This metric represents fraction of cycles the CPU was
stalled due to retired misprediction by indirect CALL
instructions."""


class Ind_Jump_Mispredicts:
    name = "Ind_Jump_Mispredicts"
    domain = "Clocks_Retired"
    area = "BAD"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BrMispredicts'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = max((EV("BR_MISP_RETIRED.INDIRECT_COST", 3) * EV("BR_MISP_RETIRED.INDIRECT_COST", 999) - EV("BR_MISP_RETIRED.INDIRECT_CALL_COST", 3) * EV("BR_MISP_RETIRED.INDIRECT_CALL_COST", 999)) / CLKS(self, EV, 3) , 0 )
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Ind_Jump_Mispredicts zero division")
        return self.val
    desc = """
This metric represents fraction of cycles the CPU was
stalled due to retired misprediction by indirect JMP
instructions."""


class Ret_Mispredicts:
    name = "Ret_Mispredicts"
    domain = "Clocks_Retired"
    area = "BAD"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BrMispredicts'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("BR_MISP_RETIRED.RET_COST", 3) * EV("BR_MISP_RETIRED.RET_COST", 999) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Ret_Mispredicts zero division")
        return self.val
    desc = """
This metric represents fraction of cycles the CPU was
stalled due to retired misprediction by (indirect) RET
instructions."""


class Other_Mispredicts:
    name = "Other_Mispredicts"
    domain = "Slots"
    area = "BAD"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvIO', 'BrMispredicts'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = max(self.Branch_Mispredicts.compute(EV) * (1 - EV("BR_MISP_RETIRED.ALL_BRANCHES", 3) / (EV("INT_MISC.CLEARS_COUNT", 3) - EV("MACHINE_CLEARS.COUNT", 3))) , 0.0001 )
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Other_Mispredicts zero division")
        return self.val
    desc = """
This metric estimates fraction of slots the CPU was stalled
due to other cases of misprediction (non-retired x86
branches or other types)."""


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
            self.val = max(0 , self.Bad_Speculation.compute(EV) - self.Branch_Mispredicts.compute(EV))
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


class Other_Nukes:
    name = "Other_Nukes"
    domain = "Slots"
    area = "BAD"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvIO', 'Machine_Clears'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = max(self.Machine_Clears.compute(EV) * (1 - EV("MACHINE_CLEARS.MEMORY_ORDERING", 3) / EV("MACHINE_CLEARS.COUNT", 3)) , 0.0001 )
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Other_Nukes zero division")
        return self.val
    desc = """
This metric represents fraction of slots the CPU has wasted
due to Nukes (Machine Clears) not related to memory
ordering."""


class Backend_Bound:
    name = "Backend_Bound"
    domain = "Slots"
    area = "BE"
    level = 1
    htoff = False
    sample = ['TOPDOWN.BACKEND_BOUND_SLOTS']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvOB', 'TmaL1'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = (EV("PERF_METRICS.BACKEND_BOUND", 1) / EV("TOPDOWN.SLOTS", 1)) / PERF_METRICS_SUM(self, EV, 1) if topdown_use_fixed else EV("TOPDOWN.BACKEND_BOUND_SLOTS", 1) / SLOTS(self, EV, 1)
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
            self.val = (EV("PERF_METRICS.MEMORY_BOUND", 2) / EV("TOPDOWN.SLOTS", 2)) / PERF_METRICS_SUM(self, EV, 2) if topdown_use_fixed else EV("TOPDOWN.MEMORY_BOUND_SLOTS", 2) / SLOTS(self, EV, 2)
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
    sample = ['MEM_LOAD_RETIRED.L1_HIT']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['CacheHits', 'MemoryBound', 'TmaL3mem'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = max((EV("EXE_ACTIVITY.BOUND_ON_LOADS", 3) - EV("MEMORY_ACTIVITY.STALLS_L1D_MISS", 3)) / CLKS(self, EV, 3) , 0 )
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
    sample = ['MEM_INST_RETIRED.STLB_MISS_LOADS:pp']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvMT', 'MemoryTLB'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = EV("MEM_INST_RETIRED.STLB_HIT_LOADS", 4) * min(EV("MEM_INST_RETIRED.STLB_HIT_LOADS", 999) , Mem_STLB_Hit_Cost) / CLKS(self, EV, 4) + self.Load_STLB_Miss.compute(EV)
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


class Load_STLB_Hit:
    name = "Load_STLB_Hit"
    domain = "Clocks_Estimated"
    area = "BE/Mem"
    level = 5
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['MemoryTLB'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = max(0 , self.DTLB_Load.compute(EV) - self.Load_STLB_Miss.compute(EV))
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Load_STLB_Hit zero division")
        return self.val
    desc = """
This metric roughly estimates the fraction of cycles where
the (first level) DTLB was missed by load accesses, that
later on hit in second-level TLB (STLB)"""


class Load_STLB_Miss:
    name = "Load_STLB_Miss"
    domain = "Clocks_Calculated"
    area = "BE/Mem"
    level = 5
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['MemoryTLB'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = EV("DTLB_LOAD_MISSES.WALK_ACTIVE", 5) / CLKS(self, EV, 5)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Load_STLB_Miss zero division")
        return self.val
    desc = """
This metric estimates the fraction of cycles where the
Second-level TLB (STLB) was missed by load accesses,
performing a hardware page walk"""


class Load_STLB_Miss_4K:
    name = "Load_STLB_Miss_4K"
    domain = "Clocks_Estimated"
    area = "BE/Mem"
    level = 6
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['MemoryTLB'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = self.Load_STLB_Miss.compute(EV) * EV("DTLB_LOAD_MISSES.WALK_COMPLETED_4K", 6) / (EV("DTLB_LOAD_MISSES.WALK_COMPLETED_4K", 6) + EV("DTLB_LOAD_MISSES.WALK_COMPLETED_2M_4M", 6) + EV("DTLB_LOAD_MISSES.WALK_COMPLETED_1G", 6))
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Load_STLB_Miss_4K zero division")
        return self.val
    desc = """
This metric estimates the fraction of cycles to walk the
memory paging structures to cache translation of 4 KB pages
for data load accesses."""


class Load_STLB_Miss_2M:
    name = "Load_STLB_Miss_2M"
    domain = "Clocks_Estimated"
    area = "BE/Mem"
    level = 6
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['MemoryTLB'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = self.Load_STLB_Miss.compute(EV) * EV("DTLB_LOAD_MISSES.WALK_COMPLETED_2M_4M", 6) / (EV("DTLB_LOAD_MISSES.WALK_COMPLETED_4K", 6) + EV("DTLB_LOAD_MISSES.WALK_COMPLETED_2M_4M", 6) + EV("DTLB_LOAD_MISSES.WALK_COMPLETED_1G", 6))
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Load_STLB_Miss_2M zero division")
        return self.val
    desc = """
This metric estimates the fraction of cycles to walk the
memory paging structures to cache translation of 2 or 4 MB
pages for data load accesses."""


class Load_STLB_Miss_1G:
    name = "Load_STLB_Miss_1G"
    domain = "Clocks_Estimated"
    area = "BE/Mem"
    level = 6
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['MemoryTLB'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = self.Load_STLB_Miss.compute(EV) * EV("DTLB_LOAD_MISSES.WALK_COMPLETED_1G", 6) / (EV("DTLB_LOAD_MISSES.WALK_COMPLETED_4K", 6) + EV("DTLB_LOAD_MISSES.WALK_COMPLETED_2M_4M", 6) + EV("DTLB_LOAD_MISSES.WALK_COMPLETED_1G", 6))
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Load_STLB_Miss_1G zero division")
        return self.val
    desc = """
This metric estimates the fraction of cycles to walk the
memory paging structures to cache translation of 1 GB pages
for data load accesses."""


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


class L1_Latency_Dependency:
    name = "L1_Latency_Dependency"
    domain = "Clocks_Estimated"
    area = "BE/Mem"
    level = 4
    htoff = False
    sample = ['MEM_LOAD_RETIRED.L1_HIT']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvML', 'MemoryLat'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = min(2 *(EV("MEM_INST_RETIRED.ALL_LOADS", 4) - EV("MEM_LOAD_RETIRED.FB_HIT", 4) - EV("MEM_LOAD_RETIRED.L1_MISS", 4)) * Dependent_Loads_Weight(self, EV, 4) / 100 , max(EV("CYCLE_ACTIVITY.CYCLES_MEM_ANY", 4) - EV("MEMORY_ACTIVITY.CYCLES_L1D_MISS", 4) , 0)) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "L1_Latency_Dependency zero division")
        return self.val
    desc = """
This metric roughly estimates fraction of cycles with demand
load accesses that hit the L1D cache. The short latency of
the L1D cache may be exposed in pointer-chasing memory
access patterns as an example."""


class Lock_Latency:
    name = "Lock_Latency"
    domain = "Clocks"
    area = "BE/Mem"
    level = 4
    htoff = False
    sample = ['MEM_INST_RETIRED.LOCK_LOADS']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['LockCont', 'Offcore'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = EV("MEM_INST_RETIRED.LOCK_LOADS", 4) * EV("MEM_INST_RETIRED.LOCK_LOADS", 999) / CLKS(self, EV, 4)
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
    sample = ['MEM_INST_RETIRED.SPLIT_LOADS:pp']
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = EV("MEM_INST_RETIRED.SPLIT_LOADS", 4) * min(EV("MEM_INST_RETIRED.SPLIT_LOADS", 999) , Load_Miss_Real_Latency(self, EV, 4)) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.3)
        except ZeroDivisionError:
            handle_error(self, "Split_Loads zero division")
        return self.val
    desc = """
This metric estimates fraction of cycles handling memory
load split accesses - load that cross 64-byte cache line
boundary. . Consider aligning data or hot structure fields.
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
            self.val = EV("L1D_PEND_MISS.FB_FULL", 4) / CLKS(self, EV, 4)
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
    sample = ['MEM_LOAD_RETIRED.L2_HIT']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvML', 'CacheHits', 'MemoryBound', 'TmaL3mem'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = (EV("MEMORY_ACTIVITY.STALLS_L1D_MISS", 3) - EV("MEMORY_ACTIVITY.STALLS_L2_MISS", 3)) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "L2_Bound zero division")
        return self.val
    desc = """
This metric estimates how often the CPU was stalled due to
L2 cache accesses by loads.  Avoiding cache misses (i.e. L1
misses/L2 hits) can improve the latency and increase
performance."""


class L2_Hit_Latency:
    name = "L2_Hit_Latency"
    domain = "Clocks_Retired"
    area = "BE/Mem"
    level = 4
    htoff = False
    sample = ['MEM_LOAD_RETIRED.L2_HIT']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['MemoryLat'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("MEM_LOAD_RETIRED.L2_HIT", 4) * min(EV("MEM_LOAD_RETIRED.L2_HIT", 999) , Mem_L2_Hit_Cost(self, EV, 4)) * FB_Factor(self, EV, 4) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "L2_Hit_Latency zero division")
        return self.val
    desc = """
This metric represents fraction of cycles with demand load
accesses that hit the L2 cache under unloaded scenarios
(possibly L2 latency limited).  Avoiding L1 cache misses
(i.e. L1 misses/L2 hits) will improve the latency."""


class L3_Bound:
    name = "L3_Bound"
    domain = "Stalls"
    area = "BE/Mem"
    level = 3
    htoff = False
    sample = ['MEM_LOAD_RETIRED.L3_HIT:pp']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['CacheHits', 'MemoryBound', 'TmaL3mem'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = (EV("MEMORY_ACTIVITY.STALLS_L2_MISS", 3) - EV("MEMORY_ACTIVITY.STALLS_L3_MISS", 3)) / CLKS(self, EV, 3)
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
    sample = ['MEM_LOAD_L3_HIT_RETIRED.XSNP_FWD', 'MEM_LOAD_L3_HIT_RETIRED.XSNP_MISS']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvMS', 'DataSharing', 'LockCont', 'Offcore', 'Snoop'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = (EV("MEM_LOAD_L3_HIT_RETIRED.XSNP_MISS", 4) * min(EV("MEM_LOAD_L3_HIT_RETIRED.XSNP_MISS", 999) , Mem_XSNP_Hit_Cost(self, EV, 4) - Mem_L2_Hit_Cost(self, EV, 4)) + EV("MEM_LOAD_L3_HIT_RETIRED.XSNP_FWD", 4) * min(EV("MEM_LOAD_L3_HIT_RETIRED.XSNP_FWD", 999) , Mem_XSNP_HitM_Cost(self, EV, 4) - Mem_L2_Hit_Cost(self, EV, 4)) * True_XSNP_HitM_Fraction(self, EV, 4)) * FB_Factor(self, EV, 4) / CLKS(self, EV, 4)
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
    sample = ['MEM_LOAD_L3_HIT_RETIRED.XSNP_NO_FWD']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvMS', 'Offcore', 'Snoop'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = (EV("MEM_LOAD_L3_HIT_RETIRED.XSNP_NO_FWD", 4) * min(EV("MEM_LOAD_L3_HIT_RETIRED.XSNP_NO_FWD", 999) , Mem_XSNP_Hit_Cost(self, EV, 4) - Mem_L2_Hit_Cost(self, EV, 4)) + EV("MEM_LOAD_L3_HIT_RETIRED.XSNP_FWD", 4) * min(EV("MEM_LOAD_L3_HIT_RETIRED.XSNP_FWD", 999) , Mem_XSNP_Hit_Cost(self, EV, 4) - Mem_L2_Hit_Cost(self, EV, 4)) * (1 - True_XSNP_HitM_Fraction(self, EV, 4))) * FB_Factor(self, EV, 4) / CLKS(self, EV, 4)
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
    sample = ['MEM_LOAD_RETIRED.L3_HIT:pp']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvML', 'MemoryLat'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = EV("MEM_LOAD_RETIRED.L3_HIT", 4) * min(EV("MEM_LOAD_RETIRED.L3_HIT", 999) , Mem_XSNP_None_Cost(self, EV, 4) - Mem_L2_Hit_Cost(self, EV, 4)) * FB_Factor(self, EV, 4) / CLKS(self, EV, 4)
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
            self.val = (EV("XQ.FULL_CYCLES", 4) + EV("L1D_PEND_MISS.L2_STALLS", 4)) / CLKS(self, EV, 4)
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
    sample = ['MEM_LOAD_RETIRED.L3_MISS']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['MemoryBound', 'TmaL3mem'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = MEM_Bound_Ratio(self, EV, 3)
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
    sample = ['MEM_INST_RETIRED.ALL_STORES:pp']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['MemoryBound', 'TmaL3mem'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("EXE_ACTIVITY.BOUND_ON_STORES", 3) / CLKS(self, EV, 3)
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
    sample = ['OCR.DEMAND_RFO.L3_HIT.SNOOP_HITM']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvMS', 'DataSharing', 'LockCont', 'Offcore', 'Snoop'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = Mem_XSNP_HitM_Cost(self, EV, 4) * EV("OCR.DEMAND_RFO.L3_HIT.SNOOP_HITM", 4) / CLKS(self, EV, 4)
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
    sample = ['MEM_INST_RETIRED.SPLIT_STORES:pp']
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("MEM_INST_RETIRED.SPLIT_STORES", 4) * min(EV("MEM_INST_RETIRED.SPLIT_STORES", 999) , 1) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.2) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Split_Stores zero division")
        return self.val
    desc = """
This metric represents rate of split store accesses.
Consider aligning your data to the 64-byte cache line
granularity."""


class Streaming_Stores:
    name = "Streaming_Stores"
    domain = "Clocks_Estimated"
    area = "BE/Mem"
    level = 4
    htoff = False
    sample = ['OCR.STREAMING_WR.ANY_RESPONSE']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['MemoryBW', 'Offcore'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = 9 * EV("OCR.STREAMING_WR.ANY_RESPONSE", 4) / CLKS(self, EV, 4) if DS else 0
            EV("OCR.STREAMING_WR.ANY_RESPONSE", 4)
            self.thresh = (self.val > 0.2) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Streaming_Stores zero division")
        return self.val
    desc = """
This metric estimates how often CPU was stalled  due to
Streaming store memory accesses; Streaming store optimize
out a read request required by RFO stores. Even though store
accesses do not typically stall out-of-order CPUs; there are
few cases where stores can lead to actual stalls. This
metric will be flagged should Streaming stores be a
bottleneck."""


class DTLB_Store:
    name = "DTLB_Store"
    domain = "Clocks_Estimated"
    area = "BE/Mem"
    level = 4
    htoff = False
    sample = ['MEM_INST_RETIRED.STLB_MISS_STORES:pp']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvMT', 'MemoryTLB'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = EV("MEM_INST_RETIRED.STLB_HIT_STORES", 4) * min(EV("MEM_INST_RETIRED.STLB_HIT_STORES", 999) , Mem_STLB_Hit_Cost) / CLKS(self, EV, 4) + self.Store_STLB_Miss.compute(EV)
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


class Store_STLB_Hit:
    name = "Store_STLB_Hit"
    domain = "Clocks_Estimated"
    area = "BE/Mem"
    level = 5
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['MemoryTLB'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = max(0 , self.DTLB_Store.compute(EV) - self.Store_STLB_Miss.compute(EV))
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Store_STLB_Hit zero division")
        return self.val
    desc = """
This metric roughly estimates the fraction of cycles where
the TLB was missed by store accesses, hitting in the second-
level TLB (STLB)"""


class Store_STLB_Miss:
    name = "Store_STLB_Miss"
    domain = "Clocks_Calculated"
    area = "BE/Mem"
    level = 5
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['MemoryTLB'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = EV("DTLB_STORE_MISSES.WALK_ACTIVE", 5) / CORE_CLKS(self, EV, 5)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Store_STLB_Miss zero division")
        return self.val
    desc = """
This metric estimates the fraction of cycles where the STLB
was missed by store accesses, performing a hardware page
walk"""


class Store_STLB_Miss_4K:
    name = "Store_STLB_Miss_4K"
    domain = "Clocks_Estimated"
    area = "BE/Mem"
    level = 6
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['MemoryTLB'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = self.Store_STLB_Miss.compute(EV) * EV("DTLB_STORE_MISSES.WALK_COMPLETED_4K", 6) / (EV("DTLB_STORE_MISSES.WALK_COMPLETED_4K", 6) + EV("DTLB_STORE_MISSES.WALK_COMPLETED_2M_4M", 6) + EV("DTLB_STORE_MISSES.WALK_COMPLETED_1G", 6))
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Store_STLB_Miss_4K zero division")
        return self.val
    desc = """
This metric estimates the fraction of cycles to walk the
memory paging structures to cache translation of 4 KB pages
for data store accesses."""


class Store_STLB_Miss_2M:
    name = "Store_STLB_Miss_2M"
    domain = "Clocks_Estimated"
    area = "BE/Mem"
    level = 6
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['MemoryTLB'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = self.Store_STLB_Miss.compute(EV) * EV("DTLB_STORE_MISSES.WALK_COMPLETED_2M_4M", 6) / (EV("DTLB_STORE_MISSES.WALK_COMPLETED_4K", 6) + EV("DTLB_STORE_MISSES.WALK_COMPLETED_2M_4M", 6) + EV("DTLB_STORE_MISSES.WALK_COMPLETED_1G", 6))
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Store_STLB_Miss_2M zero division")
        return self.val
    desc = """
This metric estimates the fraction of cycles to walk the
memory paging structures to cache translation of 2 or 4 MB
pages for data store accesses."""


class Store_STLB_Miss_1G:
    name = "Store_STLB_Miss_1G"
    domain = "Clocks_Estimated"
    area = "BE/Mem"
    level = 6
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['MemoryTLB'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = self.Store_STLB_Miss.compute(EV) * EV("DTLB_STORE_MISSES.WALK_COMPLETED_1G", 6) / (EV("DTLB_STORE_MISSES.WALK_COMPLETED_4K", 6) + EV("DTLB_STORE_MISSES.WALK_COMPLETED_2M_4M", 6) + EV("DTLB_STORE_MISSES.WALK_COMPLETED_1G", 6))
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Store_STLB_Miss_1G zero division")
        return self.val
    desc = """
This metric estimates the fraction of cycles to walk the
memory paging structures to cache translation of 1 GB pages
for data store accesses."""


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
            self.val = max(0 , self.Backend_Bound.compute(EV) - self.Memory_Bound.compute(EV))
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
    sample = ['ARITH.DIV_ACTIVE']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvCB'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = EV("ARITH.DIV_ACTIVE", 3) / CLKS(self, EV, 3)
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


class FP_Divider:
    name = "FP_Divider"
    domain = "Clocks"
    area = "BE/Core"
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("ARITH.FPDIV_ACTIVE", 4) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.2) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "FP_Divider zero division")
        return self.val
    desc = """
This metric represents fraction of cycles where the
Floating-Point Divider unit was active."""


class INT_Divider:
    name = "INT_Divider"
    domain = "Clocks"
    area = "BE/Core"
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = self.Divider.compute(EV) - self.FP_Divider.compute(EV)
            self.thresh = (self.val > 0.2) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "INT_Divider zero division")
        return self.val
    desc = """
This metric represents fraction of cycles where the Integer
Divider unit was active."""


class Serializing_Operation:
    name = "Serializing_Operation"
    domain = "Clocks"
    area = "BE/Core"
    level = 3
    htoff = False
    sample = ['RESOURCE_STALLS.SCOREBOARD']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvIO', 'PortsUtil'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("RESOURCE_STALLS.SCOREBOARD", 3) / CLKS(self, EV, 3) + self.C02_Wait.compute(EV)
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Serializing_Operation zero division")
        return self.val
    desc = """
This metric represents fraction of cycles the CPU issue-
pipeline was stalled due to serializing operations.
Instructions like CPUID; WRMSR or LFENCE serialize the out-
of-order execution which may limit performance."""


class Slow_Pause:
    name = "Slow_Pause"
    domain = "Clocks"
    area = "BE/Core"
    level = 4
    htoff = False
    sample = ['CPU_CLK_UNHALTED.PAUSE_INST']
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("CPU_CLK_UNHALTED.PAUSE", 4) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Slow_Pause zero division")
        return self.val
    desc = """
This metric represents fraction of cycles the CPU was
stalled due to PAUSE Instructions."""


class C01_Wait:
    name = "C01_Wait"
    domain = "Clocks"
    area = "BE/Core"
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['C0Wait'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("CPU_CLK_UNHALTED.C01", 4) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "C01_Wait zero division")
        return self.val
    desc = """
This metric represents fraction of cycles the CPU was
stalled due staying in C0.1 power-performance optimized
state (Faster wakeup time; Smaller power savings)."""


class C02_Wait:
    name = "C02_Wait"
    domain = "Clocks"
    area = "BE/Core"
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['C0Wait'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("CPU_CLK_UNHALTED.C02", 4) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "C02_Wait zero division")
        return self.val
    desc = """
This metric represents fraction of cycles the CPU was
stalled due staying in C0.2 power-performance optimized
state (Slower wakeup time; Larger power savings)."""


class Memory_Fence:
    name = "Memory_Fence"
    domain = "Clocks"
    area = "BE/Core"
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = 13 * EV("MISC2_RETIRED.LFENCE", 4) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Memory_Fence zero division")
        return self.val
    desc = """
This metric represents fraction of cycles the CPU was
stalled due to LFENCE Instructions."""


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
            self.val = Core_Bound_Cycles(self, EV, 3) / CLKS(self, EV, 3) if (EV("ARITH.DIV_ACTIVE", 3)<(EV("CYCLE_ACTIVITY.STALLS_TOTAL", 3) - EV("EXE_ACTIVITY.BOUND_ON_LOADS", 3))) else Few_Uops_Executed_Threshold(self, EV, 3) / CLKS(self, EV, 3)
            EV("CYCLE_ACTIVITY.STALLS_TOTAL", 3)
            EV("EXE_ACTIVITY.BOUND_ON_LOADS", 3)
            EV("ARITH.DIV_ACTIVE", 3)
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
            self.val = max(EV("EXE_ACTIVITY.EXE_BOUND_0_PORTS", 4) - EV("RESOURCE_STALLS.SCOREBOARD", 4) , 0) / CLKS(self, EV, 4)
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


class Mixing_Vectors:
    name = "Mixing_Vectors"
    domain = "Clocks"
    area = "BE/Core"
    level = 5
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = 160 * EV("ASSISTS.SSE_AVX_MIX", 5) / CLKS(self, EV, 5)
            self.thresh = (self.val > 0.05)
        except ZeroDivisionError:
            handle_error(self, "Mixing_Vectors zero division")
        return self.val
    desc = """
This metric estimates penalty in terms of percentage of
cycles. Usually a Mixing_Vectors over 5% is worth
investigating. Read more in Appendix B1 of the Optimizations
Guide for this topic."""


class Ports_Utilized_1:
    name = "Ports_Utilized_1"
    domain = "Clocks"
    area = "BE/Core"
    level = 4
    htoff = False
    sample = ['EXE_ACTIVITY.1_PORTS_UTIL']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['PortsUtil'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("EXE_ACTIVITY.1_PORTS_UTIL", 4) / CLKS(self, EV, 4)
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
    sample = ['EXE_ACTIVITY.2_PORTS_UTIL']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['PortsUtil'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("EXE_ACTIVITY.2_PORTS_UTIL", 4) / CLKS(self, EV, 4)
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
    sample = ['UOPS_EXECUTED.CYCLES_GE_3']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvCB', 'PortsUtil'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("UOPS_EXECUTED.CYCLES_GE_3", 4) / CLKS(self, EV, 4)
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
            self.val = (EV("UOPS_DISPATCHED.PORT_0", 5) + EV("UOPS_DISPATCHED.PORT_1", 5) + EV("UOPS_DISPATCHED.PORT_5_11", 5) + EV("UOPS_DISPATCHED.PORT_6", 5)) / (5 * CORE_CLKS(self, EV, 5))
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
    sample = ['UOPS_DISPATCHED.PORT_0']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['Compute'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("UOPS_DISPATCHED.PORT_0", 6) / CORE_CLKS(self, EV, 6)
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
    sample = ['UOPS_DISPATCHED.PORT_1']
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("UOPS_DISPATCHED.PORT_1", 6) / CORE_CLKS(self, EV, 6)
            self.thresh = (self.val > 0.6)
        except ZeroDivisionError:
            handle_error(self, "Port_1 zero division")
        return self.val
    desc = """
This metric represents Core fraction of cycles CPU
dispatched uops on execution port 1 (ALU)"""


class Port_6:
    name = "Port_6"
    domain = "Core_Clocks"
    area = "BE/Core"
    level = 6
    htoff = False
    sample = ['UOPS_DISPATCHED.PORT_1']
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("UOPS_DISPATCHED.PORT_6", 6) / CORE_CLKS(self, EV, 6)
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
    sample = ['UOPS_DISPATCHED.PORT_2_3_10']
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("UOPS_DISPATCHED.PORT_2_3_10", 5) / (3 * CORE_CLKS(self, EV, 5))
            self.thresh = (self.val > 0.6)
        except ZeroDivisionError:
            handle_error(self, "Load_Op_Utilization zero division")
        return self.val
    desc = """
This metric represents Core fraction of cycles CPU
dispatched uops on execution port for Load operations"""


class Store_Op_Utilization:
    name = "Store_Op_Utilization"
    domain = "Core_Execution"
    area = "BE/Core"
    level = 5
    htoff = False
    sample = ['UOPS_DISPATCHED.PORT_7_8']
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = (EV("UOPS_DISPATCHED.PORT_4_9", 5) + EV("UOPS_DISPATCHED.PORT_7_8", 5)) / (4 * CORE_CLKS(self, EV, 5))
            self.thresh = (self.val > 0.6)
        except ZeroDivisionError:
            handle_error(self, "Store_Op_Utilization zero division")
        return self.val
    desc = """
This metric represents Core fraction of cycles CPU
dispatched uops on execution port for Store operations"""


class Retiring:
    name = "Retiring"
    domain = "Slots"
    area = "RET"
    level = 1
    htoff = False
    sample = ['UOPS_RETIRED.SLOTS']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvUW', 'TmaL1'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = (EV("PERF_METRICS.RETIRING", 1) / EV("TOPDOWN.SLOTS", 1)) / PERF_METRICS_SUM(self, EV, 1) if topdown_use_fixed else EV("UOPS_RETIRED.SLOTS", 1) / SLOTS(self, EV, 1)
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
            self.val = max(0 , self.Retiring.compute(EV) - self.Heavy_Operations.compute(EV))
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
achieved.  .. Focus on techniques that reduce instruction
count or result in more efficient instructions generation
such as vectorization."""


class FP_Arith:
    name = "FP_Arith"
    domain = "Uops"
    area = "RET"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['HPC'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = self.X87_Use.compute(EV) + self.FP_Scalar.compute(EV) + self.FP_Vector.compute(EV)
            self.thresh = (self.val > 0.2) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "FP_Arith zero division")
        return self.val
    desc = """
This metric represents overall arithmetic floating-point
(FP) operations fraction the CPU has executed (retired).
Note this metric's value may exceed its parent due to use of
\"Uops\" CountDomain and FMA double-counting."""


class X87_Use:
    name = "X87_Use"
    domain = "Uops"
    area = "RET"
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['Compute'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = self.Retiring.compute(EV) * EV("UOPS_EXECUTED.X87", 4) / EV("UOPS_EXECUTED.THREAD", 4)
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "X87_Use zero division")
        return self.val
    desc = """
This metric serves as an approximation of legacy x87 usage.
It accounts for instructions beyond X87 FP arithmetic
operations; hence may be used as a thermometer to avoid X87
high usage and preferably upgrade to modern ISA. See Tip
under Tuning Hint.. Tip: consider compiler flags to generate
newer AVX (or SSE) instruction sets; which typically perform
better and feature vectors."""


class FP_Scalar:
    name = "FP_Scalar"
    domain = "Uops"
    area = "RET"
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['Compute', 'Flops'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = FP_Arith_Scalar(self, EV, 4) / Retired_Slots(self, EV, 4)
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "FP_Scalar zero division")
        return self.val
    desc = """
This metric approximates arithmetic floating-point (FP)
scalar uops fraction the CPU has retired. May overcount due
to FMA double counting.. Investigate what limits (compiler)
generation of vector code."""


class FP_Vector:
    name = "FP_Vector"
    domain = "Uops"
    area = "RET"
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['Compute', 'Flops'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = FP_Arith_Vector(self, EV, 4) / Retired_Slots(self, EV, 4)
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "FP_Vector zero division")
        return self.val
    desc = """
This metric approximates arithmetic floating-point (FP)
vector uops fraction the CPU has retired aggregated across
all vector widths. May overcount due to FMA double
counting.. Check if vector width is expected"""


class FP_Vector_128b:
    name = "FP_Vector_128b"
    domain = "Uops"
    area = "RET"
    level = 5
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['Compute', 'Flops'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = (EV("FP_ARITH_INST_RETIRED.128B_PACKED_DOUBLE", 5) + EV("FP_ARITH_INST_RETIRED.128B_PACKED_SINGLE", 5)) / Retired_Slots(self, EV, 5)
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "FP_Vector_128b zero division")
        return self.val
    desc = """
This metric approximates arithmetic FP vector uops fraction
the CPU has retired for 128-bit wide vectors. May overcount
due to FMA double counting prior to LNL.. Try to exploit
wider vector length"""


class FP_Vector_256b:
    name = "FP_Vector_256b"
    domain = "Uops"
    area = "RET"
    level = 5
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['Compute', 'Flops'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = (EV("FP_ARITH_INST_RETIRED.256B_PACKED_DOUBLE", 5) + EV("FP_ARITH_INST_RETIRED.256B_PACKED_SINGLE", 5)) / Retired_Slots(self, EV, 5)
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "FP_Vector_256b zero division")
        return self.val
    desc = """
This metric approximates arithmetic FP vector uops fraction
the CPU has retired for 256-bit wide vectors. May overcount
due to FMA double counting prior to LNL.. Try to exploit
wider vector length"""


class Int_Operations:
    name = "Int_Operations"
    domain = "Uops"
    area = "RET"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['Pipeline'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = self.Int_Vector_128b.compute(EV) + self.Int_Vector_256b.compute(EV)
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Int_Operations zero division")
        return self.val
    desc = """
This metric represents overall Integer (Int) select
operations fraction the CPU has executed (retired).
Vector/Matrix Int operations and shuffles are counted. Note
this metric's value may exceed its parent due to use of
\"Uops\" CountDomain."""


class Int_Vector_128b:
    name = "Int_Vector_128b"
    domain = "Uops"
    area = "RET"
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['Compute', 'IntVector', 'Pipeline'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = (EV("INT_VEC_RETIRED.ADD_128", 4) + EV("INT_VEC_RETIRED.VNNI_128", 4)) / Retired_Slots(self, EV, 4)
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Int_Vector_128b zero division")
        return self.val
    desc = """
This metric represents 128-bit vector Integer ADD/SUB/SAD or
VNNI (Vector Neural Network Instructions) uops fraction the
CPU has retired."""


class Int_Vector_256b:
    name = "Int_Vector_256b"
    domain = "Uops"
    area = "RET"
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['Compute', 'IntVector', 'Pipeline'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = (EV("INT_VEC_RETIRED.ADD_256", 4) + EV("INT_VEC_RETIRED.MUL_256", 4) + EV("INT_VEC_RETIRED.VNNI_256", 4)) / Retired_Slots(self, EV, 4)
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Int_Vector_256b zero division")
        return self.val
    desc = """
This metric represents 256-bit vector Integer
ADD/SUB/SAD/MUL or VNNI (Vector Neural Network Instructions)
uops fraction the CPU has retired."""


class Memory_Operations:
    name = "Memory_Operations"
    domain = "Slots"
    area = "RET"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['Pipeline'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = self.Light_Operations.compute(EV) * EV("MEM_UOP_RETIRED.ANY", 3) / Retired_Slots(self, EV, 3)
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Memory_Operations zero division")
        return self.val
    desc = """
This metric represents fraction of slots where the CPU was
retiring memory operations -- uops for memory load or store
accesses."""


class Fused_Instructions:
    name = "Fused_Instructions"
    domain = "Slots"
    area = "RET"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['Branches', 'BvBO', 'Pipeline'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = self.Light_Operations.compute(EV) * EV("INST_RETIRED.MACRO_FUSED", 3) / Retired_Slots(self, EV, 3)
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Fused_Instructions zero division")
        return self.val
    desc = """
This metric represents fraction of slots where the CPU was
retiring fused instructions -- where one uop can represent
multiple contiguous instructions. CMP+JCC or DEC+JCC are
common examples of legacy fusions. { Note new MOV+OP and
Load+OP fusions appear under Other_Light_Ops in MTL!}. See
section 'Optimizing for Macro-fusion' in Optimization
Manual:"""


class Non_Fused_Branches:
    name = "Non_Fused_Branches"
    domain = "Slots"
    area = "RET"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['Branches', 'BvBO', 'Pipeline'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = self.Light_Operations.compute(EV) * (EV("BR_INST_RETIRED.ALL_BRANCHES", 3) - EV("INST_RETIRED.MACRO_FUSED", 3)) / Retired_Slots(self, EV, 3)
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Non_Fused_Branches zero division")
        return self.val
    desc = """
This metric represents fraction of slots where the CPU was
retiring branch instructions that were not fused. Non-
conditional branches like direct JMP or CALL would count
here. Can be used to examine fusible conditional jumps that
were not fused."""


class Other_Light_Ops:
    name = "Other_Light_Ops"
    domain = "Slots"
    area = "RET"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['Pipeline'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = max(0 , self.Light_Operations.compute(EV) - Light_Ops_Sum(self, EV, 3))
            self.thresh = (self.val > 0.3) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Other_Light_Ops zero division")
        return self.val
    desc = """
This metric represents the remaining light uops fraction the
CPU has executed - remaining means not covered by other
sibling nodes. May undercount due to FMA double counting"""


class Nop_Instructions:
    name = "Nop_Instructions"
    domain = "Slots"
    area = "RET"
    level = 4
    htoff = False
    sample = ['INST_RETIRED.NOP']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvBO', 'Pipeline'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = self.Light_Operations.compute(EV) * EV("INST_RETIRED.NOP", 4) / Retired_Slots(self, EV, 4)
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Nop_Instructions zero division")
        return self.val
    desc = """
This metric represents fraction of slots where the CPU was
retiring NOP (no op) instructions. Compilers often use NOPs
for certain address alignments - e.g. start address of a
function or loop body.. Improve Codegen by correctly placing
NOPs outside hot sections (e.g. outside loop body)."""


class Shuffles_256b:
    name = "Shuffles_256b"
    domain = "Slots"
    area = "RET"
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['HPC', 'Pipeline'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = self.Light_Operations.compute(EV) * EV("INT_VEC_RETIRED.SHUFFLES", 4) / Retired_Slots(self, EV, 4)
            self.thresh = (self.val > 0.1) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Shuffles_256b zero division")
        return self.val
    desc = """
This metric represents fraction of slots where the CPU was
retiring Shuffle operations of 256-bit vector size (FP or
Integer). Shuffles may incur slow cross \"vector lane\" data
transfers."""


class Heavy_Operations:
    name = "Heavy_Operations"
    domain = "Slots"
    area = "RET"
    level = 2
    htoff = False
    sample = ['UOPS_RETIRED.HEAVY']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['Retire', 'TmaL2'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = (EV("PERF_METRICS.HEAVY_OPERATIONS", 2) / EV("TOPDOWN.SLOTS", 2)) / PERF_METRICS_SUM(self, EV, 2) if topdown_use_fixed else EV("UOPS_RETIRED.HEAVY", 2) / SLOTS(self, EV, 2)
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


class Few_Uops_Instructions:
    name = "Few_Uops_Instructions"
    domain = "Slots"
    area = "RET"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = max(0 , self.Heavy_Operations.compute(EV) - self.Microcode_Sequencer.compute(EV))
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Few_Uops_Instructions zero division")
        return self.val
    desc = """
This metric represents fraction of slots where the CPU was
retiring instructions that that are decoder into two or more
uops. This highly-correlates with the number of uops in such
instructions."""


class Microcode_Sequencer:
    name = "Microcode_Sequencer"
    domain = "Slots"
    area = "RET"
    level = 3
    htoff = False
    sample = ['UOPS_RETIRED.MS']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['MicroSeq'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("UOPS_RETIRED.MS", 3) / SLOTS(self, EV, 3)
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
    sample = ['ASSISTS.ANY']
    errcount = 0
    sibling = None
    metricgroup = frozenset(['BvIO'])
    maxval = 1
    def compute(self, EV):
        try:
            self.val = Avg_Assist_Cost * EV("ASSISTS.ANY", 4) / SLOTS(self, EV, 4)
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


class Page_Faults:
    name = "Page_Faults"
    domain = "Slots_Estimated"
    area = "RET"
    level = 5
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = 99 * EV("ASSISTS.PAGE_FAULT", 5) / SLOTS(self, EV, 5)
            self.thresh = (self.val > 0.05)
        except ZeroDivisionError:
            handle_error(self, "Page_Faults zero division")
        return self.val
    desc = """
This metric roughly estimates fraction of slots the CPU
retired uops as a result of handing Page Faults. A Page
Fault may apply on first application access to a memory
page. Note operating system handling of page faults accounts
for the majority of its cost."""


class FP_Assists:
    name = "FP_Assists"
    domain = "Slots_Estimated"
    area = "RET"
    level = 5
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['HPC'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = 30 * EV("ASSISTS.FP", 5) / SLOTS(self, EV, 5)
            self.thresh = (self.val > 0.1)
        except ZeroDivisionError:
            handle_error(self, "FP_Assists zero division")
        return self.val
    desc = """
This metric roughly estimates fraction of slots the CPU
retired uops as a result of handing Floating Point (FP)
Assists. FP Assist may apply when working with very small
floating point values (so-called Denormals).. Consider DAZ
(Denormals Are Zero) and/or FTZ (Flush To Zero) options in
your compiler; \"-ffast-math\" with -O2 in GCC for example.
This option may improve performance if the denormal values
are not critical in your application. Also note that the DAZ
and FTZ modes are not compatible with the IEEE Standard
754.. https://www.intel.com/content/www/us/en/develop/docume
ntation/vtune-help/top/reference/cpu-metrics-reference/bad-
speculation-back-end-bound-pipeline-slots/fp-assists.html"""


class AVX_Assists:
    name = "AVX_Assists"
    domain = "Slots_Estimated"
    area = "RET"
    level = 5
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset(['HPC'])
    maxval = None
    def compute(self, EV):
        try:
            self.val = 63 * EV("ASSISTS.SSE_AVX_MIX", 5) / SLOTS(self, EV, 5)
            self.thresh = (self.val > 0.1)
        except ZeroDivisionError:
            handle_error(self, "AVX_Assists zero division")
        return self.val
    desc = """
This metric estimates fraction of slots the CPU retired uops
as a result of handing SSE to AVX* or AVX* to SSE transition
Assists."""


class CISC:
    name = "CISC"
    domain = "Slots"
    area = "RET"
    level = 4
    htoff = False
    sample = ['FRONTEND_RETIRED.MS_FLOWS']
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


class Metric_Mispredictions:
    name = "Mispredictions"
    domain = "Scaled_Slots"
    maxval = 0
    errcount = 0
    area = "Bottleneck"
    metricgroup = frozenset(['Bad', 'BadSpec', 'BrMispredicts', 'BvMP'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Mispredictions(self, EV, 0)
            self.thresh = (self.val > 20)
        except ZeroDivisionError:
            handle_error_metric(self, "Mispredictions zero division")
    desc = """
Total pipeline cost of Branch Misprediction related
bottlenecks"""


class Metric_Big_Code:
    name = "Big_Code"
    domain = "Scaled_Slots"
    maxval = 0
    errcount = 0
    area = "Bottleneck"
    metricgroup = frozenset(['BvBC', 'BigFootprint', 'Fed', 'Frontend', 'IcMiss', 'MemoryTLB'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Big_Code(self, EV, 0)
            self.thresh = (self.val > 20)
        except ZeroDivisionError:
            handle_error_metric(self, "Big_Code zero division")
    desc = """
Total pipeline cost of instruction fetch related bottlenecks
by large code footprint programs (i-side cache; TLB and BTB
misses)"""


class Metric_Instruction_Fetch_BW:
    name = "Instruction_Fetch_BW"
    domain = "Scaled_Slots"
    maxval = 0
    errcount = 0
    area = "Bottleneck"
    metricgroup = frozenset(['BvFB', 'Fed', 'FetchBW', 'Frontend'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Instruction_Fetch_BW(self, EV, 0)
            self.thresh = (self.val > 20)
        except ZeroDivisionError:
            handle_error_metric(self, "Instruction_Fetch_BW zero division")
    desc = """
Total pipeline cost of instruction fetch bandwidth related
bottlenecks (when the front-end could not sustain operations
delivery to the back-end)"""


class Metric_Cache_Memory_Bandwidth:
    name = "Cache_Memory_Bandwidth"
    domain = "Scaled_Slots"
    maxval = 0
    errcount = 0
    area = "Bottleneck"
    metricgroup = frozenset(['BvMB', 'Mem', 'MemoryBW', 'Offcore'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Cache_Memory_Bandwidth(self, EV, 0)
            self.thresh = (self.val > 20)
        except ZeroDivisionError:
            handle_error_metric(self, "Cache_Memory_Bandwidth zero division")
    desc = """
Total pipeline cost of external Memory- or Cache-Bandwidth
related bottlenecks"""


class Metric_Cache_Memory_Latency:
    name = "Cache_Memory_Latency"
    domain = "Scaled_Slots"
    maxval = 0
    errcount = 0
    area = "Bottleneck"
    metricgroup = frozenset(['BvML', 'Mem', 'MemoryLat', 'Offcore'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Cache_Memory_Latency(self, EV, 0)
            self.thresh = (self.val > 20)
        except ZeroDivisionError:
            handle_error_metric(self, "Cache_Memory_Latency zero division")
    desc = """
Total pipeline cost of external Memory- or Cache-Latency
related bottlenecks"""


class Metric_Memory_Data_TLBs:
    name = "Memory_Data_TLBs"
    domain = "Scaled_Slots"
    maxval = 0
    errcount = 0
    area = "Bottleneck"
    metricgroup = frozenset(['BvMT', 'Mem', 'MemoryTLB', 'Offcore'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Memory_Data_TLBs(self, EV, 0)
            self.thresh = (self.val > 20)
        except ZeroDivisionError:
            handle_error_metric(self, "Memory_Data_TLBs zero division")
    desc = """
Total pipeline cost of Memory Address Translation related
bottlenecks (data-side TLBs)"""


class Metric_Memory_Synchronization:
    name = "Memory_Synchronization"
    domain = "Scaled_Slots"
    maxval = 0
    errcount = 0
    area = "Bottleneck"
    metricgroup = frozenset(['BvMS', 'LockCont', 'Mem', 'Offcore'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Memory_Synchronization(self, EV, 0)
            self.thresh = (self.val > 10)
        except ZeroDivisionError:
            handle_error_metric(self, "Memory_Synchronization zero division")
    desc = """
Total pipeline cost of Memory Synchronization related
bottlenecks (data transfers and coherency updates across
processors)"""


class Metric_Compute_Bound_Est:
    name = "Compute_Bound_Est"
    domain = "Scaled_Slots"
    maxval = 0
    errcount = 0
    area = "Bottleneck"
    metricgroup = frozenset(['BvCB', 'Cor'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Compute_Bound_Est(self, EV, 0)
            self.thresh = (self.val > 20)
        except ZeroDivisionError:
            handle_error_metric(self, "Compute_Bound_Est zero division")
    desc = """
Total pipeline cost when the execution is compute-bound - an
estimation. Covers Core Bound when High ILP as well as when
long-latency execution units are busy."""


class Metric_Irregular_Overhead:
    name = "Irregular_Overhead"
    domain = "Scaled_Slots"
    maxval = 0
    errcount = 0
    area = "Bottleneck"
    metricgroup = frozenset(['Bad', 'BvIO', 'Cor', 'Ret'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Irregular_Overhead(self, EV, 0)
            self.thresh = (self.val > 10)
        except ZeroDivisionError:
            handle_error_metric(self, "Irregular_Overhead zero division")
    desc = """
Total pipeline cost of irregular execution (e.g. FP-assists
in HPC, Wait time with work imbalance multithreaded
workloads, overhead in system services or virtualized
environments)"""


class Metric_Other_Bottlenecks:
    name = "Other_Bottlenecks"
    domain = "Scaled_Slots"
    maxval = 0
    errcount = 0
    area = "Bottleneck"
    metricgroup = frozenset(['BvOB', 'Cor', 'Offcore'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Other_Bottlenecks(self, EV, 0)
            self.thresh = (self.val > 20)
        except ZeroDivisionError:
            handle_error_metric(self, "Other_Bottlenecks zero division")
    desc = """
Total pipeline cost of remaining bottlenecks in the back-
end. Examples include data-dependencies (Core Bound when Low
ILP) and other unlisted memory-related stalls."""


class Metric_Branching_Overhead:
    name = "Branching_Overhead"
    domain = "Scaled_Slots"
    maxval = 0
    errcount = 0
    area = "Bottleneck"
    metricgroup = frozenset(['BvBO', 'Ret'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Branching_Overhead(self, EV, 0)
            self.thresh = (self.val > 5)
        except ZeroDivisionError:
            handle_error_metric(self, "Branching_Overhead zero division")
    desc = """
Total pipeline cost of instructions used for program
control-flow - a subset of the Retiring category in TMA.
Examples include function calls; loops and alignments. (A
lower bound). Consider Loop Unrolling or function inlining
optimizations"""


class Metric_Useful_Work:
    name = "Useful_Work"
    domain = "Scaled_Slots"
    maxval = 0
    errcount = 0
    area = "Bottleneck"
    metricgroup = frozenset(['BvUW', 'Ret'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Useful_Work(self, EV, 0)
            self.thresh = (self.val > 20)
        except ZeroDivisionError:
            handle_error_metric(self, "Useful_Work zero division")
    desc = """
Total pipeline cost of \"useful operations\" - the portion
of Retiring category not covered by Branching_Overhead nor
Irregular_Overhead."""


class Metric_Core_Bound_Likely:
    name = "Core_Bound_Likely"
    domain = "Metric"
    maxval = 1
    errcount = 0
    area = "Info.Botlnk.L0"
    metricgroup = frozenset(['Cor', 'SMT'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Core_Bound_Likely(self, EV, 0)
            self.thresh = (self.val > 0.5)
        except ZeroDivisionError:
            handle_error_metric(self, "Core_Bound_Likely zero division")
    desc = """
Probability of Core Bound bottleneck hidden by SMT-profiling
artifacts. Tip: consider analysis with SMT disabled"""


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


class Metric_Slots_Utilization:
    name = "Slots_Utilization"
    domain = "Metric"
    maxval = 1
    errcount = 0
    area = "Info.Thread"
    metricgroup = frozenset(['SMT', 'TmaL1'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Slots_Utilization(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Slots_Utilization zero division")
    desc = """
Fraction of Physical Core issue-slots utilized by this
Logical Processor"""


class Metric_Execute_per_Issue:
    name = "Execute_per_Issue"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Thread"
    metricgroup = frozenset(['Cor', 'Pipeline'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Execute_per_Issue(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Execute_per_Issue zero division")
    desc = """
The ratio of Executed- by Issued-Uops. Ratio > 1 suggests
high rate of uop micro-fusions. Ratio < 1 suggest high rate
of \"execute\" at rename stage."""


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


class Metric_FLOPc:
    name = "FLOPc"
    domain = "Core_Metric"
    maxval = 10
    errcount = 0
    area = "Info.Core"
    metricgroup = frozenset(['Ret', 'Flops'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = FLOPc(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "FLOPc zero division")
    desc = """
Floating Point Operations Per Cycle"""


class Metric_FP_Arith_Utilization:
    name = "FP_Arith_Utilization"
    domain = "Core_Metric"
    maxval = 2
    errcount = 0
    area = "Info.Core"
    metricgroup = frozenset(['Cor', 'Flops', 'HPC'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = FP_Arith_Utilization(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "FP_Arith_Utilization zero division")
    desc = """
Actual per-core usage of the Floating Point non-X87
execution units (regardless of precision or vector-width).
Values > 1 are possible due to  Fused-Multiply Add  use all
of ADD/MUL/FMA in Scalar or 128/256-bit vectors - less
common."""


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


class Metric_EPC:
    name = "EPC"
    domain = "Metric"
    maxval = 20
    errcount = 0
    area = "Info.Core"
    metricgroup = frozenset(['Power'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = EPC(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "EPC zero division")
    desc = """
uops Executed per Cycle"""


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


class Metric_IpFLOP:
    name = "IpFLOP"
    domain = "Inst_Metric"
    maxval = 0
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = frozenset(['Flops', 'InsType'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpFLOP(self, EV, 0)
            self.thresh = (self.val < 10)
        except ZeroDivisionError:
            handle_error_metric(self, "IpFLOP zero division")
    desc = """
Instructions per Floating Point (FP) Operation (lower number
means higher occurrence rate). Reference: Tuning Performance
via Metrics with Expectations.
https://doi.org/10.1109/LCA.2019.2916408"""


class Metric_IpArith:
    name = "IpArith"
    domain = "Inst_Metric"
    maxval = 0
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = frozenset(['Flops', 'InsType'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpArith(self, EV, 0)
            self.thresh = (self.val < 10)
        except ZeroDivisionError:
            handle_error_metric(self, "IpArith zero division")
    desc = """
Instructions per FP Arithmetic instruction (lower number
means higher occurrence rate). Values < 1 are possible due
to intentional FMA double counting. Approximated prior to
BDW."""


class Metric_IpArith_Scalar_SP:
    name = "IpArith_Scalar_SP"
    domain = "Inst_Metric"
    maxval = 0
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = frozenset(['Flops', 'FpScalar', 'InsType'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpArith_Scalar_SP(self, EV, 0)
            self.thresh = (self.val < 10)
        except ZeroDivisionError:
            handle_error_metric(self, "IpArith_Scalar_SP zero division")
    desc = """
Instructions per FP Arithmetic Scalar Single-Precision
instruction (lower number means higher occurrence rate).
Values < 1 are possible due to intentional FMA double
counting."""


class Metric_IpArith_Scalar_DP:
    name = "IpArith_Scalar_DP"
    domain = "Inst_Metric"
    maxval = 0
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = frozenset(['Flops', 'FpScalar', 'InsType'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpArith_Scalar_DP(self, EV, 0)
            self.thresh = (self.val < 10)
        except ZeroDivisionError:
            handle_error_metric(self, "IpArith_Scalar_DP zero division")
    desc = """
Instructions per FP Arithmetic Scalar Double-Precision
instruction (lower number means higher occurrence rate).
Values < 1 are possible due to intentional FMA double
counting."""


class Metric_IpArith_AVX128:
    name = "IpArith_AVX128"
    domain = "Inst_Metric"
    maxval = 0
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = frozenset(['Flops', 'FpVector', 'InsType'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpArith_AVX128(self, EV, 0)
            self.thresh = (self.val < 10)
        except ZeroDivisionError:
            handle_error_metric(self, "IpArith_AVX128 zero division")
    desc = """
Instructions per FP Arithmetic AVX/SSE 128-bit instruction
(lower number means higher occurrence rate). Values < 1 are
possible due to intentional FMA double counting."""


class Metric_IpArith_AVX256:
    name = "IpArith_AVX256"
    domain = "Inst_Metric"
    maxval = 0
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = frozenset(['Flops', 'FpVector', 'InsType'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpArith_AVX256(self, EV, 0)
            self.thresh = (self.val < 10)
        except ZeroDivisionError:
            handle_error_metric(self, "IpArith_AVX256 zero division")
    desc = """
Instructions per FP Arithmetic AVX* 256-bit instruction
(lower number means higher occurrence rate). Values < 1 are
possible due to intentional FMA double counting."""


class Metric_IpPause:
    name = "IpPause"
    domain = "Inst_Metric"
    maxval = 0
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = frozenset(['Flops', 'FpVector', 'InsType'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpPause(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "IpPause zero division")
    desc = """
Instructions per PAUSE (lower number means higher occurrence
rate)"""


class Metric_IpSWPF:
    name = "IpSWPF"
    domain = "Inst_Metric"
    maxval = 1000
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = frozenset(['Prefetches'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpSWPF(self, EV, 0)
            self.thresh = (self.val < 100)
        except ZeroDivisionError:
            handle_error_metric(self, "IpSWPF zero division")
    desc = """
Instructions per Software prefetch instruction (of any type:
NTA/T0/T1/T2/Prefetch) (lower number means higher occurrence
rate)"""


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


class Metric_Strings_Cycles:
    name = "Strings_Cycles"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Pipeline"
    metricgroup = frozenset(['MicroSeq', 'Pipeline', 'Ret'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Strings_Cycles(self, EV, 0)
            self.thresh = (self.val > 0.1)
        except ZeroDivisionError:
            handle_error_metric(self, "Strings_Cycles zero division")
    desc = """
Estimated fraction of retirement-cycles dealing with repeat
instructions"""


class Metric_IpAssist:
    name = "IpAssist"
    domain = "Inst_Metric"
    maxval = 0
    errcount = 0
    area = "Info.Pipeline"
    metricgroup = frozenset(['MicroSeq', 'Pipeline', 'Ret', 'Retire'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpAssist(self, EV, 0)
            self.thresh = (self.val < 100000)
        except ZeroDivisionError:
            handle_error_metric(self, "IpAssist zero division")
    desc = """
Instructions per a microcode Assist invocation. See Assists
tree node for details (lower number means higher occurrence
rate)"""


class Metric_Execute:
    name = "Execute"
    domain = "Metric"
    maxval = Exe_Ports
    errcount = 0
    area = "Info.Pipeline"
    metricgroup = frozenset(['Cor', 'Pipeline', 'PortsUtil', 'SMT'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Execute(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Execute zero division")
    desc = """
Instruction-Level-Parallelism (average number of uops
executed when there is execution) per physical core"""


class Metric_Fetch_LSD:
    name = "Fetch_LSD"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Pipeline"
    metricgroup = frozenset(['Fed', 'FetchBW'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Fetch_LSD(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Fetch_LSD zero division")
    desc = """
Average number of uops fetched from LSD per cycle"""


class Metric_Fetch_DSB:
    name = "Fetch_DSB"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Pipeline"
    metricgroup = frozenset(['Fed', 'FetchBW'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Fetch_DSB(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Fetch_DSB zero division")
    desc = """
Average number of uops fetched from DSB per cycle"""


class Metric_Fetch_MITE:
    name = "Fetch_MITE"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Pipeline"
    metricgroup = frozenset(['Fed', 'FetchBW'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Fetch_MITE(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Fetch_MITE zero division")
    desc = """
Average number of uops fetched from MITE per cycle"""


class Metric_Fetch_UpC:
    name = "Fetch_UpC"
    domain = "Metric"
    maxval = 6
    errcount = 0
    area = "Info.Frontend"
    metricgroup = frozenset(['Fed', 'FetchBW'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Fetch_UpC(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Fetch_UpC zero division")
    desc = """
Average number of Uops issued by front-end when it issued
something"""


class Metric_LSD_Coverage:
    name = "LSD_Coverage"
    domain = "Metric"
    maxval = 1
    errcount = 0
    area = "Info.Frontend"
    metricgroup = frozenset(['Fed', 'LSD'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = LSD_Coverage(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "LSD_Coverage zero division")
    desc = """
Fraction of Uops delivered by the LSD (Loop Stream Detector;
aka Loop Cache)"""


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


class Metric_Unknown_Branch_Cost:
    name = "Unknown_Branch_Cost"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Frontend"
    metricgroup = frozenset(['Fed'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Unknown_Branch_Cost(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Unknown_Branch_Cost zero division")
    desc = """
Average number of cycles the front-end was delayed due to an
Unknown Branch detection. See Unknown_Branches node."""


class Metric_DSB_Switch_Cost:
    name = "DSB_Switch_Cost"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Frontend"
    metricgroup = frozenset(['DSBmiss'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = DSB_Switch_Cost(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "DSB_Switch_Cost zero division")
    desc = """
Average number of cycles of a switch from the DSB fetch-unit
to MITE fetch unit - see DSB_Switches tree node for details."""


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


class Metric_DSB_Misses:
    name = "DSB_Misses"
    domain = "Scaled_Slots"
    maxval = 0
    errcount = 0
    area = "Info.Botlnk.L2"
    metricgroup = frozenset(['DSBmiss', 'Fed'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = DSB_Misses(self, EV, 0)
            self.thresh = (self.val > 10)
        except ZeroDivisionError:
            handle_error_metric(self, "DSB_Misses zero division")
    desc = """
Total pipeline cost of DSB (uop cache) misses - subset of
the Instruction_Fetch_BW Bottleneck."""


class Metric_DSB_Bandwidth:
    name = "DSB_Bandwidth"
    domain = "Scaled_Slots"
    maxval = 0
    errcount = 0
    area = "Info.Botlnk.L2"
    metricgroup = frozenset(['DSB', 'Fed', 'FetchBW'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = DSB_Bandwidth(self, EV, 0)
            self.thresh = (self.val > 10)
        except ZeroDivisionError:
            handle_error_metric(self, "DSB_Bandwidth zero division")
    desc = """
Total pipeline cost of DSB (uop cache) hits - subset of the
Instruction_Fetch_BW Bottleneck."""


class Metric_DSB_Switches_Ret:
    name = "DSB_Switches_Ret"
    domain = "Clocks_Retired"
    maxval = 0
    errcount = 0
    area = "Info.Frontend"
    metricgroup = frozenset(['DSBmiss', 'Fed', 'FetchLat'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = DSB_Switches_Ret(self, EV, 0)
            self.thresh = (self.val > 0.05)
        except ZeroDivisionError:
            handle_error_metric(self, "DSB_Switches_Ret zero division")
    desc = """
This metric represents fraction of cycles the CPU retirement
was stalled likely due to retired DSB misses"""


class Metric_MS_Latency_Ret:
    name = "MS_Latency_Ret"
    domain = "Clocks_Retired"
    maxval = 0
    errcount = 0
    area = "Info.Frontend"
    metricgroup = frozenset(['Fed', 'FetchLat', 'MicroSeq'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = MS_Latency_Ret(self, EV, 0)
            self.thresh = (self.val > 0.05)
        except ZeroDivisionError:
            handle_error_metric(self, "MS_Latency_Ret zero division")
    desc = """
This metric represents fraction of cycles the CPU retirement
was stalled likely due to retired operations that invoke the
Microcode Sequencer"""


class Metric_Unknown_Branches_Ret:
    name = "Unknown_Branches_Ret"
    domain = "Clocks_Retired"
    maxval = 0
    errcount = 0
    area = "Info.Frontend"
    metricgroup = frozenset(['Fed', 'FetchLat'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Unknown_Branches_Ret(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Unknown_Branches_Ret zero division")
    desc = """
This metric represents fraction of cycles the CPU retirement
was stalled likely due to retired branches who got branch
address clears"""


class Metric_ICache_Miss_Latency:
    name = "ICache_Miss_Latency"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Frontend"
    metricgroup = frozenset(['Fed', 'FetchLat', 'IcMiss'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = ICache_Miss_Latency(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "ICache_Miss_Latency zero division")
    desc = """
Average Latency for L1 instruction cache misses"""


class Metric_IC_Misses:
    name = "IC_Misses"
    domain = "Scaled_Slots"
    maxval = 0
    errcount = 0
    area = "Info.Botlnk.L2"
    metricgroup = frozenset(['Fed', 'FetchLat', 'IcMiss'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IC_Misses(self, EV, 0)
            self.thresh = (self.val > 5)
        except ZeroDivisionError:
            handle_error_metric(self, "IC_Misses zero division")
    desc = """
Total pipeline cost of Instruction Cache misses - subset of
the Big_Code Bottleneck."""


class Metric_IpDSB_Miss_Ret:
    name = "IpDSB_Miss_Ret"
    domain = "Inst_Metric"
    maxval = 0
    errcount = 0
    area = "Info.Frontend"
    metricgroup = frozenset(['DSBmiss', 'Fed'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpDSB_Miss_Ret(self, EV, 0)
            self.thresh = (self.val < 50)
        except ZeroDivisionError:
            handle_error_metric(self, "IpDSB_Miss_Ret zero division")
    desc = """
Instructions per non-speculative DSB miss (lower number
means higher occurrence rate)"""


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


class Metric_L2MPKI_Code:
    name = "L2MPKI_Code"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Frontend"
    metricgroup = frozenset(['IcMiss'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = L2MPKI_Code(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "L2MPKI_Code zero division")
    desc = """
L2 cache true code cacheline misses per kilo instruction"""


class Metric_L2MPKI_Code_All:
    name = "L2MPKI_Code_All"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Frontend"
    metricgroup = frozenset(['IcMiss'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = L2MPKI_Code_All(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "L2MPKI_Code_All zero division")
    desc = """
L2 cache speculative code cacheline misses per kilo
instruction"""


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


class Metric_IpMisp_Cond_Ntaken:
    name = "IpMisp_Cond_Ntaken"
    domain = "Inst_Metric"
    maxval = 0
    errcount = 0
    area = "Info.Bad_Spec"
    metricgroup = frozenset(['Bad', 'BrMispredicts'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpMisp_Cond_Ntaken(self, EV, 0)
            self.thresh = (self.val < 200)
        except ZeroDivisionError:
            handle_error_metric(self, "IpMisp_Cond_Ntaken zero division")
    desc = """
Instructions per retired Mispredicts for conditional non-
taken branches (lower number means higher occurrence rate)."""


class Metric_IpMisp_Cond_Taken:
    name = "IpMisp_Cond_Taken"
    domain = "Inst_Metric"
    maxval = 0
    errcount = 0
    area = "Info.Bad_Spec"
    metricgroup = frozenset(['Bad', 'BrMispredicts'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpMisp_Cond_Taken(self, EV, 0)
            self.thresh = (self.val < 200)
        except ZeroDivisionError:
            handle_error_metric(self, "IpMisp_Cond_Taken zero division")
    desc = """
Instructions per retired Mispredicts for conditional taken
branches (lower number means higher occurrence rate)."""


class Metric_IpMisp_Ret:
    name = "IpMisp_Ret"
    domain = "Inst_Metric"
    maxval = 0
    errcount = 0
    area = "Info.Bad_Spec"
    metricgroup = frozenset(['Bad', 'BrMispredicts'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpMisp_Ret(self, EV, 0)
            self.thresh = (self.val < 500)
        except ZeroDivisionError:
            handle_error_metric(self, "IpMisp_Ret zero division")
    desc = """
Instructions per retired Mispredicts for return branches
(lower number means higher occurrence rate)."""


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


class Metric_Branch_Misprediction_Cost:
    name = "Branch_Misprediction_Cost"
    domain = "Core_Metric"
    maxval = 50
    errcount = 0
    area = "Info.Bad_Spec"
    metricgroup = frozenset(['Bad', 'BrMispredicts'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Branch_Misprediction_Cost(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Branch_Misprediction_Cost zero division")
    desc = """
Branch Misprediction Cost: Cycles representing fraction of
TMA slots wasted per non-speculative branch misprediction
(retired JEClear)"""


class Metric_Spec_Clears_Ratio:
    name = "Spec_Clears_Ratio"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Bad_Spec"
    metricgroup = frozenset(['BrMispredicts'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Spec_Clears_Ratio(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Spec_Clears_Ratio zero division")
    desc = """
Speculative to Retired ratio of all clears (covering
Mispredicts and nukes)"""


class Metric_Cond_NT:
    name = "Cond_NT"
    domain = "Fraction"
    maxval = 1
    errcount = 0
    area = "Info.Branches"
    metricgroup = frozenset(['Bad', 'Branches', 'CodeGen', 'PGO'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Cond_NT(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Cond_NT zero division")
    desc = """
Fraction of branches that are non-taken conditionals"""


class Metric_Cond_TK:
    name = "Cond_TK"
    domain = "Fraction"
    maxval = 1
    errcount = 0
    area = "Info.Branches"
    metricgroup = frozenset(['Bad', 'Branches', 'CodeGen', 'PGO'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Cond_TK(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Cond_TK zero division")
    desc = """
Fraction of branches that are taken conditionals"""


class Metric_CallRet:
    name = "CallRet"
    domain = "Fraction"
    maxval = 1
    errcount = 0
    area = "Info.Branches"
    metricgroup = frozenset(['Bad', 'Branches'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = CallRet(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "CallRet zero division")
    desc = """
Fraction of branches that are CALL or RET"""


class Metric_Jump:
    name = "Jump"
    domain = "Fraction"
    maxval = 1
    errcount = 0
    area = "Info.Branches"
    metricgroup = frozenset(['Bad', 'Branches'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Jump(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Jump zero division")
    desc = """
Fraction of branches that are unconditional (direct or
indirect) jumps"""


class Metric_Other_Branches:
    name = "Other_Branches"
    domain = "Fraction"
    maxval = 1
    errcount = 0
    area = "Info.Branches"
    metricgroup = frozenset(['Bad', 'Branches'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Other_Branches(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Other_Branches zero division")
    desc = """
Fraction of branches of other types (not individually
covered by other metrics in Info.Branches group)"""


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


class Metric_L1MPKI_Load:
    name = "L1MPKI_Load"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Memory"
    metricgroup = frozenset(['CacheHits', 'Mem'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = L1MPKI_Load(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "L1MPKI_Load zero division")
    desc = """
L1 cache true misses per kilo instruction for all demand
loads (including speculative)"""


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


class Metric_L2MPKI_All:
    name = "L2MPKI_All"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Memory"
    metricgroup = frozenset(['CacheHits', 'Mem', 'Offcore'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = L2MPKI_All(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "L2MPKI_All zero division")
    desc = """
L2 cache  true misses per kilo instruction for all request
types (including speculative)"""


class Metric_L2MPKI_Load:
    name = "L2MPKI_Load"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Memory"
    metricgroup = frozenset(['CacheHits', 'Mem'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = L2MPKI_Load(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "L2MPKI_Load zero division")
    desc = """
L2 cache  true misses per kilo instruction for all demand
loads  (including speculative)"""


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


class Metric_L2HPKI_All:
    name = "L2HPKI_All"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Memory"
    metricgroup = frozenset(['CacheHits', 'Mem'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = L2HPKI_All(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "L2HPKI_All zero division")
    desc = """
L2 cache hits per kilo instruction for all request types
(including speculative)"""


class Metric_L2HPKI_Load:
    name = "L2HPKI_Load"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Memory"
    metricgroup = frozenset(['CacheHits', 'Mem'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = L2HPKI_Load(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "L2HPKI_Load zero division")
    desc = """
L2 cache hits per kilo instruction for all demand loads
(including speculative)"""


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


class Metric_FB_HPKI:
    name = "FB_HPKI"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Memory"
    metricgroup = frozenset(['CacheHits', 'Mem'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = FB_HPKI(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "FB_HPKI zero division")
    desc = """
Fill Buffer (FB) hits per kilo instructions for retired
demand loads (L1D misses that merge into ongoing miss-
handling entries)"""


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


class Metric_L3_Cache_Access_BW:
    name = "L3_Cache_Access_BW"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Memory"
    metricgroup = frozenset(['Mem', 'MemoryBW', 'Offcore'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = L3_Cache_Access_BW(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "L3_Cache_Access_BW zero division")
    desc = """
Average per-thread data access bandwidth to the L3 cache [GB
/ sec]"""


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


class Metric_Code_STLB_MPKI:
    name = "Code_STLB_MPKI"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Memory.TLB"
    metricgroup = frozenset(['Fed', 'MemoryTLB'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Code_STLB_MPKI(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Code_STLB_MPKI zero division")
    desc = """
STLB (2nd level TLB) code speculative misses per kilo
instruction (misses of any page-size that complete the page
walk)"""


class Metric_Load_STLB_MPKI:
    name = "Load_STLB_MPKI"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Memory.TLB"
    metricgroup = frozenset(['Mem', 'MemoryTLB'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Load_STLB_MPKI(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Load_STLB_MPKI zero division")
    desc = """
STLB (2nd level TLB) data load speculative misses per kilo
instruction (misses of any page-size that complete the page
walk)"""


class Metric_Store_STLB_MPKI:
    name = "Store_STLB_MPKI"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Memory.TLB"
    metricgroup = frozenset(['Mem', 'MemoryTLB'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Store_STLB_MPKI(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Store_STLB_MPKI zero division")
    desc = """
STLB (2nd level TLB) data store speculative misses per kilo
instruction (misses of any page-size that complete the page
walk)"""


class Metric_Load_STLB_Miss_Ret:
    name = "Load_STLB_Miss_Ret"
    domain = "Clocks_Retired"
    maxval = 0
    errcount = 0
    area = "Info.Memory.TLB"
    metricgroup = frozenset(['Mem', 'MemoryTLB'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Load_STLB_Miss_Ret(self, EV, 0)
            self.thresh = (self.val > 0.05)
        except ZeroDivisionError:
            handle_error_metric(self, "Load_STLB_Miss_Ret zero division")
    desc = """
This metric represents fraction of cycles the CPU retirement
was stalled likely due to STLB misses by demand loads"""


class Metric_Store_STLB_Miss_Ret:
    name = "Store_STLB_Miss_Ret"
    domain = "Clocks_Retired"
    maxval = 0
    errcount = 0
    area = "Info.Memory.TLB"
    metricgroup = frozenset(['Mem', 'MemoryTLB'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Store_STLB_Miss_Ret(self, EV, 0)
            self.thresh = (self.val > 0.05)
        except ZeroDivisionError:
            handle_error_metric(self, "Store_STLB_Miss_Ret zero division")
    desc = """
This metric represents fraction of cycles the CPU retirement
was stalled likely due to STLB misses by demand stores"""


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


class Metric_L3_Cache_Access_BW_2T:
    name = "L3_Cache_Access_BW_2T"
    domain = "Core_Metric"
    maxval = 0
    errcount = 0
    area = "Info.Memory.Core"
    metricgroup = frozenset(['Mem', 'MemoryBW', 'Offcore'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = L3_Cache_Access_BW_2T(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "L3_Cache_Access_BW_2T zero division")
    desc = """
Average per-core data access bandwidth to the L3 cache [GB /
sec]"""


class Metric_Useless_HWPF:
    name = "Useless_HWPF"
    domain = "Metric"
    maxval = 1
    errcount = 0
    area = "Info.Memory.Prefetches"
    metricgroup = frozenset(['Prefetches'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Useless_HWPF(self, EV, 0)
            self.thresh = (self.val > 0.15)
        except ZeroDivisionError:
            handle_error_metric(self, "Useless_HWPF zero division")
    desc = """
Rate of L2 HW prefetched lines that were not used by demand
accesses"""


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


class Metric_Load_L3_Miss_Latency:
    name = "Load_L3_Miss_Latency"
    domain = "Clocks_Latency"
    maxval = 1000
    errcount = 0
    area = "Info.Memory.Latency"
    metricgroup = frozenset(['Memory_Lat', 'Offcore'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Load_L3_Miss_Latency(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Load_L3_Miss_Latency zero division")
    desc = """
Average Latency for L3 cache miss demand Loads"""


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


class Metric_UC_Load_PKI:
    name = "UC_Load_PKI"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Memory.Mix"
    metricgroup = frozenset(['Mem'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = UC_Load_PKI(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "UC_Load_PKI zero division")
    desc = """
Un-cacheable retired load per kilo instruction"""


class Metric_Bus_Lock_PKI:
    name = "Bus_Lock_PKI"
    domain = "Metric"
    maxval = 0
    errcount = 0
    area = "Info.Memory.Mix"
    metricgroup = frozenset(['Mem'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Bus_Lock_PKI(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Bus_Lock_PKI zero division")
    desc = """
\"Bus lock\" per kilo instruction"""


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


class Metric_GFLOPs:
    name = "GFLOPs"
    domain = "Metric"
    maxval = 200
    errcount = 0
    area = "Info.System"
    metricgroup = frozenset(['Cor', 'Flops', 'HPC'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = GFLOPs(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "GFLOPs zero division")
    desc = """
Giga Floating Point Operations Per Second. Aggregate across
all supported options of: FP precisions, scalar and vector
instructions, vector-width"""


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


class Metric_C0_Wait:
    name = "C0_Wait"
    domain = "Metric"
    maxval = 1
    errcount = 0
    area = "Info.System"
    metricgroup = frozenset(['C0Wait'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = C0_Wait(self, EV, 0)
            self.thresh = (self.val > 0.05)
        except ZeroDivisionError:
            handle_error_metric(self, "C0_Wait zero division")
    desc = """
Fraction of cycles the processor is waiting yet unhalted;
covering legacy PAUSE instruction, as well as C0.1 / C0.2
power-performance optimized states. Sample code of TPAUSE: h
ttps://github.com/torvalds/linux/blob/master/arch/x86/lib/de
lay.c"""


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


class Metric_MEM_Parallel_Reads:
    name = "MEM_Parallel_Reads"
    domain = "System_Metric"
    maxval = 100
    errcount = 0
    area = "Info.System"
    metricgroup = frozenset(['Mem', 'MemoryBW', 'SoC'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = MEM_Parallel_Reads(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "MEM_Parallel_Reads zero division")
    desc = """
Average number of parallel data read requests to external
memory. Accounts for demand loads and L1/L2 prefetches"""


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
        n = Code_L2_Hit() ; r.run(n) ; o["Code_L2_Hit"] = n
        n = Code_L2_Miss() ; r.run(n) ; o["Code_L2_Miss"] = n
        n = ITLB_Misses() ; r.run(n) ; o["ITLB_Misses"] = n
        n = Code_STLB_Hit() ; r.run(n) ; o["Code_STLB_Hit"] = n
        n = Code_STLB_Miss() ; r.run(n) ; o["Code_STLB_Miss"] = n
        n = Code_STLB_Miss_4K() ; r.run(n) ; o["Code_STLB_Miss_4K"] = n
        n = Code_STLB_Miss_2M() ; r.run(n) ; o["Code_STLB_Miss_2M"] = n
        n = Branch_Resteers() ; r.run(n) ; o["Branch_Resteers"] = n
        n = Mispredicts_Resteers() ; r.run(n) ; o["Mispredicts_Resteers"] = n
        n = Clears_Resteers() ; r.run(n) ; o["Clears_Resteers"] = n
        n = Unknown_Branches() ; r.run(n) ; o["Unknown_Branches"] = n
        n = MS_Switches() ; r.run(n) ; o["MS_Switches"] = n
        n = LCP() ; r.run(n) ; o["LCP"] = n
        n = DSB_Switches() ; r.run(n) ; o["DSB_Switches"] = n
        n = Fetch_Bandwidth() ; r.run(n) ; o["Fetch_Bandwidth"] = n
        n = MITE() ; r.run(n) ; o["MITE"] = n
        n = Decoder0_Alone() ; r.run(n) ; o["Decoder0_Alone"] = n
        n = DSB() ; r.run(n) ; o["DSB"] = n
        n = LSD() ; r.run(n) ; o["LSD"] = n
        n = MS() ; r.run(n) ; o["MS"] = n
        n = Bad_Speculation() ; r.run(n) ; o["Bad_Speculation"] = n
        n = Branch_Mispredicts() ; r.run(n) ; o["Branch_Mispredicts"] = n
        n = Cond_NT_Mispredicts() ; r.run(n) ; o["Cond_NT_Mispredicts"] = n
        n = Cond_TK_Mispredicts() ; r.run(n) ; o["Cond_TK_Mispredicts"] = n
        n = Ind_Call_Mispredicts() ; r.run(n) ; o["Ind_Call_Mispredicts"] = n
        n = Ind_Jump_Mispredicts() ; r.run(n) ; o["Ind_Jump_Mispredicts"] = n
        n = Ret_Mispredicts() ; r.run(n) ; o["Ret_Mispredicts"] = n
        n = Other_Mispredicts() ; r.run(n) ; o["Other_Mispredicts"] = n
        n = Machine_Clears() ; r.run(n) ; o["Machine_Clears"] = n
        n = Other_Nukes() ; r.run(n) ; o["Other_Nukes"] = n
        n = Backend_Bound() ; r.run(n) ; o["Backend_Bound"] = n
        n = Memory_Bound() ; r.run(n) ; o["Memory_Bound"] = n
        n = L1_Bound() ; r.run(n) ; o["L1_Bound"] = n
        n = DTLB_Load() ; r.run(n) ; o["DTLB_Load"] = n
        n = Load_STLB_Hit() ; r.run(n) ; o["Load_STLB_Hit"] = n
        n = Load_STLB_Miss() ; r.run(n) ; o["Load_STLB_Miss"] = n
        n = Load_STLB_Miss_4K() ; r.run(n) ; o["Load_STLB_Miss_4K"] = n
        n = Load_STLB_Miss_2M() ; r.run(n) ; o["Load_STLB_Miss_2M"] = n
        n = Load_STLB_Miss_1G() ; r.run(n) ; o["Load_STLB_Miss_1G"] = n
        n = Store_Fwd_Blk() ; r.run(n) ; o["Store_Fwd_Blk"] = n
        n = L1_Latency_Dependency() ; r.run(n) ; o["L1_Latency_Dependency"] = n
        n = Lock_Latency() ; r.run(n) ; o["Lock_Latency"] = n
        n = Split_Loads() ; r.run(n) ; o["Split_Loads"] = n
        n = FB_Full() ; r.run(n) ; o["FB_Full"] = n
        n = L2_Bound() ; r.run(n) ; o["L2_Bound"] = n
        n = L2_Hit_Latency() ; r.run(n) ; o["L2_Hit_Latency"] = n
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
        n = Streaming_Stores() ; r.run(n) ; o["Streaming_Stores"] = n
        n = DTLB_Store() ; r.run(n) ; o["DTLB_Store"] = n
        n = Store_STLB_Hit() ; r.run(n) ; o["Store_STLB_Hit"] = n
        n = Store_STLB_Miss() ; r.run(n) ; o["Store_STLB_Miss"] = n
        n = Store_STLB_Miss_4K() ; r.run(n) ; o["Store_STLB_Miss_4K"] = n
        n = Store_STLB_Miss_2M() ; r.run(n) ; o["Store_STLB_Miss_2M"] = n
        n = Store_STLB_Miss_1G() ; r.run(n) ; o["Store_STLB_Miss_1G"] = n
        n = Core_Bound() ; r.run(n) ; o["Core_Bound"] = n
        n = Divider() ; r.run(n) ; o["Divider"] = n
        n = FP_Divider() ; r.run(n) ; o["FP_Divider"] = n
        n = INT_Divider() ; r.run(n) ; o["INT_Divider"] = n
        n = Serializing_Operation() ; r.run(n) ; o["Serializing_Operation"] = n
        n = Slow_Pause() ; r.run(n) ; o["Slow_Pause"] = n
        n = C01_Wait() ; r.run(n) ; o["C01_Wait"] = n
        n = C02_Wait() ; r.run(n) ; o["C02_Wait"] = n
        n = Memory_Fence() ; r.run(n) ; o["Memory_Fence"] = n
        n = Ports_Utilization() ; r.run(n) ; o["Ports_Utilization"] = n
        n = Ports_Utilized_0() ; r.run(n) ; o["Ports_Utilized_0"] = n
        n = Mixing_Vectors() ; r.run(n) ; o["Mixing_Vectors"] = n
        n = Ports_Utilized_1() ; r.run(n) ; o["Ports_Utilized_1"] = n
        n = Ports_Utilized_2() ; r.run(n) ; o["Ports_Utilized_2"] = n
        n = Ports_Utilized_3m() ; r.run(n) ; o["Ports_Utilized_3m"] = n
        n = ALU_Op_Utilization() ; r.run(n) ; o["ALU_Op_Utilization"] = n
        n = Port_0() ; r.run(n) ; o["Port_0"] = n
        n = Port_1() ; r.run(n) ; o["Port_1"] = n
        n = Port_6() ; r.run(n) ; o["Port_6"] = n
        n = Load_Op_Utilization() ; r.run(n) ; o["Load_Op_Utilization"] = n
        n = Store_Op_Utilization() ; r.run(n) ; o["Store_Op_Utilization"] = n
        n = Retiring() ; r.run(n) ; o["Retiring"] = n
        n = Light_Operations() ; r.run(n) ; o["Light_Operations"] = n
        n = FP_Arith() ; r.run(n) ; o["FP_Arith"] = n
        n = X87_Use() ; r.run(n) ; o["X87_Use"] = n
        n = FP_Scalar() ; r.run(n) ; o["FP_Scalar"] = n
        n = FP_Vector() ; r.run(n) ; o["FP_Vector"] = n
        n = FP_Vector_128b() ; r.run(n) ; o["FP_Vector_128b"] = n
        n = FP_Vector_256b() ; r.run(n) ; o["FP_Vector_256b"] = n
        n = Int_Operations() ; r.run(n) ; o["Int_Operations"] = n
        n = Int_Vector_128b() ; r.run(n) ; o["Int_Vector_128b"] = n
        n = Int_Vector_256b() ; r.run(n) ; o["Int_Vector_256b"] = n
        n = Memory_Operations() ; r.run(n) ; o["Memory_Operations"] = n
        n = Fused_Instructions() ; r.run(n) ; o["Fused_Instructions"] = n
        n = Non_Fused_Branches() ; r.run(n) ; o["Non_Fused_Branches"] = n
        n = Other_Light_Ops() ; r.run(n) ; o["Other_Light_Ops"] = n
        n = Nop_Instructions() ; r.run(n) ; o["Nop_Instructions"] = n
        n = Shuffles_256b() ; r.run(n) ; o["Shuffles_256b"] = n
        n = Heavy_Operations() ; r.run(n) ; o["Heavy_Operations"] = n
        n = Few_Uops_Instructions() ; r.run(n) ; o["Few_Uops_Instructions"] = n
        n = Microcode_Sequencer() ; r.run(n) ; o["Microcode_Sequencer"] = n
        n = Assists() ; r.run(n) ; o["Assists"] = n
        n = Page_Faults() ; r.run(n) ; o["Page_Faults"] = n
        n = FP_Assists() ; r.run(n) ; o["FP_Assists"] = n
        n = AVX_Assists() ; r.run(n) ; o["AVX_Assists"] = n
        n = CISC() ; r.run(n) ; o["CISC"] = n

        # parents

        o["Fetch_Latency"].parent = o["Frontend_Bound"]
        o["ICache_Misses"].parent = o["Fetch_Latency"]
        o["Code_L2_Hit"].parent = o["ICache_Misses"]
        o["Code_L2_Miss"].parent = o["ICache_Misses"]
        o["ITLB_Misses"].parent = o["Fetch_Latency"]
        o["Code_STLB_Hit"].parent = o["ITLB_Misses"]
        o["Code_STLB_Miss"].parent = o["ITLB_Misses"]
        o["Code_STLB_Miss_4K"].parent = o["Code_STLB_Miss"]
        o["Code_STLB_Miss_2M"].parent = o["Code_STLB_Miss"]
        o["Branch_Resteers"].parent = o["Fetch_Latency"]
        o["Mispredicts_Resteers"].parent = o["Branch_Resteers"]
        o["Clears_Resteers"].parent = o["Branch_Resteers"]
        o["Unknown_Branches"].parent = o["Branch_Resteers"]
        o["MS_Switches"].parent = o["Fetch_Latency"]
        o["LCP"].parent = o["Fetch_Latency"]
        o["DSB_Switches"].parent = o["Fetch_Latency"]
        o["Fetch_Bandwidth"].parent = o["Frontend_Bound"]
        o["MITE"].parent = o["Fetch_Bandwidth"]
        o["Decoder0_Alone"].parent = o["MITE"]
        o["DSB"].parent = o["Fetch_Bandwidth"]
        o["LSD"].parent = o["Fetch_Bandwidth"]
        o["MS"].parent = o["Fetch_Bandwidth"]
        o["Branch_Mispredicts"].parent = o["Bad_Speculation"]
        o["Cond_NT_Mispredicts"].parent = o["Branch_Mispredicts"]
        o["Cond_TK_Mispredicts"].parent = o["Branch_Mispredicts"]
        o["Ind_Call_Mispredicts"].parent = o["Branch_Mispredicts"]
        o["Ind_Jump_Mispredicts"].parent = o["Branch_Mispredicts"]
        o["Ret_Mispredicts"].parent = o["Branch_Mispredicts"]
        o["Other_Mispredicts"].parent = o["Branch_Mispredicts"]
        o["Machine_Clears"].parent = o["Bad_Speculation"]
        o["Other_Nukes"].parent = o["Machine_Clears"]
        o["Memory_Bound"].parent = o["Backend_Bound"]
        o["L1_Bound"].parent = o["Memory_Bound"]
        o["DTLB_Load"].parent = o["L1_Bound"]
        o["Load_STLB_Hit"].parent = o["DTLB_Load"]
        o["Load_STLB_Miss"].parent = o["DTLB_Load"]
        o["Load_STLB_Miss_4K"].parent = o["Load_STLB_Miss"]
        o["Load_STLB_Miss_2M"].parent = o["Load_STLB_Miss"]
        o["Load_STLB_Miss_1G"].parent = o["Load_STLB_Miss"]
        o["Store_Fwd_Blk"].parent = o["L1_Bound"]
        o["L1_Latency_Dependency"].parent = o["L1_Bound"]
        o["Lock_Latency"].parent = o["L1_Bound"]
        o["Split_Loads"].parent = o["L1_Bound"]
        o["FB_Full"].parent = o["L1_Bound"]
        o["L2_Bound"].parent = o["Memory_Bound"]
        o["L2_Hit_Latency"].parent = o["L2_Bound"]
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
        o["Streaming_Stores"].parent = o["Store_Bound"]
        o["DTLB_Store"].parent = o["Store_Bound"]
        o["Store_STLB_Hit"].parent = o["DTLB_Store"]
        o["Store_STLB_Miss"].parent = o["DTLB_Store"]
        o["Store_STLB_Miss_4K"].parent = o["Store_STLB_Miss"]
        o["Store_STLB_Miss_2M"].parent = o["Store_STLB_Miss"]
        o["Store_STLB_Miss_1G"].parent = o["Store_STLB_Miss"]
        o["Core_Bound"].parent = o["Backend_Bound"]
        o["Divider"].parent = o["Core_Bound"]
        o["FP_Divider"].parent = o["Divider"]
        o["INT_Divider"].parent = o["Divider"]
        o["Serializing_Operation"].parent = o["Core_Bound"]
        o["Slow_Pause"].parent = o["Serializing_Operation"]
        o["C01_Wait"].parent = o["Serializing_Operation"]
        o["C02_Wait"].parent = o["Serializing_Operation"]
        o["Memory_Fence"].parent = o["Serializing_Operation"]
        o["Ports_Utilization"].parent = o["Core_Bound"]
        o["Ports_Utilized_0"].parent = o["Ports_Utilization"]
        o["Mixing_Vectors"].parent = o["Ports_Utilized_0"]
        o["Ports_Utilized_1"].parent = o["Ports_Utilization"]
        o["Ports_Utilized_2"].parent = o["Ports_Utilization"]
        o["Ports_Utilized_3m"].parent = o["Ports_Utilization"]
        o["ALU_Op_Utilization"].parent = o["Ports_Utilized_3m"]
        o["Port_0"].parent = o["ALU_Op_Utilization"]
        o["Port_1"].parent = o["ALU_Op_Utilization"]
        o["Port_6"].parent = o["ALU_Op_Utilization"]
        o["Load_Op_Utilization"].parent = o["Ports_Utilized_3m"]
        o["Store_Op_Utilization"].parent = o["Ports_Utilized_3m"]
        o["Light_Operations"].parent = o["Retiring"]
        o["FP_Arith"].parent = o["Light_Operations"]
        o["X87_Use"].parent = o["FP_Arith"]
        o["FP_Scalar"].parent = o["FP_Arith"]
        o["FP_Vector"].parent = o["FP_Arith"]
        o["FP_Vector_128b"].parent = o["FP_Vector"]
        o["FP_Vector_256b"].parent = o["FP_Vector"]
        o["Int_Operations"].parent = o["Light_Operations"]
        o["Int_Vector_128b"].parent = o["Int_Operations"]
        o["Int_Vector_256b"].parent = o["Int_Operations"]
        o["Memory_Operations"].parent = o["Light_Operations"]
        o["Fused_Instructions"].parent = o["Light_Operations"]
        o["Non_Fused_Branches"].parent = o["Light_Operations"]
        o["Other_Light_Ops"].parent = o["Light_Operations"]
        o["Nop_Instructions"].parent = o["Other_Light_Ops"]
        o["Shuffles_256b"].parent = o["Other_Light_Ops"]
        o["Heavy_Operations"].parent = o["Retiring"]
        o["Few_Uops_Instructions"].parent = o["Heavy_Operations"]
        o["Microcode_Sequencer"].parent = o["Heavy_Operations"]
        o["Assists"].parent = o["Microcode_Sequencer"]
        o["Page_Faults"].parent = o["Assists"]
        o["FP_Assists"].parent = o["Assists"]
        o["AVX_Assists"].parent = o["Assists"]
        o["CISC"].parent = o["Microcode_Sequencer"]

        # user visible metrics

        n = Metric_Mispredictions() ; r.metric(n) ; o["Mispredictions"] = n
        n = Metric_Big_Code() ; r.metric(n) ; o["Big_Code"] = n
        n = Metric_Instruction_Fetch_BW() ; r.metric(n) ; o["Instruction_Fetch_BW"] = n
        n = Metric_Cache_Memory_Bandwidth() ; r.metric(n) ; o["Cache_Memory_Bandwidth"] = n
        n = Metric_Cache_Memory_Latency() ; r.metric(n) ; o["Cache_Memory_Latency"] = n
        n = Metric_Memory_Data_TLBs() ; r.metric(n) ; o["Memory_Data_TLBs"] = n
        n = Metric_Memory_Synchronization() ; r.metric(n) ; o["Memory_Synchronization"] = n
        n = Metric_Compute_Bound_Est() ; r.metric(n) ; o["Compute_Bound_Est"] = n
        n = Metric_Irregular_Overhead() ; r.metric(n) ; o["Irregular_Overhead"] = n
        n = Metric_Other_Bottlenecks() ; r.metric(n) ; o["Other_Bottlenecks"] = n
        n = Metric_Branching_Overhead() ; r.metric(n) ; o["Branching_Overhead"] = n
        n = Metric_Useful_Work() ; r.metric(n) ; o["Useful_Work"] = n
        n = Metric_Core_Bound_Likely() ; r.metric(n) ; o["Core_Bound_Likely"] = n
        n = Metric_IPC() ; r.metric(n) ; o["IPC"] = n
        n = Metric_UopPI() ; r.metric(n) ; o["UopPI"] = n
        n = Metric_UpTB() ; r.metric(n) ; o["UpTB"] = n
        n = Metric_CPI() ; r.metric(n) ; o["CPI"] = n
        n = Metric_CLKS() ; r.metric(n) ; o["CLKS"] = n
        n = Metric_SLOTS() ; r.metric(n) ; o["SLOTS"] = n
        n = Metric_Slots_Utilization() ; r.metric(n) ; o["Slots_Utilization"] = n
        n = Metric_Execute_per_Issue() ; r.metric(n) ; o["Execute_per_Issue"] = n
        n = Metric_CoreIPC() ; r.metric(n) ; o["CoreIPC"] = n
        n = Metric_FLOPc() ; r.metric(n) ; o["FLOPc"] = n
        n = Metric_FP_Arith_Utilization() ; r.metric(n) ; o["FP_Arith_Utilization"] = n
        n = Metric_ILP() ; r.metric(n) ; o["ILP"] = n
        n = Metric_EPC() ; r.metric(n) ; o["EPC"] = n
        n = Metric_CORE_CLKS() ; r.metric(n) ; o["CORE_CLKS"] = n
        n = Metric_IpLoad() ; r.metric(n) ; o["IpLoad"] = n
        n = Metric_IpStore() ; r.metric(n) ; o["IpStore"] = n
        n = Metric_IpBranch() ; r.metric(n) ; o["IpBranch"] = n
        n = Metric_IpCall() ; r.metric(n) ; o["IpCall"] = n
        n = Metric_IpTB() ; r.metric(n) ; o["IpTB"] = n
        n = Metric_BpTkBranch() ; r.metric(n) ; o["BpTkBranch"] = n
        n = Metric_IpFLOP() ; r.metric(n) ; o["IpFLOP"] = n
        n = Metric_IpArith() ; r.metric(n) ; o["IpArith"] = n
        n = Metric_IpArith_Scalar_SP() ; r.metric(n) ; o["IpArith_Scalar_SP"] = n
        n = Metric_IpArith_Scalar_DP() ; r.metric(n) ; o["IpArith_Scalar_DP"] = n
        n = Metric_IpArith_AVX128() ; r.metric(n) ; o["IpArith_AVX128"] = n
        n = Metric_IpArith_AVX256() ; r.metric(n) ; o["IpArith_AVX256"] = n
        n = Metric_IpPause() ; r.metric(n) ; o["IpPause"] = n
        n = Metric_IpSWPF() ; r.metric(n) ; o["IpSWPF"] = n
        n = Metric_Instructions() ; r.metric(n) ; o["Instructions"] = n
        n = Metric_Retire() ; r.metric(n) ; o["Retire"] = n
        n = Metric_Strings_Cycles() ; r.metric(n) ; o["Strings_Cycles"] = n
        n = Metric_IpAssist() ; r.metric(n) ; o["IpAssist"] = n
        n = Metric_Execute() ; r.metric(n) ; o["Execute"] = n
        n = Metric_Fetch_LSD() ; r.metric(n) ; o["Fetch_LSD"] = n
        n = Metric_Fetch_DSB() ; r.metric(n) ; o["Fetch_DSB"] = n
        n = Metric_Fetch_MITE() ; r.metric(n) ; o["Fetch_MITE"] = n
        n = Metric_Fetch_UpC() ; r.metric(n) ; o["Fetch_UpC"] = n
        n = Metric_LSD_Coverage() ; r.metric(n) ; o["LSD_Coverage"] = n
        n = Metric_DSB_Coverage() ; r.metric(n) ; o["DSB_Coverage"] = n
        n = Metric_Unknown_Branch_Cost() ; r.metric(n) ; o["Unknown_Branch_Cost"] = n
        n = Metric_DSB_Switch_Cost() ; r.metric(n) ; o["DSB_Switch_Cost"] = n
        n = Metric_TBpC() ; r.metric(n) ; o["TBpC"] = n
        n = Metric_DSB_Misses() ; r.metric(n) ; o["DSB_Misses"] = n
        n = Metric_DSB_Bandwidth() ; r.metric(n) ; o["DSB_Bandwidth"] = n
        n = Metric_DSB_Switches_Ret() ; r.metric(n) ; o["DSB_Switches_Ret"] = n
        n = Metric_MS_Latency_Ret() ; r.metric(n) ; o["MS_Latency_Ret"] = n
        n = Metric_Unknown_Branches_Ret() ; r.metric(n) ; o["Unknown_Branches_Ret"] = n
        n = Metric_ICache_Miss_Latency() ; r.metric(n) ; o["ICache_Miss_Latency"] = n
        n = Metric_IC_Misses() ; r.metric(n) ; o["IC_Misses"] = n
        n = Metric_IpDSB_Miss_Ret() ; r.metric(n) ; o["IpDSB_Miss_Ret"] = n
        n = Metric_IpUnknown_Branch() ; r.metric(n) ; o["IpUnknown_Branch"] = n
        n = Metric_L2MPKI_Code() ; r.metric(n) ; o["L2MPKI_Code"] = n
        n = Metric_L2MPKI_Code_All() ; r.metric(n) ; o["L2MPKI_Code_All"] = n
        n = Metric_IpMispredict() ; r.metric(n) ; o["IpMispredict"] = n
        n = Metric_IpMisp_Cond_Ntaken() ; r.metric(n) ; o["IpMisp_Cond_Ntaken"] = n
        n = Metric_IpMisp_Cond_Taken() ; r.metric(n) ; o["IpMisp_Cond_Taken"] = n
        n = Metric_IpMisp_Ret() ; r.metric(n) ; o["IpMisp_Ret"] = n
        n = Metric_IpMisp_Indirect() ; r.metric(n) ; o["IpMisp_Indirect"] = n
        n = Metric_Branch_Misprediction_Cost() ; r.metric(n) ; o["Branch_Misprediction_Cost"] = n
        n = Metric_Spec_Clears_Ratio() ; r.metric(n) ; o["Spec_Clears_Ratio"] = n
        n = Metric_Cond_NT() ; r.metric(n) ; o["Cond_NT"] = n
        n = Metric_Cond_TK() ; r.metric(n) ; o["Cond_TK"] = n
        n = Metric_CallRet() ; r.metric(n) ; o["CallRet"] = n
        n = Metric_Jump() ; r.metric(n) ; o["Jump"] = n
        n = Metric_Other_Branches() ; r.metric(n) ; o["Other_Branches"] = n
        n = Metric_Load_Miss_Real_Latency() ; r.metric(n) ; o["Load_Miss_Real_Latency"] = n
        n = Metric_MLP() ; r.metric(n) ; o["MLP"] = n
        n = Metric_L1MPKI() ; r.metric(n) ; o["L1MPKI"] = n
        n = Metric_L1MPKI_Load() ; r.metric(n) ; o["L1MPKI_Load"] = n
        n = Metric_L2MPKI() ; r.metric(n) ; o["L2MPKI"] = n
        n = Metric_L2MPKI_All() ; r.metric(n) ; o["L2MPKI_All"] = n
        n = Metric_L2MPKI_Load() ; r.metric(n) ; o["L2MPKI_Load"] = n
        n = Metric_L2MPKI_RFO() ; r.metric(n) ; o["L2MPKI_RFO"] = n
        n = Metric_L2HPKI_All() ; r.metric(n) ; o["L2HPKI_All"] = n
        n = Metric_L2HPKI_Load() ; r.metric(n) ; o["L2HPKI_Load"] = n
        n = Metric_L3MPKI() ; r.metric(n) ; o["L3MPKI"] = n
        n = Metric_FB_HPKI() ; r.metric(n) ; o["FB_HPKI"] = n
        n = Metric_L1D_Cache_Fill_BW() ; r.metric(n) ; o["L1D_Cache_Fill_BW"] = n
        n = Metric_L2_Cache_Fill_BW() ; r.metric(n) ; o["L2_Cache_Fill_BW"] = n
        n = Metric_L3_Cache_Fill_BW() ; r.metric(n) ; o["L3_Cache_Fill_BW"] = n
        n = Metric_L3_Cache_Access_BW() ; r.metric(n) ; o["L3_Cache_Access_BW"] = n
        n = Metric_Page_Walks_Utilization() ; r.metric(n) ; o["Page_Walks_Utilization"] = n
        n = Metric_Code_STLB_MPKI() ; r.metric(n) ; o["Code_STLB_MPKI"] = n
        n = Metric_Load_STLB_MPKI() ; r.metric(n) ; o["Load_STLB_MPKI"] = n
        n = Metric_Store_STLB_MPKI() ; r.metric(n) ; o["Store_STLB_MPKI"] = n
        n = Metric_Load_STLB_Miss_Ret() ; r.metric(n) ; o["Load_STLB_Miss_Ret"] = n
        n = Metric_Store_STLB_Miss_Ret() ; r.metric(n) ; o["Store_STLB_Miss_Ret"] = n
        n = Metric_L1D_Cache_Fill_BW_2T() ; r.metric(n) ; o["L1D_Cache_Fill_BW_2T"] = n
        n = Metric_L2_Cache_Fill_BW_2T() ; r.metric(n) ; o["L2_Cache_Fill_BW_2T"] = n
        n = Metric_L3_Cache_Fill_BW_2T() ; r.metric(n) ; o["L3_Cache_Fill_BW_2T"] = n
        n = Metric_L3_Cache_Access_BW_2T() ; r.metric(n) ; o["L3_Cache_Access_BW_2T"] = n
        n = Metric_Useless_HWPF() ; r.metric(n) ; o["Useless_HWPF"] = n
        n = Metric_Load_L2_Miss_Latency() ; r.metric(n) ; o["Load_L2_Miss_Latency"] = n
        n = Metric_Load_L3_Miss_Latency() ; r.metric(n) ; o["Load_L3_Miss_Latency"] = n
        n = Metric_Load_L2_MLP() ; r.metric(n) ; o["Load_L2_MLP"] = n
        n = Metric_Data_L2_MLP() ; r.metric(n) ; o["Data_L2_MLP"] = n
        n = Metric_UC_Load_PKI() ; r.metric(n) ; o["UC_Load_PKI"] = n
        n = Metric_Bus_Lock_PKI() ; r.metric(n) ; o["Bus_Lock_PKI"] = n
        n = Metric_CPU_Utilization() ; r.metric(n) ; o["CPU_Utilization"] = n
        n = Metric_CPUs_Utilized() ; r.metric(n) ; o["CPUs_Utilized"] = n
        n = Metric_Core_Frequency() ; r.metric(n) ; o["Core_Frequency"] = n
        n = Metric_GFLOPs() ; r.metric(n) ; o["GFLOPs"] = n
        n = Metric_Turbo_Utilization() ; r.metric(n) ; o["Turbo_Utilization"] = n
        n = Metric_SMT_2T_Utilization() ; r.metric(n) ; o["SMT_2T_Utilization"] = n
        n = Metric_Kernel_Utilization() ; r.metric(n) ; o["Kernel_Utilization"] = n
        n = Metric_Kernel_CPI() ; r.metric(n) ; o["Kernel_CPI"] = n
        n = Metric_C0_Wait() ; r.metric(n) ; o["C0_Wait"] = n
        n = Metric_DRAM_BW_Use() ; r.metric(n) ; o["DRAM_BW_Use"] = n
        n = Metric_MEM_Parallel_Reads() ; r.metric(n) ; o["MEM_Parallel_Reads"] = n
        n = Metric_Power() ; r.metric(n) ; o["Power"] = n
        n = Metric_Time() ; r.metric(n) ; o["Time"] = n
        n = Metric_Socket_CLKS() ; r.metric(n) ; o["Socket_CLKS"] = n
        n = Metric_IpFarBranch() ; r.metric(n) ; o["IpFarBranch"] = n

        # references between groups

        o["Code_L2_Hit"].Code_L2_Miss = o["Code_L2_Miss"]
        o["Code_STLB_Hit"].Code_STLB_Miss = o["Code_STLB_Miss"]
        o["Branch_Resteers"].Unknown_Branches = o["Unknown_Branches"]
        o["Mispredicts_Resteers"].Backend_Bound = o["Backend_Bound"]
        o["Mispredicts_Resteers"].Retiring = o["Retiring"]
        o["Mispredicts_Resteers"].Branch_Mispredicts = o["Branch_Mispredicts"]
        o["Mispredicts_Resteers"].Bad_Speculation = o["Bad_Speculation"]
        o["Mispredicts_Resteers"].Frontend_Bound = o["Frontend_Bound"]
        o["Clears_Resteers"].Backend_Bound = o["Backend_Bound"]
        o["Clears_Resteers"].Retiring = o["Retiring"]
        o["Clears_Resteers"].Branch_Mispredicts = o["Branch_Mispredicts"]
        o["Clears_Resteers"].Bad_Speculation = o["Bad_Speculation"]
        o["Clears_Resteers"].Frontend_Bound = o["Frontend_Bound"]
        o["Fetch_Bandwidth"].Fetch_Latency = o["Fetch_Latency"]
        o["Fetch_Bandwidth"].Frontend_Bound = o["Frontend_Bound"]
        o["Bad_Speculation"].Backend_Bound = o["Backend_Bound"]
        o["Bad_Speculation"].Retiring = o["Retiring"]
        o["Bad_Speculation"].Frontend_Bound = o["Frontend_Bound"]
        o["Other_Mispredicts"].Branch_Mispredicts = o["Branch_Mispredicts"]
        o["Machine_Clears"].Backend_Bound = o["Backend_Bound"]
        o["Machine_Clears"].Retiring = o["Retiring"]
        o["Machine_Clears"].Bad_Speculation = o["Bad_Speculation"]
        o["Machine_Clears"].Frontend_Bound = o["Frontend_Bound"]
        o["Machine_Clears"].Branch_Mispredicts = o["Branch_Mispredicts"]
        o["Other_Nukes"].Backend_Bound = o["Backend_Bound"]
        o["Other_Nukes"].Retiring = o["Retiring"]
        o["Other_Nukes"].Branch_Mispredicts = o["Branch_Mispredicts"]
        o["Other_Nukes"].Machine_Clears = o["Machine_Clears"]
        o["Other_Nukes"].Bad_Speculation = o["Bad_Speculation"]
        o["Other_Nukes"].Frontend_Bound = o["Frontend_Bound"]
        o["DTLB_Load"].Load_STLB_Miss = o["Load_STLB_Miss"]
        o["Load_STLB_Hit"].DTLB_Load = o["DTLB_Load"]
        o["Load_STLB_Hit"].Load_STLB_Miss = o["Load_STLB_Miss"]
        o["Load_STLB_Miss_4K"].Load_STLB_Miss = o["Load_STLB_Miss"]
        o["Load_STLB_Miss_2M"].Load_STLB_Miss = o["Load_STLB_Miss"]
        o["Load_STLB_Miss_1G"].Load_STLB_Miss = o["Load_STLB_Miss"]
        o["MEM_Latency"].MEM_Bandwidth = o["MEM_Bandwidth"]
        o["DTLB_Store"].Store_STLB_Miss = o["Store_STLB_Miss"]
        o["Store_STLB_Hit"].Store_STLB_Miss = o["Store_STLB_Miss"]
        o["Store_STLB_Hit"].DTLB_Store = o["DTLB_Store"]
        o["Store_STLB_Miss_4K"].Store_STLB_Miss = o["Store_STLB_Miss"]
        o["Store_STLB_Miss_2M"].Store_STLB_Miss = o["Store_STLB_Miss"]
        o["Store_STLB_Miss_1G"].Store_STLB_Miss = o["Store_STLB_Miss"]
        o["Core_Bound"].Memory_Bound = o["Memory_Bound"]
        o["Core_Bound"].Backend_Bound = o["Backend_Bound"]
        o["INT_Divider"].Divider = o["Divider"]
        o["INT_Divider"].FP_Divider = o["FP_Divider"]
        o["Serializing_Operation"].C02_Wait = o["C02_Wait"]
        o["Ports_Utilization"].Retiring = o["Retiring"]
        o["Ports_Utilization"].Ports_Utilized_0 = o["Ports_Utilized_0"]
        o["Retiring"].Heavy_Operations = o["Heavy_Operations"]
        o["Light_Operations"].Heavy_Operations = o["Heavy_Operations"]
        o["Light_Operations"].Retiring = o["Retiring"]
        o["FP_Arith"].FP_Vector = o["FP_Vector"]
        o["FP_Arith"].Retiring = o["Retiring"]
        o["FP_Arith"].X87_Use = o["X87_Use"]
        o["FP_Arith"].FP_Scalar = o["FP_Scalar"]
        o["X87_Use"].Retiring = o["Retiring"]
        o["FP_Scalar"].Retiring = o["Retiring"]
        o["FP_Vector"].Retiring = o["Retiring"]
        o["FP_Vector_128b"].Retiring = o["Retiring"]
        o["FP_Vector_256b"].Retiring = o["Retiring"]
        o["Int_Operations"].Retiring = o["Retiring"]
        o["Int_Operations"].Int_Vector_256b = o["Int_Vector_256b"]
        o["Int_Operations"].Int_Vector_128b = o["Int_Vector_128b"]
        o["Int_Vector_128b"].Retiring = o["Retiring"]
        o["Int_Vector_256b"].Retiring = o["Retiring"]
        o["Memory_Operations"].Heavy_Operations = o["Heavy_Operations"]
        o["Memory_Operations"].Retiring = o["Retiring"]
        o["Memory_Operations"].Light_Operations = o["Light_Operations"]
        o["Fused_Instructions"].Heavy_Operations = o["Heavy_Operations"]
        o["Fused_Instructions"].Retiring = o["Retiring"]
        o["Fused_Instructions"].Light_Operations = o["Light_Operations"]
        o["Non_Fused_Branches"].Heavy_Operations = o["Heavy_Operations"]
        o["Non_Fused_Branches"].Retiring = o["Retiring"]
        o["Non_Fused_Branches"].Light_Operations = o["Light_Operations"]
        o["Other_Light_Ops"].FP_Vector = o["FP_Vector"]
        o["Other_Light_Ops"].X87_Use = o["X87_Use"]
        o["Other_Light_Ops"].Memory_Operations = o["Memory_Operations"]
        o["Other_Light_Ops"].FP_Arith = o["FP_Arith"]
        o["Other_Light_Ops"].FP_Scalar = o["FP_Scalar"]
        o["Other_Light_Ops"].Non_Fused_Branches = o["Non_Fused_Branches"]
        o["Other_Light_Ops"].Int_Operations = o["Int_Operations"]
        o["Other_Light_Ops"].Int_Vector_128b = o["Int_Vector_128b"]
        o["Other_Light_Ops"].Fused_Instructions = o["Fused_Instructions"]
        o["Other_Light_Ops"].Light_Operations = o["Light_Operations"]
        o["Other_Light_Ops"].Retiring = o["Retiring"]
        o["Other_Light_Ops"].Heavy_Operations = o["Heavy_Operations"]
        o["Other_Light_Ops"].Int_Vector_256b = o["Int_Vector_256b"]
        o["Nop_Instructions"].Heavy_Operations = o["Heavy_Operations"]
        o["Nop_Instructions"].Retiring = o["Retiring"]
        o["Nop_Instructions"].Light_Operations = o["Light_Operations"]
        o["Shuffles_256b"].Heavy_Operations = o["Heavy_Operations"]
        o["Shuffles_256b"].Retiring = o["Retiring"]
        o["Shuffles_256b"].Light_Operations = o["Light_Operations"]
        o["Few_Uops_Instructions"].Heavy_Operations = o["Heavy_Operations"]
        o["Few_Uops_Instructions"].Microcode_Sequencer = o["Microcode_Sequencer"]
        o["CISC"].Assists = o["Assists"]
        o["CISC"].Microcode_Sequencer = o["Microcode_Sequencer"]
        o["Mispredictions"].ITLB_Misses = o["ITLB_Misses"]
        o["Mispredictions"].Mispredicts_Resteers = o["Mispredicts_Resteers"]
        o["Mispredictions"].Unknown_Branches = o["Unknown_Branches"]
        o["Mispredictions"].Microcode_Sequencer = o["Microcode_Sequencer"]
        o["Mispredictions"].Backend_Bound = o["Backend_Bound"]
        o["Mispredictions"].Retiring = o["Retiring"]
        o["Mispredictions"].Branch_Resteers = o["Branch_Resteers"]
        o["Mispredictions"].DSB_Switches = o["DSB_Switches"]
        o["Mispredictions"].Bad_Speculation = o["Bad_Speculation"]
        o["Mispredictions"].Frontend_Bound = o["Frontend_Bound"]
        o["Mispredictions"].LCP = o["LCP"]
        o["Mispredictions"].ICache_Misses = o["ICache_Misses"]
        o["Mispredictions"].Other_Mispredicts = o["Other_Mispredicts"]
        o["Mispredictions"].MS_Switches = o["MS_Switches"]
        o["Mispredictions"].Fetch_Latency = o["Fetch_Latency"]
        o["Mispredictions"].Branch_Mispredicts = o["Branch_Mispredicts"]
        o["Big_Code"].ITLB_Misses = o["ITLB_Misses"]
        o["Big_Code"].Unknown_Branches = o["Unknown_Branches"]
        o["Big_Code"].Branch_Resteers = o["Branch_Resteers"]
        o["Big_Code"].DSB_Switches = o["DSB_Switches"]
        o["Big_Code"].LCP = o["LCP"]
        o["Big_Code"].ICache_Misses = o["ICache_Misses"]
        o["Big_Code"].MS_Switches = o["MS_Switches"]
        o["Big_Code"].Fetch_Latency = o["Fetch_Latency"]
        o["Instruction_Fetch_BW"].ITLB_Misses = o["ITLB_Misses"]
        o["Instruction_Fetch_BW"].LSD = o["LSD"]
        o["Instruction_Fetch_BW"].Other_Mispredicts = o["Other_Mispredicts"]
        o["Instruction_Fetch_BW"].MS_Switches = o["MS_Switches"]
        o["Instruction_Fetch_BW"].Unknown_Branches = o["Unknown_Branches"]
        o["Instruction_Fetch_BW"].Fetch_Bandwidth = o["Fetch_Bandwidth"]
        o["Instruction_Fetch_BW"].Branch_Resteers = o["Branch_Resteers"]
        o["Instruction_Fetch_BW"].DSB_Switches = o["DSB_Switches"]
        o["Instruction_Fetch_BW"].Clears_Resteers = o["Clears_Resteers"]
        o["Instruction_Fetch_BW"].LCP = o["LCP"]
        o["Instruction_Fetch_BW"].ICache_Misses = o["ICache_Misses"]
        o["Instruction_Fetch_BW"].Fetch_Latency = o["Fetch_Latency"]
        o["Instruction_Fetch_BW"].Microcode_Sequencer = o["Microcode_Sequencer"]
        o["Instruction_Fetch_BW"].Frontend_Bound = o["Frontend_Bound"]
        o["Instruction_Fetch_BW"].Bad_Speculation = o["Bad_Speculation"]
        o["Instruction_Fetch_BW"].MS = o["MS"]
        o["Instruction_Fetch_BW"].Mispredicts_Resteers = o["Mispredicts_Resteers"]
        o["Instruction_Fetch_BW"].Backend_Bound = o["Backend_Bound"]
        o["Instruction_Fetch_BW"].Retiring = o["Retiring"]
        o["Instruction_Fetch_BW"].DSB = o["DSB"]
        o["Instruction_Fetch_BW"].MITE = o["MITE"]
        o["Instruction_Fetch_BW"].Branch_Mispredicts = o["Branch_Mispredicts"]
        o["Cache_Memory_Bandwidth"].Split_Loads = o["Split_Loads"]
        o["Cache_Memory_Bandwidth"].Store_Bound = o["Store_Bound"]
        o["Cache_Memory_Bandwidth"].Lock_Latency = o["Lock_Latency"]
        o["Cache_Memory_Bandwidth"].Data_Sharing = o["Data_Sharing"]
        o["Cache_Memory_Bandwidth"].MEM_Bandwidth = o["MEM_Bandwidth"]
        o["Cache_Memory_Bandwidth"].L1_Bound = o["L1_Bound"]
        o["Cache_Memory_Bandwidth"].SQ_Full = o["SQ_Full"]
        o["Cache_Memory_Bandwidth"].DRAM_Bound = o["DRAM_Bound"]
        o["Cache_Memory_Bandwidth"].DTLB_Load = o["DTLB_Load"]
        o["Cache_Memory_Bandwidth"].FB_Full = o["FB_Full"]
        o["Cache_Memory_Bandwidth"].L2_Bound = o["L2_Bound"]
        o["Cache_Memory_Bandwidth"].L1_Latency_Dependency = o["L1_Latency_Dependency"]
        o["Cache_Memory_Bandwidth"].L3_Bound = o["L3_Bound"]
        o["Cache_Memory_Bandwidth"].Contested_Accesses = o["Contested_Accesses"]
        o["Cache_Memory_Bandwidth"].MEM_Latency = o["MEM_Latency"]
        o["Cache_Memory_Bandwidth"].L3_Hit_Latency = o["L3_Hit_Latency"]
        o["Cache_Memory_Bandwidth"].Store_Fwd_Blk = o["Store_Fwd_Blk"]
        o["Cache_Memory_Bandwidth"].Memory_Bound = o["Memory_Bound"]
        o["Cache_Memory_Bandwidth"].Load_STLB_Miss = o["Load_STLB_Miss"]
        o["Cache_Memory_Latency"].Split_Loads = o["Split_Loads"]
        o["Cache_Memory_Latency"].Split_Stores = o["Split_Stores"]
        o["Cache_Memory_Latency"].Store_Bound = o["Store_Bound"]
        o["Cache_Memory_Latency"].Lock_Latency = o["Lock_Latency"]
        o["Cache_Memory_Latency"].Data_Sharing = o["Data_Sharing"]
        o["Cache_Memory_Latency"].MEM_Bandwidth = o["MEM_Bandwidth"]
        o["Cache_Memory_Latency"].L1_Bound = o["L1_Bound"]
        o["Cache_Memory_Latency"].SQ_Full = o["SQ_Full"]
        o["Cache_Memory_Latency"].False_Sharing = o["False_Sharing"]
        o["Cache_Memory_Latency"].DRAM_Bound = o["DRAM_Bound"]
        o["Cache_Memory_Latency"].DTLB_Load = o["DTLB_Load"]
        o["Cache_Memory_Latency"].FB_Full = o["FB_Full"]
        o["Cache_Memory_Latency"].Store_Latency = o["Store_Latency"]
        o["Cache_Memory_Latency"].L2_Bound = o["L2_Bound"]
        o["Cache_Memory_Latency"].L1_Latency_Dependency = o["L1_Latency_Dependency"]
        o["Cache_Memory_Latency"].L3_Bound = o["L3_Bound"]
        o["Cache_Memory_Latency"].Contested_Accesses = o["Contested_Accesses"]
        o["Cache_Memory_Latency"].DTLB_Store = o["DTLB_Store"]
        o["Cache_Memory_Latency"].MEM_Latency = o["MEM_Latency"]
        o["Cache_Memory_Latency"].Store_STLB_Miss = o["Store_STLB_Miss"]
        o["Cache_Memory_Latency"].L3_Hit_Latency = o["L3_Hit_Latency"]
        o["Cache_Memory_Latency"].Store_Fwd_Blk = o["Store_Fwd_Blk"]
        o["Cache_Memory_Latency"].Memory_Bound = o["Memory_Bound"]
        o["Cache_Memory_Latency"].Streaming_Stores = o["Streaming_Stores"]
        o["Cache_Memory_Latency"].Load_STLB_Miss = o["Load_STLB_Miss"]
        o["Memory_Data_TLBs"].Split_Loads = o["Split_Loads"]
        o["Memory_Data_TLBs"].Split_Stores = o["Split_Stores"]
        o["Memory_Data_TLBs"].Store_Bound = o["Store_Bound"]
        o["Memory_Data_TLBs"].Lock_Latency = o["Lock_Latency"]
        o["Memory_Data_TLBs"].L1_Bound = o["L1_Bound"]
        o["Memory_Data_TLBs"].False_Sharing = o["False_Sharing"]
        o["Memory_Data_TLBs"].DRAM_Bound = o["DRAM_Bound"]
        o["Memory_Data_TLBs"].DTLB_Load = o["DTLB_Load"]
        o["Memory_Data_TLBs"].FB_Full = o["FB_Full"]
        o["Memory_Data_TLBs"].Store_Latency = o["Store_Latency"]
        o["Memory_Data_TLBs"].L2_Bound = o["L2_Bound"]
        o["Memory_Data_TLBs"].L1_Latency_Dependency = o["L1_Latency_Dependency"]
        o["Memory_Data_TLBs"].L3_Bound = o["L3_Bound"]
        o["Memory_Data_TLBs"].DTLB_Store = o["DTLB_Store"]
        o["Memory_Data_TLBs"].Store_STLB_Miss = o["Store_STLB_Miss"]
        o["Memory_Data_TLBs"].Store_Fwd_Blk = o["Store_Fwd_Blk"]
        o["Memory_Data_TLBs"].Memory_Bound = o["Memory_Bound"]
        o["Memory_Data_TLBs"].Streaming_Stores = o["Streaming_Stores"]
        o["Memory_Data_TLBs"].Load_STLB_Miss = o["Load_STLB_Miss"]
        o["Memory_Synchronization"].DRAM_Bound = o["DRAM_Bound"]
        o["Memory_Synchronization"].Split_Stores = o["Split_Stores"]
        o["Memory_Synchronization"].Store_Bound = o["Store_Bound"]
        o["Memory_Synchronization"].Store_Latency = o["Store_Latency"]
        o["Memory_Synchronization"].L2_Bound = o["L2_Bound"]
        o["Memory_Synchronization"].Frontend_Bound = o["Frontend_Bound"]
        o["Memory_Synchronization"].L3_Bound = o["L3_Bound"]
        o["Memory_Synchronization"].Machine_Clears = o["Machine_Clears"]
        o["Memory_Synchronization"].Data_Sharing = o["Data_Sharing"]
        o["Memory_Synchronization"].Bad_Speculation = o["Bad_Speculation"]
        o["Memory_Synchronization"].Contested_Accesses = o["Contested_Accesses"]
        o["Memory_Synchronization"].Other_Nukes = o["Other_Nukes"]
        o["Memory_Synchronization"].L1_Bound = o["L1_Bound"]
        o["Memory_Synchronization"].DTLB_Store = o["DTLB_Store"]
        o["Memory_Synchronization"].Backend_Bound = o["Backend_Bound"]
        o["Memory_Synchronization"].Retiring = o["Retiring"]
        o["Memory_Synchronization"].Store_STLB_Miss = o["Store_STLB_Miss"]
        o["Memory_Synchronization"].L3_Hit_Latency = o["L3_Hit_Latency"]
        o["Memory_Synchronization"].SQ_Full = o["SQ_Full"]
        o["Memory_Synchronization"].False_Sharing = o["False_Sharing"]
        o["Memory_Synchronization"].Memory_Bound = o["Memory_Bound"]
        o["Memory_Synchronization"].Streaming_Stores = o["Streaming_Stores"]
        o["Memory_Synchronization"].Branch_Mispredicts = o["Branch_Mispredicts"]
        o["Compute_Bound_Est"].Backend_Bound = o["Backend_Bound"]
        o["Compute_Bound_Est"].Retiring = o["Retiring"]
        o["Compute_Bound_Est"].Serializing_Operation = o["Serializing_Operation"]
        o["Compute_Bound_Est"].C02_Wait = o["C02_Wait"]
        o["Compute_Bound_Est"].Ports_Utilized_2 = o["Ports_Utilized_2"]
        o["Compute_Bound_Est"].Divider = o["Divider"]
        o["Compute_Bound_Est"].Ports_Utilization = o["Ports_Utilization"]
        o["Compute_Bound_Est"].Ports_Utilized_3m = o["Ports_Utilized_3m"]
        o["Compute_Bound_Est"].Ports_Utilized_0 = o["Ports_Utilized_0"]
        o["Compute_Bound_Est"].Memory_Bound = o["Memory_Bound"]
        o["Compute_Bound_Est"].Ports_Utilized_1 = o["Ports_Utilized_1"]
        o["Compute_Bound_Est"].Core_Bound = o["Core_Bound"]
        o["Irregular_Overhead"].ITLB_Misses = o["ITLB_Misses"]
        o["Irregular_Overhead"].Memory_Bound = o["Memory_Bound"]
        o["Irregular_Overhead"].Few_Uops_Instructions = o["Few_Uops_Instructions"]
        o["Irregular_Overhead"].Microcode_Sequencer = o["Microcode_Sequencer"]
        o["Irregular_Overhead"].Divider = o["Divider"]
        o["Irregular_Overhead"].LSD = o["LSD"]
        o["Irregular_Overhead"].Frontend_Bound = o["Frontend_Bound"]
        o["Irregular_Overhead"].Other_Mispredicts = o["Other_Mispredicts"]
        o["Irregular_Overhead"].MS_Switches = o["MS_Switches"]
        o["Irregular_Overhead"].Machine_Clears = o["Machine_Clears"]
        o["Irregular_Overhead"].Bad_Speculation = o["Bad_Speculation"]
        o["Irregular_Overhead"].MS = o["MS"]
        o["Irregular_Overhead"].Other_Nukes = o["Other_Nukes"]
        o["Irregular_Overhead"].Core_Bound = o["Core_Bound"]
        o["Irregular_Overhead"].Mispredicts_Resteers = o["Mispredicts_Resteers"]
        o["Irregular_Overhead"].Unknown_Branches = o["Unknown_Branches"]
        o["Irregular_Overhead"].Backend_Bound = o["Backend_Bound"]
        o["Irregular_Overhead"].Branch_Resteers = o["Branch_Resteers"]
        o["Irregular_Overhead"].Clears_Resteers = o["Clears_Resteers"]
        o["Irregular_Overhead"].Retiring = o["Retiring"]
        o["Irregular_Overhead"].DSB_Switches = o["DSB_Switches"]
        o["Irregular_Overhead"].Fetch_Bandwidth = o["Fetch_Bandwidth"]
        o["Irregular_Overhead"].DSB = o["DSB"]
        o["Irregular_Overhead"].Serializing_Operation = o["Serializing_Operation"]
        o["Irregular_Overhead"].C02_Wait = o["C02_Wait"]
        o["Irregular_Overhead"].Assists = o["Assists"]
        o["Irregular_Overhead"].MITE = o["MITE"]
        o["Irregular_Overhead"].LCP = o["LCP"]
        o["Irregular_Overhead"].Ports_Utilization = o["Ports_Utilization"]
        o["Irregular_Overhead"].Heavy_Operations = o["Heavy_Operations"]
        o["Irregular_Overhead"].ICache_Misses = o["ICache_Misses"]
        o["Irregular_Overhead"].Ports_Utilized_0 = o["Ports_Utilized_0"]
        o["Irregular_Overhead"].Fetch_Latency = o["Fetch_Latency"]
        o["Irregular_Overhead"].Branch_Mispredicts = o["Branch_Mispredicts"]
        o["Other_Bottlenecks"].Split_Stores = o["Split_Stores"]
        o["Other_Bottlenecks"].Divider = o["Divider"]
        o["Other_Bottlenecks"].LSD = o["LSD"]
        o["Other_Bottlenecks"].Other_Mispredicts = o["Other_Mispredicts"]
        o["Other_Bottlenecks"].MS_Switches = o["MS_Switches"]
        o["Other_Bottlenecks"].Data_Sharing = o["Data_Sharing"]
        o["Other_Bottlenecks"].MEM_Bandwidth = o["MEM_Bandwidth"]
        o["Other_Bottlenecks"].Core_Bound = o["Core_Bound"]
        o["Other_Bottlenecks"].L1_Bound = o["L1_Bound"]
        o["Other_Bottlenecks"].Unknown_Branches = o["Unknown_Branches"]
        o["Other_Bottlenecks"].Fetch_Bandwidth = o["Fetch_Bandwidth"]
        o["Other_Bottlenecks"].Clears_Resteers = o["Clears_Resteers"]
        o["Other_Bottlenecks"].Ports_Utilization = o["Ports_Utilization"]
        o["Other_Bottlenecks"].SQ_Full = o["SQ_Full"]
        o["Other_Bottlenecks"].False_Sharing = o["False_Sharing"]
        o["Other_Bottlenecks"].Fetch_Latency = o["Fetch_Latency"]
        o["Other_Bottlenecks"].DRAM_Bound = o["DRAM_Bound"]
        o["Other_Bottlenecks"].Microcode_Sequencer = o["Microcode_Sequencer"]
        o["Other_Bottlenecks"].L1_Latency_Dependency = o["L1_Latency_Dependency"]
        o["Other_Bottlenecks"].Other_Nukes = o["Other_Nukes"]
        o["Other_Bottlenecks"].Mispredicts_Resteers = o["Mispredicts_Resteers"]
        o["Other_Bottlenecks"].DTLB_Store = o["DTLB_Store"]
        o["Other_Bottlenecks"].Backend_Bound = o["Backend_Bound"]
        o["Other_Bottlenecks"].Retiring = o["Retiring"]
        o["Other_Bottlenecks"].Assists = o["Assists"]
        o["Other_Bottlenecks"].DSB = o["DSB"]
        o["Other_Bottlenecks"].MITE = o["MITE"]
        o["Other_Bottlenecks"].Store_Fwd_Blk = o["Store_Fwd_Blk"]
        o["Other_Bottlenecks"].Ports_Utilized_0 = o["Ports_Utilized_0"]
        o["Other_Bottlenecks"].C02_Wait = o["C02_Wait"]
        o["Other_Bottlenecks"].Memory_Bound = o["Memory_Bound"]
        o["Other_Bottlenecks"].Streaming_Stores = o["Streaming_Stores"]
        o["Other_Bottlenecks"].ITLB_Misses = o["ITLB_Misses"]
        o["Other_Bottlenecks"].Split_Loads = o["Split_Loads"]
        o["Other_Bottlenecks"].Store_Bound = o["Store_Bound"]
        o["Other_Bottlenecks"].Lock_Latency = o["Lock_Latency"]
        o["Other_Bottlenecks"].Ports_Utilized_3m = o["Ports_Utilized_3m"]
        o["Other_Bottlenecks"].Ports_Utilized_1 = o["Ports_Utilized_1"]
        o["Other_Bottlenecks"].Branch_Resteers = o["Branch_Resteers"]
        o["Other_Bottlenecks"].DSB_Switches = o["DSB_Switches"]
        o["Other_Bottlenecks"].Serializing_Operation = o["Serializing_Operation"]
        o["Other_Bottlenecks"].Ports_Utilized_2 = o["Ports_Utilized_2"]
        o["Other_Bottlenecks"].LCP = o["LCP"]
        o["Other_Bottlenecks"].ICache_Misses = o["ICache_Misses"]
        o["Other_Bottlenecks"].Few_Uops_Instructions = o["Few_Uops_Instructions"]
        o["Other_Bottlenecks"].DTLB_Load = o["DTLB_Load"]
        o["Other_Bottlenecks"].FB_Full = o["FB_Full"]
        o["Other_Bottlenecks"].Frontend_Bound = o["Frontend_Bound"]
        o["Other_Bottlenecks"].L2_Bound = o["L2_Bound"]
        o["Other_Bottlenecks"].Store_Latency = o["Store_Latency"]
        o["Other_Bottlenecks"].L3_Bound = o["L3_Bound"]
        o["Other_Bottlenecks"].Machine_Clears = o["Machine_Clears"]
        o["Other_Bottlenecks"].Bad_Speculation = o["Bad_Speculation"]
        o["Other_Bottlenecks"].MS = o["MS"]
        o["Other_Bottlenecks"].MEM_Latency = o["MEM_Latency"]
        o["Other_Bottlenecks"].Store_STLB_Miss = o["Store_STLB_Miss"]
        o["Other_Bottlenecks"].L3_Hit_Latency = o["L3_Hit_Latency"]
        o["Other_Bottlenecks"].Heavy_Operations = o["Heavy_Operations"]
        o["Other_Bottlenecks"].Contested_Accesses = o["Contested_Accesses"]
        o["Other_Bottlenecks"].Branch_Mispredicts = o["Branch_Mispredicts"]
        o["Other_Bottlenecks"].Load_STLB_Miss = o["Load_STLB_Miss"]
        o["Useful_Work"].Few_Uops_Instructions = o["Few_Uops_Instructions"]
        o["Useful_Work"].Heavy_Operations = o["Heavy_Operations"]
        o["Useful_Work"].Microcode_Sequencer = o["Microcode_Sequencer"]
        o["Useful_Work"].Retiring = o["Retiring"]
        o["Useful_Work"].Assists = o["Assists"]
        o["Core_Bound_Likely"].Ports_Utilization = o["Ports_Utilization"]
        o["Core_Bound_Likely"].Backend_Bound = o["Backend_Bound"]
        o["Core_Bound_Likely"].Retiring = o["Retiring"]
        o["Core_Bound_Likely"].Ports_Utilized_0 = o["Ports_Utilized_0"]
        o["Core_Bound_Likely"].Memory_Bound = o["Memory_Bound"]
        o["Core_Bound_Likely"].Core_Bound = o["Core_Bound"]
        o["UopPI"].Retiring = o["Retiring"]
        o["UpTB"].Retiring = o["Retiring"]
        o["Retire"].Retiring = o["Retiring"]
        o["DSB_Misses"].ITLB_Misses = o["ITLB_Misses"]
        o["DSB_Misses"].LSD = o["LSD"]
        o["DSB_Misses"].Frontend_Bound = o["Frontend_Bound"]
        o["DSB_Misses"].MS_Switches = o["MS_Switches"]
        o["DSB_Misses"].MS = o["MS"]
        o["DSB_Misses"].Unknown_Branches = o["Unknown_Branches"]
        o["DSB_Misses"].Fetch_Bandwidth = o["Fetch_Bandwidth"]
        o["DSB_Misses"].Branch_Resteers = o["Branch_Resteers"]
        o["DSB_Misses"].DSB_Switches = o["DSB_Switches"]
        o["DSB_Misses"].DSB = o["DSB"]
        o["DSB_Misses"].MITE = o["MITE"]
        o["DSB_Misses"].LCP = o["LCP"]
        o["DSB_Misses"].ICache_Misses = o["ICache_Misses"]
        o["DSB_Misses"].Fetch_Latency = o["Fetch_Latency"]
        o["DSB_Bandwidth"].MITE = o["MITE"]
        o["DSB_Bandwidth"].Fetch_Bandwidth = o["Fetch_Bandwidth"]
        o["DSB_Bandwidth"].Fetch_Latency = o["Fetch_Latency"]
        o["DSB_Bandwidth"].DSB = o["DSB"]
        o["DSB_Bandwidth"].MS = o["MS"]
        o["DSB_Bandwidth"].LSD = o["LSD"]
        o["DSB_Bandwidth"].Frontend_Bound = o["Frontend_Bound"]
        o["IC_Misses"].ITLB_Misses = o["ITLB_Misses"]
        o["IC_Misses"].LCP = o["LCP"]
        o["IC_Misses"].Unknown_Branches = o["Unknown_Branches"]
        o["IC_Misses"].ICache_Misses = o["ICache_Misses"]
        o["IC_Misses"].Branch_Resteers = o["Branch_Resteers"]
        o["IC_Misses"].DSB_Switches = o["DSB_Switches"]
        o["IC_Misses"].MS_Switches = o["MS_Switches"]
        o["IC_Misses"].Fetch_Latency = o["Fetch_Latency"]
        o["Branch_Misprediction_Cost"].ITLB_Misses = o["ITLB_Misses"]
        o["Branch_Misprediction_Cost"].Microcode_Sequencer = o["Microcode_Sequencer"]
        o["Branch_Misprediction_Cost"].Frontend_Bound = o["Frontend_Bound"]
        o["Branch_Misprediction_Cost"].Other_Mispredicts = o["Other_Mispredicts"]
        o["Branch_Misprediction_Cost"].MS_Switches = o["MS_Switches"]
        o["Branch_Misprediction_Cost"].Bad_Speculation = o["Bad_Speculation"]
        o["Branch_Misprediction_Cost"].Mispredicts_Resteers = o["Mispredicts_Resteers"]
        o["Branch_Misprediction_Cost"].Unknown_Branches = o["Unknown_Branches"]
        o["Branch_Misprediction_Cost"].Backend_Bound = o["Backend_Bound"]
        o["Branch_Misprediction_Cost"].Retiring = o["Retiring"]
        o["Branch_Misprediction_Cost"].Branch_Resteers = o["Branch_Resteers"]
        o["Branch_Misprediction_Cost"].DSB_Switches = o["DSB_Switches"]
        o["Branch_Misprediction_Cost"].LCP = o["LCP"]
        o["Branch_Misprediction_Cost"].ICache_Misses = o["ICache_Misses"]
        o["Branch_Misprediction_Cost"].Fetch_Latency = o["Fetch_Latency"]
        o["Branch_Misprediction_Cost"].Branch_Mispredicts = o["Branch_Mispredicts"]

        # siblings cross-tree

        o["Mispredicts_Resteers"].sibling = (o["Branch_Mispredicts"],)
        o["Clears_Resteers"].sibling = (o["MS_Switches"], o["Machine_Clears"], o["L1_Bound"], o["Microcode_Sequencer"],)
        o["MS_Switches"].sibling = (o["Clears_Resteers"], o["Machine_Clears"], o["L1_Bound"], o["Serializing_Operation"], o["Mixing_Vectors"], o["Microcode_Sequencer"],)
        o["LCP"].sibling = (o["DSB_Switches"], o["Fetch_Bandwidth"],)
        o["DSB_Switches"].sibling = (o["LCP"], o["Fetch_Bandwidth"],)
        o["Fetch_Bandwidth"].sibling = (o["LCP"], o["DSB_Switches"],)
        o["Decoder0_Alone"].sibling = (o["Few_Uops_Instructions"],)
        o["Branch_Mispredicts"].sibling = (o["Mispredicts_Resteers"],)
        o["Machine_Clears"].sibling = (o["Clears_Resteers"], o["MS_Switches"], o["L1_Bound"], o["Contested_Accesses"], o["Data_Sharing"], o["False_Sharing"], o["Microcode_Sequencer"],)
        o["L1_Bound"].sibling = (o["Clears_Resteers"], o["MS_Switches"], o["Machine_Clears"], o["Ports_Utilized_1"], o["Microcode_Sequencer"],)
        o["DTLB_Load"].sibling = (o["DTLB_Store"],)
        o["Lock_Latency"].sibling = (o["Store_Latency"],)
        o["FB_Full"].sibling = (o["SQ_Full"], o["MEM_Bandwidth"], o["Store_Latency"], o["Streaming_Stores"],)
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
        o["Streaming_Stores"].sibling = (o["FB_Full"],)
        o["DTLB_Store"].sibling = (o["DTLB_Load"],)
        o["Serializing_Operation"].sibling = (o["MS_Switches"],)
        o["Mixing_Vectors"].sibling = (o["MS_Switches"],)
        o["Ports_Utilized_1"].sibling = (o["L1_Bound"],)
        o["Ports_Utilized_2"].sibling = (o["Port_0"], o["Port_1"], o["Port_6"], o["FP_Scalar"], o["FP_Vector"], o["FP_Vector_128b"], o["FP_Vector_256b"], o["Int_Vector_128b"], o["Int_Vector_256b"],)
        o["Port_0"].sibling = (o["Ports_Utilized_2"], o["Port_1"], o["Port_6"], o["FP_Scalar"], o["FP_Vector"], o["FP_Vector_128b"], o["FP_Vector_256b"], o["Int_Vector_128b"], o["Int_Vector_256b"],)
        o["Port_1"].sibling = (o["Ports_Utilized_2"], o["Port_0"], o["Port_6"], o["FP_Scalar"], o["FP_Vector"], o["FP_Vector_128b"], o["FP_Vector_256b"], o["Int_Vector_128b"], o["Int_Vector_256b"],)
        o["Port_6"].sibling = (o["Ports_Utilized_2"], o["Port_0"], o["Port_1"], o["FP_Scalar"], o["FP_Vector"], o["FP_Vector_128b"], o["FP_Vector_256b"], o["Int_Vector_128b"], o["Int_Vector_256b"],)
        o["FP_Scalar"].sibling = (o["Ports_Utilized_2"], o["Port_0"], o["Port_1"], o["Port_6"], o["FP_Vector"], o["FP_Vector_128b"], o["FP_Vector_256b"], o["Int_Vector_128b"], o["Int_Vector_256b"],)
        o["FP_Vector"].sibling = (o["Ports_Utilized_2"], o["Port_0"], o["Port_1"], o["Port_6"], o["FP_Scalar"], o["FP_Vector_128b"], o["FP_Vector_256b"], o["Int_Vector_128b"], o["Int_Vector_256b"],)
        o["FP_Vector_128b"].sibling = (o["Ports_Utilized_2"], o["Port_0"], o["Port_1"], o["Port_6"], o["FP_Scalar"], o["FP_Vector"], o["FP_Vector_256b"], o["Int_Vector_128b"], o["Int_Vector_256b"],)
        o["FP_Vector_256b"].sibling = (o["Ports_Utilized_2"], o["Port_0"], o["Port_1"], o["Port_6"], o["FP_Scalar"], o["FP_Vector"], o["FP_Vector_128b"], o["Int_Vector_128b"], o["Int_Vector_256b"],)
        o["Int_Vector_128b"].sibling = (o["Ports_Utilized_2"], o["Port_0"], o["Port_1"], o["Port_6"], o["FP_Scalar"], o["FP_Vector"], o["FP_Vector_128b"], o["FP_Vector_256b"], o["Int_Vector_256b"],)
        o["Int_Vector_256b"].sibling = (o["Ports_Utilized_2"], o["Port_0"], o["Port_1"], o["Port_6"], o["FP_Scalar"], o["FP_Vector"], o["FP_Vector_128b"], o["FP_Vector_256b"], o["Int_Vector_128b"],)
        o["Few_Uops_Instructions"].sibling = (o["Decoder0_Alone"],)
        o["Microcode_Sequencer"].sibling = (o["Clears_Resteers"], o["MS_Switches"], o["Machine_Clears"], o["L1_Bound"],)
        o["Mispredictions"].sibling = (o["Mispredicts_Resteers"], o["Branch_Mispredicts"],)
        o["Cache_Memory_Bandwidth"].sibling = (o["FB_Full"], o["SQ_Full"], o["MEM_Bandwidth"],)
        o["Cache_Memory_Latency"].sibling = (o["L3_Hit_Latency"], o["MEM_Latency"],)
        o["Memory_Data_TLBs"].sibling = (o["DTLB_Load"], o["DTLB_Store"],)
        o["Memory_Synchronization"].sibling = (o["Machine_Clears"], o["Contested_Accesses"], o["Data_Sharing"], o["False_Sharing"],)
        o["Irregular_Overhead"].sibling = (o["MS_Switches"], o["Microcode_Sequencer"],)
        o["IpTB"].sibling = (o["LCP"], o["DSB_Switches"], o["Fetch_Bandwidth"],)
        o["DSB_Coverage"].sibling = (o["LCP"], o["DSB_Switches"], o["Fetch_Bandwidth"],)
        o["DSB_Misses"].sibling = (o["LCP"], o["DSB_Switches"], o["Fetch_Bandwidth"],)
        o["DSB_Bandwidth"].sibling = (o["LCP"], o["DSB_Switches"], o["Fetch_Bandwidth"],)
        o["Branch_Misprediction_Cost"].sibling = (o["Mispredicts_Resteers"], o["Branch_Mispredicts"],)
        o["DRAM_BW_Use"].sibling = (o["FB_Full"], o["SQ_Full"], o["MEM_Bandwidth"],)
