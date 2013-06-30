#!/usr/bin/env python
# library and tool to access PCI config space
import os
import struct

# no multiple domains, controllers so far

def probe(bus, dev, func):
    fn = "/sys/devices/pci0000:%02x/0000:%02x:%02x.%01x/config" % (bus, bus, dev, func)
    return os.path.isfile(fn)    

def openpci(bus, dev, func, offset, mode):
    fn = "/sys/devices/pci0000:%02x/0000:%02x:%02x.%01x/config" % (bus, bus, dev, func)
    f = os.open(fn, mode)
    os.lseek(f, offset, os.SEEK_SET)
    return f

sizes = {8: "Q", 4: "I", 2: "H", 1: "B"}

def writepci(bus, device, func, offset, size, val):
    f = openpci(bus, device, func, offset, os.O_WRONLY)
    os.write(f, struct.pack(sizes[size], val))
    os.close(f)

def readpci(bus, device, func, offset, size):
    f = openpci(bus, device, func, offset, os.O_RDONLY)
    v = struct.unpack(sizes[size], os.read(f, size))[0]
    os.close(f)
    return v

def changebit(bus, device, func, offset, bit, val):
    f = openpci(bus, device, func, offset, os.O_RDWR)
    v = struct.unpack("I", os.read(f, 4))[0]
    if val:
        v = v | (1 << bit)
    else:
        v = v & ~(1 << bit)
    os.lseek(f, offset, os.SEEK_SET)
    os.write(f, struct.pack('I', v))
    os.close(f)
    
