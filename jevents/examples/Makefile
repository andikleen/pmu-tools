# build jevents first
CFLAGS := -g -Wall -O2  -I ..
CXXFLAGS := -g -Wall  -O2 
LDFLAGS := -L ..
LDLIBS = -ljevents

all: addr rtest rtest2

# no deps on the includes

OBJ := addr.o hist.o cpu.o

addr: ${OBJ}

addr: LDLIBS += -lstdc++ -ldl

rtest2: LDFLAGS += -lm

rtest: rtest.o

rtest2: rtest2.o

clean:
	rm -f addr ${OBJ}
	rm -f rtest2 rtest2.o rtest rtest.o 

