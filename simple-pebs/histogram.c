/* Print histograms from simple-pebs output. */

#include <stdio.h>
#include <assert.h>
#include <stdlib.h>
#include "map.h"
#include "elf.h"
#include "symtab.h"

typedef unsigned long long u64;

#define err(x) perror(x), exit(1)

static int cmp_sym_hits(const void *ap, const void *bp)
{
	const struct sym *a = ap;
	const struct sym *b = bp;
	return a->hits - b->hits;
}

double min_percent = 1.0;

void print_histogram(u64 *map, int num)
{
	int i;
	unsigned long total = 0, unknown = 0;
	struct sym *ref_next = NULL;
	struct sym *referenced = NULL;

	int num_referenced = 0;

	for (i = 0; i < num; i++) {
		struct sym *sym = findsym(map[i]);
		if (sym) {
			if (sym->hits == 0) {
				if (!referenced) {
					referenced = sym;
					ref_next = sym;
				}
				ref_next->link = sym;
				num_referenced++;
			}
			sym->hits++;
		} else
			unknown++;
		total++;
	}
	if (total == 0) {
		printf("no samples found\n");
		return;
	}

	struct sym **ref = malloc(num_referenced * sizeof(struct sym *));
	struct sym *link;
	i = 0;
	for (link = referenced; link; link = link->link, i++)
		ref[i] = link;
	assert(i == num_referenced);

	qsort(ref, num_referenced, sizeof(struct sym *), cmp_sym_hits);

	printf("%5s %8s  %s\n", "PCT", "HITS", "NAME");
	printf("%5.2f%% %8lu unknown hits\n", 100. * ((double)unknown / total),
			unknown);
	for (i = 0; i < num_referenced; i++) {
		struct sym *sym = ref[i];
		double pct = 100. * ((double)sym->hits / total);
		if (pct <= min_percent)
			break;
		printf("%5.2f%% %8lu %s\n", pct, sym->hits, sym->name);
	}
}


void usage(void)
{
	fprintf(stderr, "Usage: histogram file elf ...\n");

}

int main(int ac, char **av)
{
	char *file = *++av;

	if (!file)
		usage();
	while (*++av)
		read_elf(*av);

	size_t fsize;
	u64 *fmap = mapfile(file, &fsize);

	if (!fmap)
		err(file);
	print_histogram(fmap,  fsize / 8);
	return 0;
}
