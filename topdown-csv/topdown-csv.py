#!/usr/bin/env python3
# Copyright (c) 2012-2024, Intel Corporation
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
# convert topdown spreadsheet to python code
# EVENTMAP=eventfile.json topdown-csv.py spreadsheet.csv > module.py CPU-acronym "long cpu name"
#
# somewhat of a mess. should really use a real parser.
#
# TOFIX:
# use count domain number for sanity checks
# special case leaking events with option? (l3 bound to memory bound)
# figure out Cycles_False_Sharing_Client on HSX
# uncore handle arb events directly
#

from __future__ import print_function
import sys
import csv
import re
import textwrap
import argparse
import json
import itertools
from copy import copy
from string import Template
T = Template
sys.path.append("../pmu-tools")
sys.path.append("..")
import ocperf

ap = argparse.ArgumentParser(usage='Convert topdown spreadsheet to python code. Specify EVENTMAP=eventfile.json. Spreadsheet must be in CSV format.')
ap.add_argument('spreadsheet', type=argparse.FileType('r'))
ap.add_argument('product_match')
ap.add_argument('long_cpu_name')
ap.add_argument('--product')
ap.add_argument('--hybrid', action='store_true')
ap.add_argument('--memory', default=0)
ap.add_argument('--extra-match')
ap.add_argument('--count-domain', default='Count Domain')
ap.add_argument('-v', '--verbose', action='store_true')
ap.add_argument('-j', '--json', type=argparse.FileType('w'), help="Output formulas and events in flat JSON format")
ap.add_argument('--eventcsv', type=argparse.FileType('r'), help="Use CSV to convert events instead of JSON")
ap.add_argument('--nosmt', action='store_true', help="Set default for EBS mode in model")
ap.add_argument('--ignore-missing', action='store_true', help="Ignore missing events")
args = ap.parse_args()

if args.product:
    args.product_match = args.product

emap = None
if not args.eventcsv:
    emap = ocperf.find_emap()
    if not emap:
        sys.exit("Cannot find CPU map")

# From "for tools developers" in TMA spreadsheet

server_products = "JKT;IVT;HSX;BDX;SKX;CLX;CPX;ICX;SPR/EMR;SPR-HBM;EMR;GNR".split(";")
client_products = "SNB;IVB;HSW;BDW;SKL;KBL;KBLR;CFL;CNL;ICL;RKL;RKL;TGL;ADL;MTL;LNL".split(";")

server_products.reverse()
client_products.reverse()

server_client = {
    "SPR": "ADL",
    "ICX": "ICL",
    "CPX": "KBLR",
    "CLX": "KBLR",
    "SKX": "SKL",
    "BDX": "BDW",
    "HSX": "HSW",
    "IVT": "IVB",
    "JKT": "SNB",
    "EMR": "ADL",
    "GNR": "MTL",
    "SPR-HBM": "ADL",
    "SPR/EMR": "ADL",
}

clients_with_server = set(server_client.values())

ratio_column = { "TNT": ("TNT", ), "CMT": ("CMT",), args.product_match: (args.product_match, ) }
for i, name in enumerate(client_products):
    ratio_column[name] = client_products[i:]
for i, name in enumerate(server_products):
    ratio_column[name] = []
    for server in server_products[i:]:
        client = server_client[server]
        seen = set()
        ratio_column[name] += [server, client]
        j = client_products.index(client) + 1
        while j < len(client_products) and client_products[j] not in clients_with_server:
            if client_products[j] not in seen:
                ratio_column[name].append(client_products[j])
                seen.add(client_products[j])
            j += 1

aliases = {
    "SPR": "SPR/EMR",
    "CFL": "KBLR/CFL/CML",
    "KBLR": "KBLR/CFL/CML",
    "ADL": "ADL/RPL",
    "SKL": "SKL/KBL",
    "KBL": "SKL/KBL",
    "JKT": "JKT/SNB-EP",
    "EMR": "SPR/EMR",
    #"SPR-HBM": "SPR",
    "LNL": "LNL/ARL",
}

if args.product_match in aliases and aliases[args.product_match] in ratio_column:
    args.product_match = aliases[args.product_match]

#import pprint
#pprint.pprint(ratio_column, stream=sys.stderr)
print("Used columns", " ".join(ratio_column[args.product_match]), file=sys.stderr)

match_products = set(ratio_column.keys())

topdown_use_fixed = False

aux_skip = set(["SMT_on", "Base_Frequency", "EBS_Mode", "PERF_METRICS_MSR"])

#fixes = {
#}

event_replace = (
)

event_fixes = (
    ("_UOPS_", "_UOP_"),
    ("TOPDOWN.SLOTS:perf_metrics", "slots"),
)

special_events = {
    "DurationTimeInMiliSeconds": ("interval-ms", ),
    "DurationTimeInMilliSeconds": ("interval-ms", ),
    "DurationTimeInSeconds": ("interval-s", ),
    "TSC": ("msr/tsc/", ),
}

