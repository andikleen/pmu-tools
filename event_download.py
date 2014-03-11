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

def dodir():
    try:
        d = "%s/.events" % (os.getenv('HOME'))
        if not os.path.isdir(d):
            os.mkdir(d)
        os.chdir(d)
    except OSError:
        sys.exit('Cannot access ~/.events')

def getfile(url, fn):
    print "Downloading", url, "to", fn
    f = urlopen(url)
    o = open(fn, "w")
    o.write(f.read())
    o.close()
    f.close()

def download(match, key="core"):
    found = 0
    try:
        print "Downloading", modelpath
        models = urlopen(modelpath)
        for j in models:
            cpu, version, name, type  = j.rstrip().split(",")
            if not fnmatch(cpu, match) or type != key:
                continue
            cpu = sanitize(cpu, string.ascii_letters + '-' + string.digits)
            url = urlpath + name
            getfile(url, "%s-%s.json" % (cpu, key))
            found += 1
        models.close()
        getfile(urlpath + "/readme.txt", "readme.txt")
    except URLError as e:
        print "Cannot access event server:", e
    except OSError as e:
        print "Cannot write events file:", e
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
    cpustr = get_cpustr()
    dodir()
    if len(sys.argv) == 1:
        found = download_current()
    elif len(sys.argv) == 2 and sys.argv[1] == '-a':
        found = download('*')
    else:
        found = 0
        for j in sys.argv[1:]:
            found += download(j)

    if found == 0:
        print >>sys.stderr, "Nothing found"

    el = eventlist_name()
    if os.path.exists(el):
        print "my event list", el
