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

#ifndef RDPMC_H
#define RDPMC_H 1

#include <linux/perf_event.h>

struct rdpmc_ctx {
	int fd;
	struct perf_event_mmap_page *buf;
};

int rdpmc_open(unsigned counter, struct rdpmc_ctx *ctx);
int rdpmc_open_attr(struct perf_event_attr *attr, struct rdpmc_ctx *ctx, 
		    struct rdpmc_ctx *leader_ctx);
void rdpmc_close(struct rdpmc_ctx *ctx);
unsigned long long rdpmc_read(struct rdpmc_ctx *ctx);


#endif
