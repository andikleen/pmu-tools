/* Resolve perf event descriptions with symbolic names to raw perf descriptions */
#include "jevents.h"
#include <linux/perf_event.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>

int main(int ac, char **av)
{
	int test = 0;
	int ret = 0;

	while (*++av) {
		if (!strcmp(*av, "--test")) {
			test = 1;
			continue;
		}

		struct perf_event_attr attr;
		if (resolve_event(*av, &attr) < 0) {
			fprintf(stderr, "Cannot resolve %s\n", *av); 
			ret = 1;
			continue;
		}
		char *ev = format_raw_event(&attr, *av);
		printf("%s\n", ev);
		free(ev);
		if (test) {
			if (perf_event_open(&attr, 0, -1, -1, 0) < 0)
				perror("perf_event_open");
		}
	}
	return ret;
}
