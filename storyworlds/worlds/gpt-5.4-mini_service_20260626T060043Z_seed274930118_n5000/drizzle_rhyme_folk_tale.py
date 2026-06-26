#!/usr/bin/env python3
"""
storyworlds/worlds/drizzle_rhyme_folk_tale.py
==============================================

A small folk-tale story world about a village child, a drizzle, and a rhyming
way to keep a promise. The premise is built as a simulation: the weather shifts,
a task gets harder, a helper offers a clever rhyme, and the ending proves what
changed in the world.

The seed word is "drizzle". The stylistic instrument is rhyme, and the prose
leans folk-tale: simple, rhythmic, concrete, and gentle.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    owns: list[str] = field(default_factory=list)

    charm: object | None = None
    helper: object | None = None
    hero: object | None = None
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
class Place:
    name: str
    indoors: bool = False
    drip_sounds: list[str] = field(default_factory=list)
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
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
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
class Charm:
    id: str
    label: str
    helps: set[str]
    covers: set[str]
    rhyme: str
    action: str
    ending: str
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


@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    charm: str
    name: str
    gender: str
    helper: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.weather: str = ""
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.weather = self.weather
        clone.facts = dict(self.facts)
        return clone


def _r_drizzle_soak(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.kind != "character":
            continue
        if e.meters.get("drizzle", 0.0) < THRESHOLD:
            continue
        for item_id in e.owns:
            item = world.get(item_id)
            if item.meters.get("dry", 1.0) < THRESHOLD:
                continue
            sig = ("soak", e.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] = item.meters.get("wet", 0.0) + 1
            item.meters["messy"] = item.meters.get("messy", 0.0) + 1
            out.append(f"The drizzle kissed {e.pronoun('possessive')} {item.label} and made it damp.")
    return out


def _r_charm_help(world: World) -> list[str]:
    out: list[str] = []
    helper = world.facts.get("helper")
    charm = world.facts.get("charm")
    if not helper or not charm:
        return out
    h = world.get(helper.id)
    if h.memes.get("hope", 0.0) < THRESHOLD:
        return out
    sig = ("help", helper.id, charm.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if charm.id == "raincloak":
        target = world.get(world.facts["prize"].id)
        target.meters["dry"] = target.meters.get("dry", 1.0) + 1
        out.append("The raincloak stood like a leaf-green roof, and the child stayed dry beneath it.")
    elif charm.id == "wooden_umbrella":
        target = world.get(world.facts["prize"].id)
        target.meters["dry"] = target.meters.get("dry", 1.0) + 1
        out.append("The wooden umbrella held the drizzle away, round as a moon above the path.")
    return out


CAUSAL_RULES = [_r_drizzle_soak, _r_charm_help]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            res = rule(world)
            if res:
                changed = True
                for s in res:
                    world.say(s)


def rhyme_line(charm: Charm, task: Task) -> str:
    return f"“{charm.rhyme},” said the helper, “and {task.action} will follow the spinner.”"


def tell(place: Place, task: Task, prize_cfg: Prize, charm_cfg: Charm, name: str, gender: str, helper_name: str) -> World:
    world = World(place)
    world.weather = task.weather

    hero = world.add(Entity(id=name, kind="character", type=gender, memes={"hope": 0.0, "worry": 0.0}))
    helper = world.add(Entity(id=helper_name, kind="character", type="elder", memes={"wisdom": 1.0, "hope": 1.0}))
    prize = world.add(Entity(id=prize_cfg.id, kind="thing", type=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase))
    charm = world.add(Entity(id=charm_cfg.id, kind="thing", type="charm", label=charm_cfg.label, phrase=charm_cfg.rhyme, plural=charm_cfg.plural))

    hero.owns.append(prize.id)
    hero.meters["drizzle"] = 0.0
    prize.meters["dry"] = 1.0
    charm.meters["ready"] = 1.0
    world.facts.update(hero=hero, helper=helper, prize=prize, charm=charm, task=task, place=place)

    world.say(f"In {place.name}, {hero.id} was a small {gender} with a bright wish and a steady heart.")
    world.say(f"{hero.pronoun().capitalize()} loved to {task.gerund}, and {place.name} seemed made for little footsteps.")
    world.say(f"One day {hero.id} carried {hero.pronoun('possessive')} {prize.label}, {prize.phrase}, as proud as a cat with a bell.")

    world.para()
    world.say(f"Then came a drizzle, soft as lace and quick as a mouse.")
    world.say(f"{hero.id} wanted to {task.verb}, but the path turned slick and the sky kept weeping.")
    hero.meters["drizzle"] = 1.0
    hero.memes["worry"] = 1.0
    propagate(world)
    world.say(f"{hero.id} frowned, for the drizzle could make {hero.pronoun('possessive')} {prize.label} {task.risk}.")

    world.para()
    helper.memes["hope"] = 1.0
    world.say(f"By the gate stood {helper.id}, the village helper, with a kind eye and a pocket full of rhyme.")
    world.say(rhyme_line(charm_cfg, task))
    world.say(f"“Then let us {charm_cfg.action},” said {helper.id}, “and keep your {prize.label} safe from the blue-bell rain.”")
    if charm_cfg.id in {"raincloak", "wooden_umbrella"}:
        charm.meters["ready"] = 1.0
    propagate(world)

    world.para()
    world.say(f"{hero.id} smiled and trusted the plan.")
    world.say(f"Together they {task.verb} as the drizzle danced on leaves and shingles.")
    if prize.meters.get("dry", 0.0) >= THRESHOLD:
        world.say(f"In the end, {hero.id}'s {prize.label} stayed dry, and the little road sparkled like silver thread.")
    else:
        world.say(f"In the end, the {prize.label} still felt damp, and the helper had to think again.")

    world.facts["resolved"] = prize.meters.get("dry", 0.0) >= THRESHOLD
    return world


SETTINGS = {
    "village_lane": Place(name="the village lane", indoors=False, drip_sounds=["tap", "tink", "drip"]),
    "mill_path": Place(name="the mill path", indoors=False, drip_sounds=["drip", "tap"]),
    "cottage_yard": Place(name="the cottage yard", indoors=False, drip_sounds=["plip", "plop"]),
    "hearth_room": Place(name="the hearth room", indoors=True, drip_sounds=["tick"]),
}

TASKS = {
    "berry_pick": Task(
        id="berry_pick",
        verb="pick berries",
        gerund="picking berries",
        rush="run for the berry bush",
        risk="stain it purple",
        weather="drizzle",
        tags={"berry", "fruit", "drizzle"},
    ),
    "deliver_bread": Task(
        id="deliver_bread",
        verb="deliver bread",
        gerund="delivering bread",
        rush="hurry to the baker",
        risk="make it soggy",
        weather="drizzle",
        tags={"bread", "weather", "drizzle"},
    ),
    "gather_sticks": Task(
        id="gather_sticks",
        verb="gather sticks",
        gerund="gathering sticks",
        rush="dash to the hedge",
        risk="muddy it",
        weather="drizzle",
        tags={"wood", "drizzle"},
    ),
}

PRIZES = {
    "apron": Prize(id="apron", label="apron", phrase="a neat little apron", region="torso"),
    "basket": Prize(id="basket", label="basket", phrase="a willow basket", region="hands"),
    "cloak": Prize(id="cloak", label="cloak", phrase="a wool cloak", region="torso"),
}

CHARMS = {
    "raincloak": Charm(
        id="raincloak",
        label="raincloak",
        helps={"drizzle"},
        covers={"torso"},
        rhyme="Drip-drop, skip-stop, under cloth and leaf, the drizzle loses mischief and the day keeps its chief",
        action="wear the raincloak",
        ending="walked on beneath the raincloak",
    ),
    "wooden_umbrella": Charm(
        id="wooden_umbrella",
        label="wooden umbrella",
        helps={"drizzle"},
        covers={"head", "torso"},
        rhyme="Tip-tap, flap-snap, hold the willow high; the drizzle drifts away like a bird across the sky",
        action="raise the wooden umbrella",
        ending="tripped along beneath the wooden umbrella",
    ),
}

GENDER_NAMES = {
    "girl": ["Mara", "Nina", "Elsa", "Bria", "Tess"],
    "boy": ["Finn", "Oren", "Pavel", "Tomas", "Wren"],
}

HELPERS = ["Old Nan", "Grandpa Holt", "Aunt Miri", "Bram the Miller", "Silk-Shoe Jo"]

TRAITS = ["quick", "curious", "gentle", "brave", "merry"]


@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    charm: str
    name: str
    gender: str
    helper: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place_id, place in SETTINGS.items():
        for task_id, task in TASKS.items():
            if task.weather != "drizzle":
                continue
            for prize_id, prize in PRIZES.items():
                if prize.region != "torso":
                    continue
                for charm_id, charm in CHARMS.items():
                    if "drizzle" in charm.helps and prize.region in charm.covers:
                        combos.append((place_id, task_id, prize_id, charm_id))
    return combos


def explain_rejection(task: Task, prize: Prize, charm: Charm) -> str:
    return f"(No story: {charm.label} does not meaningfully protect a {prize.label} during {task.gerund}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale drizzle story world with rhyme and a small clever fix.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    if getattr(args, "task", None) and getattr(args, "prize", None) and getattr(args, "charm", None):
        if not (getattr(args, "task", None) in TASKS and getattr(args, "prize", None) in PRIZES and getattr(args, "charm", None) in CHARMS):
            return _fallback_storyparams(args, rng, StoryParams, globals())
        task, prize, charm = _safe_lookup(TASKS, getattr(args, "task", None)), _safe_lookup(PRIZES, getattr(args, "prize", None)), _safe_lookup(CHARMS, getattr(args, "charm", None))
        if prize.region not in charm.covers:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
              and (getattr(args, "charm", None) is None or c[3] == getattr(args, "charm", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, prize, charm = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(GENDER_NAMES, gender))
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    return StoryParams(place=place, task=task, prize=prize, charm=charm, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TASKS, params.task), _safe_lookup(PRIZES, params.prize), _safe_lookup(CHARMS, params.charm), params.name, params.gender, params.helper)
    prompts = [
        f"Write a short folk tale about drizzle, rhyme, and a child named {params.name}.",
        f"Tell a gentle story in rhyme where {params.name} wants to {_safe_lookup(TASKS, params.task).verb} but must keep a {_safe_lookup(PRIZES, params.prize).label} safe.",
        f"Write a village story that begins with drizzle and ends with a clever helper's rhyme.",
    ]
    story_qa = [
        QAItem(
            question=f"Why did {params.name} need help when the drizzle began?",
            answer=f"{params.name} needed help because the drizzle could make the {_safe_lookup(PRIZES, params.prize).label} {_safe_lookup(TASKS, params.task).risk}, so the path became tricky.",
        ),
        QAItem(
            question=f"What did the helper say that made the story feel like a rhyme?",
            answer=f"The helper spoke in a rhyme about the {_safe_lookup(CHARMS, params.charm).label} and how it could keep the day bright and safe.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {params.name} could {_safe_lookup(TASKS, params.task).verb} with the helper, and the {_safe_lookup(PRIZES, params.prize).label} stayed dry.",
        ),
    ]
    world_qa = [
        QAItem(question="What is drizzle?", answer="Drizzle is a very light rain, with small drops that fall softly from the sky."),
        QAItem(question="Why do people use a cloak in wet weather?", answer="A cloak can cover the body and help keep clothes dry when the weather is damp."),
        QAItem(question="Why is rhyme often used in folk tales?", answer="Rhyme helps a story sound musical and memorable, like an old song told by the fire."),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.owns:
            bits.append(f"owns={e.owns}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/4.

valid(Place,Task,Prize,Charm) :-
    place(Place), task(Task), prize(Prize), charm(Charm),
    task_weather(Task, drizzle),
    prize_region(Prize, torso),
    charm_helps(Charm, drizzle),
    charm_covers(Charm, torso),
    place_supports(Place, Task).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("task_weather", tid, t.weather))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        for h in sorted(c.helps):
            lines.append(asp.fact("charm_helps", cid, h))
        for cov in sorted(c.covers):
            lines.append(asp.fact("charm_covers", cid, cov))
    for pid, place in SETTINGS.items():
        for tid in TASKS:
            lines.append(asp.fact("place_supports", pid, tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def select_params_list() -> list[StoryParams]:
    out = []
    for i, combo in enumerate(valid_combos()):
        place, task, prize, charm = combo
        out.append(StoryParams(place=place, task=task, prize=prize, charm=charm, name=GENDER_NAMES["girl"][i % 5], gender="girl", helper=_safe_lookup(HELPERS, i % len(HELPERS))))
    return out


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in select_params_list()]
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
            header = f"### {p.name}: {p.task} at {p.place} (prize: {p.prize}, charm: {p.charm})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
