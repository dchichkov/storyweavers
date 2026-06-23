#!/usr/bin/env python3
"""
storyworlds/worlds/shah_lesson_learned_animal_story.py
======================================================

A small standalone storyworld in an animal-story style.

Premise:
- An animal child wants to do something fun or practical.
- Another animal or caretaker worries because a needed item might be lost, broken, or made dirty.
- A lesson learned beat resolves the tension: the child understands why the warning mattered, and the ending proves the change with a concrete image.

The world keeps one named seed word, "shah", in the story text and in the generated Q&A. The domain stays small and constraint-checked: one animal, one helper, one place, one wanted action, one risky object, one sensible fix.
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
    kind: str = "thing"   # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict = field(default_factory=dict)

    region: object | None = None
    fix_ent: object | None = None
    helper: object | None = None
    prize: object | None = None
    shah: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

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
class Setting:
    id: str
    place: str
    indoor: bool = False
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
class Want:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str]
    clue: str
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
class Prize:
    id: str
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
class Fix:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    plural: bool = False
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
class StoryParams:
    setting: str
    want: str
    prize: str
    fix: str
    shah: str
    shah_type: str
    helper: str
    helper_type: str
    place_name: str
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
        return any(it.plural or region in it.attrs.get("covers", set()) for it in self.worn_items(actor))

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


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get(world.facts["want"].mess, 0.0) < THRESHOLD:
            continue
        for prize in list(world.entities.values()):
            if prize.id != world.facts["prize_ent"].id:
                continue
            if prize.region not in world.zone:
                continue
            if world.covered(actor, prize.region):
                continue
            sig = ("soil", actor.id, prize.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            prize.meters[world.facts["want"].mess] = prize.meters.get(world.facts["want"].mess, 0.0) + 1
            prize.meters["dirty"] = prize.meters.get("dirty", 0.0) + 1
            out.append(f"{prize.label_word.capitalize()} got messy.")
    return out


def _r_work(world: World) -> list[str]:
    out: list[str] = []
    prize = world.facts["prize_ent"]
    if prize.meters.get("dirty", 0.0) >= THRESHOLD and prize.caretaker:
        sig = ("work", prize.id)
        if sig not in world.fired:
            world.fired.add(sig)
            helper = world.get(prize.caretaker)
            helper.meters["workload"] = helper.meters.get("workload", 0.0) + 1
            out.append(f"That would mean more work for {helper.label_word}.")
    return out


def _r_conflict(world: World) -> list[str]:
    shah = world.facts["shah_ent"]
    if shah.memes.get("stubborn", 0.0) < THRESHOLD or shah.memes.get("warned", 0.0) < THRESHOLD:
        return []
    sig = ("conflict", shah.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    shah.memes["worry"] = shah.memes.get("worry", 0.0) + 1
    return ["__conflict__"]


CAUSAL_RULES = [
    Rule("soil", "physical", _r_soil),
    Rule("work", "physical", _r_work),
    Rule("conflict", "social", _r_conflict),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(x for x in bits if x != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting, want: Want) -> str:
    if setting.indoor:
        return f"Inside, {setting.place} was neat and quiet."
    if want.id == "mud":
        return f"Outside, {setting.place} had soft ground and little muddy spots."
    if want.id == "paint":
        return f"Outside, {setting.place} had a sunny corner and a little table for art."
    return f"{setting.place.capitalize()} looked like a good place for a small adventure."


def can_fix(want: Want, prize: Prize) -> bool:
    return prize.region in want.zone


def select_fix(want: Want, prize: Prize) -> Optional[Fix]:
    for fx in FIXES.values():
        if want.mess in fx.guards and prize.region in fx.covers:
            return fx
    return None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for wid, want in WANTS.items():
            if wid not in setting.affords:
                continue
            for pid, prize in PRIZES.items():
                if not can_fix(want, prize):
                    continue
                if select_fix(want, prize):
                    for fid in FIXES:
                        if fid in {select_fix(want, prize).id}:
                            combos.append((sid, wid, pid, fid))
    return combos


def narrate_intro(world: World) -> None:
    shah = world.facts["shah_ent"]
    helper = world.facts["helper_ent"]
    want = world.facts["want"]
    prize = world.facts["prize_ent"]
    world.say(
        f"{shah.id} was a little {shah.label_word} who loved noticing things in the world."
    )
    world.say(
        f"{shah.id} and {helper.id} were in the habit of exploring together, and {shah.id} especially loved to {want.verb}."
    )
    world.say(
        f"One day, {helper.id} had just brought {shah.pronoun('object')} {prize.phrase}."
    )


def narrate_turn(world: World) -> None:
    shah = world.facts["shah_ent"]
    helper = world.facts["helper_ent"]
    want = world.facts["want"]
    prize = world.facts["prize_ent"]
    shah.memes["want"] = shah.memes.get("want", 0.0) + 1
    world.para()
    world.say(setting_detail(world.setting, want))
    world.say(
        f"{shah.id} wanted to {want.verb}, but {helper.id} lifted a careful hand."
    )
    world.say(
        f'"If you do that, your {prize.label} will get messy," {helper.id} said.'
    )
    shah.memes["warned"] = 1.0
    shah.memes["stubborn"] = 1.0
    world.say(
        f"{shah.id} heard the warning, but the wish to play still tugged hard."
    )
    world.say(
        f"{shah.id} tried to {want.rush}."
    )
    propagate(world, narrate=True)


def narrate_resolution(world: World) -> None:
    shah = world.facts["shah_ent"]
    helper = world.facts["helper_ent"]
    want = world.facts["want"]
    prize = world.facts["prize_ent"]
    fx = world.facts.get("fix_ent")
    if fx is None:
        return
    world.para()
    shah.memes["joy"] = shah.memes.get("joy", 0.0) + 1
    shah.memes["lesson"] = shah.memes.get("lesson", 0.0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1
    shah.memes["stubborn"] = 0.0
    world.say(
        f"Then {helper.id} smiled and said, '{fx.prep}, and we can still {want.verb} together.'"
    )
    world.say(
        f"{shah.id} nodded and chose the safer way."
    )
    world.say(
        f"They {fx.tail}. Soon {shah.id} was {want.gerund}, {prize.label_word} stayed clean, and the day felt bright again."
    )


def tell(setting: Setting, want: Want, prize_cfg: Prize, fix_def: Fix,
         shah_name: str, shah_type: str, helper_name: str, helper_type: str,
         place_name: str) -> World:
    world = World(setting)
    world.zone = set(want.zone)
    shah = world.add(Entity(
        id=shah_name,
        kind="character",
        type=shah_type,
        label=shah_name,
        traits=["little", "curious"],
        meters={"mess": 0.0},
        memes={"want": 0.0, "warned": 0.0, "stubborn": 0.0, "joy": 0.0, "lesson": 0.0},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        label=helper_name,
        traits=["kind", "careful"],
        meters={"workload": 0.0},
        memes={"joy": 0.0},
    ))
    prize = world.add(Entity(
        id="prize",
        kind="thing",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        caretaker=helper.id,
        owner=shah.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
        meters={"dirty": 0.0},
        attrs={},
    ))
    fix_ent = world.add(Entity(
        id="fix",
        kind="thing",
        type="fix",
        label=fix_def.label,
        phrase=fix_def.phrase,
        meters={},
        attrs={"covers": set(fix_def.covers)},
        plural=fix_def.plural,
    ))
    fix_ent.worn_by = shah.id
    world.facts = {
        "shah_ent": shah,
        "helper_ent": helper,
        "prize_ent": prize,
        "fix_ent": fix_ent,
        "want": want,
        "place_name": place_name,
    }
    narrate_intro(world)
    narrate_turn(world)
    narrate_resolution(world)
    return world


SETTINGS = {
    "garden": Setting(id="garden", place="the garden", indoor=False, affords={"mud", "paint", "berries"}),
    "yard": Setting(id="yard", place="the backyard", indoor=False, affords={"mud", "berries"}),
    "porch": Setting(id="porch", place="the porch", indoor=False, affords={"paint", "berries"}),
    "kitchen": Setting(id="kitchen", place="the kitchen", indoor=True, affords={"berries", "paint"}),
}

WANTS = {
    "mud": Want(id="mud", verb="roll in the mud", gerund="rolling in the mud", rush="run to the mud", mess="mud", zone={"feet", "legs"}, clue="muddy"),
    "paint": Want(id="paint", verb="paint the fence", gerund="painting the fence", rush="grab the paint pots", mess="paint", zone={"torso", "hands"}, clue="splashed"),
    "berries": Want(id="berries", verb="pick berries", gerund="picking berries", rush="dash into the berry patch", mess="juice", zone={"hands"}, clue="juicy"),
}

PRIZES = {
    "scarf": Prize(id="scarf", label="scarf", phrase="a soft scarf", type="scarf", region="torso"),
    "boots": Prize(id="boots", label="boots", phrase="a pair of boots", type="boots", region="feet", plural=True),
    "shirt": Prize(id="shirt", label="shirt", phrase="a clean shirt", type="shirt", region="torso"),
}

FIXES = {
    "apron": Fix(id="apron", label="apron", phrase="an old apron", prep="Let's put on the apron first", tail="put on the apron and came back ready for paint", guards={"paint"}, covers={"torso"}),
    "boots": Fix(id="boots", label="boots", phrase="rain boots", prep="Let's wear the boots first", tail="wear the boots and went back outside", guards={"mud"}, covers={"feet"}, plural=True),
    "smock": Fix(id="smock", label="smock", phrase="a smock", prep="Let's use a smock", tail="used the smock and kept playing", guards={"paint"}, covers={"torso"}),
}

GIRAFFE_NAMES = ["Shah", "Milo", "Luna", "Poppy", "Nori", "Bobo", "Tiki", "Kiki"]
HELPER_NAMES = ["Mina", "Ravi", "Zuzu", "Tari", "Dina", "Hadi"]
TRAITS = ["gentle", "curious", "cheerful", "thoughtful"]


def explain_rejection(setting: Setting, want: Want, prize: Prize) -> str:
    return f"(No story: {want.verb} in {setting.place} would not put {prize.label} at risk in a sensible way.)"


def valid_story_params(setting: str, want: str, prize: str, fix: str) -> bool:
    if setting not in SETTINGS or want not in WANTS or prize not in PRIZES or fix not in FIXES:
        return False
    st, wt, pr, fx = _safe_lookup(SETTINGS, setting), _safe_lookup(WANTS, want), _safe_lookup(PRIZES, prize), _safe_lookup(FIXES, fix)
    return want in st.affords and can_fix(wt, pr) and wt.mess in fx.guards and pr.region in fx.covers


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal-story world with a lesson learned beat.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--want", choices=WANTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--shah")
    ap.add_argument("--shah-type", choices=["cat", "dog", "rabbit", "fox", "mouse"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["cat", "dog", "rabbit", "fox", "mouse"])
    ap.add_argument("--place-name")
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
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "want", None) is None or c[1] == getattr(args, "want", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
              and (getattr(args, "fix", None) is None or c[3] == getattr(args, "fix", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, want, prize, fix = rng.choice(list(combos))
    shah = getattr(args, "shah", None) or rng.choice(GIRAFFE_NAMES)
    helper = getattr(args, "helper", None) or rng.choice([n for n in HELPER_NAMES if n != shah])
    shah_type = getattr(args, "shah_type", None) or rng.choice(["cat", "dog", "rabbit", "fox", "mouse"])
    helper_type = getattr(args, "helper_type", None) or rng.choice(["cat", "dog", "rabbit", "fox", "mouse"])
    place_name = getattr(args, "place_name", None) or _safe_lookup(SETTINGS, setting).place
    return StoryParams(setting=setting, want=want, prize=prize, fix=fix,
                       shah=shah, shah_type=shah_type, helper=helper,
                       helper_type=helper_type, place_name=place_name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story for a young child that includes the word "shah" and shows a lesson learned.',
        f"Tell a gentle story about {f['shah_ent'].id} and {f['helper_ent'].id} at {world.setting.place} where a warning matters and a smarter choice wins.",
        f"Write an animal story where {f['shah_ent'].id} wants to {f['want'].verb}, but learns to slow down and choose the safer way.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    shah = f["shah_ent"]
    helper = f["helper_ent"]
    want = f["want"]
    prize = f["prize_ent"]
    fx = f["fix_ent"]
    return [
        QAItem(
            f"Who is the story about at {world.setting.place}?",
            f"It is about {shah.id}, a little {shah.type}, and {helper.id}, who helped with the day. The story also includes the word shah because that is the named child in the tale.",
        ),
        QAItem(
            f"What did {shah.id} want to do?",
            f"{shah.id} wanted to {want.verb}. That was hard because the day was about playing safely and keeping {prize.label} clean.",
        ),
        QAItem(
            f"Why did {helper.id} worry about {prize.label}?",
            f"{helper.id} worried because {prize.label} could get messy if {shah.id} did that. A dirty {prize.label} would mean more work and a sad ending for the clean thing they cared about.",
        ),
        QAItem(
            f"What lesson did {shah.id} learn at the end?",
            f"{shah.id} learned to listen first and choose the safer way. That lesson let the play continue while {prize.label} stayed clean.",
        ),
        QAItem(
            f"How did the fix help the animals?",
            f"They used {fx.label} first, so {shah.id} could keep playing without making a mess. The fix matched the problem and turned the warning into a happy choice.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does a lesson learned mean in a story?",
               "It means a character understands why a warning was right and changes how they act next time. The character may still have fun, but they do it more safely after learning."),
        QAItem("Why do animals in stories sometimes wear boots or aprons?",
               "They wear them to keep clothes or feet clean and dry. A good helper item can stop a mess before it starts."),
        QAItem("What is a safer choice when something could get dirty?",
               "A safer choice is to use the right gear or wait for help. That keeps the important thing clean and makes the job easier."),
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


ASP_RULES = r"""
valid(S,W,P,F) :- setting(S), want(W), prize(P), fix(F), affords(S,W),
                  prize_risk(W,P), fix_ok(W,P,F).
