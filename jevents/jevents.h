#ifndef JEVENTS_H
#define JEVENTS_H 1

#include <sys/types.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

int json_events(const char *fn,
		int (*func)(void *data, char *name, char *event, char *desc,
			    char *pmu),
		void *data);
char *get_cpu_str(void);
char *get_cpu_str_type(char *type, char **idstr_step);

struct perf_event_attr;

int jevent_name_to_attr(const char *str, struct perf_event_attr *attr);
int resolve_event(const char *name, struct perf_event_attr *attr);
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
bool jevent_pmu_uncore(const char *str);

#ifdef __cplusplus
}
#endif

#endif
