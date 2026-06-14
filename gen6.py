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
from the previous engine - to exercise the engine end to end. The previous
engine (gen5.py and its packs) is kept untouched under ``legacy/``.
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
    "fireman", "policeman", "postman", "snowman", "fisherman", "mailman",
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
        if self.kind == "character":
            return self.name
        return f"the {_camel_words(self.name)}"

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


# Object-status -> adjective for state-aware references ("the lost ball").
_STATUS_ADJECTIVES = {"lost": "lost", "missing": "missing", "broken": "broken"}


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

    # -- object memory (world-model state-aware references) ------------------
    def set_owner(self, obj: Any, owner: Any) -> None:
        """Record that ``owner`` possesses ``obj`` so later mentions can use a
        possessive ("her ball") instead of a bare article ("the ball")."""
        if (isinstance(obj, Entity) and obj.kind != "character"
                and isinstance(owner, Entity) and owner.kind == "character"):
            obj.facts["owner"] = owner.name

    def thing_phrase(self, obj: Any, *, with_status: bool = True) -> str:
        """A state-aware noun phrase for an object, drawn from accumulated world
        state: its owner (-> possessive pronoun) and its status (lost/missing/
        broken -> adjective). Falls back to the plain "the <thing>" rendering."""
        if not (isinstance(obj, Entity) and obj.kind != "character"):
            return _name(obj) if isinstance(obj, Entity) else str(obj)
        noun = _camel_words(obj.name)
        adj = ""
        if with_status:
            status = obj.facts.get("status")
            if status in _STATUS_ADJECTIVES:
                adj = _STATUS_ADJECTIVES[status] + " "
        owner_name = obj.facts.get("owner")
        owner = self.entities.get(owner_name) if owner_name else None
        if owner is not None and owner.kind == "character":
            return f"{owner.pronoun('possessive')} {adj}{noun}"
        return f"the {adj}{noun}"

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

    def __contains__(self, name: str) -> bool:
        return name in self.kernels

    def variants(self, name: str) -> List["Variant"]:
        return self.kernels.get(name, [])

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
        selected = self._select_variant(world, name, args, kwargs)
        if selected is None:
            # Unknown kernel or no signature fits: degrade gracefully.
            body = fallback_text(world, name, args, kwargs)
        else:
            variant, bound_args, bound_kwargs = selected
            try:
                result = variant.fn(world, *bound_args, **bound_kwargs)
                body = result.text if isinstance(result, Trace) else str(result or "")
            except Exception:
                body = fallback_text(world, name, args, kwargs)

        text = (transition + body) if body else ""
        trace = Trace(name, text, world.effects[start:])
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
            return None
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
# Skipping an optional positional param is allowed but disfavoured vs consuming
# an available argument; kept below the actor-fallback penalty.
_OPTIONAL_SKIP_PENALTY = 100
# Dropping an un-nameable kwarg (no **kw to catch it) is a last resort: heavily
# penalised so a variant that actually consumes the kwarg always wins.
_DROP_KWARG_PENALTY = 800


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
    var_positional: Optional[Tuple[str, Any]] = None  # (name, annotation)
    kw_bound: Dict[str, Any] = {}
    plan: List[Tuple[inspect.Parameter, Any, bool]] = []

    for param in params:
        annotation = variant.hints.get(param.name, param.annotation)
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            # `*args` collects any leftover positional arguments (optionally
            # type-filtered, e.g. `*chars: Character`).
            var_positional = (param.name, annotation)
            continue
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
        optional = param.default is not inspect.Parameter.empty
        plan.append((param, annotation, optional))

    # Stray kwargs the signature can't name (and there's no **kw to catch them)
    # are *dropped* with a penalty rather than failing the whole bind. The
    # dataset is full of ad-hoc kwargs (`Gratitude(Tom, for=...)`); dropping one
    # and narrating the verb beats degrading to fallback "Tom gratituded". Any
    # variant that genuinely consumes the kwarg scores lower and still wins.
    drop_penalty = 0
    if unused_kwargs and not var_keyword:
        drop_penalty = _DROP_KWARG_PENALTY * len(unused_kwargs)
        unused_kwargs = {}
    # A fixed positional param supplied by keyword can't be combined with `*args`
    # (Python would fill it positionally too), so reject that rare combination.
    if var_positional is not None and kw_bound:
        return None

    pool = list(enumerate(args))
    # best = (score, assigned, variadic_values)
    best: Optional[Tuple[int, Dict[str, Any], List[Any]]] = None

    def consider(score: int, assigned: Dict[str, Any], available: List[Tuple[int, Any]]) -> None:
        nonlocal best
        if var_positional is None:
            if available:
                return  # leftover positional args with nowhere to go
            variadic: List[Any] = []
        else:
            ann = var_positional[1]
            rem = [v for _, v in available]
            if ann not in (inspect._empty, Any) and not all(_matches(v, ann) for v in rem):
                return  # a leftover arg doesn't fit the typed *args
            score += sum(idx for idx, _ in available)
            variadic = rem
        if best is None or score < best[0]:
            best = (score, dict(assigned), variadic)

    def search(i: int, available: List[Tuple[int, Any]], score: int, assigned: Dict[str, Any]) -> None:
        if i == len(plan):
            consider(score, assigned, available)
            return
        param, annotation, optional = plan[i]
        for k, (orig_index, value) in enumerate(available):
            if _matches(value, annotation):
                assigned[param.name] = value
                search(i + 1, available[:k] + available[k + 1:], score + orig_index, assigned)
                del assigned[param.name]
        if annotation is Actor and world.actor is not None:
            assigned[param.name] = world.actor
            search(i + 1, available, score + _ACTOR_FALLBACK_PENALTY, assigned)
            del assigned[param.name]
        if optional:
            # Leave this parameter to its default and continue.
            search(i + 1, available, score + _OPTIONAL_SKIP_PENALTY, assigned)

    search(0, pool, 0, {})
    if best is None:
        return None

    score, assigned, variadic = best
    score += drop_penalty

    if var_positional is None:
        # No `*args`: pass everything by name to avoid positional/keyword skew.
        bound_kwargs: Dict[str, Any] = {}
        bound_kwargs.update(kw_bound)
        bound_kwargs.update(assigned)
        if var_keyword:
            bound_kwargs.update(unused_kwargs)
        return score, [], bound_kwargs

    # With `*args`, fixed positional params must be passed positionally (in
    # declaration order), then the variadic items, then keyword extras.
    positional: List[Any] = []
    for param, _ann, _opt in plan:
        if param.name in assigned:
            positional.append(assigned[param.name])
        else:
            positional.append(param.default)
    positional.extend(variadic)
    bound_kwargs = dict(unused_kwargs) if var_keyword else {}
    return score, positional, bound_kwargs


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
# Natural-language utilities (ported from gen5.py)
# =============================================================================