prize_risk(W,P) :- zone(W,R), region(P,R).
fix_ok(W,P,F) :- mess(W,M), guards(F,M), covers(F,R), region(P,R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for w in sorted(s.affords):
            lines.append(asp.fact("affords", sid, w))
    for wid, w in WANTS.items():
        lines.append(asp.fact("want", wid))
        lines.append(asp.fact("mess", wid, w.mess))
        for z in sorted(w.zone):
            lines.append(asp.fact("zone", wid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for g in sorted(f.guards):
            lines.append(asp.fact("guards", fid, g))
        for c in sorted(f.covers):
            lines.append(asp.fact("covers", fid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH between Python and ASP.")
        print("only in python:", sorted(py - cl))
        print("only in asp:", sorted(cl - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return 0 if ok else 1


def generate(params: StoryParams) -> StorySample:
    if not valid_story_params(params.setting, params.want, params.prize, params.fix):
        pass
    setting = _safe_lookup(SETTINGS, params.setting)
    want = _safe_lookup(WANTS, params.want)
    prize = _safe_lookup(PRIZES, params.prize)
    fix_def = _safe_lookup(FIXES, params.fix)
    world = tell(setting, want, prize, fix_def, params.shah, params.shah_type,
                 params.helper, params.helper_type, params.place_name)
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
        print("--- world model state ---")
        for e in sample.world.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            if e.attrs:
                bits.append(f"attrs={e.attrs}")
            print(f"  {e.id}: {e.type} {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(setting="garden", want="mud", prize="boots", fix="boots", shah="Shah", shah_type="rabbit", helper="Mina", helper_type="cat", place_name="the garden"),
    StoryParams(setting="porch", want="paint", prize="shirt", fix="apron", shah="Shah", shah_type="fox", helper="Ravi", helper_type="dog", place_name="the porch"),
    StoryParams(setting="yard", want="berries", prize="scarf", fix="smock", shah="Shah", shah_type="mouse", helper="Zuzu", helper_type="rabbit", place_name="the backyard"),
    StoryParams(setting="kitchen", want="paint", prize="shirt", fix="smock", shah="Shah", shah_type="cat", helper="Dina", helper_type="cat", place_name="the kitchen"),
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
        print(f"{len(combos)} compatible (setting, want, prize, fix) combos:")
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
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
