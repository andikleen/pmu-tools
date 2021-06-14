
# -*- coding: latin-1 -*-
#
# auto generated TopDown/TMA 7.2 description for Intel 12th gen Core (code name Alderlake) with Grace Mont
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
version = "7.2"
base_frequency = -1.0
Memory = 0
Average_Frequency = 0.0


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


# Aux. formulas


# pipeline allocation width
def Pipeline_Width(self, EV, level):
    return 5

def CLKS(self, EV, level):
    return EV("CPU_CLK_UNHALTED.THREAD", level)

def SLOTS(self, EV, level):
    return Pipeline_Width(self, EV, level) * CLKS(self, EV, level)

# Instructions Per Cycle
def IPC(self, EV, level):
    return EV("INST_RETIRED.ANY", level) / CLKS(self, EV, level)

# Cycles Per Instruction
def CPI(self, EV, level):
    return CLKS(self, EV, level) / EV("INST_RETIRED.ANY", level)

# Uops Per Instruction
def UPI(self, EV, level):
    return EV("UOPS_RETIRED.ALL", level) / EV("INST_RETIRED.ANY", level)

# Instructions per Branch (lower number means higher occurance rate)
def IpBranch(self, EV, level):
    return EV("INST_RETIRED.ANY", level) / EV("BR_INST_RETIRED.ALL_BRANCHES", level)

# Branches per 1000 instructions
def Branch_per_1KI(self, EV, level):
    return 1000 * EV("BR_INST_RETIRED.ALL_BRANCHES", level) / EV("INST_RETIRED.ANY", level)

# Instruction per (near) call (lower number means higher occurance rate)
def IpCall(self, EV, level):
    return EV("INST_RETIRED.ANY", level) / EV("BR_INST_RETIRED.CALL", level)

# Instructions per Load
def IpLoad(self, EV, level):
    return EV("INST_RETIRED.ANY", level) / EV("MEM_UOPS_RETIRED.ALL_LOADS", level)

# Instructions per Store
def IpStore(self, EV, level):
    return EV("INST_RETIRED.ANY", level) / EV("MEM_UOPS_RETIRED.ALL_STORES", level)

# Number of Instructions per non-speculative Branch Misprediction
def IpMispredict(self, EV, level):
    return EV("INST_RETIRED.ANY", level) / EV("BR_MISP_RETIRED.ALL_BRANCHES", level)

# Instructions per Far Branch
def IpFarBranch(self, EV, level):
    return EV("INST_RETIRED.ANY", level) / (EV("BR_INST_RETIRED.FAR_BRANCH", level) / 2 )

# Ratio of all branches which mispredict
def Branch_Mispredict_Ratio(self, EV, level):
    return EV("BR_MISP_RETIRED.ALL_BRANCHES", level) / EV("BR_INST_RETIRED.ALL_BRANCHES", level)

# Ratio between Mispredicted branches and unknown branches
def Branch_Mispredict_to_Unknown_Branch_Ratio(self, EV, level):
    return EV("BR_MISP_RETIRED.ALL_BRANCHES", level) / EV("BACLEARS.ANY", level)

# Percentage of all uops which are ucode ops
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

# Average Frequency Utilization relative nominal frequency
def Turbo_Utilization(self, EV, level):
    return CLKS(self, EV, level) / EV("CPU_CLK_UNHALTED.REF_TSC", level)

# Fraction of cycles spent in Kernel mode
def Kernel_Utilization(self, EV, level):
    return EV("CPU_CLK_UNHALTED.THREAD:sup", level) / EV("CPU_CLK_UNHALTED.THREAD", level)

# Estimated Pause cost. In percent
def Estimated_Pause_Cost(self, EV, level):
    return 100 * EV("SERIALIZATION.NON_C01_MS_SCB", level) / SLOTS(self, EV, level)

def Cycles_per_Demand_Load_L2_Hit(self, EV, level):
    return EV("MEM_BOUND_STALLS.LOAD_L2_HIT", level) / EV("MEM_LOAD_UOPS_RETIRED.L2_HIT", level)

def Cycles_per_Demand_Load_LLC_Hit(self, EV, level):
    return EV("MEM_BOUND_STALLS.LOAD_LLC_HIT", level) / EV("MEM_LOAD_UOPS_RETIRED.L3_HIT", level)

def Cycles_per_Demand_Load_DRAM_Hit(self, EV, level):
    return EV("MEM_BOUND_STALLS.LOAD_DRAM_HIT", level) / EV("MEM_LOAD_UOPS_RETIRED.DRAM_HIT", level)

def Inst_Miss_Cost_L2Hit(self, EV, level):
    return 100 * EV("MEM_BOUND_STALLS.IFETCH_L2_HIT", level) / (EV("MEM_BOUND_STALLS.IFETCH_L2_HIT", level) + EV("MEM_BOUND_STALLS.IFETCH_LLC_HIT", level) + EV("MEM_BOUND_STALLS.IFETCH_DRAM_HIT", level))

def Inst_Miss_Cost_LLCHit(self, EV, level):
    return 100 * EV("MEM_BOUND_STALLS.IFETCH_LLC_HIT", level) / (EV("MEM_BOUND_STALLS.IFETCH_L2_HIT", level) + EV("MEM_BOUND_STALLS.IFETCH_LLC_HIT", level) + EV("MEM_BOUND_STALLS.IFETCH_DRAM_HIT", level))

