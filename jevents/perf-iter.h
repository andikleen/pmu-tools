#ifndef _PERF_ITER_H
#define _PERF_ITER_H 1

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

struct perf_event_mmap_page;
struct perf_event_header;

/* Iterator for perf ring buffer */

struct perf_iter {
	uint64_t ring_buffer_mask;
	uint64_t head, cur, raw_head, bufsize;
	int64_t avail;
	char *data;
	struct perf_event_mmap_page *mpage;
};

struct perf_fd { 
	int pfd;
	struct perf_event_mmap_page *mpage;
	int buf_size_shift;
};

struct perf_aux_map {
	void *aux_map;
};

int perf_fd_open(struct perf_fd *p, struct perf_event_attr *attr, int buf_size_shift);
int perf_fd_open_other(struct perf_fd *p, struct perf_event_attr *attr, int buf_size_shift,
		       int pid, int cpu);
void perf_fd_close(struct perf_fd *p);
void perf_iter_continue(struct perf_iter *iter);
struct perf_event_header *perf_buffer_read(struct perf_iter *iter, void *buffer, int bufsize);
void perf_iter_init(struct perf_iter *iter, struct perf_fd *pfd);
int perf_enable(struct perf_fd *p);
int perf_disable(struct perf_fd *p);

unsigned perf_mmap_size(int buf_size_shift);

int perf_aux_map(struct perf_fd *pfd, struct perf_aux_map *aux, int size, bool snapshot);
void perf_aux_unmap(struct perf_fd *pfd, struct perf_aux_map *aux);

static inline int perf_iter_finished(struct perf_iter *iter)
{
	return iter->avail <= 0;
}

static inline uint64_t *perf_hdr_payload(struct perf_event_header *hdr)
{
	return (uint64_t *)(hdr + 1);
}

#ifdef __cplusplus
}
#endif

#endif
