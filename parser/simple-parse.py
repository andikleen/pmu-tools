#!/usr/bin/python
# quick hackish perf event parsing
# only dump event headers and itrace regions
import os, sys, struct

f = os.open(sys.argv[1], os.O_RDONLY)

magic, size, attr_size, attr_off, attr_len, events_off, events_len = struct.unpack('QQQQQQQ', os.read(f, 7*8))
if magic != 0x32454c4946524550: # PERFILE2
    sys.exit("bad file format")
print "size", size, "attr_size", attr_size
print "events_off", events_off, "events_len", events_len

offset = events_off

while offset < events_off + events_len:
    os.lseek(f, offset, os.SEEK_SET)
    hdr = os.read(f, 8)
    type, misc, len = struct.unpack('IHH', hdr)
    # subset only
    records = { 1: "MMAP", 2: "LOST", 3: "COMM", 4: "EXIT", 7: "FORK", 70: "ITRACE_INFO", 71: "ITRACE", 72: "ITRACE_ERROR" }
    if type in records:
        type = records[type]
    print "o:%x" % (offset), "type:", type, "misc:", misc, "len:", len
    if type == "ITRACE": # ITRACE has a extra size field
       isize, ioffset, ref, idx, tid, cpu, res = struct.unpack('QQQIIII', os.read(f, 3*8 + 4*4))
       print "itrace at %x len %x ioffset:%x tid:%d cpu:%d" % (os.lseek(f, 0, os.SEEK_CUR), isize, ioffset, tid, cpu)
       offset += isize
    offset += len
