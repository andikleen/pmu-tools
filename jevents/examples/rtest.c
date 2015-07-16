/* Demonstrate self profiling for context switches */
#include <sys/time.h>
#include <stdio.h>
#include <stdlib.h>
#include "rdpmc.h"

#define HW_INTERRUPTS 0x1cb

typedef unsigned long long u64;

u64 get_time(void)
{
	struct timeval tv;
	gettimeofday(&tv, NULL);
	return (u64)tv.tv_sec * 1000000 + tv.tv_usec;
}

int main(int ac, char **av)
{
	int i;
	int cswitch = 0;
	struct rdpmc_ctx ctx;
	int iter = 10000;

	if (av[1])
		iter = atoi(av[1]);
	
	if (rdpmc_open(HW_INTERRUPTS, &ctx) < 0)
		exit(1);

	u64 t0 = get_time();
	u64 prev = rdpmc_read(&ctx);
	for (i = 0; i < iter; i++) {
		u64 n = rdpmc_read(&ctx);
		if (n != prev) {
			cswitch++;
			prev = n;
		}
	}
			
	u64 t1 = get_time();
	
	printf("%d interrupts, %llu usec duration\n", cswitch, t1-t0);

	rdpmc_close(&ctx);
	return 0;
}
