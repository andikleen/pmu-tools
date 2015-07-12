PREFIX := /usr/local
LIB := ${PREFIX}/lib64
BIN := ${PREFIX}/bin
INCLUDE := ${PREFIX}/include
CFLAGS := -g -Wall -O2
OBJ := json.o jsmn.o jevents.o resolve.o cache.o cpustr.o rawevent.o perf.o \
       interrupts.o rdpmc.o measure.o
KDOC = /usr/src/linux/scripts/kernel-doc

all: libjevents.a showevent listevents rmap

install: libjevents.a listevents showevent rmap
	install -d ${BIN}
	install -d ${LIB}
	install -d ${INCLUDE}
	install -m 755 listevents showevent ${BIN}
	install -m 755 ${BIN}/rmap-event
	install -m 644 libjevents.a ${LIB}
	install -m 644 rdpmc.h jevents.h measure.h perf.h ${INCLUDE}
	# xxx install man page

libjevents.a: ${OBJ}
	rm -f libjevents.a
	ar q libjevents.a $^
	ranlib libjevents.a

clean:
	rm -f ${OBJ} libjevents.a resolve showevent listfiles jevents.html rmap rmap.o \
		listevents resolve-test showevent.o listevents.o

resolve: resolve.c
	$(CC) $(CFLAGS) -DTEST=1 -o $@ $^

showevent: showevent.o libjevents.a

listevents: listevents.o libjevents.a

rmap: rmap.o libjevents.a

DOCFILES := cache.c jevents.c cpustr.c rawevent.c perf.c interrupts.c measure.c rdpmc.c

html: jevents.html

man: jeventstmp.man
	perl -ne 's/Kernel Hacker.s Manual/jevents/; open(F,">" . $$1 . ".man") if /^\.TH "(.*?)"/; print F $$_' jevents.man

jeventstmp.man: $(DOCFILES)
	${KDOC} -man ${DOCFILES} > $@

jevents.html: $(DOCFILES)
	${KDOC} -html ${DOCFILES} > $@
