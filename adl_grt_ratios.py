# -*- coding: latin-1 -*-
#
# auto generated TopDown/TMA 4 description for Intel 12th gen Core (code name Alderlake) with GraceMont
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
version = "4"
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

Pipeline_Width = 5

# Aux. formulas


def CLKS(self, EV, level):
    return EV("CPU_CLK_UNHALTED.CORE", level)

def SLOTS(self, EV, level):
    return Pipeline_Width * CLKS(self, EV, level)

# Percentage of time that retirement is stalled by the Memory Cluster due to a pipeline stall. See Info.Mem_Exec_Bound
def PCT_Mem_Exec_Bound_Cycles(self, EV, level):
    return 100 * EV("LD_HEAD.ANY_AT_RET", level) / CLKS(self, EV, level)

# Percentage of time that retirement is stalled due to an L1 miss. See Info.Load_Miss_Bound
def PCT_Load_Miss_Bound_Cycles(self, EV, level):
    return 100 * EV("MEM_BOUND_STALLS.LOAD", level) / CLKS(self, EV, level)

# Percentage of time that retirement is stalled due to a first level data TLB miss
def PCT_DTLB_Miss_Bound_Cycles(self, EV, level):
    return 100 *(EV("LD_HEAD.DTLB_MISS_AT_RET", level) + EV("LD_HEAD.PGWALK_AT_RET", level)) / CLKS(self, EV, level)

# Percentage of time that allocation and retirement is stalled by the Frontend Cluster due to an Ifetch Miss, either Icache or ITLB Miss. See Info.Ifetch_Bound
def PCT_IFetch_Miss_Bound_Cycles(self, EV, level):
    return 100 * EV("MEM_BOUND_STALLS.IFETCH", level) / CLKS(self, EV, level)

# Instructions Per Cycle
def IPC(self, EV, level):
    return EV("INST_RETIRED.ANY", level) / CLKS(self, EV, level)

# Cycles Per Instruction
def CPI(self, EV, level):
    return CLKS(self, EV, level) / EV("INST_RETIRED.ANY", level)

# Uops Per Instruction
def UPI(self, EV, level):
    return EV("UOPS_RETIRED.ALL", level) / EV("INST_RETIRED.ANY", level)

# Instructions per Branch (lower number means higher occurrence rate)
def IpBranch(self, EV, level):
    return EV("INST_RETIRED.ANY", level) / EV("BR_INST_RETIRED.ALL_BRANCHES", level)

# Instruction per (near) call (lower number means higher occurrence rate)
def IpCall(self, EV, level):
    return EV("INST_RETIRED.ANY", level) / EV("BR_INST_RETIRED.CALL", level)

# Instructions per Far Branch ( Far Branches apply upon transition from application to operating system, handling interrupts, exceptions) [lower number means higher occurrence rate]
def IpFarBranch(self, EV, level):
    return EV("INST_RETIRED.ANY", level) / EV("BR_INST_RETIRED.FAR_BRANCH:USER", level)

# Instructions per retired Branch Misprediction
def IpMispredict(self, EV, level):
    return EV("INST_RETIRED.ANY", level) / EV("BR_MISP_RETIRED.ALL_BRANCHES", level)

# Instructions per retired conditional Branch Misprediction where the branch was not taken
def IpMisp_Cond_Ntaken(self, EV, level):
    return EV("INST_RETIRED.ANY", level) / (EV("BR_MISP_RETIRED.COND", level) - EV("BR_MISP_RETIRED.COND_TAKEN", level))

# Instructions per retired conditional Branch Misprediction where the branch was taken
def IpMisp_Cond_Taken(self, EV, level):
    return EV("INST_RETIRED.ANY", level) / EV("BR_MISP_RETIRED.COND_TAKEN", level)

# Instructions per retired return Branch Misprediction
def IpMisp_Ret(self, EV, level):
    return EV("INST_RETIRED.ANY", level) / EV("BR_MISP_RETIRED.RETURN", level)

# Instructions per retired indirect call or jump Branch Misprediction
def IpMisp_Indirect(self, EV, level):
    return EV("INST_RETIRED.ANY", level) / EV("BR_MISP_RETIRED.INDIRECT", level)

# Percentage of all uops which are microcode ops
def Microcode_Uop_Ratio(self, EV, level):
    return 100 * EV("UOPS_RETIRED.MS", level) / EV("UOPS_RETIRED.ALL", level)

# Percentage of all uops which are FPDiv uops
def FPDiv_Uop_Ratio(self, EV, level):
    return 100 * EV("UOPS_RETIRED.FPDIV", level) / EV("UOPS_RETIRED.ALL", level)

# Percentage of all uops which are IDiv uops
def IDiv_Uop_Ratio(self, EV, level):
    return 100 * EV("UOPS_RETIRED.IDIV", level) / EV("UOPS_RETIRED.ALL", level)

# Percentage of all uops which are x87 uops
def X87_Uop_Ratio(self, EV, level):
    return 100 * EV("UOPS_RETIRED.X87", level) / EV("UOPS_RETIRED.ALL", level)

# Instructions per Load
def IpLoad(self, EV, level):
    return EV("INST_RETIRED.ANY", level) / EV("MEM_UOPS_RETIRED.ALL_LOADS", level)

# Instructions per Store
def IpStore(self, EV, level):
    return EV("INST_RETIRED.ANY", level) / EV("MEM_UOPS_RETIRED.ALL_STORES", level)

# Ratio of mem load uops to all uops
def MemLoad_Ratio(self, EV, level):
    return 1000 * EV("MEM_UOPS_RETIRED.ALL_LOADS", level) / EV("UOPS_RETIRED.ALL", level)

# Percentage of total non-speculative loads that are splits
def Load_Splits_Ratio(self, EV, level):
    return 100 * EV("MEM_UOPS_RETIRED.SPLIT_LOADS", level) / EV("MEM_UOPS_RETIRED.ALL_LOADS", level)

# Percentage of total non-speculative loads that perform one or more locks
def Load_Locks_Ratio(self, EV, level):
    return 100 * EV("MEM_UOPS_RETIRED.LOCK_LOADS", level) / EV("MEM_UOPS_RETIRED.ALL_LOADS", level)

# Percentage of total non-speculative loads with a store forward or unknown store address block
def PCT_Loads_with_StoreFwdBlk(self, EV, level):
    return 100 * EV("LD_BLOCKS.DATA_UNKNOWN", level) / EV("MEM_UOPS_RETIRED.ALL_LOADS", level)

# Percentage of total non-speculative loads with an address aliasing block
def PCT_Loads_with_AdressAliasing(self, EV, level):
    return 100 * EV("LD_BLOCKS.4K_ALIAS", level) / EV("MEM_UOPS_RETIRED.ALL_LOADS", level)

# Percentage of Memory Execution Bound due to a second level TLB miss
def PCT_LoadHead_with_STLBHit(self, EV, level):
    return 100 * EV("LD_HEAD.DTLB_MISS_AT_RET", level) / EV("LD_HEAD.ANY_AT_RET", level)

