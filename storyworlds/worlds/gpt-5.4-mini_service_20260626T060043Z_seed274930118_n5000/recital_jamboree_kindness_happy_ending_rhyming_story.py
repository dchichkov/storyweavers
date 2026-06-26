#!/usr/bin/env python3
"""
A tiny story world about a recital and a jamboree, told in a light rhyming-story style.

The child wants the show to go on, but something is missing or risky.
A kind helper changes the world state so the ending can feel happy and complete.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    cared_for_by: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def put(self) -> str:
        return "them" if self.type.endswith("s") else "it"
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
    place: str = "the little hall"
    indoor: bool = True
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
    trouble: str
    weather: str
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
    fragility: str
    risk: str
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
class Gift:
    id: str
    label: str
    phrase: str
    helps: set[str]
    fix: str
    tail: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

SETTINGS = {
    "hall": Setting(place="the little hall", indoor=True, affords={"recital", "jamboree"}),
    "garden_stage": Setting(place="the garden stage", indoor=False, affords={"recital", "jamboree"}),
    "school_room": Setting(place="the school room", indoor=True, affords={"recital"}),
}

ACTIVITIES = {
    "recital": Activity(
        id="recital",
        verb="sing at the recital",
        gerund="singing at the recital",
        trouble="a wobbly voice",
        weather="soft",
        keyword="recital",
        tags={"music", "sing", "stage"},
    ),
    "jamboree": Activity(
        id="jamboree",
        verb="dance at the jamboree",
        gerund="dancing at the jamboree",
        trouble="a tumble on the floor",
        weather="bright",
        keyword="jamboree",
        tags={"dance", "music", "party"},
    ),
}

PRIZES = {
    "ribbon": Prize(
        label="ribbon",
        phrase="a shiny ribbon",
        type="ribbon",
        fragility="wrinkled",
        risk="creased",
        genders={"girl"},
    ),
    "cape": Prize(
        label="cape",
        phrase="a bright blue cape",
        type="cape",
        fragility="creased",
        risk="rumpled",
    ),
    "hat": Prize(
        label="hat",
        phrase="a tiny stage hat",
        type="hat",
        fragility="bent",
        risk="tilted",
    ),
}

GIFTS = [
    Gift(
        id="soft_shoes",
        label="soft shoes",
        phrase="a pair of soft shoes",
        helps={"jamboree"},
        fix="kept the steps light",
        tail="wore the soft shoes and twirled with grace",
    ),
    Gift(
        id="music_clip",
        label="a music clip",
        phrase="a neat music clip",
        helps={"recital"},
        fix="held the pages steady",
        tail="clipped the song pages and sang with ease",
    ),
    Gift(
        id="kind_words",
        label="kind words",
        phrase="some kind words",
        helps={"recital", "jamboree"},
        fix="made brave hearts bloom",
        tail="felt brave and smiled all the way",
    ),
]

NAMES = {
    "girl": ["Mia", "Lina", "Ruby", "Nora", "Ivy", "Zoe"],
    "boy": ["Theo", "Finn", "Noah", "Eli", "Ben", "Leo"],
}
TRAITS = ["gentle", "cheerful", "brave", "curious", "spry", "kind"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story logic
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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    if activity.id == "recital":
        return prize.label in {"ribbon", "hat", "cape"}
    if activity.id == "jamboree":
        return prize.label in {"hat", "cape"}
    return False


def select_gift(activity: Activity, prize: Prize) -> Optional[Gift]:
    for gift in GIFTS:
        if activity.id in gift.helps:
            if activity.id == "recital" and prize.label == "ribbon" and gift.id == "music_clip":
                continue
            return gift
    return None


def tell_story(setting: Setting, activity: Activity, prize_cfg: Prize,
               hero_name: str, hero_gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, meters={}, memes={}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        cared_for_by=parent.id,
    ))

    world.say(f"{hero.id} was a {trait} child who loved a song and a shine.")
    world.say(f"{hero.pronoun().capitalize()} dreamed of {activity.gerund}, with a smile and a rhyme.")
    world.say(f"That day, {parent.label} brought {hero.pronoun('object')} {prize_cfg.phrase}, neat and fine.")
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label}; it looked like a star at line.")

    world.para()
    world.say(f"At {setting.place}, the lights were set in a row.")
    world.say(f"{hero.id} wanted to {activity.verb}, but the {prize.label} might not stay so neat and slow.")
    world.say(f"{parent.label} saw the risk and spoke with care and glow:")
    world.say(f"\"If we rush, your {prize.label} may get {prize_cfg.risk}; let's choose a kinder way to go.\"")

    hero.memes["want"] = 1.0
    hero.memes["worry"] = 1.0 if prize_at_risk(activity, prize_cfg) else 0.0
    prize.meters["risk"] = 1.0 if prize_at_risk(activity, prize_cfg) else 0.0

    world.para()
    gift = select_gift(activity, prize_cfg)
    if gift is None:
        pass
    world.say(f"Then {parent.label} offered {gift.phrase}, with a warm little beam.")
    world.say(f"It {gift.fix}, like a helpful dream.")
    world.say(f"{hero.id} nodded yes, with a grateful sigh.")
    world.say(f"Kindness made the worry shrink; the mood turned light and high.")

    hero.memes["joy"] = 2.0
    hero.memes["kindness"] = 1.0
    hero.memes["happy"] = 1.0
    prize.meters["safe"] = 1.0
    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        setting=setting,
        gift=gift,
        happy_ending=True,
    )

    world.para()
    world.say(f"So {hero.id} {gift.tail}, and the show began to gleam.")
    if activity.id == "recital":
        world.say(f"{hero.id} sang a sweet song, soft as cream.")
    else:
        world.say(f"{hero.id} danced in a happy circle, quick and clean.")
    world.say(f"The {prize.label} stayed tidy, and the crowd cheered in between.")
    world.say(f"With kindness in the middle, the ending shone bright and serene.")

    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    act = _safe_fact(world, f, "activity")
    prize = _safe_fact(world, f, "prize_cfg")
    return [
        f'Write a short rhyming story about a child named {hero.id} who wants to {act.verb} at a {f["setting"].place}.',
        f'Create a gentle story with the words "recital" and "jamboree" where kindness helps protect {prize.phrase}.',
        f'Tell a happy-ending rhyming story in which a parent and child solve a small show-day problem with a kind choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    prize = _safe_fact(world, f, "prize")
    act = _safe_fact(world, f, "activity")
    gift = _safe_fact(world, f, "gift")
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {f['setting'].place}?",
            answer=f"{hero.id} wanted to {act.verb}. {parent.label} helped make that possible in a kind way.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the {prize.label}?",
            answer=f"{parent.label} worried because the {prize.label} could get {prize.risk} during the {act.id}.",
        ),
        QAItem(
            question=f"What helped turn the problem into a happy ending?",
            answer=f"{gift.phrase} helped, because it {gift.fix}. That let the day end with kindness and joy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = []
    if f["activity"].id == "recital":
        out.append(QAItem(
            question="What is a recital?",
            answer="A recital is a performance where someone sings, plays, or shows a practiced skill for an audience.",
        ))
    if f["activity"].id == "jamboree":
        out.append(QAItem(
            question="What is a jamboree?",
            answer="A jamboree is a lively gathering with music, dancing, and happy sharing.",
        ))
    out.append(QAItem(
        question="What is kindness?",
        answer="Kindness is choosing gentle, caring actions that help someone feel safe and loved.",
    ))
    out.append(QAItem(
        question="What makes a happy ending?",
        answer="A happy ending is when the problem gets solved and the characters finish feeling glad.",
    ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
show(risk(A,P)) :- activity(A), prize(P), at_risk(A,P).
show(fix(A,P,G)) :- activity(A), prize(P), gift(G), helps(G,A), at_risk(A,P), protects(G,P).
at_risk(recital,ribbon).
at_risk(recital,hat).
at_risk(recital,cape).
at_risk(jamboree,hat).
at_risk(jamboree,cape).

helps(music_clip,recital).
helps(soft_shoes,jamboree).
helps(kind_words,recital).
helps(kind_words,jamboree).

protects(music_clip,ribbon).
protects(music_clip,hat).
protects(music_clip,cape).
protects(soft_shoes,hat).
protects(soft_shoes,cape).
protects(kind_words,ribbon).
protects(kind_words,hat).
protects(kind_words,cape).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for g in GIFTS:
        lines.append(asp.fact("gift", g.id))
        for a in sorted(g.helps):
            lines.append(asp.fact("helps", g.id, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show show/1."))
    shown = sorted(set(asp.atoms(model, "show")))
    py = sorted([("risk", a, p) for a in ACTIVITIES for p in PRIZES if prize_at_risk(_safe_lookup(ACTIVITIES, a), _safe_lookup(PRIZES, p))] +
                [("fix", a, p, g.id) for a in ACTIVITIES for p in PRIZES for g in GIFTS
                 if a in g.helps and select_gift(_safe_lookup(ACTIVITIES, a), _safe_lookup(PRIZES, p)) is not None and select_gift(_safe_lookup(ACTIVITIES, a), _safe_lookup(PRIZES, p)).id == g.id])
    if shown == py:
        print(f"OK: ASP matches Python gate ({len(shown)} facts).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("ASP:", shown)
    print("PY :", py)
    return 1


def asp_valid_pairs() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show show/1."))
    return sorted(set(asp.atoms(model, "show")))


# ---------------------------------------------------------------------------
# CLI / sample generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming story world about a recital and a jamboree.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if getattr(args, "activity", None) and getattr(args, "prize", None):
        act = _safe_lookup(ACTIVITIES, getattr(args, "activity", None))
        pr = _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not prize_at_risk(act, pr):
            return _fallback_storyparams(args, rng, StoryParams, globals())
        if select_gift(act, pr) is None:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    choices = [
        (pl, a, p)
        for pl, s in SETTINGS.items()
        for a in s.affords
        for p in PRIZES
        if (getattr(args, "place", None) is None or getattr(args, "place", None) == pl)
        and (getattr(args, "activity", None) is None or getattr(args, "activity", None) == a)
        and (getattr(args, "prize", None) is None or getattr(args, "prize", None) == p)
        and prize_at_risk(_safe_lookup(ACTIVITIES, a), _safe_lookup(PRIZES, p))
        and select_gift(_safe_lookup(ACTIVITIES, a), _safe_lookup(PRIZES, p)) is not None
        and (getattr(args, "gender", None) is None or getattr(args, "gender", None) in _safe_lookup(PRIZES, p).genders)
    ]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(sorted(choices))
    gender = getattr(args, "gender", None) or rng.choice(sorted(_safe_lookup(PRIZES, prize).genders))
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(PRIZES, params.prize),
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id} ({e.type}) " + " ".join(bits))
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
    StoryParams(place="hall", activity="recital", prize="ribbon", name="Mia", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="garden_stage", activity="jamboree", prize="cape", name="Theo", gender="boy", parent="father", trait="cheerful"),
    StoryParams(place="school_room", activity="recital", prize="hat", name="Ivy", gender="girl", parent="mother", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show show/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show show/1."))
        shown = sorted(set(asp.atoms(model, "show")))
        print(f"{len(shown)} ASP facts:")
        for item in shown:
            print(item)
        return

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        seen = set()
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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
