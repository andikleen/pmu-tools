// SPDX-License-Identifier: BSD-3-Clause
// Copyright 2021 Intel Corporation.
// Author: Andi Kleen
#include "jevents.h"
#include "jsession.h"

static void print_runtime(FILE *outfh, uint64_t *val)
{
	if (val[1] != val[2])
		fprintf(outfh, " [%2.2f%%]", ((double)val[2] / val[1]) * 100.);
}

/**
 * session_print_timestamp - Print perf stat style timestamp into buffer
 * @buf: String buffer. Should be SESSION_TIMESTAMP_LEN sized.
 * @bufs: Buffer size.
 * @ts: Timestamp
 */
void session_print_timestamp(char *buf, int bufs, double ts)
{
	snprintf(buf, bufs, "% 12.9f\t", ts);
}

/**
 * session_print_aggr - Print event list values in perf stat like output aggregated
 * @outfh: File descriptor to print to.
 * @el: Event list to print. It must have been measured before.
 * @arg: Argument. Used prefix and merge.
 *
 * This version aggregates values over all CPUs.
 */

void session_print_aggr(FILE *outfh, struct eventlist *el, struct session_print *arg)
{
	struct event *e;
	int i;

	for (e = el->eventlist; e; e = e->next) {
		if (arg->merge && e->orig)
			continue;

		uint64_t v = 0, val[3] = { 0, 0, 0 };
		for (i = 0; i < el->num_cpus; i++) {
			v += event_scaled_value(e, i);
			// assumes all are scaled the same way
			if (e->efd[i].val[2]) {
				val[1] += e->efd[i].val[1];
				val[2] += e->efd[i].val[2];
			}
		}
		if (val[1] == 0 && el->num_cpus > 0) {
			val[1] = e->efd[0].val[1];
			val[2] = e->efd[0].val[2];
		}

		fprintf(outfh, "%s%-30s %'15lu", arg->prefix ? arg->prefix : "",
				e->extra.name ? e->extra.name : e->event, v);
		print_runtime(outfh, val);
		putc('\n', outfh);
	}
}

/**
 * session_print - Print event list values in perf stat like output.
 * @outfh: File descriptor to print to.
 * @el: Event list to print. It must have been measured before.
 * @arg: Argument. Used prefix and merge.
 *
 * This version prints each CPU individually (like perf stat -A)
 */
void session_print(FILE *outfh, struct eventlist *el, struct session_print *arg)
{
	struct event *e;
	int i;

	for (e = el->eventlist; e; e = e->next) {
		uint64_t v;
		for (i = 0; i < el->num_cpus; i++) {
			if (e->efd[i].fd < 0)
				continue;
			if (arg->merge && e->orig)
				continue;
			v = event_scaled_value(e, i);
			fprintf(outfh, "%s%3d %-30s %'15lu", arg->prefix ? arg->prefix : "",
					i,
					e->extra.name ? e->extra.name : e->event, v);
			print_runtime(outfh, e->efd[i].val);
			putc('\n', outfh);
		}
	}
}
