/*
 * Simple Processor Trace self monitoring example using libjevents
 * This uses PT in a ring buffer configuration.
 *
 * Copyright (c) 2020 Intel Corporation
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
#define _GNU_SOURCE 1
#include <linux/perf_event.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <math.h>
#include <time.h>

#include "jevents.h"
#include "hist.h"
#include "perf-iter.h"
#include "perf-record.h"
#include "util.h"

/* 2^n size of event ring buffer (in pages) */
#define BUF_SIZE_SHIFT 8

static char psb[16] = {
	0x02, 0x82, 0x02, 0x82, 0x02, 0x82, 0x02, 0x82,
	0x02, 0x82, 0x02, 0x82, 0x02, 0x82, 0x02, 0x82
};

#define LEFT(x) ((end - p) >= (x))

void dump_pt(char *map, int len)
{
	char *p;
	char *end = map + len;

	p = map;
	/* look for PSB */
	while (p < end) {
		p = memmem(p, len, psb, 16);
		if (!p)
			return;
		printf("PSB at offset %ld\n", p - map);
		p += 16;
	}
}

void handle_pt(struct perf_fd *pfd, struct perf_aux_map *aux)
{
	struct perf_iter iter;

	perf_iter_init(&iter, pfd);
	while (!perf_iter_finished(&iter)) {
		char buffer[64];
		struct perf_event_header *hdr = perf_buffer_read(&iter, buffer, 64);

		if (!hdr)
			continue;

		/* Could check for PERF_RECORD_ITRACE_START here, but we already
		 * know the process.
		 */

		if (hdr->type == PERF_RECORD_AUX) {
			struct perf_record_aux *pa = (struct perf_record_aux *)hdr;

			dump_pt(aux->aux_map + pa->aux_offset, pa->aux_size);
		}

		if (hdr->type == PERF_RECORD_LOST_SAMPLES) {
			struct perf_record_lost_samples *lost = (struct perf_record_lost_samples *)hdr;

			printf("lost samples %llu\n", lost->lost);
		}
	}
	perf_iter_continue(&iter);
}

double nstime(void)
{
	struct timespec tv;
	clock_gettime(CLOCK_MONOTONIC, &tv);
	return (double)tv.tv_sec * 1e9 + tv.tv_nsec;
}

/* Run for at least 1 second to give the kernel enough time to generate an aux sample */
void test_load(void)
{
	volatile float v = 1;
	double starttime = nstime();

	while (nstime() < starttime + 1e9)
		v += sin(v) + cos(v);
}

int main(int ac, char **av)
{
	struct perf_event_attr ptattr;
	struct perf_aux_map ptaux;
	struct perf_fd ptfd;
	char *ptconfig = "intel_pt/tsc,mtc,mtc_period=3,psb_period=3,branch,pt/u";

	if (jevent_name_to_attr(ptconfig, &ptattr) < 0) {
		printf("cannot parse %s\n", ptconfig);
		exit(1);
	}
	if (perf_fd_open(&ptfd, &ptattr, BUF_SIZE_SHIFT) < 0)
		err("perf event init for PT");

	if (perf_aux_map(&ptfd, &ptaux, BUF_SIZE_SHIFT, true) < 0)
		err("perf event mmap aux buffer for PT");

	if (perf_enable(&ptfd) < 0)
		err("PERF_EVENT_IOC_ENABLE");

	test_load();

	if (perf_disable(&ptfd) < 0)
		err("PERF_EVENT_IOC_DISABLE");

	handle_pt(&ptfd, &ptaux);

	perf_aux_unmap(&ptfd, &ptaux);
	perf_fd_close(&ptfd);

	return 0;
}
