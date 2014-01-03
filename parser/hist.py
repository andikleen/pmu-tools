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
p.add_argument('--min-percent', help='Minimum percent to print', default=1.0)
args = p.parse_args()

def print_feat(feat):
    print "# Measured on %s (%s)" % (
            feat.hostname.hostname,
            feat.osrelease.osrelease)
    print "# %s, %s" % (
            feat.cpudesc.cpudesc,
            feat.cpuid.cpuid)
    print "# %s" % (" ".join(map(lambda x: x.cmdline, feat.cmdline.cmdline)))

def compute_cols(c):
    return min(max(map(lambda x: len(x), c)) + 5, 70)

min_percent = float(args.min_percent) / 100.0
for d in args.datafiles:
    df, et, feat = perfpd.read_samples(d, (args.sort == 'line'))
    print_feat(feat)

    # xxx split by event
    if 'period' in df:
        total = float(df['period'].sum())
        g = df.groupby(args.sort)
        h = g.period.sum()
        h.sort(ascending=False)
        h = h.apply(lambda x: x / total)
    else:
        h = df[args.sort].value_counts(normalize=True)

    h = h[h >= min_percent]

    cols = compute_cols(h.index)
    for s, v in zip(h.index, h.values):
        print "%-*s %.2f%%" % (cols, s, v*100.0)
