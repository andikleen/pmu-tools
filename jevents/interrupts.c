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

/** DOC: Account for interrupts on Intel Core/Xeon systems
 *
 * This is useful for micro benchmarks to filter out measurement
 * samples that are disturbed by a context switch caused by OS
 * noise.
 *
 * Requires a Linux 3.3+ kernel
 */
#include "rdpmc.h"
#include "interrupts.h"

/* Intel Sandy Bridge */
#define HW_INTERRUPTS 0x1cb

static __thread int int_ok = -1;
static __thread struct rdpmc_ctx int_ctx;

/**
 * interrupts_init - Initialize interrupt counter per thread
 *
 * Must be called for each application thread.
 */
void interrupts_init(void)
{
	int_ok = rdpmc_open(HW_INTERRUPTS, &int_ctx);
}

/**
 * interrupts_exit - Free interrupt counter per thread.
 *
 * Must be called for each application thread.
 */
void interrupts_exit(void)
{
	if (int_ok >= 0)
		rdpmc_close(&int_ctx);
}

/**
 * get_interrupts - get current interrupt counter.
 *
 * Get the current hardware interrupt count. When the number changed
 * for a measurement period you had some sort of context switch.
 * The sample for this period should be discarded.
 * This returns absolute numbers.
 */
unsigned long long get_interrupts(void)
{
	if (int_ok >= 0)
		return rdpmc_read(&int_ctx);
	return 0;
}
