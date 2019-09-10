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

#include <cpuid.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <linux/perf_event.h>

#include "cpu.h"
#include "jevents.h"

/**  
 * mem_stores_event - Return precise mem load event for current CPU.
 * This is an event which supports load address monitoring.
 * Return: raw event, can be put int perf_event_attr->config. 
 * -1 or error.
 */

unsigned mem_loads_event(void)
{
	struct perf_event_attr attr;

	if (!resolve_event("MEM_INST_RETIRED.LOAD_LATENCY_ABOVE_THRESHOLD_0", &attr) ||
	    !resolve_event("MEM_TRANS_RETIRED.LOAD_LATENCY_GT_4", &attr))
		return attr.config;
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
	struct perf_event_attr attr;

	if (!resolve_event("MEM_INST_RETIRED.ALL_STORES", &attr) ||
	    !resolve_event("MEM_UOPS_RETIRED.ALL_STORES", &attr))
		return attr.config;
	return -1;
}
