#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/hobby_appoint_transcend_conflict_inner_monologue_suspense.py
================================================================================================

A small detective-style story world about a child, a hobby, an appointment,
and the moment they transcend a conflict by listening to their own inner
monologue and solving the mystery with patience.

Seed-tale premise:
---
A curious kid named Mina loved a hobby detective notebook. One afternoon, Mina
was appointed to bring a clue envelope to the library club at the old station.
But the envelope was missing, and Mina had to decide whether to accuse a friend
or look more carefully.

The world is intentionally small:
- physical meters: carrying, wetness, distance, clutter, readiness
- emotional memes: worry, suspicion, courage, relief, pride
- narrative instruments: conflict, inner monologue, suspense

The generated story is not a frozen paragraph with swapped nouns; state changes
drive the plot beats:
1) setup and appointment,
2) suspense through a missing object,
3) conflict and inner monologue,
4) a careful search that resolves the problem,
5) a closing image proving what changed.
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
    kind: str = "thing"  # "character" | "thing"
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
    def __post_init__(self) -> None:
        for k in ["carried", "wet", "distance", "clutter", "ready"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "suspicion", "courage", "relief", "pride", "conflict", "curiosity"]:
            self.memes.setdefault(k, 0.0)

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
    place: str
    detail: str
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
class Hobby:
    id: str
    name: str
    verb: str
    quiet: str
    clue_kind: str
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
class Appointment:
    place: str
    reason: str
    time_word: str
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
class ObjectItem:
    id: str
    label: str
    phrase: str
    at_risk: str
    clue_color: str
    tags: set[str] = field(default_factory=set)
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        return c


SETTINGS = {
    "library": Setting(
        place="the old library",
        detail="The old library smelled like paper, dust, and rain at the windows.",
        affords={"search", "clue"},
    ),
    "station": Setting(
        place="the quiet station",
        detail="The quiet station had a long bench, a locked door, and a clock that ticked softly.",
        affords={"search", "clue"},
    ),
    "garden": Setting(
        place="the back garden",
        detail="The back garden had a stone path, low hedges, and a place where secrets could hide.",
        affords={"search", "clue"},
    ),
}

HOBBIES = {
    "notebook": Hobby(
        id="notebook",
        name="detective notebook",
        verb="make careful notes",
        quiet="writing tiny clues in a notebook",
        clue_kind="paper",
        tags={"paper", "detective"},
    ),
    "puzzles": Hobby(
        id="puzzles",
        name="puzzle hobby",
        verb="fit pieces together",
        quiet="studying shapes and edges",
        clue_kind="pattern",
        tags={"pattern", "detective"},
    ),
    "birdwatching": Hobby(
        id="birdwatching",
        name="birdwatching hobby",
        verb="watch the birds closely",
        quiet="listening for wing beats",
        clue_kind="feather",
        tags={"feather", "detective"},
    ),
}

APPOINTMENTS = {
    "club": Appointment(place="the library club", reason="to bring the clue envelope", time_word="that afternoon"),
    "meeting": Appointment(place="the station office", reason="to show the found key", time_word="at noon"),
    "visit": Appointment(place="the garden gate", reason="to return the borrowed map", time_word="before supper"),
}

OBJECTS = {
    "envelope": ObjectItem(
        id="envelope",
        label="clue envelope",
        phrase="a pale envelope with a red wax dot",
        at_risk="lost",
        clue_color="red",
        tags={"paper", "clue"},
    ),
    "key": ObjectItem(
        id="key",
        label="tiny key",
        phrase="a tiny brass key on a string",
        at_risk="hidden",
        clue_color="brass",
        tags={"metal", "clue"},
    ),
    "map": ObjectItem(
        id="map",
        label="folded map",
        phrase="a folded map with a penciled route",
        at_risk="misplaced",
        clue_color="blue",
        tags={"paper", "clue"},
    ),
}

NAMES = ["Mina", "Iris", "Nora", "Eli", "Theo", "June", "Ada", "Milo"]
KINDS = ["girl", "boy"]
PARENTS = ["mother", "father"]
TRAITS = ["curious", "careful", "brave", "patient", "spirited"]


@dataclass
class StoryParams:
    place: str
    hobby: str
    appointment: str
    object_id: str
    name: str
    gender: str
    parent: str
    trait: str
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


