/*
 * Copyright (c) 2012,2013 Intel Corporation
 * Author: Andi Kleen
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that: (1) source code distributions
 * retain the above copyright notice and this paragraph in its entirety, (2)
 * distributions including binary code include the above copyright notice and
 * this paragraph in its entirety in the documentation or other materials
 * provided with the distribution
 *
 * THIS SOFTWARE IS PROVIDED ``AS IS'' AND WITHOUT ANY EXPRESS OR IMPLIED
 * WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
 */

#include <stdlib.h>
#include <pthread.h>
#include <string.h>
#include <stdio.h>
#include "measure.h"
#include "rdpmc.h"

/**
 * DOC: Measuring of predefined counter groups in a process
 *
 * Higher level interface to measure CPU performance counters in process
 * context. The program calls the appropiate functions around 
 * code that should be measured in individual thread.
 *
 * The data is accumulated globally and printed
 */

struct res {
	struct res *next;
	unsigned long long start[N_COUNTER];
	unsigned long long count[N_COUNTER];
	char *name;
	struct measure *measure;
};

static struct res *all_res;
static pthread_mutex_t all_res_lock = PTHREAD_MUTEX_INITIALIZER;
static __thread struct rdpmc_ctx ctx[N_COUNTER];
static __thread struct res *cur_res;

static struct res *alloc_res(char *name, struct measure *measure)
{
	struct res *r = calloc(sizeof(struct res), 1);
	if (!name)
		name = "";
	r->name = strdup(name);
	r->measure = measure;
	pthread_mutex_lock(&all_res_lock);
	r->next = all_res;
	all_res = r;
	pthread_mutex_unlock(&all_res_lock);
	return r;
}

/**
 * measure_group_init - Initialize a measurement group
 * @g: measurement group (usually predefined)
 * @name: name of measurements or NULL
 *
 * Initialize a measurement group and allocate the counters.
 * All measurements with the same name are printed together (so multiple
 * names can be used to measure different parts of the program)
 * Exits when the counters cannot be allocated.
 * Has to be freed in the same thread with measure_group_finish()
 * Only one measurement group per thread can be active at a time.
 */
void measure_group_init(struct measure *g, char *name)
{
	struct res *r = alloc_res(name, g);
	cur_res = r;

	int i;
	struct rdpmc_ctx *leader = NULL;
	for (i = 0; i < N_COUNTER; i++) {
		struct perf_event_attr attr = {
			.type = PERF_TYPE_RAW,
			.size = sizeof(struct perf_event_attr),
			.config = g[i].counter,
			.sample_type = PERF_SAMPLE_READ,
			.exclude_kernel = 1,
		};
		if (rdpmc_open_attr(&attr, &ctx[i], leader) < 0)
			exit(1);
		if (!leader)
			leader = &ctx[i];
	}
}

/**	
 * measure_group_start - Start measuring in a measurement group.
 * 
 * Start a measurement period for the current group in this thread.
 * Multiple measurement periods are accumulated.
 */
void measure_group_start(void)
{
	int i;
	for (i = 0; i < N_COUNTER; i++)
		cur_res->start[i] = rdpmc_read(&ctx[i]);
}

/**
 * measure_group_stop - Stop measuring a measurement group
 *
 * Stop the measurement for the current measurement group.
 */
void measure_group_stop(void)
{
	unsigned long long end[N_COUNTER];
	int i;
	for (i = 0; i < N_COUNTER; i++)
		end[i] = rdpmc_read(&ctx[i]);
	for (i = 0; i < N_COUNTER; i++)
		cur_res->count[i] += end[i] - cur_res->start[i];
}

/**
 * measurement_group_finish - Free the counter resources of a group
 *
 * Has to be called in the thread that executed measure_group_init()
 */
void measure_group_finish(void)
{
	cur_res = NULL;
	int i;
	for (i = 0; i < N_COUNTER; i++)
		rdpmc_close(&ctx[i]);	      
}

static int cmp_res(const void *a, const void *b)
{
	struct res **ra = (struct res **)a;
	struct res **rb = (struct res **)b;
	return strcmp((*ra)->name, (*rb)->name);
}

static struct res **sort_results(int *lenp)
{
	struct res *r;
	int len = 0;
	for (r = all_res; r; r = r->next)
		len++;
	struct res **sr = malloc(len * sizeof(struct res *));
	int j = 0;
	for (r = all_res; r; r = r->next)
		sr[j++] = r;
	qsort(sr, len, sizeof(struct res *), cmp_res);
	*lenp = len;
	return sr;
}

static void print_counters(FILE *fh, struct measure *m, 
		           unsigned long long total[N_COUNTER])
{
	int i;
	for (i = 0; i < N_COUNTER; i++) {
		if (m[i].name == NULL)
			continue;
		if (m[i].func)
			total[i] = m[i].func(m, total, i);
		printf("%20s\t%8llu ", m[i].name, total[i]);
		if (m[i].ratio_to >= 0)
			printf("(%.2f%%)", 
			       100.0 * (total[m[i].ratio_to] * (double)total[i]));
		putchar('\n');
	}
}

/**
 * measure_print_all - Print the accumulated data for all measurement groups
 * @fh:		stdio file descriptor to output data
 */
void measure_print_all(FILE *fh)
{
	unsigned long long total[N_COUNTER];
	int len;
	struct res **sr = sort_results(&len);
	int i, j;

	for (j = 0; j < len; j++) {
		if (j == 0 || strcmp(sr[j - 1]->name, sr[j]->name)) {
			if (j > 0) {
				printf("%s:\n", sr[j]->name);
				print_counters(fh, sr[j]->measure, total);
			}
			memset(total, 0, sizeof(unsigned long long) * N_COUNTER);
		}				
		for (i = 0; i < N_COUNTER; i++)
			total[i] += sr[j]->count[i];
	}
	free(sr);       
}

/**
 * measure_free_all - Free the accumulated data from past measurements
 */
void measure_free_all(void)
{
	struct res *r, *next;
	for (r = all_res; r; r = next) {
		next = r->next;
		free(r);
	}
	all_res = NULL;
}
