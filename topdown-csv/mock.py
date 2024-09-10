#!/usr/bin/env python3
# Do basic python sanity check of translation output
import sys
sys.path.append(".")
import t
l = []
m = []

def pev(e):
    print("\t",e)
    return 1

class R:
    def run(self, p):
        #print p
        l.append(p)
    def metric(self, p):
        m.append(p)

t.Setup(R())
for p in l:
    p.thresh = True
for p in l:
    print(p.name)
    p.compute(lambda e, level: pev(e))
    if p.sample:
        print("    Sample:", " ".join(p.sample))
    if p.sibling:
        print("    Siblings:", " ".join([o.name for o in p.sibling]))

for p in m:
    print(p.name)
    p.compute(lambda e, level: pev(e))

