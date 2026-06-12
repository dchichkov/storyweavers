"""
gen6.py - Unified story engine: typed world + AST->AST rewrites + coherency.

This module assembles two earlier prototypes into a single, self-contained
generation engine:

  * wrld6.py - a typed "world / memeplex" executor. Kernels declare typed
    parameters; a backtracking dispatcher binds arguments; uppercase meme slots
    carry concept-specific ``+=`` behaviour; effects and narration are traced
    automatically.

  * rewr6.py - a declarative AST -> AST rewrite engine. Rules are written in the
    same pseudo-Python "story algebra" and rewrite kernel source *before*
    execution (normalization, enrichment, prerequisites).

gen6 keeps wrld6.py and rewr6.py as standalone demos and re-implements the parts
it needs here, plus a thin **coherency layer**:

  1. Declarative rewrites run first (enrich / normalize the AST).
  2. A coherence pass tags repeated subjects so the renderer uses pronouns and
     can inject transitions - the recurring weakness of the gen5 engine, where
     every kernel had to make these decisions on its own.
  3. The typed world executor runs the transformed source and traces narration.

Pipeline::

    source --[declarative rewrites]--> source' --[coherence pass]--> source''
           --[typed world execution]--> traces --[narrate]--> story

The kernel set here is intentionally *minimal* - a representative slice ported
from gen5.py - to exercise the engine end to end. gen5.py is left untouched.
"""

from __future__ import annotations

import ast
import copy
import inspect
import re
import types
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, get_args, get_origin, get_type_hints


# =============================================================================
# Type markers
# =============================================================================

class Character:
    """A character entity in the story world."""


class Physical:
    """A lowercase physical / world object."""


class Actor:
    """The current actor; supplied from World.actor when not passed explicitly."""


# Keyword arguments that the coherency layer injects and the engine consumes
# centrally (so kernel signatures stay clean and typed).
COHERENCE_KWARGS = ("_use_pronoun", "_transition")


# =============================================================================
# Pronouns
# =============================================================================

_SHE_TYPES = {
    "girl", "woman", "queen", "princess", "mother", "mom", "mommy", "grandma",
    "lady", "aunt", "sister", "daughter", "hen", "cow", "she",
}
_HE_TYPES = {
    "boy", "man", "king", "prince", "father", "dad", "daddy", "grandpa",
    "uncle", "brother", "son", "rooster", "he",
}


def _pronouns_for(type_name: str) -> Tuple[str, str, str]:
    """Return (subject, object, possessive) pronouns for a character type."""
    t = (type_name or "").lower()
    if t in _SHE_TYPES:
        return ("she", "her", "her")
    if t in _HE_TYPES:
        return ("he", "him", "his")
    return ("they", "them", "their")


# =============================================================================
# World state: effects, traces, entities
# =============================================================================

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
            # Augmented assignment reassigns the slot after it mutates; ignore.
            return
        self.fact(name, value)

    # -- pronouns -----------------------------------------------------------
    def pronoun(self, case: str = "subject") -> str:
        subj, obj, poss = _pronouns_for(self.type_name)
        return {"subject": subj, "object": obj, "possessive": poss}.get(case, subj)

    # -- meme / link / fact mutation ---------------------------------------
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
    """Proxy returned for ``entity.Uppercase`` so kernels can write ``x.Joy += 1``
    or ``x.Fear += dog`` (link) and read ``x.Fear > 0.2`` (magnitude)."""

    def __init__(self, owner: Entity, name: str):
        self.owner = owner
        self.name = name

    def __iadd__(self, value: Any) -> "MemeSlot":
        if isinstance(value, (int, float)):
            self.owner.add_meme(self.name, float(value))
        elif self.owner.world is not None:
            self.owner.world.add_to_meme(self.owner, self.name, value)
        else:
            self.owner.add_meme(self.name, 1.0)
            self.owner.add_link(self.name, value)
        return self

    def __isub__(self, value: Any) -> "MemeSlot":
        if not isinstance(value, (int, float)):
            raise TypeError("Meme subtraction expects a number")
        self.owner.add_meme(self.name, -float(value))
        return self

    def __float__(self) -> float:
        return self.owner.meme(self.name)

    def _val(self) -> float:
        return self.owner.meme(self.name)

    def __gt__(self, other: float) -> bool:
        return self._val() > other

    def __ge__(self, other: float) -> bool:
        return self._val() >= other

    def __lt__(self, other: float) -> bool:
        return self._val() < other

    def __le__(self, other: float) -> bool:
        return self._val() <= other


