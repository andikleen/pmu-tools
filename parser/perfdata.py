#!/usr/bin/python
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
# read_format?
# 

from construct import *

def sample_type(ctx):
    return ctx.attr.perf_event_attr.sample_type

def sample_id_size(ctx):
    st = sample_type(ctx)
    return (st.tid + st.time + st.id + st.stream_id + st.cpu +
            st.identifier) * 8

def sample_id():
    return If(lambda ctx: True, # xxx check size
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

def throttle(name):
    return Struct(name,
                  UNInt64("time"),
                  UNInt64("id"),
                  UNInt64("stream_id"),
                  sample_id())

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
                #If(lambda ctx: ctx.attr.sample_type.read,
                #   read_format()),
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
                                                 Padding(64 - 1*8)))))),
                If(lambda ctx: sample_type(ctx).regs_user,
                   Struct("regs_user",
                          Enum(UNInt64("abi"),
                               NONE = 0,
                               ABI_32 = 1,
                               ABI_64 = 2),
                          Array(lambda ctx: sample_regs_user,
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
                Anchor("end_event"),
                Padding(lambda ctx: max(0, ctx.size - ctx.end_event))))

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
    if "end_id" in ctx and ctx.end_id:
        idx = ctx.end_id
    elif 'id' in ctx and ctx['id']:
        idx = ctx['id']
    else:
        idx = 0
    return get_attr_list(ctx)[idx]

# XXX need to make OnDemand for large files

def perf_event_header():
    return Embedded(Struct(None,
                           Enum(UNInt32("type"),
                                MMAP			= 1,
                                LOST			= 2,
                                COMM			= 3,
                                EXIT			= 4,
                                THROTTLE		= 5,
                                UNTHROTTLE		= 6,
                                FORK			= 7,
                                READ			= 8,
                                SAMPLE			= 9),
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
                                 Pointer(lambda ctx: ctx.start + ctx.size - 8,
                                   UNInt64("end_id"))),
                           Value("attr", lookup_event_attr)))

def PaddedCString(name):
    return Embedded(Struct(name,
                           Anchor("sstart"),
                           CString(name),
                           Anchor("send"),
                           Padding(lambda ctx:
                                       8 - ((ctx.send - ctx.sstart) % 8))))

def mmap():
    return Struct("mmap",
                  SNInt32("pid"),
                  SNInt32("tid"),
                  UNInt64("addr"),
                  UNInt64("len"),
                  UNInt64("pgoff"),
                  Anchor("start_of_filename"),
                  CString("filename"),
                  Anchor("end_of_filename"),
                  # hack for now. this shouldn't be needed.
                  If(lambda ctx: True, # XXX
                     Embedded(Pointer(lambda ctx: 
                                      ctx.size + ctx.start - 
                                      sample_id_size(ctx),
                                      sample_id()))))

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

def perf_event():
    return Struct("perf_event",
                  Anchor("start"),
                  perf_event_header(),
                  Anchor("header_end"),
                  Switch("data",
                           lambda ctx: ctx.type,
                           {
                              "MMAP": mmap(),
                              "LOST": Struct("lost",
                                              UNInt64("id"),
                                              UNInt64("lost"),
                                             sample_id()),
                              "COMM": Struct("comm",
                                             SNInt32("pid"),
                                             SNInt32("tid"),
                                             PaddedCString("comm"),
                                             sample_id()),
                              "EXIT": fork_exit("exit"),
                              "THROTTLE": throttle("throttle"),
                              "UNTHROTTLE": throttle("unthrottle"),
                              "FORK": fork_exit("fork"),
                              "READ": Embedded(Struct("read_event",
                                                      SNInt32("pid"),
                                                      SNInt32("tid"),
                                                      read_format(),
                                                      sample_id())),
                              "SAMPLE": event()
                           }),
			Anchor("end"),
			Padding(lambda ctx:
                                    ctx.size - (ctx.end - ctx.start)))

def perf_event_seq(attr):
    return GreedyRange(perf_event(attr))

perf_event_attr_sizes = (64, 72, 80, 96)

perf_event_attr = Struct("perf_event_attr",
                         Anchor("start"),                         
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
                                   
                                   Padding(7),
                                   Flag("identifier"),

                                   Padding(64 - 3*8)),
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
                         Anchor("end"),
                         Value("perf_event_attr_size",
                               lambda ctx: ctx.end - ctx.start),
                         Padding(lambda ctx: ctx.size - ctx.perf_event_attr_size))

def pad(l = "len"):
    return Padding(lambda ctx: ctx[l] - (ctx.offset - ctx.start))

def str_with_len(name):
    return Struct(name,
                  UNInt32("len"),
                  Anchor("start"),
                  CString(name),
                  Anchor("offset"),
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
                               Anchor("start"),
                               CString(name),
                               Anchor("offset"),
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

def build_id():
    return Struct("build_id",
                  Anchor("start"),
                  UNInt32("type"),
                  UNInt16("misc"),
                  UNInt16("size"),
                  SNInt32("pid"),
                  HexDumpAdapter(String("build_id", 24)),
                  CString("filename"),
                  Anchor("offset"),
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
                                       group_desc())))

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
                          Anchor("here"),
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

                             Padding(6),
                             Flag("group_desc"),
                             Flag("pmu_mappings"),

                             Padding(256 - 3*8))),
                   Pointer(lambda ctx: ctx.data.offset + ctx.data.size,
                           perf_features()),
                   Padding(3 * 8))

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
        print h
        #print get_events(h)

