# ucevent uncore monitoring

The largest part of modern CPUs is outside the actual cores.
On Intel CPUs this is part is called the "Uncore" and and has last
level caches, PCI-Express, memory controller, QPI, power management
and other functionalities. To understand its performance the uncore
also provides a range of performance monitoring units (PMU) with
performance counters that can count various events.

This can be useful to monitor power management, IO bandwidth, memory
bandwidth, QPI (interconnect) traffic, cache hit rates and other metrics. 
The Linux kernel as part of perf has an uncore driver for Xeon
systems since Linux 3.8.  But since the uncore is complex, and the perf tool's
view of them is quite raw, they have been hard to use directly.

ucevent is a tool that provides a generic uncore event list, standard
equations and an (as friendly as possible) frontend to the uncore
metrics. It runs as a wrapper around perf stat. The output is similar
to turbostat.

In general the uncore can only monitor metrics. It cannot tell exactly
where in a program something occurs (it is not a profiler). It can, however,
report trends over time.

# Supported systems and configurations

ucevent currently only supports Intel Xeon E5 2600 series (codename Sandy
Bridge EP) 

For the QPI and memory controller metrics the BIOS also needs to
expose the uncore monitoring PCI devices (this is often disabled by default
and, depending on the system, may need a BIOS update to enable).

When the BIOS does not support these devices only a subset (mostly
power management) of the uncore monitoring is available. Enabling
them may also require setting a BIOS option.

You can check in lspci if the monitoring devices are available. It
should show output similar to this:

	# lspci | grep Performance
	ff:13.1 Performance counters: Intel Corporation Sandy Bridge Ring to PCI Express Performance Monitor (rev 07)
	ff:13.4 Performance counters: Intel Corporation Sandy Bridge QuickPath Interconnect Agent Ring Registers (rev 07)
	ff:13.5 Performance counters: Intel Corporation Sandy Bridge Ring to QuickPath Interconnect Link 0 Performance Monitor (rev 07)
	ff:13.6 System peripheral: Intel Corporation Sandy Bridge Ring to QuickPath Interconnect Link 1 Performance Monitor (rev 07)

The uncore driver is active if a number of uncore files show up
in /sys/devices/

	# ls -d /sys/devices/uncore_*

The monitoring works best with a 3.10+ kernel with the patches in
patches-3.10 applied. Later kernels may already include some/all of
them.  The perf tool should be installed in a new enough version.
Without the right patches there will be various problems.

# Tutorial / Examples

The uncore does not profile individual programs, it profiles
everything going on on a socket with cores (each of which may execute
a different program).  Normally the monitoring is done in the
background parallel to some workload.  By default ucevent prints a
sample every second and runs until stopped with Ctrl-C.

It generates the perf command line to collect the data, runs perf
and then does data post processing (computing equations) and finally
outputs the data.

First set up pmu-tools if you haven't already

	% git clone https://github.com/andikleen/pmu-tools
	% cd pmu-tools

The rest of the tutorial needs to run as root, as the uncore 
is a global resource:

	# cd pmu-tools/ucevent
	# export PATH=$PATH:$(pwd)

"sleep XXX" can be used to define the number of seconds to measure:
Measure PCI bandwidth for 10 seconds, print measurement every two seconds:

	# ucevent.py -I 2000  CBO.PCIE_DATA_BYTES sleep 10
	S0-CBO.PCIE_DATA_BYTES
	|      S1-CBO.PCIE_DATA_BYTES
	384.00 256.00 
	0.00   256.00 
	0.00   0.00   
	0.00   0.00   

The data is output separately for each CPU socket.

As you can see this is a fairly idle system. If we generate some PCI-E 
traffic (for example an ping -f -s1400 to a neighboring system), it looks more like

	S0-CBO.PCIE_DATA_BYTES
	|             S1-CBO.PCIE_DATA_BYTES
	15,369,344.00 0.00  
	15,587,904.00 0.00  
	15,577,408.00 0.00  
	14,942,336.00 0.00  

As you can see the ping was on socket 0, while the PCI-E on socket 1
is still idle.  ping -f is a fairly drastic way to generate load: make
sure the owner of the other system and the network concur.  There is
currently no way to limit the data to specific PCI devices.

Alternatively a program can be also run from ucevent and measure while
the program runs.  However again it is important to keep it mind it
will profile the whole sockets specified unlike normal perf stat.

