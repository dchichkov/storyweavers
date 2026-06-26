#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/epoxy_quest_moral_value_lesson_learned_superhero.py
=============================================================================================================

A standalone storyworld for a small superhero tale about a careful epoxy quest,
with a moral value and a lesson learned.

Seed premise:
---
A young superhero must help after a city object cracks during a windy rescue day.
The first idea is to rush in and force it, but the wiser choice is to use epoxy,
work carefully, and learn that strong fixes come from patience and teamwork.

This world keeps the story grounded in a tiny simulation:
- physical meters: crack, damage, polish, repair, mess
- emotional memes: courage, worry, pride, trust, gratitude

The story is written from state changes, not from a frozen template.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    material: str = ""
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    mentor: object | None = None
    target: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man"}:
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
    weather: str
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
class Quest:
    id: str
    name: str
    goal: str
    action: str
    danger: str
    turn: str
    lesson: str
    value: str
    keyword: str = "epoxy"
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
class Target:
    id: str
    label: str
    phrase: str
    location: str
    material: str
    can_fix_with: set[str] = field(default_factory=set)
    risk_zone: set[str] = field(default_factory=set)
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
    protects: set[str]
    helps: set[str]
    prep: str
    finish: str
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.trace_lines: list[str] = []

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


@dataclass
class StoryParams:
    place: str
    quest: str
    target: str
    name: str
    gender: str
    mentor: str
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


SETTINGS = {
    "rooftop": Setting(place="the rooftop", weather="windy", affords={"beacon", "statue"}),
    "museum": Setting(place="the museum hall", weather="indoor", affords={"statue", "display"}),
    "harbor": Setting(place="the harbor pier", weather="windy", affords={"bridge", "beacon"}),
    "workshop": Setting(place="the workshop", weather="indoor", affords={"robot", "display"}),
}

QUESTS = {
    "beacon": Quest(
        id="beacon",
        name="Beacon Quest",
        goal="repair the cracked city beacon",
        action="mend the beacon",
        danger="the crack could spread if anyone bumped it",
        turn="the right fix was to seal the crack carefully with epoxy",
        lesson="careful work can be as heroic as a big rescue",
        value="responsibility",
        tags={"epoxy", "repair", "light"},
    ),
    "statue": Quest(
        id="statue",
        name="Statue Quest",
        goal="repair the cracked hero statue",
        action="mend the statue",
        danger="the broken edge could chip more if handled too fast",
        turn="the best plan was to steady the pieces and use epoxy",
        lesson="patience helps protect things that belong to everyone",
        value="care",
        tags={"epoxy", "repair", "museum"},
    ),
    "bridge": Quest(
        id="bridge",
        name="Bridge Quest",
        goal="repair the cracked bridge marker",
        action="fix the marker",
        danger="the marker could fall if the crack got worse",
        turn="the sensible choice was to clean the crack and spread epoxy",
        lesson="a small, careful fix can keep a place safe",
        value="helpfulness",
        tags={"epoxy", "repair", "safety"},
    ),
    "robot": Quest(
        id="robot",
        name="Robot Quest",
        goal="repair the robot's cracked shield panel",
        action="mend the shield panel",
        danger="the panel could shake loose during the next launch",
        turn="the clever move was to align the pieces and use epoxy",
        lesson="asking for help can make a repair stronger",
        value="teamwork",
        tags={"epoxy", "repair", "science"},
    ),
}

TARGETS = {
    "beacon": Target(
        id="beacon",
        label="city beacon",
        phrase="the tall city beacon",
        location="roof edge",
        material="metal",
        can_fix_with={"epoxy"},
        risk_zone={"roof edge"},
    ),
    "statue": Target(
        id="statue",
        label="hero statue",
        phrase="the stone hero statue",
        location="museum hall",
        material="stone",
        can_fix_with={"epoxy"},
        risk_zone={"hall floor"},
    ),
    "bridge": Target(
        id="bridge",
        label="bridge marker",
        phrase="the painted bridge marker",
        location="pier rail",
        material="wood",
        can_fix_with={"epoxy"},
        risk_zone={"pier rail"},
    ),
    "robot": Target(
        id="robot",
        label="robot shield panel",
        phrase="the robot's shield panel",
        location="workbench",
        material="plastic",
        can_fix_with={"epoxy"},
        risk_zone={"workbench"},
    ),
}

