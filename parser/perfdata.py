#!/usr/bin/env python
# A description of the perf.data file format in "construct"
#
# Copyright (c) 2011-2013, Intel Corporation
# Author: Andi Kleen
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# Only works on Little-Endian with LE input files. Sorry.
#
# TBD:
# Generic Bitfield adapter that handles endian properly?
# check size in all cases (or use optional+tunnel)
# tracing support
# processor trace (aux) data and extra info headers
# sample_id is not handled correctly in all cases
#
from __future__ import print_function
from construct import (If, Embedded, Struct, SNInt32, UNInt64, Flag, BitStruct,
                       Padding, Enum, Array, Bytes, Anchor, UNInt32, GreedyRange,
                       CString, PrefixedArray, TunnelAdapter, Magic, Pointer,
                       BitField, UNInt16, HexDumpAdapter, String, Pass, Value,
                       Switch)

def sample_type(ctx):
    return ctx.attr.perf_event_attr.sample_type

def sample_id_size(ctx):
    st = sample_type(ctx)
    return (st.tid + st.time + st.id + st.stream_id + st.cpu +
            st.identifier) * 8

def sample_id():
    return If(lambda ctx: True,  # xxx check size
              Embedded(Struct("id_all",
                              If(lambda ctx: sample_type(ctx).tid,
                                 Embedded(Struct("pid2",
                                                 SNInt32("pid2"),
                                                 SNInt32("tid2")))),
                              If(lambda ctx: sample_type(ctx).time,
                                 UNInt64("time2")),
                              If(lambda ctx: sample_type(ctx).id,
                                 UNInt64("id2")),
                              If(lambda ctx: sample_type(ctx).stream_id,
                                 UNInt64("stream_id2")),
                              If(lambda ctx: sample_type(ctx).cpu,
                                 Embedded(Struct("cpu",
                                                 UNInt32("cpu2"),
                                                 UNInt32("res")))),
                              If(lambda ctx: sample_type(ctx).identifier,
                                 UNInt64("identifier2")))))

def fork_exit(name):
    return Struct(name,
                  SNInt32("pid"),
                  SNInt32("ppid"),
                  SNInt32("tid"),
                  SNInt32("ptid"),
                  UNInt64("time"),
                  sample_id())

def thread_map():
    return Struct("thread_map",
                  UNInt64("nr"),
                  Array(lambda ctx: ctx.nr,
                        Struct("thread_map_entry",
                                       UNInt64("pid"),
                                       String("comm", 16))))

def id_index():
    return Struct("id_index",
                  UNInt64("nr"),
                  Array(lambda ctx: ctx.nr,
                     Struct("id_index_entry",
                        UNInt64("id"),
                        UNInt64("idx"),
                        UNInt64("cpu"),
                        UNInt64("tid"))))

def as_is():
    return Embedded(Struct("data", Bytes("data", lambda ctx: ctx.size - 8)))

def throttle(name):
    return Struct(name,
                  UNInt64("time"),
                  UNInt64("id"),
                  UNInt64("stream_id"),
                  sample_id())

def hweight64(ctx):
    return bin(ctx._.attr.perf_event_attr.sample_regs_user).count("1")

