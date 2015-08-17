struct pollfd;

typedef uint64_t u64;

int device_open(void);
int get_size(void);
void open_cpu(void **mapp, int cnum, struct pollfd *pfd, int size);
