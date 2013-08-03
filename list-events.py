#!/usr/bin/python
import ocperf
emap = ocperf.find_emap()
for j in emap.events:
    print j
