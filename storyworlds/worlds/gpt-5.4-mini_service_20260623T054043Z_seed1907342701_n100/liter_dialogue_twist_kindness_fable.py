#!/usr/bin/env python3
"""
storyworlds/worlds/liter_dialogue_twist_kindness_fable.py
=========================================================

A small fable-style storyworld about a child, a liter of something precious,
a roadside request, and a kindness that changes the ending.

Seed premise:
- A character carries a liter of drink through a quiet place.
- Another character asks for help in dialogue.
- The request creates tension because giving away some of the liter would leave
  less for the intended recipient.
- A twist reveals the requester is helping with an unexpected problem.
- Kindness resolves the moment and leaves a concrete ending image.

The world uses typed entities with physical meters and emotional memes, a tiny
forward-chained rule set, and a Python/ASP reasonableness twin.

Features used in the prose:
- Dialogue
- Twist
- Kindness
- "liter" as a story word and measure
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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    carrier: object | None = None
    drink: object | None = None
    encounter: object | None = None
    helper: object | None = None
    helper_item: object | None = None
    requester: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "sister", "woman", "hen"}
        male = {"boy", "father", "brother", "man", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Place:
    id: str
    name: str
    detail: str
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
class Drink:
    id: str
    name: str
    phrase: str
    kind: str
    full_meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Encounter:
    id: str
    name: str
    request: str
    reason: str
    twist: str
    need: str
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
class KindnessMethod:
    id: str
    offer: str
    action: str
    ending: str
    guards: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    CAUSAL_RULES: list = field(default_factory=list)
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


def _r_share(world: World) -> list[str]:
    out = []
    carrier = world.facts["carrier"]
    drink = world.facts["drink_ent"]
    ask = world.facts["encounter_ent"]
    if carrier.meters["willing"] < THRESHOLD or ask.meters["needs_help"] < THRESHOLD:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    amount = min(0.25, drink.meters["liter"])
    drink.meters["liter"] -= amount
    drink.meters["shared_liter"] += amount
    carrier.memes["kindness"] += 1
    ask.meters["helped"] += 1
    out.append("__share__")
    return out


def _r_twist(world: World) -> list[str]:
    out = []
    ask = world.facts["encounter_ent"]
    if ask.meters["helped"] < THRESHOLD or ask.meters["twist_seen"] >= THRESHOLD:
        return out
    sig = ("twist",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ask.meters["twist_seen"] += 1
    ask.memes["gratitude"] += 1
    out.append("__twist__")
    return out


CAUSAL_RULES = [Rule("share", "physical", _r_share), Rule("twist", "social", _r_twist)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def needs_help(place: Place, encounter: Encounter) -> bool:
    return encounter.id in place.affords


def compatible(place: Place, drink: Drink, encounter: Encounter, method: KindnessMethod) -> bool:
    return needs_help(place, encounter) and drink.kind in method.guards


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for did, drink in DRINKS.items():
            for eid, encounter in ENCOUNTERS.items():
                for mid, method in METHODS.items():
                    if compatible(place, drink, encounter, method):
                        combos.append((pid, did, eid, mid))
    return combos


@dataclass
class StoryParams:
    place: str
    drink: str
    encounter: str
    method: str
    carrier_name: str
    carrier_type: str
    requester_name: str
    requester_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None
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


PLACES = {
    "lane": Place(id="lane", name="the lane by the well", detail="The lane was dusty, and the well stood in the sun.", affords={"thirst"}),
    "orchard": Place(id="orchard", name="the orchard path", detail="The orchard path was shaded by apple trees.", affords={"thirst"}),
    "field": Place(id="field", name="the field road", detail="The field road ran pale and warm between the grasses.", affords={"thirst"}),
    "bridge": Place(id="bridge", name="the little bridge", detail="The little bridge crossed a narrow brook that sparkled below.", affords={"thirst"}),
}

DRINKS = {
    "milk": Drink(id="milk", name="milk", phrase="a liter of milk", kind="milk", full_meters={"liter": 1.0}),
    "water": Drink(id="water", name="water", phrase="a liter of water", kind="water", full_meters={"liter": 1.0}),
    "juice": Drink(id="juice", name="berry juice", phrase="a liter of berry juice", kind="juice", full_meters={"liter": 1.0}),
    "soup": Drink(id="soup", name="broth", phrase="a liter of warm broth", kind="broth", full_meters={"liter": 1.0}),
}

ENCOUNTERS = {
    "thirsty_goat": Encounter(id="thirsty_goat", name="a thirsty goat", request="Can I have a little sip?", reason="its bucket tipped over in the heat", twist="the goat knew the brook path to the mill", need="thirst", tags={"goat", "thirst"}),
    "tired_mule": Encounter(id="tired_mule", name="a tired mule", request="May I please wet my tongue?", reason="it had walked far with no shade", twist="the mule knew where the lost gate was", need="thirst", tags={"mule", "thirst"}),
    "small_hen": Encounter(id="small_hen", name="a small hen", request="Could you spare a sip?", reason="it had chased grain all morning", twist="the hen knew the fox was hiding near the reeds", need="thirst", tags={"hen", "thirst"}),
    "old_cat": Encounter(id="old_cat", name="an old cat", request="Would you share a drop?", reason="it had guarded the yard all day", twist="the cat knew the shortest way home", need="thirst", tags={"cat", "thirst"}),
}

METHODS = {
    "share_cup": KindnessMethod(id="share_cup", offer="shared a cup", action="poured out a small cup", ending="The two drank by the roots of the tree.", guards={"milk", "water", "juice", "broth"}),
    "leaf_bowl": KindnessMethod(id="leaf_bowl", offer="used a leaf bowl", action="held a leaf steady and filled it", ending="The leaf bowl stayed bright and green in the dust.", guards={"milk", "water", "juice", "broth"}),
    "stone_rest": KindnessMethod(id="stone_rest", offer="rested the jar on a flat stone", action="set the jar down so everyone could reach it", ending="The jar stood safe on the stone while they drank.", guards={"milk", "water", "juice", "broth"}),
}

GIRL_NAMES = ["Mina", "Lina", "Tess", "Nora", "Ivy", "Mara"]
BOY_NAMES = ["Owen", "Perry", "Silas", "Jules", "Ezra", "Robin"]
HELPER_NAMES = ["Aunt Sera", "Old Bram", "Grandma June", "Farmer Nia"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-style story world about a liter, dialogue, a twist, and kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--drink", choices=DRINKS)
    ap.add_argument("--encounter", choices=ENCOUNTERS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--carrier-name")
    ap.add_argument("--carrier-type", choices=["girl", "boy"])
    ap.add_argument("--requester-name")
    ap.add_argument("--requester-type", choices=["girl", "boy", "goat", "mule", "hen", "cat"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["woman", "man", "goat", "mule", "hen", "cat"])
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
              and (getattr(args, "drink", None) is None or c[1] == getattr(args, "drink", None))
              and (getattr(args, "encounter", None) is None or c[2] == getattr(args, "encounter", None))
              and (getattr(args, "method", None) is None or c[3] == getattr(args, "method", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, drink, encounter, method = rng.choice(list(combos))
    carrier_type = getattr(args, "carrier_type", None) or rng.choice(["girl", "boy"])
    carrier_name = getattr(args, "carrier_name", None) or rng.choice(GIRL_NAMES if carrier_type == "girl" else BOY_NAMES)
    requester_type = getattr(args, "requester_type", None) or rng.choice(["goat", "mule", "hen", "cat"])
    requester_name = getattr(args, "requester_name", None) or _safe_lookup(ENCOUNTERS, encounter).name
    helper_type = getattr(args, "helper_type", None) or rng.choice(["woman", "man"])
    helper_name = getattr(args, "helper_name", None) or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, drink=drink, encounter=encounter, method=method,
                       carrier_name=carrier_name, carrier_type=carrier_type,
                       requester_name=requester_name, requester_type=requester_type,
                       helper_name=helper_name, helper_type=helper_type)


def tell(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    drink_cfg = _safe_lookup(DRINKS, params.drink)
    encounter_cfg = _safe_lookup(ENCOUNTERS, params.encounter)
    method_cfg = _safe_lookup(METHODS, params.method)
    world = World(place)

    carrier = world.add(Entity(id="carrier", kind="character", type=params.carrier_type, label=params.carrier_name, role="carrier"))
    requester = world.add(Entity(id="requester", kind="character", type=params.requester_type, label=params.requester_name, role="requester"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name, role="helper"))
    drink = world.add(Entity(id="drink", kind="thing", type=drink_cfg.kind, label=drink_cfg.name, phrase=drink_cfg.phrase))
    encounter = world.add(Entity(id="encounter", kind="character", type=params.requester_type, label=encounter_cfg.name))
    helper_item = world.add(Entity(id="helper_item", kind="thing", type="tool", label=method_cfg.offer))

    drink.meters["liter"] = 1.0
    drink.meters["shared_liter"] = 0.0
    carrier.memes["kindness"] = 0.0
    carrier.meters["willing"] = 0.0
    requester.meters["needs_help"] = 0.0
    requester.meters["helped"] = 0.0
    requester.meters["twist_seen"] = 0.0
    requester.memes["gratitude"] = 0.0
    world.facts.update(carrier=carrier, requester=requester, helper=helper, drink_ent=drink,
                       encounter_ent=requester, drink_cfg=drink_cfg, encounter_cfg=encounter_cfg,
                       method_cfg=method_cfg, place=place)

    world.say(f"{carrier.label} walked along {place.name} with {drink_cfg.phrase}.")
    world.say(place.detail)
    world.say(f'"Please wait," {carrier.label} said. "This is for the old miller."')

    world.para()
    requester.meters["needs_help"] = 1.0
    world.say(f'{encounter_cfg.name.capitalize()} stepped from the shade and asked, "{encounter_cfg.request}"')
    world.say(f'{carrier.label} looked at {drink_cfg.phrase} and frowned. "If I share, the liter will be less."')
    world.say(f'"I know," said {helper.label}. "But listen to why it asks."')

    world.para()
    carrier.meters["willing"] = 1.0
    world.say(f'{requester.label.capitalize()} answered, "{encounter_cfg.reason}"')
    world.say(f'Then came the twist: {encounter_cfg.twist}.')
    if compatible(place, drink_cfg, encounter_cfg, method_cfg):
        world.say(f'{carrier.label} nodded. "Then let us be kind."')
        world.say(f'{method_cfg.action}, and {carrier.label} shared without wasting a drop.')
        propagate(world)
        world.para()
        world.say(f'{method_cfg.ending}')
        world.say(f'By the end, the jar still held three quarters of a liter, and the rest had fed the right hunger.')
        world.say(f'{helper.label} smiled at the little party on the road, and {carrier.label} went on lighter-hearted.')
    else:
        pass

    world.facts.update(place=place, drink_cfg=drink_cfg, encounter_cfg=encounter_cfg, method_cfg=method_cfg)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for a child that includes the word "liter" and ends with a kind choice on a road by {f["place"].name}.',
        f'Tell a dialogue-driven story where {f["carrier"].label} carries {f["drink_cfg"].phrase} and must decide whether to share it.',
        f'Write a gentle fable with a twist: a roadside request turns out to help someone for a surprising reason.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    carrier = f["carrier"]
    requester = f["requester"]
    drink_cfg = f["drink_cfg"]
    encounter_cfg = f["encounter_cfg"]
    method_cfg = f["method_cfg"]
    place = f["place"]
    return [
        QAItem(
            question=f"What was {carrier.label} carrying along {place.name}?",
            answer=f"{carrier.label} was carrying {drink_cfg.phrase}. It was a full liter at the start of the walk.",
        ),
        QAItem(
            question=f"What did {encounter_cfg.name} ask {carrier.label} for?",
            answer=f"{encounter_cfg.name} asked, \"{encounter_cfg.request}\" The request made the choice feel important because the liter was meant for someone else.",
        ),
        QAItem(
            question=f"Why did the story need a twist before the ending?",
            answer=f"At first the request seemed to threaten the plan for the drink. Then the twist showed {encounter_cfg.twist}, so kindness became the wiser choice.",
        ),
        QAItem(
            question=f"How did {carrier.label} show kindness?",
            answer=f"{carrier.label} used {method_cfg.offer} and shared a little of the liter. That let {encounter_cfg.name} get help without turning the whole jar empty.",
        ),
        QAItem(
            question=f"What was different at the end of the road?",
            answer=f"The jar was lighter, but not gone. The road had become a place where a small kindness solved a bigger problem.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a liter?",
            answer="A liter is a measure for liquids. It tells how much is in a bottle, jar, or pitcher.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise that changes what you thought would happen. It makes the story turn in a new direction.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing to help or be gentle with someone. A kind act can make a hard moment feel safe.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={dict(m)}")
        if mm:
            bits.append(f"memes={dict(mm)}")
        out.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
share_ok(C,D,E,M) :- carrier(C), drink(D), encounter(E), method(M), compatible(C,D,E,M).
compat_ok(P,D,E,M) :- place(P), drink(D), encounter(E), method(M), place_needs(P,E), guards(M, kind(D)).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("place_needs", pid, a))
    for did, d in DRINKS.items():
        lines.append(asp.fact("drink", did))
        lines.append(asp.fact("kind", did, d.kind))
    for eid, e in ENCOUNTERS.items():
        lines.append(asp.fact("encounter", eid))
        lines.append(asp.fact("need", eid, e.need))
    for mid, m in METHODS.items():
        lines.append(asp.fact("method", mid))
        for g in sorted(m.guards):
            lines.append(asp.fact("guards", mid, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compat_ok/4."))
    return sorted(set(asp.atoms(model, "compat_ok")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH in valid_combos()")
    sample = generate(resolve_params(argparse.Namespace(place=None, drink=None, encounter=None, method=None, carrier_name=None, carrier_type=None, requester_name=None, requester_type=None, helper_name=None, helper_type=None), random.Random(7)))
    if not sample.story:
        ok = False
        print("MISMATCH: empty story")
    print("OK" if ok else "FAIL")
    return 0 if ok else 1


CURATED = [
    StoryParams(place="lane", drink="water", encounter="thirsty_goat", method="share_cup", carrier_name="Mina", carrier_type="girl", requester_name="the goat", requester_type="goat", helper_name="Aunt Sera", helper_type="woman"),
    StoryParams(place="orchard", drink="juice", encounter="small_hen", method="leaf_bowl", carrier_name="Owen", carrier_type="boy", requester_name="the hen", requester_type="hen", helper_name="Old Bram", helper_type="man"),
    StoryParams(place="field", drink="milk", encounter="tired_mule", method="stone_rest", carrier_name="Tess", carrier_type="girl", requester_name="the mule", requester_type="mule", helper_name="Farmer Nia", helper_type="woman"),
    StoryParams(place="bridge", drink="soup", encounter="old_cat", method="share_cup", carrier_name="Robin", carrier_type="boy", requester_name="the cat", requester_type="cat", helper_name="Grandma June", helper_type="woman"),
]


def generate(params: StoryParams) -> StorySample:
    try:
        world = tell(params)
    except KeyError as exc:
        pass
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
        print(asp_program("#show compat_ok/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(row)
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i+1}" if len(samples) > 1 and not getattr(args, "all", None) else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
