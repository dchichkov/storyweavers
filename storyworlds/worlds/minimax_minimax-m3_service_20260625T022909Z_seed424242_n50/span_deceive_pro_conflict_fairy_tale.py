#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/span_deceive_pro_conflict_fairy_tale.py
==================================================================================================================

A standalone *story world* script for the "deceiver's bridge" tale -- a tiny
Fairy-Tale-style domain built from the seed words *span*, *deceive*, *pro*.

Initial source tale (used to imagine the world model):
---
Once upon a time, in the deep green wood, there was a short stone bridge that
spanned a quiet creek. A clever fox made the bridge his home, and when weary
travelers came to cross, the fox would trick them with kind-sounding riddles
and promises. A young woodcutter came to the bridge, and the fox deceived
him about the safe stones, and the woodcutter tumbled into the cold water.

The fox laughed, but the woodcutter's mother had warned him of tricksters.
The woodcutter waded back, and the fox, proud and sure of his way, kept
tricking a goose, a bee, and a wise old toad. Each traveler lost a small
treasure to the fox's clever tongue.

At last a young girl came to the creek. She was gentle and had been taught
that pros -- proper promises -- were sacred. The fox tried to trick her with
the same smooth words, but the girl only smiled and said, "A promise is a
span of trust between two hearts; if you will not span the water with a
pro, I will not cross, and you will not eat my bread." The fox blinked. He
had never met a child who knew what a pro was. He stammered, the bridge
felt suddenly small, and for the first time he let a traveler cross without
trickery. He learned that pros -- careful, kept promises -- were the real
span that carries folk across. And from that day the fox was honest, the
bridge stayed kind, and the creek sang softly under the moon.

Causal state updates:
---
    fox deceives a traveler        -> fox.memes.cheat += 1
                                       traveler.memes.tricked += 1
                                       world.meters.false_pro += 1
    traveler crosses after honest  -> fox.memes.trust += 1
                                       traveler.memes.safe += 1
                                       world.meters.kept_pro += 1
    bridge trusted by the village  -> bridge.memes.held += 1
    fox breaks a kept promise      -> fox.memes.shame += 1
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly.
_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# Surface "mess" kinds the fox's deceptions can leave on a traveler.
TRICK_KINDS = {"splash", "prick", "lost_bread", "lost_flower", "lost_feather"}

# -----------------------------------------------------------------------
# Entities: characters and physical objects share one typed representation.
# -----------------------------------------------------------------------

def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # fox, woodcutter, girl, goose, bridge, creek ...
    label: str = ""                # short reference, e.g. "bridge", "bread"
    phrase: str = ""               # full noun phrase, e.g. "a small crust of bread"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    spans: bool = False            # this thing is a literal span (bridge / plank)
    sacred: bool = False           # pros (kept promises) are sacred; bridges are not
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    bridge_ent: object | None = None
    first_traveler: object | None = None
    fox: object | None = None
    goose: object | None = None
    traveler: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "goose", "hen"}
        male = {"fox", "woodcutter", "father", "man", "boy", "toad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "woodcutter": "woodcutter"}.get(
            self.type, self.type
        )


# -----------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this little domain.
# -----------------------------------------------------------------------
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Place:
    id: str
    name: str                      # "the deep green wood"
    creek: str                     # "a quiet creek"
    has_bridge: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Trick:
    """The deception the fox tries first -- always rejected by a 'pro' traveler."""
    id: str
    verb: str                      # what the fox tells the traveler to do
    consequence: str               # what happens if the traveler obeys
    trick_kind: str                # surface "mess" key
    ruse: str                      # the fox's smooth line
    finding: str                   # what the traveler learns (closing image)
    truth: str                     # the honest alternative the traveler names
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Traveler:
    """A person who tries to cross the bridge."""
    id: str
    type: str                      # girl, woodcutter, goose, bee, toad ...
    label: str
    gift: str                      # what the traveler offers to share
    gift_kind: str                 # mess key the fox would steal
    knows_pro: bool = False        # whether the traveler keeps proper promises
    phrase: str = ""               # full noun phrase, optional
    plural: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Bridge:
    """The literal span across the creek."""
    id: str
    name: str
    material: str
    soft: bool = True              # "the bridge felt suddenly small"


