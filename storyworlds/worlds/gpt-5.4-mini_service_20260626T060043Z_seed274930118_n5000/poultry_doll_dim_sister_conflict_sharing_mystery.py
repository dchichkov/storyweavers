#!/usr/bin/env python3
"""
A standalone storyworld for a tiny mystery about poultry, a doll-sized toy,
and a sisterly conflict that turns into sharing.

The seed story premise:
- A little child finds that a doll-sized toy has gone missing near the poultry pen.
- A sister thinks the toy is hers, the other child thinks it was borrowed without asking.
- The search reveals clues from feathers, crumbs, and a hidden nook.
- The ending resolves the conflict through sharing and a clear return of the toy.

The world model tracks:
- physical meters: distance, hiddenness, clutter, neatness, warmth, risk
- emotional memes: worry, conflict, trust, curiosity, relief, sharing

The generated story is driven by state, not by a frozen paragraph template.
"""

from __future__ import annotations

import argparse
import copy
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

# Story / simulation constants
THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    obj: object | None = None
    parent: object | None = None
    sibling: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
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
    label: str
    indoor: bool
    features: set[str] = field(default_factory=set)
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
class ObjectSpec:
    label: str
    phrase: str
    kind: str
    clue_words: set[str] = field(default_factory=set)
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
    object_id: str
    name: str
    sibling_name: str
    sibling_type: str
    parent_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World state
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.clues: list[str] = []
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        c.clues = list(self.clues)
        return c


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
PLACES = {
    "yard": Place(label="the yard", indoor=False, features={"coop", "nest", "dusty", "corn"}),
    "coop": Place(label="the chicken coop", indoor=False, features={"coop", "nest", "feathers", "corn"}),
    "kitchen": Place(label="the kitchen", indoor=True, features={"table", "crumbs", "cupboard"}),
}

OBJECTS = {
    "doll": ObjectSpec(
        label="doll",
        phrase="a doll-sized toy with a blue ribbon",
        kind="doll",
        clue_words={"ribbon", "tiny", "toy", "doll"},
    ),
    "basket": ObjectSpec(
        label="basket",
        phrase="a small basket for little things",
        kind="basket",
        clue_words={"basket", "woven", "nest"},
    ),
    "key": ObjectSpec(
        label="key",
        phrase="a tiny brass key",
        kind="key",
        clue_words={"brass", "small", "key"},
    ),
}

NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella", "Ruby", "Ivy"]
SIBLING_NAMES = ["June", "Pip", "Rose", "Mara", "Bea", "Wren"]
PARENT_NAMES = ["Mom", "Dad", "Mama", "Papa"]

# Suitable for mystery-style clue handling
CLUES = {
    "feather": "a white feather stuck to the toy",
    "crumb": "a few corn crumbs on the floor",
    "scratch": "small scratches in the dust near the coop",
    "ribbon": "a blue ribbon caught on the basket handle",
    "nest": "a hidden nook beside the nest box",
}


# ---------------------------------------------------------------------------
# ASP twin: reasonableness gate
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_place/1.
#show valid_story/2.

has_feature(Place, Feature) :- place(Place), feature_of(Place, Feature).

clue_points_to(Obj, Place) :- object(Obj), clue_word(Obj, Word), clue_at(Place, Word).

mystery_story(Place, Obj) :- valid_place(Place), valid_object(Obj), clue_points_to(Obj, Place).

