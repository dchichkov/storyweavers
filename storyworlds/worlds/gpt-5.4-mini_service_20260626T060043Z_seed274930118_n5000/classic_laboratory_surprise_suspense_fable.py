#!/usr/bin/env python3
"""
classic_laboratory_surprise_suspense_fable.py
=============================================

A small, self-contained story world about a classic laboratory, a careful
experiment, and a surprising turn that resolves with a fable-like lesson.

Premise:
- A young helper in a classic laboratory is preparing a simple experiment.
- The helper is curious, but also impatient.
- A suspenseful wait builds around what the experiment will become.
- A surprising result changes what everyone expected.
- The ending teaches a gentle lesson about patience, care, and paying attention.

This script follows the Storyweavers world contract:
- typed entities with meters and memes
- a reasonableness gate in Python
- an inline ASP twin
- story + QA + trace + JSON emission
- deterministic generation with seed support
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    hero: object | None = None
    hint: object | None = None
    mentor: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "fox", "hen", "mother", "maiden"}
        male = {"boy", "owl", "bear", "father", "farmer"}
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
    indoors: bool
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
class Trial:
    id: str
    goal: str
    wait: str
    reveal: str
    surprise: str
    suspense: str
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
    trait: str
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
class Hint:
    id: str
    label: str
    reveal: str
    helps: set[str]
    covers: set[str] = field(default_factory=set)
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
        self.facts: dict = {}
        self.phase: str = "setup"

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.phase = self.phase
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


def _r_pressure(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["waiting"] < THRESHOLD:
            continue
        if actor.meters["pressure"] >= THRESHOLD:
            continue
        sig = ("pressure", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["nervous"] += 1
        out.append(f"{actor.id} kept glancing at the little glass and felt the suspense grow.")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["jostle"] < THRESHOLD:
            continue
        for item in list(world.entities.values()):
            if item.caretaker != actor.id or item.meters["fragile"] < THRESHOLD:
                continue
            sig = ("spill", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["tipped"] += 1
            out.append(f"The tray wobbled, and {item.label} trembled on the bench.")
    return out


def _r_discover(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["observed"] < THRESHOLD:
            continue
        if actor.memes["surprise"] >= THRESHOLD:
            continue
        sig = ("discover", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["surprise"] += 1
        out.append(f"{actor.id} saw the answer at last, and the answer was not what anyone had guessed.")
    return out


CAUSAL_RULES = [
    Rule("pressure", "social", _r_pressure),
    Rule("spill", "physical", _r_spill),
    Rule("discover", "social", _r_discover),
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


def predict_outcome(world: World, actor: Entity, trial: Trial, prize_id: str) -> dict:
    sim = world.copy()
    perform_trial(sim, sim.get(actor.id), trial, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "revealed": bool(prize and prize.meters["revealed"] >= THRESHOLD),
        "surprise": sum(e.memes["surprise"] for e in sim.characters()),
    }


def perform_trial(world: World, actor: Entity, trial: Trial, narrate: bool = True) -> None:
    actor.meters["pressure"] += 1
    actor.memes["waiting"] += 1
    actor.meters["observed"] += 1
    actor.meters["jostle"] += 0.5
    propagate(world, narrate=narrate)


def choose_hint(trial: Trial, prize: Prize) -> Optional[Hint]:
    for hint in HINTS:
        if trial.id in hint.helps and prize.trait in hint.covers:
            return hint
    return None


def setting_line(setting: Setting) -> str:
    if setting.indoors:
        return f"The {setting.place} was quiet, and old bottles winked in the lamplight."
    return f"{setting.place.capitalize()} stood still, as if even the birds were listening."


SETTINGS = {
    "laboratory": Setting(place="the classic laboratory", indoors=True, affords={"mix", "wait", "reveal"}),
    "greenhouse": Setting(place="the glass greenhouse", indoors=True, affords={"wait", "reveal"}),
    "workbench": Setting(place="the old workbench room", indoors=True, affords={"mix", "wait"}),
}

TRIALS = {
    "mixing": Trial(
        id="mixing",
        goal="mix a careful potion",
        wait="wait for the steam to settle",
        reveal="watch the cork pop up",
        surprise="the cork leaps high",
        suspense="the beaker keeps humming",
        keyword="bubble",
        tags={"classic", "laboratory", "suspense"},
    ),
    "glow": Trial(
        id="glow",
        goal="wake a sleepy lantern",
        wait="wait for the glow to wake",
        reveal="see the jar shine",
        surprise="the jar shines blue",
        suspense="the jar keeps blinking",
        keyword="glow",
        tags={"classic", "laboratory", "surprise"},
    ),
    "seed": Trial(
        id="seed",
        goal="sprout a tiny seed",
        wait="wait for the soil to stir",
        reveal="find a green curl",
        surprise="a tiny leaf appears",
        suspense="the pot keeps breathing",
        keyword="seed",
        tags={"fable", "laboratory", "suspense"},
    ),
}

PRIZES = {
    "clock": Prize(label="clock", phrase="a brass clock", type="clock", trait="metal"),
    "jar": Prize(label="jar", phrase="a glass jar", type="jar", trait="glass"),
    "seedpot": Prize(label="pot", phrase="a little seed pot", type="pot", trait="soil"),
}

HINTS = [
    Hint(id="cloth", label="a soft cloth", reveal="lift the lid gently", helps={"mixing", "glow"}, covers={"metal", "glass"}),
    Hint(id="tongs", label="wooden tongs", reveal="move the warm jar carefully", helps={"glow"}, covers={"glass"}),
    Hint(id="shade", label="a paper shade", reveal="block the lamp for a moment", helps={"mixing", "seed"}, covers={"soil", "glass"}),
]

NAMES = ["Mina", "Toby", "Pip", "Nell", "Otto", "Wren", "Pru", "Bram"]
TYPES = ["fox", "owl", "mouse", "bear", "hen", "badger"]
TRAITS = ["careful", "curious", "patient", "brave", "gentle", "quick"]


@dataclass
class StoryParams:
    setting: str
    trial: str
    prize: str
    name: str
    type: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s, setting in SETTINGS.items():
        for t, trial in TRIALS.items():
            for p, prize in PRIZES.items():
                if setting.indoors and (trial.id == "seed" and p == "clock"):
                    continue
                if trial.id in {"mixing", "glow", "seed"}:
                    out.append((s, t, p))
    return out


def reason_invalid(trial: Trial, prize: Prize) -> str:
    return f"(No story: a {trial.goal} does not fit well with {prize.phrase} in this fable world.)"


def tell(setting: Setting, trial: Trial, prize_cfg: Prize, name: str, kind: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=kind, traits=["little", trait]))
    mentor = world.add(Entity(id="Mentor", kind="character", type="owl", label="the owl mentor"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=mentor.id
    ))
    hint = world.add(Entity(id="hint", type="thing", label="the hint", caretaker=mentor.id))
    hint.meters["ready"] = 1
    prize.meters["fragile"] = 1

    world.say(f"{hero.id} was a little {trait} {kind} who loved the old ways of the classic laboratory.")
    world.say(f"{hero.pronoun().capitalize()} and {mentor.label} kept the lamps clean and the jars in a straight row.")
    world.say(f"One day they wanted to {trial.goal}, and {hero.id} hoped the result would be wise and bright.")

    world.para()
    world.say(setting_line(setting))
    world.say(f"{hero.id} began to {trial.wait}, but {trial.suspense} and made the room feel hushed.")
    hero.memes["waiting"] += 1
    hero.meters["observed"] += 1

    pred = predict_outcome(world, hero, trial, prize.id)
    if pred["surprise"]:
        world.facts["predicted_surprise"] = pred["surprise"]

    world.say(f"{mentor.label} said, \"{trial.suspense.capitalize()}, and a careful heart can hear it.\"")
    world.say(f"{hero.id} almost rushed, but then {hero.pronoun('possessive')} eyes found the {prize.label} on the bench.")

    world.para()
    world.say(f"{hero.id} reached for the {prize.label} and tried to {trial.reveal}.")
    hero.meters["jostle"] += 1
    hero.meters["observed"] += 1
    propagate(world, narrate=True)

    if pred["revealed"]:
        prize.meters["revealed"] += 1
    if trial.id == "mixing":
        prize.meters["revealed"] += 1
    if trial.id == "glow":
        prize.meters["revealed"] += 1
    if trial.id == "seed":
        prize.meters["revealed"] += 1

    hint_def = choose_hint(trial, prize)
    if hint_def:
        world.say(f"{mentor.label} passed over {hint_def.label} and showed {hero.id} how to move more gently.")
        world.say(f"With {hint_def.label}, {hero.id} could finish without upsetting the careful setup.")

    world.para()
    hero.memes["surprise"] += 1
    if trial.id == "mixing":
        world.say(f"Then the beaker gave a bright pop, and instead of a mess, a tiny ribbon of light rose from it.")
        world.say(f"{hero.id} laughed in astonishment, because the {prize.label} stayed safe and the experiment came alive.")
    elif trial.id == "glow":
        world.say(f"Then the jar shone blue, not from a trick, but from a gentle glow hidden in the dust.")
        world.say(f"{hero.id} stared, wide-eyed, and the {prize.label} looked ordinary until it suddenly looked magical.")
    else:
        world.say(f"Then a green curl poked from the soil, small as a mouse ear and just as brave.")
        world.say(f"{hero.id} smiled at the surprise, because even the quietest seed had been working all along.")

    world.say(f"In the end, {hero.id} learned that a patient hand often finds the most surprising answer.")
    world.facts.update(hero=hero, mentor=mentor, prize=prize, setting=setting, trial=trial, hint=hint_def)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    trial = _safe_fact(world, f, "trial")
    prize = _safe_fact(world, f, "prize")
    return [
        f"Write a short fable about a {hero.type} named {hero.id} in a classic laboratory who waits for {trial.goal}.",
        f"Tell a gentle surprise story where {hero.id} watches a {prize.label} during {trial.goal} and learns patience.",
        f"Write a child-friendly story with suspense, a laboratory, and a surprising ending that teaches care.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mentor, prize, trial = f["hero"], f["mentor"], f["prize"], f["trial"]
    return [
        QAItem(
            question=f"Who was the story about in the classic laboratory?",
            answer=f"It was about {hero.id}, a little {hero.traits[-1]} {hero.type}, and {mentor.label}, who helped keep the lab careful and calm.",
        ),
        QAItem(
            question=f"What was {hero.id} trying to do?",
            answer=f"{hero.id} was trying to {trial.goal}, and {hero.id} had to wait for the answer to appear.",
        ),
        QAItem(
            question=f"What did {hero.id} watch closely during the experiment?",
            answer=f"{hero.id} watched {prize.phrase} closely, because it was part of the experiment and could have been damaged if the work became careless.",
        ),
        QAItem(
            question=f"What made the middle of the story suspenseful?",
            answer=f"The suspense came from waiting for {trial.suspense}, so everyone had to be patient before the result appeared.",
        ),
        QAItem(
            question=f"What surprising thing happened at the end?",
            answer=(
                "The result was surprising: instead of an ordinary ending, the experiment turned into something bright and special, "
                "and that surprise showed why patience mattered."
            ),
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that a patient hand often finds the most surprising answer, especially in a careful laboratory.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a laboratory?",
            answer="A laboratory is a place where people carefully do experiments, mix things, and watch for results.",
        ),
        QAItem(
            question="What does suspense mean?",
            answer="Suspense is the feeling of waiting to find out what will happen next.",
        ),
        QAItem(
            question="What does surprise mean?",
            answer="A surprise is something unexpected that makes you stop and look again.",
        ),
        QAItem(
            question="Why do careful helpers move slowly around fragile things?",
            answer="Careful helpers move slowly so fragile things do not tip, crack, or spill.",
        ),
    ]


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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
% Reasonable stories exist when the setting hosts the trial.
valid_story(S, T, P) :- setting(S), trial(T), prize(P), affords(S, T).

% A setup is suspenseful when waiting and observation are both present.
suspenseful(H) :- waiting(H), observed(H).

% A surprise happens when the reveal becomes true.
surprising(P) :- revealed(P).

% A gentle resolution is possible when a hint matches the trial and prize trait.
helpful(HI, T, P) :- hint(HI), helps(HI, T), covers(HI, X), prize_trait(P, X).

valid(S, T, P) :- valid_story(S, T, P), helpful(_, T, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TRIALS.items():
        lines.append(asp.fact("trial", tid))
        lines.append(asp.fact("trial_goal", tid, t.goal))
        lines.append(asp.fact("trial_tag", tid, "suspense"))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_trait", pid, p.trait))
    for h in HINTS:
        lines.append(asp.fact("hint", h.id))
        for t in sorted(h.helps):
            lines.append(asp.fact("helps", h.id, t))
        for c in sorted(h.covers):
            lines.append(asp.fact("covers", h.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(setting="laboratory", trial="mixing", prize="jar", name="Mina", type="mouse", trait="curious"),
    StoryParams(setting="laboratory", trial="glow", prize="clock", name="Pip", type="fox", trait="careful"),
    StoryParams(setting="greenhouse", trial="seed", prize="seedpot", name="Nell", type="hen", trait="patient"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A classic laboratory fable with surprise and suspense.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trial", choices=TRIALS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--type", choices=TYPES)
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
    if getattr(args, "trial", None) and getattr(args, "prize", None):
        trial = _safe_lookup(TRIALS, getattr(args, "trial", None))
        prize = _safe_lookup(PRIZES, getattr(args, "prize", None))
        if getattr(args, "trial", None) == "seed" and getattr(args, "prize", None) == "clock":
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "trial", None) is None or c[1] == getattr(args, "trial", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, trial, prize = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    kind = getattr(args, "type", None) or rng.choice(TYPES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, trial=trial, prize=prize, name=name, type=kind, trait=trait)


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, t, p) for s in SETTINGS for t in TRIALS for p in PRIZES]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(TRIALS, params.trial), _safe_lookup(PRIZES, params.prize),
                 params.name, params.type, params.trait)
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
        print(asp_program("#show valid/3.\n#show valid_story/3.\n"))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, trial, prize) combos:\n")
        for s, t, p in combos:
            print(f"  {s:12} {t:8} {p:8}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
            header = f"### {p.name}: {p.trial} in {p.setting} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
