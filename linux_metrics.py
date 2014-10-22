#
# basic linux software metrics
#

import os, sys

class CPU_Utilization:
    name = "CPU utilization"
    desc = " Number of CPUs used"
    nogroup = True
    def compute(self, EV):
        try:
            self.val = EV("task-clock", 1) / EV("interval-ns", 1)
        except ZeroDivisionError:
            self.val = 0

class CS:
    name = "Context switches"
    desc = " Number of context switches"
    nogroup = True
    def compute(self, EV):
        self.val = EV("cs", 1)

class MinorFaults:
    name = "Minor faults"
    desc = " Page faults not leading to disk IO (such as allocation of memory)."
    nogroup = True
    def compute(self, EV):
        self.val = EV("minor-faults", 1)

class MajorFaults:
    name = "Major faults"
    desc = " Page faults leading to disk IO."
    nogroup = True
    def compute(self, EV):
        self.val = EV("major-faults", 1)

class Migrations:
    name = "Migrations"
    desc = " Number of thread migrations to another CPU."
    nogroup = True
    def compute(self, EV):
        self.val = EV("migrations", 1)

class Syscalls:
    name = "Syscalls"
    desc = " Number of syscalls."
    nogroup = True
    def compute(self, EV):
        self.val = EV("raw_syscalls:sys_enter", 1)

class Interrupts:
    name = "Interrupts"
    desc = " Number of interrupts."
    nogroup = True
    # can overcount with shared vectors
    def compute(self, EV):
        self.val = EV("irq:irq_handler_entry", 1) + EV("nmi:nmi_handler", 1)

class Workqueues:
    name = "Workqueues"
    desc = " Work queue item executions."
    nogroup = True
    def compute(self, EV):
        self.val = EV("workqueue:workqueue_execute_start", 1)

# trace events
# IPIs
# syscalls
# nmis
# irqs
# workqueue execute start
# sched wakeup
# sched iowait
# filemap add to page cache
# compaction begin
# page_alloc
# block bio_queue
# net:net_dev_start_xmit
# net:netif_receive_skb + net
# napi_poll
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
            r.metric(Workqueues())
        else:
            print >>sys.stderr, "Need to be root for trace point Linux software metrics."
