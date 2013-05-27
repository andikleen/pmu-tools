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

/* Simple perf library */
#include <linux/perf_event.h>
#include <asm/unistd.h>
#include <unistd.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/unistd.h>
#include <sys/ioctl.h>

#include "util.h"
#include "perf.h"

/* Iterator for perf ring buffer */

void perf_iter_init(struct perf_iter *iter, struct perf_fd *pfd)
{
	int pagesize = sysconf(_SC_PAGESIZE);
	int page_shift = ffs(pagesize) - 1;

	iter->mpage = pfd->mpage;
	iter->bufsize = (1ULL << (pfd->buf_size_shift + page_shift));
	iter->ring_buffer_mask = iter->bufsize - 1;
	iter->cur = iter->mpage->data_tail & iter->ring_buffer_mask;
	/* Kernel only changes head */
	iter->raw_head = iter->mpage->data_head;
	iter->avail = iter->raw_head - iter->mpage->data_tail;
        iter->head = iter->raw_head & iter->ring_buffer_mask;
	mb();
	iter->data = (char *)(iter->mpage) + pagesize;
}

/* Read from the ring buffer */
struct perf_event_header *perf_buffer_read(struct perf_iter *iter, void *buffer, int bufsize)
{
	struct perf_event_header *hdr = (struct perf_event_header *)(iter->data + iter->cur);
	u64 left = iter->bufsize - iter->cur;

	if (left >= sizeof(hdr->size) && hdr->size <= left) { 
		iter->cur += hdr->size;
		iter->avail -= hdr->size;
		/* Copy less fast path */
		return hdr;
	} else {
		/*
		 * Buffer wraps. This case is untested in this example.
		 * Assumes hdr->size is always continuous by itself.
		 */
		if (left == 0) { 
			if (hdr->size > bufsize)
				return NULL;
			memcpy(buffer, hdr, left);
		} else { 
			hdr = (struct perf_event_header *)iter->data;
			if (hdr->size > bufsize)
				return NULL;
		}
		memcpy(buffer + left, iter->data, hdr->size - left);
		iter->cur = hdr->size - left;
		iter->avail -= hdr->size;
		return buffer;
	}
}

/* Allow the kernel to log over our data */
void perf_iter_continue(struct perf_iter *iter)
{
	iter->mpage->data_tail = iter->raw_head;
	mb();
}

static unsigned perf_mmap_size(int buf_size_shift)
{
	return ((1U << buf_size_shift) + 1) * sysconf(_SC_PAGESIZE);
}

/* Open a perf event with ring buffer for the current thread */
int perf_fd_open(struct perf_fd *p, struct perf_event_attr *attr, int buf_size_shift)
{
	p->pfd = syscall(__NR_perf_event_open, attr, 0, -1, -1, 0);
	if (p->pfd < 0)
		return -1;

	struct perf_event_mmap_page *mpage;
	mpage = mmap(NULL,  perf_mmap_size(buf_size_shift),
		    PROT_READ|PROT_WRITE, MAP_SHARED,
		   p->pfd, 0);
	if (mpage == (struct perf_event_mmap_page *)-1L) {
		close(p->pfd);
		return -1;
	}
	p->mpage = mpage;
	p->buf_size_shift = buf_size_shift;
	return 0;
}

void perf_fd_close(struct perf_fd *p)
{
	munmap(p->mpage, perf_mmap_size(p->buf_size_shift));
	close(p->pfd);
	p->mpage = NULL;
}

int perf_enable(struct perf_fd *p)
{
	return ioctl(p->pfd, PERF_EVENT_IOC_ENABLE, 0);
}

int perf_disable(struct perf_fd *p)
{
	return ioctl(p->pfd, PERF_EVENT_IOC_DISABLE, 0);
}