@dataclass
class World:
    registry: "Registry"
    entities: Dict[str, Entity] = field(default_factory=dict)
    effects: List[Effect] = field(default_factory=list)
    traces: List[Trace] = field(default_factory=list)
    actor: Entity | None = None
    current_object: Entity | None = None

    # Coherency state, set per-call from injected kwargs.
    use_pronoun: bool = False

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

    def say(self, entity: Any) -> str:
        """Render a sentence subject, honouring the coherence pronoun flag.

        Kernels call this for the *grammatical subject* only; other references
        (objects, recipients) should be rendered as plain ``{entity}``.
        """
        if self.use_pronoun and isinstance(entity, Entity) and entity.kind == "character":
            return entity.pronoun("subject")
        return _name(entity) if isinstance(entity, Entity) else str(entity)

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


# =============================================================================
# Registry and typed dispatch
# =============================================================================

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
            variant = Variant(
                name, fn, inspect.signature(fn),
                get_type_hints(fn, globalns=globals(), localns=locals()),
            )
            self.kernels.setdefault(name, []).append(variant)
            return fn
        return decorator

    def addition(self, meme: str, rhs_type: Any) -> Callable[[Callable[..., None]], Callable[..., None]]:
        rhs_name = _type_name(rhs_type)

        def decorator(fn: Callable[[World, Entity, Any], None]) -> Callable[[World, Entity, Any], None]:
            self.additions[(meme, rhs_name)] = fn
            return fn
        return decorator

    def call(self, world: World, name: str, args: List[Any], kwargs: Dict[str, Any]) -> Trace:
        # Pull coherence directives out before binding so kernel signatures stay
        # clean and typed.
        kwargs = dict(kwargs)
        world.use_pronoun = bool(kwargs.pop("_use_pronoun", False))
        transition = str(kwargs.pop("_transition", "") or "")
        for extra in COHERENCE_KWARGS:
            kwargs.pop(extra, None)

        start = len(world.effects)
        variant, bound_args, bound_kwargs = self._select_variant(world, name, args, kwargs)
        result = variant.fn(world, *bound_args, **bound_kwargs)
        body = result.text if isinstance(result, Trace) else str(result or "")
        text = (transition + body) if body else ""
        trace = Trace(name, text, world.effects[start:])
        world.traces.append(trace)
        world.use_pronoun = False
        return trace

    def apply_addition(self, world: World, owner: Entity, meme: str, value: Any) -> None:
        for rhs_type in _value_types(value):
            handler = self.additions.get((meme, rhs_type))
            if handler is not None:
                handler(world, owner, value)
                return
        owner.add_meme(meme, 1.0)
        owner.add_link(meme, value)

    def _select_variant(self, world: World, name: str, args: List[Any], kwargs: Dict[str, Any]):
        candidates = []
        for variant in self.kernels.get(name, []):
            bound = _try_bind(world, variant, args, kwargs)
            if bound is not None:
                score, bound_args, bound_kwargs = bound
                bound_count = len(bound_args) + len(bound_kwargs)
                candidates.append((-bound_count, score, variant, bound_args, bound_kwargs))
        if not candidates:
            raise TypeError(f"No matching variant for {name}({', '.join(_name(a) for a in args)})")
        # Enumeration index is the final tie-breaker so we never have to compare
        # Variant objects (which are not orderable).
        ranked = sorted(
            ((c[0], c[1], i, c[2], c[3], c[4]) for i, c in enumerate(candidates)),
            key=lambda c: (c[0], c[1], c[2]),
        )
        _, _, _, variant, bound_args, bound_kwargs = ranked[0]
        return variant, bound_args, bound_kwargs


REGISTRY = Registry()


_ACTOR_FALLBACK_PENALTY = 1000


