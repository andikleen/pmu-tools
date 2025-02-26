#!/usr/bin/env python3
# -*- coding: utf-8
# generate return latencies to tune toplev model
# Copyright (c) 2023, Intel Corporation
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
from __future__ import print_function
import subprocess as subp
import os
import sys
import ocperf
import json
import argparse
import random
import glob
import re
from dummyarith import DummyArith
from collections import Counter, defaultdict
from copy import copy
import csv

def cmd(args, l):
    if args.verbose:
        print(" ".join(l))
    return l

class SamplePerfRun(object):
    """Run perf record to collect Timed PEBS information and generate averages for event weights."""
    def __init__(self, args):
        self.pi = self.pr = self.ps = None
        self.args = args

    def execute(self, perf, evsamples, origevents, pargs):
        self.perf = perf
        self.rmap = { x: y for x, y in zip(evsamples, origevents) }
        pr = subp.Popen(cmd(self.args, [perf, "record",
                                   "-W",
                                   "-B",
                                   "-c", "%d" % self.args.interval,
                                   "-e", ",".join(evsamples),
                                   "-o", "-"] + pargs),
                                   stdout=subp.PIPE)
        pi = subp.Popen(cmd(self.args, [perf, "inject"]),
                                 stdin=pr.stdout,
                                 stdout=subp.PIPE)
        ps = subp.Popen(cmd(self.args, [perf, "script",
                                   "-i", "-",
                                   "--ns",
                                   "-F", "time,retire_lat,event"]),
                                   stdin=pi.stdout,
                                   stdout=subp.PIPE)
        pi.stdout.close()
        pr.stdout.close()
        self.pr, self.pi, self.ps = pr, pi, ps

    def handle_samples(self):
        for l in self.ps.stdout:
            l = l.decode()
            n = l.split()
            ts, event, weight = float(n[0].replace(":","")), n[1].replace(":",""), int(n[2])
            if self.args.csvplot:
                self.args.csvplot.writerow([ts, self.rmap[event] if event in self.rmap else event, weight])
            if self.args.fake:
                yield event, random.randint(0, 100)
            else:
                yield event, weight
        self.pr.wait()
        self.pi.wait()
        self.ps.wait()

NUM_SPARKS = 8
SPARK_SHIFT = 8

def spark_f(l):
    min_ = min(l)
    f = int(max(((max(l) - min_) << SPARK_SHIFT) / (NUM_SPARKS - 1), 1))
    return f, min_

# this samples unlike normal spark lines
def gen_spark_buckets(l):
    if len(l) == 0:
        return [], 0, 1
    f, min_ = spark_f(l)
    return [((x - min_) << SPARK_SHIFT) / f for x in random.sample(l, min(NUM_SPARKS, len(l)))], min_, f

def lookup(s, i, fb):
    if 0 <= i <= len(s) - 1:
        return s[i]
    return fb

def gen_spark(buckets, min_, f):
    return "".join([lookup("▁▂▃▄▅▆▇█", int((int((x - min_)) << SPARK_SHIFT) / f), " ") for x in buckets])

