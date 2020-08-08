# build jevents first
CFLAGS := -g -Wall -O2 -Wno-unused-result
CXXFLAGS := -g -Wall  -O2  -fPIC
override CFLAGS += -I ..
override LDFLAGS += -L ..
LDLIBS = -ljevents

all: addr rtest rtest2 rtest3 jestat ptself

# no deps on the includes

ADDR_OBJ := addr.o hist.o cpu.o

addr: ${ADDR_OBJ} ../libjevents.a

addr: LDLIBS += -lstdc++ -ldl

rtest2: LDLIBS += -lm

rtest: rtest.o ../libjevents.a

rtest2: rtest2.o ../libjevents.a

rtest3: rtest3.o ../libjevents.a

jestat: jestat.o ../libjevents.a

clean:
	rm -f addr ${ADDR_OBJ} jestat jestat.o
	rm -f rtest3 rtest3.o rtest2 rtest2.o rtest rtest.o