def _try_bind(world: World, variant: Variant, args: List[Any], kwargs: Dict[str, Any]):
    """Backtracking binder.

    Finds a complete assignment of positional args to typed parameters (allowing
    ``Actor`` params to fall back to ``world.actor``), preferring explicit
    bindings and earlier argument positions. Returns ``(score, [], by_name)`` or
    ``None``. Everything is passed by name to avoid positional/keyword misalign.
    """
    params = list(variant.signature.parameters.values())
    if params and params[0].name in ("ctx", "world"):
        params = params[1:]

    unused_kwargs = dict(kwargs)
    var_keyword = False
    kw_bound: Dict[str, Any] = {}
    plan: List[Tuple[inspect.Parameter, Any]] = []

    for param in params:
        annotation = variant.hints.get(param.name, param.annotation)
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            return None
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            var_keyword = True
            continue
        if param.name in unused_kwargs:
            value = unused_kwargs.pop(param.name)
            if not _matches(value, annotation):
                return None
            kw_bound[param.name] = value
            continue
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            if param.default is inspect.Parameter.empty:
                return None  # required keyword not supplied
            continue  # optional keyword: use its default
        if param.default is not inspect.Parameter.empty:
            continue  # optional positional with default: skip unless matched below
        plan.append((param, annotation))

    if unused_kwargs and not var_keyword:
        return None

    pool = list(enumerate(args))
    best: Tuple[int, Dict[str, Any]] | None = None

    def search(i: int, available: List[Tuple[int, Any]], score: int, assigned: Dict[str, Any]) -> None:
        nonlocal best
        if i == len(plan):
            if not available and (best is None or score < best[0]):
                best = (score, dict(assigned))
            return
        param, annotation = plan[i]
        for k, (orig_index, value) in enumerate(available):
            if _matches(value, annotation):
                assigned[param.name] = value
                search(i + 1, available[:k] + available[k + 1:], score + orig_index, assigned)
                del assigned[param.name]
        if annotation is Actor and world.actor is not None:
            assigned[param.name] = world.actor
            search(i + 1, available, score + _ACTOR_FALLBACK_PENALTY, assigned)
            del assigned[param.name]

    search(0, pool, 0, {})
    if best is None:
        return None

    score, assigned = best
    bound_kwargs: Dict[str, Any] = {}
    bound_kwargs.update(kw_bound)
    bound_kwargs.update(assigned)
    if var_keyword:
        bound_kwargs.update(unused_kwargs)
    return score, [], bound_kwargs


def _matches(value: Any, annotation: Any) -> bool:
    if annotation in (inspect._empty, Any):
        return True
    if annotation is Actor or annotation is Character:
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


# =============================================================================
# Memeplex additions (concept-specific `+=` behaviour)
# =============================================================================

@REGISTRY.addition("Fear", Physical)
@REGISTRY.addition("Fear", Character)
def _add_fear(world: World, owner: Entity, target: Entity) -> None:
    owner.add_meme("Fear", 1.0)
    owner.add_link("Fear", target)


@REGISTRY.addition("Loss", Physical)
@REGISTRY.addition("Loss", Character)
def _add_loss(world: World, owner: Entity, target: Entity) -> None:
    owner.add_meme("Loss", 1.0)
    owner.add_link("Loss", target)
    owner.add_meme("Sadness", 0.8)
    if target.kind != "character":
        target.status = "lost"


@REGISTRY.addition("Search", Physical)
@REGISTRY.addition("Search", Character)
def _add_search(world: World, owner: Entity, target: Entity) -> None:
    owner.add_meme("Search", 1.0)
    owner.add_link("Search", target)
    owner.add_meme("Hope", 0.25)


@REGISTRY.addition("Find", Physical)
@REGISTRY.addition("Find", Character)
def _add_find(world: World, owner: Entity, target: Entity) -> None:
    owner.add_meme("Find", 1.0)
    owner.add_link("Find", target)
    owner.add_meme("Joy", 0.35)
    target.status = "found"


@REGISTRY.addition("Return", Character)
def _add_return(world: World, owner: Entity, recipient: Entity) -> None:
    owner.add_meme("Return", 1.0)
    owner.add_link("Return", recipient)
    recipient.Relief += 0.6


@REGISTRY.addition("Warning", Character)
def _add_warning(world: World, owner: Entity, listener: Entity) -> None:
    owner.add_meme("Warning", 1.0)
    owner.add_link("Warning", listener)
    owner.add_meme("Authority", 0.35)


@REGISTRY.addition("Gratitude", Character)
def _add_gratitude(world: World, owner: Entity, receiver: Entity) -> None:
    owner.add_meme("Gratitude", 1.0)
    owner.add_link("Gratitude", receiver)
    owner.Joy += 0.3


@REGISTRY.addition("Friendship", Character)
def _add_friendship(world: World, owner: Entity, other: Entity) -> None:
    owner.add_meme("Friendship", 1.0)
    owner.add_link("Friendship", other)
    owner.Love += 0.5


@REGISTRY.addition("Give", Physical)
@REGISTRY.addition("Give", Character)
def _add_give(world: World, owner: Entity, target: Entity) -> None:
    owner.add_meme("Give", 1.0)
    owner.add_link("Give", target)


