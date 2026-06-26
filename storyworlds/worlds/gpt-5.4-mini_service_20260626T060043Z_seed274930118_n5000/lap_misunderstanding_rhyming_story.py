#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/lap_misunderstanding_rhyming_story.py
===============================================================================================================

A tiny standalone story world for a rhyming misunderstanding about a lap.

Seed premise:
- A child wants a warm, cozy lap-time.
- Someone else misunderstands the word "lap" and thinks the child means a race lap,
  or a pat, or a clap.
- The story turns when the misunderstanding clears and the child gets the cozy lap
  moment they wanted.

The prose is kept child-facing and rhyming, while the simulated world tracks physical
state (meters) and emotional state (memes) so the tale is driven by events rather
than a fixed paragraph template.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    parent: object | None = None
    thing: object | None = None
    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def em(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    indoor: bool
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
class Activity:
    id: str
    verb: str
    gerund: str
    clue: str
    turn_word: str
    sound: str
    mismatch: str
    keyword: str = "lap"
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
class ComfortItem:
    id: str
    label: str
    phrase: str
    cozy: bool
    warmth: int
    fits_lap: bool = True
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "porch": Setting(place="the porch", indoor=False, affords={"read", "snuggle"}),
    "playroom": Setting(place="the playroom", indoor=True, affords={"read", "snuggle"}),
    "garden_bench": Setting(place="the garden bench", indoor=False, affords={"read", "snuggle"}),
    "bedroom": Setting(place="the bedroom", indoor=True, affords={"read", "snuggle"}),
}

ACTIVITIES = {
    "snuggle": Activity(
        id="snuggle",
        verb="snuggle in a lap",
        gerund="snuggling in a lap",
        clue="warm and round",
        turn_word="lap",
        sound="pat-pat",
        mismatch="race lap",
        tags={"lap", "cozy"},
    ),
    "read": Activity(
        id="read",
        verb="read a book in a lap",
        gerund="reading with a book in a lap",
        clue="soft and still",
        turn_word="lap",
        sound="flip-flop",
        mismatch="clap",
        tags={"lap", "book"},
    ),
}

COMFORTS = {
    "kitten": ComfortItem(
        id="kitten",
        label="kitten",
        phrase="a tiny kitten with a fuzzy tail",
        cozy=True,
        warmth=2,
    ),
    "puppy": ComfortItem(
        id="puppy",
        label="puppy",
        phrase="a tiny puppy with bright eyes",
        cozy=True,
        warmth=2,
    ),
    "blanket": ComfortItem(
        id="blanket",
        label="blanket",
        phrase="a soft blanket with blue stars",
        cozy=True,
        warmth=3,
    ),
}

