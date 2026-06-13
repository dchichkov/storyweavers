"""
wrld5.py - Prototype: world/memeplex state while executing story kernels.

Goal
----
Illustrate the "world model" side of Storyweavers at the same prototype level as
rewr5.py. This is not wired into gen5.py. It is a small runnable sketch showing
how kernel execution can:

  - treat uppercase names as executable story/memeplex concepts
  - treat lowercase names as physical terminal objects
  - apply effects to character/story state as kernels run
  - keep an execution trace that can be inspected after narration

Kernel style
------------
The point of this file is to keep kernel implementations close to the story
algebra, instead of making every state update look like arbitrary Python
plumbing. These are the intended idioms:

  char.Joy += 5
  char += Joy(5, reason="found something")
  char -= Fear(0.35, reason="bravery regulates fear")
  char.Fear += dog
  giver.Gratitude += receiver

  obj.status = Fact("found", reason="Find kernel")
  obj.owner = Fact(char, reason="Return recipient")

That is still plain Python, but the surface area is closer to the kernel DSL:
uppercase memeplex names are executable/stateful concepts, lowercase names are
physical objects or relation/fact names, and arithmetic leaves an effect trace.
Kernels may return plain text; the registry wraps it into a StoryTrace with the
effects created while the kernel ran.
Kernels can declare typed parameters; the registry binds evaluated AST args by
type/name before calling the function:

  def kernel_gratitude(
      ctx: WorldContext,
      giver: Character | None = None,
      receiver: Character | None = None,
  ) -> str:
      giver = giver or ctx.last_actor
      ...

Registry operations can define what memeplex arithmetic means:

  @REGISTRY.addition("Gratitude", "Character")
  def gratitude_to_character(owner, receiver, reason=""):
      owner.add_meme_link("Gratitude", receiver, reason=reason)
      owner += Joy(0.3, reason="gratitude lifts joy")

Key idea
--------
A kernel does not only produce text. It also applies small effects to the world:

  Fear(Lily, dog)     -> Lily.Fear += 1.0, Lily.Fear += dog
  Brave(Lily)         -> Lily.Brave += 1.0, Lily.Fear -= 0.35
  Return(eraser,Lily) -> eraser.owner = Lily

Those effects let later kernels narrate with more context.
"""

from __future__ import annotations

import ast
import inspect
import types
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, get_args, get_origin, get_type_hints


# ----------------------------
# World state and trace objects
# ----------------------------

class Character:
    """Type-hint marker for character WorldEntity values."""


class Physical:
    """Type-hint marker for physical/non-character WorldEntity values."""


@dataclass(frozen=True)
class MemeRef:
    """A reference to an uppercase story/memeplex concept."""
    name: str


@dataclass(frozen=True)
class MemeDelta:
    """A weighted meme/state update, e.g. Joy(5) or Fear(0.25)."""
    name: str
    amount: float = 1.0
    reason: str = ""

    def scaled(self, factor: float) -> "MemeDelta":
        return MemeDelta(self.name, self.amount * factor, self.reason)

    def __mul__(self, factor: float) -> "MemeDelta":
        return self.scaled(float(factor))

    def __rmul__(self, factor: float) -> "MemeDelta":
        return self.scaled(float(factor))

    def __truediv__(self, divisor: float) -> "MemeDelta":
        return self.scaled(1.0 / float(divisor))

    def __neg__(self) -> "MemeDelta":
        return self.scaled(-1.0)

    def with_reason(self, reason: str) -> "MemeDelta":
        return MemeDelta(self.name, self.amount, reason)


@dataclass(frozen=True)
class FactValue:
    """A fact assignment with an optional effect-trace reason."""
    value: Any
    reason: str = ""


@dataclass(frozen=True)
class RelationValue:
    """A relation addition with an optional effect-trace reason."""
    value: Any
    reason: str = ""


def Meme(name: str, amount: float = 1.0, reason: str = "") -> MemeDelta:
    return MemeDelta(name, float(amount), reason)


def _meme_factory(name: str) -> Callable[[float, str], MemeDelta]:
    def make(amount: float = 1.0, reason: str = "") -> MemeDelta:
        return MemeDelta(name, float(amount), reason)

    make.__name__ = name
    return make


Joy = _meme_factory("Joy")
Fear = _meme_factory("Fear")
Brave = _meme_factory("Brave")
Sadness = _meme_factory("Sadness")
Hope = _meme_factory("Hope")
Relief = _meme_factory("Relief")
Gratitude = _meme_factory("Gratitude")
Authority = _meme_factory("Authority")
Anger = _meme_factory("Anger")
Warning = _meme_factory("Warning")
Vanish = _meme_factory("Vanish")
Loss = _meme_factory("Loss")
Search = _meme_factory("Search")
Find = _meme_factory("Find")
Return = _meme_factory("Return")


def Fact(value: Any, reason: str = "") -> FactValue:
    return FactValue(value, reason)


def Rel(value: Any, reason: str = "") -> RelationValue:
    return RelationValue(value, reason)


