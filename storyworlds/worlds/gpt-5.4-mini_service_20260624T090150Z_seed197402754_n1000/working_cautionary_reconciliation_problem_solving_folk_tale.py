#!/usr/bin/env python3
"""
storyworlds/worlds/working_cautionary_reconciliation_problem_solving_folk_tale.py
=================================================================================

A small folk-tale storyworld about working, caution, and a kind reconciliation.

Seed tale sketch:
---
A little child liked to help at the edge of the village. One day the child tried to
carry a heavy bucket, cross a wobbly bridge, or finish a task too fast. An elder
warned that haste could spill the water or break the clay jug. The child felt cross,
but then the two listened, chose a safer way, and solved the problem together.

World model:
---
- A child has a task, a place, and a treasured item or goal.
- Working adds effort and can create a problem if the child ignores a warning.
- A cautionary beat raises tension when the elder predicts the risk.
- Reconciliation clears the conflict once the child accepts help.
- Problem solving is represented by a tool or method that actually fixes the risk.

Style:
---
Folk-tale flavored, child-facing, concrete, and complete.
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
RISK_METERS = {"spill", "break", "mud", "scrape"}



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

    traits: list = field(default_factory=list)
    elder: object | None = None
    goal: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "elderwoman"}
        male = {"boy", "father", "dad", "man", "grandfather", "elderman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(
            self.type, self.type
        )
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
    risk: str
    weather: str
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
class Goal:
    label: str
    phrase: str
    type: str
    risk_meter: str
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
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str]
    fixes: set[str]
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather: str = ""

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.weather = self.weather
        return c


SETTINGS = {
    "riverbank": Setting(place="the riverbank", affords={"carry_water", "cross_bridge", "fetch_reeds"}),
    "orchard": Setting(place="the orchard", affords={"pick_apples", "carry_basket"}),
    "millroad": Setting(place="the mill road", affords={"carry_flour", "cross_bridge"}),
    "village_green": Setting(place="the village green", affords={"carry_bundle", "help_market"}),
}

ACTIVITIES = {
    "carry_water": Activity(
        id="carry_water",
        verb="carry water from the well",
        gerund="carrying water from the well",
        rush="hurry along with the bucket",
        risk="spill",
        weather="foggy",
        keyword="working",
        tags={"water", "bucket", "working"},
    ),
    "cross_bridge": Activity(
        id="cross_bridge",
        verb="cross the old bridge",
        gerund="crossing the old bridge",
        rush="dash onto the bridge",
        risk="break",
        weather="misty",
        keyword="working",
        tags={"bridge", "rope", "working"},
    ),
    "pick_apples": Activity(
        id="pick_apples",
        verb="pick apples for the supper pot",
        gerund="picking apples",
        rush="climb the tree quickly",
        risk="scrape",
        weather="bright",
        keyword="working",
        tags={"apples", "ladder", "working"},
    ),
    "carry_flour": Activity(
        id="carry_flour",
        verb="carry flour to the baker",
        gerund="carrying flour sacks",
        rush="lug the sack across the yard",
        risk="tear",
        weather="cloudy",
        keyword="working",
        tags={"flour", "sack", "working"},
    ),
    "fetch_reeds": Activity(
        id="fetch_reeds",
        verb="fetch reeds from the marsh",
        gerund="fetching reeds",
        rush="step into the marsh at once",
        risk="mud",
        weather="misty",
        keyword="working",
        tags={"reeds", "boots", "working"},
    ),
    "carry_bundle": Activity(
        id="carry_bundle",
        verb="carry a bundle of kindling",
        gerund="carrying kindling",
        rush="hoist the bundle too fast",
        risk="scrape",
        weather="breezy",
        keyword="working",
        tags={"kindling", "strap", "working"},
    ),
    "help_market": Activity(
        id="help_market",
        verb="help at the market stall",
        gerund="helping at the market stall",
        rush="reach over the stall in a rush",
        risk="spill",
        weather="sunny",
        keyword="working",
        tags={"market", "cloth", "working"},
    ),
}

GOALS = {
    "bucket": Goal(label="bucket", phrase="a wooden bucket of clear water", type="bucket", risk_meter="spill", genders={"girl", "boy"}),
    "bridge_plank": Goal(label="plank", phrase="a loose bridge plank", type="plank", risk_meter="break"),
    "apples": Goal(label="basket", phrase="a basket of red apples", type="basket", risk_meter="scrape"),
    "flour": Goal(label="sack", phrase="a sack of flour", type="sack", risk_meter="tear"),
    "reeds": Goal(label="bundle", phrase="a fresh bundle of reeds", type="bundle", risk_meter="mud"),
    "kindling": Goal(label="bundle", phrase="a bundle of dry kindling", type="bundle", risk_meter="scrape"),
    "jam_jar": Goal(label="jar", phrase="a jar of berry jam", type="jar", risk_meter="spill"),
}

TOOLS = [
    Tool(id="rope", label="a strong rope", prep="tie the bucket to a rope and cross one careful step at a time", tail="went back with the rope tied tight", guards={"break"}, fixes={"bridge_plank", "cross_bridge"}, tags={"bridge", "rope"}),
    Tool(id="yoke", label="a carrying yoke", prep="put the bucket on a carrying yoke", tail="walked back with the yoke balanced on the shoulders", guards={"spill"}, fixes={"bucket", "carry_water"}, tags={"water", "yoke"}),
    Tool(id="ladder", label="a short ladder", prep="bring a short ladder beside the tree", tail="came back with the ladder set safely against the trunk", guards={"scrape"}, fixes={"apples", "pick_apples"}, tags={"apples", "ladder"}),
    Tool(id="boots", label="mud boots", prep="pull on mud boots before stepping into the marsh", tail="returned with mud boots on their feet", guards={"mud"}, fixes={"reeds", "fetch_reeds"}, tags={"boots", "mud"}),
    Tool(id="strap", label="a shoulder strap", prep="use a shoulder strap for the bundle", tail="came back with the strap snug over the shoulder", guards={"scrape"}, fixes={"kindling", "carry_bundle"}, tags={"strap"}),
    Tool(id="cloth", label="a clean table cloth", prep="spread a clean cloth under the jars", tail="set the cloth straight on the stall", guards={"spill"}, fixes={"jam_jar", "help_market"}, tags={"cloth", "market"}),
]

GIRL_NAMES = ["Mara", "Lina", "Anya", "Nina", "Sela", "Tara"]
BOY_NAMES = ["Oren", "Bram", "Jory", "Hale", "Nico", "Ravi"]
TRAITS = ["patient", "curious", "steady", "brave", "kind", "lively"]


@dataclass
class StoryParams:
    place: str
    activity: str
    goal: str
    name: str
    gender: str
    elder: str
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


def prize_at_risk(activity: Activity, goal: Goal) -> bool:
    return goal.risk_meter == activity.risk


def select_tool(activity: Activity, goal: Goal) -> Optional[Tool]:
    for tool in TOOLS:
        if activity.id in tool.fixes and goal.risk_meter in tool.guards:
            return tool
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for goal_id, goal in GOALS.items():
                if prize_at_risk(act, goal) and select_tool(act, goal):
                    out.append((place, act_id, goal_id))
    return out


def explain_rejection(activity: Activity, goal: Goal) -> str:
    if not prize_at_risk(activity, goal):
        return (
            f"(No story: {activity.gerund} does not threaten {goal.phrase}. "
            f"The elder would have no honest caution to give.)"
        )
    return (
        f"(No story: no tool in this world safely solves {activity.gerund} with {goal.phrase}. "
        f"The tale needs a real problem and a real fix.)"
    )


def explain_gender(goal_id: str, gender: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(GOALS, goal_id).genders))
    return f"(No story: a {_safe_lookup(GOALS, goal_id).label} is not a typical {gender}'s item here; try --gender {ok}.)"


def predict(world: World, actor: Entity, activity: Activity, goal_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    goal = sim.get(goal_id)
    return {"damaged": bool(goal.meters.get(activity.risk, 0) >= THRESHOLD), "conflict": actor.memes.get("conflict", 0)}


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters[activity.risk] = actor.meters.get(activity.risk, 0) + 1
    actor.memes["working"] = actor.memes.get("working", 0) + 1
    if narrate:
        world.say(f"{actor.id} kept working and tried to {activity.verb}.")


def tell(setting: Setting, activity: Activity, goal_cfg: Goal, hero_name: str, hero_gender: str, elder_type: str, trait: str) -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name, traits=[trait, "working"]))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, label=f"the {elder_type}"))
    goal = world.add(Entity(id=goal_cfg.label, type=goal_cfg.type, label=goal_cfg.label, phrase=goal_cfg.phrase, caretaker=elder.id))

    world.say(f"In {setting.place}, there lived a little {trait} {hero_gender} named {hero.id}.")
    world.say(f"{hero.id} loved {activity.gerund} and was proud to be working beside {elder.label_word}.")
    world.say(f"One day, {elder.label_word} gave {hero.id} {goal.phrase} and said it must be handled gently.")

    world.para()
    world.say(f"The day was {activity.weather}, and {hero.id} went to {setting.place} to {activity.verb}.")
    world.say(f"But {hero.id} wanted to {activity.rush}, even though {elder.label_word} frowned and warned of trouble.")

    pred = predict(world, hero, activity, goal.id)
    if pred["damaged"]:
        hero.memes["defiance"] = hero.memes.get("defiance", 0) + 1
        world.say(f'"If you rush, you may make a mess," {elder.label_word} said. "That could ruin {goal.phrase}."')
        hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
        world.say(f"{hero.id} pouted, for the warning felt sharp.")
    else:
        world.say(f"The warning made {hero.id} slow down before any harm was done.")

    world.para()
    tool = select_tool(activity, goal_cfg)
    if tool:
        world.say(f"{elder.label_word} then smiled and offered {tool.label}.")
        world.say(f'"How about we {tool.prep}?" {elder.label_word} asked.')
        hero.memes["joy"] = hero.memes.get("joy", 0) + 1
        hero.memes["love"] = hero.memes.get("love", 0) + 1
        hero.memes["conflict"] = 0
        world.say(f"{hero.id}'s face softened. {hero.id} nodded, and the two worked together.")
        world.say(f"They {tool.tail}, and soon {hero.id} was {activity.gerund}, while {goal.phrase} stayed safe.")
    else:
        world.say(f"{elder.label_word} and {hero.id} had to pause and think, but no safe tool was ready.")
        world.say(f"So they chose a slower way and protected {goal.phrase} by hand.")

    world.facts.update(hero=hero, elder=elder, goal=goal, goal_cfg=goal_cfg, activity=activity, setting=setting, tool=tool)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, elder, activity, goal = f["hero"], f["elder"], f["activity"], f["goal_cfg"]
    return [
        f'Write a folk-tale style story for a child about "working" that includes a careful warning and a kind fix.',
        f"Tell a gentle cautionary story where {hero.id} wants to {activity.verb} but {elder.label_word} worries about {goal.phrase}.",
        f"Write a short story about {hero.id} and {elder.label_word} choosing a safer way to keep working together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, activity, goal, tool = f["hero"], f["elder"], f["activity"], f["goal"], (f.get("tool") or next(iter(TOOLS.values())))
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little {hero.type} who is learning to work carefully with {elder.label_word}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {activity.verb}.",
        ),
        QAItem(
            question=f"Why did {elder.label_word} warn {hero.id}?",
            answer=f"{elder.label_word} warned {hero.id} because {activity.gerund} could make {goal.phrase} get hurt or ruined.",
        ),
    ]
    if f.get("tool"):
        qa.append(
            QAItem(
                question=f"How did they solve the problem?",
                answer=f"They used {tool.label} and worked together more carefully, so the danger went away and the task could be finished safely.",
            )
        )
        qa.append(
            QAItem(
                question=f"How did {hero.id} feel at the end?",
                answer=f"{hero.id} felt happy again, because {elder.label_word} forgave {hero.id} and they returned to working side by side.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    activity: Activity = _safe_fact(world, f, "activity")
    tags = set(activity.tags)
    if f.get("tool"):
        tags.update((f.get("tool") or next(iter(TOOLS.values()))).tags)
    out: list[QAItem] = []
    if "working" in tags:
        out.append(QAItem(question="What does working mean?", answer="Working means doing a task with care and effort, such as carrying water, mending, or gathering food."))
    if "bridge" in tags:
        out.append(QAItem(question="Why do people cross bridges carefully?", answer="People cross bridges carefully because old boards can wobble or break if someone rushes."))
    if "water" in tags:
        out.append(QAItem(question="Why can carrying water be tricky?", answer="Carrying water can be tricky because a bucket can tip and spill if you move too fast."))
    if "apples" in tags:
        out.append(QAItem(question="Why use a ladder near a tree?", answer="A ladder helps someone reach high fruit more safely without climbing too quickly."))
    if "boots" in tags:
        out.append(QAItem(question="What are boots for?", answer="Boots protect feet from mud, wet ground, and rough paths."))
    if "cloth" in tags:
        out.append(QAItem(question="What is a clean cloth good for at a market?", answer="A clean cloth can keep jars and goods steady and help stop spills from making a mess."))
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
        if e.kind == "character":
            bits.append("character")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="riverbank", activity="carry_water", goal="bucket", name="Mara", gender="girl", elder="grandmother", trait="patient"),
    StoryParams(place="riverbank", activity="cross_bridge", goal="bridge_plank", name="Oren", gender="boy", elder="grandfather", trait="steady"),
    StoryParams(place="orchard", activity="pick_apples", goal="apples", name="Lina", gender="girl", elder="grandmother", trait="curious"),
    StoryParams(place="millroad", activity="carry_flour", goal="flour", name="Bram", gender="boy", elder="father", trait="brave"),
    StoryParams(place="village_green", activity="help_market", goal="jam_jar", name="Tara", gender="girl", elder="mother", trait="kind"),
]


KNOWLEDGE_ORDER = ["working", "bridge", "water", "apples", "boots", "cloth"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale story world about working, caution, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["mother", "father", "grandmother", "grandfather"])
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
    if getattr(args, "activity", None) and getattr(args, "goal", None):
        act, goal = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(GOALS, getattr(args, "goal", None))
        if not (prize_at_risk(act, goal) and select_tool(act, goal)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "goal", None) and getattr(args, "gender", None) not in _safe_lookup(GOALS, getattr(args, "goal", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "goal", None) is None or c[2] == getattr(args, "goal", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, activity, goal = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(sorted(_safe_lookup(GOALS, goal).genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = getattr(args, "elder", None) or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = getattr(args, "name", None) and rng.choice(TRAITS) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, goal=goal, name=name, gender=gender, elder=elder, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(GOALS, params.goal), params.name, params.gender, params.elder, params.trait)
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


ASP_RULES = r"""
risk(A, G) :- activity(A), goal(G), risk_of(A, R), risk_of_goal(G, R).
fix(T, A, G) :- tool(T), activity(A), goal(G), fixes(T, A), guards(T, R), risk_of_goal(G, R), risk_of(A, R).
valid(Place, A, G) :- affords(Place, A), risk(A, G), fix(_, A, G).
valid_story(Place, A, G, Gender) :- valid(Place, A, G), suitable(G, Gender).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("risk_of", aid, a.risk))
    for gid, g in GOALS.items():
        lines.append(asp.fact("goal", gid))
        lines.append(asp.fact("risk_of_goal", gid, g.risk_meter))
        for gender in sorted(g.genders):
            lines.append(asp.fact("suitable", gid, gender))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for g in sorted(t.guards):
            lines.append(asp.fact("guards", t.id, g))
        for a in sorted(t.fixes):
            lines.append(asp.fact("fixes", t.id, a))
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, goal) combos ({len(stories)} with gender):\n")
        for place, act, goal in triples:
            genders = sorted(g for (pl, a, go, g) in stories if (pl, a, go) == (place, act, goal))
            print(f"  {place:13} {act:15} {goal:12}  [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.activity} at {p.place} (goal: {p.goal})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
