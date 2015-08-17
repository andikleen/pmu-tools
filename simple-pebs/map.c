#include "map.h"

#ifdef __linux__

#include <sys/mman.h>
#include <sys/fcntl.h>
#include <unistd.h>
#include <stddef.h>
#include <sys/stat.h>

#define round_up(x, y) (((x) + (y) - 1) & ~((y) - 1))

static int pagesize;

static void __attribute__((constructor)) init_ps(void)
{
	pagesize = sysconf(_SC_PAGESIZE);
}

void *mapfile(char *fn, size_t *size)
{
	int fd = open(fn, O_RDWR);
	if (fd < 0)
		return NULL;
	struct stat st;
	void *map = (void *)-1L;
	if (fstat(fd, &st) >= 0) {
		*size = st.st_size;
		map = mmap(NULL, round_up(st.st_size, pagesize),
			   PROT_READ|PROT_WRITE,
			   MAP_PRIVATE, fd, 0);
	}
	close(fd);
	return map != (void *)-1L ? map : NULL;
}

void unmapfile(void *map, size_t size)
{
	munmap(map, round_up(size, pagesize));
}

#else
/* Fallback based on stdio */
#include <stdio.h>
#include <stdlib.h>

void *mapfile(char *fn, size_t *size)
{
	FILE *f = fopen(fn, "r");
	char *map;
	int ok;
	if (!f)
		return NULL;
	fseek(f, 0, SEEK_END);
	*size = ftell(f);
	rewind(f);
	map = malloc(*size);
	ok = map && fread(map, 1, *size, f) == *size;
	fclose(f);
	if (!ok) {
		free(map);
		map = NULL;
	}
	return map;
}

void unmapfile(void *map, size_t size)
{
	free(map);
}

#endif
