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


class UVal:
    """
    Measurement value annotated with uncertainty. Supports binary operators for error propagation.
    """

    def __init__(self, name, value, stddev=0., samples=1, comment="", computed=False):
        self.name = name
        self.comment = comment
        self.value = value
        self.stddev = stddev
        self.samples = samples
        self.computed = computed
        self.used = False

    def __repr__(self):
        return "{} [{} +- {}]*{}".format(self.name, self.value, self.stddev, self.samples)

    def set_desc(self, name, comment):
        """set name and description in one go"""
        self.name = name
        self.comment = comment

    def update(self, other):
        """merge data from other event into this"""
        assert isinstance(other, UVal), "wrong type"
        # --
        # calc weighted average
        n = self.samples + other.samples
        res = (1. / n) * (self.samples * self + other.samples * other)
        strbefore = "{}".format(self)
        # apply 'res' to this
        self.samples = n
        self.value = res.value
        self.stddev = res.stddev
        log.warning("updated {} with {} => {}".format(strbefore, other, self))

    ######################
    # same-type operators
    ######################

    def __sub__(self, other):
        """self - other"""
        if isinstance(other, UVal):
            o = other
        elif isinstance(other, (float, int)):
            o = UVal(TEMPVAL, value=other, stddev=0)
        else:
            return NotImplemented
        return self._calc(operator.sub, self, o)

    def __add__(self, other):
        """self + other"""
        if isinstance(other, UVal):
            o = other
        elif isinstance(other, (float, int)):
            o = UVal(TEMPVAL, value=other, stddev=0)
        else:
            return NotImplemented
        return self._calc(operator.add, self, o)

    def __mul__(self, other):
        """self * other"""
        if isinstance(other, UVal):
            o = other
        elif isinstance(other, (float, int)):
            o = UVal(TEMPVAL, value=other, stddev=0)
        else:
            return NotImplemented
        return self._calc(operator.mul, self, o)

    def __div__(self, other):
        """self / other"""
        if isinstance(other, UVal):
            o = other
        elif isinstance(other, (float, int)):
            o = UVal(TEMPVAL, value=other, stddev=0)
        else:
            return NotImplemented
        return self._calc(operator.div, self, o)

    #######################
    # mixed-type operators
    #######################

    def __rsub__(self, other):
        """other - self"""
        tmp = UVal(TEMPVAL, value=other, stddev=0)
        return self._calc(operator.sub, tmp, self)

    def __rmul__(self, other):
        """other * self"""
        tmp = UVal(TEMPVAL, value=other, stddev=0)
        return self._calc(operator.mul, tmp, self)

    #########################
    # uncertainty propagator
    #########################

    def _calc(ev, op, lhs, rhs, cov=0.):
        """Compute the result of 'lhs [op] rhs' and propagate standard deviations"""
        lhs.used = rhs.used = True
        A = lhs.value
        B = rhs.value
        a = lhs.stddev
        b = rhs.stddev
        # new value
        f = op(float(A), B)
        if isinstance(f, float) and f.is_integer(): f = int(f)
        # uncertainty: FIXME covariance neglected
        if op in (operator.mul, operator.truediv, operator.div):
            sgn = 1 if op == operator.mul else -1
            if A != 0 and B != 0:
                u = abs(f) * math.sqrt(pow(float(a)/A, 2) + pow(float(b)/B, 2) + sgn*2.*cov/(A*B))
            elif op == operator.mul:
                u = 0.
            elif op == operator.div:
                u = 0.
                if A != 0:
                    log.warning("Error prop failed because of DIV/0: {} {} {}".format(lhs, op, rhs))

        elif op in (operator.add, operator.sub):
            sgn = 1 if op == operator.add else -1
            u = math.sqrt(pow(a, 2) + pow(b, 2) + sgn*2.*cov)

        else:
            u = None
            log.error("Unsupported operation for uncertainty propagator in {} {} {}".format\
                      (lhs, op, rhs))
        # --
        ret = UVal(TEMPVAL, value=f, stddev=u, computed=True)
        log.debug("{} {} {} => {}".format(lhs, op, rhs, ret))
        return ret
