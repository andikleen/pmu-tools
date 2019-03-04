
#
# auto generated TopDown/TMAM 3.5-full description for Intel 2nd gen Core (code named SandyBridge)
# Please see http://ark.intel.com for more details on these CPUs.
#
# References:
# http://halobates.de/blog/p/262
# https://sites.google.com/site/analysismethods/yasin-pubs
# https://download.01.org/perfmon/
#

# Helpers

print_error = lambda msg: False
smt_enabled = False
ebs_mode = False
version = "3.5-full"
base_frequency = -1.0
model = ""
Memory = 0

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

Pipeline_Width = 4
Mem_L3_Weight = 7
Mem_STLB_Hit_Cost = 7
BAClear_Cost = 12
MS_Switches_Cost = 3
OneMillion = 1000000
OneBillion = 1000000000

# Aux. formulas


# Floating Point computational (arithmetic) Operations Count
def FLOP_Count(self, EV, level):
    return (1 *(EV("FP_COMP_OPS_EXE.SSE_SCALAR_SINGLE", level) + EV("FP_COMP_OPS_EXE.SSE_SCALAR_DOUBLE", level)) + 2 * EV("FP_COMP_OPS_EXE.SSE_PACKED_DOUBLE", level) + 4 *(EV("FP_COMP_OPS_EXE.SSE_PACKED_SINGLE", level) + EV("SIMD_FP_256.PACKED_DOUBLE", level)) + 8 * EV("SIMD_FP_256.PACKED_SINGLE", level))

def Fetched_Uops(self, EV, level):
    return (EV("IDQ.DSB_UOPS", level) + EV("LSD.UOPS", level) + EV("IDQ.MITE_UOPS", level) + EV("IDQ.MS_UOPS", level))

def Recovery_Cycles(self, EV, level):
    return (EV("INT_MISC.RECOVERY_CYCLES_ANY", level) / 2) if smt_enabled else EV("INT_MISC.RECOVERY_CYCLES", level)

def Execute_Cycles(self, EV, level):
    return (EV("UOPS_DISPATCHED.CORE:c1", level) / 2) if smt_enabled else EV("UOPS_DISPATCHED.CORE:c1", level)

def ITLB_Miss_Cycles(self, EV, level):
    return (12 * EV("ITLB_MISSES.STLB_HIT", level) + EV("ITLB_MISSES.WALK_DURATION", level))

def Frontend_RS_Empty_Cycles(self, EV, level):
    EV("RS_EVENTS.EMPTY_CYCLES", level)
    return EV("RS_EVENTS.EMPTY_CYCLES", level) if(self.Frontend_Latency.compute(EV)> 0.1)else 0

def Frontend_Latency_Cycles(self, EV, level):
    return EV(lambda EV , level :  min(EV("CPU_CLK_UNHALTED.THREAD", level) , EV("IDQ_UOPS_NOT_DELIVERED.CYCLES_0_UOPS_DELIV.CORE", level)) , level )

def STALLS_MEM_ANY(self, EV, level):
    return EV(lambda EV , level :  min(EV("CPU_CLK_UNHALTED.THREAD", level) , EV("CYCLE_ACTIVITY.STALLS_L1D_PENDING", level)) , level )

def STALLS_TOTAL(self, EV, level):
    return EV(lambda EV , level :  min(EV("CPU_CLK_UNHALTED.THREAD", level) , EV("CYCLE_ACTIVITY.CYCLES_NO_DISPATCH", level)) , level )

def ORO_DRD_Any_Cycles(self, EV, level):
    return EV(lambda EV , level :  min(EV("CPU_CLK_UNHALTED.THREAD", level) , EV("OFFCORE_REQUESTS_OUTSTANDING.CYCLES_WITH_DATA_RD", level)) , level )

def ORO_DRD_BW_Cycles(self, EV, level):
    return EV(lambda EV , level :  min(EV("CPU_CLK_UNHALTED.THREAD", level) , EV("OFFCORE_REQUESTS_OUTSTANDING.ALL_DATA_RD:c6", level)) , level )

def Few_Uops_Executed_Threshold(self, EV, level):
    EV("UOPS_DISPATCHED.THREAD:c3", level)
    EV("UOPS_DISPATCHED.THREAD:c2", level)
    return EV("UOPS_DISPATCHED.THREAD:c3", level) if(IPC(self, EV, level)> 1.8)else EV("UOPS_DISPATCHED.THREAD:c2", level)

def Backend_Bound_Cycles(self, EV, level):
    return (STALLS_TOTAL(self, EV, level) + EV("UOPS_DISPATCHED.THREAD:c1", level) - Few_Uops_Executed_Threshold(self, EV, level) - Frontend_RS_Empty_Cycles(self, EV, level) + EV("RESOURCE_STALLS.SB", level))

def Memory_Bound_Fraction(self, EV, level):
    return (STALLS_MEM_ANY(self, EV, level) + EV("RESOURCE_STALLS.SB", level)) / Backend_Bound_Cycles(self, EV, level)

def Mem_L3_Hit_Fraction(self, EV, level):
    return EV("MEM_LOAD_UOPS_RETIRED.LLC_HIT", level) /(EV("MEM_LOAD_UOPS_RETIRED.LLC_HIT", level) + Mem_L3_Weight * EV("MEM_LOAD_UOPS_MISC_RETIRED.LLC_MISS", level))

def Mispred_Clears_Fraction(self, EV, level):
    return EV("BR_MISP_RETIRED.ALL_BRANCHES", level) /(EV("BR_MISP_RETIRED.ALL_BRANCHES", level) + EV("MACHINE_CLEARS.COUNT", level))

def Retire_Uop_Fraction(self, EV, level):
    return EV("UOPS_RETIRED.RETIRE_SLOTS", level) / EV("UOPS_ISSUED.ANY", level)

def DurationTimeInSeconds(self, EV, level):
    return 0 if 0 > 0 else(EV("interval-ms", 0) / 1000 )

def HighIPC(self, EV, level):
    return IPC(self, EV, level) / Pipeline_Width

# Instructions Per Cycle (per logical thread)
def IPC(self, EV, level):
    return EV("INST_RETIRED.ANY", level) / CLKS(self, EV, level)

# Uops Per Instruction
def UPI(self, EV, level):
    return EV("UOPS_RETIRED.RETIRE_SLOTS", level) / EV("INST_RETIRED.ANY", level)

# Rough Estimation of fraction of fetched lines bytes that were likely (includes speculatively fetches) consumed by program instructions
def IFetch_Line_Utilization(self, EV, level):
    return min(1 , EV("UOPS_ISSUED.ANY", level) /(UPI(self, EV, level)* 32 *(EV("ICACHE.HIT", level) + EV("ICACHE.MISSES", level)) / 4))

# Fraction of Uops delivered by the DSB (aka Decoded ICache; or Uop Cache). See section 'Decoded ICache' in Optimization Manual. http://www.intel.com/content/www/us/en/architecture-and-technology/64-ia-32-architectures-optimization-manual.html
def DSB_Coverage(self, EV, level):
    return EV("IDQ.DSB_UOPS", level) / Fetched_Uops(self, EV, level)

# Fraction of Uops delivered by the LSD (Loop Stream Detector; aka Loop Cache)
def LSD_Coverage(self, EV, level):
    return EV("LSD.UOPS", level) / Fetched_Uops(self, EV, level)

# Cycles Per Instruction (threaded)
def CPI(self, EV, level):
    return 1 / IPC(self, EV, level)

# Per-thread actual clocks when the logical processor is active.
def CLKS(self, EV, level):
    return EV("CPU_CLK_UNHALTED.THREAD", level)

# Total issue-pipeline slots ( per core )
def SLOTS(self, EV, level):
    return Pipeline_Width * CORE_CLKS(self, EV, level)

# Total number of retired Instructions
def Instructions(self, EV, level):
    return EV("INST_RETIRED.ANY", level)

# Instructions Per Cycle (per physical core)
def CoreIPC(self, EV, level):
    return EV("INST_RETIRED.ANY", level) / CORE_CLKS(self, EV, level)

# Floating Point Operations Per Cycle
def FLOPc(self, EV, level):
    return FLOP_Count(self, EV, level) / CORE_CLKS(self, EV, level)

# Instruction-Level-Parallelism (average number of uops executed when there is at least 1 uop executed)
def ILP(self, EV, level):
    return EV("UOPS_DISPATCHED.THREAD", level) / Execute_Cycles(self, EV, level)

# Branch Misprediction Cost: Fraction of TopDown slots wasted per non-speculative branch misprediction (jeclear)
def Branch_Misprediction_Cost(self, EV, level):
    return 0

# Core actual clocks when any thread is active on the physical core
def CORE_CLKS(self, EV, level):
    return ((EV("CPU_CLK_UNHALTED.THREAD", level) / 2)*(1 + EV("CPU_CLK_UNHALTED.ONE_THREAD_ACTIVE", level) / EV("CPU_CLK_UNHALTED.REF_XCLK", level))) if ebs_mode else(EV("CPU_CLK_UNHALTED.THREAD_ANY", level) / 2) if smt_enabled else CLKS(self, EV, level)

# Actual Average Latency for L1 data-cache miss demand loads (in core cycles)
def Load_Miss_Real_Latency(self, EV, level):
    return 0

# Memory-Level-Parallelism (average number of L1 miss demand load when there is at least one such miss. Per-thread)
def MLP(self, EV, level):
    return 0

