/*
 * Copyright (c) 2014, Intel Corporation
 * Author: Andi Kleen
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 * this list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright
 * notice, this list of conditions and the following disclaimer in the
 * documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 * COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
 * INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
*/

#define _GNU_SOURCE 1
#include <stdio.h>
#include <stdlib.h>
#include "jevents.h"

/**
 * get_cpu_str - Return string describing the current CPU or NULL.
 * Needs to be freed by caller.
 *
 * Used to store JSON event lists in the cache directory.
 */
char *get_cpu_str(void)
{
	return get_cpu_str_type("-core", NULL);
}

/**
 * get_cpu_str - Return string describing the current CPU for type or NULL.
 * @type: "-core" or "-uncore"
 * @idstr_step: if non NULL write idstr with stepping to pointer.
 * Both result and idstr_step (if non NULL) need to be freed by
 * caller.
 */
char *get_cpu_str_type(char *type, char **idstr_step)
{
	char *line = NULL;
	size_t llen = 0;
	int found = 0, n;
	char vendor[30];
	int model = 0, fam = 0, step = 0;
	char *res = NULL;
	FILE *f = fopen("/proc/cpuinfo", "r");

	if (!f)
		return NULL;
	while (getline(&line, &llen, f) > 0) {
		if (sscanf(line, "vendor_id : %29s", vendor) == 1)
			found++;
		else if (sscanf(line, "model : %d", &model) == 1)
			found++;
		else if (sscanf(line, "cpu family : %d", &fam) == 1)
			found++;
		else if (sscanf(line, "stepping : %d", &step) == 1)
			found++;
		if (found == 4) {
			if (idstr_step)
				asprintf(idstr_step, "%s-%d-%X-%X%s", vendor, fam,
						model, step, type);
			n = asprintf(&res, "%s-%d-%X%s", vendor, fam, model,
					type);
			if (n < 0)
				res = NULL;
			break;
		}
	}
	free(line);
	fclose(f);
	return res;
}
