#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pulley_model_rhyme_conflict_reconciliation_whodunit.py
======================================================================================

A small whodunit-style storyworld about a model scene, a pulley, a clue trail of
rhyme, a conflict between suspects, and a reconciliation that reveals the real
cause.

The world is deliberately tiny and classical:
- children build or inspect a model display,
- something odd happens with a pulley,
- two characters disagree over what happened,
- clues accumulate through physical and emotional state,
- the mystery is solved, and the characters make amends.

This script follows the Storyweavers contract:
- standalone stdlib script under storyworlds/worlds/
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily in ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    light: str
    hiding_spot: str


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    is_model: bool = False
    is_pulley: bool = False
    is_clue: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Suspicion:
    id: str
    label: str
    hint: str
    pressure: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Reveal:
    id: str
    cause: str
    fix: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    model: str
    pulley: str
    suspicion: str
    reveal: str
    kid1: str
    kid1_gender: str
    kid2: str
    kid2_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def build_registries():
    SETTINGS = {
        "attic": Setting("attic", "the attic", "a quiet attic with dust motes and a hanging lamp", "a thin window", "under the old blanket"),
        "workshop": Setting("workshop", "the workshop", "a neat workshop with shelves of parts and a chalkboard", "a bright desk lamp", "behind the stacked boxes"),
        "library": Setting("library", "the library room", "a small library room with a table for crafts", "a round lamp", "under the reading table"),
    }
    MODELS = {
        "ship": Toy("ship", "model ship", "a painted model ship", is_model=True, tags={"model", "ship"}),
        "train": Toy("train", "model train", "a tiny model train", is_model=True, tags={"model", "train"}),
        "tower": Toy("tower", "model tower", "a careful model tower", is_model=True, tags={"model", "tower"}),
    }
    PULLEYS = {
        "hoist": Toy("hoist", "pulley", "a little pulley on a string", is_pulley=True, is_clue=True, tags={"pulley", "string"}),
        "lift": Toy("lift": ???)
