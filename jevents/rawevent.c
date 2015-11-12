/* Output raw events in perf form. */
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

#include <linux/perf_event.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "jevents.h"

#define BUFS 1024

/** 
 * format_raw_event - Format a resolved event for perf's command line tool
 * @attr: Previously resolved perf_event_attr.
 * @name: Name to add to the event or NULL.
 * Return a string of the formatted event. The caller must free string.
 */

char *format_raw_event(struct perf_event_attr *attr, char *name)
{
	char buf[BUFS];
	int off = 0;
	char *pmu;

	pmu = resolve_pmu(attr->type);
	if (!pmu)
		return NULL;
	off = snprintf(buf, BUFS, "%s/config=%#llx", pmu, attr->config);
	free(pmu);
	if (attr->config1)
		off += sprintf(buf + off, ",config1=%#llx", attr->config1);
	if (attr->config2)
		off += sprintf(buf + off, ",config2=%#llx", attr->config2);
	if (name)
		off += snprintf(buf + off, BUFS - off, ",name=%s", name);
	off += snprintf(buf + off, BUFS - off, "/");
	return strdup(buf);
}
