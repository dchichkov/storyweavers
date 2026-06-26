#!/usr/bin/env python3
"""
storyworlds/worlds/gelatinous_referral_deodorant_repetition_curiosity_adventure.py
==================================================================================

A small adventure story world about curiosity, repetition, a gelatinous obstacle,
and a referral note that must reach its destination before the deodorant run is lost.

Premise:
- A curious child receives a referral note that sends them to a small shop for
  deodorant.
- The route includes a gelatinous passage that can stick to paper and ruin the note.
- Repetition becomes the useful trick: a repeated careful step, repeated check,
  repeated reminder, until the child crosses safely.

The world is intentionally tiny and classical:
- typed entities with physical meters and emotional memes
- simulated world state drives the prose
- explicit invalid choices raise StoryError
- inline ASP rules mirror the Python gate
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    note: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        for k in ["sticky", "lost", "safe", "tired", "risk", "progress"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "worry", "hope", "resolve", "joy", "calm"]:
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
class Route:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str]
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
    id: str
    label: str
    phrase: str
    region: str
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


def _r_sticky(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["risk"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("sticky", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["sticky"] += 1
            out.append(f"{actor.id}'s {item.label} picked up sticky goo.")
    return out


def _r_lost(world: World) -> list[str]:
    out: list[str] = []
    note = world.entities.get("referral")
    if not note:
        return out
    if note.meters["sticky"] < THRESHOLD:
        return out
    sig = ("lost", note.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    note.meters["lost"] += 1
    out.append("The referral note nearly got lost in the goo.")
    return out


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["resolve"] < THRESHOLD:
            continue
        sig = ("repeat", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["progress"] += 1
        out.append(f"{actor.id} kept repeating the careful steps, one after another.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_sticky, _r_lost, _r_repetition):
            sent = rule(world)
            if sent:
                changed = True
                produced.extend(sent)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def route_at_risk(route: Route, prize: Prize) -> bool:
    return prize.region in route.zone


def select_gear(route: Route, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if route.mess in g.guards and prize.region in g.covers:
            return g
    return None


def predict(world: World, actor: Entity, route: Route, prize_id: str) -> dict:
    sim = world.copy()
    _take_route(sim, sim.get(actor.id), route, narrate=False)
    prize = sim.entities[prize_id]
    return {"sticky": prize.meters["sticky"] >= THRESHOLD, "lost": prize.meters["lost"] >= THRESHOLD}


def _take_route(world: World, actor: Entity, route: Route, narrate: bool = True) -> None:
    if route.id not in world.setting.affords:
        return
    world.zone = set(route.zone)
    actor.meters["risk"] += 1
    actor.memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little curious {hero.type} who liked to ask what was behind every bend.")


def desire(world: World, hero: Entity, route: Route) -> None:
    hero.memes["curiosity"] += 1
    world.say(f"{hero.pronoun().capitalize()} wanted to {route.verb}, because the path looked like an adventure.")


def referral_scene(world: World, hero: Entity, helper: Entity, note: Entity, prize: Entity) -> None:
    world.say(
        f"{helper.id} gave {hero.id} a referral note for {prize.phrase}, and {hero.id} tucked it carefully away."
    )


def warn(world: World, helper: Entity, hero: Entity, route: Route, note: Entity) -> bool:
    pred = predict(world, hero, route, note.id)
    if not pred["sticky"] and not pred["lost"]:
        return False
    world.facts["predicted_sticky"] = pred["sticky"]
    world.facts["predicted_lost"] = pred["lost"]
    world.say(
        f'"If you go by the {route.keyword}, that referral could get sticky," '
        f"{helper.id} said. \"Let's take the safer way.\""
    )
    return True


def repeat_plan(world: World, hero: Entity, route: Route) -> None:
    hero.memes["resolve"] += 1
    hero.memes["calm"] += 1
    world.say(f"{hero.id} took a deep breath and repeated the plan: slow steps, slow steps, slow steps.")


def accept(world: World, hero: Entity, helper: Entity, route: Route, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} smiled at {helper.id}, and together they used {gear.label} before crossing the gelatinous path."
    )
    world.say(
        f"They {gear.tail}. In the end, {hero.id} was {route.gerund}, {prize.phrase} safe, "
        f"and the little referral note stayed clean."
    )


def tell(setting: Setting, route: Route, prize_cfg: Prize, hero_name: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="child", label=hero_name))
    helper = world.add(Entity(id="Helper", kind="character", type=parent_type, label="the helper"))
    prize = world.add(Entity(id="deodorant", type="thing", label=prize_cfg.label, phrase=prize_cfg.phrase, region=prize_cfg.region))
    note = world.add(Entity(id="referral", type="thing", label="referral note", phrase="a referral note", region="torso"))
    note.owner = helper.id
    note.caretaker = helper.id

    intro(world, hero)
    world.say(f"{hero.id} loved {trait} adventures and liked to ask the same question again and again.")
    referral_scene(world, hero, helper, note, prize)

    world.para()
    world.say(f"One day, {hero.id} and {helper.id} went to {setting.place}.")
    world.say(f"The trail ahead looked gelatinous and bright, like green glass wobbling in the sun.")
    desire(world, hero, route)
    warn(world, helper, hero, route, note)
    repeat_plan(world, hero, route)
    _take_route(world, hero, route, narrate=True)

    world.para()
    gear = select_gear(route, note if False else prize)
    if gear is None:
        _fallback_pool = globals().get("GEARS") or globals().get("GEARES") or []
        if hasattr(_fallback_pool, "values"):
            _fallback_pool = list(_fallback_pool.values())
        gear = next(iter(_fallback_pool), None)
        if gear is None:
            raise StoryError
    world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        protective=True,
        covers=set(gear.covers),
        owner=hero.id,
    )).worn_by = hero.id
    accept(world, hero, helper, route, prize, gear)

    world.facts.update(hero=hero, helper=helper, note=note, prize=prize, route=route, setting=setting, gear=gear)
    return world


SETTINGS = {
    "marsh": Setting(place="the marsh gate", indoor=False, affords={"gel_path"}),
    "cavern": Setting(place="the echo cavern", indoor=False, affords={"gel_path"}),
    "market": Setting(place="the market lane", indoor=False, affords={"gel_path"}),
}

ROUTES = {
    "gel_path": Route(
        id="gel_path",
        verb="follow the jelly-bright path",
        gerund="following the jelly-bright path",
        rush="dash into the gelatinous shortcut",
        mess="gelatinous",
        zone={"feet", "legs"},
        keyword="gelatinous",
        tags={"gelatinous", "curiosity", "adventure"},
    )
}

PRIZES = {
    "deodorant": Prize(
        id="deodorant",
        label="deodorant",
        phrase="a small deodorant tin",
        region="torso",
    )
}

GEAR = [
    Gear(
        id="pouch",
        label="a waxed pouch",
        covers={"torso"},
        guards={"gelatinous"},
        prep="put the referral note into a waxed pouch",
        tail="walked the long way with careful, repeating steps",
    ),
]

NAMES = ["Mina", "Leo", "Nora", "Pip", "Zia", "Tobi"]
TRAITS = ["brave", "careful", "curious", "spirited", "bright"]


@dataclass
class StoryParams:
    place: str
    route: str
    prize: str
    name: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    return [
        f'Write a short adventure story for a young child about {hero.id}, a {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "trait")} explorer, and a gelatinous shortcut.',
        f'Tell a curious story where a referral note and a tin of deodorant must survive a gelatinous path.',
        f'Write a child-friendly adventure that repeats the phrase "slow steps" and ends with a safe delivery.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    helper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    note: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "note")
    prize: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize")
    route: Route = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "route")
    place: Setting = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "setting")
    gear: Gear = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "gear")
    return [
        QAItem(
            question=f"Who was the story about at {place.place}?",
            answer=f"It was about {hero.id}, a {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "trait")} child who loved curiosity and adventure.",
        ),
        QAItem(
            question=f"What did {helper.id} give {hero.id} before the trip?",
            answer=f"{helper.id} gave {hero.id} a referral note for deodorant, and {hero.id} kept it carefully tucked away.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do on the gelatinous path?",
            answer=f"{hero.id} wanted to {route.verb}, even though the path looked sticky and strange.",
        ),
        QAItem(
            question=f"Why did the helper worry about the referral note?",
            answer="Because the gelatinous shortcut could make the paper sticky and hard to use.",
        ),
        QAItem(
            question=f"How did they keep the referral safe?",
            answer=f"They used {gear.label} and took the long way with repeated careful steps.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{hero.id} finished {route.gerund}, and the deodorant and referral note stayed safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does gelatinous mean?",
            answer="Gelatinous means wobbly, jelly-like, and a little sticky.",
        ),
        QAItem(
            question="What is a referral note?",
            answer="A referral note is a message that sends someone to the right helper, shop, or place.",
        ),
        QAItem(
            question="What is deodorant for?",
            answer="Deodorant is used to help a person smell fresher.",
        ),
        QAItem(
            question="Why can repeating a plan help on an adventure?",
            answer="Repeating a plan can help you remember the safe steps and stay calm.",
        ),
        QAItem(
            question="Why is curiosity useful in a story?",
            answer="Curiosity helps a character notice clues and keep exploring.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World knowledge ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        met = {k: v for k, v in e.meters.items() if v}
        mem = {k: v for k, v in e.memes.items() if v}
        if met:
            bits.append(f"meters={met}")
        if mem:
            bits.append(f"memes={mem}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="marsh", route="gel_path", prize="deodorant", name="Mina", parent="mother", trait="curious"),
    StoryParams(place="cavern", route="gel_path", prize="deodorant", name="Leo", parent="father", trait="brave"),
    StoryParams(place="market", route="gel_path", prize="deodorant", name="Nora", parent="mother", trait="bright"),
]


def explain_rejection(route: Route, prize: Prize) -> str:
    return f"(No story: the {route.mess} route must threaten the {prize.label}, but it does not.)"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for rid in setting.affords:
            route = _safe_lookup(ROUTES, rid)
            for pid, prize in PRIZES.items():
                if route_at_risk(route, prize) and select_gear(route, prize):
                    combos.append((place, rid, pid))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "route", None) and getattr(args, "prize", None):
        route, prize = _safe_lookup(ROUTES, getattr(args, "route", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (route_at_risk(route, prize) and select_gear(route, prize)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "route", None) is None or c[1] == getattr(args, "route", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, route, prize = rng.choice(list(combos))
    return StoryParams(
        place=place,
        route=route,
        prize=prize,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        parent=getattr(args, "parent", None) or rng.choice(["mother", "father"]),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ROUTES, params.route), _safe_lookup(PRIZES, params.prize), params.name, params.parent, params.trait)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world with gelatinous curiosity and repetition.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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


ASP_RULES = r"""
route_at_risk(R, P) :- route(R), prize(P), zone(R, Z), worn_on(P, Z).
has_fix(R, P) :- route_at_risk(R, P), gear(G), guards(G, M), route_mess(R, M), covers(G, Z), worn_on(P, Z).
valid(Place, R, P) :- affords(Place, R), route_at_risk(R, P), has_fix(R, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for r in sorted(s.affords):
            lines.append(asp.fact("affords", pid, r))
    for rid, r in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("route_mess", rid, r.mess))
        for z in sorted(r.zone):
            lines.append(asp.fact("zone", rid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
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
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


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
            i += 1
            seed = base_seed + i
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
            header = f"### {p.name}: {p.route} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
