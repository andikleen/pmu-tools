# build jevents first
CFLAGS := -g -Wall -O2  -I .. -Wno-unused-result
CXXFLAGS := -g -Wall  -O2 
LDFLAGS := -L ..
LDLIBS = -ljevents

all: addr rtest rtest2 jestat

# no deps on the includes

ADDR_OBJ := addr.o hist.o cpu.o

addr: ${ADDR_OBJ}

addr: LDLIBS += -lstdc++ -ldl

rtest2: LDLIBS += -lm

rtest: rtest.o

rtest2: rtest2.o

clean:
	rm -f addr ${ADDR_OBJ} jestat jestat.o
	rm -f rtest2 rtest2.o rtest rtest.o 

