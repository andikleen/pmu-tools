# generate levels for events from the model
# utility module for other tools
# the model used must be a superset of all
import ivb_server_ratios
import hsw_client_ratios
import power_metrics
import linux_metrics
import tsx_metrics
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
    oname = name
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

def is_metric(name):
    return name in metric

runner = Runner()
ivb_server_ratios.Setup(runner)
hsw_client_ratios.Setup(runner)
power_metrics.Setup(runner)
linux_metrics.Setup(runner)
tsx_metrics.Setup(runner)
