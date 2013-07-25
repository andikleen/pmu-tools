# Copyright (c) 2013, Intel Corporation
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
# do some (not so) simple expression parsing, mainly to handle the
# with:... construct look up the sub events and convert them into a
# function call we also expand sub expressions (references to other
# events), but we need to recurse on () and for sub exprs
# this does not require handling full operator precedence
#
import re
import inspect

import ucevent
import ucmsg

class ParseError(Exception):
    def __init__(self, msg):
        self.msg = msg

def is_id(t):
    return re.match(r"[a-zA-Z][[\]:a-zA-Z0.9.]*", t)

def is_number(t):
    return re.match(r"(0x)?[0-9]+", t)

cpu_events = {
    "INST_RETIRED.ALL": "instructions"
}

def event_expr(v, n):
    return "EV('%s', '%s')" % (v, n)

def fix_token(t, box, user_mode):
    if ((t.find(".") >= 0 and re.match(r"[A-Z][0-9a-zA-Z_.]{5,}", t))
            or re.match(r"[A-Z]", t)
            or t.startswith("iMC")
            or t.startswith("R2PCIe")):
        if t in cpu_events:
            return event_expr(cpu_events[t], t)
        if t in ucevent.cpu_aux.alias_events:
            return event_expr(ucevent.cpu_aux.alias_events[t], t)
        if user_mode:
            m = re.match(r"([^.]+)\.", t)
            if m:
                box = m.group(1)
        name = t
        if not t.startswith(box + "."):
            name = box + "." + t
        ev = ucevent.lookup_event(name)
        if not ev:
            ev = ucevent.lookup_event(t)
        if ev:
            if "Equation" in ev:
                tl = tokenize(ev["Equation"], box)
                n = expr(tl)
                return n
            evl = ucevent.format_event(ev)
            n = event_expr(evl[0], name)
            if len(evl) > 1:
                n = n.replace("_0/", "_INDEX/")
            return n
    return t

# really poor man's tokenizer
def tokenize(eq, box, user_mode=False):
    eq = eq.replace(".{", " .{")
    eq = eq.replace("with:", "with: ")
    eq = eq.replace("(on Core)", "")
    eq = re.sub(r"([*={}(),/<>]|>=|==|<=)", r" \1 ", eq)
    eq = re.sub(r"\.([a-z])", r" . \1", eq) 
    eq = re.sub(r"([=<>])  \1", r"\1\1", eq)
    eq = re.sub(r"([<>])  =", r"\1=", eq)
    return map(lambda x: fix_token(x, box, user_mode), eq.split())

# expand event lists to multiple boxes after parsing
# this avoids having to pass this all around the parser
# we assume all are for the same box
def expand_events(s):
    m = re.search(r"uncore_([^/]+)_INDEX", s)
    if not m:
        return [s]
    l = []
    n = 0
    while ucevent.box_exists("%s_%d" % (m.group(1), n)):
        l.append(s.replace("_INDEX", "_%d" % (n)))
        n += 1
    if len(l) == 0:
        return [s]
    return l

def expect(tl, c):
    #print "expecting",c
    if not tl:
        raise ParseError("expected %s, got end" % (c))
    if tl[0] != c:
        raise ParseError("expected %s instead of %s: %s" % (c, tl[0], tl[:5]))
    return tl[1:]

def convert_qual(q, v):
    qual_alias = ucevent.cpu_aux.qual_alias
    if q in qual_alias:
        return (qual_alias[q], v)
    m = re.match(r"([A-Za-z0-9_]+)\[(\d+):(\d+)\]", q)
    if m:
        q = m.group(1)
        val = (int(v, 0) << int(m.group(3)))
        v = "%#x" % (val)
    if q in qual_alias:
        return (qual_alias[q], v)
    return (q, v)

def is_ev(l):
    return isinstance(l, basestring) and l.startswith("EV(")

