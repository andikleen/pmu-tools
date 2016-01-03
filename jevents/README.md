# jevents

jevents is a C library to use from C programs to make access to the kernel Linux perf interface easier.
It also includes some examples to use the library.

## Features

* Resolving symbolic event names using downloaded event files
* Reading performance counters from ring 3 in C programs,
* Handling the perf ring buffer (for example to read memory addresses)

For more details see the [API reference](http://halobates.de/jevents.html) 

## Building

	cd jevents
	make
	sudo make install

## Downloading event lists

Before using event lists they need to be downloaded. Use the pmu-tools
event_download.py script for this.

	% event_download.py

## Examples

* listevents: List all named perf and JSON events
* showevent: Convert JSON name or perf alias to perf format and test with perf
* event-rmap: Map low level perf event to named high-level event
* addr: Profile a loadable test kernel with address profiling
* jstat: Simple perf stat like tool with JSON event resolution.

## self profiling 

Reading performance counters directly in the program without entering
the kernel.

This is very simplified, for a real benchmark you almost certainly
want some warmup, multiple iterations, possibly context switch
filtering and some filler code to avoid cache effects.

```C
	#include "rdpmc.h"

	struct rdpmc_ctx ctx;
	unsigned long long start, end;

	if (rdpmc_open(PERF_COUNT_HW_CPU_CYCLES, &ctx) < 0) ... error ...
	start = rdpmc_read(&ctx);
	... your workload ...
	end = rdpmc_read(&ctx);
```

/sys/devices/cpu/rdpmc must be 1.

http://halobates.de/modern-pmus-yokohama.pdf provides some
additional general information on cycle counting. The techniques used
with simple-pmu described there can be used with jevents too.

## Resolving named events

Resolving named events to a perf event and set up reading from the perf ring buffer.

First run event_download.py to download a current event list for your CPU.

```C
	#include "jevents.h"
	#include "perf-iter.h"
	#include <linux/perf_event.h>
	#include <sys/syscall.h>
	#include <unistd.h>

	struct perf_event_attr attr;
	if (resolve_event("cpu_clk_thread_unhalted.ref_xclk", &attr) < 0) {
		... error ...
	}

	/* You can change attr, see the perf_event_open man page for details */

'''
