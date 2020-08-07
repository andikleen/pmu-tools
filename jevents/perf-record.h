#ifndef PERF_RECORD_H
#define PERF_RECORD_H 1

#include <asm/types.h>
#include <linux/perf_event.h>

/*
 * Define the fixed size records (or fixed size initial portions) of the perf
 * record stream format. Many records are variable size based on the
 * configured read/sample formats.
 *
 * We define some common variants here, others will either more structures
 * or custom parsers.
 *
 * The actual reference for the records is linux/perf_event.h, but it only
 * defines the records in comments.
 *
 * Uptodate as of Linux 5.8
 */

struct perf_record_mmap {
	struct perf_event_header hdr; /* type == PERF_RECORD_MMAP */
	__u32			 pid;
	__u32			 tid;
	__u64			 len;
	__u64			 pgoff;
	char		         filename[]; /* variable length[len] */
	/* followed by variable length sample_id */
};

struct perf_record_lost {
	struct perf_event_header hdr; /* type == PERF_RECORD_LOST */
	__u64			 id;
	__u64			 lost;
	/* followed by variable length sample_id */
};

struct perf_record_comm {
	struct perf_event_header hdr; /* type == PERF_RECORD_COMM */
	__u32			 pid;
	__u32			 tid;
	char			 comm[]; /* variable length */
	/* followed by variable length sample_id */
};

struct perf_record_exit {
	struct perf_event_header hdr; /* type == PERF_RECORD_EXIT */
	__u32			 pid;
	__u32			 ppid;
	__u32			 tid;
	__u32			 ptid;
	__u64			 time;
	/* followed by variable length sample_id */
};

struct perf_record_throttle {
	struct perf_event_header hdr; /* type == PERF_RECORD_THROTTLE/UNTHROTTLE */
	__u64			 time;
	__u64			 id;
	__u64			 stream_id;
	/* followed by variable length sample_id */
};

struct perf_record_fork {
	struct perf_event_header hdr; /* type == PERF_RECORD_FORK */
	__u32			 pid, ppid;
	__u32			 tid, ptid;
	__u64			 time;
	/* followed by variable length sample_id */
};

/* perf_record_read depends on the read_format. Here are some common variants only */

/* PERF_FORMAT_TOTAL_TIME_ENABLED|PERF_FORMAT_TOTAL_TIME_RUNNING|PERF_FORMAT_ID */
struct perf_record_read_time_id {
	struct perf_event_header hdr; /* type == PERF_RECORD_READ */
	__u32			 pid;
	__u32			 tid;
	__u64			 value;
	__u64			 time_enabled;
	__u64			 time_running;
	__u64			 id;
	/* followed by variable length sample_id */
};

/* PERF_FORMAT_TOTAL_TIME_ENABLED|PERF_FORMAT_TOTAL_TIME_RUNNING|PERF_FORMAT_ID|PERF_FORMAT_GROUP */
struct perf_record_read_time_id_group {
	struct perf_event_header hdr; /* type == PERF_RECORD_READ */
	__u32			 pid;
	__u32			 tid;
	__u64			 nr;
	struct {
		__u64		 value;
		__u64		 time_enabled;
		__u64		 time_running;
		__u64		 id;
	} cntr[]; /* [nr] */
	/* followed by variable length sample_id */
};

/* perf_record_sample:
 * perf record sample is very complicated with many optional fields
 * depending on the sample_format.
 * We define just a few common variants. For others a custom structure
 * or a custom parser is needed.
 */

/* PERF_SAMPLE_IDENTIFIER|PERF_SAMPLE_IP */
struct perf_record_sample_ip {
	struct perf_event_header hdr; /* type == PERF_RECORD_SAMPLE */
	__u64			 id;
	__u64			 ip;
};

/* PERF_SAMPLE_IDENTIFIER|PERF_SAMPLE_IP|PERF_SAMPLE_TID|PERF_SAMPLE_TIME */
struct perf_record_sample_ip_tid_time {
	struct perf_event_header hdr; /* type == PERF_RECORD_SAMPLE */
	__u64			 id;
	__u64			 ip;
	__u64			 pid;
	__u64			 tid;
	__u64			 time;
};

/* PERF_SAMPLE_IDENTIFIER|PERF_SAMPLE_IP|PERF_SAMPLE_CPU|PERF_SAMPLE_TIME */
struct perf_record_sample_ip_cpu_time {
	struct perf_event_header hdr; /* type == PERF_RECORD_SAMPLE */
	__u64			 id;
	__u64			 ip;
	__u64			 cpu;
	__u64			 time;
};

/* PERF_SAMPLE_IDENTIFIER|PERF_SAMPLE_IP|PERF_SAMPLE_ADDR|PERF_SAMPLE_WEIGHT|PERF_SAMPLE_DATA_SRC */
struct perf_record_sample_ip_addr {
	struct perf_event_header hdr; /* type == PERF_RECORD_SAMPLE */
	__u64			 id;
	__u64			 ip;
	__u64			 addr;
	__u64			 weight;
	__u64			 data_src;
};

struct perf_sample_branch_stack {
	__u64 from;
	__u64 to;
	__u64 flags;
};

