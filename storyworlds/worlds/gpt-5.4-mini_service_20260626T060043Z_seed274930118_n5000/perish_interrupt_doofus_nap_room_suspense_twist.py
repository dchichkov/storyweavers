#!/usr/bin/env python3
"""
A small fairy-tale storyworld set in a nap room.

Premise:
- A little sleeper is trying to nap in a quiet room.
- A doofus interruption threatens the hush.
- Suspense rises as the nap might perish.
- Twist: the doofus meant well.
- Lesson learned: gentle help works better than noisy haste.

This script is standalone and follows the Storyweavers world contract.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    doofus: object | None = None
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "mother", "queen", "woman"}
        male = {"boy", "prince", "father", "king", "man"}
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
    place: str = "the nap room"
    afforded: set[str] = field(default_factory=lambda: {"nap", "whisper"})
    SETTING: object | None = None
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
class Interruption:
    id: str
    trigger: str
    clue: str
    sound: str
    risk: str
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
class Comfort:
    id: str
    label: str
    phrase: str
    covers: set[str]
    hushes: set[str]
    prep: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for e in self.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={dict(meters)}")
            if memes:
                bits.append(f"memes={dict(memes)}")
            if e.protective:
                bits.append(f"covers={sorted(e.covers)}")
            lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
        lines.append(f"  fired rules: {sorted({n for n, *_ in self.fired})}")
        return "\n".join(lines)


@dataclass
class StoryParams:
    name: str
    gender: str
    doofus: str
    comfort: str
    seed: Optional[int] = None
    p: object | None = None
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


SETTING = Setting()

INTERUPTIONS = {
    "squeak": Interruption(
        id="squeak",
        trigger="a squeaky slipper",
        clue="its little squeak",
        sound="squeak",
        risk="the hush might perish",
        keyword="squeak",
        tags={"quiet", "noise"},
    ),
    "clatter": Interruption(
        id="clatter",
        trigger="a clattering wooden spoon",
        clue="its clatter",
        sound="clatter",
        risk="the nap could be broken",
        keyword="clatter",
        tags={"quiet", "noise"},
    ),
    "bump": Interruption(
        id="bump",
        trigger="a bumping toy bucket",
        clue="its bump-bump",
        sound="bump",
        risk="the sleep spell could scatter",
        keyword="bump",
        tags={"quiet", "noise"},
    ),
}

COMFORTS = {
    "blanket": Comfort(
        id="blanket",
        label="a soft blanket",
        phrase="a soft blanket with moon stitches",
        covers={"body"},
        hushes={"noise"},
        prep="wrap the child in a soft blanket first",
        tail="wrapped the child in the soft blanket and sat like a mouse",
    ),
    "pillow": Comfort(
        id="pillow",
        label="a cloud pillow",
        phrase="a cloud pillow stuffed with lavender",
        covers={"head"},
        hushes={"noise"},
        prep="set out a cloud pillow first",
        tail="set out the cloud pillow and spoke in tiny whispers",
    ),
    "nightcap": Comfort(
        id="nightcap",
        label="a nightcap",
        phrase="a knitted nightcap",
        covers={"head"},
        hushes={"noise"},
        prep="put on a nightcap first",
        tail="put on the nightcap and crept softly to the bed",
    ),
}

NAMES = ["Mina", "Lina", "Tessa", "Ivo", "Rowan", "Pip", "Elin", "Bram"]
GENDERS = {"girl": ["girl", "princess"], "boy": ["boy", "prince"]}
DOOFUS_TITLES = ["doofus sprite", "doofus goblin", "doofus page"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for i in INTERUPTIONS.values():
        for c in COMFORTS.values():
            if i.id == "squeak" and "noise" in c.hushes:
                combos.append((i.id, c.id))
            elif i.id == "clatter" and "noise" in c.hushes:
                combos.append((i.id, c.id))
            elif i.id == "bump" and "noise" in c.hushes:
                combos.append((i.id, c.id))
    return combos


def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    hero_type = params.gender if params.gender in GENDERS else "girl"
    hero_role = "princess" if hero_type == "girl" else "prince"
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=hero_role,
        label=params.name,
        memes={"sleepy": 1.0, "hope": 1.0},
    ))
    doofus = world.add(Entity(
        id="Doofus",
        kind="character",
        type=params.doofus,
        label=params.doofus,
        memes={"fuss": 1.0, "well_meaning": 1.0},
    ))
    comfort = _safe_lookup(COMFORTS, params.comfort)
    interruption = _safe_lookup(INTERUPTIONS, params.doofus)
    item = world.add(Entity(
        id="Comfort",
        type=comfort.id,
        label=comfort.label,
        phrase=comfort.phrase,
        caretaker=hero.id,
        protective=True,
        covers=set(comfort.covers),
        plural=comfort.plural,
    ))
    world.facts.update(hero=hero, doofus=doofus, comfort=item, interruption=interruption)
    return world


def predict(world: World, interruption: Interruption) -> dict:
    sim = world.copy()
    hero = next(e for e in sim.characters() if e.id != "Doofus")
    hero.meters["sleep"] = 1.0
    hero.memes["unease"] = 1.0
    if interruption.sound in {"squeak", "clatter", "bump"}:
        hero.memes["startled"] = hero.memes.get("startled", 0.0) + 1.0
    ruined = hero.memes.get("startled", 0.0) >= THRESHOLD
    return {"ruined": ruined}


def setup(world: World) -> None:
    hero = next(e for e in world.characters() if e.id != "Doofus")
    comfort = _safe_fact(world, world.facts, "comfort")
    world.say(
        f"Once in the nap room, little {hero.id} dreamed of a nap so deep it might last until supper."
    )
    world.say(
        f"Beside the bed stood {comfort.phrase}, and the room smelled of warm milk and clean linen."
    )
    hero.memes["want_sleep"] = 1.0


def suspense(world: World) -> None:
    hero = next(e for e in world.characters() if e.id != "Doofus")
    interruption = _safe_fact(world, world.facts, "interruption")
    hero.memes["unease"] = 1.0
    hero.meters["quiet"] = 1.0
    world.say(
        f"Then came {interruption.trigger}, and its {interruption.clue} skated through the hush."
    )
    world.say(
        f"{hero.id} blinked. If the noise grew louder, {interruption.risk}."
    )
    hero.memes["worry"] = 1.0


def interrupt(world: World) -> None:
    hero = next(e for e in world.characters() if e.id != "Doofus")
    doofus = world.get("Doofus")
    interruption = _safe_fact(world, world.facts, "interruption")
    doofus.memes["fuss"] += 1.0
    hero.memes["startled"] = hero.memes.get("startled", 0.0) + 1.0
    hero.meters["quiet"] = 0.0
    world.say(
        f"With a mighty {interruption.sound}, the doofus interrupted the room, and the sleepy child sat up at once."
    )


def twist(world: World) -> None:
    hero = next(e for e in world.characters() if e.id != "Doofus")
    doofus = world.get("Doofus")
    comfort = _safe_fact(world, world.facts, "comfort")
    doofus.memes["well_meaning"] += 1.0
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1.0
    world.say(
        f"But the doofus bowed low and showed {hero.id} a tiny lost moon-button sewn to {comfort.label}."
    )
    world.say(
        f"He had been clattering because he meant to return it before the nap began."
    )


def lesson_learned(world: World) -> None:
    hero = next(e for e in world.characters() if e.id != "Doofus")
    comfort = _safe_fact(world, world.facts, "comfort")
    interruption = _safe_fact(world, world.facts, "interruption")
    doofus = world.get("Doofus")
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1.0
    hero.memes["sleep"] = 1.0
    world.say(
        f"{hero.id} smiled and learned that even a doofus can help if he uses gentle hands and honest words."
    )
    world.say(
        f"So the room grew still again, {comfort.tail}, and at last the nap arrived like a soft white dove."
    )


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    setup(world)
    world.para()
    suspense(world)
    interrupt(world)
    world.para()
    twist(world)
    lesson_learned(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    interruption = _safe_fact(world, f, "interruption")
    return [
        f'Write a fairy-tale story in a nap room where {hero.id} is trying to sleep and a {interruption.id} causes suspense, a twist, and a lesson learned.',
        f'Tell a gentle story about a doofus who interrupts a nap room, then reveals a kind reason for the noise.',
        f'Write a child-friendly fairy tale using the words "perish", "interrupt", and "doofus" in a nap room setting.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    interruption = _safe_fact(world, f, "interruption")
    comfort = _safe_fact(world, f, "comfort")
    return [
        QAItem(
            question=f"Where was {hero.id} trying to rest?",
            answer="They were in the nap room, where the blankets were warm and the light was soft.",
        ),
        QAItem(
            question=f"What interrupted the quiet in the story?",
            answer=f"The {interruption.trigger} interrupted the quiet with its little {interruption.sound}.",
        ),
        QAItem(
            question=f"What was the comfort item in the room?",
            answer=f"It was {comfort.phrase}, which helped the room feel cozy and safe.",
        ),
        QAItem(
            question=f"Why did the child forgive the doofus?",
            answer="Because the doofus was not trying to be mean; he was trying to return a lost moon-button and help the nap room stay peaceful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a nap room for?",
            answer="A nap room is a quiet place where tired children can rest, close their eyes, and sleep for a while.",
        ),
        QAItem(
            question="Why should people be quiet in a nap room?",
            answer="People should be quiet so sleepy children can fall asleep without being startled.",
        ),
        QAItem(
            question="What does lesson learned mean in a story?",
            answer="Lesson learned means the characters understand something important by the end and behave better next time.",
        ),
        QAItem(
            question="What is a doofus?",
            answer="A doofus is a silly, clumsy person or creature who makes mistakes, but sometimes still means well.",
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


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "nap_room"),
        asp.fact("affords", "nap_room", "nap"),
        asp.fact("affords", "nap_room", "whisper"),
    ]
    for iid, intr in INTERUPTIONS.items():
        lines.append(asp.fact("interruption", iid))
        lines.append(asp.fact("sound", iid, intr.sound))
        lines.append(asp.fact("risk", iid, intr.risk))
    for cid, c in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        for h in sorted(c.hushes):
            lines.append(asp.fact("hushes", cid, h))
        for cov in sorted(c.covers):
            lines.append(asp.fact("covers", cid, cov))
    return "\n".join(lines)


ASP_RULES = r"""
valid(I, C) :- interruption(I), comfort(C), hushes(C, noise), sound(I, _).
compatible(I, C) :- valid(I, C).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "doofus", None) and getattr(args, "comfort", None):
        if (getattr(args, "doofus", None), getattr(args, "comfort", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = valid_combos()
    if getattr(args, "doofus", None):
        combos = [c for c in combos if c[0] == getattr(args, "doofus", None)]
    if getattr(args, "comfort", None):
        combos = [c for c in combos if c[1] == getattr(args, "comfort", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    doofus, comfort = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    return StoryParams(name=name, gender=gender, doofus=doofus, comfort=comfort)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld in a nap room with suspense, twist, and lesson learned."
    )
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--doofus", choices=sorted(INTERUPTIONS))
    ap.add_argument("--comfort", choices=sorted(COMFORTS))
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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:\n")
        for doofus, comfort in combos:
            print(f"  {doofus:8} {comfort}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for doofus, comfort in valid_combos():
            p = StoryParams(
                name="Mina",
                gender="girl",
                doofus=doofus,
                comfort=comfort,
                seed=base_seed,
            )
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