This example shows the number of DIMM page misses in the DDR memory controller.
This can be a fairly important metric, as it affects memory latency significantly.

	# ucevent.py iMC.PCT_REQUESTS_PAGE_MISS my-workload

Only specific sockets can be measured. In this case it can help
to bind a workload to that socket. Note that a socket in ucevent
is not always the same as a node, but it often is.

	# ucevent.py -v --socket 0 iMC.PCT_REQUESTS_PAGE_HIT numactl --cpunodebind=0 workload
	Expression 1 - (PCT_REQUESTS_PAGE_EMPTY + PCT_REQUESTS_PAGE_MISS)
	Events: iMC.PCT_REQUESTS_PAGE_HIT
	perf stat -e '{uncore_imc_0/event=0x1/, ... lots of events ...  }' -I1000 -x, -C0 ...
	iMC0.PCT_REQUESTS_PAGE_HIT
	|      iMC1.PCT_REQUESTS_PAGE_HIT
	|      |      iMC2.PCT_REQUESTS_PAGE_HIT
	|      |      |      iMC3.PCT_REQUESTS_PAGE_HIT
	9.09   49.33  10.71  8.60   

Here we measure the percentage of DIMM page hits.
This also specifies verbose mode, so you can see the generated perf command line
and some more information.

List derived (higher level) available metrics that can be measured
(this is a subset of the full list)

	# ucevent.py
	...
	CBO CACHE Events
	  CBO.LLC_DRD_MISS_PCT           LLC DRD Miss Ratio                      
	  CBO.MEM_WB_BYTES               Memory Writebacks
        ...

List all PCU (Power Management Control Unit) events with description

	# ucevent.py --desc --unsupported --cat PCU

Display the memory read and write bandwidth

	# ucevent.py  --scale GB iMC.MEM_BW_WRITES iMC.MEM_BW_READS

"--scale GB" scales the metric to GB/s. The values are printed every second
(can be changed with -I)

Display the QPI bandwidth and PCI-e bandwidth on socket 0 in GB/s This
system has four memory controllers per socket, which are accounted
separately

	# ucevent.py -S0 "QPI_LL.DATA_FROM_QPI / GB" "CBO.PCIE_DATA_BYTES / GB"
        ...
        iMC.MEM_BW_WRITES / GB
	|     iMC.MEM_BW_WRITES / GB
	|     |     iMC.MEM_BW_WRITES / GB
	|     |     |     iMC.MEM_BW_WRITES / GB
	|     |     |     |     iMC.MEM_BW_WRITES / GB
	|     |     |     |     |     iMC.MEM_BW_WRITES / GB
	|     |     |     |     |     |     iMC.MEM_BW_WRITES / GB
	|     |     |     |     |     |     |     iMC.MEM_BW_WRITES / GB
	0.30  0.29  0.30  0.29  0.37  0.37  0.40  0.38  
	0.34  0.33  0.35  0.33  0.43  0.44  0.47  0.45  
	0.32  0.31  0.32  0.31  0.42  0.42  0.45  0.43  

Display the percentage of time the uncore was running higher than
2.0Ghz and higher than 3.0Ghz.  The filter uses a multiplier of
100. Make sure to use the right filter for the right band.  Upto 4
bands are possible. 

	# ucevent.py PCU.PCT_FREQ_BAND0,filter_band0=20 PCU.PCT_FREQ_BAND1,filter_band1=30

The parameter after the comma is a qualifier. --desc will output the
possible qualifiers / filters for an event.  Some qualifier combinations may 
be non-sensical, the documentation will usually list the useful ones.

List the percentage of time the memory controllers spent in
self-refresh mode. Output the data in CSV mode to a file without any
extra output.

	# ucevent.py -o out.csv -x, iMC.PCT_CYCLES_SELF_REFRESH

Plot the data using R

	% R
	...
	> x <- read.csv("out.csv")
	> summary(x)
	> plot(x$iMC.PCT_CYCLES_SELF_REFRESH, type="o")

