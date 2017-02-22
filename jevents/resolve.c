/* Resolve perf style event descriptions to attr */
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
#include <linux/perf_event.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <stdlib.h>
#include <stdbool.h>
#include <unistd.h>
#include <sys/fcntl.h>
#include <glob.h>

#ifndef PERF_ATTR_SIZE_VER1
#define PERF_ATTR_SIZE_VER1	72
#endif

#define MAXFILE 4096

static int read_file(char **val, const char *fmt, ...)
{
	char *fn;
	va_list ap;
	int fd;
	int ret = -1;
	int len;

	*val = malloc(MAXFILE);	
	va_start(ap, fmt);
	vasprintf(&fn, fmt, ap);
	va_end(ap);
	fd = open(fn, O_RDONLY);
	free(fn);
	if (fd >= 0) {
		if ((len = read(fd, *val, MAXFILE - 1)) > 0) {
			ret = 0;
			(*val)[len] = 0;
		}
		close(fd);
	}
	if (ret < 0) {
		free(*val);
		*val = NULL;
	}
	return ret;
}

#define BITS(x) ((1U << (x)) - 1)

static bool try_parse(char *format, char *fmt, __u64 val, __u64 *config)
{
	int start, end;
	int n = sscanf(format, fmt, &start, &end);
	if (n == 1)
		end = start + 1;
	if (n == 0)
		return false;
	*config |= (val & BITS(end - start + 1)) << start;
	return true;
}

static int read_qual(char *qual, struct perf_event_attr *attr)
{
	while (*qual) {
		switch (*qual) { 
		case 'p':
			attr->precise_ip++;
			break;
		case 'k':
			attr->exclude_user = 1;
			break;
		case 'u':
			attr->exclude_kernel = 1;
			break;
		case 'h':
			attr->exclude_guest = 1;
			break;
		/* XXX more */
		default:
			fprintf(stderr, "Unknown modifier %c at end\n", *qual);
			return -1;
		}
		qual++;
	}
	return 0;
}

static bool special_attr(char *name, int val, struct perf_event_attr *attr)
{
	if (!strcmp(name, "period")) {
		attr->sample_period = val;
		return true;
	}
	if (!strcmp(name, "freq")) {
		attr->sample_freq = val;
		attr->freq = 1;
		return true;
	}
	return false;
}

static int parse_terms(char *pmu, char *config, struct perf_event_attr *attr, int recur)
{
	char *format = NULL;
	char *term;

	char *newl = strchr(config, '\n');
	if (newl)
		*newl = 0;

	while ((term = strsep(&config, ",")) != NULL) {
		char name[30];
		int n, val = 1;

		n = sscanf(term, "%30[^=]=%i", name, &val);
		if (n < 1)
			break;
		if (special_attr(name, val, attr))
			continue;
		free(format);
		if (read_file(&format, "/sys/devices/%s/format/%s", pmu, name) < 0) {
			char *alias = NULL;

			if (recur == 0 &&
			    read_file(&alias, "/sys/devices/%s/events/%s", pmu, name) == 0) {
				if (parse_terms(pmu, alias, attr, 1) < 0) {
					free(alias);
					fprintf(stderr, "Cannot parse kernel event alias %s\n", name);
					break;
				}
				free(alias);
				continue;
			}
			fprintf(stderr, "Cannot parse qualifier %s\n", name);
			break;
		}
		bool ok = try_parse(format, "config:%d-%d", val, &attr->config) ||
			try_parse(format, "config:%d", val, &attr->config) ||
			try_parse(format, "config1:%d-%d", val, &attr->config1) ||
			try_parse(format, "config1:%d", val, &attr->config1);
		bool ok2 = try_parse(format, "config2:%d-%d", val, &attr->config2) ||
			try_parse(format, "config2:%d", val, &attr->config2);
		if (!ok && !ok2) {
			fprintf(stderr, "Cannot parse kernel format %s: %s\n",
					name, format);
			break;
		}
		if (ok2)
			attr->size = PERF_ATTR_SIZE_VER1;
	}
	free(format);
	if (term)
       		return -1;
	return 0;
}

static int try_pmu_type(char **type, char *fmt, char *pmu)
{
	char newpmu[30];
	snprintf(newpmu, 30, fmt, pmu);
	int ret = read_file(type, "/sys/devices/%s/type", newpmu);
	if (ret >= 0)
		strcpy(pmu, newpmu);
	return ret;
}

