# generate levels for events from the model
# utility module for other tools
# the model used must be a superset of all
import ivb_server_ratios
import skl_client_ratios
import power_metrics
import linux_metrics
import tsx_metrics
import perf_metrics
import frequency
import re

omap = dict()
metric = dict()

class Runner:
    def run(self, n):
        omap[n.name] = n

    def metric(self, n):
        metric[n.name] = n

def clean_name(name):
    name = name.strip()
    dot = name.rfind(".")
    if dot >= 0:
        name = name[dot + 1:]
    return name

def find_obj(name):
    if name in omap:
        return omap[name], name
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name, 999)
    name = name.replace(" ", "_")
    if name in omap:
        return omap[name], name
    return None, name

def get_level(name):
    name = clean_name(name)
    #oname = name
    obj, name = find_obj(name)
    if obj:
        return obj.level
    #if name not in metric and oname not in metric:
    #    print "level for %s not found" % (oname)
    return 0

def get_subplot(name):
    if name in metric:
        obj = metric[name]
        if 'subplot' in obj.__class__.__dict__:
            return metric[name].subplot
    return None

# XXX move to model
metric_unit = {
    "Latencies": "Cycles",
    "Basic_Block_Length": "Insns",
    "CPU utilization": "CPUs"
}

def get_unit(name):
    if name in metric:
        obj = metric[name]
        if 'unit' in obj.__class__.__dict__:
            return metric[name].unit
        if name in metric_unit:
            return metric_unit[name]
    return None

def is_metric(name):
    return name in metric

# XXX: move to model
metric_levels = {
    "L1dMissLatency": "Latencies",
    "InstPerTakenBranch": "Basic Block Length",
}

def level_name(name):
    if name.count(".") > 0:
        f = name.split(".")[:-1]
        n = ".".join(f)
    elif is_metric(name):
        n = get_subplot(name)
        if not n:
            n = metric_levels[name] if name in metric_levels else "CPU-METRIC"
    else:
        n = "TopLevel"
    n = n.replace(" ", "_")
    return n

runner = Runner()
ivb_server_ratios.Setup(runner)
skl_client_ratios.Setup(runner)
power_metrics.Setup(runner)
linux_metrics.Setup(runner)
tsx_metrics.Setup(runner)
perf_metrics.Setup(runner)

class CPU:
    freq = 0.0

frequency.SetupCPU(runner, CPU())
