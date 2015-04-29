CFLAGS := -g -Wall
OBJ := json.o jsmn.o jevents.o resolve.o cache.o cpustr.o rawevent.o
KDOC = /usr/src/linux/scripts/kernel-doc

all: libjevents.a showevent listevents rmap

libjevents.a: ${OBJ}
	rm -f libjevents.a
	ar q libjevents.a $^
	ranlib libjevents.a

clean:
	rm -f ${OBJ} libjevents.a resolve showevent listfiles jevents.man jevents.html rmap rmap.o \
		listevents resolve-test showevent.o listevents.o

resolve: resolve.c
	$(CC) $(CFLAGS) -DTEST=1 -o $@ $^

showevent: showevent.o libjevents.a

listevents: listevents.o libjevents.a

rmap: rmap.o libjevents.a

DOCFILES := cache.c jevents.c cpustr.c rawevent.c

html: jevents.html

man: jevents.man

jevents.man: $(DOCFILES)
	${KDOC} -man ${DOCFILES} > $@

jevents.html: $(DOCFILES)
	${KDOC} -html ${DOCFILES} > $@
