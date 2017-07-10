#!/usr/bin/env python
# resolve ELF and DWARF symbol tables using elftools
#
# Copyright (c) 2013-2014, Intel Corporation
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

from elftools.common.py3compat import maxint, bytes2str
from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection
import elftools.common.exceptions
import util
import kernel

# global caches
open_files = dict()
resolved = dict()
symtables = dict()
lines = dict()

def build_line_table(dwarfinfo):
    lines = []
    for CU in dwarfinfo.iter_CUs():
        lp = dwarfinfo.line_program_for_CU(CU)
        prevstate = None
        for entry in lp.get_entries():
            if entry.state is None or entry.state.end_sequence:
                continue
            if prevstate:
                lines.append((prevstate.address, 
                              entry.state.address,
                              lp['file_entry'][prevstate.file - 1].name,
                              prevstate.line))
            prevstate = entry.state
    lines.sort()
    return lines
                              
def build_symtab(elffile):
    syms = []
    for section in elffile.iter_sections():
        if isinstance(section, SymbolTableSection):
            for nsym, sym in enumerate(section.iter_symbols()):
                name = bytes2str(sym.name)
                if not name:
                    continue
                if sym.entry.st_info.type != 'STT_FUNC':
                    continue
                end = sym['st_value'] + sym['st_size']
                syms.append((sym['st_value'], end, 
                             bytes2str(sym.name)))
    syms.sort()
    return syms

reported = set()

def find_elf_file(fn):
    if fn.startswith("//"):
        return None
    if fn in open_files:
        elffile = open_files[fn]
    else:
        try:
            f = open(fn, 'rb')
            elffile = ELFFile(f)
            open_files[fn] = elffile
        except (IOError, elftools.common.exceptions.ELFError):
            if fn not in reported:
                print "Cannot open", fn
            reported.add(fn)
            return None

    return elffile

def resolve_line(fn, ip):
    elffile = find_elf_file(fn)
    if elffile is None:
        return "?"
    if fn not in lines and elffile.has_dwarf_info():
        lines[fn] = build_line_table(elffile.get_dwarf_info())

    src = None
    if resolve_line and fn in lines:
        pos = util.find_le(lines[fn], ip)
        if pos:
            src = "%s:%d" % (pos[2], pos[3])    
    return src

# global one hit cache
# helps a lot for LBR decoding
# tbd use a small list with LRU?
last_sym = None

def resolve_sym(fn, ip):
    elffile = find_elf_file(fn)
    if elffile is None:
        return "?", 0
    global last_sym

    try:
        if fn not in symtables:
            symtables[fn] = build_symtab(elffile)

        if last_sym and last_sym[0] <= ip <= last_sym[1]:
            return last_sym[2], ip - last_sym[0]

        loc = None
        offset = None
        if fn in symtables:
            sym = util.find_le(symtables[fn], ip)
            if sym:
                loc, offset = sym[2], ip - sym[0]
    except elftools.common.exceptions.ELFError:
        return  "?", 0

    return loc, offset
        
def resolve_ip(filename, foffset, ip, need_line):
    sym, soffset, line = None, 0, None
    if filename and filename.startswith("/"):
        sym, soffset = resolve_sym(filename, foffset)
        if not sym:
            sym, soffset = resolve_sym(filename, ip)
        if need_line:
            line = resolve_line(filename, ip)
    else:
        sym, soffset = kernel.resolve_kernel(ip)
    return sym, soffset, line

if __name__ == '__main__':
    import sys
    print resolve_addr(sys.argv[1], int(sys.argv[2], 16))
    print resolve_line(sys.argv[1], int(sys.argv[2], 16))
