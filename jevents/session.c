/* Simple session layer for multiple perf events. */
/*
 * Copyright (c) 2015, Intel Corporation
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

#include <string.h>
#include <unistd.h>
#include <linux/perf_event.h>
#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>
#include <errno.h>
#include <sys/fcntl.h>
#include <stdbool.h>
#include "jevents.h"
#include "jsession.h"

/**
 * alloc_eventlist - Alloc a list of events.
 */

struct eventlist *alloc_eventlist(void)
{
	struct eventlist *el = calloc(sizeof(struct eventlist), 1);
	if (!el)
		return NULL;
	el->num_cpus = sysconf(_SC_NPROCESSORS_CONF);
	return el;
}

static struct event *new_event(struct eventlist *el, char *s)
{
	struct event *e = calloc(sizeof(struct event) +
				 sizeof(struct efd) * el->num_cpus, 1);
	e->next = NULL;
	if (!el->eventlist)
		el->eventlist = e;
	if (el->eventlist_last)
		el->eventlist_last->next = e;
	el->eventlist_last = e;
	e->event = strdup(s);
	return e;
}

/**
 * parse_events - parse a perf style string with events
 * @el: List of events allocated earlier
 * @events: Comma separated lists of events. {} style groups are legal.
 *
 * JSON events are supported, if the event lists are downloaded first.
 */
int parse_events(struct eventlist *el, char *events)
{
	char *s, *tmp;

	events = strdup(events);
	if (! events) return -1;
	for (s = strtok_r(events, ",", &tmp);
	     s;
	     s = strtok_r(NULL, ",", &tmp)) {
		bool group_leader = false, end_group = false;
		int len;

		if (s[0] == '{') {
			s++;
			group_leader = true;
		} else if (len = strlen(s), len > 0 && s[len - 1] == '}') {
			s[len - 1] = 0;
			end_group = true;
		}

		struct event *e = new_event(el, s);
		e->group_leader = group_leader;
		e->end_group = end_group;
		if (resolve_event(s, &e->attr) < 0) {
			fprintf(stderr, "Cannot resolve %s\n", e->event);
			return -1;
		}
	}
	free(events);
	return 0;
}

static bool cpu_online(int i)
{
	bool ret = false;
	char fn[100];
	sprintf(fn, "/sys/devices/system/cpu/cpu%d/online", i);
	int fd = open(fn, O_RDONLY);
	if (fd >= 0) {
		char buf[128];
		int n = read(fd, buf, 128);
		if (n > 0 && !strncmp(buf, "1", 1))
			ret = true;
		close(fd);
	}
	return ret;
}

/**
 * setup_event - Create perf descriptor for a single event.
 * @e: Event to measure.
 * @cpu: CPU to measure.
 * @leader: Leader event to define a group.
 * @measure_all: If true measure all processes (may need root)
 * @measure_pid: If not -1 measure specific process.
 *
 * This is a low level function. Normally setup_events() should be used.
 * Return -1 on failure.
 */

int setup_event(struct event *e, int cpu, struct event *leader,
		bool measure_all, int measure_pid)
{
	e->attr.inherit = 1;
	if (!measure_all) {
		e->attr.disabled = 1;
		e->attr.enable_on_exec = 1;
	}
	e->attr.read_format |= PERF_FORMAT_TOTAL_TIME_ENABLED |
				PERF_FORMAT_TOTAL_TIME_RUNNING;

	e->efd[cpu].fd = perf_event_open(&e->attr,
			measure_all ? -1 : measure_pid,
			cpu,
			leader ? leader->efd[cpu].fd : -1,
			0);

	if (e->efd[cpu].fd < 0) {
		/* Handle offline CPU */
		if (errno == EINVAL && !cpu_online(cpu))
			return 0;

		fprintf(stderr, "Cannot open perf event for %s/%d: %s\n",
				e->event, cpu, strerror(errno));
		return -1;
	}
	return 0;
}

/**
 * setup_events - Set up perf events for a event list.
 * @el: List of events, allocated and parsed earlier.
 * @measure_all: If true measure all of system (may need root)
 * @measure_pid: If not -1 measure pid.
 *
 * Return -1 on failure, otherwise 0.
 */

int setup_events(struct eventlist *el, bool measure_all, int measure_pid)
{
	struct event *e, *leader = NULL;
	int i;

	for (e = el->eventlist; e; e = e->next) {
		for (i = 0; i < el->num_cpus; i++) {
			if (setup_event(e, i, leader,
					measure_all,
					measure_pid) < 0)
				return -1;
		}
		if (e->group_leader)
			leader = e;
		if (e->end_group)
			leader = NULL;
	}
	return 0;
}

/**
 * read_event - Read the value of a single event for one CPU.
 * @e: event to read
 * @cpu: cpu number to read
 * Returns -1 on failure, otherwise 0.
 * The value read can be retrieved later with event_scaled_value.
 */

int read_event(struct event *e, int cpu)
{
	int n = read(e->efd[cpu].fd, &e->efd[cpu].val, 3 * 8);
	if (n < 0) {
		fprintf(stderr, "Error reading from %s/%d: %s\n",
				e->event, cpu, strerror(errno));
		return -1;
	}
	return 0;
}

/**
 * read_event - Read value of all events on all CPUs.
 * @el: eventlist. Must be allocated, parsed, set up earlier.
 * Returns -1 on failure, otherwise 0.
 */

int read_all_events(struct eventlist *el)
{
	struct event *e;
	int i;

	for (e = el->eventlist; e; e = e->next) {
		for (i = 0; i < el->num_cpus; i++) {
			if (e->efd[i].fd < 0)
				continue;
			if (read_event(e, i) < 0)
				return -1;
		}
	}
	return 0;
}

/**
 * event_scaled_value - Retrieve a read value for a cpu
 * @e: Event
 * @cpu: CPU number
 * Return scaled value read earlier.
 */
uint64_t event_scaled_value(struct event *e, int cpu)
{
	uint64_t *val = e->efd[cpu].val;
	if (val[1] != val[2] && val[2])
		return val[0] * (double)val[1] / (double)val[2];
	return val[0];
}