/* PERF_SAMPLE_IDENTIFIER|PERF_SAMPLE_IP|PERF_SAMPLE_CPU|PERF_SAMPLE_TIME|PERF_SAMPLE_BRANCH_STACK */
struct perf_record_sample_ip_cpu_branch {
	struct perf_event_header hdr; /* type == PERF_RECORD_SAMPLE */
	__u64			 ip;
	__u64			 cpu;
	__u64			 time;
	__u64			 nr;
	struct perf_sample_branch_stack lbr[]; /* [nr] */
};

/* PERF_SAMPLE_IDENTIFIER|PERF_SAMPLE_IP|PERF_SAMPLE_TID|PERF_SAMPLE_TIME|PERF_SAMPLE_CALLCHAIN */
struct perf_record_sample_ip_tid_callchain {
	struct perf_event_header hdr; /* type == PERF_RECORD_SAMPLE */
	__u64			 ip;
	__u64			 pid;
	__u64			 tid;
	__u64			 time;
	__u64			 nr;
	__u64			 ips[]; /* [nr] */
};

/* PERF_SAMPLE_IDENTIFIER|PERF_SAMPLE_IP|PERF_SAMPLE_TID|PERF_SAMPLE_TIME|PERF_SAMPLE_CALLCHAIN */
struct perf_record_sample_ip_tid_regs {
	struct perf_event_header hdr; /* type == PERF_RECORD_SAMPLE */
	__u64			 ip;
	__u64			 pid;
	__u64			 tid;
	__u64			 time;
	__u64			 abi;
	__u64			 regs[]; /* [weight(mask)] */
};

/* PERF_SAMPLE_IDENTIFIER|PERF_SAMPLE_IP|PERF_SAMPLE_TID|PERF_SAMPLE_TIME|PERF_SAMPLE_READ */
/* PERF_FORMAT_TOTAL_TIME_ENABLED|PERF_FORMAT_TOTAL_TIME_RUNNING|PERF_FORMAT_ID|PERF_FORMAT_GROUP */
struct perf_record_sample_ip_tid_regs_group {
	struct perf_event_header hdr; /* type == PERF_RECORD_SAMPLE */
	__u64			 ip;
	__u64			 pid;
	__u64			 tid;
	__u64			 time;
	__u64			 nr;
	struct {
		__u64		 value;
		__u64		 time_enabled;
		__u64		 time_running;
		__u64		 id;
	} cntr[]; /* [nr] */
};

struct perf_record_mmap2 {
	struct perf_event_header hdr; /* type == PERF_RECORD_MMAP2 */
	__u32			 pid;
	__u32			 tid;
	__u64			 addr;
	__u64			 len;
	__u64			 pgoff;
	__u32			 maj;
	__u32			 min;
	__u64			 ino;
	__u64			 ino_generation;
	__u32			 prot;
	__u32			 flags;
	char			 filename[]; /* variable length */
	/* followed by variable length sample_id */
};

struct perf_record_itrace_start {
	struct perf_event_header hdr; /* type == PERF_RECORD_ITRACE_START */
	__u32			 pid;
	__u32			 tid;
	/* followed by variable length sample_id */
};

struct perf_record_aux {
	struct perf_event_header hdr; /* type == PERF_RECORD_AUX */
	__u64    aux_offset;
	__u64    aux_size;
	__u64    flags;
	/* followed by variable length sample_id */
};

struct perf_record_lost_samples {
	struct perf_event_header hdr; /* type == PERF_RECORD_LOST_SAMPLES */
	__u64			 lost;
	/* followed by variable length sample_id */
};

struct perf_record_switch {
	struct perf_event_header hdr; /* type == PERF_RECORD_SWITCH */
	/* followed by variable length sample_id */
};

struct perf_record_switch_cpu_wide {
	struct perf_event_header hdr; /* type == PERF_RECORD_SWITCH_CPU_WIDE */
	__u32			 next_prev_pid;
	__u32			 next_prev_tid;
	/* followed by variable length sample_id */
};

struct perf_namespace {
	__u64			dev;
	__u64			inode;
};

struct perf_record_namespaces {
	struct perf_event_header hdr; /* type == PERF_RECORD_NAMESPACES */
	__u32			 pid;
	__u32			 tid;
	__u64			 nr_namespaces;
	struct perf_namespace    name_spaces[]; /* [nr_namespaces] */
	/* followed by variable length sample_id */
};

struct perf_record_ksymbol {
	struct perf_event_header hdr; /* type == PERF_RECORD_KSYMBOL */
	__u64			 addr;
	__u32			 len;
	__u16			 ksym_type;
	__u16			 flags;
	char			 name[]; /* variable length */
	/* followed by variable length sample_id */
};

#define BPF_TAG_SIZE 8

struct perf_record_bpf_event {
	struct perf_event_header hdr; /* type == PERF_RECORD_BPF_EVENT */
	__u16			 type; /* PERF_BPF_EVENT_* below */
	__u16			 flags;
	__u32			 id;
	__u8			 tag[BPF_TAG_SIZE];
	/* followed by variable length sample_id */
};

#define PERF_BPF_EVENT_UNKNOWN 0
#define PERF_BPF_EVENT_PROG_LOAD 1
#define PERF_BPF_EVENT_PROG_UNLOAD 2

struct perf_record_cgroup {
	struct perf_event_header hdr; /* type == PERF_RECORD_CGROUP */
	__u64			 id;
	char			 path[]; /* variable length */
	/* followed by variable length sample_id */
};

#endif