def Inst_Miss_Cost_DRAMHit(self, EV, level):
    return 100 * EV("MEM_BOUND_STALLS.IFETCH_DRAM_HIT", level) / (EV("MEM_BOUND_STALLS.IFETCH_L2_HIT", level) + EV("MEM_BOUND_STALLS.IFETCH_LLC_HIT", level) + EV("MEM_BOUND_STALLS.IFETCH_DRAM_HIT", level))

# load ops retired per 1000 instruction
def MemLoad_per_1KI(self, EV, level):
    return 1000 * EV("MEM_UOPS_RETIRED.ALL_LOADS", level) / EV("INST_RETIRED.ANY", level)

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
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_FE_BOUND.ALL", 1) / SLOTS(self, EV, 1)
            self.thresh = (self.val > 0.20)
        except ZeroDivisionError:
            handle_error(self, "Frontend_Bound zero division")
        return self.val
    desc = """
Counts the number of uops the front-end does not deliver to
the back-end in a given cycle."""


class Frontend_Latency:
    name = "Frontend_Latency"
    domain = "Slots"
    area = "FE"
    level = 2
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = (EV("TOPDOWN_FE_BOUND.ICACHE", 2) + EV("TOPDOWN_FE_BOUND.ITLB", 2) + EV("TOPDOWN_FE_BOUND.BRANCH_DETECT", 2) + EV("TOPDOWN_FE_BOUND.BRANCH_RESTEER", 2)) / SLOTS(self, EV, 2)
            self.thresh = (self.val > 0.15)
        except ZeroDivisionError:
            handle_error(self, "Frontend_Latency zero division")
        return self.val
    desc = """
Derived Event equivalent to Frontend_Latency event found in
CORE. Top Down umasks can be programmed with multiple
subevents on one counter.  In the examples above we have
created a 'Level 2' similar to CORE in which we set several
umask bits for 1 event."""


class Icache:
    name = "Icache"
    domain = "Slots"
    area = "FE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_FE_BOUND.ICACHE", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.05)
        except ZeroDivisionError:
            handle_error(self, "Icache zero division")
        return self.val
    desc = """
Counts the number of issue slots every cycle that were not
delivered by the frontend due to an icache miss"""


class ITLB:
    name = "ITLB"
    domain = "Slots"
    area = "FE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_FE_BOUND.ITLB", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.05)
        except ZeroDivisionError:
            handle_error(self, "ITLB zero division")
        return self.val
    desc = """
Counts the number of issue slots every cycle that were not
delivered by the frontend due to itlb miss"""


class Branch_Detect:
    name = "Branch_Detect"
    domain = "Slots"
    area = "FE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_FE_BOUND.BRANCH_DETECT", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.05)
        except ZeroDivisionError:
            handle_error(self, "Branch_Detect zero division")
        return self.val
    desc = """
Counts the number of issue slots every cycle that were not
delivered by the frontend due to BAClear (Branch Target
Buffer (BTB) prediction or lack thereof was later corrected
by a branch address calculator in the front-end)"""


class Branch_Resteer:
    name = "Branch_Resteer"
    domain = "Slots"
    area = "FE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_FE_BOUND.BRANCH_RESTEER", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.05)
        except ZeroDivisionError:
            handle_error(self, "Branch_Resteer zero division")
        return self.val
    desc = """
Counts the number of issue slots every cycle that were not
delivered by the frontend due to a BTClear (Branch Target
Buffer (BTB) predicted a taken branch)"""


class Frontend_Bandwidth:
    name = "Frontend_Bandwidth"
    domain = "Slots"
    area = "FE"
    level = 2
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = (EV("TOPDOWN_FE_BOUND.CISC", 2) + EV("TOPDOWN_FE_BOUND.DECODE", 2) + EV("TOPDOWN_FE_BOUND.PREDECODE", 2) + EV("TOPDOWN_FE_BOUND.OTHER", 2)) / SLOTS(self, EV, 2)
            self.thresh = (self.val > 0.10)
        except ZeroDivisionError:
            handle_error(self, "Frontend_Bandwidth zero division")
        return self.val
    desc = """
Derived Event equivalent to Frontend_Bandwidth event found
in CORE. Top Down umasks can be programmed with multiple
subevents on one counter.  In the examples above we have
created a 'Level 2' similar to CORE in which we set several
umask bits for 1 event."""


class Cisc:
    name = "Cisc"
    domain = "Slots"
    area = "FE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_FE_BOUND.CISC", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.05)
        except ZeroDivisionError:
            handle_error(self, "Cisc zero division")
        return self.val
    desc = """
Counts the number of issue slots every cycle that were not
delivered by the frontend due to ms"""


class Decode:
    name = "Decode"
    domain = "Slots"
    area = "FE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_FE_BOUND.DECODE", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.05)
        except ZeroDivisionError:
            handle_error(self, "Decode zero division")
        return self.val
    desc = """
Counts the number of issue slots every cycle that were not
delivered by the frontend due to decode stall"""