# Percentage of Memory Execution Bound due to a pagewalk
def PCT_LoadHead_with_Pagewalk(self, EV, level):
    return 100 * EV("LD_HEAD.PGWALK_AT_RET", level) / EV("LD_HEAD.ANY_AT_RET", level)

# Percentage of Memory Execution Bound due to a store forward address match
def PCT_LoadHead_with_StoreFwding(self, EV, level):
    return 100 * EV("LD_HEAD.ST_ADDR_AT_RET", level) / EV("LD_HEAD.ANY_AT_RET", level)

# Percentage of Memory Execution Bound due to other block cases, such as pipeline conflicts, fences, etc
def PCT_LoadHead_with_OtherPipelineBlks(self, EV, level):
    return 100 * EV("LD_HEAD.OTHER_AT_RET", level) / EV("LD_HEAD.ANY_AT_RET", level)

# Percentage of Memory Execution Bound due to a first level data cache miss
def PCT_LoadHead_with_L1miss(self, EV, level):
    return 100 * EV("LD_HEAD.L1_MISS_AT_RET", level) / EV("LD_HEAD.ANY_AT_RET", level)

# Counts the number of cycles the core is stalled due to store buffer full
def Store_Bound(self, EV, level):
    return 100 *(EV("MEM_SCHEDULER_BLOCK.ST_BUF", level) / EV("MEM_SCHEDULER_BLOCK.ALL", level)) * (EV("TOPDOWN_BE_BOUND.MEM_SCHEDULER", level) / SLOTS(self, EV, level))

# Counts the number of cycles that the oldest load of the load buffer is stalled at retirement
def Load_Bound(self, EV, level):
    return 100 *(EV("LD_HEAD.L1_BOUND_AT_RET", level) + EV("MEM_BOUND_STALLS.LOAD", level)) / CLKS(self, EV, level)

# Counts the number of cycles that the oldest load of the load buffer is stalled at retirement due to a pipeline block
def L1_Bound(self, EV, level):
    return 100 * EV("LD_HEAD.L1_BOUND_AT_RET", level) / CLKS(self, EV, level)

# Percentage of memory bound stalls where retirement is stalled due to an L1 miss that hit the L2
def PCT_LoadMissBound_with_L2Hit(self, EV, level):
    return 100 * EV("MEM_BOUND_STALLS.LOAD_L2_HIT", level) / EV("MEM_BOUND_STALLS.LOAD", level)

# Percentage of memory bound stalls where retirement is stalled due to an L1 miss that subsequently misses in the L2
def PCT_LoadMissBound_with_L2Miss(self, EV, level):
    return 100 *(EV("MEM_BOUND_STALLS.LOAD_LLC_HIT", level) + EV("MEM_BOUND_STALLS.LOAD_DRAM_HIT", level)) / EV("MEM_BOUND_STALLS.LOAD", level)

# Percentage of memory bound stalls where retirement is stalled due to an L1 miss that hit the L3
def PCT_LoadMissBound_with_L3Hit(self, EV, level):
    return 100 * EV("MEM_BOUND_STALLS.LOAD_LLC_HIT", level) / EV("MEM_BOUND_STALLS.LOAD", level)

# Percentage of memory bound stalls where retirement is stalled due to an L1 miss that subsequently misses the L3
def PCT_LoadMissBound_with_L3Miss(self, EV, level):
    return 100 * EV("MEM_BOUND_STALLS.LOAD_DRAM_HIT", level) / EV("MEM_BOUND_STALLS.LOAD", level)

# Percentage of ifetch miss bound stalls, where the ifetch miss hits in the L2
def PCT_IfetchMissBound_with_L2Hit(self, EV, level):
    return 100 * EV("MEM_BOUND_STALLS.IFETCH_L2_HIT", level) / EV("MEM_BOUND_STALLS.IFETCH", level)

# Percentage of ifetch miss bound stalls, where the ifetch miss doesn't hit in the L2
def PCT_IfetchMissBound_with_L2Miss(self, EV, level):
    return 100 *(EV("MEM_BOUND_STALLS.IFETCH_LLC_HIT", level) + EV("MEM_BOUND_STALLS.IFETCH_DRAM_HIT", level)) / EV("MEM_BOUND_STALLS.IFETCH", level)

# Percentage of ifetch miss bound stalls, where the ifetch miss hits in the L3
def PCT_IfetchMissBound_with_L3Hit(self, EV, level):
    return 100 * EV("MEM_BOUND_STALLS.IFETCH_LLC_HIT", level) / EV("MEM_BOUND_STALLS.IFETCH", level)

# Percentage of ifetch miss bound stalls, where the ifetch miss subsequently misses in the L3
def PCT_IfetchMissBound_with_L3Miss(self, EV, level):
    return 100 * EV("MEM_BOUND_STALLS.IFETCH_DRAM_HIT", level) / EV("MEM_BOUND_STALLS.IFETCH", level)

# Ratio of all branches which mispredict
def Branch_Mispredict_Ratio(self, EV, level):
    return EV("BR_MISP_RETIRED.ALL_BRANCHES", level) / EV("BR_INST_RETIRED.ALL_BRANCHES", level)

# Ratio between Mispredicted branches and unknown branches
def Branch_Mispredict_to_Unknown_Branch_Ratio(self, EV, level):
    return EV("BR_MISP_RETIRED.ALL_BRANCHES", level) / EV("BACLEARS.ANY", level)

# Counts the number of machine clears relative to thousands of instructions retired, due to memory disambiguation
def Machine_Clears_Disamb_PKI(self, EV, level):
    return 1000 * EV("MACHINE_CLEARS.DISAMBIGUATION", level) / EV("INST_RETIRED.ANY", level)

# Counts the number of machine clears relative to thousands of instructions retired, due to floating point assists
def Machine_Clears_FP_Assist_PKI(self, EV, level):
    return 1000 * EV("MACHINE_CLEARS.FP_ASSIST", level) / EV("INST_RETIRED.ANY", level)

# Counts the number of machine clears relative to thousands of instructions retired, due to memory ordering
def Machine_Clears_Monuke_PKI(self, EV, level):
    return 1000 * EV("MACHINE_CLEARS.MEMORY_ORDERING", level) / EV("INST_RETIRED.ANY", level)

# Counts the number of machine clears relative to thousands of instructions retired, due to page faults
def Machine_Clears_Page_Fault_PKI(self, EV, level):
    return 1000 * EV("MACHINE_CLEARS.PAGE_FAULT", level) / EV("INST_RETIRED.ANY", level)

# Counts the number of machine clears relative to thousands of instructions retired, due to memory renaming
def Machine_Clears_MRN_PKI(self, EV, level):
    return 1000 * EV("MACHINE_CLEARS.MRN_NUKE", level) / EV("INST_RETIRED.ANY", level)

# Counts the number of machine clears relative to thousands of instructions retired, due to self-modifying code
def Machine_Clears_SMC_PKI(self, EV, level):
    return 1000 * EV("MACHINE_CLEARS.SMC", level) / EV("INST_RETIRED.ANY", level)

