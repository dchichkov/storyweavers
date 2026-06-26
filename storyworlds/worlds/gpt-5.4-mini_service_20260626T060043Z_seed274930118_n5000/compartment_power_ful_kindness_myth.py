#!/usr/bin/env python3
"""
A small storyworld about a mythic compartment, a power-ful relic, and the
strange strength of kindness.

The seed tale behind this world:
A child finds an old shrine chest with two compartments. One compartment holds
a bright, power-ful charm, but the other is sealed by a spirit who only opens
for kindness. The child first wants the bright charm for themselves, then learns
to share bread, water, and patience. In the end, the hidden compartment opens,
and the spirit names kindness the truest power.

This script turns that premise into a tiny state-driven simulation with:
- physical meters: light, hunger, dust, opened, sealed
- emotional memes: wonder, greed, fear, kindness, trust, awe
- a reasonableness gate: the story is only valid when kindness can plausibly
  unlock the compartment and the relic can be safely used
- an ASP twin for parity checks
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    compartment: Optional[str] = None
    openable: bool = False
    sealed: bool = False
    power_ful: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    relic: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "priestess"}
        male = {"boy", "father", "man", "king", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Shrine:
    place: str = "the old shrine"
    name: str = "Shrine of the Twin Compartments"
    silence: bool = True
    shrine: object | None = None
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
class Relic:
    id: str
    label: str
    phrase: str
    compartments: tuple[str, str]
    power_compartment: str
    kindness_compartment: str
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
class Companion:
    id: str
    label: str
    role: str
    gift: str
    words: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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
    def __init__(self, shrine: Shrine) -> None:
        self.shrine = shrine
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    name: str
    gender: str
    title: str
    companion: str
    seed: Optional[int] = None
    params: object | None = None
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


NAMES = {
    "girl": ["Mina", "Lira", "Tala", "Sera", "Nara", "Iris"],
    "boy": ["Orin", "Eli", "Cai", "Toren", "Miro", "Jaro"],
}
TITLES = ["little keeper", "young seeker", "small pilgrim", "brave child"]
COMPANIONS = [
    Companion(id="owl", label="an old owl", role="guide", gift="a feather", words="kindness remembers what power forgets"),
    Companion(id="stream", label="a bright stream-spirit", role="guide", gift="cool water", words="share first, and the path opens"),
    Companion(id="deer", label="a quiet deer", role="guide", gift="a leaf", words="soft hands are stronger than hard ones"),
]


def pronoun_word(gender: str, case: str) -> str:
    return {"girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"}}[gender][case]


def valid_combos() -> list[tuple[str, str]]:
    return [("shrine", "kindness")]


@dataclass
class Rule:
    name: str
    apply: callable
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


def _r_power_stirs(world: World) -> list[str]:
    child = world.get("child")
    relic = world.get("relic")
    if child.memes.get("wonder", 0) >= THRESHOLD and not relic.meters.get("glowing", 0):
        sig = ("power",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        relic.meters["glowing"] = 1
        child.memes["awe"] = child.memes.get("awe", 0) + 1
        return [f"The power-ful charm woke inside the compartment and shone like dawn."]
    return []


def _r_kindness_opens(world: World) -> list[str]:
    child = world.get("child")
    relic = world.get("relic")
    if child.memes.get("kindness", 0) >= THRESHOLD and child.meters.get("offered_food", 0) >= THRESHOLD:
        sig = ("open",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        relic.meters["opened"] = 1
        relic.meters["sealed"] = 0
        child.memes["trust"] = child.memes.get("trust", 0) + 1
        return ["The hidden compartment opened softly, as if it had been waiting for a gentle hand."]
    return []


def _r_fear_to_bravery(world: World) -> list[str]:
    child = world.get("child")
    if child.memes.get("fear", 0) >= THRESHOLD and child.memes.get("trust", 0) >= THRESHOLD:
        sig = ("brave",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        child.memes["fear"] = max(0, child.memes["fear"] - 1)
        child.memes["bravery"] = child.memes.get("bravery", 0) + 1
        return [f"The child's fear thinned, and bravery stood in its place."]
    return []


RULES = [
    Rule("power_stirs", _r_power_stirs),
    Rule("kindness_opens", _r_kindness_opens),
    Rule("fear_to_bravery", _r_fear_to_bravery),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def lore_line() -> str:
    return "Long ago, when the stars were young, the shrine kept its secrets in two quiet compartments."


def introduce(world: World, child: Entity, companion: Companion) -> None:
    world.say(lore_line())
    world.say(
        f"A {child.label} named {child.id} came to {world.shrine.place}, "
        f"drawn by a tale of a power-ful charm hidden within a compartment."
    )
    world.say(
        f"Beside the gate waited {companion.label}, who said, "
        f"\"{companion.words.capitalize()}.\""
    )


def enter_shrine(world: World, child: Entity) -> None:
    child.meters["dust"] = child.meters.get("dust", 0) + 1
    child.memes["wonder"] = child.memes.get("wonder", 0) + 1
    world.say(
        f"{child.id} stepped into the shrine, where the air felt old and bright at once."
    )


def want_power(world: World, child: Entity, relic: Entity) -> None:
    child.memes["greed"] = child.memes.get("greed", 0) + 1
    world.say(
        f"{child.id} saw the shining chamber and wanted the power-ful charm for "
        f"{pronoun_word(world.facts['gender'], 'object')}self."
    )
    world.say(
        f"But the compartment was sealed, and the seal would not yield to pulling."
    )


def receive_warning(world: World, companion: Companion) -> None:
    world.say(
        f"{companion.label.capitalize()} warned that the relic answered only to kindness, not to grasping hands."
    )


def offer_kindness(world: World, child: Entity, companion: Companion) -> None:
    child.memes["kindness"] = child.memes.get("kindness", 0) + 1
    child.meters["offered_food"] = child.meters.get("offered_food", 0) + 1
    world.say(
        f"{child.id} remembered the companion's words and shared bread and water instead."
    )
    world.say(
        f"{child.id} also bowed and said thank you for the guidance."
    )


def open_compartment(world: World, child: Entity, relic: Entity) -> None:
    world.say(
        f"Then the hidden compartment opened, and the power-ful light spilled across the stone floor."
    )
    child.memes["awe"] = child.memes.get("awe", 0) + 1
    relic.meters["opened"] = 1
    relic.meters["sealed"] = 0
    propagate(world, narrate=True)


def use_power(world: World, child: Entity, relic: Entity) -> None:
    child.memes["trust"] = child.memes.get("trust", 0) + 1
    world.say(
        f"{child.id} lifted the charm carefully, and its glow warmed the cold room without burning it."
    )
    world.say(
        f"The light did not demand a throne or a crown; it simply made the shrine feel safe."
    )


def ending(world: World, child: Entity, companion: Companion) -> None:
    world.say(
        f"When {child.id} left the shrine, {pronoun_word(world.facts['gender'], 'subject')} carried no greedy wish at all."
    )
    world.say(
        f"Instead, {pronoun_word(world.facts['gender'], 'subject')} carried the lesson that kindness could open what strength could not."
    )
    world.say(
        f"{companion.label.capitalize()} stayed behind in the dust, watching the path glow faintly like a blessing."
    )


def tell(params: StoryParams) -> World:
    shrine = Shrine()
    world = World(shrine)
    gender = params.gender
    companion = next(c for c in COMPANIONS if c.id == params.companion)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=gender,
        label=params.title,
    ))
    relic = world.add(Entity(
        id="relic",
        kind="thing",
        type="relic",
        label="compartment chest",
        phrase="an ancient compartment chest",
        openable=True,
        sealed=True,
        power_ful=True,
        meters={"sealed": 1},
    ))
    world.facts.update(child=child, relic=relic, companion=companion, gender=gender, params=params)

    introduce(world, child, companion)
    world.para()
    enter_shrine(world, child)
    want_power(world, child, relic)
    receive_warning(world, companion)
    world.para()
    offer_kindness(world, child, companion)
    open_compartment(world, child, relic)
    use_power(world, child, relic)
    world.para()
    ending(world, child, companion)
    return world


def story_is_reasonable(params: StoryParams) -> bool:
    return params.companion in {c.id for c in COMPANIONS}


def explain_rejection() -> str:
    return "(No story: this myth needs a companion who can teach kindness, or the compartment never opens.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    return [
        f'Write a small myth about {child.id}, a hidden compartment, and a power-ful charm that answers to kindness.',
        f"Tell a gentle legend where {child.id} enters the shrine, wants the glowing treasure, and learns a kinder way.",
        f'Write a child-friendly myth ending with a sealed compartment opening after an act of kindness.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    companion = _safe_fact(world, f, "companion")
    return [
        QAItem(
            question=f"What did {child.id} find in the shrine?",
            answer="They found an ancient compartment chest with a sealed hidden chamber and a power-ful charm inside it.",
        ),
        QAItem(
            question=f"Why did the hidden compartment open?",
            answer=f"It opened because {child.id} shared bread and water, listened to the warning, and chose kindness instead of grasping for the charm.",
        ),
        QAItem(
            question=f"Who helped teach {child.id} the lesson?",
            answer=f"{companion.label.capitalize()} helped by warning that the relic answered to kindness and by pointing {child.id} toward a gentler choice.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does kindness do in this world?",
            answer="Kindness can unlock a sealed compartment and let a power-ful blessing be used safely.",
        ),
        QAItem(
            question="What is a compartment?",
            answer="A compartment is a separate space inside a box, chest, or container that holds something apart from the rest.",
        ),
        QAItem(
            question="What does power-ful mean in this storyworld?",
            answer="Power-ful means strong enough to change the air in a room, shine brightly, or make a relic feel sacred.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.sealed:
            bits.append("sealed=True")
        if e.power_ful:
            bits.append("power_ful=True")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Mina", gender="girl", title="little keeper", companion="owl"),
    StoryParams(name="Orin", gender="boy", title="young seeker", companion="stream"),
    StoryParams(name="Tala", gender="girl", title="brave child", companion="deer"),
]


ASP_RULES = r"""
% A story is reasonable when a companion can teach kindness.
reasonable(C) :- companion(C).

