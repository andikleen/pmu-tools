#include "jevents.h"
#include <stdlib.h>
#include <stdio.h>

int main(int ac, char **av)
{
	while (*++av) {
		unsigned event = strtoul(*av, NULL, 0);
		char *name, *desc;
		if (rmap_event(event, &name, &desc) == 0)
			printf("%x: %s : %s\n", event, name, desc);
		else
			printf("%x not found\n", event);
	}
	return 0;
}
