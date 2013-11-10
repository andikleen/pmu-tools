#!/usr/bin/python
# A description of the perf.data file format in "construct"
#
# Only works on Little-Endian with LE input files. Sorry.
#
from construct import *

def fork_exit(name): 
    return Struct(name,
                  SNInt32("pid"),
                  SNInt32("ppid"),
                  SNInt32("tid"),
                  SNInt32("ptid"),
                  UNInt64("time"))

def throttle(name):
    return Struct(name,
                  UNInt64("time"),
                  UNInt64("id"),
                  UNInt64("stream_id"))

def event(sample_type, read_format, sample_regs_user):
    return Embedded(
         Struct("event",
                If(lambda ctx: sample_type.identifier,
                   UNInt64("identifier")),
                If(lambda ctx: sample_type.ip,
                   UNInt64("ip")),
                If(lambda ctx: sample_type.tid,
                   Struct("tid",
                          SNInt32("pid"),
                          SNInt32("tid"))),
                If(lambda ctx: sample_type.time,
                   UNInt64("time")),
                If(lambda ctx: sample_type.addr,
                   UNInt64("addr")),
                If(lambda ctx: sample_type.id,
                   UNInt64("id")),
                If(lambda ctx: sample_type.stream_id,
                   UNInt64("stream_id")),
                If(lambda ctx: sample_type.cpu,
                   Struct("cpu",
                          UNInt32("cpu"),
                          UNInt32("res"))),
                If(lambda ctx: sample_type.period,
                   UNInt64("period")),
                # XXX
                #If(lambda ctx: sample_type.read,
                #   read_format(rformat)),
                If(lambda ctx: sample_type.callchain,
                   Struct("callchain",
                          UNInt64("nr"),
                          Array(lambda ctx: ctx.nr,
                                UNInt64("addr")))),
                If(lambda ctx: sample_type.raw,
                   Struct("raw",
                          UNInt32("size"),
                          Bytes("raw", lambda ctx: ctx.size))),
                If(lambda ctx: sample_type.branch_stack,
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
                If(lambda ctx: sample_type.regs_user,
                   Struct("regs_user",
                          Enum(UNInt64("abi"),
                               NONE = 0,
                               ABI_32 = 1,
                               ABI_64 = 2),
                          Array(lambda ctx: sample_regs_user,
                                UNInt64("reg")))),
                If(lambda ctx: sample_type.stack_user,
                   Struct("stack_user", 
                          UNInt64("size"),
                          Bytes("data", lambda ctx: ctx.size),
                          UNInt64("dyn_size"))),
                If(lambda ctx: sample_type.weight,
                   UNInt64("weight")),
                If(lambda ctx: sample_type.data_src,
                   UNInt64("data_src")),
                Anchor("end_event"),
                Padding(lambda ctx: max(0, ctx.size - ctx.end_event))))

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
                           UNInt16("size")))

def perf_event(sample_type, read_format, sample_regs_user):         
    return Struct("perf_event",
                  Anchor("start"),
                  perf_event_header(),
                  Switch("data",
                           lambda ctx: ctx.type,
                           {
                              "MMAP": Struct("mmap",
                                              SNInt32("pid"),
                                              SNInt32("tid"),
                                              UNInt64("addr"),
                                              UNInt64("len"),
                                              UNInt64("pgoff"),
                                                CString("filename")),
                              "LOST": Struct("lost",
                                              UNInt64("id"),
                                              UNInt64("lost")),
                              "COMM": Struct("comm",
                                             SNInt32("pid"),
                                             SNInt32("tid"),
                                             CString("comm")),
                              "EXIT": fork_exit("exit"),
                              "THROTTLE": throttle("thottle"),
                              "UNTHROTTLE": throttle("unthottle"),
                              "FORK": fork_exit("fork"),
                              #"READ": read_format(read_format),
                              "SAMPLE": event(sample_type, read_format, 
                                              sample_regs_user),
                           }),
			Anchor("end"),
			Padding(lambda ctx:
                                    ctx.size - (ctx.end - ctx.start)))

def perf_event_seq(sample_type, read_format, sample_regs_user):
    return GreedyRange(perf_event(sample_type, read_format, sample_regs_user))


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
                         Value("perf_event_attr_size", lambda ctx: ctx.end - ctx.start),
                         Padding(lambda ctx: ctx.size - ctx.perf_event_attr_size))

def pad():
    return Padding(lambda ctx: ctx.len - (ctx.offset - ctx.start))

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
                                Struct(name,
                                       UNInt32("len"),
                                       CString(name))))

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

def perf_features():
    return Struct("features",
                  If(lambda ctx: ctx._.tracing_data,
                     perf_file_section("tracing_data",
                                       Pass)),
                  If(lambda ctx: ctx._.build_id,
                     perf_file_section("build_id",
                                       # FIXME array
                                       Struct("build_id",
                                              UNInt32("type"),
                                              UNInt16("misc"),
                                              UNInt16("size"),
                                              SNInt32("pid"),
                                              Bytes("build_id", 20),
                                              CString("filename")))),
                  feature_string("hostname"),
                  feature_string("osrelease"),
                  feature_string("version"),
                  feature_string("arch"),
                  If(lambda ctx: ctx._.nrcpus,
                     perf_file_section("nrcpus",
                                       Struct("nrcpus",
                                              UNInt32("nr_cpus_online"),
                                              UNInt32("nr_cpus_avail")))),
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
                                       Pass)),                           
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
                                       Pass)),
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

perf_data = OnDemand(Bytes("perf_data", lambda ctx: ctx.size))

perf_file = Struct("perf_file_header",
                   # no support for version 1
                   Magic("PERFILE2"),
                   UNInt64("size"),
                   UNInt64("attr_size"),
                   perf_file_section("attrs", perf_file_attr),
                   perf_file_section("data", perf_data),
                   perf_file_section("event_types", perf_event_types),
                   # XXX decoders for all of these
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

                             Padding(64 - 3*8))),
                   Pointer(lambda ctx: ctx.data.offset + ctx.data.size,
                           perf_features()),
                   Padding(3 * 8))

def get_events(h):
    data = h.data.perf_data.value
    # assumes event 0 attributes applies to all samples?
    ev0 = h.attrs.perf_file_attr.f_attr[0].perf_event_attr
    assert ev0.size in perf_event_attr_sizes
    return perf_event_seq(ev0.sample_type, ev0.read_format, ev0.sample_regs_user).parse(data)

if __name__ == '__main__':
    import sys
    
    with open(sys.argv[1], "rb") as f:
        h = perf_file.parse_stream(f)
        print h
        print get_events(h)

