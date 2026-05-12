"""
wrld6.py - Minimal typed world/memeplex kernel prototype.

This is a cleaner sketch after wrld5.py. The experiment here is:

  - kernels define typed parameters instead of parsing *args
  - the registry dispatches calls to the variant whose signature fits
  - actor/context fallback happens in the binder, not in every kernel
  - uppercase meme slots carry concept-specific `+=` behavior
  - kernel bodies return plain text; tracing is automatic

The desired kernel style is deliberately small:

  @REGISTRY.kernel("Gratitude")
  def Gratitude(ctx: World, giver: Character, receiver: Character) -> str:
      giver.Gratitude += receiver
      return f"{giver} was grateful to {receiver}."

  @REGISTRY.kernel("Find")
  def Find(ctx: World, finder: Character, obj: Physical, location: Physical) -> str:
      finder.Find += obj
      obj.location = location
      return f"{finder} found {obj} near {location}."

No `*args`, no `= None`, no repeated `is not None` checks in normal kernels.
Cases that are genuinely different become separate variants for the same kernel
name. Messy dataset shapes should be handled by AST rewrites or by dispatch
fallbacks, not by bloating every kernel body.
"""

from __future__ import annotations

import ast
import inspect
import types
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Tuple, Union, get_args, get_origin, get_type_hints


# ----------------------------
# Type markers
# ----------------------------

class Character:
    """A character entity in the story world."""


class Physical:
    """A lowercase physical/world object."""


class Actor:
    """The current actor; always supplied from World.actor."""


# ----------------------------
# World state
# ----------------------------

@dataclass
class Effect:
    kind: str
    target: str
    key: str
    value: Any

    def describe(self) -> str:
        if self.kind == "meme":
            sign = "+" if self.value >= 0 else ""
            return f"{self.target}.{self.key} {sign}{self.value:.2f}"
        if self.kind == "link":
            return f"{self.target}.{self.key} += {self.value}"
        return f"{self.target}.{self.key} = {self.value}"


@dataclass
class Trace:
    kernel: str
    text: str
    effects: List[Effect]


