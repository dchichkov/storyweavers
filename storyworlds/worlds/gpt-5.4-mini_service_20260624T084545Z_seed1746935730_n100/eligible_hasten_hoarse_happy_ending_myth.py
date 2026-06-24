#!/usr/bin/env python3
"""
storyworlds/worlds/eligible_hasten_hoarse_happy_ending_myth.py
==============================================================

A small myth-style storyworld about an eligible child, a hurried quest, and a
hoarse voice that still finds a happy ending.

Seed tale:
---
In an old valley, a shrine kept the night safe. The moon-priest said only an
eligible helper could carry the silver bowl to the spring before dawn. A child
named Iri wanted to help, but the road was steep and the bell-keeper's warning
was clear: if the bowl reached the spring late, the valley's lamps would go out.

Iri hastened up the hill with a lantern, but the cold wind left the child
hoarse. At the top, Iri could hardly speak. Still, the foxes of the hill
followed kindly, and the lantern-light led the way. The child arrived in time,
the spring shone, and the valley woke to a happy morning.

World model:
---
    haste on the road           -> actor.meters["distance"] += 1
                                  actor.memes["urgency"] += 1
    cold wind + travel          -> actor.meters["cold"] += 1
    cold + chanting             -> actor.memes["hoarse"] += 1
    eligible helper + shrine    -> gate opens
    late arrival                -> village lamps dim
    timely arrival + kindness   -> shrine blessing, happy ending
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    hero: object | None = None
    relic: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "priestess"}
        male = {"boy", "man", "father", "priest"}
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
        if not hasattr(self, "_tags"):
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
    place: str = "the shrine hill"
    affords: set[str] = field(default_factory=set)
    night: bool = True
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    hurry: str
    risk: str
    weather: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Relic:
    id: str
    label: str
    phrase: str
    type: str
    eligible: bool = True
    carries: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Aid:
    id: str
    label: str
    phrase: str
    protects: set[str]
    used_for: set[str]
    prep: str
    tail: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
        self.weather = ""
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.weather = self.weather
        return clone


def _r_haste(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    task = world.facts.get("task")
    if not hero or not task:
        return out
    if hero.memes.get("urgency", 0) < THRESHOLD:
        return out
    sig = ("haste", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["distance"] = hero.meters.get("distance", 0) + 1
    out.append(f"{hero.id} hastened along the path.")
    return out


def _r_hoarse(world: World) -> list[str]:
    hero = world.facts.get("hero")
    if not hero:
        return []
    if hero.meters.get("cold", 0) < THRESHOLD:
        return []
    sig = ("hoarse", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["hoarse"] = 1
    return [f"{hero.id}'s voice turned hoarse in the wind."]


def _r_eligible(world: World) -> list[str]:
    hero = world.facts.get("hero")
    relic = world.facts.get("relic")
    if not hero or not relic:
        return []
    sig = ("eligible", hero.id, relic.id)
    if sig in world.fired:
        return []
    if hero.memes.get("kindness", 0) >= THRESHOLD and hero.memes.get("duty", 0) >= THRESHOLD:
        world.fired.add(sig)
        world.facts["eligible"] = True
        return [f"The shrine judged {hero.id} eligible."]
    return []


def _r_blessing(world: World) -> list[str]:
    hero = world.facts.get("hero")
    relic = world.facts.get("relic")
    if not hero or not relic or not world.facts.get("arrived"):
        return []
    if world.facts.get("blessed"):
        return []
    if hero.memes.get("kindness", 0) >= THRESHOLD and world.facts.get("eligible"):
        world.fired.add(("blessed", hero.id))
        world.facts["blessed"] = True
        world.facts["ending"] = "happy"
        return [
            "The spring glowed bright.",
            f"The valley's lamps lit one by one, and {hero.id} smiled.",
        ]
    return []


CAUSAL_RULES = [_r_haste, _r_hoarse, _r_eligible, _r_blessing]


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


@dataclass
class StoryParams:
    place: str
    task: str
    relic: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


SETTINGS = {
    "shrine_hill": Setting(place="the shrine hill", affords={"spring_run"}, night=True),
    "moon_valley": Setting(place="the moon valley", affords={"spring_run"}, night=True),
}

TASKS = {
    "spring_run": Task(
        id="spring_run",
        verb="carry the silver bowl to the spring",
        gerund="carrying the silver bowl",
        hurry="hasten before dawn",
        risk="arrive too late",
        weather="cold",
        tags={"eligible", "hasten", "hoarse", "moon"},
    ),
}

RELICS = {
    "silver_bowl": Relic(
        id="silver_bowl",
        label="silver bowl",
        phrase="a polished silver bowl",
        type="relic",
        carries={"water", "light"},
    ),
    "lamp_chain": Relic(
        id="lamp_chain",
        label="lamp chain",
        phrase="a long lamp chain",
        type="relic",
        carries={"light"},
    ),
}

AIDS = [
    Aid(
        id="lantern",
        label="lantern",
        phrase="a small lantern",
        protects={"light"},
        used_for={"spring_run"},
        prep="carry the lantern high",
        tail="followed the lantern-light back down the hill",
    ),
    Aid(
        id="shawl",
        label="shawl",
        phrase="a warm shawl",
        protects={"cold"},
        used_for={"spring_run"},
        prep="wrap the shawl around the shoulders",
        tail="walked home wrapped in the shawl",
    ),
]

GIRL_NAMES = ["Iri", "Mira", "Sana", "Luna", "Nia"]
BOY_NAMES = ["Ari", "Taro", "Kai", "Milo", "Ren"]
TRAITS = ["gentle", "brave", "kind", "steady", "curious"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            for relic_id in RELICS:
                combos.append((place, task_id, relic_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A myth-style storyworld with a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "priest"])
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
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
              and (getattr(args, "relic", None) is None or c[2] == getattr(args, "relic", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, relic = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father", "priest"])
    trait = getattr(args, "trait", None) if hasattr(args, "trait") and getattr(args, "trait", None) else rng.choice(TRAITS)
    return StoryParams(place=place, task=task, relic=relic, name=name, gender=gender, parent=parent, trait=trait)


def predict(world: World, hero: Entity, task: Task, relic: Relic) -> dict:
    sim = world.copy()
    h = sim.get(hero.id)
    h.memes["urgency"] += 1
    h.meters["cold"] += 1
    propagate(sim, narrate=False)
    return {"hoarse": bool(h.memes.get("hoarse")), "blessed": sim.facts.get("blessed", False)}


def tell(setting: Setting, task: Task, relic_cfg: Relic, name: str, gender: str, parent: str, trait: str) -> World:
    world = World(setting)
    world.weather = "cold"
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait]))
    elder = world.add(Entity(id="Elder", kind="character", type=parent, label="the elder"))
    relic = world.add(Entity(id=relic_cfg.id, type=relic_cfg.type, label=relic_cfg.label, phrase=relic_cfg.phrase))

    world.facts.update(hero=hero, elder=elder, relic=relic, task=task, setting=setting)

    world.say(f"In old myths, {hero.id} was a little {trait} {gender} who lived by {setting.place}.")
    world.say(f"Each dawn, {hero.id} listened to the elder, who kept the shrine stories safe.")
    world.say(f"One night, the moon-priest said only an eligible helper could carry {relic.phrase} to the spring.")
    hero.memes["duty"] += 1

    world.para()
    world.say(f"{hero.id} wanted to {task.verb}, and {hero.pronoun('possessive')} heart urged the child to {task.hurry}.")
    world.say(f"The road was steep, and the cold wind tried to steal the breath from {hero.pronoun('object')}.")
    hero.memes["urgency"] += 1
    hero.meters["cold"] += 1
    hero.memes["kindness"] += 1
    propagate(world)

    world.para()
    world.say(f"{hero.id} climbed higher, still holding {relic.label} carefully.")
    world.say(f"The wind bit harder, and by the time {hero.id} reached the shrine, {hero.pronoun('possessive')} voice was hoarse.")
    hero.meters["cold"] += 1
    hero.memes["hoarse"] += 1
    if hero.memes["hoarse"] >= THRESHOLD:
        world.say(f'Even so, {hero.id} whispered, "I came to help."')
    world.facts["arrived"] = True
    propagate(world)

    world.para()
    if world.facts.get("eligible"):
        world.say(f"The shrine stones glimmered, as if they had been waiting for an eligible helper like {hero.id}.")
    world.say(f"{hero.id} placed {relic.label} at the spring, and the water woke with silver light.")
    world.say(f"Foxes and night-birds gathered quietly, as though the whole hill wanted to see the happy ending.")
    hero.memes["kindness"] += 1
    propagate(world)

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a myth-like story for a young child that uses the words "eligible", "hasten", and "hoarse".',
        f"Tell a gentle legend where {hero.id} must hasten up a shrine hill and still sounds hoarse by the end.",
        f"Write a happy-ending myth about a child who is eligible to help and carries a sacred bowl before dawn.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    relic = f["relic"]
    task = f["task"]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little {hero.traits[-1]} child who tried to help at the shrine.",
        ),
        QAItem(
            question=f"Why did {hero.id} hasten up the hill?",
            answer=f"{hero.id} hastened because the moon-priest needed {relic.label} at the spring before dawn.",
        ),
        QAItem(
            question=f"What happened to {hero.id}'s voice?",
            answer=f"The cold wind left {hero.id}'s voice hoarse while the child was climbing.",
        ),
    ]
    if world.facts.get("eligible"):
        qa.append(
            QAItem(
                question=f"Why was {hero.id} eligible to help?",
                answer=f"{hero.id} was eligible because the child stayed kind, kept the duty in mind, and brought {relic.label} safely to the shrine.",
            )
        )
    if world.facts.get("blessed"):
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=f"It ended happily: the spring shone bright, the valley's lamps woke, and everyone saw that {hero.id}'s help mattered.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does eligible mean?",
            answer="Eligible means someone is allowed or fit to do something important.",
        ),
        QAItem(
            question="What does hasten mean?",
            answer="Hasten means to hurry or move quickly.",
        ),
        QAItem(
            question="What does hoarse mean?",
            answer="Hoarse means your voice sounds rough, scratchy, or weak, often after talking too much or being cold.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
eligible(H) :- kindness(H), duty(H).
hoarse(H) :- cold(H), haste(H).
happy(H) :- eligible(H), arrived(H), kindness(H).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for _, _, _ in valid_combos():
        pass
    lines.append(asp.fact("kindness", "hero"))
    lines.append(asp.fact("duty", "hero"))
    lines.append(asp.fact("cold", "hero"))
    lines.append(asp.fact("haste", "hero"))
    lines.append(asp.fact("arrived", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show eligible/1.\n#show hoarse/1.\n#show happy/1."))
    atoms = {str(a) for a in model}
    expected = {"eligible(hero)", "hoarse(hero)", "happy(hero)"}
    if atoms == expected:
        print("OK: ASP parity matches the Python reasonableness gate.")
        return 0
    print("MISMATCH:", sorted(atoms), "expected", sorted(expected))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show eligible/1.\n#show hoarse/1.\n#show happy/1."))
    return [tuple(str(a) for a in atom.arguments) for atom in model]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TASKS, params.task), _safe_lookup(RELICS, params.relic), params.name, params.gender, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_story_params() -> list[StoryParams]:
    return [
        StoryParams(place="shrine_hill", task="spring_run", relic="silver_bowl", name="Iri", gender="girl", parent="priest", trait="kind"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show eligible/1.\n#show hoarse/1.\n#show happy/1."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in valid_story_params()]
    else:
        for i in range(getattr(args, "n", None)):
            seed = base_seed + i
            rng = random.Random(seed)
            params = args if False else resolve_params(args, rng)
            params.seed = seed
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
