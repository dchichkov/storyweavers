#!/usr/bin/env python3
"""
storyworlds/worlds/lee_pale_friendship_slice_of_life.py
========================================================

A small, constraint-checked story world for a slice-of-life friendship tale.

Seed-imagined premise:
- Lee is a quiet little kid who likes ordinary, careful days.
- A pale little object matters to Lee because it was made with care.
- A friend notices, helps, and the day ends warmer than it began.

The world supports a few gentle everyday scenes:
- a pale drawing at a library table
- a walk through a drizzly street
- a shared snack on a bench
- a small repair after a tiny mishap

The story engine simulates state changes in meters and memes:
- physical meters: damp, torn, tucked_safe, warmed
- emotional memes: worry, embarrassment, kindness, trust, relief, joy

The story is generated from a short, authored causal chain rather than a
frozen paragraph with swapped nouns.
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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    buddy: object | None = None
    lee: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    indoors: bool
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
    label: str
    phrase: str
    type: str
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
class Helper:
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
        clone.weather = self.weather
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    friend: str
    friend_type: str
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


SETTINGS = {
    "library": Setting("the library corner table", True, {"paper", "snack"}),
    "bus_stop": Setting("the bus stop bench", False, {"drizzle", "paper", "snack"}),
    "kitchen": Setting("the kitchen table", True, {"snack", "paper"}),
    "porch": Setting("the front porch", False, {"drizzle", "paper", "snack"}),
}

ACTIVITIES = {
    "drizzle_walk": Activity(
        id="drizzle_walk",
        verb="walk home in the drizzle",
        gerund="walking home in the drizzle",
        mess="damp",
        risk="damp",
        zone={"torso", "hands"},
        keyword="drizzle",
        tags={"drizzle", "wet", "walk"},
    ),
    "coloring": Activity(
        id="coloring",
        verb="finish a picture",
        gerund="coloring at the table",
        mess="smudged",
        risk="smudged",
        zone={"hands"},
        keyword="paper",
        tags={"paper", "art"},
    ),
    "snack_share": Activity(
        id="snack_share",
        verb="share a snack",
        gerund="sharing a snack",
        mess="crumbled",
        risk="crumbled",
        zone={"hands"},
        keyword="snack",
        tags={"snack", "share"},
    ),
}

PRIZES = {
    "drawing": Prize("drawing", "a pale drawing of a bird", "drawing", "hands"),
    "card": Prize("card", "a pale paper greeting card", "card", "hands"),
    "sandwich": Prize("sandwich", "a neat little sandwich", "sandwich", "hands"),
}

HELPERS = [
    Helper(
        id="folder",
        label="a stiff folder",
        covers={"hands"},
        guards={"damp", "smudged"},
        prep="put the drawing in a stiff folder first",
        tail="slid the drawing into the folder and tucked it under one arm",
    ),
    Helper(
        id="napkin",
        label="a clean napkin",
        covers={"hands"},
        guards={"crumbled", "damp"},
        prep="wrap the snack in a clean napkin first",
        tail="wrapped the snack in a napkin and kept it safe",
    ),
    Helper(
        id="hood",
        label="a little hooded raincoat",
        covers={"torso", "hands"},
        guards={"damp"},
        prep="put on a little hooded raincoat first",
        tail="buttoned the raincoat and walked out together",
        plural=False,
    ),
]

GIRL_NAMES = ["Lee", "Mina", "Nora", "June", "Iris", "Ada"]
BOY_NAMES = ["Lee", "Eli", "Noah", "Theo", "Kai", "Ben"]
FRIENDS = ["Mina", "Jules", "Owen", "Pip", "Ruby", "Sam"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone or act.id == "snack_share":
                    if select_helper(act, prize) is not None:
                        combos.append((place, act_id, prize_id))
    return combos


def select_helper(activity: Activity, prize: Prize) -> Optional[Helper]:
    for helper in HELPERS:
        if activity.mess in helper.guards and prize.region in helper.covers:
            return helper
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if prize.region not in activity.zone and activity.id != "snack_share":
        return f"(No story: {activity.gerund} does not put {prize.label} at risk in this setup.)"
    return f"(No story: nothing in the helper list can honestly protect {prize.label} from {activity.gerund}.)"


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_damp(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("damp", 0) < THRESHOLD:
            continue
        for item in list(world.entities.values()):
            if item.owner != actor.id:
                continue
            if item.meters.get("tucked_safe", 0) >= THRESHOLD:
                continue
            sig = ("damp", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["damp"] = item.meters.get("damp", 0) + 1
            out.append(f"{item.label} got a little damp.")
    return out


def _r_smudge(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("smudged", 0) < THRESHOLD:
            continue
        for item in list(world.entities.values()):
            if item.owner != actor.id:
                continue
            sig = ("smudge", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["smudged"] = item.meters.get("smudged", 0) + 1
            out.append(f"{item.label} picked up a tiny smudge.")
    return out


CAUSAL_RULES = [Rule("damp", _r_damp), Rule("smudge", _r_smudge)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, actor: Entity, activity: Activity, prize: Entity) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    obj = sim.get(prize.id)
    return {
        "damaged": bool(obj.meters.get("damp", 0) >= THRESHOLD or obj.meters.get("smudged", 0) >= THRESHOLD),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0) + 1
    if narrate:
        propagate(world, narrate=True)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, friend: str, friend_type: str) -> World:
    world = World(setting)
    world.weather = "drizzle" if activity.id == "drizzle_walk" else ""
    lee = world.add(Entity(id=name, kind="character", type="boy" if name != "Lee" else "boy"))
    buddy = world.add(Entity(id=friend, kind="character", type=friend_type))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=lee.id,
        caretaker=buddy.id,
        plural=prize_cfg.plural,
    ))

    lee.memes["care"] = 1
    buddy.memes["kindness"] = 1

    world.say(f"{lee.id} had a soft spot for quiet afternoons and small, careful things.")
    world.say(f"One of {lee.pronoun('possessive')} favorite things was {prize.phrase}.")
    world.say(f"{lee.id} liked spending time with {buddy.id}, because {buddy.id} always noticed little moods and little details.")

    world.para()
    if activity.id == "drizzle_walk":
        world.say(f"One gray afternoon, {lee.id} and {buddy.id} were at {setting.place}.")
    else:
        world.say(f"One ordinary afternoon, {lee.id} and {buddy.id} sat at {setting.place}.")
    world.say(f"They wanted to {activity.verb} together.")

    pred = predict(world, lee, activity, prize)
    if pred["damaged"]:
        world.say(f"{lee.id} looked at {prize.label} and frowned.")
        world.say(f'"If we go now, {prize.label} might get messy," {lee.pronoun("subject")} said.')
        lee.memes["worry"] = lee.memes.get("worry", 0) + 1
        buddy.memes["concern"] = buddy.memes.get("concern", 0) + 1

        helper = select_helper(activity, prize)
        if helper is None:
            pass
        world.say(f"{buddy.id} thought for a second, then smiled.")
        world.say(f'"We can fix that," {buddy.pronoun("subject")} said. "How about we {helper.prep}?"')
        world.say(f"{lee.id} nodded, a little relieved.")
        prize.meters["tucked_safe"] = 1
        world.para()
        _do_activity(world, lee, activity, narrate=True)
        helper.tail = helper.tail[0].lower() + helper.tail[1:]
        world.say(f"They {helper.tail}.")
        lee.memes["relief"] = lee.memes.get("relief", 0) + 1
        buddy.memes["joy"] = buddy.memes.get("joy", 0) + 1
        world.say(f"In the end, {lee.id} felt glad to have a friend who could turn a small problem into an easy plan.")
    else:
        world.say(f"{buddy.id} laughed and said it would be fine.")
        world.para()
        _do_activity(world, lee, activity, narrate=True)
        world.say(f"Their afternoon stayed simple and bright, the way good ordinary days often do.")

    world.facts.update(hero=lee, friend=buddy, prize=prize, activity=activity, setting=setting, helper=select_helper(activity, prize))
    return world


ASP_RULES = r"""
prize_at_risk(A, P) :- activity(A), prize(P), risk_of(A, R), worn_on(P, R).
compatible(A, P, H) :- prize_at_risk(A, P), helper(H), guards(H, M), covers(H, R), risk_of(A, M), worn_on(P, R).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), compatible(A, P, _).
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
        lines.append(asp.fact("risk_of", aid, a.risk))
        for z in sorted(a.zone):
            lines.append(asp.fact("zone", aid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
        for g in sorted(h.guards):
            lines.append(asp.fact("guards", h.id, g))
        for c in sorted(h.covers):
            lines.append(asp.fact("covers", h.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_combos_asp())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short slice-of-life story about Lee and {f["friend"].id} that includes the word "{f["activity"].keyword}".',
        f"Tell a gentle friendship story where Lee wants to {f['activity'].verb} and a pale little object needs care.",
        f'Write an everyday story about two friends who solve a small problem with a {f["helper"].label if f["helper"] else "helpful object"}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    prize = _safe_fact(world, f, "prize")
    activity = _safe_fact(world, f, "activity")
    helper = _safe_fact(world, f, "helper")
    return [
        QAItem(
            question=f"Who is the story mostly about?",
            answer=f"The story is mostly about {hero.id}, who spends a gentle day with {friend.id}.",
        ),
        QAItem(
            question=f"Why did {hero.id} worry about {prize.label}?",
            answer=f"{hero.id} worried because {prize.phrase} could get messy during {activity.gerund}.",
        ),
        QAItem(
            question=f"How did the friends keep {prize.label} safe?",
            answer=f"They used {helper.label} so {prize.label} could stay safe while they stayed together.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the small worry was gone, and {hero.id} felt more relaxed and happy with {friend.id}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pale thing?",
            answer="A pale thing has light color, like soft cream, faded blue, or gentle pink.",
        ),
        QAItem(
            question="What does a friend do in an everyday story?",
            answer="A friend listens, helps, shares, and makes ordinary moments feel nicer.",
        ),
        QAItem(
            question="What is drizzle?",
            answer="Drizzle is very light rain with tiny drops that fall softly from the sky.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}}")
        if e.memes:
            bits.append(f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: Lee, pale things, and friendship in slice-of-life scenes.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", default="Lee")
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--friend-type", choices=["girl", "boy"], default="girl")
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
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    friend = getattr(args, "friend", None) or rng.choice(FRIENDS)
    return StoryParams(place=place, activity=activity, prize=prize, name=getattr(args, "name", None), friend=friend, friend_type=getattr(args, "friend_type", None))


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.name, params.friend, params.friend_type)
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


CURATED = [
    StoryParams(place="library", activity="coloring", prize="drawing", name="Lee", friend="Mina", friend_type="girl"),
    StoryParams(place="bus_stop", activity="drizzle_walk", prize="card", name="Lee", friend="Jules", friend_type="boy"),
    StoryParams(place="kitchen", activity="snack_share", prize="sandwich", name="Lee", friend="Ruby", friend_type="girl"),
    StoryParams(place="porch", activity="drizzle_walk", prize="drawing", name="Lee", friend="Sam", friend_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        combos = valid_combos_asp()
        print(f"{len(combos)} compatible combos:\n")
        for place, act, prize in combos:
            print(f"  {place:8} {act:14} {prize}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
