int json_events(const char *fn,
		int (*func)(void *data, char *name, char *event, char *desc),
		void *data);
char *get_cpu_str(void);

struct perf_event_attr;

int jevent_name_to_attr(char *str, struct perf_event_attr *attr);
int resolve_event(char *name, struct perf_event_attr *attr);
int read_events(char *fn);
int walk_events(int (*func)(void *data, char *name, char *event, char *desc),
		                void *data);