@REGISTRY.addition("Help", Character)
def _add_help(world: World, owner: Entity, other: Entity) -> None:
    owner.add_meme("Help", 1.0)
    owner.add_link("Help", other)
    owner.Love += 0.3


# =============================================================================
# Kernels (minimal typed set ported from gen5.py)
# =============================================================================

# --- emotions / states -------------------------------------------------------

@REGISTRY.kernel("Happy")
def Happy(ctx: World, char: Actor) -> str:
    was_brave = char.Brave > 0
    char.Joy += 1
    char.Fear -= 0.2
    if was_brave:
        return f"After being brave, {ctx.say(char)} felt happy."
    return f"{ctx.say(char)} felt happy."


@REGISTRY.kernel("Joy")
def Joy(ctx: World, char: Actor) -> str:
    char.Joy += 1
    return f"{ctx.say(char)} felt full of joy."


@REGISTRY.kernel("Sadness")
@REGISTRY.kernel("Sad")
def Sad(ctx: World, char: Actor) -> str:
    char.Sadness += 1
    char.Joy -= 0.3
    return f"{ctx.say(char)} felt sad."


@REGISTRY.kernel("Anger")
def Anger(ctx: World, char: Actor) -> str:
    char.Anger += 1
    char.Joy -= 0.2
    return f"{ctx.say(char)} felt angry."


@REGISTRY.kernel("Surprise")
def Surprise(ctx: World, char: Actor) -> str:
    char.Surprise += 1
    return f"{ctx.say(char)} was very surprised."


@REGISTRY.kernel("Proud")
@REGISTRY.kernel("Pride")
def Proud(ctx: World, char: Actor) -> str:
    char.Pride += 1
    char.Joy += 0.5
    return f"{ctx.say(char)} felt proud."


@REGISTRY.kernel("Fear")
def Fear(ctx: World, char: Character, target: Physical) -> str:
    char.Fear += target
    ctx.actor = char
    return f"{ctx.say(char)} became afraid of {target}."


@REGISTRY.kernel("Fear")
def FearFeeling(ctx: World, char: Actor) -> str:
    char.Fear += 1
    return f"{ctx.say(char)} felt scared."


@REGISTRY.kernel("Brave")
def Brave(ctx: World, char: Character) -> str:
    had_fear = char.Fear > 0.2
    char.Brave += 1
    char.Fear -= 0.35
    ctx.actor = char
    if had_fear:
        return f"Even though {ctx.say(char)} was afraid, {ctx.say(char)} was brave."
    return f"{ctx.say(char)} was very brave."


# --- actions on objects ------------------------------------------------------

@REGISTRY.kernel("Vanish")
def Vanish(ctx: World, obj: Physical) -> str:
    obj.Vanish += 1
    obj.status = "missing"
    ctx.current_object = obj
    return f"{str(obj).capitalize()} suddenly vanished."


@REGISTRY.kernel("Loss")
def Loss(ctx: World, owner: Character, obj: Physical) -> str:
    owner.Loss += obj
    ctx.actor = owner
    ctx.current_object = obj
    return f"{ctx.say(owner)} lost {obj} and felt sad."


@REGISTRY.kernel("Search")
def Search(ctx: World, actor: Character, obj: Physical) -> str:
    actor.Search += obj
    ctx.actor = actor
    return f"{ctx.say(actor)} looked everywhere for {obj}."


@REGISTRY.kernel("Find")
def Find(ctx: World, finder: Character, obj: Physical) -> str:
    finder.Find += obj
    ctx.actor = finder
    ctx.current_object = obj
    return f"{ctx.say(finder)} finally found {obj}."


@REGISTRY.kernel("Find")
def FindAt(ctx: World, finder: Character, obj: Physical, location: Physical) -> str:
    finder.Find += obj
    obj.location = location
    ctx.actor = finder
    ctx.current_object = obj
    return f"{ctx.say(finder)} found {obj} near {location}."


@REGISTRY.kernel("Return")
def Return(ctx: World, giver: Actor, obj: Physical, recipient: Character) -> str:
    obj.add_meme("Return", 1.0)
    giver.Return += recipient
    ctx.actor = recipient
    ctx.current_object = obj
    return f"{ctx.say(giver)} returned {obj} to {recipient}."


@REGISTRY.kernel("See")
def See(ctx: World, char: Character, obj: Physical) -> str:
    ctx.actor = char
    ctx.current_object = obj
    return f"{ctx.say(char)} saw {obj}."


# --- movement ----------------------------------------------------------------

@REGISTRY.kernel("Run")
def Run(ctx: World, char: Actor) -> str:
    char.Fear += 0.2
    return f"{ctx.say(char)} ran away as fast as possible."