# Utilization of the core's Page Walker(s) serving STLB misses triggered by instruction/Load/Store accesses
def Page_Walks_Utilization(self, EV, level):
    return 0

# Average data fill bandwidth to the L1 data cache [GB / sec]
def L1D_Cache_Fill_BW(self, EV, level):
    return 0

# Average data fill bandwidth to the L2 cache [GB / sec]
def L2_Cache_Fill_BW(self, EV, level):
    return 0

# Average per-core data fill bandwidth to the L3 cache [GB / sec]
def L3_Cache_Fill_BW(self, EV, level):
    return 0

# Average per-core data fill bandwidth to the L3 cache [GB / sec]
def L3_Cache_Access_BW(self, EV, level):
    return 0

# L1 cache true misses per kilo instruction for retired demand loads
def L1MPKI(self, EV, level):
    return 0

# L2 cache true misses per kilo instruction for retired demand loads
def L2MPKI(self, EV, level):
    return 0

# L2 cache misses per kilo instruction for all request types (including speculative)
def L2MPKI_All(self, EV, level):
    return 0

# L2 cache misses per kilo instruction for all demand loads  (including speculative)
def L2MPKI_Load(self, EV, level):
    return 0

# L2 cache hits per kilo instruction for all request types (including speculative)
def L2HPKI_All(self, EV, level):
    return 0

# L2 cache hits per kilo instruction for all demand loads  (including speculative)
def L2HPKI_Load(self, EV, level):
    return 0

# L3 cache true misses per kilo instruction for retired demand loads
def L3MPKI(self, EV, level):
    return 0

# Average CPU Utilization
def CPU_Utilization(self, EV, level):
    return EV("CPU_CLK_UNHALTED.REF_TSC", level) / EV("msr/tsc/", 0)

# Measured Average Frequency for unhalted processors [GHz]
def Average_Frequency(self, EV, level):
    return base_frequency * Turbo_Utilization(self, EV, level) / 1000

# Giga Floating Point Operations Per Second
def GFLOPs(self, EV, level):
    return (FLOP_Count(self, EV, level) / OneBillion) / EV("interval-s", 0)

# Average Frequency Utilization relative nominal frequency
def Turbo_Utilization(self, EV, level):
    return CLKS(self, EV, level) / EV("CPU_CLK_UNHALTED.REF_TSC", level)

# Fraction of cycles where both hardware threads were active
def SMT_2T_Utilization(self, EV, level):
    return 1 - EV("CPU_CLK_THREAD_UNHALTED.ONE_THREAD_ACTIVE", level) /(EV("CPU_CLK_THREAD_UNHALTED.REF_XCLK_ANY", level) / 2) if smt_enabled else 0

# Fraction of cycles spent in Kernel mode
def Kernel_Utilization(self, EV, level):
    return EV("CPU_CLK_UNHALTED.REF_TSC:sup", level) / EV("CPU_CLK_UNHALTED.REF_TSC", level)

# Average external Memory Bandwidth Use for reads and writes [GB / sec]
def DRAM_BW_Use(self, EV, level):
    return 64 *(EV("UNC_ARB_TRK_REQUESTS.ALL", level) + EV("UNC_ARB_COH_TRK_REQUESTS.ALL", level)) / OneMillion / EV("interval-s", 0) / 1000

# Average latency of all requests to external memory (in Uncore cycles)
def MEM_Request_Latency(self, EV, level):
    return EV("UNC_ARB_TRK_OCCUPANCY.ALL", level) / EV("UNC_ARB_TRK_REQUESTS.ALL", level)

# Average number of parallel requests to external memory. Accounts for all requests
def MEM_Parallel_Requests(self, EV, level):
    return EV("UNC_ARB_TRK_OCCUPANCY.ALL", level) / EV("UNC_ARB_TRK_OCCUPANCY.CYCLES_WITH_ANY_REQUEST", level)

# Average latency of data read request to external DRAM memory [in nanoseconds]. Accounts for demand loads and L1/L2 data-read prefetches
def MEM_DRAM_Read_Latency(self, EV, level):
    return 0

# Total package Power in Watts
def Power(self, EV, level):
    return 0

# Run duration time in seconds
def Time(self, EV, level):
    return EV("interval-s", 0)

# Socket actual clocks when any core is active on that socket
def Socket_CLKS(self, EV, level):
    return EV("UNC_CLOCK.SOCKET", level)

# Event groups


class Frontend_Bound:
    name = "Frontend_Bound"
    domain = "Slots"
    area = "FE"
    desc = """
This category represents fraction of slots where the
processor's Frontend undersupplies its Backend. Frontend
denotes the first part of the processor core responsible to
fetch operations that are executed later on by the Backend
part. Within the Frontend; a branch predictor predicts the
next address to fetch; cache-lines are fetched from the
memory subsystem; parsed into instructions; and lastly
decoded into micro-ops (uops). Ideally the Frontend can
issue 4 uops every cycle to the Backend. Frontend Bound
denotes unutilized issue-slots when there is no Backend
stall; i.e. bubbles where Frontend delivered no uops while
Backend could have accepted them. For example; stalls due to
instruction-cache misses would be categorized under Frontend
Bound."""
    level = 1
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['TopDownL1']
    def compute(self, EV):
        try:
            self.val = EV("IDQ_UOPS_NOT_DELIVERED.CORE", 1) / SLOTS(self, EV, 1)
            self.thresh = (self.val > 0.2)
        except ZeroDivisionError:
            handle_error(self, "Frontend_Bound zero division")
        return self.val

class Frontend_Latency:
    name = "Frontend_Latency"
    domain = "Slots"
    area = "FE"
    desc = """
This metric represents fraction of slots the CPU was stalled
due to Frontend latency issues.  For example; instruction-
cache misses; iTLB misses or fetch stalls after a branch
misprediction are categorized under Frontend Latency. In
such cases; the Frontend eventually delivers no uops for
some period."""
    level = 2
    htoff = False
    sample = ['RS_EVENTS.EMPTY_END']
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Frontend_Bound', 'TopDownL2']
    def compute(self, EV):
        try:
            self.val = Pipeline_Width * Frontend_Latency_Cycles(self, EV, 2) / SLOTS(self, EV, 2)
            self.thresh = (self.val > 0.15) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Frontend_Latency zero division")
        return self.val

class ICache_Misses:
    name = "ICache_Misses"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents fraction of cycles the CPU was
stalled due to instruction cache misses.. Using compiler's
Profile-Guided Optimization (PGO) can reduce i-cache misses
through improved hot code layout."""
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Frontend_Latency']
    def compute(self, EV):
        try:
            self.val = 0
            self.thresh = (self.val > 0.05) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "ICache_Misses zero division")
        return self.val

class ITLB_Misses:
    name = "ITLB_Misses"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents fraction of cycles the CPU was
stalled due to instruction TLB misses.. Consider large 2M
pages for code (selectively prefer hot large-size function,
due to limited 2M entries). Linux options: standard binaries
use libhugetlbfs; Hfsort.. https://github.com/libhugetlbfs/l
ibhugetlbfs;https://research.fb.com/publications/optimizing-
function-placement-for-large-scale-data-center-
applications-2/"""
    level = 3
    htoff = False
    sample = ['ITLB_MISSES.WALK_COMPLETED']
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Frontend_Latency', 'TLB']
    def compute(self, EV):
        try:
            self.val = ITLB_Miss_Cycles(self, EV, 3) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.05) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "ITLB_Misses zero division")
        return self.val

class Branch_Resteers:
    name = "Branch_Resteers"
    domain = "Clocks_Estimated"
    area = "FE"
    desc = """
This metric represents fraction of cycles the CPU was
stalled due to Branch Resteers. Branch Resteers estimates
the Frontend delay in fetching operations from corrected
path; following all sorts of miss-predicted branches. For
example; branchy code with lots of miss-predictions might
get categorized under Branch Resteers. Note the value of
this node may overlap with its siblings."""
    level = 3
    htoff = False
    sample = ['BR_MISP_RETIRED.ALL_BRANCHES:pp']
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Bad_Speculation', 'Frontend_Latency']
    def compute(self, EV):
        try:
            self.val = BAClear_Cost *(EV("BR_MISP_RETIRED.ALL_BRANCHES", 3) + EV("MACHINE_CLEARS.COUNT", 3) + EV("BACLEARS.ANY", 3)) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.05) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Branch_Resteers zero division")
        return self.val

class Mispredicts_Resteers:
    name = "Mispredicts_Resteers"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents fraction of cycles the CPU was
stalled due to Branch Resteers as a result of Branch
Misprediction at execution stage."""
    level = 4
    htoff = False
    sample = ['BR_MISP_RETIRED.ALL_BRANCHES:pp']
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Branch_Mispredicts']
    def compute(self, EV):
        try:
            self.val = 0
            self.thresh = (self.val > 0.05) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Mispredicts_Resteers zero division")
        return self.val

class Clears_Resteers:
    name = "Clears_Resteers"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents fraction of cycles the CPU was
stalled due to Branch Resteers as a result of Machine
Clears."""
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Machine_Clears']
    def compute(self, EV):
        try:
            self.val = 0
            self.thresh = (self.val > 0.05) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Clears_Resteers zero division")
        return self.val

