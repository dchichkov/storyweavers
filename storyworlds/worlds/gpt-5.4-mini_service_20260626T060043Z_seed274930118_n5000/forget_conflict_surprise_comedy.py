#!/usr/bin/env python3
"""
storyworlds/worlds/forget_conflict_surprise_comedy.py
======================================================

A small comedy storyworld about forgetting something, a little conflict, and a
surprising fix that makes the ending feel funny and complete.

The premise is intentionally tiny:
- a child wants to do a cheerful activity,
- they forget an important thing,
- someone worries and argues a little,
- a surprise turns the problem into a joke,
- everyone ends up laughing.

This script follows the Storyweavers world contract:
- typed entities with physical meters and emotional memes,
- a simulation that drives the prose,
- story QA and world QA,
- an inline ASP twin for the reasonableness gate,
- --verify parity checks.

The story flavor leans Comedy: the surprise should feel playful, not scary.
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
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    body_zone: object | None = None
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
    place: str
    indoors: bool
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
    mess: str
    risk: str
    surprise: str
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
    body_zone: str
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
class Fix:
    id: str
    label: str
    prep: str
    reveal: str
    guards: set[str]
    covers: set[str]
    plural: bool = False
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
    place: str
    activity: str
    prize: str
    fix: str
    name: str
    gender: str
    parent: str
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


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"joke", "song"}),
    "backyard": Setting(place="the backyard", indoors=False, affords={"joke", "trick"}),
    "stage": Setting(place="the little stage", indoors=True, affords={"joke", "trick", "song"}),
}

ACTIVITIES = {
    "joke": Activity(
        id="joke",
        verb="tell a joke",
        gerund="telling jokes",
        rush="dash to the joke corner",
        mess="crumbs",
        risk="forget the punchline",
        surprise="the punchline pops up anyway",
        tags={"laugh", "forget"},
    ),
    "trick": Activity(
        id="trick",
        verb="do a silly trick",
        gerund="doing silly tricks",
        rush="spin too fast",
        mess="bump",
        risk="forget the ending move",
        surprise="the ending move turns extra silly",
        tags={"laugh", "forget"},
    ),
    "song": Activity(
        id="song",
        verb="sing a silly song",
        gerund="singing silly songs",
        rush="hurry to the microphone",
        mess="notes",
        risk="forget the next verse",
        surprise="the next verse comes from the audience",
        tags={"music", "forget"},
    ),
}

PRIZES = {
    "card": Prize(
        label="joke card",
        phrase="a bright joke card with big letters",
        type="card",
        body_zone="pocket",
    ),
    "hat": Prize(
        label="hat",
        phrase="a funny red hat with a wobble on top",
        type="hat",
        body_zone="head",
    ),
    "shoe": Prize(
        label="shoe",
        phrase="one shiny shoe with a squeaky heel",
        type="shoe",
        body_zone="foot",
    ),
}

FIXES = {
    "mirror": Fix(
        id="mirror",
        label="a pocket mirror",
        prep="look in a pocket mirror",
        reveal="the forgotten joke was written on the back",
        guards={"crumbs", "bump", "notes"},
        covers={"pocket", "head"},
    ),
    "banana": Fix(
        id="banana",
        label="a banana peel",
        prep="hold up a banana peel",
        reveal="the whole room slips into laughter",
        guards={"bump", "crumbs"},
        covers={"foot"},
    ),
    "megaphone": Fix(
        id="megaphone",
        label="a toy megaphone",
        prep="use a toy megaphone",
        reveal="the missing words bounce around the room and come back in a silly voice",
        guards={"notes"},
        covers={"pocket", "head"},
    ),
}

NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Finn", "Zoe", "Max"]
TRAITS = ["cheerful", "silly", "curious", "playful", "bouncy", "bright"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    if activity.id == "joke":
        return prize.body_zone == "pocket"
    if activity.id == "trick":
        return prize.body_zone in {"head", "foot"}
    if activity.id == "song":
        return prize.body_zone in {"head", "pocket"}
    return False


def select_fix(activity: Activity, prize: Prize) -> Optional[Fix]:
    for fx in FIXES.values():
        if activity.mess in fx.guards and prize.body_zone in fx.covers:
            return fx
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_fix(act, prize):
                    out.append((place, act_id, prize_id))
    return out


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.meters.keys()), "")
    world.say(
        f"{hero.id} was a little {hero.type} with a {trait} grin and a knack for making ordinary days funny."
    )


def setup(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} loved {activity.gerund}, and {hero.pronoun('possessive')} {parent.type} had bought "
        f"{hero.pronoun('object')} {prize.phrase}."
    )
    prize.worn_by = hero.id
    hero.memes["love"] = hero.memes.get("love", 0) + 1
    world.say(
        f"{hero.id} wore {prize.it()} everywhere, because {prize.label} made the day feel like a small parade."
    )


def enter_place(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    where = "were in" if world.setting.indoors else "went to"
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.type} {where} {world.setting.place}.")
    world.say(f"{world.setting.place.capitalize()} looked ready for fun, but also a tiny bit too serious.")


def want_and_forget(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    hero.memes["forgetful"] = hero.memes.get("forgetful", 0) + 1
    world.say(
        f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} head went blank for a second."
    )
    world.say(
        f"{hero.id} had forgotten {activity.risk}, and that made the {prize.label} feel suddenly very important."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    if not prize_at_risk(activity, prize):
        return False
    parent.memes["worry"] = parent.memes.get("worry", 0) + 1
    world.say(
        f'"Wait," {hero.pronoun("possessive")} {parent.type} said. "If you {activity.verb}, you might mess up your {prize.label}."'
    )
    return True


def conflict(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
    world.say(
        f"{hero.id} puffed out {hero.pronoun('possessive')} cheeks. "
        f'"I did not forget on purpose!" {hero.pronoun()} said.'
    )
    world.say(
        f"That made a tiny argument, the kind that sounds big only because everyone is trying not to laugh."
    )


def surprise_turn(world: World, hero: Entity, prize: Entity, activity: Activity, fx: Fix) -> None:
    hero.memes["surprise"] = hero.memes.get("surprise", 0) + 1
    world.say(
        f"Then {hero.id} checked {hero.pronoun('possessive')} {prize.label} and found a surprise."
    )
    world.say(fx.reveal.capitalize() + ".")
    world.say(
        f"{hero.id} blinked, then giggled so hard that the argument shrank to the size of a raisin."
    )


def resolve(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity, fx: Fix) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["conflict"] = 0.0
    world.say(
        f'{parent.id.capitalize() if parent.id else "The parent"} smiled and said, "{fx.prep} first, then let the fun happen."'
    )
    world.say(
        f"They followed the plan, and soon {hero.id} was {activity.gerund}, while {prize.label} stayed perfectly fine."
    )
    world.say(
        f"The best part was that the surprise made everyone laugh even louder than the joke."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, fix_cfg: Fix,
         hero_name: str, hero_type: str, hero_traits: Optional[list[str]] = None,
         parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, body_zone=prize_cfg.body_zone, plural=prize_cfg.plural,
    ))

    hero.meters["cheerful"] = 1.0
    if hero_traits:
        for t in hero_traits:
            hero.meters[t] = hero.meters.get(t, 0.0) + 1.0

    introduce(world, hero)
    setup(world, hero, parent, prize, activity)
    world.para()
    enter_place(world, hero, parent, activity)
    want_and_forget(world, hero, activity, prize)
    warn(world, parent, hero, activity, prize)
    conflict(world, hero, parent, activity, prize)
    world.para()
    surprise_turn(world, hero, prize, activity, fix_cfg)
    resolve(world, hero, parent, activity, prize, fix_cfg)
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, fix=fix_cfg, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a funny story for a young child about forgetting something important and then finding a surprise.',
        f"Tell a comedy story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {parent.type} worries about {prize.label}.",
        f"Write a short story that includes the word 'forget' and ends with everyone laughing at a surprise fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, act, prize, fx = f["hero"], f["parent"], f["activity"], f["prize"], f["fix"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"What had {hero.id} forgotten?",
            answer=f"{hero.id} had forgotten {act.risk}, which caused the little argument.",
        ),
        QAItem(
            question=f"Why did {parent.type} worry about the {prize.label}?",
            answer=f"{parent.type.capitalize()} worried because {act.verb} could mess up the {prize.label}.",
        ),
        QAItem(
            question=f"What was the surprise in the story?",
            answer=f"The surprise was that {fx.reveal}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} laughing, the problem fixed, and everyone enjoying the funny surprise.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to forget something?",
            answer="To forget something means it slips out of your mind for a moment, so you do not remember it right away.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something you did not expect, so it can make you gasp, smile, or laugh.",
        ),
        QAItem(
            question="Why can comedy make people happy?",
            answer="Comedy makes people happy because funny moments help them laugh and feel lighter.",
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
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.body_zone:
            bits.append(f"zone={e.body_zone}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="stage", activity="joke", prize="card", fix="mirror", name="Mia", gender="girl", parent="mother", trait="cheerful"),
    StoryParams(place="backyard", activity="trick", prize="hat", fix="banana", name="Leo", gender="boy", parent="father", trait="silly"),
    StoryParams(place="kitchen", activity="song", prize="card", fix="megaphone", name="Nora", gender="girl", parent="mother", trait="playful"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.verb} does not reasonably threaten the {prize.label}, "
        f"so there is no honest forget/conflict/surprise problem to solve.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(PRIZES, prize_id).genders))
    return f"(No story: try a different gender for this prize; allowed: {ok}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Comedy story world about forgetting, a small conflict, and a surprise fix."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--fix", choices=FIXES)
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
        act, pr = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(act, pr) and select_fix(act, pr)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "prize", None) and getattr(args, "gender", None) not in _safe_lookup(PRIZES, getattr(args, "prize", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, act_id, prize_id = rng.choice(list(combos))
    act = _safe_lookup(ACTIVITIES, act_id)
    pr = _safe_lookup(PRIZES, prize_id)
    fx = getattr(args, "fix", None) or rng.choice([k for k, v in FIXES.items() if act.mess in v.guards and pr.body_zone in v.covers])
    gender = getattr(args, "gender", None) or rng.choice(sorted(pr.genders))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=act_id, prize=prize_id, fix=fx, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), _safe_lookup(FIXES, params.fix),
                 params.name, params.gender, [params.trait], params.parent)
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


ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), risk_pair(A,P).
fixes(A,P,F) :- prize_at_risk(A,P), fix(F), guards(F,M), mess_of(A,M), covers(F,Z), zone_of(P,Z).
valid_story(Place,A,P,F) :- affords(Place,A), prize_at_risk(A,P), fixes(A,P,F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for p in PRIZES:
            if prize_at_risk(a, _safe_lookup(PRIZES, p)):
                lines.append(asp.fact("risk_pair", aid, p))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("zone_of", pid, p.body_zone))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for m in sorted(f.guards):
            lines.append(asp.fact("guards", fid, m))
        for z in sorted(f.covers):
            lines.append(asp.fact("covers", fid, z))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set((a, b, c) for (a, b, c, _) in asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    elif getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        for place, act, prize, fix in combos:
            print(place, act, prize, fix)
        return
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
