# Handle warnings and errors
# Separate module to avoid circular imports
import sys
import fnmatch

quiet = False
debug = None

def debug_msg(x, y):
    if debug and any(map(lambda p: fnmatch.fnmatch(x, p), debug.split(","))):
        print >>sys.stderr, "debug:", x + ": " + str(y)

def warning(x):
    if not quiet:
        print >>sys.stderr, "WARNING:", x
