#include <stdlib.h>
#include <stdio.h>
#include <errno.h>
#include "symtab.h"

struct symtab *symtabs;

struct symtab *add_symtab(unsigned num)
{
	struct symtab *st = malloc(sizeof(struct symtab));
	if (!st)
		exit(ENOMEM);
	st->num = num;
	st->next = symtabs;
	st->syms = calloc(num * sizeof(struct sym), 1);
	if (!st->syms)
		exit(ENOMEM);
	symtabs = st;
	return st;
}

int cmp_sym(const void *ap, const void *bp)
{
	const struct sym *a = ap;
	const struct sym *b = bp;
	if (a->val >= b->val && a->val < b->val + b->size)
		return 0;
	if (b->val >= a->val && b->val < a->val + a->size)
		return 0;
	return a->val - b->val;
}

struct sym *findsym(unsigned long val)
{
	struct symtab *st;
	struct sym search = { .val = val }, *s;
	for (st = symtabs; st; st = st->next) {
		s = bsearch(&search, st->syms,  st->num, sizeof(struct sym), cmp_sym);
		if (s)
			return s;
	}
	return NULL;
}

void dump_symtab(struct symtab *st)
{
	int j;
	for (j = 0; j < st->num; j++) {
		struct sym *s = &st->syms[j];
		if (s->val && s->name[0])
			printf("%lx %s\n", s->val, s->name);
	}
}

void sort_symtab(struct symtab *st)
{
	qsort(st->syms, st->num, sizeof(struct sym), cmp_sym);
}
