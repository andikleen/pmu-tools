#!/usr/bin/python
# resolve ELF and DWARF symbol tables using elftools
import bisect
from elftools.common.py3compat import maxint, bytes2str
from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection

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
                end = sym['st_value'] + sym['st_size']
                syms.append((sym['st_value'], end, 
                             bytes2str(sym.name)))
    syms.sort()
    return syms

def find_le(f, key):
    pos = bisect.bisect_left(f, (key,))
    if pos < len(f) and f[pos][0] == key:
        return f[pos]
    if pos == 0:
        return None
    return f[pos - 1]

def resolve_addr(fn, ip):
    if fn in open_files:
        elffile = open_files[fn]
    else:
        f = open(fn, 'rb')
        elffile = ELFFile(f)
        open_files[fn] = elffile

    if fn not in lines and elffile.has_dwarf_info():
        lines[fn] = build_line_table(elffile.get_dwarf_info())

    if fn not in symtables:
        symtables[fn] = build_symtab(elffile)

    loc = None
    offset = None
    if fn in symtables:
        sym = find_le(symtables[fn], ip)
        if sym:
            loc, offset = sym[2], ip - sym[0]

    src = None
    if fn in lines:
        pos = find_le(lines[fn], ip)
        if pos:
            src = "%s:%d" % (pos[2], pos[3])    

    return loc, offset, src
        
if __name__ == '__main__':
    import sys
    print resolve_addr(sys.argv[1], int(sys.argv[2], 16))
