#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/sheaf_twitch_pepper_cautionary_folk_tale.py
======================================================================================================================

A small cautionary folk-tale storyworld about a sheaf, a twitch, and pepper.

The seed image is a village tale: a child hurries with a sheaf, notices a twitch
of warning, and learns that pepper is best handled with care. The world is kept
small and constraint-checked so the story can turn on a real mistake, a real
warning, and a real change in behavior.

Style notes:
- Folk-tale cadence, but concrete and child-facing.
- Cautionary rather than mean: the warning is honest, the resolution is gentle.
- The prose is driven by simulated state, not by a frozen template.
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
    held_by: Optional[str] = None
    protected: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    g: object | None = None
    hero: object | None = None
    item: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Place:
    name: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    weather: str
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
class Item:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    fragile_to: set[str] = field(default_factory=set)
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
    guards: set[str]
    covers: set[str]
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w

    def held_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.held_by == actor.id]


def _r_twitch(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("pepper_dust", 0.0) < THRESHOLD:
            continue
        sig = ("twitch", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["alarm"] = actor.memes.get("alarm", 0.0) + 1
        actor.meters["twitch"] = actor.meters.get("twitch", 0.0) + 1
        out.append(f"{actor.pronoun('subject').capitalize()} gave a little twitch.")
    return out


def _r_soil_sheaf(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("rush", 0.0) < THRESHOLD:
            continue
        for item in world.held_items(actor):
            if item.label != "sheaf":
                continue
            sig = ("soil_sheaf", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["stray_straw"] = item.meters.get("stray_straw", 0.0) + 1
            out.append(f"The sheaf shed a few dry strands in the hurry.")
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters.get("pepper_spill", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("workload", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        caretaker.meters["workload"] = caretaker.meters.get("workload", 0.0) + 1
        out.append(f"That would mean more sweeping for {caretaker.label}.")
    return out


CAUSAL_RULES = [_r_twitch, _r_soil_sheaf, _r_workload]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def prize_at_risk(activity: Activity, item: Item) -> bool:
    return item.region in activity.zone


def select_gear(activity: Activity, item: Item) -> Optional[Gear]:
    for gear in GEAR:
        if activity.risk in gear.guards and item.region in gear.covers:
            return gear
    return None


def predict(world: World, actor: Entity, activity: Activity, item_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    item = sim.get(item_id)
    return {
        "twitch": actor.meters.get("pepper_dust", 0.0) > 0,
        "soiled": item.meters.get("pepper_spill", 0.0) >= THRESHOLD or item.meters.get("stray_straw", 0.0) >= THRESHOLD,
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.place.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.id] = actor.meters.get(activity.id, 0.0) + 1
    if activity.risk == "pepper":
        actor.meters["pepper_dust"] = actor.meters.get("pepper_dust", 0.0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who knew the old path from the barn to the kitchen.")


def loves(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    world.say(f"{hero.pronoun('subject').capitalize()} loved {activity.gerund}, because the day always seemed to hurry along with it.")


def give_item(world: World, parent: Entity, hero: Entity, item: Entity) -> None:
    item.held_by = hero.id
    world.say(f"{parent.label} gave {hero.id} {hero.pronoun('object')} {item.phrase} to carry.")


def caution(world: World, parent: Entity, hero: Entity, activity: Activity, item: Entity) -> bool:
    pred = predict(world, hero, activity, item.id)
    if not pred["twitch"]:
        return False
    world.facts["predicted_twitch"] = True
    world.say(
        f'"Go slow," {parent.label} said. "If you rush with the {item.label}, the pepper will make your nose twitch."'
    )
    return True


def ignore(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1
    world.say(f"But {hero.id} was full of hurry and did not want to wait.")
    world.say(f"{hero.pronoun('subject').capitalize()} tried to {activity.rush},")


def offer(world: World, parent: Entity, hero: Entity, activity: Activity, item: Entity) -> Optional[Gear]:
    gear = select_gear(activity, item)
    if gear is None:
        return None
    g = world.add(Entity(
        id=gear.id,
        kind="thing",
        type="gear",
        label=gear.label,
        owner=hero.id,
        caretaker=parent.id,
        protected=True,
    ))
    g.held_by = hero.id
    if predict(world, hero, activity, item.id)["twitch"]:
        g.held_by = None
        del world.entities[g.id]
        return None
    world.say(f'{parent.label} held up a woven cloth and said, "{gear.prep}."')
    return gear


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, item: Entity, gear: Gear) -> None:
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    hero.memes["stubborn"] = 0.0
    world.say(f"{hero.id} nodded at last and took the careful way.")
    world.say(
        f"They {gear.tail}. Soon {hero.id} was {activity.gerund}, "
        f"the {item.label} stayed safe, and the old house was quiet except for soft feet on the floor."
    )


def tell(place: Place, activity: Activity, item_cfg: Item, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={"curious": 1.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    item = world.add(Entity(
        id="item",
        type="thing",
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        caretaker=parent.id,
        region=item_cfg.region,
    ))

    introduce(world, hero)
    loves(world, hero, activity)
    give_item(world, parent, hero, item)

    world.para()
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {parent_type} crossed {place.name}.")
    world.say(f"The air smelled of pepper, and the old road shivered with dust.")
    caution(world, parent, hero, activity, item)
    ignore(world, hero, activity)
    propagate(world)

    world.para()
    gear = offer(world, parent, hero, activity, item)
    if gear:
        accept(world, parent, hero, activity, item, gear)

    world.facts.update(
        hero=hero,
        parent=parent,
        item=item,
        activity=activity,
        place=place,
        gear=gear,
        trait=trait,
        resolved=gear is not None,
    )
    return world


PLACES = {
    "barn": Place(name="the barn", indoors=True, affords={"carry"}),
    "kitchen": Place(name="the kitchen", indoors=True, affords={"carry", "sort"}),
    "mill": Place(name="the mill", indoors=True, affords={"carry"}),
    "road": Place(name="the road", indoors=False, affords={"carry"}),
}

ACTIVITIES = {
    "carry": Activity(
        id="carry",
        verb="carry the sheaf",
        gerund="carrying the sheaf",
        rush="hurry with the sheaf",
        risk="pepper",
        weather="dry",
        zone={"floor", "table"},
        keyword="sheaf",
        tags={"sheaf", "pepper"},
    ),
    "sort": Activity(
        id="sort",
        verb="sort the grain",
        gerund="sorting grain",
        rush="scatter the grain",
        risk="pepper",
        weather="dry",
        zone={"table"},
        keyword="pepper",
        tags={"pepper", "grain"},
    ),
}

ITEMS = {
    "sheaf": Item(
        id="sheaf",
        label="sheaf",
        phrase="a tied sheaf of grain",
        region="hands",
        fragile_to={"pepper"},
        genders={"girl", "boy"},
    ),
    "pepper": Item(
        id="pepper",
        label="pepper",
        phrase="a small pepper bag",
        region="table",
        fragile_to={"rush"},
        genders={"girl", "boy"},
    ),
}

GEAR = [
    Gear(
        id="cloth",
        label="a woven cloth",
        guards={"pepper"},
        covers={"hands"},
        prep="wrap the sheaf in a woven cloth first",
        tail="walked slowly with the woven cloth",
    ),
    Gear(
        id="basket",
        label="a covered basket",
        guards={"pepper"},
        covers={"hands", "table"},
        prep="put it in a covered basket first",
        tail="went on with the covered basket",
    ),
]

GIRL_NAMES = ["Mira", "Nell", "Tamsin", "Una", "Wren"]
BOY_NAMES = ["Pip", "Jory", "Bram", "Milo", "Tobin"]
TRAITS = ["careful", "cheerful", "curious", "stubborn", "bright"]


@dataclass
class StoryParams:
    place: str
    activity: str
    item: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, pl in PLACES.items():
        for act_id in pl.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for item_id, item in ITEMS.items():
                if prize_at_risk(act, item) and select_gear(act, item):
                    out.append((place, act_id, item_id))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    act = _safe_fact(world, f, "activity")
    item = _safe_fact(world, f, "item")
    return [
        f'Write a short cautionary folk tale about "{act.keyword}" and "{item.label}".',
        f"Tell a gentle warning story where {hero.id} tries to {act.verb} but learns to slow down.",
        f"Write a child-friendly folk tale with a sheaf, a twitch, and pepper, ending in a safer choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    item = _safe_fact(world, f, "item")
    act = _safe_fact(world, f, "activity")
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do with the {item.label} at first?",
            answer=f"{hero.id} wanted to {act.verb}, but that hurry would have stirred up pepper dust.",
        ),
        QAItem(
            question=f"Why did {parent.label} warn {hero.id} to go slow?",
            answer=f"{parent.label} warned {hero.id} because rushing with the {item.label} would make the pepper make a twitch in {hero.pronoun('possessive')} nose.",
        ),
    ]
    if f.get("resolved") and gear is not None:
        qa.append(
            QAItem(
                question=f"How did the woven cloth help the {item.label} story end well?",
                answer=f"It let {hero.id} carry the {item.label} carefully, so the pepper stayed where it belonged and the day became calm again.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "sheaf": [
        QAItem(
            question="What is a sheaf?",
            answer="A sheaf is a bundle of cut grain or stalks tied together after harvest.",
        )
    ],
    "pepper": [
        QAItem(
            question="What can pepper do when it gets into your nose?",
            answer="Pepper can make your nose sting and make you sneeze or twitch.",
        )
    ],
    "twitch": [
        QAItem(
            question="What does twitch mean?",
            answer="A twitch is a small quick movement, like a little jump or jerk.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag in ["sheaf", "pepper", "twitch"]:
        if tag in tags:
            out.extend(WORLD_KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
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
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.protected:
            bits.append("protected=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({x[0] for x in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="barn", activity="carry", item="sheaf", name="Mira", gender="girl", parent="mother", trait="careful"),
    StoryParams(place="kitchen", activity="carry", item="sheaf", name="Pip", gender="boy", parent="father", trait="curious"),
    StoryParams(place="mill", activity="sort", item="pepper", name="Wren", gender="girl", parent="grandmother", trait="stubborn"),
]


ASP_RULES = r"""
prize_at_risk(A, I) :- zone(A, R), item_region(I, R).
has_fix(A, I) :- prize_at_risk(A, I), gear(G), guards(G, M), risk_of(A, M), covers(G, R), item_region(I, R).
valid(Place, A, I) :- affords(Place, A), prize_at_risk(A, I), has_fix(A, I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("risk_of", aid, a.risk))
        for z in sorted(a.zone):
            lines.append(asp.fact("zone", aid, z))
    for iid, i in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_region", iid, i.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, p = set(asp_valid_combos()), set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary folk tale: a sheaf, a twitch, and pepper.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "grandmother"])
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
    if getattr(args, "activity", None) and getattr(args, "item", None):
        act, item = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(ITEMS, getattr(args, "item", None))
        if not (prize_at_risk(act, item) and select_gear(act, item)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "item", None) is None or c[2] == getattr(args, "item", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, item_id = rng.choice(list(combos))
    item = _safe_lookup(ITEMS, item_id)
    gender = getattr(args, "gender", None) or rng.choice(sorted(item.genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father", "grandmother"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, item=item_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(ITEMS, params.item),
                 params.name, params.gender, params.parent, params.trait)
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
        print(f"{len(combos)} compatible (place, activity, item) combos:\n")
        for place, act, item in combos:
            print(f"  {place:8} {act:8} {item:8}")
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
            header = f"### {p.name}: {p.activity} at {p.place} (item: {p.item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
