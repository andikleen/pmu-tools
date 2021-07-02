#ifndef JSESSION_H
#define JSESSION_H 1

#include <linux/perf_event.h>
#include <stdbool.h>
#include <stdint.h>
#include "jevents.h"

#ifdef __cplusplus
extern "C" {
#endif

struct event {
	struct event *next;
	struct perf_event_attr attr;
	char *event;
	bool end_group, group_leader, ingroup;
	bool uncore;
	struct event *orig;	/* Original event if cloned */
	int num_clones;		/* number of clones for this event */
	struct jevent_extra extra;
	struct efd {
		int fd;
		uint64_t val[3];
	} efd[0]; /* num_cpus */
};

struct eventlist {
	struct event *eventlist;
	struct event *eventlist_last;
	int num_cpus;
	int num_sockets;
	int *socket_cpus;
};

int parse_events(struct eventlist *el, char *events);
int setup_events(struct eventlist *el, bool measure_all, int measure_pid);
int setup_events_cpumask(struct eventlist *el, int measure_pid,
			 char *cpumask, int flags);
int setup_event(struct event *e, int cpu, struct event *leader, bool measure_all,
		int measure_pid);
int setup_event_flags(struct event *e, int cpu, struct event *leader, int measure_pid,
		      int flags);
#define SE_ENABLE_ON_EXEC (1 << 0)
#define SE_MEASURE_ALL    (1 << 1)

int read_event(struct event *e, int cpu);
int read_all_events(struct eventlist *el);
struct eventlist *alloc_eventlist(void);
uint64_t event_scaled_value(struct event *e, int cpu);
uint64_t event_scaled_value_sum(struct event *e, int cpu);
void free_eventlist(struct eventlist *el);
void print_event_list_attr(struct eventlist *el, FILE *f);

/**
 * struct session_print - Arguments for printing eventlists
 * @size:	size of session_print or 0 (for compatibility)
 * @sep:	separator string. Only used for CSV mode. Or NULL. Default ;
 * @prefix:	String prefix to print before output (e.g. timestamp).
 *		Needs to include separators. Or NULL.
 * @merge:	Merge identical events
 */
struct session_print {
	int size;	/* 0 or size for binary compatibility */
	char *sep;
	char *prefix;
	bool merge;
};

void session_print_csv(FILE *outfh, struct eventlist *el, struct session_print *arg);
void session_print_aggr(FILE *outfh, struct eventlist *el, struct session_print *arg);
void session_print(FILE *outfh, struct eventlist *el, struct session_print *arg);
void session_print_timestamp(char *buf, int bufs, double ts);
#define SESSION_TIMESTAMP_LEN 30

#ifdef __cplusplus
}
#endif

#endif
