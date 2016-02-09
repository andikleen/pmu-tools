#!/usr/bin/env python
# resolve kernel symbols through kallsyms (when no vmlinux is available)
#
# Copyright (c) 2014, Intel Corporation
# Author: Andi Kleen
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.

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
