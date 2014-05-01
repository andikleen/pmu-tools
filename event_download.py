#!/usr/bin/python
# automatically download json event files
#
# event_download.py         download for current cpu
# event_download.py -a      download all
# event_download.py cpustr...  Download for specific CPU
import sys
from urllib2 import urlopen, URLError
import argparse
import os
import string
from fnmatch import fnmatch
import argparse

urlpath = 'https://download.01.org/perfmon'
mapfile = 'mapfile.csv'
modelpath = urlpath + "/" + mapfile

def get_cpustr():
    f = open('/proc/cpuinfo', 'r')
    cpu = [None, None, None]
    for j in f:
        n = j.split()
        if n[0] == 'vendor_id':
            cpu[0] = n[2]
        elif n[0] == 'model' and n[1] == ':':
            cpu[2] = int(n[2])
        elif n[0] == 'cpu' and n[1] == 'family':
            cpu[1] = int(n[3])
        if all(cpu):
            break
    return "%s-%d-%X" % (cpu[0], cpu[1], cpu[2])

def sanitize(s, a):
    o = ""
    for j in s:
        if j in a:
            o += j
    return o

def getdir():
    try:
        d = os.getenv("CACHEDIR")
        home = os.getenv("HOME")
        if not d:
            d = "%s/.cache/pmu-events" % (home)
        if not os.path.isdir(d):
            os.makedirs(d)
        return d
    except OSError:
        raise Exception('Cannot access ' + d) 

def getfile(url, dir, fn):
    print "Downloading", url, "to", fn
    f = urlopen(url)
    o = open(os.path.join(dir, fn), "w")
    o.write(f.read())
    o.close()
    f.close()

def download(match, key="core"):
    found = 0
    dir = getdir()
    try:
        getfile(modelpath, dir, "mapfile.csv")
        models = open(os.path.join(dir, "mapfile.csv"))
        for j in models:
            cpu, version, name, type  = j.rstrip().split(",")
            if not fnmatch(cpu, match) or type != key:
                continue
            cpu = sanitize(cpu, string.ascii_letters + '-' + string.digits)
            url = urlpath + name
            getfile(url, dir, "%s-%s.json" % (cpu, key))
            found += 1
        models.close()
        getfile(urlpath + "/readme.txt", dir, "readme.txt")
    except URLError as e:
        print >>sys.stderr, "Cannot access event server:", e
    except OSError as e:
        print >>sys.stderr, "Cannot write events file:", e
    return found

def download_current():
    """Download JSON event list for current cpu.
       Returns >0 when a event list is found"""
    return download(get_cpustr())

def eventlist_name(name=None, key="core"):
    if not name:
        name = get_cpustr()
    cache = os.getenv("XDG_CACHE_HOME")
    if not cache:
        cache = os.getenv("HOME")
        if not cache:
            return None
        cache += "/.cache"
    return "%s/pmu-events/%s-%s.json" % (cache, name, key)

if __name__ == '__main__':
    p = argparse.ArgumentParser(usage='download Intel event files')
    p.add_argument('--all', '-a', help='Download all available event files', action='store_true')
    p.add_argument('--verbose', '-v', help='Be verbose', action='store_true')
    p.add_argument('--mine', help='Print name of current CPU', action='store_true')
    p.add_argument('cpus', help='Cpu strings to download', nargs='*')
    args = p.parse_args()

    cpustr = get_cpustr()
    if args.verbose or args.mine:
        print "My CPU", cpustr
    if args.mine:
        sys.exit(0)
    d = getdir()
    if args.all:
        found = download('*')
    elif len(args.cpus) == 0:
        found = download_current()
    else:
        found = 0
        for j in args.cpus:
            found += download(j)

    if found == 0:
        print >>sys.stderr, "Nothing found"

    el = eventlist_name()
    if os.path.exists(el):
        print "my event list", el