class MemeSlot:
    """Attribute facade that makes char.Joy += 5 mutate meme state."""
    def __init__(self, entity: "WorldEntity", name: str):
        self.entity = entity
        self.name = name

    @property
    def value(self) -> float:
        return self.entity.meme(self.name)

    def __iadd__(self, amount: Any) -> "MemeSlot":
        if isinstance(amount, MemeDelta):
            delta = MemeDelta(self.name, amount.amount, amount.reason)
        elif isinstance(amount, (int, float)):
            delta = MemeDelta(self.name, float(amount), reason=f"{self.name} arithmetic")
        else:
            reason = amount.reason if isinstance(amount, RelationValue) else ""
            value = amount.value if isinstance(amount, RelationValue) else amount
            self.entity.add_to_meme(self.name, value, reason=reason)
            return self
        self.entity += delta
        return self

    def __isub__(self, amount: Any) -> "MemeSlot":
        if isinstance(amount, MemeDelta):
            delta = MemeDelta(self.name, -amount.amount, amount.reason)
        else:
            delta = MemeDelta(self.name, -float(amount), reason=f"{self.name} arithmetic")
        self.entity += delta
        return self

    def __float__(self) -> float:
        return self.value

    def __gt__(self, other: float) -> bool:
        return self.value > other

    def __str__(self) -> str:
        return f"{self.entity.name}.{self.name}={self.value:.2f}"


class RelationSlot:
    """Attribute facade for lowercase physical/world relations when needed."""
    def __init__(self, entity: "WorldEntity", name: str):
        self.entity = entity
        self.name = name

    def __iadd__(self, value: Any) -> "RelationSlot":
        if isinstance(value, RelationValue):
            self.entity.add_relation(self.name, value.value, value.reason)
        else:
            self.entity.add_relation(self.name, value, reason=f"{self.name} relation")
        return self

    def __iter__(self):
        return iter(self.entity.relations.get(self.name, []))

    def __str__(self) -> str:
        return "+".join(self.entity.relations.get(self.name, []))


@dataclass
class WorldEntity:
    """A character or physical object with attached meme/story state."""
    name: str
    kind: str = "physical"
    type_name: str = "thing"
    memes: Dict[str, float] = field(default_factory=dict)
    meme_links: Dict[str, List[str]] = field(default_factory=dict)
    facts: Dict[str, Any] = field(default_factory=dict)
    relations: Dict[str, List[str]] = field(default_factory=dict)
    _ctx: Optional["WorldContext"] = field(default=None, repr=False, compare=False)

    _CORE_FIELDS = {"name", "kind", "type_name", "memes", "meme_links", "facts", "relations", "_ctx"}

    def __setattr__(self, name: str, value: Any) -> None:
        if name in WorldEntity._CORE_FIELDS or name.startswith("_"):
            object.__setattr__(self, name, value)
            return

        if isinstance(value, (MemeSlot, RelationSlot)):
            # Python assigns the result of augmented attribute operations back to
            # the attribute. The slot has already applied the mutation.
            return

        if name and name[0].isupper():
            amount = value.amount if isinstance(value, MemeDelta) else float(value)
            reason = value.reason if isinstance(value, MemeDelta) else f"set {name}"
            self.set_meme(name, amount, reason=reason)
            return

        if isinstance(value, FactValue):
            self.set_fact(name, value.value, value.reason)
            return

        self.set_fact(name, value, reason=f"set {name}")

    def __getattr__(self, name: str) -> Any:
        if name in self.facts:
            return self.facts[name]
        if name and name[0].isupper():
            return MemeSlot(self, name)
        if name and name[0].islower():
            return RelationSlot(self, name)
        raise AttributeError(name)

    def __iadd__(self, delta: MemeDelta) -> "WorldEntity":
        if not isinstance(delta, MemeDelta):
            raise TypeError(f"Can only add MemeDelta to WorldEntity, got {type(delta).__name__}")
        self.adjust_meme(delta.name, delta.amount, reason=delta.reason)
        return self

    def __isub__(self, delta: MemeDelta) -> "WorldEntity":
        if not isinstance(delta, MemeDelta):
            raise TypeError(f"Can only subtract MemeDelta from WorldEntity, got {type(delta).__name__}")
        self.adjust_meme(delta.name, -delta.amount, reason=delta.reason)
        return self

    def meme(self, name: str) -> float:
        return self.memes.get(name, 0.0)

    def bind(self, ctx: "WorldContext") -> "WorldEntity":
        object.__setattr__(self, "_ctx", ctx)
        return self

    def set_meme(self, name: str, amount: float, reason: str = "") -> Optional["Effect"]:
        before = self.memes.get(name, 0.0)
        after = max(0.0, float(amount))
        actual = after - before
        self.memes[name] = after
        return self._record_meme(name, actual, reason)

    def adjust_meme(self, name: str, delta: float, reason: str = "") -> Optional["Effect"]:
        attention = self._ctx.attention if self._ctx else 1.0
        requested = float(delta) * attention
        before = self.memes.get(name, 0.0)
        after = max(0.0, before + requested)
        actual = after - before
        self.memes[name] = after
        return self._record_meme(name, actual, reason)

    def set_fact(self, key: str, value: Any, reason: str = "") -> Optional["Effect"]:
        rendered_value = _name(value)
        self.facts[key] = rendered_value
        if self._ctx is None:
            return None
        effect = Effect("fact", self.name, key, rendered_value, reason)
        self._ctx.effects.append(effect)
        return effect

    def add_relation(self, relation: str, obj: Any, reason: str = "") -> Optional["Effect"]:
        obj_name = _name(obj)
        values = self.relations.setdefault(relation, [])
        if obj_name not in values:
            values.append(obj_name)
        if self._ctx is None:
            return None
        effect = Effect("relation", self.name, relation, obj_name, reason)
        self._ctx.effects.append(effect)
        return effect

    def add_to_meme(self, meme: str, value: Any, reason: str = "") -> Optional["Effect"]:
        if self._ctx is not None and self._ctx.registry is not None:
            return self._ctx.registry.apply_addition(self, meme, value, reason=reason)
        return self.add_meme_link(meme, value, reason=reason or f"{meme} addition")

    def add_meme_link(self, meme: str, value: Any, reason: str = "") -> Optional["Effect"]:
        value_name = _name(value)
        values = self.meme_links.setdefault(meme, [])
        if value_name not in values:
            values.append(value_name)
        if self._ctx is None:
            return None
        effect = Effect("meme_link", self.name, meme, value_name, reason)
        self._ctx.effects.append(effect)
        return effect

    def _record_meme(self, name: str, actual: float, reason: str = "") -> Optional["Effect"]:
        if self._ctx is None or abs(actual) <= 0.001:
            return None
        effect = Effect("meme", self.name, name, actual, reason)
        self._ctx.effects.append(effect)
        return effect


