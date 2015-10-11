# distinguish the bewildering variety of perf/toplev CSV formats
import re
from collections import namedtuple

def is_number(n):
    return re.match(r'[0-9.]+%?', n) != None

def is_cpu(n):
    return re.match(r'(CPU)|(S\d+(-C\d+)?)', n) is not None

def is_socket(n):
    return re.match(r'S\d+', n) is not None

Row = namedtuple('Row', ['ts', 'cpu', 'ev', 'val'])

def parse_csv_row(row):
    # 1.354075473,0,cpu-migrations                                  old perf w/o cpu
    # 1.354075473,CPU0,0,cpu-migrations                             old perf w/ cpu
    # 0.799553738,137765150,,branches                               new perf with unit
    # 0.799553738,CPU1,137765150,,branches                        new perf with unit and cpu
    # 0.100879059,402.603109,,task-clock,402596410,100.00         new perf with unit without cpu and stats
    # 0.200584389,FrontendBound.Branch Resteers,15.87%,above,"",    toplev single thread
    # 0.200584389,0,FrontendBound.Branch Resteers,15.87%,above,"",  toplev w/ cpu
    # 1.001365014,CPU2,1819888,,instructions,93286388,100.00      new perf w/ unit w/ cpu and stats
    # 0.609113353,S0,4,405.454531,,task-clock,405454468,100.00      perf --per-socket with cores
    if len(row) == 0:
        return None
    ts = row[0].strip()
    if len(row) == 3: # old perf
        cpu, ev, val = None, row[2], row[1]
    elif len(row) == 4: # new perf w/ unit or old perf w/ CPU
        if is_cpu(row[1]):  # old
            cpu, ev, val = row[1], row[3], row[2]
        else: # new
            cpu, ev, val = None, row[3], row[1]
    elif len(row) == 5: # new perf w/ CPU
        cpu, ev, val = row[1], row[4], row[2]
    elif len(row) > 5: # toplev or new perf
        if is_number(row[1]) and is_number(row[4]):     # new perf w/o CPU
            cpu, ev, val = None, row[3], row[1]
        elif is_cpu(row[1]) and is_number(row[2]) and is_number(row[5]):
            cpu, ev, val = row[1], row[4], row[2]
        elif len(row) > 6 and is_socket(row[1]) and is_number(row[3]) and is_number(row[6]):
            cpu, ev, val = row[2], row[5], row[3]
        elif "." in row[2] and is_number(row[2]):
            cpu, ev, val = None, row[1], row[2].replace("%", "")
        else:
            cpu, ev, val = row[1], row[2], row[3].replace("%", "")
    elif row[0].startswith("#"):    # comment
        return None
    else:
        print "PARSE-ERROR", row
        return None
    ev = ev.strip()
    return Row(ts=ts, cpu=cpu, ev=ev, val=val)
