/* Poor man's perf stat using jevents */
/* jstat [-a] [-p pid] [-e events] program */
/* Supports named events if downloaded first (w/ event_download.py) */
/* Run listevents to show the available events */

#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <getopt.h>
#include <signal.h>
#include <locale.h>
#include <sys/wait.h>
#include <sys/fcntl.h>
#include "jevents.h"
#include "jsession.h"

#define err(x) perror(x), exit(1)
#define PAIR(x) x, sizeof(x) - 1

void print_data(struct eventlist *el)
{
	struct event *e;
	int i;

	for (e = el->eventlist; e; e = e->next) {
		uint64_t v = 0;
		for (i = 0; i < el->num_cpus; i++)
			v += event_scaled_value(e, i);
		printf("%-30s %'10lu\n", e->event, v);
	}
}

static struct option opts[] = {
	{ "all", no_argument, 0, 'a' },
	{ "events", required_argument, 0, 'e'},
	{},
};

void usage(void)
{
	fprintf(stderr, "Usage: jstat [-a] [-e events] program\n"
			"--all -a  Measure global system\n"
			"-e --events list  Comma separate list of events to measure. Use {} for groups\n"
			"Run event_download.py once first to use symbolic events\n");
	exit(1);
}

void sigint(int sig) {}

int main(int ac, char **av)
{
	char *events = "instructions,cpu-cycles,cache-misses,cache-references";
	int opt;
	int child_pipe[2];
	struct eventlist *el;
	bool measure_all = false;
	int measure_pid = -1;
	int child_pid;

	setlocale(LC_NUMERIC, "");
	el = alloc_eventlist();

	while ((opt = getopt_long(ac, av, "ae:p:", opts, NULL)) != -1) {
		switch (opt) {
		case 'e':
			events = optarg;
			break;
		case 'a':
			measure_all = true;
			break;
		default:
			usage();
		}
	}
	if (parse_events(el, events) < 0)
		exit(1);
	pipe(child_pipe);
	signal(SIGCHLD, SIG_IGN);
	child_pid = measure_pid = fork();
	if (measure_pid < 0)
		err("fork");
	if (measure_pid == 0) {
		char buf;
		/* Wait for events to be set up */
		read(child_pipe[0], &buf, 1);
		execvp(av[optind], av + optind);
		write(2, PAIR("Cannot execute program\n"));
		_exit(1);
	}
	setup_events(el, measure_all, measure_pid);
	signal(SIGINT, sigint);
	if (child_pid >= 0) {
		write(child_pipe[1], "x", 1);
		waitpid(measure_pid, NULL, 0);
	} else {
		pause();
	}
	read_all_events(el);
	print_data(el);
	return 0;
}
