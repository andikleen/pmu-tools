/* Caching layer to resolve events without re-reading them */

/*
 * Copyright (c) 2014, Intel Corporation
 * Author: Andi Kleen
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 * this list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright
 * notice, this list of conditions and the following disclaimer in the
 * documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 * COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
 * INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
*/

#define _GNU_SOURCE 1
#include "jevents.h"
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <errno.h>
#include <stdio.h>
#include <ctype.h>
#include <linux/perf_event.h>

/**
 * DOC: Resolve named Intel performance events to perf
 *
 * This library allows to resolve named Intel performance counter events
 * (for example INST_RETIRED.ANY)
 * by name and turn them into perf_event_attr attributes. It also
 * supports listing all events and resolving numeric events back to names.
 *
 * The standard workflow is the user calling "event_download.py"
 * to download the current list, and then
 * these functions can resolve or walk names. Alternatively
 * a JSON event file from https://download.01.org/perfmon
 * can be specified through the EVENTMAP= environment variable.
 */

struct event {
	struct event *next;
	char *name;
	char *desc;
	char *event;
	char *pmu;
};

#define HASHSZ 37

static struct event *eventlist[HASHSZ];
static bool eventlist_init;

/* Weinberg's identifier hash */
static unsigned hashfn(const char *s, int len)
{
	unsigned h = 0;
	while (*s && len--) {
		int c = tolower(*s);
		s++;
		h = h * 67 + (c - 113);
	}
	return h % HASHSZ;
}

static int collect_events(void *data, char *name, char *event, char *desc,
			  char *pmu)
{
	unsigned h = hashfn(name, strlen(name));
	struct event *e = malloc(sizeof(struct event));
	if (!e)
		exit(ENOMEM);
	e->next = eventlist[h];
	eventlist[h] = e;
	e->name = strdup(name);
	e->desc = strdup(desc);
	e->event = strdup(event);
	e->pmu = strdup(pmu);
	return 0;
}

static void free_events(void)
{
	struct event *e, *next;
	int i;
	for (i = 0; i < HASHSZ; i++) {
		for (e = eventlist[i]; e; e = next) {
			next = e->next;
			free(e->name);
			free(e->desc);
			free(e->event);
			free(e->pmu);
			free(e);
		}
		eventlist[i] = NULL;
	}
	eventlist_init = false;
}

/**
 * read_events - Read JSON performance counter event list
 * @fn: File name to read. NULL to chose default location.
 *
 * Read the JSON event list fn. The other functions in the library
 * automatically read the default event list for the current CPU,
 * but calling this explicitly is useful to chose a specific one.
 *
 * This function is not thread safe and should not be called
 * from multiple threads in parallel. However once it is called
 * once all other functions are thread-safe. So for multi-threaded
 * use the main thread should call it once before other threads.
 *
 * Return: -1 on failure, otherwise 0.
 */
int read_events(const char *fn)
{
	if (eventlist_init) {
		// treat subsequent read_events calls after the first as replacing the
		// event list
		free_events();
	}
	eventlist_init = true;
	/* ??? free on error */
	return json_events(fn, collect_events, NULL);
}

static struct fixed {
	char *name;
	char *event;
} fixed[] = {
	{ "inst_retired.any", "event=0xc0" },
	{ "cpu_clk_unhalted.thread", "event=0x3c" },
	{ "cpu_clk_unhalted.thread_any", "event=0x3c,any=1" },
	{},
};

/*
 * Handle different fixed counter encodings between JSON and perf.
 */
static char *real_event(char *name, char *event, int nlen)
{
	int i;
	for (i = 0; fixed[i].name; i++)
		if (!strncasecmp(name, fixed[i].name, nlen))
			return fixed[i].event;
	return event;
}

/**
 * resolve_event_extra - Resolve named performance counter event
 * @name: Name of performance counter event (case in-sensitive)
 * @attr: perf_event_attr to initialize with name.
 * @extra: Extra structure to fill in, or 0. When passed its content
 * have to be freed with jevent_free_extra()
 *
 * The attr structure is cleared initially.
 * The user typically has to set up attr->sample_type/read_format
 * _after_ this call.
 * Note this function is only thread-safe when read_events() has
 * been called first single-threaded.
 * When extra is passed and no error happens extra must be freed
 * later with jevent_free_extra()
 * Return: -1 on failure, otherwise 0.
 *
 * Some events may need multiple PMUs. In this case extra->multi_pmu
 * is set, and jevent_next_pmu() must be used to iterate the attr
 * through the extra PMUs.
 *
 * The decoded event in perf format is in extra->decoded
 */

