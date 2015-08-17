USER_CFLAGS := -g -Wall -std=c89
KDIR = /lib/modules/`uname -r`/build

USER_EXE := dumper samples histogram toperf
USER_OBJ := dumper.o dump-util.o elf.o symtab.o samples.o map.o \
	    histogram.o toperf.o

obj-m := simple-pebs.o
M := make -C ${KDIR} M=`pwd`

all:
	${M} modules

install:
	${M} modules_install

clean:
	${M} clean
	rm -rf ${USER_EXE} ${USER_OBJS}

user: ${USER_EXE}
${USER_OBJ} ${USER_EXE}: CFLAGS := ${USER_CFLAGS}

dumper: dump-util.o dumper.o

samples: LDLIBS := -lelf
samples: samples.o elf.o symtab.o dump-util.o

histogram: LDLIBS := -lelf
histogram: histogram.o elf.o symtab.o map.o

toperf: toperf.o map.o
