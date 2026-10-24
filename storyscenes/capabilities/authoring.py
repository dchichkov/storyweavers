"""Role-bound composition over the one capability registry.

Bindings are explicit values, never string replacement in Python or predicates.
An unbound operation cannot enter a world: every action needs a physical actor.
"""
from dataclasses import dataclass, fields, is_dataclass, replace
import math

from .core import Action, CapabilityError


@dataclass(frozen=True)
class Role:
    name: str


def resolve(value, bindings):
    if isinstance(value, Role):
        if value.name not in bindings:
            raise CapabilityError(f"Unbound role: {value.name}")
        return bindings[value.name]
    if is_dataclass(value):
        return type(value)(**{f.name: resolve(getattr(value, f.name), bindings) for f in fields(value)})
    if isinstance(value, dict):
        return {k: resolve(v, bindings) for k, v in value.items()}
    if isinstance(value, tuple):
        return tuple(resolve(v, bindings) for v in value)
    if isinstance(value, list):
        return [resolve(v, bindings) for v in value]
    return value


@dataclass(frozen=True, kw_only=True)
class Pattern:
    actions: tuple[Action, ...]

    def __post_init__(self):
        if len({a.id for a in self.actions}) != len(self.actions):
            raise CapabilityError("Composed actions need unique IDs")

    def __add__(self, other):
        if not isinstance(other, Pattern):
            return NotImplemented
        return Pattern(actions=self.actions + other.actions)

    def __truediv__(self, divisor):
        if type(divisor) not in (int, float) or not math.isfinite(divisor) or divisor <= 0:
            raise CapabilityError("Attention divisor must be finite and positive")
        return Pattern(actions=tuple(replace(a, weight=a.weight / divisor) for a in self.actions))


@dataclass(frozen=True, kw_only=True)
class Kernel:
    operation: str
    actor: Role
    arguments: dict

    def bind(self, action_id, *, bindings, requires=(), intent=(), reason=None, reason_support=(), max_uses=1):
        actor = resolve(self.actor, bindings)
        if not isinstance(actor, str) or not actor:
            raise CapabilityError("A kernel must bind to a physical actor")
        return Pattern(actions=(Action(id=action_id, operation=self.operation, actor=actor,
                    args=resolve(self.arguments, bindings), requires=resolve(requires, bindings),
                    intent=resolve(intent, bindings), reason=reason,
                    reason_support=reason_support, max_uses=max_uses),))
