# generate levels for events from the model
# utility module for other tools
# the model used must be a superset of all
import ivb_server_ratios
import hsw_client_ratios
import power_metrics
import re

omap = dict()
metric = dict()

class Runner:
    def run(self, n):
        #print "name |%s|" % (n.name)
        omap[n.name] = n

    def metric(self, n):
        metric[n.name] = n
        #print "metric |%s|" % (n.name)
        pass

def get_level(name):
    name = name.strip()
    dot = name.rfind(".")
    if dot >= 0:
        name = name[dot + 1:]
    oname = name
    if name in omap:
        return omap[name].level
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name, 999)
    name = name.replace(" ", "_")
    if name in omap:
        return omap[name].level
    if name not in metric and oname not in metric:
        print "level for %s not found" % (oname)
    return 0

runner = Runner()
ivb_server_ratios.Setup(runner)
hsw_client_ratios.Setup(runner)
power_metrics.Setup(runner)