def event():
    return Embedded(
        Struct("event",
                If(lambda ctx: sample_type(ctx).identifier,
                   UNInt64("identifier")),
                If(lambda ctx: sample_type(ctx).ip,
                   UNInt64("ip")),
                If(lambda ctx: sample_type(ctx).tid,
                   Embedded(Struct("tid",
                                   SNInt32("pid"),
                                   SNInt32("tid")))),
                If(lambda ctx: sample_type(ctx).time,
                   UNInt64("time")),
                If(lambda ctx: sample_type(ctx).addr,
                   UNInt64("addr")),
                If(lambda ctx: sample_type(ctx).id,
                   UNInt64("id")),
                If(lambda ctx: sample_type(ctx).stream_id,
                   UNInt64("stream_id")),
                If(lambda ctx: sample_type(ctx).cpu,
                   Embedded(Struct("cpu",
                                   UNInt32("cpu"),
                                   UNInt32("res")))),
                If(lambda ctx: sample_type(ctx).period,
                   UNInt64("period")),
                If(lambda ctx: sample_type(ctx).read,
                   read_format()),
                If(lambda ctx: sample_type(ctx).callchain,
                   Struct("callchain",
                          UNInt64("nr"),
                          Array(lambda ctx: ctx.nr,
                                UNInt64("caller")))),
                If(lambda ctx: sample_type(ctx).raw,
                   Struct("raw",
                          UNInt32("size"),
                          Bytes("raw", lambda ctx: ctx.size))),
                If(lambda ctx: sample_type(ctx).branch_stack,
                   Struct("branch_stack",
                          UNInt64("nr"),
                          Array(lambda ctx: ctx.nr,
                                Struct("branch",
                                       UNInt64("from"),
                                       UNInt64("to"),
                                       # Little-Endian!
                                       BitStruct("flags",
                                                 Padding(4),
                                                 Flag("abort"),
                                                 Flag("in_tx"),
                                                 Flag("predicted"),
                                                 Flag("mispred"),
                                                 Padding(64 - 1 * 8)))))),
                If(lambda ctx: sample_type(ctx).regs_user,
                   Struct("regs_user",
                          Enum(UNInt64("abi"),
                               NONE = 0,
                               ABI_32 = 1,
                               ABI_64 = 2),
                          Array(lambda ctx: hweight64(ctx),
                                UNInt64("reg")))),
                If(lambda ctx: sample_type(ctx).stack_user,
                   Struct("stack_user",
                          UNInt64("size"),
                          Bytes("data", lambda ctx: ctx.size),
                          UNInt64("dyn_size"))),
                If(lambda ctx: sample_type(ctx).weight,
                   UNInt64("weight")),
                If(lambda ctx: sample_type(ctx).data_src,
                   UNInt64("data_src")),
                If(lambda ctx: sample_type(ctx).transaction,
                   UNInt64("transaction")),
                If(lambda ctx: sample_type(ctx).regs_intr,
                   Struct("regs_intr",
                          Enum(UNInt64("abi"),
                               NONE = 0,
                               ABI_32 = 1,
                               ABI_64 = 2),
                          Array(lambda ctx: hweight64(ctx),
                                UNInt64("reg")))),
                Anchor("anchor_end_event"),
                Padding(lambda ctx: max(0, ctx.size - ctx.anchor_end_event))))

def get_attr_list(ctx):
    return ctx._._.attrs.perf_file_attr.f_attr

# assume that sample_id_all is the same in all events
# we cannot look up the event without this.
def has_sample_id_all(ctx):
    attr = get_attr_list(ctx)[0]
    if 'sample_id_all' in attr:
        return attr.sample_id_all
    return False

# when sample_id_all is not supported, we may
# not look up the right one (perf.data limitation)
def lookup_event_attr(ctx):
    if "anchor_end_id" in ctx and ctx.anchor_end_id:
        idx = ctx.anchor_end_id
    elif 'id' in ctx and ctx['id']:
        idx = ctx['id']
    else:
        idx = 0
    return get_attr_list(ctx)[idx]

# XXX need to make OnDemand for large files

