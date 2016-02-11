#!/usr/bin/env python
# generate dot diagram of top down tree from module
import sys

max_level = 5
first = 1
if sys.argv[1:] and sys.argv[1][:2] == "-l":
    max_level = int(sys.argv[1][2:])
    first += 1
if len(sys.argv) > first and sys.argv[first] == "simple":
    import simple_ratios
    m = simple_ratios
else:
    import ivb_client_ratios
    m = ivb_client_ratios

def has(obj, name):
    return name in obj.__class__.__dict__

class Runner:
    def __init__(self):
        self.olist = []

    def run(self, n):
        if n.level <= max_level:
            self.olist.append(n)

    def metric(self, n):
        pass

    def finish(self):
        for n in self.olist:
            if n.level == 1:
                print '"%s";' % (n.name)
            elif n.parent:
                print '"%s" -> "%s";' % (n.parent.name, n.name)
            #if n.sibling:
            #    print '"%s" -> "%s";' % (n.name, n.sibling.name)

runner = Runner()
m.Setup(runner)
print >>sys.stderr, runner.olist
print "digraph {"
print "fontname=\"Courier\";"
runner.finish()
print "}"