extra_desc = {
}

csv_fixes = {
}

env_var = {
    "NUM_CORES": "num_cores",
    "NUM_THREADS": "num_threads",
    "Base_Frequency": "base_frequency",
    "SMT_on": "smt_enabled",
    "PERF_METRICS_MSR": "topdown_use_fixed",
    "EBS_Mode": "ebs_mode",
    "NUM_SOCKETS": "num_sockets",
}

def read_eventcsv(e):
    if not args.eventcsv:
        return {}
    allevents = dict()
    c = csv.DictReader(args.eventcsv)
    for j in c:
        if "SimEvent" in j:
            allevents[j["Name"]] = j["SimEvent"]
        if "CohoStat" in j:
            ev = j["CohoStat"].replace("p0.c0.t0.", "")
            si = j['SiliconEventName']
            allevents[si] = ev
            allevents[j["EventName"]] = ev
            allevents["%s.%s" % (j["MainEventName"], j["SubEventName"])] = ev
            if si.endswith("_P"):
                allevents[si[:-2]] = ev
            if si in csv_fixes:
                allevents[csv_fixes[si]] = ev
    return allevents

allevents = read_eventcsv(args.eventcsv)

class Rule:
    pass

class BadEvent(Exception):
    pass

def findevent(ev):
    if emap:
        return emap.getevent(ev) is not None
    if args.eventcsv:
        def munge(e):
            if e == "":
                return None
            return e

        if ev in allevents:
            return munge(allevents[ev])
        ev = ev.lower()
        if ev in allevents:
            return munge(allevents[ev])
        return None
    sys.exit("No events")

def find_replacement(t, what):
    if findevent(t + "_0"):
        print("replaced %s event %s with %s" % (what, t, t + "_0"), file=sys.stderr)
        return t + "_0"
    if "OCR" in t:
        nn = t.replace("OCR", "OFFCORE_RESPONSE")
    else:
        nn = t.replace("OFFCORE_RESPONSE", "OCR")
    if findevent(nn):
        print("replaced %s event %s with %s" % (what, t, nn), file=sys.stderr)
        return nn
    for e, r in event_fixes:
        nt = t.replace(e, r)
        if not args.hybrid:
            nt = nt.replace("cpu_core", "cpu")
        if nt.startswith("topdown-") or nt == "slots" or nt.startswith("cpu"):
            return nt
        if findevent(nt):
            print("replaced %s event %s with %s" % (what, t, nt), file=sys.stderr)
            return nt
    return None

def verify_event(t, what):
    #for e, r in event_replace:
    #    t = t.replace(e, r)
    extra = ""
    m = re.match(r'(.*?)([:/].*)', t)
    if m:
        t = m.group(1)
        extra = m.group(2)
    e = findevent(t)
    if not e:
        if t.startswith("UNC"):
            print("not found", t, file=sys.stderr)
        if t.endswith("_ANY"):
            return verify_event(t.replace("_ANY", ":amt1"), what)
        nt = find_replacement(t, what)
        if not nt:
            print("WARNING ",product_match,extra,"cannot find %s event %s" % (what, t), file=sys.stderr)
            if args.ignore_missing:
                return "0"
            raise BadEvent()
        t = nt
    if isinstance(e, str):
        t = e
    if extra:
        if extra == "sup" or extra == "SUP":
            extra = "k"
        if extra.startswith("/"):
            extra = ":" + extra[1:]
        t = t + extra
    return t

groups = []
consts = []
aux    = []
info   = []
names = {}
deleted = []
aux_names = set()
not_aux_areas = set()
runtime_ids = set(("#SMT_on", "#SMT_On", "#EBS_Mode", "#PERF_METRICS_MSR",))

parent_stack = []

product_match = ""
if args.product_match:
    product_match = args.product_match
    print("PRODUCT",product_match, file=sys.stderr)
long_name = product_match
if args.long_cpu_name:
    long_name = args.long_cpu_name

skipped = 0
skipped_event = 0

def supported_event(ev):
    try:
        return verify_event(ev, "locate")
    except BadEvent:
        return None


OP, ID, EVENT, MATCH, END = list(range(5))
toknames = ("op", "id", "event", "match", "end")

class ParseError(BaseException):
    pass

def parse_error(x, l=""):
    print("PARSE-ERROR", x, "got %s %s" % (toknames[l[0]], l[1]) if l else "", file=sys.stderr)
    raise ParseError()

def is_op(tok, m):
    return tok and tok[0] == OP and tok[1] == m

