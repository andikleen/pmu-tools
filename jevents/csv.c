// SPDX-License-Identifier: BSD-3-Clause
// Copyright 2021 Intel Corporation.
// Author: Andi Kleen
#include <stdint.h>
#include "jevents.h"
#include "jsession.h"

/**
 * session_print_csv - Print event list values to CSV file in perf stat format
 * @outfh: File descriptor to print to.
 * @el: Event list to print. It must have been measured before.
 * @arg: Arguments. sep can be set there, as well as prefix.
 */

void session_print_csv(FILE *outfh, struct eventlist *el, struct session_print *arg)
{
	struct event *e;
	int i;
	char *sep = arg->sep ? arg->sep : ";";

	for (e = el->eventlist; e; e = e->next) {
		uint64_t v;
		for (i = 0; i < el->num_cpus; i++) {
			if (e->efd[i].fd < 0)
				continue;
			if (arg->merge && e->orig)
				continue;
			v = event_scaled_value(e, i);
			fprintf(outfh, "%s%3d%s%s%s%lu%s%lu%s%lu\n",
				arg->prefix ? arg->prefix : "",
				i, sep,
				e->extra.name ? e->extra.name : e->event, sep,
				v, sep,
				e->efd[i].val[1], sep,
				e->efd[i].val[2]);
		}
	}
}
