#!/usr/bin/python
import ocperf
emap = ocperf.find_emap()
for j in sorted(emap.events):
    print j
