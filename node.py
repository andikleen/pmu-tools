# Helper classes and functions for nodes

# Decorator class to declare reference dependecies between classes
class requires(object):
    """Decorator to mark required references. These references will
    be added to the object as instance attributes. Example:

    @requires("ref1", "ref2")
    class SomeClass(object):
        def some_method(self):
            return self.ref1 + self.ref2

    """
    def __init__(self, *required_refs):
        self.required_refs = required_refs

    def __call__(self, cls):
        setattr(cls, "required_refs", self.required_refs)
        return cls

def set_parent(parent, nodes):
    for node in nodes:
        node.parent = parent

# Check that all required references are set
def check_refs(fn):
    """Decorator to check if required references for an object
    are set. If it finds missing references, it will raise an
    exception. Example:

    @requires("retiring", "bad_speculation", "frontend_bound")
    class BackendBound(object):
        @check_refs
        def _compute(self, ev):
            # checks if required refs are set before executing

    """
    def wrapped(self, *args, **kwargs):
        if not hasattr(self, "required_refs"):
            raise Exception("Missing required_refs object")
        missing_refs = [ref for ref in self.required_refs
                        if not hasattr(self, ref)]
        if missing_refs:
            raise Exception("Missing references: {0}".format(missing_refs))

        return fn(self, *args, **kwargs)

    wrapped.__name__ = fn.__name__
    return wrapped

def add_references(node, **refs):
    """Adds an attribute to node, as specified in the **refs argument.
    Example:

    ...
    backend = BackendBound()
    add_references(backend, retiring=retiring, frontend_bound=frontend,
                   bad_speculation=bad_speculation)

    """
    for name, obj in refs.items():
        setattr(node, name, obj)

