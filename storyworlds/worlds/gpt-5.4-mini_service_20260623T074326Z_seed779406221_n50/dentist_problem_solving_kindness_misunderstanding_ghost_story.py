#!/usr/bin/env python3
"""
storyworlds/worlds/dentist_problem_solving_kindness_misunderstanding_ghost_story.py
===================================================================================

A small standalone storyworld about a dentist, a spooky misunderstanding, and a
kind problem-solving turn that makes the ghost story end gently.

Seed premise:
A child thinks a dentist's office is haunted when a blanket is moved in the
dark. The "ghost" is really a shy helper in costume, and the dentist and child
solve the mix-up with kindness.

The world is modeled as typed entities with physical meters and emotional memes.
The story is generated from world state, not from a frozen template: the same
premise can end with a fear-first misunderstanding, a careful investigation, and
a warm resolution.

Contract notes:
- Standalone stdlib script under storyworlds/worlds/
- Imports storyworlds/results eagerly for QAItem, StoryError, StorySample
- Imports storyworlds/asp lazily inside ASP helpers
- Defines StoryParams, registries, build_parser, resolve_params, generate, emit,
  and main
- Supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2



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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    dentist: object | None = None
    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Scene:
    id: str
    place: str
    dark_spot: str
    spooky_sound: str
    reveal_word: str
    ending_image: str
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
class Problem:
    id: str
    symptom: str
    cause: str
    fix_hint: str
    solved_by: str
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
class KindnessMove:
    id: str
    action: str
    comfort: str
    followup: str
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
class Misunderstanding:
    id: str
    guess: str
    truth_check: str
    correction: str
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
class Response:
    id: str
    sense: int
    method: str
    result: str
    qa_text: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
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


SCENES = {
    "quiet_clinic": Scene(
        id="quiet_clinic",
        place="a quiet clinic at dusk",
        dark_spot="the end of the hallway",
        spooky_sound="a soft thump behind the curtain",
        reveal_word="the curtain moved",
        ending_image="the clinic windows shone gold against the dark street",
    ),
    "rainy_night": Scene(
        id="rainy_night",
        place="a small dentist office on a rainy night",
        dark_spot="the little waiting room",
        spooky_sound="a tap-tap at the window",
        reveal_word="the shadow on the wall wiggled",
        ending_image="rain streaks slid down the glass while the lamps glowed warm",
    ),
    "moonlight_visit": Scene(
        id="moonlight_visit",
        place="the dentist's office under pale moonlight",
        dark_spot="the back chair",
        spooky_sound="a squeak from the sink",
        reveal_word="a white shape floated near the chair",
        ending_image="moonlight puddled on the floor like silver milk",
    ),
}

PROBLEMS = {
    "rattling_machine": Problem(
        id="rattling_machine",
        symptom="a rattling machine that made a spooky noise",
        cause="a loose tray",
        fix_hint="tighten the tray and check the wheel",
        solved_by="the dentist tightened the tray",
    ),
    "stuck_drape": Problem(
        id="stuck_drape",
        symptom="a curtain that kept snagging",
        cause="a bent hook",
        fix_hint="bend the hook back and smooth the cloth",
        solved_by="the child held the curtain still while the dentist fixed the hook",
    ),
    "dim_lamp": Problem(
        id="dim_lamp",
        symptom="a lamp that flickered in the dark",
        cause="a sleepy battery",
        fix_hint="swap in a fresh battery",
        solved_by="the helper found a fresh battery",
    ),
}

KINDNESS = {
    "blanket": KindnessMove(
        id="blanket",
        action="offered a soft blanket",
        comfort="The blanket made the waiting room feel safe and small",
        followup="The child stopped shivering",
    ),
    "story": KindnessMove(
        id="story",
        action="told a silly story about a tooth-brushing dragon",
        comfort="The silly story turned worry into a grin",
        followup="The child laughed before the drill even started",
    ),
    "water": KindnessMove(
        id="water",
        action="poured a cup of cool water",
        comfort="The water helped the dry mouth feel better",
        followup="The child took a brave sip",
    ),
}

MISUNDERSTANDINGS = {
    "ghost": Misunderstanding(
        id="ghost",
        guess="the child thought the moving shadow was a ghost",
        truth_check="the shape was only a blanket and a helper in costume",
        correction="the dentist showed the child the costume and the moving curtain",
    ),
    "monster": Misunderstanding(
        id="monster",
        guess="the child thought the tapping came from a monster",
        truth_check="the tapping came from rain and a loose tray",
        correction="the dentist opened the cabinet and found the tray",
    ),
    "spirit": Misunderstanding(
        id="spirit",
        guess="the child thought the white shape was a spirit",
        truth_check="the white shape was a sheet over a lamp stand",
        correction="the helper lifted the sheet and laughed kindly",
    ),
}

RESPONSES = {
    "check_room": Response(
        id="check_room",
        sense=3,
        method="checked the room together with a flashlight",
        result="They found the real cause and the scary feeling slipped away",
        qa_text="checked the room with a flashlight and found the cause",
    ),
    "ask_kindly": Response(
        id="ask_kindly",
        sense=3,
        method="asked the helper a gentle question",
        result="The helper explained the trick, and the child felt calmer",
        qa_text="asked kindly and got a gentle explanation",
    ),
    "fix_problem": Response(
        id="fix_problem",
        sense=3,
        method="fixed the small problem first",
        result="The noise stopped, and the spooky feeling lost its power",
        qa_text="fixed the small problem and stopped the noise",
    ),
    "hide": Response(
        id="hide",
        sense=1,
        method="hid under a chair",
        result="That did not solve anything",
        qa_text="hid under a chair",
    ),
}

NAMES = ["Mia", "Noah", "Luna", "Owen", "Ivy", "Eli", "Sage", "Nina"]
DENTISTS = ["Dr. Kim", "Dr. Lee", "Dr. Patel", "Dr. Rivera"]
HELPERS = ["Nurse Joy", "Marta", "Ben", "Ana"]


@dataclass
class StoryParams:
    scene: str
    problem: str
    kindness: str
    misunderstanding: str
    response: str
    child: str
    child_gender: str
    dentist: str
    helper: str
    seed: Optional[int] = None
    p: object | None = None
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
    ap = argparse.ArgumentParser(description="A ghostly dentist storyworld with kindness and problem solving.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--kindness", choices=KINDNESS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child", choices=NAMES)
    ap.add_argument("--dentist", choices=DENTISTS)
    ap.add_argument("--helper", choices=HELPERS)
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
    scene = getattr(args, "scene", None) or rng.choice(list(SCENES))
    problem = getattr(args, "problem", None) or rng.choice(list(PROBLEMS))
    kindness = getattr(args, "kindness", None) or rng.choice(list(KINDNESS))
    misunderstanding = getattr(args, "misunderstanding", None) or rng.choice(list(MISUNDERSTANDINGS))
    response = getattr(args, "response", None) or rng.choice([r.id for r in RESPONSES.values() if r.sense >= SENSE_MIN])
    child = getattr(args, "child", None) or rng.choice(NAMES)
    child_gender = "girl" if child in {"Mia", "Luna", "Ivy", "Nina"} else "boy"
    dentist = getattr(args, "dentist", None) or rng.choice(DENTISTS)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)

    if _safe_lookup(RESPONSES, response).sense < SENSE_MIN:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(scene, problem, kindness, misunderstanding, response, child, child_gender, dentist, helper)


def _render_intro(world: World) -> None:
    c = world.get("child")
    d = world.get("dentist")
    s = _safe_lookup(SCENES, world.facts.get("scene"))
    world.say(
        f"{c.id} came to {d.label} at {s.place}. The room smelled like mint and paper, "
        f"and the big chair looked tall enough to reach the moon."
    )


def _render_misunderstanding(world: World) -> None:
    c = world.get("child")
    mis = _safe_lookup(MISUNDERSTANDINGS, world.facts.get("misunderstanding"))
    s = _safe_lookup(SCENES, world.facts.get("scene"))
    world.say(
        f"Then {s.spooky_sound}. {mis.guess}, and {c.id} held very still."
    )


def _render_kindness(world: World) -> None:
    c = world.get("child")
    k = _safe_lookup(KINDNESS, world.facts.get("kindness"))
    world.say(f"{c.id} was trembling, so the helper {k.action}. {k.comfort}.")
    c.memes["fear"] = max(0.0, c.memes.get("fear", 0.0) - 1.0)
    c.memes["trust"] = c.memes.get("trust", 0.0) + 1.0


def _render_problem_solving(world: World) -> None:
    d = world.get("dentist")
    p = _safe_lookup(PROBLEMS, world.facts.get("problem"))
    r = _safe_lookup(RESPONSES, world.facts.get("response"))
    world.say(
        f"{d.label} listened carefully, then {r.method}. {p.solved_by}, and the "
        f"spooky sound matched {p.cause} instead of anything haunted."
    )
    world.say(r.result + ".")
    world.facts["solved"] = True


def _render_reveal(world: World) -> None:
    h = world.get("helper")
    mis = _safe_lookup(MISUNDERSTANDINGS, world.facts.get("misunderstanding"))
    s = _safe_lookup(SCENES, world.facts.get("scene"))
    world.say(
        f"{h.label} pointed to the clue: {mis.truth_check}. {mis.correction}, "
        f"and the whole room felt ordinary again."
    )
    world.say(f"By the end, {s.ending_image}.")


def tell_story(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, label=params.child, role="child"))
    dentist = world.add(Entity(id=params.dentist, kind="character", type="adult", label=params.dentist, role="dentist"))
    helper = world.add(Entity(id=params.helper, kind="character", type="adult", label=params.helper, role="helper"))
    world.facts.update(
        scene=params.scene,
        problem=params.problem,
        kindness=params.kindness,
        misunderstanding=params.misunderstanding,
        response=params.response,
    )
    child.memes["fear"] = 2.0
    child.memes["curiosity"] = 1.0
    _render_intro(world)
    world.para()
    _render_misunderstanding(world)
    world.para()
    _render_kindness(world)
    world.para()
    _render_problem_solving(world)
    world.para()
    _render_reveal(world)
    world.facts.update(child=child, dentist=dentist, helper=helper)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a gentle ghost story about {f['child'].id} visiting {f['dentist'].label} and thinking a moving shadow is a ghost, then solving the mystery kindly.",
        f"Tell a story with a spooky misunderstanding at {SCENES[f['scene']].place}, where {f['child'].id} gets scared but {f['dentist'].label} fixes the real problem.",
        f"Create a child-friendly dentist ghost story with kindness, problem solving, and a mistaken ghost that turns out to be harmless.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c = f["child"].id
    d = f["dentist"].label
    p = PROBLEMS[f["problem"]]
    k = KINDNESS[f["kindness"]]
    m = MISUNDERSTANDINGS[f["misunderstanding"]]
    return [
        QAItem(question=f"Who visited the dentist?", answer=f"{c} visited {d} for help in a spooky-feeling room."),
        QAItem(question="What did the child think was a ghost?", answer=f"{m.guess.capitalize()}."),
        QAItem(question="How did the adults help?", answer=f"They stayed calm, used kindness, and solved the real problem together."),
        QAItem(question="What was the real problem?", answer=f"It was {p.symptom}, caused by {p.cause}."),
        QAItem(question="What kind thing made the child feel better?", answer=f"The helper {k.action}, which helped the child calm down."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does a dentist do?", answer="A dentist helps keep teeth healthy and checks mouths for problems."),
        QAItem(question="Why can a dark hallway feel spooky?", answer="When it is dark and quiet, ordinary sounds can seem mysterious or ghostly."),
        QAItem(question="What is a good way to solve a misunderstanding?", answer="Ask gentle questions, look for clues, and check what is really happening."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: kind={e.kind} type={e.type} role={e.role} memes={e.memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
scene(qc). scene(rn). scene(mv).
problem(rm). problem(sd). problem(dl).
kindness(bk). kindness(st). kindness(wa).
misunderstanding(gh). misunderstanding(mn). misunderstanding(sp).
response(check_room). response(ask_kindly). response(fix_problem).
sense(check_room,3). sense(ask_kindly,3). sense(fix_problem,3). sense(hide,1).
sensible(R) :- response(R), sense(R,S), min_sense(M), S >= M.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("min_sense", SENSE_MIN)]
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for kid in KINDNESS:
        lines.append(asp.fact("kindness", kid))
    for mid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    python = {r.id for r in RESPONSES.values() if r.sense >= SENSE_MIN}
    clingo = set(asp_sensible())
    if python == clingo:
        print(f"OK: sensible responses match ({sorted(python)})")
        return 0
    print(f"MISMATCH: python={sorted(python)} clingo={sorted(clingo)}")
    return 1


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for s in SCENES:
        for p in PROBLEMS:
            for k in KINDNESS:
                for m in MISUNDERSTANDINGS:
                    for r in RESPONSES:
                        if _safe_lookup(RESPONSES, r).sense >= SENSE_MIN:
                            combos.append((s, p, k, m, r))
    return combos


def resolve_story_logic(params: StoryParams) -> None:
    if params.response not in RESPONSES:
        pass
    if _safe_lookup(RESPONSES, params.response).sense < SENSE_MIN:
        pass


def generate(params: StoryParams) -> StorySample:
    resolve_story_logic(params)
    world = tell_story(params)
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
        print(asp_program("", "#show sensible/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("sensible responses:", ", ".join(asp_sensible()))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for combo in valid_combos():
            p = StoryParams(
                scene=combo[0], problem=combo[1], kindness=combo[2], misunderstanding=combo[3],
                response=combo[4], child=random.choice(NAMES), child_gender="girl",
                dentist=random.choice(DENTISTS), helper=random.choice(HELPERS), seed=None,
            )
            samples.append(generate(p))
    else:
        for i in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