class Unknown_Branches:
    name = "Unknown_Branches"
    domain = "Clocks_Estimated"
    area = "FE"
    desc = """
This metric represents fraction of cycles the CPU was
stalled due to new branch address clears. These are fetched
branches the Branch Prediction Unit was unable to recognize
(First fetch or hitting BPU capacity limit)."""
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Unknown_Branches']
    def compute(self, EV):
        try:
            self.val = 0
            self.thresh = (self.val > 0.05) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Unknown_Branches zero division")
        return self.val

class DSB_Switches:
    name = "DSB_Switches"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents fraction of cycles the CPU was
stalled due to switches from DSB to MITE pipelines. The DSB
(decoded i-cache; introduced with the Sandy Bridge
microarchitecture) pipeline has shorter latency and
delivered higher bandwidth than the MITE (legacy instruction
decode pipeline). Switching between the two pipelines can
cause penalties. This metric estimates when such penalty can
be exposed. Optimizing for better DSB hit rate may be
considered.. See section 'Optimization for Decoded Icache'
in Optimization Manual:.
http://www.intel.com/content/www/us/en/architecture-and-
technology/64-ia-32-architectures-optimization-manual.html"""
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['DSB', 'Frontend_Latency']
    def compute(self, EV):
        try:
            self.val = EV("DSB2MITE_SWITCHES.PENALTY_CYCLES", 3) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.05) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "DSB_Switches zero division")
        return self.val

class LCP:
    name = "LCP"
    domain = "Clocks"
    area = "FE"
    desc = """
This metric represents fraction of cycles CPU was stalled
due to Length Changing Prefixes (LCPs). Using proper
compiler flags or Intel Compiler by default will certainly
avoid this."""
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Frontend_Latency']
    def compute(self, EV):
        try:
            self.val = EV("ILD_STALL.LCP", 3) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.05) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "LCP zero division")
        return self.val

class MS_Switches:
    name = "MS_Switches"
    domain = "Clocks"
    area = "FE"
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
    level = 3
    htoff = False
    sample = ['IDQ.MS_SWITCHES']
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Frontend_Latency', 'Microcode_Sequencer']
    def compute(self, EV):
        try:
            self.val = MS_Switches_Cost * EV("IDQ.MS_SWITCHES", 3) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.05) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "MS_Switches zero division")
        return self.val

class Frontend_Bandwidth:
    name = "Frontend_Bandwidth"
    domain = "Slots"
    area = "FE"
    desc = """
This metric represents fraction of slots the CPU was stalled
due to Frontend bandwidth issues.  For example;
inefficiencies at the instruction decoders; or code
restrictions for caching in the DSB (decoded uops cache) are
categorized under Frontend Bandwidth. In such cases; the
Frontend typically delivers non-optimal amount of uops to
the Backend (less than four)."""
    level = 2
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Frontend_Bound', 'TopDownL2']
    def compute(self, EV):
        try:
            self.val = self.Frontend_Bound.compute(EV) - self.Frontend_Latency.compute(EV)
            self.thresh = (self.val > 0.1) & self.parent.thresh & (HighIPC(self, EV, 2) > 0)
        except ZeroDivisionError:
            handle_error(self, "Frontend_Bandwidth zero division")
        return self.val

class Bad_Speculation:
    name = "Bad_Speculation"
    domain = "Slots"
    area = "BAD"
    desc = """
This category represents fraction of slots wasted due to
incorrect speculations. This include slots used to issue
uops that do not eventually get retired and slots for which
the issue-pipeline was blocked due to recovery from earlier
incorrect speculation. For example; wasted work due to miss-
predicted branches are categorized under Bad Speculation
category. Incorrect data speculation followed by Memory
Ordering Nukes is another example."""
    level = 1
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Bad_Speculation', 'TopDownL1']
    def compute(self, EV):
        try:
            self.val = (EV("UOPS_ISSUED.ANY", 1) - EV("UOPS_RETIRED.RETIRE_SLOTS", 1) + Pipeline_Width * Recovery_Cycles(self, EV, 1)) / SLOTS(self, EV, 1)
            self.thresh = (self.val > 0.1)
        except ZeroDivisionError:
            handle_error(self, "Bad_Speculation zero division")
        return self.val

class Branch_Mispredicts:
    name = "Branch_Mispredicts"
    domain = "Slots"
    area = "BAD"
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
    level = 2
    htoff = False
    sample = ['BR_MISP_RETIRED.ALL_BRANCHES:pp']
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Bad_Speculation', 'Branch_Mispredicts', 'TopDownL2']
    def compute(self, EV):
        try:
            self.val = Mispred_Clears_Fraction(self, EV, 2)* self.Bad_Speculation.compute(EV)
            self.thresh = (self.val > 0.05) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Branch_Mispredicts zero division")
        return self.val

class Machine_Clears:
    name = "Machine_Clears"
    domain = "Slots"
    area = "BAD"
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
    level = 2
    htoff = False
    sample = ['MACHINE_CLEARS.COUNT']
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Bad_Speculation', 'Machine_Clears', 'TopDownL2']
    def compute(self, EV):
        try:
            self.val = self.Bad_Speculation.compute(EV) - self.Branch_Mispredicts.compute(EV)
            self.thresh = (self.val > 0.05) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Machine_Clears zero division")
        return self.val

class Backend_Bound:
    name = "Backend_Bound"
    domain = "Slots"
    area = "BE"
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
    level = 1
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['TopDownL1']
    def compute(self, EV):
        try:
            self.val = 1 -(self.Frontend_Bound.compute(EV) + self.Bad_Speculation.compute(EV) + self.Retiring.compute(EV))
            self.thresh = (self.val > 0.1)
        except ZeroDivisionError:
            handle_error(self, "Backend_Bound zero division")
        return self.val

class Memory_Bound:
    name = "Memory_Bound"
    domain = "Slots"
    area = "BE/Mem"
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
    level = 2
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Backend_Bound', 'TopDownL2']
    def compute(self, EV):
        try:
            self.val = Memory_Bound_Fraction(self, EV, 2)* self.Backend_Bound.compute(EV)
            self.thresh = (self.val > 0.1) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Memory_Bound zero division")
        return self.val

class L1_Bound:
    name = "L1_Bound"
    domain = "Stalls"
    area = "BE/Mem"
    desc = """
This metric estimates how often the CPU was stalled without
loads missing the L1 data cache.  The L1 data cache
typically has the shortest latency.  However; in certain
cases like loads blocked on older stores; a load might
suffer due to high latency even though it is being satisfied
by the L1. Another example is loads who miss in the TLB.
These cases are characterized by execution unit stalls;
while some non-completed demand load lives in the machine
without having that demand load missing the L1 cache."""
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Cache_Misses', 'Memory_Bound']
    def compute(self, EV):
        try:
            self.val = 0
            self.thresh = (self.val > 0.1) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "L1_Bound zero division")
        return self.val

class DTLB_Load:
    name = "DTLB_Load"
    domain = "Clocks_Estimated"
    area = "BE/Mem"
    desc = """
This metric roughly estimates the fraction of cycles where
the TLB was missed by load accesses. TLBs (Translation Look-
aside Buffers) are processor caches for recently used
entries out of the Page Tables that are used to map virtual-
to physical-addresses by the operating system. This metric
approximates the potential delay of demand loads missing the
first-level data TLB (assuming worst case scenario with back
to back misses to different pages). This includes hitting in
the second-level TLB (STLB) as well as performing a hardware
page walk on an STLB miss.."""
    level = 4
    htoff = False
    sample = ['MEM_UOPS_RETIRED.STLB_MISS_LOADS:pp']
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['TLB']
    def compute(self, EV):
        try:
            self.val = (Mem_STLB_Hit_Cost * EV("DTLB_LOAD_MISSES.STLB_HIT", 4) + EV("DTLB_LOAD_MISSES.WALK_DURATION", 4)) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.1) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "DTLB_Load zero division")
        return self.val

class Lock_Latency:
    name = "Lock_Latency"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric represents fraction of cycles the CPU spent
handling cache misses due to lock operations. Due to the
microarchitecture handling of locks; they are classified as
L1_Bound regardless of what memory source satisfied them."""
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = 0
            self.thresh = (self.val > 0.2) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Lock_Latency zero division")
        return self.val

class L2_Bound:
    name = "L2_Bound"
    domain = "Stalls"
    area = "BE/Mem"
    desc = """
This metric estimates how often the CPU was stalled due to
L2 cache accesses by loads.  Avoiding cache misses (i.e. L1
misses/L2 hits) can improve the latency and increase
performance."""
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Cache_Misses', 'Memory_Bound']
    def compute(self, EV):
        try:
            self.val = 0
            self.thresh = (self.val > 0.05) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "L2_Bound zero division")
        return self.val

class L3_Bound:
    name = "L3_Bound"
    domain = "Stalls"
    area = "BE/Mem"
    desc = """
This metric estimates how often the CPU was stalled due to
loads accesses to L3 cache or contended with a sibling Core.
Avoiding cache misses (i.e. L2 misses/L3 hits) can improve
the latency and increase performance."""
    level = 3
    htoff = False
    sample = ['MEM_LOAD_UOPS_RETIRED.LLC_HIT:pp']
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Cache_Misses', 'Memory_Bound']
    def compute(self, EV):
        try:
            self.val = Mem_L3_Hit_Fraction(self, EV, 3)* EV("CYCLE_ACTIVITY.STALLS_L2_PENDING", 3) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.05) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "L3_Bound zero division")
        return self.val