class Predecode:
    name = "Predecode"
    domain = "Slots"
    area = "FE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_FE_BOUND.PREDECODE", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.05)
        except ZeroDivisionError:
            handle_error(self, "Predecode zero division")
        return self.val
    desc = """
Counts the number of issue slots every cycle that were not
delivered by the frontend due to predecode wrong"""


class Other_FB:
    name = "Other_FB"
    domain = "Slots"
    area = "FE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_FE_BOUND.OTHER", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.05)
        except ZeroDivisionError:
            handle_error(self, "Other_FB zero division")
        return self.val
    desc = """
Counts the number of issue slots every cycle that were not
delivered by the frontend that do not categorize into any
other common frontend stall"""


class Bad_Speculation:
    name = "Bad_Speculation"
    domain = "Slots"
    area = "BAD"
    level = 1
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_BAD_SPECULATION.ALL", 1) / SLOTS(self, EV, 1)
            self.thresh = (self.val > 0.15)
        except ZeroDivisionError:
            handle_error(self, "Bad_Speculation zero division")
        return self.val
    desc = """
Counts the number of issue slots that were not consumed by
the backend because allocation is stalled waiting for a
mispredicted jump to retire or other branch-like conditions
(e.g. the event is relevant during certain microcode flows).
Counts all issue slots blocked while within this window
including slots where uops were not available in the IQ."""


class Branch_Mispredicts:
    name = "Branch_Mispredicts"
    domain = "Slots"
    area = "BAD"
    level = 2
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_BAD_SPECULATION.MISPREDICT", 2) / SLOTS(self, EV, 2)
            self.thresh = (self.val > 0.05)
        except ZeroDivisionError:
            handle_error(self, "Branch_Mispredicts zero division")
        return self.val
    desc = """
Counts the number of issue slots every cycle that were not
consumed by the backend due to Branch Mispredict (jeclear)"""


class Machine_Clears:
    name = "Machine_Clears"
    domain = "Slots"
    area = "BAD"
    level = 2
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = (EV("TOPDOWN_BAD_SPECULATION.NUKE", 2) + EV("TOPDOWN_BAD_SPECULATION.FASTNUKE", 2)) / SLOTS(self, EV, 2)
            self.thresh = (self.val > 0.05)
        except ZeroDivisionError:
            handle_error(self, "Machine_Clears zero division")
        return self.val
    desc = """
Derived Event equivalent to Machine_Clears event found in
CORE. Top Down umasks can be programmed with multiple
subevents on one counter.  In the examples above we have
created a 'Level 2' similar to CORE in which we set several
umask bits for 1 event."""


class Nuke:
    name = "Nuke"
    domain = "Slots"
    area = "BAD"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_BAD_SPECULATION.NUKE", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.05)
        except ZeroDivisionError:
            handle_error(self, "Nuke zero division")
        return self.val
    desc = """
Counts the number of issue slots every cycle that were not
consumed by the backend due to a Machine Clear"""


class FastNuke_MoNuke:
    name = "FastNuke_MoNuke"
    domain = "Slots"
    area = "BAD"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_BAD_SPECULATION.FASTNUKE", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.05)
        except ZeroDivisionError:
            handle_error(self, "FastNuke_MoNuke zero division")
        return self.val
    desc = """
Counts the number of issue slots every cycle that were not
consumed by the backend due to Memory Ordering Machine
clears (Requires Memory Disambiguation to be enabled).
Fastnuke version available from GRT onwards also includes
MRN nukes."""


class Backend_Bound:
    name = "Backend_Bound"
    domain = "Slots"
    area = "BE"
    level = 1
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_BE_BOUND.ALL", 1) / SLOTS(self, EV, 1)
            self.thresh = (self.val > 0.20)
        except ZeroDivisionError:
            handle_error(self, "Backend_Bound zero division")
        return self.val
    desc = """
Counts the number of issue slots that were not consumed
because of a full resource in the backend.  Note that UOPS
must be available for consumption in order for this event to
fire.  If a uop is not available (IQ is empty), this event
will not count."""


class Resource_Bound:
    name = "Resource_Bound"
    domain = "Slots"
    area = "BE"
    level = 2
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_BE_BOUND.ALL", 2) / SLOTS(self, EV, 2)
            self.thresh = (self.val > 0.20)
        except ZeroDivisionError:
            handle_error(self, "Resource_Bound zero division")
        return self.val
    desc = """
Derived event to account for Core_Bound event found in CORE.
If Memory_Bound is used  ***TOPDOWN_BE_BOUND.CORE_BOUND =
(TOPDOWN_BE_BOUND.ALL/(4*CPU_CLK_UNHALTED.CORE)) - ((MEM_BOU
ND_STALLS.LOAD_L2_HIT+MEM_BOUND_STALLS.LOAD_LLC_HIT+MEM_BOUN
D_STALLS.LOAD_DRAM_HIT)/CPU_CLK_UNHALTED.CORE).  Else if not
using Memory_Bound, Level 2 = Level 1,
TOPDOWN_BE_BOUND.CORE_BOUND =
TOPDOWN_BE_BOUND.ALL/(4*CPU_CLK_UNHALTED.CORE).  (By
default, Level1 == Level2)"""


