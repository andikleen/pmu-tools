#
# Silvermont top level model
# Can be collected without multiplexing
# Please see http://ark.intel.com for more details on these CPUs.
#

import metrics
import node

print_error = lambda msg: False
version = "1.0"

# Override using set_clks_event_name()
CLKS_EVENT_NAME = "CPU_CLK_UNHALTED.THREAD"

# Module-level function used to work around event name differences,
# e.g. Knights Landing
def set_clks_event_name(ev_name):
    CLKS_EVENT_NAME = ev_name

# Instructions Per Cycle
def IPC(EV, level):
    return EV("INST_RETIRED.ANY", level) / EV("cycles", 1)

# Average Frequency Utilization relative nominal frequency
def TurboUtilization(EV, level):
    return EV("cycles", level) / EV("CPU_CLK_UNHALTED.REF_TSC", level)

def DurationTimeInSeconds(EV, level):
    return EV("interval-ns", 0) / 1e+06 / 1000

# Run duration time in seconds
def Time(EV, level):
    return DurationTimeInSeconds(EV, level)

# Per-thread actual clocks
def CLKS(EV, level):
    return EV(CLKS_EVENT_NAME, level)

# Cycles Per Instruction (threaded)
def CPI(EV, level):
    return 1 / IPC(EV, level)

def slots(ev, level):
    return PIPELINE_WIDTH * core_clks(ev, level)

def icache_line_fetch_cost(ev, level):
    return ev("FETCH_STALL.ICACHE_FILL_PENDING_CYCLES", level) / \
           CLKS(ev, level)

def predecode_wrong_cost(ev, level):
    return (ev("DECODE_RESTRICTION.PREDECODE_WRONG", level) * 3 /
            CLKS(ev, level))

def ba_clears_cost(ev, level):
    return ev("BACLEARS.ALL", level) * 5 / CLKS(ev, level)

def ms_entry_cost(ev, level):
    return ev("MS_DECODED.MS_ENTRY", level) * 5 / CLKS(ev, level)

def itlb_misses_cost(ev, level):
    return ev("PAGE_WALKS.I_SIDE_CYCLES", level) / CLKS(ev, level)

# LEVEL 0, user-visible metrics"
class CyclesPerUop(metrics.MetricBase):
    name = "CyclesPerUop"
    domain = "Metric"
    desc = "\nCycles per uop."
    def _compute(self, ev):
        return ev("CPU_CLK_UNHALTED.THREAD", self.level) / \
               ev("UOPS_RETIRED.ALL", self.level)

# LEVEL 1
class FrontendBound(metrics.FrontendBound):
    def _compute(self, ev):
        return ev("NO_ALLOC_CYCLES.NOT_DELIVERED", 1) / CLKS(ev, self.level)

@node.requires("retiring", "bad_speculation", "frontend")
class BackendBound(metrics.BackendBound):
    @node.check_refs
    def _compute(self, ev):
        return 1 - (self.retiring.compute(ev) +
                    self.bad_speculation.compute(ev) +
                    self.frontend.compute(ev))

class BadSpeculation(metrics.BadSpeculation):
    def _compute(self, ev):
        return ev("NO_ALLOC_CYCLES.MISPREDICTS", 1) / CLKS(ev, self.level)

class Retiring(metrics.Retiring):
    def _compute(self, ev):
        return ev("UOPS_RETIRED.ALL", 1) / (2 * CLKS(ev, self.level))

# LEVEL 2
@node.requires("icache_misses", "itlb", "ms_cost", "frontend")
class FrontendLatency(metrics.FrontendLatency):
    @node.check_refs
    def _compute(self, ev):
        return (self.icache_misses.compute(ev) + self.itlb.compute(ev) +
                self.ms_cost.compute(ev) + ba_clears_cost(ev, self.level)
               ) / CLKS(ev, self.level)

# LEVEL 3
class ICacheMisses(metrics.ICacheMisses):
    def _compute(self, ev):
        return (icache_line_fetch_cost(ev, self.level) +
                predecode_wrong_cost(ev, self.level))

class ITLBMisses(metrics.ITLBMisses):
    def _compute(self, ev):
        return itlb_misses_cost(ev, self.level)

class MSSwitches(metrics.MSSwitches):
    def _compute(self, ev):
        return ms_entry_cost(ev, self.level)

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

class Setup:
    def __init__(self, runner):
        # Instantiate nodes as required to be able to specify their
        # references

        # L3 objects
        icache_misses = ICacheMisses()
        itlb_misses = ITLBMisses()
        ms_cost = MSSwitches()

        #L1 objects
        frontend = FrontendBound()
        bad_speculation = BadSpeculation()
        retiring = Retiring()
        backend = BackendBound(retiring=retiring,
                               bad_speculation=bad_speculation,
                               frontend=frontend)


        # L2 objects
        frontend_latency = FrontendLatency(icache_misses=icache_misses,
                                           itlb=itlb_misses,
                                           ms_cost=ms_cost,
                                           frontend=frontend
                                           )

        # Set parents
        node.set_parent(None, [frontend, bad_speculation, retiring, backend])
        node.set_parent(frontend, [frontend_latency])
        node.set_parent(frontend_latency,
                        [icache_misses, itlb_misses, ms_cost])

        # User visible metrics
        user_metrics = [Metric_IPC(), Metric_CPI(), Metric_TurboUtilization(),
                        Metric_CLKS(), Metric_Time(), CyclesPerUop()]

        nodes = [obj for obj in locals().values()
                 if issubclass(obj.__class__, metrics.MetricBase) and
                 obj.level > 0]

        nodes = sorted(nodes, key=lambda n: n.level)

        # Pass to runner
        map(lambda n : runner.run(n), nodes)
        map(lambda m : runner.metric(m), user_metrics)
