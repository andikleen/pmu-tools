* interval-normalize has a new --normalize-cpu option to normalize multi CPU
  CSV files from toplev or perf
* toplev now supports an experimental --drilldown option to automatically rerun
  with the nodes needed to analyze the bottleneck further.
* toplev can now output combined output xlsx files with the --xlsx option. This
  requires installing the xlsxwriter library using 'pip install xlsxwriter' for the
  correct python version. This is still an experimental feature.
* toplev now hides idle CPUs by default, unless the output is CSV. This
  is configurable using the new --idle-threshold argument. The default is hiding if less
  than 5% busy.
* toplev now gives suggestions on how to get better sampling events, and also got better
  at selecting them in the first place. In addition it can now suggest how to get more
  details on the bottleneck by enabling its children nodes.
* toplev can now add whole sub trees with --nodes 'nodename*'. Useful to drill down in specific
  areas while still keeping multiplexing overhead under control. With /NUM it is possible to
  to specify the max level nodes to add.
* With -v, toplev now indicates nodes that are below threshold with < not ? to avoid confusion.
  Note this is a potentially breaking change for CSV output users.
* pmu-tools is now generally python3 clean. One exception
  is parser which would need to be ported to the python3 construct.
* New tool utilized.py to remove idle CPUs from toplev output
* toplev --import can now directly decompress xz and gz files. -o / --valcsv / --perf-output
  can now directly compress files if their names are specified with .xz or .gz.
* toplev update to Ahmad Yasin's/Anton Hanna's TMA 4.0:
   New Models
    ICL: New model for IceLake client processor

    Note that running on Icelake with HyperThreading enabled requires updating the perf
    tool to a recent version that supports the "percore" notifier.

    New Metrics and Info groups
    - IpFLOP: Instructions per Floating Point (FP) Operation [BDW onwards]
    - New breakdown for Frontend\_Bandwidth per fetch unit: MITE, DSB & LSD
    - IO\_{Read|Write}\_BW: Average IO (network or disk) Bandwidth Use for {Reads|Writes} [server models]
    - LSD\_Coverage: Fraction of Uops delivered by the LSD (Loop Stream Detector; aka Loop Cache)
    - New Info group: Frontend that hosts LSD\_Coverage, DSB\_Coverage and IpBAClear

    Key Enhancements & fixes

    - Tuned/balanced Frontend\_Latency & Frontend\_Bandwidth (Bandwidth exposed as a very short FE latency) [SKL onwards]
    - Tuned/balanced Memory\_Bound & Core\_Bound in Backend\_Bound breakdown [SKL onwards]
    - Tuned L2\_Bound Node for high memory BW workloads [SKL onwards]
    - BpTB, IpL, IpS & IpB renamed to BpTkBranch, IpLoad, IpStore & IpBranch respectively (Inst\_Mix info metrics)
    - Backporting IpFarBranch to all pre SKL models
    - Renamed DRAM\_{Read\_Latency|Parallel\_Reads} to MEM\_{Read\_Latency|Parallel\_Reads}
    - Fixed Count Domain for (Load|Store|ALU)\_Op\_Utilization [SNB onwards]
    - Removed OCR L3 prefetch Remote HitM events [SKX,CLX]
    - Fixed descriptions for Ports\_Utilized\_{0|1|2|3m}
    - Fixed Pause latency [CLX]

* toplev can now generate a script with --gen-script to collect toplev data on a different
  system. The generated data can be then imported with --import
* toplev / event_download / ocperf have been ported to python3. They still work with python2,
  which is so far the default and used by the standard #! shebangs. But on systems that
  have no python2 they can be run with a python3 interpreter. This feature is still
  experimental, please report any regressions.
* toplev now supports --per-core / --per-socket output in SMT mode, and also a --global mode.
  This also works with reprocessed data (from --perf-output / --import), so it is possible
  to slice a single collection. It is also possible to specify them at the same time
  to get separate summaries. With --split-output -o file the different aggregations
  are written to different files.
* toplev update to Ahmad Yasin's/Anton Hanna's TMA 3.6:
	- {Load|Store}\_STLB\_(Hit|Miss): new metrics that breakdown DTLB\_{Load|Store} costs
	- L2\_Evictions\_(Silent|NonSilent)\_PKI: L2 (silent|non silent) evictions rate per Kilo instructios
	- IpFarBranch - Instructions per Far Branch
	- Renamed 0/1/2/3m\_Ports\_Utilized
	- DSB\_Switches is now available
	- Count Domain changes for multiple nodes. New threshold for IpTB ( Instructions per Taken Branches )
	- Re-organized/renamed Metric Group (e.g. Frontend\_Bound => Frontend)
* toplev now can run with the NMI watchdog enabled
	- This may reduce the need for being root to change this setting
	- It may still require kernel.perf\_event\_paranoid settings <1, unless
	  --single-thread --user is used. Some functionality like uncore
	  monitoring requires root or kernel.perf_event_paranoid < 0.
* toplev now supports running in KVM guests
	- The guest needs to have the PMU enabled (e.g. -cpu host for qemu)
	- The guest should report the same CPU type as the host (also -cpu host),
	  otherwise the current CPU needs to be overriden with FORCECPU=../EVENTMAP=..
	- PEBS sampling, offcore response, and uncore monitoring are not supported
* toplev now has a new --all option to enable all features.
* toplev now has a simple TSX metrics model with --tsx on Haswell/Broadwell
CPUs.
* toplev now supports some Linux software metrics with --sw. The trace
point based events may require running as root.
* toplev now supports power measurements with --power.
* toplev now supports a --no-multiplex mode to avoid multiplexing errors
on very reproducible workloads.
* toplev now supports a --no-group mode to work around bugs on older kernels
(such as RHEL/CentOS 6)
* ucevent now supports Intel Xeon v3 (codenamed Haswell server)
* toplev now supports measurements with HyperThreading enabled.
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