class Mem_Scheduler:
    name = "Mem_Scheduler"
    domain = "Slots"
    area = "BE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_BE_BOUND.MEM_SCHEDULER", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.10)
        except ZeroDivisionError:
            handle_error(self, "Mem_Scheduler zero division")
        return self.val
    desc = """
Counts the number of issue slots every cycle that were not
consumed by the backend due to memory reservation stall (MIQ
not being able to accept another uop)."""


class Non_Mem_Scheduler:
    name = "Non_Mem_Scheduler"
    domain = "Slots"
    area = "BE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_BE_BOUND.NON_MEM_SCHEDULER", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.10)
        except ZeroDivisionError:
            handle_error(self, "Non_Mem_Scheduler zero division")
        return self.val
    desc = """
Counts the number of issue slots every cycle that were not
consumed by the backend due to IEC and FPC RAT stalls -
which can be due to the FIQ and IEC reservation station
stall (integer, FP and SIMD scheduler not being able to
accept another uop. )"""


class Register:
    name = "Register"
    domain = "Slots"
    area = "BE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_BE_BOUND.REGISTER", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.10)
        except ZeroDivisionError:
            handle_error(self, "Register zero division")
        return self.val
    desc = """
Counts the number of issue slots every cycle that were not
consumed by the backend due to mrbl stall"""


class Reorder_Buffer:
    name = "Reorder_Buffer"
    domain = "Slots"
    area = "BE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_BE_BOUND.REORDER_BUFFER", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.10)
        except ZeroDivisionError:
            handle_error(self, "Reorder_Buffer zero division")
        return self.val
    desc = """
Counts the number of issue slots every cycle that were not
consumed by the backend due to ROB full"""


class Alloc_Restriction:
    name = "Alloc_Restriction"
    domain = "Slots"
    area = "BE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_BE_BOUND.ALLOC_RESTRICTIONS", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.10)
        except ZeroDivisionError:
            handle_error(self, "Alloc_Restriction zero division")
        return self.val
    desc = """
Counts the number of issue slots every cycle that were not
consumed by the backend due to an alloc restriction such as
dual dest/dual exec/sync_uop/alloc_by_itself"""


class Serialization:
    name = "Serialization"
    domain = "Slots"
    area = "BE"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_BE_BOUND.SERIALIZATION", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.10)
        except ZeroDivisionError:
            handle_error(self, "Serialization zero division")
        return self.val
    desc = """
Counts the number of issue slots every cycle that were not
consumed by the backend due to iq/jeu scoreboards or ms scb"""


class Core_Bound:
    name = "Core_Bound"
    domain = "Cycles"
    area = "BE_alt"
    level = 2
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = max(0 , self.Backend_Bound.compute(EV) - self.Memory_Bound.compute(EV))
            self.thresh = (self.val > 0.10)
        except ZeroDivisionError:
            handle_error(self, "Core_Bound zero division")
        return self.val
    desc = """
Derived event to account for Core_Bound event found in CORE.
Counts the number of backend bound stalls that are core
bound and not attributed to outstanding demand load stalls
with a hittypes of L2, LLC or DRAM. Alternate Backend Bound
subevents to account for 'Memory Bound' (L1, L2, L3 misses,
respectively).These are not slot based and can NOT be
precisely added/subtracted from the backend bound subevents.
For an estimated calculation ONLY, Level 2 Memory Bound stat
can be subtracted from Level 1 Backend_Bound and the
resulting stat can be called Level 2 Core_Bound. Else, the
default definition of Level 2 Resource_Bound is equal to
that of Level 1 Backend Bound. ( == Resource_Bound% -
Memory_Bound%)"""


class Memory_Bound:
    name = "Memory_Bound"
    domain = "Cycles"
    area = "BE_alt"
    level = 2
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = (EV("MEM_BOUND_STALLS.LOAD_L2_HIT", 2) + EV("MEM_BOUND_STALLS.LOAD_LLC_HIT", 2) + EV("MEM_BOUND_STALLS.LOAD_DRAM_HIT", 2)) / CLKS(self, EV, 2)
            self.thresh = (self.val > 0.20)
        except ZeroDivisionError:
            handle_error(self, "Memory_Bound zero division")
        return self.val
    desc = """
Counts the number of demand load stalls - can be used to
account for memory bound stalls. Alternate Backend Bound
subevents to account for 'Memory Bound' (L1, L2, L3 misses,
respectively). These are not slot based and can NOT be
precisely added/subtracted from the backend bound subevents.
 For an estimated calculation ONLY, Level 2 Memory Bound
stat can be subtracted from Level 1 Backend_Bound and the
resulting stat can be called Level 2 Core_Bound.  Else, the
default definition of Level 2 Resource_Bound is equal to
that of Level 1 Backend Bound. (aka
C0_STALLS/MEM_BOUND_STALLS, Alternate LEVEL2 usage)"""


class L2_Hit:
    name = "L2_Hit"
    domain = "Cycles"
    area = "BE_alt"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("MEM_BOUND_STALLS.LOAD_L2_HIT", 3) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.05)
        except ZeroDivisionError:
            handle_error(self, "L2_Hit zero division")
        return self.val
    desc = """
Counts the number of demand load stalls with an L2 hittype,
conditioned on being the head of the LLB (not ROB), having
been a DCU miss and no jeclear in progress"""