def apply_expr(o, fl, vl):
    if is_list(o):
        return map(lambda x: apply_expr(x, fl, vl), o)
    if is_ev(o):
        for f, v in zip(fl, vl):
            nn, nv = convert_qual(f, v)
            # existing qualifier to or it to?
            m = re.search(r",%s=([^,/]+)" % (nn), o)
            if m:
                val = int(m.group(1), 0)
                val |= int(nv, 0)
                o = re.sub(r",(%s)=([^,/]+)", r"\1=%#x," % (val), o)
            else:
                add = ",%s=%s" % (nn, nv)
                o = o.replace("/'", add + "/'")
    return o

def has_ev(l):
    if is_list(l):
        for j in l:
            if has_ev(j):
                return True
    elif is_ev(l):
        return True
    return False

def apply_list(o, fl, vl):
    ucmsg.debug_msg("expr", "apply %s and %s to %s from %s" % 
                   (fl, vl, o, inspect.stack()[1][2:]))
    for j in fl:
        if is_list(j):
            for k in j:
                n = k.split('=')
                o = apply_expr(o, [n[0]], [n[1]])
    fl = filter(lambda x: not is_list(x), fl)
    if len(fl) != len(vl):
        print "MISMATCHED APPLY",fl,vl,o,inspect.stack()[1][2:]
        return o
    if not has_ev(o):
        evo = []
        for f, v in zip(fl, vl):
            if is_id(f):
                f = "." + f
            evo.append("%s%s=%s" % (o, f, v))
        return evo
    return apply_expr(o, fl, vl)

closener = { "{": "}", "(": ")" }

# a = NUMBER
# a
# NUMBER
# [...]           (???)
# a { list } 
def parse_term(tl):
    name = tl[0]
    if not (is_id(name) or is_number(name) or name[0] == '['):
        raise ParseError("expected identifier or number in list not %s: %s" %
                            (tl[0], tl[:5]))
    tl = tl[1:]
    if tl[0] == '=':
        tl = tl[1:]
        if not is_number(tl[0]):
            raise ParseError("expected number after =, not %s" % (tl[0]))
        return name, tl[0], tl[1:]
    if tl[0] == '{':
        fl, vl, tl = parse_list(tl[1:])
        tl = expect(tl, '}')
        if tl[0] == '=':
            tl = tl[1:]
            if tl[0] not in ('(', '{'):
                raise ParseError("expect ( or {, not %s" % (tl[:5]))
            opener = tl[0]
            vl, _, tl = parse_list(tl[1:])
            tl = expect(tl, closener[opener])
        name = apply_list(name, fl, vl)
    return name, None, tl

# term { , term } 
def parse_list(tl):
    ls = []
    nm = []
    while True:
        term, nmt, tl = parse_term(tl)
        ls.append(term)
        if nmt != None:
            nm.append(nmt)
        if tl[0] != ',':
            break
        tl = tl[1:]
    return ls, nm, tl


