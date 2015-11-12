#ifndef JEVENTS_H
#define JEVENTS_H 1

#include <sys/types.h>

int json_events(const char *fn,
		int (*func)(void *data, char *name, char *event, char *desc,
			    char *pmu),
		void *data);
char *get_cpu_str(void);
char *get_cpu_str_type(char *type);

struct perf_event_attr;

int jevent_name_to_attr(char *str, struct perf_event_attr *attr);
int resolve_event(char *name, struct perf_event_attr *attr);
int read_events(char *fn);
int walk_events(int (*func)(void *data, char *name, char *event, char *desc),
		                void *data);
int walk_perf_events(int (*func)(void *data, char *name, char *event, char *desc),
		     void *data);
char *format_raw_event(struct perf_event_attr *attr, char *name);
int rmap_event(unsigned event, char **name, char **desc);

int perf_event_open(struct perf_event_attr *attr, pid_t pid,
		    int cpu, int group_fd, unsigned long flags);
char *resolve_pmu(int type);

#endif
