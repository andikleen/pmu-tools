/* List all events */
/* -v print descriptions */
/* pattern  print only events matching shell pattern */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fnmatch.h>
#include "jevents.h"

int verbose = 0;

static int show_event(void *data, char *name, char *event, char *desc)
{
	if (data && fnmatch((char *)data, name, 0))
		return 0;
	printf("%-40s ", name);
	printf("cpu/%s/\n", event);
	if (verbose)
		printf("\t%s\n", desc); /* XXX word wrap */
	return 0;
}

int main(int ac, char **av)
{
	if (av[1] && !strcmp(av[1], "-v"))
		verbose = 1;

	read_events(NULL);
	walk_events(show_event, av[1]);
	return 0;
}