class NLGUtils:
    """Verb inflection, articles, pluralization, list joining."""

    IRREGULAR_PAST = {
        'be': 'was', 'have': 'had', 'do': 'did', 'go': 'went', 'get': 'got',
        'make': 'made', 'see': 'saw', 'come': 'came', 'take': 'took', 'know': 'knew',
        'run': 'ran', 'eat': 'ate', 'find': 'found', 'feed': 'fed', 'give': 'gave',
        'say': 'said', 'tell': 'told', 'think': 'thought', 'feel': 'felt',
        'hear': 'heard', 'begin': 'began', 'fall': 'fell', 'fly': 'flew', 'grow': 'grew',
        'hide': 'hid', 'hold': 'held', 'lose': 'lost', 'meet': 'met', 'read': 'read',
        'sing': 'sang', 'sit': 'sat', 'sleep': 'slept', 'swim': 'swam', 'teach': 'taught',
        'throw': 'threw', 'understand': 'understood', 'wake': 'woke', 'win': 'won',
        'write': 'wrote', 'bring': 'brought', 'buy': 'bought', 'catch': 'caught',
        'choose': 'chose', 'draw': 'drew', 'drink': 'drank', 'drive': 'drove',
        'forget': 'forgot', 'freeze': 'froze', 'hurt': 'hurt', 'keep': 'kept',
        'lead': 'led', 'leave': 'left', 'let': 'let', 'put': 'put', 'ride': 'rode',
        'rise': 'rose', 'seek': 'sought', 'send': 'sent', 'shake': 'shook',
        'shine': 'shone', 'show': 'showed', 'shut': 'shut', 'speak': 'spoke',
        'spend': 'spent', 'stand': 'stood', 'steal': 'stole', 'stick': 'stuck',
        'strike': 'struck', 'sweep': 'swept', 'wear': 'wore', 'weep': 'wept',
        'build': 'built', 'bend': 'bent', 'lend': 'lent', 'tear': 'tore',
        'bite': 'bit', 'break': 'broke', 'blow': 'blew', 'dig': 'dug',
        # Common multi-syllable verbs whose final consonant must NOT double
        # (unstressed last syllable): visit -> visited, not "visitted".
        'visit': 'visited', 'open': 'opened', 'offer': 'offered',
        'happen': 'happened', 'enter': 'entered', 'listen': 'listened',
        'answer': 'answered', 'water': 'watered', 'gather': 'gathered',
        'cover': 'covered', 'remember': 'remembered', 'travel': 'traveled',
        'wander': 'wandered', 'whisper': 'whispered', 'order': 'ordered',
    }

    AN_WORDS = {
        'honest', 'hour', 'honor', 'heir',
        'a', 'e', 'i', 'o', 'u', 'x', 'f', 's', 'm', 'l', 'n', 'r',
    }

    IRREGULAR_PLURAL = {
        'child': 'children', 'person': 'people', 'man': 'men', 'woman': 'women',
        'tooth': 'teeth', 'foot': 'feet', 'mouse': 'mice', 'goose': 'geese',
        'ox': 'oxen', 'sheep': 'sheep', 'deer': 'deer', 'fish': 'fish',
    }

    @staticmethod
    def past_tense(verb: str) -> str:
        if not verb:
            return verb
        verb = verb.strip().lower()
        if verb in NLGUtils.IRREGULAR_PAST:
            return NLGUtils.IRREGULAR_PAST[verb]
        if verb.endswith('e'):
            return verb + 'd'
        if verb.endswith('y') and len(verb) > 1 and verb[-2] not in 'aeiou':
            return verb[:-1] + 'ied'
        # Double the final consonant only for short (≈single-syllable, stressed)
        # words: stop->stopped, hug->hugged. Longer words with an unstressed
        # final syllable (visit, offer, …) are handled by IRREGULAR_PAST above.
        if (len(verb) <= 4 and len(verb) >= 3 and verb[-1] not in 'aeiouwxy'
                and verb[-2] in 'aeiou' and verb[-3] not in 'aeiou'):
            return verb + verb[-1] + 'ed'
        return verb + 'ed'

    @staticmethod
    def article(word: str) -> str:
        if not word:
            return "a"
        word = word.strip().lower()
        first = word[0]
        if first == 'u' and (word.startswith('uni') or word.startswith('use') or word.startswith('usu')):
            return "a"
        if word in NLGUtils.AN_WORDS:
            return "an"
        if first in 'aeiou':
            return "an"
        return "a"

    @staticmethod
    def pluralize(word: str) -> str:
        if not word:
            return word
        word = word.strip().lower()
        if word in NLGUtils.IRREGULAR_PLURAL:
            return NLGUtils.IRREGULAR_PLURAL[word]
        if word.endswith(('s', 'x', 'z', 'ch', 'sh')):
            return word + 'es'
        if word.endswith('y') and len(word) > 1 and word[-2] not in 'aeiou':
            return word[:-1] + 'ies'
        if word.endswith('f'):
            return word[:-1] + 'ves'
        if word.endswith('fe'):
            return word[:-2] + 'ves'
        if word.endswith('o') and len(word) > 1 and word[-2] not in 'aeiou':
            return word + 'es'
        return word + 's'

    @staticmethod
    def join_list(items: List[str], conjunction: str = "and") -> str:
        items = [i for i in items if i]
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return f"{items[0]} {conjunction} {items[1]}"
        return ", ".join(items[:-1]) + f", {conjunction} " + items[-1]


