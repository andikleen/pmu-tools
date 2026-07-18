# Copyright (c) 2018 Technical University of Munich
# Author: Martin Becker
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
import math
import logging
import operator
from tl_io import warn

log = logging.getLogger(__name__)
TEMPVAL = 'anon'

div_op = operator.div if 'div' in operator.__dict__ else None # type: ignore

def combine_uval(ulist):
    """
    Combine multiple measurements of the same event into one measurement.
    Uses weighted average.
    """
    combined = None
    if ulist is not None:
        combined = ulist[0]
        for oth in ulist[1:]:
            combined.update(oth)
    return combined


class UVal:
    """
    Measurement value annotated with uncertainty. Supports binary operators for error propagation.
    """

    def __init__(self, name, value, stddev=0., samples=1, mux=100., comment="", computed=False):
        self.name = name
        self.comment = comment
        self.value = value
        self.stddev = stddev
        self.samples = samples
        self.computed = computed
        self.is_ratio = False
        self.multiplex = mux

    def __repr__(self):
        return "{} [{} +- {}]*{}".format(self.name, self.value, self.stddev, self.samples)

    def format_value(self, unit):
        if self.value is None:
            return ""
        if self.is_ratio:
            return "{:>16.1f} ".format(self.value * 100.)
        elif unit == "Count" or unit == "Clocks":
            return "{:16,.0f}   ".format(self.value)
        elif self.value > 1000:
            return "{:16,.1f} ".format(self.value)
        else:
            return "{:16.2f}".format(self.value)

    def format_value_raw(self):
        if self.value is None:
            return ""
        if self.is_ratio:
            return "{:>13.1f}".format(self.value * 100.)
        else:
            return "{:13.1f}".format(self.value)

    def format_uncertainty(self):
        """string representation of measurement uncertainty"""
        vs = ""
        if self.stddev is not None:
            if self.is_ratio:
                if self.value != 0.:
                    v = self.stddev * 100.
                else:
                    v = 0.
                vs += "{:.1f}".format(v)
            else:
                vs += "{:6,.1f}".format(self.stddev)
        return vs

    def format_mux(self):
        vs = ""
        if self.multiplex and self.multiplex == self.multiplex:
            vs = "[{:4.1f}%]".format(self.multiplex)
        return vs

    @staticmethod
    def _merge_mux(lhs, rhs):
        return min(lhs.multiplex, rhs.multiplex)

    def update(self, other):
        """merge data from other event into this"""
        assert isinstance(other, UVal), "wrong type"
        # --
        # calc weighted average
        n = self.samples + other.samples
        res = (1. / n) * (self.samples * self + other.samples * other)
        # apply 'res' to this
        self.samples = n
        if isinstance(res, UVal):
            self.value = res.value
            self.stddev = res.stddev
        else:
            self.value = res
            self.stddev = 0.
        self.multiplex = UVal._merge_mux(self, other)

    ######################
    # operators
    ######################

    def __sub__(self, other):
        if isinstance(other, UVal):
            if self.stddev == 0 and other.stddev == 0 and self.multiplex == 100.0 and other.multiplex == 100.0:
                return self.value - other.value
            return UVal._calc(operator.sub, self, other)
        elif isinstance(other, (float, int)):
            if self.stddev == 0 and self.multiplex == 100.0:
                return self.value - other
            return UVal._calc(operator.sub, self, UVal(TEMPVAL, value=other, stddev=0))
        return NotImplemented

    def __add__(self, other):
        if isinstance(other, UVal):
            if self.stddev == 0 and other.stddev == 0 and self.multiplex == 100.0 and other.multiplex == 100.0:
                return self.value + other.value
            return UVal._calc(operator.add, self, other)
        elif isinstance(other, (float, int)):
            if self.stddev == 0 and self.multiplex == 100.0:
                return self.value + other
            return UVal._calc(operator.add, self, UVal(TEMPVAL, value=other, stddev=0))
        return NotImplemented

    def __mul__(self, other):
        if isinstance(other, UVal):
            if self.stddev == 0 and other.stddev == 0 and self.multiplex == 100.0 and other.multiplex == 100.0:
                return self.value * other.value
            return UVal._calc(operator.mul, self, other)
        elif isinstance(other, (float, int)):
            if self.stddev == 0 and self.multiplex == 100.0:
                return self.value * other
            return UVal._calc(operator.mul, self, UVal(TEMPVAL, value=other, stddev=0))
        return NotImplemented

    def __div__(self, other):
        if isinstance(other, UVal):
            if self.stddev == 0 and other.stddev == 0 and self.multiplex == 100.0 and other.multiplex == 100.0:
                return operator.div(self.value, other.value)
            return UVal._calc(operator.div, self, other)
        elif isinstance(other, (float, int)):
            if self.stddev == 0 and self.multiplex == 100.0:
                return operator.div(self.value, other)
            return UVal._calc(operator.div, self, UVal(TEMPVAL, value=other, stddev=0))
        return NotImplemented

    def __truediv__(self, other):
        if isinstance(other, UVal):
            if self.stddev == 0 and other.stddev == 0 and self.multiplex == 100.0 and other.multiplex == 100.0:
                return self.value / other.value
            return UVal._calc(operator.truediv, self, other)
        elif isinstance(other, (float, int)):
            if self.stddev == 0 and self.multiplex == 100.0:
                return self.value / other
            return UVal._calc(operator.truediv, self, UVal(TEMPVAL, value=other, stddev=0))
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, UVal):
            return self.value < other.value
        elif isinstance(other, (float, int)):
            return self.value < other
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, UVal):
            return self.value <= other.value
        elif isinstance(other, (float, int)):
            return self.value <= other
        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, UVal):
            return self.value == other.value
        elif isinstance(other, (float, int)):
            return self.value == other
        return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __ge__(self, other):
        if isinstance(other, UVal):
            return self.value >= other.value
        elif isinstance(other, (float, int)):
            return self.value >= other
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, UVal):
            return self.value > other.value
        elif isinstance(other, (float, int)):
            return self.value > other
        return NotImplemented

    def __rsub__(self, other):
        if isinstance(other, (float, int)):
            if self.stddev == 0 and self.multiplex == 100.0:
                return other - self.value
            return UVal._calc(operator.sub, UVal(TEMPVAL, value=other, stddev=0), self)
        return NotImplemented

    def __radd__(self, other):
        if isinstance(other, (float, int)):
            if self.stddev == 0 and self.multiplex == 100.0:
                return other + self.value
            return UVal._calc(operator.add, UVal(TEMPVAL, value=other, stddev=0), self)
        return NotImplemented

    def __rmul__(self, other):
        if isinstance(other, (float, int)):
            if self.stddev == 0 and self.multiplex == 100.0:
                return other * self.value
            return UVal._calc(operator.mul, UVal(TEMPVAL, value=other, stddev=0), self)
        return NotImplemented

    def __rdiv__(self, other):
        if isinstance(other, (float, int)):
            if self.stddev == 0 and self.multiplex == 100.0:
                return operator.div(other, self.value)
            return UVal._calc(operator.div, UVal(TEMPVAL, value=other, stddev=0), self)
        return NotImplemented

    def __rtruediv__(self, other):
        if isinstance(other, (float, int)):
            if self.stddev == 0 and self.multiplex == 100.0:
                return other / self.value
            return UVal._calc(operator.truediv, UVal(TEMPVAL, value=other, stddev=0), self)
        return NotImplemented

    def __nonzero__(self): # python 2
        return self.value != 0.0

    def __bool__(self): # python 3
        return self.value != 0.0

    #########################
    # uncertainty propagator
    #########################

    @staticmethod
    def _calc(op, lhs, rhs, cov=0.):
        """Compute the result of 'lhs [op] rhs' and propagate standard deviations"""
        A = lhs.value
        B = rhs.value
        a = lhs.stddev
        b = rhs.stddev
        # new value
        f = op(float(A), B)
        if isinstance(f, float) and f.is_integer():
            f = int(f)
        # uncertainty
        if op in (operator.mul, operator.truediv, div_op):
            sgn = 1 if op == operator.mul else -1
            if A != 0 and B != 0:
                u = abs(f) * math.sqrt(pow(float(a)/A, 2) + pow(float(b)/B, 2) + sgn*2.*cov/(A*B))
            elif op == operator.mul:
                u = 0.
            elif op == div_op or op == operator.truediv:
                u = 0.
                if A != 0:
                    warn("Error prop failed because of DIV/0: {} {} {}".format(lhs, op, rhs))

        elif op in (operator.add, operator.sub):
            sgn = 1 if op == operator.add else -1
            u = math.sqrt(pow(a, 2) + pow(b, 2) + sgn*2.*cov)

        else:
            u = None
            log.error("Unsupported operation for uncertainty propagator in {} {} {}".format(lhs, op, rhs))
        # --
        ret = UVal(TEMPVAL, value=f, stddev=u, mux=UVal._merge_mux(lhs, rhs), computed=True)
        log.debug("{} {} {} => {}", lhs, op, rhs, ret)
        return ret
