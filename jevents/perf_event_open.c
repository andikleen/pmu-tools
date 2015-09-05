/* Until glibc provides a proper stub ... */
#include <linux/perf_event.h>
#include <unistd.h>
#include <sys/syscall.h>

/* If someone else has a better one we use that */

__attribute__((weak))
int perf_event_open(struct perf_event_attr *attr, pid_t pid,
		    int cpu, int group_fd, unsigned long flags)
{
	return syscall(__NR_perf_event_open, attr, pid, cpu, group_fd, flags);
}
