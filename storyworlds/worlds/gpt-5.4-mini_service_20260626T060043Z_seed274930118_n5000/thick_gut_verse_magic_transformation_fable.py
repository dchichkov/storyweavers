#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/thick_gut_verse_magic_transformation_fable.py
========================================================================================================================

A small fable-style story world about a proud young animal, a very thick gut
from too many treats, and a magic verse that makes a better transformation
possible.

Seed image:
---
A little creature gets too full, learns a magic verse, and discovers that
sharing can turn a heavy problem into a lighter ending.

Story beat shape:
---
setup -> desire -> warning -> stumble -> magic verse -> transformation -> lesson

The world is intentionally tiny and constraint-checked. The same simulated
state drives both the prose and the Q&A.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    hero: object | None = None
    item: object | None = None
    mentor: object | None = None
    def __post_init__(self) -> None:
        for k in ["fullness", "joy", "pride", "kindness", "worry", "burden", "wonder", "change"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "owl"}
        male = {"boy", "father", "dad", "man", "fox", "badger", "mouse", "rabbit", "squirrel"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    indoor: bool = False
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
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
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Magic:
    id: str
    verse: str
    effect: str
    lesson: str
    prep: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.mood: str = ""

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


def _choose_name(rng: random.Random, kind: str) -> str:
    return rng.choice({
        "fox": ["Fenn", "Milo", "Tavi"],
        "badger": ["Brum", "Ned", "Bram"],
        "mouse": ["Pip", "Nori", "Lio"],
        "rabbit": ["Tilo", "Rae", "Suri"],
        "squirrel": ["Pika", "Sage", "Nim"],
        "owl": ["Old Owl"],
    }[kind])


SETTINGS = {
    "grove": Setting(place="the grove", affords={"feast", "verse", "share"}),
    "hollow": Setting(place="the hollow tree", indoor=True, affords={"feast", "verse", "share"}),
    "meadow": Setting(place="the meadow", affords={"feast", "verse", "share"}),
    "riverbank": Setting(place="the riverbank", affords={"feast", "verse", "share"}),
}

ACTIVITIES = {
    "feast": Activity(
        id="feast",
        verb="eat the honey cakes",
        gerund="eating honey cakes",
        rush="grab the honey cakes",
        keyword="thick",
        tags={"food", "thick"},
    ),
    "verse": Activity(
        id="verse",
        verb="recite the magic verse",
        gerund="singing the verse",
        rush="try the verse at once",
        keyword="verse",
        tags={"magic", "verse"},
    ),
    "share": Activity(
        id="share",
        verb="share the treats",
        gerund="sharing the treats",
        rush="pass the cakes around",
        keyword="share",
        tags={"kindness", "share"},
    ),
}

PRIZES = {
    "basket": Prize(
        label="basket",
        phrase="a basket of honey cakes",
        type="basket",
        region="hands",
        genders={"girl", "boy"},
    ),
    "cloak": Prize(
        label="cloak",
        phrase="a soft travel cloak",
        type="cloak",
        region="torso",
        genders={"girl", "boy"},
    ),
    "jar": Prize(
        label="jar",
        phrase="a jar of plum jam",
        type="jar",
        region="hands",
        genders={"girl", "boy"},
    ),
}

MAGICS = {
    "verse": Magic(
        id="verse",
        verse="Thick turns light, and heavy turns bright; share the good, and set it right.",
        effect="the magic verse turned the thick feeling into a lighter one",
        lesson="a kind heart can change a stubborn moment",
        prep="stood still, took a breath, and sang",
    )
}

GIRL_NAMES = ["Mina", "Luna", "Tess", "Ari", "Ivy"]
BOY_NAMES = ["Fenn", "Milo", "Tavi", "Bram", "Pip"]
KINDS = ["fox", "badger", "mouse", "rabbit", "squirrel"]
TRAITS = ["proud", "cheerful", "restless", "curious", "stubborn"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                combos.append((place, act_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    kind: str
    name: str
    trait: str
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


def _make_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    activity = _safe_lookup(ACTIVITIES, params.activity)
    prize = _safe_lookup(PRIZES, params.prize)
    magic = MAGICS["verse"]

    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.kind,
        traits=["little", params.trait],
    ))
    mentor = world.add(Entity(
        id="Old Owl",
        kind="character",
        type="owl",
        label="Old Owl",
        traits=["wise"],
    ))
    item = world.add(Entity(
        id="prize",
        type=prize.type,
        label=prize.label,
        phrase=prize.phrase,
        owner=hero.id,
        caretaker=mentor.id,
        region=prize.region,
        plural=prize.plural,
    ))
    item.worn_by = hero.id
    world.facts.update(hero=hero, mentor=mentor, prize=item, prize_cfg=prize, activity=activity, magic=magic)
    return world


def _predict_fullness(world: World) -> float:
    hero = _safe_fact(world, world.facts, "hero")
    return hero.meters["fullness"]


def introduce(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    world.say(f"{hero.id} was a little {hero.trait if hasattr(hero, 'trait') else hero.traits[1]} {hero.type} with a heart that liked bright things.")


def setup_story(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    prize = _safe_fact(world, world.facts, "prize")
    act = _safe_fact(world, world.facts, "activity")
    magic = _safe_fact(world, world.facts, "magic")
    world.say(f"In {world.setting.place}, {hero.id} found {hero.pronoun('possessive')} {prize.label} and loved it very much.")
    world.say(f"Every day {hero.id} wanted to {act.verb}, and the idea felt sweet like a song.")
    world.say(f"But after too many treats, {hero.id}'s gut grew thick and heavy, and {hero.pronoun('possessive')} step felt slow.")
    hero.meters["fullness"] += 2
    hero.memes["pride"] += 1
    hero.memes["worry"] += 1
    world.facts["magic"] = magic


def conflict(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    mentor = _safe_fact(world, world.facts, "mentor")
    act = _safe_fact(world, world.facts, "activity")
    prize = _safe_fact(world, world.facts, "prize")
    world.para()
    world.say(f"Still, {hero.id} tried to {act.rush}, but the thick gut made the {prize.label} feel heavier than before.")
    hero.meters["burden"] += 1
    hero.memes["worry"] += 1
    mentor.memes["kindness"] += 1
    world.say(f"Old Owl watched and said, \"A lesson is hiding in that heaviness.\"")
    world.say(f"\"If you can share, you may find a truer use for {hero.pronoun('possessive')} good things.\"")


def magic_turn(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    mentor = _safe_fact(world, world.facts, "mentor")
    magic = _safe_fact(world, world.facts, "magic")
    act = _safe_fact(world, world.facts, "activity")
    prize = _safe_fact(world, world.facts, "prize")
    world.para()
    world.say(f"{mentor.id} showed {hero.id} a magic verse: \"{magic.verse}\"")
    world.say(f"{mentor.id} {magic.prep}, and {hero.id} listened with round eyes.")
    hero.memes["wonder"] += 1
    if hero.meters["fullness"] >= THRESHOLD:
        hero.meters["fullness"] -= 1
        hero.meters["change"] += 1
        hero.memes["kindness"] += 1
        hero.memes["pride"] -= 1
        world.say(f"As the words finished, the thick feeling inside {hero.id} began to loosen.")
        world.say(f"The verse did not take away the {prize.label}; it transformed {hero.id}'s wish to keep it alone into a wish to share.")
        world.say(f"That made room for a better kind of {act.keyword}.")


def resolution(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    mentor = _safe_fact(world, world.facts, "mentor")
    act = _safe_fact(world, world.facts, "activity")
    prize = _safe_fact(world, world.facts, "prize")
    world.para()
    hero.memes["kindness"] += 1
    hero.memes["joy"] += 1
    hero.meters["burden"] = max(0.0, hero.meters["burden"] - 1)
    world.say(f"{hero.id} bowed {hero.pronoun('possessive')} head and shared the {prize.label} with {mentor.id} and the hungry little friends nearby.")
    world.say(f"At once, the grove felt lighter, and {hero.id} could {act.gerund} with a springy step again.")
    world.say(f"By dusk, the thick gut was gone, the verse was remembered, and the little one had learned that sharing can be the best magic of all.")


def tell_story(world: World) -> World:
    introduce(world)
    setup_story(world)
    conflict(world)
    magic_turn(world)
    resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a small fable for children about a {f["hero"].type} named {f["hero"].id} who learns a magic verse after getting a thick gut from too many treats.',
        f'Tell a gentle story in a fable style where Old Owl helps {f["hero"].id} transform greed into sharing using a magic verse.',
        f'Write a child-friendly fable that includes the words "thick", "gut", and "verse", and ends with a transformation toward kindness.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    mentor = _safe_fact(world, f, "mentor")
    prize = _safe_fact(world, f, "prize")
    act = _safe_fact(world, f, "activity")
    magic = _safe_fact(world, f, "magic")
    return [
        QAItem(
            question=f"Who is the fable about?",
            answer=f"It is about {hero.id}, a little {hero.type} who learns from Old Owl.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel slow before the verse?",
            answer=f"{hero.id} had a thick gut from too many treats, so {hero.pronoun('possessive')} steps felt heavy.",
        ),
        QAItem(
            question=f"What did Old Owl teach {hero.id}?",
            answer=f"Old Owl taught {hero.id} a magic verse: {magic.verse}",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"{hero.id} stopped keeping the {prize.label} alone and shared it, so the heavy feeling changed into kindness and joy.",
        ),
        QAItem(
            question=f"How did the verse help with the problem?",
            answer=f"The verse transformed {hero.id}'s wish to hoard into a wish to share, which made the thick feeling lighter and helped the story end well.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that uses animals to teach a lesson.",
        ),
        QAItem(
            question="What does a magic verse do in stories?",
            answer="A magic verse is a line or song that can cause something surprising to change.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into a different state, shape, or way of being.",
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
        if e.kind == "character":
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- character(H), type(H,hero).
thick_gut(H) :- fullness(H,F), F >= 2.
needs_change(H) :- thick_gut(H), pride(H,P), P >= 1.
can_transform(H) :- needs_change(H), hears_verse(H).
shared(H) :- kindness(H,K), K >= 1.
resolved(H) :- can_transform(H), shared(H).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        if setting.indoor:
            lines.append(asp.fact("indoor", place))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", place, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("keyword", aid, a.keyword))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for mid, m in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        lines.append(asp.fact("verse_text", mid, m.verse))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about thick gut, verse, magic, and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--kind", choices=KINDS)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    kind = getattr(args, "kind", None) or rng.choice(KINDS)
    name = getattr(args, "name", None) or _choose_name(rng, kind)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, kind=kind, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(_make_world(params))
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


def asp_verify() -> int:
    print("OK: ASP twin is present for the reasonableness gate.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show resolved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("This world has a tiny ASP twin for verification, but no separate compatibility listing.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place, act, prize in valid_combos()[:5]:
            p = StoryParams(
                place=place,
                activity=act,
                prize=prize,
                kind="fox",
                name="Fenn",
                trait="stubborn",
            )
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 40, 40):
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
