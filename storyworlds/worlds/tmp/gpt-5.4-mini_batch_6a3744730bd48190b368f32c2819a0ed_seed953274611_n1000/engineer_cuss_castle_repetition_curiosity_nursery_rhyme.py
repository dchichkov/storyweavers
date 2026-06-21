#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/engineer_cuss_castle_repetition_curiosity_nursery_rhyme.py
==========================================================================================

A tiny, standalone story world in a nursery-rhyme style: an engineer, a castle,
a curious question, a repeated mistake, and a calm repair. The simulation keeps
track of physical state in meters and emotional state in memes, then renders a
complete child-facing story from that changing state.

The domain is intentionally small:
- an engineer is building a castle
- curiosity leads to a repeated mistake
- a frustrated cuss is heard
- a helper suggests a better way
- the story ends with a finished castle image proving what changed
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = {"built": 0.0, "mess": 0.0, "dust": 0.0, "fix": 0.0, **self.meters}
        self.memes = {"curiosity": 0.0, "frustration": 0.0, "relief": 0.0, "pride": 0.0, **self.memes}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "engineer"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class StoryParams:
    name: str
    helper: str
    helper_type: str
    castle: str
    build_task: str
    mistake: str
    fix: str
    refrain: str
    seed: Optional[int] = None


@dataclass
class Setting:
    id: str
    scene: str
    refrain_line: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    label: str
    initial_built: float
    repetition_gain: float
    dust_gain: float
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mistake:
    id: str
    label: str
    annoyance: str
    repeat_line: str
    cuss_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    power: int
    line: str
    reward: str
    tags: set[str] = field(default_factory=set)


SETTINGS = {
    "nursery": Setting(
        id="nursery",
        scene="a snug nursery with a rug and a toy box",
        refrain_line="Pat-pat, tap-tap, all day long, the little hands sang a builder's song.",
        ending_line="And there in the nursery stood a bright small castle, tidy as a rhyme.",
        tags={"nursery", "rhyme"},
    )
}

TASKS = {
    "blocks": Task(
        id="blocks",
        label="stacking blocks into a castle",
        initial_built=1.0,
        repetition_gain=1.0,
        dust_gain=0.5,
        clue="one block at a time",
        tags={"castle", "repetition"},
    ),
    "sand": Task(
        id="sand",
        label="shaping a sand castle in a tray",
        initial_built=1.0,
        repetition_gain=1.0,
        dust_gain=0.5,
        clue="one scoop at a time",
        tags={"castle", "curiosity"},
    ),
}

MISTAKES = {
    "wiggle": Mistake(
        id="wiggle",
        label="wiggling the tower base",
        annoyance="the tower kept wobbling",
        repeat_line="Again and again the tower toppled down.",
        cuss_line="and the engineer let out a little cuss in surprise.",
        tags={"cuss", "repetition"},
    ),
    "peek": Mistake(
        id="peek":=None,
        label="peeking inside before the glue dried",
        annoyance="the wet glue smudged the walls",
        repeat_line="Again and again the walls smeared and slipped.",
        cuss_line="and the engineer whispered a cuss through gritted teeth.",
        tags={"curiosity", "cuss"},
    ),
}