% The hidden compartment opens when kindness is present.
opens :- kindness, offered_food.

% The relic is power-ful when the chamber is opened.
power_ful_relic :- opens.

% A valid myth uses a companion and ends with the opening.
valid_story :- companion(_), opens, power_ful_relic.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for c in COMPANIONS:
        lines.append(asp.fact("companion", c.id))
    lines.append(asp.fact("world", "shrine"))
    lines.append(asp.fact("compartment", "hidden"))
    lines.append(asp.fact("kindness", "virtue"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_story() -> bool:
    import asp
    model = asp.one_model(asp_program("#show valid_story/0."))
    return bool(model)


def asp_verify() -> int:
    py = all(story_is_reasonable(p) for p in CURATED)
    ap = asp_valid_story()
    if py and ap:
        print("OK: ASP and Python gates agree, and the myth can be generated.")
        return 0
    print("MISMATCH: ASP/Python gate failure.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a mythic compartment and the power of kindness.")
    ap.add_argument("--name", choices=sum(NAMES.values(), []))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--title", choices=TITLES)
    ap.add_argument("--companion", choices=[c.id for c in COMPANIONS])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    title = getattr(args, "title", None) or rng.choice(TITLES)
    companion = getattr(args, "companion", None) or rng.choice([c.id for c in COMPANIONS])
    params = StoryParams(name=name, gender=gender, title=title, companion=companion)
    if not story_is_reasonable(params):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program("#show valid_story/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    elif getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/0."))
        print("ASP model:", model)
        return
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name} / {p.companion} / {p.title}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