@dataclass
class Effect:
    """One world-state modification produced by a kernel execution."""
    kind: str
    target: str
    key: str
    value: Any
    reason: str = ""

    def describe(self) -> str:
        suffix = f"  # {self.reason}" if self.reason else ""
        if self.kind == "meme":
            sign = "+" if self.value >= 0 else ""
            return f"{self.target}.{self.key} {sign}{self.value:.2f}{suffix}"
        if self.kind == "fact":
            return f"{self.target}.{self.key} = {self.value}{suffix}"
        if self.kind == "relation":
            return f"{self.target}.{self.key} -> {self.value}{suffix}"
        if self.kind == "meme_link":
            return f"{self.target}.{self.key} += {self.value}{suffix}"
        return f"{self.kind}: {self.target}.{self.key} = {self.value}{suffix}"


@dataclass
class StoryTrace:
    """Text plus effects caused by one kernel."""
    kernel_name: str
    text: str = ""
    effects: List[Effect] = field(default_factory=list)
    weight: float = 1.0

    def __str__(self) -> str:
        return self.text


@dataclass
class WorldContext:
    """Mutable execution state for this prototype."""
    entities: Dict[str, WorldEntity] = field(default_factory=dict)
    effects: List[Effect] = field(default_factory=list)
    traces: List[StoryTrace] = field(default_factory=list)
    last_actor: Optional[WorldEntity] = None
    current_object: Optional[WorldEntity] = None
    attention: float = 1.0
    registry: Optional["WorldRegistry"] = None

    def mark(self) -> int:
        return len(self.effects)

    def trace(self, kernel_name: str, text: str, start: int) -> StoryTrace:
        return StoryTrace(kernel_name, text, self.effects[start:])

    def get_or_create_physical(self, name: str, type_name: str = "thing") -> WorldEntity:
        if name not in self.entities:
            self.entities[name] = WorldEntity(name=name, kind="physical", type_name=type_name).bind(self)
        return self.entities[name]

    def add_character(self, name: str, type_name: str, traits: List[str]) -> WorldEntity:
        entity = self.entities.get(name)
        if entity is None:
            entity = WorldEntity(name=name, kind="character", type_name=type_name).bind(self)
            self.entities[name] = entity
        else:
            entity.bind(self)
            entity.kind = "character"
            entity.type_name = type_name

        for trait in traits:
            entity += Meme(trait, 1.0, reason="character trait")

        self.last_actor = entity
        return entity

    def add_meme(self, target: WorldEntity, meme: str, delta: float, reason: str = "") -> Effect:
        effect = target.adjust_meme(meme, delta, reason=reason)
        if effect is None:
            return Effect("meme", target.name, meme, 0.0, reason)
        return effect

    def set_fact(self, target: WorldEntity, key: str, value: Any, reason: str = "") -> Effect:
        effect = target.set_fact(key, value, reason=reason)
        if effect is None:
            return Effect("fact", target.name, key, _name(value), reason)
        return effect

    def relate(self, subject: WorldEntity, relation: str, obj: Any, reason: str = "") -> Effect:
        effect = subject.add_relation(relation, obj, reason=reason)
        if effect is None:
            return Effect("relation", subject.name, relation, _name(obj), reason)
        return effect

    def format_state(self) -> str:
        lines: List[str] = []
        for entity in self.entities.values():
            parts = [f"{entity.name} ({entity.kind}:{entity.type_name})"]

            if entity.memes:
                memes = ", ".join(
                    f"{name}={value:.2f}"
                    for name, value in sorted(entity.memes.items())
                    if abs(value) > 0.001
                )
                if memes:
                    parts.append(f"memes[{memes}]")

            if entity.facts:
                facts = ", ".join(f"{key}={value}" for key, value in sorted(entity.facts.items()))
                parts.append(f"facts[{facts}]")

            if entity.meme_links:
                links = ", ".join(
                    f"{key}={'+'.join(values)}"
                    for key, values in sorted(entity.meme_links.items())
                )
                parts.append(f"meme_links[{links}]")

            if entity.relations:
                rels = ", ".join(
                    f"{key}={'+'.join(values)}"
                    for key, values in sorted(entity.relations.items())
                )
                parts.append(f"relations[{rels}]")

            lines.append(" | ".join(parts))
        return "\n".join(lines)