@REGISTRY.kernel("Walk")
def Walk(ctx: World, char: Actor) -> str:
    return f"{ctx.say(char)} went for a walk."


# --- social ------------------------------------------------------------------

@REGISTRY.kernel("Give")
def Give(ctx: World, giver: Character, obj: Physical, receiver: Character) -> str:
    giver.Give += obj
    receiver.Joy += 0.4
    ctx.actor = giver
    return f"{ctx.say(giver)} gave {obj} to {receiver}."


@REGISTRY.kernel("Share")
def Share(ctx: World, char: Character, obj: Physical, other: Character) -> str:
    char.Love += 0.3
    ctx.actor = char
    return f"{ctx.say(char)} shared {obj} with {other}."


@REGISTRY.kernel("Help")
def Help(ctx: World, helper: Character, other: Character) -> str:
    helper.Help += other
    ctx.actor = helper
    return f"{ctx.say(helper)} helped {other}."


@REGISTRY.kernel("Play")
def PlayWith(ctx: World, char: Character, other: Character) -> str:
    char.Joy += 0.5
    ctx.actor = char
    return f"{ctx.say(char)} played happily with {other}."


@REGISTRY.kernel("Play")
def PlayObject(ctx: World, char: Character, obj: Physical) -> str:
    char.Joy += 0.4
    ctx.actor = char
    return f"{ctx.say(char)} played with {obj}."


@REGISTRY.kernel("Hug")
def Hug(ctx: World, char: Character, other: Character) -> str:
    char.Love += 0.5
    ctx.actor = char
    return f"{ctx.say(char)} gave {other} a big hug."


@REGISTRY.kernel("Cry")
def Cry(ctx: World, char: Actor) -> str:
    char.Sadness += 1
    return f"{ctx.say(char)} began to cry."


@REGISTRY.kernel("Laugh")
def Laugh(ctx: World, char: Actor) -> str:
    char.Joy += 0.6
    return f"{ctx.say(char)} laughed and laughed."


@REGISTRY.kernel("Friendship")
def Friendship(ctx: World, a: Character, b: Character) -> str:
    a.Friendship += b
    ctx.actor = a
    return f"{ctx.say(a)} and {b} became good friends."


@REGISTRY.kernel("Gratitude")
def Gratitude(ctx: World, giver: Character, receiver: Character) -> str:
    giver.Gratitude += receiver
    ctx.actor = giver
    return f"{ctx.say(giver)} was very grateful to {receiver}."


@REGISTRY.kernel("Gratitude")
def GratitudeFeeling(ctx: World, giver: Actor) -> str:
    giver.Gratitude += 1
    giver.Joy += 0.3
    return f"{ctx.say(giver)} felt grateful."


@REGISTRY.kernel("Warning")
def Warning(ctx: World, speaker: Character, listener: Character) -> str:
    speaker.Warning += listener
    ctx.actor = speaker
    return f"{ctx.say(speaker)} warned {listener} to be careful."


@REGISTRY.kernel("Comfort")
def Comfort(ctx: World, char: Character, other: Character) -> str:
    char.Love += 0.3
    other.Sadness -= 0.5
    ctx.actor = char
    return f"{ctx.say(char)} comforted {other}."


@REGISTRY.kernel("Apology")
def Apology(ctx: World, char: Character, other: Character) -> str:
    char.Love += 0.2
    ctx.actor = char
    return f"{ctx.say(char)} said sorry to {other}."


@REGISTRY.kernel("Apology")
def ApologyAlone(ctx: World, char: Actor) -> str:
    return f"{ctx.say(char)} apologized."


@REGISTRY.kernel("Thank")
def Thank(ctx: World, char: Character, other: Character) -> str:
    char.Gratitude += other
    ctx.actor = char
    return f"{ctx.say(char)} thanked {other}."


# --- lesson / endings --------------------------------------------------------

@REGISTRY.kernel("Lesson")
def Lesson(ctx: World, char: Actor) -> str:
    char.Wisdom += 1
    return f"{ctx.say(char)} learned an important lesson that day."


@REGISTRY.kernel("HappyEnd")
@REGISTRY.kernel("HappilyEverAfter")
def HappyEnd(ctx: World) -> str:
    return "And from that day on, everyone was happy."


# =============================================================================
# AST -> AST rewrite engine (from rewr6.py)
# =============================================================================

