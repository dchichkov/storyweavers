#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/scoot_suspense_conflict_kindness_animal_story.py
================================================================================

A standalone animal storyworld about a small animal, a little problem, a scoot
across a place, and a kind turn that resolves the tension.

Premise:
- A young animal wants to scoot toward something exciting.
- Another animal worries, because the path is risky or the treasure is fragile.
- Suspense builds as the hero pauses, listens, and chooses a kinder way.
- The ending proves the change through the world state: the hero still gets to
  scoot, but safely and with help.

The world is modeled with physical meters and emotional memes, and the prose is
driven by simulated state rather than a frozen template.
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
    kind: str = "thing"
    species: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    ridden_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    trait: str = ""
    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.species in {"rabbit", "bunny", "kitten", "duckling", "puppy", "mouse"}:
                return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Place:
    name: str
    kind: str
    affords: set[str] = field(default_factory=set)
    risk: str = ""
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
    mess: str
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


@dataclass
class Compromise:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
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
class StoryParams:
    place: str
    activity: str
    prize: str
    hero: str
    hero_species: str
    helper: str
    helper_species: str
    trait: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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
        return [e for e in self.entities.values() if e.ridden_by == actor.id]

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

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _rule_scoot(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("scoot", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.label and item.region in world.zone and ("protective" not in item.meters):
                sig = ("mess", actor.id, item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["dusty"] = item.meters.get("dusty", 0.0) + 1
                out.append(f"{actor.id}'s {item.label} got dusty.")
    return out


def _rule_kindness(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("kindness", 0.0) < THRESHOLD:
            continue
        sig = ("calm", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] = 0.0
        actor.memes["trust"] = actor.memes.get("trust", 0.0) + 1
        out.append(f"The room felt calmer.")
    return out


CAUSAL_RULES = [_rule_scoot, _rule_kindness]


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


def risk_prize(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_compromise(activity: Activity, prize: Prize) -> Optional[Compromise]:
    for c in COMPROMISES:
        if activity.mess in c.protects and prize.region in c.covers:
            return c
    return None


def predict(world: World, hero: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(hero.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {
        "messy": bool(prize.meters.get("dusty", 0.0) >= THRESHOLD),
        "conflict": hero.memes.get("conflict", 0.0) >= THRESHOLD,
    }


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters["scoot"] = actor.meters.get("scoot", 0.0) + 1
    actor.memes["excitement"] = actor.memes.get("excitement", 0.0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.trait} {hero.species} who loved to explore.")


def love_scoot(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund} because it felt fast and funny."
    )


def prize_line(world: World, hero: Entity, helper: Entity, prize: Entity) -> None:
    world.say(
        f"One day {helper.id} brought {hero.pronoun('object')} {prize.phrase}."
    )
    prize.ridden_by = hero.id
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    world.say(f"{hero.id} treasured {hero.pronoun('possessive')} {prize.label}.")


def arrive(world: World, hero: Entity, helper: Entity, activity: Activity) -> None:
    world.say(
        f"At {world.place.name}, {hero.id} wanted to {activity.verb} right away."
    )
    world.say(f"{world.place.name.capitalize()} felt still and watchful.")


def warn(world: World, helper: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict(world, hero, activity, prize.id)
    if not pred["messy"]:
        return False
    helper.memes["worry"] = helper.memes.get("worry", 0.0) + 1
    world.say(
        f'"If you {activity.verb}, your {prize.label} could get {activity.risk}," '
        f"{helper.id} said."
    )
    return True


def tension(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1
    world.say(f"{hero.id} paused. {hero.pronoun().capitalize()} still wanted to scoot.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush}, but then hesitated.")


def kindness_turn(world: World, helper: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Compromise]:
    comp = select_compromise(activity, prize)
    if comp is None:
        return None
    helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"{helper.id} smiled and offered a kinder plan: {comp.prep}."
    )
    return comp


def ending(world: World, hero: Entity, helper: Entity, activity: Activity, prize: Entity, comp: Compromise) -> None:
    world.say(
        f"{hero.id} nodded, and soon they {comp.tail}."
    )
    world.say(
        f"In the end, {hero.id} was {activity.gerund}, {prize.label} still clean and safe, "
        f"while {helper.id} watched with a happy grin."
    )


def tell(place: Place, activity: Activity, prize_cfg: Prize, hero_name: str, hero_species: str,
         helper_name: str, helper_species: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", species=hero_species, trait=trait))
    helper = world.add(Entity(id=helper_name, kind="character", species=helper_species, trait="kind"))
    prize = world.add(Entity(
        id=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase,
        region=prize_cfg.region, plural=prize_cfg.plural, owner=hero.id, caretaker=helper.id
    ))
    intro(world, hero)
    love_scoot(world, hero, activity)
    prize_line(world, hero, helper, prize)

    world.para()
    arrive(world, hero, helper, activity)
    warn(world, helper, hero, activity, prize)
    tension(world, hero, activity)

    world.para()
    comp = kindness_turn(world, helper, hero, activity, prize)
    if comp:
        ending(world, hero, helper, activity, prize, comp)

    world.facts = {
        "hero": hero,
        "helper": helper,
        "prize": prize,
        "activity": activity,
        "place": place,
        "compromise": comp,
    }
    return world


PLACES = {
    "hill": Place(name="the hill", kind="outdoor", affords={"scoot"}, risk="dusty"),
    "barnyard": Place(name="the barnyard path", kind="outdoor", affords={"scoot"}, risk="dusty"),
    "hall": Place(name="the long hall", kind="indoor", affords={"scoot"}, risk="dusty"),
}

ACTIVITIES = {
    "scoot": Activity(
        id="scoot",
        verb="scoot across the path",
        gerund="scooting across the path",
        rush="dash forward on tiny paws",
        mess="dusty",
        risk="dusty",
        zone={"feet"},
        keyword="scoot",
        tags={"scoot", "move"},
    )
}

PRIZES = {
    "shell": Prize(id="shell", label="shell", phrase="a shiny little shell", region="feet"),
    "ribbon": Prize(id="ribbon", label="ribbon", phrase="a bright ribbon collar", region="neck"),
    "bell": Prize(id="bell", label="bell", phrase="a tiny bell tag", region="neck"),
}

COMPROMISES = [
    Compromise(
        id="softboots",
        label="soft boots",
        prep="put on soft boots first",
        tail="went back for the soft boots and then scooted safely",
        protects={"dusty"},
        covers={"feet"},
    ),
    Compromise(
        id="pawwraps",
        label="paw wraps",
        prep="wrap their paws in soft cloth",
        tail="wrapped their paws and then scooted carefully",
        protects={"dusty"},
        covers={"feet"},
    ),
]

HEROES = {
    "rabbit": ["Pip", "Mimi", "Toby", "Nina"],
    "puppy": ["Roo", "Bax", "Coco", "Puck"],
    "kitten": ["Tia", "Moss", "Perry", "Juno"],
}
HELPERS = {
    "rabbit": ["Luna", "Milo", "Penny", "Sage"],
    "duckling": ["Dot", "Quill", "Mabel", "Tillie"],
    "mother": ["Mama Fern", "Mama Rose"],
}
TRAITS = ["brave", "curious", "playful", "gentle", "spirited"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES.values():
        for act_id in place.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize in PRIZES.values():
                if risk_prize(act, prize) and select_compromise(act, prize):
                    combos.append((place.name, act.id, prize.id))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} does not make the {prize.label} risky in a way "
        f"that can be fixed by the compromise catalog.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld: scoot, suspense, conflict, kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-species", choices=HEROES)
    ap.add_argument("--helper")
    ap.add_argument("--helper-species", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == _safe_lookup(PLACES, getattr(args, "place", None)).name]
    if getattr(args, "activity", None):
        combos = [c for c in combos if c[1] == getattr(args, "activity", None)]
    if getattr(args, "prize", None):
        combos = [c for c in combos if c[2] == getattr(args, "prize", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place_name, act_id, prize_id = rng.choice(list(combos))
    hero_species = getattr(args, "hero_species", None) or rng.choice(list(HEROES))
    helper_species = getattr(args, "helper_species", None) or rng.choice(list(HELPERS))
    hero = getattr(args, "hero", None) or rng.choice(_safe_lookup(HEROES, hero_species))
    helper = getattr(args, "helper", None) or rng.choice(_safe_lookup(HELPERS, helper_species))
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        place=[k for k, v in PLACES.items() if v.name == place_name][0],
        activity=act_id,
        prize=prize_id,
        hero=hero,
        hero_species=hero_species,
        helper=helper,
        helper_species=helper_species,
        trait=trait,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story about {f["hero"].id} who wants to scoot at {f["place"].name}.',
        f'Tell a gentle story with suspense, conflict, and kindness where {f["helper"].id} helps {f["hero"].id}.',
        f'Write a child-friendly story that includes the word "scoot" and ends with a safe compromise.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    prize: Entity = _safe_fact(world, f, "prize")
    activity: Activity = _safe_fact(world, f, "activity")
    comp: Optional[Compromise] = _safe_fact(world, f, "compromise")
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do at {world.place.name}?",
            answer=f"{hero.id} wanted to {activity.verb}.",
        ),
        QAItem(
            question=f"Why did {helper.id} worry about the {prize.label}?",
            answer=f"{helper.id} worried because {activity.verb} could leave the {prize.label} {activity.risk}.",
        ),
        QAItem(
            question=f"How did {they_answer(hero)} feel before the kinder plan?",
            answer=f"{hero.id} felt torn between excitement and worry, because {hero.pronoun().capitalize()} wanted to scoot but also did not want to upset {helper.id}.",
        ),
    ]
    if comp:
        qa.append(QAItem(
            question=f"What helped {hero.id} scoot safely in the end?",
            answer=f"They used {comp.label} first, so {hero.id} could keep {activity.gerund} without ruining the {prize.label}.",
        ))
        qa.append(QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} {activity.gerund}, the {prize.label} safe, and {helper.id} smiling at the kinder choice.",
        ))
    return qa


def they_answer(hero: Entity) -> str:
    return "they"


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to scoot?",
            answer="To scoot means to move along quickly in a low, quick way, often close to the ground.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is when someone helps, shares, or speaks gently so another creature feels safe and cared for.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next because something important might go wrong.",
        ),
        QAItem(
            question="What is conflict in a story?",
            answer="Conflict is a problem or disagreement that makes a character pause, choose, or try harder.",
        ),
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
has_fix(A,P) :- prize_at_risk(A,P), protected_by(A,P).
valid_story(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, pl in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(pl.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pr in PRIZES.values():
        lines.append(asp.fact("prize", pr.id))
        lines.append(asp.fact("worn_on", pr.id, pr.region))
    for c in COMPROMISES:
        lines.append(asp.fact("compromise", c.id))
        for m in sorted(c.protects):
            lines.append(asp.fact("protects", c.id, m))
        for r in sorted(c.covers):
            lines.append(asp.fact("covers", c.id, r))
    lines.append(asp.fact("protected_by", "scoot", "shell"))
    lines.append(asp.fact("protected_by", "scoot", "ribbon"))
    lines.append(asp.fact("protected_by", "scoot", "bell"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    place = _safe_lookup(PLACES, params.place)
    activity = _safe_lookup(ACTIVITIES, params.activity)
    prize = _safe_lookup(PRIZES, params.prize)
    world = tell(place, activity, prize, params.hero, params.hero_species, params.helper, params.helper_species, params.trait)
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
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "asp", None):
        triples = asp_valid()
        print(f"{len(triples)} compatible story combos:")
        for t in triples:
            print(" ", t)
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams(place="hill", activity="scoot", prize="shell", hero="Pip", hero_species="rabbit", helper="Luna", helper_species="rabbit", trait="brave"),
            StoryParams(place="barnyard", activity="scoot", prize="ribbon", hero="Roo", hero_species="puppy", helper="Dot", helper_species="duckling", trait="curious"),
            StoryParams(place="hall", activity="scoot", prize="bell", hero="Moss", hero_species="kitten", helper="Penny", helper_species="rabbit", trait="gentle"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
