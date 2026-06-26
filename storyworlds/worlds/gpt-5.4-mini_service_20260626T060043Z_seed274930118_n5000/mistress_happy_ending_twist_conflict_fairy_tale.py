#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/mistress_happy_ending_twist_conflict_fairy_tale.py
=================================================================================================

A small fairy-tale story world with a mistress, a conflict, a twist, and a
happy ending.

Seed tale used to build the simulation:
---
A little child serves a kind mistress in an enchanted cottage by the woods.
The child wants to help collect moonflowers for supper, but the path is damp
and the clean apron or slippers could be ruined. The mistress warns the child,
the child resists, and then a small twist appears: the thing that seemed lost
or frightening is actually helpful. With the right gear and a gentle plan,
they finish the task together and end with a bright, safe, happy ending.
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
REGIONS = {"feet", "legs", "torso", "hands"}



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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gear: object | None = None
    hero: object | None = None
    mistress: object | None = None
    prize: object | None = None
    def __post_init__(self):
        for k in ["wet", "muddy", "torn", "lost", "found", "clean", "dirty", "workload"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "love", "fear", "conflict", "hope", "relief", "wonder", "defiance"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mistress"}
        male = {"boy", "man", "father", "prince"}
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
    mess: str
    soil: str
    zone: set[str]
    weather: str
    keyword: str = ""
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


def _r_soil(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        for mess in ("wet", "muddy", "torn"):
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soil", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["dirty"] += 1
                out.append(f"{actor.id}'s {item.label} got {mess}.")
    return out


def _r_workload(world: World) -> list[str]:
    out = []
    for item in list(world.entities.values()):
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        caretaker.meters["workload"] += 1
        out.append(f"That would mean more work for the caretaker.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["defiance"] < THRESHOLD or actor.memes["warned"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


CAUSAL_RULES = [
    ("soil", _r_soil),
    ("workload", _r_workload),
    ("conflict", _r_conflict),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for _, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD),
            "workload": sum(e.meters["workload"] for e in sim.characters())}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"Inside {setting.place}, candlelight made the corners glow."
    if activity.weather == "night":
        return f"Under the night sky, {setting.place} glimmered like a storybook page."
    return f"{setting.place.capitalize()} waited in a hush of leaves and silver light."


def introduce(world: World, child: Entity) -> None:
    trait = next((t for t in child.traits if t != "little"), "gentle")
    world.say(f"{child.id} was a little {trait} child who lived near the woods.")


def loves_mistress(world: World, child: Entity, mistress: Entity) -> None:
    child.memes["love"] += 1
    world.say(
        f"{child.id} loved helping {mistress.id}, the kind mistress of the cottage, "
        f"who always knew a warm answer."
    )


def prize_sentence(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive')} {prize.label}"


def buys(world: World, mistress: Entity, child: Entity, prize: Entity) -> None:
    world.say(
        f"One day, {mistress.id} gave {child.id} {child.pronoun('object')} {prize.phrase}."
    )


def loves_prize(world: World, child: Entity, prize: Entity) -> None:
    child.memes["hope"] += 1
    prize.worn_by = child.id
    world.say(f"{child.id} treasured {child.pronoun('possessive')} {prize.label} and wore {prize.it()} every morning.")


def arrive(world: World, child: Entity, mistress: Entity, activity: Activity) -> None:
    day = {"night": "One moonlit night, ", "day": "One bright day, "}.get(world.weather, "One day, ")
    go = "went to" if not world.setting.indoor else "stayed in"
    world.say(f"{day}{child.id} and {mistress.id} {go} {world.setting.place}.")
    world.say(setting_detail(world.setting, activity))


def wants(world: World, child: Entity, mistress: Entity, activity: Activity) -> None:
    child.memes["defiance"] += 1
    world.say(f"{child.id} wanted to {activity.verb}, even before the mist had lifted.")
    world.say(f"{child.id} hurried to {activity.rush}.")


def warn(world: World, mistress: Entity, child: Entity, activity: Activity, prize: Prize) -> bool:
    pred = predict_mess(world, child, activity, prize.id)
    if not pred["soiled"]:
        return False
    child.memes["warned"] += 1
    clause = f"You'll spoil your {prize.label}"
    if pred["workload"] >= THRESHOLD:
        clause += ", and I'll have more to mend"
    world.say(f'"{clause}," {mistress.id} said. "Choose a safer way, my dear."')
    return True


def twist(world: World, mistress: Entity, child: Entity, activity: Activity) -> None:
    world.facts["twist"] = "helper"
    child.memes["wonder"] += 1
    world.say(
        f"Then a small twist appeared: a silver moth landed on the path and led them to the missing lantern key."
    )
    world.say(
        f"It had not been lost after all. A shy robin had tucked it into a mossy knot so the wind would not take it away."
    )


def compromised_offer(world: World, mistress: Entity, child: Entity, activity: Activity, prize: Prize) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=child.id,
        caretaker=mistress.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = child.id
    if predict_mess(world, child, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(f'{mistress.id} smiled and said, "How about we {gear_def.prep} first?"')
    return gear_def


def accept(world: World, mistress: Entity, child: Entity, activity: Activity, prize: Prize, gear_def: Gear) -> None:
    child.memes["joy"] += 1
    child.memes["love"] += 1
    child.memes["conflict"] = 0.0
    child.memes["defiance"] = 0.0
    world.say(f"{child.id} hugged {mistress.id} and nodded at once.")
    world.say(
        f'Together they {gear_def.tail}. Soon {child.id} was {activity.gerund}, {prize_sentence(child, prize)} stayed safe, '
        f"and the moonlit path looked friendly instead of strange."
    )
    world.say(
        f'At last, the lantern shone, the mist turned to glitter, and their little trouble ended in a happy ending.'
    )


SETTINGS = {
    "cottage": Setting(place="the cottage garden", indoor=False, affords={"dew", "berries", "path"}),
    "woods": Setting(place="the woods", indoor=False, affords={"dew", "berries", "path"}),
    "tower": Setting(place="the old tower room", indoor=True, affords={"mending"}),
}

ACTIVITIES = {
    "dew": Activity(
        id="dew",
        verb="dance in the dew",
        gerund="dancing in the dew",
        rush="run through the silver grass",
        mess="wet",
        soil="wet",
        zone={"feet", "legs"},
        weather="night",
        keyword="dew",
        tags={"water", "moon"},
    ),
    "berries": Activity(
        id="berries",
        verb="pick moonberries",
        gerund="picking moonberries",
        rush="reach into the brambles",
        mess="muddy",
        soil="muddy",
        zone={"hands", "legs"},
        weather="night",
        keyword="berries",
        tags={"berries", "forest"},
    ),
    "path": Activity(
        id="path",
        verb="cross the lantern path",
        gerund="crossing the lantern path",
        rush="hurry across the stones",
        mess="torn",
        soil="torn",
        zone={"feet", "legs", "torso"},
        weather="night",
        keyword="path",
        tags={"path", "lantern"},
    ),
    "mending": Activity(
        id="mending",
        verb="mend the torn ribbon",
        gerund="mending a ribbon",
        rush="pull the thread quickly",
        mess="torn",
        soil="frayed",
        zone={"hands", "torso"},
        weather="",
        keyword="ribbon",
        tags={"thread", "ribbon"},
    ),
}

PRIZES = {
    "slippers": Prize(label="slippers", phrase="a pair of clean silk slippers", type="slippers", region="feet", plural=True),
    "apron": Prize(label="apron", phrase="a clean white apron", type="apron", region="torso"),
    "gloves": Prize(label="gloves", phrase="soft garden gloves", type="gloves", region="hands", plural=True),
}

GEAR = [
    Gear(id="boots", label="little rain boots", covers={"feet"}, guards={"wet", "muddy"}, prep="put on little rain boots", tail="walked on in their little rain boots", plural=True),
    Gear(id="cloak", label="a wool cloak", covers={"torso", "legs"}, guards={"wet", "muddy", "torn"}, prep="wrap in a wool cloak", tail="set off wrapped in the wool cloak"),
    Gear(id="mitts", label="patched mitts", covers={"hands"}, guards={"muddy", "torn"}, prep="slip on patched mitts", tail="went forward in patched mitts", plural=True),
]

GIRL_NAMES = ["Mina", "Lina", "Tessa", "Ivy", "Nora"]
BOY_NAMES = ["Finn", "Theo", "Owen", "Leo", "Jasper"]
TRAITS = ["brave", "curious", "gentle", "cheerful", "stubborn"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    mistress: str
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
    "dew": [("What is dew?", "Dew is tiny drops of water that rest on grass and leaves after the air cools at night.")],
    "berries": [("What are berries?", "Berries are small soft fruits that can grow on bushes and vines.")],
    "path": [("What is a path?", "A path is a strip of ground that people walk on to go from one place to another.")],
    "ribbon": [("What is a ribbon?", "A ribbon is a long, narrow strip of cloth that can tie up hair, gifts, or clothes.")],
    "boots": [("What are rain boots for?", "Rain boots help keep your feet dry when the ground is wet.")],
    "cloak": [("What does a cloak do?", "A cloak is a warm cover that helps keep your clothes dry and your body snug.")],
    "mitts": [("What are mitts for?", "Mitts cover your hands and help keep them warm or clean.")],
}
KNOWLEDGE_ORDER = ["dew", "berries", "path", "ribbon", "boots", "cloak", "mitts"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, mistress, act, prize = f["hero"], f["mistress"], f["activity"], f["prize_cfg"]
    return [
        f'Write a fairy tale for a small child about {hero.id} and {mistress.id}, with a conflict, a twist, and a happy ending.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} while wearing {prize.phrase}, but {mistress.id} worries and a twist appears.",
        f'Write a story about a {hero.type} named {hero.id}, a kind mistress, and the word "{act.keyword or act.id}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mistress, prize, act = f["hero"], f["mistress"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a little {next((t for t in hero.traits if t != 'little'), 'gentle')} child, and {mistress.id}, the kind mistress of the cottage.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {act.verb}, but that would have made {hero.pronoun('possessive')} {prize.label} get messy.",
        ),
        QAItem(
            question=f"Why did {mistress.id} worry?",
            answer=f"{mistress.id} worried because {prize.phrase} could be spoiled by the {act.mess} part of the walk.",
        ),
    ]
    if f.get("conflict"):
        qa.append(QAItem(
            question=f"What was the conflict in the story?",
            answer=f"The conflict was that {hero.id} wanted to {act.verb}, but {mistress.id} said no at first because the path could ruin {hero.pronoun('possessive')} {prize.label}.",
        ))
    if f.get("twist"):
        qa.append(QAItem(
            question=f"What was the twist?",
            answer="The twist was that the missing lantern key was not truly lost. A shy robin had hidden it in a mossy knot, and the silver moth showed them where to look.",
        ))
    if f.get("resolved") and f.get("gear"):
        gear = _safe_fact(world, f, "gear")
        qa.append(QAItem(
            question=f"How did the happy ending happen?",
            answer=f"{mistress.id} offered {gear.label}, and that let {hero.id} keep {hero.pronoun('possessive')} {prize.label} safe while still taking part in the adventure.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and relieved, because the trouble was solved and the fairy-tale night ended with light, laughter, and a happy ending.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("gear"):
        tags.add(f["gear"].id)
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="cottage", activity="dew", prize="slippers", name="Mina", gender="girl", mistress="Mistress Rowan", trait="curious"),
    StoryParams(place="woods", activity="berries", prize="gloves", name="Finn", gender="boy", mistress="Mistress Elowen", trait="brave"),
    StoryParams(place="woods", activity="path", prize="apron", name="Tessa", gender="girl", mistress="Mistress Willow", trait="gentle"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not threaten {noun}.)"
    return f"(No story: no gear in this world sensibly protects {noun} from {activity.gerund}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(PRIZES, prize_id).genders))
    return f"(No story: try --gender {ok}; this setting does not fit a {gender}'s-only version for that prize.)"


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_stories() -> list[tuple]:
    return sorted(set(valid_combos()))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    c, p = set(asp_valid_combos()), set(valid_combos())
    if c == p:
        print(f"OK: clingo gate matches valid_combos() ({len(c)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if c - p:
        print("  only in clingo:", sorted(c - p))
    if p - c:
        print("  only in python:", sorted(p - c))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world: mistress, conflict, twist, happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mistress")
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
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
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
    mistress = getattr(args, "mistress", None) or rng.choice(["Mistress Rowan", "Mistress Willow", "Mistress Elowen"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, mistress=mistress, trait=trait)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, mistress_name: str, hero_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["gentle", "stubborn"])))
    mistress = world.add(Entity(id=mistress_name, kind="character", type="mistress"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=mistress.id, region=prize_cfg.region, plural=prize_cfg.plural))
    introduce(world, hero)
    loves_mistress(world, hero, mistress)
    buys(world, mistress, hero, prize)
    loves_prize(world, hero, prize)
    world.para()
    arrive(world, hero, mistress, activity)
    wants(world, hero, mistress, activity)
    if warn(world, mistress, hero, activity, prize):
        world.say(f"{hero.id} frowned, because the warning felt unfair.")
    world.say(f"{hero.id} tried to {activity.rush}, but the path looked too tempting to stop.")
    hero.memes["defiance"] += 1
    propagate(world, narrate=True)
    world.para()
    twist(world, mistress, hero, activity)
    gear_def = compromised_offer(world, mistress, hero, activity, prize)
    if gear_def:
        accept(world, mistress, hero, activity, prize, gear_def)
    world.facts.update(hero=hero, mistress=mistress, prize=prize, prize_cfg=prize_cfg, activity=activity, setting=setting, gear=gear_def, conflict=hero.memes["conflict"] >= THRESHOLD, twist=True, resolved=gear_def is not None)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.mistress, [params.trait, "stubborn"])
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
            print(f"  {place:8} {act:8} {prize:8}  [{', '.join(genders)}]")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