/**
 * jevent_name_to_attr - Resolve perf style event to perf_attr
 * @str: perf style event (e.g. cpu/event=1/)
 * @attr: perf_attr to fill in.
 *
 * Resolve perf new style event descriptor to perf ATTR. User must initiali
 * attr->sample_type and attr->read_format as needed after this call,
 * and possibly other fields. Returns 0 when succeeded.
 */
int jevent_name_to_attr(char *str, struct perf_event_attr *attr)
{
	char pmu[30], config[200];
	int qual_off;

	memset(attr, 0, sizeof(struct perf_event_attr));
	attr->size = PERF_ATTR_SIZE_VER0;
	attr->type = PERF_TYPE_RAW;

	if (sscanf(str, "r%llx%n", &attr->config, &qual_off) == 1) {
		if (str[qual_off] == 0)
			return 0;
		if (str[qual_off] == ':' && read_qual(str + qual_off, attr) == 0)
			return 0;
		return -1;
	}
	if (sscanf(str, "%30[^/]/%200[^/]/%n", pmu, config, &qual_off) < 2)
		return -1;
	char *type = NULL;
	/* FIXME need interface for multiple outputs and try more instances */
	if (try_pmu_type(&type, "%s", pmu) < 0 &&
	    try_pmu_type(&type, "uncore_%s", pmu) < 0 &&
	    try_pmu_type(&type, "uncore_%s_0", pmu) < 0 &&
	    try_pmu_type(&type, "uncore_%s_1", pmu) < 0)
		return -1;
	attr->type = atoi(type);
	free(type);
	if (parse_terms(pmu, config, attr, 0) < 0)
		return -1;
	if (read_qual(str + qual_off, attr) < 0)
		return -1;
	return 0;
}

/**
 * walk_perf_events - walk all kernel supplied perf events
 * @func: Callback function to call for each event.
 * @data: data pointer to pass to func.
 */
int walk_perf_events(int (*func)(void *data, char *name, char *event, char *desc, char *pmu),
		     void *data)
{
	int ret = 0;
	glob_t g;
	if (glob("/sys/devices/*/events/*", 0, NULL, &g) != 0)
		return -1;
	int i;
	for (i = 0; i < g.gl_pathc; i++) {
		char pmu[32], event[32];

		if (sscanf(g.gl_pathv[i], "/sys/devices/%30[^/]/events/%30s",
			   pmu, event) != 2) {
			fprintf(stderr, "No match on %s\n", g.gl_pathv[i]);
			continue;
		}
		if (strchr(event, '.'))
			continue;


		char *val;
		if (read_file(&val, g.gl_pathv[i])) {
			fprintf(stderr, "Cannot read %s\n", g.gl_pathv[i]);
			continue;
		}
		char *s;
		for (s = val; *s; s++) {
			if (*s == '\n')
				*s = 0;
		}
		char *val2;
		asprintf(&val2, "%s/%s/", pmu, val);
		free(val);

		char *buf;
		asprintf(&buf, "%s/%s/", pmu, event);
		ret = func(data, buf, val2, "", pmu);
		free(val2);
		free(buf);
		if (ret)
			break;
	}
	globfree(&g);
	return ret;
}

/* Should cache pmus. Caller must free return value. */
char *resolve_pmu(int type)
{
	glob_t g;
	if (glob("/sys/devices/*/type", 0, NULL, &g))
		return NULL;
	int i;
	char *pmun = NULL;
	for (i = 0; i < g.gl_pathc; i++) {
		char pmu[30];
		if (sscanf(g.gl_pathv[i], "/sys/devices/%30[^/]/type", pmu) != 1)
			continue;
		char *numbuf;
		int num;
		if (read_file(&numbuf, g.gl_pathv[i]) < 0 ||
		    sscanf(numbuf, "%d", &num) != 1)
			break;
		if (num == type) {
			pmun = strdup(pmu);
			break;
		}
	}
	globfree(&g);
	return pmun;
}

#ifdef TEST
#include "jevents.h"
int main(int ac, char **av)
{
	struct perf_event_attr attr =  { 0 };
	int ret = 1;

	if (!av[1]) {
		printf("Usage: ... perf-event-to-parse\n");
		exit(1);
	}
	while (*++av) {
		if (jevent_name_to_attr(*av, &attr) < 0)
			printf("cannot parse %s\n", *av);
		printf("config %llx config1 %llx\n", attr.config, attr.config1);
		int fd;
		if ((fd = perf_event_open(&attr, 0, -1, -1, 0)) < 0)
			perror("perf_event_open");
		else
			ret = 0;
		close(fd);
	}
	return ret;
}
#endif