def _article(word: str) -> str:
    return NLGUtils.article(word)


def _camel_words(name: str) -> str:
    """`CamelCase`/`snake_case` -> lowercase words: ``NewPlace`` -> ``new place``."""
    phrase = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)
    phrase = phrase.replace("_", " ")
    return phrase.lower()


def to_phrase(value: Any) -> str:
    """Render any runtime value as an embeddable noun/verb phrase (no trailing period)."""
    if isinstance(value, Trace):
        return value.text.rstrip(".!?").strip()
    if isinstance(value, Entity):
        return str(value)
    if isinstance(value, bool):
        return ""
    if isinstance(value, (list, tuple)):
        return NLGUtils.join_list([to_phrase(v) for v in value])
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return str(value)
    return _camel_words(str(value))


def state_to_phrase(value: Any) -> str:
    """Render a 'state' value (for ``X was <state>``)."""
    if isinstance(value, Trace):
        text = value.text.rstrip(".!?").strip()
        if " was " in text:
            return text.split(" was ", 1)[1]
        if " felt " in text:
            return text.split(" felt ", 1)[1]
        return text
    return to_phrase(value)


def action_to_phrase(value: Any) -> str:
    """Render an 'action/process' value as a past-tense verb phrase."""
    if isinstance(value, Trace):
        text = value.text.rstrip(".!?").strip()
        words = text.split()
        if len(words) >= 2 and words[0][:1].isupper():
            return " ".join(words[1:])
        return text
    if isinstance(value, str):
        words = _camel_words(value).split()
        if words:
            return NLGUtils.past_tense(words[0]) + ((" " + " ".join(words[1:])) if len(words) > 1 else "")
        return value
    return to_phrase(value)


# Inverse of NLGUtils.IRREGULAR_PAST (past -> base), for clause reduction.
_PAST_TO_BASE = {past: base for base, past in NLGUtils.IRREGULAR_PAST.items()}
# Common base verbs that end in silent 'e' (so "danced" -> "dance", not "danc").
_SILENT_E_VERBS = frozenset({
    "dance", "love", "move", "like", "make", "smile", "share", "care", "save",
    "place", "hope", "ride", "write", "give", "live", "close", "use", "race",
    "wave", "bake", "name", "taste", "dare", "chase", "hide", "invite", "decide",
    "wave", "smile", "wave", "bounce", "dive", "tie", "bite", "hike", "tease",
    "wipe", "shine", "snore", "rake", "stare", "wave", "explore", "imagine",
    "behave", "arrive", "believe", "escape", "celebrate", "create", "prepare",
})


def _present_base(past: str) -> str:
    """Best-effort past-tense -> base form (for infinitives/gerunds)."""
    w = past.lower()
    if w in _PAST_TO_BASE:
        return _PAST_TO_BASE[w]
    if w.endswith("ied"):
        return w[:-3] + "y"
    if w.endswith("ed"):
        stem = w[:-2]
        if len(stem) >= 2 and stem[-1] == stem[-2] and stem[-1] not in "aeiou":
            return stem[:-1]            # stopped -> stop
        if (stem + "e") in _SILENT_E_VERBS:
            return stem + "e"           # danced -> dance
        return stem                     # climbed -> climb
    return w


def _gerund(base: str) -> str:
    """Base verb -> -ing form (run -> running, dance -> dancing)."""
    b = base.lower()
    if b.endswith("ie"):
        return b[:-2] + "ying"          # tie -> tying
    if len(b) > 2 and b.endswith("e") and not b.endswith(("ee", "oe", "ye")):
        return b[:-1] + "ing"           # dance -> dancing (but be -> being)
    if (len(b) == 3 and b[-1] not in "aeiouwxy"
            and b[-2] in "aeiou" and b[-3] not in "aeiou"):
        return b + b[-1] + "ing"        # run -> running
    return b + "ing"


def _strip_subject(text: str) -> str:
    """Drop a leading capitalized proper-name/pronoun subject from a clause,
    leaving the predicate ("Mom climbed the tree" -> "climbed the tree")."""
    words = text.rstrip(".!?").strip().split()
    if len(words) >= 2 and words[0][:1].isupper():
        return " ".join(words[1:])
    return text.rstrip(".!?").strip()


