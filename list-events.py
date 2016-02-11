#!/usr/bin/env python
# print all events in a eventmap
import ocperf
import sys
emap = ocperf.find_emap()
if not emap:
    sys.exit("Unknown CPU or cannot find event table")
for j in sorted(emap.events):
    print j
