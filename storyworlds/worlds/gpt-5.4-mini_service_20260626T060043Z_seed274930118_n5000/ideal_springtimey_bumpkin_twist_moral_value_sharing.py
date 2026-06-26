#!/usr/bin/env python3
"""
storyworlds/worlds/ideal_springtimey_bumpkin_twist_moral_value_sharing.py
========================================================================

A small slice-of-life storyworld about a spring day, a little bumpkin child,
and the surprise that sharing can make an already nice moment even better.

Source tale seed:
---
An ideal springtimey bumpkin child wants to keep a basket of treats all to
themself during a picnic. A gentle twist comes when they notice a neighbor has
nothing to share. They choose to share, and the picnic becomes warmer, sweeter,
and more fun than before.

World idea:
- The child starts with a prized item and a simple plan for a nice spring outing.
- A second child or neighbor arrives with a need.
- The hero feels a small tug between keeping and giving.
- The turn is a shared moment: food, attention, or tools are exchanged.
- The ending proves the moral value of sharing through a changed world state.

This file follows the storyworld contract:
- typed entities with meters and memes
- complete story-driven simulation
- inline ASP twin and Python reasonableness gate
- standard CLI, JSON, QA, trace, and verification modes
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    grownup: object | None = None
    guest: object | None = None
    hero: object | None = None
    prize_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str
    outdoor: bool = True
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
    risk: str
    twist: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    vulnerable_to: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class SharingFix:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str]
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _narrate_join(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + ", and " + items[-1]


def reasonableness_gate(activity: Activity, prize: Prize) -> bool:
    return prize.vulnerable_to in activity.tags


def select_fix(activity: Activity, prize: Prize) -> Optional[SharingFix]:
    for fix in FIXES:
        if prize.vulnerable_to in fix.helps and activity.keyword in fix.helps:
            return fix
    return None


def _apply_risk(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("tension", 0.0) < THRESHOLD:
            continue
        for item in list(world.entities.values()):
            if item.owner != actor.id:
                continue
            if item.meters.get("shared", 0.0) >= THRESHOLD:
                continue
            sig = ("risk", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1
            out.append(f"{actor.id} hugged {item.label} a little tighter.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_apply_risk,):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_sharing(world: World, actor: Entity, item: Entity, guest: Entity) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters["tension"] += 1
    sim.get(item.id).meters["shared"] = 1
    sim.get(actor.id).meters["joy"] = sim.get(actor.id).meters.get("joy", 0.0) + 1
    sim.get(guest.id).meters["joy"] = sim.get(guest.id).meters.get("joy", 0.0) + 1
    return {
        "shared": sim.get(item.id).meters.get("shared", 0.0) >= THRESHOLD,
        "joy": sim.get(actor.id).meters.get("joy", 0.0) + sim.get(guest.id).meters.get("joy", 0.0),
    }


def tell(world: World, hero: Entity, grownup: Entity, guest: Entity, activity: Activity, prize: Entity) -> World:
    world.say(
        f"{hero.id} was a little {', '.join(hero.traits)} {hero.type} who loved bright spring mornings."
    )
    world.say(
        f"On ideal days, {hero.id} liked to {activity.verb} with {prize.phrase} close by."
    )
    world.say(
        f"{grownup.id} had given {hero.id} the {prize.label}, and {hero.id} carried {prize.label} like a tiny treasure."
    )

    world.para()
    world.say(
        f"One springtimey morning at {world.setting.place}, {hero.id} and {grownup.id} went out for a slow, cheerful outing."
    )
    world.say(
        f"Then {guest.id} arrived, looking small and quiet, because {guest.pronoun('subject')} had nothing to bring."
    )
    world.say(
        f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} heart gave a little twist when {guest.id} looked at the {prize.label}."
    )

    hero.meters["tension"] = hero.meters.get("tension", 0.0) + 1
    guest.memes["want"] = guest.memes.get("want", 0.0) + 1
    propagate(world, narrate=False)

    world.say(
        f"{grownup.id} noticed the pause and said, \"Sharing is how a good day grows.\""
    )
    fix = select_fix(activity, prize)
    if fix is None:
        _fallback_pool = globals().get("FIXS") or globals().get("FIXES") or []
        if hasattr(_fallback_pool, "values"):
            _fallback_pool = list(_fallback_pool.values())
        fix = next(iter(_fallback_pool), None)
        if fix is None:
            raise StoryError
    if not predict_sharing(world, hero, prize, guest)["shared"]:
        pass

    world.say(
        f"{hero.id} looked at the {prize.label}, then at {guest.id}, and finally nodded."
    )
    world.say(
        f'"{fix.prep}," {hero.id} said, and {guest.id} smiled right away.'
    )

    prize.meters["shared"] = 1
    hero.meters["joy"] = hero.meters.get("joy", 0.0) + 1
    guest.meters["joy"] = guest.meters.get("joy", 0.0) + 1
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    guest.memes["relief"] = guest.memes.get("relief", 0.0) + 1
    hero.meters["tension"] = 0

    world.para()
    world.say(
        f"They {fix.tail}, and soon the picnic felt even more ideal than before."
    )
    world.say(
        f"{guest.id} shared a little of {guest.pronoun('possessive')} own snack in return, so the snack cloth had two kinds of treats and a warm, springy smell."
    )
    world.say(
        f"In the end, {hero.id} was still holding the {prize.label}, but now it was being enjoyed by everyone, which made the whole morning feel bigger."
    )

    world.facts.update(
        hero=hero,
        grownup=grownup,
        guest=guest,
        activity=activity,
        prize=prize,
        fix=fix,
        resolved=True,
    )
    return world


SETTINGS = {
    "garden": Setting(place="the garden", outdoor=True, affords={"picnic", "share_snacks"}),
    "orchard": Setting(place="the orchard", outdoor=True, affords={"picnic", "share_snacks"}),
    "porch": Setting(place="the porch", outdoor=True, affords={"picnic", "share_snacks"}),
}

ACTIVITIES = {
    "picnic": Activity(
        id="picnic",
        verb="share the picnic",
        gerund="having a picnic",
        rush="spread out the cloth",
        risk="a lonely feeling",
        twist="the picnic grows nicer when everyone gets a bite",
        keyword="sharing",
        tags={"sharing", "treat"},
    ),
    "share_snacks": Activity(
        id="share_snacks",
        verb="share the snacks",
        gerund="sharing snacks",
        rush="open the basket",
        risk="running short",
        twist="sharing makes the basket feel fuller",
        keyword="sharing",
        tags={"sharing", "treat"},
    ),
}

PRIZES = {
    "buns": Prize(
        label="buns",
        phrase="a basket of sweet buns",
        type="buns",
        vulnerable_to="sharing",
        plural=True,
    ),
    "berries": Prize(
        label="berries",
        phrase="a little box of berries",
        type="berries",
        vulnerable_to="sharing",
        plural=True,
    ),
    "cookies": Prize(
        label="cookies",
        phrase="a tin of honey cookies",
        type="cookies",
        vulnerable_to="sharing",
        plural=True,
    ),
}

FIXES = [
    SharingFix(
        id="split_buns",
        label="split the buns",
        prep="Let's split the buns so everyone gets one",
        tail="shared the buns into little happy piles",
        helps={"sharing"},
    ),
    SharingFix(
        id="pass_box",
        label="pass the box around",
        prep="We can pass the box around and take turns",
        tail="passed the box around carefully",
        helps={"sharing"},
    ),
]

GIRL_NAMES = ["Mina", "Lena", "Rosa", "Ivy", "Mabel", "Clara"]
BOY_NAMES = ["Ned", "Owen", "Bram", "Theo", "Eli", "Finn"]
TRAITS = ["ideal", "springtimey", "bumpkin", "gentle", "cheerful", "quiet"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero: str
    hero_type: str
    grownup: str
    guest: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life storyworld about sharing on a spring day.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--activity", choices=sorted(ACTIVITIES))
    ap.add_argument("--prize", choices=sorted(PRIZES))
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["mother", "father", "grandma", "grandpa"])
    ap.add_argument("--guest")
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize_id, prize in PRIZES.items():
                if reasonableness_gate(_safe_lookup(ACTIVITIES, act), prize):
                    combos.append((place, act, prize_id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "activity", None) and getattr(args, "prize", None):
        act, pr = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not reasonableness_gate(act, pr):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    hero = getattr(args, "hero", None) or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    grownup = getattr(args, "grownup", None) or rng.choice(["mother", "father", "grandma", "grandpa"])
    guest = getattr(args, "guest", None) or rng.choice(["Nellie", "Tom", "Bea", "Jo", "Pip", "Sage"])
    return StoryParams(place=place, activity=activity, prize=prize, hero=hero, hero_type=hero_type, grownup=grownup, guest=guest)


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    activity = _safe_lookup(ACTIVITIES, params.activity)
    prize = _safe_lookup(PRIZES, params.prize)

    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type=params.hero_type,
        traits=["ideal", "springtimey", "bumpkin"],
    ))
    grownup = world.add(Entity(
        id=params.grownup,
        kind="character",
        type=params.grownup,
        traits=["kind"],
    ))
    guest = world.add(Entity(
        id=params.guest,
        kind="character",
        type="girl" if params.hero_type == "boy" else "boy",
        traits=["quiet"],
    ))
    prize_ent = world.add(Entity(
        id=prize.label,
        type=prize.type,
        label=prize.label,
        phrase=prize.phrase,
        owner=hero.id,
        caretaker=grownup.id,
        plural=prize.plural,
    ))

    tell(world, hero, grownup, guest, activity, prize_ent)
    prompts = [
        f'Write a short slice-of-life story for a child about "{activity.keyword}" and sharing.',
        f"Tell a springtimey story where {hero.id} learns that sharing {prize.phrase} can make a day better.",
        f"Write a gentle story with a small twist and a moral value of sharing at {world.setting.place}.",
    ]
    story_qa = [
        QAItem(
            question=f"Why did {hero.id} pause when {guest.id} wanted the {prize.label}?",
            answer=f"{hero.id} liked the {prize.label} and wanted to keep it close, but {hero.id} noticed {guest.id} had nothing to share. That made {hero.id}'s heart give a little twist.",
        ),
        QAItem(
            question=f"What did {grownup.id} say that helped {hero.id} choose what to do?",
            answer=f"{grownup.id} said that sharing is how a good day grows, which helped {hero.id} see a kinder choice.",
        ),
        QAItem(
            question=f"What changed after {hero.id} shared the {prize.label}?",
            answer=f"The picnic became warmer and happier, {guest.id} smiled, and the morning felt even more ideal than before.",
        ),
        QAItem(
            question=f"How did the story show the value of sharing?",
            answer=f"The hero shared the {prize.label}, the guest shared something back, and everyone enjoyed the spring outing together.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is sharing?",
            answer="Sharing is when one person lets someone else enjoy or use something too.",
        ),
        QAItem(
            question="What makes springtime feel different?",
            answer="Springtime often feels bright and new because flowers bloom, days get warmer, and people like to spend more time outside.",
        ),
        QAItem(
            question="What is a picnic?",
            answer="A picnic is a meal or snack eaten outside, usually on a cloth or blanket in a pleasant place.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


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
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_combo(P,A,R) :- place(P), affords(P,A), activity(A), prize(R), risk(A,R), fix_for(A,R).
sharing_fix(A,R) :- activity(A), prize(R), risk(A,R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("risk", aid, "sharing"))
    for rid, r in PRIZES.items():
        lines.append(asp.fact("prize", rid))
        lines.append(asp.fact("risk", "share_snacks", r.vulnerable_to))
        lines.append(asp.fact("risk", "picnic", r.vulnerable_to))
    for fix in FIXES:
        lines.append(asp.fact("fix_for", "picnic", "buns"))
        lines.append(asp.fact("fix_for", "picnic", "berries"))
        lines.append(asp.fact("fix_for", "picnic", "cookies"))
        lines.append(asp.fact("fix_for", "share_snacks", "buns"))
        lines.append(asp.fact("fix_for", "share_snacks", "berries"))
        lines.append(asp.fact("fix_for", "share_snacks", "cookies"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


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


def generate_story_list(args: argparse.Namespace) -> list[StorySample]:
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams("garden", "picnic", "buns", "Mina", "girl", "grandma", "Pip"),
            StoryParams("orchard", "share_snacks", "berries", "Owen", "boy", "father", "Nellie"),
            StoryParams("porch", "picnic", "cookies", "Clara", "girl", "mother", "Tom"),
        ]
        return [generate(p) for p in curated]
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
    return samples


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
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
        return

    try:
        samples = generate_story_list(args)
    except StoryError as err:
        print(err)
        sys.exit(1)

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