def perf_event_header():
    return Embedded(Struct(None,
                           Enum(UNInt32("type"),
                                MMAP            = 1,
                                LOST            = 2,
                                COMM            = 3,
                                EXIT            = 4,
                                THROTTLE        = 5,
                                UNTHROTTLE      = 6,
                                FORK            = 7,
                                READ            = 8,
                                SAMPLE          = 9,
                                MMAP2           = 10,
                                RECORD_AUX      = 11,
                                ITRACE_START    = 12,
                                LOST_SAMPLES    = 13,
                                SWITCH          = 14,
                                SWITCH_CPU_WIDE = 15,
                                NAMESPACES      = 16,
                                KSYMBOL         = 17,
                                BPF_EVENT       = 18,
                                CGROUP          = 19,
                                TEXT_POKE       = 20,
                                AUX_OUTPUT_HW_ID= 21,
                                HEADER_ATTR     = 64,
                                HEADER_EVENT_TYPE = 65,
                                TRACING_DATA    = 66,
                                HEADER_BUILD_ID = 67,
                                FINISHED_ROUND  = 68,
                                ID_INDEX        = 69,
                                AUXTRACE_INFO   = 70,
                                AUXTRACE        = 71,
                                AUXTRACE_ERROR  = 72,
                                THREAD_MAP      = 73,
                                CPU_MAP         = 74,
                                STAT_CONFIG     = 75,
                                STAT            = 76,
                                STAT_ROUND      = 77,
                                EVENT_UPDATE    = 78,
                                TIME_CONV       = 79,
                                HEADER_FEATURE  = 80,
                                COMPRESSED      = 81,
                                FINISHED_INIT   = 82),
                           Embedded(BitStruct(None,
                                              Padding(1),
                                              Enum(BitField("cpumode", 7),
                                                   UNKNOWN = 0,
                                                   KERNEL = 1,
                                                   USER = 2,
                                                   HYPERVISOR = 3,
                                                   GUEST_KERNEL = 4,
                                                   GUEST_USER = 5),

                                              Flag("ext_reserved"),
                                              Flag("exact_ip"),
                                              Flag("mmap_data"),
                                              Padding(5))),
                           UNInt16("size"),
                           If(has_sample_id_all,
                                 Pointer(lambda ctx: ctx.anchor_start + ctx.size - 8,
                                   UNInt64("anchor_end_id"))),
                           Value("attr", lookup_event_attr)))

def mmap():
    return Struct("mmap",
                  SNInt32("pid"),
                  SNInt32("tid"),
                  UNInt64("addr"),
                  UNInt64("len"),
                  UNInt64("pgoff"),
                  Anchor("anchor_start_of_filename"),
                  CString("filename"),
                  Anchor("anchor_end_of_filename"),
                  # hack for now. this shouldn't be needed.
                  If(lambda ctx: True, # XXX
                     Embedded(Pointer(lambda ctx:
                                      ctx.size + ctx.anchor_start -
                                      sample_id_size(ctx),
                                      sample_id()))))
def mmap2():
    return Struct("mmap2",
                  SNInt32("pid"),
                  SNInt32("tid"),
                  UNInt64("addr"),
                  UNInt64("len"),
                  UNInt64("pgoff"),
                  UNInt32("maj"),
                  UNInt32("min"),
                  UNInt64("ino"),
                  UNInt64("ino_generation"),
                  UNInt32("prot"),
                  UNInt32("flags"),
                  CString("filename"),
                  sample_id())

def read_flags(ctx):
    return ctx._.attr.read_format

def enabled_running():
    return Struct("enabled_running",
                  If(lambda ctx: read_flags(ctx).total_time_enabled,
                     UNInt64("total_time_enabled")),
                  If(lambda ctx: read_flags(ctx).total_time_running,
                     UNInt64("total_time_running")))

def read_format():
    return Struct("read",
                  If(lambda ctx: read_flags(ctx).group,
                     Struct("group",
                            UNInt64("nr"),
                            Embedded(enabled_running()),
                            Array(lambda ctx: ctx.nr,
                                  Struct("val",
                                         UNInt64("value"),
                                         If(lambda ctx:
                                            read_flags(ctx).id,
                                            UNInt64("id2")))))),
                  If(lambda ctx: not read_flags(ctx).group,
                      Struct("single",
                             UNInt64("value"),
                             Embedded(enabled_running()),
                             If(lambda ctx: read_flags(ctx).id,
                                UNInt64("id2")))))

