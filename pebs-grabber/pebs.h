#undef TRACE_SYSTEM
#define TRACE_SYSTEM pebs

#if !defined(_TRACE_PEBS_H) || defined(TRACE_HEADER_MULTI_READ)
#define _TRACE_PEBS_H

#include <linux/tracepoint.h>

/* PEBS trace points. These always follow on each other */

TRACE_EVENT(pebs_v1, 
	    TP_PROTO(u64 ip,
		     u64 status,
		     u64 dla,
		     u64 dse,
		     u64 lat),
	    TP_ARGS(ip, status, dla, dse, lat),
	    TP_STRUCT__entry(
		    __field(u64, ip)
		    __field(u64, status)
		    __field(u64, dla)
		    __field(u64, dse)
		    __field(u64, lat)
		    ),
	    TP_fast_assign(
		    __entry->ip = ip;
		    __entry->status = status;
		    __entry->dla = dla;
		    __entry->dse = dse;
		    __entry->lat = lat;
		    ),
	    TP_printk("ip=%llx status=%llx dla=%llx dse=%llx lat=%llx\n",
		      __entry->ip,
		      __entry->status,
		      __entry->dla,
		      __entry->dse,
		      __entry->lat)
	);

TRACE_EVENT(pebs_v2, 
	    TP_PROTO(u64 eventingip,
		     u64 tsx_tuning,
		     u64 ax),
	    TP_ARGS(eventingip, tsx_tuning, ax),
	    TP_STRUCT__entry(
		    __field(u64, eventingip)
		    __field(u64, tsx_tuning)
		    __field(u64, ax)
		    ),
	    TP_fast_assign(
		    __entry->eventingip = eventingip;
		    __entry->tsx_tuning = tsx_tuning;
		    __entry->ax = ax;
		    ),
	    TP_printk("eventingip=%llx tsx_tuning=%llx ax=%llx\n",
		      __entry->eventingip,
		      __entry->tsx_tuning,
		      __entry->ax)
	);

TRACE_EVENT(pebs_regs, 
	    TP_PROTO(u64 flags, u64 *regs),
	    TP_ARGS(flags, regs),
	    TP_STRUCT__entry(
		    __field(u64, flags)
		    __field(u64, regs[16])
		    ),
	    TP_fast_assign(
		    __entry->flags = flags;
		    memcpy(__entry->regs, regs, sizeof(u64) * 16);
		    ),
	    TP_printk("flags=%llx\n"
		      "ax=%llx bx=%0llx cx=%llx dx=%llx si=%llx di=%llx bp=%llx sp=%llx\n"
		      "r8=%llx r9=%llx r10=%llx r11=%llx r12=%llx r13=%llx r14=%llx r15=%llx\n",
		      __entry->flags,
		      __entry->regs[0],
		      __entry->regs[1],
		      __entry->regs[2],
		      __entry->regs[3],
		      __entry->regs[4],
		      __entry->regs[5],
		      __entry->regs[6],
		      __entry->regs[7],
		      __entry->regs[8],
		      __entry->regs[9],
		      __entry->regs[10],
		      __entry->regs[11],
		      __entry->regs[12],
		      __entry->regs[13],
		      __entry->regs[14],
		      __entry->regs[15])
	);

#endif

#include <trace/define_trace.h>
	    

		   
