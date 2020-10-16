#!/usr/bin/env python
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

# convert toplev output to xlsx files using xlsxwriter
# toplev.py --all --valcsv xv.log --perf-output xp.log -A -a --split-output --per-socket --global --summary \
# --per-core --per-thread -x, -o x.log -I 1000 sleep 10
# tl_xlsx.py --valcsv xv.log --perf xp.log --socket x-socket.log --global x-global.log --core x-core.log --thread x-thread.log x.xlsx
from __future__ import print_function
import sys
import argparse
import re
import collections
import csv
try:
    import xlsxwriter
except ImportError:
    sys.exit("Please install xlswriter with 'pip%s install xlsxwriter'" % sys.version[0])
import gen_level

ap = argparse.ArgumentParser(description="Convert toplev CSV files to xlsx")
ap.add_argument('xlsxfile', help="xlsx output name")
ap.add_argument('--socket', type=argparse.FileType('r'), help="toplev socket csv file", metavar="csvfile")
ap.add_argument('--global', type=argparse.FileType('r'), help="toplev global csv file", dest='global_', metavar="csvfile")
ap.add_argument('--core', type=argparse.FileType('r'), help="toplev core csv file", metavar="csvfile")
ap.add_argument('--program', type=argparse.FileType('r'), help="toplev program csv file", metavar="csvfile")
ap.add_argument('--thread', type=argparse.FileType('r'), help="toplev thread csv file", metavar="csvfile")
ap.add_argument('--add', nargs=2, help="toplev thread generic csv file. Specify csvfile and sheet name as two arguments",
            metavar="name", action="append")
ap.add_argument('--valcsv', type=argparse.FileType('r'), help="toplev valcsv input file", metavar="csvfile")
ap.add_argument('--perf', type=argparse.FileType('r'), help="toplev perf values csv file")
ap.add_argument('--cpuinfo', type=argparse.FileType('r'), help="cpuinfo file")
ap.add_argument('--chart', help="add sheet with plots of normalized sheet. argument is normalied sheet name",
                action="append")
ap.add_argument('--no-summary', help='Do not generate summary charts', action='store_true')
args = ap.parse_args()

workbook = xlsxwriter.Workbook(args.xlsxfile, {'constant_memory': True})
bold = workbook.add_format({'bold': True})
valueformat = workbook.add_format({'num_format': '###,###,###,###,##0.0'})
valueformat_bold = workbook.add_format({'num_format': '###,###,###,###,##0.0',
    'bold': True})
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
headers = dict()

def get_worksheet(name):
    if name in worksheets:
        return worksheets[name]
    worksheet = workbook.add_worksheet(name)
    worksheets[name] = worksheet
    rows[name] = 1
    return worksheet

def to_float(n):
    if re.match(r'-?[,.0-9]+$', n):
        n = float(n)
    return n

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
            title = collections.OrderedDict()
            for i, k in enumerate(c):
                title[k] = i
            titlerow = c
            headers[name] = title
        if row < 10:
            set_columns(worksheet, c, lengths)
        if not summary and len(c) > 0 and c[0] == "SUMMARY":
            if args.no_summary:
                continue
            rows[name] = row
            sname = name + " summary"
            worksheet = get_worksheet(sname)
            set_columns(worksheet, c, lengths)
            worksheet.write_row(0, 0, titlerow)
            headers[sname] = titlerow
            row = rows[sname]
            summary = True
        elif summary and len(c) > 0 and c[0] != "SUMMARY" and c[0][0] != "#":
            worksheet = get_worksheet(name)
            summary = False
            rows[sname] = row
            row = rows[name]
        c = list(map(to_float, c))
        worksheet.write_row(row, 0, c)
        isbn = False
        if "Bottleneck" in title:
            bn = title["Bottleneck"]
            if len(c) > bn and c[bn] == "<==":
                worksheet.write(row, title["Area"], c[title["Area"]], bold)
                worksheet.write(row, title["Value"], c[title["Value"]], bold)
                if "CPUs" in title:
                    worksheet.write(row, title["CPUs"], c[title["CPUs"]], bold)
                isbn = True
                worksheet.write(row, bn, c[bn], bold)
        if "Value" in title and len(c) > title["Value"] and isinstance(c[title["Value"]], float):
            worksheet.write_number(row, title["Value"], c[title["Value"]],
                                   valueformat_bold if isbn else valueformat)
        elif "0" in title:
            num = 0
            while num in title:
                col = title["%d" % num]
                if len(c) > col and re.match(r'[0-9]+', c[col]):
                    worksheet.write_number(row, col, float(c[col]), valueformat)
                num += 1
        row += 1
    return version

ROW_SCALE = 18
MIN_ROWS = 15
GRAPH_ROWS = 15

def gen_chart(source):
    if source not in headers:
        print("source %s for chart not found" % source, file=sys.stderr)
        return

    worksheet = get_worksheet(source + " chart")
    charts = collections.OrderedDict()

    for n, ind in headers[source].items():
        if n == "Timestamp":
            continue
        ns = n.split()
        if len(ns) > 1:
            prefix = ns[0] + " "
            nn = " ".join(ns[1:])
        else:
            prefix = ''
            nn = n

        if gen_level.is_metric(nn):
            chart = workbook.add_chart({'type': 'line'})
            charts[n] = chart
            chart.set_title({'name': n})
        else:
            key = n[:n.rindex('.')] if '.' in n else prefix
            if key not in charts:
                charts[key] = workbook.add_chart(
                        {'type': 'column', 'subtype': 'percent_stacked' })
            chart = charts[key]
            chart.set_title({
                'name': '%s Level %d %s' % (prefix, n.count('.') + 1,
                                            key[key.index(' '):] if ' ' in key else key) })
            chart.set_x_axis({'name': 'Timestamp'})
        chart.add_series({
            'name':        [source, 0, ind],
            'categories':  [source, 1, 0,   rows[source], 0],
            'values':      [source, 1, ind, rows[source], ind]
        })
        chart.set_size({'width': (rows[source] + MIN_ROWS ) * ROW_SCALE})
        chart.set_legend({
            'overlay': True,
            'layout': { 'x': 0.01, 'y': 0.01, 'width': 0.12, 'height': 0.12 },
            'fill': { 'none': True, 'transparency': True }
        })
    row = 1
    for j in charts.keys():
        worksheet.insert_chart('A%d' % row, charts[j])
        row += GRAPH_ROWS

version = None
if args.global_:
    version = create_sheet("global", args.global_, version=version)
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
if args.chart:
    for cname in args.chart:
        gen_chart(cname)
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
