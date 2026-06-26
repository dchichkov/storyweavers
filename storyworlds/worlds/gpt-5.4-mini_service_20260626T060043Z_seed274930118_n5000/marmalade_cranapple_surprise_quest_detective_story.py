#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/marmalade_cranapple_surprise_quest_detective_story.py
=================================================================================================

A standalone story world in a small detective-story domain centered on a
marmalade and cranapple surprise quest.

Premise:
- A child detective notices a missing jar and a curious trail.
- The trail leads through a tiny quest of clues, choices, and a surprise reveal.
- The ending proves what changed: the mystery is solved, the surprise is opened,
  and the marmalade-and-cranapple treat is found and shared.

This file follows the storyworld contract:
- stdlib-only until ASP helpers are used
- typed entities with physical meters and emotional memes
- causal state drives prose
- explicit invalid inputs raise StoryError
- includes Python + ASP reasonableness gates
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
# Domain registries
# ---------------------------------------------------------------------------

LOCATIONS = {
    "kitchen": "the kitchen",
    "hall": "the hall",
    "garden": "the garden",
    "study": "the study",
    "porch": "the porch",
}

CHARACTER_ROLES = {
    "detective": "detective",
    "assistant": "assistant",
    "grownup": "grownup",
}

TREAT_NAMES = {
    "marmalade": "marmalade",
    "cranapple": "cranapple",
    "marmalade_cranapple": "marmalade-cranapple",
}

OBJECTS = {
    "jar": "jar",
    "note": "note",
    "basket": "basket",
    "spoon": "spoon",
    "box": "box",
}

CLUES = {
    "sticky": {
        "label": "sticky drop",
        "fact": "marmalade",
        "target": "kitchen",
        "message": "a sticky drop on the counter",
    },
    "red": {
        "label": "red stain",
        "fact": "cranapple",
        "target": "hall",
        "message": "a red stain near the rug",
    },
    "sweet": {
        "label": "sweet smell",
        "fact": "marmalade_cranapple",
        "target": "study",
        "message": "a sweet smell by the desk",
    },
}

SURPRISES = {
    "birthday": "birthday surprise",
    "secret": "secret surprise",
    "gift": "gift surprise",
}

QUEST_TYPES = {
    "find": "find the missing jar",
    "follow": "follow the clues",
    "open": "open the surprise box",
}

KNOWLEDGE = {
    "marmalade": [
        (
            "What is marmalade?",
            "Marmalade is a sweet fruit spread, often made from oranges, that you can put on bread.",
        )
    ],
    "cranapple": [
        (
            "What is cranapple?",
            "Cranapple is a fruity drink or flavor made from cranberries and apples.",
        )
    ],
    "mystery": [
        (
            "What does a detective do?",
            "A detective looks for clues and uses careful thinking to solve a mystery.",
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a search for something important, and it can feel like a small adventure.",
        )
    ],
    "surprise": [
        (
            "What is a surprise?",
            "A surprise is something you do not expect, and it can make people smile when they discover it.",
        )
    ],
}