# Copulas / auxiliaries: present as a past form but never the *action* of a
# clause, so they must not drive infinitive/gerund reduction ("there was X" must
# not become "to be X" / "being X").
_COPULAS = frozenset({"was", "were", "is", "are", "been", "being", "be",
                      "had", "has", "have", "did", "does", "do"})


def _is_past_verb(word: str) -> bool:
    """Whether a word is a past-tense *action* verb we can confidently de-tense."""
    w = word.lower()
    if w in _COPULAS:
        return False
    return w in _PAST_TO_BASE or (len(w) > 3 and w.endswith("ed"))


def base_phrase(value: Any) -> str:
    """An action value as a *base* verb phrase ("climb the tree"), no leading
    "to". Returns "" for a Trace whose predicate isn't a clean action verb."""
    if isinstance(value, Trace) and value.kernel not in ("Concept", ""):
        words = _strip_subject(value.text).split()
        if words and _is_past_verb(words[0]):
            words[0] = _present_base(words[0])
            return " ".join(words)
        return ""
    return to_phrase(value)


def infinitive_phrase(value: Any) -> str:
    """Render an action value as an infinitive ("to climb the tree") for a
    desire/goal slot. Returns "" for an action Trace that doesn't cleanly reduce
    (e.g. "up into the sky it flew"); a plain object becomes a noun phrase."""
    if isinstance(value, Trace) and value.kernel not in ("Concept", ""):
        b = base_phrase(value)
        return ("to " + b) if b else ""
    return to_phrase(value)


def gerund_phrase(value: Any) -> str:
    """Render an action value as a gerund ("climbing the tree") for slots like
    "a lesson about <X>". Returns "" for a non-reducible action Trace; a plain
    concept becomes a noun phrase."""
    if isinstance(value, Trace) and value.kernel not in ("Concept", ""):
        words = _strip_subject(value.text).split()
        if words and _is_past_verb(words[0]):
            words[0] = _gerund(_present_base(words[0]))
            return " ".join(words)
        return ""
    return to_phrase(value)


def clause_inline(value: Any) -> str:
    """For "X realized that <clause>" / "X learned that <clause>" slots: keep the
    embedded clause's own subject but lower-case its first word so it reads as a
    subordinate clause ("...that help was on the way")."""
    if isinstance(value, Trace) and value.kernel not in ("Concept", ""):
        text = value.text.rstrip(".!?").strip()
        if text:
            return text[0].lower() + text[1:]
    return to_phrase(value)


def event_to_phrase(value: Any) -> str:
    """Render an 'event/catalyst' value (for ``One day, <event>``)."""
    if isinstance(value, Trace):
        text = value.text.rstrip(".!?").strip()
        if text[:1].isupper():
            text = text[0].lower() + text[1:]
        return text
    if isinstance(value, str):
        return f"something {_camel_words(value)} happened"
    return to_phrase(value)


# =============================================================================
# Meta-kernel phase rendering (shared by the structural kernels in the packs)
# =============================================================================
#
# Phase values arrive already evaluated: a *concept* (string / list), ``None``,
# or a narration ``Trace`` that already carries its own grammatical subject
# (e.g. ``Chase(ball)`` -> "Lily chased the ball."). The old approach tried to
# splice a fragment out of a rendered child sentence by string surgery (split on
# " was "), which mangled multi-sentence ``+`` compositions and produced double
# subjects ("Leopard was Leopard really wanted..."). The helpers below instead
# emit child Traces *as their own sentences* and only template bare concepts.

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def split_sentences(text: str) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []
    return [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip()]


def _lower_first(s: str) -> str:
    return s[0].lower() + s[1:] if s else s


# Leading words that should be lower-cased when a clause is spliced after a lead
# like "One day, " / "In the end, "; proper names keep their capital.
_LOWERABLE_LEAD = {
    "he", "she", "they", "it", "there", "the", "a", "an", "everyone",
    "everything", "one", "that", "this", "his", "her", "their", "its",
    "suddenly", "soon",
}


def _lead_join(lead: str, sentence: str) -> str:
    """Prepend ``lead`` to ``sentence``; lower-case the first word only if it is a
    common function word (so "Bobo was happy" stays capitalised but "They lived
    happily" becomes lower-case after "In the end, ")."""
    if not sentence:
        return lead.rstrip()
    head = sentence.split(" ", 1)[0]
    if head.lower().strip(".,!?'") in _LOWERABLE_LEAD:
        sentence = head[0].lower() + sentence[1:]
    return lead + sentence


def child_sentences(value: Any) -> Optional[List[str]]:
    """A narration Trace's sentences (each already subjected), or ``None`` for a
    concept/None that the caller must wrap in a template."""
    if isinstance(value, Trace) and value.kernel != "Concept" and value.text.strip():
        return split_sentences(value.text)
    return None


def render_state(subject: str, value: Any) -> List[str]:
    cs = child_sentences(value)
    if cs is not None:
        return cs
    phrase = state_to_phrase(value)
    return [f"{subject} was {phrase}."] if phrase else []


def render_action(subject: str, value: Any) -> List[str]:
    cs = child_sentences(value)
    if cs is not None:
        return cs
    phrase = action_to_phrase(value)
    return [f"{subject} {phrase}."] if phrase and subject else ([phrase.capitalize() + "."] if phrase else [])


