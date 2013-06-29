KDIR := /lib/modules/`uname -r`/build

CFLAGS_pebs-grabber.o := -DTRACE_INCLUDE_PATH=${M}

obj-m := pebs-grabber.o

all:
	make -C ${KDIR} M=`pwd`

install:
	make -C ${KDIR} M=`pwd` install

clean:
	make -C ${KDIR} M=`pwd` clean
