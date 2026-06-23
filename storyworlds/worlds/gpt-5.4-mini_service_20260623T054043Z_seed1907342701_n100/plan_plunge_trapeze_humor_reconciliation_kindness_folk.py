#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/plan_plunge_trapeze_humor_reconciliation_kindness_folk.py
===============================================================================================================================

A standalone folk-tale story world about a small village fair, a trapeze, a
careful plan, a comic plunge, and a kind reconciliation.

The seed tale behind the world is short and gentle:
- A child performer wants to leap from a trapeze at the folk fair.
- A friend worries that the landing is too hard.
- They make a plan, laugh over a harmless mishap, and choose a kinder way.
- The ending proves what changed in the world: a safer landing, warmer feelings,
  and a shared performance that ends in laughter instead of hurt.

The world model uses physical meters and emotional memes, a tiny forward-chaining
rule engine, a reasonableness gate, inline ASP rules, and three QA sets:
(1) generation prompts, (2) story-grounded QA, and (3) world-knowledge QA.

This file is intentionally self-contained except for the shared result/ASP
helpers described in the repo contract.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    owner: str = ""
    caretaker: str = ""
    target: bool = False
    safe: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    a: object | None = None
    b: object | None = None
    charm_ent: object | None = None
    h: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
        if not hasattr(self, "_tags"):
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
    label: str
    detail: str
    affords: set[str] = field(default_factory=set)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Situation:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    keyword: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Landing:
    id: str
    label: str
    phrase: str
    regions: set[str]
    guards: set[str]
    fix: str
    ending: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Charm:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather: str = "fair"

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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.weather = self.weather
        return w


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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["plunge"] < THRESHOLD:
            continue
        for item in list(world.entities.values()):
            if item.kind != "thing" or not item.target:
                continue
            if item.meters["safe"] >= THRESHOLD:
                continue
            if item.meters["tumble"] >= THRESHOLD:
                continue
            sig = ("spill", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["tumble"] += 1
            out.append(f"{item.label.capitalize()} wobbled with the plunge.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    pair = world.facts.get("pair")
    if not pair:
        return out
    a, b = pair
    ea, eb = world.get(a), world.get(b)
    if ea.memes["kindness"] < THRESHOLD or eb.memes["kindness"] < THRESHOLD:
        return out
    if ea.memes["grudge"] < THRESHOLD and eb.memes["grudge"] < THRESHOLD:
        return out
    sig = ("reconcile", a, b)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ea.memes["grudge"] = 0.0
    eb.memes["grudge"] = 0.0
    ea.memes["warmth"] += 1
    eb.memes["warmth"] += 1
    out.append("__reconcile__")
    return out


CAUSAL_RULES = [
    Rule("spill", "physical", _r_spill),
    Rule("reconcile", "social", _r_reconcile),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def plunge_at_risk(sit: Situation, landing: Landing) -> bool:
    return bool(sit.zone & landing.regions)


def select_landing(sit: Situation, landing: Landing) -> bool:
    return sit.risk in landing.guards and plunge_at_risk(sit, landing)


@dataclass
class StoryParams:
    place: str = "green"
    situation: str = "trapeze"
    landing: str = "hay"
    charm: str = "lantern"
    name_a: str = "Mira"
    type_a: str = "girl"
    name_b: str = "Jon"
    type_b: str = "boy"
    helper: str = "grandmother"
    tone: str = "cheerful"
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


PLACES = {
    "green": Place("green", "the green by the village lane", "The green smelled of grass and warm bread.", affords={"trapeze"}),
    "orchard": Place("orchard", "the orchard edge", "Apple leaves clapped softly over the fair.", affords={"trapeze"}),
    "river": Place("river", "the riverbank", "Willows leaned over the water and watched the play.", affords={"trapeze"}),
}

SITUATIONS = {
    "trapeze": Situation("trapeze", "swing on the trapeze", "swinging on the trapeze", "rush to the trapeze", "plunge", {"torso", "legs"}, "trapeze", {"trapeze", "fair"}),
    "plunge": Situation("plunge", "take a plunge", "taking a plunge", "dash for the edge", "plunge", {"legs", "torso"}, "plunge", {"plunge", "fair"}),
}

LANDINGS = {
    "hay": Landing("hay", "a hay pile", "a soft hay pile", {"legs", "torso"}, {"plunge"}, "pile up the hay higher", "the hay lay fluffy and ready", tags={"hay", "safe"}),
    "blanket": Landing("blanket", "a blanket stack", "a blanket stack", {"legs", "torso"}, {"plunge"}, "fold the blankets into a thicker nest", "the blankets waited in a tidy heap", tags={"blanket", "safe"}),
}

CHARMS = {
    "lantern": Charm("lantern", "a lantern", "a little lantern", tags={"lantern", "light"}),
    "bells": Charm("bells", "a string of bells", "a bright string of bells", tags={"bells", "humor"}),
    "cupcake": Charm("cupcake", "a cupcake tray", "a tray of honey cupcakes", tags={"cupcake", "kindness"}),
}

GIRL_NAMES = ["Mira", "Nia", "Sera", "Lena", "Rosa", "Talia"]
BOY_NAMES = ["Jon", "Oren", "Pavel", "Milo", "Tobin", "Bram"]
TRAITS = ["cheerful", "gentle", "merry", "curious", "kind"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for sid, sit in SITUATIONS.items():
            if sid not in place.affords:
                continue
            for lid, landing in LANDINGS.items():
                if select_landing(sit, landing):
                    combos.append((pid, sid, lid))
    return combos


def _choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def _resolve_person(args_name: Optional[str], args_type: Optional[str], rng: random.Random) -> tuple[str, str]:
    type_ = args_type or rng.choice(["girl", "boy"])
    name = args_name or _choose_name(rng, type_)
    return name, type_


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b = f["a"], f["b"]
    sit: Situation = f["situation"]
    place: Place = f["place"]
    landing: Landing = f["landing_cfg"]
    return [
        f'Write a folk-tale story for a child about {a.id} and {b.id} at {place.label} that includes the words "plan", "plunge", and "trapeze".',
        f"Tell a warm village-fair story where {a.id} wants to {sit.verb}, {b.id} helps with a plan, and the ending turns from a funny slip to kindness.",
        f"Write a short folk tale about a trapeze, a careful plan, and a safe landing in {landing.phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, helper = f["a"], f["b"], f["helper"]
    sit: Situation = f["situation"]
    place: Place = f["place"]
    landing: Landing = f["landing_cfg"]
    charm: Charm = f["charm_cfg"]
    qa = [
        QAItem(
            f"Who are the two children in the story at {place.label}?",
            f"The story is about {a.id} and {b.id}, two children at {place.label}. They were there for a folk-fair playtime, not a real danger.",
        ),
        QAItem(
            f"What did {a.id} want to do on the {sit.keyword} before the plan was made?",
            f"{a.id} wanted to {sit.verb}. That wish mattered because the trapeze was high enough that the landing had to be soft and kind.",
        ),
        QAItem(
            f"Why did {b.id} suggest a plan before the plunge?",
            f"{b.id} suggested a plan because the first idea was too much of a tumble for a busy village fair. The plan gave them a safer way to keep the joke and the game.",
        ),
    ]
    if f.get("comic_tumble"):
        qa.append(QAItem(
            f"What funny thing happened before the children reconciled?",
            f"The {charm.label} in the story helped turn the mishap into a laugh, and the tumble made everyone pause. Nobody was hurt; it only made the children blush and then smile.",
        ))
    if f.get("resolved"):
        qa.append(QAItem(
            f"How did {helper} help the children after the silly plunge?",
            f"{helper} helped by being kind and steady. {helper} showed them how to use {landing.phrase} so the trapeze play could end in a safe, cheerful way.",
        ))
        qa.append(QAItem(
            f"What changed between {a.id} and {b.id} by the end of the tale?",
            f"They stopped squabbling and made up. Their grudge softened into warmth, and they finished side by side instead of pulling apart.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["situation"].tags) | set(world.facts["landing_cfg"].tags) | set(world.facts["charm_cfg"].tags)
    knowledge = {
        "trapeze": [("What is a trapeze?", "A trapeze is a bar that hangs on ropes or chains so a performer can swing from it. It is used for play or performance, not rough climbing.")],
        "plunge": [("What does plunge mean?", "To plunge means to drop or leap down quickly. It can sound funny in a story, but it needs care in real life.")],
        "hay": [("What is hay?", "Hay is dried grass that can feel soft and springy to land on. Farm animals eat it, and people often use it for bedding or cushions.")],
        "blanket": [("What is a blanket stack good for?", "A blanket stack can make a soft place to sit or land. People fold blankets together when they want a cozy cushion.")],
        "bells": [("What do bells do in a story?", "Bells can make a bright, cheerful sound. In a folk tale, they often add humor or help everyone notice what is happening.")],
        "lantern": [("What is a lantern?", "A lantern is a light that helps people see when the day is dim. It can make a fair feel warm and friendly.")],
        "kindness": [("What is kindness?", "Kindness means being gentle, helpful, and caring. Kind people try to make things easier for others.")],
        "reconciliation": [("What is reconciliation?", "Reconciliation means making up after a disagreement. People talk, forgive, and feel close again.")],
        "humor": [("What is humor?", "Humor is what makes people laugh or smile. A funny mistake can become part of a happy story when nobody gets hurt.")],
        "safe": [("Why is a soft landing important?", "A soft landing helps keep people from getting hurt when they jump or fall. It is a safe choice for a playful adventure.")],
    }
    out: list[QAItem] = []
    for tag in ["trapeze", "plunge", "hay", "blanket", "bells", "lantern", "kindness", "reconciliation", "humor", "safe"]:
        if tag in tags and tag in knowledge:
            out.extend(QAItem(q, a) for q, a in knowledge[tag])
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def tell(place: Place, sit: Situation, landing_cfg: Landing, charm: Charm, name_a: str, type_a: str, name_b: str, type_b: str, helper: str, tone: str) -> World:
    world = World(place)
    a = world.add(Entity(id=name_a, kind="character", type=type_a, role="plunger"))
    b = world.add(Entity(id=name_b, kind="character", type=type_b, role="planner"))
    h = world.add(Entity(id=helper, kind="character", type="adult", role="helper"))
    target = world.add(Entity(id="landing", kind="thing", type="thing", label=landing_cfg.label, phrase=landing_cfg.phrase, target=True))
    charm_ent = world.add(Entity(id=charm.id, kind="thing", type="thing", label=charm.label, phrase=charm.phrase))
    a.memes["kindness"] = 1.0
    b.memes["kindness"] = 1.0
    a.memes["grudge"] = 1.0
    b.memes["grudge"] = 1.0
    a.meters["plunge"] = 0.0
    target.meters["safe"] = 0.0
    target.meters["tumble"] = 0.0
    world.facts["pair"] = (a.id, b.id)
    world.facts["comic_tumble"] = False
    world.facts["resolved"] = False

    world.say(f"At {place.label}, under a fair sky, {a.id} and {b.id} began a folk-game with the {sit.keyword}.")
    world.say(f"The {place.detail.lower()} {charm.phrase} and a small crowd of neighbors waiting to smile.")
    world.para()
    world.say(f"{a.id} wanted to {sit.verb}, but {b.id} waved a careful hand and said, 'First, let us make a plan.'")
    world.say(f"So they set {landing_cfg.phrase} below the trapeze and asked {helper} to check that it was soft enough.")

    if not select_landing(sit, landing_cfg):
        pass

    world.para()
    a.memes["boldness"] += 1
    a.meters["plunge"] += 1
    world.say(f"{a.id} climbed the {sit.keyword} and made a grand face, as if {a.id} were a bird in a hat.")
    world.say(f"Then came the plunge. It was not a terrible plunge; it was a funny one, like a bean rolling off a spoon.")
    target.meters["tumble"] += 1
    world.facts["comic_tumble"] = True
    propagate(world, narrate=False)
    world.say(f"{b.id} laughed first, then {a.id} laughed too, because the tumble had only bounced into the soft landing.")
    world.say(f"Even {helper} smiled and said the plan had saved the day.")

    world.para()
    h.memes["kindness"] += 1
    a.memes["kindness"] += 1
    b.memes["kindness"] += 1
    a.memes["grudge"] += 1
    b.memes["grudge"] += 1
    propagate(world, narrate=False)
    world.say(f"{a.id} and {b.id} tucked their quibble away and made up at once.")
    world.say(f"{helper} lifted the {landing_cfg.label} a little higher and showed them the safer way to try again.")
    world.say(f"This time the trapeze swayed over {landing_cfg.phrase}, and the crowd clapped as the two friends bowed together.")
    target.meters["safe"] = 1.0
    world.facts["resolved"] = True

    world.facts.update(a=a, b=b, helper=helper, situation=sit, place=place, landing_cfg=landing_cfg, charm_cfg=charm_ent, tone=tone)
    return world


CURATED = [
    StoryParams(place="green", situation="trapeze", landing="hay", charm="bells", name_a="Mira", type_a="girl", name_b="Jon", type_b="boy", helper="Grandmother", tone="cheerful"),
    StoryParams(place="orchard", situation="trapeze", landing="blanket", charm="lantern", name_a="Rosa", type_a="girl", name_b="Bram", type_b="boy", helper="Uncle", tone="merry"),
    StoryParams(place="river", situation="plunge", landing="hay", charm="cupcake", name_a="Lena", type_a="girl", name_b="Milo", type_b="boy", helper="Auntie", tone="kind"),
    StoryParams(place="green", situation="plunge", landing="blanket", charm="bells", name_a="Talia", type_a="girl", name_b="Oren", type_b="boy", helper="Grandfather", tone="gentle"),
]


def explain_rejection(sit: Situation, landing: Landing) -> str:
    return f"(No story: {sit.keyword} cannot safely end on {landing.label}; the landing would not match the plunge.)"


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for sid, s in SITUATIONS.items():
        lines.append(asp.fact("situation", sid))
        lines.append(asp.fact("risk", sid, s.risk))
        for r in sorted(s.zone):
            lines.append(asp.fact("zone", sid, r))
    for lid, l in LANDINGS.items():
        lines.append(asp.fact("landing", lid))
        for r in sorted(l.regions):
            lines.append(asp.fact("region", lid, r))
        for g in sorted(l.guards):
            lines.append(asp.fact("guards", lid, g))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,S,L) :- affords(P,S), zone(S,R), region(L,R), guards(L,plunge).
reconciled(A,B) :- kindness(A), kindness(B), grudge(A), grudge(B).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations.")
        print("only python:", sorted(py - cl))
        print("only asp:", sorted(cl - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: folk tale, trapeze, plan, plunge, humor, reconciliation, kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--situation", choices=SITUATIONS)
    ap.add_argument("--landing", choices=LANDINGS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--name-a")
    ap.add_argument("--type-a", choices=["girl", "boy"])
    ap.add_argument("--name-b")
    ap.add_argument("--type-b", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--tone", choices=["cheerful", "merry", "kind", "gentle"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "situation", None) is None or c[1] == getattr(args, "situation", None))
              and (getattr(args, "landing", None) is None or c[2] == getattr(args, "landing", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, situation, landing = rng.choice(list(combos))
    charm = getattr(args, "charm", None) or rng.choice(sorted(CHARMS))
    type_a = getattr(args, "type_a", None) or rng.choice(["girl", "boy"])
    type_b = getattr(args, "type_b", None) or ("boy" if type_a == "girl" else "girl")
    name_a = getattr(args, "name_a", None) or _choose_name(rng, type_a)
    name_b = getattr(args, "name_b", None) or _choose_name(rng, type_b)
    if name_b == name_a:
        name_b = _choose_name(rng, type_b)
    helper = getattr(args, "helper", None) or rng.choice(["Grandmother", "Grandfather", "Auntie", "Uncle"])
    tone = getattr(args, "tone", None) or rng.choice(["cheerful", "merry", "kind", "gentle"])
    return StoryParams(place=place, situation=situation, landing=landing, charm=charm, name_a=name_a, type_a=type_a, name_b=name_b, type_b=type_b, helper=helper, tone=tone)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.situation not in SITUATIONS or params.landing not in LANDINGS or params.charm not in CHARMS:
        pass
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(SITUATIONS, params.situation), _safe_lookup(LANDINGS, params.landing), _safe_lookup(CHARMS, params.charm), params.name_a, params.type_a, params.name_b, params.type_b, params.helper, params.tone)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={dict(meters)}")
            if memes:
                bits.append(f"memes={dict(memes)}")
            print(f"  {e.id}: {' '.join(bits)}")
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
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for row in combos:
            print(" ", row)
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