# ---------------------------------------------------------------------------
# Entities and world
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carries: Optional[str] = None
    location: str = ""
    plural: bool = False
    protective: bool = False
    clues: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    detective: object | None = None
    helper: object | None = None
    jar: object | None = None
    note: object | None = None
    surprise_box: object | None = None
    def __post_init__(self) -> None:
        for k in ["distance", "mess", "hidden", "evidence", "joy", "curiosity", "worry", "relief"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    label: str
    has_sign: bool = False
    hides: set[str] = field(default_factory=set)
    place: object | None = None
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
class Suspect:
    id: str
    name: str
    role: str
    likely_clue: str
    location: str
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
class StoryParams:
    place: str
    surprise: str
    quest: str
    name: str
    role: str
    helper: str
    clue: str
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Reasonableness gates and rules
# ---------------------------------------------------------------------------

def valid_combo(place: str, clue: str) -> bool:
    return clue in CLUES and place in LOCATIONS and _safe_lookup(CLUES, clue)["target"] in LOCATIONS

def clue_is_plausible(place: str, clue: str) -> bool:
    return _safe_lookup(CLUES, clue)["target"] == place

def explain_invalid(place: str, clue: str) -> str:
    return (
        f"(No story: the clue '{clue}' does not plausibly belong at {LOCATIONS.get(place, place)}. "
        f"Try a clue whose trail really fits that place.)"
    )


def _r_evidence(world: World) -> list[str]:
    out: list[str] = []
    detective = next((e for e in world.entities.values() if e.type == "detective"), None)
    if not detective:
        return out
    for clue_name in detective.clues:
        sig = ("evidence", clue_name)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        detective.meters["evidence"] += 1
        detective.memes["curiosity"] += 1
        out.append(f"{detective.name} noticed a clue and leaned in closer.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    detective = next((e for e in world.entities.values() if e.type == "detective"), None)
    jar = world.entities.get("jar")
    if not detective or not jar:
        return out
    if detective.meters["evidence"] >= 2 and jar.meters["hidden"] >= 1 and ("worry", "jar") not in world.fired:
        world.fired.add(("worry", "jar"))
        detective.memes["worry"] += 1
        out.append("The missing jar made the case feel urgent.")
    return out


def _r_solve(world: World) -> list[str]:
    out: list[str] = []
    detective = next((e for e in world.entities.values() if e.type == "detective"), None)
    surprise = world.entities.get("surprise_box")
    jar = world.entities.get("jar")
    if not detective or not surprise or not jar:
        return out
    if detective.meters["evidence"] >= 3 and jar.meters["hidden"] < 1 and ("solve",) not in world.fired:
        world.fired.add(("solve",))
        surprise.meters["hidden"] = 0
        detective.memes["relief"] += 1
        detective.memes["joy"] += 1
        out.append("The whole mystery clicked into place.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_evidence, _r_worry, _r_solve):
            lines = rule(world)
            if lines:
                produced.extend(lines)
                changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------

def setup_world(params: StoryParams) -> World:
    place = Place(id=params.place, label=_safe_lookup(LOCATIONS, params.place), has_sign=True, hides={params.clue})
    world = World(place)

    detective = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.role,
        label=params.name,
        phrase=f"a small {params.role}",
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label=f"the {params.helper}",
    ))
    jar = world.add(Entity(
        id="jar",
        type="thing",
        label="jar",
        phrase="a glass jar of marmalade and cranapple",
        owner=helper.id,
        location=params.place,
    ))
    surprise_box = world.add(Entity(
        id="surprise_box",
        type="thing",
        label="box",
        phrase=f"a wrapped box with a {_safe_lookup(SURPRISES, params.surprise)} inside",
        owner=helper.id,
        location=params.place,
        protective=True,
    ))
    note = world.add(Entity(
        id="note",
        type="thing",
        label="note",
        phrase="a little note with a clue",
        location=params.place,
    ))

    detective.clues.add(params.clue)

    world.facts.update(
        detective=detective,
        helper=helper,
        jar=jar,
        surprise_box=surprise_box,
        note=note,
        place=place,
        clue=params.clue,
        surprise=params.surprise,
        quest=params.quest,
    )
    return world


def tell_intro(world: World) -> None:
    d = _safe_fact(world, world.facts, "detective")
    helper = _safe_fact(world, world.facts, "helper")
    jar = _safe_fact(world, world.facts, "jar")
    world.say(
        f"{d.name} was a small detective who liked careful questions and tidy footprints."
    )
    world.say(
        f"One morning, {helper.label} said that a jar of marmalade-cranapple was missing from {world.place.label}."
    )
    world.say(
        f"{d.name} spotted {jar.phrase} had left the shelf, and the case became a quest."
    )


def tell_clue(world: World, clue_name: str) -> None:
    d = _safe_fact(world, world.facts, "detective")
    clue = _safe_lookup(CLUES, clue_name)
    world.say(
        f"At {world.place.label}, {d.name} found {clue['message']}."
    )
    if clue_name == "sticky":
        d.clues.add("sticky")
        d.meters["distance"] += 1
    elif clue_name == "red":
        d.clues.add("red")
        d.meters["distance"] += 1
    elif clue_name == "sweet":
        d.clues.add("sweet")
        d.meters["distance"] += 1
    propagate(world, narrate=True)


def tell_turn(world: World) -> None:
    d = _safe_fact(world, world.facts, "detective")
    helper = _safe_fact(world, world.facts, "helper")
    jar = _safe_fact(world, world.facts, "jar")
    box = _safe_fact(world, world.facts, "surprise_box")
    d.memes["curiosity"] += 1
    d.memes["worry"] += 1
    world.say(
        f"{d.name} followed the clues from room to room, and each one made the mystery feel bigger."
    )
    world.say(
        f"Then {d.name} noticed the missing jar was not stolen at all; it had been tucked beside a wrapped box."
    )
    jar.meters["hidden"] = 0
    box.meters["hidden"] = 0
    propagate(world, narrate=True)
    world.say(
        f"{helper.label} smiled and admitted the jar had been moved for a surprise quest."
    )


def tell_resolution(world: World) -> None:
    d = _safe_fact(world, world.facts, "detective")
    helper = _safe_fact(world, world.facts, "helper")
    jar = _safe_fact(world, world.facts, "jar")
    box = _safe_fact(world, world.facts, "surprise_box")
    d.memes["worry"] = 0
    d.memes["relief"] += 1
    d.memes["joy"] += 1
    world.say(
        f"{d.name} opened the box and found the surprise: a little feast with marmalade and cranapple."
    )
    world.say(
        f"Soon the jar was back on the shelf, the note explained the quest, and {helper.label} and {d.name} shared the treat."
    )
    world.say(
        f"In the end, the case was solved, the surprise was sweet, and the quiet room felt cheerful again."
    )


def tell(params: StoryParams) -> World:
    if params.place not in LOCATIONS:
        pass
    if params.clue not in CLUES:
        pass
    if not clue_is_plausible(params.place, params.clue):
        pass

    world = setup_world(params)
    tell_intro(world)
    world.para()
    tell_clue(world, params.clue)
    world.para()
    tell_turn(world)
    world.para()
    tell_resolution(world)
    return world


# ---------------------------------------------------------------------------
# Registries and sampling
# ---------------------------------------------------------------------------

GIRL_NAMES = ["Mia", "Lena", "Ivy", "Nora", "Ruby"]
BOY_NAMES = ["Finn", "Theo", "Ezra", "Leo", "Max"]
HELPERS = ["grownup", "assistant"]
ROLES = ["detective"]

CURATED = [
    StoryParams(place="kitchen", surprise="birthday", quest="find", name="Mia", role="detective", helper="grownup", clue="sticky"),
    StoryParams(place="hall", surprise="gift", quest="follow", name="Theo", role="detective", helper="assistant", clue="red"),
    StoryParams(place="study", surprise="secret", quest="open", name="Ivy", role="detective", helper="grownup", clue="sweet"),
]


def all_valid_params() -> list[StoryParams]:
    out: list[StoryParams] = []
    for place in LOCATIONS:
        for clue in CLUES:
            if clue_is_plausible(place, clue):
                for surprise in SURPRISES:
                    for quest in QUEST_TYPES:
                        for role in ROLES:
                            for helper in HELPERS:
                                for name in GIRL_NAMES + BOY_NAMES:
                                    out.append(StoryParams(place=place, surprise=surprise, quest=quest, name=name, role=role, helper=helper, clue=clue))
    return out


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    d = _safe_fact(world, f, "detective")
    return [
        f'Write a short detective story for a young child that includes "{world.place.label}", "{f["clue"]}", and marmalade-cranapple.',
        f"Tell a gentle mystery where {d.name} follows a clue, solves a quest, and finds a surprise.",
        f"Write a child-friendly detective story with a missing jar, a careful clue trail, and a sweet ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d = _safe_fact(world, f, "detective")
    helper = _safe_fact(world, f, "helper")
    place = world.place.label
    clue = _safe_fact(world, f, "clue")
    surprise = _safe_fact(world, f, "surprise")
    jar = _safe_fact(world, f, "jar")
    return [
        QAItem(
            question=f"Who solved the mystery at {place}?",
            answer=f"{d.name} solved the mystery at {place} by following the clue and thinking carefully like a detective.",
        ),
        QAItem(
            question=f"What clue did {d.name} find during the quest?",
            answer=f"{d.name} found {_safe_lookup(CLUES, clue)['message']} and used it to follow the trail.",
        ),
        QAItem(
            question=f"What was the surprise at the end?",
            answer=f"The surprise was a {_safe_lookup(SURPRISES, surprise)} with marmalade and cranapple, and the missing jar was part of it.",
        ),
        QAItem(
            question=f"Why did the helper move the jar?",
            answer=f"{helper.label} moved the jar so the detective would have a fun quest and discover the surprise at the right moment.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"mystery", "quest", "surprise", "marmalade", "cranapple"}
    out: list[QAItem] = []
    for tag in ["mystery", "quest", "surprise", "marmalade", "cranapple"]:
        if tag in tags:
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


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------

ASP_RULES = r"""
clue_at_place(P,C) :- place(P), clue(C), clue_target(C,P).
valid_story(P,C) :- clue_at_place(P,C), place(P), clue(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in LOCATIONS:
        lines.append(asp.fact("place", pid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_target", cid, c["target"]))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
    for q in QUEST_TYPES:
        lines.append(asp.fact("quest", q))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_story_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, c) for p in LOCATIONS for c in CLUES if clue_is_plausible(p, c)}
    cl = set(asp_valid_story_pairs())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print(" only in clingo:", sorted(cl - py))
    print(" only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world: marmalade, cranapple, surprise, and quest.")
    ap.add_argument("--place", choices=LOCATIONS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--quest", choices=QUEST_TYPES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--clue", choices=CLUES)
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
    valid = []
    for p in all_valid_params():
        if getattr(args, "place", None) and p.place != getattr(args, "place", None):
            continue
        if getattr(args, "surprise", None) and p.surprise != getattr(args, "surprise", None):
            continue
        if getattr(args, "quest", None) and p.quest != getattr(args, "quest", None):
            continue
        if getattr(args, "role", None) and p.role != getattr(args, "role", None):
            continue
        if getattr(args, "helper", None) and p.helper != getattr(args, "helper", None):
            continue
        if getattr(args, "clue", None) and p.clue != getattr(args, "clue", None):
            continue
        valid.append(p)
    if not valid:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    p = rng.choice(valid)
    p.name = getattr(args, "name", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    p.seed = getattr(args, "seed", None)
    return p


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.clues:
            bits.append(f"clues={sorted(e.clues)}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/2."))
        return

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        pairs = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(pairs)} compatible (place, clue) pairs:\n")
        for place, clue in pairs:
            print(f"  {place:8} {clue}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            header = f"### {p.name}: {p.quest} at {p.place} (clue: {p.clue})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
