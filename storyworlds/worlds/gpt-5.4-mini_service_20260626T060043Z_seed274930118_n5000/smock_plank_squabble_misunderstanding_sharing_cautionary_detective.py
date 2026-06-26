#!/usr/bin/env python3
"""
storyworlds/worlds/smock_plank_squabble_misunderstanding_sharing_cautionary_detective.py
=======================================================================================

A small detective-style story world about a missing smock, a plank, and a squabble
that turns out to be a misunderstanding. The story is child-facing, state-driven,
and built to support a gentle sharing resolution with a cautionary ending.

Premise:
- A child detective notices a smock on a plank.
- Two friends start squabbling over it because they think it belongs to one of them.
- The detective investigates the clue trail and discovers the smock was only set
  aside there to dry.
- The friends share the plank, the smock is returned, and everyone learns to ask
  before grabbing.

World model:
- typed entities with physical meters and emotional memes
- a clue-and-guess loop that can escalate to a squabble
- a correction that resolves the misunderstanding through sharing

The script includes:
- parameter registries
- a reasonableness gate
- inline ASP_RULES and asp_facts()
- generate / emit / main
- trace, QA, JSON, ASP, and verification modes
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    a: object | None = None
    b: object | None = None
    hero: object | None = None
    plank: object | None = None
    smock: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
    name: str
    indoor: bool = False
    clues: set[str] = field(default_factory=set)
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
class Item:
    id: str
    label: str
    phrase: str
    clue: str
    type: str = "thing"
    owner: str = ""
    placeable: bool = True
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
class StoryParams:
    place: str
    clue: str
    item: str
    name: str
    gender: str
    friend1: str
    friend2: str
    seed: Optional[int] = None
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
        self.item_positions: dict[str, str] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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

    def copy(self) -> "World":
        import copy as _copy

        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.item_positions = dict(self.item_positions)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("Detective")
    for fid in ("FriendA", "FriendB"):
        friend = world.get(fid)
        if detective.memes.get("clue", 0) >= THRESHOLD and friend.memes.get("assumption", 0) >= THRESHOLD:
            sig = ("misunderstanding", fid)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            friend.memes["conflict"] = friend.memes.get("conflict", 0) + 1
            detective.memes["concern"] = detective.memes.get("concern", 0) + 1
            out.append(f"{friend.label} thought the smock had been taken on purpose.")
    return out


def _r_squabble(world: World) -> list[str]:
    a = world.get("FriendA")
    b = world.get("FriendB")
    if a.memes.get("conflict", 0) >= THRESHOLD and b.memes.get("conflict", 0) >= THRESHOLD:
        sig = ("squabble",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        a.memes["squabble"] = a.memes.get("squabble", 0) + 1
        b.memes["squabble"] = b.memes.get("squabble", 0) + 1
        return ["__squabble__"]
    return []


def _r_sharing(world: World) -> list[str]:
    a = world.get("FriendA")
    b = world.get("FriendB")
    detective = world.get("Detective")
    if detective.memes.get("proof", 0) < THRESHOLD:
        return []
    sig = ("sharing",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["conflict"] = 0.0
    b.memes["conflict"] = 0.0
    a.memes["calm"] = a.memes.get("calm", 0) + 1
    b.memes["calm"] = b.memes.get("calm", 0) + 1
    return ["__sharing__"]


CAUSAL_RULES = [
    Rule("misunderstanding", _r_misunderstanding),
    Rule("squabble", _r_squabble),
    Rule("sharing", _r_sharing),
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


def setup_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)
    hero = world.add(Entity(id="Detective", kind="character", type=params.gender, label=params.name))
    a = world.add(Entity(id="FriendA", kind="character", type="boy", label=params.friend1))
    b = world.add(Entity(id="FriendB", kind="character", type="girl", label=params.friend2))
    smock = world.add(Entity(
        id="Smock",
        type="thing",
        label="smock",
        phrase="a blue smock",
        owner=hero.id,
        caretaker=hero.id,
        plural=False,
    ))
    plank = world.add(Entity(
        id="Plank",
        type="thing",
        label="plank",
        phrase="a wide wooden plank",
        owner="",
        caretaker="",
        plural=False,
    ))
    world.item_positions[smock.id] = plank.id

    hero.memes["curious"] = 1
    hero.memes["clue"] = 1
    a.memes["assumption"] = 1
    b.memes["assumption"] = 1

    world.facts.update(hero=hero, a=a, b=b, smock=smock, plank=plank, params=params)
    return world


def tell(world: World) -> None:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    a = _safe_fact(world, f, "a")
    b = _safe_fact(world, f, "b")
    smock = _safe_fact(world, f, "smock")
    plank = _safe_fact(world, f, "plank")
    place = world.place.name

    world.say(
        f"{hero.label} was a small detective who noticed every clue."
    )
    world.say(
        f"One morning at {place}, {hero.label} spotted {smock.phrase} resting on {plank.phrase}."
    )
    world.say(
        f"{a.label} and {b.label} both reached for it at the same time."
    )

    world.para()
    world.say(
        f"{a.label} thought the smock had been left there for {a.pronoun('object')},"
        f" but {b.label} thought it was waiting for {b.pronoun('object')}."
    )
    a.memes["conflict"] += 1
    b.memes["conflict"] += 1
    propagate(world)

    hero.memes["proof"] += 1
    world.say(
        f"{hero.label} knelt down and checked the plank like a true detective."
    )
    world.say(
        f"Under the smock, {hero.label} found a neat little tag that showed the smock had only been put there to dry."
    )

    world.para()
    propagate(world)

    world.say(
        f'{hero.label} smiled and said, "It was a misunderstanding. No one stole it."'
    )
    world.say(
        f'{hero.label} asked them to share the plank, and {a.label} and {b.label} took turns holding the smock while it dried.'
    )
    world.say(
        f"By the end, the squabble was gone, the smock was safe, and everyone knew to ask before grabbing."
    )

    world.facts["resolved"] = True
    world.facts["squabble"] = a.memes.get("squabble", 0) > 0 or b.memes.get("squabble", 0) > 0


PLACES = {
    "porch": Place(name="the porch", indoor=False, clues={"wood", "dry"}),
    "shed": Place(name="the shed", indoor=True, clues={"tag", "dust"}),
    "dock": Place(name="the dock", indoor=False, clues={"water", "rope"}),
    "yard": Place(name="the yard", indoor=False, clues={"grass", "wind"}),
}

ITEMS = {
    "smock": Item(id="smock", label="smock", phrase="a blue smock", clue="tag"),
    "plank": Item(id="plank", label="plank", phrase="a wide wooden plank", clue="wood"),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava", "Maya"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Ben", "Max", "Eli"]
FRIENDS = [("Jace", "Pia"), ("Owen", "June"), ("Noah", "Ivy"), ("Sam", "Luna"), ("Kai", "Rose")]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_name, place in PLACES.items():
        for clue in place.clues:
            for item_name, item in ITEMS.items():
                if item.clue == clue or item_name == "smock":
                    combos.append((place_name, clue, item_name))
    return sorted(set(combos))


@dataclass
class StoryRegistry:
    pass
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


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a young child about a smock, a plank, and a misunderstanding at {world.place.name}.',
        f"Tell a gentle mystery where {f['hero'].label} investigates why two friends squabbled over a smock.",
        "Write a child-friendly detective story that ends with sharing instead of blaming.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    a = _safe_fact(world, f, "a")
    b = _safe_fact(world, f, "b")
    smock = _safe_fact(world, f, "smock")
    plank = _safe_fact(world, f, "plank")
    return [
        QAItem(
            question=f"What clue did {hero.label} spot at {world.place.name}?",
            answer=f"{hero.label} spotted {smock.phrase} resting on {plank.phrase}. That clue made {hero.label} curious.",
        ),
        QAItem(
            question=f"Why did {a.label} and {b.label} start squabbling?",
            answer=f"They each thought the smock belonged to them, so they both reached for it at once.",
        ),
        QAItem(
            question=f"How did the detective solve the problem?",
            answer=f"{hero.label} checked the plank, found the tag, and showed that it was a misunderstanding. Then the friends shared the plank and waited their turns.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a smock used for?",
            answer="A smock is a cover people wear to help keep clothes clean while they work or play.",
        ),
        QAItem(
            question="What is a plank?",
            answer="A plank is a long flat piece of wood.",
        ),
        QAItem(
            question="Why is sharing helpful?",
            answer="Sharing helps people take turns and avoid squabbles when they both want the same thing.",
        ),
        QAItem(
            question="Why should children ask before taking something?",
            answer="Asking first helps prevent misunderstandings and keeps other people from feeling upset.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  item_positions={world.item_positions}")
    lines.append(f"  fired rules={sorted({x[0] for x in world.fired if x})}")
    return "\n".join(lines)


ASP_RULES = r"""
% A misunderstanding happens when the detective has a clue and both friends make assumptions.
misunderstanding(D) :- clue(D), assumption(a), assumption(b).

