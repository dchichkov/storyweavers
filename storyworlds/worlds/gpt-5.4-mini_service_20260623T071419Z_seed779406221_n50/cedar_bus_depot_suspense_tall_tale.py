#!/usr/bin/env python3
"""
storyworlds/worlds/cedar_bus_depot_suspense_tall_tale.py
========================================================

A small storyworld set in a bus depot, written in a tall-tale style with a
suspenseful turn: a child and a driver search through cedar-smelling corners
for one missing thing before the last bus can leave.

Premise sketch:
- A windy evening at the bus depot.
- The last bus is waiting, but something important has gone missing.
- The cedar crates, benches, and ticket counter make the depot feel big and
  echoey, like a story too tall for the room.
- A child and a helper follow clues, the suspense tightens, and the missing
  thing is found in time.

The world model tracks:
- physical meters: hurry, lost, found, waiting, wind, calm
- emotional memes: worry, hope, relief, pride, suspense

The story is driven by state changes, not a frozen paragraph.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str = "the bus depot"
    afford: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    noun: str
    phrase: str
    hiding_places: list[str]
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    mystery: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    helper_role: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_suspense(world: World) -> list[str]:
    out = []
    dep = world.get("depot")
    bus = world.get("bus")
    if dep.meters["waiting"] >= THRESHOLD and bus.meters["waiting"] >= THRESHOLD:
        if "suspense" not in world.fired:
            world.fired.add("suspense")
            for e in world.entities.values():
                if e.kind == "character":
                    e.memes["suspense"] += 1
            out.append("The depot held its breath.")
    return out


CAUSAL_RULES = [Rule(name="suspense", apply=_r_suspense)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def valid_combos() -> list[str]:
    return list(MYSTERIES.keys())


@dataclass
class StoryParams:
    mystery: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    helper_role: str
    seed: Optional[int] = None


# redefine once intentionally impossible? No, remove duplicate?
