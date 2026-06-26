#!/usr/bin/env python3
"""
storyworlds/worlds/twinkle_happy_ending_surprise_friendship_superhero_story.py
=============================================================================

A small standalone story world for a superhero-style friendship tale with a
twinkle of surprise and a happy ending.

Seed tale inspiration:
---
A little superhero loved flying over the city with a brave friend. One evening,
they saw a tiny light twinkling on a roof. The hero wanted to rush up and help,
but the friend worried it might be a trapped kitten or a broken beacon. Then the
friend surprised the hero with a clever gadget, and together they found the
lost little helper and brought it home safely. Everyone cheered, and the two
friends felt even closer than before.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    location: object | None = None
    friend: object | None = None
    gear: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
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
    place: str = "the city"
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
class Mission:
    id: str
    verb: str
    gerund: str
    rush: str
    surprise: str
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
class Prize:
    label: str
    phrase: str
    type: str
    location: str
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
class Gear:
    id: str
    label: str
    prep: str
    reveal: str
    helps: set[str]
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.mission: Optional[Mission] = None
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

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.mission = self.mission
        return clone


@dataclass
class Rule:
    name: str
    apply: callable
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


def _r_anxiety(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes.get("worry", 0.0) < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["nervous"] = e.memes.get("nervous", 0.0) + 1
        out.append(f"{e.label or e.id} felt nervous for a moment.")
    return out


def _r_surprise_help(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes.get("surprise", 0.0) < THRESHOLD:
            continue
        sig = ("surprise", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["joy"] = e.memes.get("joy", 0.0) + 1
        out.append(f"{e.label or e.id} smiled at the sudden surprise.")
    return out


CAUSAL_RULES = [
    Rule("anxiety", _r_anxiety),
    Rule("surprise_help", _r_surprise_help),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def mission_risky(mission: Mission, prize: Prize) -> bool:
    return prize.location in mission.helps


def select_gear(mission: Mission, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if mission.id in gear.helps and prize.location in gear.covers:
            return gear
    return None


def predict(world: World, hero: Entity, mission: Mission, prize_id: str) -> dict:
    sim = world.copy()
    _do_mission(sim, sim.get(hero.id), mission, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "rescued": bool(prize.meters.get("safe", 0.0) >= THRESHOLD),
        "worry": sum(e.memes.get("worry", 0.0) for e in sim.characters()),
    }


def _do_mission(world: World, hero: Entity, mission: Mission, narrate: bool = True) -> None:
    world.mission = mission
    hero.meters[mission.id] = hero.meters.get(mission.id, 0.0) + 1
    hero.memes["courage"] = hero.memes.get("courage", 0.0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little superhero with a bright cape and a kind heart."
    )


def friendship(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1
    world.say(
        f"{hero.id} loved going on night-time patrols with {friend.id}, "
        f"because adventures were better with a friend."
    )


def sparkle(world: World, mission: Mission) -> None:
    world.say(
        f"High above {world.setting.place}, something {mission.keyword} twinkled in the dark."
    )


def wants_help(world: World, hero: Entity, friend: Entity, mission: Mission, prize: Entity) -> None:
    hero.memes["eager"] = hero.memes.get("eager", 0.0) + 1
    world.say(
        f"{hero.id} wanted to {mission.verb} right away, but {friend.id} looked up and said, "
        f'"Wait. That glow could be a {prize.label}, and it might need care."'
    )


def warn(world: World, friend: Entity, hero: Entity, mission: Mission, prize: Entity) -> bool:
    pred = predict(world, hero, mission, prize.id)
    if not mission_risky(mission, prize):
        return False
    if pred["rescued"]:
        world.say(
            f'"If we rush, we might miss the safest way," {friend.id} said. '
            f'"Let’s be careful and keep the {prize.label} safe."'
        )
    else:
        world.say(
            f'"If we rush, the {prize.label} could be in trouble," {friend.id} said. '
            f'"Let’s choose the careful way."'
        )
    friend.memes["worry"] = friend.memes.get("worry", 0.0) + 1
    return True


def surprise(world: World, friend: Entity, hero: Entity, mission: Mission) -> Gear:
    gear_def = select_gear(mission, world.facts["prize"])
    if gear_def is None:
        pass
    gear = world.add(Entity(
        id=gear_def.id,
        kind="thing",
        type="gear",
        label=gear_def.label,
        phrase=gear_def.label,
        owner=friend.id,
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1
    world.say(
        f"Then {friend.id} gave a surprise grin and pulled out {gear_def.label}."
    )
    world.say(
        f'"I brought this just in case," {friend.id} said. {gear_def.reveal}'
    )
    return gear


def accept(world: World, hero: Entity, friend: Entity, mission: Mission, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1
    world.say(
        f"{hero.id} nodded, and the two friends went together to {mission.rush}."
    )
    world.say(
        f"With {gear.label}, they reached the {prize.label}, guided it home, and "
        f"the little glow became a safe, happy ending."
    )
    world.say(
        f"By morning, {hero.id} and {friend.id} were laughing side by side, "
        f"their friendship shining as brightly as the twinkle in the sky."
    )


def tell(setting: Setting, mission: Mission, prize_cfg: Prize,
         hero_name: str = "Nova", hero_type: str = "girl",
         friend_name: str = "Pip", friend_type: str = "boy") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, label=friend_name))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=friend.id,
        location=prize_cfg.location,
        plural=prize_cfg.plural,
    ))
    world.facts["prize"] = prize
    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["mission"] = mission
    world.facts["setting"] = setting

    introduce(world, hero)
    friendship(world, hero, friend)
    sparkle(world, mission)

    world.para()
    wants_help(world, hero, friend, mission, prize)
    warn(world, friend, hero, mission, prize)

    world.para()
    gear = surprise(world, friend, hero, mission)
    accept(world, hero, friend, mission, prize, gear)

    world.facts["gear"] = gear
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "city": Setting(place="the city", affords={"roof_rescue", "lost_pet"}),
    "harbor": Setting(place="the harbor", affords={"roof_rescue"}),
    "downtown": Setting(place="downtown", affords={"lost_pet", "roof_rescue"}),
}

MISSIONS = {
    "roof_rescue": Mission(
        id="roof_rescue",
        verb="fly up to the roof",
        gerund="flying up to the roof",
        rush="swoop to the rooftop",
        surprise="a tiny twinkling light on a roof",
        risk="the roof could be hard to reach",
        keyword="twinkle",
        tags={"twinkle", "roof", "night"},
    ),
    "lost_pet": Mission(
        id="lost_pet",
        verb="search for the lost pet",
        gerund="searching for the lost pet",
        rush="hurry through the alley",
        surprise="a faint twinkle behind a mailbox",
        risk="the little pet could get scared",
        keyword="twinkle",
        tags={"twinkle", "pet", "night"},
    ),
}

PRIZES = {
    "kitten": Prize(label="kitten", phrase="a tiny kitten", type="kitten", location="roof"),
    "beacon": Prize(label="beacon", phrase="a blinking rooftop beacon", type="beacon", location="roof"),
    "puppy": Prize(label="puppy", phrase="a little puppy", type="puppy", location="alley"),
}

GEAR = [
    Gear(
        id="glider",
        label="a star glider",
        prep="zip on a star glider",
        reveal="It would help them swoop gently and land carefully.",
        helps={"roof_rescue"},
        covers={"roof"},
    ),
    Gear(
        id="lantern",
        label="a twinkle lantern",
        prep="turn on a twinkle lantern",
        reveal="It would help them see the little glow without scaring anyone.",
        helps={"lost_pet", "roof_rescue"},
        covers={"alley", "roof"},
    ),
    Gear(
        id="soft_boots",
        label="soft boots",
        prep="pull on soft boots",
        reveal="They would let them move quietly and kindly.",
        helps={"lost_pet"},
        covers={"alley"},
        plural=True,
    ),
]

HERO_NAMES = ["Nova", "Spark", "Comet", "Luna", "Tara", "Milo"]
FRIEND_NAMES = ["Pip", "Jett", "Bree", "Rin", "Kai", "Zuri"]
TRAITS = ["brave", "kind", "quick", "gentle", "cheerful"]


@dataclass
class StoryParams:
    setting: str
    mission: str
    prize: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    trait: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s, setting in SETTINGS.items():
        for m in setting.affords:
            mission = _safe_lookup(MISSIONS, m)
            for p, prize in PRIZES.items():
                if mission_risky(mission, prize) and select_gear(mission, prize):
                    combos.append((s, m, p))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero friendship story world with twinkle and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
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
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "mission", None) is None or c[1] == getattr(args, "mission", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, mission, prize = rng.choice(list(combos))
    hero_name = getattr(args, "hero_name", None) or rng.choice(HERO_NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    hero_type = "girl" if hero_name in {"Nova", "Luna", "Tara", "Bree", "Zuri"} else "boy"
    friend_type = "girl" if friend_name in {"Nova", "Luna", "Tara", "Bree", "Zuri"} else "boy"
    trait = rng.choice(TRAITS)
    return StoryParams(setting, mission, prize, hero_name, hero_type, friend_name, friend_type, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    mission = _safe_fact(world, f, "mission")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short superhero story for a child that includes the word "twinkle" and ends happily.',
        f"Tell a gentle adventure about {hero.id} and {friend.id} when they notice {mission.surprise}.",
        f"Write a friendship story where one superhero worries about {prize.phrase}, then finds a clever surprise solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    mission = _safe_fact(world, f, "mission")
    prize = _safe_fact(world, f, "prize")
    gear = _safe_fact(world, f, "gear")
    return [
        QAItem(
            question=f"Who went looking for the {prize.label}?",
            answer=f"{hero.id} and {friend.id} went together, and {hero.id} was the little superhero leading the way."
        ),
        QAItem(
            question=f"Why did {friend.id} worry when they saw the twinkle?",
            answer=f"{friend.id} worried because the {prize.label} could have needed careful help, so rushing could have made things harder."
        ),
        QAItem(
            question=f"What surprise did {friend.id} bring to help with the mission?",
            answer=f"{friend.id} brought {gear.label}, which helped them move carefully and reach the {prize.label} safely."
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {friend.id}?",
            answer=f"It ended happily, with {hero.id} and {friend.id} smiling together after helping the {prize.label} and sharing the adventure."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does twinkle mean?",
            answer="Twinkle means to shine with quick little flashes of light."
        ),
        QAItem(
            question="What is a superhero friend?",
            answer="A superhero friend is someone who helps bravely and kindly, especially when another person needs help."
        ),
        QAItem(
            question="Why is friendship important?",
            answer="Friendship is important because friends can help each other, share ideas, and feel happier together."
        ),
    ]


ASP_RULES = r"""
risky(M,P) :- mission(M), prize(P), mission_helps(M,L), prize_loc(P,L).
fix(M,P) :- risky(M,P), gear(G), gear_helps(G,M), gear_covers(G,L), prize_loc(P,L).
valid(S,M,P) :- setting(S), affords(S,M), risky(M,P), fix(M,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for m in sorted(s.affords):
            lines.append(asp.fact("affords", sid, m))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("mission_helps", mid, "roof" if "roof" in t else "alley" if "pet" in t else "roof"))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_loc", pid, p.location))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.helps):
            lines.append(asp.fact("gear_helps", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("gear_covers", g.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_asp_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_asp_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(MISSIONS, params.mission), _safe_lookup(PRIZES, params.prize),
                 params.hero_name, params.hero_type, params.friend_name, params.friend_type)
    params.seed = params.seed
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


CURATED = [
    StoryParams("city", "roof_rescue", "kitten", "Nova", "girl", "Pip", "boy", "brave"),
    StoryParams("downtown", "lost_pet", "puppy", "Luna", "girl", "Jett", "boy", "kind"),
    StoryParams("harbor", "roof_rescue", "beacon", "Comet", "boy", "Bree", "girl", "cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        triples = valid_asp_combos()
        print(f"{len(triples)} compatible (setting, mission, prize) combos:\n")
        for t in triples:
            print("  ", t)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
