#!/usr/bin/env python3
"""
storyworlds/worlds/peculiar_pawn_proclamation_lesson_learned_curiosity_space.py
===============================================================================

A small space-adventure storyworld about curiosity, a peculiar pawn, and a
lesson learned after a shipboard proclamation.

Premise:
- A young space traveler sees a peculiar pawn-shaped relic or toy on a station.
- Curiosity pushes them to investigate it right away.
- A proclamation warns that the pawn is delicate, lost, or tethered to a task.
- The child wants to explore anyway, causing a near-miss.
- A careful space-themed compromise lets them satisfy curiosity safely.

This world is designed to stay small and constraint-checked:
- physically, things have meters like distance, drift, and damage;
- emotionally, characters have memes like curiosity, worry, pride, and relief.
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
    location: str = ""
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    hero: object | None = None
    item: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pilot"}
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
    kind: str
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
    zone: set[str]
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
    covers: set[str]
    fixes: set[str]
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
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.zone = set(self.zone)
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


def _apply_drift(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("drift", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.location not in world.zone:
                continue
            sig = ("drift", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["damage"] = item.meters.get("damage", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} drifted and bumped the hatch.")
    return out


def _apply_alarm(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters.get("damage", 0.0) < THRESHOLD:
            continue
        if not item.caretaker:
            continue
        sig = ("alarm", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["worry"] = carer.meters.get("worry", 0.0) + 1
        out.append(f"That would make {carer.label} worry.")
    return out


def _apply_calm(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("comfort", 0.0) < THRESHOLD:
            continue
        if actor.memes.get("curiosity", 0.0) < THRESHOLD:
            continue
        sig = ("calm", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = 0.0
        out.append(f"{actor.id} felt calmer and could think clearly.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_apply_drift, _apply_alarm, _apply_calm):
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def preview_mishap(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    act = sim.get(actor.id)
    act.meters["drift"] = act.meters.get("drift", 0.0) + 1
    sim.zone = set(activity.zone)
    propagate(sim, narrate=False)
    prize = sim.get(prize_id)
    return {
        "damaged": prize.meters.get("damage", 0.0) >= THRESHOLD,
        "worry": sum(e.meters.get("worry", 0.0) for e in sim.characters()),
    }


def hero_intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "young"), "brave")
    world.say(f"{hero.id} was a young {trait} space traveler who liked to count stars through the dome.")


def curiosity_line(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} was full of curiosity and wanted to {activity.verb} at once; "
        f"the whole station felt like a mystery waiting to be opened."
    )


def proclamation(world: World, captain: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"Then the loudspeaker carried a proclamation: \"Please do not touch the {prize.label} yet; "
        f"it is delicate and can be lost in zero-g.\""
    )


def warning(world: World, captain: Entity, hero: Entity, activity: Activity, prize: Entity) -> None:
    pred = preview_mishap(world, hero, activity, prize.id)
    if not pred["damaged"]:
        return
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f"\"If you {activity.verb}, your {prize.label} could get bumped away,\" {captain.pronoun()} said. "
        f"\"Let's find a safer way.\""
    )


def near_miss(world: World, hero: Entity, activity: Activity) -> None:
    hero.meters["drift"] = hero.meters.get("drift", 0.0) + 1
    hero.memes["impulse"] = hero.memes.get("impulse", 0.0) + 1
    world.say(f"{hero.id} still leaned in to {activity.rush}, and the tiny boots skimmed the floor.")


def stop_and_help(world: World, captain: Entity, hero: Entity) -> None:
    hero.memes["stopped"] = hero.memes.get("stopped", 0.0) + 1
    world.say(
        f"{captain.pronoun('possessive').capitalize()} hand closed gently around {hero.pronoun('possessive')} sleeve, "
        f"and {hero.id} paused."
    )


def compromise(world: World, captain: Entity, hero: Entity, activity: Activity, prize: Prize) -> Optional[Gear]:
    gear = None
    for g in GEAR:
        if prize.location in g.covers and activity.keyword in g.fixes:
            gear = g
            break
    if gear is None:
        return None
    if preview_mishap(world, hero, activity, prize.label)["damaged"]:
        return None
    item = world.add(Entity(
        id=gear.id,
        label=gear.label,
        type="gear",
        protective=True,
        plural=gear.plural,
        owner=hero.id,
        caretaker=captain.id,
    ))
    item.worn_by = hero.id
    world.say(f"{captain.id} offered {gear.label} and said, \"How about we {gear.prep} first?\"")
    return item


def resolution(world: World, captain: Entity, hero: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["worry"] = 0.0
    world.say(
        f"{hero.id}'s face brightened. \"Yes!\" {hero.pronoun()} said, and the two of them {gear.tail}."
    )
    world.say(
        f"At last {hero.id} could {activity.gerund}, watch the peculiar {prize.label} stay safe, "
        f"and remember the lesson learned: curiosity is best when it listens."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["young", "curious", "careful"]))
    captain = world.add(Entity(id="Captain", kind="character", type=parent_type, label="the captain"))
    prize = world.add(Entity(
        id="pawn",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=captain.id,
        location=prize_cfg.location,
        plural=prize_cfg.plural,
    ))

    hero_intro(world, hero)
    world.say(
        f"{hero.id} had found a peculiar pawn from an old starboard game, and {hero.pronoun('possessive')} eyes "
        f"kept returning to it."
    )
    curiosity_line(world, hero, activity)
    world.para()
    world.say(f"On the station, {world.setting.place} hummed softly.")
    proclamation(world, captain, prize, activity)
    warning(world, captain, hero, activity, prize)
    near_miss(world, hero, activity)
    stop_and_help(world, captain, hero)
    world.para()
    gear = compromise(world, captain, hero, activity, prize)
    if gear:
        resolution(world, captain, hero, activity, prize, gear)
    world.facts.update(hero=hero, captain=captain, prize=prize, activity=activity, gear=gear, setting=setting)
    return world


SETTINGS = {
    "space_station": Setting(place="the space station", kind="station", affords={"drift", "scan"}),
    "moon_dock": Setting(place="the moon dock", kind="dock", affords={"drift", "scan"}),
    "cargo_bay": Setting(place="the cargo bay", kind="bay", affords={"drift", "scan"}),
}

ACTIVITIES = {
    "drift": Activity(
        id="drift",
        verb="peek into the airlock",
        gerund="peeking into the airlock",
        rush="float toward the airlock",
        risk="drift away",
        zone={"hands", "torso"},
        keyword="curiosity",
        tags={"space", "curiosity"},
    ),
    "scan": Activity(
        id="scan",
        verb="scan the strange signal",
        gerund="scanning strange signals",
        rush="race toward the blinking console",
        risk="bump the pawn",
        zone={"hands", "torso"},
        keyword="proclamation",
        tags={"space", "signal"},
    ),
}

PRIZES = {
    "pawn": Prize(
        label="pawn",
        phrase="a peculiar pawn with a chipped silver edge",
        type="pawn",
        location="hands",
    ),
    "token": Prize(
        label="token",
        phrase="a peculiar pawn-shaped token",
        type="token",
        location="hands",
    ),
}

GEAR = [
    Gear(
        id="tether_glove",
        label="a tether glove",
        covers={"hands"},
        fixes={"curiosity", "proclamation"},
        prep="put on a tether glove and hold the rail",
        tail="slipped on the tether glove and followed the rail back",
    ),
    Gear(
        id="clear_case",
        label="a clear case",
        covers={"hands"},
        fixes={"curiosity", "proclamation"},
        prep="carry the pawn in a clear case",
        tail="carried the clear case carefully",
    ),
]

GIRL_NAMES = ["Mina", "Zoe", "Lia", "Nora", "Rin"]
BOY_NAMES = ["Kai", "Finn", "Jace", "Theo", "Noah"]
TRAITS = ["brave", "bright", "spirited", "patient", "curious"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if prize.location in act.zone and any(prize.location in g.covers for g in GEAR):
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
    "curiosity": [
        ("What is curiosity?",
         "Curiosity is the feeling that makes someone want to know more, look closer, and ask questions."),
    ],
    "proclamation": [
        ("What is a proclamation?",
         "A proclamation is a public announcement that tells everyone an important message."),
    ],
    "pawn": [
        ("What is a pawn?",
         "A pawn is the smallest piece in chess, and it usually moves one step at a time."),
    ],
    "space": [
        ("Why do things float in space?",
         "Things float in space because there is very little gravity pulling them down the way Earth does."),
    ],
}

KNOWLEDGE_ORDER = ["curiosity", "proclamation", "pawn", "space"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, captain, prize, act = f["hero"], f["captain"], f["prize"], f["activity"]
    return [
        f'Write a short space adventure for a young child that uses the words "peculiar", "pawn", and "proclamation".',
        f"Tell a story where {hero.id} feels curiosity about a peculiar {prize.label}, but {captain.label} gives a proclamation and they choose a safer way to explore.",
        f"Write a gentle space story about a child who wants to {act.verb} near a peculiar pawn and learns a lesson learned at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, captain, prize, act = f["hero"], f["captain"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Who was curious about the peculiar {prize.label}?",
            answer=f"{hero.id} was curious about the peculiar {prize.label}, and {hero.pronoun('subject')} wanted to see it up close.",
        ),
        QAItem(
            question=f"What did the proclamation tell everyone about the {prize.label}?",
            answer=f"The proclamation said not to touch the {prize.label} yet because it was delicate and could be lost in zero-g.",
        ),
        QAItem(
            question=f"How did {hero.id} avoid trouble while still exploring?",
            answer=(
                f"{hero.id} used {f['gear'].label if f.get('gear') else 'care'} and stayed near the rail, "
                f"so {hero.pronoun('possessive')} curiosity could be safe instead of messy."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in world.facts["activity"].tags or tag == "space":
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
            bits.append("protective=True")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} only risks items in {sorted(activity.zone)}, "
        f"but the {prize.label} is not a good fit for this setup.)"
    )


CURATED = [
    StoryParams(place="space_station", activity="drift", prize="pawn", name="Mina", gender="girl", parent="captain", trait="curious"),
    StoryParams(place="moon_dock", activity="scan", prize="token", name="Kai", gender="boy", parent="captain", trait="bright"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for z in sorted(a.zone):
            lines.append(asp.fact("zone", aid, z))
        lines.append(asp.fact("keyword", aid, a.keyword))
    for prid, p in PRIZES.items():
        lines.append(asp.fact("prize", prid))
        lines.append(asp.fact("location", prid, p.location))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for f in sorted(g.fixes):
            lines.append(asp.fact("fixes", g.id, f))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, A, P) :- affords(Place, A), location(P, R), zone(A, R), gear(G), covers(G, R), fixes(G, K), keyword(A, K).
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
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld about curiosity and a peculiar pawn.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent="captain", trait=rng.choice(TRAITS))


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.parent)
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
