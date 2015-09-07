/* Generate files in perf.data format from raw PEBS ip file */
/* toperf pebs-ip-file elffile ... > perf.data */

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


#include <elf.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <stdint.h>
#include <assert.h>
#include <linux/perf_event.h>
#include "map.h"

#define err(x) perror(x), exit(1)

#define EVENT 0x1234
#define PERIOD 100003
#define PATH_MAX 4096

struct perf_file_section {
	uint64_t offset;
	uint64_t size;
};

struct perf_file_attr {
	struct perf_event_attr	attr;
	struct perf_file_section	ids;
};

struct perf_file_header {
	uint64_t magic;
	uint64_t size;
	uint64_t attr_size;
	struct perf_file_section	attrs;
	struct perf_file_section	data;
	/* event_types is ignored */
	struct perf_file_section	event_types;
	/*DECLARE_BITMAP(adds_features, HEADER_FEAT_BITS);*/
	char adds_features[32];
};

struct perf_header {
	char magic[8];
	uint64_t size;
	uint64_t attr_size;
	struct perf_file_section attrs;
	struct perf_file_section data;
	struct perf_file_section event_types;
	uint64_t flags;
	uint64_t pad[3];
};

struct mmap_event {
	struct perf_event_header	header;
	uint32_t			pid, tid;
	uint64_t			start;
	uint64_t			len;
	uint64_t			pgoff;
	char				filename[];
};

struct mmap2_event {
	struct perf_event_header header;
	uint32_t pid, tid;
	uint64_t start;
	uint64_t len;
	uint64_t pgoff;
	uint32_t maj;
	uint32_t min;
	uint64_t ino;
	uint64_t ino_generation;
	uint32_t prot;
	uint32_t flags;
	char filename[PATH_MAX];
};

struct comm_event {
	struct perf_event_header header;
	uint32_t pid, tid;
	char comm[16];
};

struct sample_event {
	struct perf_event_header	header;
	uint64_t array[2];
};

#define DATA_OFFSET 2048

void init_header(FILE *f)
{
	fseek(f, DATA_OFFSET, SEEK_SET); /* we write the header later */
}

void gen_attr(FILE *out)
{
	struct perf_event_attr attr;
	struct perf_file_attr f_attr;
	memset(&attr, 0, sizeof(struct perf_event_attr));
	attr.type = PERF_TYPE_RAW;
	attr.size = sizeof(struct perf_event_attr);
	attr.config = EVENT;
	attr.sample_period = PERIOD;
	attr.sample_type = PERF_SAMPLE_IP | PERF_SAMPLE_TID;
	attr.read_format = 0;
	f_attr = (struct perf_file_attr){
		.attr = attr,
		.ids = {
			.offset = sizeof(struct perf_file_header) + 0 * sizeof(uint64_t),
			.size = 0 * sizeof(uint64_t),
		}
	};
	fwrite(&f_attr, sizeof(struct perf_file_attr), 1, out);
}

void gen_header(FILE *out)
{
	struct perf_file_header h;
	size_t datasize;
	int num_attrs = 1;

	memset(&h, 0, sizeof(struct perf_file_header));
	datasize = ftell(out) - DATA_OFFSET;
	fseek(out, 0, SEEK_SET);
	memcpy(&h.magic, "PERFILE2", 8);
	h.size = sizeof(struct perf_file_header);
	h.attr_size = sizeof(struct perf_file_attr);
	h.attrs.offset = sizeof(struct perf_file_header);
	h.attrs.size = num_attrs * sizeof(struct perf_file_attr);
	h.data.offset = DATA_OFFSET;
	h.data.size = datasize;
	assert(sizeof(struct perf_file_header) + sizeof(struct perf_event_attr) < DATA_OFFSET);
	fwrite(&h, sizeof(struct perf_file_header), 1, out);

	gen_attr(out);
}

