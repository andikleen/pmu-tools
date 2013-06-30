#!/usr/bin/python
# generate dot diagram of top down tree from module
import sys
if len(sys.argv) > 1 and sys.argv[1] == "simple":
    import simple_ratios
    m = simple_ratios
else:
    import ivb_client_ratios
    m = ivb_client_ratios

class Runner:
    def __init__(self):
        self.olist = []
    def run(self, n):
        self.olist.append(n)
    def finish(self):
        for n in self.olist:
            if n.parent:
                print '"%s" -> "%s";' % (n.parent.__class__.__name__, 
                                        n.__class__.__name__)
            elif n.level == 1:
                print '"%s";' % (n.name)

    def fix_parents(self):
	for obj in self.olist:
	    if not obj.parent:
	        continue
	    if obj.level == 1:
                obj.parent = None
	    elif obj.parent.level >= obj.level:
                my_list = self.olist[:self.olist.index(obj)]
		all_parents = filter(lambda x: x.level < obj.level, my_list)
                print >>sys.stderr, obj.name, "all-parents", all_parents
		obj.parent = all_parents[-1]
	        assert obj.parent.level < obj.level


runner = Runner()
m.Setup(runner)
print >>sys.stderr, runner.olist
runner.fix_parents()
print "digraph {"
runner.finish()
print "}"