def render_event(value: Any, *, lead: str = "One day, ") -> List[str]:
    cs = child_sentences(value)
    if cs is not None:
        return [_lead_join(lead, cs[0])] + cs[1:]
    phrase = event_to_phrase(value)
    return [f"{lead}{phrase}."] if phrase else []


def render_outcome(subject: str, value: Any, *, lead: str = "In the end, ", verb: str = "felt") -> List[str]:
    cs = child_sentences(value)
    if cs is not None:
        return [_lead_join(lead, cs[0])] + cs[1:]
    phrase = state_to_phrase(value)
    if not phrase:
        return []
    return [f"{lead}{subject} {verb} {phrase}."] if subject else [f"{lead}there was {phrase}."]


def render_clause(value: Any, template: str) -> List[str]:
    """Emit a child Trace as-is, else fill ``template`` with the concept phrase
    (``template`` must contain one ``{}``, e.g. ``"But there was {}."``)."""
    cs = child_sentences(value)
    if cs is not None:
        return cs
    phrase = to_phrase(value)
    return [template.format(phrase)] if phrase else []


def coherent(world: World, hero: Optional[Entity], sentences: List[str]) -> str:
    """Join sentences, collapsing a repeated leading hero-name into a pronoun.

    This is a *world-model* coherence pass: it knows the hero entity and its
    pronoun, so consecutive sentences about the hero read "Lily ran. She fell."
    instead of "Lily ran. Lily fell." The first hero sentence keeps the name
    unless the AST coherence layer already flagged this kernel as a continuation
    of the same subject (``world.use_pronoun``).
    """
    sentences = [s.strip() for s in sentences if s and s.strip()]
    if not (isinstance(hero, Entity) and hero.kind == "character"):
        return " ".join(sentences)
    name = hero.name
    pron = hero.pronoun("subject")
    out: List[str] = []
    prev_hero = bool(world.use_pronoun)
    for s in sentences:
        is_hero = s.startswith(name + " ") or s.startswith(name + "'")
        if is_hero and prev_hero:
            s = pron.capitalize() + s[len(name):]
        out.append(s)
        prev_hero = is_hero
    return " ".join(out)


# Phase keys that signal a "simple" kernel is actually being used as a
# multi-phase meta structure (e.g. ``Guidance(Lily, state=..., process=...)``).
_META_KEYS = (
    "state", "catalyst", "trigger", "goal", "want", "process", "action",
    "actions", "journey", "obstacle", "conflict", "insight", "discovery",
    "lesson", "realization", "consequence", "outcome", "transformation",
    "resolution", "mistake",
)


def is_meta_call(kw: Dict[str, Any]) -> bool:
    return any(k in kw for k in _META_KEYS)


