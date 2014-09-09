![pmu-tools] (http://halobates.de/pmu-tools.png)

pmu tools is a collection of tools for profile collection and performance
analysis on Intel CPUs on top of [Linux perf](https://perf.wiki.kernel.org/index.php/Main_Page). This uses performance counters in the CPU.

# Recent new features:
* ucevent now supports Haswell server
* toplev now supports measurements with HyperThreading enabled
on IvyBridge system (but may need patching the kernel with this
[patch](http://halobates.de/ivb-allow-mem-load-uops) for levels larger than three)
* toplev now supports Silvermont CPUs, with a simple 1 level model.
* ocperf now outputs all possible offcore event combinations when 
an offcore file is available
* toplev now can plot directly with --graph. It can also 
now plot metrics.
* toplev updated to TopDown 2.5. Supports standard metrics (--metrics)
and has an experimential feature to suggest sample command lines
(--sample)
* ocperf now automatically downloads JSON event lists (3/29/2014)
This changed various event names. The old CSV files have been removed.
"PS" events are gone now. Use /p instead. 
Note this may require setting up https_proxy if you are behind a firewall.
* New jevents library to resolve event lists from C (3/28/2014)
* ucevent now supports Xeon E5/E7 v2 (IvyBridge Server) (old news)

# All features:

## Major tools/libraries

* The "ocperf" wrapper to "perf" that provides a full core performance 
counter event list for common Intel CPUs. This allows to use all the
Intel events, not just the builtin events of perf. Can be also used
as a library from other python programs
* The "toplev.py" tool to identify the micro-architectural bottleneck for a workload. 
This implements the [TopDown](http://software.intel.com/en-us/articles/how-to-tune-applications-using-a-top-down-characterization-of-microarchitectural-issues)
methology.
* The "ucevent" tool to manage and compute uncore performance events. Uncore is the part of the CPU that is not core.  Supports many metrics for power management, IO, QPI (interconnect), caches, and others.  ucevent automatically generates event descriptions
for the perf uncore driver and pretty prints the output. It also supports
computing higher level metrics derived from multiple events. 
* A library to resolve named intel events (like INST_RETIRED.ANY) 
to perf_event_attr ([jevents](http://halobates.de/jevents.html))
* A library for self profiling with Linux since Linux 3.3. Self
profiling is a program monitoring its own execution, either for controlled
benchmarking or to optimize itself.
For self-profiling on older kernels you can use
[simple-pmu] (http://halobates.de/simple-pmu)
* Support for Intel "offcore" events on older Linux systems where
the kernel perf subsystem does not support them natively.
Offcore events allow to categorize memory accesses that go outside the core.
* Workarounds for [some issues](http://software.intel.com/en-us/articles/performance-monitoring-on-intel-xeon-processor-e5-family) with offcore events on Sandy Bridge EP 
(Intel Xeon E5 v1)
This is automatically enabled for the respective events with ocperf, and also
available as a standalone program or python library.
* A variety of tools for plotting and post processing perf stat -I1000 -x, 
or toplev.py -I1000 -x, interval measurements.

---

## Experimental/minor tools:
- An example program for address profiling on Nehalem and later
Intel CPUs (addr)
- Some utility programs to access pci space or msrs on
the command line
- A utility program to program the PMU directly from user space
(pmumon.py) for counting. This is mainly useful for testing
and experimental purposes.
- A program to print the currently running events (event-rmap)
- Support for analyzing the raw PEBS records with perf.
- A pandas/scipy data model for perf.data analytics (work in progress)

---

# Usage:

Check out the repository. Run the tools from the directory you
checked out (but it does not need to be the current directory)
They automatically search for other modules and data files
in the same directory the script was located in.

# Dependencies
All tools (except for parser/) should work with a python 2.7
standard installation.  All need a reasonably recent perf (RHEL5 is too old)
ocperf.py should work with python 2.6, or likely 2.5 when the json
module is installed.

Except for the modules in parser/ there are no special
dependencies outside a standard python install on a recent
Linux system with perf. 

old. parser/ needs a scipy stack with pandas and pyelftools.

# Tools

## ocperf:

ocperf is a wrapper to "perf" that provides a full core event list for 
common Intel CPUs. This allows to use all the Intel defined events,
not just the builtin events of perf. 

A more detailed introduction is in [Andi's blog](http://halobates.de/blog/p/245)

ocperf.py list
List all the events perf and ocperf supports on the current CPU

	ocperf.py stat -e eventname ... 

	ocperf.py record -c default -e eventname ...

	ocperf.py report

When a older kernel is used with offcore events (events
that count types of memory accesses outside the CPU core)
that does not support offcore events natively, ocperf has to run
as root and only one such profiling can be active on a machine.

When "-c default" is specified for record, the default sampling overflow value will be
filled in for the sampling period. This option needs to be specified before 
the events and is not supported for all CPUs. By default perf uses 
a dynamic sampling period, which can cause varying (and sometimes
large) overhead. The fixed period minimizes this problem.

If you have trouble with one of the many acronyms in the event
list descriptions, the [Intel optimization manual](http://www.intel.com/content/www/us/en/architecture-and-technology/64-ia-32-architectures-optimization-manual.html) describes many of them.

### ocperf API

ocperf.py can be also used as a python module to convert or list
events for the current CPU:

```python
	import ocperf

	emap = ocperf.find_emap()
	if not emap:
		sys.exit("Unknown CPU or cannot find event table")
	ev = emap.getevent("BR_MISP_EXEC.ANY")
	if ev:
		print "name:", ev.output()
		print "raw form:", ev.output(use_raw=True)
		print "description:, ev.desc
```

To retrieve data for other CPUs set the EVENTMAP environment variable
to the csv file of the CPU before calling find\_emap()

### changing MSRs and PCI config space

The msr.py, pci.py, latego.py can be used as standalone programs
or python modules to change MSRs, PCI config space or enable/disable
the [workarounds](http://software.intel.com/en-us/articles/performance-monitoring-on-intel-xeon-processor-e5-family).

For example to set the MSR 0x123 on all CPUs to value 1 use:

	$ sudo ./msr.py 0x123 1

To read MSR 0x123 on CPU 0 

	$ sudo ./msr.py 0x123

To read MSR 0x123 on CPU 3: 

	$ sudo python
	>>> import msr
	>>> msr.readmsr(0x123, 3)

To set bit 0 in MSR 0x123 on all CPUs:

	$ sudo python
	>>> import msr
	>>> msr.writemsr(0x123, msr.readmsr(0x123) | 1)

(this assumes the MSR has the same value on all CPUs, otherwise iterate the readmsr 
over the CPUs)

## toplev.py:

Identify the micro-architectural bottleneck of a workload.

The bottlenecks are expressed as a tree with different levels (max 5).
Each bottleneck is only meaningful if the parent higher level crossed the
threshold (it acts similar to a binary search). The tool automatically only
prints meaningful ratios, unless -v is specified.

This follows the "Top Down" methology. The best description of the method
is in the "A top-down method for performance analysis and counter architecture"
paper (ISPASS 2014, unfortunately paywalled) Older descriptions of Top Down are in B.3.2 of
the [Intel optimization manual](http://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-optimization-manual.pdf) and
in this [article](http://software.intel.com/en-us/articles/how-to-tune-applications-using-a-top-down-characterization-of-microarchitectural-issues) and in [Ahmad Yasin's presentation](https://docs.google.com/viewer?a=v&pid=sites&srcid=ZGVmYXVsdGRvbWFpbnxhbmFseXNpc21ldGhvZHN8Z3g6MWJjNTE2OTU4ODVlZGFkMw) at a [ISCA workshop](https://sites.google.com/site/analysismethods/isca2013/program-1). I didn't invent it, I'm just implementing it.

A more gentle introduction is in [andi's blog](http://halobates.de/blog/p/262)

toplev.py only supports counting, that is it cannot tell you where in
the program the problem occurred, just what happened. There is now
an experimential --sample option to suggest sampling events for specific
problems.

Requires an Intel Sandy Bridge, Ivy Bridge, Haswell CPU (Core 2rd, 3rd, 4th generation)
On Sandy Bridge E/EP (Xeon E5, Core i7 39xx) only level 1 is supported
currently.

It works best on Ivy Bridge currently.  By default the simple high level model
is used. The detailed model is selected with -d, and the max level
specified with -l (max 5, default 2).

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
	--kernel Only measure kernel code
	--user	Only measure user code

Other perf arguments allowed (see the perf documentation)
After -- perf arguments conflicting with toplevel can be used.

### Some caveats:

The lower levels of the measurement tree are less reliable
than the higher levels.  They also rely on counter multi-plexing
and cannot use groups, which can cause larger measurement errors
with non steady state workloads.

(If you don't understand this terminology; it means measurements
in higher levels are less accurate and it works best with programs that
primarily do the same thing over and over)

It's recommended to measure the work load only after
the startup phase by using interval mode or attaching later.
level 1 or running without -d is generally the most reliable.
If your perf stat is new enough (3.12+) the --initial-delay option
is useful to skip the startup phase.

One of the events (even used by level 1) requires a recent enough
kernel that understands its counter constraints.  3.10+ is safe.

If you are on SandyBridge E/EP which does not have a detailed
model currently it's possible to force normal SandyBridge
with "FORCECPU=snb ./toplev.py ..."
to get higher levels working.  However some of the estimated latencies will be wrong
and some tree nodes may not work correctly. You have been
warned.

## ucevent uncore monitoring

Please see the [ucevent documentation] (http://github.com/andikleen/pmu-tools/tree/master/ucevent/#ucevent-uncore-monitoring)

## interval-plot:

interval-plot.py can plot the output of perf stat -I1000 -x

Requires matplotlib to be installed.

Below is the level 2 toplev measurement of a Linux kernel compile.
Note that tl-barplot below is normally better to plot toplev output.

![plot-example] (http://halobates.de/interval.plot.l2.png)

## interval-normalize:

This converts the output of perf stat -Ixxx -x, / toplev.py -Ixxx -x, 
to a normalized output (one column for each event). This allows
easier plotting and processing with other tools (spreadsheets, R, JMP, 
gnuplot etc.)

## plot-normalized:

Plot an already normalized data file. Requires pyplot to be installed.

## tl-barplot:

Plot output from toplev.py -I 1000 -v -x, --output file.csv -lLEVELS
toplev outputs percentages, so it's better to use a stacked plot,
instead of the absolute values interval-plot displays.  tl-barplot
implements a stacked barplot plot.

Requires matplotlib to be installed.

	toplev.py -I 100 -v -x, -l3 --output grep.3.csv grep -r foo /usr/*
	tl-barplot.py grep.3.csv  --title "GNU grep"

![tl-barplot-example] (http://halobates.de/grep.3.svg)

With a new enough matplotlib you can also enable xkcd mode
(install Humor Sans first)

	toplev.py -I 100 -v -x, -l2 --output povray.2.csv povray --benchmark
	tl-barplot.py povray.2.csv  --title "povray" --output povray-xkcd.png  --xkcd

![tl-barplot-xkcd] (http://halobates.de/povray.2.png)

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

```C
	#include "rdpmc.h"

	struct rdpmc_ctx ctx;
	unsigned long long start, end;

	if (rdpmc_open(EVENTNUMBER, &ctx) < 0) ... error ...
	start = rdpmc_read(&ctx);
	... your workload ...
	end = rdpmc_read(&ctx);
```

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

Older perf doesn't export the raw PEBS output, which contains a lot of useful
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
	  perf record -e cycles:p,pebs_v1,pebs\_v2 [command, -a for all etc.]
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

Also provides a simple [perf ring buffer API](http://halobates.de/addr.html)

## event-rmap

event-rmap [cpu] prints the currently running events. This provides
an easier answer to question Q2j in Vince Weaver's perf events FAQ.

# Mailing list

Please post to the linux-perf-users@vger.kernel.org mailing list.
For bugs please open an issue on https://github.com/andikleen/pmu-tools/issues

# Licenses

ocperf, toplev, ucevent are under GPLv2, self and addr under the modified BSD license.

Andi Kleen
pmu-tools@halobates.de
