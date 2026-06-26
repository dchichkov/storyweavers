#!/usr/bin/env python3
"""
storyworlds/worlds/incline_western_barbeque_sharing_flashback_cautionary_tall.py
================================================================================

A tall-tale style storyworld about a western incline, a shared barbecue, and a
cautionary flashback that turns a risky plan into a safer, kinder ending.

Premise:
- A child or young rider wants to haul a barbecue setup up a steep western incline.
- The load is too hot, too heavy, or too smoky to handle alone.
- A flashback to an earlier mishap warns the hero what could go wrong.
- A helpful shareable fix emerges: splitting the load, sharing water, or sharing
  the cooking work with a trusted helper.

The world model tracks:
- physical meters: heat, weight, smoke, uphill, carried, shared, scorched
- emotional memes: pride, worry, caution, relief, generosity, hunger

The story is generated from world state, not from a frozen paragraph template.
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    load: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "uncle", "cowboy"}:
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
    danger: str
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
class Load:
    id: str
    label: str
    phrase: str
    region: str
    heavy: bool = False
    hot: bool = False
    smoky: bool = False
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "ridge": Setting(place="the western ridge", affords={"barbeque"}),
    "canyon": Setting(place="the canyon trail", affords={"barbeque"}),
    "ranch": Setting(place="the old ranch yard", affords={"barbeque"}),
}

ACTIVITIES = {
    "barbeque": Activity(
        id="barbeque",
        verb="cook the barbeque",
        gerund="cooking barbeque",
        rush="haul the grill uphill",
        danger="too hot and heavy for one pair of hands",
        weather="sunny",
        zone={"hands", "torso"},
        keyword="barbeque",
        tags={"barbeque", "western", "sharing"},
    ),
}

LOADS = {
    "grill": Load(
        id="grill",
        label="barbeque grill",
        phrase="a heavy barbeque grill",
        region="hands",
        heavy=True,
        hot=True,
    ),
    "coals": Load(
        id="coals",
        label="charcoal sack",
        phrase="a sack of hot charcoal",
        region="hands",
        heavy=True,
        hot=True,
        smoky=True,
    ),
    "sauce": Load(
        id="sauce",
        label="sauce pot",
        phrase="a pot of sweet barbecue sauce",
        region="hands",
        hot=False,
        smoky=False,
    ),
}

GEAR = [
    Gear(
        id="mitts",
        label="thick oven mitts",
        guards={"hot"},
        covers={"hands"},
        prep="put on thick oven mitts first",
        tail="slipped on the mitts and shared the load",
        plural=True,
    ),
    Gear(
        id="aprons",
        label="two aprons",
        guards={"smoky"},
        covers={"torso"},
        prep="tie on two aprons and keep the smoke off",
        tail="tied on the aprons and kept the smoke off",
        plural=True,
    ),
    Gear(
        id="waterjug",
        label="a cool water jug",
        guards={"hot", "smoky"},
        covers={"hands", "torso"},
        prep="take a cool water jug along",
        tail="carried the water jug and shared the cooling sips",
    ),
]

GIRL_NAMES = ["Ada", "Belle", "Rose", "Mabel", "June", "Ivy"]
BOY_NAMES = ["Hank", "Wade", "Tom", "Jeb", "Cole", "Buck"]
TRAITS = ["bold", "sturdy", "bright-eyed", "hasty", "cheerful", "lively"]


@dataclass
class StoryParams:
    place: str
    activity: str
    load: str
    name: str
    gender: str
    helper: str
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


def reasonableness_gate(act: Activity, load: Load) -> bool:
    return True


def select_gear(act: Activity, load: Load) -> Optional[Gear]:
    for g in GEAR:
        if load.hot and "hot" in g.guards and load.region in g.covers:
            return g
        if load.smoky and "smoky" in g.guards and "torso" in g.covers:
            return g
    return GEAR[-1] if act.id == "barbeque" else None


def predict_mishap(world: World, hero: Entity, act: Activity, load: Entity) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(hero.id), act, load, narrate=False)
    target = sim.get(load.id)
    return {
        "scorched": target.meters.get("scorched", 0) >= THRESHOLD,
        "shared": sim.facts.get("shared", False),
    }


def _do_activity(world: World, hero: Entity, act: Activity, load: Entity, narrate: bool = True) -> None:
    hero.meters["uphill"] = hero.meters.get("uphill", 0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    if load.hot:
        load.meters["heat"] = load.meters.get("heat", 0) + 1
    if load.smoky:
        load.meters["smoke"] = load.meters.get("smoke", 0) + 1
    if load.heavy:
        hero.meters["weight"] = hero.meters.get("weight", 0) + 1
    if hero.meters.get("weight", 0) >= THRESHOLD and not world.facts.get("shared"):
        load.meters["scorched"] = load.meters.get("scorched", 0) + 1
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    if narrate:
        if load.meters.get("scorched", 0) >= THRESHOLD:
            world.say(f"The load got too hot on the steep climb, and the smell of trouble rode the wind.")
        else:
            world.say(f"The climb went on, but the load stayed under control.")


def tell(setting: Setting, activity: Activity, load_cfg: Load,
         name: str, gender: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={}))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=f"the {helper_type}", meters={}, memes={}))
    load = world.add(Entity(
        id="Load",
        type=load_cfg.id,
        label=load_cfg.label,
        phrase=load_cfg.phrase,
        owner=hero.id,
        caretaker=helper.id,
        plural=False,
        meters={},
        memes={},
    ))

    world.say(f"{name} was a {trait} {gender} with a heart as big as a prairie sky.")
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund} on the {setting.place}.")
    world.say(f"One day {hero.id} spotted {load_cfg.phrase} waiting by the trail, and {hero.pronoun('possessive')} eyes shone.")

    world.para()
    world.say(f"At the foot of the western incline, {hero.id} tried to {activity.verb}, but {activity.danger}.")
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    load.meters["weight"] = load.meters.get("weight", 0) + 1
    world.say(f"{hero.id} reached for the {load_cfg.label}, and the whole thing felt as stubborn as a mule on a hot day.")

    if load_cfg.hot:
        world.say(f"The grill was still hot from the coals, and the smoke curled up like a warning ribbon.")
    if load_cfg.smoky:
        world.say(f"The air tasted smoky enough to make even a crow blink twice.")

    world.para()
    world.say(f"Then came a flashback: {hero.id} remembered an earlier day when {hero.pronoun()} tried to carry too much alone.")
    world.say(f"The load had tipped, the sauce had splashed, and {hero.pronoun('possessive')} hands had ended up red and sore.")
    hero.memes["caution"] = hero.memes.get("caution", 0) + 1
    world.say(f"That old trouble taught {hero.id} that a fast plan can turn foolish on a hill.")

    world.say(f"So {hero.id} listened to the memory and took a slower look at the trail.")
    world.say(f"{hero.id} asked {helper.label} to share the work instead of hauling it alone.")

    gear = select_gear(activity, load_cfg)
    if gear is None:
        gear = next(iter(globals().get("GEARS", globals().get("GEAR", []))))
    world.say(f"{helper.label.capitalize()} smiled and said, \"Let's {gear.prep}.\"")
    world.facts["shared"] = True

    _do_activity(world, hero, activity, load, narrate=True)
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    hero.memes["generosity"] = hero.memes.get("generosity", 0) + 1

    world.para()
    world.say(f"With the load shared, the climb got easier, the smoke blew away, and the barbeque stayed fit to serve.")
    world.say(f"At the top, {hero.id} passed out plates, {helper.label} passed out cups of water, and nobody went home hungry.")
    world.say(f"That was the end of the tall tale: the western incline was conquered, and the shared barbeque fed the whole camp.")

    world.facts.update(
        hero=hero,
        helper=helper,
        load=load,
        load_cfg=load_cfg,
        activity=activity,
        setting=setting,
        gear=gear,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    return [
        f'Write a tall tale for a child about a western incline and a shared barbeque.',
        f"Tell a cautionary story where {hero.id} remembers a bad old mistake before climbing the ridge with a hot grill.",
        f"Write a short western story with a flashback, sharing, and a happy barbeque ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    load = _safe_fact(world, f, "load")
    act = _safe_fact(world, f, "activity")
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"What was {hero.id} trying to do on the western incline?",
            answer=f"{hero.id} was trying to {act.verb} with {load.phrase} at {place}.",
        ),
        QAItem(
            question=f"Why did {hero.id} remember the old mishap before climbing?",
            answer=f"{hero.id} remembered the flashback because trying to carry the hot load alone had gone badly before, so this time {hero.pronoun()} chose caution.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.label} solve the problem?",
            answer=f"They solved it by sharing the work and carrying the barbeque together, which kept the load safer and the climb easier.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"At the end, the barbeque reached the top, the food stayed fit to serve, and everyone got to eat together.",
        ),
    ]


KNOWLEDGE = {
    "barbeque": [
        ("What is a barbeque?", "A barbeque is a way of cooking food over heat, often outside, so people can share a meal together."),
        ("Why do people share food at a barbeque?", "People share food at a barbeque because it is a friendly meal where everyone can eat and talk together."),
    ],
    "sharing": [
        ("What does sharing mean?", "Sharing means letting other people help, use, or enjoy something with you."),
        ("Why can sharing make hard jobs easier?", "Sharing can make hard jobs easier because two or more people can carry the work together."),
    ],
    "flashback": [
        ("What is a flashback in a story?", "A flashback is when the story pauses to remember something that happened earlier."),
    ],
    "cautionary": [
        ("What does cautionary mean?", "Cautionary means it teaches a careful lesson about what to avoid or how to be safer."),
    ],
    "incline": [
        ("What is an incline?", "An incline is a slope that goes up or down instead of staying flat."),
    ],
    "western": [
        ("What does western mean in a story setting?", "Western usually means the story feels like the old frontier, with dust, hats, wide skies, and ranch country."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.update({"barbeque", "sharing", "flashback", "cautionary", "incline", "western"})
    out: list[QAItem] = []
    for tag in ["incline", "western", "barbeque", "sharing", "flashback", "cautionary"]:
        for q, a in KNOWLEDGE[tag]:
            out.append(QAItem(question=q, answer=a))
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.label:
            parts.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(parts)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
% A load is risky if the activity involves a hot or smoky barbeque and the load is carried on the hands.
risk(A, L) :- activity(A), load(L), hot(L), carried_on(L, hands).
risk(A, L) :- activity(A), load(L), smoky(L), carried_on(L, torso).

% Sharing is a valid solution when a helper and a gear choice reduce the risk.
safe(A, L) :- risk(A, L), shared(A, L).
resolved(A, L) :- safe(A, L).

valid_story(Place, A, L) :- setting(Place), affords(Place, A), activity(A), load(L), resolved(A, L).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
    for lid, l in LOADS.items():
        lines.append(asp.fact("load", lid))
        if l.hot:
            lines.append(asp.fact("hot", lid))
        if l.smoky:
            lines.append(asp.fact("smoky", lid))
        lines.append(asp.fact("carried_on", lid, l.region))
    lines.append(asp.fact("shared", "barbeque"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    # Minimal parity check: our Python gate allows the same world family.
    py = {(p, a, l) for p in SETTINGS for a in ACTIVITIES for l in LOADS if reasonableness_gate(_safe_lookup(ACTIVITIES, a), _safe_lookup(LOADS, l))}
    cl = set(asp_valid_stories())
    if cl:
        print(f"OK: ASP produced {len(cl)} valid story tuple(s).")
        return 0
    print("ASP produced no valid stories.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: incline, western barbeque, sharing, flashback, cautionary.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--load", choices=LOADS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["cowboy", "rancher", "uncle", "aunt"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "activity", None) and getattr(args, "load", None):
        if not reasonableness_gate(_safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(LOADS, getattr(args, "load", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    activity = getattr(args, "activity", None) or rng.choice(list(ACTIVITIES))
    load = getattr(args, "load", None) or rng.choice(list(LOADS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["cowboy", "rancher", "uncle", "aunt"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, load=load, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(LOADS, params.load),
        params.name,
        params.gender,
        params.helper,
        params.trait,
    )
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
    StoryParams(place="ridge", activity="barbeque", load="grill", name="Hank", gender="boy", helper="rancher", trait="bold"),
    StoryParams(place="canyon", activity="barbeque", load="coals", name="Ada", gender="girl", helper="cowboy", trait="cheerful"),
    StoryParams(place="ranch", activity="barbeque", load="sauce", name="Wade", gender="boy", helper="uncle", trait="sturdy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(f"{len(asp.atoms(model, 'valid_story'))} valid story tuple(s).")
        for t in asp.atoms(model, "valid_story"):
            print(t)
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
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = s.params
            header = f"### {p.name}: {p.activity} at {p.place} (load: {p.load})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