Plot the data in a web browser using [dygraphs](http://dygraphs.com/)

	% mkdir web
	% cp dygraph-out.html web/index.html
	% cp out.csv web
	% cd web
 	% python -m SimpleHTTPServer
	... point web browser at localhost:8000 ...

Note that dygraphs only works when the page is served through a HTTP
server, not directly through the file system. Also some firewall
settings may prevent serve, in this case copy the web directory to a
HTTP server directory to view it there.

List how much of the time each socket's frequency is thermally limited

	# ucevent.py PCU.PCT_FREQ_THERMAL_LTD

Using ucevent as non root (insecure). Run as root once:

	# sysctl -w kernel.perf_event_paranoid=-1

# Command Line options reference

	usage: ucevent.py [-h] [--cat CAT] [--unsupported] [--desc] [--name-only] [--equation]
	                  [--attr] [--scale {KB,GB,MB}] [--csv CSV] [--interval INTERVAL]
	                  [--socket SOCKET] [--cpu CPU] [--fieldlen FIELDLEN] [--verbose]
	                  [--no-sum] [--output OUTPUT]
	                  [events [events ...]]
	
	Intel Xeon uncore performance counter events frontend for perf. The uncore is the part
	of the CPU that is not core. This tool allows to monitor a variety of metrics in the
	uncore, including memory, QPI, PCI-E bandwidth, cache hit rates, power management
	statistics and various others.
	
	positional arguments:
	  events                List of events to be converted. May have a comma separate list
	                        of name=val qualifiers after comma for each event (see --desc
	                        output for valid qualifiers). Can use { and } (each as own
	                        argument and quoted) to define groups. Valid to use shell-style
	                        wildcards (quoted) to match multiple events. It is also valid
	                        to specify a equation (quoted, containing space). After -- a
	                        perf argument line can be specified (e.g. sleep NUM or a
	                        workload to run). Please note that ucevent measurements are
	                        always global to the specified socket(s) unlike normal perf
	                        stat.
	
	optional arguments:
	  -h, --help            show this help message and exit
	  --cat CAT             Only print events from categories containing this in list
	  --unsupported         Print all events, including unsupported and potentially broken
	                        ones. Use at your own risk.
	  --desc                Print detailed descriptions in list
	  --name-only           Only print event name in list
	  --equation            Print equations for derived events in list
	  --attr                Print attributes
	  --scale {KB,GB,MB}    Scale numbers to unit (GB,MB,KB)
	  --csv CSV, -x CSV     Enable CSV mode and use argument to separate fields
	  --interval INTERVAL, -I INTERVAL
	                        Measurement interval in ms
	  --socket SOCKET, -S SOCKET
	                        Measure only socket (default all)
	  --cpu CPU, -C CPU     Measure socket associated with CPU, or use that CPU for the
	                        (very few) events that use core events
	  --fieldlen FIELDLEN   Set output field length
	  --verbose, -v         More verbose output
	  --no-sum              Don't sum up multiple instances of units
	  --output OUTPUT, -o OUTPUT
	                        Set output file
# Attributes

Individual events have additional attributes. These can be specified
after the event separated with comma.

	# ucevent PCU.PCT_FREQ_BAND0,filter_band0=20

ucevent --desc will list the available qualifiers for each event. Note
that many qualifier combinations are not useful. The description in
"--desc" usually mentions the useful qualifiers.

Qualifiers can be also used with derived events, but there are some
limitations. The qualifier will always apply to all events used in the
derived event, which can result in some non-working combinations.

The qualifier displayed in "Filter" usually correspond to the filters 
discussed in the description.

# Grouping, event scheduling and measurement inaccuracy

The uncore contains different units (Power Control Unit, QPI, Memory
Controller etc.). These are also sometimes called boxes.  Each unit
can have multiple instances (for example each CPU core has its own CBO
last level cache slice). For more details please see the uncore
manual for the CPU in the references.

Each system can have multiple uncores for each
CPU socket. The individual uncore units have their performance
monitoring counters. Typically they have 4 counters, and some
additional filter registers.  There are also some additional restrictions.

ucevent works by programming different events for each of these
counters. When the output requires more than 4 counters (or runs
into the additional restrictions) for a given unit, or some filter register
is oversubscribed, the perf driver code has to multiplex the measurement.

Perf will then periodically switch to a different set of events during the
measurement period.

Many metrics are actually multiple events in a equation (for example a
ratio to the clock ticks get percent, see --equation output). When the
different terms of a equation are not monitored in the same time slice
this can add large errors. This is a common cause for "impossible results",
like percentages being larger than 100% or negative results.

There is the concept of "groups", that is events that always run
together. A group can be manually specified by using '{' and '}' as
arguments to ucevent.

	# ucevent '{' iMC.MEM_BW_WRITES iMC.MEM_BW_WRITES_TOTAL '}'

Some metrics cannot be run in a group, as they need more counters or
filters thnt are available at the same time by the monitoring units.
In this case putting them in a group will cause "#NC" (not counted) or
"#NS" (not supported) errors.

ucevent by default puts derived metrics and user equations into groups
of their own if they fit and there is no user specified
group. It currently cannot create groups automatically for some units
(primarily CBOX) Different events or equations on the command line can still run
at different time, unless explicit groups are specified. This may
cause visible inaccuracies when different columns are compared.

Also due to perf limitations some valid groups don't run. A common
case of this is multiple events from a different instance of the same
box on the same socket. The scheduler does not know that different 
instances are independent.

**In general avoiding multiplexing will yield the best results**

Some useful metrics require multiplexing though. When the automatic
grouping is not accurate enough the user should specific explicit groups.

Multiplexing works best when the workload is very "steady", and does not fluctuate much.

The multiplexing frequency can be configured in sysfs. For example to switch
to 10ms

	echo 10 > /sys/devices/uncore_name/perf_event_mux_interval_ms

The default is 4ms. Different multiplexing values may affect the results.

(Kernel before 3.11 or 3.10 with the included patches not applied, did not have
this setting, and had other multiplexing problems)

Another side effect of multiplexing is that it causes wakeups of one
core per socket at the multiplexing frequency.  This can disturb
power measurements.  If that is a problem decrease the
multiplexing frequency or avoid multiplexing.

# Unit summing

When there are multiple instances of a unit in a socket ucevent sums up
the individual instances by default (with some exceptions).
This can be disabled with the --no-sum option. This is primarily for
the cache slices (CBO), of which there is one for each core.

# Equations

Equations can be specified on the command line. They should contain a
(quoted) space or () so that the parser can detect them.

The equations are particularly useful to scale BYTES metrics to more easily readable units.

	ucevent.py "CBO.MEM_WB_BYTES / KB"

Available predefined units are GIGA, MEGA, KILO (10^x) and GB, MB, KB (2^(10x))

Some units have multiple instances, which ucevents automatically expands. When referencing
such multi-instance units in a equation, only events in the same unit can be referenced.
Wildcards are also not allowed in equations.

# Post processing data

The easiest way is to enable the CSV output mode (with -x,) 
and redirect the output to a file (-o file) Other separators can be also specified.
The output is normalized and can be directly processed with gnuplot, spreadsheets, R etc.

# Error display

perf may fail to measure a counter (for example if the group is not schedulable)
or ucevent may fail to compute a value. In this case it shows spreadsheet style
'#' errors. When you see a string of such errors they were summed up from multiple
measurements.

Current errors:

- #NS: Not supported. perf was not able to measure the event.
- #NC: Not counted. perf was not able to schedule the event.
- #NA: Not available. Value missing in perf output.
- #EVAL: ucevent failed to evaluate an equation

Division by zero is silently turned into 0, as that is somewhat common.

# Debugging and testing

ucevent has a variety of test suites. The most useful is the CHECK-ALL script that
runs all events for two seconds and SANITY-RUN which does simple sanity checks on
all the high level derived events. These should be run with some background load.
They require [GNU parallel](http://www.gnu.org/software/parallel/) to be installed.

RUN-ALL will run all tests (some errors are expected). 

ucevent has some undocumented options for debugging. If something goes wrong
--debug '\*' will enable a lot of extra output.

# References

[Xeon E5 2600 series uncore guide](http://www.intel.com/content/dam/www/public/us/en/documents/design-guides/xeon-e5-2600-uncore-guide.pdf)

# Support

Please contact linux-perf-users@vger.kernel.org

# Other Projects providing uncore monitoring

[Intel PCM](http://software.intel.com/en-us/articles/intel-performance-counter-monitor-a-better-way-to-measure-cpu-utilization) Runs from user space and provides a library.

[likwid](http://code.google.com/p/likwid/) 

[libpfm4](http://perfmon2.sourceforge.net/) has another program to convert (non derived) uncore events to perf form.

# Author

Andi Kleen 
pmu-tools@halobates.de