struct elf32_hdr {
	unsigned char e_ident[16];
	uint16_t e_type;
	uint16_t e_machine;
	uint32_t e_version;
	uint32_t e_entry;
	uint32_t e_phoff;
	uint32_t e_shoff;
	uint32_t e_flags;
	uint16_t e_ehsize;
	uint16_t e_phentsize;
	uint16_t e_phnum;
	uint16_t e_shentsize;
	uint16_t e_shnum;
	uint16_t e_shstrndx;
};

struct elf64_hdr {
	unsigned char e_ident[16];
	uint16_t e_type;
	uint16_t e_machine;
	uint32_t e_version;
	uint64_t e_entry;
	uint64_t e_phoff;
	uint64_t e_shoff;
	uint32_t e_flags;
	uint16_t e_ehsize;
	uint16_t e_phentsize;
	uint16_t e_phnum;
	uint16_t e_shentsize;
	uint16_t e_shnum;
	uint16_t e_shstrndx;
};

#define ELFCLASS32      1
#define ELFCLASS64      2
#define ELFDATA2LSB     1

struct elf32_phdr {
	uint32_t p_type;
	uint32_t p_offset;
	uint32_t p_vaddr;
	uint32_t p_paddr;
	uint32_t p_filesz;
	uint32_t p_memsz;
	uint32_t p_flags;
	uint32_t p_align;
};

struct elf64_phdr {
	uint32_t p_type;
	uint32_t p_flags;
	uint64_t p_offset;
	uint64_t p_vaddr;
	uint64_t p_paddr;
	uint64_t p_filesz;
	uint64_t p_memsz;
	uint64_t p_align;
};

struct elf32_shdr {
	uint32_t sh_name;
	uint32_t sh_type;
	uint32_t sh_flags;
	uint32_t sh_addr;
	uint32_t sh_offset;
	uint32_t sh_size;
	uint32_t sh_link;
	uint32_t sh_info;
	uint32_t sh_addralign;
	uint32_t sh_entsize;
};

struct elf64_shdr {
	uint32_t sh_name;
	uint32_t sh_type;
	uint64_t sh_flags;
	uint64_t sh_addr;
	uint64_t sh_offset;
	uint64_t sh_size;
	uint32_t sh_link;
	uint32_t sh_info;
	uint64_t sh_addralign;
	uint64_t sh_entsize;
};

#define PT_LOAD	 1

#define PAGE_SHIFT	12

uint64_t get_load_address(char *fn, uint64_t *pgoff, uint64_t *len)
{
	size_t size;
	struct elf32_hdr *elf32 = mapfile(fn, &size);
	struct elf64_hdr *elf64 = (struct elf64_hdr *)elf32;
	int use64 = 0;
	char *end = (char *)elf32 + size;
	struct elf32_phdr *phdr32;
	struct elf64_phdr *phdr64;
	int i;
	uint64_t addr = -1L;
	uint64_t end_addr = 0;

	if (!elf32) {
		perror(fn);
		return 0;
	}

	/* check ident */
	if (elf32->e_ident[0] != 0x7f ||
	    elf32->e_ident[1] != 'E' ||
	    elf32->e_ident[2] != 'L' ||
	    elf32->e_ident[3] != 'F' ||
	    (elf32->e_ident[4] != ELFCLASS32 &&
	     elf32->e_ident[4] != ELFCLASS64) ||
	    elf32->e_ident[5] != ELFDATA2LSB) {
		fprintf(stderr, "%s not an LE ELF file\n", fn);
		goto out;
	}
	*pgoff = 0;

	if (elf32->e_ident[4] == ELFCLASS64)
		use64 = 1;

	/* find load addr */
	if (use64) {
		phdr64 = (struct elf64_phdr *)((char *)elf64 + elf64->e_phoff);
		for (i = 0; i < elf64->e_phnum; i++, phdr64++) {
			if (phdr64->p_flags & PF_X) {
				if ((char *)(phdr64 + 1) > end || (char *)phdr64 < (char *)elf64) {
					fprintf(stderr, "%s has bad phdr64 offset\n", fn);
					goto out;
				}
				if (phdr64->p_vaddr < addr) {
					*pgoff = phdr64->p_offset >> PAGE_SHIFT;
					addr = phdr64->p_vaddr;
				}
				if (phdr64->p_vaddr + phdr64->p_memsz > end_addr)
					end_addr = phdr64->p_vaddr + phdr64->p_memsz;
			}
		}
	} else {
		phdr32 = (struct elf32_phdr *)((char *)elf32 + elf32->e_phoff);
		for (i = 0; i < elf32->e_phnum; i++, phdr32++) {
			if ((char *)(phdr32 + 1) > end || (char *)phdr32 < (char *)elf32) {
				fprintf(stderr, "%s has bad phdr32 offset\n", fn);
				goto out;
			}
			if (phdr32->p_vaddr < addr) {
				*pgoff = phdr32->p_offset >> PAGE_SHIFT;
				addr = phdr32->p_vaddr;
			}
			if (phdr32->p_vaddr + phdr32->p_memsz > end_addr)
				end_addr = phdr32->p_vaddr + phdr32->p_memsz;
		}
	}
	*len = ((end_addr - addr + (1 << PAGE_SHIFT) - 1) / (1 << PAGE_SHIFT)) * (1 << PAGE_SHIFT);
out:
	unmapfile(elf32, size);
	return addr == -1L ? 0 : addr;
}