class LLC_Hit:
    name = "LLC_Hit"
    domain = "Cycles"
    area = "BE_alt"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("MEM_BOUND_STALLS.LOAD_LLC_HIT", 3) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.05)
        except ZeroDivisionError:
            handle_error(self, "LLC_Hit zero division")
        return self.val
    desc = """
Counts the number of demand load stalls with an LLC hittype,
conditioned on being the head of the LLB (not ROB), having
been a DCU miss and no jeclear in progress"""


class DRAM_Hit:
    name = "DRAM_Hit"
    domain = "Cycles"
    area = "BE_alt"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("MEM_BOUND_STALLS.LOAD_DRAM_HIT", 3) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.10)
        except ZeroDivisionError:
            handle_error(self, "DRAM_Hit zero division")
        return self.val
    desc = """
Counts the number of demand load stalls with a dram hittype,
conditioned on being the head of the LLB (not ROB), having
been a DCU miss and no jeclear in progress"""


class Retiring:
    name = "Retiring"
    domain = "Slots"
    area = "RET"
    level = 1
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("TOPDOWN_RETIRING.ALL", 1) / SLOTS(self, EV, 1)
            self.thresh = (self.val > 0.75)
        except ZeroDivisionError:
            handle_error(self, "Retiring zero division")
        return self.val
    desc = """
Counts the numer of issue slots every cycle that result in
retirement slots"""


class Base:
    name = "Base"
    domain = "Slots"
    area = "RET"
    level = 2
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = (EV("TOPDOWN_RETIRING.ALL", 2) - EV("UOPS_RETIRED.MS", 2)) / SLOTS(self, EV, 2)
            self.thresh = (self.val > 0.60)
        except ZeroDivisionError:
            handle_error(self, "Base zero division")
        return self.val
    desc = """
Derived event equivalent to Base event found in CORE"""


class FP_uops:
    name = "FP_uops"
    domain = "Slots"
    area = "RET"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("UOPS_RETIRED.FPDIV", 3) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.20)
        except ZeroDivisionError:
            handle_error(self, "FP_uops zero division")
        return self.val
    desc = """
Derived event equivalent to FP uops event found in CORE.
Counts the number of floating point divide uops retired (x87
and sse, including x87 sqrt)"""


class Other:
    name = "Other"
    domain = "Slots"
    area = "RET"
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = (EV("TOPDOWN_RETIRING.ALL", 3) - EV("UOPS_RETIRED.MS", 3) - EV("UOPS_RETIRED.FPDIV", 3)) / SLOTS(self, EV, 3)
            self.thresh = (self.val > 0.30)
        except ZeroDivisionError:
            handle_error(self, "Other zero division")
        return self.val
    desc = """
Derived event equivalent to other event found in CORE.
Counts the number of uops retired excluding ms and fp div
uops"""


class MS_uops:
    name = "MS_uops"
    domain = "Slots"
    area = "RET"
    level = 2
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("UOPS_RETIRED.MS", 2) / SLOTS(self, EV, 2)
            self.thresh = (self.val > 0.05)
        except ZeroDivisionError:
            handle_error(self, "MS_uops zero division")
        return self.val
    desc = """
Derived event equivalent to MS uops event found in CORE.
Counts the number of uops that are from the complex flows
issued by the micro-sequencer (MS).  This includes uops from
flows due to complex instructions, faults, assists, and
inserted flows."""


class Metric_CLKS:
    name = "CLKS"
    domain = "Cycles"
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Thread"
    metricgroup = []
    sibling = None

    def compute(self, EV):
        try:
            self.val = CLKS(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "CLKS zero division")
    desc = """
"""


class Metric_SLOTS:
    name = "SLOTS"
    domain = "Cycles"
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Thread"
    metricgroup = []
    sibling = None

    def compute(self, EV):
        try:
            self.val = SLOTS(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "SLOTS zero division")
    desc = """
"""


class Metric_IPC:
    name = "IPC"
    domain = ""
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Thread"
    metricgroup = []
    sibling = None

    def compute(self, EV):
        try:
            self.val = IPC(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "IPC zero division")
    desc = """
Instructions Per Cycle"""


class Metric_CPI:
    name = "CPI"
    domain = ""
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Thread"
    metricgroup = []
    sibling = None

    def compute(self, EV):
        try:
            self.val = CPI(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "CPI zero division")
    desc = """
Cycles Per Instruction"""


class Metric_UPI:
    name = "UPI"
    domain = ""
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Thread"
    metricgroup = []
    sibling = None

    def compute(self, EV):
        try:
            self.val = UPI(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "UPI zero division")
    desc = """
Uops Per Instruction"""


class Metric_IpBranch:
    name = "IpBranch"
    domain = ""
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = []
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpBranch(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "IpBranch zero division")
    desc = """
Instructions per Branch (lower number means higher occurance
rate)"""


class Metric_Branch_per_1KI:
    name = "Branch_per_1KI"
    domain = ""
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = []
    sibling = None

    def compute(self, EV):
        try:
            self.val = Branch_per_1KI(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "Branch_per_1KI zero division")
    desc = """
Branches per 1000 instructions"""


