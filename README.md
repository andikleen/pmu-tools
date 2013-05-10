
pmu tools is a collection of tools for profile collection and performance
analysis on Intel CPUs on top of Linux perf.

Current features:

- A wrapper to "perf" that provides a full core event list for 
common Intel CPUs. This allows to use all the Intel events,
not just the builtin events of perf.
- Support for Intel "offcore" events on older systems that
do not have support for  this in the Intel. Offcore events
allow to profile the location of a memory access outside the
CPU's caches.
- Implement a workaround for some issues with offcore events 
on Sandy Bridge EP (Intel Xeon E5 first generation)
This is automatically enabled for the respective events, and also
available as a standalone program.
- Some utility programs to access pci space or msrs on
the command line

Usage:

Check out the repository
Copy all the files to a directory (or run from the source)
Run ocperf.py from that directory
ocperf.py searches for the data files in the same directory
as the binary

ocperf.py list
List all the events perf and ocperf supports on the current CPU

ocperf.py stat -e eventname ... 

ocperf.py record -e eventname ...

ocperf.py report --stdio

The translation back from the raw event name for report is only supported
for the --stdio mode. The interactive browser can be also used, but will
display raw perf event names.

When a older kernel is used with offcore events,
that does not support offcore events natively, ocperf has to run
as root and only one such profiling can be active on a machine.

tester provides a simple test suite.

Andi Kleen