# '{' list '}'
# '{' list '}' = ( val_list)
# a = NUMBER
# a . '{' list '}' = ( val_list )
# a . x = NUMBER
def parse_with(tl, orig):
    #print "with",tl
    if tl[0] == '{':
        ls, nm, tl = parse_list(tl[1:])
        vl = []
        tl = expect(tl, '}')
        if tl and tl[0] == '=':
            tl = tl[1:]
            if tl[0] in ('(', '{'):
                opener = tl[0]
                nm, _, tl = parse_list(tl[1:])
                tl = expect(tl, closener[opener])
            else:
                raise ParseError("expected { or (, not %s" % (tl[:5]))
        orig = apply_list(orig, ls, nm)
        return orig, tl
    # id
    if is_id(tl[0]) or tl[0][0] == '[':
        idn = tl[0]
        tl = tl[1:]
        if tl[0] == '.':
            tl = tl[1:]
            # id . id
            if is_id(tl[0]):
                id2 = tl[0]
                tl = tl[1:]
                # id . id = NUMBER
                if tl[0] == '=':
                    tl = tl[1:]
                    if not is_number(tl[0]):
                        raise ParseError("expecting number after =, not %s" % (tl[:5]))
                    number = tl[0]
                    tl = tl[1:]
                else:
                    number = "1"
                orig = apply_list(orig, [idn + "." + id2], [number])
                return orig, tl
            # .{ list } = { list }
            tl = expect(tl, '{')
            ls, vl, tl = parse_list(tl)
            tl = expect(tl, '}')
            if tl[0] == '=':
                tl = tl[1:]
                if tl[0] == '(' or tl[0] == '{':
                    opener = tl[0]
                    vl, _, tl = parse_list(tl[1:])
                    tl = expect(tl, closener[opener])
            orig = apply_list(orig, ls, vl)
            return orig, tl
        tl = expect(tl, '=')
        num = tl[0]
        if not is_number(num):
            raise ParseError("expected number, not %s" % (num))
        orig = apply_list(orig, [idn], [num])
        return orig, tl[1:]
    elif tl[0] == '.':
        tl = tl[1:]
        if is_id(tl[0]):
            # id . a = NUMBER
            vl = [tl[0]]
            tl = tl[1:]
            if tl[0] == '=':
                tl = tl[1:]
                num = tl[0]
                if not is_number(num):
                    raise ParseError("Expected number, not %s" % (tl[:5]))
            else:
                num = 1
            vl = [num]
        else:
            tl = expect(tl, '{')
            fl, _, tl = parse_list(tl)
            tl = expect(tl, '}')
            tl = expect(tl, '=')
            tl = expect(tl, '(')
            vl, _, tl = parse_list(tl)
            tl = expect(tl, ')')
        orig = apply_list(orig, fl, vl)
        return orig, tl
    raise ParseError("parse error in with clause at %s (%s)" % (tl[0], tl))
    return [], []

operators = ("+", "-", "*", "/", ">", "<", ">=", "<=", "==", "<<", ">>")

def expr_term(tl):
    if tl[0] == '(':
        out, tl = expr(tl[1:])
        if isinstance(out, list):
            out = [out]
        tl = expect(tl, ')')
    else:
        out = [tl[0]]
        tl = tl[1:]        
        if tl and tl[0] == '{':
            fl, vl, tl = parse_list(tl[1:])
            tl = expect(tl, '}')
            out = apply_list(out, fl, vl)
    if not tl:
        return out, tl
    if tl and tl[0] == 'with:':
        out, tl = parse_with(tl[1:], out)
    return out, tl

def expr(tl):
    out = []
    while True:
        no, tl = expr_term(tl)
        out += no
        if tl and tl[0] in operators:
            out.append(tl[0])
            tl = tl[1:]
        else:
            break
    return out, tl

def is_list(e):
    return isinstance(e, list) or isinstance(e, tuple)

def expr_flat(e):
    if not is_list(e):
        return e
    l = []
    for i in e:
        s = expr_flat(i)
        if is_list(s):
            if len(s) > 0:
                l.append('(')
                l += s
                l.append(')')
        else:
            l.append(s)
    return l

def apply_one_user_qual(x, qual):
    if not x.startswith("EV("):
        return x
    if any(map(lambda r: re.search(r, x), ucevent.cpu_aux.clockticks)):
        return x
    return x.replace("/'", "," + qual + "/'")

def apply_user_qual(e, qual):
    return map(lambda x: apply_one_user_qual(x, qual), e)

def parse(s, box, quiet=False, user_mode=False, qual=None):
    try:
        if not quiet:
            print "Expression", s
        tl = tokenize(s, box, user_mode)
        ucmsg.debug_msg("tokenize", tl)
        e, tl = expr(tl)
        if len(tl) > 0:
            raise ParseError("unexpected token %s at end" % (tl[0]))
        ucmsg.debug_msg("expr", e)
        eflat = expr_flat(e)
        if qual:
            eflat = apply_user_qual(eflat, qual)
        res = " ".join(eflat)
        res = expand_events(res)
        ucmsg.debug_msg("expanded", tl)
        return res
    except ParseError as p:
        print "PARSE-ERROR", p.msg
        return []

if __name__ == '__main__':
    assert is_id("x")
    print parse("a + b + c", "foo")
    print parse("a with:x=1 + (b with:.{o}=(1) + c with:{edge}) with:{x=1,y=2} + d", "foo")

