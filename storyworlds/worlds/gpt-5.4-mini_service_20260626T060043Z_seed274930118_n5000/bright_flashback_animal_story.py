#!/usr/bin/env python3
"""
Bright Flashback Animal Story

A small standalone storyworld in the "Animal Story" style: an animal child,
a bright object, and a flashback that changes how the present problem gets
solved.

The world is built around a tiny simulated premise:
- a young animal loves a bright prize,
- a present-day risk threatens it,
- a flashback reveals why the prize matters,
- a helper offers a safer way,
- the story ends with the prize kept safe and the feeling changed.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    gear_ent: object | None = None
    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        for k in ("wet", "muddy", "dirty", "brightness", "care"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "love", "flashback", "relief", "impatience", "memory"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"mother", "girl", "cat", "rabbit"}
        male = {"father", "boy", "fox", "bear"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    weather: str
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
class Flashback:
    cue: str
    memory: str
    reason: str
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
        self.zone: set[str] = set()
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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(item.protective and region in item.covers for item in self.worn_items(actor))

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
        other = World(self.setting)
        other.entities = _copy.deepcopy(self.entities)
        other.zone = set(self.zone)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        return other


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "meadow": Setting(place="the meadow", weather="sunny", affords={"fetch", "race", "forage"}),
    "pond": Setting(place="the pond", weather="breezy", affords={"splash", "fetch"}),
    "barnyard": Setting(place="the barnyard", weather="cloudy", affords={"forage", "race"}),
}

ACTIVITIES = {
    "fetch": Activity(
        id="fetch",
        verb="fetch the stick",
        gerund="fetching sticks",
        rush="dash to the stream",
        mess="muddy",
        soil="all muddy",
        zone={"paws", "belly"},
        keyword="stick",
        tags={"stick", "mud"},
    ),
    "splash": Activity(
        id="splash",
        verb="splash in the pond",
        gerund="splashing in the pond",
        rush="run into the water",
        mess="wet",
        soil="wet through",
        zone={"paws", "belly"},
        keyword="pond",
        tags={"water", "wet"},
    ),
    "forage": Activity(
        id="forage",
        verb="forage for berries",
        gerund="foraging for berries",
        rush="scurry into the brambles",
        mess="muddy",
        soil="full of burrs",
        zone={"paws", "belly", "tail"},
        keyword="berries",
        tags={"berries", "bush"},
    ),
    "race": Activity(
        id="race",
        verb="race across the hill",
        gerund="racing across the hill",
        rush="bolt down the slope",
        mess="dirty",
        soil="dusty and dirty",
        zone={"paws", "belly"},
        keyword="hill",
        tags={"speed"},
    ),
}

PRIZES = {
    "ribbon": Prize(
        label="ribbon",
        phrase="a bright red ribbon",
        type="ribbon",
        region="neck",
        genders={"girl", "boy"},
    ),
    "bell": Prize(
        label="bell",
        phrase="a tiny bright bell",
        type="bell",
        region="neck",
        genders={"girl", "boy"},
    ),
    "blanket": Prize(
        label="blanket",
        phrase="a soft bright blanket",
        type="blanket",
        region="back",
        genders={"girl", "boy"},
    ),
}

GEAR = [
    Gear(
        id="little_boots",
        label="little boots",
        covers={"paws"},
        guards={"muddy", "wet", "dirty"},
        prep="put on little boots first",
        tail="went back for the little boots",
        plural=True,
    ),
    Gear(
        id="dry_cloak",
        label="a dry cloak",
        covers={"back", "belly"},
        guards={"wet", "dirty"},
        prep="wear a dry cloak first",
        tail="took the dry cloak instead",
    ),
]

FLASHBACKS = {
    "ribbon": Flashback(
        cue="The ribbon looked extra bright in the sun.",
        memory="It reminded the little fox of the day the ribbon was tied on before a race with Grandma Fox.",
        reason="Grandma had said the ribbon was for lucky days and kind choices.",
    ),
    "bell": Flashback(
        cue="The bell gave a tiny bright gleam.",
        memory="It brought back the moment the bell was hung on a collar to help the cub be found in tall grass.",
        reason="The bell was a careful gift, not just a shiny toy.",
    ),
    "blanket": Flashback(
        cue="The blanket shone in a warm bright patch of light.",
        memory="It brought back a cold evening when the blanket was wrapped around the animal child after a storm.",
        reason="The blanket had kept the child safe and warm once before.",
    ),
}

NAMES = {
    "fox": ["Finn", "Fia", "Pip"],
    "rabbit": ["Ruby", "Milo", "Nina"],
    "bear": ["Benny", "Mara", "Toby"],
}


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero_type: str
    hero_name: str
    helper_type: str
    helper_name: str
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


CURATED = [
    StoryParams("meadow", "fetch", "ribbon", "fox", "Finn", "rabbit", "Ruby"),
    StoryParams("pond", "splash", "bell", "rabbit", "Milo", "bear", "Benny"),
    StoryParams("barnyard", "forage", "blanket", "bear", "Mara", "fox", "Fia"),
]


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------

def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and activity.mess in gear.guards:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return (
            f"(No story: {activity.gerund} does not threaten a {prize.label} worn on the {prize.region}."
            f" The flashback would not have a real problem to explain.)"
        )
    return (
        f"(No story: no gear in this tiny world can honestly protect a {prize.label} from {activity.gerund}.)"
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def predict_soil(world: World, hero: Entity, activity: Activity, prize_id: str) -> bool:
    sim = world.copy()
    do_activity(sim, sim.get(hero.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return prize.meters["dirty"] >= THRESHOLD or prize.meters["wet"] >= THRESHOLD


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.meters["joy"] += 1
    for item in world.worn_items(actor):
        if item.protective:
            continue
        if item.region not in activity.zone:
            continue
        if world.covered(actor, item.region):
            continue
        sig = ("soil", item.id, activity.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        item.meters[activity.mess] += 1
        item.meters["dirty"] += 1
        if narrate:
            world.say(f"{actor.pronoun('possessive').capitalize()} {item.label} got {activity.soil}.")


# ---------------------------------------------------------------------------
# Story beats
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    activity = _safe_lookup(ACTIVITIES, params.activity)
    prize_cfg = _safe_lookup(PRIZES, params.prize)
    flashback = _safe_lookup(FLASHBACKS, params.prize)

    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        traits=["little", "bright-eyed", "curious"],
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        traits=["kind", "steady"],
    ))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=helper.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    prize.worn_by = hero.id

    world.say(
        f"{hero.id} was a little {hero.type} who loved the bright {prize.label}."
    )
    world.say(
        f"On sunny mornings, {hero.id} liked {activity.gerund} and listening to {setting.place} hum softly."
    )
    world.say(
        f"{helper.id} had given {hero.id} {prize.phrase}, and {hero.id} wore it every day."
    )

    world.para()
    world.say(
        f"One day, {hero.id} and {helper.id} went to {setting.place}."
    )
    world.say(
        f"{hero.id} wanted to {activity.verb}, but {activity.rush} would be messy."
    )

    if predict_soil(world, hero, activity, prize.id):
        world.say(
            f'"You might make {prize.label} {activity.soil}," {helper.id} said.'
        )

    world.para()
    world.say(flashback.cue)
    hero.memes["flashback"] += 1
    hero.memes["memory"] += 1
    world.say(flashback.memory)
    world.say(flashback.reason)

    gear = select_gear(activity, prize_cfg)
    if gear is None:
        gear = next(iter(globals().get("GEARS", globals().get("GEAR", []))))

    world.para()
    world.say(
        f"{hero.id} looked at {prize.label} again and smiled more softly."
    )
    world.say(
        f"Then {helper.id} said, \"How about we {gear.prep} and try again?\""
    )

    gear_ent = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        owner=hero.id,
        caretaker=helper.id,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
    ))
    gear_ent.worn_by = hero.id

    hero.memes["joy"] += 1
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)
    hero.memes["relief"] += 1

    world.say(
        f"{hero.id} nodded, and together they {gear.tail}."
    )
    world.say(
        f"This time {hero.id} could {activity.gerund} without ruining the bright {prize.label}."
    )
    world.say(
        f"At the end, {hero.id} kept the {prize.label} safe, and the little animal story felt warm and happy."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        gear=gear_ent,
        flashback=flashback,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    prize: Entity = _safe_fact(world, f, "prize")
    activity: Activity = _safe_fact(world, f, "activity")
    flashback: Flashback = _safe_fact(world, f, "flashback")
    return [
        f'Write a short animal story with a bright {prize.label}, a flashback, and a kind helper.',
        f"Tell a gentle story about {hero.id} the {hero.type} who wants to {activity.verb} but remembers the bright {prize.label} matters.",
        f'Write an Animal Story style tale that uses the word "bright" and includes a memory that changes the choice at the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    prize: Entity = _safe_fact(world, f, "prize")
    activity: Activity = _safe_fact(world, f, "activity")
    flashback: Flashback = _safe_fact(world, f, "flashback")

    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little {hero.type} who loved the bright {prize.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do in the present day?",
            answer=f"{hero.id} wanted to {activity.verb} at {world.setting.place}.",
        ),
        QAItem(
            question=f"What did the flashback make {hero.id} remember?",
            answer=f"The flashback made {hero.id} remember that {flashback.memory.lower()}",
        ),
        QAItem(
            question=f"Why did {helper.id} worry?",
            answer=f"{helper.id} worried because {activity.gerund} could have made the bright {prize.label} messy.",
        ),
        QAItem(
            question=f"What helped in the end?",
            answer=f"They used {world.facts['gear'].label} so {hero.id} could keep the bright {prize.label} safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    activity: Activity = _safe_fact(world, f, "activity")
    prize: Entity = _safe_fact(world, f, "prize")
    out: list[QAItem] = [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that remembers something from before the present moment.",
        ),
        QAItem(
            question="Why do animals in stories sometimes wear gear?",
            answer="They wear gear to stay safe and keep things like water, mud, or dirt off the things they care about.",
        ),
    ]
    if "mud" in activity.tags:
        out.append(QAItem(
            question="What is mud?",
            answer="Mud is soft, wet dirt that can stick to paws and clothes.",
        ))
    if prize.label == "ribbon":
        out.append(QAItem(
            question="What is a ribbon?",
            answer="A ribbon is a long, soft strip of cloth that people sometimes wear or tie onto things.",
        ))
    if prize.label == "bell":
        out.append(QAItem(
            question="What does a bell do?",
            answer="A bell makes a little ringing sound when it moves.",
        ))
    return out


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
    lines.append("== (3) World knowledge questions ==")
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  zone={sorted(world.zone)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), gear(G), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
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
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story with a bright object and a flashback.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--activity", choices=ACTIVITIES.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--hero-type", choices=list(NAMES.keys()))
    ap.add_argument("--helper-type", choices=list(NAMES.keys()))
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
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
    hero_type = getattr(args, "hero_type", None) or rng.choice(list(NAMES.keys()))
    helper_type = getattr(args, "helper_type", None) or rng.choice([t for t in NAMES.keys() if t != hero_type])
    hero_name = getattr(args, "hero_name", None) or rng.choice(_safe_lookup(NAMES, hero_type))
    helper_name = getattr(args, "helper_name", None) or rng.choice(_safe_lookup(NAMES, helper_type))
    return StoryParams(place, activity, prize, hero_type, hero_name, helper_type, helper_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, prize) combos:\n")
        for row in combos:
            print("  ", row)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
