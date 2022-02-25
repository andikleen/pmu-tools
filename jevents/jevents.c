/* Parse event JSON files */

/*
 * Copyright (c) 2014, Intel Corporation
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
#include <errno.h>
#include <string.h>
#include <ctype.h>
#include <stdbool.h>
#include <unistd.h>
#include <pwd.h>
#include "jsmn.h"
#include "json.h"
#include "jevents.h"

char *getenv_copy(const char* name)
{
	const char* value = getenv(name);
	return value ? strdup(value) : 0;
}

static const char *json_default_name(char *type)
{
	char *cache = NULL;
	char *idstr_step = NULL;
	char *idstr = get_cpu_str_type(type, &idstr_step);
	char *res = NULL;
	char *home = NULL;
	char *sudo_user = NULL;
	char *emap;
	struct passwd *pwd;
	char free_cache;

	free_cache = 0;
	emap = getenv("EVENTMAP");
	if (emap) {
		if (access(emap, R_OK) == 0)
			return strdup(emap);
		free(idstr);
		if (asprintf(&idstr, "%s%s", emap, type) < 0)
			goto out;
	}

	cache = getenv("JEVENTS_CACHEDIR");
	if (!cache)
		cache = getenv("XDG_CACHE_HOME");
	if (!cache) {
		sudo_user = getenv("SUDO_USER");
		if (sudo_user) {
			/* Get the home directory of the sudo_user */
			pwd = getpwnam(sudo_user);
			if (!pwd)
				goto out;
			free_cache = 1;
			if (asprintf(&cache, "%s/.cache", pwd->pw_dir) < 0) {
				goto out;
			}
		}
	}
	if (!cache) {
		home = getenv("HOME");
		if (home) {
			free_cache = 1;
			if (asprintf(&cache, "%s/.cache", home) < 0)
				goto out;
		}
	}

	if (cache && idstr) {
		asprintf(&res, "%s/pmu-events/%s.json", cache, idstr_step);
		if (access(res, R_OK) != 0) {
			free(res);
			asprintf(&res, "%s/pmu-events/%s.json",
				     cache,
				     idstr);
		}
	}

out:
	if(free_cache)
		free(cache);
	free(idstr);
	free(idstr_step);
	return res;
}

static void addfield(char *map, char **dst, const char *sep,
		     const char *a, jsmntok_t *bt)
{
	unsigned len = strlen(a) + 1 + strlen(sep);
	int olen = *dst ? strlen(*dst) : 0;
	int blen = bt ? json_len(bt) : 0;

	*dst = realloc(*dst, len + olen + blen);
	if (!*dst)
		exit(ENOMEM);
	if (!olen)
		*(*dst) = 0;
	else
		strcat(*dst, sep);
	strcat(*dst, a);
	if (bt)
		strncat(*dst, map + bt->start, blen);
}

static void fixname(char *s)
{
	for (; *s; s++)
		*s = tolower(*s);
}

static void fixdesc(char *s)
{
	char *e;

	if (!s)
		return;

	e = s + strlen(s);

	/* Remove trailing dots that look ugly in perf list */
	--e;
	while (e >= s && isspace(*e))
		--e;
	if (e >= s && *e == '.')
		*e = 0;
}

static struct map {
	const char *json;
	const char *perf;
} unit_to_pmu[] = {
	{ "CBO", "cbox" },
	{ "QPI LL", "qpi" },
	{ "SBO", "sbox" },
	{ "IMPH-U", "cbox" },
	/* FIXME: need to convert event/umask like ocperf for ncu */
	{ "NCU", "cbox" },
	{ "UPI LL", "upi" },
	{}
};

static const char *field_to_perf(struct map *table, char *map, jsmntok_t *val)
{
	int i;

	for (i = 0; table[i].json; i++) {
		if (json_streq(map, val, table[i].json))
			return table[i].perf;
	}
	return NULL;
}

#define EXPECT(e, t, m) do { if (!(e)) {			\
	jsmntok_t *loc = (t);					\
	if (!(t)->start && (t) > tokens)			\
		loc = (t) - 1;					\
	fprintf(stderr, "%s:%d: " m ", got %s\n", fn,		\
		json_line(map, loc),				\
		json_name(t));					\
	goto out_free;						\
} } while (0)

static struct msrmap {
	const char *num;
	const char *pname;
} msrmap[] = {
	{ "0x3F6", "ldlat=" },
	{ "0x1A6", "offcore_rsp=" },
	{ "0x1A7", "offcore_rsp=" },
	{ "0x3F7", "frontend="},
	{ NULL, NULL }
};

static struct field {
	const char *field;
	const char *kernel;
} fields[] = {
	{ "UMask",	"umask=" },
	{ "CounterMask", "cmask=" },
	{ "Invert",	"inv=" },
	{ "AnyThread",	"any=" },
	{ "EdgeDetect",	"edge=" },
	{ "SampleAfterValue", "period=" },
	{ NULL, NULL }
};

static void cut_comma(char *map, jsmntok_t *newval)
{
	int i;

	/* Cut off everything after comma */
	for (i = newval->start; i < newval->end; i++) {
		if (map[i] == ',')
			newval->end = i;
	}
}

static int match_field(char *map, jsmntok_t *field, int nz,
		       char **event, jsmntok_t *val)
{
	struct field *f;
	jsmntok_t newval = *val;

	for (f = fields; f->field; f++)
		if (json_streq(map, field, f->field) && nz) {
			if (json_streq(map, val, "0x00") ||
			     json_streq(map, val, "0x0"))
				return 1;
			cut_comma(map, &newval);
			addfield(map, event, ",", f->kernel, &newval);
			return 1;
		}
	return 0;
}