class Metric_IpCall:
    name = "IpCall"
    domain = ""
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = []
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpCall(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "IpCall zero division")
    desc = """
Instruction per (near) call (lower number means higher
occurance rate)"""


class Metric_IpLoad:
    name = "IpLoad"
    domain = ""
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = []
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpLoad(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "IpLoad zero division")
    desc = """
Instructions per Load"""


class Metric_IpStore:
    name = "IpStore"
    domain = ""
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = []
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpStore(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "IpStore zero division")
    desc = """
Instructions per Store"""


class Metric_IpMispredict:
    name = "IpMispredict"
    domain = ""
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = []
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpMispredict(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "IpMispredict zero division")
    desc = """
Number of Instructions per non-speculative Branch
Misprediction"""


class Metric_IpFarBranch:
    name = "IpFarBranch"
    domain = ""
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = []
    sibling = None

    def compute(self, EV):
        try:
            self.val = IpFarBranch(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "IpFarBranch zero division")
    desc = """
Instructions per Far Branch"""


class Metric_Branch_Mispredict_Ratio:
    name = "Branch_Mispredict_Ratio"
    domain = ""
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = []
    sibling = None

    def compute(self, EV):
        try:
            self.val = Branch_Mispredict_Ratio(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "Branch_Mispredict_Ratio zero division")
    desc = """
Ratio of all branches which mispredict"""


class Metric_Branch_Mispredict_to_Unknown_Branch_Ratio:
    name = "Branch_Mispredict_to_Unknown_Branch_Ratio"
    domain = ""
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = []
    sibling = None

    def compute(self, EV):
        try:
            self.val = Branch_Mispredict_to_Unknown_Branch_Ratio(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "Branch_Mispredict_to_Unknown_Branch_Ratio zero division")
    desc = """
Ratio between Mispredicted branches and unknown branches"""


class Metric_Microcode_Uop_Ratio:
    name = "Microcode_Uop_Ratio"
    domain = ""
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = []
    sibling = None

    def compute(self, EV):
        try:
            self.val = Microcode_Uop_Ratio(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "Microcode_Uop_Ratio zero division")
    desc = """
Percentage of all uops which are ucode ops"""


class Metric_FPDiv_Uop_Ratio:
    name = "FPDiv_Uop_Ratio"
    domain = ""
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = []
    sibling = None

    def compute(self, EV):
        try:
            self.val = FPDiv_Uop_Ratio(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "FPDiv_Uop_Ratio zero division")
    desc = """
Percentage of all uops which are FPDiv uops"""


class Metric_IDiv_Uop_Ratio:
    name = "IDiv_Uop_Ratio"
    domain = ""
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = []
    sibling = None

    def compute(self, EV):
        try:
            self.val = IDiv_Uop_Ratio(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "IDiv_Uop_Ratio zero division")
    desc = """
Percentage of all uops which are IDiv uops"""


class Metric_X87_Uop_Ratio:
    name = "X87_Uop_Ratio"
    domain = ""
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = []
    sibling = None

    def compute(self, EV):
        try:
            self.val = X87_Uop_Ratio(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "X87_Uop_Ratio zero division")
    desc = """
Percentage of all uops which are x87 uops"""


class Metric_Turbo_Utilization:
    name = "Turbo_Utilization"
    domain = ""
    maxval = 0
    server = False
    errcount = 0
    area = "Info"
    metricgroup = []
    sibling = None

    def compute(self, EV):
        try:
            self.val = Turbo_Utilization(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "Turbo_Utilization zero division")
    desc = """
Average Frequency Utilization relative nominal frequency"""


class Metric_Kernel_Utilization:
    name = "Kernel_Utilization"
    domain = ""
    maxval = 0
    server = False
    errcount = 0
    area = "Info"
    metricgroup = []
    sibling = None

    def compute(self, EV):
        try:
            self.val = Kernel_Utilization(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "Kernel_Utilization zero division")
    desc = """
Fraction of cycles spent in Kernel mode"""


class Metric_Estimated_Pause_Cost:
    name = "Estimated_Pause_Cost"
    domain = ""
    maxval = 0
    server = False
    errcount = 0
    area = "Info"
    metricgroup = []
    sibling = None

    def compute(self, EV):
        try:
            self.val = Estimated_Pause_Cost(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "Estimated_Pause_Cost zero division")
    desc = """
Estimated Pause cost. In percent"""


class Metric_Cycles_per_Demand_Load_L2_Hit:
    name = "Cycles_per_Demand_Load_L2_Hit"
    domain = ""
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Memory"
    metricgroup = []
    sibling = None

    def compute(self, EV):
        try:
            self.val = Cycles_per_Demand_Load_L2_Hit(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "Cycles_per_Demand_Load_L2_Hit zero division")
    desc = """
"""


class Metric_Cycles_per_Demand_Load_LLC_Hit:
    name = "Cycles_per_Demand_Load_LLC_Hit"
    domain = ""
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Memory"
    metricgroup = []
    sibling = None

    def compute(self, EV):
        try:
            self.val = Cycles_per_Demand_Load_LLC_Hit(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "Cycles_per_Demand_Load_LLC_Hit zero division")
    desc = """
"""


