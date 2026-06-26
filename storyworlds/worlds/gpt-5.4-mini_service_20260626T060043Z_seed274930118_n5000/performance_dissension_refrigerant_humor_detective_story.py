#!/usr/bin/env python3
"""
storyworlds/worlds/performance_dissension_refrigerant_humor_detective_story.py
===============================================================================

A small detective-story world about a performance, a dissension, and a
refrigerant mystery with a humorous turn.

Premise:
- A child detective watches a stage performance in a community hall.
- A cooling machine starts hissing refrigerant, making some people uneasy.
- A small dissension grows when the show is at risk.
- The detective uses humor and careful observation to find the real cause.

The story is state-driven: pressure, chill, fear, and trust shift as the
investigation unfolds. The ending proves what changed: the show continues,
the leak is fixed, and the room relaxes.
"""

from __future__ import annotations

import argparse
import copy
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

HUMOR_THRESHOLD = 1.0
TENSION_THRESHOLD = 1.0
COLD_THRESHOLD = 1.0
CONFUSION_THRESHOLD = 1.0



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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    prob: object | None = None
    room: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    indoor: bool = True
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
class Performance:
    id: str
    label: str
    genre: str
    noise: str
    keyword: str
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
class Problem:
    id: str
    label: str
    smell: str
    chill: str
    danger: str
    keyword: str
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
class Fix:
    id: str
    label: str
    action: str
    effect: str
    helps: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    performance: str
    problem: str
    fix: str
    name: str
    gender: str
    sidekick: str
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
    "hall": Setting(place="the community hall", indoor=True, affords={"show"}),
    "theater": Setting(place="the little theater", indoor=True, affords={"show"}),
    "auditorium": Setting(place="the school auditorium", indoor=True, affords={"show"}),
}

PERFORMANCES = {
    "play": Performance(
        id="play",
        label="a small play",
        genre="play",
        noise="the cast was speaking in loud, dramatic voices",
        keyword="performance",
        tags={"performance", "humor"},
    ),
    "magic": Performance(
        id="magic",
        label="a funny magic show",
        genre="magic show",
        noise="the magician was making the crowd laugh",
        keyword="performance",
        tags={"performance", "humor"},
    ),
    "music": Performance(
        id="music",
        label="a cheerful music performance",
        genre="music performance",
        noise="the instruments were ringing bright and clear",
        keyword="performance",
        tags={"performance"},
    ),
}

PROBLEMS = {
    "leak": Problem(
        id="leak",
        label="a refrigerant leak",
        smell="sharp and chilly",
        chill="cold air",
        danger="the room could get too cold for the show",
        keyword="refrigerant",
        tags={"refrigerant"},
    ),
    "hiss": Problem(
        id="hiss",
        label="a hissing refrigerant canister",
        smell="stingy and frosty",
        chill="a sneaky chill",
        danger="the hissing could distract everyone",
        keyword="refrigerant",
        tags={"refrigerant"},
    ),
}

FIXES = {
    "seal": Fix(
        id="seal",
        label="a rubber seal kit",
        action="seal the leak",
        effect="stopped the hissing",
        helps={"leak", "hiss"},
        tags={"refrigerant"},
    ),
    "vent": Fix(
        id="vent",
        label="a vent hose",
        action="guide the cold air outside",
        effect="made the room steady again",
        helps={"leak", "hiss"},
        tags={"refrigerant"},
    ),
}