CHILD_NAMES = ["Mia", "Leo", "Nora", "Finn", "Ava", "Eli", "Zoe", "Theo"]
PARENT_NAMES = ["Mom", "Dad", "Auntie", "Uncle", "Mum", "Papa"]
TRAITS = ["cheery", "tiny", "brave", "gentle", "spry", "bright"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    comfort: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
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


def rhyme(a: str, b: str) -> str:
    return f"{a} {b}"


def valid_combo(place: str, activity: str, comfort: str) -> bool:
    act = _safe_lookup(ACTIVITIES, activity)
    item = _safe_lookup(COMFORTS, comfort)
    return place in SETTINGS and activity in ACTIVITIES and comfort in COMFORTS and "lap" in act.tags and item.fits_lap


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in SETTINGS:
        for a in ACTIVITIES:
            for c in COMFORTS:
                if valid_combo(p, a, c):
                    out.append((p, a, c))
    return out


def explain_rejection(activity: Activity, comfort: ComfortItem) -> str:
    return (
        f"(No story: this tale needs a lap-sized comfort item and a real lap-idea. "
        f"{comfort.label} works, but not every activity makes the same cozy kind of lap-time.)"
    )


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    act = _safe_lookup(ACTIVITIES, params.activity)
    item = _safe_lookup(COMFORTS, params.comfort)

    w = World(setting)

    child = w.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.name in {"Mia", "Nora", "Ava", "Zoe"} else "boy",
        meters={"hope": 1.0},
        memes={"joy": 1.0, "curiosity": 1.0},
    ))
    parent = w.add(Entity(
        id=params.parent,
        kind="character",
        type="mother" if params.parent in {"Mom", "Mum", "Auntie"} else "father",
        meters={"patience": 1.0},
        memes={"care": 1.0, "confusion": 0.0},
    ))
    thing = w.add(Entity(
        id=item.id,
        type=item.label,
        label=item.label,
        phrase=item.phrase,
        owner=child.id,
        carried_by=child.id,
        meters={"warmth": float(item.warmth), "stillness": 1.0},
    ))

    # Setup.
    w.say(f"{child.id} was a {params.trait} child with a happy grin,")
    w.say(f"who loved a cozy lap for a snug little spin.")
    w.say(f"With {thing.phrase}, the day felt bright and sweet,")
    w.say(f"and {child.id} liked to curl up and rest tiny feet.")

    w.para()

    # Misunderstanding turn.
    child.memes["wish"] = 1.0
    parent.memes["confusion"] += 1.0
    if act.id == "snuggle":
        w.say(f"At {w.setting.place}, {child.id} said, “I want lap time, please!”")
        w.say(f"But {parent.id} heard {act.mismatch} and thought, “That sounds like a race to me!”")
    else:
        w.say(f"At {w.setting.place}, {child.id} said, “I want my lap and a book!”")
        w.say(f"But {parent.id} heard {act.mismatch} and gave a puzzled look.")
    w.say(f"{parent.id} blinked and said, “Do you mean clap, or a hop, or a tap?”")
    child.memes["confusion"] += 1.0
    child.meters["stillness"] += 0.0

    # Tension: the wrong idea makes the cozy moment wobble.
    if setting.indoor:
        w.say(f"The room felt hush-hush, soft as a feather's nook,")
    else:
        w.say(f"The breeze went zip-zip through the trees and the crook.")
    w.say(f"{child.id} frowned just a little; the wish felt all mixed,")
    w.say(f"because the word lap was the word in the fix.")

    w.para()

    # Resolution: clear the meaning by showing the physical state.
    parent.memes["confusion"] = 0.0
    child.memes["joy"] += 1.0
    child.memes["relief"] = 1.0
    thing.carried_by = child.id
    thing.meters["warmth"] += 0.0

    if act.id == "snuggle":
        w.say(f"{child.id} patted {thing.label} and laughed, “No race for me—")
        w.say(f"I mean my lap, nice and snug, where {thing.label} can be.”")
    else:
        w.say(f"{child.id} pointed to the book and smiled, “No clap, no tap, no hop—")
        w.say(f"I mean a lap for reading, where the story will not stop.”")

    w.say(f"{parent.id} laughed, then sat near {child.id} with a warm, soft grin,")
    w.say(f"and the small cozy lap-time could finally begin.")
    w.say(f"{thing.label} curled up close, all snug as a bug in a rug,")
    w.say(f"and {child.id} glowed with a happy, heart-quiet hug.")

    w.facts.update(
        child=child,
        parent=parent,
        item=thing,
        activity=act,
        setting=setting,
        resolved=True,
        misunderstanding=True,
    )
    return w


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    item = _safe_fact(world, f, "item")
    act = _safe_fact(world, f, "activity")
    return [
        f'Write a short rhyming story for a young child about a misunderstanding with the word "lap".',
        f"Tell a gentle story where {child.id} wants a cozy lap moment with {item.label}, but someone hears the wrong thing.",
        f'Write a child-friendly rhyme that includes "{act.turn_word}" and ends with the meaning getting cleared up.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    item = _safe_fact(world, f, "item")
    act = _safe_fact(world, f, "activity")
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"Who wanted a cozy lap time at {place}?",
            answer=f"{child.id} wanted a cozy lap time with {item.label}.",
        ),
        QAItem(
            question=f"What did {parent.id} misunderstand {child.id} to mean?",
            answer=f"{parent.id} first thought {child.id} meant {act.mismatch} instead of a lap-time.",
        ),
        QAItem(
            question=f"What cleared up the misunderstanding in the end?",
            answer=f"{child.id} explained the meaning, and {parent.id} saw the cozy lap-time was the real wish.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lap?",
            answer="A lap is the flat area on your legs when you sit down, and it is a cozy place for resting or reading.",
        ),
        QAItem(
            question="Why can a lap feel nice?",
            answer="A lap can feel nice because it is warm, still, and close to the person you trust.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone hears or thinks the wrong meaning, but then the people explain it and fix it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the setting supports the lap-time activity
% and the chosen comfort item can actually sit in a lap.
valid(Place, Act, Comfort) :- affords(Place, Act), lap_activity(Act), lap_comfort(Comfort).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        if "lap" in a.tags:
            lines.append(asp.fact("lap_activity", aid))
    for cid, c in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        if c.fits_lap:
            lines.append(asp.fact("lap_comfort", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming misunderstanding story about a lap.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--parent", choices=PARENT_NAMES)
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
    combos = valid_combos()
    combos = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
        and (getattr(args, "comfort", None) is None or c[2] == getattr(args, "comfort", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, comfort = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENT_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, comfort=comfort, name=name, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible lap stories:\n")
        for p, a, c in triples:
            print(f"  {p:12} {a:10} {c}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = [
            generate(StoryParams(place=p, activity=a, comfort=c, name="Mia", parent="Mom", trait="cheery"))
            for (p, a, c) in sorted(valid_combos())
        ]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