def _first(kw: Dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if k in kw and kw[k] is not None:
            return kw[k]
    return None


def meta_story(world: World, hero: Optional[Entity], kw: Dict[str, Any],
               *, fallback: Optional[str] = None) -> Optional[str]:
    """Render a generic multi-phase narrative from keyword phases.

    Shared by structural kernels and by the gen6k03 factories (so any simple
    kernel called with phase kwargs still produces a full story instead of
    collapsing to one line). Returns ``None`` (so the caller can fall back to
    its simple rendering) when no phase produced text.
    """
    name = hero.name if isinstance(hero, Entity) and hero.kind == "character" else None
    if isinstance(hero, Entity):
        world.actor = hero
    sents: List[str] = []

    state = _first(kw, "state", "mood")
    if state is not None and name:
        sents += render_state(name, state)

    goal = _first(kw, "goal", "want", "desire")
    if goal is not None:
        cs = child_sentences(goal)
        if cs is not None:
            sents += cs
        elif name:
            sents.append(f"{name} wanted {to_phrase(goal)}.")

    catalyst = _first(kw, "catalyst", "trigger")
    if catalyst is not None:
        sents += render_event(catalyst)

    mistake = _first(kw, "mistake")
    if mistake is not None and name:
        sents += render_action(name, mistake)

    obstacle = _first(kw, "obstacle", "conflict")
    if obstacle is not None:
        sents += render_clause(obstacle, "But there was {}.")

    process = _first(kw, "process", "action", "actions", "journey", "method")
    if process is not None and name:
        sents += render_action(name, process)

    consequence = _first(kw, "consequence")
    if consequence is not None:
        sents += render_clause(consequence, "Because of that, {}.")

    insight = _first(kw, "insight", "discovery", "lesson", "realization")
    if insight is not None:
        if isinstance(hero, Entity):
            hero.add_meme("Wisdom", 1.0)
        cs = child_sentences(insight)
        if cs is not None:
            sents += cs
        elif name:
            sents.append(f"{name} learned {to_phrase(insight)}.")

    outcome = _first(kw, "outcome", "transformation", "resolution", "result")
    if outcome is not None:
        if isinstance(hero, Entity):
            hero.add_meme("Joy", 1.0)
        sents += render_outcome(name or "", outcome)

    if not sents:
        return fallback
    return coherent(world, hero, sents)


# =============================================================================
# Fallback rendering (graceful degradation for unknown / unmatched kernels)
# =============================================================================

_NOUNISH_SUFFIXES = ("ness", "ment", "ity", "ship", "tion", "sion", "ance",
                     "ence", "hood", "dom", "th", "ude")

# Curated abstract-noun / emotion concept names that are *never* the intended
# verb in this dataset, so when an unknown kernel by one of these names hits the
# fallback it should read "X felt <noun>" instead of being past-tensed into a
# bogus verb ("joyed", "griefed", "angered-as-state"). Words that double as
# common verbs (help, play, care, hug, share, ...) are deliberately excluded.
_NOUNISH_WORDS = frozenset({
    "joy", "sadness", "anger", "fear", "pride", "grief", "guilt", "relief",
    "courage", "hope", "envy", "jealousy", "loneliness", "boredom", "calm",
    "comfort", "peace", "wonder", "awe", "shame", "sorrow", "worry", "dread",
    "delight", "glee", "bliss", "contentment", "gratitude", "compassion",
    "kindness", "patience", "honesty", "loyalty", "curiosity", "excitement",
    "happiness", "sympathy", "empathy", "confidence", "determination",
    "satisfaction", "disappointment", "frustration", "embarrassment",
})


def _looks_nounish(phrase: str) -> bool:
    """Heuristic: a multi-word, abstract-noun-suffixed, or known abstract concept
    is a thing/state, not a verb (so it should not be past-tensed in fallback)."""
    words = phrase.split()
    if len(words) > 1:
        return True
    return phrase in _NOUNISH_WORDS or phrase.endswith(_NOUNISH_SUFFIXES)


def fallback_text(world: World, name: str, args: List[Any], kwargs: Dict[str, Any]) -> str:
    """Produce readable text for a kernel with no matching variant.

    Mirrors gen5's ``_fallback_kernel`` so unknown kernels degrade to a sentence
    instead of aborting the whole story. Nested kernel results (Traces in args or
    kwargs) are folded in so structural kernels still narrate their children.
    """
    phrase = _camel_words(name)
    chars = [a for a in args if isinstance(a, Entity) and a.kind == "character"]
    objs = [a for a in args if isinstance(a, Entity) and a.kind != "character"]
    concepts = [a for a in args if isinstance(a, str)]
    sub_traces = [a for a in list(args) + list(kwargs.values()) if isinstance(a, Trace) and a.text.strip()]

    sub_text = " ".join(t.text.strip() for t in sub_traces)

    if chars:
        actor = chars[0]
        world.actor = actor
        words = phrase.split()
        targets = [str(c) for c in chars[1:]] + [str(o) for o in objs] + list(concepts)
        tail = (" " + NLGUtils.join_list(targets)) if targets else ""
        if _looks_nounish(phrase) and not tail:
            # Abstract noun kernels (Warmth, FamilySupport, Confidence) read as a
            # feeling, not a verb -- avoids "warmthed" / "familied".
            body = f"{world.say(actor)} felt {phrase}."
        else:
            verb = NLGUtils.past_tense(words[0]) if words else phrase
            rest = " ".join(words[1:])
            body = f"{world.say(actor)} {verb}{(' ' + rest) if rest else ''}{tail}.".replace("  ", " ")
        return (body + (" " + sub_text if sub_text else "")).strip()

    if sub_text:
        return sub_text

    if objs or concepts:
        targets = [str(o) for o in objs] + [c.lower() for c in concepts]
        return f"There was {NLGUtils.join_list(targets)}."

    if phrase.endswith("ing"):
        return f"{phrase.capitalize()}."
    return f"Something {phrase} happened."


def _combine(left: Any, right: Any) -> Trace:
    """Combine two evaluated operands of a ``+`` composition into one Trace.

    If either side is a narration Trace, the result sequences sentences;
    otherwise it is a conceptual composition joined with "and" (e.g. entity
    names or traits).
    """
    def _is_narration(v: Any) -> bool:
        return isinstance(v, Trace) and v.kernel != "Concept" and bool(v.text.strip())

    if _is_narration(left) or _is_narration(right):
        parts: List[str] = []
        for v in (left, right):
            if _is_narration(v):
                parts.append(v.text.strip())
            else:
                # A bare concept (or concept-composition Trace) inside a
                # narrative sequence becomes its own sentence rather than a naked
                # phrase jammed between sentences ("...the flowers Frog realized").
                p = to_phrase(v)
                if p:
                    # Plural agreement: "There were dolls." not "There was dolls."
                    head = p.split()[0].lower()
                    plural = (head not in ("the", "a", "an", "his", "her", "their", "its", "some")
                              and p.endswith("s") and not p.endswith(("ss", "us", "is")))
                    parts.append(f"There {'were' if plural else 'was'} {p}.")
        return Trace("Compose", " ".join(parts), [])
    # Two concepts compose into a noun phrase, not narration. Tag it "Concept"
    # so `child_sentences` won't mistake it for a pre-subjected sentence.
    joined = NLGUtils.join_list([to_phrase(left), to_phrase(right)])
    return Trace("Concept", joined, [])


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
    if isinstance(receiver, Entity) and receiver.kind == "character":
        receiver.Joy += 0.2  # being thanked feels good


@REGISTRY.addition("Friendship", Character)
def _add_friendship(world: World, owner: Entity, other: Entity) -> None:
    owner.add_meme("Friendship", 1.0)
    owner.add_link("Friendship", other)
    owner.Love += 0.5
    # Friendship is mutual: record the reverse link/feeling so relationship-aware
    # kernels (HappyEnd, Reunion, Farewell) read it from either character.
    if isinstance(other, Entity) and other.kind == "character":
        other.add_meme("Friendship", 1.0)
        other.add_link("Friendship", owner.name)
        other.Love += 0.5


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


@REGISTRY.kernel("Surprise")
def SurpriseObject(ctx: World, char: Actor, thing: Physical) -> str:
    char.Surprise += 1
    ctx.actor = char
    ctx.current_object = thing
    return f"{ctx.say(char)} was surprised by {thing}."


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
    ctx.set_owner(obj, owner)  # they owned it before losing it -> "her ball"
    owner.Loss += obj
    ctx.actor = owner
    ctx.current_object = obj
    return f"{ctx.say(owner)} lost {ctx.thing_phrase(obj, with_status=False)} and felt sad."


@REGISTRY.kernel("Search")
def Search(ctx: World, actor: Actor, obj: Physical) -> str:
    actor.Search += obj
    ctx.actor = actor
    # Reads accumulated state: a previously-lost object reads "her lost ball".
    return f"{ctx.say(actor)} looked everywhere for {ctx.thing_phrase(obj)}."


@REGISTRY.kernel("Find")
def Find(ctx: World, finder: Actor, obj: Physical) -> str:
    # Reclaiming a previously-lost item reads "found her ball again"; a fresh
    # discovery stays "found the treasure" (render before taking ownership).
    again = " again" if obj.facts.get("status") in ("lost", "missing") else ""
    phrase = ctx.thing_phrase(obj, with_status=False)
    finder.Find += obj
    ctx.set_owner(obj, finder)
    ctx.actor = finder
    ctx.current_object = obj
    return f"{ctx.say(finder)} finally found {phrase}{again}."


@REGISTRY.kernel("Find")
def FindAt(ctx: World, finder: Actor, obj: Physical, location: Physical) -> str:
    again = " again" if obj.facts.get("status") in ("lost", "missing") else ""
    phrase = ctx.thing_phrase(obj, with_status=False)
    finder.Find += obj
    obj.location = location
    ctx.set_owner(obj, finder)
    ctx.actor = finder
    ctx.current_object = obj
    return f"{ctx.say(finder)} found {phrase}{again} near {location}."


@REGISTRY.kernel("Return")
def Return(ctx: World, giver: Actor, obj: Physical, recipient: Character) -> str:
    phrase = ctx.thing_phrase(obj, with_status=False)  # render before re-owning
    obj.add_meme("Return", 1.0)
    giver.Return += recipient
    ctx.set_owner(obj, recipient)
    ctx.actor = recipient
    ctx.current_object = obj
    return f"{ctx.say(giver)} returned {phrase} to {recipient}."


@REGISTRY.kernel("See")
def See(ctx: World, char: Actor, obj: Physical) -> str:
    ctx.actor = char
    ctx.current_object = obj
    return f"{ctx.say(char)} saw {ctx.thing_phrase(obj)}."


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
    phrase = ctx.thing_phrase(obj, with_status=False)  # render before re-owning
    giver.Give += obj
    receiver.Joy += 0.4
    ctx.set_owner(obj, receiver)
    ctx.actor = giver
    ctx.current_object = obj
    return f"{ctx.say(giver)} gave {phrase} to {receiver}."


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
def PlayWith(ctx: World, char: Actor, other: Character) -> str:
    char.Joy += 0.5
    ctx.actor = char
    return f"{ctx.say(char)} played happily with {other}."


@REGISTRY.kernel("Play")
def PlayObject(ctx: World, char: Actor, obj: Physical = None) -> str:
    char.Joy += 0.4
    ctx.actor = char
    if obj is not None:
        ctx.current_object = obj
        return f"{ctx.say(char)} played with {obj}."
    return f"{ctx.say(char)} played happily."


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
    # World-model-aware ending: reflect the emotional arc accumulated in the
    # world state instead of always emitting the same sentence.
    chars = [e for e in ctx.entities.values() if e.kind == "character"]
    joy = sum(e.meme("Joy") + e.meme("Love") for e in chars)
    sad = sum(e.meme("Sadness") + e.meme("Fear") for e in chars)
    # A character who built up Brave while carrying Fear overcame something.
    overcame = any(e.meme("Brave") > 0 and e.meme("Fear") > 0 for e in chars)
    reunited = any(e.meme("Reunion") > 0 or e.meme("Return") > 0 for e in chars)
    befriended = any(e.meme("Friendship") > 0 for e in chars)
    if chars and sad > joy + 0.5:
        return "And though it had been hard, everything turned out all right in the end."
    if reunited and befriended:
        return "And, together again, they were the best of friends from that day on."
    if befriended:
        return "And from that day on, they were the best of friends."
    if overcame:
        return "And from that day on, they were braver than ever before."
    return "And from that day on, everyone lived happily."


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
        # Only top-level statements emit narration; nested calls (inside args /
        # kwargs / compositions) are executed for their effects and returned to
        # the parent kernel, matching gen5's emission model.
        for stmt in tree.body:
            if isinstance(stmt, ast.Expr):
                result = self.eval(stmt.value)
                if isinstance(result, Trace) and result.text and result.text.strip():
                    self.world.traces.append(result)
        return self.world

    def execute(self, source: str) -> World:
        return self.execute_tree(ast.parse(source))

    def eval(self, node: ast.AST) -> Any:
        if isinstance(node, ast.BinOp):
            if isinstance(node.op, ast.Add):
                left = self.eval(node.left)
                right = self.eval(node.right)
                return _combine(left, right)
            if isinstance(node.op, ast.Div):
                # Attention dilution: `X / n`. A strong dilution suppresses X.
                left = self.eval(node.left)
                right = self.value(node.right)
                if isinstance(right, (int, float)) and right >= 3:
                    return Trace("Dilute", "", [])
                return left
            # Other operators: best-effort, evaluate the left operand.
            return self.eval(node.left)

        if isinstance(node, ast.Call):
            if _is_character_decl(node):
                return self._character_decl(node)
            if not isinstance(node.func, ast.Name):
                return Trace("?", "", [])
            # Pre-bind focus: if the first positional arg names a character, make
            # it the actor before evaluating the rest, so nested sub-expressions
            # (in args/kwargs) resolve to the right protagonist (gen5 meta-pattern).
            if node.args and isinstance(node.args[0], ast.Name):
                ent = self.world.entities.get(node.args[0].id)
                if ent is not None and ent.kind == "character":
                    self.world.actor = ent
            args = [self.value(arg) for arg in node.args]
            kwargs = {kw.arg: self.value(kw.value) for kw in node.keywords if kw.arg is not None}
            return self.registry.call(self.world, node.func.id, args, kwargs)

        if isinstance(node, ast.Name):
            if node.id in self.registry.kernels:
                return self.registry.call(self.world, node.id, [], {})
            return self.value(node)

        return self.value(node)

    def value(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Name):
            if node.id in self.world.entities:
                return self.world.entities[node.id]
            # A bare kernel name used as an argument/kwarg should execute, so
            # `catalyst=Threat` or `state=Routine` narrate rather than degrade to
            # the literal concept string "threat" / "routine".
            if node.id in self.registry.kernels:
                return self.eval(node)
            if node.id and node.id[0].isupper():
                return node.id
            return self.world.physical(node.id)
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Call):
            return self.eval(node)
        if isinstance(node, ast.BinOp):
            return self.eval(node)
        if isinstance(node, ast.List):
            return [self.value(el) for el in node.elts]
        if isinstance(node, ast.Tuple):
            return [self.value(el) for el in node.elts]
        if isinstance(node, ast.Subscript):
            container = self.value(node.value)
            if isinstance(container, list):
                idx = self.value(node.slice)
                if isinstance(idx, int) and -len(container) <= idx < len(container):
                    return container[idx]
            return container
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            inner = self.value(node.operand)
            return -inner if isinstance(inner, (int, float)) else inner
        # Unknown expression: render its source as a concept string.
        try:
            return _camel_words(ast.unparse(node))
        except Exception:
            return ""

    def _character_decl(self, node: ast.Call) -> Trace:
        assert isinstance(node.func, ast.Name)
        start = len(self.world.effects)
        name = node.func.id
        is_first = not any(e.kind == "character" for e in self.world.entities.values())

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
        descriptor = f"{adj} {type_name}".strip()
        article = _article(descriptor.split()[0] if descriptor else "person")

        if is_first:
            text = f"Once upon a time, there was {article} {descriptor} named {name}."
        else:
            text = f"There was also {article} {descriptor} named {name}."
        return Trace("Character", text, self.world.effects[start:])

    def _traits(self, node: ast.AST) -> List[str]:
        if isinstance(node, ast.Name):
            return [node.id]
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return self._traits(node.left) + self._traits(node.right)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            # e.g. Hat(leather) -> "leather hat"
            inner = [self._concept(a) for a in node.args]
            inner = [i for i in inner if i]
            base = _camel_words(node.func.id)
            return [f"{' '.join(inner)} {base}".strip()] if inner else [base]
        return [_camel_words(ast.unparse(node))]

    def _concept(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return _camel_words(node.id) if node.id[:1].isupper() else node.id
        if isinstance(node, ast.Constant):
            return str(node.value)
        return _camel_words(ast.unparse(node))


# =============================================================================
# Rendering
# =============================================================================

def narrate(world: World) -> str:
    parts = [t.text.strip() for t in world.traces if t.text and t.text.strip()]
    story = " ".join(parts)
    story = re.sub(r"\s+", " ", story)
    story = re.sub(r"\s+([.,!?])", r"\1", story)
    story = re.sub(r"\.\.+", ".", story)
    # Capitalize the first letter of every sentence.
    story = re.sub(r"(^|[.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), story)
    story = _dedupe_adjacent_sentences(story)
    return story.strip()


def _dedupe_adjacent_sentences(story: str) -> str:
    """Drop immediately-repeated sentences (e.g. two kernels that both render
    "There was lots of fun.") which read as accidental stutter."""
    pieces = re.split(r"(?<=[.!?])\s+", story)
    out: List[str] = []
    for p in pieces:
        if out and p.strip().lower() == out[-1].strip().lower():
            continue
        out.append(p)
    return " ".join(out)


# =============================================================================
# Default rules + entrypoint
# =============================================================================

DEFAULT_RULES: List[Rewrite] = [
    # Enrichment: a strict mother is also caring.
    Rewrite(
        pattern_src="__C(Character, mother, Strict)",
        output_src="__C(Character, mother, Strict + Caring)",
    ),
    # Enrichment: a witch reads as mysterious unless already qualified.
    Rewrite(
        pattern_src="__C(Character, witch)",
        output_src="__C(Character, witch, Mysterious)",
    ),
    # Normalization: a bare Anger after a Warning belongs to the warner.
    Rewrite(
        pattern_src="Warning(__S, __C) + Anger",
        output_src="Warning(__S, __C) + Anger(__S)",
    ),
    # Normalization: a bare Sadness after a Loss belongs to the one who lost it
    # (Loss already narrates the sadness, but an explicit owner keeps coherence
    # if the bare emotion is rewritten onto the right subject).
    Rewrite(
        pattern_src="Loss(__C, __O) + Sadness",
        output_src="Loss(__C, __O) + Sadness(__C)",
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