# ----------------------------
# Kernel registry
# ----------------------------

class WorldRegistry:
    def __init__(self) -> None:
        self.kernels: Dict[str, Callable[..., StoryTrace]] = {}
        self.additions: Dict[Tuple[str, str], Callable[[WorldEntity, Any, str], Optional[Effect]]] = {}

    def kernel(self, name: str) -> Callable[[Callable[..., Any]], Callable[..., StoryTrace]]:
        def decorator(fn: Callable[..., Any]) -> Callable[..., StoryTrace]:
            signature = inspect.signature(fn)
            hints = get_type_hints(fn, globalns=globals(), localns=locals())

            def wrapped(ctx: WorldContext, *args: Any, **kwargs: Any) -> StoryTrace:
                start = ctx.mark()
                bound_args, bound_kwargs = _bind_kernel_call(ctx, signature, hints, list(args), dict(kwargs))
                result = fn(ctx, *bound_args, **bound_kwargs)
                if isinstance(result, StoryTrace):
                    return result
                if result is None:
                    result = ""
                return ctx.trace(name, str(result), start)

            self.kernels[name] = wrapped
            return wrapped

        return decorator

    def addition(
        self,
        meme: Any,
        rhs_type: Any,
    ) -> Callable[[Callable[[WorldEntity, Any, str], Optional[Effect]]], Callable[[WorldEntity, Any, str], Optional[Effect]]]:
        meme_name = _symbol_name(meme)
        rhs_name = _symbol_name(rhs_type)

        def decorator(
            fn: Callable[[WorldEntity, Any, str], Optional[Effect]]
        ) -> Callable[[WorldEntity, Any, str], Optional[Effect]]:
            self.additions[(meme_name, rhs_name)] = fn
            return fn

        return decorator

    def apply_addition(self, owner: WorldEntity, meme: str, rhs: Any, reason: str = "") -> Optional[Effect]:
        for rhs_type in _addition_types(rhs):
            handler = self.additions.get((meme, rhs_type))
            if handler is not None:
                return handler(owner, rhs, reason)
        return owner.add_meme_link(meme, rhs, reason=reason or f"{meme} addition")


REGISTRY = WorldRegistry()


# ----------------------------
# Typed kernel argument binding
# ----------------------------

_AUTO_ACTOR_NAMES = {"actor", "char", "character", "giver", "speaker", "owner"}


def _bind_kernel_call(
    ctx: WorldContext,
    signature: inspect.Signature,
    hints: Dict[str, Any],
    args: List[Any],
    kwargs: Dict[str, Any],
) -> Tuple[List[Any], Dict[str, Any]]:
    """
    Bind evaluated AST args to typed kernel parameters.

    This keeps kernels from repeatedly doing:
      chars = _characters(list(args))
      actor = chars[0] if chars else ctx.last_actor

    It is intentionally modest: explicit *args kernels still receive raw args,
    while typed kernels get best-effort matching by annotation and parameter name.
    """
    params = list(signature.parameters.values())
    if params and params[0].name == "ctx":
        params = params[1:]

    # Old-style kernels keep their current behavior.
    if any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in params):
        return args, kwargs

    positional: List[Any] = []
    keyword: Dict[str, Any] = {}
    remaining = list(args)

    for param in params:
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            keyword.update(kwargs)
            kwargs = {}
            continue

        if param.name in kwargs:
            value = kwargs.pop(param.name)
        else:
            annotation = hints.get(param.name, param.annotation)
            index = _find_matching_arg(remaining, annotation)
            if index is not None:
                value = remaining.pop(index)
            elif _can_use_last_actor(ctx, param, annotation):
                value = ctx.last_actor
            elif param.default is not inspect._empty:
                value = param.default
            else:
                raise TypeError(f"Could not bind parameter {param.name!r}")

        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            keyword[param.name] = value
        else:
            positional.append(value)

    return positional, keyword


def _find_matching_arg(values: List[Any], annotation: Any) -> Optional[int]:
    if annotation is inspect._empty:
        return 0 if values else None

    for index, value in enumerate(values):
        if _matches_annotation(value, annotation):
            return index
    return None


