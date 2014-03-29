CFLAGS := -g -Wall -O2 
CXXFLAGS := -g -Wall  -O2 
LDFLAGS := -lstdc++ -ldl
KDOC = /usr/src/linux/scripts/kernel-doc

# no deps on the includes

OBJ := addr.o hist.o perf.o cpu.o

addr: ${OBJ}

clean:
	rm -f addr ${OBJ} addr.html addr.man

DOCFILES := perf.c cpu.c

html: addr.html

man: addr.man

addr.man: $(DOCFILES)
	${KDOC} -man ${DOCFILES} > $@

addr.html: $(DOCFILES)
	${KDOC} -html ${DOCFILES} > $@
