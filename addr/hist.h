
#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>

struct hist;

struct hist *init_hist(void);
void hist_add(struct hist *h, uint64_t);
void hist_print(struct hist *h, double min_percent);
void free_hist(struct hist *);

#ifdef __cplusplus
}
#endif