def time_conv():
    return Struct("time_conv",
                  UNInt64("time_shift"),
                  UNInt64("time_mult"),
                  UNInt64("time_zero"))

def perf_event():
    return Struct("perf_event",
                  Anchor("anchor_start"),
                  perf_event_header(),
                  Switch("data",
                           lambda ctx: ctx.type,
                           {
                              "MMAP": mmap(), # noqa E121
                              "MMAP2": mmap2(),
                              "LOST": Struct("lost",
                                              UNInt64("id"),
                                              UNInt64("lost"),
                                             sample_id()),
                              "COMM": Struct("comm",
                                             SNInt32("pid"),
                                             SNInt32("tid"),
                                             CString("comm"),
                                             sample_id()),
                              "EXIT": fork_exit("exit"),
                              "THROTTLE": throttle("throttle"),
                              "UNTHROTTLE": throttle("unthrottle"),
                              "FINISHED_ROUND": as_is(),
                              "FORK": fork_exit("fork"),
                              "READ": Embedded(Struct("read_event",
                                                      SNInt32("pid"),
                                                      SNInt32("tid"),
                                                      read_format(),
                                                      sample_id())),
                              "SAMPLE": event(),
                              "TIME_CONV": time_conv(),
                              "THREAD_MAP": thread_map(),

                              # below are the so far not handled ones. Dump their
                              # raw data only
                              "RECORD_AUX": as_is(),
                              "AUX": as_is(),
                              "ITRACE_START": as_is(),
                              "LOST_SAMPLES": as_is(),
                              "SWITCH": as_is(),
                              "SWITCH_CPU_WIDE": as_is(),
                              "NAMESPACES": as_is(),
                              "KSYMBOL": as_is(),
                              "BPF_EVENT": as_is(),
                              "CGROUP": as_is(),
                              "TEXT_POKE": as_is(),
                              "AUX_OUTPUT_HW_ID": as_is(),
                              "HEADER_ATTR": as_is(),
                              "HEADER_EVENT_TYPE": as_is(),
                              "TRACING_DATA": as_is(),
                              "HEADER_BUILD_ID": as_is(),
                              "ID_INDEX":id_index(),
                              "AUXTRACE_INFO": as_is(),
                              "AUXTRACE": as_is(),
                              "AUXTRACE_ERROR": as_is(),
                              "CPU_MAP": as_is(),
                              "STAT": as_is(),
                              "STAT_ROUND": as_is(),
                              "EVENT_UPDATE": as_is(),
                              "HEADER_FEATURE": as_is(),
                              "COMPRESSED": as_is(),
                              "FINISHED_INIT": as_is(),
                           }),
                        Anchor("anchor_end"),
                        Padding(lambda ctx:
                                    ctx.size - (ctx.anchor_end - ctx.anchor_start)))

def perf_event_seq(attr):
    return GreedyRange(perf_event(attr))

perf_event_attr_sizes = (64, 72, 80, 96, 104, 112, 120, 128, 136)

