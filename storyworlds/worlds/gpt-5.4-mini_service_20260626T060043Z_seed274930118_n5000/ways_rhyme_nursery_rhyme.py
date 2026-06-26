#!/usr/bin/env python3
"""
storyworlds/worlds/ways_rhyme_nursery_rhyme.py
==============================================

A tiny nursery-rhyme story world about choosing between different ways, with a
little rhyme in the narration and a state-driven turn from risky way to safe way.

Seed idea:
---
A small child and a little animal follow a rhyme down a lane with many ways.
One way is bright, one way is muddy, and one way is blocked by a gate. The
grown-up warns that the muddy way will spoil the shoes, so the child tries to
force it, feels stuck, then follows a safer way with a lantern and a song.
The ending proves what changed: the child is home, the shoes are clean, and the
chosen way is lit and kind.
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

# Small threshold for state becoming narratable.
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
    path: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    entities: set[str] = field(default_factory=set)
    gear: object | None = None
    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wet": 0.0, "muddy": 0.0, "dirty": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "stuck": 0.0, "hope": 0.0}

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
    ways: tuple[str, ...] = ("left way", "right way", "old way")
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
class Way:
    id: str
    label: str
    rhyme: str
    hazard: str
    safe: bool = False
    blocked: bool = False
    mess: str = ""
    soil: str = ""
    zone: set[str] = field(default_factory=set)
    keyword: str = "ways"
    tags: set[str] = field(default_factory=set)
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


def _r_mud(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        way = world.facts.get("way")
        prize = world.facts.get("prize")
        if not way or not prize:
            continue
        if actor.meters["muddy"] < THRESHOLD:
            continue
        if prize.worn_by != actor.id:
            continue
        if prize.region not in way.zone:
            continue
        if world.covered(actor, prize.region):
            continue
        sig = ("mud", actor.id, prize.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        prize.meters["muddy"] += 1
        prize.meters["dirty"] += 1
        out.append(f"{actor.pronoun('possessive').capitalize()} {prize.label} got muddy on the way.")
    return out


def _r_stuck(world: World) -> list[str]:
    out: list[str] = []
    way = world.facts.get("way")
    if not way or not way.blocked:
        return out
    for actor in world.characters():
        if actor.memes["worry"] < THRESHOLD:
            continue
        sig = ("stuck", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["stuck"] += 1
        out.append(f"The blocked way made {actor.id} feel stuck.")
    return out


CAUSAL_RULES = [_r_mud, _r_stuck]


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


def prize_at_risk(way: Way, prize: Prize) -> bool:
    return prize.region in way.zone and not way.safe


def select_gear(way: Way, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if way.hazard in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, way: Way, prize_id: str) -> dict:
    sim = World(world.setting)
    sim.entities = {k: Entity(**{
        "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
        "phrase": v.phrase, "owner": v.owner, "caretaker": v.caretaker,
        "worn_by": v.worn_by, "path": v.path, "protective": v.protective,
        "covers": set(v.covers), "plural": v.plural,
        "meters": dict(v.meters), "memes": dict(v.memes)
    }) for k, v in world.entities.items()}
    sim.facts = dict(world.facts)
    sim.facts["way"] = way
    a = sim.get(actor.id)
    p = sim.get(prize_id)
    a.meters[way.mess] += 1
    propagate(sim, narrate=False)
    return {"soiled": p.meters["dirty"] >= THRESHOLD, "stuck": a.memes["stuck"] >= THRESHOLD}


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who liked to follow ways and watch the day go by.")


def loves_rhyme(world: World, hero: Entity, way: Way) -> None:
    hero.memes["joy"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved a small rhyme: “A way may sway, but a bright one will stay.”")


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"That morning, {hero.pronoun('possessive')} {parent.type} brought home {hero.pronoun('object')} {prize.phrase}.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["joy"] += 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} for the walk.")


def arrive(world: World, hero: Entity, parent: Entity, way: Way) -> None:
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.type} went to {world.setting.place}.")
    if way.blocked:
        world.say("There were three ways, and one had a gate that would not stay open.")
    elif way.safe:
        world.say("There were three ways, and one shone clear and kind.")
    else:
        world.say("There were three ways, and one looked muddy and mean.")


def wants(world: World, hero: Entity, way: Way) -> None:
    hero.memes["worry"] += 1
    world.say(f"{hero.id} wanted the {way.label}, because the rhyme in {way.rhyme} sounded fun.")
    world.say(f"{hero.pronoun().capitalize()} tried to take the {way.label} at once.")


def warn(world: World, parent: Entity, hero: Entity, way: Way, prize: Entity) -> bool:
    pred = predict_mess(world, hero, way, prize.id)
    if not pred["soiled"] and not pred["stuck"]:
        return False
    reason = f"“If you take the {way.label}, your {prize.label} will get {way.soil},”"
    if pred["stuck"]:
        reason += f" {hero.pronoun('possessive')} {parent.type} said, “and the gate will leave us in a pickle.”"
    else:
        reason += f" {hero.pronoun('possessive')} {parent.type} said."
    world.say(reason)
    return True


def defies(world: World, hero: Entity, way: Way) -> None:
    hero.memes["worry"] += 1
    world.say(f"But {hero.id} still stepped toward the {way.label}, little feet pat-pat-patting.")
    if way.blocked:
        world.say(f"Then the gate swayed and said no, so {hero.id} could not pass.")
    else:
        world.say(f"The mud was deep, and the way began to cling and creep.")


def compromise(world: World, parent: Entity, hero: Entity, way: Way, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(way, prize)
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
    if predict_mess(world, hero, way, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(f"“How about we {gear_def.prep}?” said {hero.pronoun('possessive')} {parent.type}.")
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, way: Way, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 2
    hero.memes["hope"] += 2
    hero.memes["worry"] = 0
    world.say(f"{hero.id} smiled wide and held {hero.pronoun('possessive')} {parent.type}'s hand.")
    world.say(
        f"They {gear_def.tail}, and soon {hero.id} was on the {way.label}, "
        f"while {prize.label} stayed clean and neat."
    )


def tell(setting: Setting, way: Way, prize_cfg: Prize,
         hero_name: str = "Nell", hero_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="grown-up"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    world.facts = {"hero": hero, "parent": parent, "prize": prize, "way": way, "setting": setting}

    introduce(world, hero)
    loves_rhyme(world, hero, way)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent, way)
    wants(world, hero, way)
    warn(world, parent, hero, way, prize)
    defies(world, hero, way)

    world.para()
    gear_def = compromise(world, parent, hero, way, prize)
    if gear_def:
        accept(world, parent, hero, way, prize, gear_def)

    world.facts["gear"] = gear_def
    return world


SETTINGS = {
    "lane": Setting(place="the lane"),
    "garden": Setting(place="the garden"),
    "bridge": Setting(place="the little bridge"),
}

WAYS = {
    "muddy_way": Way(
        id="muddy_way",
        label="muddy way",
        rhyme="mud and fluff and a puddle puff",
        hazard="mud",
        safe=False,
        blocked=False,
        mess="muddy",
        soil="all muddy",
        zone={"feet", "legs"},
        tags={"mud", "ways"},
    ),
    "bright_way": Way(
        id="bright_way",
        label="bright way",
        rhyme="light and bright and soft as kite",
        hazard="light",
        safe=True,
        blocked=False,
        mess="dry",
        soil="messy",
        zone=set(),
        tags={"light", "ways"},
    ),
    "gate_way": Way(
        id="gate_way",
        label="gate way",
        rhyme="close the gate and wait and wait",
        hazard="gate",
        safe=False,
        blocked=True,
        mess="stopped",
        soil="stopped",
        zone=set(),
        tags={"gate", "ways"},
    ),
}

PRIZES = {
    "shoes": Prize("shoes", "little blue shoes", "shoes", "feet", True),
    "dress": Prize("dress", "a fresh little dress", "dress", "legs"),
    "coat": Prize("coat", "a clean yellow coat", "coat", "torso"),
}

GEAR = [
    Gear("boots", "mud boots", {"feet"}, {"mud"}, "put on mud boots", "walked on, and the boots kept the mud off", True),
    Gear("cloak", "a rain cloak", {"torso"}, {"rain"}, "put on a rain cloak", "went along dry and safe"),
]

GIRL_NAMES = ["Nell", "Mia", "Lily", "Ava", "Zoe", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Leo", "Sam", "Finn"]
TRAITS = ["brave", "cheery", "curious", "tiny", "spry"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for way_id, way in WAYS.items():
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(way, prize) and select_gear(way, prize):
                    combos.append((place, way_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    way: str
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
    "ways": [("What are ways?", "Ways are paths or routes that people can follow to go from one place to another.")],
    "mud": [("What is mud?", "Mud is wet dirt. It can stick to shoes and make them dirty.")],
    "gate": [("What does a gate do?", "A gate can open and close to help keep a place safe or to stop a path.")],
    "boots": [("What are boots for?", "Boots help protect feet, especially when the ground is wet or muddy.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, way, prize = f["hero"], f["parent"], f["way"], f["prize"]
    return [
        f'Write a short nursery-rhyme story about "{way.label}" and a child named {hero.id}.',
        f"Tell a gentle story where {hero.id} wants the {way.label} but {hero.pronoun('possessive')} {parent.type} worries about {prize.phrase}.",
        f'Write a simple rhyme about a child, a way, and a clean ending with the word "ways".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, way = f["hero"], f["parent"], f["prize"], f["way"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little {hero.type}, and {hero.pronoun('possessive')} {parent.type}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to take the {way.label} because its rhyme sounded fun.",
        ),
        QAItem(
            question=f"Why did {parent.type} worry?",
            answer=f"{parent.type} worried that {prize.label} would get {way.soil} on the risky way.",
        ),
    ]
    if f.get("gear"):
        gear = _safe_fact(world, f, "gear")
        qa.append(QAItem(
            question=f"How did the family make the trip safer?",
            answer=f"They used {gear.label} so {hero.id} could follow the way without ruining {prize.label}.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["way"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    for tag, items in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="lane", way="muddy_way", prize="shoes", name="Nell", gender="girl", parent="mother", trait="cheery"),
    StoryParams(place="garden", way="muddy_way", prize="dress", name="Tom", gender="boy", parent="father", trait="curious"),
    StoryParams(place="bridge", way="muddy_way", prize="coat", name="Mia", gender="girl", parent="mother", trait="spry"),
]


def explain_rejection(way: Way, prize: Prize) -> str:
    if not prize_at_risk(way, prize):
        return f"(No story: the {way.label} would not soil {prize.label}, so there is no honest warning.)"
    return f"(No story: nothing in the gear set safely fixes the {way.label} for a {prize.label}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(PRIZES, prize_id).genders))
    return f"(No story: a {_safe_lookup(PRIZES, prize_id).label} is not a typical {gender}'s item here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(W, P) :- zone(W, R), worn_on(P, R), risky(W).
compatible(G, W, P) :- prize_at_risk(W, P), way_hazard(W, H), guards(G, H), covers(G, R), worn_on(P, R).
valid(Place, W, P) :- setting(Place), way(W), prize(P), prize_at_risk(W, P), compatible(_, W, P).
valid_story(Place, W, P, Gender) :- valid(Place, W, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for wid, w in WAYS.items():
        lines.append(asp.fact("way", wid))
        if w.safe:
            lines.append(asp.fact("safe", wid))
        if w.blocked:
            lines.append(asp.fact("blocked", wid))
        if w.hazard:
            lines.append(asp.fact("way_hazard", wid, w.hazard))
        if w.mess:
            lines.append(asp.fact("mess_of", wid, w.mess))
        if not w.safe:
            lines.append(asp.fact("risky", wid))
        for z in sorted(w.zone):
            lines.append(asp.fact("zone", wid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for h in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, h))
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
    ap = argparse.ArgumentParser(description="Nursery-rhyme ways story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--way", choices=WAYS)
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
    if getattr(args, "way", None) and getattr(args, "prize", None):
        way, prize = _safe_lookup(WAYS, getattr(args, "way", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(way, prize) and select_gear(way, prize)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "prize", None) and getattr(args, "gender", None) not in _safe_lookup(PRIZES, getattr(args, "prize", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "way", None) is None or c[1] == getattr(args, "way", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, way_id, prize_id = rng.choice(list(combos))
    prize = _safe_lookup(PRIZES, prize_id)
    gender = getattr(args, "gender", None) or rng.choice(sorted(prize.genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, way=way_id, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(WAYS, params.way), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.parent)
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
        print(f"{len(triples)} compatible (place, way, prize) combos ({len(stories)} with gender):\n")
        for place, way, prize in triples:
            genders = sorted(g for (pl, w, pr, g) in stories if (pl, w, pr) == (place, way, prize))
            print(f"  {place:9} {way:10} {prize:8}  [{', '.join(genders)}]")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
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
            header = f"### {p.name}: {p.way} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
