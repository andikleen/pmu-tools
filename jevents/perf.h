typedef unsigned long long u64;
typedef long long s64;

struct perf_event_mmap_page;
struct perf_event_header;

/* Iterator for perf ring buffer */

struct perf_iter {
	u64 ring_buffer_mask;	
	u64 head, cur, raw_head, bufsize;
	s64 avail;
	char *data;
	struct perf_event_mmap_page *mpage;
};

struct perf_fd { 
	int pfd;
	struct perf_event_mmap_page *mpage;
	int buf_size_shift;
};

int perf_fd_open(struct perf_fd *p, struct perf_event_attr *attr, int buf_size_shift);
void perf_fd_close(struct perf_fd *p);
void perf_iter_continue(struct perf_iter *iter);
struct perf_event_header *perf_buffer_read(struct perf_iter *iter, void *buffer, int bufsize);
void perf_iter_init(struct perf_iter *iter, struct perf_fd *pfd);
int perf_enable(struct perf_fd *p);
int perf_disable(struct perf_fd *p);

static inline int perf_iter_finished(struct perf_iter *iter)
{
	return iter->avail <= 0;
}

static inline u64 *perf_hdr_payload(struct perf_event_header *hdr)
{
	return (u64 *)(hdr + 1);
}