GIRL_NAMES = ["Mina", "Tia", "Nora", "Maya", "Lila", "Zoe", "Ava"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Theo", "Ben", "Leo", "Max"]
SIDEKICKS = ["cat", "dog", "parrot", "mouse", "raccoon"]
TRAITS = ["curious", "brave", "clever", "cheerful", "funny", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for perf_id in setting.affords:
            for prob_id, prob in PROBLEMS.items():
                if "refrigerant" not in prob.tags:
                    continue
                for fix_id, fix in FIXES.items():
                    if prob_id in fix.helps:
                        combos.append((place, perf_id, prob_id))
    return combos


def reasonableness_check(performance: Performance, problem: Problem, fix: Fix) -> bool:
    return problem.id in fix.helps and "refrigerant" in problem.tags and "performance" in performance.tags


def explain_rejection(performance: Performance, problem: Problem) -> str:
    return (
        f"(No story: {performance.label} and {problem.label} do not make a usable "
        f"detective problem/fix pair here.)"
    )


def explain_gender(problem_id: str, gender: str) -> str:
    return f"(No story: this world can still use a {problem_id} with a {gender} hero, but the chosen name pool must match.)"


def _suspense(world: World, hero: Entity, problem: Problem) -> list[str]:
    out = []
    if hero.meters.get("tension", 0.0) >= TENSION_THRESHOLD:
        sig = ("tension", hero.id, problem.id)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append(f"{hero.pronoun('subject').capitalize()} felt the case tighten like a knot.")
    return out


def _leak_cold(world: World) -> list[str]:
    out = []
    hall = world.entities.get("room")
    leak = world.entities.get("problem")
    if not hall or not leak:
        return out
    if leak.meters.get("active", 0.0) >= 1.0:
        sig = ("cold",)
        if sig not in world.fired:
            world.fired.add(sig)
            hall.meters["cold"] = hall.meters.get("cold", 0.0) + 1.0
            out.append("A chilly breath rolled across the room.")
    return out


def _dissension(world: World, hero: Entity, bystanders: list[Entity]) -> list[str]:
    out = []
    if hero.memes.get("humor", 0.0) < HUMOR_THRESHOLD:
        return out
    if hero.meters.get("tension", 0.0) < TENSION_THRESHOLD:
        return out
    sig = ("dissension", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["dissension"] = hero.memes.get("dissension", 0.0) + 1.0
    for b in bystanders:
        b.memes["unease"] = b.memes.get("unease", 0.0) + 1.0
    out.append("People started disagreeing in whispers about whether the show could go on.")
    return out


CAUSAL_RULES = []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    produced.extend(_leak_cold(world))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def introduce(world: World, hero: Entity, sidekick: Entity) -> None:
    world.say(
        f"{hero.id} was a little {next((t for t in hero.traits if t != 'little'), 'curious')} detective, "
        f"and {hero.pronoun('subject')} liked noticing tiny clues."
    )
    world.say(
        f"{hero.id} brought {hero.pronoun('possessive')} {sidekick.label} friend, {sidekick.id}, "
        f"who always made serious things feel a little funnier."
    )


def set_scene(world: World, performance: Performance) -> None:
    world.say(
        f"That evening, {world.setting.place} was full of seats, bright curtains, and a {performance.label}."
    )
    world.say(performance.noise.capitalize() + ".")


def trouble_starts(world: World, hero: Entity, performance: Performance, problem: Problem) -> None:
    hero.meters["tension"] = hero.meters.get("tension", 0.0) + 1.0
    hero.memes["humor"] = hero.memes.get("humor", 0.0) + 1.0
    world.say(
        f"Then {problem.label} drifted in from behind the curtain, and the air felt {problem.smell}."
    )
    world.say(
        f"{problem.danger.capitalize()}, and that was enough to start a little dissension among the grown-ups."
    )


def investigate(world: World, hero: Entity, problem: Problem, sidekick: Entity) -> None:
    world.say(
        f"{hero.id} squinted at the old cooling machine, then at a floor vent, then at a bent tube behind it."
    )
    world.say(
        f"{hero.id} whispered, \"This case smells like refrigerant.\" {sidekick.id} sneezed, as if agreeing."
    )
    hero.memes["humor"] = hero.memes.get("humor", 0.0) + 1.0
    hero.meters["clue"] = hero.meters.get("clue", 0.0) + 1.0
    propagate(world, narrate=True)


def joke_to_calm(world: World, hero: Entity, bystanders: list[Entity]) -> None:
    world.say(
        f"{hero.id} pointed at the twitchy machine and said, \"I knew it was suspicious. It has cold feet and a guilty hiss.\""
    )
    for b in bystanders:
        b.memes["relief"] = b.memes.get("relief", 0.0) + 1.0
    world.say("A few people chuckled, and the room stopped feeling quite so sharp.")


def fix_problem(world: World, hero: Entity, problem: Problem, fix: Fix) -> None:
    world.say(
        f"{hero.id} asked for {fix.label}, and carefully used it to {fix.action}."
    )
    world.say(fix.effect.capitalize() + ".")
    prob_ent = world.entities["problem"]
    prob_ent.meters["active"] = 0.0
    hall = world.entities["room"]
    hall.meters["cold"] = 0.0
    hero.meters["tension"] = 0.0
    hero.memes["dissension"] = 0.0
    hero.memes["humor"] = hero.memes.get("humor", 0.0) + 1.0


def ending(world: World, hero: Entity, performance: Performance) -> None:
    world.say(
        f"After that, the performance went on, the crowd smiled, and {hero.id} watched the final scene with a proud grin."
    )
    world.say(
        f"The room stayed warm enough, the refrigerant stayed where it belonged, and the detective case was closed with a laugh."
    )


def tell(
    setting: Setting,
    performance: Performance,
    problem: Problem,
    fix: Fix,
    hero_name: str = "Mina",
    hero_type: str = "girl",
    sidekick_kind: str = "cat",
) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            traits=["little", "curious", "funny"],
        )
    )
    sidekick = world.add(
        Entity(id="Sidekick", kind="character", type=sidekick_kind, label=sidekick_kind)
    )
    room = world.add(Entity(id="room", type="room", label=setting.place))
    prob = world.add(Entity(id="problem", type=problem.id, label=problem.label))
    prob.meters["active"] = 1.0
    room.meters["cold"] = 0.0

    world.facts["hero"] = hero
    world.facts["sidekick"] = sidekick
    world.facts["performance"] = performance
    world.facts["problem"] = problem
    world.facts["fix"] = fix
    world.facts["room"] = room

    introduce(world, hero, sidekick)
    world.para()
    set_scene(world, performance)
    trouble_starts(world, hero, performance, problem)
    investigate(world, hero, problem, sidekick)
    joke_to_calm(world, hero, [sidekick])
    world.para()
    fix_problem(world, hero, problem, fix)
    ending(world, hero, performance)
    return world


KNOWLEDGE = {
    "performance": [
        (
            "What is a performance?",
            "A performance is a show where people act, sing, play music, or do something for an audience.",
        )
    ],
    "refrigerant": [
        (
            "What is refrigerant?",
            "Refrigerant is a special cooling liquid used in machines like air conditioners and some freezers.",
        )
    ],
    "humor": [
        (
            "What is humor?",
            "Humor is the part of a story or joke that makes people smile or laugh.",
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks carefully for clues and tries to solve a mystery.",
        )
    ],
}

KNOWLEDGE_ORDER = ["detective", "performance", "refrigerant", "humor"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    performance = _safe_fact(world, f, "performance")
    problem = _safe_fact(world, f, "problem")
    return [
        f'Write a child-friendly detective story with a {performance.label} and a {problem.label}.',
        f"Tell a humorous mystery about {hero.id}, who solves a refrigerant problem at {world.setting.place}.",
        f"Write a short story where a detective notices a cooling machine trouble during a performance.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    sidekick = _safe_fact(world, f, "sidekick")
    performance = _safe_fact(world, f, "performance")
    problem = _safe_fact(world, f, "problem")
    fix = _safe_fact(world, f, "fix")
    qa = [
        QAItem(
            question=f"Who is the detective in the story?",
            answer=f"The detective is {hero.id}, a little {next((t for t in hero.traits if t != 'little'), 'curious')} child who notices clues carefully.",
        ),
        QAItem(
            question=f"What kind of show was happening at {world.setting.place}?",
            answer=f"It was {performance.label}, and the audience was there to watch the performance.",
        ),
        QAItem(
            question=f"What problem made the room feel chilly?",
            answer=f"The room had {problem.label}, which brought a sharp, cold feeling and caused a little dissension.",
        ),
        QAItem(
            question=f"How was the problem fixed?",
            answer=f"{hero.id} used {fix.label} to {fix.action}, and that stopped the problem from bothering the show.",
        ),
    ]
    if hero.memes.get("humor", 0.0) >= HUMOR_THRESHOLD:
        qa.append(
            QAItem(
                question=f"How did humor help the detective?",
                answer=f"{hero.id}'s funny line helped the crowd relax, so the dissension cooled down and everyone could keep listening.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["performance"].id, world.facts["problem"].id, "humor", "detective"}
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hall", performance="play", problem="leak", fix="seal", name="Mina", gender="girl", sidekick="cat"),
    StoryParams(place="theater", performance="magic", problem="hiss", fix="vent", name="Eli", gender="boy", sidekick="dog"),
    StoryParams(place="auditorium", performance="music", problem="leak", fix="vent", name="Nora", gender="girl", sidekick="parrot"),
]


def valid_story_combo(place: str, performance: str, problem: str, fix: str) -> bool:
    return reasonableness_check(_safe_lookup(PERFORMANCES, performance), _safe_lookup(PROBLEMS, problem), _safe_lookup(FIXES, fix)) and place in SETTINGS


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PERFORMANCES.items():
        lines.append(asp.fact("performance", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("tagged", pid, t))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("tagged_problem", pid, t))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for p in sorted(f.helps):
            lines.append(asp.fact("helps", fid, p))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Perf, Prob, Fix) :- setting(Place), affords(Place, show), performance(Perf), problem(Prob), fix(Fix),
                                 tagged(Perf, performance), tagged_problem(Prob, refrigerant), helps(Fix, Prob).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, perf, prob, fix) for p, perf, prob, fix in (
        (p, perf, prob, fx)
        for p in SETTINGS
        for perf in PERFORMANCES
        for prob in PROBLEMS
        for fx in FIXES
    ) if valid_story_combo(p, perf, prob, fix)}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_story combos ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python validity:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A humorous detective story world about a performance and a refrigerant mystery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--performance", choices=PERFORMANCES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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
    if getattr(args, "performance", None) and getattr(args, "problem", None) and getattr(args, "fix", None):
        if not reasonableness_check(_safe_lookup(PERFORMANCES, getattr(args, "performance", None)), _safe_lookup(PROBLEMS, getattr(args, "problem", None)), _safe_lookup(FIXES, getattr(args, "fix", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "performance", None) is None or c[1] == getattr(args, "performance", None))
        and (getattr(args, "problem", None) is None or c[2] == getattr(args, "problem", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, perf, prob = rng.choice(list(combos))
    fix = getattr(args, "fix", None) or rng.choice([fid for fid, f in FIXES.items() if prob in f.helps])
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    sidekick = getattr(args, "sidekick", None) or rng.choice(SIDEKICKS)
    return StoryParams(place=place, performance=perf, problem=prob, fix=fix, name=name, gender=gender, sidekick=sidekick)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(PERFORMANCES, params.performance),
        _safe_lookup(PROBLEMS, params.problem),
        _safe_lookup(FIXES, params.fix),
        hero_name=params.name,
        hero_type=params.gender,
        sidekick_kind=params.sidekick,
    )
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
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid/4."))
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
            header = f"### {p.name}: {p.performance} at {p.place} (problem: {p.problem})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
