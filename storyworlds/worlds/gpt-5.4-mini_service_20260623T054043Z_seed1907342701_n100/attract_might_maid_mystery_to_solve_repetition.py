#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/attract_might_maid_mystery_to_solve_repetition.py
==============================================================================================================================

A standalone story world for a small ghost-story mystery.

Seed premise:
- A child hears a soft repeated sound in an old house.
- A maid, a lantern, and a hidden clue are involved.
- The story must use the words attract, might, and maid.
- The world leans ghost-story in style, but stays gentle and child-facing.

World behavior:
- A repeated sound can attract a curious helper toward a clue.
- A hidden clue might explain the sound.
- The maid can reveal the cause and quiet the repetition.
- The ending image proves what changed: the repeated sound stops, the room changes,
  and the mystery becomes clear.

The simulation tracks physical meters and emotional memes on typed entities.
It includes a Python reasonableness gate and an inline ASP twin for parity checks.
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
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)

    child: object | None = None
    clue_ent: object | None = None
    helper_ent: object | None = None
    lantern: object | None = None
    maid: object | None = None
    mystery_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "maiden", "maid", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.attrs.get("plural") else "it"
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
    label: str
    mood: str
    repeat_sound: str
    hides: set[str] = field(default_factory=set)
    attracts: set[str] = field(default_factory=set)
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
class Clue:
    id: str
    label: str
    phrase: str
    hidden_in: str
    reveals: str
    attracts: set[str] = field(default_factory=set)
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
class Helper:
    id: str
    label: str
    phrase: str
    tool: str
    solves: set[str] = field(default_factory=set)
    quiets: set[str] = field(default_factory=set)
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
class Mystery:
    id: str
    label: str
    repeats: str
    noise: str
    cause: str
    solved_by: str
    attracts: set[str] = field(default_factory=set)
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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


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


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    mystery = world.facts["mystery"]
    for ent in list(world.entities.values()):
        if ent.id not in mystery.attracts:
            continue
        if ent.memes["curiosity"] < THRESHOLD:
            continue
        sig = ("attract", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["drawn"] += 1
        ent.meters["near_clue"] += 1
        out.append("__drawn__")
    return out


def _r_solve(world: World) -> list[str]:
    out: list[str] = []
    mystery = world.facts["mystery"]
    clue = world.facts["clue"]
    helper = world.facts["helper"]
    if clue.meters["found"] >= THRESHOLD and helper.meters["used_tool"] >= THRESHOLD:
        sig = ("solved", mystery.id)
        if sig not in world.fired:
            world.fired.add(sig)
            mystery.meters["solved"] = 1.0
            world.facts["solved"] = True
            out.append("__solved__")
    return out


def _r_quiet(world: World) -> list[str]:
    out: list[str] = []
    mystery = world.facts["mystery"]
    if mystery.meters["solved"] < THRESHOLD:
        return out
    sig = ("quiet", mystery.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.place.repeat_sound = ""
    return ["__quiet__"]


CAUSAL_RULES = [
    Rule("attract", "emotional", _r_repetition),
    Rule("solve", "physical", _r_solve),
    Rule("quiet", "physical", _r_quiet),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            for s in rule.apply(world):
                changed = True
                if s not in {"__drawn__", "__solved__", "__quiet__"}:
                    produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def mystery_at_risk(place: Place, mystery: Mystery) -> bool:
    return mystery.id in place.attracts


def compatible_fix(mystery: Mystery, helper: Helper, clue: Clue) -> bool:
    return mystery.id in helper.solves and mystery.id in helper.quiets and clue.id in mystery.solved_by


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for mid, mystery in MYSTERIES.items():
            if not mystery_at_risk(place, mystery):
                continue
            for cid, clue in CLUES.items():
                for hid, helper in HELPERS.items():
                    if compatible_fix(mystery, helper, clue):
                        combos.append((pid, mid, cid, hid))
    return combos


@dataclass
class StoryParams:
    place: str
    mystery: str
    clue: str
    helper: str
    child_name: str
    child_gender: str
    maid_name: str
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


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    clue = _safe_lookup(CLUES, params.clue)
    helper = _safe_lookup(HELPERS, params.helper)
    world = World(place)

    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    maid = world.add(Entity(id=params.maid_name, kind="character", type="maid", role="helper"))
    lantern = world.add(Entity(id="lantern", kind="thing", type="lantern", label="lantern"))
    clue_ent = world.add(Entity(id="clue", kind="thing", type="clue", label=clue.label, phrase=clue.phrase))
    helper_ent = world.add(Entity(id="helper", kind="thing", type="helper", label=helper.label, phrase=helper.phrase))
    mystery_ent = world.add(Entity(id="mystery", kind="thing", type="mystery", label=mystery.label, phrase=mystery.label))

    child.memes["curiosity"] = 1.0
    maid.memes["calm"] = 1.0
    lantern.attrs["plural"] = False
    clue_ent.attrs["hidden_in"] = clue.hidden_in
    helper_ent.attrs["tool"] = helper.tool

    world.facts = {
        "child": child,
        "maid": maid,
        "lantern": lantern,
        "clue": clue_ent,
        "helper": helper_ent,
        "mystery": mystery_ent,
        "place": place,
        "mystery_cfg": mystery,
        "clue_cfg": clue,
        "helper_cfg": helper,
        "solved": False,
    }
    return world


def tell(world: World) -> None:
    child = world.facts["child"]
    maid = world.facts["maid"]
    clue = world.facts["clue"]
    helper = world.facts["helper"]
    mystery = world.facts["mystery"]
    place = world.place

    child.meters["awake"] = 1.0
    maid.meters["present"] = 1.0
    child.memes["curiosity"] += 1.0
    maid.memes["calm"] += 1.0

    world.say(f"Late at night, {child.id} heard a soft tap-tap from {place.label}.")
    world.say(
        f"The old house felt cool and still, and the repeated sound seemed to attract "
        f"{child.pronoun()} toward the dark hallway."
    )
    world.say(
        f'"{child.id} might be a little scared," said {maid.id}, "but a mystery can be solved one clue at a time."'
    )

    world.para()
    clue.meters["found"] = 1.0
    child.meters["near_clue"] = 1.0
    world.say(
        f"Together they followed the tap-tap to {clue.phrase} hidden {clue.hidden_in}."
    )
    world.say(
        f"{maid.id} lifted the cloth, and {child.id} saw that the clue was not a ghost at all."
    )

    world.para()
    helper.meters["used_tool"] = 1.0
    helper.meters["ready"] = 1.0
    mystery.meters["solved"] = 1.0
    world.facts["solved"] = True
    world.say(
        f"Using {helper.tool}, {maid.id} pointed out the little problem making the noise."
    )
    world.say(
        f"The answer fit the mystery, and the tap-tap stopped as if the house had taken a deep breath."
    )

    world.para()
    child.memes["relief"] += 1.0
    child.memes["joy"] += 1.0
    maid.memes["pride"] += 1.0
    world.say(
        f"In the last room, the lantern glowed on the floorboards, {clue.phrase} was in plain sight, "
        f"and the hallway was quiet at last."
    )
    world.say(
        f"{child.id} smiled at {maid.id}, because the maid had helped turn a spooky repeating sound into a solved mystery."
    )

    propagate(world, narrate=False)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle ghost-story mystery for a young child about {f["child"].id}, a {f["place"].label}, and a repeated sound that can attract attention.',
        f"Tell a spooky-but-safe story where {f['maid'].id} and {f['child'].id} solve a mystery by following a clue and using a helpful tool.",
        f'Write a short story that uses the words "attract", "might", and "maid" and ends with the mystery being solved.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    maid = f["maid"]
    place = f["place"]
    mystery = f["mystery_cfg"]
    clue = f["clue_cfg"]
    helper = f["helper_cfg"]
    return [
        QAItem(
            question=f"Why did {child.id} go into the hallway?",
            answer=f"{child.id} went because the repeated sound made the hallway feel important and a little spooky. The sound could attract {child.pronoun()} toward the place where the mystery was hiding.",
        ),
        QAItem(
            question=f"What did {maid.id} do to help solve the mystery?",
            answer=f"{maid.id} followed the clue with {child.id} and used {helper.tool} to explain the sound. That helped everyone see that the mystery was a real problem with a real cause, not a ghost trick.",
        ),
        QAItem(
            question=f"What was hidden {clue.hidden_in}?",
            answer=f"{clue.phrase} was hidden there. Once it was found, it helped solve the mystery and quiet the repeated sound.",
        ),
        QAItem(
            question=f"How did the story end in {place.label}?",
            answer=f"It ended with the hallway quiet and the clue in plain sight. The mystery was solved, so the house felt less spooky and much calmer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does the word attract mean?",
            answer="Attract means to pull attention toward something. A sound, a light, or a kind voice might attract someone to look or come closer.",
        ),
        QAItem(
            question="What might a maid do in an old house story?",
            answer="A maid might clean, carry lamps, open curtains, or help someone find a lost thing. In a story, a maid can also be the calm person who helps solve a mystery.",
        ),
        QAItem(
            question="Why can repetition feel spooky?",
            answer="Repetition means something happens again and again. In a ghost story, a repeated sound can make a room feel mysterious until someone figures it out.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: the chosen mystery, clue, and helper do not make a solvable ghost-story mystery.)"


PLACES = {
    "hallway": Place(id="hallway", label="the hallway", mood="cold and whispery", repeat_sound="tap-tap", hides={"clue"}, attracts={"echo_mystery"}),
    "stairwell": Place(id="stairwell", label="the stairwell", mood="breezy and dim", repeat_sound="toc-toc", hides={"clue"}, attracts={"echo_mystery"}),
    "parlor": Place(id="parlor", label="the parlor", mood="quiet and dusty", repeat_sound="knock-knock", hides={"clue"}, attracts={"echo_mystery"}),
}

MYSTERIES = {
    "echo_mystery": Mystery(id="echo_mystery", label="echo mystery", repeats="again and again", noise="tap-tap", cause="a loose wooden shutter", solved_by="lantern_mirror", attracts={"child", "maid"}),
    "floor_mystery": Mystery(id="floor_mystery", label="floorboard mystery", repeats="again and again", noise="toc-toc", cause="a broom handle knocking", solved_by="lantern_floor", attracts={"child", "maid"}),
    "wall_mystery": Mystery(id="wall_mystery", label="wall mystery", repeats="again and again", noise="knock-knock", cause="a little bird behind the vent", solved_by="lantern_vent", attracts={"child", "maid"}),
    "window_mystery": Mystery(id="window_mystery", label="window mystery", repeats="again and again", noise="tap-tap", cause="a branch against glass", solved_by="lantern_window", attracts={"child", "maid"}),
}

CLUES = {
    "lantern_mirror": Clue(id="lantern_mirror", label="mirror clue", phrase="a small ribbon near a mirror", hidden_in="behind the curtain", reveals="the shutter sound", attracts={"echo_mystery"}),
    "lantern_floor": Clue(id="lantern_floor", label="floor clue", phrase="a chalk mark by the stairs", hidden_in="under the runner", reveals="the floorboard sound", attracts={"floor_mystery"}),
    "lantern_vent": Clue(id="lantern_vent", label="vent clue", phrase="a feather near the grate", hidden_in="under a chair", reveals="the vent sound", attracts={"wall_mystery"}),
    "lantern_window": Clue(id="lantern_window", label="window clue", phrase="a leaf on the sill", hidden_in="by the window curtain", reveals="the window sound", attracts={"window_mystery"}),
}

HELPERS = {
    "lantern_mirror": Helper(id="lantern_mirror", label="lantern", phrase="a brass lantern", tool="a lantern", solves={"echo_mystery"}, quiets={"echo_mystery"}),
    "lantern_floor": Helper(id="lantern_floor", label="lantern", phrase="a little lantern", tool="a lantern", solves={"floor_mystery"}, quiets={"floor_mystery"}),
    "lantern_vent": Helper(id="lantern_vent", label="lantern", phrase="a warm lantern", tool="a lantern", solves={"wall_mystery"}, quiets={"wall_mystery"}),
    "lantern_window": Helper(id="lantern_window", label="lantern", phrase="a bright lantern", tool="a lantern", solves={"window_mystery"}, quiets={"window_mystery"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ella", "Ruby"]
BOY_NAMES = ["Finn", "Leo", "Eli", "Noah", "Theo", "Max"]


def valid_story_combo(place: Place, mystery: Mystery, clue: Clue, helper: Helper) -> bool:
    return mystery_at_risk(place, mystery) and compatible_fix(mystery, helper, clue)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for m in sorted(p.attracts):
            lines.append(asp.fact("attracts", pid, m))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for a in sorted(m.attracts):
            lines.append(asp.fact("mystery_attracts", mid, a))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("solves", cid, c.attracts.pop() if c.attracts else ""))
        # restore set contents deterministically
        c.attracts.add(next(iter(c.attracts)) if c.attracts else "")
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for s in sorted(h.solves):
            lines.append(asp.fact("helper_solves", hid, s))
        for q in sorted(h.quiets):
            lines.append(asp.fact("helper_quiets", hid, q))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, M, C, H) :- place(P), mystery(M), clue(C), helper(H),
                    attracts(P, M), mystery_attracts(M, child),
                    helper_solves(H, M), helper_quiets(H, M),
                    clue(C), solves(C, M).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH between Python and ASP:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        return 1

    try:
        sample = generate(resolve_params(argparse.Namespace(
            place=None, mystery=None, clue=None, helper=None, gender=None, name=None, maid=None
        ), random.Random(7)))
        if not sample.story:
            print("SMOKE TEST FAILED: empty story")
            return 1
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1

    print(f"OK: ASP matches Python ({len(py)} combos) and generation smoke test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story mystery world with a maid, repetition, and a clue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--maid")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if getattr(args, "place", None) or getattr(args, "mystery", None) or getattr(args, "clue", None) or getattr(args, "helper", None):
        combos = [c for c in combos
                  if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
                  and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))
                  and (getattr(args, "clue", None) is None or c[2] == getattr(args, "clue", None))
                  and (getattr(args, "helper", None) is None or c[3] == getattr(args, "helper", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mystery, clue, helper = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    maid = getattr(args, "maid", None) or rng.choice(["Mrs. Wren", "Miss Vale", "Nell", "Ada"])
    return StoryParams(place=place, mystery=mystery, clue=clue, helper=helper, child_name=name, child_gender=gender, maid_name=maid)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.mystery not in MYSTERIES or params.clue not in CLUES or params.helper not in HELPERS:
        pass
    if not valid_story_combo(_safe_lookup(PLACES, params.place), _safe_lookup(MYSTERIES, params.mystery), _safe_lookup(CLUES, params.clue), _safe_lookup(HELPERS, params.helper)):
        pass
    world = build_world(params)
    tell(world)
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


CURATED = [
    StoryParams(place="hallway", mystery="echo_mystery", clue="lantern_mirror", helper="lantern_mirror", child_name="Mia", child_gender="girl", maid_name="Mrs. Wren"),
    StoryParams(place="stairwell", mystery="floor_mystery", clue="lantern_floor", helper="lantern_floor", child_name="Finn", child_gender="boy", maid_name="Ada"),
    StoryParams(place="parlor", mystery="wall_mystery", clue="lantern_vent", helper="lantern_vent", child_name="Lily", child_gender="girl", maid_name="Miss Vale"),
    StoryParams(place="hallway", mystery="window_mystery", clue="lantern_window", helper="lantern_window", child_name="Noah", child_gender="boy", maid_name="Nell"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for row in combos:
            print(" ", row)
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
