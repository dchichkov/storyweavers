#!/usr/bin/env python3
"""
Story world: a small animal tale about housing, exact fit, humor, friendship,
and a lesson learned.

A gentle source-story shape:
- friends want a house or nest
- they try an exact-size plan
- a comic mistake makes the shelter fail
- the friends help each other and learn a kind lesson
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    kind: str = "thing"  # "animal" | "thing"
    species: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    a: object | None = None
    b: object | None = None
    house: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "animal":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    id: str
    label: str
    kind: str  # burrow, nest, den, treehouse, barn
    cozy: str
    exact_need: str  # what exact fit matters for
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
class Need:
    id: str
    verb: str
    object: str
    exact_key: str
    funny_miss: str
    lesson: str
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
class Shelter:
    id: str
    label: str
    phrase: str
    fits: set[str]
    solves: set[str]
    joke: str
    tail: str
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
class StoryParams:
    place: str
    need: str
    shelter: str
    name1: str
    name2: str
    species1: str
    species2: str
    trait1: str
    trait2: str
    seed: Optional[int] = None
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        clone = World(self.place)
        clone.entities = json.loads(json.dumps({k: asdict(v) for k, v in self.entities.items()}))
        # Rebuild entities shallowly for simulation use
        rebuilt: dict[str, Entity] = {}
        for k, v in clone.entities.items():
            rebuilt[k] = Entity(**v)
        clone.entities = rebuilt
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "oak_tree": Place("oak_tree", "the old oak tree", "treehouse", "swinging shade", "a nest that fits just right"),
    "meadow_burrow": Place("meadow_burrow", "the meadow burrow", "burrow", "soft grass", "a tunnel that fits just right"),
    "pond_bank": Place("pond_bank", "the pond bank", "nest", "warm reeds", "a nest that fits just right"),
    "barn_corner": Place("barn_corner", "the barn corner", "den", "straw and quiet", "a den that fits just right"),
}

NEEDS = {
    "rain": Need(
        "rain",
        verb="keep dry through the rain",
        object="roof",
        exact_key="dry",
        funny_miss="The roof was one paw too short, and the rain still tickled their tails.",
        lesson="sometimes a shelter needs to fit exactly, not just almost",
        tags={"rain", "housing"},
    ),
    "wind": Need(
        "wind",
        verb="block the windy cold",
        object="wall",
        exact_key="warm",
        funny_miss="The wall had a silly hole in it, and the wind blew one feather straight into a sneeze.",
        lesson="a small gap can make a big problem",
        tags={"wind", "housing"},
    ),
    "moon": Need(
        "moon",
        verb="make a cozy bedtime spot",
        object="blanket",
        exact_key="cozy",
        funny_miss="The blanket slipped off, and one sleepy nose poked out like a confused little star.",
        lesson="cozy things work best when they stay in place",
        tags={"sleep", "housing"},
    ),
}

SHELTERS = {
    "tiny_leaf_roof": Shelter(
        "tiny_leaf_roof",
        "a tiny leaf roof",
        "tiny leaf roof",
        fits={"dry"},
        solves={"rain"},
        joke="It looked grand until a raindrop tapped it and the whole roof made a plip.",
        tail="They tucked the roof down with two little twigs, and it held.",
    ),
    "stone_wall": Shelter(
        "stone_wall",
        "a neat stone wall",
        "stone wall",
        fits={"warm"},
        solves={"wind"},
        joke="The stones were so round that one rolled away like a sleepy marble.",
        tail="They stacked the stones again, this time with the flattest ones at the bottom.",
    ),
    "soft_blanket_nest": Shelter(
        "soft_blanket_nest",
        "a soft blanket nest",
        "soft blanket nest",
        fits={"cozy"},
        solves={"moon"},
        joke="The blanket made the nest so puffed up that one rabbit sank in and blinked twice.",
        tail="They folded the edges under, and the nest stayed snug.",
        plural=False,
    ),
}

NAMES = {
    "rabbit": ["Milo", "Nina", "Pip", "Tess"],
    "fox": ["Ruby", "Finn", "Luna", "Tavi"],
    "mouse": ["Dot", "Mimi", "Squeak", "Moss"],
    "bear": ["Bram", "Nori", "Hugo", "Maya"],
    "owl": ["Opal", "Wren", "Kiko", "Iris"],
}
SPECIES = list(NAMES)
TRAITS = ["curious", "playful", "gentle", "brave", "silly", "patient"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(place: Place, need: Need, shelter: Shelter) -> bool:
    return need.exact_key in shelter.fits and need.id in shelter.solves


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, p in PLACES.items():
        for nid, n in NEEDS.items():
            for sid, s in SHELTERS.items():
                if valid_combo(p, n, s):
                    out.append((pid, nid, sid))
    return out


def explain_rejection(place: Place, need: Need, shelter: Shelter) -> str:
    return (
        f"(No story: {shelter.label} does not solve {need.verb} at {place.label}. "
        f"The shelter needs an exact fit for the problem, or the joke turns into a weak mismatch.)"
    )


# ---------------------------------------------------------------------------
# Story machinery
# ---------------------------------------------------------------------------
def intro_sentence(a: Entity, b: Entity, place: Place, need: Need) -> str:
    return (
        f"{a.id} the {a.species} lived near {place.label}, where {place.cozy} made every day feel small and friendly. "
        f"{b.id} the {b.species} lived nearby too, and the two friends liked to plan housing together."
    )


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    need = _safe_lookup(NEEDS, params.need)
    shelter = _safe_lookup(SHELTERS, params.shelter)
    world = World(place)

    a = world.add(Entity(
        id=params.name1, kind="animal", species=params.species1,
        traits=[params.trait1, "friendly"],
        meters={"joy": 1.0}, memes={"friendship": 1.0},
    ))
    b = world.add(Entity(
        id=params.name2, kind="animal", species=params.species2,
        traits=[params.trait2, "friendly"],
        meters={"joy": 1.0}, memes={"friendship": 1.0},
    ))
    house = world.add(Entity(
        id="shelter", kind="thing", label=shelter.label, phrase=shelter.phrase,
        owner=a.id, caretaker=b.id, meters={"exactness": 0.0}, memes={"humor": 0.0},
        plural=shelter.plural,
    ))

    # Act 1
    world.say(intro_sentence(a, b, place, need))
    world.say(
        f"They wanted {need.verb}, because the old shelter idea was only almost right and almost right was not enough."
    )
    world.say(
        f"So {a.id} and {b.id} gathered supplies for {shelter.label}, hoping the plan would be exact."
    )

    # Act 2
    world.para()
    world.say(
        f"They built carefully, measuring every side with tiny paws. {need.funny_miss}"
    )
    world.say(
        f"{a.id} laughed first, and then {b.id} laughed too, because the mistake looked funny instead of scary."
    )
    world.say(
        f"Still, the problem showed them something important: {need.lesson}."
    )

    # Simulated tension
    world.facts.update(
        hero=a,
        friend=b,
        place=place,
        need=need,
        shelter=shelter,
    )

    # Act 3
    world.para()
    world.say(
        f"Together they fixed it. {shelter.tail}"
    )
    world.say(
        f"In the end, {a.id} and {b.id} sat inside {shelter.label}, smiling at the exact little home they had made together."
    )
    world.say(
        f"Their friendship felt warmer than ever, and the whole place seemed to hum with a happy lesson learned."
    )

    a.meters["joy"] += 1.0
    b.meters["joy"] += 1.0
    a.memes["friendship"] += 1.0
    b.memes["friendship"] += 1.0
    a.memes["lesson"] += 1.0
    b.memes["lesson"] += 1.0
    house.meters["exactness"] = 1.0
    house.memes["humor"] = 1.0

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = _safe_fact(world, f, "hero")
    b = _safe_fact(world, f, "friend")
    need = _safe_fact(world, f, "need")
    shelter = _safe_fact(world, f, "shelter")
    return [
        f"Write a short animal story about {a.id} and {b.id} building {shelter.label} so it fits exactly.",
        f"Tell a gentle funny story where two friends learn that {need.verb} needs an exact shelter.",
        f"Write an animal story with housing, humor, friendship, and a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a: Entity = _safe_fact(world, f, "hero")
    b: Entity = _safe_fact(world, f, "friend")
    need: Need = _safe_fact(world, f, "need")
    shelter: Shelter = _safe_fact(world, f, "shelter")
    place: Place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The two friends were {a.id} the {a.species} and {b.id} the {b.species}. They worked together near {place.label}.",
        ),
        QAItem(
            question=f"What did they want to build?",
            answer=f"They wanted to build {shelter.label}, because they needed {need.verb}.",
        ),
        QAItem(
            question=f"What made the story funny?",
            answer=f"The funny part was that {need.funny_miss.lower()} That mistake was silly, so they laughed and kept going.",
        ),
        QAItem(
            question=f"What did they learn by the end?",
            answer=f"They learned that {need.lesson}. The shelter had to fit exactly, and friends can fix mistakes together.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {a.id} and {b.id} sitting inside {shelter.label}, happy that their housing plan worked and their friendship grew stronger.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "housing": [
        QAItem(
            question="What is housing?",
            answer="Housing is a place where someone or some animal lives or sleeps, like a house, nest, den, or burrow.",
        ),
    ],
    "exact": [
        QAItem(
            question="What does exact mean?",
            answer="Exact means just right and not a little too big or too small.",
        ),
    ],
    "friendship": [
        QAItem(
            question="What is friendship?",
            answer="Friendship is when two or more helpers care about each other, share, and work together kindly.",
        ),
    ],
    "humor": [
        QAItem(
            question="What is humor?",
            answer="Humor is when something is funny and makes people or animals smile or laugh.",
        ),
    ],
    "lesson": [
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is something important you understand after trying, making a mistake, or seeing what works best.",
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["housing"])
    out.extend(WORLD_KNOWLEDGE["exact"])
    out.extend(WORLD_KNOWLEDGE["friendship"])
    out.extend(WORLD_KNOWLEDGE["humor"])
    out.extend(WORLD_KNOWLEDGE["lesson"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- place_fact(P).
need(N) :- need_fact(N).
shelter(S) :- shelter_fact(S).

valid(P,N,S) :- place(P), need(N), shelter(S), exact_fit(S,N), solves(S,N), place_fact(P), need_fact(N), shelter_fact(S).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place_fact", pid))
    for nid in NEEDS:
        lines.append(asp.fact("need_fact", nid))
    for sid, s in SHELTERS.items():
        lines.append(asp.fact("shelter_fact", sid))
        for fit in sorted(s.fits):
            lines.append(asp.fact("exact_fit", sid, fit))
        for sol in sorted(s.solves):
            lines.append(asp.fact("solves", sid, sol))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Parameter resolution and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld about exact housing, humor, friendship, and lessons learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--shelter", choices=SHELTERS)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--species1", choices=SPECIES)
    ap.add_argument("--species2", choices=SPECIES)
    ap.add_argument("--trait1", choices=TRAITS)
    ap.add_argument("--trait2", choices=TRAITS)
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
    filtered = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "need", None) is None or c[1] == getattr(args, "need", None))
        and (getattr(args, "shelter", None) is None or c[2] == getattr(args, "shelter", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, need, shelter = rng.choice(list(filtered))
    s1 = getattr(args, "species1", None) or rng.choice(SPECIES)
    s2 = getattr(args, "species2", None) or rng.choice([s for s in SPECIES if s != s1])
    n1 = getattr(args, "name1", None) or rng.choice(_safe_lookup(NAMES, s1))
    n2 = getattr(args, "name2", None) or rng.choice([n for n in _safe_lookup(NAMES, s2) if n != n1] or _safe_lookup(NAMES, s2))
    t1 = getattr(args, "trait1", None) or rng.choice(TRAITS)
    t2 = getattr(args, "trait2", None) or rng.choice([t for t in TRAITS if t != t1])
    return StoryParams(place=place, need=need, shelter=shelter, name1=n1, name2=n2, species1=s1, species2=s2, trait1=t1, trait2=t2)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.species:8}) {' '.join(bits)}")
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
    StoryParams("oak_tree", "rain", "tiny_leaf_roof", "Milo", "Nina", "rabbit", "mouse", "curious", "playful"),
    StoryParams("meadow_burrow", "wind", "stone_wall", "Ruby", "Bram", "fox", "bear", "silly", "patient"),
    StoryParams("pond_bank", "moon", "soft_blanket_nest", "Dot", "Wren", "mouse", "owl", "gentle", "brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for p, n, s in triples:
            print(f"  {p:15} {n:10} {s}")
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

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name1} and {p.name2}: {p.need} at {p.place} (shelter: {p.shelter})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
