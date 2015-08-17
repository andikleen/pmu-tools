/* Dump sample data from linux kernel driver and resolve IPs */
#include <unistd.h>
#include <sys/mman.h>
#include <sys/fcntl.h>
#include <sys/ioctl.h>
#include <stdio.h>
#include <poll.h>
#include <stdlib.h>
#include <stdint.h>

#include "simple-pebs.h"
#include "dump-util.h"
#include "elf.h"
#include "symtab.h"

#define err(x) perror(x), exit(1)

static void print_ip(uint64_t ip)
{
	struct sym *sym = findsym(ip);
	if (sym) {
		printf("%s", sym->name);
		if (ip - sym->val > 0)
			printf("+%ld", ip - sym->val);
	} else
		printf("%lx", ip);
}

void dump_data(int cpunum, u64 *map, int num)
{
	int i;
	printf("dump %d\n", num);
	for (i = 0; i < num; i++) {
		printf("%d: %lx ", cpunum, map[i]);
		print_ip(map[i]);
		putchar('\n');
	}
}

int main(int ac, char **av)
{
	int size = get_size();
	int ncpus = sysconf(_SC_NPROCESSORS_ONLN);
	void *map[ncpus];
	struct pollfd pfd[ncpus];

	while (*++av) {
		printf("reading %s\n", *av);
		read_elf(*av);
	}

	int i;
	for (i = 0; i < ncpus; i++)
		open_cpu(&map[i], i, &pfd[i], size);

	for (;;) {
		if (poll(pfd, ncpus, -1) < 0)
			perror("poll");
		for (i = 0; i < ncpus; i++) {
			if (pfd[i].revents & POLLIN) {
				int len;

				if (ioctl(pfd[i].fd, SIMPLE_PEBS_GET_OFFSET, &len) < 0) {
					perror("SIMPLE_PEBS_GET_OFFSET");
					continue;
				}

				/* copy out data */
				dump_data(i, map[i], len / sizeof(u64));

				if (ioctl(pfd[i].fd, SIMPLE_PEBS_RESET, 0) < 0) {
					perror("SIMPLE_PEBS_RESET");
					continue;
				}
			}
		}
	}
	return 0;
}
