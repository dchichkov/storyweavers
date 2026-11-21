"""Opt-in authored story prototypes over the existing classical sampler."""
NAMES=('pottery','music','greenhouse')


def pack(name, *, decision_beats=False):
    from importlib import import_module
    from .engine import CraftedPack
    if name not in NAMES:raise ValueError('crafted edition supports '+', '.join(NAMES))
    spec=import_module('.'+name,__name__).SPEC
    if decision_beats:
        from .decision_bank import enrich
        spec=enrich(spec)
    return CraftedPack(spec)
