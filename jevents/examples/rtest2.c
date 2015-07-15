/* Measure a thousand sins */
#include <stdio.h>
#include <stdlib.h>
#include <linux/perf_event.h>
#include <math.h>
#include "interrupts.h"
#include "rdpmc.h"

/* Requires a Intel Sandy or Ivy Bridge CPU for the interrupt test,
   On others it may loop forever, unless you disable the interrupt test.
   This is not a realistic test of real performance because it's too
   predictable for cache and branch predictors,
   see http://halobates.de/blog/p/227 */

#define ITER 1000
typedef unsigned long long u64;

volatile double var = 10.0;
volatile double var2;

int main(void)
{
	struct rdpmc_ctx ctx;
	int warmup = 0;
		
	if (rdpmc_open(PERF_COUNT_HW_CPU_CYCLES, &ctx) < 0)
		exit(1);
	interrupts_init();
	for (;;) {
		int i;
	        u64 start_int;
		u64 a, b;

		start_int = get_interrupts();		
		a = rdpmc_read(&ctx);
		for (i = 0; i < ITER; i++)
			var2 += sin(var);
		b = rdpmc_read(&ctx);
		if (get_interrupts() == start_int && warmup > 0) {
			printf("%u sin() took %llu cycles avg\n", ITER, (b-a)/ITER);
			break;
		}
		warmup++;
	}
	interrupts_exit();	
	rdpmc_close(&ctx);
	return 0;
}
