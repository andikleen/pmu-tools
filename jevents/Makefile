CFLAGS := -g -Wall
OBJ := json.o jsmn.o jevents.o resolve.o cache.o cpustr.o
KDOC = /usr/src/linux/scripts/kernel-doc

all: libjevents.a

libjevents.a: ${OBJ}
	rm -f libjevents.a
	ar q libjevents.a $^
	ranlib libjevents.a

clean:
	rm -f ${OBJ} libjevents.a resolve test jevents.man jevents.html

resolve: resolve.c
	$(CC) $(CFLAGS) -DTEST=1 -o $@ $^

test: test.o libjevents.a

DOCFILES := cache.c jevents.c cpustr.c

html: jevents.html

man: jevents.man

jevents.man: $(DOCFILES)
	${KDOC} -man ${DOCFILES} > $@

jevents.html: $(DOCFILES)
	${KDOC} -html ${DOCFILES} > $@
