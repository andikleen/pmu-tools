/*
 * Support for mapping the AUX buffer, e.g. for reading Intel Processor Trace
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

#include <linux/perf_event.h>
#include "perf-iter.h"
#include <sys/mman.h>
#include <stdlib.h>
#include <unistd.h>

/**
 * perf_aux_map - Map AUX buffer for an open perf_fd.
 * @pfd: Already opened perf_fd on PMU supporting aux.
 * @aux: perf_aux structure to store the mapping.
 * @aux_size_shift: log 2 of mapped buffer size in pages.
 * @snapshot: When true the aux buffer will run in continuous ring buffer mode and not stop on overflow.
 *
 * Some perf event PMUs, such as intel_pt, support an extra aux buffer to
 * report raw data from the hardware. Map the AUX buffer for an already
 * mapped perf_fd
 *
 * The aux buffer size is limited by the mlock rlimit, as well as
 * /proc/sys/kernel/perf_event_mlock_kb.
 *
 * Returns -1 if the mapping failed, otherwise 0.
 */
int perf_aux_map(struct perf_fd *pfd, struct perf_aux_map *aux, int aux_size_shift,
		  bool snapshot)
{
	struct perf_event_mmap_page *mp = pfd->mpage;

	mp->aux_offset = perf_mmap_size(pfd->buf_size_shift);
	mp->aux_size = sysconf(_SC_PAGE_SIZE) << aux_size_shift;
	aux->aux_map = mmap(NULL, mp->aux_size,
			    PROT_READ | (snapshot ? 0 : PROT_WRITE),
			    MAP_SHARED,
			    pfd->pfd,
			    mp->aux_offset);
	return aux->aux_map == (void*)-1L ? -1 : 0;
}

/**
 * perf_aux_unmap - Unmap an aux buffer.
 * @pfd: perf_fd passed to perf_aux_map.
 * @aux: Aux structure to unmap.
 */
void perf_aux_unmap(struct perf_fd *pfd, struct perf_aux_map *aux)
{
	munmap(aux->aux_map, pfd->mpage->aux_size);
}
