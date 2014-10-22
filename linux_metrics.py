#
# basic linux software metrics
#
# for most of these it would be much nicer to measure durations, but
# perf stat doesn't support that
#

import os, sys

class CPU_Utilization:
    name = "CPU utilization"
    desc = " Number of CPUs used"
    nogroup = True
    subplot = "CPU Utilization"
    def compute(self, EV):
        try:
            # interval-ns is not a perf event, but handled by toplev internally.
            self.val = EV("task-clock", 1) / EV("interval-ns", 1)
        except ZeroDivisionError:
            self.val = 0

class CS:
    name = "Context switches"
    desc = " Number of context switches between threads or processes on a CPU."
    nogroup = True
    subplot = "OS metrics"
    def compute(self, EV):
        self.val = EV("cs", 1)

class MinorFaults:
    name = "Minor faults"
    desc = " Page faults not leading to disk IO, such as allocation of memory."
    nogroup = True
    subplot = "OS metrics"
    def compute(self, EV):
        self.val = EV("minor-faults", 1)

class MajorFaults:
    name = "Major faults"
    desc = """
Page faults leading to disk IO, such as loading executable text or do mmap'ed IO."""
    nogroup = True
    subplot = "OS metrics"
    def compute(self, EV):
        self.val = EV("major-faults", 1)

class Migrations:
    name = "Migrations"
    desc = " Number of thread/process migrations to another CPU."
    nogroup = True
    subplot = "OS metrics"
    def compute(self, EV):
        self.val = EV("migrations", 1)

# The events below require trace points, so typically root.

class Syscalls:
    name = "Syscalls"
    desc = " Number of syscalls, not including vsyscalls such as gettimeofday."
    nogroup = True
    subplot = "OS metrics"
    def compute(self, EV):
        self.val = EV("raw_syscalls:sys_enter", 1)

class Interrupts:
    name = "Interrupts"
    desc = """
Number of interrupts, including NMIs, excluding exceptions. These are interrupts caused by hardware,
typically to indicate IO. This includes performance counter sampling interrupts."""
    nogroup = True
    subplot = "OS metrics"
    # can overcount with shared vectors
    def compute(self, EV):
        self.val = EV("irq:irq_handler_entry", 1) + EV("nmi:nmi_handler", 1)

# XXX on older kernels will not count TLB flushes, when they still had an
# own vector
class IPIs:
    name = "IPIs"
    desc = """
Number of inter-processor-interrupts (IPIs). These are caused by software, for example to flush TLBs,
finish IOs on the originating CPU, flush per CPU software caches (such as slab allocator caches)
or force reschedules."""
    nogroup = True
    subplot = "OS metrics"
    # can overcount with shared vectors
    def compute(self, EV):
        self.val = (EV("irq_vectors:call_function_entry", 1) +
                    EV("irq_vectors:call_function_single_entry", 1) +
                    EV("irq_vectors:reschedule_entry", 1))

class Workqueues:
    name = "Workqueues"
    desc = " Work queue item executions. These are tasks executed by the kernel in the background."
    nogroup = True
    subplot = "OS metrics"
    def compute(self, EV):
        self.val = EV("workqueue:workqueue_execute_start", 1)

class BlockIOs:
    name = "BlockIOs"
    desc = " Block IOs issued. This counts the number of block IO requests inserted into a queue."
    nogroup = True
    subplot = "OS metrics"
    def compute(self, EV):
        self.val = EV("block:block_rq_insert", 1)

class NetworkTX:
    name = "NetworkTX"
    desc = " Network packets send to a network device. Aggregated (TSO/GRO) packets are counted as single packets."
    nogroup = True
    subplot = "OS metrics"
    def compute(self, EV):
        self.val = EV("net:net_dev_start_xmit", 1)

class NetworkRX:
    name = "NetworkRX"
    desc = " Network packets received from a network device. Aggregated (GRO) packets are counted as single packets."
    nogroup = True
    subplot = "OS metrics"
    def compute(self, EV):
        self.val = (EV("net:netif_rx", 1) +
                    EV("net:netif_receive_skb", 1) +
                    EV("net:napi_gro_receive_entry", 1) +
                    EV("net:napi_gro_frags_entry", 1))

# trace events
# sched wakeup
# sched iowait
# filemap add to page cache
# compaction begin
# page_alloc
# start reclaim
# XXX large page alloc
# intel_gpu_freq_change
# XXX gpu
# kvm:kvm_exit

class Setup:
    def __init__(self, r):
        r.metric(CPU_Utilization())
        r.metric(CS())
        r.metric(MinorFaults())
        r.metric(MajorFaults())
        r.metric(Migrations())
        if os.path.exists("/sys/kernel/debug/tracing/events"):
            r.metric(Syscalls())
            r.metric(Interrupts())
            r.metric(IPIs())
            r.metric(Workqueues())
            r.metric(BlockIOs())
            r.metric(NetworkTX())
            r.metric(NetworkRX())
        else:
            print >>sys.stderr, "Need to be root for trace point Linux software metrics."
