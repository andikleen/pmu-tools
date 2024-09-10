# Copyright (c) 2020, Intel Corporation
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
import sys
import subprocess
import os
import argparse
if sys.version_info.major == 3:
    from typing import Set # noqa

if sys.version_info.major == 3:
    popentext = dict(universal_newlines=True)
else:
    popentext = {}

def popen_stdout(cmd):
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, **popentext) # type: ignore

def popen_stdinout(cmd, f):
    return subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=f, **popentext) # type: ignore

def flex_open_r(fn):
    if fn.endswith(".xz"):
        xz = popen_stdout(["xz", "-d", "--stdout", fn])
        return xz.stdout
    if fn.endswith(".gz"):
        gzip = popen_stdout(["gzip", "-d", "-c", fn])
        return gzip.stdout
    if fn.endswith(".zst"):
        return popen_stdout(["zstd", "-d", "--stdout", fn]) .stdout
    return open(fn, 'r')

def flex_open_w(fn):
    f = open(fn, "w")
    if fn.endswith(".xz"):
        xz = popen_stdinout(["xz", "-z", "--stdout"], f)
        return xz.stdin
    if fn.endswith(".gz"):
        gzip = popen_stdinout(["gzip", "-c"], f)
        return gzip.stdin
    if fn.endswith(".zst"):
        return popen_stdinout(["zstd", "--stdout"], f).stdin
    return f

tl_tester = os.getenv("TL_TESTER")
test_mode = tl_tester and tl_tester != "0"

args = argparse.Namespace()

def set_args(a):
    global args
    args = a

def warn_no_assert(msg):
    if not args.quiet:
        print("warning: " + msg, file=sys.stderr)

def warn_test(msg):
    if test_mode:
        warn_no_assert(msg)

def warn(msg):
    warn_no_assert(msg)
    if test_mode:
        assert 0, msg

warned = set() # type: Set[str]

def warn_once_no_assert(msg):
    if msg not in warned and not args.quiet:
        print("warning: " + msg, file=sys.stderr)
        warned.add(msg)

def warn_once(msg):
    warn_once_no_assert(msg)
    if test_mode:
        assert 0, msg

def print_once(msg):
    if msg not in warned and not args.quiet:
        print(msg)
        warned.add(msg)

def inform(msg):
    if not args.quiet:
        print(msg)

def debug_print(x):
    if args.debug:
        print(x, file=sys.stderr)

def obj_debug_print(obj, x):
    if args.debug or (args.dfilter and obj.name in args.dfilter):
        print(x, file=sys.stderr)

def test_debug_print(x):
    if args.debug or test_mode:
        print(x, file=sys.stderr)
