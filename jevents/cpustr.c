#define _GNU_SOURCE 1
#include <stdio.h>
#include <stdlib.h>
#include "jevents.h"

/**
 * get_cpu_str - Return string describing the current CPU
 *
 * Used to store JSON event lists in the cache directory.
 */
char *get_cpu_str(void)
{
	char *line = NULL;
	size_t llen = 0;
	int found = 0, n;
	char vendor[30];
	int model, fam;
	char *res = NULL;
	FILE *f = fopen("/proc/cpuinfo", "r");

	if (!f)
		return NULL;
	while (getline(&line, &llen, f) > 0) {
		if (sscanf(line, "vendor_id : %30s", vendor) == 1)
			found++;
		else if (sscanf(line, "model : %d", &model) == 1)
			found++;
		else if (sscanf(line, "cpu family : %d", &fam) == 1)
			found++;
		if (found == 3) {
			n = asprintf(&res, "%s-%d-%X-core", vendor, fam, model);
			if (n < 0)
				res = NULL;
			break;
		}
	}
	free(line);
	fclose(f);
	return res;
}
