#!/usr/bin/env python
# translate raw events to names
# event-translate rXXX ...
import re
import sys
import ocperf
from pmudef import *

emap = ocperf.find_emap()
if not emap:
    sys.exit("Unknown CPU or cannot find event table")
for j in sys.argv[1:]:
    m = re.match(r'r([0-9a-f]+)(:.*)?', j)
    if m:
        print m.group(1)
        evsel = int(m.group(1), 16)
        print "%s:" % (j)
        if evsel & EVMASK in emap.codes:
            print emap.codes[evsel & EVMASK].name
        elif (evsel & (EVENTSEL_EVENT|EVENTSEL_UMASK)) in emap.codes:
            print emap.codes[evsel & (EVENTSEL_EVENT|EVENTSEL_UMASK)].name,
            for k in extra_flags:
                if evsel & k[0]:
                    m = k[0]
                    en = evsel
                    while (m & 1) == 0:
                        m >>= 1
                        en >>= 1
                    print "%s=%d" % (k[1], en & m),
            print
        else:
            print "cannot find", m.group(1)
    else:
        # XXX implement offcore new style events
        print "cannot parse", j

