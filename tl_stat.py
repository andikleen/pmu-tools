# Copyright (c) 2012-2015, Intel Corporation
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
#
# Maintain error data on perf measurements
import sys
import math
from collections import namedtuple

ValStat = namedtuple('ValStat', ['stddev', 'multiplex'])

def geoadd(l):
    return math.sqrt(sum([x**2 for x in l]))

# use geomean of stddevs and minimum of multiplex ratios for combining
# XXX better way to combine multiplex ratios?
def combine_valstat(l):
    if not l:
        return []
    return ValStat(geoadd([x.stddev for x in l]), min([x.multiplex for x in l]))

def isnan(x):
    return x != x

def format_valstat(valstat):
    vs = ""
    if valstat:
        if valstat.stddev:
            vs += "+-%6.2f " % valstat.stddev
        if valstat.multiplex and not isnan(valstat.multiplex):
            vs += "[%6.2f%%]" % valstat.multiplex
    if vs:
        vs = "%8s" % vs
    return vs

class ComputeStat:
    """Maintain statistics on measurement data."""
    def __init__(self, quiet):
        self.referenced = set()
        self.already_warned = set()
        self.errcount = 0
        self.errors = set()
        self.prev_errors = set()
        self.mismeasured = set()
        self.prev_mismeasured = set()
        self.quiet = quiet

    def referenced_check(self, res):
        referenced = self.referenced
        referenced = referenced - self.already_warned
        if not referenced:
            return
        self.already_warned |= referenced

        # sanity check: did we reference all results?
        if len(res.keys()) > 0:
            r = res[res.keys()[0]]
            if len(referenced) != len(r) and not self.quiet:
                print >>sys.stderr, "warning: %d results not referenced:" % (len(r) - len(referenced)),
                print >>sys.stderr, " ".join(["%d" % x for x in sorted(set(range(len(r))) - referenced)])

    def compute_errors(self):
        if self.errcount > 0 and self.errors != self.prev_errors:
            if not self.quiet:
                print >>sys.stderr, "warning: %d division by zero errors:" % (self.errcount),
                print >>sys.stderr, " ".join(self.errors)
            self.errcount = 0
            self.prev_errors = self.errors
            self.errors = set()
        if self.mismeasured and self.mismeasured > self.prev_mismeasured and not self.quiet:
            print "warning: Mismeasured:", " ".join(self.mismeasured)
            self.prev_mismeasured = self.mismeasured
