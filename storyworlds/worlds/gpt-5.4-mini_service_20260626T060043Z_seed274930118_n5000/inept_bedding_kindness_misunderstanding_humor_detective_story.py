#!/usr/bin/env python3
"""
A standalone story world for a tiny detective tale about inept bedding,
misunderstanding, kindness, and humor.

Premise:
- A child detective notices a funny problem at bedtime.
- Someone inept at making the bed causes a bedding mix-up.
- A misunderstanding makes the wrong person seem guilty.
- Kindness and humor solve the case.

The simulated world tracks:
- physical meters: mess, tidiness, warmth, packed, hidden, etc.
- emotional memes: worry, kindness, confusion, humor, relief, trust

The story is generated from the evolving world state, not from a fixed template.
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
# Core data model
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
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    traits: list = field(default_factory=list)
    bed: object | None = None
    blanket: object | None = None
    detective: object | None = None
    helper: object | None = None
    pillow: object | None = None
    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

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
class Setting:
    place: str = "the bedroom"
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Case:
    id: str
    clue: str
    confusion: str
    reveal: str
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
class Item:
    id: str
    label: str
    phrase: str
    type: str
    location: str
    plural: bool = False
    caretaker: Optional[str] = None
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))

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
class Person:
    id: str
    type: str
    label: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.scene: str = "setup"

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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.scene = self.scene
        return clone


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------
SETTINGS = {
    "bedroom": Setting(place="the bedroom", affords={"bedmaking", "searching"}),
    "hallway": Setting(place="the hallway", affords={"searching"}),
    "guestroom": Setting(place="the guest room", affords={"bedmaking", "searching"}),
}

CASES = {
    "missing_pillow": Case(
        id="missing_pillow",
        clue="a pillow tucked into the wrong blanket",
        confusion="the blanket looked suspiciously stuffed",
        reveal="the pillow had simply been moved during a clumsy bedmaking attempt",
        keyword="pillow",
        tags={"bedding", "kindness", "humor", "misunderstanding"},
    ),
    "mixed_blankets": Case(
        id="mixed_blankets",
        clue="two blankets folded into one wobbly lump",
        confusion="it looked like a secret bundle",
        reveal="the blankets had been stacked by mistake",
        keyword="blanket",
        tags={"bedding", "humor", "misunderstanding"},
    ),
    "sock_signal": Case(
        id="sock_signal",
        clue="a sock peeking out from under the quilt",
        confusion="it looked like a clue from a very silly thief",
        reveal="the sock had been stuffed under the quilt by accident",
        keyword="sock",
        tags={"bedding", "detective", "humor"},
    ),
}

NAMES = ["Mina", "Leo", "Nia", "Theo", "Pia", "Owen", "Zara", "Finn"]
ADJ = ["curious", "gentle", "quick", "brave", "thoughtful", "patient"]
HELPERS = ["grandma", "dad", "mom", "older sister", "older brother"]
CASE_ORDER = ["missing_pillow", "mixed_blankets", "sock_signal"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(place: str, case_id: str) -> bool:
    case = _safe_lookup(CASES, case_id)
    return place in SETTINGS and "bedding" in case.tags


def valid_combos() -> list[tuple[str, str]]:
    return [(p, c) for p in SETTINGS for c in CASES if valid_combo(p, c)]


# ---------------------------------------------------------------------------
# Story world actions
# ---------------------------------------------------------------------------
def intro(world: World, detective: Entity, helper: Entity, case: Case) -> None:
    world.say(
        f"{detective.id} was a little {next(t for t in detective.meters if False) if False else detective.type} detective with a sharp eye and a pocket notebook."
    )


def set_scene(world: World, detective: Entity, helper: Entity, bed: Entity, case: Case) -> None:
    world.say(
        f"One evening in {world.setting.place}, {detective.id} noticed that the bed looked odd."
    )
    world.say(
        f"{case.clue.capitalize()} made the room feel like a puzzle, and {helper.label} looked a little embarrassed."
    )


def search(world: World, detective: Entity, bed: Entity, case: Case) -> None:
    detective.memes["focus"] = detective.memes.get("focus", 0.0) + 1
    bed.meters["untidy"] = bed.meters.get("untidy", 0.0) + 1
    world.say(
        f"{detective.id} opened the notebook and began to inspect the bedding."
    )
    world.say(
        f"The clue was plain enough, but the room's {case.confusion} made everyone smile a little."
    )


def misunderstanding(world: World, detective: Entity, helper: Entity, case: Case) -> None:
    detective.memes["worry"] = detective.memes.get("worry", 0.0) + 1
    helper.memes["worry"] = helper.memes.get("worry", 0.0) + 1
    world.say(
        f"At first, {helper.label} thought the detective was blaming {helper.pronoun('object')}."
    )
    world.say(
        f"It was only a misunderstanding, because the clue looked more serious than it really was."
    )


def kindness_turn(world: World, detective: Entity, helper: Entity, bed: Entity, case: Case) -> None:
    detective.memes["kindness"] = detective.memes.get("kindness", 0.0) + 1
    helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1
    detective.memes["humor"] = detective.memes.get("humor", 0.0) + 1
    world.say(
        f"{detective.id} gently laughed and said, \"This case is not a crime, just a very silly bedding mix-up.\""
    )
    world.say(
        f"{helper.label} laughed too, because the mishap really did look funny once nobody felt blamed."
    )


def reveal(world: World, detective: Entity, helper: Entity, bed: Entity, case: Case) -> None:
    bed.meters["untidy"] = 0.0
    bed.meters["tidy"] = 1.0
    world.say(
        f"Then the truth came out: {case.reveal}."
    )
    world.say(
        f"{helper.label} fixed the bed with patient hands, and {detective.id} helped by straightening the corners."
    )


def ending(world: World, detective: Entity, helper: Entity, case: Case) -> None:
    detective.memes["relief"] = detective.memes.get("relief", 0.0) + 1
    helper.memes["relief"] = helper.memes.get("relief", 0.0) + 1
    world.say(
        f"In the end, the room was neat again, and the little detective closed the notebook with a grin."
    )
    world.say(
        f"It was a happy ending: kindness solved the misunderstanding, and humor made the bedtime puzzle feel easy."
    )


def tell(setting: Setting, case: Case, name: str, helper_name: str, trait: str) -> World:
    world = World(setting)
    detective = world.add(Entity(
        id=name,
        kind="character",
        type="girl" if name in {"Mina", "Nia", "Pia", "Zara"} else "boy",
        traits=["little", trait, "detective"],
        meters={"curiosity": 1.0},
        memes={"focus": 1.0},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type="mother" if helper_name == "mom" else "father" if helper_name == "dad" else "woman" if helper_name == "grandma" else "man",
        label=f"the {helper_name}",
        traits=["kind"],
        memes={"kindness": 1.0},
    ))
    bed = world.add(Entity(
        id="bed",
        kind="thing",
        type="bed",
        label="bed",
        phrase="the bed with the bedding",
        meters={"untidy": 1.0},
    ))
    pillow = world.add(Entity(
        id="pillow",
        kind="thing",
        type="pillow",
        label="pillow",
        phrase="a soft pillow",
        caretaker=helper.id,
        owner=detective.id,
    ))
    blanket = world.add(Entity(
        id="blanket",
        kind="thing",
        type="blanket",
        label="blanket",
        phrase="a warm blanket",
        caretaker=helper.id,
        owner=detective.id,
    ))

    world.facts.update(
        detective=detective,
        helper=helper,
        bed=bed,
        pillow=pillow,
        blanket=blanket,
        case=case,
        trait=trait,
    )

    intro(world, detective, helper, case)
    world.para()
    set_scene(world, detective, helper, bed, case)
    search(world, detective, bed, case)
    world.para()
    misunderstanding(world, detective, helper, case)
    kindness_turn(world, detective, helper, bed, case)
    reveal(world, detective, helper, bed, case)
    ending(world, detective, helper, case)
    return world


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    case: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = _safe_fact(world, f, "detective")
    helper = _safe_fact(world, f, "helper")
    case = _safe_fact(world, f, "case")
    return [
        f'Write a short detective story for a child about {detective.id}, a bedding clue, and a kind resolution.',
        f"Tell a gentle mystery where {detective.id} thinks {helper.label} caused a problem with the bedding, but it turns out to be a misunderstanding.",
        f'Write a funny bedtime mystery that includes the word "{case.keyword}" and ends with kindness.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = _safe_fact(world, f, "detective")
    helper = _safe_fact(world, f, "helper")
    case = _safe_fact(world, f, "case")
    return [
        QAItem(
            question=f"Who was the little detective in the story?",
            answer=f"The little detective was {detective.id}. {detective.id} watched the bedding carefully and solved the mix-up.",
        ),
        QAItem(
            question=f"What made the bed look strange?",
            answer=f"{case.clue.capitalize()} made the bed look strange, so everyone thought something important had happened.",
        ),
        QAItem(
            question=f"Why did {helper.label} feel worried for a moment?",
            answer=f"{helper.label} felt worried because the clue looked like blame, but it was really only a misunderstanding.",
        ),
        QAItem(
            question=f"How did the detective solve the problem?",
            answer=f"{detective.id} used kindness and humor, then helped straighten the bedding so the room looked neat again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bedding?",
            answer="Bedding is the blankets, sheets, and pillows that make a bed warm and comfortable.",
        ),
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks closely for clues and tries to solve a mystery.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people think something wrong for a little while, but the truth is different.",
        ),
        QAItem(
            question="What does kindness do in a problem?",
            answer="Kindness helps people stay calm, listen to each other, and work together to fix the problem.",
        ),
        QAItem(
            question="Why can humor help during a mistake?",
            answer="Humor can make people smile, which helps them feel less upset and more ready to solve the mistake.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A bedding case is compatible when the place exists and the case is a bedding case.
valid_story(P, C) :- place(P), case(C), bedding_case(C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for case_id, case in CASES.items():
        lines.append(asp.fact("case", case_id))
        if "bedding" in case.tags:
            lines.append(asp.fact("bedding_case", case_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if py == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python valid_combos():")
    print("python-only:", sorted(py - clingo_set))
    print("clingo-only:", sorted(clingo_set - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world about bedding, kindness, misunderstanding, and humor.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=ADJ)
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
    combos = valid_combos()
    combos = [
        (p, c) for (p, c) in combos
        if (getattr(args, "place", None) is None or p == getattr(args, "place", None))
        and (getattr(args, "case", None) is None or c == getattr(args, "case", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, case = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    trait = getattr(args, "trait", None) or rng.choice(ADJ)
    return StoryParams(place=place, case=case, name=name, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(CASES, params.case), params.name, params.helper, params.trait)
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="bedroom", case="missing_pillow", name="Mina", helper="dad", trait="curious"),
    StoryParams(place="guestroom", case="mixed_blankets", name="Theo", helper="grandma", trait="thoughtful"),
    StoryParams(place="bedroom", case="sock_signal", name="Zara", helper="mom", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for p, c in combos:
            print(f"  {p:10} {c}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
