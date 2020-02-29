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
import subprocess

def popen_stdout(cmd):
    try:
        # python 3
        return subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
    except TypeError:
        # python 2
        return subprocess.Popen(cmd, stdout=subprocess.PIPE)

def popen_stdinout(cmd, f):
    try:
        return subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=f, text=True)
    except TypeError:
        return subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=f)

def flex_open_r(fn):
    if fn.endswith(".xz"):
        xz = popen_stdout(["xz", "-d", "--stdout", fn])
        return xz.stdout
    if fn.endswith(".gz"):
        gzip = popen_stdout(["gzip", "-d", "-c", fn])
        return gzip.stdout
    return open(fn, 'r')

def flex_open_w(fn):
    f = open(fn, "w")
    if fn.endswith(".xz"):
        xz = popen_stdinout(["xz", "-z", "--stdout"], f)
        return xz.stdin
    if fn.endswith(".gz"):
        gzip = popen_stdinout(["gzip", "-c"], f)
        return gzip.stdin
    return f
