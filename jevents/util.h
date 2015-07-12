#define err(x) perror(x), exit(1)
#define mb() asm volatile("" ::: "memory")
#define MB (1024*1024)
typedef unsigned long long u64;
typedef long long s64;