class DRAM_Bound:
    name = "DRAM_Bound"
    domain = "Stalls"
    area = "BE/Mem"
    desc = """
This metric estimates how often the CPU was stalled on
accesses to external memory (DRAM) by loads. Better caching
can improve the latency and increase performance."""
    level = 3
    htoff = False
    sample = ['MEM_LOAD_UOPS_MISC_RETIRED.LLC_MISS:pp']
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Memory_Bound']
    def compute(self, EV):
        try:
            self.val = (1 - Mem_L3_Hit_Fraction(self, EV, 3))* EV("CYCLE_ACTIVITY.STALLS_L2_PENDING", 3) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.1) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "DRAM_Bound zero division")
        return self.val

class MEM_Bandwidth:
    name = "MEM_Bandwidth"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric estimates fraction of cycles where the core's
performance was likely hurt due to approaching bandwidth
limits of external memory (DRAM).  The underlying heuristic
assumes that a similar off-core traffic is generated by all
IA cores. This metric does not aggregate non-data-read
requests by this thread; requests from other IA
threads/cores/sockets; or other non-IA devices like GPU;
hence the maximum external memory bandwidth limits may or
may not be approached when this metric is flagged (see
Uncore counters for that).. Improve data accesses to reduce
cacheline transfers from/to memory. Examples: 1) Consume all
bytes of a each cacheline before it is evicted (e.g. reorder
structure elements and split non-hot ones), 2) merge
computed-limited with BW-limited loops, 3) NUMA
optimizations in multi-socket system. Note: software
prefetches will not help BW-limited application.."""
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Memory_BW']
    def compute(self, EV):
        try:
            self.val = ORO_DRD_BW_Cycles(self, EV, 4) / CLKS(self, EV, 4)
            self.thresh = (self.val > 0.1) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "MEM_Bandwidth zero division")
        return self.val

class MEM_Latency:
    name = "MEM_Latency"
    domain = "Clocks"
    area = "BE/Mem"
    desc = """
This metric estimates fraction of cycles where the
performance was likely hurt due to latency from external
memory (DRAM).  This metric does not aggregate requests from
other threads/cores/sockets (see Uncore counters for that)..
Improve data accesses or interleave them with compute.
Examples: 1) Data layout re-structuring, 2) Software
Prefetches (also through the compiler).."""
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Memory_Lat']
    def compute(self, EV):
        try:
            self.val = ORO_DRD_Any_Cycles(self, EV, 4) / CLKS(self, EV, 4) - self.MEM_Bandwidth.compute(EV)
            self.thresh = (self.val > 0.1) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "MEM_Latency zero division")
        return self.val

class Store_Bound:
    name = "Store_Bound"
    domain = "Stalls"
    area = "BE/Mem"
    desc = """
This metric estimates how often CPU was stalled  due to
store memory accesses. Even though store accesses do not
typically stall out-of-order CPUs; there are few cases where
stores can lead to actual stalls. This metric will be
flagged should any of these cases be a bottleneck."""
    level = 3
    htoff = False
    sample = ['MEM_UOPS_RETIRED.ALL_STORES:pp']
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Memory_Bound']
    def compute(self, EV):
        try:
            self.val = EV("RESOURCE_STALLS.SB", 3) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.2) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Store_Bound zero division")
        return self.val

class Store_Latency:
    name = "Store_Latency"
    domain = "Clocks_Estimated"
    area = "BE/Mem"
    desc = """
This metric estimates fraction of cycles the CPU spent
handling L1D store misses. Store accesses usually less
impact out-of-order core performance; however; holding
resources for longer time can lead into undesired
implications (e.g. contention on L1D fill-buffer entries -
see FB_Full). Consider to avoid/reduce unnecessary (or
easily load-able/computable) memory store."""
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Memory_Lat']
    def compute(self, EV):
        try:
            self.val = 0
            self.thresh = (self.val > 0.1) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Store_Latency zero division")
        return self.val

class DTLB_Store:
    name = "DTLB_Store"
    domain = "Clocks_Estimated"
    area = "BE/Mem"
    desc = """
This metric represents fraction of cycles spent handling
first-level data TLB store misses.  As with ordinary data
caching; focus on improving data locality and reducing
working-set size to reduce DTLB overhead.  Additionally;
consider using profile-guided optimization (PGO) to
collocate frequently-used data on the same page.  Try using
larger page sizes for large amounts of frequently-used data."""
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['TLB']
    def compute(self, EV):
        try:
            self.val = 0
            self.thresh = (self.val > 0.05) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "DTLB_Store zero division")
        return self.val

class Core_Bound:
    name = "Core_Bound"
    domain = "Slots"
    area = "BE/Core"
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
    level = 2
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Backend_Bound', 'TopDownL2']
    def compute(self, EV):
        try:
            self.val = self.Backend_Bound.compute(EV) - self.Memory_Bound.compute(EV)
            self.thresh = (self.val > 0.1) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Core_Bound zero division")
        return self.val

class Divider:
    name = "Divider"
    domain = "Clocks"
    area = "BE/Core"
    desc = """
This metric represents fraction of cycles where the Divider
unit was active. Divide and square root instructions are
performed by the Divider unit and can take considerably
longer latency than integer or Floating Point addition;
subtraction; or multiplication."""
    level = 3
    htoff = False
    sample = ['ARITH.FPU_DIV_ACTIVE']
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("ARITH.FPU_DIV_ACTIVE", 3) / CORE_CLKS(self, EV, 3)
            self.thresh = (self.val > 0.2) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Divider zero division")
        return self.val

class Ports_Utilization:
    name = "Ports_Utilization"
    domain = "Clocks"
    area = "BE/Core"
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
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = (Backend_Bound_Cycles(self, EV, 3) - EV("RESOURCE_STALLS.SB", 3) - STALLS_MEM_ANY(self, EV, 3)) / CLKS(self, EV, 3)
            self.thresh = (self.val > 0.2) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Ports_Utilization zero division")
        return self.val

class G0_Ports_Utilized:
    name = "0_Ports_Utilized"
    domain = "CoreClocks"
    area = "BE/Core"
    desc = """
This metric represents Core fraction of cycles CPU executed
no uops on any execution port. Long-latency instructions
like divides may contribute to this metric.. Check assembly
view and Appendix C in Optimization Manual to find out
instructions with say 5 or more cycles latency..
http://www.intel.com/content/www/us/en/architecture-and-
technology/64-ia-32-architectures-optimization-manual.html"""
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Ports_Utilization']
    def compute(self, EV):
        try:
            self.val = 0
            self.thresh = (self.val > 0.2) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "G0_Ports_Utilized zero division")
        return self.val

class Serializing_Operation:
    name = "Serializing_Operation"
    domain = "Clocks"
    area = "BE/Core"
    desc = """
This metric represents fraction of cycles the CPU issue-
pipeline was stalled due to serializing operations.
Instructions like CPUID; WRMSR or LFENCE serialize the out-
of-order execution which may limit performance."""
    level = 5
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = 0
            self.thresh = (self.val > 0.1) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Serializing_Operation zero division")
        return self.val

class G1_Port_Utilized:
    name = "1_Port_Utilized"
    domain = "CoreClocks"
    area = "BE/Core"
    desc = """
This metric represents Core fraction of cycles where the CPU
executed total of 1 uop per cycle on all execution ports.
This can be due to heavy data-dependency among software
instructions; or over oversubscribing a particular hardware
resource. In some other cases with high 1_Port_Utilized and
L1_Bound; this metric can point to L1 data-cache latency
bottleneck that may not necessarily manifest with complete
execution starvation (due to the short L1 latency e.g.
walking a linked list) - looking at the assembly can be
helpful. Tip: consider 'Core Ports Saturation' analysis-type
as next step."""
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Ports_Utilization']
    def compute(self, EV):
        try:
            self.val = 0
            self.thresh = (self.val > 0.2) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "G1_Port_Utilized zero division")
        return self.val

class G2_Ports_Utilized:
    name = "2_Ports_Utilized"
    domain = "CoreClocks"
    area = "BE/Core"
    desc = """
This metric represents Core fraction of cycles CPU executed
total of 2 uops per cycle on all execution ports. Tip:
consider 'Core Port Saturation' analysis-type as next step.
Loop Vectorization -most compilers feature auto-
Vectorization options today- reduces pressure on the
execution ports as multiple elements are calculated with
same uop."""
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Ports_Utilization']
    def compute(self, EV):
        try:
            self.val = 0
            self.thresh = (self.val > 0.2) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "G2_Ports_Utilized zero division")
        return self.val

class G3m_Ports_Utilized:
    name = "3m_Ports_Utilized"
    domain = "CoreClocks"
    area = "BE/Core"
    desc = """
This metric represents Core fraction of cycles CPU executed
total of 3 or more uops per cycle on all execution ports.
Tip: consider 'Core Port Saturation' analysis-type as next
step"""
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Ports_Utilization']
    def compute(self, EV):
        try:
            self.val = 0
            self.thresh = (self.val > 0.7) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "G3m_Ports_Utilized zero division")
        return self.val

class Retiring:
    name = "Retiring"
    domain = "Slots"
    area = "RET"
    desc = """
