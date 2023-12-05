
# dummy arithmetic type without any errors, for collecting
# the events from the model. Otherwise divisions by zero cause
# early exits

class DummyArith(object):
    def __add__(self, o):
        return self
    __sub__ = __add__
    __mul__ = __add__
    __div__ = __add__
    __truediv__ = __add__
    __rsub__ = __add__
    __radd__ = __add__
    __rmul__ = __add__
    __rdiv__ = __add__
    __rtruediv__ = __add__
    def __lt__(self, o):
        return True
    __eq__ = __lt__
    __ne__ = __lt__
    __gt__ = __lt__
    __ge__ = __lt__
    __or__ = __add__
    __and__ = __add__
    __min__ = __add__
    __max__ = __add__
