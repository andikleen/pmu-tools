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


log = logging.getLogger(__name__)
TEMPVAL = 'anon'

div_op = operator.div if 'div' in operator.__dict__ else None

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

    def format_value(self):
        if self.value is None:
            return ""
        if self.is_ratio:
            return "{:>16.1f}".format(self.value * 100.)
        elif self.value > 1000:
            return "{:16,.1f}".format(self.value)
        else:
            return "{:16.1f}".format(self.value)

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
            vs = "[{:3.1f}%]".format(self.multiplex)
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
        self.value = res.value
        self.stddev = res.stddev
        self.multiplex = UVal._merge_mux(self, other)

    ######################
    # operators
    ######################

    def ensure_uval(binop):
        """decorator to ensure binary operators are both UVals"""
        def wrapper(self, v):
            if isinstance(v, UVal):
                return binop(self, v)
            elif isinstance(v, (float, int)):
                return binop(self, UVal(TEMPVAL, value=v, stddev=0))
            else:
                return NotImplemented
        return wrapper

    @ensure_uval
    def __sub__(self, other):
        return UVal._calc(operator.sub, self, other)

    @ensure_uval
    def __add__(self, other):
        return UVal._calc(operator.add, self, other)

    @ensure_uval
    def __mul__(self, other):
        return UVal._calc(operator.mul, self, other)

    @ensure_uval
    def __div__(self, other):
        return UVal._calc(operator.div, self, other)

    @ensure_uval
    def __truediv__(self, other):
        return UVal._calc(operator.truediv, self, other)

    @ensure_uval
    def __lt__(self, other):
        return self.value < other.value

    @ensure_uval
    def __le__(self, other):
        return self.value <= other.value

    @ensure_uval
    def __eq__(self, other):
        return self.value == other.value

    @ensure_uval
    def __ne__(self, other):
        return not self.__eq__(other)

    @ensure_uval
    def __ge__(self, other):
        return self.value >= other.value

    @ensure_uval
    def __gt__(self, other):
        return self.value > other.value

    @ensure_uval
    def __rsub__(self, other):
        """other - self"""
        return UVal._calc(operator.sub, other, self)

    @ensure_uval
    def __radd__(self, other):
        """other + self"""
        return UVal._calc(operator.add, other, self)

    @ensure_uval
    def __rmul__(self, other):
        """other * self"""
        return UVal._calc(operator.mul, other, self)

    @ensure_uval
    def __rdiv__(self, other):
        """other / self"""
        return UVal._calc(operator.div, other, self)

    @ensure_uval
    def __rtruediv__(self, other):
        """other / self"""
        return UVal._calc(operator.truediv, other, self)

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
                    log.warning("Error prop failed because of DIV/0: {} {} {}", lhs, op, rhs)

        elif op in (operator.add, operator.sub):
            sgn = 1 if op == operator.add else -1
            u = math.sqrt(pow(a, 2) + pow(b, 2) + sgn*2.*cov)

        else:
            u = None
            log.error("Unsupported operation for uncertainty propagator in {} {} {}", lhs, op, rhs)
        # --
        ret = UVal(TEMPVAL, value=f, stddev=u, mux=UVal._merge_mux(lhs, rhs), computed=True)
        log.debug("{} {} {} => {}", lhs, op, rhs, ret)
        return ret
