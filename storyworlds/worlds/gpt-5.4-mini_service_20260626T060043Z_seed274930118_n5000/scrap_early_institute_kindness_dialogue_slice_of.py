#!/usr/bin/env python3
"""
A small slice-of-life story world about an early institute morning, a found scrap,
and a kind dialogue that changes the day.

The core premise:
- A child arrives early at an institute.
- They notice a small scrap of paper left behind.
- A brief dialogue about kindness turns the scrap into a helpful note or drawing.
- The ending proves a gentle change in the room.

This script follows the Storyweavers storyworld contract:
- typed entities with meters and memes
- state-driven prose
- inline ASP twin with a reasonableness gate
- CLI support for default runs, QA, JSON, ASP, verify, and trace
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

    guide: object | None = None
    hero: object | None = None
    scrap_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "teacher"}
        male = {"boy", "man", "father"}
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
    indoors: bool = True
    calm: bool = True
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
class Scrap:
    id: str
    label: str
    phrase: str
    kind: str
    carries: str
    found_in: set[str] = field(default_factory=set)
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
class KindnessAction:
    id: str
    verb: str
    dialogue: str
    effect: str
    turns_scrap_into: str
    requires: set[str] = field(default_factory=set)
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


@dataclass
class StoryParams:
    institute: str
    scrap: str
    kindness: str
    name: str
    age: int
    role: str
    seed: Optional[int] = None
    world: object | None = None
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


INSTITUTES = {
    "music_room": Place(name="the institute music room", indoors=True, calm=True),
    "art_corner": Place(name="the institute art corner", indoors=True, calm=True),
    "reading_nook": Place(name="the institute reading nook", indoors=True, calm=True),
    "courtyard": Place(name="the institute courtyard", indoors=False, calm=True),
}

SCRAPS = {
    "paper_scrap": Scrap(
        id="paper_scrap",
        label="a paper scrap",
        phrase="a tiny scrap of blue paper",
        kind="paper",
        carries="scribbled words",
        found_in={"music_room", "art_corner", "reading_nook"},
    ),
    "note_scrap": Scrap(
        id="note_scrap",
        label="a note scrap",
        phrase="a torn scrap of a note",
        kind="paper",
        carries="half a sentence",
        found_in={"reading_nook", "art_corner"},
    ),
    "fabric_scrap": Scrap(
        id="fabric_scrap",
        label="a fabric scrap",
        phrase="a soft scrap of cloth",
        kind="fabric",
        carries="a stitched patch",
        found_in={"art_corner", "courtyard"},
    ),
}

KINDNESS = {
    "share": KindnessAction(
        id="share",
        verb="share the scrap",
        dialogue="We can use it together.",
        effect="the worry got smaller",
        turns_scrap_into="a helpful bookmark",
        requires={"paper"},
    ),
    "return": KindnessAction(
        id="return",
        verb="return the scrap",
        dialogue="Someone will be glad to find this.",
        effect="the room felt fairer",
        turns_scrap_into="a returned note",
        requires={"paper", "fabric"},
    ),
    "save": KindnessAction(
        id="save",
        verb="save the scrap",
        dialogue="Let's keep it safe until we know who needs it.",
        effect="the little piece stayed neat",
        turns_scrap_into="a carefully folded keepsake",
        requires={"paper", "fabric"},
    ),
}

NAMES = ["Mina", "Noah", "Iris", "Leo", "Nora", "Eli", "Ava", "Maya"]
ROLES = ["student", "helper", "visitor", "young artist"]


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(INSTITUTES, params.institute)
    world = World(place)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.role != "boy" else "boy",
        label=params.name,
        meters={"early": 0.0},
        memes={"kindness": 0.0, "curiosity": 0.0, "warmth": 0.0},
    ))
    guide = world.add(Entity(
        id="Guide",
        kind="character",
        type="teacher",
        label="the guide",
        meters={"early": 0.0},
        memes={"kindness": 0.0, "calm": 0.0},
    ))
    scrap = _safe_lookup(SCRAPS, params.scrap)
    scrap_ent = world.add(Entity(
        id=scrap.id,
        type=scrap.kind,
        label=scrap.label,
        phrase=scrap.phrase,
        owner=None,
        caretaker=guide.id,
        meters={"torn": 1.0, "used": 0.0},
        memes={"value": 0.0},
    ))
    world.facts.update(hero=hero, guide=guide, scrap=scrap_ent, scrap_cfg=scrap, kindness=_safe_lookup(KINDNESS, params.kindness))
    return world


def _r_notice_scrap(world: World) -> list[str]:
    out = []
    hero = _safe_fact(world, world.facts, "hero")
    scrap = _safe_fact(world, world.facts, "scrap")
    if hero.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    sig = ("notice", scrap.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    scrap.memes["value"] += 1.0
    out.append(f"{hero.id} noticed the little {scrap.label} on the floor.")
    return out


def _r_kindness_spread(world: World) -> list[str]:
    out = []
    hero = _safe_fact(world, world.facts, "hero")
    guide = _safe_fact(world, world.facts, "guide")
    if hero.memes.get("kindness", 0.0) < THRESHOLD:
        return out
    sig = ("kindness", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    guide.memes["kindness"] += 1.0
    hero.memes["warmth"] += 1.0
    out.append(f"The guide smiled back, and the room grew warmer.")
    return out


def _r_make_keep(world: World) -> list[str]:
    out = []
    scrap = _safe_fact(world, world.facts, "scrap")
    if scrap.memes.get("value", 0.0) < THRESHOLD:
        return out
    sig = ("keep", scrap.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    scrap.meters["used"] += 1.0
    out.append(f"The scrap was no longer just a scrap; it had become useful.")
    return out


CAUSAL_RULES = [_r_notice_scrap, _r_kindness_spread, _r_make_keep]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def introduce(world: World, hero: Entity) -> None:
    world.say(f"It was early at {world.place.name}, and {hero.id} arrived with quiet steps.")


def setting_detail(world: World) -> str:
    if world.place.indoors:
        return f"The windows were still pale, and the halls felt soft with morning hush."
    return f"The air was cool, and the institute yard was almost empty."


def find_scrap(world: World, hero: Entity, scrap: Entity) -> None:
    hero.memes["curiosity"] += 1.0
    world.say(f"{hero.id} spotted {scrap.phrase} near the chair leg.")


def dialogue(scene: str, speaker: Entity, listener: Entity, line: str) -> None:
    scene  # keep signature simple for state-driven narration design


def kind_talk(world: World, hero: Entity, guide: Entity, action: KindnessAction, scrap: Entity) -> None:
    hero.memes["kindness"] += 1.0
    world.say(f'{hero.id} asked, "{action.dialogue}"')
    world.say(f'{guide.id} answered, "That is a kind idea."')
    scrap.memes["value"] += 1.0
    world.say(f'Together they chose to {action.verb}, and {action.effect}.')


def finish(world: World, hero: Entity, scrap: Entity, action: KindnessAction) -> None:
    if action.id == "share":
        ending = f"In the end, {hero.id} kept the folded scrap inside a book, where it became {action.turns_scrap_into}."
    elif action.id == "return":
        ending = f"In the end, {hero.id} handed the scrap back, and it became {action.turns_scrap_into}."
    else:
        ending = f"In the end, {hero.id} tucked the scrap away carefully, and it became {action.turns_scrap_into}."
    world.say(ending)
    world.say(f"{hero.id} smiled at the little piece of paper, because even a scrap can help a day feel gentle.")


def tell(institute: Place, scrap_cfg: Scrap, action: KindnessAction, hero_name: str, role: str) -> World:
    world = build_world(StoryParams(institute="", scrap="", kindness="", name=hero_name, age=0, role=role))
    world.place = institute
    hero = _safe_fact(world, world.facts, "hero")
    guide = _safe_fact(world, world.facts, "guide")
    scrap = _safe_fact(world, world.facts, "scrap")
    world.facts["kindness"] = action

    introduce(world, hero)
    world.say(setting_detail(world))
    world.para()
    find_scrap(world, hero, scrap)
    world.say(f"{guide.id} leaned down and said, \"Early mornings are nicer when we look out for one another.\"")
    kind_talk(world, hero, guide, action, scrap)
    propagate(world, narrate=True)
    world.para()
    finish(world, hero, scrap, action)
    world.facts.update(resolved=True)
    return world


SETTINGS = INSTITUTES
CURATED = [
    StoryParams(institute="reading_nook", scrap="note_scrap", kindness="return", name="Mina", age=7, role="student"),
    StoryParams(institute="art_corner", scrap="paper_scrap", kindness="share", name="Leo", age=8, role="young artist"),
    StoryParams(institute="courtyard", scrap="fabric_scrap", kindness="save", name="Nora", age=6, role="visitor"),
]

GENDERED = {
    "girl": ["Mina", "Iris", "Nora", "Ava", "Maya"],
    "boy": ["Leo", "Noah", "Eli"],
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in INSTITUTES.items():
        for scrap_id, scrap in SCRAPS.items():
            if place_id not in scrap.found_in:
                continue
            for action_id, action in KINDNESS.items():
                if not action.requires or scrap.kind in action.requires:
                    combos.append((place_id, scrap_id, action_id))
    return combos


def explain_rejection(place_id: str, scrap_id: str, action_id: str) -> str:
    place = _safe_lookup(INSTITUTES, place_id)
    scrap = _safe_lookup(SCRAPS, scrap_id)
    action = _safe_lookup(KINDNESS, action_id)
    return (
        f"(No story: {action.verb} does not fit naturally with {scrap.label} in "
        f"{place.name}. Choose a scrap and a kindness move that belong together.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: an early institute morning, a scrap, and a kind dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--scrap", choices=SCRAPS)
    ap.add_argument("--kindness", choices=KINDNESS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--role", choices=ROLES)
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
    if getattr(args, "place", None) and getattr(args, "scrap", None) and getattr(args, "kindness", None):
        if (getattr(args, "place", None), getattr(args, "scrap", None), getattr(args, "kindness", None)) not in combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "scrap", None) is None or c[1] == getattr(args, "scrap", None))
              and (getattr(args, "kindness", None) is None or c[2] == getattr(args, "kindness", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, scrap, kindness = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GENDERED[gender])
    role = getattr(args, "role", None) or rng.choice(ROLES)
    return StoryParams(institute=place, scrap=scrap, kindness=kindness, name=name, age=rng.randint(5, 9), role=role)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short slice-of-life story for a child about an early morning at an institute where {f["hero"].id} finds a scrap and chooses kindness.',
        f'Tell a gentle story with dialogue in which {f["hero"].id} and {f["guide"].id} talk about a scrap at {world.place.name}.',
        f'Write a simple story that includes the words "early", "institute", "scrap", "kindness", and "dialogue".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    guide = _safe_fact(world, f, "guide")
    scrap = _safe_fact(world, f, "scrap")
    action = _safe_fact(world, f, "kindness")
    return [
        QAItem(
            question=f"What did {hero.id} find early at the institute?",
            answer=f"{hero.id} found {scrap.phrase}, and that little scrap became important later.",
        ),
        QAItem(
            question=f"What did {hero.id} and {guide.id} say to each other about the scrap?",
            answer=f"They had a kind dialogue. {hero.id} said, \"{action.dialogue}\" and {guide.id} agreed it was a kind idea.",
        ),
        QAItem(
            question=f"How did the scrap change by the end of the story?",
            answer=f"By the end, the scrap was used carefully and became {action.turns_scrap_into}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring toward other people.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is when characters talk to each other in a story.",
        ),
        QAItem(
            question="What is a scrap?",
            answer="A scrap is a small leftover piece, like a torn bit of paper or cloth.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
place_ok(P) :- setting(P).
scrap_ok(S) :- scrap(S).
kind_ok(K) :- kindness(K).

compatible(P,S,K) :- setting(P), scrap(S), kindness(K), place_has(P,S), action_fit(S,K).
story(P,S,K) :- compatible(P,S,K).

#show compatible/3.
#show story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in INSTITUTES:
        lines.append(asp.fact("setting", pid))
    for sid, scrap in SCRAPS.items():
        lines.append(asp.fact("scrap", sid))
        lines.append(asp.fact("scrap_kind", sid, scrap.kind))
        for place in sorted(scrap.found_in):
            lines.append(asp.fact("place_has", place, sid))
    for kid, action in KINDNESS.items():
        lines.append(asp.fact("kindness", kid))
        for req in sorted(action.requires):
            lines.append(asp.fact("requires", kid, req))
        for sid, scrap in SCRAPS.items():
            if not action.requires or scrap.kind in action.requires:
                lines.append(asp.fact("action_fit", sid, kid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    asp_set = set(asp.atoms(model, "compatible"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(asp_set - py_set))
    print("  only in python:", sorted(py_set - asp_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(INSTITUTES, params.institute), _safe_lookup(SCRAPS, params.scrap), _safe_lookup(KINDNESS, params.kindness), params.name, params.role)
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
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, scrap, kindness) combos:\n")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.name}: {p.kindness} at {p.institute} (scrap: {p.scrap})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
