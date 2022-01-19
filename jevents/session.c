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
	jevents_socket_cpus(&el->num_sockets, &el->socket_cpus);
	return el;
}

static struct event *new_event(struct eventlist *el, char *s)
{
	struct event *e = calloc(sizeof(struct event) +
				 sizeof(struct efd) * el->num_cpus, 1);
	int i;

	e->event = strdup(s);
	for (i = 0; i < el->num_cpus; i++)
		e->efd[i].fd = -1;
	return e;
}

static void add_event(struct eventlist *el, struct event *e)
{
	e->next = NULL;
	if (!el->eventlist)
		el->eventlist = e;
	if (el->eventlist_last)
		el->eventlist_last->next = e;
	el->eventlist_last = e;
}

static char *grab_event(char *s, char **next)
{
	char *p = s;
	if (s == NULL || *s == 0)
		return NULL;
	*next = NULL;
	while (*s) {
		if (*s == '/') {
			s++;
			while (*s && *s != '/')
				s++;
		}
		if (*s == ',') {
			*s = 0;
			*next = s + 1;
			break;
		}
		s++;
	}
	return p;
}

/**
 * parse_events - parse a perf style string with events
 * @el: List of events allocated earlier
 * @events: Comma separated lists of events. {} style groups are legal.
 *
 * JSON events are supported, if the event lists are downloaded first.
 * In case of an error the caller needs to call free_eventlist, unless
 * they want to reuse the already existing events.
 */
