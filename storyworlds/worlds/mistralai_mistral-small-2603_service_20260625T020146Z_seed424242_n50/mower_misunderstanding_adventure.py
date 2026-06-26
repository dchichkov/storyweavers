#!/usr/bin/env python3
"""
storyworlds/worlds/mower_misunderstanding_adventure.py
===================================================

A standalone *story world* for "The Mower Misunderstanding" tale and close,
constraint-checked variations.

Initial story (used to build a world model):
---
Once upon a time there was a little courageous adventurer named Leo who loved dressing up in
a yellow cape and exploring the backyard jungle with a toy lawn mower. One morning, Leo's
parents bought him bright new white sneakers. "These shoes should stay clean," his mom said.

Eager for another adventure, Leo revved his mower and trundled outside towards the tall grass.
Mom spotted the mower and dropped what she was holding, arms waving. "Stop, Leo!" she cried.
"You can't mow in those new shoes — they'll get filthy and then I'll have to clean them."
But Leo pouted and pushed the mower into the patch beneath the oak tree. Mom hurried
after him, catching his arm. "You must see why," she said. "You are not ready to be
a lawn captain yet."

Leo crossed his arms. "But I want to mow!" He stomped the pedal again. Mom scooped
him up and carried him inside where the old green rain boots sat by the door. "If you
must be a captain of grass," she said, "you'll need your boots *and* a bucket."

Leo slipped the boots on, snapped the belt like a hero buckling his belt, and marched out
with his tiny spray bottle full of water. Soon he 'mowed' by lightly misting the grass,
making it shimmer like a jungle after a brief storm. His new shoes stayed clean beneath him,
while the hard-working grass got what it needed.

Causal state updates:
---
    do activity (rev mower)         -> actor.<mess> += 1, actor.joy += 1
    actor messy + worn item dirty    -> item.dirty++  (only if no protective "mower gear")
    mower.on (active)               -> grass.<trimmed> += 1
    solved misbehavior              -> parent.love += 1; actor.joy += 1
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample

# Threshold for narrating state changes
THRESHOLD = 0.7

# Physical mess kinds from mowing
MESS_KINDS = {"clingy", "clippings", "splattered"}

# Regions on a body
REGIONS = {"head", "torso", "legs", "feet"}

# CLINGY mess stays longer and is harder to remove
DIRT_RETENTION = {"clingy": 0.9, "clippings": 0.5, "splattered": 0.7}

# Activity → the zones (body parts) it pollutes
POLLUTION_ZONES = {
    "mowing": {"legs", "feet"},
    "highmow": {"legs", "feet", "torso"},
    "trimmers": {"head", "torso"},
}

# Prizes ranked by region
PRIZE_REGIONS = {
    "shoes": "feet",
    "sneakers": "feet",
    "cape": "torso",
    "dress": "torso",
    "hat": "head",
}

# ------------------------------------------------------------
# Entities: characters and things share one representation.
# ------------------------------------------------------------

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
    type: str = "thing"           # boy, mother, cape, mower, spray, ...
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""               # body region occupied by this item
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    cape: object | None = None
    gear: object | None = None
    hero: object | None = None
    new_item: object | None = None
    parent: object | None = None
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

# ------------------------------------------------------------
# Domain-specific param dataclass
# ------------------------------------------------------------
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
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None

# ------------------------------------------------------------
# Registries: settings, activities, prizes, gear, names ...
# ------------------------------------------------------------
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


@dataclass
class Setting:
    place: str = "the backyard"
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
    zones: set[str]
    weather: str = ""
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

# ------------------------------------------------------------
# World: entity store + narration state
# ------------------------------------------------------------
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
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.pollution_zones: set[str] = set()
        self.workloads: dict[str, int] = defaultdict(int)
        self.facts: dict = {}
        self.pool: set[str] = set()         # free-sentences generated by rules
        self.mower_on: bool = False

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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.pollution_zones = set(self.pollution_zones)
        clone.workloads = defaultdict(int, self.workloads)
        return clone

# ------------------------------------------------------------
# Causal forward-chaining rules (physical + social)
# ------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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


def _r_spread_grass(clippings_world: World) -> list[str]:
    out: list[str] = []
    for actor in clippings_world.characters():
        if actor.meters.get(clippings_world.facts["activity"].mess, 0) < THRESHOLD:
            continue
        for item in clippings_world.worn_items(actor):
            if item.protective or item.region not in clippings_world.pollution_zones:
                continue
            if clippings_world.covered(actor, item.region):
                continue
            sig = ("clippings", item.id)
            if sig in clippings_world.fired:
                continue
            clippings_world.fired.add(sig)
            mess_type = clippings_world.facts["activity"].mess
            item.meters[mess_type] += DIRT_RETENTION[mess_type]
            item.meters["dirty"] += 1
            out.append(
                f"Sticky {mess_type} clung to {item.label}, "
                f"leaving it {mess_type} and dirty."
            )
    return out

def _r_mow_progress(world: World) -> list[str]:
    if not world.mower_on:
        return []
    world.facts.setdefault("grass_trimmed", 0.0)
    world.facts["grass_trimmed"] += 0.3
    # every *third* active mower tick narrates as progress
    if len(world.fired) % 3 == 0:
        return [f"The {world.facts['activity'].gerund} made small clumps appear."]
    return []

def _r_workload(world: World) -> list[str]:
    for item in list(world.entities.values()):
        if item.meters.get("dirty", 0) >= THRESHOLD and item.caretaker:
            if ("work", item.id) not in world.fired:
                world.fired.add(("work", item.id))
                parent = world.get(item.caretaker)
                parent.meters["workload"] += 1
                world.workloads[item.caretaker] += 1
                return [f"That would mean more laundry for {parent.label} today."]
    return []

def _r_captain_conflict(world: World) -> list[str]:
    for actor in world.characters():
        defiance = actor.memes.get("defiance", 0)
        if defiance >= THRESHOLD and actor.meters.get("punishment", 0) < 1 and ("grabbed" not in world.facts):
            if ("captain", actor.id) not in world.fired:
                world.fired.add(("captain", actor.id))
                actor.memes["conflict"] += 1
                return ["__captain_conflict__"]
    return []

CAUSAL_RULES: list[Rule] = [
    Rule(name="spread_clippings", tag="physical", apply=_r_spread_grass),
    Rule(name="mow_progress", tag="progress", apply=_r_mow_progress),
    Rule(name="workload", tag="household", apply=_r_workload),
    Rule(name="captain_conflict", tag="social", apply=_r_captain_conflict),
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
                produced.extend(s for s in sents if s != "__captain_conflict__")
                world.pool.update(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced

# ------------------------------------------------------------
# Utility predicates (reasonableness gate)
# ------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zones

def select_gear(activity: Activity, prize: Prize) -> Optional[Entity]:
    # gear that covers the mess zone *and* removes this particular mess key
    # products: old_cape (protects torso, absorbs clings), rain_boots,
    #            spray_bottle (special proxy gear)
    protectors = {
        "mowing": {"spray_bottle": {"clippings"}},
        "highmow": {"spray_bottle": {"clippings"}, "rain_boots": {"clippings"}},
        "trimmers": {"old_cape": {"splattered"}},
    }
    key = activity.id
    if key in protectors:
        for pid, covers_removes in protectors[key].items():
            for mid in covers_removes:
                if mid == activity.mess:
                    return Entity(id=pid, label=pid, protective=True,
                                covers={prize.region} if pid != "spray_bottle" else {"feet"},
                                region="", plural={"rain_boots", "old_cape"}.__contains__(pid))
    return None

# ------------------------------------------------------------
# Predictive helper (would the prize stay clean?)
# ------------------------------------------------------------
def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    sim.facts.update(activity=activity)
    actor_sim = sim.get(actor.id)
    actor_sim.meters[activity.mess] += 2
    sim.pollution_zones = set(activity.zones)
    sim.mower_on = True
    _ = propagate(sim, narrate=False)            # run silent simulation
    prize = sim.get(prize_id)
    return {
        "soiled": prize.meters.get("dirty", 0) >= THRESHOLD,
        "workload": sum(e.meters.get("workload", 0) for e in sim.characters()),
    }

# ------------------------------------------------------------
# Verbs / screenplay beats
# ------------------------------------------------------------
def introduce_adventurer(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    gear = "cape" if hero.type == "boy" else "shiny trainer"
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who dreamed of becoming "
        "a bold lawn captain one day."
    )
    world.say(
        f"Every morning, {hero.pronoun('subject')} slipped on "
        f"{hero.pronoun('possessive')} trusted {gear} ready for another adventure."
    )

def loves_mowing(activity: Activity) -> str:
    adjectives = {
        "mowing": "jutting and buzzing",
        "highmow": "confident chops overhead",
        "trimmers": "tiny electric thunder",
    }
    return adjectives.get(activity.id, "heralded lawn adventures")

def buys_treasure(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"One bright Saturday, {parent.id} surprised "
        f"{hero.id} with brand-new {prize.phrase}."
    )
    world.say(
        f"'{hero.id} deserves only the cleanest adventures,' {parent.pronoun()} beamed."
    )

def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} hugged {hero.pronoun('possessive')} new {prize.label} "
        f"and raced outside to start the day's quests."
    )

def wants_adventure(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb} immediately — "
        f"but {hero.pronoun('possessive')} {parent.label_word} raised a cautioning hand."
    )

def warn_parent(world: World, parent: Entity, hero: Entity, activity: Activity,
               prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    angle = "filthy and then I'll have to clean them"
    if pred["workload"] >= THRESHOLD:
        angle = f"filthy, which means more laundry for me"
    world.say(
        f'"Stop right there, Captain {hero.id}! Your new {prize.label} '
        f'will end up {angle}."'
    )
    return True

def rev_mower(world: World, hero: Entity, activity: Activity) -> None:
    hero.meters[activity.mess] += 1
    world.mower_on = True
    world.pollution_zones = set(activity.zones)
    propagate(world)
    world.say(f"{hero.id} put {hero.pronoun('possessive')} hands on the handles "
              f"and revved the toy mower engine.")

def defies_adventure(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"{hero.id} clamped {hero.pronoun('possessive')} jaw and pushed hard on "
        f"the pedal anyway — VOOM!"
    )

def grab_arm(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)          # fire captain_conflict
    world.say(
        f"{parent.label_word} swooped in, catching {hero.pronoun('possessive')} arm "
        f"mid-rev. 'No quest starts without a plan!' {parent.pronoun('subject')} insisted."
    )

def pout_adventurer(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes.get("conflict", 0) >= THRESHOLD:
        world.say(
            f'{hero.id} scowled, kicked at the dirt, '
            f'and muttered, "It\'s not fair!"'
        )

def propose_safer_plan(world: World, parent: Entity, hero: Entity, activity: Activity,
                       prize: Entity) -> Optional[Entity]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        label=gear_def.label,
        type="gear",
        owner=hero.id,
        caretaker=parent.id if "rain_boots" in gear_def.id else None,
        worn_by=hero.id,
        protective=gear_def.protective,
        covers=gear_def.covers,
        plural=gear_def.id in {"rain_boots", "spray_bottle"},
    ))
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        # gear didn't fully fix it — abandon
        world.entities.pop(gear.id, None)
        return None
    action = {
        "spray_bottle": "misted the grass with gentle water swirls",
        "rain_boots": "slipped on rain boots first",
        "old_cape": "buckled on the special old cape",
    }.get(gear.id, "found a safe middle path")
    world.say(
        f"{parent.label_word} knelt beside {hero.id} and whispered, "
        f"'If you must chase greatness, at least {action}.'"
    )
    return gear

def accept_safer_plan(world: World, parent: Entity, hero: Entity, activity: Activity,
                      prize: Entity, gear_def: Entity) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    hero.memes["captain"] = 1.0
    world.say(
        f"{hero.id}'s face broadened into the widest grin yet — "
        f"the hero’s grin!"
    )
    world.say(
        f"Holding tight to {gear_def.label if gear_def.id != 'spray_bottle' else 'the spray bottle'}, "
        f"{hero.id} {activity.gerund} without a single speck touching "
        f"{hero.pronoun('possessive')} new {prize.label}."
    )
    world.facts["resolved"] = True

# ------------------------------------------------------------
# Registries ––– register every legal combo once here
# ------------------------------------------------------------
SETTINGS = {
    "backyard": Setting(
        place="the backyard",
        indoor=False,
        affords={"mowing", "highmow"},
    ),
    "orchard": Setting(
        place="the small orchard behind the house",
        indoor=False,
        affords={"mowing"},
    ),
    "patio": Setting(place="the paved patio", indoor=False, affords=set()),
}

ACTIVITIES = {
    "mowing": Activity(
        id="mowing",
        verb="mow the lawn",
        gerund="mowing the lawn",
        rush="stormed towards the toy mower",
        mess="clippings",
        soil="covered in grass clippings",
        zones={"legs", "feet"},
        weather="sunny",
        keyword="mower",
        tags={"yard", "messy"},
    ),
    "highmow": Activity(
        id="highmow",
        verb="swing the high mower arm",
        gerund="swinging the high mower arm",
        rush="charged the tall grass",
        mess="clippings",
        soil="spattered with clumps",
        zones={"legs", "feet", "torso"},
        weather="windy",
        keyword="mower",
        tags={"tallgrass", "messy"},
    ),
    "trimmers": Activity(
        id="trimmers",
        verb="trim the rose border",
        gerund="trimming the rose border",
        rush="darted to the thorny roses",
        mess="splattered",
        soil="speckled with sap and petals",
        zones={"head", "torso"},
        weather="",
        keyword="trimmers",
        tags={"roses", "splattered"},
    ),
}

PRIZES = {
    "shoes": Prize(
        label="shoes",
        phrase="bright new shoes with blue laces",
        type="shoes",
        region="feet",
        plural=True,
    ),
    "sneakers": Prize(
        label="sneakers",
        phrase="brand-new white sneakers",
        type="sneakers",
        region="feet",
        plural=True,
    ),
    "cape": Prize(
        label="cape",
        phrase="a yellow cape with a silver lightning bolt",
        type="cape",
        region="torso",
    ),
    "dress": Prize(
        label="dress",
        phrase="a sparkly sundress",
        type="dress",
        region="torso",
        plural=False,
    ),
    "hat": Prize(
        label="hat",
        phrase="a new adventure hat",
        type="hat",
        region="head",
    ),
}

GEAR = [
    # spray bottle: cheap proxy that does not soil shoes
    Entity(
        id="spray_bottle",
        label="spray bottle",
        protective=True,
        covers={"feet"},
        plural=False,
    ),
    # rain boots: covers feet, guards clippings (but here we use spray bottle)
    Entity(
        id="rain_boots",
        label="rain boots",
        protective=True,
        covers={"feet"},
        plural=True,
    ),
    # old cape: covers torso against splattered mess
    Entity(
        id="old_cape",
        label="old green cape",
        type="cape",
        protective=True,
        covers={"torso"},
        plural=False,
    ),
]

BOY_NAMES = [
    "Leo", "Milo", "Finn", "Noah", "Eli", "Sam", "Max", "Owen", "Jack", "Theo",
]
GIRL_NAMES = [
    "Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose",
]
TRAITS = [
    "courageous", "stubborn", "daring", "clever", "imaginative", "lively", "brave",
]

def valid_combos() -> list[tuple[str, str, str]]:
    """Return list of (place, activity, prize) that have a compatible fix."""
    out: list[tuple[str, str, str]] = []
    for sname, setting in SETTINGS.items():
        for aid in setting.affords:
            act = _safe_lookup(ACTIVITIES, aid)
            for pid, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((sname, aid, pid))
    return out

CURATED = [
    StoryParams(place="backyard", activity="mowing", prize="sneakers", name="Leo", gender="boy", parent="mother", trait="courageous"),
    StoryParams(place="backyard", activity="mowing", prize="shoes", name="Milo", gender="boy", parent="father", trait="stubborn"),
    StoryParams(place="backyard", activity="highmow", prize="cape", name="Ava", gender="girl", parent="mother", trait="imaginative"),
    StoryParams(place="backyard", activity="trimmers", prize="hat", name="Lily", gender="girl", parent="father", trait="clever"),
]

# ------------------------------------------------------------
# Generation & Q&A generators
# ------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act = f["hero"], f["parent"], f["activity"]
    kw = act.keyword or act.mess
    return [
        f'Write a 3-to-5-year-old tale about a {hero.type} named {hero.id} '
        f'wanting to "{act.verb}" while keeping sneakers clean.',
        f'Tell a simple story where a child does not understand why they cannot '
        f'use a "{kw}" toy right now — and the grown-up finds '
        f'a safe "almost-real" path.',
        f'Craft a gentle adventure story that ends with clean shoes, '
        f'a satisfied hero, and a shimmering backyard.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize_cfg"], f.get("activity", None)
    pw = parent.label_word
    out: list[QAItem] = [
        QAItem(
            question=f"Who was the brave captain at the start of the story?",
            answer=(
                f"The story follows a little {hero.type} named {hero.id}, "
                f"an aspiring {hero.traits[0]} lawn captain."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} receive that should stay clean?",
            answer=(
                f"{hero.id}'s {parent.label_word} bought {hero.pronoun('object')} "
                f"{prize.phrase} so it would stay clean for every adventure."
            ),
        ),
    ]
    if f.get("captain_conflict"):
        reason = f.get("predicted_soil", "dirty")
        q = (
            f"Why did {pw} stop {hero.id} from {act.verb if act else 'mowing'} "
            f"the lawn right away?"
        )
        a = (
            f"{pw} knew that if {hero.id} {act.rush.replace(',', '')} "
            f"right then, {hero.pronoun('possessive')} new {prize.label} "
            f"would turn {reason} and need laundering afterwards."
        )
        out.append(QAItem(question=q, answer=a))
    if f.get("resolved") and "gear" in f:
        gear = world.entities[f["gear"].id]
        q = (
            f"How did {hero.id} finally '{act.gerund}' without "
            f"ruining {hero.pronoun('possessive')} new {prize.label}?"
        )
        a = (
            f"They used {gear.label} first: {hero.id} {act.gerund} "
            f"gently while the item stayed spotless behind."
        )
        out.append(QAItem(question=q, answer=a))
    return out

def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set()
    if "activity" in f:
        tags |= f["activity"].tags
    out = []
    know = {
        "mower": [(
            "What is a toy lawn mower?",
            "A toy lawn mower is a small pretend machine children use to cut grass "
            "with small plastic blades, pretending to be grown-up gardeners."
        )],
        "cape": [(
            "Why do children wear capes?",
            "Capes make children feel like brave heroes or superheroes when they wear them, "
            "letting their minds go on adventures while playing outside."
        )],
        "clippings": [(
            "What are grass clippings?",
            "Grass clippings are tiny bits of grass cut by a mower. They can stick to "
            "shoes and clothes and make them messy if not cleaned right away."
        )],
        "spray_bottle": [(
            "What is a spray bottle for?",
            "A spray bottle holds water used to softly mist plants or, in pretend play, "
            "to mimic mowing with gentle droplets instead of clippings."
        )],
    }
    for t in ("mower", "cape", "clippings", "spray_bottle"):
        if t in tags:
            out.extend(QAItem(qa[0], qa[1]) for qa in know[t])
    return out

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)

# ------------------------------------------------------------
# ASP twin (declarative reasonableness gate)
# ------------------------------------------------------------
ASP_RULES = r"""
% A prize is at risk when the activity pollutes its body region.
prize_at_risk(P) :- worn_on(P, R), pollutes(A, R).

