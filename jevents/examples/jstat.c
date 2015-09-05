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
		uint64_t val[3];
	} efd[0]; /* num_cpus */
};

struct eventlist {
	struct event *eventlist;
	struct event *eventlist_last;
	int num_cpus;
};

bool measure_all;
int measure_pid = -1;
int child_pid = -1;

struct eventlist *alloc_eventlist(void)
{
	struct eventlist *el = calloc(sizeof(struct eventlist), 1);
	if (!el)
		return NULL;
	el->num_cpus = sysconf(_SC_NPROCESSORS_CONF);
	return el;
}

static struct event *new_event(struct eventlist *el, char *s)
{
	struct event *e = calloc(sizeof(struct event) +
				 sizeof(struct efd) * el->num_cpus, 1);
	e->next = NULL;
	if (!el->eventlist)
		el->eventlist = e;
	if (el->eventlist_last)
		el->eventlist_last->next = e;
	el->eventlist_last = e;
	e->event = strdup(s);
	return e;
}

int parse_events(struct eventlist *el, char *events)
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

		struct event *e = new_event(el, s);
		e->group_leader = group_leader;
		e->end_group = end_group;
		if (resolve_event(s, &e->attr) < 0) {
			fprintf(stderr, "Cannot resolve %s\n", e->event);
			return -1;
		}
	}
	free(events);
	return 0;
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

int setup_event(struct event *e, int cpu, struct event *leader)
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
			return 0;

		fprintf(stderr, "Cannot open perf event for %s/%d: %s\n",
				e->event, cpu, strerror(errno));
		return -1;
	}
	return 0;
}

int setup_events(struct eventlist *el)
{
	struct event *e, *leader = NULL;
	int i;

	for (e = el->eventlist; e; e = e->next) {
		for (i = 0; i < el->num_cpus; i++) {
			if (setup_event(e, i, leader) < 0)
				return -1;
		}
		if (e->group_leader)
			leader = e;
		if (e->end_group)
			leader = NULL;
	}
	return 0;
}

int read_event(struct event *e, int cpu)
{
	int n = read(e->efd[cpu].fd, &e->efd[cpu].val, 3 * 8);
	if (n < 0) {
		fprintf(stderr, "Error reading from %s/%d: %s\n",
				e->event, cpu, strerror(errno));
		return -1;
	}
	return 0;
}

int read_data(struct eventlist *el)
{
	struct event *e;
	int i;

	for (e = el->eventlist; e; e = e->next) {
		for (i = 0; i < el->num_cpus; i++) {
			if (e->efd[i].fd < 0)
				continue;
			if (read_event(e, i) < 0)
				return -1;
		}
	}
	return 0;
}

uint64_t event_scaled_value(struct event *e, int cpu)
{
	uint64_t *val = e->efd[cpu].val;
	if (val[1] != val[2] && val[2])
		return val[0] * (double)val[1] / (double)val[2];
	return val[0];
}

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
	setup_events(el);
	signal(SIGINT, sigint);
	if (child_pid >= 0) {
		write(child_pipe[1], "x", 1);
		waitpid(measure_pid, NULL, 0);
	} else {
		pause();
	}
	read_data(el);
	print_data(el);
	return 0;
}
