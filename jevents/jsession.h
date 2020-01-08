#ifndef JSESSION_H
#define JSESSION_H 1

#include <linux/perf_event.h>
#include <stdbool.h>
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
int setup_events_cpumask(struct eventlist *el, bool measure_all, int measure_pid,
			 char *cpumask, bool enable_on_exec);
int setup_event(struct event *e, int cpu, struct event *leader, bool measure_all,
		int measure_pid, bool enable_on_exec);
int read_event(struct event *e, int cpu);
int read_all_events(struct eventlist *el);
struct eventlist *alloc_eventlist(void);
uint64_t event_scaled_value(struct event *e, int cpu);
void free_eventlist(struct eventlist *el);
void print_event_list_attr(struct eventlist *el, FILE *f);

#ifdef __cplusplus
}
#endif

#endif
