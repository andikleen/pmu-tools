![pmu-tools](http://halobates.de/pmu-tools.png)

![Python linting and testing](https://github.com/andikleen/pmu-tools/workflows/Python%20linting%20and%20testing/badge.svg)
![jevents test](https://github.com/andikleen/pmu-tools/workflows/jevents%20test/badge.svg)

pmu tools is a collection of tools and libraries for profile collection and performance
analysis on Intel CPUs on top of [Linux perf](https://perf.wiki.kernel.org/index.php/Main_Page).
This uses performance counters in the CPU.

# Quick (non-) installation

pmu-tools doesn't really need to be installed. It's enough to clone the repository
and run the respective tool (like toplev or ocperf) out of the source directory.

To run it from other directories you can use
   export PATH=$PATH:/path/to/pmu-tools
or symlink the tool you're interested in to /usr/local/bin or ~/bin. The tools automatically
handle finding the python dependencies.

When first run toplev / ocperf will automatically download the Intel event lists from
https://download.01.org. This requires working internet access. Later runs can
be done offline. It's also possible to download the event lists ahead, see
[pmu-tools offline](https://github.com/andikleen/pmu-tools/wiki/Running-ocperf-toplev-when-not-on-the-internet)

toplev works with both python 2.7 and python 3. However it requires an not
too old perf tools and depending on the CPU an uptodate kernel. For more details
see [toplev kernel support](https://github.com/andikleen/pmu-tools/wiki/toplev-kernel-support)

The majority of the tools also don't require any python dependencies and run
in "included batteries only" mode. The main exception is generating plots or XLSX
spreadsheets, which require external libraries.

If you want to use those run

      pip install -r requirements.txt

once, or follow the command suggested in error messages.

jevents is a C library. It has no dependencies other than gcc and can be built with

	cd jevents
	make

# Quick examples

	toplev -l2 program
measure whole system in level 2 while program is running

	toplev -l1 --single-thread program
measure single threaded program. system must be idle.

	toplev -l3 --no-desc -I 100 -x, sleep X
measure whole system for X seconds every 100ms, outputting in CSV format.

	toplev --all --core C0 taskset -c 0,1 program
Measure program running on core 0 with all nodes and metrics enabled.

	toplev --all --xlsx x.xlsx -a sleep 10
Generate spreadsheet with full system measurement for 10 seconds

For more details on toplev please see the [toplev tutorial](https://github.com/andikleen/pmu-tools/wiki/toplev-manual)

# What tool to use for what?

You want to:

- understand CPU bottlenecks on the high-level: use toplev.
- display toplev output graphically: toplev --xlsx (or --graph)
- know what CPU events to run, but want to use symbolic names for a new CPU: use ocperf.
- measure interconnect/caches/memory/power management on Xeon E5+: use ucevent or toplev
- Use perf events from a C program: use jevents
- Query CPU topology or disable HyperThreading: use cputop
- Change Model Specific Registers: use msr
- Change PCI config space: use pci

For more details on the tools see [TOOLS](TOOLS.md)

# All features:

## Major tools/libraries

* The "ocperf" wrapper to "perf" that provides a full core performance
counter event list for common Intel CPUs. This allows to use all the
Intel events, not just the builtin events of perf. Can be also used
as a library from other python programs
* The "toplev.py" tool to identify the micro-architectural bottleneck for a workload.
This implements the [TopDown](https://sites.google.com/site/analysismethods/yasin-pubs) or [TopDown2](http://software.intel.com/en-us/articles/how-to-tune-applications-using-a-top-down-characterization-of-microarchitectural-issues)
methodology.
* The "ucevent" tool to manage and compute uncore performance events. Uncore is the part of the CPU that is not core.  Supports many metrics for power management, IO, QPI (interconnect), caches, and others.  ucevent automatically generates event descriptions
for the perf uncore driver and pretty prints the output. It also supports
computing higher level metrics derived from multiple events.
* A library to resolve named intel events (like INST_RETIRED.ANY)
to perf_event_attr ([jevents](http://halobates.de/jevents.html))
and provide higher level function for using the Linux perf API
for self profiling or profiling other programs.
It also has a "perf stat" clone called "jestat"
* A variety of tools for plotting and post processing perf stat -I1000 -x,
or toplev.py -I1000 -x, interval measurements.
* Some utility libraries and functions for MSR access, CPU topology
and other functionality,as well as example programs how to program the Intel PMU.

There are some obsolete tools which are not supported anymore, like simple-pebs.
These are kept as PMU programming reference, but may need some updates to build
on newer Linux kernels.

# Recent new features:

* toplev updated to Ahmad Yasin's TMA 4.2:
    Bottlenecks Info group, Tuned memory access costs
    New Metrics
    * New Info.Bottlenecks group aggregating total performance-issue costs in SLOTS across the tree: [SKL onwards]
    ** Memory_Latency, Memory_Bandwidth, Memory_Data_TLBs
    ** Big_Code, Instruction_Fetch_BW, Branching_Overheads and
    ** Mispredictions (introduced in 4.1 release)
    * New tree node for Streaming_Stores [ICL onwards]
    Key Enhancements & fixes
    ** The Average_Frequency is calculated using the TSC (TimeStamp Counter) value
    ** With this key enhancement #Mem costs become NanoSecond- (was Constant), DurationTimeInMilliSeconds becomes ExternalParameter CountDomain and #Base_Frequency is deprecated
    * Fixed Ports_Utilization for detection of serializing operations [SKL onwards]
    * Tuned MITE, DSB, LSD and move to Slots_Estimated domain [all]
    * Capping DTLB_Load and STLB_Hit_Load cost using events in Clocks CountDomain [SKL onwards]
    * Tuned Pause latency using default setting [CLX]
    * Fixed average Assists cost [IVB onwards]
    * Fixed Mispredicts_Resteers Clears_Resteers Branch_Mispredicts Machine_Clears and Mispredictions [ICL+]
    * A parameter to avoid using PERF_METRICS MSR e.g. for older OS kernels (implies higher event multiplexing)
    * Reduced # events for select nodes collections (lesser event multiplexing): Backend_Bound/Core_Bound, Clear_Resteers/Unknwon_Branches, Kernel_Utilization
    * Other fixes: Thresholds, Tagging (e.g. Ports_Utilized_2), Locate-with, etc
* toplev now has a --parallel argument to can process large --import input files
  with multiple threads. There is a new interval-merge tool that can merge
  multiple perf-output files.
* toplev now supports a --subset argument that can process parts of --import input files,
  either by splitting them or by sampling. This is a building block for more efficient
  processing of large input files.
* toplev can now generate scripts to collect data with perf stat record to lower runtime
  collection overhead, and import the perf.data, using a new --script-record option.
  This currently requires unreleased perf patches, hopefully in Linux 5.11.
* toplev can now support json files for Chrome's about://tracing with --json
* toplev now supports --no-multiplex in interval mode (-Ixxx)
* The tools now don't force python 2 anymore to support running out of the box
  on distributions which do not install python 2.
* toplev now hides the perf command line by default. Override with --perf.
* Updated to TMA 4.11: Fixed an error in misprediction-related and Power License metrics
* toplev now supports the new fixed TMA metrics counters on Icelake. This requires
  the upcoming 5.9+ kernel.
* toplev was updated to Ahmad Yasin's/Anton Hanna's TMA 4.1
  New Metrics:
  - Re-arrange Retiring Level 2 into Light\_Operations & Heavy\_Operations. Light\_Operations replaces
    the previous Base (or "General Retirement") while Heavy\_Operations is a superset of the
    Microcode\_Sequencer node (that moves to Level 3)
  - Mixing\_Vectors: hints on a pitfall when intermixing the newer AVX* with legacy SSE* vectors,
    a tree node under Core Bound [SKL onwards]
  Key Enhancements & fixes
  - Tuning of Level 2 breakdown for Backend\_Bound, Frontend\_Bound (rollback FRONTEND\_RETIRED 2-events use) [SKL onwards]
  - Improved branch misprediction related metrics to leverage a new PerfMon event [ICL onwards]
  - Improved CORE\_CLKS & #Retire\_Slots-based metrics [ICL onwards]
  - Adjusted cost of all nodes using MEM\_LOAD*RETIRED.* in case of shadow L1 d-cache misses
  - renamed Frontend_ to FetchLatency/Bandwidth [all]
  - Additional documentation/details to aid automated parsing in ‘For Tool Developers’.
  - Other fixes including Thresholds, Tagging (e.g. $issueSnoops), Locate-with, Metric Group
* toplev can now generate charts in xlsx files with the --xchart option.

Older changes in [CHANGES](CHANGES.md)

# Help wanted

- The plotting tools could use a lot of improvements. Both tl-serve and tl-barplot.
If you're good in python or JS plotting any help improving those would be appreciated.

# Mailing list

Please post to the linux-perf-users@vger.kernel.org mailing list.
For bugs please open an issue on https://github.com/andikleen/pmu-tools/issues

# Licenses

ocperf, toplev, ucevent, parser are under GPLv2, jevents is under the modified BSD license.

Andi Kleen
pmu-tools@halobates.de
