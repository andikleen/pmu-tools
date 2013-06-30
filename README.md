![pmu-tools] (http://halobates.de/pmu-tools.png)

pmu tools is a collection of tools for profile collection and performance
analysis on Intel CPUs on top of Linux perf.

# Current features:

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
- A "toplev.py" tool to do cycle composition for a workload, that is 
measure where in the CPU pipe line it bottle necks.
- A plot tool to plot perf stat -Ixxx -x, or toplev.py -Ixxx -x, output
- Some utility programs to access pci space or msrs on
the command line
- A utility program to program the PMU directly from user space
(pmumon.py) for counting. This is mainly useful for testing
and experimental purposes.
- A library for self profiling with Linux since Linux 3.3
Note for self-profiling on older kernels you can use
[simple-pmu] (http://halobates.de/simple-pmu)
- An example program for address profiling on Nehalem and later
Intel CPUs (addr)
- A program to print the currently running events (event-rmap)
- Support for analyzing the raw PEBS records with perf.

# Usage:

Check out the repository

## ocperf:

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

The latego.py, msr.py, pci.py modules can be also used as standalone programs
to enable the offcore workaround, change MSRs or change PCI config space respectively.

## toplev.py:

Do cycle decomposition on a workload: estimate on which part of the
CPU pipeline it bottlenecks. The bottlenecks are expressed as a tree
with different levels (max 4).

This follows the "Top Down" methology described in B.3.2 of
the [Intel optimization manual] (http://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-optimization-manual.pdf)

toplev.py only supports counting, that is it cannot tell you where in
the program the problem occurred.

Requires an Intel Sandy, Ivy Bridge, Haswell CPU.
It works best on Ivy Bridge currently, the others only support
a basic (but reliable) model.

[IVB model] (http://halobates.de/ivb-hierarchy.svg)
[Simple model] (http://halobates.de/simple-hierarchy.svg)

Usage:

	./toplev.py [-lX] [-v] [-d] [-o logfile] program
	measure program
	./toplev.py [-lX] [-v] [-d] [-o logfile] -a sleep X
	measure whole system for X seconds
	./toplev.py [-lX] [-v] [-d] [-o logfile] -p PID
	measure pid PID

### Options:

	-o set output file
	-v print everything
	-d use detailed model if available (only Ivy Bridge currently)
	-lLEVEL only use events upto max level (max 4)
	-x,     Enable CSV mode with separator ,
	-Ixxx   Enable interval mode, measure every xxx ms

Other perf arguments allowed (see the perf documentation)
After -- perf arguments conflicting with toplevel can be used.

### Some caveats:

The lower levels of the measurement tree are much less reliable
than the higher levels.  They also rely on counter multi-plexing
and cannot use groups, which can cause larger measurement errors
with non steady state workloads.

(If you don't understand this terminology; it means measurements
are much less accurate and it works best with programs that primarily
do the same thing over and over)

In this case it's recommended to measure the program only after
the startup phase by profiling globally or attaching later.
level 1 or running without -d is generally the most reliable.

One of the events (even used by level 1) requires a recent enough
kernel that understands its counter constraints.  3.10+ is safe.

## interval-plot:

interval-plot.py can plot the output of perf stat -I1000 -x, or 
or toplev.py -I1000 -x, 

![plot-example] (http://halobates.de/interval.plot.l2.png)

## self: 

Self is a simple library to support self-profiling of programs, that is programs
that measure their own execution.

cd self
make

Read the documentation. 

[rdpmc] (http://htmlpreview.github.com/?https://github.com/andikleen/pmu-tools/blob/master/self/rdpmc.html)
is the basic facility to access raw counters.

ocperf can be used to generate raw perf numbers for your CPU to pass
to rdpmc_open()

	ocperf list | less
<look for intended event>
	DIRECT_MSR=1 ./ocperf.py stat -e eventname true
<look for perf stat -e rXXXX in output>

![example] (http://halobates.de/pmutools-event.png)

XXX is the needed event number in hex. Note that self does not support
offcore or uncore events.

Also the event numbers are CPU specific, so you may need a
/proc/cpuinfo model check for portable programs (see the ocperf source
for example)

Example (replace EVENTNUMBER with your intended event from above or a
perf event like PERF_COUNT_HW_CPU_CYCLES). 

This is very simplified, for a real benchmark you almost certainly
want some warmup, multiple iterations, possibly context switch
filtering and some filler code to avoid cache effects.

	#include "rdpmc.h"

	struct rdpmc_ctx ctx;
	unsigned long long start, end;

	if (rdpmc_open(EVENTNUMBER, &ctx) < 0) ... error ...
	start = rdpmc_read(&ctx);
	... your workload ...
	end = rdpmc_read(&ctx);

[measure] (http://htmlpreview.github.com/?https://github.com/andikleen/pmu-tools/blob/master/self/measure.html)
supports event group profiling.  
[interrupts] (http://htmlpreview.github.com/?https://github.com/andikleen/pmu-tools/blob/master/self/interrupts.html)
provides functions for a common use case of filtering out context
switches and interrupts from micro benchmarks. These only work on
Intel Ivy and Sandy Bridge CPUs.

Link the object files and include the header files in your program

/sys/devices/cpu/rdpmc must be 1.

rtest.c and test2.c provide
examples. http://halobates.de/modern-pmus-yokohama.pdf provides some
additional general information on cycle counting. The techniques used
with simple-pmu described there can be used with self too.

## pebs-grabber:

Perf doesn't export the raw PEBS output, which contains a lot of useful
information. PEBS is a sampling format generated by Intel CPUs for
some events.

pebs-grabber gabs PEBS data from perf. This assumes the perf pebs
handler is running, we just also do trace points with the raw data.

May need some minor tweaks as kernel interface change, and will also
not likely work on very old kernels.

This will create two new trace points trace_pebs_v1 and trace_pebs_v2
that log the complete PEBS record. When the CPU supports PEBSv2
(Haswell) the additional fields will be logged in pebs_v2.

	  make [KDIR=/my/kernel/build/dir]
	  insmod pebs-grabber.ko 
	  # needs to record as root
	  perf record -e cycles:p,pebs_v1,pebs_v2 [command, -a for all etc.]
	  perf report
	  perf script to display pebs data
	  # alternatively trace-cmd and kernelshark can be also used to dump
   	  # the pebs data

See http://download.intel.com/products/processor/manual/253669.pdf
18.10.2 for a description of the PEBS fields.

Note this doesn't work with standard FC18 kernels, as they broke
trace points in modules. It works with later and earlier kernels.

## addr:

addr is a basic frame work for self profiling of memory addresses accessed by the program.
Requires a Linux 3.10+ kernel and a supported CPU.

## event-rmap

event-rmap [cpu] prints the currently running events. This provides
an easier answer to question Q2j in Vince Weaver's perf events FAQ.

# Licenses

ocperf is under GPLv2, self and addr under the modified BSD license.

Andi Kleen
