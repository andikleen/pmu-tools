version = "1.0"

import metrics
import node
import slm_ratios as slm

slm.set_clks_event_name("CPU_CLK_UNHALTED.CORE")

smt_enabled = False

class CyclesPerUop(slm.CyclesPerUop):
    server = True

# LEVEL 1
class FrontendBound(slm.FrontendBound):
    server = True

class BackendBound(slm.BackendBound):
    server = True

class BadSpeculation(slm.BadSpeculation):
    server = True

class Retiring(slm.Retiring):
    server = True

# LEVEL 2
class FrontendLatency(slm.FrontendLatency):
    server = True

# LEVEL 3
class ICacheMisses(slm.ICacheMisses):
    server = True
    # Override _compute(), since KNL does not have
    # the DECODE_RESTRICTION.PDCACHE_WRONG event
    def _compute(self, ev):
        return slm.icache_line_fetch_cost(ev, self.level)

class ITLBMisses(slm.ITLBMisses):
    server = True

class MSSwitches(slm.MSSwitches):
    server = True

class Setup(object):
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
        user_metrics = [slm.Metric_IPC(), slm.Metric_CPI(),
                        slm.Metric_TurboUtilization(),
                        slm.Metric_CLKS(), slm.Metric_Time(),
                        slm.CyclesPerUop()]

        nodes = [obj for obj in locals().values()
                 if issubclass(obj.__class__, metrics.MetricBase) and
                 obj.level > 0]

        nodes = sorted(nodes, key=lambda n: n.level)

        # Pass to runner
        map(lambda n : runner.run(n), nodes)
        map(lambda m : runner.metric(m), user_metrics)
