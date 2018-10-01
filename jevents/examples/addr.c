/* 
 * perf address sampling self profiling demo.
 * Requires a 3.10+ kernel with PERF_SAMPLE_ADDR support and a supported Intel CPU.
 *
 * Copyright (c) 2013 Intel Corporation
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
#include <linux/perf_event.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <cpuid.h>
#include <stdbool.h>
#include <assert.h>
#include <dlfcn.h>

#include "hist.h"
#include "perf-iter.h"
#include "util.h"
#include "cpu.h"

/* 2^n size of event ring buffer (in pages) */
#define BUF_SIZE_SHIFT 8

#define SIZE ((100*MB)/sizeof(float))

float *x, *y;

void simple_test_init(void)
{
	y = calloc(SIZE, sizeof(float));
        x = calloc(SIZE, sizeof(float));
        int i;
        for (i = 0; i < SIZE; i++) {
                y[i] = 1.0;
                x[i] = 2.0;
        }
 
	printf("test area %p-%p, %p-%p\n", x, x+SIZE, y, y+SIZE);
}

void simple_test_load(void)
{
        int i;
        int j;
        for (j = 0; j < 20; j++) {
        	for (i = 0; i < SIZE; i++) {
                	y[i] = y[i] * x[i];
			mb();	/* Don't optimize the loop away */
		}
	}
}

void (*test_init)(void) = simple_test_init;
void (*test_load)(void) = simple_test_load;

void gen_hist(char *name, struct perf_fd *pfd)
{
	struct perf_iter iter;
	struct hist *h = init_hist();

	perf_iter_init(&iter, pfd);
	int samples = 0, others = 0, throttled = 0, skipped = 0;
	u64 lost = 0;
	while (!perf_iter_finished(&iter)) {
		char buffer[64];
		struct perf_event_header *hdr = perf_buffer_read(&iter, buffer, 64);

		if (!hdr) {
			skipped++;
			continue;
		}

		if (hdr->type != PERF_RECORD_SAMPLE) {
			if (hdr->type == PERF_RECORD_THROTTLE)
				throttled++;
			else if (hdr->type == PERF_RECORD_LOST)
				lost += perf_hdr_payload(hdr)[1];
			else
				others++;
			continue;
		}
		samples++;
		if (hdr->size != 16) {
			printf("unexpected sample size %d\n", hdr->size);
			continue;
		}

		u64 val = perf_hdr_payload(hdr)[0];
		/* Filter out kernel samples, which can happen due to OOO skid */
		if ((long long)val < 0)
			continue;
		hist_add(h, val);
	}
	perf_iter_continue(&iter);

	printf("%s: %d samples, %d others, %llu lost, %d throttled, %d skipped\n",
				name,
				samples,
				others,
				lost,
				throttled,
				skipped);
	hist_print(h, 0.001);
	free_hist(h);
}

int main(int ac, char **av)
{
	bool cycles_only = false;

	/* Set up perf for loads */
	struct perf_event_attr attr = {
		.type = PERF_TYPE_RAW,
		.size = PERF_ATTR_SIZE_VER0,
		.sample_type = PERF_SAMPLE_ADDR,
		.sample_period = 10000,		/* Period */
		.exclude_kernel = 1,
		.precise_ip = 1,		/* Enable PEBS */
		.config1 = 3,			/* Load Latency threshold */
		.config = mem_loads_event(),	/* Event */
		.disabled = 1,
	};

	if (attr.config == -1) {
		printf("Unknown CPU model\n");
		exit(1);
	}

	if (av[1] && !strcmp(av[1], "cycles")) {
		attr.sample_type = PERF_SAMPLE_IP;
		attr.precise_ip = 0;
		attr.config = 0x3c;
		cycles_only = true;
		av--;
	}

	if (av[1]) { 
		void *test_obj;
		test_obj = dlopen(av[1], RTLD_NOW);
		if (!test_obj) { 
			fprintf(stderr, "Cannot load %s: %s\n", av[1], dlerror());
			exit(1);
		}
		test_init = dlsym(test_obj, "test_init");
		test_load = dlsym(test_obj, "test_load");
		if (!test_init || !test_load) {
			fprintf(stderr, "%s missing test_init or test_load symbols: %s\n",
					av[1], dlerror());
			exit(1);
		}
	}

	struct perf_fd loads, stores;
	if (perf_fd_open(&loads, &attr, BUF_SIZE_SHIFT) < 0)
		err("perf event init loads");
	printf("loads event %llx\n", attr.config);

	bool have_stores = false;
	if (0 && !cycles_only) {
		attr.config = mem_stores_event();
		attr.config1 = 0;
		if (perf_fd_open(&stores, &attr, BUF_SIZE_SHIFT) < 0)
			err("perf event init stores");
		printf("stores event %llx\n", attr.config);
		have_stores = true;
	}

	test_init();

	/* Run measurement */

	if (perf_enable(&loads) < 0)
		err("PERF_EVENT_IOC_ENABLE");
	if (0)
		perf_enable(&stores);

	test_load();

	if (perf_disable(&loads) < 0)
		err("PERF_EVENT_IOC_DISABLE");
	if (0)
		perf_disable(&stores);

	gen_hist("loads", &loads);
	perf_fd_close(&loads);
	if (have_stores) {
       		gen_hist("stores", &stores);	
		perf_fd_close(&stores);
	}

	return 0;
}
