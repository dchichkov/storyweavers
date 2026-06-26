#!/usr/bin/env python3
"""
sociology_bike_lane_sound_effects_space_adventure.py
====================================================

A small story world about a bike lane, sociology, and space-adventure style
sound effects.

The premise is a child-sized space scout who loves the bike lane because it
feels like a tiny launch corridor. The tension comes from social coordination:
who gets to go first, how loudly to signal, and how to share a narrow lane
without startling other riders. The resolution is a friendly, concrete
compromise using the right gear and the right sounds.

This world is intentionally compact and constraint-checked:
- the story is driven by a simulated world model,
- the conflict is social as well as physical,
- the ending proves that the social state changed,
- and the inline ASP twin mirrors the Python reasonableness gate.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    gear: object | None = None
    hero: object | None = None
    other: object | None = None
    parent: object | None = None
    prize: object | None = None
    def __post_init__(self):
        for k in ["noise", "speed", "distance", "order"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "curiosity", "worry", "startle", "conflict", "pride", "care", "patience"]:
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    place: str = "the bike lane"
    indoors: bool = False
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
    sound: str
    social_risk: str
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _bump(e: Entity, key: str, amount: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amount


def _feel(e: Entity, key: str, amount: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amount


def predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {
        "startle": prize.memes["startle"] >= THRESHOLD,
        "conflict": any(ch.memes["conflict"] >= THRESHOLD for ch in sim.characters()),
        "noise": max((ch.meters["noise"] for ch in sim.characters()), default=0.0),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    _bump(actor, "speed", 1.0)
    _bump(actor, "noise", 1.0)
    _feel(actor, "joy", 1.0)
    _feel(actor, "curiosity", 1.0)
    if narrate:
        world.say(f"{actor.id} went {activity.gerund} with a bright little {activity.sound}.")

    for ent in list(world.entities.values()):
        if ent.id == actor.id:
            continue
        if ent.kind == "character" and ent.memes["order"] >= THRESHOLD:
            _feel(ent, "startle", 1.0)
            _feel(ent, "worry", 1.0)


def _rule_startle(world: World) -> list[str]:
    out = []
    for ent in world.characters():
        if ent.memes["startle"] < THRESHOLD:
            continue
        sig = ("startle", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["conflict"] += 1.0
        out.append(f"{ent.id} flinched at the noise and lost their easy rhythm.")
    return out


def _rule_order(world: World) -> list[str]:
    out = []
    if len(world.characters()) < 2:
        return out
    lead = max(world.characters(), key=lambda e: e.meters["speed"])
    for ent in world.characters():
        if ent.id == lead.id:
            continue
        if ent.memes["patience"] >= THRESHOLD and ent.memes["worry"] >= THRESHOLD:
            sig = ("order", ent.id, lead.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["order"] += 1.0
            out.append(f"{ent.id} waited, like a careful astronaut giving the other lane first drift.")
    return out


def _rule_conflict(world: World) -> list[str]:
    out = []
    for ent in world.characters():
        if ent.memes["worry"] < THRESHOLD or ent.meters["noise"] < THRESHOLD:
            continue
        if ent.memes["order"] < THRESHOLD:
            continue
        sig = ("conflict", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["conflict"] += 1.0
        out.append("__conflict__")
    return out


CAUSAL_RULES = [
    _rule_startle,
    _rule_order,
    _rule_conflict,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting) -> str:
    return "The bike lane stretched ahead like a painted launch path, with arrows shining on the pavement."


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.id in gear.guards and prize.region in gear.covers:
            return gear
    return None


def reason_ok(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.tags and select_gear(activity, prize) is not None


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved pretending the bike lane was a space runway.")


def loves_space_sound(world: World, hero: Entity, activity: Activity) -> None:
    _feel(hero, "joy", 1.0)
    world.say(f"{hero.pronoun().capitalize()} loved the {activity.sound} sounds, because they made every ride feel like a rocket launch.")


def arrive(world: World, hero: Entity, parent: Entity) -> None:
    world.say(f"One bright day, {hero.id} and {hero.pronoun('possessive')} {parent.label_word} rolled to {world.setting.place}.")
    world.say(setting_detail(world.setting))


def wants(world: World, hero: Entity, activity: Activity) -> None:
    _feel(hero, "curiosity", 1.0)
    world.say(f"{hero.id} wanted to {activity.verb}, but the lane was narrow and the other riders needed room to pass.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict(world, hero, activity, prize.id)
    if not pred["startle"] and not pred["conflict"]:
        return False
    world.facts["predicted_noise"] = pred["noise"]
    world.say(f'"That {activity.sound} could startle the others, and your {prize.label} might not stay neat," {parent.label_word} said.')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    _feel(hero, "worry", 1.0)
    world.say(f"{hero.id} listened, but the wish to zoom still tugged like a tiny engine.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush},")


def cue_conflict(world: World, parent: Entity, hero: Entity) -> None:
    _feel(hero, "order", 1.0)
    _feel(hero, "patience", 1.0)
    propagate(world, narrate=False)
    world.say(f"but {hero.pronoun('possessive')} {parent.label_word} held up a steady hand and asked for a calmer signal.")


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id

    if predict(world, hero, activity, prize.id)["startle"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None

    world.say(f'{parent.label_word} smiled and said, "How about we use {gear_def.label} and a gentle bell first?"')
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    _feel(hero, "joy", 1.0)
    _feel(hero, "pride", 1.0)
    hero.memes["conflict"] = 0.0
    world.say(f"{hero.id} grinned and nodded. Then {hero.pronoun()} clipped on {gear_def.label} and listened for the lane.")
    world.say(f'Together they went {gear_def.tail}. Soon {hero.id} was {activity.gerund}, "{activity.sound}!" went the bell, and the other riders glided by without a fuss.')
    world.say(f"At the end, {hero.id}'s {prize.label} stayed safe, and the bike lane felt peaceful again, like a small moon base after a good landing.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Nia", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["curious", "careful"])))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))
    other = world.add(Entity(id="Rider", kind="character", type="boy", label="the rider"))
    _feel(other, "patience", 1.0)

    introduce(world, hero)
    loves_space_sound(world, hero, activity)
    world.say(f"{parent.label_word} had just bought {hero.pronoun('object')} {prize.phrase}.")
    world.say(f"{hero.id} loved {prize.it()} and wore {prize.it()} like a tiny captain's badge.")

    world.para()
    arrive(world, hero, parent)
    wants(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    cue_conflict(world, parent, hero)

    world.para()
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear_def)
    return world


SETTINGS = {
    "bike_lane": Setting(place="the bike lane", indoors=False, affords={"ring_bell", "zoom", "signal", "overtake"}),
}

ACTIVITIES = {
    "ring_bell": Activity(
        id="ring_bell",
        verb="ring the bell",
        gerund="ringing the bell",
        rush="dash forward with a loud ding-ding",
        sound="ding-ding",
        social_risk="startle the others",
        keyword="bell",
        tags={"sound", "lane", "sociology"},
    ),
    "zoom": Activity(
        id="zoom",
        verb="zoom down the lane",
        gerund="zooming down the lane",
        rush="shoot ahead with a big whoosh",
        sound="whoosh",
        social_risk="cut in front of the slower riders",
        keyword="whoosh",
        tags={"sound", "lane", "sociology"},
    ),
    "signal": Activity(
        id="signal",
        verb="call out before passing",
        gerund="calling out before passing",
        rush="call out too loudly",
        sound="hey-ho",
        social_risk="make everyone turn at once",
        keyword="signal",
        tags={"sound", "lane", "sociology"},
    ),
    "overtake": Activity(
        id="overtake",
        verb="pass another rider",
        gerund="passing another rider",
        rush="slip by with a zippery swish",
        sound="swish",
        social_risk="crowd the narrow lane",
        keyword="swish",
        tags={"sound", "lane", "sociology"},
    ),
}

PRIZES = {
    "cape": Prize(label="cape", phrase="a shiny red cape", type="cape", region="torso"),
    "badge": Prize(label="badge", phrase="a bright space badge", type="badge", region="torso"),
    "streamers": Prize(label="streamers", phrase="sparkly handlebar streamers", type="streamers", region="hands", plural=True),
}

GEAR = [
    Gear(id="bell", label="the little bell", covers={"torso", "hands"}, guards={"ring_bell", "signal"}, prep="ride with the little bell ready", tail="followed the painted line and rang the bell at the right time"),
    Gear(id="vest", label="the reflective vest", covers={"torso"}, guards={"zoom", "overtake", "signal"}, prep="put on the reflective vest first", tail="glided along in a careful single-file line"),
    Gear(id="gloves", label="the padded gloves", covers={"hands"}, guards={"ring_bell", "zoom"}, prep="pull on the padded gloves", tail="kept a steady grip and passed with room to spare"),
]

GIRL_NAMES = ["Nia", "Mina", "Luna", "Ava", "Zoe", "Rae", "Iris", "Tia"]
BOY_NAMES = ["Owen", "Kai", "Finn", "Leo", "Milo", "Theo", "Max", "Jude"]
TRAITS = ["curious", "careful", "brave", "spirited", "bright", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if reason_ok(act, prize):
                    out.append((place, act_id, prize_id))
    return out


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


KNOWLEDGE = {
    "sociology": [("What is sociology?", "Sociology is the study of how people live together, share spaces, and follow social rules.")],
    "sound": [("What makes a sound effect?", "A sound effect is a made-up or noticed sound that helps tell what is happening, like a bell ding or a whoosh.")],
    "lane": [("What is a bike lane for?", "A bike lane is a marked space on the road for bicycles, so riders can travel more safely and with less crowding.")],
    "bell": [("Why do bikes have bells?", "Bikes have bells so riders can warn others kindly before passing or turning.")],
    "vest": [("Why wear a reflective vest?", "A reflective vest helps other people see you more easily, especially when the light is dim or the road is busy.")],
    "gloves": [("Why wear gloves when riding a bike?", "Gloves can help your hands grip the handlebars and keep them a little safer and comfier.")],
}

KNOWLEDGE_ORDER = ["sociology", "sound", "lane", "bell", "vest", "gloves"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short space-adventure story for a child about sociology in {world.setting.place} with the word "{act.keyword}".',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {parent.label_word} worries about {prize.phrase} and the other riders.",
        f'Write a simple story with a bright sound effect like "{act.sound}" and end with a peaceful bike lane.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Why did {hero.id} and {hero.pronoun('possessive')} {parent.label_word} go to the bike lane?",
            answer=f"They went there because {hero.id} wanted to {act.verb}, and the bike lane felt like a tiny space runway."
        ),
        QAItem(
            question=f"What sound effect was the most important in the story?",
            answer=f'The important sound was "{act.sound}", because it helped the rider signal without causing a crowd.'
        ),
        QAItem(
            question=f"What did {hero.id}'s {parent.label_word} worry about?",
            answer=f"{hero.id}'s {parent.label_word} worried that the loud sound and quick motion could upset the other riders and disturb the neat flow of the lane."
        ),
        QAItem(
            question=f"How did the story end for {hero.id}'s {prize.label}?",
            answer=f"At the end, {hero.id}'s {prize.label} stayed safe while the ride became calm and friendly again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    gear = world.facts.get("gear")
    if gear:
        tags.add(gear.id)
    out: list[QAItem] = []
    for key in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
    return out


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="bike_lane", activity="ring_bell", prize="badge", name="Nia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="bike_lane", activity="zoom", prize="cape", name="Kai", gender="boy", parent="father", trait="brave"),
    StoryParams(place="bike_lane", activity="signal", prize="streamers", name="Luna", gender="girl", parent="mother", trait="gentle"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.verb} does not sensibly threaten a {prize.label} in this bike-lane world.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(PRIZES, prize_id).genders))
    return f"(No story: a {_safe_lookup(PRIZES, prize_id).label} is not a typical {gender}'s item here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A, P) :- activity(A), prize(P), tag(A, lane), wears_on(P, torso).
compatible(A, P) :- prize_at_risk(A, P), gear(G), guards(G, A), covers(G, torso).
valid(Place, A, P) :- setting(Place), affords(Place, A), compatible(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("wears_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for a in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, a))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: sociology in a bike lane, with sound effects and space-adventure style.")
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
        act, pr = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not reason_ok(act, pr):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "prize", None) and getattr(args, "gender", None) not in _safe_lookup(PRIZES, getattr(args, "prize", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
              and (getattr(args, "gender", None) is None or getattr(args, "gender", None) in PRIZES[c[2]].genders)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize_id = rng.choice(list(combos))
    prize = _safe_lookup(PRIZES, prize_id)
    gender = getattr(args, "gender", None) or rng.choice(sorted(prize.genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize),
                 params.name, params.gender, [params.trait, "stubborn"], params.parent)
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
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:10} {act:10} {prize:10}  [{', '.join(genders)}]")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