def gen_stat(samples):
    # {
    #     "COUNT": 5358917,
    #     "MIN": 0,
    #     "MAX": 65535,
    #     "MEAN": 3.23,
    #     "MEDIAN": 0,
    #     "NZ_MEDIAN": 1,
    #     "MODE": 0,
    #     "MODE_COUNT": 3631698,
    #     "NZ_MODE": 1,
    #     "NZ_MODE_COUNT": 1213029,
    #     "BUCKETS": 2344
    #   },
    nz = [x for x in samples if x != 0.0]
    buckets = Counter(samples)
    nz_buckets = copy(buckets)
    if 0 in nz_buckets:
        del nz_buckets[0]
    spark, min_, f = gen_spark_buckets(samples)
    spark_nz, min_nz, f_nz = gen_spark_buckets(nz)
    return {
        "COUNT": len(samples),
        "MIN": min(samples),
        "MAX": max(samples),
        "MEAN": round(float(sum(samples)) / len(samples), 2),
        "MEDIAN": sorted(samples)[len(samples)//2] if len(samples) > 0 else 0.0,
        "NZ_MEDIAN": sorted(nz)[len(nz)//2] if len(nz) > 0 else 0.0,
        "MODE": buckets.most_common(1)[0][0] if len(buckets) > 0 else 0.0,
        "MODE_COUNT": buckets.most_common(1)[0][1] if len(buckets) > 0 else 0,
        "NZ_MODE": nz_buckets.most_common(1)[0][0] if len(nz_buckets) > 0 else 0,
        "NZ_MODE_COUNT": nz_buckets.most_common(1)[0][1] if len(nz_buckets) > 0 else 0,
        "BUCKETS": len(buckets),
        "F": f,
        "F_NZ": f_nz,
        "MIN_NZ": min_nz,
        "SPARK_BUCKETS": ",".join(["%d" % x for x in spark]),
        "SPARK_BUCKETS_NZ": ",".join(["%d" % x for x in spark_nz]),
    }

def human_output(data):
    d = data["Data"]
    for ev in sorted(d.keys()):
        print("%s: " % ev, end="")
        for m in sorted(d[ev].keys()):
            if m.startswith("SPARK"):
                if d[ev][m] == "":
                    continue
                l = [(int(x) if x.isdecimal() else 0) for x in d[ev][m].split(",")]
                s = gen_spark(l, d[ev]["MIN"], d[ev]["F_NZ" if m.endswith("_NZ") else "F"])
                print("%s %s " % (m.lower(), s), end="")
            else:
                print("%s %s " % (m.lower(), d[ev][m]), end="")
        print()

def get_model_number():
    with open("/proc/cpuinfo") as f:
        for l in f:
            n = l.split()
            if len(n) >= 3 and n[0] == "model" and n[1] == ":":
                return int(n[2])
    return 0

def find_model(args):
    if not args.cpu:
        cpu = "?"
        cl = glob.glob("/sys/bus/event_source/devices/cpu*/caps/pmu_name")
        for fn in cl:
            cpu = open(fn).read().strip()
            if cpu == "meteorlake_hybrid":
                args.cpu = "mtl"
            elif cpu == "sapphire_rapids":
                model = get_model_number()
                if model == 0xad or model == 0xae:
                    args.cpu = "gnr"
                else:
                    sys.exit("Unsupported CPU %d" % model)
            elif cpu == "granite_rapids":
                args.cpu = "gnr"
            elif cpu == "lunarlake_hybrid":
                args.cpu = "lnl"
    if not args.cpu:
        sys.exit("Unsupported CPU %s" % cpu)
    if args.cpu == "mtl":
        import mtl_rwc_ratios
        return mtl_rwc_ratios
    elif args.cpu == "gnr":
        import gnr_server_ratios
        return gnr_server_ratios
    elif args.cpu == "lnl":
        import lnl_lnc_ratios
        return lnl_lnc_ratios
    sys.exit("Unknown cpu %s" % args.cpu)

def gen_events(args):
    model = find_model(args)

    nodes = []
    class Runner(object):
        def metric(self, n):
            nodes.append(n)
            n.thresh = True
        def run(self, n):
            nodes.append(n)
            n.thresh = True

    model.Setup(Runner())

    events = set()
    def collect(name, level):
        if level == 999:
            events.add(name + ":pp")
        return DummyArith()

    for n in nodes:
        n.compute(collect)

    return sorted(events)

def getevent(emap, e):
    ev = emap.getevent(e)
    if ev is None:
        print(e, "not found")
        return "dummy"
    return ev.output()

def init_args():
    ap = argparse.ArgumentParser('Generate JSON of retirement latencies to tune toplev')
    ap.add_argument('--output', '-o', type=argparse.FileType('w'), default=sys.stdout,
                    help="")
    ap.add_argument('--verbose', '-v', action='store_true', help='be verbose')
    ap.add_argument('--fake', action='store_true', help=argparse.SUPPRESS)
    ap.add_argument('--interval', '-i', type=int, default=1003, help="Interval for sampling")
    ap.add_argument('--pmu', '-p', nargs='*', default=["cpu", "cpu_core"], help="for which PMUs to collect")
    ap.add_argument('--quiet', '-q', action='store_true')
    ap.add_argument('--csv', '-c', type=argparse.FileType('w'), help="Generate CSV file with pushout latencies", default=None)
    ap.add_argument('--cpu', help="Set CPU type (gnr, mtl, lnl)")
    args, rest = ap.parse_known_args()
    if args.csv:
        args.csvplot = csv.writer(args.csv)
    else:
        args.csvplot = None
    return args, rest

def main():
    args, rest = init_args()
    events = gen_events(args)
    pmus = ocperf.find_pmus()
    emap = ocperf.find_emap(pmu=[x for x in pmus if x != "cpu_atom"][0])
    if emap is None:
        sys.exit("Cannot find json event list")
    pevents = [getevent(emap, e) for e in events]
    if args.verbose:
        print(events)
    s = SamplePerfRun(args)
    perf = os.getenv("PERF")
    if perf is None:
        perf = "perf"
    try:
        s.execute(perf, pevents, events, rest)
        samples = defaultdict(list)
        for ev, weight in s.handle_samples():
            samples[ev].append(weight)
    except KeyboardInterrupt:
        pass
    data = { "Data": { re.sub(r"[:/][uU]?", "", ev.upper()).replace("CPU_CORE","").replace("RETIRED_", "RETIRED."): gen_stat(s)
                       for ev, s in samples.items()
                       if "/" not in ev or any([x in ev for x in args.pmu]) } }
    json.dump(data, args.output, indent=2, sort_keys=True)
    if not args.quiet:
        human_output(data)

if __name__ == '__main__':
    main()
