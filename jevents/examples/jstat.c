/* Poor man's perf stat using jevents */
/* jstat [-a] [-p pid] [-e events] program */
/* Supports named events if downloaded first (w/ event_download.py) */
/* Run listevents to show the available events */

#include <linux/perf_event.h>
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdint.h>
#include <errno.h>
#include <string.h>
#include <getopt.h>
#include <stdbool.h>
#include <unistd.h>
#include <signal.h>
#include <locale.h>
#include <sys/wait.h>
#include <sys/syscall.h>
#include <sys/fcntl.h>
#include "jevents.h"

#define err(x) perror(x), exit(1)
#define PAIR(x) x, sizeof(x) - 1

struct event {
	struct event *next;
	struct perf_event_attr attr;
	char *event;
	bool end_group, group_leader;
	struct efd {
		int fd;
		uint64_t val;
	} efd[0]; /* num_cpus */
};

struct event *eventlist;
struct event *eventlist_last;
int num_cpus;
bool measure_all;
int measure_pid = -1;
int child_pid = -1;

struct event *new_event(char *s)
{
	struct event *e = calloc(sizeof(struct event) + sizeof(struct efd)*num_cpus, 1);
	e->next = NULL;
	if (!eventlist)
		eventlist = e;
	if (eventlist_last)
		eventlist_last->next = e;
	eventlist_last = e;
	e->event = strdup(s);
	return e;
}

void parse_events(char *events)
{
	char *s, *tmp;

	events = strdup(events);
	for (s = strtok_r(events, ",", &tmp);
	     s;
	     s = strtok_r(NULL, ",", &tmp)) {
		bool group_leader = false, end_group = false;
		int len;

		if (s[0] == '{') {
			s++;
			group_leader = true;
		} else if (len = strlen(s), len > 0 && s[len - 1] == '}') {
			s[len - 1] = 0;
			end_group = true;
		}

		struct event *e = new_event(s);
		e->group_leader = group_leader;
		e->end_group = end_group;
		if (resolve_event(s, &e->attr) < 0) {
			fprintf(stderr, "Cannot resolve %s\n", e->event);
			exit(1);
		}
	}
	free(events);
}

static bool cpu_online(int i)
{
	bool ret = false;
	char fn[100];
	sprintf(fn, "/sys/devices/system/cpu/cpu%d/online", i);
	int fd = open(fn, O_RDONLY);
	if (fd >= 0) {
		char buf[128];
		int n = read(fd, buf, 128);
		if (n > 0 && !strncmp(buf, "1", 1))
			ret = true;
		close(fd);
	}
	return ret;
}

void setup_event(struct event *e, int cpu, struct event *leader)
{
	e->attr.inherit = 1;
	if (!measure_all) {
		e->attr.disabled = 1;
		e->attr.enable_on_exec = 1;
	}
	e->attr.read_format = PERF_FORMAT_TOTAL_TIME_ENABLED |
				PERF_FORMAT_TOTAL_TIME_RUNNING;

	e->efd[cpu].fd = perf_event_open(&e->attr,
			measure_all ? -1 : measure_pid,
			cpu,
			leader ? leader->efd[cpu].fd : -1,
			0);

	if (e->efd[cpu].fd < 0) {
		/* Handle offline CPU */
		if (errno == EINVAL && !cpu_online(cpu))
			return;

		fprintf(stderr, "Cannot open perf event for %s/%d: %s\n",
				e->event, cpu, strerror(errno));
		exit(1);
	}
}

void setup_events(void)
{
	struct event *e, *leader = NULL;
	int i;

	for (e = eventlist; e; e = e->next) {
		for (i = 0; i < num_cpus; i++) {
			setup_event(e, i, leader);
		}
		if (e->group_leader)
			leader = e;
		if (e->end_group)
			leader = NULL;
	}
}

void read_event(struct event *e, int cpu)
{
	uint64_t val[3];
	e->efd[cpu].val = 0;
	int n = read(e->efd[cpu].fd, &val, sizeof(val));
	if (n < 0) {
		fprintf(stderr, "Error reading from %s/%d: %s\n",
				e->event, cpu, strerror(errno));
		return;
	}
	e->efd[cpu].val = val[0];
	if (val[1] != val[2] && val[2])
		e->efd[cpu].val *= (double)val[1] / (double)val[2];
}

void read_data(void)
{
	struct event *e;
	int i;

	for (e = eventlist; e; e = e->next) {
		for (i = 0; i < num_cpus; i++) {
			if (e->efd[i].fd < 0)
				continue;
			read_event(e, i);
		}
	}
}

void print_data(void)
{
	struct event *e;
	int i;

	for (e = eventlist; e; e = e->next) {
		uint64_t v = 0;
		for (i = 0; i < num_cpus; i++)
			v += e->efd[i].val;
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

	setlocale(LC_NUMERIC, "");
	num_cpus = sysconf(_SC_NPROCESSORS_CONF);

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
	parse_events(events);
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
	setup_events();
	signal(SIGINT, sigint);
	if (child_pid >= 0) {
		write(child_pipe[1], "x", 1);
		waitpid(measure_pid, NULL, 0);
	} else {
		pause();
	}
	read_data();
	print_data();
	return 0;
}
