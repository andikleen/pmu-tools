class CPU_Utilization:
    name = "CPU utilization"
    desc = """
Number of CPUs used. The top down CPU metrics are only meaningful
when a CPU thread is executing.  The percentage are always relative to
the executing time. When the utilization is low the workload may
actually not be CPU bound, but IO (network, block) IO bound
instead. Check the scheduler and IO metrics below. Or it may be CPU
bound, but not use enough parallelism, if the number of CPUs is less
than the number of cores."""
    nogroup = True
    subplot = "CPU Utilization"
    unit = "CPUs"
    def compute(self, EV):
        try:
            # interval-ns is not a perf event, but handled by toplev internally.
            self.val = (EV("task-clock", 1) * 1e6) / EV("interval-ns", 1)
        except ZeroDivisionError:
            self.val = 0

class MUX:
    name = "MUX"
    desc = """
PerfMon Event Multiplexing accuracy indicator"""
    unit = "%"
    maxval = 100.0
    errcount = 0

    def compute(self, EV):
        self.val = EV("mux", 0)
        self.thresh = 0 < self.val < 100.0

class Setup:
    def __init__(self, r):
        #r.metric(CPU_Utilization())
        r.metric(MUX())