int parse_events(struct eventlist *el, char *events)
{
	char *s, *next;
	bool ingroup = false;
	int err;
	struct perf_event_attr attr;
	struct event *ne;

	/* Keeps track of in-group multi-pmu events for
	   later parsing and duplication of group */
	char **multi_pmu_strs;
	struct event **multi_pmu_events;
	int num_multi_pmu, i, n;

	events = strdup(events);
	if (!events)
		return -1;

	multi_pmu_strs = NULL;
	multi_pmu_events = NULL;
	num_multi_pmu = 0;
	next = events;
	while ((s = grab_event(next, &next)) != NULL) {
		bool group_leader = false, end_group = false;
		int len;

		if (s[0] == '{') {
			s++;
			group_leader = true;
			ingroup = true;
		}
		if (len = strlen(s), len > 0 && s[len - 1] == '}') {
			s[len - 1] = 0;
			end_group = true;
		}

		struct event *e = new_event(el, s);
		e->group_leader = group_leader;
		e->end_group = end_group;
		e->ingroup = ingroup;
		if (resolve_event_extra(s, &e->attr, &e->extra) < 0) {
			fprintf(stderr, "Cannot resolve %s\n", e->event);
			goto err;
		}
		e->uncore = jevent_pmu_uncore(e->extra.decoded);
		if (!(e->extra.multi_pmu)) {
			add_event(el, e);
		} else {
			attr = e->attr;

			if (ingroup) {
				/* We'll store this multi-PMU event for now; at the end of the group,
				   we'll parse and handle it. */
				multi_pmu_strs = realloc(multi_pmu_strs, (num_multi_pmu + 1) * sizeof(char **));
				if (!multi_pmu_strs)
					goto err;
				multi_pmu_events = realloc(multi_pmu_events, (num_multi_pmu + 1) * sizeof(struct event *));
				if (!multi_pmu_events)
					goto err;
				multi_pmu_strs[num_multi_pmu] = strdup(s);
				multi_pmu_events[num_multi_pmu] = e;
				num_multi_pmu++;
			} else {
				while ((err = jevent_next_pmu(&e->extra, &attr)) == 1) {
					ne = new_event(el, s);
					add_event(el, ne);
					ne->group_leader = e->group_leader;
					ne->end_group = e->end_group;
					ne->ingroup = e->ingroup;
					ne->attr = attr;
					ne->orig = e;
					ne->uncore = e->uncore;
					e->num_clones++;
					jevent_copy_extra(&ne->extra, &e->extra);
				}
				if (err < 0) {
					fprintf(stderr, "Cannot find PMU for event %s\n", e->event);
					goto err;
				}
			}
		}
		if (end_group) {
			ingroup = false;
			if (num_multi_pmu) {
				/* This ends the group that contained multi-pmu events.
				   Go back through those events and create a new copy
				   of the group for each PMU. Here, we can simply use
				   the number of PMUs in the first event as the number of groups. */
				for (i = 0; i < multi_pmu_events[0]->extra.pmus.gl_pathc; i++) {
					for (n = 0; n < num_multi_pmu; n++) {
						err = jevent_next_pmu(&(multi_pmu_events[n]->extra), &(multi_pmu_events[n]->attr));
						if (err == 0) {
							fprintf(stderr, "There was a mismatch in the number of multi-PMU events: %s\n", multi_pmu_events[n]->event);
							goto err;
						} else if (err == -1) {
							fprintf(stderr, "Failed to get next PMU for multi-PMU event %s.\n", multi_pmu_events[n]->event);
							goto err;
						}
						ne = new_event(el, multi_pmu_strs[n]);
						add_event(el, ne);
						ne->group_leader = multi_pmu_events[n]->group_leader;
						ne->end_group = multi_pmu_events[n]->end_group;
						ne->ingroup = multi_pmu_events[n]->ingroup;
						ne->attr = multi_pmu_events[n]->attr;
						ne->orig = multi_pmu_events[n];
						ne->uncore = multi_pmu_events[n]->uncore;
						multi_pmu_events[n]->num_clones++;
						jevent_copy_extra(&ne->extra, &(multi_pmu_events[n]->extra));
					}
				}

				/* Free up multi-PMU storage */
				free(multi_pmu_events);
				for (i = 0; i < num_multi_pmu; i++)
					free(multi_pmu_strs[i]);
				free(multi_pmu_strs);
				multi_pmu_strs = NULL;
				multi_pmu_events = NULL;
				num_multi_pmu = 0;
			}
		}
	}
	free(events);
	return 0;

err:
	free(events);
	return -1;
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

static bool cpumask_match(char *mask, int ocpu)
{
	if (!mask)
		return true;
	while (*mask) {
		char *endp;
		int cpu = strtoul(mask, &endp, 0);
		if (mask == endp)
			return false;
		if (cpu == ocpu)
			return true;
		if (*endp == '-') {
			mask = endp + 1;
			int cpu2 = strtoul(mask, &endp, 0);
			if (mask == endp)
				return ocpu > cpu;
			if (ocpu > cpu && ocpu <= cpu2)
				return true;
		}
		mask = endp;
		if (*mask == ',')
			mask++;
	}
	return false;
}

/**
 * setup_event - Create perf descriptor for a single event.
 * @e: Event to measure.
 * @cpu: CPU to measure.
 * @leader: Leader event to define a group.
 * @measure_pid: If not -1 measure specific process.
 * @flags:  Measurement flags: %SE_ENABLE_ON_EXEC, %SE_MEASURE_ALL
 *
 * This is a low level function. Normally setup_events() should be used.
 * Return -1 on failure.
 */

int setup_event_flags(struct event *e, int cpu, struct event *leader,
		      int measure_pid, int flags)
{
	e->attr.inherit = 1;
	if (flags & SE_ENABLE_ON_EXEC) {
		e->attr.disabled = 1;
		e->attr.enable_on_exec = 1;
	}
	e->attr.read_format |= PERF_FORMAT_TOTAL_TIME_ENABLED |
				PERF_FORMAT_TOTAL_TIME_RUNNING;

	e->efd[cpu].fd = perf_event_open(&e->attr,
			(flags & SE_MEASURE_ALL) ? -1 : measure_pid,
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
	return setup_event_flags(e, cpu, leader,
			measure_pid,
			!measure_all ? SE_ENABLE_ON_EXEC : 0);
}

/**
 * setup_events - Set up perf events for a event list.
 * @el: List of events, allocated and parsed earlier.
 * @measure_pid: If not -1 measure pid.
 * @cpumask: string of cpus to measure on, or NULL for all
 * @flags: %SE_MEASURE_ALL or %SE_ENABLE_ON_EXEC
 *
 * Return -1 on failure, otherwise 0.
 */

int setup_events_cpumask(struct eventlist *el, int measure_pid,
			 char *cpumask, int flags)
{
	struct event *e, *leader = NULL;
	int i;
	int err = 0;
	int ret;
	int success = 0;

	for (e = el->eventlist; e; e = e->next) {
		if (e->uncore) {
			for (i = 0; i < el->num_cpus; i++)
				e->efd[i].fd = -1;
			for (i = 0; i < el->num_sockets; i++) {
				if (!cpumask_match(cpumask, el->socket_cpus[i]))
					continue;
				ret = setup_event_flags(e, el->socket_cpus[i], leader,
						  measure_pid, flags);
				if (ret < 0) {
					err = ret;
					continue;
				} else {
					success++;
				}
			}
		} else {
			for (i = 0; i < el->num_cpus; i++) {
				if (!cpumask_match(cpumask, i))
					continue;
				ret = setup_event_flags(e, i, leader,
						measure_pid,
						flags);
				if (ret < 0) {
					err = ret;
					continue;
				} else {
					success++;
				}
			}
		}
		if (e->group_leader)
			leader = e;
		if (e->end_group)
			leader = NULL;
	}
	if (success > 0)
		return 0;
	return err;
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
	return setup_events_cpumask(el, measure_pid, NULL,
			measure_all ? SE_MEASURE_ALL : SE_ENABLE_ON_EXEC);
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

/**
 * event_scaled_value_sum - Retrieve a summed up read value for a cpu
 * @e: Event
 * @cpu: CPU number
 * Return scaled value read earlier. When the event was cloned
 * (e.g. uncore event with multiple instances) it returns
 * the sum of clones. @e must be the first event, and later
 * clones (e->orig != NULL) should be skipped by caller.
 */
uint64_t event_scaled_value_sum(struct event *e, int cpu)
{
	uint64_t sum = event_scaled_value(e, cpu);
	int num_clones = e->num_clones;
	struct event *ce;
	for (ce = e->next; ce && num_clones > 0; ce = ce->next) {
		if (ce->orig == e)
			sum += event_scaled_value(ce, cpu);
	}
	return sum;
}

/**
 * close_event - Close (but not free) an event.
 * @el: Event list
 * @e: Event to close
 * After this setup_event can be called again.
 */
void close_event(struct eventlist *el, struct event *e)
{
	int i;
	for (i = 0; i < el->num_cpus; i++) {
		if (e->efd[i].fd >= 0) {
			close(e->efd[i].fd);
			e->efd[i].fd = -1;
		}
	}
}

/**
 * free_eventlist - Free and close a event list and its events.
 * @el: Event list to free.
 */
void free_eventlist(struct eventlist *el)
{
	struct event *e, *next;

	for (e = el->eventlist; e; e = next) {
		next = e->next;
		close_event(el, e);
		jevent_free_extra(&e->extra);
		free(e->event);
		free(e);
	}
	free(el->socket_cpus);
	free(el);
}

void print_event_list_attr(struct eventlist *el, FILE *f)
{
	struct event *e;
	int num, next;
	char *name;

	for (e = el->eventlist; e; e = e->next) {
		fprintf(f, "%s:\n", e->event);
		if (e->extra.name)
			fprintf(f, "name: %s\n", e->extra.name);
		if (e->extra.decoded)
			fprintf(f, "perf: %s\n", e->extra.decoded);
		jevent_print_attr(f, &e->attr);
		for (num = 0; (name = jevent_pmu_name(&e->extra, num, &next)) != NULL; num = next)
			printf("pmu%d: %s\n", num, name);
		fprintf(f, "\n");
	}
}
