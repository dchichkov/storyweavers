"""Opt-in authored story prototypes over the existing classical sampler."""
NAMES=('pottery','music','greenhouse')


def pack(name):
    from importlib import import_module
    from .engine import CraftedPack
    if name not in NAMES:raise ValueError('crafted edition supports '+', '.join(NAMES))
    return CraftedPack(import_module('.'+name,__name__).SPEC)
