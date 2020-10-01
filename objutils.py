# generic utilities for objects

def has(obj, name):
    return name in obj.__class__.__dict__

def safe_ref(obj, name):
    if has(obj, name):
        return obj.__class__.__dict__[name]
    return None

def map_fields(obj, fields):
    def map_field(name):
        return safe_ref(obj, name)
    return list(map(map_field, fields))
