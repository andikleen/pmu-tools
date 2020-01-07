/*
 * Copyright (c) 2015, Intel Corporation
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
#include <sys/time.h>
#include "jevents.h"
#include "jsession.h"

#define err(x) perror(x), exit(1)
#define PAIR(x) x, sizeof(x) - 1

void print_data(struct eventlist *el, double ts, bool print_ts)
{
	struct event *e;
	int i;

	for (e = el->eventlist; e; e = e->next) {
		uint64_t v = 0;
		for (i = 0; i < el->num_cpus; i++)
			v += event_scaled_value(e, i);
		if (print_ts)
			printf("%08.4f\t", ts);
		printf("%-30s %'15lu\n", e->extra.name ? e->extra.name : e->event, v);
	}
}

static struct option opts[] = {
	{ "all-cpus", no_argument, 0, 'a' },
	{ "events", required_argument, 0, 'e'},
	{ "interval", required_argument, 0, 'I' },
	{},
};

void usage(void)
{
	fprintf(stderr, "Usage: jstat [-a] [-e events] [-I interval] program\n"
			"--all -a	    Measure global system\n"
			"-e --events list    Comma separate list of events to measure. Use {} for groups\n"
			"-I N --interval N   Print events every N ms\n"
			"Run event_download.py once first to use symbolic events\n");
	exit(1);
}

void sigint(int sig) {}

volatile bool gotalarm;

double starttime;

void sigalarm(int sig)
{
	gotalarm = true;
}

double gettime(void)
{
	struct timeval tv;
	gettimeofday(&tv, NULL);
	return (double)tv.tv_sec * 1e6 + tv.tv_usec;
}

bool cont_measure(int ret, struct eventlist *el)
{
	if (ret < 0 && gotalarm) {
		gotalarm = false;
		read_all_events(el);
		if (!starttime)
			starttime = gettime();
		print_data(el, (gettime() - starttime) / 1e6, true);
		return true;
	}
	return false;
}

int main(int ac, char **av)
{
	char *events = "instructions,cpu-cycles,cache-misses,cache-references";
	int opt;
	int child_pipe[2];
	struct eventlist *el;
	bool measure_all = false;
	int measure_pid = -1;
	int interval = 0;
	int child_pid;
	int ret;

	setlocale(LC_NUMERIC, "");
	el = alloc_eventlist();

	while ((opt = getopt_long(ac, av, "ae:p:I:", opts, NULL)) != -1) {
		switch (opt) {
		case 'e':
			if (parse_events(el, optarg) < 0)
				exit(1);
			events = NULL;
			break;
		case 'a':
			measure_all = true;
			break;
		case 'I':
			interval = atoi(optarg);
			break;
		default:
			usage();
		}
	}
	if (av[optind] == NULL && !measure_all) {
		fprintf(stderr, "Specify command or -a\n");
		exit(1);
	}
	if (events && parse_events(el, events) < 0)
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
		if (av[optind] == NULL) {
			pause();
			_exit(0);
		}
		execvp(av[optind], av + optind);
		write(2, PAIR("Cannot execute program\n"));
		_exit(1);
	}
	if (setup_events(el, measure_all, measure_pid) < 0)
		exit(1);
	signal(SIGINT, sigint);
	if (interval) {
		struct itimerval itv = {
			.it_value = {
				.tv_sec = interval / 1000,
				.tv_usec = (interval % 1000) * 1000
			},
		};
		itv.it_interval = itv.it_value;

		sigaction(SIGALRM, &(struct sigaction){
				.sa_handler = sigalarm,
			 }, NULL);
		setitimer(ITIMER_REAL, &itv, NULL);
	}
	if (child_pid >= 0) {
		write(child_pipe[1], "x", 1);
		for (;;) {
			ret = waitpid(measure_pid, NULL, 0);
			if (!cont_measure(ret, el))
				break;
		}
	} else {
		for (;;) {
			ret = pause();
			if (!cont_measure(ret, el))
				break;
		}
	}
	read_all_events(el);
	print_data(el, 0, false);
	return 0;
}
