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

#define err(x) perror(x), exit(1)

int device_open(void)
{
	int fd = open("/dev/simple-pebs", O_RDONLY);
	if (fd < 0)
		err("/dev/simple-pebs open");
	return fd;
}

int get_size(void)
{
	int fd = device_open();
	int size;

	if (ioctl(fd, SIMPLE_PEBS_GET_SIZE, &size) < 0)
		err("SIMPLE_PEBS_GET_SIZE");
	close(fd);
	printf("size %d\n", size);
	return size;
}

void open_cpu(void **mapp, int cnum, struct pollfd *pfd, int size)
{
	int fd = device_open();
	if (ioctl(fd, SIMPLE_PEBS_SET_CPU, cnum) < 0)
		err("SIMPLE_PEBS_SET_CPU");
	if (ioctl(fd, SIMPLE_PEBS_START, 0) < 0)
		err("SIMPLE_PEBS_START");
	void *map = mmap(NULL, size, PROT_READ, MAP_PRIVATE, fd, 0);
	if (map == (void *)-1)
		err("mmap");
	*mapp = map;
	pfd->fd = fd;
	pfd->events = POLLIN;
}
