CFLAGS := -g  -Wall
KDOC = /usr/src/linux/scripts/kernel-doc

all: rtest interrupts.o measure.o html rtest2

HTML := measure.html rdpmc.html interrupts.html

html: ${HTML}

rtest: rdpmc.o rtest.o

rtest2: rdpmc.o interrupts.o rtest2.o

rtest2: LDFLAGS += -lm

rdpmc.html: rdpmc.c
measure.html: measure.c
interrupts.html: interrupts.c

%.html: %.c
	${KDOC} -html $^ > $@

clean:
	rm -f rtest2 rtest2.o rtest rdpmc.o rtest.o interrupts.o \
	      gdb.txt measure.o

all-clean: clean
	rm -f ${HTML}

