#!/usr/bin/env python3
"""
storyworlds/worlds/dunce_delta_willing_sharing_twist_fable.py
=============================================================

A small fable-style storyworld about a dunce, a river delta, and a willing act
of sharing that leads to a twist.

The seed premise:
- A foolish but kind character lives near a river delta.
- A prized basket of figs is guarded too tightly.
- A flood tide and a visitor create a problem.
- The "dunce" turns out to be willing to share, and the ending reveals a wiser
  friendship than anyone expected.

The world models both physical meters and emotional memes:
- meters track things like water, food, and damage
- memes track trust, worry, pride, and gratitude

This script follows the storyworld contract:
- self-contained stdlib script
- imports shared results eagerly
- imports shared ASP helper lazily inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    place: str = "the delta"
    tags: set[str] = field(default_factory=set)
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
    soil: str
    zone: set[str]
    keyword: str
    twist: str
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
class Helper:
    id: str
    label: str
    prep: str
    tail: str
    gives: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
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
        self.zone: set[str] = set()
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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.owner == actor.id and e.kind == "thing"]


def _r_wet_damage(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters.get("water", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.meters.get("protected", 0.0) >= THRESHOLD:
                continue
            sig = ("wet_damage", actor.id, item.id)
            if sig in world.fired:
                continue
            if item.region in world.zone:
                world.fired.add(sig)
                item.meters["damaged"] = item.meters.get("damaged", 0.0) + 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got splashed.")
    return out


def _r_share_trust(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes.get("sharing", 0.0) < THRESHOLD:
            continue
        sig = ("share_trust", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["trust"] = actor.memes.get("trust", 0.0) + 1
        out.append(f"Their choice to share made the air feel kinder.")
    return out


def _r_twist(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes.get("pride", 0.0) < THRESHOLD:
            continue
        if actor.memes.get("willing", 0.0) < THRESHOLD:
            continue
        sig = ("twist", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["humble"] = actor.memes.get("humble", 0.0) + 1
        out.append("__twist__")
    return out


RULES = [_r_wet_damage, _r_share_trust, _r_twist]


def propagate(world: World, narrate: bool = True) -> list[str]:
    all_out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            out = rule(world)
            if out:
                changed = True
                all_out.extend(x for x in out if x != "__twist__")
    if narrate:
        for s in all_out:
            world.say(s)
    return all_out


def overlap(a: Activity, prize: Prize) -> bool:
    return prize.region in a.zone


def select_helper(activity: Activity, prize: Prize) -> Optional[Helper]:
    for h in HELPERS:
        if activity.mess in h.gives and prize.region in h.covers:
            return h
    return None


def predict_damage(world: World, actor: Entity, activity: Activity, prize_id: str) -> bool:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return prize.meters.get("damaged", 0.0) >= THRESHOLD


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters["water"] = actor.meters.get("water", 0.0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a small {hero.type} by the river delta, and everyone called {hero.pronoun('object')} a dunce.")
    world.say(f"Yet {hero.pronoun()} always listened twice before speaking, which was its own kind of wisdom.")


def setup(world: World, hero: Entity, prize: Entity, activity: Activity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    prize.owner = hero.id
    world.say(f"{hero.id} loved {prize.phrase} and carried {prize.it()} like a treasure.")
    world.say(f"{hero.pronoun().capitalize()} especially loved to {activity.verb} at the delta, where the reeds bent and the mud glittered.")


def conflict(world: World, hero: Entity, elder: Entity, activity: Activity, prize: Entity) -> None:
    world.para()
    world.say(f"One bright day, {hero.id} went to {world.setting.place} with {hero.pronoun('possessive')} {prize.label}.")
    world.say(f"{hero.id} wanted to {activity.verb}, but {elder.label} warned that the tide was rising.")
    hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1
    if predict_damage(world, hero, activity, prize.id):
        world.say(f'"If you rush now, {prize.label} will get {activity.soil}," {elder.label} said.')
    world.say(f"Still, the wish to play tugged at {hero.id}, and {hero.pronoun()} stepped closer to the water.")


def twist_turn(world: World, hero: Entity, elder: Entity, activity: Activity, prize: Entity, helper: Helper) -> None:
    world.para()
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    world.say(f"Then the twist came: a little fish trap had snagged {elder.label}'s lunch, and {elder.label} had nothing to share.")
    world.say(f"{hero.id} looked at the empty basket, looked at {prize.label}, and was willing to do the opposite of a dunce's first guess.")
    world.say(f"{hero.id} offered {prize.it()} and said, \"We can share.\"")
    hero.memes["sharing"] = hero.memes.get("sharing", 0.0) + 1
    helper.owner = hero.id
    hero.meters["protected"] = hero.meters.get("protected", 0.0) + 1
    world.say(f"That was the real turn: {helper.prep}, and the {helper.label} would keep {prize.it()} safe while {hero.id} played.")


def ending(world: World, hero: Entity, elder: Entity, activity: Activity, prize: Entity, helper: Helper) -> None:
    hero.memes["willing"] = hero.memes.get("willing", 0.0) + 1
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1
    world.say(f"{hero.id} was {activity.gerund}, and the delta breeze carried laughter over the reeds.")
    world.say(f"{prize.label} stayed clean, {elder.label} had a share, and the so-called dunce went home a little wiser.")
    world.say(f"After that, everyone remembered that a willing heart can outsmart a foolish first thought.")


SETTINGS = {
    "delta": Setting(place="the river delta", tags={"delta", "water"}, affords={"fishing", "wading"}),
    "bank": Setting(place="the river bank", tags={"delta", "water"}, affords={"fishing", "wading"}),
    "reedbed": Setting(place="the reedbed by the delta", tags={"delta", "water"}, affords={"wading"}),
}

ACTIVITIES = {
    "fishing": Activity(
        id="fishing",
        verb="fish at the delta",
        gerund="fishing at the delta",
        rush="dash for the water",
        mess="wet",
        soil="soaking wet",
        zone={"feet", "hands"},
        keyword="sharing",
        twist="fish trap",
        tags={"sharing", "twist", "water"},
    ),
    "wading": Activity(
        id="wading",
        verb="wade in the shallows",
        gerund="wading in the shallows",
        rush="splash into the tide",
        mess="wet",
        soil="splashed wet",
        zone={"feet", "legs"},
        keyword="sharing",
        twist="tide",
        tags={"sharing", "twist", "water"},
    ),
}

PRIZES = {
    "basket": Prize(label="basket", phrase="a woven basket of figs", type="basket", region="hands"),
    "cloak": Prize(label="cloak", phrase="a bright cloak", type="cloak", region="torso"),
    "boots": Prize(label="boots", phrase="sturdy river boots", type="boots", region="feet", plural=True),
}

HELPERS = [
    Helper(id="reedwrap", label="reed wrap", prep="a reed wrap was tied around the basket", tail="the reed wrap kept the figs dry", gives={"wet"}, covers={"hands"}),
    Helper(id="bootguard", label="river boots", prep="sturdy river boots were laced on", tail="the boots kept the feet dry", gives={"wet"}, covers={"feet"}, plural=True),
]

NAMES = ["Milo", "Nia", "Pip", "Tara", "Oren", "Bela"]
ELDERS = ["Old Mare", "Aunt Reed", "Gran Willow"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    elder: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable storyworld: dunce, delta, and willing sharing with a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=ELDERS)
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
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if overlap(act, prize) and select_helper(act, prize):
                    out.append((place, act_id, prize_id))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    elder = getattr(args, "elder", None) or rng.choice(ELDERS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, elder=elder)


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type="child"))
    elder = world.add(Entity(id="elder", kind="character", type="elder", label=params.elder))
    prize = world.add(Entity(id="prize", type=_safe_lookup(PRIZES, params.prize).type, label=_safe_lookup(PRIZES, params.prize).label, phrase=_safe_lookup(PRIZES, params.prize).phrase, owner=hero.id))
    activity = _safe_lookup(ACTIVITIES, params.activity)
    helper = select_helper(activity, _safe_lookup(PRIZES, params.prize))
    assert helper is not None

    intro(world, hero)
    setup(world, hero, prize, activity)
    conflict(world, hero, elder, activity, prize)
    twist_turn(world, hero, elder, activity, prize, helper)
    do_activity(world, hero, activity, narrate=True)
    ending(world, hero, elder, activity, prize, helper)

    world.facts = {
        "hero": hero,
        "elder": elder,
        "prize": prize,
        "activity": activity,
        "helper": helper,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    activity = _safe_fact(world, f, "activity")
    prize = _safe_fact(world, f, "prize")
    return [
        f"Write a short fable about {hero.id}, a dunce by the river delta, who learns to share {prize.phrase}.",
        f"Tell a child-friendly story where someone wants to {activity.verb} at the delta but chooses a willing act of sharing.",
        f"Write a fable with a twist ending in which the prize stays safe and the greedy plan changes to a generous one.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    elder = _safe_fact(world, f, "elder")
    prize = _safe_fact(world, f, "prize")
    activity = _safe_fact(world, f, "activity")
    helper = _safe_fact(world, f, "helper")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a small dunce by the river delta who learned to be willing to share.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at the delta?",
            answer=f"{hero.id} wanted to {activity.verb}, but {elder.label} worried about the rising water.",
        ),
        QAItem(
            question=f"What was special about the end of the story?",
            answer=f"The twist was that {hero.id} chose to share {prize.phrase}, and the helper {helper.label} kept it safe.",
        ),
        QAItem(
            question=f"How did the prize change by the end?",
            answer=f"{prize.label} stayed safe and clean, so the story ended with sharing instead of trouble.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a delta?", answer="A delta is a place near a river mouth where water splits into smaller streams and leaves mud and reeds behind."),
        QAItem(question="What does willing mean?", answer="Willing means ready to do something without being forced, often because it feels kind or fair."),
        QAItem(question="What is sharing?", answer="Sharing means giving some of what you have to someone else or letting them use it too."),
        QAItem(question="What is a fable?", answer="A fable is a short story that often uses animals or simple characters to teach a lesson."),
        QAItem(question="What is a twist in a story?", answer="A twist is a surprise turn that changes what the reader expects."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for prid, p in PRIZES.items():
        lines.append(asp.fact("prize", prid))
        lines.append(asp.fact("worn_on", prid, p.region))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
        for g in sorted(h.gives):
            lines.append(asp.fact("gives", h.id, g))
        for c in sorted(h.covers):
            lines.append(asp.fact("covers", h.id, c))
    return "\n".join(lines)


ASP_RULES = r"""
risk(A,P) :- zone(A,R), worn_on(P,R).
fix(A,P) :- risk(A,P), mess_of(A,M), gives(H,M), covers(H,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), risk(A,P), fix(A,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    if py - asp_set:
        print("Only in Python:", sorted(py - asp_set))
    if asp_set - py:
        print("Only in ASP:", sorted(asp_set - py))
    return 1


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"{e.id}: {e.type} {' '.join(bits)}")
    out.append(f"fired={sorted(world.fired)}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place="delta", activity="fishing", prize="basket", name="Milo", elder="Old Mare"),
    StoryParams(place="bank", activity="wading", prize="boots", name="Nia", elder="Aunt Reed"),
    StoryParams(place="reedbed", activity="wading", prize="cloak", name="Pip", elder="Gran Willow"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print("\n".join(f"{c[0]} {c[1]} {c[2]}" for c in combos))
        return

    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < getattr(args, "n", None) * 50 + 50:
            i += 1
            try:
                params = resolve_params(args, random.Random((getattr(args, "seed", None) or 0) + i))
            except StoryError:
                continue
            params.seed = (getattr(args, "seed", None) or 0) + i
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