@dataclass
class Entity:
    name: str
    kind: str = "physical"
    type_name: str = "thing"
    world: "World | None" = field(default=None, repr=False)
    memes: Dict[str, float] = field(default_factory=dict)
    links: Dict[str, List[str]] = field(default_factory=dict)
    facts: Dict[str, str] = field(default_factory=dict)

    _FIELDS = {"name", "kind", "type_name", "world", "memes", "links", "facts"}

    def __str__(self) -> str:
        return self.name if self.kind == "character" else f"the {self.name}"

    def __getattr__(self, name: str) -> Any:
        if name in self.facts:
            return self.facts[name]
        if name and name[0].isupper():
            return MemeSlot(self, name)
        raise AttributeError(name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in Entity._FIELDS or name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        if isinstance(value, MemeSlot):
            # Augmented assignment assigns the slot back after it mutates.
            return
        self.fact(name, value)

    def meme(self, name: str) -> float:
        return self.memes.get(name, 0.0)

    def add_meme(self, name: str, amount: float) -> None:
        before = self.memes.get(name, 0.0)
        after = max(0.0, before + amount)
        delta = after - before
        self.memes[name] = after
        if self.world is not None and abs(delta) > 0.001:
            self.world.effect("meme", self.name, name, delta)

    def add_link(self, name: str, value: Any) -> None:
        rendered = _name(value)
        values = self.links.setdefault(name, [])
        if rendered not in values:
            values.append(rendered)
        if self.world is not None:
            self.world.effect("link", self.name, name, rendered)

    def fact(self, name: str, value: Any) -> None:
        rendered = _name(value)
        self.facts[name] = rendered
        if self.world is not None:
            self.world.effect("fact", self.name, name, rendered)


class MemeSlot:
    def __init__(self, owner: Entity, name: str):
        self.owner = owner
        self.name = name

    def __iadd__(self, value: Any) -> "MemeSlot":
        if isinstance(value, (int, float)):
            self.owner.add_meme(self.name, float(value))
        else:
            self.owner.world.add_to_meme(self.owner, self.name, value)
        return self

    def __isub__(self, value: Any) -> "MemeSlot":
        if not isinstance(value, (int, float)):
            raise TypeError("Meme subtraction expects a number")
        self.owner.add_meme(self.name, -float(value))
        return self

    def __gt__(self, value: float) -> bool:
        return self.owner.meme(self.name) > value


@dataclass
class World:
    registry: "Registry"
    entities: Dict[str, Entity] = field(default_factory=dict)
    effects: List[Effect] = field(default_factory=list)
    traces: List[Trace] = field(default_factory=list)
    actor: Entity | None = None
    current_object: Entity | None = None

    def character(self, name: str, type_name: str, traits: List[str]) -> Entity:
        entity = self.entities.get(name)
        if entity is None:
            entity = Entity(name=name, kind="character", type_name=type_name, world=self)
            self.entities[name] = entity
        else:
            entity.kind = "character"
            entity.type_name = type_name
            entity.world = self

        for trait in traits:
            entity.add_meme(trait, 1.0)
        self.actor = entity
        return entity

    def physical(self, name: str) -> Entity:
        entity = self.entities.get(name)
        if entity is None:
            entity = Entity(name=name, kind="physical", type_name="thing", world=self)
            self.entities[name] = entity
        return entity

    def effect(self, kind: str, target: str, key: str, value: Any) -> None:
        self.effects.append(Effect(kind, target, key, value))

    def add_to_meme(self, owner: Entity, meme: str, value: Any) -> None:
        self.registry.apply_addition(self, owner, meme, value)

    def state(self) -> str:
        lines: List[str] = []
        for entity in self.entities.values():
            parts = [f"{entity.name} ({entity.kind}:{entity.type_name})"]
            if entity.memes:
                parts.append("memes[" + ", ".join(f"{k}={v:.2f}" for k, v in sorted(entity.memes.items())) + "]")
            if entity.links:
                parts.append("links[" + ", ".join(f"{k}={'+'.join(v)}" for k, v in sorted(entity.links.items())) + "]")
            if entity.facts:
                parts.append("facts[" + ", ".join(f"{k}={v}" for k, v in sorted(entity.facts.items())) + "]")
            lines.append(" | ".join(parts))
        return "\n".join(lines)


# ----------------------------
# Registry and typed dispatch
# ----------------------------

@dataclass
class Variant:
    name: str
    fn: Callable[..., Any]
    signature: inspect.Signature
    hints: Dict[str, Any]


class Registry:
    def __init__(self) -> None:
        self.kernels: Dict[str, List[Variant]] = {}
        self.additions: Dict[Tuple[str, str], Callable[[World, Entity, Any], None]] = {}

    def kernel(self, name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            variant = Variant(name, fn, inspect.signature(fn), get_type_hints(fn, globalns=globals(), localns=locals()))
            self.kernels.setdefault(name, []).append(variant)
            return fn
        return decorator

    def addition(self, meme: str, rhs_type: Any) -> Callable[[Callable[[World, Entity, Any], None]], Callable[[World, Entity, Any], None]]:
        rhs_name = _type_name(rhs_type)

        def decorator(fn: Callable[[World, Entity, Any], None]) -> Callable[[World, Entity, Any], None]:
            self.additions[(meme, rhs_name)] = fn
            return fn
        return decorator

    def call(self, world: World, name: str, args: List[Any], kwargs: Dict[str, Any]) -> Trace:
        start = len(world.effects)
        variant, bound_args, bound_kwargs = self._select_variant(world, name, args, kwargs)
        result = variant.fn(world, *bound_args, **bound_kwargs)
        text = result.text if isinstance(result, Trace) else str(result or "")
        trace = Trace(name, text, world.effects[start:])
        world.traces.append(trace)
        return trace

    def apply_addition(self, world: World, owner: Entity, meme: str, value: Any) -> None:
        for rhs_type in _value_types(value):
            handler = self.additions.get((meme, rhs_type))
            if handler is not None:
                handler(world, owner, value)
                return
        owner.add_meme(meme, 1.0)
        owner.add_link(meme, value)

    def _select_variant(self, world: World, name: str, args: List[Any], kwargs: Dict[str, Any]) -> Tuple[Variant, List[Any], Dict[str, Any]]:
        candidates = []
        for variant in self.kernels.get(name, []):
            bound = _try_bind(world, variant, args, kwargs)
            if bound is not None:
                bound_count = len(bound[1]) + len(bound[2])
                candidates.append((-bound_count, bound[0], variant, bound[1], bound[2]))
        if not candidates:
            raise TypeError(f"No matching variant for {name}({', '.join(_name(a) for a in args)})")
        _, _, variant, bound_args, bound_kwargs = sorted(candidates, key=lambda item: (item[0], item[1]))[0]
        return variant, bound_args, bound_kwargs


REGISTRY = Registry()


def _try_bind(world: World, variant: Variant, args: List[Any], kwargs: Dict[str, Any]) -> Tuple[int, List[Any], Dict[str, Any]] | None:
    params = list(variant.signature.parameters.values())
    if params and params[0].name in ("ctx", "world"):
        params = params[1:]

    remaining = list(args)
    unused_kwargs = dict(kwargs)
    bound_args: List[Any] = []
    bound_kwargs: Dict[str, Any] = {}
    score = 0

    for param in params:
        annotation = variant.hints.get(param.name, param.annotation)
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            return None
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            bound_kwargs.update(unused_kwargs)
            unused_kwargs = {}
            continue

        if param.name in unused_kwargs:
            value = unused_kwargs.pop(param.name)
            if not _matches(value, annotation):
                return None
            score += 0
        elif annotation is Actor:
            index = _find_match(remaining, annotation)
            if index is not None:
                value = remaining.pop(index)
                score += index
            elif world.actor is not None:
                value = world.actor
                score += 1
            else:
                return None
        else:
            index = _find_match(remaining, annotation)
            if index is None:
                return None
            value = remaining.pop(index)
            score += index

        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            bound_kwargs[param.name] = value
        else:
            bound_args.append(value)

    if remaining or unused_kwargs:
        return None
    return score, bound_args, bound_kwargs


def _find_match(values: List[Any], annotation: Any) -> int | None:
    for i, value in enumerate(values):
        if _matches(value, annotation):
            return i
    return None


def _matches(value: Any, annotation: Any) -> bool:
    if annotation in (inspect._empty, Any):
        return True
    if annotation is Actor:
        return isinstance(value, Entity) and value.kind == "character"
    if annotation is Character:
        return isinstance(value, Entity) and value.kind == "character"
    if annotation is Physical:
        return isinstance(value, Entity) and value.kind != "character"
    if annotation is Entity:
        return isinstance(value, Entity)
    origin = get_origin(annotation)
    if origin in (Union, types.UnionType):
        return any(_matches(value, option) for option in get_args(annotation))
    return isinstance(annotation, type) and isinstance(value, annotation)


def _value_types(value: Any) -> List[str]:
    if isinstance(value, Entity):
        if value.kind == "character":
            return [value.type_name, "Character", "Entity", "Any"]
        return [value.type_name, "Physical", "Entity", "Any"]
    return [type(value).__name__, "Any"]


def _type_name(value: Any) -> str:
    if isinstance(value, str):
        return value
    return getattr(value, "__name__", str(value))


def _name(value: Any) -> str:
    if isinstance(value, Entity):
        return value.name
    return str(value)


def _phrase(value: Any) -> str:
    if isinstance(value, Entity):
        return str(value)
    return str(value)


# ----------------------------
# Memeplex operations
# ----------------------------

@REGISTRY.addition("Fear", Physical)
@REGISTRY.addition("Fear", Character)
def add_fear_target(world: World, owner: Entity, target: Entity) -> None:
    owner.add_meme("Fear", 1.0)
    owner.add_link("Fear", target)


@REGISTRY.addition("Warning", Character)
def add_warning_listener(world: World, owner: Entity, listener: Entity) -> None:
    owner.add_meme("Warning", 1.0)
    owner.add_link("Warning", listener)
    owner.add_meme("Authority", 0.35)


@REGISTRY.addition("Loss", Physical)
@REGISTRY.addition("Loss", Character)
def add_loss_target(world: World, owner: Entity, target: Entity) -> None:
    owner.add_meme("Loss", 1.0)
    owner.add_link("Loss", target)
    owner.add_meme("Sadness", 0.8)
    if target.kind != "character":
        target.owner = "unknown"
        target.status = "lost"


@REGISTRY.addition("Search", Physical)
@REGISTRY.addition("Search", Character)
def add_search_target(world: World, owner: Entity, target: Entity) -> None:
    owner.add_meme("Search", 1.0)
    owner.add_link("Search", target)
    owner.add_meme("Hope", 0.25)


@REGISTRY.addition("Find", Physical)
@REGISTRY.addition("Find", Character)
def add_find_target(world: World, owner: Entity, target: Entity) -> None:
    owner.add_meme("Find", 1.0)
    owner.add_link("Find", target)
    owner.add_meme("Joy", 0.35)
    target.status = "found"
    target.finder = owner


@REGISTRY.addition("Return", Character)
def add_return_recipient(world: World, owner: Entity, recipient: Entity) -> None:
    owner.add_meme("Return", 1.0)
    owner.add_link("Return", recipient)
    if owner.kind != "character":
        owner.owner = recipient
        owner.status = "returned"
        recipient.Relief += 0.7


@REGISTRY.addition("Return", Physical)
def add_return_object(world: World, owner: Entity, obj: Entity) -> None:
    owner.add_meme("Return", 1.0)
    owner.add_link("Return", obj)


@REGISTRY.addition("Gratitude", Character)
def add_gratitude_receiver(world: World, owner: Entity, receiver: Entity) -> None:
    owner.add_meme("Gratitude", 1.0)
    owner.add_link("Gratitude", receiver)
    owner.Joy += 0.3


# ----------------------------
# Kernels
# ----------------------------

@REGISTRY.kernel("Fear")
def Fear(ctx: World, char: Character, target: Physical) -> str:
    char.Fear += target
    ctx.actor = char
    return f"{char} became afraid of {target}."


@REGISTRY.kernel("Brave")
def Brave(ctx: World, char: Character) -> str:
    had_fear = char.Fear > 0.2
    char.Brave += 1
    char.Fear -= 0.35
    ctx.actor = char
    if had_fear:
        return f"Even though {char} was afraid, {char} acted bravely."
    return f"{char} acted bravely."


@REGISTRY.kernel("Happy")
def Happy(ctx: World, char: Actor) -> str:
    was_brave = char.Brave > 0
    char.Joy += 1
    char.Fear -= 0.2
    if was_brave:
        return f"After being brave, {char} felt happy."
    return f"{char} felt happy."


@REGISTRY.kernel("Warning")
def Warning(ctx: World, speaker: Character, listener: Character) -> str:
    speaker.Warning += listener
    ctx.actor = speaker
    return f"{speaker} warned {listener}."


@REGISTRY.kernel("Anger")
def Anger(ctx: World, char: Actor) -> str:
    char.Anger += 1
    char.Joy -= 0.2
    return f"{char} felt angry."


@REGISTRY.kernel("Vanish")
def Vanish(ctx: World, obj: Physical) -> str:
    obj.Vanish += 1
    obj.status = "missing"
    ctx.current_object = obj
    return f"{str(obj).capitalize()} vanished."


@REGISTRY.kernel("Loss")
def Loss(ctx: World, owner: Character, obj: Physical) -> str:
    owner.Loss += obj
    ctx.actor = owner
    ctx.current_object = obj
    return f"{owner} lost {obj} and felt sad."


@REGISTRY.kernel("Search")
def Search(ctx: World, actor: Character, obj: Physical) -> str:
    actor.Search += obj
    ctx.actor = actor
    return f"{actor} searched for {obj}."


@REGISTRY.kernel("Find")
def Find(ctx: World, finder: Character, obj: Physical) -> str:
    finder.Find += obj
    ctx.actor = finder
    ctx.current_object = obj
    return f"{finder} found {obj}."


@REGISTRY.kernel("Find")
def FindAt(ctx: World, finder: Character, obj: Physical, location: Physical) -> str:
    finder.Find += obj
    obj.location = location
    ctx.actor = finder
    ctx.current_object = obj
    return f"{finder} found {obj} near {location}."


@REGISTRY.kernel("Return")
def Return(ctx: World, giver: Actor, obj: Physical, recipient: Character) -> str:
    obj.Return += recipient
    giver.Return += obj
    ctx.actor = recipient
    ctx.current_object = obj
    return f"{giver} returned {obj} to {recipient}."


@REGISTRY.kernel("Joy")
def Joy(ctx: World, char: Character) -> str:
    char.Joy += 1
    ctx.actor = char
    return f"{char} felt joyful."


@REGISTRY.kernel("Gratitude")
def Gratitude(ctx: World, giver: Character, receiver: Character) -> str:
    giver.Gratitude += receiver
    ctx.actor = giver
    return f"{giver} was grateful to {receiver}."


@REGISTRY.kernel("Gratitude")
def GratitudeFeeling(ctx: World, giver: Actor) -> str:
    giver.Gratitude += 1
    giver.Joy += 0.3
    return f"{giver} felt grateful."


@REGISTRY.kernel("Gratitude")
def GratitudeConcept(ctx: World) -> str:
    return "There was gratitude."


# ----------------------------
# AST execution
# ----------------------------

class Executor:
    def __init__(self, registry: Registry):
        self.world = World(registry=registry)

    def execute(self, source: str) -> World:
        tree = ast.parse(source)
        for stmt in tree.body:
            if isinstance(stmt, ast.Expr):
                self.eval(stmt.value)
        return self.world

    def eval(self, node: ast.AST) -> Any:
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left = self.eval(node.left)
            right = self.eval(node.right)
            return Trace("Add", " ".join(t.text for t in (left, right) if isinstance(t, Trace)), [])

        if isinstance(node, ast.Call):
            if self.is_character_decl(node):
                return self.character_decl(node)
            if not isinstance(node.func, ast.Name):
                raise TypeError("Only Name(...) calls are supported")
            args = [self.value(arg) for arg in node.args]
            kwargs = {kw.arg: self.value(kw.value) for kw in node.keywords if kw.arg is not None}
            return REGISTRY.call(self.world, node.func.id, args, kwargs)

        if isinstance(node, ast.Name):
            if node.id in REGISTRY.kernels:
                return REGISTRY.call(self.world, node.id, [], {})
            return self.value(node)

        raise TypeError(f"Unsupported AST: {ast.dump(node)}")

    def value(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Name):
            if node.id in self.world.entities:
                return self.world.entities[node.id]
            if node.id and node.id[0].isupper():
                return node.id
            return self.world.physical(node.id)
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Call):
            return self.eval(node)
        raise TypeError(f"Unsupported value AST: {ast.dump(node)}")

    def is_character_decl(self, node: ast.Call) -> bool:
        return (
            isinstance(node.func, ast.Name)
            and node.args
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id == "Character"
        )

    def character_decl(self, node: ast.Call) -> Trace:
        assert isinstance(node.func, ast.Name)
        start = len(self.world.effects)
        name = node.func.id
        type_name = node.args[1].id if len(node.args) > 1 and isinstance(node.args[1], ast.Name) else "character"
        traits: List[str] = []
        for arg in node.args[2:]:
            traits.extend(self.traits(arg))
        entity = self.world.character(name, type_name, traits)
        text = f"{entity} entered as a {type_name}" + (f" with {', '.join(traits)}." if traits else ".")
        trace = Trace("Character", text, self.world.effects[start:])
        self.world.traces.append(trace)
        return trace

    def traits(self, node: ast.AST) -> List[str]:
        if isinstance(node, ast.Name):
            return [node.id]
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return self.traits(node.left) + self.traits(node.right)
        return [ast.unparse(node)]


def execute_world(source: str) -> World:
    return Executor(REGISTRY).execute(source)


if __name__ == "__main__":
    src = """
Lily(Character, girl, Curious)
Fear(Lily, dog) + Brave(Lily)
Happy

Mom(Character, mother, Strict)
Warning(Mom, Lily) + Anger

Vanish(eraser) + Loss(Lily, eraser) + Search(Lily, eraser)
Find(Mom, eraser, location=couch) + Return(eraser, Lily)
Joy(Lily) + Gratitude(Lily, Mom)
"""

    world = execute_world(src)

    print("--- SOURCE ---")
    print(src.strip())

    print("\n--- NARRATION TRACE ---")
    for trace in world.traces:
        print(trace.text)

    print("\n--- EFFECT TRACE ---")
    for effect in world.effects:
        print(effect.describe())

    print("\n--- WORLD STATE ---")
    print(world.state())
