# distinguish the bewildering variety of perf/toplev CSV formats
import re
from collections import namedtuple

def is_val(n):
    return re.match(r'-?[0-9.]+%?|<.*>', n) != None

def is_cpu(n):
    return re.match(r'(CPU)|(S\d+(-C\d+)?)|C\d+', n) is not None

def is_socket(n):
    return re.match(r'S\d+', n) is not None

def is_event(n):
    return re.match(r'[a-zA-Z.-]+', n) is not None

def is_number(n):
    return re.match(r'[0-9]+', n) is not None

def is_ts(n):
    return re.match(r'\s*[0-9.]+', n) is not None

def is_unit(n):
    return re.match(r'[a-zA-Z]*', n) is not None

def is_running(n):
    return is_number(n)

def is_enabled(n):
    return is_number(n)

formats = (
# 0.100997872;CPU0;4612809;;inst_retired_any_0;3491526;2.88     new perf
        (is_ts, is_cpu, is_val, is_unit, is_event, is_enabled, is_running),
# 1.354075473,0,cpu-migrations                            old perf w/o cpu
        (is_ts, is_val, is_event),
# 1.354075473,CPU0,0,cpu-migrations                          old perf w/ cpu
        (is_ts, is_cpu, is_val, is_event),
# 0.799553738,137765150,,branches                              new perf with unit
        (is_ts, is_val, is_unit, is_event),
# 0.799553738,CPU1,137765150,,branches                  new perf with unit and cpu
        (is_ts, is_cpu, is_val, is_unit, is_event),
# 0.100879059,402.603109,,task-clock,402596410,100.00    new perf with unit without cpu and stats
        (is_ts, is_val, is_unit, is_event, is_running, is_enabled),
# 0.200584389,0,FrontendBound.Branch Resteers,15.87%,above,"",  toplev w/ cpu
        (is_ts, is_cpu, is_event, is_val),
# 1.001365014,CPU2,1819888,,instructions,93286388,100.00      new perf w/ unit w/ cpu and stats
        (is_ts, is_cpu, is_val, is_unit, is_event, is_running, is_enabled),
# 0.609113353,S0,4,405.454531,,task-clock,405454468,100.00      perf --per-socket with cores
        (is_ts, is_socket, is_number, is_val, is_unit, is_event, is_running, is_enabled),
# 0.806231582,S0,4,812751,,instructions                  older perf --per-socket w/ cores w/o stats
        (is_ts, is_socket, is_number, is_val, is_unit, is_event),
# 0.200584389,FrontendBound.Branch Resteers,15.87%,above,"",    toplev single thread
        (is_ts, is_event, is_val),
# 0.936482669,C1-T0,Frontend_Bound.Frontend_Latency.ITLB_Misses,0.39,%below,,itlb_misses.walk_completed,,
# 0.301553743,C1,Retiring,31.81,%,,,,
        (is_ts, is_cpu, is_event, is_val),
)

fmtmaps = {
    is_ts: 0,
    is_cpu: 1,
    is_event: 2,
    is_val: 3,
    is_enabled : 4,
    is_running : 5
}

Row = namedtuple('Row', ['ts', 'cpu', 'ev', 'val', 'enabled', 'running'])

def check_format(fmt, row):
    if len(row) < len(fmt):
       False
    if all([x(n) for (x, n) in zip(fmt, row)]):
        vals = [None] * 6
        for i, j in enumerate(fmt):
            if j in fmtmaps:
                vals[fmtmaps[j]] = row[i]
        r = Row._make(vals)
        return r;
    return False

fmt_cache = formats[0]

def parse_csv_row(row):
    if len(row) == 0:
        return None
    global fmt_cache
    r = check_format(fmt_cache, row)
    if r:
        return r
    for fmt in formats:
        r = check_format(fmt, row)
        if r:
            fmt_cache = fmt
            return r
    if row[0].startswith("#"):    # comment
        return None
    print "PARSE-ERROR", row
    return None
