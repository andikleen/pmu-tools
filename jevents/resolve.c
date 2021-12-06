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
#include "jevents.h"
#include <linux/perf_event.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <stdlib.h>
#include <stdbool.h>
#include <unistd.h>
#include <sys/fcntl.h>
#include <glob.h>
#include <assert.h>
#include <ctype.h>

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

#define BITS(x) ((x) == 64 ? -1ULL : (1ULL << (x)) - 1)

static bool try_parse(char *format, char *fmt, __u64 val, __u64 *config, int *err)
{
	int start, end;
	unsigned long long mask;
	int n = sscanf(format, fmt, &start, &end);
	if (n == 1)
		end = start;
	if (n == 0)
		return false;
	mask = BITS(end - start + 1);
	if (val & ~mask) {
		fprintf(stderr, "Value %llu too big for format %s", val, format);
		*err = 1;
		return false;
	}
	*config |= (val & mask) << start;
	return true;
}

/**
 * jevents_update_qual - Update perf_event_attr with event attributes.
 * @qual: String with qualifiers, see below.
 * @attr: perf_event_attr to update
 * @str: Original event, only used for error messages.
 *
 * Update a perf_event_attr with qualifiers after :.
 * Supports most perf qualifiers like p,k,u,I,G etc. (see man perf-list),
 * and special config=0xxx/config1=0xxxx/config2=0xxx to overwrite
 * the raw attribute fields.
 */
int jevents_update_qual(const char *qual, struct perf_event_attr *attr,
			const char *str)
{
	while (*qual) {
		/* Should support more qualifiers, like filter */
		if (!strncmp(qual, "config", 6)) {
			unsigned long long c;
			int skip = 0;

			if (sscanf(qual, "config=%llx%n", &c, &skip) == 1)
				attr->config |= c;
			else if (sscanf(qual, "config1=%llx%n", &c, &skip) == 1)
				attr->config1 |= c;
			else if (sscanf(qual, "config2=%llx%n", &c, &skip) == 1)
				attr->config2 |= c;
			qual += skip;
			if (*qual == 0)
				break;
		}

		switch (*qual) {
		case 'p':
			attr->precise_ip++;
			break;
		case 'k':
			attr->exclude_user = 1;
			attr->exclude_hv = 1;
			break;
		case 'u':
			attr->exclude_kernel = 1;
			attr->exclude_guest = 1;
			attr->exclude_hv = 1;
			break;
		case 'h':
			attr->exclude_user = 1;
			attr->exclude_kernel = 1;
			break;
		case 'H':
			attr->exclude_guest = 1;
			break;
		case 'I':
			attr->exclude_idle = 1;
			break;
		case 'G':
			attr->exclude_host = 1;
			break;
		case 'D':
			attr->pinned = 1;
			break;
		case ':':
			break;
		/* should implement 'P'.  */
		default:
			fprintf(stderr, "Unknown modifier %c at end for %s\n", *qual, str);
			return -1;
		}
		qual++;
	}
	return 0;
}

static bool special_attr(char *name, unsigned long long val,
			 struct perf_event_attr *attr,
			 struct jevent_extra *je, char *term)
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
	if (!strcmp(name, "config")) {
		attr->config |= val;
		return true;
	}
	if (!strcmp(name, "config1")) {
		attr->config1 |= val;
		return true;
	}
	if (!strcmp(name, "config2")) {
		attr->config2 |= val;
		return true;
	}
	if (!strcmp(name, "name")) {
		char nname[500];
		if (je && sscanf(term, "%*[^=]=%499s", nname) != 1)
			return false;
		je->name = strdup(nname + ((nname[0] == '"' || nname[0] == '\'') ? 1 : 0));
		je->name[strcspn(je->name, "\"'")] = 0;
		return true;
	}
	return false;
}

static int parse_terms(char *pmu, char *config, struct perf_event_attr *attr, int recur,
		       struct jevent_extra *extra)
{
	char *format = NULL;
	char *term;

	char *newl = strchr(config, '\n');
	if (newl)
		*newl = 0;

