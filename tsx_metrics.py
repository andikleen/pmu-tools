#
# TSX metrics
#

# XXX force all these into a single group
# XXX: force % in caller

def TXCycles(EV, level):
    return EV("cpu/cycles-t/", level) / EV("cycles", level)

class TransactionalCycles:
    name = "Transactional cycles"
    desc = """
Percent cycles spent in a transaction. When low or zero either the program
does not use locks (or other transactions), or the locks are not enabled with lock elision."""
    subplot = "TSX"
    unit = "%"
    sample = ["mem_uops_retired.lock_loads"]
    server = True
    def compute(self, EV):
        try:
            self.val = TXCycles(EV, 1) * 100.
            self.thresh = (self.val >= 0.01)
        except ZeroDivisionError:
            self.val = 0
            self.thresh = False

class AbortedCycles:
    name = "Aborted cycles"
    desc = """
Percent cycles wasted in transaction aborts. When a significant part of the transactional cycles
start sampling for abort causes."""
    subplot = "TSX"
    unit = "%"
    sample = ["cpu/tx-abort/pp", "cpu/hle-abort/pp"]
    server = True
    def compute(self, EV):
        try:
            self.val = ((EV("cpu/cycles-t/", 1) - EV("cpu/cycles-ct/", 1)) / EV("cycles", 1)) * 100.
            self.thresh = (self.val >= 0.01)
        except ZeroDivisionError:
            self.val = 0
            self.thresh = False

class AverageRTM:
    name = "Average RTM transaction length"
    desc = """
Average RTM transaction length. Assumes most transactions are RTM.
When low consider increasing the size of the critical sections to lower overhead."""
    subplot = "TSX Latencies"
    unit = "cycles"
    server = True
    def compute(self, EV):
        try:
            self.val = EV("cpu/cycles-t/", 1) / EV("RTM_RETIRED.START", 1)
            self.thresh = TXCycles(EV, 1) >= 0.01 and self.val > 0
        except ZeroDivisionError:
            self.val = 0
            self.thresh = False

class AverageHLE:
    name = "Average HLE transaction length"
    desc = """
Average HLE transaction length. Assumes most transactions are HLE.
When low consider increasing the size of the critical sections to lower overhead."""
    subplot = "TSX Latencies"
    unit = "cycles"
    def compute(self, EV):
        try:
            self.val = EV("cpu/cycles-t/", 1) / EV("HLE_RETIRED.START", 1)
            self.thresh = TXCycles(EV, 1) >= 0.01 and self.val > 0
        except ZeroDivisionError:
            self.val = 0
            self.thresh = False

class Setup:
    def __init__(self, r):
        r.metric(TransactionalCycles())
        r.metric(AbortedCycles())
        r.metric(AverageRTM())
        r.metric(AverageHLE())

