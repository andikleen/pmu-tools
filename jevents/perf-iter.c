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

/**
 * DOC: A simple perf library to manage the perf ring buffer
 *
 * This library provides a simple wrapping layer for the perf 
 * mmap ring buffer. This allows to access perf events in 
 * zero-copy from a user program.
 */

#include <linux/perf_event.h>
#include <unistd.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/unistd.h>
#include <sys/ioctl.h>
#include "jevents.h"

#include "util.h"
#include "perf-iter.h"

/**
 * perf_iter_init - Initialize iterator for perf ring buffer
 * @iter: Iterator to initialize.
 * @pfd: perf_fd from perf_fd_open() to use with the iterator.
 *
 * Needs to be called first to start walking a perf buffer.
 */

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

/**
 * perf_buffer_read - Access data in perf ring iterator.
 * @iter: Iterator to copy data from
 * @buffer: Temporary buffer to use for wrapped events
 * @bufsize: Size of buffer
 *
 * Return the next available perf_event_header in the ring buffer.
 * This normally does zero copy, but for wrapped events
 * they are copied into the temporary buffer supplied and a
 * pointer into that is returned.
 *
 * Return: NULL when nothing available, otherwise perf_event_header.
 */

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

/**
 * perf_iter_continue - Allow the kernel to log over our data.
 * @iter: Iterator.
 * Tell the kernel we are finished with the data and it can
 * continue logging.
 */

void perf_iter_continue(struct perf_iter *iter)
{
	iter->mpage->data_tail = iter->raw_head;
	mb();
}

static unsigned perf_mmap_size(int buf_size_shift)
{
	return ((1U << buf_size_shift) + 1) * sysconf(_SC_PAGESIZE);
}

/**
 * perf_fd_open - Open a perf event with ring buffer for the current thread 
 * @p: perf_fd to initialize
 * @attr: perf event attribute to use
 * @buf_size_shift: log2 of buffer size.
 * Return: -1 on error, otherwise 0.
 */
int perf_fd_open(struct perf_fd *p, struct perf_event_attr *attr, int buf_size_shift)
{
	p->pfd = perf_event_open(attr, 0, -1, -1, 0);
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

/**
 * perf_fd_close - Close perf_fd
 * @p: pfd to close.
 */

void perf_fd_close(struct perf_fd *p)
{
	munmap(p->mpage, perf_mmap_size(p->buf_size_shift));
	close(p->pfd);
	p->mpage = NULL;
}

/**
 * perf_enable - Start perf collection on pfd
 * @p: perf fd
 * Return: -1 for error, otherwise 0.
 */

int perf_enable(struct perf_fd *p)
{
	return ioctl(p->pfd, PERF_EVENT_IOC_ENABLE, 0);
}

/**
 * perf_enable - Stop perf collection on pfd
 * @p: perf fd
 * Return: -1 for error, otherwise 0.
 */
int perf_disable(struct perf_fd *p)
{
	return ioctl(p->pfd, PERF_EVENT_IOC_DISABLE, 0);
}