def _can_use_last_actor(ctx: WorldContext, param: inspect.Parameter, annotation: Any) -> bool:
    if ctx.last_actor is None:
        return False
    if param.default is inspect._empty:
        return False
    if param.name not in _AUTO_ACTOR_NAMES:
        return False
    return _matches_annotation(ctx.last_actor, annotation)


def _matches_annotation(value: Any, annotation: Any) -> bool:
    if annotation in (inspect._empty, Any):
        return True

    options = _annotation_options(annotation)
    if type(None) in options and value is None:
        return True

    for option in options:
        if option is type(None):
            continue
        if option is Character:
            if isinstance(value, WorldEntity) and value.kind == "character":
                return True
        elif option is Physical:
            if isinstance(value, WorldEntity) and value.kind != "character":
                return True
        elif option is WorldEntity:
            if isinstance(value, WorldEntity):
                return True
        elif isinstance(option, type) and isinstance(value, option):
            return True

    return False


def _annotation_options(annotation: Any) -> Tuple[Any, ...]:
    origin = get_origin(annotation)
    if origin in (Union, types.UnionType):
        return tuple(get_args(annotation))
    return (annotation,)


# ----------------------------
# Small NLG helpers
# ----------------------------

def _name(value: Any) -> str:
    if isinstance(value, WorldEntity):
        return value.name
    if isinstance(value, MemeRef):
        return value.name
    if isinstance(value, StoryTrace):
        return value.kernel_name or value.text
    return str(value)


def _phrase(value: Any) -> str:
    if isinstance(value, WorldEntity):
        if value.kind == "character":
            return value.name
        return f"the {value.name}"
    if isinstance(value, MemeRef):
        return value.name.lower()
    if isinstance(value, StoryTrace):
        return value.text.rstrip(".")
    return str(value)


def _first_character(values: List[Any]) -> Optional[WorldEntity]:
    return next((v for v in values if isinstance(v, WorldEntity) and v.kind == "character"), None)


def _characters(values: List[Any]) -> List[WorldEntity]:
    return [v for v in values if isinstance(v, WorldEntity) and v.kind == "character"]


def _non_character(values: List[Any]) -> List[Any]:
    return [v for v in values if not (isinstance(v, WorldEntity) and v.kind == "character")]


def _symbol_name(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, MemeDelta):
        return value.name
    if isinstance(value, MemeRef):
        return value.name
    if callable(value):
        return getattr(value, "__name__", str(value))
    return getattr(value, "__name__", str(value))


def _addition_types(value: Any) -> List[str]:
    if isinstance(value, WorldEntity):
        if value.kind == "character":
            return [value.type_name, "Character", "WorldEntity", "Any"]
        return [value.type_name, "Physical", "WorldEntity", "Any"]
    if isinstance(value, MemeRef):
        return [value.name, "MemeRef", "Any"]
    return [type(value).__name__, "Any"]


# ----------------------------
# Memeplex operation hooks
# ----------------------------

@REGISTRY.addition("Fear", "Physical")
@REGISTRY.addition("Fear", "Character")
def addition_fear_target(owner: WorldEntity, target: Any, reason: str = "") -> Optional[Effect]:
    return owner.add_meme_link("Fear", target, reason=reason or "Fear target")


@REGISTRY.addition("Gratitude", "Character")
def addition_gratitude_character(owner: WorldEntity, receiver: Any, reason: str = "") -> Optional[Effect]:
    owner += Gratitude(1.0, reason="Gratitude kernel")
    effect = owner.add_meme_link("Gratitude", receiver, reason=reason or "Gratitude target")
    owner += Joy(0.3, reason="gratitude lifts joy")
    return effect


@REGISTRY.addition("Warning", "Character")
def addition_warning_character(owner: WorldEntity, listener: Any, reason: str = "") -> Optional[Effect]:
    effect = owner.add_meme_link("Warning", listener, reason=reason or "Warning listener")
    owner += Authority(0.35, reason="warning speaker")
    return effect


@REGISTRY.addition("Loss", "Physical")
@REGISTRY.addition("Loss", "Character")
def addition_loss_target(owner: WorldEntity, target: Any, reason: str = "") -> Optional[Effect]:
    effect = owner.add_meme_link("Loss", target, reason=reason or "Loss target")
    owner += Sadness(0.8, reason="lost valued object")
    if isinstance(target, WorldEntity) and target.kind != "character":
        target.owner = Fact("unknown", reason="Loss kernel")
        target.status = Fact("lost", reason="Loss kernel")
    return effect


@REGISTRY.addition("Search", "Physical")
@REGISTRY.addition("Search", "Character")
def addition_search_target(owner: WorldEntity, target: Any, reason: str = "") -> Optional[Effect]:
    effect = owner.add_meme_link("Search", target, reason=reason or "Search target")
    owner += Hope(0.25, reason="searching implies hope")
    return effect


@REGISTRY.addition("Find", "Physical")
@REGISTRY.addition("Find", "Character")
def addition_find_target(owner: WorldEntity, target: Any, reason: str = "") -> Optional[Effect]:
    effect = owner.add_meme_link("Find", target, reason=reason or "Find target")
    owner += Joy(0.35, reason="found something")
    if isinstance(target, WorldEntity):
        target.status = Fact("found", reason="Find kernel")
        target.finder = Fact(owner, reason="Find kernel")
    return effect