int resolve_event_extra(const char *name, struct perf_event_attr *attr,
			struct jevent_extra *extra)
{
	struct event *e;
	char *buf;
	int ret;
	int nlen = strcspn(name, ":");
	unsigned h = hashfn(name, nlen);
	struct jevent_extra extras;

	if (!eventlist_init) {
		if (read_events(NULL) < 0)
			return -1;
	}
	if (!extra)
		extra = &extras;
	for (e = eventlist[h]; e; e = e->next) {
		if (!strncasecmp(e->name, name, nlen)) {
			char *event = real_event(e->name, e->event, nlen);
			char *s;

			asprintf(&buf, "%s/%s/%s", e->pmu, event, name + nlen + (name[nlen] ? 1 : 0));
			for (s = buf; *s; s++) {
				if (*s == ':')
					*s = ',';
			}
			ret = jevent_name_to_attr_extra(buf, attr, extra);
			extra->decoded = buf;
			if (ret && (extra == &extras)) {
				jevent_free_extra(extra);
			}
			return ret;
		}
	}
	/* Try a perf style event */
	if (jevent_name_to_attr_extra(name, attr, extra) == 0) {
		if (extra != &extras)
			extra->decoded = strdup(name);
		return 0;
	}
	asprintf(&buf, "cpu/%s/", name);
	ret = jevent_name_to_attr_extra(buf, attr, extra);
	extra->decoded = buf;
	if (extra == &extras || ret) {
		free(buf);
		extra->decoded = NULL;
	}
	if (ret == 0)
		return ret;
	return -1;
}

/**
 * resolve_event - Resolve named performance counter event
 * @name: Name of performance counter event (case in-sensitive)
 * @attr: perf_event_attr to initialize with name.
 *
 * The attr structure is cleared initially.
 * The user typically has to set up attr->sample_type/read_format
 * _after_ this call.
 * Note this function is only thread-safe when read_events() has
 * been called first single-threaded.
 * Return: -1 on failure, otherwise 0.
 *
 * Deprecated. Should migrate to resolve_event_extra
 */

int resolve_event(const char *name, struct perf_event_attr *attr)
{
	return resolve_event_extra(name, attr, NULL);
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
	if (!eventlist_init) {
		if (read_events(NULL) < 0)
			return -1;
	}
	int i;
	for (i = 0; i < HASHSZ; i++) {
		for (e = eventlist[i]; e; e = e->next) {
			char *buf;
			asprintf(&buf, "%s/%s/", e->pmu, e->event);
			int ret = func(data, e->name, buf, e->desc);
			free(buf);
			if (ret)
				return ret;
		}
	}
	return 0;
}

/**
 * rmap_event - Map numeric event back to name and description.
 * @target:  Event code to match (umask + event).
 * @name: Put pointer to event name into this. No need to free.
 * @desc: Put pointer to description into this. No need to free. Can be NULL.
 *
 * Offcore matrix events are not fully supported.
 * Ignores bits other than umask/event for now, so some events using cmask,inv
 * may be misidentified. May be slow.
 * Return: -1 on failure, otherwise 0.
 */

int rmap_event(unsigned target, char **name, char **desc)
{
	struct event *e;
	if (!eventlist_init) {
		if (read_events(NULL) < 0)
			return -1;
	}
	int i;
	for (i = 0; i < HASHSZ; i++) {
		for (e = eventlist[i]; e; e = e->next) {
			// XXX should cache the numeric value
			char *s;
			unsigned event = 0, umask = 0;
			s = strstr(e->event, "event=");
			if (s)
				sscanf(s, "event=%x", &event);
			s = strstr(e->event, "umask=");
			if (s)
				sscanf(s, "umask=%x", &umask);
			if ((event | (umask << 8)) == (target & 0xffff)) {
				*name = e->name;
				if (desc)
					*desc = e->desc;
				return 0;
			}
		}
	}
	return -1;

}
