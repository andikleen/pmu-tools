import multiprocessing as multip
import subprocess as subp
import os
from collections import Counter
try: # handle python arbitrary meanness
    from queue import Empty
except ImportError:
    from Queue import Empty

class SamplePerfRun(object):
    """Run perf record in background to collect Timed PEBS information
       and generate averages for event weights."""
    def __init__(self):
        self.pi = self.pr = self.ps = None
        self.events_sum = Counter()
        self.events_num = Counter()

    def execute(self, perf, evsamples, pargs, interval):
        self.perf = perf
        self.interval = interval
        pr = subp.Popen([perf, "record",
                                   "-W",
                                   "-e", ",".join(evsamples),
                                   "-o", "-"] + pargs,
                                   stdout=subp.PIPE)
        pi = subp.Popen([perf, "inject"],
                                 stdin=pr.stdout,
                                 stdout=subp.PIPE)
        ps = subp.Popen([perf, "script",
                                   "-i", "-",
                                   "-F", "time,comm,weight,event"],
                                   stdin=pi.stdout,
                                   stdout=subp.PIPE)
        pi.stdout.close()
        pr.stdout.close()
        self.pr, self.pi, self.ps = pr, pi, ps

    def flush(self, ts):
        self.queue.put((ts, {k: (self.events_sum[k] / float(v))
                        for k, v in self.events_num.items()}))
        self.events_sum.clear()
        self.events_num.clear()

    # child process
    def handle_samples(self):
        first_ts = None
        ts = 0.0
        # XXX the intervals do not quite match perf stat, but would need
        # absolute time for perf stat. So for now we assume the start time
        # is roughly similar
        for l in self.ps.stdout:
            l = l.decode()
            # handle process with spaces
            comm = l[:16].strip()
            n = l[17:].replace(":", "").split()
            ts, event, weight = float(n[0]), n[1], int(n[2])
            if comm == self.perf: # XXX pid would be better
                continue
            if first_ts is None:
                first_ts = ts
            self.events_sum[event] += weight
            self.events_num[event] += 1
            if self.interval and ts - first_ts >= self.interval:
                self.flush(ts)
                first_ts = ts
        self.flush(ts)
        self.queue.put(())
        self.pr.wait()    
        self.pi.wait()    
        self.ps.wait()    

    def start(self):
        self.queue = multip.Queue()
        self.child = multip.Process(target=self.handle_samples, args=())
        self.child.start()

    # returns (timestamp, dict-of-event-weights) or None for timeout or () for end
    def get_events(self):
        try:
            return self.queue.get(True, 1) # XXX 1s is too long
        except Empty:
            return None

    def finish(self):
        self.child.join()

if __name__ == '__main__':        
    s = SamplePerfRun()
    s.execute("perf", ["mem_trans_retired.load_latency_gt_4:pp"], ["-a", "./workloads/BC1s"], 1.0)
    s.start()
    while True:
        l = s.get_events()
        if l is not None and len(l) == 0:
            break
        print(l)
    s.finish()
    
