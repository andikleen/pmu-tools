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

def event(sample_type, read_format):
    return Embedded(
         Struct("event",
                If(lambda ctx: sample_type.identifier,
                   UNInt64("id")),
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
                # both need parameters passed in
                # sample reg
                # stack user
                If(lambda ctx: sample_type.weight,
                   UNInt64("weight")),
                If(lambda ctx: sample_type.data_src,
                   UNInt64("data_src")),
                Anchor("end_event"),
                Padding(lambda ctx: max(0, ctx.size - ctx.end_event))))

# XXX need to make OnDemand for large files

def perf_event(sample_type, read_format):         
    return Struct("perf_event",
                    Anchor("start"),
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
                    UNInt16("misc"),
                    UNInt16("size"),
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
                              "SAMPLE": event(sample_type, read_format),
                           }),
			Anchor("end"),
			Padding(lambda ctx: ctx.size - (ctx.end - ctx.start))
                    )

def perf_event_seq(sample_type, read_format):
    return GreedyRange(perf_event(sample_type, read_format))


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
                         BitStruct(None,
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
                                            Padding(41)),
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

# assumes all attributes are the same size

perf_file_attr = Struct("perf_file_attr",
                        Peek(Embedded(Struct(None, UNInt32("type"), UNInt32("size")))),
                        Array(lambda ctx: ctx._.size / ctx.size, perf_event_attr))

perf_event_types = Struct("perf_file_attr",
                          Anchor("here"),
                          Padding(lambda ctx: ctx._.size))

perf_data = OnDemand(Bytes("perf_data", lambda ctx: ctx.size))
                             
def perf_file_section(name, target):
    return Struct(name,
                  UNInt64("offset"),
                  UNInt64("size"),
                  Pointer(lambda ctx: ctx.offset, target))

perf_file = Struct("perf_file_header",
                   UNInt64("magic"), # XXX
                   UNInt64("size"),
                   UNInt64("attr_size"),
                   perf_file_section("attrs", perf_file_attr),
                   perf_file_section("data", perf_data),
                   perf_file_section("event_types", perf_event_types),
                   BitStruct("adds_features",
                             Flag("tracing_data"),
                             Flag("build_id"),
                             Flag("hostname"),
                             Flag("osrelease"),
                             Flag("version"),
                             Flag("arch"),
                             Flag("nrcpus"),
                             Flag("cpudesc"),
                             Flag("cpuid"),
                             Flag("total_mem"),
                             Flag("cmdline"),
                             Flag("event_desc"),
                             Flag("cpu_topology"),
                             Flag("numa_topology"),
                             Flag("branch_stack"),
                             Flag("pmu_mappings"),
                             Flag("group_desc"),
                             Padding(64 - 17)),
                   Padding(3 * 8))

def get_events(h):
    data = h.data.perf_data.value
    # assumes event 0 attributes applies to all samples?
    # XXX
    ev0 = h.attrs.perf_file_attr.perf_event_attr[0]
    assert ev0.size in perf_event_attr_sizes
    return perf_event_seq(ev0.sample_type, ev0.read_format).parse(data)

if __name__ == '__main__':
    import sys
    
    with open(sys.argv[1], "rb") as f:
        h = perf_file.parse_stream(f)
        print h
        print get_events(h)