@REGISTRY.addition("Return", "Physical")
def addition_return_physical(owner: WorldEntity, target: Any, reason: str = "") -> Optional[Effect]:
    return owner.add_meme_link("Return", target, reason=reason or "Return object")


@REGISTRY.addition("Return", "Character")
def addition_return_character(owner: WorldEntity, recipient: Any, reason: str = "") -> Optional[Effect]:
    effect = owner.add_meme_link("Return", recipient, reason=reason or "Return recipient")
    if owner.kind != "character" and isinstance(recipient, WorldEntity):
        owner.owner = Fact(recipient, reason="Return recipient")
        owner.status = Fact("returned", reason="Return kernel")
        recipient += Relief(0.7, reason="object returned")
    return effect


# ----------------------------
# Demo kernels with world effects
# ----------------------------

@REGISTRY.kernel("Fear")
def kernel_fear(ctx: WorldContext, *args: Any, **kwargs: Any) -> StoryTrace:
    start = ctx.mark()
    char = _first_character(list(args)) or ctx.last_actor
    target = next((a for a in _non_character(list(args)) if not isinstance(a, StoryTrace)), None)

    if char is None:
        return ctx.trace("Fear", "Fear entered the story.", start)

    char += Fear(1.0, reason="Fear kernel")
    if target is not None:
        char.Fear += target
        text = f"{char.name} became afraid of {_phrase(target)}."
    else:
        text = f"{char.name} became afraid."

    ctx.last_actor = char
    return ctx.trace("Fear", text, start)


@REGISTRY.kernel("Brave")
def kernel_brave(ctx: WorldContext, *args: Any, **kwargs: Any) -> StoryTrace:
    start = ctx.mark()
    char = _first_character(list(args)) or ctx.last_actor

    if char is None:
        return ctx.trace("Brave", "Someone acted bravely.", start)

    had_fear = char.meme("Fear") > 0.2
    char += Brave(1.0, reason="Brave kernel")
    char -= Fear(0.35, reason="bravery regulates fear")

    if had_fear:
        text = f"Even though {char.name} was afraid, {char.name} acted bravely."
    else:
        text = f"{char.name} acted bravely."

    ctx.last_actor = char
    return ctx.trace("Brave", text, start)


@REGISTRY.kernel("Happy")
def kernel_happy(ctx: WorldContext, *args: Any, **kwargs: Any) -> StoryTrace:
    start = ctx.mark()
    char = _first_character(list(args)) or ctx.last_actor

    if char is None:
        return ctx.trace("Happy", "There was happiness.", start)

    was_brave = char.meme("Brave") > 0.0
    char += Joy(1.0, reason="Happy kernel")
    char -= Fear(0.2, reason="joy softens fear")

    if was_brave:
        text = f"After being brave, {char.name} felt happy."
    else:
        text = f"{char.name} felt happy."

    ctx.last_actor = char
    return ctx.trace("Happy", text, start)


@REGISTRY.kernel("Warning")
def kernel_warning(ctx: WorldContext, *args: Any, **kwargs: Any) -> StoryTrace:
    start = ctx.mark()
    chars = _characters(list(args))
    speaker = chars[0] if chars else ctx.last_actor
    listeners = chars[1:]

    if speaker is None:
        return ctx.trace("Warning", "A warning was given.", start)

    speaker += Warning(1.0, reason="Warning kernel")
    for listener in listeners:
        speaker.Warning += listener

    if listeners:
        names = " and ".join(listener.name for listener in listeners)
        text = f"{speaker.name} warned {names}."
    else:
        text = f"{speaker.name} gave a warning."

    ctx.last_actor = speaker
    return ctx.trace("Warning", text, start)


@REGISTRY.kernel("Anger")
def kernel_anger(ctx: WorldContext, *args: Any, **kwargs: Any) -> StoryTrace:
    start = ctx.mark()
    char = _first_character(list(args)) or ctx.last_actor

    if char is None:
        return ctx.trace("Anger", "Anger rose.", start)

    char += Anger(1.0, reason="Anger kernel")
    char -= Joy(0.2, reason="anger suppresses joy")
    ctx.last_actor = char
    return ctx.trace("Anger", f"{char.name} felt angry.", start)


@REGISTRY.kernel("Vanish")
def kernel_vanish(ctx: WorldContext, *args: Any, **kwargs: Any) -> StoryTrace:
    start = ctx.mark()
    obj = next((a for a in args if isinstance(a, WorldEntity)), None)

    if obj is None:
        return ctx.trace("Vanish", "Something vanished.", start)

    obj += Vanish(1.0, reason="Vanish kernel")
    obj.status = Fact("missing", reason="Vanish kernel")
    ctx.current_object = obj
    return ctx.trace("Vanish", f"{_phrase(obj).capitalize()} vanished.", start)