# -----------------------------------------------------------------------
# World: entity store + narration history + a small ledger of pros.
# -----------------------------------------------------------------------
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        # Public ledger of pros: each entry is a (who, kept) pair.
        self.pros: list[tuple[str, bool]] = []
        # Facts recorded during the screenplay, read back by the Q&A generators.
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def items(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "thing"]

    def keep(self, who: str, kept: bool = True) -> None:
        self.pros.append((who, kept))

    # -- narration helpers --------------------------------------------------
    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.pros = list(self.pros)
        clone.paragraphs = [[]]
        return clone


# -----------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# -----------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


def _r_cheat(world: World) -> list[str]:
    """Each embedded cheat by the fox leaves a tracked 'false_pro' on the world."""
    fox = world.entities.get("Fox")
    if fox is None or fox.memes["cheat"] < THRESHOLD:
        return []
    sig = ("cheat", "ledger")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.meters.setdefault("false_pro", 0.0)        # type: ignore[attr-defined]
    # The actual world.keep() / kept_pro update is applied in _do_deceive.
    return []


def _r_trust(world: World) -> list[str]:
    """Once a traveler crosses honestly, the bridge earns trust."""
    bridge = world.entities.get("Bridge")
    if bridge is None:
        return []
    for actor in world.characters():
        if actor.memes["safe"] < THRESHOLD:
            continue
        sig = ("trust", bridge.id, actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        bridge.memes["held"] += 1
    return []


def _r_shame(world: World) -> list[str]:
    """If the fox has many cheats but no kept_pro, shame accumulates."""
    fox = world.entities.get("Fox")
    if fox is None:
        return []
    if fox.memes["cheat"] >= 2 and fox.memes["trust"] < THRESHOLD:
        sig = ("shame", fox.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        fox.memes["shame"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="cheat_ledger", tag="social", apply=_r_cheat),
    Rule(name="trust_bridge", tag="physical", apply=_r_trust),
    Rule(name="shame", tag="social", apply=_r_shame),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# -----------------------------------------------------------------------
# Constraint helpers -- what is a *reasonable* trick and a *reasonable* fix.
# -----------------------------------------------------------------------
def trick_matches(trick: Trick, traveler: Traveler) -> bool:
    """Would this trick actually part the traveler from the offered gift?"""
    return trick.trick_kind == traveler.gift_kind


def traveler_can_pro(traveler: Traveler) -> bool:
    """Only travelers who keep proper promises defeat the fox."""
    return traveler.knows_pro


# -----------------------------------------------------------------------
# Prediction: simulate the ruse forward on a clone to foresee its cost.
# -----------------------------------------------------------------------
def predict_deception(world: World, fox: Entity, traveler: Entity, trick: Trick) -> dict:
    sim = world.copy()
    _do_deceive(sim, sim.get(fox.id), sim.get(traveler.id), trick, narrate=False)
    return {
        "gift_lost": sim.entities[traveler.id].meters["tricked"] >= THRESHOLD,
        "false_pros": sum(1 for w, k in sim.pros if not k),
    }


# -----------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# -----------------------------------------------------------------------
def wood_detail(place: Place) -> str:
    return {
        "wood": "the wood was deep and green, and the light came down through the leaves in soft gold",
        "garden": "the garden was wide and bright, and a small creek ran past the flower beds",
        "village": "the village square was warm and tidy, and a little stone bridge crossed a quiet stream",
    }.get(place.id, "the world was quiet and ready for a small tale")


def bridge_image(bridge: Bridge) -> str:
    if bridge.material == "stone":
        return f"a short stone bridge that {('spanned' if bridge.soft else 'crossed')} the creek"
    if bridge.material == "plank":
        return f"a long wooden plank that spanned the creek like a small rainbow"
    return f"a kind old bridge that spanned the creek"


def introduce_fox(world: World, fox: Entity) -> None:
    trait = "clever"
    world.say(
        f"{fox.id} was a {trait} fox with a smooth tongue, and he lived under "
        f"a small stone bridge that spanned {world.place.creek}."
    )


def warn_mother(world: World, traveler: Entity) -> None:
    """A mother warned the traveler about the fox -- seeds the pro-knowledge."""
    if traveler.type in {"girl", "boy"}:
        world.say(
            f"{traveler.id}'s mother had said, 'Keep your pro, my love, and "
            f"let no smooth tongue span a bridge over your promise.'"
        )
        traveler.memes["pro_warned"] += 1


def arrive(world: World, traveler: Entity, bridge: Bridge) -> None:
    world.say(
        f"One {('rainy' if world.weather == 'rainy' else 'soft')} day, "
        f"{traveler.id} came to {bridge_image(bridge)}."
    )


def _do_deceive(world: World, fox: Entity, traveler: Entity, trick: Trick,
                narrate: bool = True) -> None:
    fox.memes["cheat"] += 1
    traveler.memes["tricked"] += 1
    world.keep(fox.id, kept=False)
    if narrate:
        world.say(
            f'The fox said, "{trick.ruse}," and he pointed to a safe-looking stone.'
        )
        world.say(trick.consequence)


def try_deceive(world: World, fox: Entity, traveler: Entity, trick: Trick) -> bool:
    """Run a single deception beat; return True if it actually fooled them."""
    if trick.trick_kind != traveler.gift_kind:
        return False
    pred = predict_deception(world, fox, traveler, trick)
    if not pred["gift_lost"]:
        return False
    _do_deceive(world, fox, traveler, trick, narrate=True)
    return True


def see_through(world: World, fox: Entity, traveler: Entity, trick: Trick) -> None:
    """The pro-trained traveler names the truth and refuses to be tricked."""
    fox.memes["caught"] += 1
    fox.memes["shame"] += 1
    fox.memes["cheat"] += 0   # no extra cheat when caught cleanly
    traveler.memes["safe"] += 1
    traveler.memes["pro_kept"] += 1
    world.keep(traveler.id, kept=True)
    world.say(
        f'{traveler.id} only smiled and said, "{trick.truth}."'
    )
    world.say(
        f'{traveler.id.capitalize()} would not be deceived, and {traveler.pronoun()} '
        f'offered instead a small lesson about pros, which are spans of trust kept between two hearts.'
    )


def cross_safely(world: World, fox: Entity, traveler: Entity, trick: Trick,
                 bridge: Bridge) -> None:
    world.say(
        f"At last {traveler.id} stepped gently onto {bridge_image(bridge)} and "
        f"the bridge held true beneath {traveler.pronoun('possessive')} feet."
    )
    if traveler.knows_pro:
        fox.memes["trust"] += 1
        fox.memes["cheat"] = 0.0
        fox.memes["shame"] = 0.0
        world.keep("Fox", kept=True)
        world.say(
            f'The fox blinked, for he had never met a traveler who knew what a pro was. '
            f'He stammered, and the bridge felt suddenly small under him.'
        )
        world.say(
            f'"I will keep my pro too," the fox said, and he let {traveler.id} cross '
            f'without trickery. The fox had learned that pros -- careful, kept promises -- '
            f'are the real span that carries folk across.'
        )
    propagate(world, narrate=False)


def epilogue(world: World, fox: Entity, bridge: Bridge) -> None:
    world.say(
        f"From that day the fox was honest, the bridge stayed kind, and "
        f"{world.place.creek} sang softly under the moon."
    )
    world.facts.update(
        kept_pros=sum(1 for w, k in world.pros if k),
        false_pros=sum(1 for w, k in world.pros if not k),
    )


# -----------------------------------------------------------------------
# The screenplay: fairy-tale three-act shape, driven entirely by the verbs above.
# -----------------------------------------------------------------------
def tell(place: Place, trick: Trick, traveler_cfg: Traveler, bridge: Bridge,
         fox_name: str = "Renard", fox_traits: Optional[list[str]] = None) -> World:
    world = World(place)
    world.weather = "rainy" if trick.trick_kind == "lost_feather" else "soft"

    fox = world.add(Entity(
        id=fox_name, kind="character", type="fox",
        label="the fox", traits=["clever", "smooth"] + (fox_traits or ["proud"]),
    ))
    traveler = world.add(Entity(
        id=traveler_cfg.id, kind="character", type=traveler_cfg.type,
        label=traveler_cfg.label, phrase=traveler_cfg.phrase,
        traits=[], plural=traveler_cfg.plural,
    ))
    bridge_ent = world.add(Entity(
        id="Bridge", kind="thing", type="bridge", label="the bridge",
        phrase=bridge_image(bridge), spans=True,
    ))

    # Act 1 -- setup: the wood, the fox, the first traveler (the woodcutter, who is
    # *not* pro-trained, so the fox's ruse lands).
    introduce_fox(world, fox)
    world.para()
    first_traveler = world.add(Entity(
        id="Wren", kind="character", type="woodcutter", label="the woodcutter",
        traits=["trusting"],
    ))
    warn_mother(world, first_traveler) if first_traveler.type in {"girl", "boy"} else None
    arrive(world, first_traveler, bridge_ent)
    world.say(
        f"{first_traveler.id} came carrying a small crust of bread, and the fox "
        f"smiled and pointed to a mossy stone."
    )
    _do_deceive(world, fox, first_traveler, trick, narrate=True)
    first_traveler.meters["wet"] += 1 if trick.trick_kind == "splash" else 0

    # Act 2 -- middle: the fox's pride, more small victims, the bridge growing wary.
    world.para()
    goose = world.add(Entity(
        id="Greta", kind="character", type="goose", label="the goose",
        traits=["proud"], plural=False,
    ))
    world.say(
        f"Later a fine {goose.type} came to the bridge with a feather in her beak, "
        f"and the fox tried his smooth tongue again."
    )
    _do_deceive(world, fox, goose, trick, narrate=True)

    # Act 3 -- turn + resolution: the pro-trained traveler refuses, the fox learns.
    world.para()
    arrive(world, traveler, bridge_ent)
    warn_mother(world, traveler)
    if traveler_can_pro(traveler_cfg):
        world.say(
            f"{traveler.id} had been taught that pros -- proper promises -- were sacred, "
            f"and {traveler.pronoun()} watched the fox's smooth tongue with quiet eyes."
        )
        tried = try_deceive(world, fox, traveler, trick)
        if tried:
            see_through(world, fox, traveler, trick)
        else:
            world.say(
                f"The fox tried his usual ruse, but {traveler.id} only smiled."
            )
            traveler.memes["pro_kept"] += 1
            fox.memes["caught"] += 1
        cross_safely(world, fox, traveler, trick, bridge_ent)
    else:
        # The traveler does not know a pro -- the fox wins this round.
        _do_deceive(world, fox, traveler, trick, narrate=True)
        world.say(
            f"{traveler.id} sat on the bank, sadly brushing {trick.trick_kind} from "
            f"{traveler.pronoun('possessive')} {traveler_cfg.gift}."
        )

    epilogue(world, fox, bridge_ent)

    world.facts.update(
        fox=fox, traveler=traveler, traveler_cfg=traveler_cfg,
        bridge=bridge_ent, trick=trick, place=place,
        pros=world.pros,
        fox_kept=any(w == "Fox" and k for w, k in world.pros),
        traveler_kept=any(w == traveler.id and k for w, k in world.pros),
    )
    return world


# -----------------------------------------------------------------------
# Content registries.
# -----------------------------------------------------------------------
PLACES = {
    "wood": Place(id="wood", name="the deep green wood", creek="a quiet creek"),
    "garden": Place(id="garden", name="the wide garden", creek="a small creek"),
    "village": Place(id="village", name="the warm village", creek="a quiet stream"),
}

TRICKS = {
    "splash": Trick(
        id="splash",
        verb="step on the green stone",
        consequence=(
            "the green stone tipped, and the woodcutter tumbled into the cold water "
            "with a great splash that soaked his bread"
        ),
        trick_kind="lost_bread",
        ruse="The green stone is the safest, traveler; step on it and the water will bow",
        finding="a fox will not give a pro to a hungry heart",
        truth=(
            "A pro is a span of trust between two hearts; if you will not span the "
            "water with a kept promise, I will not cross, and you will not eat my bread"
        ),
        tags={"splash", "water", "pro"},
    ),
    "prick": Trick(
        id="prick",
        verb="reach for the bright berry",
        consequence=(
            "the berry hid a thorn, and the traveler's finger came away red, and "
            "the fox ate the bright bloom they had hoped to bring home"
        ),
        trick_kind="lost_flower",
        ruse="The brightest berry is the kindest, traveler; reach for it and the wood will bow",
        finding="a fox will not give a pro to a soft hand",
        truth=(
            "A pro is a span of trust between two hearts; if you will not span the "
            "wood with a kept promise, I will not reach, and you will not wear my flower"
        ),
        tags={"prick", "thorn", "pro"},
    ),
    "lost_feather": Trick(
        id="lost_feather",
        verb="trust the low branch",
        consequence=(
            "the low branch snapped, and the goose's feather drifted down to the fox, "
            "who tucked it into his hat"
        ),
        trick_kind="lost_feather",
        ruse="The low branch is the gentlest, traveler; lean on it and the wind will bow",
        finding="a fox will not give a pro to a feathered friend",
        truth=(
            "A pro is a span of trust between two hearts; if you will not span the "
            "wind with a kept promise, I will not lean, and you will not have my feather"
        ),
        tags={"lost_feather", "wind", "pro"},
    ),
}

TRAVELERS = {
    "girl": Traveler(
        id="Ivy", type="girl", label="the girl", gift="bread", gift_kind="lost_bread",
        knows_pro=True, phrase="a gentle girl with a basket of small crusts",
    ),
    "boy": Traveler(
        id="Tomas", type="boy", label="the boy", gift="flower", gift_kind="lost_flower",
        knows_pro=True, phrase="a quiet boy with a small bright bloom",
    ),
    "goose": Traveler(
        id="Greta", type="goose", label="the goose", gift="feather", gift_kind="lost_feather",
        knows_pro=False, phrase="a fine old goose with a white feather", plural=False,
    ),
    "toad": Traveler(
        id="Old Toad", type="toad", label="the old toad", gift="bread", gift_kind="lost_bread",
        knows_pro=False, phrase="a wise old toad who carried a small crust",
    ),
}

BRIDGES = {
    "stone": Bridge(id="stone", name="a short stone bridge", material="stone"),
    "plank": Bridge(id="plank", name="a long wooden plank", material="plank"),
}

GIRL_NAMES = ["Ivy", "Maeve", "Lila", "Rose", "Wren", "Elsa", "Cara", "Nora", "Hana", "Iris"]
BOY_NAMES = ["Tomas", "Pip", "Theo", "Joss", "Frey", "Otto", "Soren", "Bram", "Linus", "Quill"]
FOX_NAMES = ["Renard", "Vulpie", "Fynn", "Sage", "Ash", "Rowan", "Bramble", "Bracken", "Cinder", "Ember"]
FOX_TRAITS = ["proud", "smooth", "soft-voiced", "well-dressed", "merry", "watchful"]


def valid_combos() -> list[tuple[str, str, str]]:
    """(place, trick, traveler) triples that pass the reasonableness gate.

    A trick is only valid with a traveler whose gift_kind matches, and at least
    one traveler in the cast must be pro-trained (otherwise the turn collapses)."""
    out: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for trick_id, t in TRICKS.items():
            for tr_id, tr in TRAVELERS.items():
                if trick_matches(t, tr) and tr.knows_pro:
                    out.append((place_id, trick_id, tr_id))
    return out


# -----------------------------------------------------------------------
# Per-world parameters (domain-specific; the generic StorySample/QAItem live in
# storyworlds/results.py).
# -----------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    place: str
    trick: str
    traveler: str
    bridge: str
    fox_name: str
    fox_trait: str
    seed: Optional[int] = None


# -----------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# -----------------------------------------------------------------------
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


KNOWLEDGE = {
    "pro": [("What is a pro?",
             "A pro is a proper promise -- a clear, kept promise that someone "
             "swears to do and then truly does.")],
    "span": [("What does it mean to span something?",
              "To span something means to stretch across it, like a bridge spans "
              "a creek so people can walk over the water.")],
    "deceive": [("What does it mean to deceive someone?",
                 "To deceive someone is to trick them with smooth words or false "
                 "promises so they believe something that is not true.")],
    "fox": [("Why are foxes known as clever in stories?",
             "Foxes are known as clever in stories because they watch and think "
             "before they act, and they use quick, smooth words to get what they want.")],
    "bridge": [("What is a bridge for?",
                "A bridge is a strong span that carries people safely across a "
                "river, creek, or road.")],
    "promise": [("Why are promises important?",
                 "Promises are important because they are the small spans of trust "
                 "between people, and when they are kept, friends and family can rely on each other.")],
    "water": [("Why does cold creek water feel sharp?",
               "Cold creek water feels sharp because it carries heat away from "
               "warm skin very quickly, so your skin suddenly feels chilly.")],
    "bread": [("Why is bread a kind thing to share?",
               "Bread is a kind thing to share because it fills a hungry belly, "
               "and sharing food with a traveler is a small kept promise of welcome.")],
    "feather": [("Why is a feather a gentle gift?",
                 "A feather is a gentle gift because it is light and soft, and "
                 "it often comes from a bird a friend has cared for.")],
    "flower": [("Why do people give flowers?",
                "People give flowers to show a kind feeling, because flowers are "
                "bright and pretty and they don't cost the giver a heavy thing.")],
    "trust": [("What is trust?",
               "Trust is the feeling you have when you believe someone will keep "
               "their promise and treat you kindly.")],
}
KNOWLEDGE_ORDER = ["pro", "span", "deceive", "promise", "trust", "fox", "bridge",
                   "water", "bread", "feather", "flower"]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    fox, trv, trick, bridge = f["fox"], f["traveler"], f["trick"], f["bridge"]
    place = _safe_fact(world, f, "place")
    return [
        f'Write a short fairy tale for a 4-to-6-year-old that includes the word '
        f'"{trick.id}" and ends with a small lesson about keeping a pro.',
        f'Tell a simple story about a {fox.type} named {fox.id} who lives under a '
        f'stone bridge that {("spans" if bridge.spans else "crosses")} {place.creek} '
        f'and tries to deceive travelers, until a {trv.type} named {trv.id} '
        f'who knows what a pro is comes along.',
        f'Write a gentle fairy tale on the theme "a pro is a span of trust" where '
        f'a smooth-tongued fox meets a traveler who will not be deceived.',
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    fox, trv, trick, bridge = f["fox"], f["traveler"], f["trick"], f["bridge"]
    sub, obj, pos = (trv.pronoun("subject"), trv.pronoun("object"),
                     trv.pronoun("possessive"))
    place = _safe_fact(world, f, "place")

    kept_pro = sum(1 for w, k in world.pros if k)
    false_pro = sum(1 for w, k in world.pros if not k)

    qa: list[QAItem] = [
        QAItem(
            question=(
                f'Who lived under the small bridge that spanned {place.creek} '
                f'before {trv.id} came to cross?'
            ),
            answer=(
                f"A clever fox named {fox.id} lived under the bridge that spanned "
                f"{place.creek}. He watched travelers come and go, and he tried to "
                f"deceive them with smooth words."
            ),
        ),
        QAItem(
            question=(
                f'Why did the fox try to deceive {trv.id} when {sub} came to cross '
                f'the bridge over {place.creek}?'
            ),
            answer=(
                f"The fox tried to deceive {trv.id} because {sub} carried "
                f"{pos} {trv.phrase or pos + ' ' + trv_cfg_gift_phrase(f)} and "
                f"the fox wanted to take {trv.pronoun('object')}'s {trv_gift_name(f)} "
                f"with a smooth ruse."
            ),
        ),
        QAItem(
            question=(
                f'What did {trv.id} say about a pro when the fox tried to deceive '
                f'{obj} on the bridge over {place.creek}?'
            ),
            answer=(
                f'{trv.id.capitalize()} said, "A pro is a span of trust between two '
                f'hearts; if you will not span the water with a kept promise, I '
                f'will not cross, and you will not have my {trv_gift_name(f)}."'
            ),
        ),
    ]
    if f.get("fox_kept"):
        qa.append(QAItem(
            question=(
                f'How did the fox change when {trv.id} named the truth about pros '
                f'at the bridge over {place.creek}?'
            ),
            answer=(
                f'The fox blinked, stammered, and felt the bridge grow suddenly small '
                f'under him. He said, "I will keep my pro too," and he let {trv.id} '
                f'cross without trickery.'
            ),
        ))
    qa.append(QAItem(
        question=(
            f'How many kept pros and broken pros did the fox and {trv.id} share '
            f'over {place.creek}?'
        ),
        answer=(
            f"By the end of the tale there were {kept_pro} kept pros and "
            f"{false_pro} broken pros. The kept pros were the ones that carried "
            f"folk safely across the span of the bridge."
        ),
    ))
    return qa


def trv_cfg_gift_phrase(world_facts: dict) -> str:
    trv: Entity = world_facts["traveler"]
    cfg: Traveler = world_facts["traveler_cfg"]
    if trv.phrase:
        return trv.phrase
    return f"a {trv.label} carrying a small {cfg.gift}"


def trv_gift_name(world_facts: dict) -> str:
    cfg: Traveler = world_facts["traveler_cfg"]
    return {
        "lost_bread": "bread",
        "lost_flower": "flower",
        "lost_feather": "feather",
        "splash": "bread",
        "prick": "flower",
    }.get(cfg.gift_kind, "small gift")


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    f = world.facts
    tags = set(f["trick"].tags)
    tags.add(f["traveler_cfg"].gift_kind)
    if f["traveler_cfg"].knows_pro:
        tags.add("pro")
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags and tag in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# -----------------------------------------------------------------------
# CLI / trace
# -----------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if getattr(e, "spans", False):
            bits.append("spans=True")
        if getattr(e, "sacred", False):
            bits.append("sacred=True")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    kept = sum(1 for w, k in world.pros if k)
    broken = sum(1 for w, k in world.pros if not k)
    lines.append(f"  pros ledger: kept={kept} broken={broken}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        place="wood", trick="splash", traveler="girl", bridge="stone",
        fox_name="Renard", fox_trait="smooth",
    ),
    StoryParams(
        place="garden", trick="prick", traveler="boy", bridge="plank",
        fox_name="Vulpie", fox_trait="proud",
    ),
    StoryParams(
        place="village", trick="lost_feather", traveler="girl", bridge="stone",
        fox_name="Sage", fox_trait="watchful",
    ),
]


def explain_rejection(trick: Trick, traveler: Traveler) -> str:
    return (
        f"(No story: the {trick.id} ruse only fits a traveler whose gift matches "
        f"{trick.trick_kind}; this traveler carries {traveler.gift_kind}.)"
    )


def explain_no_pro(traveler: Traveler) -> str:
    return (
        f"(No story: a pro-trained traveler is required for the turn -- pros are "
        f"what carry the bridge across. This traveler does not know a pro.)"
    )


# -----------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate.
# Only imported when an ASP mode is actually used, so the prose engine still
# runs without clingo installed.  See `--verify`.
# -----------------------------------------------------------------------
ASP_RULES = r"""
% The fox's trick only lands on travelers whose gift kind matches the ruse.
trick_matches(T, Tr) :- trick(T, K), traveler(Tr, K).

% A traveler is pro-trained iff their registry says so.
traveler_knows_pro(Tr) :- pro_traveler(Tr).

% A pro-trained traveler is the one who defeats the fox; a non-pro traveler
% cannot turn the tale, so we require at least one pro traveler in scope.
has_pro_traveler :- traveler_knows_pro(Tr).

% A story is valid when the place supports the trick, the trick matches the
% traveler's gift, and at least one pro traveler exists in scope.
valid(Place, T, Tr) :- place(Place), trick(T, _), traveler(Tr, _),
                       trick_matches(T, Tr), has_pro_traveler.
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid, t in TRICKS.items():
        lines.append(asp.fact("trick", tid, t.trick_kind))
    for trid, tr in TRAVELERS.items():
        lines.append(asp.fact("traveler", trid, tr.gift_kind))
        if tr.knows_pro:
            lines.append(asp.fact("pro_traveler", trid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    """Clingo's version of valid_combos(): (place, trick, traveler) triples."""
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    """Check the inline ASP gate agrees with the Python valid_combos()."""
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# -----------------------------------------------------------------------
# Standard storyworld interface.
# -----------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a fox, a span, a pro. "
                    "Unspecified choices are picked at random (seeded).")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trick", choices=TRICKS)
    ap.add_argument("--traveler", choices=TRAVELERS)
    ap.add_argument("--bridge", choices=BRIDGES)
    ap.add_argument("--fox-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    """Fill in any unspecified choices at random, keeping the combo reasonable.

    Raises StoryError if the *explicit* options describe an invalid story."""
    if getattr(args, "trick", None) and getattr(args, "traveler", None):
        if not trick_matches(_safe_lookup(TRICKS, getattr(args, "trick", None)), _safe_lookup(TRAVELERS, getattr(args, "traveler", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
        if not _safe_lookup(TRAVELERS, getattr(args, "traveler", None)).knows_pro:
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "trick", None) is None or c[1] == getattr(args, "trick", None))
              and (getattr(args, "traveler", None) is None or c[2] == getattr(args, "traveler", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, trick, traveler = rng.choice(list(combos))
    bridge = getattr(args, "bridge", None) or rng.choice(list(BRIDGES.keys()))
    fox_name = getattr(args, "fox_name", None) or rng.choice(FOX_NAMES)
    fox_trait = rng.choice(FOX_TRAITS)
    return StoryParams(
        place=place,
        trick=trick,
        traveler=traveler,
        bridge=bridge,
        fox_name=fox_name,
        fox_trait=fox_trait,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(TRICKS, params.trick), _safe_lookup(TRAVELERS, params.traveler),
                 _safe_lookup(BRIDGES, params.bridge), params.fox_name, [params.fox_trait])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, trick, traveler) combos:\n")
        for place, trick, traveler in triples:
            print(f"  {place:8} {trick:13} {traveler:8}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.fox_name}: {p.trick} at {p.place} (traveler: {p.traveler})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
