/*
 * Copyright (c) 2012,2013 Intel Corporation
 * Author: Andi Kleen
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that: (1) source code distributions
 * retain the above copyright notice and this paragraph in its entirety, (2)
 * distributions including binary code include the above copyright notice and
 * this paragraph in its entirety in the documentation or other materials
 * provided with the distribution
 *
 * THIS SOFTWARE IS PROVIDED ``AS IS'' AND WITHOUT ANY EXPRESS OR IMPLIED
 * WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
 */


#ifndef MEASURE_H
#define MEASURE_H 1

#include <stdio.h>

#define N_COUNTER 4

struct measure {
	char *name;
	unsigned long long counter;
	int ratio_to; /* or -1 */
	unsigned long long (*func)(struct measure *m, 
			           unsigned long long total[N_COUNTER], int i);
};

#ifdef EVENT_MACROS
#define ETO(x,y) { #x, x, y }
#define ETO0(x) ETO(x, 0)
#define E(x) { #x, x, -1 }
#define EFUNC(x,y, f) { #x, x, y, f }
#endif

void measure_group_init(struct measure *g, char *name);
void measure_group_start(void);
void measure_group_stop(void);
void measure_group_finish(void);
void measure_print_all(FILE *fh);
void measure_free_all(void);



#endif
