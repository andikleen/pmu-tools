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
/* jstat [-a] [-p pid] [-e events] [-A] [-C cpus] program */
/* Supports named events if downloaded first (w/ event_download.py) */
/* Run listevents to show the available events */

#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <getopt.h>
#include <errno.h>
#include <signal.h>
#include <locale.h>
#include <time.h>
#include <sys/wait.h>
#include <sys/fcntl.h>
#include <sys/time.h>
#include "jevents.h"
#include "jsession.h"

#define err(x) perror(x), exit(1)
#define PAIR(x) x, sizeof(x) - 1

void (*do_print_data)(FILE *outfh, struct eventlist *el, struct session_print *arg) =
	session_print_aggr;

enum { OPT_APPEND = 1000, OPT_MERGE };

static struct option opts[] = {
	{ "all-cpus", no_argument, 0, 'a' },
	{ "events", required_argument, 0, 'e'},
	{ "interval", required_argument, 0, 'I' },
	{ "cpu", required_argument, 0, 'C' },
	{ "no-aggr", no_argument, 0, 'A' },
	{ "verbose", no_argument, 0, 'v' },
	{ "append", no_argument, 0, OPT_APPEND },
	{ "delay", required_argument, 0, 'D' },
	{ "merge", no_argument, 0, OPT_MERGE },
	{},
};

struct session_print parg;

void usage(void)
{
	fprintf(stderr, "Usage: jstat [-a] [-e events] [-I interval] [-C cpus] [-A] program\n"
			"--all -a            Measure global system\n"
			"-e --events list    Comma separate list of events to measure. Use {} for groups\n"
			"-I N --interval N   Print events every N ms\n"
			"-C CPUS --cpu CPUS  Only measure on CPUs. List of numbers or ranges a-b\n"
			"-A --no-aggr        Print values for individual CPUs\n"
			"-v --verbose        Print perf_event_open arguments\n"
			"-o file             Output results to file\n"
			"--append            (with -o) Append results to file\n"
			"-D N --delay N      Wait N ms after starting program before measurement\n"
			"--merge             Sum multiple instances of uncore events\n"
			"Run event_download.py once first to use symbolic events\n"
			"Run listevents to show available events\n");

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
	struct timespec ts;
	clock_gettime(CLOCK_MONOTONIC, &ts);
	return (double)ts.tv_sec + ts.tv_nsec/1e9;
}

void print_data(FILE *outfh, struct eventlist *el, double timestamp, bool print_ts)
{
	char ts[SESSION_TIMESTAMP_LEN];
	if (print_ts) {
		session_print_timestamp(ts, sizeof ts, timestamp);
		parg.prefix = ts;
	}
	do_print_data(outfh, el, &parg);
}

bool cont_measure(FILE *outfh, int ret, struct eventlist *el)
{
	if (ret < 0 && gotalarm) {
		gotalarm = false;
		read_all_events(el);
		print_data(outfh, el, gettime() - starttime, true);
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
	char *cpumask = NULL;
	int verbose = 0;
	char *openmode = "w";
	char *outname = NULL;
	int initial_delay = 0;
	int flags = 0;
	FILE *outfh = stderr;

	setlocale(LC_NUMERIC, "");
	el = alloc_eventlist();

	while ((opt = getopt_long(ac, av, "ae:p:I:C:Avo:D:x:", opts, NULL)) != -1) {
		switch (opt) {
		case 'e':
			if (parse_events(el, optarg) < 0) {
				free_eventlist(el);
				exit(1);
			}
			events = NULL;
			break;
		case 'a':
			measure_all = true;
			flags |= SE_MEASURE_ALL;
			break;
		case 'I':
			interval = atoi(optarg);
			break;
		case 'C':
			cpumask = optarg;
			break;
		case 'A':
			do_print_data = session_print;
			break;
		case 'v':
			verbose++;
			break;
		case OPT_APPEND:
			openmode = "a";
			break;
		case OPT_MERGE:
			parg.merge = true;
			break;
		case 'x':
			/* Implies -A for now */
			do_print_data = session_print_csv;
			parg.sep = optarg;
			break;
		case 'o':
			outname = optarg;
			break;
		case 'D':
			initial_delay = atoi(optarg);
			break;
		default:
			usage();
		}
	}
	if (outname) {
		outfh = fopen(outname, openmode);
		if (!outfh) {
			fprintf(stderr, "Cannot open %s: %s\n", optarg,
					strerror(errno));
			free_eventlist(el);
			exit(1);
		}
	}
	if (av[optind] == NULL && !measure_all) {
		fprintf(stderr, "Specify command or -a\n");
		usage();
	}
	if (events && parse_events(el, events) < 0) {
		free_eventlist(el);
		exit(1);
	}
	pipe(child_pipe);
	signal(SIGCHLD, SIG_IGN);
	child_pid = measure_pid = fork();
	if (measure_pid < 0)
		err("fork");
	if (measure_pid == 0) {
		char buf;
		/* Wait for events to be set up */
		if (!initial_delay)
			read(child_pipe[0], &buf, 1);
		if (av[optind] == NULL) {
			pause();
			_exit(0);
		}
		execvp(av[optind], av + optind);
		write(2, PAIR("Cannot execute program\n"));
		_exit(1);
	}
	if (initial_delay)
		usleep(initial_delay * 1000);
	if (initial_delay == 0 && !measure_all)
		flags |= SE_ENABLE_ON_EXEC;

	if (setup_events_cpumask(el, measure_pid, cpumask, flags) < 0)
		exit(1);
	if (verbose)
		print_event_list_attr(el, stdout);
	signal(SIGINT, sigint);
	if (interval) {
		struct itimerval itv = {
			.it_value = {
				.tv_sec = interval / 1000,
				.tv_usec = (interval % 1000) * 1000,
			},
		};
		itv.it_interval = itv.it_value;

		sigaction(SIGALRM, &(struct sigaction){
				.sa_handler = sigalarm,
			 }, NULL);
		starttime = gettime();
		setitimer(ITIMER_REAL, &itv, NULL);
	}
	if (child_pid >= 0) {
		write(child_pipe[1], "x", 1);
		do
			ret = waitpid(measure_pid, NULL, 0);
		while (cont_measure(outfh, ret, el));
	} else {
		do
			ret = pause();
		while (cont_measure(outfh, ret, el));
	}
	read_all_events(el);
	print_data(outfh, el, gettime() - starttime,
		   interval != 0 && starttime);
	free_eventlist(el);
	return 0;
}