This category represents fraction of slots utilized by
useful work i.e. issued uops that eventually get retired.
Ideally; all pipeline slots would be attributed to the
Retiring category.  Retiring of 100% would indicate the
maximum 4 uops retired per cycle has been achieved.
Maximizing Retiring typically increases the Instruction-Per-
Cycle metric. Note that a high Retiring value does not
necessary mean there is no room for more performance.  For
example; Microcode assists are categorized under Retiring.
They hurt performance and can often be avoided. . A high
Retiring value for non-vectorized code may be a good hint
for programmer to consider vectorizing his code.  Doing so
essentially lets more computations be done without
significantly increasing number of instructions thus
improving the performance."""
    level = 1
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['TopDownL1']
    def compute(self, EV):
        try:
            self.val = EV("UOPS_RETIRED.RETIRE_SLOTS", 1) / SLOTS(self, EV, 1)
            self.thresh = (self.val > 0.75) | self.Microcode_Sequencer.thresh
        except ZeroDivisionError:
            handle_error(self, "Retiring zero division")
        return self.val

class Base:
    name = "Base"
    domain = "Slots"
    area = "RET"
    desc = """
This metric represents fraction of slots where the CPU was
retiring regular uops (ones not originated from the
microcode-sequencer). This correlates with total number of
instructions used by the program. A uops-per-instruction
ratio of 1 should be expected. While this is the most
desirable of the top 4 categories; high values does not
necessarily mean there no room for performance
optimizations.. Focus on techniques that reduce instruction
count or result in more efficient instructions generation
such as vectorization."""
    level = 2
    htoff = False
    sample = ['INST_RETIRED.PREC_DIST']
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['TopDownL2']
    def compute(self, EV):
        try:
            self.val = self.Retiring.compute(EV) - self.Microcode_Sequencer.compute(EV)
            self.thresh = (self.val > 0.6) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Base zero division")
        return self.val

class FP_Arith:
    name = "FP_Arith"
    domain = "Uops"
    area = "RET"
    desc = """
This metric represents overall arithmetic floating-point
(FP) uops fraction the CPU has executed (retired)"""
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Retiring']
    def compute(self, EV):
        try:
            self.val = self.X87_Use.compute(EV) + self.FP_Scalar.compute(EV) + self.FP_Vector.compute(EV)
            self.thresh = (self.val > 0.2) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "FP_Arith zero division")
        return self.val

class X87_Use:
    name = "X87_Use"
    domain = "Uops"
    area = "RET"
    desc = """
This metric serves as an approximation of legacy x87 usage.
It accounts for instructions beyond X87 FP arithmetic
operations; hence may be used as a thermometer to avoid X87
high usage and preferably upgrade to modern ISA. Tip:
consider compiler flags to generate newer AVX (or SSE)
instruction sets; which typically perform better and feature
vectors."""
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = EV("FP_COMP_OPS_EXE.X87", 4) / EV("UOPS_DISPATCHED.THREAD", 4)
            self.thresh = (self.val > 0.1) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "X87_Use zero division")
        return self.val

class FP_Scalar:
    name = "FP_Scalar"
    domain = "Uops"
    area = "RET"
    desc = """
This metric represents arithmetic floating-point (FP) scalar
uops fraction the CPU has executed (retired).. Investigate
what limits (compiler) generation of vector code."""
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['FLOPS']
    def compute(self, EV):
        try:
            self.val = (EV("FP_COMP_OPS_EXE.SSE_SCALAR_SINGLE", 4) + EV("FP_COMP_OPS_EXE.SSE_SCALAR_DOUBLE", 4)) / EV("UOPS_DISPATCHED.THREAD", 4)
            self.thresh = (self.val > 0.1) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "FP_Scalar zero division")
        return self.val

class FP_Vector:
    name = "FP_Vector"
    domain = "Uops"
    area = "RET"
    desc = """
This metric represents arithmetic floating-point (FP) vector
uops fraction the CPU has executed (retired) aggregated
across all vector widths.. Check if vector width is expected"""
    level = 4
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['FLOPS']
    def compute(self, EV):
        try:
            self.val = (EV("FP_COMP_OPS_EXE.SSE_PACKED_DOUBLE", 4) + EV("FP_COMP_OPS_EXE.SSE_PACKED_SINGLE", 4) + EV("SIMD_FP_256.PACKED_SINGLE", 4) + EV("SIMD_FP_256.PACKED_DOUBLE", 4)) / EV("UOPS_DISPATCHED.THREAD", 4)
            self.thresh = (self.val > 0.2) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "FP_Vector zero division")
        return self.val

class Other:
    name = "Other"
    domain = "Uops"
    area = "RET"
    desc = """
This metric represents non-floating-point (FP) uop fraction
the CPU has executed. If you application has no FP
operations and performs with decent IPC (Instructions Per
Cycle); this node will likely be biggest fraction."""
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = 1 - self.FP_Arith.compute(EV)
            self.thresh = (self.val > 0.3) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Other zero division")
        return self.val

class Microcode_Sequencer:
    name = "Microcode_Sequencer"
    domain = "Slots"
    area = "RET"
    desc = """
This metric represents fraction of slots the CPU was
retiring uops fetched by the Microcode Sequencer (MS) unit.
The MS is used for CISC instructions not supported by the
default decoders (like repeat move strings; or CPUID); or by
microcode assists used to address some operation modes (like
in Floating Point assists). These cases can often be
avoided.."""
    level = 2
    htoff = False
    sample = ['IDQ.MS_UOPS']
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Microcode_Sequencer', 'Retiring', 'TopDownL2']
    def compute(self, EV):
        try:
            self.val = Retire_Uop_Fraction(self, EV, 2)* EV("IDQ.MS_UOPS", 2) / SLOTS(self, EV, 2)
            self.thresh = (self.val > 0.05)
        except ZeroDivisionError:
            handle_error(self, "Microcode_Sequencer zero division")
        return self.val

class Assists:
    name = "Assists"
    domain = "Slots_Estimated"
    area = "RET"
    desc = """
This metric estimates fraction of cycles the CPU retired
uops delivered by the Microcode_Sequencer as a result of
Assists. Assists are long sequences of uops that are
required in certain corner-cases for operations that cannot
be handled natively by the execution pipeline. For example;
when working with very small floating point values (so-
called Denormals); the FP units are not set up to perform
these operations natively. Instead; a sequence of
instructions to perform the computation on the Denormals is
injected into the pipeline. Since these microcode sequences
might be hundreds of uops long; Assists can be extremely
deleterious to performance and they can be avoided in many
cases."""
    level = 3
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = []
    def compute(self, EV):
        try:
            self.val = 0
            self.thresh = (self.val > 0.1) & self.parent.thresh
        except ZeroDivisionError:
            handle_error(self, "Assists zero division")
        return self.val

class Metric_IPC:
    name = "IPC"
    desc = """
Instructions Per Cycle (per logical thread)"""
    domain = "Metric"
    maxval = 5.0
    server = False
    errcount = 0
    area = "Info.Thread"
    metricgroup = ['TopDownL1']

    def compute(self, EV):
        try:
            self.val = IPC(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "IPC zero division")


class Metric_UPI:
    name = "UPI"
    desc = """
Uops Per Instruction"""
    domain = "Metric"
    maxval = 2.0
    server = False
    errcount = 0
    area = "Info.Thread"
    metricgroup = ['Pipeline', 'Retiring']

    def compute(self, EV):
        try:
            self.val = UPI(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "UPI zero division")


class Metric_IFetch_Line_Utilization:
    name = "IFetch_Line_Utilization"
    desc = """
Rough Estimation of fraction of fetched lines bytes that
were likely (includes speculatively fetches) consumed by
program instructions"""
    domain = "Metric"
    maxval = 1.0
    server = False
    errcount = 0
    area = "Info.Thread"
    metricgroup = ['PGO']

    def compute(self, EV):
        try:
            self.val = IFetch_Line_Utilization(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "IFetch_Line_Utilization zero division")


class Metric_DSB_Coverage:
    name = "DSB_Coverage"
    desc = """
Fraction of Uops delivered by the DSB (aka Decoded ICache;
or Uop Cache). See section 'Decoded ICache' in Optimization
Manual. http://www.intel.com/content/www/us/en/architecture-
and-technology/64-ia-32-architectures-optimization-
manual.html"""
    domain = "Metric"
    maxval = 1.0
    server = False
    errcount = 0
    area = "Info.Thread"
    metricgroup = ['DSB', 'Frontend_Bandwidth']

    def compute(self, EV):
        try:
            self.val = DSB_Coverage(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "DSB_Coverage zero division")


class Metric_LSD_Coverage:
    name = "LSD_Coverage"
    desc = """
Fraction of Uops delivered by the LSD (Loop Stream Detector;
aka Loop Cache)"""
    domain = "Metric"
    maxval = 1.0
    server = False
    errcount = 0
    area = "Info.Thread"
    metricgroup = ['LSD']

    def compute(self, EV):
        try:
            self.val = LSD_Coverage(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "LSD_Coverage zero division")


class Metric_CPI:
    name = "CPI"
    desc = """
Cycles Per Instruction (threaded)"""
    domain = "Metric"
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Thread"
    metricgroup = ['Pipeline', 'Summary']

    def compute(self, EV):
        try:
            self.val = CPI(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "CPI zero division")


class Metric_CLKS:
    name = "CLKS"
    desc = """
