# jevents

jevents is a C library to use from C programs.

## Features

* Handling the perf ring buffer and reading performance counters from ring 3 in C programs,
* Basic frame work for self profiling of memory addresses accessed by the program.
* resolving symbolic event names using downloaded event files

For more details see the [API reference](http://halobates.de/jevents.html) 

## Building

cd jevents
make
sudo make install


## self profiling 

Self is a simple library to support self-profiling of programs, that is programs
that measure their own execution.

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

