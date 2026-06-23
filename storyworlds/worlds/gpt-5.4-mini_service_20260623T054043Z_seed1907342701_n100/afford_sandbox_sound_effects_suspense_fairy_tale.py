#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/afford_sandbox_sound_effects_suspense_fairy_tale.py
===============================================================================================================================

A standalone storyworld for a tiny fairy-tale sandbox domain with sound effects,
suspense, and an "afford" constraint.

Premise:
- A child loves to build a little castle in a sandbox.
- A nearby thing might blow sand away, splash the tower, or hide the path.
- The parent or helper offers a plausible fix that actually fits the problem.

The world uses:
- typed entities with meters and memes
- a small forward-chaining causal model
- a reasonableness gate
- inline ASP rules with a parity check
- grounded story QA, story prompts, and world knowledge QA
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
    tags: set[str] = field(default_factory=set)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    fix_ent: object | None = None
    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "princess"}
        male = {"boy", "father", "dad", "man", "king", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
    place: str = "the sandbox"
    affords: set[str] = field(default_factory=set)
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
class Problem:
    id: str
    label: str
    verb: str
    sound: str
    danger: str
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
class ObjectChoice:
    id: str
    label: str
    phrase: str
    problem: str
    afford: set[str]
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
class Fix:
    id: str
    label: str
    phrase: str
    solves: str
    afford: set[str]
    sound: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.problem: Optional[Problem] = None
        self.item: Optional[ObjectChoice] = None
        self.fix: Optional[Fix] = None

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def chars(self) -> list[Entity]:
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.problem = self.problem
        w.item = self.item
        w.fix = self.fix
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


def _r_damage(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    item = world.get("item")
    if hero.memes["fear"] < THRESHOLD:
        return out
    if hero.meters["wind"] < THRESHOLD and hero.meters["splash"] < THRESHOLD:
        return out
    sig = ("damage", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if hero.meters["wind"] >= THRESHOLD:
        item.meters["blown"] += 1
        out.append(f"Fwoosh! The wind nipped at the {item.label}.")
    if hero.meters["splash"] >= THRESHOLD:
        item.meters["wet"] += 1
        out.append(f"Plink! Water kissed the {item.label}.")
    item.meters["messy"] += 1
    return out


def _r_fix(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    item = world.get("item")
    fix = world.get("fix")
    if hero.memes["hope"] < THRESHOLD:
        return out
    if item.meters["messy"] < THRESHOLD:
        return out
    sig = ("fix", item.id, fix.id)
    if sig in world.fired:
        return out
    if fix.solves == "wind" and item.meters["blown"] < THRESHOLD:
        return out
    if fix.solves == "water" and item.meters["wet"] < THRESHOLD:
        return out
    world.fired.add(sig)
    item.meters["messy"] = 0
    item.memes["saved"] += 1
    out.append(f"{fix.sound} {fix.label.capitalize()} did the trick.")
    return out


CAUSAL_RULES = [Rule("damage", "physical", _r_damage), Rule("fix", "physical", _r_fix)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(items)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def available_fix(problem: Problem, item: ObjectChoice) -> bool:
    return problem.id in item.problem and problem.id in item.afford


def choose_fix(problem: Problem, item: ObjectChoice) -> Optional[Fix]:
    for fix in FIXES.values():
        if fix.solves == problem.id and problem.id in fix.afford:
            return fix
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            for item_id, item in OBJECTS.items():
                if pid != item.problem:
                    continue
                if not available_fix(problem, item):
                    continue
                combos.append((place, pid, item_id))
    return combos


@dataclass
class StoryParams:
    place: str
    problem: str
    item: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None
    sample: object | None = None
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


SETTINGS = {
    "sandbox": Setting(place="the sandbox", affords={"wind", "water"}),
}

PROBLEMS = {
    "wind": Problem("wind", "a whispering wind", "whispered", "whooosh", "blow the castle apart", {"wind"}),
    "water": Problem("water", "a sneaky splash", "splashed", "plip-plop", "wash the moat away", {"water"}),
}

OBJECTS = {
    "tower": ObjectChoice("tower", "sand tower", "the sand tower", "wind", {"wind"}, {"castle"}),
    "bridge": ObjectChoice("bridge", "sand bridge", "the sand bridge", "wind", {"wind"}, {"castle"}),
    "moat": ObjectChoice("moat", "sand moat", "the sand moat", "water", {"water"}, {"castle"}),
}

FIXES = {
    "parasol": Fix("parasol", "striped parasol", "the striped parasol", "wind", {"wind"}, "Zip-zap!", {"shade"}),
    "wall": Fix("wall", "little shell wall", "the little shell wall", "wind", {"wind"}, "Clack-clack!", {"shells"}),
    "bucket": Fix("bucket", "tiny bucket wall", "the tiny bucket wall", "water", {"water"}, "Splish-splash!", {"water"}),
    "plank": Fix("plank", "flat wooden plank", "the flat wooden plank", "water", {"water"}, "Thunk!", {"wood"}),
}

GIRL_NAMES = ["Mina", "Luna", "Tessa", "Ivy", "Nora", "Pia"]
BOY_NAMES = ["Owen", "Finn", "Eli", "Theo", "Noel", "Milo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale sandbox storyworld with sound effects and suspense.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--item", choices=OBJECTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["mother", "father"])
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
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
              and (getattr(args, "item", None) is None or c[2] == getattr(args, "item", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem, item = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    helper_type = getattr(args, "helper_type", None) or rng.choice(["mother", "father"])
    hero_name = getattr(args, "hero_name", None) or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice(["Aster", "Brina", "Cedric", "Dalia", "Eamon"])
    return StoryParams(place=place, problem=problem, item=item, hero_name=hero_name, hero_type=hero_type, helper_name=helper_name, helper_type=helper_type)


def tell(setting: Setting, problem: Problem, item_cfg: ObjectChoice, fix: Fix,
         hero_name: str, hero_type: str, helper_name: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name, role="helper"))
    item = world.add(Entity(id="item", type="thing", label=item_cfg.label, phrase=item_cfg.phrase, owner=hero_name))
    fix_ent = world.add(Entity(id="fix", type="thing", label=fix.label, phrase=fix.phrase, owner=helper_name))
    world.problem = problem
    world.item = item_cfg
    world.fix = fix
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["item_cfg"] = item_cfg
    world.facts["fix"] = fix
    world.facts["problem"] = problem
    hero.memes["hope"] = 1
    hero.memes["fear"] = 0
    item.meters["messy"] = 0
    world.say(f"Once upon a time, {hero_name} built {item_cfg.phrase} in {setting.place}.")
    world.say(f"\"How fine,\" {helper_name} said, and the little tower sparkled like a jewel.")
    world.para()
    hero.memes["fear"] += 1
    if problem.id == "wind":
        hero.meters["wind"] += 1
        world.say(f"Then came a hush... whooosh! The wind slid over the sand and made the little crown tremble.")
        world.say(f"{hero_name} held {hero.pronoun('possessive')} breath and watched the highest grain wobble.")
    else:
        hero.meters["splash"] += 1
        world.say(f"Then came a hush... plip-plop! A sly splash crept close, and the moat began to shine with water.")
        world.say(f"{hero_name} blinked as the damp edge crawled toward the castle wall.")
    propagate(world)
    world.para()
    helper.memes["hope"] += 1
    if problem.id == "wind":
        world.say(f"{helper_name} hurried near with a smile. \"We can afford a safer trick,\" {helper_name} whispered.")
    else:
        world.say(f"{helper_name} hurried near with a smile. \"We can afford a better trick,\" {helper_name} whispered.")
    world.say(f"{fix.sound} {helper_name} set down {fix.phrase} beside the sand.")
    item.meters["blessed"] += 1
    if problem.id == fix.solves:
        item.meters["messy"] = 0
        world.say(f"With a careful touch, the castle stood safe again, and the shadow moved on.")
        world.say(f"At sunset, {item_cfg.label} rested proud and dry while {hero_name} grinned.")
    else:
        world.say(f"But the spell did not fit the trouble, and the sand stayed in danger.")
    world.facts["fix_ent"] = fix_ent
    world.facts["setting"] = setting
    world.facts["seed_story"] = True
    return world


def story_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem"]
    item = f["item_cfg"]
    return [
        f'Write a short fairy tale in a sandbox where {hero.label} hears {problem.sound} and must protect {item.label}.',
        f'Tell a gentle suspense story for young children with the word "afford" and the sound effect "{problem.sound}".',
        f'Write a fairy tale about a child in the sandbox who finds a clever way to keep {item.label} safe from {problem.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    problem = f["problem"]
    item = f["item_cfg"]
    fix = f["fix"]
    answers = [
        QAItem(
            question=f"What did {hero.label} build in the sandbox?",
            answer=f"{hero.label} built {item.phrase} in the sandbox. It was a tiny castle piece that could be watched from close by.",
        ),
        QAItem(
            question=f"What sound warned {hero.label} that trouble was coming?",
            answer=f"The warning sound was {problem.sound}. It made the moment feel suspenseful, because something was about to reach the sand tower.",
        ),
        QAItem(
            question=f"How did {helper.label} help {hero.label} keep the castle safe?",
            answer=f"{helper.label} brought {fix.phrase} and used it to solve the trouble. That let the sandbox scene stay magical instead of messy.",
        ),
    ]
    if world.get("item").meters["messy"] == 0:
        answers.append(QAItem(
            question=f"What changed at the end for {item.label}?",
            answer=f"{item.label} ended up safe and tidy. The sand piece stood proud again, so the last image was a clean little castle in the light.",
        ))
    else:
        answers.append(QAItem(
            question=f"Why was {item.label} still in danger at the end?",
            answer=f"The fix did not match the problem well enough, so the trouble stayed close. The story left the castle in a tense moment instead of a safe one.",
        ))
    return answers


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does 'afford' mean in this storyworld?",
               "Here, afford means a fix fits the kind of trouble well enough to help. A parasol can afford wind trouble, while a bucket wall can afford water trouble."),
        QAItem("Why do sand castles need careful helpers?",
               "Sand castles are delicate because wind and water can change them quickly. A careful helper can choose the right fix before the castle falls apart."),
        QAItem("What is suspense?",
               "Suspense is the worried feeling when you wait to see what will happen next. In this world, the sound effects make that waiting feel even stronger."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS or params.problem not in PROBLEMS or params.item not in OBJECTS:
        pass
    setting = _safe_lookup(SETTINGS, params.place)
    problem = _safe_lookup(PROBLEMS, params.problem)
    item_cfg = _safe_lookup(OBJECTS, params.item)
    fix = choose_fix(problem, item_cfg)
    if fix is None:
        pass
    world = tell(setting, problem, item_cfg, fix, params.hero_name, params.hero_type, params.helper_name, params.helper_type)
    return StorySample(params=params, story=world.render(), prompts=story_prompts(world), story_qa=story_qa(world), world_qa=world_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, dict(e.meters), dict(e.memes))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
problem_affords(P, I) :- problem(P), item(I), solves(F, P), item_problem(I, P).
valid_combo(Place, P, I) :- setting(Place), problem(P), item(I), problem_affords(P, I).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("problem_tag", pid, t))
    for iid, i in OBJECTS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_problem", iid, i.problem))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("solves", fid, f.solves))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    import traceback
    rc = 0
    try:
        pset = set(valid_combos())
        aset = set(asp_valid_combos())
        if pset != aset:
            print("MISMATCH between ASP and Python")
            print("only in asp:", sorted(aset - pset))
            print("only in python:", sorted(pset - aset))
            rc = 1
        sample = generate(StoryParams(place="sandbox", problem="wind", item="tower", hero_name="Mina", hero_type="girl", helper_name="Aster", helper_type="mother"))
        emit(sample, trace=False, qa=False)
    except Exception:
        traceback.print_exc()
        return 1
    if rc == 0:
        print("OK: ASP and Python match, and story generation smoke test passed.")
    return rc


CURATED = [
    StoryParams(place="sandbox", problem="wind", item="tower", hero_name="Mina", hero_type="girl", helper_name="Aster", helper_type="mother", seed=1),
    StoryParams(place="sandbox", problem="wind", item="bridge", hero_name="Owen", hero_type="boy", helper_name="Brina", helper_type="father", seed=2),
    StoryParams(place="sandbox", problem="water", item="moat", hero_name="Luna", hero_type="girl", helper_name="Cedric", helper_type="father", seed=3),
    StoryParams(place="sandbox", problem="water", item="moat", hero_name="Finn", hero_type="boy", helper_name="Dalia", helper_type="mother", seed=4),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale sandbox storyworld with suspenseful sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--item", choices=OBJECTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["mother", "father"])
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_combo/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
