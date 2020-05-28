# Handle warnings and errors
# Separate module to avoid circular imports
from __future__ import print_function
import sys
import fnmatch

quiet = False
debug = None

def debug_msg(x, y):
    if debug and any(map(lambda p: fnmatch.fnmatch(x, p), debug.split(","))):
        print("debug:", x + ": " + str(y), file=sys.stderr)

def warning(x):
    if not quiet:
        print("WARNING:", x, file=sys.stderr)
