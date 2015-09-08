/* List all events */
/* -v print descriptions */
/* pattern  print only events matching shell pattern */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fnmatch.h>
#include <assert.h>
#include "jevents.h"

int verbose = 0;

struct event {
	char *name;
	char *event;
	char *desc;
};

struct walk_data {
	int count;
	int ind;
	char *match;
	struct event *events;
};

static int count_event(void *data, char *name, char *event, char *desc)
{
	struct walk_data *wd = data;
	if (wd->match && fnmatch(wd->match, name, 0))
		return 0;
	wd->count++;
	return 0;
}

static int store_event(void *data, char *name, char *event, char *desc)
{
	struct walk_data *wd = data;

	if (wd->match && fnmatch(wd->match, name, 0))
		return 0;
	assert(wd->ind < wd->count);
	struct event *e = &wd->events[wd->ind++];
	e->name = strdup(name);
	e->event = strdup(event);
	e->desc = strdup(desc);
	return 0;
}

static int cmp_events(const void *ap, const void *bp)
{
	const struct event *a = ap;
	const struct event *b = bp;
	return strcmp(a->name, b->name);
}

int main(int ac, char **av)
{
	if (av[1] && !strcmp(av[1], "-v")) {
		av++;
		verbose = 1;
	}

	read_events(NULL);
	struct walk_data wd = { .match = av[1] };
	walk_events(count_event, &wd);
	walk_perf_events(count_event, &wd);
	wd.events = calloc(sizeof(struct event), wd.count);
	walk_events(store_event, &wd);
	walk_perf_events(store_event, &wd);
	qsort(wd.events, wd.count, sizeof(struct event), cmp_events);
	int i;
	for (i = 0; i < wd.count; i++) {
		struct event *e = &wd.events[i];
		printf("%-40s ", e->name);
		printf("%s\n", e->event);
		if (verbose && e->desc[0])
			printf("\t%s\n", e->desc); /* XXX word wrap */
	}
	return 0;
}
