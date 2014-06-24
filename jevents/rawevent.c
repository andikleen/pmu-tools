#include <linux/perf_event.h>
#include <stdio.h>
#include <string.h>

#define BUFS 1024

/** 
 * format_raw_event - Format a resolved event for perf's command line tool
 * @attr: Previously resolved perf_event_attr.
 * @name: Name to add to the event or NULL.
 * Return a string of the formatted event. The caller must free string.
 */

char *format_raw_event(struct perf_event_attr *attr, char *name)
{
	char buf[BUFS];
	int off = 0;

	off = sprintf(buf, "cpu/config=%#llx", attr->config);
	if (attr->config1)
		off += sprintf(buf + off, ",config1=%#llx", attr->config1);
	if (attr->config2)
		off += sprintf(buf + off, ",config2=%#llx", attr->config2);
	if (name)
		off += snprintf(buf + off, BUFS - off, ",name=%s", name);
	off += sprintf(buf + off, "/");
	return strdup(buf);
}
