#include "jevents.h"
#include <linux/perf_event.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/syscall.h>

int main(int ac, char **av)
{
	while (*++av) {
		struct perf_event_attr attr;
		resolve_event(*av, &attr);
		printf("config %llu config1 %llu config2 %llu\n", attr.config, attr.config1, attr.config2);
		if (syscall(__NR_perf_event_open, &attr, 0, -1, -1, 0) < 0)
			perror("perf_event_open");
	}
	return 0;
}