# Percentage of time that allocation is stalled due to store buffer full
def PCT_Store_Buffer_Stall_Cycles(self, EV, level):
    return 100 * EV("MEM_SCHEDULER_BLOCK.ST_BUF", level) / CLKS(self, EV, level)

# Percentage of time that allocation is stalled due to load buffer full
def PCT_Load_Buffer_Stall_Cycles(self, EV, level):
    return 100 * EV("MEM_SCHEDULER_BLOCK.LD_BUF", level) / CLKS(self, EV, level)

# Percentage of time that allocation is stalled due to memory reservation stations full
def PCT_Mem_RSV_Stall_Cycles(self, EV, level):
    return 100 * EV("MEM_SCHEDULER_BLOCK.RSV", level) / CLKS(self, EV, level)

# Percentage of time that the core is stalled due to a TPAUSE or UMWAIT instruction 
def PCT_Tpause_Cycles(self, EV, level):
    return 100 * EV("SERIALIZATION.C01_MS_SCB", level) / SLOTS(self, EV, level)

# Average Frequency Utilization relative nominal frequency
def Turbo_Utilization(self, EV, level):
    return CLKS(self, EV, level) / EV("CPU_CLK_UNHALTED.REF_TSC", level)

# Fraction of cycles spent in Kernel mode
def Kernel_Utilization(self, EV, level):
    return EV("CPU_CLK_UNHALTED.CORE_P:sup", level) / CLKS(self, EV, level)

# Average CPU Utilization
def CPU_Utilization(self, EV, level):
    return EV("CPU_CLK_UNHALTED.REF_TSC", level) / EV("msr/tsc/", 0)

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
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_FE_BOUND.ALL", 1) / SLOTS(self, EV, 1)
            self.thresh = (self.val > 0.20)
        except ZeroDivisionError:
            handle_error(self, "Frontend_Bound zero division")
        return self.val
    desc = """
Counts the number of issue slots that were not consumed by
the backend due to frontend stalls."""


class IFetch_Latency:
    name = "IFetch_Latency"
    domain = "Slots"
    area = "FE"
    level = 2
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_FE_BOUND.FRONTEND_LATENCY", 2) / SLOTS(self, EV, 2)
            self.thresh = (self.val > 0.15) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "IFetch_Latency zero division")
        return self.val
    desc = """
Counts the number of issue slots that were not delivered by
the frontend due to frontend latency restrictions due to
icache misses, itlb misses, branch detection, and resteer
limitations."""


class ICache_Misses:
    name = "ICache_Misses"
    domain = "Slots"
    area = "FE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_FE_BOUND.ICACHE", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "ICache_Misses zero division")
        return self.val
    desc = """
Counts the number of issue slots that were not delivered by
the frontend due to instruction cache misses."""


class ITLB_Misses:
    name = "ITLB_Misses"
    domain = "Slots"
    area = "FE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_FE_BOUND.ITLB", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "ITLB_Misses zero division")
        return self.val
    desc = """
Counts the number of issue slots that were not delivered by
the frontend due to Instruction Table Lookaside Buffer
(ITLB) misses."""


class Branch_Detect:
    name = "Branch_Detect"
    domain = "Slots"
    area = "FE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_FE_BOUND.BRANCH_DETECT", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Branch_Detect zero division")
        return self.val
    desc = """
Counts the number of issue slots that were not delivered by
the frontend due to BACLEARS, which occurs when the Branch
Target Buffer (BTB) prediction or lack thereof, was
corrected by a later branch predictor in the frontend.
Includes BACLEARS due to all branch types including
conditional and unconditional jumps, returns, and indirect
branches."""


class Branch_Resteer:
    name = "Branch_Resteer"
    domain = "Slots"
    area = "FE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_FE_BOUND.BRANCH_RESTEER", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Branch_Resteer zero division")
        return self.val
    desc = """
Counts the number of issue slots that were not delivered by
the frontend due to BTCLEARS, which occurs when the Branch
Target Buffer (BTB) predicts a taken branch."""


class IFetch_Bandwidth:
    name = "IFetch_Bandwidth"
    domain = "Slots"
    area = "FE"
    level = 2
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_FE_BOUND.FRONTEND_BANDWIDTH", 2) / SLOTS(self, EV, 2)
            self.thresh = (self.val > 0.10) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "IFetch_Bandwidth zero division")
        return self.val
    desc = """
Counts the number of issue slots that were not delivered by
the frontend due to frontend bandwidth restrictions due to
decode, predecode, cisc, and other limitations."""


class Cisc:
    name = "Cisc"
    domain = "Slots"
    area = "FE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_FE_BOUND.CISC", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Cisc zero division")
        return self.val
    desc = """
Counts the number of issue slots that were not delivered by
the frontend due to the microcode sequencer (MS)."""


class Decode:
    name = "Decode"
    domain = "Slots"
    area = "FE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_FE_BOUND.DECODE", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Decode zero division")
        return self.val
    desc = """
Counts the number of issue slots that were not delivered by
the frontend due to decode stalls."""


class Predecode:
    name = "Predecode"
    domain = "Slots"
    area = "FE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_FE_BOUND.PREDECODE", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Predecode zero division")
        return self.val
    desc = """
Counts the number of issue slots that were not delivered by
the frontend due to wrong predecodes."""


class Other_FB:
    name = "Other_FB"
    domain = "Slots"
    area = "FE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_FE_BOUND.OTHER", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Other_FB zero division")
        return self.val
    desc = """
Counts the number of issue slots that were not delivered by
the frontend due to other common frontend stalls not
categorized."""


class Bad_Speculation:
    name = "Bad_Speculation"
    domain = "Slots"
    area = "BAD"
    level = 1
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = (SLOTS(self, EV, 1) - (EV("TOPDOWN_FE_BOUND.ALL", 1) + EV("TOPDOWN_BE_BOUND.ALL", 1) + EV("TOPDOWN_RETIRING.ALL", 1))) / SLOTS(self, EV, 1)
            self.thresh = (self.val > 0.15)
        except ZeroDivisionError:
            handle_error(self, "Bad_Speculation zero division")
        return self.val
    desc = """
Counts the total number of issue slots that were not
consumed by the backend because allocation is stalled due to
a mispredicted jump or a machine clear. Only issue slots
wasted due to fast nukes such as memory ordering nukes are
counted. Other nukes are not accounted for. Counts all issue
slots blocked during this recovery window including relevant
microcode flows and while uops are not yet available in the
instruction queue (IQ). Also includes the issue slots that
were consumed by the backend but were thrown away because
they were younger than the mispredict or machine clear."""


class Branch_Mispredicts:
    name = "Branch_Mispredicts"
    domain = "Slots"
    area = "BAD"
    level = 2
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_BAD_SPECULATION.MISPREDICT", 2) / SLOTS(self, EV, 2)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Branch_Mispredicts zero division")
        return self.val
    desc = """
Counts the number of issue slots that were not consumed by
the backend due to branch mispredicts"""


