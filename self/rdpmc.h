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

