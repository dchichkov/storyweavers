#!/usr/bin/env python3
"""
storyworlds/worlds/broccoli_captain_humor_tall_tale.py
======================================================

A standalone story world for a humorous tall tale about broccoli, a captain,
and a problem that can be solved only by a reasonable, state-driven turn.

Premise:
- A small hero loves adventure and does not want to eat broccoli.
- A bold captain warns that the broccoli is the "sea-green crew food" that
  helps the ship stay steady.
- The child resists, the captain notices the trouble, and then offers a comic
  compromise: a broccoli toast, a tiny bite, or a brave ship shape promise.
- The ending proves something changed: the broccoli got eaten, the laugh was
  shared, and the captain's tall tale became true enough to tell again.

This script models:
- Physical meters: hunger, wobble, neatness, bite-size, steam, crunch.
- Emotional memes: delight, doubt, pride, worry, relief, bravado.

It also provides an inline ASP twin of the reasonableness gate and a
Python-side gate that must agree with it.
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


# ---------------------------------------------------------------------------
# Core entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the harbor kitchen"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Remedy:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str]
    helps: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy as _copy

        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        c.paragraphs = [[]]
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "galley": Setting(place="the harbor kitchen", indoors=True, affords={"cook"}),
    "deck": Setting(place="the windy deck", indoors=False, affords={"cook"}),
}

ACTIVITIES = {
    "cook": Activity(
        id="cook",
        verb="cook the broccoli",
        gerund="cooking broccoli",
        rush="dash to the stove",
        mess="steam",
        soil="soft and soggy",
        keyword="broccoli",
        tags={"broccoli", "food", "steam"},
    ),
}

PRIZES = {
    "broccoli": Prize(
        label="broccoli",
        phrase="a crown of bright green broccoli",
        type="broccoli",
        region="mouth",
        plural=False,
    )
}

REMEDIES = [
    Remedy(
        id="tinybite",
        label="a tiny brave bite",
        prep="take one tiny brave bite first",
        tail="took a tiny brave bite and then laughed at the rest",
        guards={"steam"},
        helps={"broccoli"},
    ),
    Remedy(
        id="toastboat",
        label="broccoli toast in a little sailboat shape",
        prep="turn the broccoli into a toast-boat",
        tail="sailed the broccoli toast right into supper",
        guards={"steam"},
        helps={"broccoli"},
    ),
]

HERO_NAMES = ["Ruby", "Milo", "Nina", "Otis", "June", "Piper", "Ezra", "Dot"]
TRAITS = ["brave", "curious", "silly", "cheerful", "lively", "stubborn"]


# ---------------------------------------------------------------------------
# ASP twin and reasonableness gate
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), pair(A,P).
has_remedy(A,P) :- prize_at_risk(A,P), remedy(R), helps(R,P), guards(R,M), mess_of(A,M).
valid_story(S,A,P) :- setting(S), affords(S,A), prize_at_risk(A,P), has_remedy(A,P).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for r in REMEDIES:
        lines.append(asp.fact("remedy", r.id))
        for g in sorted(r.guards):
            lines.append(asp.fact("guards", r.id, g))
        for h in sorted(r.helps):
            lines.append(asp.fact("helps", r.id, h))
    for aid in ACTIVITIES:
        for pid in PRIZES:
            lines.append(asp.fact("pair", aid, pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for aid, a in ACTIVITIES.items():
            if aid not in s.affords:
                continue
            for pid in PRIZES:
                if any(r for r in REMEDIES if pid in r.helps and a.mess in r.guards):
                    combos.append((sid, aid, pid))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def predict(world: World, hero: Entity, act: Activity, prize_id: str) -> dict:
    sim = world.copy()
    h = sim.get(hero.id)
    h.meters[act.mess] = h.meters.get(act.mess, 0) + 1
    prize = sim.get(prize_id)
    soiled = h.meters[act.mess] >= THRESHOLD and prize.label == "broccoli"
    return {"soiled": soiled}


def apply_activity(world: World, hero: Entity, act: Activity) -> None:
    hero.meters[act.mess] = hero.meters.get(act.mess, 0) + 1
    hero.memes["bravado"] = hero.memes.get("bravado", 0) + 1


def reason_gate(act: Activity, prize: Prize) -> Optional[Remedy]:
    if act.mess != "steam" or prize.label != "broccoli":
        return None
    return REMEDIES[1] if prize.region == "mouth" else REMEDIES[0]


def tell(setting: Setting, act: Activity, prize: Prize, name: str, gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={"joy": 0.0, "doubt": 0.0}))
    captain = world.add(Entity(id="Captain", kind="character", type="captain", label="the captain", meters={}, memes={"worry": 0.0, "pride": 0.0}))
    broccoli = world.add(Entity(id="Broccoli", type="broccoli", label="broccoli", phrase=prize.phrase, owner=hero.id))

    world.say(f"{hero.id} was a {trait} little {gender} who loved a big day of pretend sea adventures.")
    world.say(f"{hero.pronoun().capitalize()} wanted the {prize.label} to stay far away from supper, because it looked too green to trust.")
    world.say(f"Then {hero.id} met {captain.label} at {setting.place}, where the air smelled like salt, soup, and one very opinionated spoon.")
    world.para()

    if not setting.affords.__contains__(act.id):
        raise StoryError("This setting cannot host the chosen activity.")

    pred = predict(world, hero, act, prize.label)
    if pred["soiled"]:
        world.say(f'"{You\'ll need that {prize.label}," {captain.pronoun("subject")} said, tipping an imaginary hat. "A stormy supper needs a steady crew."')
        world.say(f"{hero.id} frowned and tried to {act.rush}, but the idea kept wobbling like a spoon in a teacup.")
        hero.memes["doubt"] = hero.memes.get("doubt", 0) + 1
        hero.memes["stubbornness"] = hero.memes.get("stubbornness", 0) + 1
        captain.memes["worry"] = captain.memes.get("worry", 0) + 1
        world.say(f"The {captain.label} scratched a whisker and made a tall-tale promise: the broccoli could be brave if it wore a better shape.")
        remedy = reason_gate(act, prize)
        if remedy is None:
            raise StoryError("No reasonable remedy exists for this story.")
        world.say(f'{captain.label.capitalize()} предлож?')
    return world