class Machine_Clears:
    name = "Machine_Clears"
    domain = "Slots"
    area = "BAD"
    level = 2
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_BAD_SPECULATION.MACHINE_CLEARS", 2) / SLOTS(self, EV, 2)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Machine_Clears zero division")
        return self.val
    desc = """
Counts the total number of issue slots that were not
consumed by the backend because allocation is stalled due to
a machine clear (nuke) of any kind including memory ordering
and memory disambiguation"""


class Nuke:
    name = "Nuke"
    domain = "Slots"
    area = "BAD"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_BAD_SPECULATION.NUKE", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Nuke zero division")
        return self.val
    desc = """
Counts the number of issue slots that were not consumed by
the backend due to a machine clear that requires the use of
microcode (slow nuke)"""


class Fast_Nuke:
    name = "Fast_Nuke"
    domain = "Slots"
    area = "BAD"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_BAD_SPECULATION.FASTNUKE", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.05) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Fast_Nuke zero division")
        return self.val
    desc = """
Counts the number of issue slots that were not consumed by
the backend due to a machine clear that does not require the
use of microcode, classified as a fast nuke, due to memory
ordering, memory disambiguation and memory renaming"""


class Backend_Bound:
    name = "Backend_Bound"
    domain = "Slots"
    area = "BE"
    level = 1
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_BE_BOUND.ALL", 1) / SLOTS(self, EV, 1)
            self.thresh = (self.val > 0.10)
        except ZeroDivisionError:
            handle_error(self, "Backend_Bound zero division")
        return self.val
    desc = """
Counts the total number of issue slots that were not
consumed by the backend due to backend stalls. Note that
uops must be available for consumption in order for this
event to count. If a uop is not available (IQ is empty),
this event will not count"""


class Core_Bound:
    name = "Core_Bound"
    domain = "Slots"
    area = "BE"
    level = 2
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_BE_BOUND.ALLOC_RESTRICTIONS", 2) / SLOTS(self, EV, 2)
            self.thresh = (self.val > 0.10) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Core_Bound zero division")
        return self.val
    desc = """
Counts the number of cycles due to backend bound stalls that
are bounded by core restrictions and not attributed to an
outstanding load or stores, or resource limitation"""


class Allocation_Restriction:
    name = "Allocation_Restriction"
    domain = "Slots"
    area = "BE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_BE_BOUND.ALLOC_RESTRICTIONS", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.10) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Allocation_Restriction zero division")
        return self.val
    desc = """
Counts the number of issue slots that were not consumed by
the backend due to certain allocation restrictions"""


class Resource_Bound:
    name = "Resource_Bound"
    domain = "Slots"
    area = "BE"
    level = 2
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = ((EV("TOPDOWN_BE_BOUND.ALL", 2) / SLOTS(self, EV, 2)) - self.Core_Bound.compute(EV))
            self.thresh = (self.val > 0.20) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Resource_Bound zero division")
        return self.val
    desc = """
Counts the number of cycles the core is stalled due to a
resource limitation"""


class Mem_Scheduler:
    name = "Mem_Scheduler"
    domain = "Slots"
    area = "BE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_BE_BOUND.MEM_SCHEDULER", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.10) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Mem_Scheduler zero division")
        return self.val
    desc = """
Counts the number of issue slots that were not consumed by
the backend due to memory reservation stalls in which a
scheduler is not able to accept uops"""


class Non_Mem_Scheduler:
    name = "Non_Mem_Scheduler"
    domain = "Slots"
    area = "BE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_BE_BOUND.NON_MEM_SCHEDULER", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.10) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Non_Mem_Scheduler zero division")
        return self.val
    desc = """
Counts the number of issue slots that were not consumed by
the backend due to IEC or FPC RAT stalls, which can be due
to FIQ or IEC reservation stalls in which the integer,
floating point or SIMD scheduler is not able to accept uops"""


class Register:
    name = "Register"
    domain = "Slots"
    area = "BE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_BE_BOUND.REGISTER", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.10) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Register zero division")
        return self.val
    desc = """
Counts the number of issue slots that were not consumed by
the backend due to the physical register file unable to
accept an entry (marble stalls)"""


class Reorder_Buffer:
    name = "Reorder_Buffer"
    domain = "Slots"
    area = "BE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_BE_BOUND.REORDER_BUFFER", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.10) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Reorder_Buffer zero division")
        return self.val
    desc = """
Counts the number of issue slots that were not consumed by
the backend due to the reorder buffer being full (ROB
stalls)"""


class Serialization:
    name = "Serialization"
    domain = "Slots"
    area = "BE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_BE_BOUND.SERIALIZATION", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.10) and self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Serialization zero division")
        return self.val
    desc = """
Counts the number of issue slots that were not consumed by
the backend due to scoreboards from the instruction queue
(IQ), jump execution unit (JEU), or microcode sequencer (MS)"""


class Retiring:
    name = "Retiring"
    domain = "Slots"
    area = "RET"
    level = 1
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    metricgroup = frozenset([])
    maxval = None
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_RETIRING.ALL", 1) / SLOTS(self, EV, 1)
            self.thresh = (self.val > 0.75)
        except ZeroDivisionError:
            handle_error(self, "Retiring zero division")
        return self.val
    desc = """
Counts the number of issue slots that result in retirement
slots"""


