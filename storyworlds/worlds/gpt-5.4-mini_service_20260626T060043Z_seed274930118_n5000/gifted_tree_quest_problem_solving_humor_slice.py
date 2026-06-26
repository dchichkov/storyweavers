#!/usr/bin/env python3
"""
Storyworld: gifted_tree_quest_problem_solving_humor_slice

A small slice-of-life story world about a child who gets a gifted tree and
sets out on a gentle quest to help it settle in, with a little humor and
problem solving along the way.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    planted: bool = False
    watered: bool = False
    sheltered: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    labels: str = ""
    child: object | None = None
    parent: object | None = None
    tree: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    affords: set[str] = field(default_factory=set)
    sun: str = "bright"
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
class Quest:
    id: str
    goal: str
    search: str
    trouble: str
    fix: str
    ending: str
    tag: str = ""
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
class Problem:
    id: str
    label: str
    risk: str
    humorous: str
    solved_by: str
    meter: str
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


@dataclass
class HumorBeat:
    id: str
    setup: str
    punch: str
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
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "garden": Place(name="the garden", indoor=False, affords={"plant", "water", "inspect"}, sun="warm"),
    "backyard": Place(name="the backyard", indoor=False, affords={"plant", "water", "inspect"}, sun="bright"),
    "windowsill": Place(name="the windowsill", indoor=True, affords={"plant", "water", "inspect"}, sun="soft"),
}

QUESTS = {
    "new_tree_home": Quest(
        id="new_tree_home",
        goal="help the gifted tree feel at home",
        search="look for the best spot",
        trouble="the pot was too heavy for one small kid",
        fix="ask for help and use a little cart",
        ending="the tree stood straight and proud in its new spot",
        tag="tree",
    ),
    "sunny_spot": Quest(
        id="sunny_spot",
        goal="find a sunny spot for the gifted tree",
        search="check the light in each corner",
        trouble="one place was sunny but the cat kept claiming it",
        fix="move a stool and nudge the cat aside with a laugh",
        ending="the tree got its sunshine and the cat got a better nap place",
        tag="tree",
    ),
    "drink_and_drain": Quest(
        id="drink_and_drain",
        goal="give the gifted tree enough water without making a muddy puddle",
        search="pour carefully and watch the soil",
        trouble="the watering can made the dirt splash like tiny raindrops",
        fix="slow down and use two small pours instead of one big splash",
        ending="the soil stayed damp, not drippy, and everyone felt clever",
        tag="tree",
    ),
}

PROBLEMS = {
    "heavy_pot": Problem(
        id="heavy_pot",
        label="a heavy pot",
        risk="it could tip and spill dirt all over the floor",
        humorous="the pot looked like it had packed too many snacks",
        solved_by="a cart",
        meter="strain",
    ),
    "crooked_tree": Problem(
        id="crooked_tree",
        label="a wobbly tree",
        risk="it could lean like it was bowing to the rug",
        humorous="the sapling stood like a sleepy ballerina",
        solved_by="a stick tie",
        meter="wobble",
    ),
    "muddy_floor": Problem(
        id="muddy_floor",
        label="muddy drips",
        risk="they could leave prints in the hallway",
        humorous="the floor was trying its best to wear brown shoes",
        solved_by="a towel",
        meter="mess",
    ),
}

HUMOR = {
    "cat_spot": HumorBeat(
        id="cat_spot",
        setup="A cat had already claimed the sunniest patch like it had a lease.",
        punch="The cat blinked once, decided the tree could share, and sat down in the shade instead.",
    ),
    "tiny_cart": HumorBeat(
        id="tiny_cart",
        setup="The little cart rolled in with a squeaky wheel that sounded very proud of itself.",
        punch="It made the serious pot look like it was riding to a party.",
    ),
    "watering_game": HumorBeat(
        id="watering_game",
        setup="Every careful pour made the tree shiver its leaves in a polite way.",
        punch="The child said the tree was doing a tiny happy dance, which was probably true.",
    ),
}

GIRL_NAMES = ["Mia", "Lila", "Zoe", "Nora", "Ava", "Ella", "Ivy", "Luna"]
BOY_NAMES = ["Theo", "Max", "Ben", "Leo", "Finn", "Owen", "Noah", "Eli"]
TRAITS = ["curious", "gentle", "thoughtful", "cheerful", "patient", "spirited"]


@dataclass
class StoryParams:
    place: str
    quest: str
    problem: str
    humor: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------
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


def quest_requires_tree(quest: Quest) -> bool:
    return quest.tag == "tree"


def reasonable_combo(place: Place, quest: Quest, problem: Problem) -> bool:
    if not quest_requires_tree(quest):
        return False
    if place.indoor and problem.id == "muddy_floor":
        return True
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for qid, quest in QUESTS.items():
            for pid, problem in PROBLEMS.items():
                if reasonable_combo(place, quest, problem):
                    out.append((place_id, qid, pid))
    return out


def setup_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        labels="",
        meters={"effort": 0.0},
        memes={"joy": 0.0, "curiosity": 1.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        meters={"effort": 0.0},
        memes={"calm": 1.0},
    ))
    tree = world.add(Entity(
        id="Tree",
        type="tree",
        label="gifted tree",
        phrase="a gifted tree in a clay pot",
        owner=child.id,
        caretaker=parent.id,
        planted=False,
        watered=False,
        sheltered=False,
        meters={"tilt": 0.0, "thirst": 0.0, "mud": 0.0},
        memes={"hope": 1.0},
    ))

    world.facts.update(child=child, parent=parent, tree=tree)
    return world


def _apply_problem(world: World, problem: Problem) -> list[str]:
    out: list[str] = []
    tree = world.get("Tree")
    if problem.id == "heavy_pot" and tree.meters["tilt"] < 1.0:
        sig = ("heavy_pot",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("Parent").meters["effort"] += 1
            out.append("The pot felt heavy, and even the floor seemed to watch.")
    if problem.id == "crooked_tree" and tree.meters["tilt"] >= 1.0:
        sig = ("crooked_tree",)
        if sig not in world.fired:
            world.fired.add(sig)
            tree.meters["tilt"] = 0.0
            out.append("The little tree stopped wobbling once it got a careful tie.")
    if problem.id == "muddy_floor" and tree.meters["mud"] >= 1.0:
        sig = ("muddy_floor",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("A towel handled the muddy drips before they could march indoors.")
    return out


def propagate(world: World, problem: Problem) -> None:
    for line in _apply_problem(world, problem):
        world.say(line)


def tell_story(world: World, quest: Quest, problem: Problem, humor: HumorBeat) -> None:
    child: Entity = _safe_fact(world, world.facts, "child")  # type: ignore[assignment]
    parent: Entity = _safe_fact(world, world.facts, "parent")  # type: ignore[assignment]
    tree: Entity = _safe_fact(world, world.facts, "tree")  # type: ignore[assignment]

    world.say(
        f"{child.id} got a gifted tree and stared at it with big eyes. "
        f"It was small, leafy, and somehow already looked like it had opinions."
    )
    world.say(
        f"{child.id} wanted to {quest.search}, because the job for the day was to "
        f"{quest.goal}."
    )
    world.say(humor.setup)

    world.para()
    world.say(
        f"At {world.place.name}, they found {problem.label}. {problem.humorous}. "
        f"That meant {problem.risk}."
    )
    world.say(
        f"{child.id} tried to solve it by {quest.fix}, while {parent.id} stayed close "
        f"and turned the whole thing into a calm little quest."
    )
    tree.meters["thirst"] += 1.0
    if problem.id == "heavy_pot":
        tree.meters["tilt"] += 1.0
        child.meters["effort"] += 1.0
    elif problem.id == "muddy_floor":
        tree.meters["mud"] += 1.0
    elif problem.id == "crooked_tree":
        tree.meters["tilt"] += 1.0

    propagate(world, problem)

    world.para()
    world.say(
        f"{child.id} smiled when the fix worked. {humor.punch} "
        f"Then they finished the quest: {quest.ending}."
    )
    tree.planted = True
    tree.watered = True
    tree.sheltered = True
    child.memes["joy"] += 1.0
    tree.memes["hope"] += 1.0
    world.say(
        f"In the end, the gifted tree stood safe and neat, and {child.id} felt "
        f"very proud of such a small, successful day."
    )


def generation_prompts(world: World) -> list[str]:
    child: Entity = _safe_fact(world, world.facts, "child")  # type: ignore[assignment]
    quest: Quest = _safe_fact(world, world.facts, "quest")  # type: ignore[assignment]
    return [
        "Write a short slice-of-life story about a gifted tree and a child who has to solve one small problem.",
        f"Tell a gentle quest story where {child.id} helps a gifted tree by {quest.goal}.",
        "Write a humorous story about a family helping a gifted tree settle in without making a fuss.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = _safe_fact(world, world.facts, "child")  # type: ignore[assignment]
    parent: Entity = _safe_fact(world, world.facts, "parent")  # type: ignore[assignment]
    tree: Entity = _safe_fact(world, world.facts, "tree")  # type: ignore[assignment]
    quest: Quest = _safe_fact(world, world.facts, "quest")  # type: ignore[assignment]
    problem: Problem = _safe_fact(world, world.facts, "problem")  # type: ignore[assignment]

    return [
        QAItem(
            question=f"What did {child.id} get at the start of the story?",
            answer=f"{child.id} got a gifted tree, and it became the special thing everyone wanted to help.",
        ),
        QAItem(
            question=f"What was {child.id} trying to do with the tree?",
            answer=f"{child.id} was trying to {quest.goal}. It was a small quest, but it still needed careful thinking.",
        ),
        QAItem(
            question=f"What problem made the day trickier for {child.id} and {parent.id}?",
            answer=f"The tricky part was {problem.label}. {problem.humorous} That was why they had to solve it carefully.",
        ),
        QAItem(
            question=f"How did {child.id} and {parent.id} solve the problem?",
            answer=f"They solved it by {quest.fix}. That simple plan let the gifted tree settle in safely.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the gifted tree was planted, watered, and steady, and {child.id} felt proud and happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tree?",
            answer="A tree is a plant with a trunk, branches, and leaves. Trees can grow big and give shade.",
        ),
        QAItem(
            question="Why do people water a new tree?",
            answer="People water a new tree so its roots can get enough drink to grow strong in its new place.",
        ),
        QAItem(
            question="What does gifted mean?",
            answer="Gifted means given as a gift, which is something kind someone gives to another person.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.planted:
            bits.append("planted=True")
        if e.watered:
            bits.append("watered=True")
        if e.sheltered:
            bits.append("sheltered=True")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
quest(quest(new_tree_home)).
quest(quest(sunny_spot)).
quest(quest(drink_and_drain)).

problem(problem(heavy_pot)).
problem(problem(crooked_tree)).
problem(problem(muddy_floor)).

place(place(garden)).
place(place(backyard)).
place(place(windowsill)).

valid(Place, Quest, Problem) :-
    place(Place), quest(Quest), problem(Problem),
    quest_requires_tree(Quest).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print(" only in Python:", sorted(py - cl))
    print(" only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def valid_story_choices() -> list[tuple[str, str, str]]:
    return valid_combos()


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_story_choices()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "quest", None):
        combos = [c for c in combos if c[1] == getattr(args, "quest", None)]
    if getattr(args, "problem", None):
        combos = [c for c in combos if c[2] == getattr(args, "problem", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, problem = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    humor = getattr(args, "humor", None) or rng.choice(list(HUMOR))
    return StoryParams(place=place, quest=quest, problem=problem, humor=humor,
                       name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    quest = _safe_lookup(QUESTS, params.quest)
    problem = _safe_lookup(PROBLEMS, params.problem)
    humor = HUMOR[params.humor]
    world.facts.update(quest=quest, problem=problem, humor=humor)
    tell_story(world, quest, problem, humor)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="garden", quest="new_tree_home", problem="heavy_pot", humor="tiny_cart",
                name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="backyard", quest="sunny_spot", problem="crooked_tree", humor="cat_spot",
                name="Theo", gender="boy", parent="father", trait="cheerful"),
    StoryParams(place="windowsill", quest="drink_and_drain", problem="muddy_floor", humor="watering_game",
                name="Nora", gender="girl", parent="mother", trait="patient"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life storyworld about a gifted tree and a small quest.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--humor", choices=HUMOR)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} valid combos:")
        for row in triples:
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