void mmap_event(FILE *out, char *fn)
{
	struct mmap_event m;
	memset(&m, 0, sizeof(struct mmap_event));
	m.header.type = PERF_RECORD_MMAP;
	m.header.size = sizeof(struct mmap_event) + strlen(fn) + 1;
	m.start = get_load_address(fn, &m.pgoff, &m.len);
	m.pid = m.tid = 1;
	fwrite(&m, sizeof(struct mmap_event), 1, out);
	fwrite(fn, strlen(fn)+1, 1, out);
}

void mmap2_event(FILE *out, char *fn)
{
	struct mmap2_event m;
	memset(&m, 0, sizeof(struct mmap2_event));
	m.header.type = PERF_RECORD_MMAP2;
	m.header.size = sizeof(struct mmap2_event) + strlen(fn) + 1;
	m.start = get_load_address(fn, &m.pgoff, &m.len);

	m.header.misc |= PERF_RECORD_MISC_USER;
	m.pid = m.tid = 1;
	fwrite(&m, sizeof(struct mmap2_event), 1, out);
	fwrite(fn, strlen(fn)+1, 1, out);
}

void comm_event(FILE *out, char *cn)
{
	struct comm_event c;
	memset(&c, 0, sizeof(struct comm_event));
	c.header.type = PERF_RECORD_COMM;
	c.header.size = sizeof(struct comm_event);
	strcpy(c.comm, cn);
	fwrite(&c, sizeof(struct comm_event), 1, out);
}

size_t gen_sample(FILE *out, uint64_t ip)
{
	struct sample_event s;
	memset(&s, 0, sizeof(struct sample_event));
	s.header.type = PERF_RECORD_SAMPLE;
	s.header.size = sizeof(struct sample_event);
	s.header.misc |= PERF_RECORD_MISC_USER;
	s.array[0] = ip;
	s.array[1] = ((uint64_t)1 << 32) | 1;
	fwrite(&s, sizeof(struct sample_event), 1, out);
	return sizeof(struct sample_event);
}

void usage(void)
{
	fprintf(stderr, "Usage: toperf pebs-ip-file elffile...\n");
	exit(1);
}

int main(int ac, char **av)
{
	FILE *out = stdout;
	size_t size;
	uint64_t *map;
	int i;
	char *infile;

	if (ac < 3)
		usage();
	infile = av[1];
	init_header(out);
	for (i = 2; i < ac; i++) {
		/* XXX generate COMM events */
		mmap_event(out, av[i]);
	}
	map = mapfile(infile, &size);
	if (!map)
		err(infile);
	for (i = 0; i < size/8; i++)
		gen_sample(out, map[i]);
	unmapfile(map, size);
	gen_header(out);
	return 0;
}
