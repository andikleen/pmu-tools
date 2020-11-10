#!/usr/bin/env python
# merge multiple --perf-output files. requires header
from __future__ import print_function
import csv
import argparse
from collections import OrderedDict, Counter
import sys

ap = argparse.ArgumentParser()
ap.add_argument('csvfiles', nargs='+', type=argparse.FileType('r'))
args = ap.parse_args()

def genkey(c, hdr, count):
    k = [count]
    if 'Timestamp' in hdr:
        k.append(c[hdr['Timestamp']])
    if 'Location' in hdr:
        k.append(c[hdr['Location']])
    k.append(c[hdr['Event']])
    return tuple(k)

d = OrderedDict()
hdr = None
hdrl = None
prev = Counter()
for fh in args.csvfiles:
    csvf = csv.reader(fh, delimiter=';')
    for c in csvf:
        if hdr is None:
            hdrl = c
            hdr = dict([(y,x) for x,y in enumerate(c)])
            continue
        if c[0] in ("Timestamp", "Location", "Value"):
            continue
        pkey = (fh, c[hdr['Timestamp']] if 'Timestamp' in hdr else None, c[hdr['Event']])
        prev[pkey] += 1
        key = genkey(c, hdr, prev[pkey])
        try:
            if key in d:
                o = d[key]
                o[hdr['Run-Time']] += float(c[hdr['Run-Time']])
                o[hdr['Enabled']] = (float(o[hdr['Enabled']]) + o[hdr['Enabled']]) / 2
                o[hdr['Value']] += float(c[hdr['Value']])
            else:
                d[key] = c
                o = d[key]
                o[hdr['Value']] = float(c[hdr['Value']])
                o[hdr['Enabled']] = float(c[hdr['Enabled']])
                o[hdr['Run-Time']] = float(c[hdr['Run-Time']])
        except ValueError as e:
            print("cannot parse", c, e, file=sys.stderr)

csvf = csv.writer(sys.stdout, delimiter=';')
csvf.writerow(hdrl)
for j in d.values():
    csvf.writerow(j)
