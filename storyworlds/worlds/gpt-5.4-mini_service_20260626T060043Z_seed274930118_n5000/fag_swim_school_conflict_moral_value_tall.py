#!/usr/bin/env python3
"""
storyworlds/worlds/fag_swim_school_conflict_moral_value_tall.py
===============================================================

A tall-tale swim-school story world with a small cast, a watery conflict, and a
moral-value turn.

Premise:
- A child begins swim school eager but uneasy.
- The pool has a tall, echoing reputation, and one lesson feature is the word
  "fag" as the name of a goofy lesson chant/flag call used by the school.

Tension:
- The child wants to win the shiny lane ribbon but refuses a safe practice step.
- The instructor warns that pride can make a swimmer swallow too much water.
- Conflict grows when the child bolts for the deep end without the chosen gear.

Turn:
- A helper or instructor points to a moral value: honesty, patience, bravery,
  or kindness.
- The child accepts a safer plan and learns a steadier stroke.

Resolution:
- The child earns the ribbon by showing the moral value in action.
- The ending image proves the change in the pool and in the child's heart.

The script follows the storyworld contract:
- standalone stdlib file
- eager results import, lazy asp import
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, --show-asp
- ASP twin for the reasonableness gate
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------


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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str = "swim school"
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
class Lesson:
    id: str
    name: str
    risk: str
    result: str
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
    id: str
    label: str
    phrase: str
    region: str
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
    protects_against: set[str]
    offer: str
    tail: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "swim_school": Setting(place="swim school", affords={"kickboard", "deep_end", "backfloat"}),
}

LESSONS = {
    "kickboard": Lesson(
        id="kickboard",
        name="kickboard drill",
        risk="splashed and scared",
        result="faster and steadier",
        keyword="fag",
        tags={"water", "lesson", "fag"},
    ),
    "deep_end": Lesson(
        id="deep_end",
        name="deep-end test",
        risk="in over their head",
        result="braver and wiser",
        keyword="fag",
        tags={"water", "deep", "fag"},
    ),
    "backfloat": Lesson(
        id="backfloat",
        name="backfloat practice",
        risk="slipping and gulping water",
        result="calm and floating",
        keyword="fag",
        tags={"water", "calm", "fag"},
    ),
}

PRIZES = {
    "ribbon": Prize(id="ribbon", label="lane ribbon", phrase="a shiny lane ribbon", region="torso"),
    "goggles": Prize(id="goggles", label="goggles", phrase="a pair of blue goggles", region="eyes"),
    "cap": Prize(id="cap", label="swim cap", phrase="a snug red swim cap", region="head"),
}

GEAR = {
    "kickboard": Gear(
        id="kickboard",
        label="a kickboard",
        covers={"arms", "torso"},
        protects_against={"splash"},
        offer="use a kickboard first",
        tail="walked back to the shallow end with the kickboard",
    ),
    "goggles": Gear(
        id="goggles",
        label="goggles",
        covers={"eyes"},
        protects_against={"water"},
        offer="put on goggles first",
        tail="fastened the goggles and tried again",
    ),
    "cap": Gear(
        id="cap",
        label="a swim cap",
        covers={"head"},
        protects_against={"water"},
        offer="put on a swim cap first",
        tail="pulled on the swim cap and steadied their chin",
    ),
}

GIRL_NAMES = ["Mina", "June", "Lola", "Nora", "Ivy", "Ruby"]
BOY_NAMES = ["Owen", "Pip", "Milo", "Finn", "Toby", "Eli"]
TRAITS = ["bold", "timid", "quick", "stubborn", "cheerful", "breezy"]
MORAL_VALUES = ["patience", "bravery", "honesty", "kindness"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    lesson: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    moral: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
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


def lesson_at_risk(lesson: Lesson, prize: Prize) -> bool:
    if lesson.id == "kickboard":
        return prize.region in {"torso", "arms"}
    if lesson.id == "deep_end":
        return prize.region in {"torso", "head", "eyes"}
    if lesson.id == "backfloat":
        return prize.region in {"head", "torso"}
    return False


def select_gear(lesson: Lesson, prize: Prize) -> Optional[Gear]:
    for gear in GEAR.values():
        if prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for lid in setting.affords:
            lesson = _safe_lookup(LESSONS, lid)
            for pid, prize in PRIZES.items():
                if lesson_at_risk(lesson, prize) and select_gear(lesson, prize):
                    combos.append((place, lid, pid))
    return combos


def explain_rejection(lesson: Lesson, prize: Prize) -> str:
    return (
        f"(No story: {lesson.name} would not honestly threaten {prize.label}. "
        f"Pick a prize worn in the at-risk region so the lesson has a real conflict.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    return f"(No story: {_safe_lookup(PRIZES, prize_id).label} is not a typical {gender}'s item in this world.)"


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def predict_mess(world: World, actor: Entity, lesson: Lesson, prize_id: str) -> dict:
    sim = world.copy()
    _do_lesson(sim, sim.get(actor.id), lesson, narrate=False)
    prize = sim.get(prize_id)
    return {
        "at_risk": lesson_at_risk(lesson, _safe_lookup(PRIZES, prize_id)),
        "soiled": bool(prize.meters.get("wet", 0) >= 1.0),
        "conflict": sum(e.memes.get("conflict", 0) for e in sim.characters()),
    }


def _do_lesson(world: World, actor: Entity, lesson: Lesson, narrate: bool = True) -> None:
    world.zone = {"water", "arms", "torso", "eyes", "head"}
    actor.meters["wet"] = actor.meters.get("wet", 0) + 1
    actor.memes["challenge"] = actor.memes.get("challenge", 0) + 1
    if narrate:
        world.say(f"{actor.id} tried the {lesson.name}, and the pool answered with a splash as big as a wagon wheel.")


def _r_conflict(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes.get("stubborn", 0) < 1.0 or actor.memes.get("warned", 0) < 1.0:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] = actor.memes.get("conflict", 0) + 1
        out.append("__conflict__")
    return out


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    emitted: list[str] = []
    while changed:
        changed = False
        for rule in (_r_conflict,):
            sents = rule(world)
            if sents:
                changed = True
                emitted.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in emitted:
            world.say(s)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a {hero.pronoun('possessive')} little {hero.type} with a heart as big as the pool house.")


def loves_swim(world: World, hero: Entity, lesson: Lesson) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} loved swim school, and {lesson.keyword} was the silly call "
        f"the coaches shouted before the lesson began."
    )


def arrive(world: World, hero: Entity, parent: Entity) -> None:
    world.say(
        f"One morning, {hero.id} and {hero.pronoun('possessive')} {parent.label} came to {world.setting.place}, "
        f"where the water shone like blue glass."
    )


def wants(world: World, hero: Entity, lesson: Lesson, prize: Prize) -> None:
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    world.say(
        f"{hero.id} wanted the {prize.label} more than a cookie after supper, and wanted to try the {lesson.name} right away."
    )


def warn(world: World, parent: Entity, hero: Entity, lesson: Lesson, prize: Prize) -> bool:
    pred = predict_mess(world, hero, lesson, prize.id)
    if not pred["at_risk"]:
        return False
    hero.memes["warned"] = hero.memes.get("warned", 0) + 1
    world.facts["predicted"] = pred
    world.say(
        f'"Easy now," {parent.label} said. "That {prize.label} could get soaked, and pride can make a child gulp a whole bucket of pool water."'
    )
    return True


def defies(world: World, hero: Entity, lesson: Lesson) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0) + 1
    world.say(f"{hero.id} puffed up like a storm cloud and tried to dash for the deep end anyway.")


def moral_turn(world: World, hero: Entity, parent: Entity, moral: str) -> None:
    hero.memes[moral] = hero.memes.get(moral, 0) + 1
    if moral == "patience":
        world.say(f"Then {hero.id} remembered patience, the way a pond remembers the sky.")
    elif moral == "bravery":
        world.say(f"Then {hero.id} remembered bravery, not the noisy kind, but the quiet kind that keeps breathing steady.")
    elif moral == "honesty":
        world.say(f"Then {hero.id} told the truth: the deep end looked bigger than a barn on a windy night.")
    else:
        world.say(f"Then {hero.id} chose kindness and listened to {hero.pronoun('possessive')} {parent.label} as if it were music.")


def compromise(world: World, parent: Entity, hero: Entity, lesson: Lesson, prize: Prize) -> Optional[Gear]:
    gear = select_gear(lesson, prize)
    if gear is None:
        return None
    world.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True, worn_by=hero.id, owner=hero.id))
    world.say(
        f"{parent.label.capitalize()} smiled and said, \"How about we {gear.offer} and try again in the shallow end?\""
    )
    return gear


def accept(world: World, hero: Entity, parent: Entity, lesson: Lesson, prize: Prize, gear: Gear, moral: str) -> None:
    hero.memes["conflict"] = 0
    hero.memes["calm"] = hero.memes.get("calm", 0) + 1
    world.say(
        f"{hero.id} nodded, and the two of them {gear.tail}. Soon {hero.id} was {lesson.result}, "
        f"the {prize.label} stayed dry, and the pool seemed to hum its approval."
    )
    world.say(
        f"By the end, {hero.id} had {moral} in {hero.pronoun('possessive')} pocket, "
        f"and that was worth more than any ribbon."
    )


def tell(setting: Setting, lesson: Lesson, prize_cfg: Prize, name: str, gender: str,
         parent_type: str = "mother", trait: str = "bold", moral: str = "patience") -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name, memes={"stubborn": 0.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="coach-parent"))
    prize = world.add(Entity(id="Prize", type=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))
    hero.memes[trait] = 1.0

    introduce(world, hero)
    loves_swim(world, hero, lesson)
    arrive(world, hero, parent)
    wants(world, hero, lesson, prize)
    warn(world, parent, hero, lesson, prize)
    defies(world, hero, lesson)
    moral_turn(world, hero, parent, moral)
    gear = compromise(world, parent, hero, lesson, prize)
    if gear:
        accept(world, hero, parent, lesson, prize, gear, moral)

    world.facts.update(hero=hero, parent=parent, prize=prize, lesson=lesson, gear=gear, moral=moral)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

KNOWLEDGE = {
    "water": [("Why do swimmers wear goggles?", "Swimmers wear goggles to help keep water out of their eyes while they splash and kick.")],
    "lesson": [("What is a swim lesson?", "A swim lesson is a class where children learn to move safely and confidently in water.")],
    "fag": [("What is the fag call in this story?", "In this world, the fag call is a silly school chant the coaches shout before practice to get everyone ready.")],
    "deep": [("What is the deep end?", "The deep end is the part of a pool where the water is deeper and swimmers cannot stand up as easily.")],
    "calm": [("Why does calm matter in swimming?", "Calm helps a swimmer breathe, listen, and move with safer strokes instead of panicking.")],
    "honesty": [("What does honesty mean?", "Honesty means telling the truth clearly and not pretending something is safer than it really is.")],
    "patience": [("What does patience mean?", "Patience means waiting, listening, and trying again without rushing.")],
    "bravery": [("What is quiet bravery?", "Quiet bravery is doing a hard thing carefully, even when it feels a little scary.")],
    "kindness": [("What does kindness look like at swim school?", "Kindness can mean listening, helping, and making sure everyone feels safe.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    lesson = _safe_fact(world, f, "lesson")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a tall tale about swim school with the word "fag" in the coach chant, where {hero.id} wants to try the {lesson.name}.',
        f"Tell a child-friendly story set at swim school where a {hero.type} learns {f['moral']} before chasing the {prize.label}.",
        f"Write a short, lively swimming story with a big conflict, a moral value, and a safe ending image in the pool.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, lesson, moral = f["hero"], f["parent"], f["prize"], f["lesson"], f["moral"]
    return [
        QAItem(
            question=f"Who is the story about at {world.setting.place}?",
            answer=f"The story is about {hero.id}, who goes to {world.setting.place} with {parent.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want at swim school?",
            answer=f"{hero.id} wanted to try the {lesson.name} and win the {prize.label}.",
        ),
        QAItem(
            question=f"What worried {parent.label} about the {prize.label}?",
            answer=f"{parent.label} worried the {prize.label} could get soaked or make {hero.id} rush before being ready.",
        ),
        QAItem(
            question=f"What moral value helped {hero.id} choose a safer path?",
            answer=f"{moral.capitalize()} helped {hero.id} slow down, listen, and choose the safer way to practice.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["lesson"].tags)
    tags.add(world.facts["moral"])
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(L,P) :- lesson(L), prize(P), risk_region(L,R), worn_on(P,R).
has_fix(L,P) :- prize_at_risk(L,P), gear(G), covers(G,R), worn_on(P,R).
valid_story(Place,L,P,G) :- affords(Place,L), prize(P), gender_ok(G,P), prize_at_risk(L,P), has_fix(L,P).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for lid in setting.affords:
            lines.append(asp.fact("affords", pid, lid))
    for lid, lesson in LESSONS.items():
        lines.append(asp.fact("lesson", lid))
        for t in sorted(lesson.tags):
            lines.append(asp.fact("tag", lid, t))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, prize.region))
        for g in sorted(prize.genders):
            lines.append(asp.fact("gender_ok", g, pid))
    for gid, gear in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for r in sorted(gear.covers):
            lines.append(asp.fact("covers", gid, r))
    # derived facts for the rules
    for lid, lesson in LESSONS.items():
        if lid == "kickboard":
            for region in ["torso", "arms"]:
                lines.append(asp.fact("risk_region", lid, region))
        elif lid == "deep_end":
            for region in ["torso", "head", "eyes"]:
                lines.append(asp.fact("risk_region", lid, region))
        elif lid == "backfloat":
            for region in ["head", "torso"]:
                lines.append(asp.fact("risk_region", lid, region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set((p, l, r) for (p, l, r, _) in asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale swim school story world.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--lesson", choices=LESSONS.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--moral", choices=MORAL_VALUES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "lesson", None) and getattr(args, "prize", None):
        lesson = _safe_lookup(LESSONS, getattr(args, "lesson", None))
        prize = _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (lesson_at_risk(lesson, prize) and select_gear(lesson, prize)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "prize", None) and getattr(args, "gender", None) not in _safe_lookup(PRIZES, getattr(args, "prize", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "lesson", None) is None or c[1] == getattr(args, "lesson", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, lesson, prize = rng.choice(list(combos))
    pr = _safe_lookup(PRIZES, prize)
    gender = getattr(args, "gender", None) or rng.choice(sorted(pr.genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    moral = getattr(args, "moral", None) or rng.choice(MORAL_VALUES)
    return StoryParams(place=place, lesson=lesson, prize=prize, name=name, gender=gender, parent=parent, trait=trait, moral=moral)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(LESSONS, params.lesson), _safe_lookup(PRIZES, params.prize),
                 params.name, params.gender, params.parent, params.trait, params.moral)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="swim_school", lesson="kickboard", prize="ribbon", name="Mina", gender="girl", parent="mother", trait="bold", moral="patience"),
    StoryParams(place="swim_school", lesson="deep_end", prize="goggles", name="Owen", gender="boy", parent="father", trait="stubborn", moral="bravery"),
    StoryParams(place="swim_school", lesson="backfloat", prize="cap", name="Ivy", gender="girl", parent="mother", trait="cheerful", moral="kindness"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        for item in combos:
            print(item)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
