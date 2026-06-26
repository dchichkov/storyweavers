#!/usr/bin/env python3
"""
A small heartwarming storyworld about an illustrator, a tag, and a doodad.

Premise:
- An illustrator makes a little doodad for someone they care about.
- The doodad ships with a blank tag.
- Curiosity leads to a gentle problem: the tag is plain and not very personal.
- A warm helper move turns the blank tag into a meaningful keepsake.

The world tracks both physical state (meters) and emotional state (memes).
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

# Physical thresholds
THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entities and world model
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
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt", "sister"}
        male = {"boy", "man", "father", "uncle", "brother"}
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
    indoor: bool
    affords: set[str] = field(default_factory=set)
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
class ThingSpec:
    id: str
    label: str
    phrase: str
    region: str
    type: str = "thing"
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
    doodad: str
    tag: str
    name: str
    gender: str
    helper: str
    trait: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_log: list[str] = []

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
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

PLACES = {
    "studio": Place(name="the studio", indoor=True, affords={"draw", "label"}),
    "library": Place(name="the library corner", indoor=True, affords={"draw", "label"}),
    "porch": Place(name="the porch", indoor=False, affords={"draw", "label"}),
    "sunroom": Place(name="the sunroom", indoor=True, affords={"draw", "label"}),
}

DOODADS = {
    "tiny_box": ThingSpec(
        id="tiny_box",
        label="doodad",
        phrase="a tiny hand-painted doodad",
        region="desk",
    ),
    "bracelet_charm": ThingSpec(
        id="bracelet_charm",
        label="doodad",
        phrase="a little charm-like doodad",
        region="palm",
    ),
    "bird_pin": ThingSpec(
        id="bird_pin",
        label="doodad",
        phrase="a bright bird-shaped doodad",
        region="jacket",
    ),
}

TAGS = {
    "blank_tag": ThingSpec(
        id="blank_tag",
        label="tag",
        phrase="a blank paper tag",
        region="desk",
    ),
    "gift_tag": ThingSpec(
        id="gift_tag",
        label="tag",
        phrase="a soft cream gift tag",
        region="palm",
    ),
    "name_tag": ThingSpec(
        id="name_tag",
        label="tag",
        phrase="a little name tag with a ribbon hole",
        region="jacket",
    ),
}

GENDERS = ["girl", "boy"]
HELPERS = ["mother", "father", "grandparent", "aunt", "uncle"]
TRAITS = ["curious", "gentle", "bright-eyed", "patient", "kind"]


# ---------------------------------------------------------------------------
# ASP twin and reasonableness gate
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A doodad story is reasonable when curiosity makes the illustrator notice
% a tag that needs a personal touch.

at_risk(D, T) :- doodad(D), tag(T), same_place(D, T), blank(T).
can_help(D, T) :- at_risk(D, T), has_pen(D), label_makes_sense(D, T).

valid_story(P, D, T) :- place(P), doodad(D), tag(T), affords(P, draw), at_risk(D, T), can_help(D, T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoor:
            lines.append(asp.fact("indoor", pid))
        for act in sorted(place.affords):
            lines.append(asp.fact("affords", pid, act))

    for did, d in DOODADS.items():
        lines.append(asp.fact("doodad", did))
        lines.append(asp.fact("same_place", did, d.region))
        lines.append(asp.fact("has_pen", did))
        lines.append(asp.fact("label_makes_sense", did, "blank_tag"))

    for tid, t in TAGS.items():
        lines.append(asp.fact("tag", tid))
        lines.append(asp.fact("same_place", tid, t.region))
        if tid == "blank_tag":
            lines.append(asp.fact("blank", tid))

    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in Python:", sorted(py - cl))
    print("only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------

def maybe_blank_tag(world: World, tag: Entity) -> bool:
    return tag.type == "tag" and tag.label == "tag" and tag.phrase.startswith("a blank")


def curiosity_strike(world: World, hero: Entity, doodad: Entity, tag: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} noticed the little {doodad.label} and turned the {tag.label} over and over in {hero.pronoun('possessive')} hands."
    )
    world.say(
        f"{hero.pronoun().capitalize()} felt curious because the {tag.label} looked like it was waiting to tell a story."
    )


def problem(world: World, hero: Entity, helper: Entity, doodad: Entity, tag: Entity) -> None:
    if maybe_blank_tag(world, tag):
        hero.memes["soft_worry"] += 1
        world.say(
            f"But the {tag.label} was still blank, and that made the {doodad.label} feel a little unfinished."
        )
        world.say(
            f"{hero.pronoun('possessive').capitalize()} {helper.type if helper.type else 'helper'} smiled, but {hero.id} kept peeking at the empty space where a name should go."
        )


def turn(world: World, hero: Entity, helper: Entity, doodad: Entity, tag: Entity) -> None:
    hero.memes["idea"] += 1
    tag.meters["written_on"] = 1
    tag.phrase = f"a tag with {hero.id}'s neat drawing and a warm little note"
    world.say(
        f"Then {hero.id} got an idea: {hero.pronoun()} could draw a tiny picture on the {tag.label} and write a note that felt like a hug."
    )
    world.say(
        f"Together, {hero.id} and {helper.id} made the {tag.label} fit the {doodad.label} perfectly."
    )


def resolution(world: World, hero: Entity, helper: Entity, doodad: Entity, tag: Entity) -> None:
    hero.memes["joy"] += 1
    helper.memes["pride"] += 1
    tag.meters["hung"] = 1
    doodad.meters["gifted"] = 1
    world.say(
        f"At last, the {doodad.label} was ready to give away, with the new {tag.label} swinging from it like a tiny promise."
    )
    world.say(
        f"{hero.id} and {helper.id} looked at it and smiled, because the little gift now felt personal and full of care."
    )


def tell(place: Place, params: StoryParams) -> World:
    world = World(place)
    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=params.gender,
            traits=["little", params.trait],
            meters={},
            memes={"curiosity": 0.0},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper.title(),
            kind="character",
            type=params.helper,
            label=params.helper,
            memes={"kindness": 1.0},
        )
    )
    doodad_spec = _safe_lookup(DOODADS, params.doodad)
    tag_spec = _safe_lookup(TAGS, params.tag)
    doodad = world.add(
        Entity(
            id=doodad_spec.id,
            type="doodad",
            label=doodad_spec.label,
            phrase=doodad_spec.phrase,
            owner=hero.id,
            carried_by=hero.id,
        )
    )
    tag = world.add(
        Entity(
            id=tag_spec.id,
            type="tag",
            label=tag_spec.label,
            phrase=tag_spec.phrase,
            owner=hero.id,
        )
    )

    world.say(
        f"{hero.id} was a {params.trait} little {params.gender} who worked as an illustrator in {place.name}."
    )
    world.say(
        f"{hero.id} loved making tiny pictures and decorating a special {doodad.label} for people they cared about."
    )
    world.para()
    world.say(
        f"One day, {hero.id} found a {tag.label} beside the {doodad.label}, and the tag was blank."
    )
    curiosity_strike(world, hero, doodad, tag)
    problem(world, hero, helper, doodad, tag)
    world.para()
    turn(world, hero, helper, doodad, tag)
    resolution(world, hero, helper, doodad, tag)

    world.facts = {
        "hero": hero,
        "helper": helper,
        "doodad": doodad,
        "tag": tag,
        "place": place,
        "params": params,
    }
    return world


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for doodad_id in DOODADS:
            for tag_id in TAGS:
                if place.affords and "draw" in place.affords:
                    combos.append((place_id, doodad_id, tag_id))
    # Keep only the actual intended story shape: a blank tag and a doodad.
    return [c for c in combos if c[2] == "blank_tag"]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    doodad = _safe_fact(world, f, "doodad")
    tag = _safe_fact(world, f, "tag")
    place = _safe_fact(world, f, "place")
    return [
        f"Write a heartwarming story about an illustrator named {hero.id} in {place.name} who finds a blank {tag.label} for a {doodad.label}.",
        f"Tell a gentle story where curiosity helps {hero.id} turn a plain {tag.label} into something meaningful.",
        f"Create a child-friendly story about an illustrator, a tag, and a doodad that ends with a warm shared smile.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    doodad = _safe_fact(world, f, "doodad")
    tag = _safe_fact(world, f, "tag")
    place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who is the story about in {place.name}?",
            answer=f"It is about {hero.id}, a curious illustrator who likes making special things with care.",
        ),
        QAItem(
            question=f"What made {hero.id} pause when {hero.id} saw the {doodad.label}?",
            answer=f"{hero.id} paused because the {tag.label} was blank, so the {doodad.label} did not feel finished yet.",
        ),
        QAItem(
            question=f"What did {hero.id} and {helper.id} do to help the {doodad.label} feel complete?",
            answer=f"They decorated the {tag.label} with a small drawing and a warm note, which made the {doodad.label} feel personal and loved.",
        ),
        QAItem(
            question=f"How did {hero.id} feel when the {tag.label} was still empty?",
            answer=f"{hero.id} felt curious first and then a little worried, because the blank tag seemed to be waiting for a name and a kind message.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The blank tag became a gentle keepsake, and the doodad was ready to be given away with care.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "illustrator": [
        QAItem(
            question="What does an illustrator do?",
            answer="An illustrator makes pictures that help tell a story or make a message look lively and special.",
        )
    ],
    "tag": [
        QAItem(
            question="What is a tag used for?",
            answer="A tag can hold a name, a note, or a little message so something feels labeled and personal.",
        )
    ],
    "doodad": [
        QAItem(
            question="What is a doodad?",
            answer="A doodad is a small object, often a fun or decorative one that people like to keep or give as a gift.",
        )
    ],
    "curiosity": [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to look closer, ask questions, and learn more.",
        )
    ],
    "heartwarming": [
        QAItem(
            question="What makes a story heartwarming?",
            answer="A heartwarming story leaves you feeling warm inside because people are kind, caring, and thoughtful with each other.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        item
        for key in ["illustrator", "tag", "doodad", "curiosity", "heartwarming"]
        for item in WORLD_KNOWLEDGE[key]
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI / serialization
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"{e.id} ({e.type}) " + " ".join(bits))
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming storyworld about an illustrator, a tag, and a doodad.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--doodad", choices=DOODADS)
    ap.add_argument("--tag", choices=TAGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "tag", None) and getattr(args, "tag", None) != "blank_tag":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    doodad = getattr(args, "doodad", None) or rng.choice(list(DOODADS))
    tag = getattr(args, "tag", None) or "blank_tag"
    gender = getattr(args, "gender", None) or rng.choice(GENDERS)
    name = getattr(args, "name", None) or rng.choice(["Mina", "Leo", "Ivy", "Noah", "Sage", "Luna"])
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, doodad=doodad, tag=tag, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), params)
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
# ASP display helpers
# ---------------------------------------------------------------------------

def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_program_with_show() -> str:
    return asp_program("#show valid_story/3.")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program_with_show())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="studio", doodad="tiny_box", tag="blank_tag", name="Mina", gender="girl", helper="mother", trait="curious"),
            StoryParams(place="library", doodad="bracelet_charm", tag="blank_tag", name="Leo", gender="boy", helper="father", trait="gentle"),
            StoryParams(place="sunroom", doodad="bird_pin", tag="blank_tag", name="Ivy", gender="girl", helper="aunt", trait="kind"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
            header = f"### {p.name} / {p.doodad} / {p.tag}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
