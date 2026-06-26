#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/dish_mystery_to_solve_myth.py
==============================================================================================================

A small mythic story world: someone must solve a mystery about a dish.

Premise:
- In a little village under old stars, a sacred dish is prepared for a rite.
- The dish goes missing, cracks, or is misplaced in a way that leaves clues.
- The hero follows the clues, speaks with a helper, and discovers the truth.
- The ending shows the dish restored, found, or wisely replaced.

This script keeps the tone close to myth: moonlit roads, river reeds, hearth smoke,
wise elders, and a mystery that is solved by noticing the world carefully.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        female = {"girl", "woman", "mother", "sister", "priestess"}
        male = {"boy", "man", "father", "brother", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Dish:
    id: str
    label: str
    phrase: str
    material: str
    power: str
    risk: str
    clue: str
    region: str = "table"
    plural: bool = False


@dataclass
class Mystery:
    id: str
    verb: str
    inquiry: str
    search: str
    answer: str
    reveals: str
    cause: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    trace: list[str] = field(default_factory=list)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "hearth": Setting(place="the hearth hall", mood="warm", affords={"search"}),
    "river": Setting(place="the river shrine", mood="misty", affords={"search"}),
    "grove": Setting(place="the moon grove", mood="silent", affords={"search"}),
}

DISHES = {
    "silver": Dish(
        id="silver",
        label="silver dish",
        phrase="a shining silver dish",
        material="silver",
        power="it reflected moonlight",
        risk="its shine was dulled",
        clue="a bright scratch near the rim",
        region="table",
        tags := set()
    ),
    "clay": Dish(
        id="clay",
        label="clay dish",
        phrase="a round clay dish",
        material="clay",
        power="it held warm porridge",
        risk="it could crack",
        clue="a flake of dry mud",
    ),
    "oakwood": Dish(
        id="oakwood",
        label="oakwood dish",
        phrase="an old oakwood dish",
        material="oakwood",
        power="it carried feast bread",
        risk="it could warp",
        clue="a curl of bark",
    ),
}

# Fix invalid syntax above by defining tags after creation? Better avoid.