Per-thread actual clocks when the logical processor is
active."""
    domain = "Count"
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Thread"
    metricgroup = ['Summary']

    def compute(self, EV):
        try:
            self.val = CLKS(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "CLKS zero division")


class Metric_SLOTS:
    name = "SLOTS"
    desc = """
Total issue-pipeline slots ( per core )"""
    domain = "Count"
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Thread"
    metricgroup = ['TopDownL1']

    def compute(self, EV):
        try:
            self.val = SLOTS(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "SLOTS zero division")


class Metric_Instructions:
    name = "Instructions"
    desc = """
Total number of retired Instructions"""
    domain = "Count"
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Inst_Mix"
    metricgroup = ['Summary']

    def compute(self, EV):
        try:
            self.val = Instructions(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "Instructions zero division")


class Metric_CoreIPC:
    name = "CoreIPC"
    desc = """
Instructions Per Cycle (per physical core)"""
    domain = "CoreMetric"
    maxval = 5.0
    server = False
    errcount = 0
    area = "Info.Core"
    metricgroup = ['SMT']

    def compute(self, EV):
        try:
            self.val = CoreIPC(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "CoreIPC zero division")


class Metric_FLOPc:
    name = "FLOPc"
    desc = """
Floating Point Operations Per Cycle"""
    domain = "CoreMetric"
    maxval = 10.0
    server = False
    errcount = 0
    area = "Info.Core"
    metricgroup = ['FLOPS']

    def compute(self, EV):
        try:
            self.val = FLOPc(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "FLOPc zero division")


class Metric_ILP:
    name = "ILP"
    desc = """
Instruction-Level-Parallelism (average number of uops
executed when there is at least 1 uop executed)"""
    domain = "CoreMetric"
    maxval = 10.0
    server = False
    errcount = 0
    area = "Info.Core"
    metricgroup = ['Pipeline', 'Ports_Utilization']

    def compute(self, EV):
        try:
            self.val = ILP(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "ILP zero division")


class Metric_Branch_Misprediction_Cost:
    name = "Branch_Misprediction_Cost"
    desc = """
Branch Misprediction Cost: Fraction of TopDown slots wasted
per non-speculative branch misprediction (jeclear)"""
    domain = "CoreMetric"
    maxval = 300.0
    server = False
    errcount = 0
    area = "Info.Core"
    metricgroup = ['Branch_Mispredicts']

    def compute(self, EV):
        try:
            self.val = Branch_Misprediction_Cost(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "Branch_Misprediction_Cost zero division")


class Metric_CORE_CLKS:
    name = "CORE_CLKS"
    desc = """
Core actual clocks when any thread is active on the physical
core"""
    domain = "Count"
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Core"
    metricgroup = ['SMT']

    def compute(self, EV):
        try:
            self.val = CORE_CLKS(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "CORE_CLKS zero division")


class Metric_Load_Miss_Real_Latency:
    name = "Load_Miss_Real_Latency"
    desc = """
Actual Average Latency for L1 data-cache miss demand loads
(in core cycles)"""
    domain = "Metric"
    maxval = 1000.0
    server = False
    errcount = 0
    area = "Info.Memory"
    metricgroup = ['Memory_Bound', 'Memory_Lat']

    def compute(self, EV):
        try:
            self.val = Load_Miss_Real_Latency(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "Load_Miss_Real_Latency zero division")


class Metric_MLP:
    name = "MLP"
    desc = """
Memory-Level-Parallelism (average number of L1 miss demand
load when there is at least one such miss. Per-thread)"""
    domain = "Metric"
    maxval = 10.0
    server = False
    errcount = 0
    area = "Info.Memory"
    metricgroup = ['Memory_Bound', 'Memory_BW']

    def compute(self, EV):
        try:
            self.val = MLP(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "MLP zero division")


class Metric_Page_Walks_Utilization:
    name = "Page_Walks_Utilization"
    desc = """
Utilization of the core's Page Walker(s) serving STLB misses
triggered by instruction/Load/Store accesses"""
    domain = "CoreMetric"
    maxval = 1
    server = False
    errcount = 0
    area = "Info.Memory"
    metricgroup = ['TLB']

    def compute(self, EV):
        try:
            self.val = Page_Walks_Utilization(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "Page_Walks_Utilization zero division")


class Metric_L1D_Cache_Fill_BW:
    name = "L1D_Cache_Fill_BW"
    desc = """
Average data fill bandwidth to the L1 data cache [GB / sec]"""
    domain = "CoreMetric"
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Memory"
    metricgroup = ['Memory_BW']

    def compute(self, EV):
        try:
            self.val = L1D_Cache_Fill_BW(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "L1D_Cache_Fill_BW zero division")


class Metric_L2_Cache_Fill_BW:
    name = "L2_Cache_Fill_BW"
    desc = """
Average data fill bandwidth to the L2 cache [GB / sec]"""
    domain = "CoreMetric"
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Memory"
    metricgroup = ['Memory_BW']

    def compute(self, EV):
        try:
            self.val = L2_Cache_Fill_BW(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "L2_Cache_Fill_BW zero division")


class Metric_L3_Cache_Fill_BW:
    name = "L3_Cache_Fill_BW"
    desc = """
Average per-core data fill bandwidth to the L3 cache [GB /
sec]"""
    domain = "CoreMetric"
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Memory"
    metricgroup = ['Memory_BW']

    def compute(self, EV):
        try:
            self.val = L3_Cache_Fill_BW(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "L3_Cache_Fill_BW zero division")


class Metric_L3_Cache_Access_BW:
    name = "L3_Cache_Access_BW"
    desc = """
Average per-core data fill bandwidth to the L3 cache [GB /
sec]"""
    domain = "CoreMetric"
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Memory"
    metricgroup = ['Memory_BW']

    def compute(self, EV):
        try:
            self.val = L3_Cache_Access_BW(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "L3_Cache_Access_BW zero division")


class Metric_L1MPKI:
    name = "L1MPKI"
    desc = """
L1 cache true misses per kilo instruction for retired demand
loads"""
    domain = "Metric"
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Memory"
    metricgroup = ['Cache_Misses']

    def compute(self, EV):
        try:
            self.val = L1MPKI(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "L1MPKI zero division")


class Metric_L2MPKI:
    name = "L2MPKI"
    desc = """
L2 cache true misses per kilo instruction for retired demand
loads"""
    domain = "Metric"
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Memory"
    metricgroup = ['Cache_Misses']

    def compute(self, EV):
        try:
            self.val = L2MPKI(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "L2MPKI zero division")


class Metric_L2MPKI_All:
    name = "L2MPKI_All"
    desc = """
L2 cache misses per kilo instruction for all request types
(including speculative)"""
    domain = "Metric"
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Memory"
    metricgroup = ['Cache_Misses']

    def compute(self, EV):
        try:
            self.val = L2MPKI_All(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "L2MPKI_All zero division")


class Metric_L2MPKI_Load:
    name = "L2MPKI_Load"
    desc = """
L2 cache misses per kilo instruction for all demand loads
(including speculative)"""
    domain = "Metric"
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Memory"
    metricgroup = ['Cache_Misses']

    def compute(self, EV):
        try:
            self.val = L2MPKI_Load(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "L2MPKI_Load zero division")


class Metric_L2HPKI_All:
    name = "L2HPKI_All"
    desc = """
L2 cache hits per kilo instruction for all request types
(including speculative)"""
    domain = "Metric"
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Memory"
    metricgroup = ['Cache_Misses']

    def compute(self, EV):
        try:
            self.val = L2HPKI_All(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "L2HPKI_All zero division")


class Metric_L2HPKI_Load:
    name = "L2HPKI_Load"
    desc = """
L2 cache hits per kilo instruction for all demand loads
(including speculative)"""
    domain = "Metric"
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Memory"
    metricgroup = ['Cache_Misses']

    def compute(self, EV):
        try:
            self.val = L2HPKI_Load(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "L2HPKI_Load zero division")


class Metric_L3MPKI:
    name = "L3MPKI"
    desc = """
L3 cache true misses per kilo instruction for retired demand
loads"""
    domain = "Metric"
    maxval = 0
    server = False
    errcount = 0
    area = "Info.Memory"
    metricgroup = ['Cache_Misses']

    def compute(self, EV):
        try:
            self.val = L3MPKI(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "L3MPKI zero division")


class Metric_CPU_Utilization:
    name = "CPU_Utilization"
    desc = """
Average CPU Utilization"""
    domain = "Metric"
    maxval = 200.0
    server = False
    errcount = 0
    area = "Info.System"
    metricgroup = ['Summary']

    def compute(self, EV):
        try:
            self.val = CPU_Utilization(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "CPU_Utilization zero division")


class Metric_Average_Frequency:
    name = "Average_Frequency"
    desc = """
Measured Average Frequency for unhalted processors [GHz]"""
    domain = "SystemMetric"
    maxval = 0
    server = False
    errcount = 0
    area = "Info.System"
    metricgroup = ['Summary', 'Power']

    def compute(self, EV):
        try:
            self.val = Average_Frequency(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "Average_Frequency zero division")


class Metric_GFLOPs:
    name = "GFLOPs"
    desc = """
Giga Floating Point Operations Per Second"""
    domain = "Metric"
    maxval = 200.0
    server = False
    errcount = 0
    area = "Info.System"
    metricgroup = ['FLOPS', 'Summary']

    def compute(self, EV):
        try:
            self.val = GFLOPs(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "GFLOPs zero division")


class Metric_Turbo_Utilization:
    name = "Turbo_Utilization"
    desc = """
