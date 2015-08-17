struct sym {
	char *name;
	unsigned long val;
	unsigned long size;
	unsigned long hits;
	struct sym *link;
};

struct symtab {
	struct symtab *next;
	unsigned num;
	struct sym *syms;
};

extern struct symtab *symtabs;

struct sym *findsym(unsigned long val);
struct symtab *add_symtab(unsigned num);
void dump_symtab(struct symtab *st);
void sort_symtab(struct symtab *st);