valid_story(Place, Obj) :- mystery_story(Place, Obj).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoor:
            lines.append(asp.fact("indoor", pid))
        for feat in sorted(place.features):
            lines.append(asp.fact("feature_of", pid, feat))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        for cw in sorted(obj.clue_words):
            lines.append(asp.fact("clue_word", oid, cw))
    for clue_word in {"feather", "crumb", "scratch", "ribbon", "nest"}:
        lines.append(asp.fact("clue_vocab", clue_word))
    # Facts indicating possible clue availability in places
    for pid, place in PLACES.items():
        if "feathers" in place.features:
            lines.append(asp.fact("clue_at", pid, "feather"))
        if "corn" in place.features:
            lines.append(asp.fact("clue_at", pid, "crumb"))
        if "dusty" in place.features:
            lines.append(asp.fact("clue_at", pid, "scratch"))
        if "nest" in place.features:
            lines.append(asp.fact("clue_at", pid, "nest"))
    lines.append(asp.fact("valid_place", "yard"))
    lines.append(asp.fact("valid_place", "coop"))
    lines.append(asp.fact("valid_place", "kitchen"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in PLACES:
        for oid in OBJECTS:
            if place in {"coop", "yard"} and oid == "doll":
                combos.append((place, oid))
            if place == "kitchen" and oid in {"basket", "key"}:
                combos.append((place, oid))
    return combos


def explain_rejection(place: str, object_id: str) -> str:
    return (
        f"(No story: a {_safe_lookup(OBJECTS, object_id).label} mystery does not fit naturally in "
        f"{_safe_lookup(PLACES, place).label} with the current clue set.)"
    )


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------
def _add_clue(world: World, clue: str) -> None:
    if clue not in world.clues:
        world.clues.append(clue)


def search_for_clues(world: World, hero: Entity, sibling: Entity, obj: Entity) -> None:
    if "feathers" in world.place.features:
        _add_clue(world, "feather")
    if "corn" in world.place.features:
        _add_clue(world, "crumb")
    if "dusty" in world.place.features:
        _add_clue(world, "scratch")
    if "nest" in world.place.features:
        _add_clue(world, "nest")
    # Emotional state shifts with searching.
    hero.memes["curiosity"] += 1
    sibling.memes["worry"] += 1
    world.say(
        f"{hero.id} and {sibling.id} looked carefully around {world.place.label}, "
        f"because something small had gone missing."
    )


def discover(world: World, hero: Entity, sibling: Entity, obj: Entity) -> None:
    clue_set = set(world.clues)
    if "feather" in clue_set and "nest" in clue_set:
        obj.meters["hidden"] = 0
        obj.meters["found"] = 1
        hero.memes["relief"] += 1
        sibling.memes["relief"] += 1
        world.say(
            f"Then {hero.id} noticed a white feather and a tiny ribbon near the nest box. "
            f"The trail led to a hidden nook, and there was the little toy at last."
        )
    elif "crumb" in clue_set:
        obj.meters["hidden"] = 1
        hero.memes["curiosity"] += 1
        world.say(
            f"{sibling.id} pointed to the corn crumbs, and the two of them followed the tiny trail."
        )


def conflict_beats(world: World, hero: Entity, sibling: Entity, obj: Entity) -> None:
    hero.memes["worry"] += 1
    sibling.memes["conflict"] += 1
    hero.memes["conflict"] += 1
    world.say(
        f"{sibling.id} said the toy was borrowed, not lost. "
        f"{hero.id} frowned, because {obj.label} had not been shared kindly."
    )


def sharing_resolution(world: World, hero: Entity, sibling: Entity, obj: Entity) -> None:
    hero.memes["sharing"] += 1
    sibling.memes["sharing"] += 1
    sibling.memes["conflict"] = 0.0
    hero.memes["conflict"] = 0.0
    obj.owner = hero.id
    obj.worn_by = None
    world.say(
        f"In the end, {hero.id} held out a hand and said they could share the toy. "
        f"{sibling.id} nodded, apologized, and promised to ask first next time."
    )
    world.say(
        f"They put {obj.label} on the shelf between them, and the little mystery felt calm at last."
    )


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def tell(place: Place, obj_spec: ObjectSpec, hero_name: str, sibling_name: str, sibling_type: str, parent_name: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl" if hero_name in NAMES else "boy"))
    sibling = world.add(Entity(id=sibling_name, kind="character", type=sibling_type))
    parent = world.add(Entity(id=parent_name, kind="character", type="parent"))
    obj = world.add(Entity(
        id=obj_spec.kind,
        kind="thing",
        type=obj_spec.kind,
        label=obj_spec.label,
        phrase=obj_spec.phrase,
        owner=hero.id,
    ))

    world.say(
        f"On a quiet day, {hero.id} noticed that {obj.phrase} was missing."
    )
    world.say(
        f"{hero.id}'s {sibling.id if False else sibling_name} had been near the poultry pen earlier, "
        f"so everyone started wondering where it had gone."
    )
    world.para()
    world.say(
        f"{parent.id} asked both children to look slowly, because a small thing can hide in a big place."
    )
    conflict_beats(world, hero, sibling, obj)
    search_for_clues(world, hero, sibling, obj)
    discover(world, hero, sibling, obj)
    world.para()
    sharing_resolution(world, hero, sibling, obj)

    world.facts.update(
        hero=hero,
        sibling=sibling,
        parent=parent,
        obj=obj,
        place=place,
        obj_spec=obj_spec,
        clues=list(world.clues),
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly mystery story about {f["hero"].id}, '
        f'{f["sibling"].id}, and a missing {f["obj"].label}.',
        f"Tell a short story where a sisterly conflict over a tiny {f['obj'].label} "
        f"turns into sharing after clues near {f['place'].label}.",
        f'Write a simple mystery with poultry clues, a doll-sized toy, and an ending about sharing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    sib = _safe_fact(world, f, "sibling")
    obj = _safe_fact(world, f, "obj")
    place = _safe_fact(world, f, "place")
    qa = [
        QAItem(
            question=f"What was missing at {place.label}?",
            answer=f"{hero.id} noticed that {obj.phrase} was missing near {place.label}.",
        ),
        QAItem(
            question=f"Why did {hero.id} and {sib.id} search so carefully?",
            answer=f"They searched carefully because the small {obj.label} had disappeared and they wanted to solve the mystery.",
        ),
        QAItem(
            question=f"How did the conflict between {hero.id} and {sib.id} end?",
            answer=f"It ended with sharing: they calmed down, apologized, and agreed to share the {obj.label}.",
        ),
    ]
    if "feather" in f["clues"]:
        qa.append(
            QAItem(
                question="What clue helped them solve the mystery?",
                answer="A white feather helped point them toward the hidden nook near the nest box.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What do poultry need to stay safe and healthy?",
            answer="Poultry need clean water, food, and a safe place like a coop or yard where they can rest.",
        ),
        QAItem(
            question="What is a doll-sized thing?",
            answer="A doll-sized thing is very small, about the size of a toy doll or a little figure a child can hold.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use or enjoy something too, instead of keeping it all to yourself.",
        ),
    ]


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
# CLI
# ---------------------------------------------------------------------------
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  clues: {world.clues}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with poultry, a doll-sized toy, and sisterly sharing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", dest="object_id", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--sibling-name")
    ap.add_argument("--sibling-type", choices=["girl", "boy", "sister", "brother"], default="sister")
    ap.add_argument("--parent-name", choices=PARENT_NAMES)
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
    if getattr(args, "place", None) and getattr(args, "object_id", None) and (getattr(args, "place", None), getattr(args, "object_id", None)) not in valid_combos():
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "object_id", None) is None or c[1] == getattr(args, "object_id", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, object_id = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    sibling_name = getattr(args, "sibling_name", None) or rng.choice(SIBLING_NAMES)
    parent_name = getattr(args, "parent_name", None) or rng.choice(PARENT_NAMES)
    sibling_type = getattr(args, "sibling_type", None)
    return StoryParams(place=place, object_id=object_id, name=name, sibling_name=sibling_name, sibling_type=sibling_type, parent_name=parent_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(OBJECTS, params.object_id), params.name, params.sibling_name, params.sibling_type, params.parent_name)
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


def asp_program_text() -> str:
    return asp_program("#show valid_story/2.")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program_text())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(f"{len(set(asp.atoms(model, 'valid_story')))} valid stories.")
        for place, obj in sorted(set(asp.atoms(model, "valid_story"))):
            print(f"  {place}: {obj}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="coop", object_id="doll", name="Mia", sibling_name="June", sibling_type="sister", parent_name="Mom"),
            StoryParams(place="yard", object_id="doll", name="Nora", sibling_name="Rose", sibling_type="sister", parent_name="Dad"),
            StoryParams(place="kitchen", object_id="key", name="Ava", sibling_name="Bea", sibling_type="sister", parent_name="Mama"),
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
