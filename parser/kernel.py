#!/usr/bin/python
# resolve kernel symbols through kallsyms (when no vmlinux is available)
import sys
import util

kernel = []

def parse_kernel():
    with open("/proc/kallsyms", 'r') as f:
        for l in f:
            n = l.split()
            addr = int(n[0], 16)
            kernel.append((addr, n[2]))

def resolve_kernel(ip):
    if not kernel:
        parse_kernel()
    n = util.find_le(kernel, ip)
    if n:
        return n[1], ip - n[0]
    return None