static struct msrmap *lookup_msr(char *map, jsmntok_t *val)
{
	jsmntok_t newval = *val;
	static bool warned = false;
	int i;

	cut_comma(map, &newval);
	for (i = 0; msrmap[i].num; i++)
		if (json_streq(map, &newval, msrmap[i].num))
			return &msrmap[i];
	if (!warned) {
		warned = true;
		fprintf(stderr, "Unknown MSR in event file %.*s\n",
			json_len(val), map + val->start);
	}
	return NULL;
}

/**
 * json_events - Read JSON event file from disk and call event callback.
 * @fn: File name to read or NULL for default.
 * @func: Callback to call for each event
 * @data: Abstract pointer to pass to func.
 *
 * The callback gets the data pointer, the event name, the event
 * in perf format and a description passed.
 *
 * Call func with each event in the json file
 * Return: negative on failure, otherwise 0.
 */
int json_events(const char *fn,
	  int (*func)(void *data, char *name, char *event, char *desc, char *pmu),
	  void *data)
{
	int err = -EIO;
	size_t size;
	jsmntok_t *tokens, *tok;
	int i, j, len;
	char *map;
	char buf[128];
	const char *orig_fn = fn;

	if (!fn)
		fn = json_default_name("-core");
	if (!fn)
		return -ENOMEM;
	tokens = parse_json(fn, &map, &size, &len);
	if (!tokens) {
		if(!orig_fn)
			free((char *) fn);
		return -EIO;
	}
	EXPECT(tokens->type == JSMN_ARRAY, tokens, "expected top level array");
	tok = tokens + 1;
	for (i = 0; i < tokens->size; i++) {
		char *event = NULL, *desc = NULL, *name = NULL;
		char *pmu = NULL;
		char *filter = NULL;
		unsigned long long eventcode = 0;
		struct msrmap *msr = NULL;
		jsmntok_t *msrval = NULL;
		jsmntok_t *precise = NULL;
		jsmntok_t *obj = tok++;

		EXPECT(obj->type == JSMN_OBJECT, obj, "expected object");
		for (j = 0; j < obj->size; j += 2) {
			jsmntok_t *field, *val;
			int nz;

			field = tok + j;
			EXPECT(field->type == JSMN_STRING, tok + j,
			       "Expected field name");
			val = tok + j + 1;
			EXPECT(val->type == JSMN_STRING, tok + j + 1,
			       "Expected string value");

			nz = !json_streq(map, val, "0") && !json_streq(map, val, "0x00");
			if (match_field(map, field, nz, &event, val)) {
				/* ok */
			} else if (json_streq(map, field, "EventCode")) {
				char *code = NULL;
				addfield(map, &code, "", "", val);
				eventcode |= strtoul(code, NULL, 0);
				free(code);
			} else if (json_streq(map, field, "ExtSel")) {
				char *code = NULL;
				addfield(map, &code, "", "", val);
				eventcode |= strtoul(code, NULL, 0) << 21;
				free(code);
			} else if (json_streq(map, field, "EventName")) {
				addfield(map, &name, "", "", val);
			} else if (json_streq(map, field, "BriefDescription")) {
				addfield(map, &desc, "", "", val);
				fixdesc(desc);
			} else if (json_streq(map, field, "PEBS") && nz && desc &&
				   !strstr(desc, "(Precise Event)")) {
				precise = val;
			} else if (json_streq(map, field, "MSRIndex") && nz) {
				msr = lookup_msr(map, val);
			} else if (json_streq(map, field, "MSRValue")) {
				msrval = val;
			} else if (json_streq(map, field, "Errata") &&
				   !json_streq(map, val, "null")) {
				addfield(map, &desc, ". ",
					" Spec update: ", val);
			} else if (json_streq(map, field, "Data_LA") && nz) {
				addfield(map, &desc, ". ",
					" Supports address when precise",
					NULL);
			} else if (json_streq(map, field, "Unit")) {
				const char *ppmu;
				char *s;

				ppmu = field_to_perf(unit_to_pmu, map, val);
				if (ppmu) {
					pmu = strdup(ppmu);
				} else {
					addfield(map, &pmu, "", "", val);
					for (s = pmu; *s; s++)
						*s = tolower(*s);
				}
				addfield(map, &desc, ". ", "Unit: ", NULL);
				addfield(map, &desc, "", pmu, NULL);
			}
			/* ignore unknown fields */
		}
		if (precise) {
			if (json_streq(map, precise, "2"))
				addfield(map, &desc, " ", "(Must be precise)",
						NULL);
			else
				addfield(map, &desc, " ",
						"(Precise event)", NULL);
		}
		snprintf(buf, sizeof buf, "event=%#llx", eventcode);
		addfield(map, &event, ",", buf, NULL);
		if (filter)
			addfield(map, &event, ",", filter, NULL);
		if (msr != NULL)
			addfield(map, &event, ",", msr->pname, msrval);
		if (!pmu)
			pmu = strdup("cpu");
		if (!desc)
			desc = strdup("No description.");
		err = -EIO;
		if (name && event) {
			fixname(name);
			err = func(data, name, event, desc, pmu);
		}
		free(event);
		free(desc);
		free(name);
		free(pmu);
		free(filter);
		if (err)
			break;
		tok += j;
	}
	EXPECT(tok - tokens == len, tok, "unexpected objects at end");
	err = 0;
out_free:
	free_json(map, size, tokens);
	if (!orig_fn && !err) {
		free((char *)fn);
		fn = json_default_name("-uncore");
		err = json_events(fn, func, data);
		/* Ignore open error */
		if (err == -EIO) {
			free((char *)fn);
			return 0;
		}
	}
	if (!orig_fn)
		free((char *)fn);
	return err;
}
