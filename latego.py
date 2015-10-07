#!/usr/bin/env python
# configure latego workaround on Sandy Bridge EP
# can be run as a standalone tool or used as module
# latego enable|disable hexevent
import msr
import pci
import signal
import struct
import os
import re

busses = (0x3f, 0x7f, 0xbf, 0xff)

def local_direct2core(val):
    c = 0
    for b in busses:
        if pci.probe(b, 14, 0):        
            pci.changebit(b, 14, 0, 0x84, 1, val)
            c += 1
    if c == 0:
        print "no local devices found"

def remote_direct2core(val):
    c = 0
    for b in busses:
        if pci.probe(b, 8, 0):
            pci.changebit(b, 8, 0, 0x80, 1, val)
            pci.changebit(b, 9, 0, 0x80, 1, val)
            c += 1
    if c == 0:
        print "no remote devices found"

def direct2core(val):
    # make sure all cores are awake when we do that
    f = os.open("/dev/cpu_dma_latency", os.O_WRONLY)
    os.write(f, struct.pack("I", 0))
    local_direct2core(val)
    remote_direct2core(val)
    os.close(f)

def set_bypass(val):
    msr.changebit(0x39c, 0, val)

bypass  = 1 << 0
d2c     = 1 << 1
latego_events = {
    0x04d1: bypass,
    0x20d1: bypass|d2c,
    0x01d3: bypass|d2c,
    0x04d3: bypass|d2c,
    0x01d2: bypass,
    0x02d2: bypass,
    0x04d2: bypass,
    0x08d2: bypass,
    0x01cd: bypass|d2c
}

latego_names = {
    "mem_load_uops_retired.llc_hit": 0x04d1,
    "mem_load_uops_retired.llc_miss": 0x20d1,
    "mem_load_uops_llc_miss_retired.local_dram": 0x01d3,
    "mem_load_uops_llc_miss_retired.remote_dram": 0x04d3,
    "mem_load_uops_llc_hit_retired.xsnp_miss": 0x01d2,
    "mem_load_uops_llc_hit_retired.xsnp_hit": 0x02d2,
    "mem_load_uops_llc_hit_retired.xsnp_hitm": 0x04d2,
    "mem_load_uops_llc_hit_retired.xsnp_none": 0x08d2,
    "mem_trans_retired.load_latency": 0x01cd
}

signal_setup = False
enabled = 0

def cleanup():
    if enabled & bypass:
        set_bypass(0)
    if enabled & d2c:
        direct2core(0)

def get_event(e):
    if re.match(r"[0-9]+", e):
        return int(e, 16)
    if e in latego_names:
        return latego_names[e]
    return e

def setup_event(event, val):
    global signal_setup
    global enabled
    action = ("Disabling", "Enabling")[val]
    if val and not signal_setup:
        signal.signal(signal.SIGINT, cleanup)
        signal.signal(signal.SIGPIPE, cleanup)
        signal_setup = True
    if event in latego_events:
        v = latego_events[event]
        if v & d2c:
            print "%s direct2core" % (action)
            direct2core(val)
        if v & bypass:
            print "%s bypass" % (action)
            set_bypass(val)
        if val:
            enabled = v
        else:
            enabled = 0

if __name__ == '__main__':
    import sys
    if len(sys.argv) == 3 and sys.argv[1] == "enable":
        setup_event(get_event(sys.argv[2]), 1)
    elif len(sys.argv) == 3 and sys.argv[1] == "disable":
        setup_event(get_event(sys.argv[2]), 0)
    elif len(sys.argv) == 2 and sys.argv[1] == "list":
        print "%-45s %04s" % ("name", "hex")
        for i in latego_names.keys():
            print "%-45s %04x" % (i, latego_names[i], )
    else:
        print "Usage: latego enable|disable hexevent|namedevent"
        print "       latego list"
        sys.exit(1)