class Metric_Cycles_per_Demand_Load_DRAM_Hit:
    name = "Cycles_per_Demand_Load_DRAM_Hit"
    domain = ""
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Memory"
    metricgroup = []
    sibling = None

    def compute(self, EV):
        try:
            self.val = Cycles_per_Demand_Load_DRAM_Hit(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "Cycles_per_Demand_Load_DRAM_Hit zero division")
    desc = """
"""


class Metric_Inst_Miss_Cost_L2Hit:
    name = "Inst_Miss_Cost_L2Hit"
    domain = ""
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Memory"
    metricgroup = []
    sibling = None

    def compute(self, EV):
        try:
            self.val = Inst_Miss_Cost_L2Hit(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "Inst_Miss_Cost_L2Hit zero division")
    desc = """
"""


class Metric_Inst_Miss_Cost_LLCHit:
    name = "Inst_Miss_Cost_LLCHit"
    domain = ""
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Memory"
    metricgroup = []
    sibling = None

    def compute(self, EV):
        try:
            self.val = Inst_Miss_Cost_LLCHit(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "Inst_Miss_Cost_LLCHit zero division")
    desc = """
"""


class Metric_Inst_Miss_Cost_DRAMHit:
    name = "Inst_Miss_Cost_DRAMHit"
    domain = ""
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Memory"
    metricgroup = []
    sibling = None

    def compute(self, EV):
        try:
            self.val = Inst_Miss_Cost_DRAMHit(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "Inst_Miss_Cost_DRAMHit zero division")
    desc = """
"""


class Metric_MemLoad_per_1KI:
    name = "MemLoad_per_1KI"
    domain = ""
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Memory"
    metricgroup = []
    sibling = None

    def compute(self, EV):
        try:
            self.val = MemLoad_per_1KI(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "MemLoad_per_1KI zero division")
    desc = """
load ops retired per 1000 instruction"""


# Schedule



