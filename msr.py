#!/usr/bin/env python
# library and tool to access MSRs (model specific registers)
import os
import glob
import struct

def writemsr(msr, val):
    n = glob.glob('/dev/cpu/*/msr')
    for c in n:
        f = os.open(c, os.O_WRONLY)
        os.lseek(f, msr, os.SEEK_SET)
        os.write(f, struct.pack('Q', val))
        os.close(f)
    
def readmsr(msr, cpu = 0):
    f = os.open('/dev/cpu/%d/msr' % (cpu,), os.O_RDONLY)
    os.lseek(f, msr, os.SEEK_SET)
    val = struct.unpack('Q', os.read(f, 8))[0]
    os.close(f)
    return val

def changebit(msr, bit, val):
    n = glob.glob('/dev/cpu/*/msr')
    for c in n:
        f = os.open(c, os.O_RDWR)
        os.lseek(f, msr, os.SEEK_SET)
        v = struct.unpack('Q', os.read(f, 8))[0]
        if val:
            v = v | (1 << bit)
        else:
            v = v & ~(1 << bit)
        os.lseek(f, msr, os.SEEK_SET)            
        os.write(f, struct.pack('Q', v))
        os.close(f)

if __name__ == '__main__':
    import sys
    # xxx allow specifying cpu(s) for read
    if len(sys.argv) == 2:
        print "%x" % (readmsr(int(sys.argv[1], 16)),)
    elif len(sys.argv) == 3:
        writemsr(int(sys.argv[1], 16), int(sys.argv[2], 16))
    else:
	print "Usage: msr msrnum [newval]"

