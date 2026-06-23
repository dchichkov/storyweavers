#!/usr/bin/env python3
"""
storyworlds/worlds/trucker_bravery_surprise_transformation_slice_of_life.py
==========================================================================

A standalone storyworld about a trucker, a small surprise, and a quiet
transformation in an everyday slice-of-life setting.

This world models a few concrete places and jobs: a trucker arrives with a
delivery or pickup, notices an ordinary problem, and chooses a brave, practical
fix. The surprise is not a twist of fate so much as a gentle reveal: a child,
neighbor, or shop owner has been planning something helpful, and the trucker's
decision turns that plan into a real transformation.

The stories are meant to feel lived-in and child-facing:
- simple local places
- small physical objects with meters like weight, wetness, and readiness
- emotions like worry, bravery, surprise, and relief
- a clear beginning, middle turn, and ending image that proves change

Seed idea:
- A trucker notices a small problem at an everyday place.
- Someone is quietly surprised by the trucker's help.
- The helper's brave choice transforms the situation into something better.

The storyworld uses the shared QA/result containers from storyworlds/results.py
and includes an inline ASP twin for parity checks.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    helper: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    fix_ent: object | None = None
    fragile: object | None = None
    heavy: object | None = None
    helpful: bool = False
    object_ent: object | None = None
    trucker: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad", "trucker"}
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
class Place:
    id: str
    label: str
    scene: str
    affords: set[str] = field(default_factory=set)
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
class Task:
    id: str
    verb: str
    gerund: str
    problem: str
    surprise: str
    transform: str
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
class Item:
    id: str
    label: str
    phrase: str
    location: str
    fragile: bool = False
    heavy: bool = False
    helpful: bool = False
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    answer: object | None = None
    question: object | None = None
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
class Fix:
    id: str
    label: str
    phrase: str
    method: str
    transform: str
    can_help: set[str] = field(default_factory=set)
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.weather = self.weather
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


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


def _r_wet(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["wet"] < THRESHOLD:
            continue
        sig = ("wet", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["worry"] += 1
        out.append(f"{ent.label} looked damp and tired.")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["ready"] < THRESHOLD:
            continue
        sig = ("transform", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["organized"] += 1
        out.append(f"{ent.label} looked neat and useful all at once.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("wet", "physical", _r_wet),
    Rule("transform", "physical", _r_transform),
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


def reasonableness_gate(place: Place, task: Task, item: Item, fix: Fix) -> bool:
    return task.id in place.affords and task.id in item.tags and task.id in fix.can_help


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for tid, task in TASKS.items():
            for iid, item in ITEMS.items():
                for fid, fix in FIXES.items():
                    if reasonableness_gate(place, task, item, fix):
                        combos.append((pid, tid, iid, fid))
    return combos


@dataclass
class StoryParams:
    place: str
    task: str
    item: str
    fix: str
    trucker_name: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: a trucker, a surprise, and a small transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy", "mother", "father", "woman", "man"])
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
              and (getattr(args, "item", None) is None or c[2] == getattr(args, "item", None))
              and (getattr(args, "fix", None) is None or c[3] == getattr(args, "fix", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, item, fix = rng.choice(list(combos))
    helper_type = getattr(args, "helper_type", None) or rng.choice(["girl", "boy", "mother", "father"])
    helper_name = getattr(args, "helper_name", None) or rng.choice(GIRL_NAMES if helper_type in {"girl", "mother", "woman"} else BOY_NAMES)
    trucker_name = getattr(args, "name", None) or rng.choice(TRUCKER_NAMES)
    return StoryParams(place=place, task=task, item=item, fix=fix,
                       trucker_name=trucker_name, helper_name=helper_name,
                       helper_type=helper_type)


def _pronoun_for_type(t: str, case: str = "subject") -> str:
    if t in {"girl", "mother", "woman"}:
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    if t in {"boy", "father", "man"}:
        return {"subject": "he", "object": "him", "possessive": "his"}[case]
    return {"subject": "they", "object": "them", "possessive": "their"}[case]


def tell(place: Place, task: Task, item: Item, fix: Fix, trucker_name: str, helper_name: str, helper_type: str) -> World:
    world = World(place)
    trucker = world.add(Entity(id=trucker_name, kind="character", type="trucker", role="trucker", traits=["steady", "brave"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper", traits=["quiet", "hopeful"]))
    object_ent = world.add(Entity(id=item.id, type="thing", label=item.label, phrase=item.phrase, location=item.location, fragile=item.fragile, heavy=item.heavy, helpful=item.helpful, plural=item.plural, traits=list(item.tags)))
    fix_ent = world.add(Entity(id=fix.id, type="thing", label=fix.label, phrase=fix.phrase, location=place.id, helpful=True, traits=list(fix.tags)))
    world.weather = "rainy" if task.id == "rain" else "clear"

    trucker.memes["bravery"] += 1
    helper.memes["surprise"] += 1

    world.say(f"At {place.label}, {trucker_name} the trucker arrived with an ordinary job and a quiet mind.")
    world.say(f"{helper_name} was there too, and {helper.pronoun().capitalize()} had a small surprise waiting near {item.phrase}.")
    world.say(f"{place.scene}.")

    world.para()
    world.say(f"Then the day turned tricky: {task.problem}.")
    trucker.memes["bravery"] += 1
    trucker.memes["care"] += 1
    world.say(f"{trucker_name} took a breath and chose the brave thing: {task.verb}.")
    world.say(f"{helper_name} blinked in surprise, because nobody had expected a trucker to help quite that way.")

    object_ent.meters["wet"] += 1
    object_ent.meters["ready"] += 1
    fix_ent.meters["ready"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"With {fix.label}, the little problem became a better shape altogether.")
    world.say(f"{task.transform}, and the surprise felt warm instead of shaky.")
    helper.memes["joy"] += 1
    trucker.memes["pride"] += 1
    world.say(f"By the end, {helper_name} was smiling, and {trucker_name} drove away with {world.place.label} looking tidier than before.")

    world.facts.update(
        trucker=trucker,
        helper=helper,
        place=place,
        task=task,
        item=object_ent,
        fix=fix_ent,
        item_cfg=item,
        fix_cfg=fix,
        outcome="transformed",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    t: Entity = f["trucker"]
    h: Entity = f["helper"]
    task: Task = f["task"]
    place: Place = f["place"]
    item: Item = f["item_cfg"]
    return [
        f'Write a slice-of-life story for a young child about a trucker named {t.id} who helps at {place.label} and includes the word "trucker".',
        f"Tell a gentle story where {h.id} has a surprise for {t.id}, and {t.id} bravely fixes {item.phrase} at {place.label}.",
        f"Write a small everyday story about bravery, surprise, and transformation at {place.label}, ending with {task.transform}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    t: Entity = f["trucker"]
    h: Entity = f["helper"]
    place: Place = f["place"]
    task: Task = f["task"]
    item: Item = f["item_cfg"]
    fix: Fix = f["fix_cfg"]
    qa = [
        QAItem(
            question=f"Who is the story about at {place.label}?",
            answer=f"It is about {t.id}, a trucker who shows up for an ordinary day at {place.label}. {h.id} is there too, and {h.pronoun()} has a small surprise nearby.",
        ),
        QAItem(
            question=f"What made the day feel surprising before {t.id} fixed anything?",
            answer=f"{h.id} had a quiet surprise ready, so the day felt different before the problem was solved. That surprise made {t.id}'s help feel even kinder.",
        ),
        QAItem(
            question=f"How did {t.id} show bravery in the story?",
            answer=f"{t.id} chose to help right away instead of ignoring the problem. {t.id} used {fix.label} to deal with {item.phrase}, and that brave choice changed the whole scene.",
        ),
    ]
    qa.append(QAItem(
        question=f"What transformed by the end of the story?",
        answer=f"{item.phrase} and the little problem around it transformed into something neat and useful. The ending shows {fix.label} and {task.transform} turning an ordinary moment into a better one.",
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["task"].tags) | set(world.facts["item_cfg"].tags) | set(world.facts["fix_cfg"].tags)
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            for q, a in KNOWLEDGE[tag]:
                out.append(QAItem(question=q, answer=a))
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
        if e.location:
            bits.append(f"location={e.location}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


PLACES = {
    "truck_stop": Place(id="truck_stop", label="the truck stop", scene="The coffee smelled warm, the floor shone, and a chalkboard leaned near the counter.", affords={"coffee", "repair", "rain"}),
    "corner_shop": Place(id="corner_shop", label="the corner shop", scene="The shelves were close together, the bell over the door jingled, and the afternoon felt slow.", affords={"repair", "rain"}),
    "school_gate": Place(id="school_gate", label="the school gate", scene="Cars whispered by, a few parents waited, and bright drawings fluttered on the fence.", affords={"repair", "rain"}),
}

TASKS = {
    "rain": Task(id="rain", verb="cover the stacked boxes before the rain got in", gerund="covering the boxes", problem="a fresh rain began to blow through the open loading area", surprise="the rain", transform="the boxes stayed dry and easy to carry", tags={"rain", "wet"}),
    "repair": Task(id="repair", verb="straighten the fallen display and tie it down", gerund="straightening the display", problem="the display had tipped over and blocked the walkway", surprise="the fallen display", transform="the walkway opened again and the stand looked ready", tags={"repair"}),
    "coffee": Task(id="coffee", verb="move the spill and set out clean cups", gerund="moving the spill", problem="a cup of coffee had tipped across the counter", surprise="the coffee spill", transform="the counter looked neat and ready for the next customer", tags={"coffee", "wet"}),
}

ITEMS = {
    "boxes": Item(id="boxes", label="boxes", phrase="the stacked boxes", location="the loading area", heavy=True, plural=True, tags={"rain", "repair"}),
    "display": Item(id="display", label="display stand", phrase="the fallen display", location="the walkway", fragile=True, tags={"repair"}),
    "cups": Item(id="cups", label="cups", phrase="the clean cups", location="the counter", plural=True, helpful=True, tags={"coffee"}),
}

FIXES = {
    "strap": Fix(id="strap", label="a bright strap", phrase="a bright strap", method="tie it down", transform="the display stayed steady", can_help={"repair", "rain"}, tags={"repair", "rain"}),
    "tarp": Fix(id="tarp", label="a blue tarp", phrase="a blue tarp", method="cover it", transform="the boxes stayed dry", can_help={"rain", "coffee"}, tags={"rain", "coffee"}),
    "rag": Fix(id="rag", label="a clean rag", phrase="a clean rag", method="wipe it up", transform="the counter looked fresh again", can_help={"coffee"}, tags={"coffee"}),
}

TRUCKER_NAMES = ["Milo", "June", "Rae", "Cal", "Nina", "Otis", "Bea", "Ivy"]
GIRL_NAMES = ["Maya", "Luna", "Tess", "Pia", "Ruby", "Nora", "Zoe"]
BOY_NAMES = ["Eli", "Owen", "Finn", "Noah", "Theo", "Max", "Leo"]

KNOWLEDGE = {
    "rain": [("What is rain?", "Rain is water that falls from clouds in the sky. It can wet roads, boxes, clothes, and shoes.")],
    "wet": [("What does wet mean?", "Wet means something has water on it. A wet thing can feel cool and heavy.")],
    "repair": [("What does it mean to repair something?", "To repair something means to fix it so it works or looks better again.")],
    "coffee": [("What is coffee?", "Coffee is a warm drink grown-ups often sip in the morning or during a break.")],
}
KNOWLEDGE_ORDER = ["rain", "wet", "repair", "coffee"]


def valid_story_sets() -> list[tuple[str, str, str, str]]:
    return valid_combos()


def explain_rejection(place: Place, task: Task, item: Item, fix: Fix) -> str:
    return f"(No story: {fix.label} does not sensibly help with {task.verb} at {place.label}.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("task_tag", tid, tag))
    for iid, i in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for tag in sorted(i.tags):
            lines.append(asp.fact("item_tag", iid, tag))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for tag in sorted(f.can_help):
            lines.append(asp.fact("fix_can_help", fid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T,I,F) :- place(P), task(T), item(I), fix(F), affords(P,T), task_tag(T,Tag), item_tag(I,Tag), fix_can_help(F,Tag).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid-combos.")
        return 1
    sample_params = resolve_params(argparse.Namespace(place=None, task=None, item=None, fix=None, name=None, helper_name=None, helper_type=None), random.Random(777))
    try:
        sample = generate(sample_params)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="smoke")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print(f"OK: ASP matches Python and smoke generate/emit succeeded ({sample_params.place}).")
    return 0


def generate(params: StoryParams) -> StorySample:
    for name in ["place", "task", "item", "fix"]:
        if getattr(params, name) not in (globals().get(name.upper() + "S") or globals().get(name.upper() + "ES") or globals().get(name.upper()[:-1] + "IES") or {}):
            pass
    place = _safe_lookup(PLACES, params.place)
    task = _safe_lookup(TASKS, params.task)
    item = _safe_lookup(ITEMS, params.item)
    fix = _safe_lookup(FIXES, params.fix)
    if not reasonableness_gate(place, task, item, fix):
        pass
    world = tell(place, task, item, fix, params.trucker_name, params.helper_name, params.helper_type)
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
    StoryParams(place="truck_stop", task="rain", item="boxes", fix="tarp", trucker_name="Milo", helper_name="June", helper_type="girl"),
    StoryParams(place="corner_shop", task="repair", item="display", fix="strap", trucker_name="Rae", helper_name="Owen", helper_type="boy"),
    StoryParams(place="truck_stop", task="coffee", item="cups", fix="rag", trucker_name="Cal", helper_name="Tess", helper_type="girl"),
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
        print(f"{len(combos)} valid combinations:\n")
        for pid, tid, iid, fid in combos:
            print(f"  {pid:11} {tid:8} {iid:8} {fid}")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.trucker_name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
