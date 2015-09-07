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

#include <gelf.h>
#include <unistd.h>
#include <sys/fcntl.h>
#include <string.h>
#include <stdio.h>
#include <errno.h>
#include <stdlib.h>
#include "symtab.h"
#include "elf.h"

static char *my_strdup(char *s)
{
	char *p = malloc(strlen(s) + 1);
	if (p)
		strcpy(p, s);
	return p;
}

void read_symtab(Elf *elf)
{
	Elf_Scn *section = NULL;

	while ((section = elf_nextscn(elf, section)) != 0) {
		GElf_Shdr shdr, *sh;
		sh = gelf_getshdr(section, &shdr);

		if (sh->sh_type == SHT_SYMTAB || sh->sh_type == SHT_DYNSYM) {
			Elf_Data *data = elf_getdata(section, NULL);
			GElf_Sym *sym, symbol;
			int j;

			unsigned numsym = sh->sh_size / sh->sh_entsize;
			struct symtab *st = add_symtab(numsym);
			for (j = 0; j < numsym; j++) {
				struct sym *s;
				sym = gelf_getsymshndx(data, NULL, j, &symbol, NULL);
				s = &st->syms[j];
				s->name = my_strdup(elf_strptr(elf, shdr.sh_link, sym->st_name));
				s->val = sym->st_value;
				s->size = sym->st_size;
				s->hits = 0;
			}
			sort_symtab(st);
		}
	}
}


static Elf *elf_open(char *fn, int *fd)
{
	*fd = open(fn, O_RDONLY);
	if (*fd < 0) {
		perror(fn);
		return NULL;
	}
	Elf *elf = elf_begin(*fd, ELF_C_READ, NULL);
	if (!elf) {
		fprintf(stderr, "elf_begin failed for %s: %s\n",
				fn, elf_errmsg(-1));
		close(*fd);
	}
	return elf;
}

static void elf_close(Elf *elf, int fd)
{
	elf_end(elf);
	close(fd);
}

int read_elf(char *fn)
{
	elf_version(EV_CURRENT);

	int fd;
	Elf *elf = elf_open(fn, &fd);
	if (elf == NULL)
		return -1;
	read_symtab(elf);
	elf_close(elf, fd);
	return 0;
}
