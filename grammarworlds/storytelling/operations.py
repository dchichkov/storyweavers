"""Shared physical effects, prerequisite checks, and validated event commitment.

World packs supply extra physical guards and specialized effects. These helpers
do not authorize an event: the exact frame must still be offered by candidates.
"""
from dataclasses import asdict, dataclass
from functools import wraps


def can_transfer(world, item, holder, recipient):
    """A held object can pass between two co-located physical people.

Permission and story obligations remain additional pack-specific guards.
"""
    e = world.entities
    return ({item, holder, recipient} <= e.keys()
            and e[holder].kind == e[recipient].kind == "person"
            and e[item].kind != "person" and e[item].location == holder
            and e[holder].location == e[recipient].location)


def enabled(world, kernel, *, once=False, causes=()):
    """Shared transition prerequisites; optional once-only and causal checks."""
    return (kernel.requires <= world.flags and not kernel.excludes & world.flags
            and (not once or not kernel.adds & world.flags)
            and (not causes or set(causes) <= {f.id for f in world.facts_for_attention()}))


@dataclass(frozen=True)
class Change:
    entity: str
    location: str | None = None
    add: tuple[str, ...] = ()
    remove: tuple[str, ...] = ()

    def bind(self, world, frame):
        def value(key):
            return getattr(frame, key[1:]) if key and key.startswith("@") else key
        entity, location = value(self.entity), value(self.location)
        if entity not in world.entities or location == "":
            raise ValueError("physical effect needs an existing carrier and a valid destination")
        return world.entities[entity], location

    def apply(self, binding):
        entity, location = binding
        if location is not None:
            entity.location = location
        entity.state.difference_update(self.remove)
        entity.state.update(self.add)


def committed(candidates, changes=None, *, flags_first=True):
    """Decorate a pack's remaining specialized effects with one commit protocol.

All declarative bindings are validated before mutation. Existing packs differ
in when flags become visible to their specialized effects; preserve that order.
"""
    changes = changes or {}

    def decorate(specialized):
        @wraps(specialized)
        def commit(world, frame, sentence):
            kernel = next((k for k, f in candidates(world) if f == frame), None)
            if kernel is None:
                raise ValueError("Forged or stale frame")
            effects = changes.get(frame.kind, ())
            bindings = [effect.bind(world, frame) for effect in effects]
            before = world.snapshot()
            if flags_first:
                world.flags.update(kernel.adds)
            for effect, binding in zip(effects, bindings):
                effect.apply(binding)
            specialized(world, frame)
            if not flags_first:
                world.flags.update(kernel.adds)
            world.focus = frame.actor
            event = dict(id=len(world.history)+1, frame=asdict(frame), sentence=sentence,
                         before=before, after=world.snapshot())
            world.history.append(event)
            return event
        return commit
    return decorate