class Setup:
    def __init__(self, r):
        o = dict()
        n = Frontend_Bound() ; r.run(n) ; o["Frontend_Bound"] = n
        n = Frontend_Latency() ; r.run(n) ; o["Frontend_Latency"] = n
        n = Icache() ; r.run(n) ; o["Icache"] = n
        n = ITLB() ; r.run(n) ; o["ITLB"] = n
        n = Branch_Detect() ; r.run(n) ; o["Branch_Detect"] = n
        n = Branch_Resteer() ; r.run(n) ; o["Branch_Resteer"] = n
        n = Frontend_Bandwidth() ; r.run(n) ; o["Frontend_Bandwidth"] = n
        n = Cisc() ; r.run(n) ; o["Cisc"] = n
        n = Decode() ; r.run(n) ; o["Decode"] = n
        n = Predecode() ; r.run(n) ; o["Predecode"] = n
        n = Other_FB() ; r.run(n) ; o["Other_FB"] = n
        n = Bad_Speculation() ; r.run(n) ; o["Bad_Speculation"] = n
        n = Branch_Mispredicts() ; r.run(n) ; o["Branch_Mispredicts"] = n
        n = Machine_Clears() ; r.run(n) ; o["Machine_Clears"] = n
        n = Nuke() ; r.run(n) ; o["Nuke"] = n
        n = FastNuke_MoNuke() ; r.run(n) ; o["FastNuke_MoNuke"] = n
        n = Backend_Bound() ; r.run(n) ; o["Backend_Bound"] = n
        n = Resource_Bound() ; r.run(n) ; o["Resource_Bound"] = n
        n = Mem_Scheduler() ; r.run(n) ; o["Mem_Scheduler"] = n
        n = Non_Mem_Scheduler() ; r.run(n) ; o["Non_Mem_Scheduler"] = n
        n = Register() ; r.run(n) ; o["Register"] = n
        n = Reorder_Buffer() ; r.run(n) ; o["Reorder_Buffer"] = n
        n = Alloc_Restriction() ; r.run(n) ; o["Alloc_Restriction"] = n
        n = Serialization() ; r.run(n) ; o["Serialization"] = n
        n = Core_Bound() ; r.run(n) ; o["Core_Bound"] = n
        n = Memory_Bound() ; r.run(n) ; o["Memory_Bound"] = n
        n = L2_Hit() ; r.run(n) ; o["L2_Hit"] = n
        n = LLC_Hit() ; r.run(n) ; o["LLC_Hit"] = n
        n = DRAM_Hit() ; r.run(n) ; o["DRAM_Hit"] = n
        n = Retiring() ; r.run(n) ; o["Retiring"] = n
        n = Base() ; r.run(n) ; o["Base"] = n
        n = FP_uops() ; r.run(n) ; o["FP_uops"] = n
        n = Other() ; r.run(n) ; o["Other"] = n
        n = MS_uops() ; r.run(n) ; o["MS_uops"] = n

        # parents

        o["Frontend_Latency"].parent = o["Frontend_Bound"]
        o["Icache"].parent = o["Frontend_Latency"]
        o["ITLB"].parent = o["Frontend_Latency"]
        o["Branch_Detect"].parent = o["Frontend_Latency"]
        o["Branch_Resteer"].parent = o["Frontend_Latency"]
        o["Frontend_Bandwidth"].parent = o["Frontend_Bound"]
        o["Cisc"].parent = o["Frontend_Bandwidth"]
        o["Decode"].parent = o["Frontend_Bandwidth"]
        o["Predecode"].parent = o["Frontend_Bandwidth"]
        o["Other_FB"].parent = o["Frontend_Bandwidth"]
        o["Branch_Mispredicts"].parent = o["Bad_Speculation"]
        o["Machine_Clears"].parent = o["Bad_Speculation"]
        o["Nuke"].parent = o["Machine_Clears"]
        o["FastNuke_MoNuke"].parent = o["Machine_Clears"]
        o["Resource_Bound"].parent = o["Backend_Bound"]
        o["Mem_Scheduler"].parent = o["Resource_Bound"]
        o["Non_Mem_Scheduler"].parent = o["Resource_Bound"]
        o["Register"].parent = o["Resource_Bound"]
        o["Reorder_Buffer"].parent = o["Resource_Bound"]
        o["Alloc_Restriction"].parent = o["Resource_Bound"]
        o["Serialization"].parent = o["Resource_Bound"]
        o["Core_Bound"].parent = o["Backend_Bound"]
        o["Memory_Bound"].parent = o["Backend_Bound"]
        o["L2_Hit"].parent = o["Memory_Bound"]
        o["LLC_Hit"].parent = o["Memory_Bound"]
        o["DRAM_Hit"].parent = o["Memory_Bound"]
        o["Base"].parent = o["Retiring"]
        o["FP_uops"].parent = o["Base"]
        o["Other"].parent = o["Base"]
        o["MS_uops"].parent = o["Retiring"]

        # user visible metrics

        n = Metric_CLKS() ; r.metric(n) ; o["CLKS"] = n
        n = Metric_SLOTS() ; r.metric(n) ; o["SLOTS"] = n
        n = Metric_IPC() ; r.metric(n) ; o["IPC"] = n
        n = Metric_CPI() ; r.metric(n) ; o["CPI"] = n
        n = Metric_UPI() ; r.metric(n) ; o["UPI"] = n
        n = Metric_IpBranch() ; r.metric(n) ; o["IpBranch"] = n
        n = Metric_Branch_per_1KI() ; r.metric(n) ; o["Branch_per_1KI"] = n
        n = Metric_IpCall() ; r.metric(n) ; o["IpCall"] = n
        n = Metric_IpLoad() ; r.metric(n) ; o["IpLoad"] = n
        n = Metric_IpStore() ; r.metric(n) ; o["IpStore"] = n
        n = Metric_IpMispredict() ; r.metric(n) ; o["IpMispredict"] = n
        n = Metric_IpFarBranch() ; r.metric(n) ; o["IpFarBranch"] = n
        n = Metric_Branch_Mispredict_Ratio() ; r.metric(n) ; o["Branch_Mispredict_Ratio"] = n
        n = Metric_Branch_Mispredict_to_Unknown_Branch_Ratio() ; r.metric(n) ; o["Branch_Mispredict_to_Unknown_Branch_Ratio"] = n
        n = Metric_Microcode_Uop_Ratio() ; r.metric(n) ; o["Microcode_Uop_Ratio"] = n
        n = Metric_FPDiv_Uop_Ratio() ; r.metric(n) ; o["FPDiv_Uop_Ratio"] = n
        n = Metric_IDiv_Uop_Ratio() ; r.metric(n) ; o["IDiv_Uop_Ratio"] = n
        n = Metric_X87_Uop_Ratio() ; r.metric(n) ; o["X87_Uop_Ratio"] = n
        n = Metric_Turbo_Utilization() ; r.metric(n) ; o["Turbo_Utilization"] = n
        n = Metric_Kernel_Utilization() ; r.metric(n) ; o["Kernel_Utilization"] = n
        n = Metric_Estimated_Pause_Cost() ; r.metric(n) ; o["Estimated_Pause_Cost"] = n
        n = Metric_Cycles_per_Demand_Load_L2_Hit() ; r.metric(n) ; o["Cycles_per_Demand_Load_L2_Hit"] = n
        n = Metric_Cycles_per_Demand_Load_LLC_Hit() ; r.metric(n) ; o["Cycles_per_Demand_Load_LLC_Hit"] = n
        n = Metric_Cycles_per_Demand_Load_DRAM_Hit() ; r.metric(n) ; o["Cycles_per_Demand_Load_DRAM_Hit"] = n
        n = Metric_Inst_Miss_Cost_L2Hit() ; r.metric(n) ; o["Inst_Miss_Cost_L2Hit"] = n
        n = Metric_Inst_Miss_Cost_LLCHit() ; r.metric(n) ; o["Inst_Miss_Cost_LLCHit"] = n
        n = Metric_Inst_Miss_Cost_DRAMHit() ; r.metric(n) ; o["Inst_Miss_Cost_DRAMHit"] = n
        n = Metric_MemLoad_per_1KI() ; r.metric(n) ; o["MemLoad_per_1KI"] = n

        # references between groups

        o["Core_Bound"].Memory_Bound = o["Memory_Bound"]
        o["Core_Bound"].Backend_Bound = o["Backend_Bound"]

        # siblings cross-tree

