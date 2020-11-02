#!/usr/bin/env python
# mock perf for limited test environments
from __future__ import print_function
import sys

out = sys.stderr
av = sys.argv
if av[-1] == "true":
    sys.exit(0)
j = 1
process = True
while j < len(sys.argv):
    if av[j] == "--version":
        print("perf version 5.6.8", end='')
        break
    elif av[j] == "-o" and process:
        j += 1
        out = open(av[j], "w")
    elif av[j] == "--":
        process = False
    j += 1
out.write("\n")