class Metric_PCT_Mem_Exec_Bound_Cycles:
    name = "PCT_Mem_Exec_Bound_Cycles"
    domain = "Cycles"
    maxval = 0
    errcount = 0
    area = "Info.Bottleneck"
    metricgroup = frozenset(['Mem_Exec'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = PCT_Mem_Exec_Bound_Cycles(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "PCT_Mem_Exec_Bound_Cycles zero division")
    desc = """
Percentage of time that retirement is stalled by the Memory
Cluster due to a pipeline stall. See Info.Mem_Exec_Bound"""


class Metric_PCT_Load_Miss_Bound_Cycles:
    name = "PCT_Load_Miss_Bound_Cycles"
    domain = "Cycles"
    maxval = 0
    errcount = 0
    area = "Info.Bottleneck"
    metricgroup = frozenset(['Load_Store_Miss'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = PCT_Load_Miss_Bound_Cycles(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "PCT_Load_Miss_Bound_Cycles zero division")
    desc = """
Percentage of time that retirement is stalled due to an L1
miss. See Info.Load_Miss_Bound"""


class Metric_PCT_DTLB_Miss_Bound_Cycles:
    name = "PCT_DTLB_Miss_Bound_Cycles"
    domain = "Cycles"
    maxval = 0
    errcount = 0
    area = "Info.Bottleneck"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = PCT_DTLB_Miss_Bound_Cycles(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "PCT_DTLB_Miss_Bound_Cycles zero division")
    desc = """
Percentage of time that retirement is stalled due to a first
level data TLB miss"""


class Metric_PCT_IFetch_Miss_Bound_Cycles:
    name = "PCT_IFetch_Miss_Bound_Cycles"
    domain = "Cycles"
    maxval = 0
    errcount = 0
    area = "Info.Bottleneck"
    metricgroup = frozenset(['Ifetch'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = PCT_IFetch_Miss_Bound_Cycles(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "PCT_IFetch_Miss_Bound_Cycles zero division")
    desc = """
Percentage of time that allocation and retirement is stalled
by the Frontend Cluster due to an Ifetch Miss, either Icache
or ITLB Miss. See Info.Ifetch_Bound"""


class Metric_IPC:
    name = "IPC"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Core"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IPC(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "IPC zero division")
    desc = """
Instructions Per Cycle"""


class Metric_CPI:
    name = "CPI"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Core"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = CPI(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "CPI zero division")
    desc = """
Cycles Per Instruction"""


class Metric_UPI:
    name = "UPI"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Core"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = UPI(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "UPI zero division")
    desc = """
Uops Per Instruction"""


class Metric_IpBranch:
    name = "IpBranch"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Br_Inst_Mix"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpBranch(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "IpBranch zero division")
    desc = """
Instructions per Branch (lower number means higher
occurrence rate)"""


class Metric_IpCall:
    name = "IpCall"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Br_Inst_Mix"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpCall(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "IpCall zero division")
    desc = """
Instruction per (near) call (lower number means higher
occurrence rate)"""


class Metric_IpFarBranch:
    name = "IpFarBranch"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Br_Inst_Mix"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpFarBranch(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "IpFarBranch zero division")
    desc = """
Instructions per Far Branch ( Far Branches apply upon
transition from application to operating system, handling
interrupts, exceptions) [lower number means higher
occurrence rate]"""


class Metric_IpMispredict:
    name = "IpMispredict"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Br_Inst_Mix"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpMispredict(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "IpMispredict zero division")
    desc = """
Instructions per retired Branch Misprediction"""


class Metric_IpMisp_Cond_Ntaken:
    name = "IpMisp_Cond_Ntaken"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Br_Inst_Mix"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpMisp_Cond_Ntaken(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "IpMisp_Cond_Ntaken zero division")
    desc = """
Instructions per retired conditional Branch Misprediction
where the branch was not taken"""


class Metric_IpMisp_Cond_Taken:
    name = "IpMisp_Cond_Taken"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Br_Inst_Mix"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpMisp_Cond_Taken(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "IpMisp_Cond_Taken zero division")
    desc = """
Instructions per retired conditional Branch Misprediction
where the branch was taken"""


class Metric_IpMisp_Ret:
    name = "IpMisp_Ret"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Br_Inst_Mix"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpMisp_Ret(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "IpMisp_Ret zero division")
    desc = """
Instructions per retired return Branch Misprediction"""


class Metric_IpMisp_Indirect:
    name = "IpMisp_Indirect"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Br_Inst_Mix"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpMisp_Indirect(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "IpMisp_Indirect zero division")
    desc = """
Instructions per retired indirect call or jump Branch
Misprediction"""


class Metric_Microcode_Uop_Ratio:
    name = "Microcode_Uop_Ratio"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Uop_Mix"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Microcode_Uop_Ratio(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Microcode_Uop_Ratio zero division")
    desc = """
Percentage of all uops which are microcode ops"""


class Metric_FPDiv_Uop_Ratio:
    name = "FPDiv_Uop_Ratio"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Uop_Mix"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = FPDiv_Uop_Ratio(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "FPDiv_Uop_Ratio zero division")
    desc = """
Percentage of all uops which are FPDiv uops"""


class Metric_IDiv_Uop_Ratio:
    name = "IDiv_Uop_Ratio"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Uop_Mix"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IDiv_Uop_Ratio(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "IDiv_Uop_Ratio zero division")
    desc = """
Percentage of all uops which are IDiv uops"""


class Metric_X87_Uop_Ratio:
    name = "X87_Uop_Ratio"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Uop_Mix"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = X87_Uop_Ratio(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "X87_Uop_Ratio zero division")
    desc = """
Percentage of all uops which are x87 uops"""


class Metric_IpLoad:
    name = "IpLoad"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Mem_Mix"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpLoad(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "IpLoad zero division")
    desc = """
Instructions per Load"""


class Metric_IpStore:
    name = "IpStore"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Mem_Mix"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpStore(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "IpStore zero division")
    desc = """
Instructions per Store"""


class Metric_MemLoad_Ratio:
    name = "MemLoad_Ratio"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Mem_Mix"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = MemLoad_Ratio(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "MemLoad_Ratio zero division")
    desc = """
Ratio of mem load uops to all uops"""


class Metric_Load_Splits_Ratio:
    name = "Load_Splits_Ratio"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Mem_Mix"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Load_Splits_Ratio(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Load_Splits_Ratio zero division")
    desc = """
Percentage of total non-speculative loads that are splits"""


class Metric_Load_Locks_Ratio:
    name = "Load_Locks_Ratio"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Mem_Mix"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Load_Locks_Ratio(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Load_Locks_Ratio zero division")
    desc = """
Percentage of total non-speculative loads that perform one
or more locks"""


class Metric_PCT_Loads_with_StoreFwdBlk:
    name = "PCT_Loads_with_StoreFwdBlk"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Mem_Exec_Blocks"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = PCT_Loads_with_StoreFwdBlk(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "PCT_Loads_with_StoreFwdBlk zero division")
    desc = """
Percentage of total non-speculative loads with a store
forward or unknown store address block"""


class Metric_PCT_Loads_with_AdressAliasing:
    name = "PCT_Loads_with_AdressAliasing"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Mem_Exec_Blocks"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = PCT_Loads_with_AdressAliasing(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "PCT_Loads_with_AdressAliasing zero division")
    desc = """
Percentage of total non-speculative loads with an address
aliasing block"""


class Metric_PCT_LoadHead_with_STLBHit:
    name = "PCT_LoadHead_with_STLBHit"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Mem_Exec_Bound"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = PCT_LoadHead_with_STLBHit(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "PCT_LoadHead_with_STLBHit zero division")
    desc = """
Percentage of Memory Execution Bound due to a second level
TLB miss"""


class Metric_PCT_LoadHead_with_Pagewalk:
    name = "PCT_LoadHead_with_Pagewalk"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Mem_Exec_Bound"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = PCT_LoadHead_with_Pagewalk(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "PCT_LoadHead_with_Pagewalk zero division")
    desc = """
Percentage of Memory Execution Bound due to a pagewalk"""


class Metric_PCT_LoadHead_with_StoreFwding:
    name = "PCT_LoadHead_with_StoreFwding"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Mem_Exec_Bound"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = PCT_LoadHead_with_StoreFwding(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "PCT_LoadHead_with_StoreFwding zero division")
    desc = """
Percentage of Memory Execution Bound due to a store forward
address match"""


class Metric_PCT_LoadHead_with_OtherPipelineBlks:
    name = "PCT_LoadHead_with_OtherPipelineBlks"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Mem_Exec_Bound"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = PCT_LoadHead_with_OtherPipelineBlks(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "PCT_LoadHead_with_OtherPipelineBlks zero division")
    desc = """
Percentage of Memory Execution Bound due to other block
cases, such as pipeline conflicts, fences, etc"""


class Metric_PCT_LoadHead_with_L1miss:
    name = "PCT_LoadHead_with_L1miss"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Mem_Exec_Bound"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = PCT_LoadHead_with_L1miss(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "PCT_LoadHead_with_L1miss zero division")
    desc = """
Percentage of Memory Execution Bound due to a first level
data cache miss"""


class Metric_Store_Bound:
    name = "Store_Bound"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Load_Store_Bound"
    metricgroup = frozenset(['load_store_bound'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Store_Bound(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Store_Bound zero division")
    desc = """
Counts the number of cycles the core is stalled due to store
buffer full"""


class Metric_Load_Bound:
    name = "Load_Bound"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Load_Store_Bound"
    metricgroup = frozenset(['load_store_bound'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Load_Bound(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Load_Bound zero division")
    desc = """
Counts the number of cycles that the oldest load of the load
buffer is stalled at retirement"""


class Metric_L1_Bound:
    name = "L1_Bound"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Load_Store_Bound"
    metricgroup = frozenset(['load_store_bound'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = L1_Bound(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "L1_Bound zero division")
    desc = """
Counts the number of cycles that the oldest load of the load
buffer is stalled at retirement due to a pipeline block"""


class Metric_PCT_LoadMissBound_with_L2Hit:
    name = "PCT_LoadMissBound_with_L2Hit"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Load_Miss_Bound"
    metricgroup = frozenset(['load_store_bound'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = PCT_LoadMissBound_with_L2Hit(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "PCT_LoadMissBound_with_L2Hit zero division")
    desc = """
Percentage of memory bound stalls where retirement is
stalled due to an L1 miss that hit the L2"""


class Metric_PCT_LoadMissBound_with_L2Miss:
    name = "PCT_LoadMissBound_with_L2Miss"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Load_Miss_Bound"
    metricgroup = frozenset(['load_store_bound'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = PCT_LoadMissBound_with_L2Miss(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "PCT_LoadMissBound_with_L2Miss zero division")
    desc = """
Percentage of memory bound stalls where retirement is
stalled due to an L1 miss that subsequently misses in the L2"""


class Metric_PCT_LoadMissBound_with_L3Hit:
    name = "PCT_LoadMissBound_with_L3Hit"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Load_Miss_Bound"
    metricgroup = frozenset(['load_store_bound'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = PCT_LoadMissBound_with_L3Hit(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "PCT_LoadMissBound_with_L3Hit zero division")
    desc = """
Percentage of memory bound stalls where retirement is
stalled due to an L1 miss that hit the L3"""


class Metric_PCT_LoadMissBound_with_L3Miss:
    name = "PCT_LoadMissBound_with_L3Miss"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Load_Miss_Bound"
    metricgroup = frozenset(['load_store_bound'])
    sibling = None

    def compute(self, EV):
        try:
            self.val = PCT_LoadMissBound_with_L3Miss(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "PCT_LoadMissBound_with_L3Miss zero division")
    desc = """
Percentage of memory bound stalls where retirement is
stalled due to an L1 miss that subsequently misses the L3"""


class Metric_PCT_IfetchMissBound_with_L2Hit:
    name = "PCT_IfetchMissBound_with_L2Hit"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Ifetch_Miss_Bound"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = PCT_IfetchMissBound_with_L2Hit(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "PCT_IfetchMissBound_with_L2Hit zero division")
    desc = """
Percentage of ifetch miss bound stalls, where the ifetch
miss hits in the L2"""


class Metric_PCT_IfetchMissBound_with_L2Miss:
    name = "PCT_IfetchMissBound_with_L2Miss"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Ifetch_Miss_Bound"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = PCT_IfetchMissBound_with_L2Miss(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "PCT_IfetchMissBound_with_L2Miss zero division")
    desc = """
Percentage of ifetch miss bound stalls, where the ifetch
miss doesn't hit in the L2"""


class Metric_PCT_IfetchMissBound_with_L3Hit:
    name = "PCT_IfetchMissBound_with_L3Hit"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Ifetch_Miss_Bound"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = PCT_IfetchMissBound_with_L3Hit(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "PCT_IfetchMissBound_with_L3Hit zero division")
    desc = """
Percentage of ifetch miss bound stalls, where the ifetch
miss hits in the L3"""


class Metric_PCT_IfetchMissBound_with_L3Miss:
    name = "PCT_IfetchMissBound_with_L3Miss"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Ifetch_Miss_Bound"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = PCT_IfetchMissBound_with_L3Miss(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "PCT_IfetchMissBound_with_L3Miss zero division")
    desc = """
Percentage of ifetch miss bound stalls, where the ifetch
miss subsequently misses in the L3"""


class Metric_Branch_Mispredict_Ratio:
    name = "Branch_Mispredict_Ratio"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Br_Mispredict_Bound"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Branch_Mispredict_Ratio(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Branch_Mispredict_Ratio zero division")
    desc = """
Ratio of all branches which mispredict"""


class Metric_Branch_Mispredict_to_Unknown_Branch_Ratio:
    name = "Branch_Mispredict_to_Unknown_Branch_Ratio"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Br_Mispredict_Bound"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Branch_Mispredict_to_Unknown_Branch_Ratio(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Branch_Mispredict_to_Unknown_Branch_Ratio zero division")
    desc = """
Ratio between Mispredicted branches and unknown branches"""


class Metric_Machine_Clears_Disamb_PKI:
    name = "Machine_Clears_Disamb_PKI"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Machine_Clear_Bound"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Machine_Clears_Disamb_PKI(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Machine_Clears_Disamb_PKI zero division")
    desc = """
Counts the number of machine clears relative to thousands of
instructions retired, due to memory disambiguation"""


class Metric_Machine_Clears_FP_Assist_PKI:
    name = "Machine_Clears_FP_Assist_PKI"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Machine_Clear_Bound"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Machine_Clears_FP_Assist_PKI(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Machine_Clears_FP_Assist_PKI zero division")
    desc = """
Counts the number of machine clears relative to thousands of
instructions retired, due to floating point assists"""


class Metric_Machine_Clears_Monuke_PKI:
    name = "Machine_Clears_Monuke_PKI"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Machine_Clear_Bound"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Machine_Clears_Monuke_PKI(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Machine_Clears_Monuke_PKI zero division")
    desc = """
Counts the number of machine clears relative to thousands of
instructions retired, due to memory ordering"""


class Metric_Machine_Clears_Page_Fault_PKI:
    name = "Machine_Clears_Page_Fault_PKI"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Machine_Clear_Bound"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Machine_Clears_Page_Fault_PKI(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Machine_Clears_Page_Fault_PKI zero division")
    desc = """
Counts the number of machine clears relative to thousands of
instructions retired, due to page faults"""


class Metric_Machine_Clears_MRN_PKI:
    name = "Machine_Clears_MRN_PKI"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Machine_Clear_Bound"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Machine_Clears_MRN_PKI(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Machine_Clears_MRN_PKI zero division")
    desc = """
Counts the number of machine clears relative to thousands of
instructions retired, due to memory renaming"""


class Metric_Machine_Clears_SMC_PKI:
    name = "Machine_Clears_SMC_PKI"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Machine_Clear_Bound"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Machine_Clears_SMC_PKI(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Machine_Clears_SMC_PKI zero division")
    desc = """
Counts the number of machine clears relative to thousands of
instructions retired, due to self-modifying code"""


class Metric_PCT_Store_Buffer_Stall_Cycles:
    name = "PCT_Store_Buffer_Stall_Cycles"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Buffer_Stalls"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = PCT_Store_Buffer_Stall_Cycles(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "PCT_Store_Buffer_Stall_Cycles zero division")
    desc = """
Percentage of time that allocation is stalled due to store
buffer full"""


class Metric_PCT_Load_Buffer_Stall_Cycles:
    name = "PCT_Load_Buffer_Stall_Cycles"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Buffer_Stalls"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = PCT_Load_Buffer_Stall_Cycles(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "PCT_Load_Buffer_Stall_Cycles zero division")
    desc = """
Percentage of time that allocation is stalled due to load
buffer full"""


class Metric_PCT_Mem_RSV_Stall_Cycles:
    name = "PCT_Mem_RSV_Stall_Cycles"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Buffer_Stalls"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = PCT_Mem_RSV_Stall_Cycles(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "PCT_Mem_RSV_Stall_Cycles zero division")
    desc = """
Percentage of time that allocation is stalled due to memory
reservation stations full"""


class Metric_PCT_Tpause_Cycles:
    name = "PCT_Tpause_Cycles"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.Serialization "
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = PCT_Tpause_Cycles(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "PCT_Tpause_Cycles zero division")
    desc = """
Percentage of time that the core is stalled due to a TPAUSE
or UMWAIT instruction"""


class Metric_Turbo_Utilization:
    name = "Turbo_Utilization"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.System"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Turbo_Utilization(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Turbo_Utilization zero division")
    desc = """
Average Frequency Utilization relative nominal frequency"""


class Metric_Kernel_Utilization:
    name = "Kernel_Utilization"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.System"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = Kernel_Utilization(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "Kernel_Utilization zero division")
    desc = """
Fraction of cycles spent in Kernel mode"""


class Metric_CPU_Utilization:
    name = "CPU_Utilization"
    domain = ""
    maxval = 0
    errcount = 0
    area = "Info.System"
    metricgroup = frozenset([])
    sibling = None

    def compute(self, EV):
        try:
            self.val = CPU_Utilization(self, EV, 0)
            self.thresh = True
        except ZeroDivisionError:
            handle_error_metric(self, "CPU_Utilization zero division")
    desc = """
Average CPU Utilization"""


# Schedule



class Setup:
    def __init__(self, r):
        o = dict()
        n = Frontend_Bound() ; r.run(n) ; o["Frontend_Bound"] = n
        n = IFetch_Latency() ; r.run(n) ; o["IFetch_Latency"] = n
        n = ICache_Misses() ; r.run(n) ; o["ICache_Misses"] = n
        n = ITLB_Misses() ; r.run(n) ; o["ITLB_Misses"] = n
        n = Branch_Detect() ; r.run(n) ; o["Branch_Detect"] = n
        n = Branch_Resteer() ; r.run(n) ; o["Branch_Resteer"] = n
        n = IFetch_Bandwidth() ; r.run(n) ; o["IFetch_Bandwidth"] = n
        n = Cisc() ; r.run(n) ; o["Cisc"] = n
        n = Decode() ; r.run(n) ; o["Decode"] = n
        n = Predecode() ; r.run(n) ; o["Predecode"] = n
        n = Other_FB() ; r.run(n) ; o["Other_FB"] = n
        n = Bad_Speculation() ; r.run(n) ; o["Bad_Speculation"] = n
        n = Branch_Mispredicts() ; r.run(n) ; o["Branch_Mispredicts"] = n
        n = Machine_Clears() ; r.run(n) ; o["Machine_Clears"] = n
        n = Nuke() ; r.run(n) ; o["Nuke"] = n
        n = Fast_Nuke() ; r.run(n) ; o["Fast_Nuke"] = n
        n = Backend_Bound() ; r.run(n) ; o["Backend_Bound"] = n
        n = Core_Bound() ; r.run(n) ; o["Core_Bound"] = n
        n = Allocation_Restriction() ; r.run(n) ; o["Allocation_Restriction"] = n
        n = Resource_Bound() ; r.run(n) ; o["Resource_Bound"] = n
        n = Mem_Scheduler() ; r.run(n) ; o["Mem_Scheduler"] = n
        n = Non_Mem_Scheduler() ; r.run(n) ; o["Non_Mem_Scheduler"] = n
        n = Register() ; r.run(n) ; o["Register"] = n
        n = Reorder_Buffer() ; r.run(n) ; o["Reorder_Buffer"] = n
        n = Serialization() ; r.run(n) ; o["Serialization"] = n
        n = Retiring() ; r.run(n) ; o["Retiring"] = n

        # parents

        o["IFetch_Latency"].parent = o["Frontend_Bound"]
        o["ICache_Misses"].parent = o["IFetch_Latency"]
        o["ITLB_Misses"].parent = o["IFetch_Latency"]
        o["Branch_Detect"].parent = o["IFetch_Latency"]
        o["Branch_Resteer"].parent = o["IFetch_Latency"]
        o["IFetch_Bandwidth"].parent = o["Frontend_Bound"]
        o["Cisc"].parent = o["IFetch_Bandwidth"]
        o["Decode"].parent = o["IFetch_Bandwidth"]
        o["Predecode"].parent = o["IFetch_Bandwidth"]
        o["Other_FB"].parent = o["IFetch_Bandwidth"]
        o["Branch_Mispredicts"].parent = o["Bad_Speculation"]
        o["Machine_Clears"].parent = o["Bad_Speculation"]
        o["Nuke"].parent = o["Machine_Clears"]
        o["Fast_Nuke"].parent = o["Machine_Clears"]
        o["Core_Bound"].parent = o["Backend_Bound"]
        o["Allocation_Restriction"].parent = o["Core_Bound"]
        o["Resource_Bound"].parent = o["Backend_Bound"]
        o["Mem_Scheduler"].parent = o["Resource_Bound"]
        o["Non_Mem_Scheduler"].parent = o["Resource_Bound"]
        o["Register"].parent = o["Resource_Bound"]
        o["Reorder_Buffer"].parent = o["Resource_Bound"]
        o["Serialization"].parent = o["Resource_Bound"]

        # user visible metrics

        n = Metric_PCT_Mem_Exec_Bound_Cycles() ; r.metric(n) ; o["PCT_Mem_Exec_Bound_Cycles"] = n
        n = Metric_PCT_Load_Miss_Bound_Cycles() ; r.metric(n) ; o["PCT_Load_Miss_Bound_Cycles"] = n
        n = Metric_PCT_DTLB_Miss_Bound_Cycles() ; r.metric(n) ; o["PCT_DTLB_Miss_Bound_Cycles"] = n
        n = Metric_PCT_IFetch_Miss_Bound_Cycles() ; r.metric(n) ; o["PCT_IFetch_Miss_Bound_Cycles"] = n
        n = Metric_IPC() ; r.metric(n) ; o["IPC"] = n
        n = Metric_CPI() ; r.metric(n) ; o["CPI"] = n
        n = Metric_UPI() ; r.metric(n) ; o["UPI"] = n
        n = Metric_IpBranch() ; r.metric(n) ; o["IpBranch"] = n
        n = Metric_IpCall() ; r.metric(n) ; o["IpCall"] = n
        n = Metric_IpFarBranch() ; r.metric(n) ; o["IpFarBranch"] = n
        n = Metric_IpMispredict() ; r.metric(n) ; o["IpMispredict"] = n
        n = Metric_IpMisp_Cond_Ntaken() ; r.metric(n) ; o["IpMisp_Cond_Ntaken"] = n
        n = Metric_IpMisp_Cond_Taken() ; r.metric(n) ; o["IpMisp_Cond_Taken"] = n
        n = Metric_IpMisp_Ret() ; r.metric(n) ; o["IpMisp_Ret"] = n
        n = Metric_IpMisp_Indirect() ; r.metric(n) ; o["IpMisp_Indirect"] = n
        n = Metric_Microcode_Uop_Ratio() ; r.metric(n) ; o["Microcode_Uop_Ratio"] = n
        n = Metric_FPDiv_Uop_Ratio() ; r.metric(n) ; o["FPDiv_Uop_Ratio"] = n
        n = Metric_IDiv_Uop_Ratio() ; r.metric(n) ; o["IDiv_Uop_Ratio"] = n
        n = Metric_X87_Uop_Ratio() ; r.metric(n) ; o["X87_Uop_Ratio"] = n
        n = Metric_IpLoad() ; r.metric(n) ; o["IpLoad"] = n
        n = Metric_IpStore() ; r.metric(n) ; o["IpStore"] = n
        n = Metric_MemLoad_Ratio() ; r.metric(n) ; o["MemLoad_Ratio"] = n
        n = Metric_Load_Splits_Ratio() ; r.metric(n) ; o["Load_Splits_Ratio"] = n
        n = Metric_Load_Locks_Ratio() ; r.metric(n) ; o["Load_Locks_Ratio"] = n
        n = Metric_PCT_Loads_with_StoreFwdBlk() ; r.metric(n) ; o["PCT_Loads_with_StoreFwdBlk"] = n
        n = Metric_PCT_Loads_with_AdressAliasing() ; r.metric(n) ; o["PCT_Loads_with_AdressAliasing"] = n
        n = Metric_PCT_LoadHead_with_STLBHit() ; r.metric(n) ; o["PCT_LoadHead_with_STLBHit"] = n
        n = Metric_PCT_LoadHead_with_Pagewalk() ; r.metric(n) ; o["PCT_LoadHead_with_Pagewalk"] = n
        n = Metric_PCT_LoadHead_with_StoreFwding() ; r.metric(n) ; o["PCT_LoadHead_with_StoreFwding"] = n
        n = Metric_PCT_LoadHead_with_OtherPipelineBlks() ; r.metric(n) ; o["PCT_LoadHead_with_OtherPipelineBlks"] = n
        n = Metric_PCT_LoadHead_with_L1miss() ; r.metric(n) ; o["PCT_LoadHead_with_L1miss"] = n
        n = Metric_Store_Bound() ; r.metric(n) ; o["Store_Bound"] = n
        n = Metric_Load_Bound() ; r.metric(n) ; o["Load_Bound"] = n
        n = Metric_L1_Bound() ; r.metric(n) ; o["L1_Bound"] = n
        n = Metric_PCT_LoadMissBound_with_L2Hit() ; r.metric(n) ; o["PCT_LoadMissBound_with_L2Hit"] = n
        n = Metric_PCT_LoadMissBound_with_L2Miss() ; r.metric(n) ; o["PCT_LoadMissBound_with_L2Miss"] = n
        n = Metric_PCT_LoadMissBound_with_L3Hit() ; r.metric(n) ; o["PCT_LoadMissBound_with_L3Hit"] = n
        n = Metric_PCT_LoadMissBound_with_L3Miss() ; r.metric(n) ; o["PCT_LoadMissBound_with_L3Miss"] = n
        n = Metric_PCT_IfetchMissBound_with_L2Hit() ; r.metric(n) ; o["PCT_IfetchMissBound_with_L2Hit"] = n
        n = Metric_PCT_IfetchMissBound_with_L2Miss() ; r.metric(n) ; o["PCT_IfetchMissBound_with_L2Miss"] = n
        n = Metric_PCT_IfetchMissBound_with_L3Hit() ; r.metric(n) ; o["PCT_IfetchMissBound_with_L3Hit"] = n
        n = Metric_PCT_IfetchMissBound_with_L3Miss() ; r.metric(n) ; o["PCT_IfetchMissBound_with_L3Miss"] = n
        n = Metric_Branch_Mispredict_Ratio() ; r.metric(n) ; o["Branch_Mispredict_Ratio"] = n
        n = Metric_Branch_Mispredict_to_Unknown_Branch_Ratio() ; r.metric(n) ; o["Branch_Mispredict_to_Unknown_Branch_Ratio"] = n
        n = Metric_Machine_Clears_Disamb_PKI() ; r.metric(n) ; o["Machine_Clears_Disamb_PKI"] = n
        n = Metric_Machine_Clears_FP_Assist_PKI() ; r.metric(n) ; o["Machine_Clears_FP_Assist_PKI"] = n
        n = Metric_Machine_Clears_Monuke_PKI() ; r.metric(n) ; o["Machine_Clears_Monuke_PKI"] = n
        n = Metric_Machine_Clears_Page_Fault_PKI() ; r.metric(n) ; o["Machine_Clears_Page_Fault_PKI"] = n
        n = Metric_Machine_Clears_MRN_PKI() ; r.metric(n) ; o["Machine_Clears_MRN_PKI"] = n
        n = Metric_Machine_Clears_SMC_PKI() ; r.metric(n) ; o["Machine_Clears_SMC_PKI"] = n
        n = Metric_PCT_Store_Buffer_Stall_Cycles() ; r.metric(n) ; o["PCT_Store_Buffer_Stall_Cycles"] = n
        n = Metric_PCT_Load_Buffer_Stall_Cycles() ; r.metric(n) ; o["PCT_Load_Buffer_Stall_Cycles"] = n
        n = Metric_PCT_Mem_RSV_Stall_Cycles() ; r.metric(n) ; o["PCT_Mem_RSV_Stall_Cycles"] = n
        n = Metric_PCT_Tpause_Cycles() ; r.metric(n) ; o["PCT_Tpause_Cycles"] = n
        n = Metric_Turbo_Utilization() ; r.metric(n) ; o["Turbo_Utilization"] = n
        n = Metric_Kernel_Utilization() ; r.metric(n) ; o["Kernel_Utilization"] = n
        n = Metric_CPU_Utilization() ; r.metric(n) ; o["CPU_Utilization"] = n

        # references between groups

        o["Resource_Bound"].Core_Bound = o["Core_Bound"]

        # siblings cross-tree

