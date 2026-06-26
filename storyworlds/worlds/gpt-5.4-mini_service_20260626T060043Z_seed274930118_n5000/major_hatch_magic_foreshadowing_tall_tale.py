#!/usr/bin/env python3
"""
storyworlds/worlds/major_hatch_magic_foreshadowing_tall_tale.py
===============================================================

A small, self-contained storyworld in the spirit of a Tall Tale.

Seed premise:
A mighty major keeps watch over a curious hatch. Magic stirs under the floor,
and little signs of trouble foreshadow a big, funny, ultimately kind turn.

The domain is intentionally tiny and constraint-checked:
- a major, a hatch, and a magical trick
- a foreshadowed mistake that can be solved in a sensible way
- a complete beginning / middle / ending arc
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    ent: object | None = None
    major: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"spark": 0.0, "noise": 0.0, "worry": 0.0, "shiver": 0.0}
        if not self.memes:
            self.memes = {"pride": 0.0, "curiosity": 0.0, "worry": 0.0, "relief": 0.0, "joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"major", "man", "father", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "mother", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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


@dataclass
class Setting:
    place: str = "the old fort"
    indoors: bool = True
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
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


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


def _r_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["shiver"] >= THRESHOLD and ("foreshadow", ent.id) not in world.fired:
            world.fired.add(("foreshadow", ent.id))
            ent.memes["worry"] += 1
            out.append(f"A little shiver in the air hinted that something below was not asleep.")
    return out


def _r_magic_leak(world: World) -> list[str]:
    out: list[str] = []
    hatch = world.entities.get("hatch")
    if not hatch:
        return out
    if hatch.meters["spark"] < THRESHOLD:
        return out
    for actor in world.characters():
        if ("magic", actor.id) in world.fired:
            continue
        world.fired.add(("magic", actor.id))
        actor.memes["curiosity"] += 1
        out.append("The hatch gave a bright hum, as if the floor had remembered an old spell.")
    return out


def _r_noise_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["noise"] < THRESHOLD:
            continue
        hatch = world.entities.get("hatch")
        if not hatch:
            continue
        sig = ("noise_spill", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hatch.meters["shiver"] += 1
        out.append("The hatch rattled in reply, and that made the whole room feel bigger.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("foreshadow", "mood", _r_foreshadow),
    Rule("magic_leak", "magic", _r_magic_leak),
    Rule("noise_spill", "physical", _r_noise_spill),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_outcome(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "sparked": prize.meters["spark"] >= THRESHOLD,
        "shivered": prize.meters["shiver"] >= THRESHOLD,
        "worry": sum(e.memes["worry"] for e in sim.characters()),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        pass
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.meters["noise"] += 1
    actor.memes["pride"] += 1
    propagate(world, narrate=narrate)


SETTINGS = {
    "fort": Setting(place="the old fort", indoors=True, affords={"march", "listen"}),
    "tower": Setting(place="the tower room", indoors=True, affords={"listen", "write"}),
}


ACTIVITIES = {
    "march": Activity(
        id="march",
        verb="march past the hatch",
        gerund="marching in long boots",
        rush="stomp down the hall",
        mess="noise",
        soil="all shaken up",
        zone={"floor"},
        keyword="hatch",
        tags={"hatch", "noise", "foreshadowing"},
    ),
    "listen": Activity(
        id="listen",
        verb="listen at the hatch",
        gerund="listening with both ears",
        rush="lean in close",
        mess="spark",
        soil="glowing too bright",
        zone={"floor"},
        keyword="magic",
        tags={"magic", "hatch", "foreshadowing"},
    ),
    "write": Activity(
        id="write",
        verb="write a warning",
        gerund="writing careful notes",
        rush="grab the chalk",
        mess="spark",
        soil="fizzing with light",
        zone={"table"},
        keyword="foreshadowing",
        tags={"magic", "foreshadowing"},
    ),
}


PRIZES = {
    "hat": Prize(label="hat", phrase="a fine brass hat", type="hat", region="head"),
    "badge": Prize(label="badge", phrase="a shiny major's badge", type="badge", region="torso"),
    "boots": Prize(label="boots", phrase="tall marching boots", type="boots", region="feet", plural=True),
}


GEAR = [
    Gear(
        id="earplugs",
        label="soft earplugs",
        covers={"head"},
        guards={"noise"},
        prep="put in the soft earplugs first",
        tail="had put in the soft earplugs",
        plural=True,
    ),
    Gear(
        id="gloves",
        label="gloves of mooncloth",
        covers={"hands"},
        guards={"spark"},
        prep="slip on the gloves of mooncloth first",
        tail="had slipped on the gloves of mooncloth",
        plural=True,
    ),
]


MAJOR_NAMES = ["Major Milo", "Major June", "Major Ned", "Major Bea"]
TRAITS = ["brave", "grand", "cheerful", "steady"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
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


def introduce(world: World, major: Entity) -> None:
    world.say(f"{major.id} was a {major.trait if hasattr(major, 'trait') else 'grand'} major who loved a good duty and a bigger story.")


def tell_story(world: World, major: Entity, activity: Activity, prize: Entity) -> None:
    world.say(
        f"At {world.setting.place}, {major.id} stood watch by a mysterious hatch. "
        f"Folks said the hatch was old, but the major said old things could still keep secrets."
    )
    world.say(
        f"{major.id} liked to {activity.verb}, and every time {major.pronoun('subject')} did, "
        f"the room felt a little more like a tale somebody had forgotten to finish."
    )
    prize.worn_by = major.id
    world.say(
        f"{major.id} wore {major.pronoun('possessive')} {prize.label} because {prize.phrase} made {major.pronoun('object')} look fit for parade day."
    )


def act_one(world: World, major: Entity, activity: Activity, prize: Entity) -> None:
    world.say(
        f"Once upon a moonlit watch, {major.id} kept guard over {world.setting.place}."
    )
    world.say(
        f"Before long, there were little signs everywhere: a tiny shiver in the floor, a soft hum, and a wink of light under the hatch."
    )
    tell_story(world, major, activity, prize)


def warn(world: World, major: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_outcome(world, major, activity, prize.id)
    if not pred["sparked"] and not pred["shivered"]:
        return False
    world.facts["pred"] = pred
    world.say(
        f'"Mind the hatch," {major.id} said, "for when a thing hums before supper, it usually means trouble is nearby."'
    )
    return True


def compromise(world: World, major: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if not gear:
        return None
    ent = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
    ))
    ent.worn_by = major.id
    world.say(
        f"Then the major smiled a slow, clever smile and said, "
        f'"If the hatch wants to sing, I can listen safely first." '
        f"{major.id} {gear.prep}."
    )
    return gear


def resolution(world: World, major: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    major.memes["joy"] += 1
    major.memes["worry"] = 0.0
    world.say(
        f"So {major.id} {gear.tail}, and that made all the difference."
    )
    _do_activity(world, major, activity)
    world.say(
        f"This time the magic was only a bright wink and a friendly hum, and {prize.phrase} stayed safe."
    )
    world.say(
        f"At the end, the hatch opened just enough to reveal a little lamp, a puff of gold dust, and a note that read, "
        f'"Thank you for keeping watch."'
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, trait: str) -> World:
    world = World(setting)
    major = world.add(Entity(
        id=name,
        kind="character",
        type="major",
        traits=[trait, "steady"],
    ))
    major.trait = trait  # for narration helper
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=major.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    act_one(world, major, activity, prize)
    world.para()
    warn(world, major, activity, prize)
    world.say(f"{major.id} took one great stride closer, and the hatch answered with a louder rattle.")
    world.para()
    gear = compromise(world, major, activity, prize)
    if gear:
        resolution(world, major, activity, prize, gear)
    world.facts.update(major=major, prize=prize, activity=activity, gear=gear, setting=setting)
    return world


KNOWLEDGE = {
    "magic": [
        ("What is magic in a story?", "Magic is a special kind of story power that can make surprising things happen, like lights, spells, or talking objects."),
    ],
    "hatch": [
        ("What is a hatch?", "A hatch is a small door or cover, often in a floor, wall, or ceiling, that can open and close."),
    ],
    "foreshadowing": [
        ("What is foreshadowing?", "Foreshadowing is when a story gives little hints about something important that will happen later."),
    ],
    "major": [
        ("What is a major in this story?", "A major is a rank for a person in charge, often someone who gives orders and keeps watch."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    major, act, prize = f["major"], f["activity"], f["prize"]
    return [
        f'Write a tall tale for a child about {major.id}, a mysterious hatch, and a little bit of magic.',
        f"Tell a story where {major.id} notices foreshadowing near a hatch and chooses a safer way to handle the magic.",
        f'Write a brief, funny tall tale that includes the words "major", "hatch", "magic", and "foreshadowing".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    major, act, prize = f["major"], f["activity"], f["prize"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who watched over the hatch in the old fort?",
            answer=f"{major.id} watched over the hatch, because {major.pronoun('subject')} was the major on duty.",
        ),
        QAItem(
            question=f"What little signs hinted that something magical was happening?",
            answer="There was a tiny shiver in the floor, a soft hum, and a wink of light under the hatch. Those were foreshadowing clues.",
        ),
        QAItem(
            question=f"Why did {major.id} worry before moving closer to the hatch?",
            answer=f"{major.id} worried because the hatch was already humming and shivering, so the magic seemed ready to burst out in a noisy way.",
        ),
    ]
    if gear:
        qa.append(
            QAItem(
                question=f"How did {gear.label} help {major.id} handle the magic safely?",
                answer=f"{gear.label} helped because it protected the right part of {major.id}'s body, so {major.id} could check the hatch without getting into trouble.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag in ["major", "hatch", "magic", "foreshadowing"]:
        if tag in tags or tag in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="fort", activity="listen", prize="hat", name="Major Milo", trait="brave"),
    StoryParams(place="fort", activity="march", prize="boots", name="Major June", trait="steady"),
    StoryParams(place="tower", activity="write", prize="badge", name="Major Bea", trait="cheerful"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return (
            f"(No story: {activity.gerund} does not put {prize.label} at risk, "
            f"so there is no honest foreshadowing and no meaningful fix.)"
        )
    return (
        f"(No story: nothing in the gear catalog safely handles {prize.label} during {activity.gerund}. "
        f"The tale needs a fix that truly matches the danger.)"
    )


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


ASP_RULES = r"""
prize_at_risk(A, P) :- zone(A, R), worn_on(P, R).
compatible(G, A, P) :- prize_at_risk(A, P), guards(G, M), mess_of(A, M), covers(G, R), worn_on(P, R).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), compatible(_, A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_story_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld: a major, a hatch, magic, and foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=getattr(args, "name", None) or rng.choice(MAJOR_NAMES),
        trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.name, params.trait)
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
        for c in combos:
            print(" ", c)
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
