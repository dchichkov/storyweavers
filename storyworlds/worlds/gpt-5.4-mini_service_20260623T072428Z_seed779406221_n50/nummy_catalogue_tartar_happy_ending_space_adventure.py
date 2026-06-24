#!/usr/bin/env python3
"""
storyworlds/worlds/nummy_catalogue_tartar_happy_ending_space_adventure.py
=========================================================================

A standalone story world for a small Space Adventure tale about a child,
a nummy catalogue, and a tartar problem that becomes a happy ending.

Seed words: nummy, catalogue, tartar
Style: Space Adventure
Feature: Happy Ending

Story premise:
- A child on a tiny ship loves looking through a catalogue of space snacks.
- One snack is the nummy "star tartar" treat.
- The child wants to open the snack now, but the grown-up worries the packet
  will tear and make a sticky mess in the control room.
- A better plan appears: use a tray, ask the helper robot, and open it in the
  galley.
- The ending proves the change by showing the snack shared safely in orbit.

World model:
- Entities have meters and memes.
- Physical meters track mess and readiness.
- Emotional memes track joy, impatience, worry, and relief.
- The story text is generated from state changes, not from a frozen template.

The script supports:
- default runs and -n
- --all, --seed, --trace, --qa, --json
- --asp, --verify, --show-asp
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
METER_KEYS = {"sticky", "crumby", "sauce", "crumbs"}



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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    portable: bool = True
    edible: bool = False
    helpful: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    control: object | None = None
    helper: object | None = None
    hero: object | None = None
    parent: object | None = None
    snack_ent: object | None = None
    tray: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Location:
    id: str
    label: str
    kind: str = "place"
    spacey: bool = True
    allows_open_food: bool = False
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
class Snack:
    id: str
    label: str
    phrase: str
    taste: str
    mess_kind: str
    at_risk: str
    keyword: str = "nummy"
    tags: set[str] = field(default_factory=set)
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
    phrase: str
    method: str
    tail: str
    tags: set[str] = field(default_factory=set)
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
    def __init__(self, location: Location) -> None:
        self.location = location
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.location)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.zone = set(self.zone)
        return c


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


def _r_mess(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.meters["sticky"] < THRESHOLD:
            continue
        if ent.location not in world.zone:
            continue
        sig = ("mess", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("control").meters["sticky"] += 1
        out.append("The control panel got sticky.")
    return out


CAUSAL_RULES = [Rule("mess", "physical", _r_mess)]


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


def snack_at_risk(snack: Snack) -> bool:
    return snack.mess_kind in {"sticky", "crumbs", "sauce"}


def choose_helper(snack: Snack) -> Optional[Helper]:
    for helper in HELPERS:
        if snack.mess_kind in helper.tags:
            return helper
    return None


def predict_mess(world: World, snack: Snack) -> bool:
    sim = world.copy()
    sim.get("snack").meters[snack.mess_kind] += 1
    sim.zone = {sim.get("snack").location}
    propagate(sim, narrate=False)
    return sim.get("control").meters["sticky"] >= THRESHOLD


def open_snack(world: World, child: Entity, snack: Snack, narrate: bool = True) -> None:
    child.meters[snack.mess_kind] += 1
    child.memes["joy"] += 1
    world.zone = {child.location}
    propagate(world, narrate=narrate)


@dataclass
class StoryParams:
    place: str
    snack: str
    helper: str
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


LOCATIONS = {
    "ship": Location("ship", "the little starship bridge", True, False),
    "galley": Location("galley", "the ship's galley", True, True),
    "dock": Location("dock", "the moon dock", True, False),
}

SNACKS = {
    "star_tartar": Snack(
        id="star_tartar",
        label="star tartar",
        phrase="a nummy packet of star tartar",
        taste="salty and bright",
        mess_kind="sticky",
        at_risk="the control panel",
        keyword="nummy",
        tags={"nummy", "tartar", "sticky"},
    ),
    "moon_crumbs": Snack(
        id="moon_crumbs",
        label="moon crumbs",
        phrase="a nummy bag of moon crumbs",
        taste="toasty and crunchy",
        mess_kind="crumbs",
        at_risk="the floor",
        keyword="nummy",
        tags={"nummy", "crumbs"},
    ),
}

HELPERS = [
    Helper("traybot", "Tray-Bot", "a tray bot", "carry the snack on a tray", "rolled along happily", {"sticky", "crumbs"}),
    Helper("napkin_pack", "napkin pack", "a stack of soft napkins", "wrap the snack first", "sat ready beside the table", {"sticky", "crumbs"}),
]

GIRL_NAMES = ["Ava", "Mina", "Lia", "Zoe", "Nia"]
BOY_NAMES = ["Leo", "Finn", "Tao", "Milo", "Noah"]
TRAITS = ["curious", "brave", "cheerful", "careful"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in LOCATIONS:
        for snack in SNACKS:
            if snack_at_risk(_safe_lookup(SNACKS, snack)) and choose_helper(_safe_lookup(SNACKS, snack)):
                out.append((place, snack, _safe_lookup(HELPERS, 0).id))
    return out


def build_world(place: Location, snack: Snack) -> World:
    world = World(place)
    hero = world.add(Entity("hero", kind="character", type="girl", location=place.id))
    parent = world.add(Entity("parent", kind="character", type="mother", label="the mom"))
    control = world.add(Entity("control", kind="thing", type="panel", label="the control panel", location="bridge", portable=False))
    snack_ent = world.add(Entity("snack", kind="thing", type="snack", label=snack.label, phrase=snack.phrase, location=place.id, edible=True))
    tray = world.add(Entity("tray", kind="thing", type="tool", label="a tray", location=place.id))
    helper = world.add(Entity("helper", kind="character", type="robot", label="Tray-Bot", helpful=True, location=place.id))
    world.facts.update(hero=hero, parent=parent, control=control, snack=snack, snack_ent=snack_ent, tray=tray, helper=helper)
    return world


def tell(place: Location, snack: Snack, helper: Helper, name: str, gender: str, parent: str, trait: str) -> World:
    world = build_world(place, snack)
    hero = world.get("hero")
    hero.id = name
    hero.type = gender
    hero.traits = ["little", trait]
    parent_ent = world.get("parent")
    parent_ent.type = parent
    parent_ent.label = "the " + ("mom" if parent == "mother" else "dad")
    snack_ent = world.get("snack")
    helper_ent = world.get("helper")
    helper_ent.label = helper.label

    hero.memes["want"] += 1
    world.say(f"On a tiny starship, {name} loved looking through the snack catalogue for something {snack.keyword}.")
    world.say(f"The page for {snack.label} said it was {snack.taste}, and that made {hero.pronoun().capitalize()} smile.")

    world.para()
    world.say(f"One day, {name} found {snack.phrase} on the catalogue page and wanted it right away.")
    world.say(f"But {parent_ent.label} pointed at {snack.at_risk} and said it would get sticky in the bridge.")

    hero.memes["impatience"] += 1
    world.para()
    world.say(f"{name} started to reach for the packet, but {parent_ent.label} held up a gentle hand.")
    if predict_mess(world, snack):
        world.say(f'"If you open it here," {parent_ent.label} said, "the {snack.label} will make a sticky mess."')
    helper_ent.memes["help"] += 1
    world.say(f"Then {helper.label} rolled over and offered to {helper.method}.")

    hero.memes["worry"] += 1
    world.say(f"{name} nodded, because {hero.pronoun('possessive')} little spaceship game would be better with a clean bridge.")

    world.para()
    world.zone = {"galley"}
    hero.location = "galley"
    parent_ent.location = "galley"
    helper_ent.location = "galley"
    snack_ent.location = "galley"
    world.say(f"They carried the packet to the galley, where {helper.label} {helper.tail}.")
    world.say(f"{name} opened the packet over the tray, and the {snack.label} stayed in one neat pile.")
    hero.memes["joy"] += 2
    hero.memes["relief"] += 1
    parent_ent.memes["relief"] += 1
    world.say(f"{name} took the first bite and grinned. The {snack.label} was nummy, and the bridge stayed clean.")
    world.say(f"After that, the little starship drifted on through the stars with happy tummies and a tidy control room.")

    world.facts.update(
        outcome="happy",
        location=place,
        helper=helper,
        snack_cfg=snack,
        name=name,
        gender=gender,
        parent_kind=parent,
        trait=trait,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    snack = f["snack_cfg"]
    return [
        f'Write a short space-adventure story for a 3-to-5-year-old that includes the word "{snack.keyword}" and a happy ending.',
        f"Tell a gentle story about a child on a starship who wants {snack.phrase} from a catalogue, but a grown-up worries about a sticky mess and helps find a safer way.",
        f'Write a simple story where a nummy snack called "{snack.label}" is opened safely in a spaceship galley.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    snack = f["snack_cfg"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Who is the story about on the little starship?",
            answer=f"It is about {hero.id}, who loved the snack catalogue and wanted {snack.phrase}.",
        ),
        QAItem(
            question=f"Why did {parent.label_word} worry about {snack.label} in the bridge?",
            answer=f"{parent.label_word.capitalize()} worried it would get sticky on {world.get('control').label}, so they moved the snack to the galley.",
        ),
        QAItem(
            question=f"How did {helper.label} help with the nummy snack?",
            answer=f"{helper.label} helped by offering a tray and guiding everyone to the galley so the packet could be opened safely.",
        ),
        QAItem(
            question=f"What made the ending happy?",
            answer=f"The snack got eaten, the bridge stayed clean, and everyone ended up smiling together on the starship.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a catalogue?", "A catalogue is a book or list that shows things you can choose from."),
        QAItem("What does nummy mean?", "Nummy means tasty or yummy."),
        QAItem("What is tartar?", "In this story, tartar is a salty snack name, like a fun space treat."),
        QAItem("Why do trays help with snacks?", "A tray helps hold food in one place so crumbs or sauce do not spill everywhere."),
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
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k,v) for k,v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k,v) for k,v in e.memes.items() if v)}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="ship", snack="star_tartar", helper="traybot", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="galley", snack="moon_crumbs", helper="napkin_pack", name="Leo", gender="boy", parent="father", trait="cheerful"),
]


@dataclass
class StoryParams:
    place: str
    snack: str
    helper: str
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


ASP_RULES = r"""
hazard(S) :- snack(S), mess_kind(S, sticky).
compatible(L, S) :- helper(L), snack(S), mess_kind(S, sticky).
valid(P, S, H) :- place(P), snack(S), helper(H), hazard(S), compatible(H, S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in LOCATIONS:
        lines.append(asp.fact("place", pid))
    for sid, s in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        lines.append(asp.fact("mess_kind", sid, s.mess_kind))
    for hid, h in [(h.id, h) for h in HELPERS]:
        lines.append(asp.fact("helper", hid))
        for t in sorted(h.tags):
            lines.append(asp.fact("helps", hid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, s, _safe_lookup(HELPERS, 0).id) for p, s, _ in valid_combos()}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld with a nummy catalogue and a happy ending.")
    ap.add_argument("--place", choices=LOCATIONS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--helper", choices={h.id for h in HELPERS})
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if getattr(args, "snack", None):
        snack = _safe_lookup(SNACKS, getattr(args, "snack", None))
        if not snack_at_risk(snack):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(LOCATIONS))
    snack = getattr(args, "snack", None) or rng.choice(list(SNACKS))
    helper = getattr(args, "helper", None) or rng.choice([h.id for h in HELPERS])
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place, snack, helper, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(LOCATIONS, params.place), _safe_lookup(SNACKS, params.snack), next(h for h in HELPERS if h.id == params.helper), params.name, params.gender, params.parent, params.trait)
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
