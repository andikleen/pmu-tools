#include "jevents.h"
#include <stdlib.h>
#include <string.h>
#include <linux/perf_event.h>

struct event {
	struct event *next;
	char *name;
	char *desc;
	char *event;
};

static struct event *eventlist;

static int collect_events(void *data, char *name, char *event, char *desc)
{
	struct event *e = malloc(sizeof(struct event));
	e->next = eventlist;
	eventlist = e;
	e->name = strdup(name);
	e->desc = strdup(desc);
	e->event = strdup(event);
	return 0;
}

void read_events(char *fn)
{
	json_events(NULL, collect_events, NULL);
}

int resolve_event(char *name, struct perf_event_attr *attr)
{
	struct event *e;
	if (!eventlist)
		read_events(NULL);
	for (e = eventlist; e; e = e->next) {
		if (!strcmp(e->name, name)) {
			return jevent_name_to_attr(e->event, attr);
		}
	}
	return -1;
}

int walk_events(int (*func)(void *data, char *name, char *event, char *desc),
		void *data)
{
	struct event *e;
	if (!eventlist)
		read_events(NULL);
	for (e = eventlist; e; e = e->next) {
		int ret = func(data, e->name, e->event, e->desc);
		if (ret)
			return ret;
	}
	return 0;
}