Average Frequency Utilization relative nominal frequency"""
    domain = "CoreMetric"
    maxval = 10.0
    server = False
    errcount = 0
    area = "Info.System"
    metricgroup = ['Power']

    def compute(self, EV):
        try:
            self.val = Turbo_Utilization(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "Turbo_Utilization zero division")


class Metric_SMT_2T_Utilization:
    name = "SMT_2T_Utilization"
    desc = """
Fraction of cycles where both hardware threads were active"""
    domain = "CoreMetric"
    maxval = 1.0
    server = False
    errcount = 0
    area = "Info.System"
    metricgroup = ['SMT', 'Summary']

    def compute(self, EV):
        try:
            self.val = SMT_2T_Utilization(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "SMT_2T_Utilization zero division")


class Metric_Kernel_Utilization:
    name = "Kernel_Utilization"
    desc = """
Fraction of cycles spent in Kernel mode"""
    domain = "Metric"
    maxval = 1.0
    server = False
    errcount = 0
    area = "Info.System"
    metricgroup = []

    def compute(self, EV):
        try:
            self.val = Kernel_Utilization(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "Kernel_Utilization zero division")


class Metric_DRAM_BW_Use:
    name = "DRAM_BW_Use"
    desc = """
Average external Memory Bandwidth Use for reads and writes
[GB / sec]"""
    domain = "SystemMetric"
    maxval = 200.0
    server = False
    errcount = 0
    area = "Info.System"
    metricgroup = ['Memory_BW']

    def compute(self, EV):
        try:
            self.val = DRAM_BW_Use(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "DRAM_BW_Use zero division")


class Metric_MEM_Request_Latency:
    name = "MEM_Request_Latency"
    desc = """
Average latency of all requests to external memory (in
Uncore cycles)"""
    domain = "Metric"
    maxval = 1000.0
    server = False
    errcount = 0
    area = "Info.System"
    metricgroup = []

    def compute(self, EV):
        try:
            self.val = MEM_Request_Latency(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "MEM_Request_Latency zero division")


class Metric_MEM_Parallel_Requests:
    name = "MEM_Parallel_Requests"
    desc = """
Average number of parallel requests to external memory.
Accounts for all requests"""
    domain = "Metric"
    maxval = 100.0
    server = False
    errcount = 0
    area = "Info.System"
    metricgroup = []

    def compute(self, EV):
        try:
            self.val = MEM_Parallel_Requests(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "MEM_Parallel_Requests zero division")


class Metric_MEM_DRAM_Read_Latency:
    name = "MEM_DRAM_Read_Latency"
    desc = """
Average latency of data read request to external DRAM memory
[in nanoseconds]. Accounts for demand loads and L1/L2 data-
read prefetches"""
    domain = "SystemMetric"
    maxval = 0
    server = False
    errcount = 0
    area = "Info.System"
    metricgroup = ['Memory_Lat']

    def compute(self, EV):
        try:
            self.val = MEM_DRAM_Read_Latency(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "MEM_DRAM_Read_Latency zero division")


class Metric_Power:
    name = "Power"
    desc = """
Total package Power in Watts"""
    domain = "SystemMetric"
    maxval = 200.0
    server = False
    errcount = 0
    area = "Info.System"
    metricgroup = ['Power']

    def compute(self, EV):
        try:
            self.val = Power(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "Power zero division")


class Metric_Time:
    name = "Time"
    desc = """
Run duration time in seconds"""
    domain = "SystemMetric"
    maxval = 0
    server = False
    errcount = 0
    area = "Info.System"
    metricgroup = ['Summary']

    def compute(self, EV):
        try:
            self.val = Time(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "Time zero division")


class Metric_Socket_CLKS:
    name = "Socket_CLKS"
    desc = """