	while ((term = strsep(&config, ",")) != NULL) {
		char name[30];
		int n;
		unsigned long long val = 1;

		n = sscanf(term, "%30[^=]=%lli", name, &val);
		if (n < 1)
			break;
		if (special_attr(name, val, attr, extra, term))
			continue;
		free(format);
		if (read_file(&format, "/sys/devices/%s/format/%s", pmu, name) < 0) {
			char *alias = NULL;

			if (recur == 0 &&
			    read_file(&alias, "/sys/devices/%s/events/%s", pmu, name) == 0) {
				if (parse_terms(pmu, alias, attr, 1, NULL) < 0) {
					free(alias);
					fprintf(stderr, "Cannot parse kernel event alias %s for %s\n", name,
							term);
					break;
				}
				free(alias);
				continue;
			}
			if (n > 1)
				fprintf(stderr, "Cannot open kernel format %s for %s\n", name, term);
			break;
		}
		int err = 0;
		bool ok = try_parse(format, "config:%d-%d", val, &attr->config, &err) ||
			try_parse(format, "config:%d", val, &attr->config, &err) ||
			try_parse(format, "config1:%d-%d", val, &attr->config1, &err) ||
			try_parse(format, "config1:%d", val, &attr->config1, &err);
		bool ok2 = try_parse(format, "config2:%d-%d", val, &attr->config2, &err) ||
			try_parse(format, "config2:%d", val, &attr->config2, &err);
		if ((!ok && !ok2) || err) {
			fprintf(stderr, "Cannot parse kernel format %s: %s for %s\n",
					name, format, term);
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

static int try_pmu_type(char **type, char *fmt, char *pmu, struct jevent_extra *extra)
{
	char newpmu[50];
	snprintf(newpmu, 50, fmt, pmu);
	int ret = read_file(type, "/sys/devices/%s/type", newpmu);
	if (ret >= 0) {
		strcpy(pmu, newpmu);
		if (extra && extra->pmus.gl_pathc == 0) {
			char *fn;
			asprintf(&fn, "/sys/devices/%s", newpmu);
			/* Fill in pmus so that the pmu name is available to users */
			ret = glob(fn, 0, NULL, &extra->pmus);
			free(fn);
		}
	}
	return ret;
}

/**
 * jevent_pmu_name - return pmu names for resolved jevent_extra
 * @extra: resolved jevent_extra
 * @num: number of PMU to return might be returned earlier in next_pmu
 * @next_pmu: pointer to integer. next pmu number that can be passed to next call of jevent_pmu_name.
 * Return:
 * Name of PMU. String will be valid until the extra argument is freed.
 *
 * Iterate through jevent_pmu_name to get all PMUs, setting num to next_num, until it returns NULL.
 * int num, next;
 * char *name;
 * for (num = 0; (name = jevent_pmu_name(&extra, num; &next)) != NULL; num = next) {
 *     ...
 * }
 *
 */
char *jevent_pmu_name(struct jevent_extra *extra, int num, int *next_num)
{
	char *s = NULL;

	if (num < 0) {
		if (next_num)
			*next_num = -1;
		return NULL;
	}
	if (num < extra->pmus.gl_pathc)
		s = extra->pmus.gl_pathv[num] ?
		    strrchr(extra->pmus.gl_pathv[num], '/') + 1 :
		    NULL;
	if (next_num)
		*next_num = num + 1;
	return s;
}

/**
 * jevent_pmu_uncore - Is perf event string for an uncore PMU.
 * @pmu: perf pmu
 * Return true if yes, false if not or unparseable.
 */
bool jevent_pmu_uncore(const char *str)
{
	char *cpumask;
	int cpus;
	char pmu[30];

	if (!strchr(str, '/'))
		return false;
	if (sscanf(str, "%30[^/]", pmu) < 1)
		return false;
	int ret = read_file(&cpumask, "/sys/devices/%s/cpumask", pmu);
	if (ret < 0)
		ret = read_file(&cpumask, "/sys/devices/uncore_%s/cpumask", pmu);
	if (ret < 0)
		ret = read_file(&cpumask, "/sys/devices/uncore_%s_0/cpumask", pmu);
	if (ret < 0)
		ret = read_file(&cpumask, "/sys/devices/uncore_%s_1/cpumask", pmu);
	if (ret < 0)
		return false;
	bool isuncore = sscanf(cpumask, "%d", &cpus) == 1 && cpus == 0;
	free(cpumask);
	return isuncore;
}

/**
 * jevent_free_extra - Free data in jevent_extra
 * @extra: extra structure to free.
 *
 * Note the extra structure itself is not freed, but supplied
 * by the caller.
 */
void jevent_free_extra(struct jevent_extra *extra)
{
	free(extra->name);
	free(extra->decoded);
	globfree(&extra->pmus);
}

/**
 * jevent_copy_extra - Copy extra structure.
 * @dst: Destination
 * @src: Source
 *
 * Result needs to be freed with jevent_free_extra().
 */

void jevent_copy_extra(struct jevent_extra *dst, struct jevent_extra *src)
{
	int len;

	memset(dst, 0, sizeof(struct jevent_extra));
	if (src->name)
		dst->name = strdup(src->name);
	if (src->decoded)
		dst->decoded = strdup(src->decoded);
	dst->pmus.gl_pathc = src->pmus.gl_pathc;
	len = sizeof(char *) * src->pmus.gl_pathc;
	dst->pmus.gl_pathv = malloc(len);
	size_t i;
	for (i = 0; i < src->pmus.gl_pathc; i++) {
		dst->pmus.gl_pathv[i] = strdup(src->pmus.gl_pathv[i]);
	}
}

/**
 * jevent_next_pmu - update multi_pmu attr to next pmu
 *
 * For extra->multi_pmu update the attr to the next pmu in the list.
 * Returns 1 when there was another pmu, 0 when the end of PMUs is
 * reached, or -1 for errors.
 */
int jevent_next_pmu(struct jevent_extra *extra,
		    struct perf_event_attr *attr)
{
	if (!extra->multi_pmu || !extra->pmus.gl_pathv)
		return 0;
	if (extra->next_pmu < extra->pmus.gl_pathc) {
		int n = extra->next_pmu++;
		char pmu[30];
		char *type = NULL;
		if (try_pmu_type(&type,
				 strrchr(extra->pmus.gl_pathv[n], '/'),
				 pmu, NULL) < 0)
			return -1;
		attr->type = atoi(type);
		free(type);
		return 1;
	}
	return 0;
}

/* check_valid_hex - Checks if a string is a valid hex value in
   its entirety. Returns 1 if so, 0 if not. */
int check_valid_hex(char *str)
{
	char *ptr;

	ptr = str;
	while (*ptr) {
		if (((*ptr < '0') || (*ptr > '9')) &&
		   ((*ptr < 'A') || (*ptr > 'F')) &&
		   ((*ptr < 'a') || (*ptr > 'f')))
			return 0;
		ptr++;
	}
	return 1;
}

/* is_valid_cpu_event - Checks if the given string is a valid
   cpu event by checking /sys/devices/cpu/events. Assumes that
   aliases have already been applied. Returns 1 if so, 0 if not,
   -1 on error. */
int check_cpu_event(char *event)
{
	glob_t globbuf;
	char *cur_event;
	int i;

	/* This event might not specify a PMU, but it's possible
	 * for it to begin with a "/". If so, simply remove this
	 * character. */
	if (event[0] == '/')
		memmove(event, event + 1, strlen(event + 1) + 1);

	if (glob("/sys/devices/cpu/events/*", GLOB_NOSORT, NULL, &globbuf) != 0)
		goto err_free;
	for (i = 0; i < globbuf.gl_pathc; i++) {
		cur_event = basename(globbuf.gl_pathv[i]);
		if (!strcmp(cur_event, event)) {
			globfree(&globbuf);
			return 1;
		}
	}

	globfree(&globbuf);
	return 0;
err_free:
	globfree(&globbuf);
	return -1;
}

/**
  remove_glob - Removes a globbed path from the structure.
  @glob: a pointer to a glob_t struct.
  @index: the index to remove from the glob_t struct.

  Note that, if you call this while iterating over indices
  in the glob_t struct, you will need to subtract one from
  your index after calling this.
  Returns 0 on success, -1 on error.
*/
int remove_glob(glob_t *glob, size_t index)
{
	size_t i;

	if (index >= glob->gl_pathc) {
		return -1;
	}

	free(glob->gl_pathv[index]);
	for (i = index + 1; i < glob->gl_pathc; i++) {
		glob->gl_pathv[i - 1] = glob->gl_pathv[i];
	}
	glob->gl_pathc--;

	return 0;
}

/**
 * jevent_name_to_attr_extra - Resolve perf style event to perf_attr
 * @str: perf style event (e.g. cpu/event=1/)
 * @attr: perf_attr to fill in.
 * @extra:  jevent_extra to output extra information, or NULL.
 *
 * Resolve perf new style event descriptor to perf ATTR. User must initialize
 * attr->sample_type and attr->read_format as needed after this call,
 * and possibly other fields. Returns 0 when succeeded.
 *
 * extra is filled in with extra information on the event. It contains
 * allocated data and needs to be freed with jevent_free_extra() later
 * unless an error was returned.
 *
 * Some events may need multiple PMUs. In this case extra->multi_pmu
 * is set, and jevent_next_pmu() must be used to iterate the attr
 * through the extra PMUs.
 */
int jevent_name_to_attr_extra(const char *str, struct perf_event_attr *attr,
			      struct jevent_extra *extra)
{
	char pmu[30], config[200];
	int qual_off = -1;
	struct jevent_extra dummy;

	memset(attr, 0, sizeof(struct perf_event_attr));
	attr->size = PERF_ATTR_SIZE_VER0;
	attr->type = PERF_TYPE_RAW;

	if (!extra)
		extra = &dummy;
	memset(extra, 0, sizeof(struct jevent_extra));

	/* Aliases */
	if (!strcmp(str, "cycles"))
		str = "cpu/cpu-cycles/";
	if (!strcmp(str, "branches"))
		str = "cpu/branch-instructions/";

	/* Raw syntax:
	 * 1. Must begin with an "r."
	 * 2. Must contain only valid hex values.
	 * 3. Optionally ends with a colon followed by qualifiers. */
	if ((sscanf(str, "r%200[^:]%n", config, &qual_off) == 1) && (check_valid_hex(config) == 1)) {
		sscanf(config, "%llx", &attr->config);
		assert(qual_off != -1);
		glob("/sys/devices/cpu", 0, NULL, &extra->pmus);
		if (str[qual_off] == 0)
			return 0;
		if (str[qual_off] == ':' && jevents_update_qual(str + qual_off + 1, attr, str) == 0)
			return 0;
		return -1;
	}

	/* Implicit CPU PMU syntax:
	 * 1. Optionally begins with a slash (nothing before the slash, though).
	 * 2. No other slashes in the string.
	 * 3. Optionally ends with a colon followed by qualifiers. */
	if ((sscanf(str, "%200[^:]%n", config, &qual_off) == 1) && (check_cpu_event(config) == 1)) {
		/* We found the event, so it's valid. */
		if (parse_terms("cpu", config, attr, 0, extra) < 0)
			goto err_free;
		glob("/sys/devices/cpu", 0, NULL, &extra->pmus);
		if (str[qual_off] == 0)
			return 0;
		if (str[qual_off] == ':' && jevents_update_qual(str + qual_off + 1, attr, str) == 0)
			return 0;
		return -1;
	}

	/* PMU-specifying syntax:
		 1. Begins with a PMU type, followed by a slash.
		 2. Includes an event, followed by another slash.
		 3. Per `perf`, cannot include qualifiers. */
	if (sscanf(str, "%30[^/]/%200[^/]/%n", pmu, config, &qual_off) < 2)
		return -1;
	char *type = NULL;
	if (try_pmu_type(&type, "%s", pmu, extra) < 0) {
		if (try_pmu_type(&type, "uncore_%s", pmu, extra) < 0) {
			char *gs;
			int ret;

			/* Glob the uncore PMUs that match this pattern */
			asprintf(&gs, "/sys/devices/uncore_%s_[0-9]*", pmu);
			ret = glob(gs, 0, NULL, &extra->pmus);
			free(gs);
			if (ret)
				return -1;

			/* In the above glob, the pattern "[0-9]*" could match
			   one digit followed by non-digits. Remove these from
			   the list of PMUs (very unlikely). */
			size_t pmui;
			int underscores;
			char *path_ptr;
			for (pmui = 0; pmui < extra->pmus.gl_pathc; pmui++) {
				/* Make path_ptr point to the character after the second
				   underscore. */
				path_ptr = extra->pmus.gl_pathv[pmui];
				underscores = 0;
				while (*path_ptr) {
					if (*path_ptr == '_') {
						underscores++;
					} else if ((underscores > 1) && !isdigit(*path_ptr)) {
						remove_glob(&extra->pmus, pmui);
						pmui--;
						break;
					}
					path_ptr++;
				}
			}

			if (try_pmu_type(&type, strrchr(extra->pmus.gl_pathv[0], '/'), pmu, NULL) < 0)
				goto err_free;
			extra->next_pmu = 0;
			extra->multi_pmu = true;
		}
	}
	attr->type = atoi(type);
	free(type);
	if (parse_terms(pmu, config, attr, 0, extra) < 0)
		goto err_free;
	if (qual_off != -1 && jevents_update_qual(str + qual_off, attr, str) < 0)
		goto err_free;
	if (extra == &dummy)
		jevent_free_extra(extra);
	return 0;

err_free:
	if (extra == &dummy)
		jevent_free_extra(extra);
	return -1;
}

/**
 * jevent_name_to_attr - Resolve perf style event to perf_attr
 * @str: perf style event (e.g. cpu/event=1/)
 * @attr: perf_attr to fill in.
 *
 * Resolve perf new style event descriptor to perf ATTR. User must initialize
 * attr->sample_type and attr->read_format as needed after this call,
 * and possibly other fields. Returns 0 when succeeded.
 *
 * Deprecated. Should migrate to jevent_name_to_attr_extra.
 */
int jevent_name_to_attr(const char *str, struct perf_event_attr *attr)
{
	return jevent_name_to_attr_extra(str, attr, NULL);
}

/**
 * walk_perf_events - walk all kernel supplied perf events
 * @func: Callback function to call for each event.
 * @data: data pointer to pass to func.
 */
int walk_perf_events(int (*func)(void *data, char *name, char *event, char *desc),
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
		ret = func(data, buf, val2, "");
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

/**
 * jevents_socket_cpus - Return a single CPU for each socket.
 * @len: Output argument, set to number of sockets
 * @cpup: Output argument, pointer to array of int for one CPU for each socket
 * Caller must free *cpup afterwards.
 */
int jevents_socket_cpus(int *len, int **cpup)
{
	glob_t g;
	if (glob("/sys/devices/system/cpu/cpu*/topology/physical_package_id", 0, NULL, &g))
		return -1;
	*cpup = calloc(g.gl_pathc, sizeof(int));
	int i;
	*len = 0;
	for (i = 0; i < g.gl_pathc; i++)
		(*cpup)[i] = -1;
	for (i = 0; i < g.gl_pathc; i++) {
		int cpu;
		char *id;
		int pid;
		sscanf(g.gl_pathv[i], "/sys/devices/system/cpu/cpu%d", &cpu);
		if (read_file(&id, g.gl_pathv[i]) < 0) {
			free(*cpup);
			*len = 0;
			return -1;
		}
		sscanf(id, "%d", &pid);
		free(id);
		if ((*cpup)[pid] < 0) {
			(*len)++;
			(*cpup)[pid] = cpu;
		}
		if (cpu < (*cpup)[pid])
			(*cpup)[pid] = cpu;
	}
	globfree(&g);
	return 0;
}

void jevent_print_attr(FILE *f, struct perf_event_attr *attr)
{
	fprintf(f, "type: %d\n", attr->type);
	fprintf(f, "config: %llx\n", attr->config);
	fprintf(f, "read_format: %llx\n", attr->read_format);
	if (attr->sample_type)
		fprintf(f, "sample_type: %llx\n", attr->sample_type);
	fprintf(f, "sample_period/freq: %lld\n", attr->sample_period);
	if (attr->config1)
		fprintf(f, "config1: %llx\n", attr->config1);
	if (attr->config2)
		fprintf(f, "config1: %llx\n", attr->config1);
	fprintf(f, "flags: ");
#define FLAG(fl) if (attr->fl) fprintf(f, "%s ", #fl);
#define FIELD(fl) if (attr->fl) fprintf(f, #fl ": %d ", attr->fl)
	FLAG(disabled);
	FLAG(inherit);
	FLAG(pinned);
	FLAG(exclusive);
	FLAG(exclude_user);
	FLAG(exclude_kernel);
	FLAG(exclude_hv);
	FLAG(exclude_idle);
	FLAG(mmap);
	FLAG(comm);
	FLAG(freq);
	FLAG(inherit_stat);
	FLAG(enable_on_exec);
	FLAG(task);
	FLAG(watermark);
	FLAG(exclude_host);
	FLAG(exclude_guest);
#undef FLAG
	fprintf(f, "\n");
	/* Some stuff missing */
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
