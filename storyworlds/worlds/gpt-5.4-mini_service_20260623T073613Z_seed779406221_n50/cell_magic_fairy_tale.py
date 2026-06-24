#!/usr/bin/env python3
"""
storyworlds/worlds/cell_magic_fairy_tale.py
===========================================

A small fairy-tale storyworld about a child, a locked cell, and a bit of magic.
The tale is classical and gentle: someone is trapped or shut in, a magical
helper changes the state of the lock, and the ending proves that the cell is
open and safe.

This world keeps to a tiny domain:
- a fairy-tale place (tower, castle dungeon, garden keep)
- a small character cast
- a cell with a lock and a keyhole
- magical tools that can open, soften, or brighten the way

The story is driven by simulated state:
- the cell starts closed and dim
- the hero wants to leave or help
- magic can loosen the lock or reveal a hidden key
- the ending reflects whether the cell was opened and how the characters feel

The script supports the standard Storyweavers interface, a Python reasonableness
gate, and an inline ASP twin for parity checks.
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
MAGIC_MIN = 1
CELL_STATES = {"closed", "open"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: str = ""
    tied_to: str = ""
    magical: bool = False
    opens: bool = False
    brightens: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "fairy", "woman"}
        male = {"boy", "father", "king", "wizard", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "queen": "queen",
                "king": "king", "fairy": "fairy", "wizard": "wizard"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Magic:
    id: str
    label: str
    phrase: str
    effect: str
    power: int
    opens: bool = False
    brightens: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Cell:
    id: str
    label: str
    phrase: str
    lock: str
    window: str
    dim: str
    needs: str
    can_open_with: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_open_cell(world: World) -> list[str]:
    out: list[str] = []
    cell = world.get("cell")
    if cell.meters["opened"] >= THRESHOLD:
        sig = ("opened", cell.id)
        if sig not in world.fired:
            world.fired.add(sig)
            cell.label = "open cell"
            out.append("The cell door swung wide.")
    return out


def _r_brighten_cell(world: World) -> list[str]:
    out: list[str] = []
    cell = world.get("cell")
    if cell.meters["lit"] >= THRESHOLD:
        sig = ("lit", cell.id)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("The dark corner grew bright enough to see.")
    return out


CAUSAL_RULES = [
    Rule("open_cell", "physical", _r_open_cell),
    Rule("brighten_cell", "physical", _r_brighten_cell),
]


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


def cell_at_risk(magic: Magic, cell: Cell) -> bool:
    return (magic.opens and "lock" in cell.can_open_with) or (magic.brightens and "darkness" in cell.tags)


def select_magic(magic: Magic, cell: Cell) -> bool:
    return cell_at_risk(magic, cell) and magic.power >= MAGIC_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for mid, magic in MAGICS.items():
            for cid, cell in CELLS.items():
                if place in SETTINGS and select_magic(magic, cell) and place in SETTINGS:
                    combos.append((place, mid, cid))
    return combos


def predict(world: World, hero: Entity, magic: Magic, cell: Cell) -> dict:
    sim = world.copy()
    use_magic(sim, sim.get(hero.id), magic, narrate=False)
    c = sim.get("cell")
    return {"opened": c.meters["opened"] >= THRESHOLD, "lit": c.meters["lit"] >= THRESHOLD}


def use_magic(world: World, hero: Entity, magic: Magic, narrate: bool = True) -> None:
    cell = world.get("cell")
    if magic.opens:
        cell.meters["opened"] += 1
    if magic.brightens:
        cell.meters["lit"] += 1
    hero.memes["hope"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity, helper: Entity, cell: Cell) -> None:
    world.say(
        f"Long ago, in {world.setting.place}, there lived a little {hero.type} named {hero.id} "
        f"and a kind {helper.label_word} who watched over {cell.label}."
    )
    world.say(
        f"The {cell.label} was {cell.phrase}, and its {cell.lock} kept the way shut while the "
        f"{cell.window} let in only a thin bit of light."
    )


def show_duty(world: World, hero: Entity, helper: Entity, cell: Cell, magic: Magic) -> None:
    helper.memes["worry"] += 1
    hero.memes["wish"] += 1
    world.say(
        f"{hero.id} wanted to {cell.needs}, but {helper.pronoun('possessive')} {helper.label_word} "
        f"said the {cell.label} must stay closed until the right {magic.label} was found."
    )


def tempt(world: World, hero: Entity, magic: Magic) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"Then {hero.id} found {magic.phrase}. It seemed to hum like a tiny song, and "
        f"{hero.pronoun()} held it close."
    )


def warn(world: World, helper: Entity, hero: Entity, cell: Cell, magic: Magic) -> None:
    pred = predict(world, hero, magic, cell)
    helper.memes["caution"] += 1
    if pred["opened"]:
        world.say(
            f'"Take care," said {helper.id}. "A true {magic.label} can open {cell.label}, '
            f"but it must be used with kindness."'
        )
    else:
        world.say(
            f'"Take care," said {helper.id}. "Not every shining thing is the right {magic.label}."'
        )


def accept_magic(world: World, hero: Entity, helper: Entity, magic: Magic, cell: Cell) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{hero.id} nodded, and {helper.id} guided {hero.pronoun('object')} to the right charm."
    )
    use_magic(world, hero, magic)
    world.say(
        f"At once, {magic.effect}, and the {cell.label} changed."
    )


def resolve(world: World, hero: Entity, helper: Entity, cell: Cell, magic: Magic) -> None:
    world.para()
    world.say(
        f"{hero.id} and {helper.id} stepped through the opening together. "
        f"{hero.id} looked back once, then smiled at the bright doorway."
    )
    world.say(
        f"By the end, the {cell.label} was no longer a prison but a doorway, and the little "
        f"{hero.type} felt brave enough to begin a new path."
    )


def tell(setting: Setting, hero_name: str, hero_type: str, helper_type: str, cell_cfg: Cell, magic: Magic) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="wise keeper"))
    cell = world.add(Entity(id="cell", type="cell", label=cell_cfg.label, phrase=cell_cfg.phrase))
    cell.meters["opened"] = 0.0
    cell.meters["lit"] = 0.0

    introduce(world, hero, helper, cell_cfg)
    show_duty(world, hero, helper, cell_cfg, magic)
    world.para()
    tempt(world, hero, magic)
    warn(world, helper, hero, cell_cfg, magic)
    accept_magic(world, hero, helper, magic, cell_cfg)
    resolve(world, hero, helper, cell_cfg, magic)

    world.facts.update(hero=hero, helper=helper, cell=cell_cfg, magic=magic, setting=setting)
    return world


SETTINGS = {
    "tower": Setting(place="the moonlit tower", mood="quiet", affords={"magic"}),
    "castle": Setting(place="the old castle", mood="gentle", affords={"magic"}),
    "garden": Setting(place="the rose garden", mood="soft", affords={"magic"}),
}

CELLS = {
    "tower_cell": Cell(
        id="tower_cell",
        label="cell",
        phrase="a small stone room with a narrow window",
        lock="iron lock",
        window="tiny window",
        dim="dim",
        needs="see the stars",
        can_open_with={"lock"},
        tags={"darkness"},
    ),
    "garden_cell": Cell(
        id="garden_cell",
        label="cell",
        phrase="a little gate-house with a sleepy door",
        lock="silver latch",
        window="glass slit",
        dim="dim",
        needs="find the path home",
        can_open_with={"lock"},
        tags={"darkness"},
    ),
}

MAGICS = {
    "moon_key": Magic(
        id="moon_key",
        label="moon key",
        phrase="a moon key that glimmered in the grass",
        effect="the lock turned like it had been waiting all night",
        power=2,
        opens=True,
        tags={"key", "magic"},
    ),
    "star_spell": Magic(
        id="star_spell",
        label="star spell",
        phrase="a star spell whispered through the air",
        effect="the air filled with silver sparks and the latch loosened",
        power=2,
        opens=True,
        brightens=True,
        tags={"spell", "magic"},
    ),
    "lantern_charm": Magic(
        id="lantern_charm",
        label="lantern charm",
        phrase="a lantern charm tucked beneath a fern",
        effect="a warm glow woke up in the corners",
        power=1,
        brightens=True,
        tags={"charm", "magic"},
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Meri", "Elin", "Nora", "Tessa"]
BOY_NAMES = ["Finn", "Oren", "Pip", "Theo", "Lio", "Bram"]


@dataclass
class StoryParams:
    setting: str
    cell: str
    magic: str
    hero_name: str
    hero_type: str
    helper_type: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "cell": [("What is a cell?", "A cell is a small enclosed room with walls and a door. It can be dark and closed."րի)],
    "magic": [("What is magic in a fairy tale?", "Magic in a fairy tale is a special kind of wonder that can change things in surprising ways.")],
    "key": [("What does a key do?", "A key can unlock a lock so a door or gate can open.")],
    "darkness": [("Why is a dark room hard to use?", "A dark room is hard to use because you cannot see well inside it.")],
}
