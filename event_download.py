#!/usr/bin/env python2
# Copyright (c) 2014, Intel Corporation
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
# Automatic event list downloader
#
# event_download.py         download for current cpu
# event_download.py -a      download all
# event_download.py cpustr...  Download for specific CPU
#
# env:
# CPUINFO=... override /proc/cpuinfo file
import sys
import re
from urllib2 import urlopen, URLError
import os
import string
from fnmatch import fnmatch

urlpath = 'https://download.01.org/perfmon'
mapfile = 'mapfile.csv'
modelpath = urlpath + "/" + mapfile

def get_cpustr():
    cpuinfo = os.getenv("CPUINFO")
    if cpuinfo is None:
        cpuinfo = '/proc/cpuinfo'
    f = open(cpuinfo, 'r')
    cpu = [None, None, None, None]
    for j in f:
        n = j.split()
        if n[0] == 'vendor_id':
            cpu[0] = n[2]
        elif n[0] == 'model' and n[1] == ':':
            cpu[2] = int(n[2])
        elif n[0] == 'cpu' and n[1] == 'family':
            cpu[1] = int(n[3])
        elif n[0] == 'stepping' and n[1] == ':':
            cpu[3] = int(n[2])
        if all(v is not None for v in cpu):
            break
    return "%s-%d-%X-%X" % tuple(cpu)

def sanitize(s, a):
    o = ""
    for j in s:
        if j in a:
            o += j
    return o

def getdir():
    try:
        d = os.getenv("XDG_CACHE_HOME")
        xd = d
        if not d:
            home = os.getenv("HOME")
            d = "%s/.cache" % (home)
        d += "/pmu-events"
        if not os.path.isdir(d):
            # try to handle the sudo case
            if not xd:
                user = os.getenv("SUDO_USER")
                if user:
                    nd = os.path.expanduser("~" + user) + "/.cache/pmu-events"
                    if os.path.isdir(nd):
                        return nd
            os.makedirs(d)
        return d
    except OSError:
        raise Exception('Cannot access ' + d)

NUM_TRIES = 3

def getfile(url, dir, fn):
    tries = 0
    print "Downloading", url, "to", fn
    while True:
        try:
            f = urlopen(url)
            data = f.read()
        except IOError:
            tries += 1
            if tries >= NUM_TRIES:
                raise
            print "retrying download"
            continue
        break
    o = open(os.path.join(dir, fn), "w")
    o.write(data)
    o.close()
    f.close()

def cpu_without_step(match):
    if match.count("-") < 3:
        return match
    n = match.split("-")
    return "%s-%s-%s" % tuple(n[:3])

allowed_chars = string.ascii_letters + '_-.' + string.digits
def download(match, key=None, link=True):
    match2 = cpu_without_step(match)
    found = 0
    dir = getdir()
    try:
        getfile(modelpath, dir, "mapfile.csv")
        models = open(os.path.join(dir, "mapfile.csv"))
        for j in models:
            if j.startswith("Family-model"):
                continue
            n = j.rstrip().split(",")
            if len(n) < 4:
                if len(n) > 0:
                    print "Cannot parse", n
                continue
            cpu, version, name, typ = n
            if not (fnmatch(cpu, match) or fnmatch(cpu, match2) or
                    fnmatch(match2, cpu) or fnmatch(match, cpu)):
                continue
            if key is not None and typ not in key:
                continue
            cpu = sanitize(cpu, allowed_chars)
            url = urlpath + name
            matchfn = match
            if matchfn == "*":
                matchfn = cpu
            fn = "%s-%s.json" % (matchfn, sanitize(typ, allowed_chars))
            try:
                os.remove(os.path.join(dir, fn))
            except OSError:
                pass
            getfile(url, dir, fn)
            if link:
                lname = re.sub(r'.*/', '', name)
                lname = sanitize(lname, allowed_chars)
                try:
                    os.remove(os.path.join(dir, lname))
                except OSError:
                    pass
                try:
                    os.symlink(fn, os.path.join(dir, lname))
                except OSError as e:
                    print >>sys.stderr, "Cannot link %s to %s:" % (name, lname), e
            found += 1
        models.close()
        getfile(urlpath + "/readme.txt", dir, "readme.txt")
    except URLError as e:
        print >>sys.stderr, "Cannot access event server:", e
        print >>sys.stderr, "If you need a proxy to access the internet please set it with:"
        print >>sys.stderr, "\texport https_proxy=http://proxyname..."
        print >>sys.stderr, "If you are not connected to the internet please run this on a connected system:"
        print >>sys.stderr, "\tevent_download.py '%s'" % (match)
        print >>sys.stderr, "and then copy ~/.cache/pmu-events to the system under test"
        print >>sys.stderr, "To get events for all possible CPUs use:"
        print >>sys.stderr, "\tevent_download.py -a"
    except OSError as e:
        print >>sys.stderr, "Cannot write events file:", e
    return found

def download_current(link=False):
    """Download JSON event list for current cpu.
       Returns >0 when a event list is found"""
    return download(get_cpustr(), link=link)

def eventlist_name(name=None, key="core"):
    if not name:
        name = get_cpustr()
    cache = getdir()
    fn = "%s/%s-%s.json" % (cache, name, key)
    if not os.path.exists(fn):
        name = cpu_without_step(name)
        fn = "%s/%s-%s.json" % (cache, name, key)
    return fn

if __name__ == '__main__':
    # only import argparse when actually called from command line
    # this makes ocperf work on older python versions without it.
    import argparse
    p = argparse.ArgumentParser(usage='download Intel event files')
    p.add_argument('--all', '-a', help='Download all available event files', action='store_true')
    p.add_argument('--verbose', '-v', help='Be verbose', action='store_true')
    p.add_argument('--mine', help='Print name of current CPU', action='store_true')
    p.add_argument('--link', help='Create links with the original event file name', action='store_true', default=True)
    p.add_argument('cpus', help='CPU identifiers to download', nargs='*')
    args = p.parse_args()

    cpustr = get_cpustr()
    if args.verbose or args.mine:
        print "My CPU", cpustr
    if args.mine:
        sys.exit(0)
    d = getdir()
    if args.all:
        found = download('*', link=args.link)
    elif len(args.cpus) == 0:
        found = download_current(link=args.link)
    else:
        found = 0
        for j in args.cpus:
            found += download(j, link=args.link)

    if found == 0:
        print >>sys.stderr, "Nothing found"

    el = eventlist_name()
    if os.path.exists(el):
        print "my event list", el