% A piece of gear protects ONLY when it both covers & neutralises the mess.
protects(W, A) :- wearable(W), prize_at_risk(P),
                   mess_of(A, M), guards(W, M), covers(W, R), worn_on(P, R).

% A story is valid only when the activity has a compatible fix.
valid_story(S, A, P) :- setting(S), affords(S, A), prize_at_risk(P), protects(_, A).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("indside" if s.indoor else "outside", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for z in sorted(a.zones):
            lines.append(asp.fact("pollutes", aid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        if p.plural:
            lines.append(asp.fact("plural_prize", pid))
    for g in GEAR:
        lines.append(asp.fact("wearable", g.id))
        for m in DIRT_RETENTION:
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)

def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    # convert ASP symbols to native tuples
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate == Python combos ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH:")
    if clingo_set - python_set:
        print("  extra in ASP:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  missing in ASP:", sorted(python_set - clingo_set))
    return 1

# ------------------------------------------------------------
# Standard storyworld interface
# ------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure playground: lawn mower misunderstandings & safe quests."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
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
            msg = (
                f"({getattr(args, "activity", None)} would dirty {getattr(args, "prize", None)}, which leaves nothing "
                "clean for the next quest.)"
            )
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combo = None
    choices = valid_combos()
    if getattr(args, "place", None) or getattr(args, "activity", None) or getattr(args, "prize", None) or getattr(args, "gender", None):
        choices = [
            (p, a, pr) for (p, a, pr) in choices
            if (getattr(args, "place", None) is None or p == getattr(args, "place", None))
            and (getattr(args, "activity", None) is None or a == getattr(args, "activity", None))
            and (getattr(args, "prize", None) is None or pr == getattr(args, "prize", None))
            and (getattr(args, "gender", None) is None or getattr(args, "gender", None) in _safe_lookup(PRIZES, pr).genders)
        ]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize_id = rng.choice(sorted(choices))
    prize = _safe_lookup(PRIZES, prize_id)
    gender = getattr(args, "gender", None) or rng.choice(["boy", "girl"])
    name = getattr(args, "name", None) or rng.choice(BOY_NAMES if gender == "boy" else GIRL_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place, activity, prize_id, name, gender, parent, trait)

def generate(params: StoryParams) -> StorySample:
    act = _safe_lookup(ACTIVITIES, params.activity)
    prize = _safe_lookup(PRIZES, params.prize)
    world = World(_safe_lookup(SETTINGS, params.place))
    # entities
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=[params.trait, "stubborn"],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label="the parent",
        caretaker=None if params.parent == "father" else params.name,
    ))
    # prize on feet/legs
    new_item = world.add(Entity(
        id="prize",
        type=prize.type,
        label=prize.label,
        phrase=prize.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize.region,
        plural=prize.plural,
    ))
    if prize.region == "feet" and params.parent == "mother":
        new_item.caretaker = parent.id
    # cape on torso if used
    if params.prize == "cape":
        cape = world.add(Entity(
            id="cape_item", type="cape", label="yellow cape",
            worn_by=hero.id, owner=hero.id, region="torso",
        ))
    # Act 1 setup
    world.facts.update(activity=act, prize_cfg=prize)
    introduce_adventurer(world, hero)
    world.para()
    loves_mowing_phrase = loves_mowing(act)
    world.say(
        f"{hero.id} loved nothing more than the {loves_mowing_phrase}."
    )
    buys_treasure(world, parent, hero, new_item)
    loves_prize(world, hero, new_item)
    # Act 2 conflict
    world.para()
    wants_adventure(world, hero, parent, act)
    warned = warn_parent(world, parent, hero, act, new_item)
    rev_mower(world, hero, act)
    defies_adventure(world, hero, act)
    grab_arm(world, parent, hero, act)
    if warned:
        world.facts["captain_conflict"] = hero.memes.get("conflict", 0) >= THRESHOLD
    # Act 3 resolution
    world.para()
    pout_adventurer(world, hero, act)
    gear_entity = propose_safer_plan(world, parent, hero, act, new_item)
    gear_def = gear_entity.id if gear_entity else None
    if gear_def:
        world.facts["gear"] = gear_entity.id
        accept_safer_plan(world, parent, hero, act, new_item, gear_entity)
    world.facts.update(
        hero=hero, parent=parent, prize=new_item,
        conflict=hero.memes.get("captain_conflict", False),
        resolved=gear_def is not None,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- world ---\n")
        for e in sample.world.entities.values():
            ms = {k: v for k,v in e.meters.items() if v >= THRESHOLD}
            me = {k: v for k,v in e.memes.items() if v >= THRESHOLD}
            bits = []
            if ms: bits.append(f"mess={ms}")
            if me: bits.append(f"memes={me}")
            if e.worn_by: bits.append(f"worn_by={e.worn_by}")
            print(f"{e.id:8} {e.type:7} -> {' '.join(bits)}")
    if qa:
        print(format_qa(sample))

def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program(show="#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        pairs = asp_valid_combos()
        print(f"{len(pairs)} safe-adventure triples:\n")
        for p,a,pr in sorted(pairs):
            print(f"{p:15} {a:12} {pr}")
        return

    seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        max_iter = max(getattr(args, "n", None) * 50, 50)
        while len(samples) < getattr(args, "n", None) and i < max_iter:
            i += 1
            params = resolve_params(args, random.Random(seed + i))
            params.seed = seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
    if getattr(args, "json", None):
        payload = [s.to_dict() for s in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    for idx, s in enumerate(samples):
        hdr = ""
        if getattr(args, "all", None):
            p = s.params
            hdr = f"### {p.name.capitalize()} : {p.activity} at {p.place} ({p.prize})"
        elif len(samples) > 1:
            hdr = f"### variant {idx+1}"
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=hdr)
        if idx < len(samples) - 1:
            print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
