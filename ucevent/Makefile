ucevent.man: ucevent.s
	FORCECPU=jkt help2man --version-string=" " -i ucevent.s -N ./ucevent.py > ucevent.man

ucevent.s:
	./md2hman.py < README.md > ucevent.s

clean:
	rm -f ucevent.s
