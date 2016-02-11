#!/usr/bin/env python
# convert README.md to include files for help2man
import sys
import re

skip_sections = ( "Command Line options reference", "Debugging and testing", "Support",
                  "Author", "Other Projects providing uncore monitoring")

tabmode = False
skip = False
for l in sys.stdin:
        after = ""
        l = l.rstrip()
        if l and l[0] == '#':
                skip = False
                if l[2:] in skip_sections:
                    skip = True
                    continue
                print "[%s]" % (l[2:])
                continue
        elif l == "" and not skip:
                print ".PP"
                tabmode = False
                continue
        if skip:
                continue
        if l and l[0] == '\t' and l[1:]:
                if not tabmode:
                        print ".nf\n.sp"
                        tabmode = True
                #print ".I ",
        elif tabmode:
                after = ".fi"
                tabmode = False
        if l and l[0] == '-':
                print ".TP"
                l = l[2:]
        if l and l[0:2] == "**":
                print ".B ",
                l = l.replace("**","")
        if l and l[0] == '[':
                m = re.match(r"\[(.*)\]\s*\((.*)\)(.*)", l)
                #l = '.URL "%s" "%s"\n%s' % (m.group(2), m.group(1), m.group(3))
                l = m.group(2) + " " + m.group(1) + " " + m.group(3)
        print l
        if after:
                print after
