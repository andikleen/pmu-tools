
#include <sys/time.h>
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include "rdpmc.h"

typedef unsigned long long u64;
typedef long long s64;

u64 get_time(void)
{
	struct timeval tv;
	gettimeofday(&tv, NULL);
	return (u64)tv.tv_sec * 1000000 + tv.tv_usec;
}

volatile int interrupted;

void stop(int sig)
{
	interrupted = 1;
}

int main(int ac, char **av)
{
	int i;
	struct rdpmc_ctx ctx;
	int thresh = 10000;

	if (av[1])
		thresh = atoi(av[1]);
	
	if (rdpmc_open(0, &ctx) < 0)
		exit(1);

	signal(SIGINT, stop);

	printf("Press Ctrl-C to stop\n");

	u64 prev = rdpmc_read(&ctx);

	i = 0;
	while (!interrupted) { 
		u64 next = rdpmc_read(&ctx);
		s64 delta = next - prev;

		if (delta > thresh)
			printf("%d: %lld\n", i, delta);

		prev = next;
		i++;
	}
			
	rdpmc_close(&ctx);
	return 0;
}