def gettok(s):
    while len(s) > 0:
        if s[0] == " ":
            s = s[1:]
            continue
        if s[0] in "?:;/":
            tok = s[0]
            s = s[1:]
            yield (OP, tok)
            continue
        if s.startswith("N/A") or s.startswith("#NA"):
            s = s[3:]
            yield (EVENT, "N/A")
            continue
        if s.startswith("SPR-HBM"):
            s = s[len("SPR-HBM"):]
            yield (MATCH, "SPR-HBM")
            continue
        m = re.match(r'".*?"', s)
        if m:
            s = s[len(m.group(0)):]
            yield (EVENT, m.group(0))
        m = re.match(r'[A-Z._][a-zA-Z0-9_.:=]*', s)
        if m:
            s = s[len(m.group(0)):]
            if m.group(0) in match_products or (m.group(0) in aliases and aliases[m.group(0)] in match_products):
                yield (MATCH, m.group(0))
            else:
                yield (EVENT, m.group(0))
            continue
        parse_error("lexing error " + s)
    yield (END, )

# locate = eventlist | match "?" eventlist ":" locate
# eventlist = event { ";" event }
def interpret_loc(l, product_match):
    if l.endswith("if #flavor > 'full_toplev' else #NA"):
        return ["#NA"]
    try:
        lexer = gettok(l)
        tok = next(lexer)
        if tok[0] == END:
            return []
        l = parse_expr(lexer, tok, product_match)
    except ParseError as e:
        import traceback
        print(e, file=sys.stderr)
        print(l, file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return []
    return l[0]

def parse_eventlist(lexer, tok):
    if tok[0] != EVENT:
        parse_error("expect event", tok)
    l = [tok[1]]
    tok = next(lexer)
    while is_op(tok, ";"):
        tok = next(lexer)
        if tok[0] != EVENT:
            parse_error("expect event", tok)
        l.append(tok[1])
        tok = next(lexer)
    return l, tok

def check_product(products):
    # XXX do inheritance here for ICL?
    return product_match in products

def parse_expr(lexer, first, product_match):
    if first[0] == MATCH:
        products = [first[1]]
        tok = next(lexer)
        while is_op(tok, "/"):
            tok = next(lexer)
            if tok[0] != MATCH:
                parse_error("expect match", tok)
            products.append(tok[1])
            tok = next(lexer)
        if not is_op(tok, "?"):
            parse_error("expect ?", tok)
        tok = next(lexer)
        if check_product(products):
            return parse_eventlist(lexer, tok)
        else:
            _, tok = parse_eventlist(lexer, tok)
            if not is_op(tok, ":"):
                parse_error("expect :", tok)
            tok = next(lexer)
            return parse_expr(lexer, tok, product_match)
    elif first[0] == EVENT:
        return parse_eventlist(lexer, first)
    else:
        parse_error("parse error before " + repr(first), first)

def compile_locate(locate):
    locate = interpret_loc(locate, product_match)
    locate = [x for x in locate if x not in ("", "N/A", "#NA")]
    locate = [x.replace("_PS", ":pp").strip() for x in locate]
    locate = list(map(supported_event, locate))
    locate = [x for x in locate if x]
    return locate


# ([SNB+] ...; [HSW+] ...) -> (...) with right product
def fix_desc(desc):
    def change(m):
        if not re.search(r'\[[A-Z]{3,3}\+?\]', m.group(0)):
            return m.group(0)
        desc = ""
        matchlen = 1000
        allseq = []
        for j in m.group(0)[1:-1].split(";"):
            m2 = re.match(r"\s*\[([A-Z]{3,3}\+?)\](.*)", j)
            if m2 is None:
                desc = j
                continue
            seq = m2.group(1)
            allseq.append(seq)
            if seq.endswith("+"):
                seq = seq.replace("+", "")
                p = ratio_column[product_match]
                # pick the shortest distance
                if seq in p and p.index(seq) < matchlen:
                    desc = m2.group(2)
                    matchlen = p.index(seq)
            else:
                if seq not in ratio_column:
                    print("Unknown desc match", seq, file=sys.stderr)
                if seq == product_match:
                    desc = m2.group(2)
                    matchlen = 1
        return desc
    n = re.sub(r'\((.*?)\)', change, desc.replace("\n", " "))
    return n

fields = None
csvf = csv.reader(args.spreadsheet)
tdversion = ""
prevr = None
for row in csvf:
    row = ["" if x == "." else x for x in row]
    if row[1] == "Version":
        tdversion = row[2]
    if row[0] == "Key":
        fields = dict([x for x in zip([k.strip() for k in row], list(range(0, len(row))))])
        if args.verbose:
            print("fields", fields, file=sys.stderr)
        continue
    if len(row) < 8 or row[0] == "" or fields is None:
        if any([x == "" for x in row]):
            continue
        print("skipped", row, file=sys.stderr)
        skipped += 1
        continue
    def translate(x):
        if x in fields:
            return x
        if x in aliases:
            return aliases[x]
        return None
    def get(x):
        f = translate(x)
        if f is None:
            sys.exit("Cannot find %s in %s" % (x, row))
        return row[fields[f]]
    if get('Key') == "HW Info":
        skipped += 1
        continue
    # does not work because perf cannot handle THREAD vs THREAD_P event
    if get('Level1') == "MUX":
        print("Skipped MUX", file=sys.stderr)
        skipped += 1
        continue
    l = [None,"","","","","",""]
    r = Rule()
    r.type = get('Key').split(".")[0]
    r.fulltype = get('Key')
    for j in range(1,7):
        n = 'Level%d' % j
        if n in fields:
            l[j] = get(n).replace("/", "_")

    column = "?"
    for j in ratio_column[product_match]:
        if isinstance(j, list):
            for k in j:
                if k in fields:
                    j = k
                    break
            else:
                sys.exit("Cannot find column %s" % j)
        if j not in fields and j not in aliases:
            continue
        ratio = get(j)
        if ratio:
            column = j
            break
    if ratio == "":
        skipped_event += 1
        continue
    if ratio.strip() == "N/A" or ratio.strip() == "#NA":
        skipped_event += 1
        continue

    if 'Metric Description' in fields:
        r.desc = fix_desc(get('Metric Description'))
    else:
        r.desc = None
    r.thresh = get('Threshold')
    if 'public' in fields:
        r.public = get('public')
    else:
        r.public = ""
    if 'Metric Group' in fields:
        r.metricgroup = [x for x in get('Metric Group').strip().split(';') if x != '']
    else:
        r.metricgroup = []

    domain = get(args.count_domain)
    r.domain = domain
    if "Metric Max" in fields and get('Metric Max') != "":
        r.maxval = get('Metric Max').replace("#", "")
    else:
        r.maxval = "0"

    product = None
    if 'Product' in fields:
        product = get('Product')
    r.htoff = False
    if 'Comment' in fields:
        comment = get('Comment').split(";")
        r.htoff = "HToffHSW" in comment and product_match in ("HSW", "HSX")
    if 'Tuning Hint' in fields and len(get('Tuning Hint').strip()) > 0:
        r.desc += ". " + get('Tuning Hint')
    if 'Link' in fields and len(get('Link').strip()) > 0:
        r.desc += ". " + get('Link')

    if 'Locate-with' in fields:
        r.locate = compile_locate(get('Locate-with'))
    else:
        r.locate = None

    for level in range(1,7):
        if l[level] and not l[level].startswith("*"):
            break

    r.level = level
    r.pname = re.sub(r'\(.*\)', '', l[level]).strip()
    if r.pname == "":
        continue
    if r.pname == "SW info":
        r.pname = l[2]
    r.name = r.pname.replace(" ","").replace("+", "PLUS").replace("%", "PCT")
    if r.desc is None:
        r.desc = r.name.replace("_", " ")
    if re.match(r"[0-9]", r.name):
        r.name = "G" + r.name
    r.name = r.name.replace("#","")
    if r.name in names and len(parent_stack) > 0:
        r.name = parent_stack[-1] + r.name
    r.prevname = None
    if prevr:
        r.prevname = prevr.name
    prevr = r
    if r.name in extra_desc and r.desc.startswith("Reuse"):
        r.desc = extra_desc[r.name]

    if (r.name.startswith("IXP_") or r.name.startswith("MEM_IXP_")) and not args.memory:
        print("SKIPPED", r.name, file=sys.stderr)
        skipped_event += 1
        continue

    while parent_stack and names[parent_stack[-1]].level >= r.level:
        parent_stack.pop()
    if parent_stack:
        r.parent = parent_stack[-1]
    else:
        assert r.level == 1
        r.parent = None
    parent_stack.append(r.name)

    r.issue = None
    issue = r.thresh.split(";")
    r.overlap = False
    if len(issue) > 0:
        r.thresh = issue[0]
    if len(issue) > 1:
        issue = [x.strip() for x in issue[1:]]
        r.issue = set(issue)
        if "~overlap" in r.issue:
            r.overlap = True
            r.issue.discard("~overlap")
    r.rawratio = ratio
    r.ratio = ratio
    if "PERF_METRICS_MSR" in r.ratio:
        topdown_use_fixed = True
    if args.verbose:
        print(r.type,r.name,r.ratio,r.thresh,r.level, file=sys.stderr)
    if r.type == "Aux" and r.domain in ("Constant", "ExternalParameter"):
        r.type = "Constant"
        runtime_ids.add(r.name)
    names[r.name] = r
    if r.type == "Constant":
        consts.append(r)
    elif r.type == "Aux":
        if r.name not in aux_skip:
            aux.append(r)
    elif r.type in ("Info", "Model", "SW_Info", "Bottleneck"):
        info.append(r)
    elif r.type == "tool_Aux":
        continue
    else:
        groups.append(r)
    if r.type.endswith("_aux"):
        aux_names.add(r.name)
        # need to handle references first
        #not_aux_areas.add(r.type.replace("_aux", ""))

if args.json:
    def resolve(v):
        v = v.group(0)
        if v == "Base_Frequency":
            return v
        if v[1:] in names:
            return names[v[1:]].ratio
        if v in names:
            if " " in names[v].ratio:
                return "( " + names[v].ratio + " )"
            return names[v].ratio
        return v

    def flatform(r):
        for i in range(8):
            oldr = r
            r = re.sub(r'#?[a-zA-Z_0-9]+', resolve, r)
            if oldr == r:
                break
        return r

    def clean(v):
        return {x: v[x] for x in list(v.keys()) if v[x] and v[x] != "0"}

    def jout(r):
        return clean({
                "type": r.fulltype,
                "formula": flatform(r.rawratio),
                "oformula": r.rawratio,
                "name": r.name,
                "issue": list(r.issue) if r.issue else [],
                "overlap": r.overlap,
                "desc": r.desc,
                "parent": r.parent,
                "maxval": r.maxval,
                "metricgroup": r.metricgroup if r.metricgroup else [],
                "domain": r.domain,
                "level": r.level})

    l = info + groups + consts
    l = [x for x in l if x.rawratio != "#NA"]

    json.dump(list(map(jout, l)), args.json, indent=4, separators=(',', ': '), sort_keys=True)

def flatten(x):
    return itertools.chain(*x)

def find_children(parent):
    return set(flatten([set([j.name]) for j in groups if j.parent == parent]))

def change_token(t, other, level, nname=""):
    all_children = False
    max_children = False
    if t[:2] == "##":
        t = t[2:]
        all_children = True
        if t[:1] == "?":
            t = t[1:]
            max_children = True
    if t[:1] == "#":
        t = t[1:]

    if t in env_var:
        return env_var[t]

    if t in ("EV", "level"):
        return t

    if t == "Avg_run_time": # XXX
        return "0"

    if t == "NA":
        return "0" # or NaN? or throw?

    if t in special_events:
        e = 'EV("%s", 0)' % special_events[t][0]
        if len(special_events[t]) > 1:
            e += " / %g" % special_events[t][1]
        return e

    if t.startswith("EV("):
        return t

    if re.match(r'[A-Z\"]', t) and (t.find(".") >= 0 or t.startswith("UNC_")):
        m = re.match(r'"(.*)"', t)
        if m:
            t = m.group(1)
        t = t.replace("_PS", "")
        t = t.replace(":perf_metrics", "")
        t = verify_event(t, "node/metric %s" % nname)
        if t.startswith("PERF_METRICS") and not allevents:
            return '(EV("%s", %s) / EV("TOPDOWN.SLOTS", %s))' % (t, level, level)
        return 'EV("%s", %s)' % (t, level)

    if re.match(r"[A-Z_]+", t):
        if t not in names:
            if t.isupper() and args.ignore_missing:
                return "0"
            print("Warning: %s not found in names" % (t,), file=sys.stderr)
            raise BadEvent()
        if names[t].type == "Constant":
            return t

        def ref_node(t, other):
            # find all references to classes, updating other
            if names[t].type not in ("Info", "Aux", "Bottleneck"):
                other.add(t)
            _, o = compile_ratio(names[t].ratio, level, names[t].name)
            other |= o
            if names[t].type not in ("Aux", "Info", "Bottleneck"):
                return 'self.%s.compute(EV)' % (t,)
            return "%s(self, EV, %s)" % (t, level, )

        if all_children:
            children = find_children(t)
            s = "( " + " + ".join([ref_node(j,other) for j in children]) + " )"
            if max_children:
                return "max(" + ref_node(t,other) + "," + s + ")"
            return s

        return ref_node(t, other)
    return t

# handle lazy evaluation: list all events separately too
# very hackish
# XXX handles only single type of if
# for runtime_mode identifiers don't duplicate counters because they are fixed at runtime
def compile_extra(tokens, indent, levelstr, nname):
    tokens = compile_ratio_if(tokens)

    # doesn't handle mixed types of if for now
    if any([t in runtime_ids for t in tokens]):
        return ""

    if "if" in tokens:
        idx = tokens.index("if")
        if args.verbose:
            print("if", tokens[idx+1], tokens[idx+2], tokens[idx+1] not in runtime_ids, file=sys.stderr)
        if tokens[idx + 1] not in runtime_ids:
            try:
                events = set([x for x in tokens if change_token(x, set(), "0", "extra " + nname).count("EV") > 0 and "." in x])
            except BadEvent:
                return ""

            aux_names = set([x.name for x in aux])
            aux_calls = aux_names & set(tokens)
            return "".join([indent + 'EV("%s", %s)' % (x.replace("_PS",""), levelstr) for x in events] +
                           [indent + '%s(self, EV, %s)' % (x, levelstr) for x in aux_calls])
    return ""

def tokenize(s):
    t = re.sub(r"#*([\(\)\[\]*+-,]|if|else|/(?!Match))", r" \1 ", s).split()
    return t

def untokenize(tokens):
    r = " ".join(tokens)
    r = re.sub(r" ?([()]) ", r"\1", r)
    r = re.sub(r"\)([+-/,*] ?|if)", r") \1 ", r)
    r = r.replace("  ", " ")
    r = r.replace(")else", ") else")
    #r = re.sub(r"[^ ]([*/+-])", r" \1", r)
    #r = re.sub(r"([*/+-])[^ ]", r"\1 ", r)
    return r

def compile_min(tokens):
    i = 0
    while i < len(tokens):
        # min( CPU_CLK_UNHALTED.THREAD , x ) ->
        # EV ( lambda EV , level: min ( CPU_CLK_UNHALTED.THREAD , x ) , 0 )
        if tokens[i:i+4] == ['min', '(', 'CPU_CLK_UNHALTED.THREAD', ','] and tokens[5] == ')':
            tokens = tokens[:i] + "EV ( lambda EV , level : ".split(" ") + tokens[i:i+5] + [")", ",", "level"] + tokens[i+5:]
            i += 7
        i += 1
    return tokens

def compile_pebs(tokens):
    event = "missing"
    #if "$PEBS" in untokenize(tokens) and "$PEBS" not in tokens:
    #    print >>sys.stderr, "compile_pebs tokens", tokens
    for j in range(len(tokens)):
        if "." in tokens[j]:
            event = tokens[j]
        if tokens[j] == "$PEBS":
            ev = verify_event(event, "timed pebs event")
            tokens[j] = 'EV("%s", 999)' % ev
    return tokens

# [ "abc" "cdf" ] -> [ "abc", "cdf" ]
def compile_list(tokens):
    listflag = [False]
    def remap(t):
        if t == '[':
            listflag[0] = True
            return t
        elif t == ']':
            listflag[0] = False
        if listflag[0]:
            return t + ","
        return t
    tokens = [remap(t) for t in tokens]
    return tokenize(untokenize(tokens))

def compile_ratio_if(tokens):
    # handle #PMM_App_Direct in [...] if. The expression needs to be split because the events are not in older CPUs.
    # these expressions can only be outter expessions, nesting is not supported
    start = 0
    while "if" in tokens[start:]:
        ifind = tokens.index("if", start)
        if tokens[ifind+1] == "#PMM_App_direct":
            if tokens[ifind+2] != "else":
                print("ERROR expected else in", tokens, file=sys.stderr)
            if args.memory:
                tokens = tokens[:ifind]
            else:
                tokens = tokens[ifind+3:]
            break
        start = ifind + 1
    return tokens

def compile_na_if(tokens, prevname):
    # handle #NA if ...
    # which means the previous node in the level is used for the #NA (for HBM / DRAM)
    if len(tokens) > 2 and tokens[0] == "#NA" and tokens[1] == "if":
        tokens[0] = prevname
    return tokens

def compile_ratio(r, level, nname, prevname="#NA"):
    other = set()
    tokens = tokenize(r)
    tokens = compile_list(tokens)
    tokens = compile_ratio_if(tokens)
    tokens = compile_na_if(tokens, prevname)
    tokens = compile_min(tokens)
    tokens = compile_pebs(tokens)
    tokens = [change_token(t, other, level, nname) for t in tokens]
    r = untokenize(tokens)
    return r, other

def compile_thresh(t, other, level, fallback):
    if t == "":
        return fallback
    t = t.strip()
    m = re.match(r"\((.*)\)$", t)
    if m and m.group(1).find("(") < 0:
        t = m.group(1)
    #t = t.replace("(>", "(self.val >")
    t = t.replace("& P", "& self.parent.thresh")
    # dont want lazy evaluation
    t = t.replace("&", "and")
    t = t.replace("|", "or")
    t = t.replace("#", "")
    if t[0] in '<>' or (t[0] == '(' and t[1] in '<>'):
        m = re.match(r"(\(?)([<>]) ?([0-9.]+)(.*)", t)
        if m is not None:
            t = "%s(self.val %s %s)%s" % (m.group(1), m.group(2), m.group(3), m.group(4))
    if t[:1] == "<":
        t = "self.val " + t
    tokens = re.sub(r"([()])", r" \1 ", t).split()
    for j in tokens:
        if j in names:
            if names[j].type not in ("Aux", "Constant", "Info", "tool_Aux", "Bottleneck"):
                t = t.replace(j, "self.%s.thresh" % (j))
                other.add(j)
            elif names[j].type in ("Aux", "Info", "Bottleneck"):
                t = t.replace(j, j + "(self, EV, %s)" % (level,))
        if j in deleted:
            raise BadEvent()
    return t

def compile_desc(d):
    if d.startswith("Reuse"):
        return ""
    d = fix_desc(d)
    d = d.replace('"', r'\"')
    d = re.sub(r"#.*","", d)
    #d = re.sub(r"\..*", ".", d)
    d = d.replace("\n", " ")
    d = "\n".join(textwrap.wrap(d, 60))
    #d = re.sub(r"Tip:.*", "", d)
    return '""\n' + d + '""'

def compile_maxval(m):
    return re.sub(r"([a-zA-Z_][a-zA-Z0-9_]*)", lambda m: m.group(1) + "(0,0,0)" if m.group(1) not in [x.name for x in consts] else m.group(1), m)

def title(p):
    print("\n# " + p + "\n")

def kill(l, r, parents):
    if r.name not in names:
        return
    print("WARNING: removed %s (ratio %s)" % (r.name, r.ratio), file=sys.stderr)
    del l[l.index(r)]
    del names[r.name]
    deleted.append(r.name)
    if parents:
        for j in copy(l):
            if j.parent == r.name:
                kill(l, j, True)

print(T("""\
# -*- coding: latin-1 -*-
#
# auto generated TopDown/TMA $tdversion description for $long_name
# Please see http://ark.intel.com for more details on these CPUs.
#
# References:
# http://bit.ly/tma-ispass14
# http://halobates.de/blog/p/262
# https://sites.google.com/site/analysismethods/yasin-pubs
# https://download.01.org/perfmon/
# https://github.com/andikleen/pmu-tools/wiki/toplev-manual
#

# Helpers

print_error = lambda msg: False$SMT
version = "$tdversion"
base_frequency = -1.0
Memory = $memory
Average_Frequency = 0.0
num_cores = 1
num_threads = 1
num_sockets = 1
$topdown$aux

def handle_error(obj, msg):
    print_error(msg)
    obj.errcount += 1
    obj.val = 0
    obj.thresh = False

def handle_error_metric(obj, msg):
    print_error(msg)
    obj.errcount += 1
    obj.val = 0

""").substitute(long_name=long_name, tdversion=tdversion, memory=args.memory, topdown="topdown_use_fixed = False" if topdown_use_fixed else "",
    SMT="""
smt_enabled = False
ebs_mode = False""" if not args.nosmt else "",
    aux="use_aux = False" if aux_names else ""))

title("Constants")
for r in consts:
    def fix_constant(s):
        s = s.replace("SMT_on", "smt_enabled")
        s = s.replace("PERF_METRICS_MSR", "topdown_use_fixed")
        s = s.replace("#", "")
        if re.match(r'^[A-Z]', s):
            return '"' + s + '"'
        return s

    print("%s = %s" % (r.name, fix_constant(r.ratio)))

title("Aux. formulas")

# prune rules with missing events
def prune_rules(l):
    while True:
        changed = False
        for r in copy(l):
            if r.name in deleted:
                continue
            try:
                ratio, other = compile_ratio(r.ratio, "level", r.name, r.prevname)
            except BadEvent:
                kill(l, r, False)
                changed = True
        if not changed:
            break

# remove unreferenced aux nodes
def remove_unref():
    ref = set()
    for r in aux + info + groups + consts:
        ref.update(tokenize(r.ratio))
        ref.update(tokenize(r.thresh))
        if r.maxval:
            ref.update(tokenize(r.maxval))

    for r in copy(aux):
        # Keep _Width constants for external tools
        if r.name not in ref and "#" + r.name not in ref and not r.name.endswith("_Width"):
            print("Removed unreferenced", r.name, file=sys.stderr)
            aux.remove(r)

prune_rules(aux)
prune_rules(info)
remove_unref()

for r in aux + info:
    extra = compile_extra(tokenize(r.ratio), "\n    ", "level", r.name)
    ratio, other = compile_ratio(r.ratio, "level", r.name, r.prevname)
    print()
    if r.desc:
        print("# " + fix_desc(r.desc))
    print("def %s(self, EV, level):%s" % (r.name, extra))
    if r.thresh:
        thresh = compile_thresh(r.thresh, other, str(r.level), "True")
        print("    val = %s" % ratio)
        thresh = thresh.replace("self.val", "val")
        if r.type == "Aux":
            ratio = thresh
        elif r.type in ("Info", "Bottleneck"):
            print("    self.thresh = %s" % thresh)
        print("    return val")
    else:
        print("    return %s" % (ratio,))

title("Event groups")

# prune rules with missing events
while True:
    changed = False
    for r in copy(groups):
        if r.name in deleted:
            continue
        try:
            _, other = compile_ratio(r.ratio, str(r.level), r.name, r.prevname)
            compile_thresh(r.thresh, other, str(r.level), "self.val > 0.0 and self.parent.thresh")
        except BadEvent:
            kill(groups, r, True)
            changed = True
    if not changed:
        break

for r in groups:
    extra = compile_extra(tokenize(r.ratio), "\n" + " " * 12, "%d" % r.level, r.name)
    ratio, r.other = compile_ratio(r.ratio, str(r.level), r.name, r.prevname)
    thresh = compile_thresh(r.thresh, r.other, str(r.level), "self.val > 0.0 and self.parent.thresh")
    print(T("""
class $name:
    name = "$pname"
    domain = "$domain"
    area = "$type"
    level = $level
    htoff = $htoff
    sample = $sample
    errcount = 0
    sibling = None
    metricgroup = frozenset($metricgroup)
    maxval = $maxval
    def compute(self, EV):
        try:
            self.val = $ratio$extra
            self.thresh = $thresh
        except ZeroDivisionError:
            handle_error(self, "$name zero division")
        return self.val
    desc = "$desc"
""").substitute(r.__dict__,
                desc=compile_desc(r.desc), ratio=ratio, thresh=thresh,
                extra=extra, sample=r.locate, server=r.public.find("pub") >= 0,
                metricgroup=r.metricgroup,
                maxval=compile_maxval(r.maxval) if r.maxval and r.maxval != "0" else "None"))

for r in info:
    try:
        ratio, r.other = compile_ratio(r.ratio, str(r.level), r.name, r.prevname)
    except BadEvent:
        continue
    thresh = compile_thresh(r.thresh, r.other, str(r.level), "True")
    print(T("""
class Metric_$name:
    name = "$name"
    domain = "$domain"
    maxval = $maxval
    errcount = 0
    area = "$fulltype"
    metricgroup = frozenset($metricgroup)
    sibling = None

    def compute(self, EV):
        try:
            self.val = $name(self, EV, 0)
            self.thresh = $thresh
        except ZeroDivisionError:
            handle_error_metric(self, "$name zero division")
    desc = "$desc"
""").substitute(r.__dict__,
            maxval=compile_maxval(r.maxval) if r.maxval and r.maxval != "0" else "0",
            name=r.name, desc=compile_desc(r.desc), server=r.public.find("puc") >= 0,
            metricgroup=r.metricgroup, thresh=thresh))

changed = True
while changed:
    changed = False
    for r in groups:
        if r.name in aux_names:
            continue
        for o in r.other:
            if o in aux_names:
                aux_names.remove(o)
                changed = True

title("Schedule")
print(T("""

class Setup:
    def __init__(self, r):
        o = dict()""").substitute(tdversion=tdversion))

def gen_aux_guard(r, r2=None):
    if r.name in aux_names or (r2 and r2.name in aux_names):
        sys.stdout.write("        if use_aux:\n    ")
    if r.type in not_aux_areas or (r2 and r2.type in not_aux_areas):
        sys.stdout.write("        if not use_aux:\n    ")

for r in groups:
    gen_aux_guard(r)
    print((T("""        n = $name() ; r.run(n) ; o["$name"] = n""").
                substitute(r.__dict__)))
print()
print("        # parents")
print()
for r in groups:
    if r.parent:
        gen_aux_guard(r, names[r.parent])
        print(T("""        o["$name"].parent = o["$pname"]""").substitute(
                r.__dict__, pname=names[r.parent].name))

print()
print("        # user visible metrics")
print()
for r in info:
    gen_aux_guard(r)
    print(T("""        n = Metric_$rname() ; r.metric(n) ; o["$rname"] = n""").substitute(
            rname=r.name, rdesc=compile_desc(r.desc)))


print()
print("        # references between groups")
print()
for r in groups + info:
    if 'other' not in r.__dict__:
        continue
    for on in r.other:
        o = names[on]
        gen_aux_guard(r)
        print(T("""        o["$rname"].$oname = o["$oname"]""").substitute(
                rname=r.name, oname=o.name))

print()
print("        # siblings cross-tree")
print()
for r in groups + info:
    if r.issue:
        match = ['o["%s"]' % ox.name for ox in groups if r.issue and ox.issue and r.issue & ox.issue and ox.name != r.name]
        if len(match) > 0:
            gen_aux_guard(r)
            print(T("""        o["$rname"].sibling = $match""").substitute(rname=r.name, match="(" + ", ".join(match) + ",)"))
        if r.overlap:
            gen_aux_guard(r)
            print(T("""        o["$rname"].overlap = True""").substitute(rname=r.name))

        #if r.issue in issues:
        #    o = filter(lambda x: x != r, issues[r.issue])
        #    if len(o) > 0:
        #        o = o[0]
        #    else:
        #        print >>sys.stderr, "issue", r.issue, "not found for", r.name
        #        continue
        #else:
        #    print >>sys.stderr, "issue", r.issue, "not found"
        #    continue
        #if o.name in names:
        #    if o.type not in ("Aux", "Info"):
        #        print T("""    o["$rname"].sibling = o["$oname"]""").substitute(
        #               rname=r.name, oname=o.name)
        #else:
        #    continue
        #   #print T("""        o["$rname"].sibling = None""").substitute(rname=r.name)
    else:
        continue
        #print T("""        o["$rname"].sibling = None""").substitute(rname=r.name)

print("SKIPPED %d lines, %d events" % (skipped, skipped_event), file=sys.stderr)