perf_event_attr = Struct("perf_event_attr",
                         Anchor("anchor_start"),
                         Enum(UNInt32("type"),
                              HARDWARE = 0,
                              SOFTWARE = 1,
                              TRACEPOINT = 2,
                              HW_CACHE = 3,
                              RAW = 4,
                              BREAKPOINT = 5),
                         UNInt32("size"),
                         UNInt64("config"),
                         UNInt64("sample_period_freq"),
                         # must be in LE order, original is a u64
                         # each byte is reversed
                         BitStruct("sample_type",
                                   Flag("cpu"),
                                   Flag("id"),
                                   Flag("callchain"),
                                   Flag("read"),
                                   Flag("addr"),
                                   Flag("time"),
                                   Flag("tid"),
                                   Flag("ip"),

                                   Flag("data_src"),
                                   Flag("weight"),
                                   Flag("stack_user"),
                                   Flag("regs_user"),
                                   Flag("branch_stack"),
                                   Flag("raw"),
                                   Flag("stream_id"),
                                   Flag("period"),

                                   Padding(5),
                                   Flag("regs_intr"),
                                   Flag("transaction"),
                                   Flag("identifier"),

                                   Padding(64 - 3 * 8)),
                         BitStruct("read_format",
                                   Padding(4),
                                   Flag("group"),
                                   Flag("id"),
                                   Flag("total_time_running"),
                                   Flag("total_time_enabled"),
                                   Padding(64 - 1*8)),
                         Embedded(BitStruct(None,
                                            Flag("disabled"),
                                            Flag("inherit"),
                                            Flag("pinned"),
                                            Flag("exclusive"),
                                            Flag("exclude_user"),
                                            Flag("exclude_kernel"),
                                            Flag("exclude_hv"),
                                            Flag("exclude_idle"),
                                            Flag("mmap"),
                                            Flag("comm"),
                                            Flag("freq"),
                                            Flag("inherit_stat"),
                                            Flag("enable_on_exec"),
                                            Flag("task"),
                                            Flag("watermark"),
                                            BitField("precise_ip", 2),
                                            Flag("mmap_data"),
                                            Flag("sample_id_all"),
                                            Flag("exclude_host"),
                                            Flag("exclude_guest"),
                                            Flag("exclude_callchain_kernel"),
                                            Flag("exclude_callchain_user"),
                                            Padding(41))),
                         UNInt32("wakeup_events"),
                         UNInt32("bp_type"),
                         UNInt64("config1"),
                         If(lambda ctx: ctx.size >= perf_event_attr_sizes[1],
                            UNInt64("config2")),
                         If(lambda ctx: ctx.size >= perf_event_attr_sizes[2],
                            UNInt64("branch_sample_type")),
                         If(lambda ctx: ctx.size >= perf_event_attr_sizes[3],
                            Embedded(Struct(None,
                                            UNInt64("sample_regs_user"),
                                            UNInt32("sample_stack_user"),
                                            UNInt32("__reserved_2")))),
                         If(lambda ctx: ctx.size >= perf_event_attr_sizes[4],
                            UNInt64("sample_regs_intr")),
                         If(lambda ctx: ctx.size >= perf_event_attr_sizes[5],
                            UNInt32("aux_watermark")),
                         If(lambda ctx: ctx.size >= perf_event_attr_sizes[6],
                            UNInt32("aux_sample_size")),
                         If(lambda ctx: ctx.size >= perf_event_attr_sizes[7],
                            UNInt64("sig_data")),
                         If(lambda ctx: ctx.size >= perf_event_attr_sizes[8],
                            UNInt64("config3")),
                         Anchor("anchor_end"),
                         Padding(lambda ctx: ctx.size - ctx.anchor_end + ctx.anchor_start))

def pad(l = "len"):
    return Padding(lambda ctx: ctx[l] - (ctx.anchor_offset - ctx.anchor_start))

def str_with_len(name):
    return Struct(name,
                  UNInt32("len"),
                  Anchor("anchor_start"),
                  CString(name),
                  Anchor("anchor_offset"),
                  pad())

def feature_string(name):
    return If(lambda ctx: ctx._[name],
              perf_file_section(name,
                                Embedded(Struct(name,
                                                UNInt32("len"),
                                                CString(name)))))

def string_list(name, extra = Pass):
    return PrefixedArray(Struct(name,
                               UNInt32("len"),
                               Anchor("anchor_start"),
                               CString(name),
                               Anchor("anchor_offset"),
                               pad(),
                               extra), UNInt32("nr"))

def numa_topology():
    return PrefixedArray(Struct("node",
                                UNInt32("nodenr"),
                                UNInt64("mem_total"),
                                UNInt64("mem_free"),
                                str_with_len("cpus")),
                         UNInt32("nr"))

