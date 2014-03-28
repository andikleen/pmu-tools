/* Caching layer to resolve events without re-reading them */
#include "jevents.h"
#include <stdlib.h>
#include <string.h>
#include <linux/perf_event.h>

/**
 * DOC: Resolve named Intel performance events to perf
 *
 * This library allows to resolve named Intel performance counter events
 * (for example INST_RETIRED.ANY)
 * by name and turn them into perf_event_attr attributes.
 *
 * The standard workflow is the user calling "event_download.py"
 * or "perf download" to download the current list, and then
 * these functions can resolve or walk names.
 */
 
struct event {
	struct event *next;
	char *name;
	char *desc;
	char *event;
};

/* Could add a hash table, but right now expected accesses are not frequent */
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

static void free_events(void)
{
	struct event *e, *next;

	for (e = eventlist; e; e = next) {
		next = e->next;
		free(e);
	}
	eventlist = NULL;
}

/**
 * read_events - Read JSON performance counter event list
 * @fn: File name to read. NULL to chose default location.
 *
 * Read the JSON event list fn. The other functions in the library
 * automatically read the default event list for the current CPU,
 * but calling this explicitly is useful to chose a specific one.
*
 * Return: -1 on failure, otherwise 0.
 */
int read_events(char *fn)
{
	if (eventlist)
		free_events();
	return json_events(NULL, collect_events, NULL);
}

/**
 * resolve_event - Resolve named performance counter event
 * @name: Name of performance counter event (case in-sensitive)
 * @attr: perf_event_attr to initialize with name.
 *
 * The attr structure is cleared initially.
 * The user typically has to set up attr->sample_type/read_format
 * _after_ this call.
 * Return: -1 on failure, otherwise 0.
 */

int resolve_event(char *name, struct perf_event_attr *attr)
{
	struct event *e;
	if (!eventlist)
		read_events(NULL);
	for (e = eventlist; e; e = e->next) {
		if (!strcasecmp(e->name, name)) {
			return jevent_name_to_attr(e->event, attr);
		}
	}
	return -1;
}

/**
 * walk_events - Walk all the available performance counter events
 * @func: Callback to call on each event.
 * @data: Abstract data pointer to pass to callback.
 *
 * The callback gets passed the data argument, the name of the 
 * event, the translated event in perf form (cpu/.../) and a 
 * description of the event.
 *
 * Return: -1 on failure, otherwise 0.
 */

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
