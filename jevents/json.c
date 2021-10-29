/* Parse JSON files using the JSMN parser. */

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

#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/fcntl.h>
#include <stdio.h>
#include <unistd.h>
#include "jsmn.h"
#include "json.h"
#include <linux/kernel.h>

static char *mapfile(const char *fn, size_t *size)
{
	struct stat st;
	char *map = NULL;
	int err;
	int fd = open(fn, O_RDONLY);

	if (fd < 0)
		return NULL;
	err = fstat(fd, &st);
	if (err < 0)
		goto out;
	*size = st.st_size;
	map = mmap(NULL, st.st_size, PROT_READ|PROT_WRITE, MAP_PRIVATE, fd, 0);
	if (map == (char *)MAP_FAILED)
		map = NULL;
out:
	close(fd);
	return map;
}

static void unmapfile(char *map, size_t size)
{
	munmap(map, size);
}

/*
 * Parse json file using jsmn. Return array of tokens,
 * and mapped file. Caller needs to free array.
 */
jsmntok_t *parse_json(const char *fn, char **map, size_t *size, int *len)
{
	jsmn_parser parser;
	jsmntok_t *tokens;
	jsmnerr_t res;
	unsigned sz;

	*map = mapfile(fn, size);
	if (!*map)
		return NULL;
	/* Heuristic */
	sz = *size * 16;
	tokens = calloc(1, sz);
	if (!tokens)
		goto error;
	jsmn_init(&parser);
	res = jsmn_parse(&parser, *map, *size, tokens,
			 sz / sizeof(jsmntok_t));
	if (res != JSMN_SUCCESS) {
		fprintf(stderr, "%s: json error %d\n", fn, res);
		goto error_free;
	}
	if (len)
		*len = parser.toknext;
	return tokens;
error_free:
	free(tokens);
error:
	unmapfile(*map, *size);
	return NULL;
}

void free_json(char *map, size_t size, jsmntok_t *tokens)
{
	free(tokens);
	unmapfile(map, size);
}

static int countchar(char *map, char c, int end)
{
	int i;
	int count = 0;
	for (i = 0; i < end; i++)
		if (map[i] == c)
			count++;
	return count;
}

/* Return line number of a jsmn token */
int json_line(char *map, jsmntok_t *t)
{
	return countchar(map, '\n', t->start) + 1;
}

static const char *jsmn_types[] = {
	[JSMN_PRIMITIVE] = "primitive",
	[JSMN_ARRAY] = "array",
	[JSMN_OBJECT] = "object",
	[JSMN_STRING] = "string"
};

#define LOOKUP(a, i) ((i) < (sizeof(a)/sizeof(*(a))) ? ((a)[i]) : "?")

/* Return type name of a jsmn token */
const char *json_name(jsmntok_t *t)
{
	return LOOKUP(jsmn_types, t->type);
}

int json_len(jsmntok_t *t)
{
	return t->end - t->start;
}

/* Is string t equal to s? */
int json_streq(char *map, jsmntok_t *t, const char *s)
{
	unsigned len = t->end - t->start;
	return len == strlen(s) && !strncasecmp(map + t->start, s, len);
}
