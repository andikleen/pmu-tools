nominal_freq = 1.0

class Frequency:
    name = "Frequency"
    desc = " Frequency in Ghz"
    subplot = "Frequency"
    domain = "CoreMetric"
    def compute(self, EV):
        try:
            self.val = (EV("cycles", 1) / EV("CPU_CLK_UNHALTED.REF_TSC", 1)) * nominal_freq
        except ZeroDivisionError:
            self.val = 0

class SetupCPU:
    def __init__(self, r, cpu):
        global nominal_freq
        if cpu.freq:
            nominal_freq = cpu.freq
        r.metric(Frequency())
