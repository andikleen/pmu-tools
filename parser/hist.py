#!/usr/bin/python
# print histogram for perf.data
import perfpd
import argparse

p = argparse.ArgumentParser(description='Print histogram for perf.data')
p.add_argument('datafiles', nargs='*', 
               help='perf.data files (default perf.data)',
               default=['perf.data'])
p.add_argument('--sort', help='field to sort on (symbol, line)', 
               default='symbol')
p.add_argument('--min-percent', help='Minimum percent to print', default=0.0)
args = p.parse_args()

def print_feat(feat):
    print "# Measured on %s (%s)" % (
            feat.hostname.hostname,
            feat.osrelease.osrelease)
    print "# %s, %s" % (
            feat.cpudesc.cpudesc,
            feat.cpuid.cpuid)
    print "# %s" % (" ".join(map(lambda x: x.cmdline, feat.cmdline.cmdline)))

min_percent = float(args.min_percent) / 100.0
for d in args.datafiles:
    df, et, feat = perfpd.read_samples(d, (args.sort == 'line'))
    print_feat(feat)
    # xxx split by event
    h = df[args.sort].value_counts(normalize=True)
    cols = min(max(map(lambda x: len(x), h.index)) + 5, 70)
    for s, v in zip(h.index, h.values):
       if v < min_percent:
           break
       print "%-*s %.2f%%" % (cols, s, v*100.0)
