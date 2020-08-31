#!/usr/bin/env python2
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
#
# Measure a workload using the topdown performance model:
# estimate on which part of the CPU pipeline it bottlenecks.
#
# Must find ocperf in python module path.
# Handles a variety of perf and kernel versions, but older ones have various
# limitations.

# convert toplev output to xlsx files using xlsxwriter
# toplev.py --all --valcsv xv.log --perf-output xp.log -A -a --split-output --per-socket --global --summary --per-core --per-thread -x, -o x.log -I 1000 sleep 10
# tl_xlsx.py --valcsv xv.log --perf xp.log --socket x-socket.log --global x-global.log --core x-core.log --thread x-thread.log x.xlsx
from __future__ import print_function
import sys
import argparse
try:
    import xlsxwriter
except ImportError:
    sys.exit("Please install xlswriter with 'pip%s install xlsxwriter'" % sys.version[0])
import sys
import csv
import re
import collections

ap = argparse.ArgumentParser(description="Convert toplev CSV files to xlsx")
ap.add_argument('xlsxfile', help="xlsx output name")
ap.add_argument('--socket', type=argparse.FileType('r'), help="toplev socket csv file", metavar="csvfile")
ap.add_argument('--global', type=argparse.FileType('r'), help="toplev global csv file", dest='_global', metavar="csvfile")
ap.add_argument('--core', type=argparse.FileType('r'), help="toplev core csv file", metavar="csvfile")
ap.add_argument('--program', type=argparse.FileType('r'), help="toplev program csv file", metavar="csvfile")
ap.add_argument('--thread', type=argparse.FileType('r'), help="toplev thread csv file", metavar="csvfile")
ap.add_argument('--add', nargs=2, help="toplev thread generic csv file. Specify csvfile and sheet name",
            metavar="name", action="append")
ap.add_argument('--valcsv', type=argparse.FileType('r'), help="toplev valcsv input file", metavar="csvfile")
ap.add_argument('--perf', type=argparse.FileType('r'), help="toplev perf values csv file")
ap.add_argument('--cpuinfo', type=argparse.FileType('r'), help="cpuinfo file")
args = ap.parse_args()

workbook = xlsxwriter.Workbook(args.xlsxfile, {'constant_memory': True})
bold = workbook.add_format({'bold': True})
valueformat = workbook.add_format({'num_format': '###,###,###,###,##0.0'})
#valueformat.set_num_format(1)

def set_columns(worksheet, c, lengths):
    for col, j in enumerate(c):
        if j == "Value":
            j = " " * 18
        if j == "Description":
            j = "Descr"
        lengths[col] = max(len(j) + 5, lengths[col])
        worksheet.set_column(col, col, lengths[col])

worksheets = dict()
rows = dict()

def get_worksheet(name):
    if name in worksheets:
        return worksheets[name]
    worksheet = workbook.add_worksheet(name)
    worksheets[name] = worksheet
    rows[name] = 1
    return worksheet

def create_sheet(name, infh, delimiter=',', version=None):
    lengths = collections.defaultdict(lambda: 0)
    worksheet = get_worksheet(name)
    cf = csv.reader(infh, delimiter=delimiter)
    row = 0
    title = dict()
    titlerow = []
    summary = False
    for c in cf:
        if len(c) > 0 and len(c[0]) > 0 and c[0][0] == "#":
            version = c
            continue
        if row == 0:
            title = { k: i for i, k in enumerate(c) }
            titlerow = c
        if row < 10:
            set_columns(worksheet, c, lengths)
        if not summary and len(c) > 0 and c[0] == "SUMMARY":
            rows[name] = row
            sname = name + " summary"
            worksheet = get_worksheet(sname)
            set_columns(worksheet, c, lengths)
            worksheet.write_row(0, 0, titlerow)
            row = rows[sname]
            summary = True
        elif summary and len(c) > 0 and c[0] != "SUMMARY" and c[0][0] != "#":
            worksheet = get_worksheet(name)
            summary = False
            rows[sname] = row
            row = rows[name]
        worksheet.write_row(row, 0, c)
        if "Bottleneck" in title:
            bn = title["Bottleneck"]
            if len(c) > bn and c[bn] == "<==":
                worksheet.write(row, title["Area"], c[title["Area"]], bold)
                worksheet.write(row, title["Value"], c[title["Value"]], bold)
                worksheet.write(row, bn, c[bn], bold)
        if "Value" in title and len(c) > title["Value"] and re.match(r'[0-9.]+', c[title["Value"]]):
            worksheet.write_number(row, title["Value"], float(c[title["Value"]]), valueformat)
        elif "0" in title:
            num = 0
            while num in title:
                col = title["%d" % num]
                if len(c) > col and re.match(r'[0-9]+', c[col]):
                    worksheet.write_number(row, col, float(c[col]), valueformat)
                num += 1
        row += 1
    return version

version = None
if args._global:
    version = create_sheet("global", args._global, version=version)
if args.socket:
    version = create_sheet("socket", args.socket, version=version)
if args.core:
    version = create_sheet("core", args.core, version=version)
if args.thread:
    version = create_sheet("thread", args.thread, version=version)
if args.program:
    version = create_sheet("prog", args.program, version=version)
if args.add:
    for fn, name in args.add:
        version = create_sheet(name, open(fn), version=version)
if args.valcsv:
    create_sheet("event values", args.valcsv)
if args.perf:
    create_sheet("raw perf output", args.perf, delimiter=';')
if args.cpuinfo:
    create_sheet("cpuinfo", args.cpuinfo, delimiter=':')

if version:
    worksheet = workbook.add_worksheet("version")
    worksheet.write_row(0, 0, version)

workbook.close()
