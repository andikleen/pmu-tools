# track mmap updates in a perf stream and allow lookup of symbols
#
# Copyright (c) 2013-2014, Intel Corporation
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

from collections import defaultdict
import bisect

# max reorder window for MMAP updates
LOOKAHEAD_WINDOW = 1024

def lookup(m, ip):
    i = bisect.bisect_left(m, (ip,))
    if i < len(m) and m[i][0] == ip:
        mr = m[i]
    elif i == 0:
        return None, 0
    else:
        mr = m[i - 1]
    return mr, ip - mr[0] 

class MmapTracker:
    """Track mmap updates in a perf stream and allow lookup of symbols."""

    def __init__(self):
        self.maps = defaultdict(list)
        self.pnames = defaultdict(str)
        self.lookahead = 0
        self.updates = []    

    # look ahead for out of order mmap updates
    def lookahead_mmap(self, ev, n):
        if n - self.lookahead == 0:
            self.lookahead = min(n + LOOKAHEAD_WINDOW, len(ev))
            for l in range(n, self.lookahead):
                j = ev[l]
                # no time stamp: assume it's synthesized and kernel
                if j.type in ('MMAP','MMAP2') and j.pid == -1 and j.tid == 0:
                    bisect.insort(self.maps[j.pid], 
                                  (j.addr, j.len, j.filename))
                elif j.type in ('COMM','MMAP','MMAP2'):
                    bisect.insort(self.updates, (j.time2, j))

    # process pending updates for a sample
    def update_sample(self, j):
        updates = self.updates
        while len(updates) > 0 and j.time >= updates[0][0]:
            u = updates[0][1]
            del updates[0]
            if u.type == 'MMAP':
                pid = u.pid
                bisect.insort(self.maps[pid], (u.addr, u.len, u.filename))
            elif u.type == 'COMM':
                self.maps[u.pid] = []
                self.pnames[u.pid] = u.comm

    # look up tables with current state
    def resolve(self, pid, ip):
        if not self.maps[pid]:
            # xxx kernel
            return None, None, 0
        m, offset = lookup(self.maps[pid], ip)
        if not m or offset >= m[1]:
            # look up kernel
            m, offset = lookup(self.maps[-1], ip)
            if not m or offset >= m[1]:
                return None, None, 0
        assert m[0] <= ip <= m[0] + m[1]
        return m[2], m[0], offset