@dataclass(frozen=True)
class Rewrite:
    pattern_src: str
    output_src: str

    def pattern_ast(self) -> ast.AST:
        return ast.parse(self.pattern_src, mode="eval").body

    def output_ast(self) -> ast.AST:
        return ast.parse(self.output_src, mode="eval").body


Bindings = Dict[str, ast.AST]


def _is_meta_name(name: str) -> bool:
    return name.startswith("__") and len(name) > 2


def _ast_equal(a: ast.AST, b: ast.AST) -> bool:
    return ast.dump(a, include_attributes=False) == ast.dump(b, include_attributes=False)


def flatten_add(node: ast.AST) -> List[ast.AST]:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return flatten_add(node.left) + flatten_add(node.right)
    return [node]


def rebuild_add(items: List[ast.AST]) -> ast.AST:
    if not items:
        raise ValueError("Cannot rebuild empty add-chain")
    node = copy.deepcopy(items[0])
    for item in items[1:]:
        node = ast.BinOp(left=node, op=ast.Add(), right=copy.deepcopy(item))
    return node


def match_pattern(pattern: ast.AST, target: ast.AST, env: Bindings) -> Optional[Bindings]:
    if isinstance(pattern, ast.Name) and _is_meta_name(pattern.id):
        bound = env.get(pattern.id)
        if bound is None:
            env2 = dict(env)
            env2[pattern.id] = target
            return env2
        return env if _ast_equal(bound, target) else None

    if isinstance(pattern, ast.Name) and isinstance(target, ast.Name):
        return env if pattern.id == target.id else None

    if isinstance(pattern, ast.Constant) and isinstance(target, ast.Constant):
        return env if pattern.value == target.value else None

    if isinstance(pattern, ast.Call) and isinstance(target, ast.Call):
        env2: Optional[Bindings] = match_pattern(pattern.func, target.func, dict(env))
        if env2 is None:
            return None
        if len(pattern.args) != len(target.args):
            return None
        for p_arg, t_arg in zip(pattern.args, target.args):
            env2 = match_pattern(p_arg, t_arg, env2)
            if env2 is None:
                return None
        if len(pattern.keywords) != len(target.keywords):
            return None
        for p_kw, t_kw in zip(pattern.keywords, target.keywords):
            if p_kw.arg != t_kw.arg:
                return None
            env2 = match_pattern(p_kw.value, t_kw.value, env2)
            if env2 is None:
                return None
        return env2

    if isinstance(pattern, ast.BinOp) and isinstance(target, ast.BinOp):
        if not (isinstance(pattern.op, ast.Add) and isinstance(target.op, ast.Add)):
            return None
        env2 = match_pattern(pattern.left, target.left, dict(env))
        if env2 is None:
            return None
        return match_pattern(pattern.right, target.right, env2)

    return env if _ast_equal(pattern, target) else None


def substitute(template: ast.AST, env: Bindings) -> ast.AST:
    if isinstance(template, ast.Name) and _is_meta_name(template.id) and template.id in env:
        return copy.deepcopy(env[template.id])
    if isinstance(template, ast.Call):
        return ast.Call(
            func=substitute(template.func, env),
            args=[substitute(arg, env) for arg in template.args],
            keywords=[ast.keyword(arg=kw.arg, value=substitute(kw.value, env)) for kw in template.keywords],
        )
    if isinstance(template, ast.BinOp):
        return ast.BinOp(
            left=substitute(template.left, env),
            op=copy.deepcopy(template.op),
            right=substitute(template.right, env),
        )
    return copy.deepcopy(template)


class _ApplyOneRule(ast.NodeTransformer):
    def __init__(self, rule: Rewrite):
        self.did_change = False
        self.pattern = rule.pattern_ast()
        self.output = rule.output_ast()

    def generic_visit(self, node: ast.AST) -> ast.AST:
        node = super().generic_visit(node)
        if self.did_change:
            return node
        if (
            isinstance(self.pattern, ast.BinOp)
            and isinstance(self.pattern.op, ast.Add)
            and isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.Add)
        ):
            replaced = self._try_add_window(node)
            if replaced is not None:
                return replaced
        env = match_pattern(self.pattern, node, {})
        if env is None:
            return node
        replacement = substitute(self.output, env)
        ast.copy_location(replacement, node)
        ast.fix_missing_locations(replacement)
        self.did_change = True
        return replacement

    def _try_add_window(self, node: ast.BinOp) -> Optional[ast.AST]:
        pattern_items = flatten_add(self.pattern)
        target_items = flatten_add(node)
        if len(pattern_items) < 2 or len(target_items) < len(pattern_items):
            return None
        for start in range(0, len(target_items) - len(pattern_items) + 1):
            env: Bindings = {}
            ok = True
            for i, pattern_item in enumerate(pattern_items):
                env2 = match_pattern(pattern_item, target_items[start + i], env)
                if env2 is None:
                    ok = False
                    break
                env = env2
            if not ok:
                continue
            output = substitute(self.output, env)
            output_items = flatten_add(output) if isinstance(output, ast.BinOp) and isinstance(output.op, ast.Add) else [output]
            new_items = target_items[:start] + output_items + target_items[start + len(pattern_items):]
            replacement = rebuild_add(new_items) if len(new_items) > 1 else copy.deepcopy(new_items[0])
            ast.copy_location(replacement, node)
            ast.fix_missing_locations(replacement)
            self.did_change = True
            return replacement
        return None