def group_desc():
    return string_list("group_desc",
                       Embedded(Struct(None,
                                       UNInt32("leader_idx"),
                                       UNInt32("nr_members"))))

def feature_bytes(name):
    return Struct(name,
                  UNInt64("offset"),
                  UNInt64("size"),
                  Pointer(lambda ctx: ctx.offset, Bytes("data", lambda ctx: ctx.size)))

def build_id():
    return Struct("build_id",
                  Anchor("anchor_start"),
                  UNInt32("type"),
                  UNInt16("misc"),
                  UNInt16("size"),
                  SNInt32("pid"),
                  HexDumpAdapter(String("build_id", 24)),
                  CString("filename"),
                  Anchor("anchor_offset"),
                  pad("size"))

def section_adapter(name, target):
    return perf_file_section(name,
                             TunnelAdapter(String("data",
                                                  lambda ctx: ctx.size),
                                           target))

def pmu_mappings():
    return PrefixedArray(Struct("pmu",
                                UNInt32("type"),
                                str_with_len("name")),
                         UNInt32("nr"))

def event_desc():
    return Struct("event_desc",
                  UNInt32("nr"),
                  UNInt32("attr_size"),
                  Array(lambda ctx: ctx.nr,
                        Struct("desc",
                               perf_event_attr,
                               UNInt32("nr_ids"),
                               str_with_len("event"),
                               Array(lambda ctx: ctx.nr_ids,
                                     UNInt64("id")))))

def perf_features():
    return Struct("features",
                  # XXX
                  If(lambda ctx: ctx._.tracing_data,
                     perf_file_section("tracing_data",
                                       Pass)),
                  If(lambda ctx: ctx._.build_id,
                     section_adapter("build_id",
                                     GreedyRange(build_id()))),
                  feature_string("hostname"),
                  feature_string("osrelease"),
                  feature_string("version"),
                  feature_string("arch"),
                  If(lambda ctx: ctx._.nrcpus,
                     perf_file_section("nrcpus",
                                       Embedded(Struct("nrcpus",
                                                UNInt32("nr_cpus_online"),
                                                UNInt32("nr_cpus_avail"))))),
                  feature_string("cpudesc"),
                  feature_string("cpuid"),
                  If(lambda ctx: ctx._.total_mem,
                     perf_file_section("total_mem",
                                       UNInt64("total_mem"))),
                  If(lambda ctx: ctx._.cmdline,
                     perf_file_section("cmdline",
                                       string_list("cmdline"))),
                  If(lambda ctx: ctx._.event_desc,
                     perf_file_section("event_desc",
                                       event_desc())),
                  If(lambda ctx: ctx._.cpu_topology,
                     perf_file_section("cpu_topology",
                                       Struct("cpu_topology",
                                              string_list("cores"),
                                              string_list("threads")))),
                  If(lambda ctx: ctx._.numa_topology,
                     perf_file_section("numa_topology",
                                       numa_topology())),
                  # not implemented in perf
                  If(lambda ctx: ctx._.branch_stack,
                     perf_file_section("branch_stack",
                                       Pass)),
                  If(lambda ctx: ctx._.pmu_mappings,
                     perf_file_section("pmu_mappings",
                                       pmu_mappings())),
                  If(lambda ctx: ctx._.group_desc,
                     perf_file_section("group_desc",
                                       group_desc())),
                  If(lambda ctx: ctx._.auxtrace,
                     feature_bytes("auxtrace")),
                  If(lambda ctx: ctx._.stat,
                     feature_bytes("stat")),
                  If(lambda ctx: ctx._.cache,
                     feature_bytes("cache")),
                  If(lambda ctx: ctx._.sample_time,
                     feature_bytes("sample_time")),
                  If(lambda ctx: ctx._.mem_tpology,
                     feature_bytes("mem_tpology")),
                  If(lambda ctx: ctx._.clock_id,
                     feature_bytes("clock_id")),
                  If(lambda ctx: ctx._.dir_format,
                     feature_bytes("dir_format")),
                  If(lambda ctx: ctx._.bpf_prog_info,
                     feature_bytes("bpf_prog_info")),
                  If(lambda ctx: ctx._.bpf_btf,
                     feature_bytes("bpf_btf")),
                  If(lambda ctx: ctx._.compressed,
                     feature_bytes("compressed")),
                  If(lambda ctx: ctx._.pmu_caps,
                     feature_bytes("pmu_caps")),
                  If(lambda ctx: ctx._.clock_data,
                     feature_bytes("clock_data")),
                  If(lambda ctx: ctx._.hybrid_topology,
                     feature_bytes("hybrid_topology")),
                  If(lambda ctx: ctx._.cpu_pmu_caps,
                     feature_bytes("cpu_pmu_caps")),)