% A squabble can happen after mutual conflict.
squabble :- conflict(a), conflict(b).

% Sharing resolves the conflict after the detective provides proof.
sharing :- proof(detective), clue(detective).

% The story is valid only if the setting contains both a smock and a plank clue.
valid_story(P, C, I) :- place(P), clue(C), item(I), compatible(P, C, I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pname, place in PLACES.items():
        lines.append(asp.fact("place", pname))
        if place.indoor:
            lines.append(asp.fact("indoor", pname))
        for c in sorted(place.clues):
            lines.append(asp.fact("clue", pname, c))
    for iname, item in ITEMS.items():
        lines.append(asp.fact("item", iname))
        lines.append(asp.fact("item_clue", iname, item.clue))
    lines.append(asp.fact("compatible", "porch", "wood", "smock"))
    lines.append(asp.fact("compatible", "shed", "tag", "smock"))
    lines.append(asp.fact("compatible", "dock", "water", "smock"))
    lines.append(asp.fact("compatible", "yard", "grass", "smock"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small detective story world about a smock, a plank, and a squabble.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=["wood", "tag", "water", "grass"])
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend1")
    ap.add_argument("--friend2")
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
    if getattr(args, "item", None) and getattr(args, "item", None) != "smock":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "place", None) and getattr(args, "clue", None):
        if getattr(args, "clue", None) not in _safe_lookup(PLACES, getattr(args, "place", None)).clues:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "place", None) and getattr(args, "item", None) and (getattr(args, "place", None), getattr(args, "clue", None) or "tag", getattr(args, "item", None)) not in valid_combos():
        return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "clue", None):
        combos = [c for c in combos if c[1] == getattr(args, "clue", None)]
    if getattr(args, "item", None):
        combos = [c for c in combos if c[2] == getattr(args, "item", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, clue, item = (list(rng.choice(combos)) + [None, None, None])[:3]
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or choose_name(gender, rng)
    friend1 = getattr(args, "friend1", None) or rng.choice([n for n, _ in FRIENDS])
    friend2 = getattr(args, "friend2", None) or rng.choice([n for _, n in FRIENDS])
    return StoryParams(place=place, clue=clue, item=item, name=name, gender=gender, friend1=friend1, friend2=friend2)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


CURATED = [
    StoryParams(place="porch", clue="wood", item="smock", name="Mia", gender="girl", friend1="Jace", friend2="Pia"),
    StoryParams(place="shed", clue="tag", item="smock", name="Leo", gender="boy", friend1="Owen", friend2="June"),
    StoryParams(place="yard", clue="grass", item="smock", name="Nora", gender="girl", friend1="Sam", friend2="Luna"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program("#show valid_story/3."))
        triples = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
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
            header = f"### {p.name}: {p.place} / {p.clue} / {p.item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