def rewrite_tree(tree: ast.AST, rules: List[Rewrite], max_iters: int = 10) -> ast.AST:
    for _ in range(max_iters):
        changed = False
        for rule in rules:
            applier = _ApplyOneRule(rule)
            tree = applier.visit(tree)
            changed = changed or applier.did_change
        if not changed:
            break
    ast.fix_missing_locations(tree)
    return tree


def rewrite_source(source: str, rules: List[Rewrite], max_iters: int = 10) -> str:
    return ast.unparse(rewrite_tree(ast.parse(source), rules, max_iters))


# =============================================================================
# Coherency layer (AST tagging: pronouns + transitions)
# =============================================================================

def _is_character_decl(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and bool(node.args)
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "Character"
    )


def _collect_characters(tree: ast.AST) -> set:
    names = set()
    for node in ast.walk(tree):
        if _is_character_decl(node):
            assert isinstance(node.func, ast.Name)
            names.add(node.func.id)
    return names


def _leading_character(call: ast.Call, characters: set) -> Optional[str]:
    for arg in call.args:
        if isinstance(arg, ast.Name) and arg.id in characters:
            return arg.id
    return None


def _ordered_calls(node: ast.AST) -> List[ast.Call]:
    """Top-level kernel calls of a statement, in left-to-right narration order."""
    out: List[ast.Call] = []
    for item in flatten_add(node):
        if isinstance(item, ast.Call):
            out.append(item)
    return out


def _has_kwarg(call: ast.Call, name: str) -> bool:
    return any(kw.arg == name for kw in call.keywords)


def tag_coherence(tree: ast.AST) -> ast.AST:
    """Tag repeated-subject kernels with ``_use_pronoun=True``.

    This is the coherency layer: instead of every kernel deciding when to use a
    pronoun (the gen5 problem), a single AST pass looks at narration order and
    marks continuation sentences. The renderer (``World.say``) honours the tag.
    """
    characters = _collect_characters(tree)
    prev_subject: Optional[str] = None

    for stmt in tree.body:
        if not isinstance(stmt, ast.Expr):
            continue
        for call in _ordered_calls(stmt.value):
            if _is_character_decl(call):
                prev_subject = None  # a fresh introduction; next mention uses the name
                continue
            subject = _leading_character(call, characters)
            if subject is not None:
                if subject == prev_subject and not _has_kwarg(call, "_use_pronoun"):
                    call.keywords.append(ast.keyword(arg="_use_pronoun", value=ast.Constant(True)))
                prev_subject = subject
    ast.fix_missing_locations(tree)
    return tree


# =============================================================================
# Executor
# =============================================================================

