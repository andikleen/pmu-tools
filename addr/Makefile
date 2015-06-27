# build jevents first
CFLAGS := -g -Wall -O2  -I ../jevents
CXXFLAGS := -g -Wall  -O2 
LDFLAGS := -lstdc++ -ldl -L ../jevents
LDLIBS = -ljevents

# no deps on the includes

OBJ := addr.o hist.o cpu.o

addr: ${OBJ}

clean:
	rm -f addr ${OBJ} addr.html addr.man
