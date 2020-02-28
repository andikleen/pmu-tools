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

def flex_open_r(fn):
    if fn.endswith(".xz"):
        xz = subprocess.Popen(["xz", "-d", "--stdout", fn], stdout=subprocess.PIPE)
        return xz.stdout
    if fn.endswith(".gz"):
        gzip = subprocess.Popen(["gzip", "-d", "-c", fn], stdout=subprocess.PIPE)
        return gzip.stdout
    return open(fn, 'r')

def flex_open_w(fn):
    f = open(fn, "w")
    if fn.endswith(".xz"):
        xz = subprocess.Popen(["xz", "-z", "--stdout"], stdin=subprocess.PIPE, stdout=f)
        return xz.stdin
    if fn.endswith(".gz"):
        gzip = subprocess.Popen(["gzip", "-c"], stdin=subprocess.PIPE, stdout=f)
        return gzip.stdin
    return f
