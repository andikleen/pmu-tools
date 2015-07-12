# jevents must be built first
CFLAGS := -g  -Wall -I ../jevents
LDFLAGS := -L ../jevents
LDLIBS := -ljevents
all: rtest rtest2

rtest: rtest.o

rtest2: rtest2.o

rtest2: LDFLAGS += -lm

clean:
	rm -f rtest2 rtest2.o rtest rtest.o 