@REGISTRY.kernel("Loss")
def kernel_loss(ctx: WorldContext, *args: Any, **kwargs: Any) -> StoryTrace:
    start = ctx.mark()
    char = _first_character(list(args)) or ctx.last_actor
    obj = next((a for a in _non_character(list(args)) if isinstance(a, WorldEntity)), None)

    if obj is None:
        obj = ctx.current_object

    if char is not None and obj is not None:
        char += Loss(1.0, reason="Loss kernel")
        char.Loss += obj
        ctx.current_object = obj
        ctx.last_actor = char
        return ctx.trace("Loss", f"{char.name} lost {_phrase(obj)} and felt sad.", start)

    if obj is not None:
        obj.status = Fact("lost", reason="Loss kernel")
        return ctx.trace("Loss", f"{_phrase(obj).capitalize()} was lost.", start)

    return ctx.trace("Loss", "Something was lost.", start)


@REGISTRY.kernel("Search")
def kernel_search(ctx: WorldContext, *args: Any, **kwargs: Any) -> StoryTrace:
    start = ctx.mark()
    char = _first_character(list(args)) or ctx.last_actor
    obj = next((a for a in _non_character(list(args)) if isinstance(a, WorldEntity)), None)

    if obj is None:
        obj = ctx.current_object

    if char is not None and obj is not None:
        char += Search(1.0, reason="Search kernel")
        char.Search += obj
        ctx.last_actor = char
        return ctx.trace("Search", f"{char.name} searched for {_phrase(obj)}.", start)

    if char is not None:
        ctx.last_actor = char
        return ctx.trace("Search", f"{char.name} searched everywhere.", start)

    return ctx.trace("Search", "There was a search.", start)


@REGISTRY.kernel("Find")
def kernel_find(ctx: WorldContext, *args: Any, **kwargs: Any) -> StoryTrace:
    start = ctx.mark()
    char = _first_character(list(args)) or ctx.last_actor
    obj = next((a for a in _non_character(list(args)) if isinstance(a, WorldEntity)), None)
    location = kwargs.get("location")

    if char is not None and obj is not None:
        char += Find(1.0, reason="Find kernel")
        char.Find += obj
        if location is not None:
            obj.location = Fact(location, reason="Find location")
        ctx.current_object = obj
        ctx.last_actor = char

        if location is not None:
            text = f"{char.name} found {_phrase(obj)} near {_phrase(location)}."
        else:
            text = f"{char.name} found {_phrase(obj)}."
        return ctx.trace("Find", text, start)

    return ctx.trace("Find", "Something was found.", start)


@REGISTRY.kernel("Return")
def kernel_return(ctx: WorldContext, *args: Any, **kwargs: Any) -> StoryTrace:
    start = ctx.mark()
    chars = _characters(list(args))
    objects = [a for a in args if isinstance(a, WorldEntity) and a.kind != "character"]

    # Return(eraser, Lily): object transfer back to a character.
    if objects and chars:
        obj = objects[0]
        recipient = chars[0]
        giver = ctx.last_actor
        obj.Return += recipient
        if giver is not None:
            giver += Return(1.0, reason="Return kernel")
            giver.Return += obj
            text = f"{giver.name} returned {_phrase(obj)} to {recipient.name}."
        else:
            text = f"{_phrase(obj).capitalize()} was returned to {recipient.name}."
        ctx.current_object = obj
        ctx.last_actor = recipient
        return ctx.trace("Return", text, start)

    # Return(home): current actor goes back to a place.
    destination = objects[0] if objects else (args[0] if args else None)
    actor = chars[0] if chars else ctx.last_actor
    if actor is not None and destination is not None:
        actor += Return(1.0, reason="Return kernel")
        actor.Return += destination
        actor.location = Fact(destination, reason="Return destination")
        return ctx.trace("Return", f"{actor.name} returned to {_phrase(destination)}.", start)

    return ctx.trace("Return", "Someone returned.", start)


@REGISTRY.kernel("Joy")
def kernel_joy(ctx: WorldContext, char: Character | None = None) -> str:
    if char is None:
        return "There was joy."

    # Slot-style arithmetic also works; this is the closest form to gen5.py's
    # existing `char.Joy += 5` idiom.
    char.Joy += 1.0
    ctx.last_actor = char
    return f"{char.name} felt joyful."


@REGISTRY.kernel("Gratitude")
def kernel_gratitude(
    ctx: WorldContext,
    giver: Character | None = None,
    receiver: Character | None = None,
) -> str:
    if giver is None:
        return "There was gratitude."

    ctx.last_actor = giver
    if receiver is not None:
        giver.Gratitude += receiver
        return f"{giver.name} was grateful to {receiver.name}."

    giver += Gratitude(1.0, reason="Gratitude kernel")
    giver += Joy(0.3, reason="gratitude lifts joy")
    return f"{giver.name} felt grateful."


# ----------------------------
# AST execution
# ----------------------------

