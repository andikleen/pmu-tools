# generate levels for events from the model
# utility module for other tools
# the model used must be a superset of all
import ivb_server_ratios

omap = dict()

class Runner:
    def run(self, n):
        #print "name |%s|" % (n.name), n
        omap[n.name] = n

    def metric(self, n):
        pass

def get_level(name):
    name = name.strip()
    if name in omap:
        return omap[name].level
    return 0

runner = Runner()
ivb_server_ratios.Setup(runner)
