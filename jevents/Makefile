CFLAGS := -g -Wall
OBJ := json.o jsmn.o jevents.o resolve.o cache.o cpustr.o

all: libjevents.a

libjevents.a: ${OBJ}
	rm -f libjevents.a
	ar q libjevents.a $^
	ranlib libjevents.a

clean:
	rm -f ${OBJ} libjevents.a resolve test

resolve: resolve.c
	$(CC) $(CFLAGS) -DTEST=1 -o $@ $^

test: test.o libjevents.a

