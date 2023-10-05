# generate levels for events from the model
# utility module for other tools
l1 = set(("Frontend_Bound", "Backend_Bound", "Retiring", "Bad_Speculation"))

def get_level(name):
    is_node = name in l1 or "." in name
    level = name.count(".") + 1
    if is_node:
        return level
    return 0

def is_metric(name):
    return get_level(name) == 0

def level_name(name):
    if name.count(".") > 0:
        f = name.split(".")[:-1]
        n = ".".join(f)
    elif is_metric(name):
        return "CPU-METRIC" # XXX split
    else:
        n = "TopLevel"
    n = n.replace(" ", "_")
    return n