Socket actual clocks when any core is active on that socket"""
    domain = "Count"
    maxval = 0
    server = False
    errcount = 0
    area = "Info.System"
    metricgroup = []

    def compute(self, EV):
        try:
            self.val = Socket_CLKS(self, EV, 0)
        except ZeroDivisionError:
            handle_error_metric(self, "Socket_CLKS zero division")


# Schedule



class Setup:
    def __init__(self, r):
        o = dict()
        n = Frontend_Bound() ; r.run(n) ; o["Frontend_Bound"] = n
        n = Frontend_Latency() ; r.run(n) ; o["Frontend_Latency"] = n
        n = ICache_Misses() ; r.run(n) ; o["ICache_Misses"] = n
        n = ITLB_Misses() ; r.run(n) ; o["ITLB_Misses"] = n
        n = Branch_Resteers() ; r.run(n) ; o["Branch_Resteers"] = n
        n = Mispredicts_Resteers() ; r.run(n) ; o["Mispredicts_Resteers"] = n
        n = Clears_Resteers() ; r.run(n) ; o["Clears_Resteers"] = n
        n = Unknown_Branches() ; r.run(n) ; o["Unknown_Branches"] = n
        n = DSB_Switches() ; r.run(n) ; o["DSB_Switches"] = n
        n = LCP() ; r.run(n) ; o["LCP"] = n
        n = MS_Switches() ; r.run(n) ; o["MS_Switches"] = n
        n = Frontend_Bandwidth() ; r.run(n) ; o["Frontend_Bandwidth"] = n
        n = Bad_Speculation() ; r.run(n) ; o["Bad_Speculation"] = n
        n = Branch_Mispredicts() ; r.run(n) ; o["Branch_Mispredicts"] = n
        n = Machine_Clears() ; r.run(n) ; o["Machine_Clears"] = n
        n = Backend_Bound() ; r.run(n) ; o["Backend_Bound"] = n
        n = Memory_Bound() ; r.run(n) ; o["Memory_Bound"] = n
        n = L1_Bound() ; r.run(n) ; o["L1_Bound"] = n
        n = DTLB_Load() ; r.run(n) ; o["DTLB_Load"] = n
        n = Lock_Latency() ; r.run(n) ; o["Lock_Latency"] = n
        n = L2_Bound() ; r.run(n) ; o["L2_Bound"] = n
        n = L3_Bound() ; r.run(n) ; o["L3_Bound"] = n
        n = DRAM_Bound() ; r.run(n) ; o["DRAM_Bound"] = n
        n = MEM_Bandwidth() ; r.run(n) ; o["MEM_Bandwidth"] = n
        n = MEM_Latency() ; r.run(n) ; o["MEM_Latency"] = n
        n = Store_Bound() ; r.run(n) ; o["Store_Bound"] = n
        n = Store_Latency() ; r.run(n) ; o["Store_Latency"] = n
        n = DTLB_Store() ; r.run(n) ; o["DTLB_Store"] = n
        n = Core_Bound() ; r.run(n) ; o["Core_Bound"] = n
        n = Divider() ; r.run(n) ; o["Divider"] = n
        n = Ports_Utilization() ; r.run(n) ; o["Ports_Utilization"] = n
        n = G0_Ports_Utilized() ; r.run(n) ; o["G0_Ports_Utilized"] = n
        n = Serializing_Operation() ; r.run(n) ; o["Serializing_Operation"] = n
        n = G1_Port_Utilized() ; r.run(n) ; o["G1_Port_Utilized"] = n
        n = G2_Ports_Utilized() ; r.run(n) ; o["G2_Ports_Utilized"] = n
        n = G3m_Ports_Utilized() ; r.run(n) ; o["G3m_Ports_Utilized"] = n
        n = Retiring() ; r.run(n) ; o["Retiring"] = n
        n = Base() ; r.run(n) ; o["Base"] = n
        n = FP_Arith() ; r.run(n) ; o["FP_Arith"] = n
        n = X87_Use() ; r.run(n) ; o["X87_Use"] = n
        n = FP_Scalar() ; r.run(n) ; o["FP_Scalar"] = n
        n = FP_Vector() ; r.run(n) ; o["FP_Vector"] = n
        n = Other() ; r.run(n) ; o["Other"] = n
        n = Microcode_Sequencer() ; r.run(n) ; o["Microcode_Sequencer"] = n
        n = Assists() ; r.run(n) ; o["Assists"] = n

        # parents

        o["Frontend_Latency"].parent = o["Frontend_Bound"]
        o["ICache_Misses"].parent = o["Frontend_Latency"]
        o["ITLB_Misses"].parent = o["Frontend_Latency"]
        o["Branch_Resteers"].parent = o["Frontend_Latency"]
        o["Mispredicts_Resteers"].parent = o["Branch_Resteers"]
        o["Clears_Resteers"].parent = o["Branch_Resteers"]
        o["Unknown_Branches"].parent = o["Branch_Resteers"]
        o["DSB_Switches"].parent = o["Frontend_Latency"]
        o["LCP"].parent = o["Frontend_Latency"]
        o["MS_Switches"].parent = o["Frontend_Latency"]
        o["Frontend_Bandwidth"].parent = o["Frontend_Bound"]
        o["Branch_Mispredicts"].parent = o["Bad_Speculation"]
        o["Machine_Clears"].parent = o["Bad_Speculation"]
        o["Memory_Bound"].parent = o["Backend_Bound"]
        o["L1_Bound"].parent = o["Memory_Bound"]
        o["DTLB_Load"].parent = o["L1_Bound"]
        o["Lock_Latency"].parent = o["L1_Bound"]
        o["L2_Bound"].parent = o["Memory_Bound"]
        o["L3_Bound"].parent = o["Memory_Bound"]
        o["DRAM_Bound"].parent = o["Memory_Bound"]
        o["MEM_Bandwidth"].parent = o["DRAM_Bound"]
        o["MEM_Latency"].parent = o["DRAM_Bound"]
        o["Store_Bound"].parent = o["Memory_Bound"]
        o["Store_Latency"].parent = o["Store_Bound"]
        o["DTLB_Store"].parent = o["Store_Bound"]
        o["Core_Bound"].parent = o["Backend_Bound"]
        o["Divider"].parent = o["Core_Bound"]
        o["Ports_Utilization"].parent = o["Core_Bound"]
        o["G0_Ports_Utilized"].parent = o["Ports_Utilization"]
        o["Serializing_Operation"].parent = o["G0_Ports_Utilized"]
        o["G1_Port_Utilized"].parent = o["Ports_Utilization"]
        o["G2_Ports_Utilized"].parent = o["Ports_Utilization"]
        o["G3m_Ports_Utilized"].parent = o["Ports_Utilization"]
        o["Base"].parent = o["Retiring"]
        o["FP_Arith"].parent = o["Base"]
        o["X87_Use"].parent = o["FP_Arith"]
        o["FP_Scalar"].parent = o["FP_Arith"]
        o["FP_Vector"].parent = o["FP_Arith"]
        o["Other"].parent = o["Base"]
        o["Microcode_Sequencer"].parent = o["Retiring"]
        o["Assists"].parent = o["Microcode_Sequencer"]

        # user visible metrics

        n = Metric_IPC() ; r.metric(n) ; o["IPC"] = n
        n = Metric_UPI() ; r.metric(n) ; o["UPI"] = n
        n = Metric_IFetch_Line_Utilization() ; r.metric(n) ; o["IFetch_Line_Utilization"] = n
        n = Metric_DSB_Coverage() ; r.metric(n) ; o["DSB_Coverage"] = n
        n = Metric_LSD_Coverage() ; r.metric(n) ; o["LSD_Coverage"] = n
        n = Metric_CPI() ; r.metric(n) ; o["CPI"] = n
        n = Metric_CLKS() ; r.metric(n) ; o["CLKS"] = n
        n = Metric_SLOTS() ; r.metric(n) ; o["SLOTS"] = n
        n = Metric_Instructions() ; r.metric(n) ; o["Instructions"] = n
        n = Metric_CoreIPC() ; r.metric(n) ; o["CoreIPC"] = n
        n = Metric_FLOPc() ; r.metric(n) ; o["FLOPc"] = n
        n = Metric_ILP() ; r.metric(n) ; o["ILP"] = n
        n = Metric_Branch_Misprediction_Cost() ; r.metric(n) ; o["Branch_Misprediction_Cost"] = n
        n = Metric_CORE_CLKS() ; r.metric(n) ; o["CORE_CLKS"] = n
        n = Metric_Load_Miss_Real_Latency() ; r.metric(n) ; o["Load_Miss_Real_Latency"] = n
        n = Metric_MLP() ; r.metric(n) ; o["MLP"] = n
        n = Metric_Page_Walks_Utilization() ; r.metric(n) ; o["Page_Walks_Utilization"] = n
        n = Metric_L1D_Cache_Fill_BW() ; r.metric(n) ; o["L1D_Cache_Fill_BW"] = n
        n = Metric_L2_Cache_Fill_BW() ; r.metric(n) ; o["L2_Cache_Fill_BW"] = n
        n = Metric_L3_Cache_Fill_BW() ; r.metric(n) ; o["L3_Cache_Fill_BW"] = n
        n = Metric_L3_Cache_Access_BW() ; r.metric(n) ; o["L3_Cache_Access_BW"] = n
        n = Metric_L1MPKI() ; r.metric(n) ; o["L1MPKI"] = n
        n = Metric_L2MPKI() ; r.metric(n) ; o["L2MPKI"] = n
        n = Metric_L2MPKI_All() ; r.metric(n) ; o["L2MPKI_All"] = n
        n = Metric_L2MPKI_Load() ; r.metric(n) ; o["L2MPKI_Load"] = n
        n = Metric_L2HPKI_All() ; r.metric(n) ; o["L2HPKI_All"] = n
        n = Metric_L2HPKI_Load() ; r.metric(n) ; o["L2HPKI_Load"] = n
        n = Metric_L3MPKI() ; r.metric(n) ; o["L3MPKI"] = n
        n = Metric_CPU_Utilization() ; r.metric(n) ; o["CPU_Utilization"] = n
        n = Metric_Average_Frequency() ; r.metric(n) ; o["Average_Frequency"] = n
        n = Metric_GFLOPs() ; r.metric(n) ; o["GFLOPs"] = n
        n = Metric_Turbo_Utilization() ; r.metric(n) ; o["Turbo_Utilization"] = n
        n = Metric_SMT_2T_Utilization() ; r.metric(n) ; o["SMT_2T_Utilization"] = n
        n = Metric_Kernel_Utilization() ; r.metric(n) ; o["Kernel_Utilization"] = n
        n = Metric_DRAM_BW_Use() ; r.metric(n) ; o["DRAM_BW_Use"] = n
        n = Metric_MEM_Request_Latency() ; r.metric(n) ; o["MEM_Request_Latency"] = n
        n = Metric_MEM_Parallel_Requests() ; r.metric(n) ; o["MEM_Parallel_Requests"] = n
        n = Metric_MEM_DRAM_Read_Latency() ; r.metric(n) ; o["MEM_DRAM_Read_Latency"] = n
        n = Metric_Power() ; r.metric(n) ; o["Power"] = n
        n = Metric_Time() ; r.metric(n) ; o["Time"] = n
        n = Metric_Socket_CLKS() ; r.metric(n) ; o["Socket_CLKS"] = n

        # references between groups

        o["Frontend_Bandwidth"].Frontend_Bound = o["Frontend_Bound"]
        o["Frontend_Bandwidth"].Frontend_Latency = o["Frontend_Latency"]
        o["Branch_Mispredicts"].Bad_Speculation = o["Bad_Speculation"]
        o["Machine_Clears"].Bad_Speculation = o["Bad_Speculation"]
        o["Machine_Clears"].Branch_Mispredicts = o["Branch_Mispredicts"]
        o["Backend_Bound"].Retiring = o["Retiring"]
        o["Backend_Bound"].Bad_Speculation = o["Bad_Speculation"]
        o["Backend_Bound"].Frontend_Bound = o["Frontend_Bound"]
        o["Memory_Bound"].Retiring = o["Retiring"]
        o["Memory_Bound"].Bad_Speculation = o["Bad_Speculation"]
        o["Memory_Bound"].Frontend_Bound = o["Frontend_Bound"]
        o["Memory_Bound"].Backend_Bound = o["Backend_Bound"]
        o["Memory_Bound"].Frontend_Latency = o["Frontend_Latency"]
        o["MEM_Latency"].MEM_Bandwidth = o["MEM_Bandwidth"]
        o["Core_Bound"].Retiring = o["Retiring"]
        o["Core_Bound"].Frontend_Bound = o["Frontend_Bound"]
        o["Core_Bound"].Memory_Bound = o["Memory_Bound"]
        o["Core_Bound"].Backend_Bound = o["Backend_Bound"]
        o["Core_Bound"].Bad_Speculation = o["Bad_Speculation"]
        o["Core_Bound"].Frontend_Latency = o["Frontend_Latency"]
        o["Ports_Utilization"].Frontend_Latency = o["Frontend_Latency"]
        o["Retiring"].Microcode_Sequencer = o["Microcode_Sequencer"]
        o["Base"].Retiring = o["Retiring"]
        o["Base"].Microcode_Sequencer = o["Microcode_Sequencer"]
        o["FP_Arith"].FP_Scalar = o["FP_Scalar"]
        o["FP_Arith"].X87_Use = o["X87_Use"]
        o["FP_Arith"].FP_Vector = o["FP_Vector"]
        o["Other"].FP_Arith = o["FP_Arith"]
        o["Other"].X87_Use = o["X87_Use"]
        o["Other"].FP_Scalar = o["FP_Scalar"]
        o["Other"].FP_Vector = o["FP_Vector"]

        # siblings cross-tree

        o["Mispredicts_Resteers"].sibling = (o["Clears_Resteers"], o["Branch_Mispredicts"],)
        o["Clears_Resteers"].sibling = (o["Mispredicts_Resteers"], o["Branch_Mispredicts"],)
        o["MS_Switches"].sibling = (o["Serializing_Operation"], o["Microcode_Sequencer"],)
        o["Branch_Mispredicts"].sibling = (o["Mispredicts_Resteers"], o["Clears_Resteers"],)
        o["L1_Bound"].sibling = (o["G1_Port_Utilized"],)
        o["Lock_Latency"].sibling = (o["Store_Latency"],)
        o["Store_Latency"].sibling = (o["Lock_Latency"],)
        o["Store_Latency"].overlap = True
        o["Serializing_Operation"].sibling = (o["MS_Switches"],)
        o["G1_Port_Utilized"].sibling = (o["L1_Bound"],)
        o["Microcode_Sequencer"].sibling = (o["MS_Switches"],)
