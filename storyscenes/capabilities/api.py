"""One registry and JSON boundary for every capability family."""
from .codec import loads
from .core import Registry


def registry():
    from . import physical, epistemic, social
    result = Registry()
    physical.register(result)
    epistemic.register(result)
    social.register(result)
    return result


def load_world(source):
    engine = registry()
    return engine, loads(engine, source)
