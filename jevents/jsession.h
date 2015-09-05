#ifndef JSESSION_H
#define JSESSION_H 1

#include <linux/perf_event.h>
#include <stdbool.h>


struct event {
	struct event *next;
	struct perf_event_attr attr;
	char *event;
	bool end_group, group_leader;
	struct efd {
		int fd;
		uint64_t val[3];
	} efd[0]; /* num_cpus */
};

struct eventlist {
	struct event *eventlist;
	struct event *eventlist_last;
	int num_cpus;
};

int parse_events(struct eventlist *el, char *events);
int setup_events(struct eventlist *el, bool measure_all, int measure_pid);
int setup_event(struct event *e, int cpu, struct event *leader, bool measure_all, int measure_pid);
int read_event(struct event *e, int cpu);
int read_all_events(struct eventlist *el);
struct eventlist *alloc_eventlist(void);
uint64_t event_scaled_value(struct event *e, int cpu);

#endif
