/*
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

/* CPU detection and event tables */
#include <cpuid.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

#include "cpu.h"

struct cpu_events {
	int *models;
	unsigned mem_stores;
	unsigned mem_loads;
};

#define MEM_LOADS_SNB 0x1cd	/* MEM_TRANS_RETIRED.LOAD_LATENCY */
#define MEM_STORES_SNB 0x2cd 	/* MEM_TRANS_RETIRED.PRECISE_STORES */
static int snb_models[] = { 42, 45, 58, 62, 0 };

#define MEM_LOADS_HSW MEM_LOADS_SNB
#define MEM_STORES_HSW 0x82d0
static int hsw_models[] = { 60, 70, 71, 63, 61, 0 };

/* Nehalem and Westmere */
#define MEM_LOADS_NHM 0x100b	/* MEM_INST_RETIRED.LOAD_LATENCY */
#define MEM_STORES_NHM -1	/* not supported */

static int nhm_models[] = { 26, 30, 46, 37, 44, 47, 0 };

struct cpu_events events[] = { 
	{ snb_models, MEM_STORES_SNB, MEM_LOADS_SNB },
	{ nhm_models, MEM_STORES_NHM, MEM_LOADS_NHM },
	{ hsw_models, MEM_STORES_HSW, MEM_LOADS_HSW },
	{}
};

static unsigned get_cpu_model(void)
{
	unsigned sig;
	if (__get_cpuid_max(0, &sig) >= 1 && sig == *(int *)"Genu") {
		unsigned a, b, c, d;
		__cpuid(1, a, b, c, d);
		unsigned family = (a >> 8) & 0xf;
		if (family == 6)
			return ((a >> 4) & 0xf) + (((a >> 16) & 0xf) << 4);
	}
	return 0;
}

static bool match_cpu_model(int mod, int *models)
{
	int i;
	for (i = 0; models[i]; i++)
		if (models[i] == mod)
			return true;
	return false;
}

/**  
 * mem_stores_event - Return precise mem load event for current CPU.
 * This is an event which supports load address monitoring.
 * Return: raw event, can be put int perf_event_attr->config. 
 * -1 or error.
 */

unsigned mem_loads_event(void)
{
	int mod = get_cpu_model();
	int i;
	for (i = 0; events[i].models; i++)
		if (match_cpu_model(mod, events[i].models))
			return events[i].mem_loads;	
	return -1;
}

/**  
 * mem_stores_event - Return precise mem stores event for current CPU.
 * This is an event which supports load address monitoring.
 * Return: raw event, can be put int perf_event_attr->config. 
 * -1 or error.
 */
unsigned mem_stores_event(void)
{
	int mod = get_cpu_model();
	int i;
	for (i = 0; events[i].models; i++)
		if (match_cpu_model(mod, events[i].models))
			return events[i].mem_stores;
	return -1;
}
