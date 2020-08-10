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
#include <stdint.h>

#include "jevents.h"
#include "perf-iter.h"
#include "perf-record.h"
#include "util.h"

/* 2^n size of event ring buffer (in pages) */
#define BUF_SIZE_SHIFT 8

static char psb[16] = {
	0x02, 0x82, 0x02, 0x82, 0x02, 0x82, 0x02, 0x82,
	0x02, 0x82, 0x02, 0x82, 0x02, 0x82, 0x02, 0x82
};

#define MAX_PSB_SIZE 128

#define LEFT(x) ((end - p) >= (x))

#if DEBUG
#define Pmsg(x) printf("%06lx %02x " #x "\n", p - start, *p);
#else
#define Pmsg(x)
#endif

/* Only enough encoding to find a TSC in a PSB. */
unsigned long find_tsc(unsigned char *p, unsigned char *map, unsigned char *end)
{
	unsigned char buf[MAX_PSB_SIZE];

	/* If there might be wrap handle PSB in a temporary buffer */
	if (end - p < MAX_PSB_SIZE) {
		int len = end - p;
		memcpy(buf, p, len);
		memcpy(buf + len, map, MAX_PSB_SIZE - len);
		p = buf;
		end = buf + MAX_PSB_SIZE;
	}

	unsigned char *start = p;
	while (p < end) {
		if (*p == 2 && LEFT(2)) {
			if (p[1] == 0b11110011 && LEFT(8)) { /* OVF */
				Pmsg(OVF);
				p += 8;
				continue;
			}
			if (p[1] == 3 && LEFT(4) && p[3] == 0) { /* CBR */
				Pmsg(CBR);
				p += 4;
				continue;
			}
			if (p[1] == 0x82 && LEFT(16) && !memcmp(p, psb, 16)) { /* PSB */
				Pmsg(PSB);
				p += 16;
				continue;
			}
			if (p[1] == 0b100011) {/* PSBEND */
				Pmsg(PSBEND);
				break;
			}
			if (p[1] == 0b01110011 && LEFT(7)) { // TMA
				Pmsg(TMA);
				p += 7;
				continue;
			}
			if (p[1] == 0b11001000 && LEFT(7)) { // VMCS
				Pmsg(VMCS);
				p += 7;
				continue;
			}
		}

		if (*p == 0) { /* PAD */
			Pmsg(PAD);
			p++;
			continue;
		}

		if ((*p & 1) == 0) { // TNT, shouldn't happen in PSB
			printf("unexpected tnt %x at %ld\n", *(unsigned char *)p, p - start);
			p++;
			continue;
		}

		switch (*p & 0x1f) {
		case 0xd:  /* TIP */
		case 0x11: /* TIP.PGE */
		case 0x1:  /* TIP.PGD */
			Pmsg(TIP);
			p += (*p >> 5)*2 + 2;
			continue;
		case 0x1d: // FUP
			Pmsg(FUP);
			p += (*p >> 5)*2 + 2;
			continue;
		}

		if (*p == 0x99 && LEFT(2)) { /* MODE */
			Pmsg(MODE);
			p += 2;
			continue;
		}
		if (*p == 0x19 && LEFT(8)) {  /* TSC */
			uint64_t tsc;
			Pmsg(TSC);
			memcpy(&tsc, p + 1, 7);
			return tsc;
		}
		if (*p == 0b01011001 && LEFT(2)) { /* MTC */
			Pmsg(MTC);
			p += 2;
			continue;
		}

		printf("unknown packet %x at %lx\n", *p, p - start);
		break;
	}
	return 0;
}

#define before(a, b) ((long)((a) - (b)) < 0)

/* Look for PSB with oldest TSC. This is the start of the trace */
unsigned char *find_trace_start(unsigned char *map, int len)
{
	unsigned char *p;
	unsigned char *end = map + len;
	unsigned long oldest = 0, tsc;
	unsigned char *start = NULL;

	/* look for PSB */
	for (p = map; p < end; p += 16) {
		p = memmem(p, len, psb, 16);
		if (!p)
			break;
		printf("PSB at %ld\n", p - map);
		tsc = find_tsc(p, map, end);
		if (!tsc) {
			printf("no TSC found after PSB at offset %ld\n", p-map);
			continue;
		}
		if (!oldest || before(tsc, oldest)) {
			oldest = tsc;
			start = map;
		}
	}
	return start;
}

volatile int v = 1;

static void func(void)
{
	v++;
}

static volatile void (*funcptr)(void) = func;

void test_load(void)
{
#ifdef SHORT_WORKLOAD
	printf("hello\n");
#else
	int i;
	for (i = 0; i < 10000000; i++)
		funcptr();
#endif
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
	ptattr.disabled = 1;
	if (perf_fd_open(&ptfd, &ptattr, BUF_SIZE_SHIFT) < 0)
		err("perf event init for PT");

	if (perf_aux_map(&ptfd, &ptaux, BUF_SIZE_SHIFT, true) < 0)
		err("perf event mmap aux buffer for PT");

	int i;
	for (i = 0; i < 3; i++) {
		if (perf_enable(&ptfd) < 0)
			err("PERF_EVENT_IOC_ENABLE");

		printf("%d:\n", i);

		test_load();

		if (perf_disable(&ptfd) < 0)
			err("PERF_EVENT_IOC_DISABLE");

		unsigned char *start = find_trace_start(ptaux.aux_map, ptfd.mpage->aux_size);
		if (!start)
			printf("No PT trace found\n");
		else
			printf("PT trace starts at offset %ld\n",
			       start - (unsigned char*)ptaux.aux_map);
	}

	perf_aux_unmap(&ptfd, &ptaux);
	perf_fd_close(&ptfd);

	return 0;
}
