/* Deal with Gleixnerfication */
#include <linux/version.h>

#if LINUX_VERSION_CODE >= KERNEL_VERSION(4,8,0)

/* No CPU hotplug / suspend with the mess in newer kernels. */

static inline void register_cpu_notifier(struct notifier_block *n) {}
static inline void unregister_cpu_notifier(struct notifier_block *n) {}

#define CPU_STARTING 0
#define CPU_DYING 1

#endif
