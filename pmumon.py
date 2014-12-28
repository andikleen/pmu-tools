#!/usr/bin/env python
# standalone simple pmu configuration tool
# allows to count an even without using perf
# will conflict with any parallel perf (and other profiler)
# usage.
# Author: Andi Kleen
# 
import os
import struct
import sys

def writemsr(msr, val, cpu):
    f = os.open('/dev/cpu/%d/msr' % (cpu,), os.O_WRONLY)
    os.lseek(f, msr, os.SEEK_SET)
    os.write(f, struct.pack('Q', val))
    os.close(f)
    
def readmsr(msr, cpu):
    f = os.open('/dev/cpu/%d/msr' % (cpu,), os.O_RDONLY)
    os.lseek(f, msr, os.SEEK_SET)
    val = struct.unpack('Q', os.read(f, 8))[0]
    os.close(f)
    return val

if len(sys.argv) != 3 and len(sys.argv) != 2:
    print "Usage: pmumon cpu [event]"
    print "When no event is specified read+clear event on cpu, otherwise start it"
    print "event == 0 clears. event is in hex"
    print "perf/oprofile/etc. must not be active. no parallel users"
    sys.exit(1)

MSR_EVNTSEL = 0x186 + 1
MSR_PERFCTR = 0xc1 + 1

cpu = int(sys.argv[1])
if len(sys.argv) > 2:
    event = int(sys.argv[2], 16)
    writemsr(MSR_EVNTSEL, 0, cpu) # disable first
    writemsr(MSR_PERFCTR, 0, cpu)
    writemsr(MSR_EVNTSEL, event, cpu)
    #print "global status %x" % (readmsr(0x38f, cpu),)
else:
    print "%x = %d" % (readmsr(MSR_EVNTSEL, cpu), readmsr(MSR_PERFCTR, cpu),)