def perf_file_section(name, target):
    return Struct(name,
                  UNInt64("offset"),
                  UNInt64("size"),
                  Pointer(lambda ctx: ctx.offset, target))

id_array = Array(lambda ctx: ctx.size / 8,
                 UNInt64("id"))

def num_attr(ctx):
    return ctx._.size / ctx._._.attr_size

perf_file_attr = Struct("perf_file_attr",
                        Array(lambda ctx: num_attr(ctx),
                              Struct("f_attr",
                                     perf_event_attr,
                                     perf_file_section("ids", id_array))))

perf_event_types = Struct("perf_file_attr",
                          Anchor("anchor_here"),
                          Padding(lambda ctx: ctx._.size))

perf_data = TunnelAdapter(Bytes("perf_data", lambda ctx: ctx.size),
                          GreedyRange(perf_event()))

#OnDemand(Bytes("perf_data", lambda ctx: ctx.size))

perf_file = Struct("perf_file_header",
                   # no support for version 1
                   Magic("PERFILE2"),
                   UNInt64("size"),
                   UNInt64("attr_size"),
                   perf_file_section("attrs", perf_file_attr),
                   perf_file_section("data", perf_data),
                   perf_file_section("event_types", perf_event_types),
                   # little endian
                   Embedded(BitStruct(None,
                             Flag("nrcpus"),
                             Flag("arch"),
                             Flag("version"),
                             Flag("osrelease"),
                             Flag("hostname"),
                             Flag("build_id"),
                             Flag("tracing_data"),
                             Flag("reserved"),

                             Flag("branch_stack"),
                             Flag("numa_topology"),
                             Flag("cpu_topology"),
                             Flag("event_desc"),
                             Flag("cmdline"),
                             Flag("total_mem"),
                             Flag("cpuid"),
                             Flag("cpudesc"),

                             Flag("clock_id"),
                             Flag("mem_tpology"),
                             Flag("sample_time"),
                             Flag("cache"),
                             Flag("stat"),
                             Flag("auxtrace"),
                             Flag("group_desc"),
                             Flag("pmu_mappings"),

                             Flag("pmu_caps"),
                             Flag("hybrid_topology"),
                             Flag("clock_data"),
                             Flag("cpu_pmu_caps"),
                             Flag("compressed"),
                             Flag("bpf_btf"),
                             Flag("bpf_prog_info"),
                             Flag("dir_format"),

                             Padding(256 - 4*8))),
                   Pointer(lambda ctx: ctx.data.offset + ctx.data.size,
                           perf_features()),)

def get_events(h):
    return h.data.perf_data

if __name__ == '__main__':
    import argparse

    args = argparse.ArgumentParser()
    args.add_argument('file', help='perf.data to read', default='perf.data',
                      nargs='?')
    p = args.parse_args()

    with open(p.file, "rb") as f:
        h = perf_file.parse_stream(f)
        print(h)
        #print(get_events(h))