class WorldExecutor:
    def __init__(self, registry: WorldRegistry):
        self.registry = registry
        self.ctx = WorldContext(registry=registry)

    def execute(self, source: str) -> WorldContext:
        tree = ast.parse(source)
        for stmt in tree.body:
            if isinstance(stmt, ast.Expr):
                self._eval_expr(stmt.value)
        return self.ctx

    def _eval_expr(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Call):
            return self._eval_call(node)

        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left = self._eval_expr(node.left)
            right = self._eval_expr(node.right)
            return StoryTrace(
                kernel_name="Add",
                text=" ".join(part.text for part in (left, right) if isinstance(part, StoryTrace) and part.text),
            )

        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            divisor = self._constant_number(node.right) or 1.0
            old_attention = self.ctx.attention
            self.ctx.attention = old_attention / divisor
            try:
                return self._eval_expr(node.left)
            finally:
                self.ctx.attention = old_attention

        if isinstance(node, ast.Name):
            # At expression position, a bare uppercase registered kernel executes.
            if node.id in self.registry.kernels:
                return self._call_kernel(node.id, [])
            return self._eval_value(node)

        if isinstance(node, ast.Constant):
            return node.value

        raise NotImplementedError(f"Unsupported expression: {ast.dump(node)}")

    def _eval_call(self, node: ast.Call) -> StoryTrace:
        if not isinstance(node.func, ast.Name):
            raise NotImplementedError("Only Name(...) calls are supported in this prototype")

        func_name = node.func.id

        if self._is_character_declaration(node):
            return self._eval_character_declaration(node)

        args = [self._eval_value(arg) for arg in node.args]
        kwargs = {kw.arg: self._eval_value(kw.value) for kw in node.keywords if kw.arg is not None}
        return self._call_kernel(func_name, args, kwargs)

    def _call_kernel(self, name: str, args: List[Any], kwargs: Optional[Dict[str, Any]] = None) -> StoryTrace:
        kwargs = kwargs or {}
        kernel = self.registry.kernels.get(name)
        if kernel is None:
            # Unknown uppercase calls still behave like memeplex concepts.
            trace = StoryTrace(name, f"{name} entered the story.")
            self.ctx.traces.append(trace)
            return trace

        trace = kernel(self.ctx, *args, **kwargs)
        self.ctx.traces.append(trace)
        return trace

    def _eval_value(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Name):
            if node.id in self.ctx.entities:
                return self.ctx.entities[node.id]
            if node.id == "Character":
                return MemeRef("Character")
            if node.id and node.id[0].isupper():
                return MemeRef(node.id)
            return self.ctx.get_or_create_physical(node.id)

        if isinstance(node, ast.Constant):
            return node.value

        if isinstance(node, ast.List):
            return [self._eval_value(item) for item in node.elts]

        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return self._eval_expr(node)

        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            return self._eval_expr(node)

        if isinstance(node, ast.Call):
            return self._eval_expr(node)

        raise NotImplementedError(f"Unsupported value: {ast.dump(node)}")

    def _eval_character_declaration(self, node: ast.Call) -> StoryTrace:
        assert isinstance(node.func, ast.Name)
        start = self.ctx.mark()
        name = node.func.id
        type_name = "character"
        if len(node.args) >= 2 and isinstance(node.args[1], ast.Name):
            type_name = node.args[1].id

        traits: List[str] = []
        for trait_node in node.args[2:]:
            traits.extend(self._flatten_meme_names(trait_node))

        char = self.ctx.add_character(name, type_name, traits)
        trait_text = f" with {', '.join(traits)}" if traits else ""
        trace = self.ctx.trace("Character", f"{char.name} entered as a {type_name}{trait_text}.", start)
        self.ctx.traces.append(trace)
        return trace

    def _flatten_meme_names(self, node: ast.AST) -> List[str]:
        if isinstance(node, ast.Name):
            return [node.id]
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return self._flatten_meme_names(node.left) + self._flatten_meme_names(node.right)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            return [node.func.id]
        return [ast.unparse(node)]

    def _is_character_declaration(self, node: ast.Call) -> bool:
        return (
            isinstance(node.func, ast.Name)
            and bool(node.args)
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id == "Character"
        )

    def _constant_number(self, node: ast.AST) -> Optional[float]:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        return None


def execute_world(source: str) -> WorldContext:
    """Execute story-kernel source against the prototype world model."""
    executor = WorldExecutor(REGISTRY)
    return executor.execute(source)


# ----------------------------
# Demo
# ----------------------------

if __name__ == "__main__":
    src = """
Lily(Character, girl, Curious)
Fear(Lily, dog) + Brave(Lily)
Happy(Lily)

Mom(Character, mother, Strict)
Warning(Mom, Lily) + Anger

Vanish(eraser) + Loss(Lily, eraser) + Search(Lily, eraser)
Find(Mom, eraser, location=couch) + Return(eraser, Lily)
Joy(Lily) + Gratitude(Lily, Mom)
"""

    ctx = execute_world(src)

    print("--- SOURCE ---")
    print(src.strip())

    print("\n--- NARRATION TRACE ---")
    for trace in ctx.traces:
        if trace.text:
            print(trace.text)

    print("\n--- EFFECT TRACE ---")
    for effect in ctx.effects:
        print(effect.describe())

    print("\n--- WORLD STATE ---")
    print(ctx.format_state())
