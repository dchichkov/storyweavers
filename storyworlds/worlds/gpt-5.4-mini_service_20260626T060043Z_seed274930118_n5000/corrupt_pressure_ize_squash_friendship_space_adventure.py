#!/usr/bin/env python3
"""
A standalone story world for a small Space Adventure domain built around
Friendship, corrupt pressure, and a squash-like rescue maneuver.

Premise:
- Two space friends are flying a tiny scout ship to deliver a glowing seed.
- A greedy command system gets corrupted and starts pressure-izing the crew
  with bad instructions.
- The friends must squash the corrupted plan, repair trust, and finish the
  mission together.

The world is state-driven:
- physical meters include pressure, damage, drift, charge, and repair
- emotional memes include trust, worry, courage, and friendship
- the final story changes based on how those values evolve

This script is self-contained and follows the Storyweavers world contract.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    commander: object | None = None
    friend: object | None = None
    gear: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"pilot", "captain", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "engineer", "robot"}:
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
    place: str = "the starport"
    sky: str = "deep space"
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
        self.zone: set[str] = set()
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
        return [e for e in self.entities.values() if e.owner == actor.id and e.kind == "thing" and e.label]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def metric(x: Entity, key: str) -> float:
    return x.meters.get(key, 0.0)


def mood(x: Entity, key: str) -> float:
    return x.memes.get(key, 0.0)


def bump_meter(x: Entity, key: str, amount: float = 1.0) -> None:
    x.meters[key] = x.meters.get(key, 0.0) + amount


def bump_meme(x: Entity, key: str, amount: float = 1.0) -> None:
    x.memes[key] = x.memes.get(key, 0.0) + amount


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return (
            f"(No story: {activity.gerund} does not reach the {prize.region}, "
            f"so {noun} would stay safe and there is no honest conflict to resolve.)"
        )
    return (
        f"(No story: nothing in the gear catalog genuinely covers {noun} from "
        f"{activity.gerund}, so this pressure-and-fix pair is not reasonable.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(PRIZES, prize_id).genders))
    return f"(No story: a {_safe_lookup(PRIZES, prize_id).label} isn't a typical {gender}'s item here; try --gender {ok}.)"


def setting_detail(setting: Setting) -> str:
    if setting.place == "the starport":
        return "The starport lights blinked softly over a row of waiting ships."
    if setting.place == "the quiet moon dock":
        return "The moon dock floated in a silver hush above the cratered ground."
    if setting.place == "the comet tunnel":
        return "The comet tunnel glittered like a long blue hallway in the dark."
    return f"{setting.place.capitalize()} waited under a wide sky of stars."


def activity_delight(activity: Activity) -> str:
    return {
        "flight": "the ship hummed like a calm song",
        "repair": "tiny sparks danced like fireflies",
        "drift": "the stars slid by like little beads",
        "scan": "the scanner made the mission feel like a game",
    }.get(activity.id, "the mission felt bright and exciting")


def introduce(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.id} and {friend.id} were best friends who loved flying together."
    )
    world.say(
        f"They always shared the controls, because friendship made the ship feel steady."
    )


def loves_mission(world: World, hero: Entity, activity: Activity) -> None:
    bump_meme(hero, "friendship")
    bump_meme(hero, "courage")
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund}; {activity_delight(activity)}."
    )


def arrives(world: World, hero: Entity, friend: Entity, activity: Activity) -> None:
    world.say(f"One day, {hero.id} and {friend.id} set off from {world.setting.place}.")
    world.say(setting_detail(world.setting))


def wants(world: World, hero: Entity, activity: Activity) -> None:
    bump_meme(hero, "desire")
    world.say(
        f"{hero.id} wanted to {activity.verb}, but the ship's screen began flashing red."
    )


def corrupt_pressure(world: World, commander: Entity, hero: Entity, prize: Entity) -> None:
    bump_meter(commander, "corrupt", 1.0)
    bump_meter(commander, "pressure", 1.0)
    bump_meme(hero, "worry", 1.0)
    world.say(
        f"The command screen had been corrupted, and it started pressure-izing everyone "
        f"with mean, rushing orders about {prize.label}."
    )
    world.say(
        f"{hero.id} felt the squeeze of it and knew the old plan was wrong."
    )


def squash_plan(world: World, hero: Entity, friend: Entity, activity: Activity, prize: Entity) -> None:
    bump_meme(hero, "courage", 1.0)
    bump_meme(friend, "trust", 1.0)
    bump_meter(hero, "repair", 1.0)
    world.say(
        f"{hero.id} and {friend.id} did not obey the bad order."
    )
    world.say(
        f"Instead, they squashed the corrupted plan, rewired the screen, and chose a gentler route."
    )


def apply_fix(world: World, hero: Entity, friend: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    gear = world.add(Entity(
        id=gear_def.id,
        kind="thing",
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        plural=gear_def.plural,
    ))
    world.say(
        f"They put on {gear.label} and used it to keep the {prize.label} safe."
    )
    world.say(
        f"{hero.id} {gear_def.tail}, and the ship finally moved in a clean, easy line."
    )
    hero.meters["pressure"] = max(0.0, hero.meters.get("pressure", 0.0) - 1.0)
    hero.memes["worry"] = max(0.0, hero.memes.get("worry", 0.0) - 1.0)
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1.0
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1.0


def resolution(world: World, hero: Entity, friend: Entity, activity: Activity, prize: Entity) -> None:
    world.say(
        f"In the end, {hero.id} and {friend.id} finished the mission together."
    )
    world.say(
        f"The {prize.label} stayed safe, the ship stayed bright, and their friendship "
        f"shone louder than the corrupted screen."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, friend_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="pilot"))
    friend = world.add(Entity(id=friend_name, kind="character", type="engineer"))
    commander = world.add(Entity(id="Commander", kind="character", type="robot", label="the command system"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero, friend)
    loves_mission(world, hero, activity)
    world.say(f"They were carrying {prize.phrase} for a faraway station.")

    world.para()
    arrives(world, hero, friend, activity)
    wants(world, hero, activity)
    corrupt_pressure(world, commander, hero, prize)

    world.para()
    squash_plan(world, hero, friend, activity, prize)
    gear_def = select_gear(activity, prize)
    if gear_def is not None:
        apply_fix(world, hero, friend, activity, prize, gear_def)
    resolution(world, hero, friend, activity, prize)

    world.facts.update(
        hero=hero,
        friend=friend,
        commander=commander,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear_def,
    )
    return world


SETTINGS = {
    "starport": Setting(place="the starport", sky="deep space", affords={"flight", "repair", "scan"}),
    "moon_dock": Setting(place="the quiet moon dock", sky="moonlight", affords={"drift", "repair", "scan"}),
    "comet_tunnel": Setting(place="the comet tunnel", sky="comet light", affords={"flight", "drift", "repair"}),
}

ACTIVITIES = {
    "flight": Activity(
        id="flight",
        verb="fly through the comet field",
        gerund="flying through the comet field",
        rush="speed into the comet field",
        mess="corrupt",
        soil="scrambled",
        zone={"torso"},
        keyword="flight",
        tags={"space", "ship"},
    ),
    "repair": Activity(
        id="repair",
        verb="repair the broken scanner",
        gerund="repairing the broken scanner",
        rush="rush at the broken scanner",
        mess="pressure",
        soil="strained",
        zone={"torso", "hands"},
        keyword="repair",
        tags={"tools", "ship"},
    ),
    "drift": Activity(
        id="drift",
        verb="drift near the moon rings",
        gerund="drifting near the moon rings",
        rush="float closer to the moon rings",
        mess="corrupt",
        soil="off-course",
        zone={"torso"},
        keyword="drift",
        tags={"space"},
    ),
    "scan": Activity(
        id="scan",
        verb="scan the glowing asteroid",
        gerund="scanning the glowing asteroid",
        rush="lean over the scanner",
        mess="pressure",
        soil="overloaded",
        zone={"hands", "torso"},
        keyword="scan",
        tags={"tools", "light"},
    ),
}

PRIZES = {
    "seed": Prize(
        label="seed",
        phrase="a glowing seed in a glass case",
        type="seed",
        region="torso",
    ),
    "beacon": Prize(
        label="beacon",
        phrase="a tiny blue beacon",
        type="beacon",
        region="hands",
        plural=False,
    ),
    "map": Prize(
        label="map",
        phrase="a folded star map",
        type="map",
        region="hands",
        plural=False,
    ),
}

GEAR = [
    Gear(
        id="shield_gloves",
        label="shield gloves",
        covers={"hands"},
        guards={"pressure"},
        prep="slide on the shield gloves first",
        tail="slid back to the scanner with the shield gloves on",
    ),
    Gear(
        id="quiet_panel",
        label="a quiet panel cover",
        covers={"torso"},
        guards={"corrupt"},
        prep="clip on a quiet panel cover first",
        tail="moved through the tunnel with the quiet panel cover in place",
    ),
    Gear(
        id="pilot_harness",
        label="a pilot harness",
        covers={"torso"},
        guards={"pressure", "corrupt"},
        prep="buckle on a pilot harness first",
        tail="flew again with the pilot harness snug and steady",
    ),
]

GIRL_NAMES = ["Luna", "Nova", "Mira", "Zara", "Iris"]
BOY_NAMES = ["Orin", "Kito", "Jett", "Pax", "Rian"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    friend: str
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
    "space": [("What is space?", "Space is the wide, dark place beyond Earth where stars, planets, and ships can travel.")],
    "ship": [("What is a spaceship?", "A spaceship is a vehicle that can fly through space.")],
    "tools": [("What do tools do?", "Tools help people fix things, build things, or do jobs more easily.")],
    "light": [("Why do glowing things shine?", "Glowing things shine because they give off light, which helps you see them in the dark.")],
    "corrupt": [("What does corrupt mean?", "Corrupt means something has gone wrong and is no longer working the way it should.")],
    "pressure": [("What is pressure?", "Pressure is a push or squeeze. Too much pressure can make things feel hard or stressful.")],
    "friendship": [("What is friendship?", "Friendship is a kind relationship where people care about each other and help each other.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    act = _safe_fact(world, f, "activity")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a gentle space adventure for a young child that includes the word "{act.keyword}".',
        f"Tell a story about two friends who notice a corrupted control screen and squash the bad plan while protecting {prize.phrase}.",
        f"Write a short space story where friendship helps fix a pressure problem and the ship can travel safely again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    friend: Entity = _safe_fact(world, f, "friend")
    prize: Entity = _safe_fact(world, f, "prize")
    activity: Activity = _safe_fact(world, f, "activity")
    gear: Optional[Gear] = _safe_fact(world, f, "gear")

    qa = [
        QAItem(
            question=f"Who are the story's main friends?",
            answer=f"The story is about {hero.id} and {friend.id}, who fly together and help each other.",
        ),
        QAItem(
            question=f"What went wrong on the ship?",
            answer=f"The command screen got corrupted and started pressure-izing everyone with bad orders.",
        ),
        QAItem(
            question=f"What were the friends trying to protect?",
            answer=f"They were trying to protect {prize.phrase} while they finished the mission.",
        ),
        QAItem(
            question=f"What did they do to the bad plan?",
            answer=f"They squashed the corrupted plan and chose a safer way to keep flying.",
        ),
    ]
    if gear is not None:
        qa.append(
            QAItem(
                question=f"How did {gear.label} help them?",
                answer=f"{gear.label.capitalize()} helped because it covered the right part of the ship work and kept the mission safe.",
            )
        )
    qa.append(
        QAItem(
            question=f"How did friendship matter in the story?",
            answer=f"Friendship helped {hero.id} trust {friend.id}, stay brave, and fix the ship together.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.update({"tools", "friendship"})
    else:
        tags.add("friendship")
    out: list[QAItem] = []
    for tag in ["space", "ship", "tools", "light", "corrupt", "pressure", "friendship"]:
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


CURATED = [
    StoryParams(place="starport", activity="flight", prize="seed", name="Luna", friend="Mika"),
    StoryParams(place="moon_dock", activity="scan", prize="beacon", name="Orin", friend="Tess"),
    StoryParams(place="comet_tunnel", activity="repair", prize="map", name="Nova", friend="Pax"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for guard in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, guard))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld about friendship, corruption, and a squash-back repair.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    friend = getattr(args, "friend", None) or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    return StoryParams(place=place, activity=activity, prize=prize, name=name, friend=friend)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.name, params.friend)
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
            print(f"  {place:12} {act:8} {prize:8}  [{', '.join(genders)}]")
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