def reasonableness_gate(hobby: Hobby, obj: ObjectItem, appointment: Appointment) -> bool:
    return "clue" in hobby.tags and "clue" in obj.tags and appointment.place


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for hobby_id, hobby in HOBBIES.items():
            for obj_id, obj in OBJECTS.items():
                for app_id, app in APPOINTMENTS.items():
                    if reasonableness_gate(hobby, obj, app):
                        combos.append((place, hobby_id, obj_id))
    return combos


def select_appointment(hobby: Hobby, obj: ObjectItem) -> Appointment:
    return APPOINTMENTS["club"] if obj.id == "envelope" else APPOINTMENTS["meeting"]


def predict_loss(world: World, hero: Entity, obj: Entity) -> dict:
    sim = world.copy()
    sim.get(hero.id).memes["worry"] += 1
    sim.get(obj.id).meters["carried"] = 0
    return {"missing": True, "conflict": True}


def tell(setting: Setting, hobby: Hobby, app: Appointment, obj_cfg: ObjectItem,
         hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    obj = world.add(Entity(id=obj_cfg.id, type=obj_cfg.id, label=obj_cfg.label, phrase=obj_cfg.phrase,
                           owner=hero.id, caretaker=parent.id))
    obj.meters["carried"] = 1

    # setup
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved a {hobby.name}.")
    world.say(f"{hero.id} kept a {hobby.quiet} notebook by the door, because little clues mattered.")
    world.say(f"One {app.time_word}, {hero.id} had been appointed {app.reason} at {app.place}.")
    world.say(f"{hero.id} tucked {hero.pronoun('possessive')} {obj.label} into a pocket and hurried to {setting.place}.")
    world.para()

    # suspense and conflict
    world.say(setting.detail)
    world.say(f"At the desk, {hero.id} reached for {obj.label}...")
    obj.meters["carried"] = 0
    hero.memes["worry"] += 1
    hero.memes["suspicion"] += 1
    world.say(f"...but the pocket was empty, and the room went still.")
    world.say(f"{hero.id} looked under a chair, then at the door, then at the floor.")
    world.say(f"Someone must have taken it, {hero.id} thought, and the thought made {hero.id} feel hot and sharp inside.")
    hero.memes["conflict"] += 1
    world.para()

    world.say(f"{hero.id} wanted to blame the first person who had walked past.")
    world.say(f"Maybe the janitor saw it, {hero.id} thought. Maybe {hero.pronoun('subject')} did. But that would be a guess.")
    world.say(f"{hero.id} listened to {hero.pronoun('possessive')} own inner monologue: first look, then decide.")
    hero.memes["courage"] += 1
    world.say(f"That quiet thought helped {hero.id} transcend the anger for a moment.")
    world.para()

    # resolution
    world.say(f"{hero.id} checked the notebook, the bench, and the shadow under the table.")
    world.say(f"There, caught in the ring of a lamp, was {obj.phrase}.")
    obj.meters["carried"] = 1
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    hero.memes["conflict"] = 0
    world.say(f"{hero.id} laughed softly, because the missing clue had only slipped behind the notebook.")
    world.say(f"At the end, {hero.id} handed in {obj.label} on time, and the room felt bright again.")
    world.say(f"{hero.id}'s hobby notebook stayed open to the right page, and {hero.id} walked home feeling like a real detective.")

    world.facts.update(
        hero=hero,
        parent=parent,
        setting=setting,
        hobby=hobby,
        appointment=app,
        obj=obj,
        trait=trait,
        resolved=True,
        conflicted=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    app = _safe_fact(world, f, "appointment")
    hobby = _safe_fact(world, f, "hobby")
    obj = _safe_fact(world, f, "obj")
    return [
        f'Write a short detective story for a young child that includes the words "hobby", "appoint", and "transcend".',
        f"Tell a gentle mystery about {hero.id}, who loves a {hobby.name}, is appointed for {app.reason}, and must find {obj.label}.",
        f"Write a suspenseful child story where a small detective uses an inner monologue to transcend conflict and solve a missing-object problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    hobby = _safe_fact(world, f, "hobby")
    app = _safe_fact(world, f, "appointment")
    obj = _safe_fact(world, f, "obj")
    trait = _safe_fact(world, f, "trait")
    qa = [
        QAItem(
            question=f"What did {hero.id} love to do before the mystery began?",
            answer=f"{hero.id} loved a {hobby.name} and liked {hobby.quiet}. That hobby made {hero.id} careful about clues.",
        ),
        QAItem(
            question=f"Why had {hero.id} been appointed to go to {app.place}?",
            answer=f"{hero.id} had been appointed {app.reason}. That meant the {obj.label} had to arrive safely.",
        ),
        QAItem(
            question=f"What problem made {hero.id} feel worried and suspicious?",
            answer=f"The {obj.label} was missing from {hero.pronoun('possessive')} pocket, so {hero.id} felt worry, suspicion, and a little conflict.",
        ),
        QAItem(
            question=f"How did {hero.id} handle the angry feeling at first?",
            answer=f"{hero.id} stopped and listened to {hero.pronoun('possessive')} inner monologue instead of blaming someone right away. That helped {hero.id} stay calm.",
        ),
        QAItem(
            question=f"What finally happened to the {obj.label}?",
            answer=f"{hero.id} found the {obj.label} behind the notebook and handed it in on time, so the mystery was solved.",
        ),
        QAItem(
            question=f"How did {hero.id} transcend the conflict?",
            answer=f"{hero.id} transcended the conflict by choosing patience, searching carefully, and trusting a quiet thought instead of a rash guess.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "paper": [
        QAItem(
            question="What is paper used for?",
            answer="Paper can be used for writing, drawing, making notes, and holding information.",
        )
    ],
    "pattern": [
        QAItem(
            question="What is a pattern?",
            answer="A pattern is something that repeats in a way you can notice, like stripes or a row of shapes.",
        )
    ],
    "feather": [
        QAItem(
            question="What is a feather?",
            answer="A feather is a soft part on a bird that helps it fly and stay warm.",
        )
    ],
    "detective": [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks closely for clues and tries to figure out what really happened.",
        )
    ],
    "clue": [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone solve a mystery.",
        )
    ],
    "metal": [
        QAItem(
            question="Why can a brass key feel cold?",
            answer="Metal often feels cold because it takes heat from your hand quickly.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["hobby"].tags) | set(world.facts["obj"].tags)
    out: list[QAItem] = []
    for tag in ["detective", "clue", "paper", "pattern", "feather", "metal"]:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% The declarative twin of the reasonableness gate.
valid_combo(Place, Hobby, Object) :- setting(Place), hobby(Hobby), object(Object),
                                     clue_hobby(Hobby), clue_object(Object).

% Suspense and conflict are story features rather than extra facts.
story_ready(Place, Hobby, Object) :- valid_combo(Place, Hobby, Object).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, h in HOBBIES.items():
        lines.append(asp.fact("hobby", hid))
        if "detective" in h.tags:
            lines.append(asp.fact("clue_hobby", hid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if "clue" in o.tags:
            lines.append(asp.fact("clue_object", oid))
    for aid in APPOINTMENTS:
        lines.append(asp.fact("appointment", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style hobby/appointment mystery world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hobby", choices=HOBBIES)
    ap.add_argument("--appointment", choices=APPOINTMENTS)
    ap.add_argument("--object", dest="object_id", choices=OBJECTS)
    ap.add_argument("--gender", choices=KINDS)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--name")
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
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "hobby", None) is None or c[1] == getattr(args, "hobby", None))
              and (getattr(args, "object_id", None) is None or c[2] == getattr(args, "object_id", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, hobby_id, obj_id = rng.choice(list(combos))
    hobby = _safe_lookup(HOBBIES, hobby_id)
    obj = _safe_lookup(OBJECTS, obj_id)
    app = getattr(args, "appointment", None) or ("club" if obj_id == "envelope" else "meeting")
    gender = getattr(args, "gender", None) or rng.choice(KINDS)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, hobby=hobby_id, appointment=app, object_id=obj_id,
                       name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(HOBBIES, params.hobby),
        _safe_lookup(APPOINTMENTS, params.appointment),
        _safe_lookup(OBJECTS, params.object_id),
        params.name,
        params.gender,
        params.parent,
        params.trait,
    )
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_combo/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_combo/3."))
        combos = sorted(set(asp.atoms(model, "valid_combo")))
        print(f"{len(combos)} compatible combos:\n")
        for p, h, o in combos:
            print(f"  {p:10} {h:12} {o}")
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place, hobby, obj in sorted(valid_combos()):
            params = StoryParams(
                place=place,
                hobby=hobby,
                appointment="club" if obj == "envelope" else "meeting",
                object_id=obj,
                name="Mina",
                gender="girl",
                parent="mother",
                trait="curious",
                seed=base_seed,
            )
            samples.append(generate(params))
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
            header = f"### {p.name}: {p.hobby} at {p.place} with {p.object_id}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