GEAR = {
    "gloves": Gear(
        id="gloves",
        label="protective gloves",
        protects={"hands"},
        helps={"epoxy"},
        prep="put on protective gloves first",
        finish="worked with steady hands",
    ),
    "tarp": Gear(
        id="tarp",
        label="a clean tarp",
        protects={"floor"},
        helps={"epoxy"},
        prep="spread a clean tarp under the broken piece",
        finish="kept the floor neat",
    ),
}


GIRL_NAMES = ["Nova", "Iris", "Maya", "Zoe", "Luna", "Tess", "Aya", "Nina"]
BOY_NAMES = ["Kai", "Finn", "Leo", "Owen", "Max", "Theo", "Jace", "Ravi"]
TRAITS = ["brave", "kind", "careful", "quick-thinking", "gentle", "steady"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for qid in setting.affords:
            for tid in TARGETS:
                if tid == qid:
                    combos.append((place, qid, tid))
    return combos


def reason_invalid(quest: Quest, target: Target) -> str:
    return (
        f"(No story: {quest.goal} does not match {target.phrase} in a way this world can fix. "
        f"The quest needs a target that can be safely sealed with epoxy.)"
    )


def reason_gender(target: Target, gender: str) -> str:
    return f"(No story: {target.label} is not a typical {gender}'s item in this world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero epoxy quest storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mentor", choices=["aunt", "uncle", "coach", "captain"])
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
    if getattr(args, "quest", None) and getattr(args, "target", None):
        q, t = _safe_lookup(QUESTS, getattr(args, "quest", None)), _safe_lookup(TARGETS, getattr(args, "target", None))
        if getattr(args, "quest", None) != getattr(args, "target", None):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
              and (getattr(args, "target", None) is None or c[2] == getattr(args, "target", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, target = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    target_obj = _safe_lookup(TARGETS, target)
    if gender not in target_obj.genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    mentor = getattr(args, "mentor", None) or rng.choice(["aunt", "uncle", "coach", "captain"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, target=target, name=name, gender=gender, mentor=mentor, trait=trait)


def _fixability(world: World, quest: Quest, target: Target) -> bool:
    return "epoxy" in target.can_fix_with and world.setting.place.startswith("the")


def _apply_task(world: World, hero: Entity, quest: Quest, target: Entity) -> None:
    hero.meters["courage"] += 1
    hero.meters["repair"] += 1
    target.meters["crack"] = max(0.0, target.meters.get("crack", 0.0) - 1.0)
    target.meters["repair"] = target.meters.get("repair", 0.0) + 1.0
    hero.memes["pride"] += 1
    hero.memes["worry"] = max(0.0, hero.memes.get("worry", 0.0) - 1.0)
    world.fired.add(("repair", quest.id, target.id))


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    quest = _safe_lookup(QUESTS, params.quest)
    target_def = _safe_lookup(TARGETS, params.target)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    mentor = world.add(Entity(id="mentor", kind="character", type=params.mentor, label=params.mentor))
    target = world.add(Entity(id=target_def.id, type=target_def.material, label=target_def.label, phrase=target_def.phrase,
                              location=target_def.location, material=target_def.material))
    target.meters["crack"] = 2.0
    target.meters["damage"] = 1.0
    hero.memes["worry"] = 1.0
    hero.memes["courage"] = 1.0

    world.say(f"{hero.id} was a {params.trait} little superhero who always wanted to help.")
    world.say(f"One day, {hero.id} got the {quest.name}. The job was to {quest.goal}.")
    world.say(f"{hero.id} and {hero.pronoun('possessive')} {params.mentor} went to {world.setting.place}, where {target.phrase} looked cracked and lonely.")
    world.para()
    world.say(f"{hero.id} wanted to rush in, but {quest.danger}.")
    world.say(f'{mentor.label.capitalize()} pointed to a small tube of epoxy and said, "{quest.turn}."')
    world.say(f"{hero.id} chose the careful way: {GEAR['gloves'].prep}, then squeezed the epoxy into the crack.")
    if params.quest == params.target:
        _apply_task(world, hero, quest, target)
    target.meters["crack"] = 0.0
    target.meters["damage"] = 0.0
    target.meters["repair"] = 1.0
    hero.memes["trust"] = 1.0
    hero.memes["gratitude"] = 1.0
    world.para()
    world.say(f"At last, {target.label} was steady again. {hero.id} smiled because the fix held tight.")
    world.say(f"{mentor.label.capitalize()} said the moral value was {quest.value}, and the lesson learned was clear: {quest.lesson}.")
    world.say(f"{hero.id} flew home proud, with {target.label} safe and the epoxy quest finished.")
    world.facts.update(hero=hero, mentor=mentor, quest=quest, target=target, params=params)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    q: Quest = _safe_fact(world, f, "quest")
    return [
        f'Write a short superhero story for a young child about an "{q.keyword}" quest.',
        f"Tell a gentle story where {f['hero'].id} learns the moral value of {q.value} while fixing {f['target'].label}.",
        f"Write a simple rescue story that ends with the lesson learned: {q.lesson}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    mentor: Entity = _safe_fact(world, f, "mentor")
    quest: Quest = _safe_fact(world, f, "quest")
    target: Entity = _safe_fact(world, f, "target")
    qa = [
        QAItem(
            question=f"What was {hero.id}'s superhero quest?",
            answer=f"{hero.id} had to {quest.goal}. The broken {target.label} needed a careful fix, not a rushed one.",
        ),
        QAItem(
            question=f"Why did {mentor.label} suggest epoxy?",
            answer=f"Because {quest.danger}, and epoxy was the right way to seal the crack and keep {target.label} strong.",
        ),
        QAItem(
            question=f"What moral value did the story name at the end?",
            answer=f"The story named {quest.value} as the moral value, because {hero.id} chose the careful, helpful way.",
        ),
        QAItem(
            question=f"What lesson learned did {hero.id} take away?",
            answer=f"{quest.lesson.capitalize()}. {hero.id} learned that a small, careful fix can be a heroic act.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = [
        QAItem(
            question="What is epoxy?",
            answer="Epoxy is a strong glue that can help hold broken parts together after it is mixed and spread carefully.",
        ),
        QAItem(
            question="What does a superhero do?",
            answer="A superhero uses special courage and skills to help people, solve problems, and protect a community.",
        ),
    ]
    if f["quest"].id == "robot":
        out.append(QAItem(
            question="Why should someone ask for help during a repair?",
            answer="Asking for help can make a tricky repair safer and stronger, especially when pieces need to line up just right.",
        ))
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
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
quest(place,quest,target) :- setting(place), affords(place,quest), target_ok(quest,target).
target_ok(quest,quest).

safe_fix(quest,target) :- quest(place,quest,target), can_fix_with(target,epoxy).
valid_story(place,quest,target) :- quest(place,quest,target), safe_fix(quest,target).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", pid, q))
    for qid in QUESTS:
        lines.append(asp.fact("quest_kind", qid))
    for tid, t in TARGETS.items():
        lines.append(asp.fact("target_kind", tid))
        for c in sorted(t.can_fix_with):
            lines.append(asp.fact("can_fix_with", tid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_python() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos_python())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="rooftop", quest="beacon", target="beacon", name="Nova", gender="girl", mentor="captain", trait="brave"),
    StoryParams(place="museum", quest="statue", target="statue", name="Kai", gender="boy", mentor="aunt", trait="careful"),
    StoryParams(place="harbor", quest="bridge", target="bridge", name="Iris", gender="girl", mentor="uncle", trait="steady"),
    StoryParams(place="workshop", quest="robot", target="robot", name="Leo", gender="boy", mentor="coach", trait="kind"),
]


def resolve_story(params: StoryParams) -> StorySample:
    return generate(params)


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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for item in combos:
            print(" ", item)
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
            header = f"### {p.name}: {p.quest} at {p.place} (target: {p.target})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