class Executor:
    def __init__(self, registry: Registry = REGISTRY):
        self.registry = registry
        self.world = World(registry=registry)

    def execute_tree(self, tree: ast.AST) -> World:
        for stmt in tree.body:
            if isinstance(stmt, ast.Expr):
                self.eval(stmt.value)
        return self.world

    def execute(self, source: str) -> World:
        return self.execute_tree(ast.parse(source))

    def eval(self, node: ast.AST) -> Any:
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left = self.eval(node.left)
            right = self.eval(node.right)
            return Trace("Add", " ".join(t.text for t in (left, right) if isinstance(t, Trace)), [])

        if isinstance(node, ast.Call):
            if _is_character_decl(node):
                return self._character_decl(node)
            if not isinstance(node.func, ast.Name):
                raise TypeError("Only Name(...) calls are supported")
            args = [self.value(arg) for arg in node.args]
            kwargs = {kw.arg: self.value(kw.value) for kw in node.keywords if kw.arg is not None}
            return self.registry.call(self.world, node.func.id, args, kwargs)

        if isinstance(node, ast.Name):
            if node.id in self.registry.kernels:
                return self.registry.call(self.world, node.id, [], {})
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
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return self.eval(node)
        raise TypeError(f"Unsupported value AST: {ast.dump(node)}")

    def _character_decl(self, node: ast.Call) -> Trace:
        assert isinstance(node.func, ast.Name)
        start = len(self.world.effects)
        name = node.func.id
        is_first = len(self.world.entities) == 0

        type_name = "person"
        traits: List[str] = []
        if len(node.args) > 1 and isinstance(node.args[1], ast.Name):
            type_name = node.args[1].id
        for arg in node.args[2:]:
            traits.extend(self._traits(arg))

        entity = self.world.character(name, type_name, traits)

        adjs: List[str] = []
        if type_name in ("boy", "girl", "child"):
            adjs.append("little")
        adjs.extend(t.lower() for t in traits[:2])
        adj = " ".join(adjs)
        article = _article(adj.split()[0] if adj else type_name)
        descriptor = f"{adj} {type_name}".strip()

        if is_first:
            text = f"Once upon a time, there was {article} {descriptor} named {name}."
        else:
            text = f"There was also {article} {descriptor} named {name}."
        trace = Trace("Character", text, self.world.effects[start:])
        self.world.traces.append(trace)
        return trace

    def _traits(self, node: ast.AST) -> List[str]:
        if isinstance(node, ast.Name):
            return [node.id]
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return self._traits(node.left) + self._traits(node.right)
        return [ast.unparse(node)]


# =============================================================================
# Rendering
# =============================================================================

def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def narrate(world: World) -> str:
    parts = [t.text.strip() for t in world.traces if t.text and t.text.strip()]
    story = " ".join(parts)
    story = re.sub(r"\s+", " ", story)
    story = re.sub(r"\s+([.,!?])", r"\1", story)
    story = re.sub(r"\.\.+", ".", story)
    # Capitalize the first letter of every sentence.
    story = re.sub(r"(^|[.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), story)
    return story.strip()


# =============================================================================
# Default rules + entrypoint
# =============================================================================

DEFAULT_RULES: List[Rewrite] = [
    # Enrichment: a strict mother is also caring.
    Rewrite(
        pattern_src="__C(Character, mother, Strict)",
        output_src="__C(Character, mother, Strict + Caring)",
    ),
    # Normalization: a bare Anger after a Warning belongs to the warner.
    Rewrite(
        pattern_src="Warning(__S, __C) + Anger",
        output_src="Warning(__S, __C) + Anger(__S)",
    ),
]


def generate(source: str, rules: Optional[List[Rewrite]] = None, coherence: bool = True) -> str:
    """Full pipeline: declarative rewrites -> coherence tagging -> execute -> narrate."""
    tree = ast.parse(source)
    tree = rewrite_tree(tree, rules if rules is not None else DEFAULT_RULES)
    if coherence:
        tree = tag_coherence(tree)
    world = Executor().execute_tree(tree)
    return narrate(world)


def generate_world(source: str, rules: Optional[List[Rewrite]] = None, coherence: bool = True) -> World:
    """Like :func:`generate` but returns the World (for effects / state inspection)."""
    tree = ast.parse(source)
    tree = rewrite_tree(tree, rules if rules is not None else DEFAULT_RULES)
    if coherence:
        tree = tag_coherence(tree)
    return Executor().execute_tree(tree)


# =============================================================================
# Demo
# =============================================================================

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
Lesson(Lily)
"""

    print("=" * 70)
    print("SOURCE")
    print("=" * 70)
    print(src.strip())

    print("\n" + "=" * 70)
    print("AFTER REWRITES + COHERENCE TAGGING")
    print("=" * 70)
    tagged = tag_coherence(rewrite_tree(ast.parse(src), DEFAULT_RULES))
    print(ast.unparse(tagged).strip())

    print("\n" + "=" * 70)
    print("GENERATED STORY")
    print("=" * 70)
    print(generate(src))

    print("\n" + "=" * 70)
    print("WORLD STATE")
    print("=" * 70)
    print(generate_world(src).state())

    # A second story, built from scratch, no rewrites needed.
    src2 = """
Tom(Character, boy, Kind)
Ben(Character, boy, Shy)
Play(Tom, Ben) + Share(Tom, ball, Ben)
Friendship(Tom, Ben)
Help(Tom, Ben) + Gratitude(Ben, Tom)
HappilyEverAfter
"""
    print("\n" + "=" * 70)
    print("SECOND STORY")
    print("=" * 70)
    print(generate(src2))
