#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/forester_fiat_land_sound_effects_moral_value.py
============================================================================

A standalone story world about two children playing at pirates on the edge of a
piece of land, hearing strange sounds around a parked fiat, and solving the
mystery with help from a forester.

The domain is built for child-facing TinyStories-style tales with:
- sound effects
- a mystery to solve
- a moral value
- a pirate-tale flavor

Core pattern
------------
The children turn a small edge of land into a pirate island. A strange sound
comes from near a fiat. One child may jump to a wild blame, but the other
pushes for clues and help. A forester reads the land carefully, solves the
mystery, fixes the small problem, and teaches the children not to blame before
they understand what happened.

Run it
------
python storyworlds/worlds/gpt-5.4/forester_fiat_land_sound_effects_moral_value.py
python storyworlds/worlds/gpt-5.4/forester_fiat_land_sound_effects_moral_value.py --all
python storyworlds/worlds/gpt-5.4/forester_fiat_land_sound_effects_moral_value.py --land pine_edge --cause branch_scrape
python storyworlds/worlds/gpt-5.4/forester_fiat_land_sound_effects_moral_value.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/forester_fiat_land_sound_effects_moral_value.py --trace --seed 777
python storyworlds/worlds/gpt-5.4/forester_fiat_land_sound_effects_moral_value.py --json
python storyworlds/worlds/gpt-5.4/forester_fiat_land_sound_effects_moral_value.py --asp
python storyworlds/worlds/gpt-5.4/forester_fiat_land_sound_effects_moral_value.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
CAREFUL_TRAITS = {"careful", "patient", "thoughtful", "steady"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    movable: bool = False
    parked: bool = False
    # physical + emotional dimensions
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man", "forester"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Land:
    id: str
    label: str
    opening: str
    pirate_name: str
    detail: str
    allows: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Cause:
    id: str
    clue: str
    sound: str
    source_label: str
    fix: str
    result_image: str
    requires: set[str] = field(default_factory=set)
    danger: int = 1
    sense: int = 3
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Theme:
    id: str
    rig: str
    captain_word: str
    mate_word: str
    quest: str
    sailing_end: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Lesson:
    id: str
    line: str
    short: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"guesser", "watcher"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


def _r_hear_fear(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("noise_on") is not True:
        return out
    sig = ("hear_fear",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["fear"] += 1
        kid.memes["curiosity"] += 1
    world.get("fiat").meters["mystery"] += 1
    out.append("__mystery__")
    return out


def _r_blame_conflict(world: World) -> list[str]:
    out: list[str] = []
    accuser = world.facts.get("accuser")
    if not accuser:
        return out
    kid = world.get(accuser)
    if kid.memes["blame"] < THRESHOLD:
        return out
    sig = ("blame_conflict", accuser)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for other in world.kids():
        if other.id != accuser:
            other.memes["worry"] += 1
    world.get("land").memes["tension"] += 1
    out.append("__blame__")
    return out


def _r_solve_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("solved") is not True:
        return out
    sig = ("solve_relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["trust"] += 1
        kid.memes["wonder"] += 1
    world.get("fiat").meters["mystery"] = 0.0
    world.get("land").memes["tension"] = 0.0
    out.append("__solved__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="hear_fear", tag="emotional", apply=_r_hear_fear),
    Rule(name="blame_conflict", tag="social", apply=_r_blame_conflict),
    Rule(name="solve_relief", tag="emotional", apply=_r_solve_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def cause_fits(land: Land, cause: Cause) -> bool:
    return bool(cause.requires & land.allows) or cause.requires <= land.allows


def sensible_lessons() -> list[Lesson]:
    return [l for l in LESSONS.values()]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for land_id, land in LANDS.items():
        for cause_id, cause in CAUSES.items():
            if not cause_fits(land, cause):
                continue
            for lesson_id in LESSONS:
                out.append((land_id, cause_id, lesson_id))
    return out


def initial_patience(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_blame_first(trait: str, bravery: int) -> bool:
    return bravery >= 6 and initial_patience(trait) < 5.0


def predict_noise(world: World, cause_id: str) -> dict:
    sim = world.copy()
    sim.facts["noise_on"] = True
    sim.facts["cause_id"] = cause_id
    propagate(sim, narrate=False)
    return {
        "mystery": sim.get("fiat").meters["mystery"],
        "fear": sum(k.memes["fear"] for k in sim.kids()),
    }


def pirate_setup(world: World, a: Entity, b: Entity, land: Land, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {a.id} and {b.id} turned {land.label} into {land.pirate_name}. "
        f"{theme.rig}"
    )
    world.say(land.opening)
    world.say(
        f'"{theme.captain_word} {a.id} and {theme.mate_word} {b.id}!" {a.id} cried. '
        f'"Today we will {theme.quest}!"'
    )


def arrive_fiat(world: World, fiat: Entity, land: Land) -> None:
    world.say(
        f"Near the edge of the land stood a little fiat, red as a berry, with sunlight on its windows. "
        f"{land.detail}"
    )


def mystery_sound(world: World, a: Entity, b: Entity, cause: Cause) -> None:
    world.facts["noise_on"] = True
    propagate(world, narrate=False)
    world.say(
        f"Then the quiet broke. {cause.sound} came from near the fiat. "
        f"{b.id} froze and grabbed {a.id}'s sleeve."
    )


def guess_and_warn(world: World, a: Entity, b: Entity, cause: Cause, forester: Entity) -> None:
    pred = predict_noise(world, cause.id)
    world.facts["predicted_fear"] = pred["fear"]
    if would_blame_first(a.traits[0], int(a.memes["bravery"])):
        a.memes["blame"] += 1
        world.facts["accuser"] = a.id
        propagate(world, narrate=False)
        world.say(
            f'"A land pirate is hiding there!" {a.id} whispered. '
            f'For one breath, the guess felt exciting.'
        )
        world.say(
            f'{b.id} shook {b.pronoun("possessive")} head. '
            f'"Maybe not. We should look for clues and ask the forester before we blame anyone."'
        )
    else:
        b.memes["care"] += 1
        world.say(
            f'{a.id} leaned closer, but {b.id} touched {a.pronoun("possessive")} arm. '
            f'"Let\'s not make up a bad story," {b.pronoun()} said. '
            f'"We should find clues and ask the forester."'
        )
    forester.memes["authority"] += 1


def call_forester(world: World, forester: Entity, cause: Cause) -> None:
    world.say(
        f'Soon the forester came along the path, boots softly crunching. '
        f'He listened once -- {cause.sound.lower()} -- and then knelt to study the ground.'
    )


def inspect_clues(world: World, forester: Entity, cause: Cause) -> None:
    forester.memes["care"] += 1
    world.say(
        f'He did not hurry. He looked at the fiat, then at the grass, then at the little marks nearby. '
        f'"I see the clue," he said. "{cause.clue}"'
    )


def solve_mystery(world: World, forester: Entity, fiat: Entity, cause: Cause, lesson: Lesson) -> None:
    world.facts["solved"] = True
    fiat.meters["rattle"] = 0.0
    fiat.meters["safe"] += 1
    world.get("land").meters["order"] += 1
    propagate(world, narrate=False)
    world.say(
        f'The forester smiled. "It is no pirate at all," he said. '
        f'"It is {cause.source_label}."'
    )
    world.say(
        f"With calm hands he {cause.fix}. At once the strange sound stopped."
    )
    world.say(
        f'"That is why we learn the land before we point a finger," he said. '
        f'"{lesson.line}"'
    )


def bright_ending(world: World, a: Entity, b: Entity, fiat: Entity, land: Land, theme: Theme, cause: Cause) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"{a.id} looked at {b.id}, and both children laughed a little at their own big guesses."
    )
    world.say(
        f"Now the fiat stood quiet, the land felt friendly again, and {cause.result_image}"
    )
    world.say(
        f'Together they marched back into {land.pirate_name}. '
        f'This time they were braver in the truest way -- watching closely, speaking kindly, and ready to {theme.sailing_end}.'
    )


def tell(
    land: Land,
    cause: Cause,
    lesson: Lesson,
    theme: Theme,
    *,
    guesser: str = "Tom",
    guesser_gender: str = "boy",
    watcher: str = "Lily",
    watcher_gender: str = "girl",
    forester_name: str = "Marek",
    guesser_trait: str = "bold",
    watcher_trait: str = "careful",
) -> World:
    world = World()
    a = world.add(Entity(
        id=guesser,
        kind="character",
        type=guesser_gender,
        label=guesser,
        traits=[guesser_trait],
        role="guesser",
    ))
    b = world.add(Entity(
        id=watcher,
        kind="character",
        type=watcher_gender,
        label=watcher,
        traits=[watcher_trait],
        role="watcher",
    ))
    forester = world.add(Entity(
        id=forester_name,
        kind="character",
        type="forester",
        label="the forester",
        traits=["steady"],
        role="helper",
    ))
    fiat = world.add(Entity(
        id="fiat",
        type="car",
        label="the fiat",
        parked=True,
        movable=True,
    ))
    land_ent = world.add(Entity(
        id="land",
        type="place",
        label=land.label,
    ))

    a.memes["bravery"] = 6.0
    b.memes["care"] = initial_patience(watcher_trait)
    fiat.meters["rattle"] = float(cause.danger)
    fiat.meters["mystery"] = 0.0
    land_ent.meters["order"] = 0.0
    land_ent.memes["tension"] = 0.0

    world.facts.update(
        land_cfg=land,
        cause_cfg=cause,
        lesson_cfg=lesson,
        theme_cfg=theme,
        guesser=a,
        watcher=b,
        forester=forester,
        fiat=fiat,
        noise_on=False,
        solved=False,
        accuser="",
    )

    pirate_setup(world, a, b, land, theme)
    arrive_fiat(world, fiat, land)

    world.para()
    mystery_sound(world, a, b, cause)
    guess_and_warn(world, a, b, cause, forester)
    call_forester(world, forester, cause)

    world.para()
    inspect_clues(world, forester, cause)
    solve_mystery(world, forester, fiat, cause, lesson)

    world.para()
    bright_ending(world, a, b, fiat, land, theme, cause)
    world.facts["blamed_first"] = a.memes["blame"] >= THRESHOLD
    return world


LANDS = {
    "pine_edge": Land(
        id="pine_edge",
        label="the pine-edge land",
        opening="A strip of sandy ground ran to the trees, and pine needles made a soft brown deck under their shoes.",
        pirate_name="Needle Island",
        detail="Behind it, the pines leaned and whispered over the land.",
        allows={"branch", "cone", "track"},
        tags={"pine", "land"},
    ),
    "orchard_gate": Land(
        id="orchard_gate",
        label="the orchard land",
        opening="Old apple trees stood in rows like watchmen, and a gate leaned beside the lane.",
        pirate_name="Apple Hook Island",
        detail="The wind moved the high leaves, and the lane crossed the land like a narrow river.",
        allows={"gate", "apple", "track"},
        tags={"orchard", "land"},
    ),
    "river_bank": Land(
        id="river_bank",
        label="the river-bank land",
        opening="The bank sloped down to clear water, and little stones flashed silver at the edge.",
        pirate_name="Silver Bank Island",
        detail="A stony path curved over the land before it reached the reeds.",
        allows={"pebble", "reed", "track"},
        tags={"river", "land"},
    ),
}

CAUSES = {
    "branch_scrape": Cause(
        id="branch_scrape",
        clue="A bent pine branch is brushing the roof whenever the wind pushes it.",
        sound="Scrrritch... tap-tap... scrrritch!",
        source_label="a pine branch scraping the fiat roof",
        fix="lifted the branch away and tied it back with a soft green cord",
        result_image="the tied branch nodded high above the car like a quiet mast rope",
        requires={"branch"},
        danger=1,
        sense=3,
        tags={"branch", "sound", "fiat"},
    ),
    "loose_gate": Cause(
        id="loose_gate",
        clue="The wind is swinging the loose gate until its latch knocks the fiat bumper.",
        sound="Clang-clang... bonk!",
        source_label="a loose gate knocking the fiat bumper",
        fix="set the latch properly and looped a rope around the gate so it would stay still",
        result_image="the gate rested neatly by the lane, and not even a puff of wind could wake it",
        requires={"gate"},
        danger=1,
        sense=3,
        tags={"gate", "sound", "fiat"},
    ),
    "pebble_click": Cause(
        id="pebble_click",
        clue="A little pebble is stuck in the tire tread from the stony track.",
        sound="Tick-tick... tick!",
        source_label="a pebble clicking in the fiat tire",
        fix="knelt beside the wheel and picked the pebble free",
        result_image="the small gray pebble sat harmless in the forester's palm",
        requires={"pebble", "track"},
        danger=1,
        sense=3,
        tags={"wheel", "sound", "fiat"},
    ),
    "apple_plonk": Cause(
        id="apple_plonk",
        clue="Wind-shaken apples are dropping from the branch onto the fiat roof.",
        sound="Plonk! plonk-plonk!",
        source_label="ripe apples falling onto the fiat roof",
        fix="moved the fiat a little and gathered the fallen apples into a basket",
        result_image="the basket of apples glowed red beside the quiet little car",
        requires={"apple"},
        danger=1,
        sense=3,
        tags={"apple", "sound", "fiat"},
    ),
}

THEMES = {
    "pirates": Theme(
        id="pirates",
        rig="A wheelbarrow was their ship, a stick was their spyglass, and a striped towel was their brave flag.",
        captain_word="Captain",
        mate_word="Mate",
        quest="find the hidden map of the shore",
        sailing_end="sail their game with open eyes",
    ),
    "corsairs": Theme(
        id="corsairs",
        rig="A wooden crate was their deck, a rake was their anchor, and a blue scarf flapped like a sea flag.",
        captain_word="Captain",
        mate_word="Scout",
        quest="search for the lost chest of morning light",
        sailing_end="steer their adventure by good sense",
    ),
}

LESSONS = {
    "ask_first": Lesson(
        id="ask_first",
        line="When a noise feels scary, ask and learn before you accuse.",
        short="Ask and learn before you accuse.",
        tags={"kindness", "moral"},
    ),
    "care_land": Lesson(
        id="care_land",
        line="Kind people care for the land and the things on it by noticing small problems early.",
        short="Notice small problems and care for the land.",
        tags={"care", "moral"},
    ),
    "clues_first": Lesson(
        id="clues_first",
        line="Good hearts use clues first and blame last.",
        short="Use clues first and blame last.",
        tags={"fairness", "moral"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
FORESTER_NAMES = ["Marek", "Oren", "Tomas", "Jonas", "Pavel"]
BOLD_TRAITS = ["bold", "curious", "eager", "restless"]
WATCHER_TRAITS = ["careful", "patient", "thoughtful", "steady"]


@dataclass
class StoryParams:
    land: str
    cause: str
    lesson: str
    theme: str
    guesser: str
    guesser_gender: str
    watcher: str
    watcher_gender: str
    forester_name: str
    guesser_trait: str
    watcher_trait: str
    seed: Optional[int] = None
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


KNOWLEDGE = {
    "forester": [
        (
            "What does a forester do?",
            "A forester cares for woods and land. A forester notices trees, paths, and small problems that other people might miss.",
        )
    ],
    "fiat": [
        (
            "What is a fiat?",
            "A fiat is a kind of small car. Like any car, it can make sounds when something brushes it or a little stone gets caught near a wheel.",
        )
    ],
    "land": [
        (
            "What does it mean to care for land?",
            "Caring for land means noticing what is growing there, keeping it safe, and fixing small problems before they become bigger ones.",
        )
    ],
    "sound": [
        (
            "Why can strange sounds seem bigger than they really are?",
            "A strange sound can feel scary when you do not know its cause. Once you find the real source, the mystery often becomes much smaller.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you understand what really happened. Good clue-finders look carefully before they decide.",
        )
    ],
    "kindness": [
        (
            "Why is it kinder not to blame right away?",
            "Blaming too fast can hurt someone who did nothing wrong. It is kinder to ask questions and learn the truth first.",
        )
    ],
    "care": [
        (
            "Why should people fix little problems on land early?",
            "Small problems are easier to fix while they are still small. A tied branch or shut gate can stop noise and keep things safe.",
        )
    ],
}
KNOWLEDGE_ORDER = ["forester", "fiat", "land", "sound", "clue", "kindness", "care"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    land = f["land_cfg"]
    cause = f["cause_cfg"]
    lesson = f["lesson_cfg"]
    a = f["guesser"]
    b = f["watcher"]
    return [
        f'Write a pirate-tale-flavored story for a 3-to-5-year-old that includes the words "forester", "fiat", and "land". '
        f'The children hear a strange sound on {land.label} and solve a mystery.',
        f"Tell a gentle mystery story where {a.id} and {b.id} pretend to be pirates, hear {cause.sound.lower()} near a fiat, "
        f"and a forester explains the true cause.",
        f'Write a child-facing story with sound effects and the moral "{lesson.short}" and end with the children returning to play.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["guesser"]
    b = f["watcher"]
    forester = f["forester"]
    land = f["land_cfg"]
    cause = f["cause_cfg"]
    lesson = f["lesson_cfg"]
    blamed = f.get("blamed_first", False)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.id} and {b.id}, two children playing pirates on {land.label}, and {forester.id} the forester. "
            f"The little fiat near the edge of the land becomes the center of their mystery.",
        ),
        (
            "What mystery did the children hear?",
            f"They heard {cause.sound.lower()} coming from near the fiat. "
            f"Because they could not see the cause at first, the sound felt bigger and stranger than it really was.",
        ),
        (
            "How did the forester solve the mystery?",
            f"He listened carefully, looked for clues, and found that the real cause was {cause.source_label}. "
            f"Then he {cause.fix}, which made the sound stop.",
        ),
    ]
    if blamed:
        qa.append(
            (
                f"Why was it important that {b.id} wanted clues first?",
                f"{a.id} almost blamed an imaginary land pirate before anyone knew the truth. "
                f"{b.id} slowed the story down and asked for clues, which helped the forester find the real cause fairly and kindly.",
            )
        )
    else:
        qa.append(
            (
                "What was the moral of the story?",
                f"The story teaches that {lesson.short.lower()} "
                f"That matters because careful looking kept the mystery from turning into an unfair guess.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the sound gone, the fiat quiet again, and the land feeling friendly instead of spooky. "
            f"The children returned to their pirate game wiser than before.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"forester", "fiat", "land", "sound", "clue"}
    if f["lesson_cfg"].id == "ask_first":
        tags.add("kindness")
    if f["lesson_cfg"].id == "care_land":
        tags.add("care")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  facts: solved={world.facts.get('solved')} blamed_first={world.facts.get('blamed_first')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        land="pine_edge",
        cause="branch_scrape",
        lesson="clues_first",
        theme="pirates",
        guesser="Tom",
        guesser_gender="boy",
        watcher="Lily",
        watcher_gender="girl",
        forester_name="Marek",
        guesser_trait="bold",
        watcher_trait="careful",
    ),
    StoryParams(
        land="orchard_gate",
        cause="loose_gate",
        lesson="ask_first",
        theme="corsairs",
        guesser="Max",
        guesser_gender="boy",
        watcher="Mia",
        watcher_gender="girl",
        forester_name="Oren",
        guesser_trait="eager",
        watcher_trait="patient",
    ),
    StoryParams(
        land="river_bank",
        cause="pebble_click",
        lesson="care_land",
        theme="pirates",
        guesser="Sam",
        guesser_gender="boy",
        watcher="Zoe",
        watcher_gender="girl",
        forester_name="Jonas",
        guesser_trait="curious",
        watcher_trait="thoughtful",
    ),
    StoryParams(
        land="orchard_gate",
        cause="apple_plonk",
        lesson="care_land",
        theme="pirates",
        guesser="Ella",
        guesser_gender="girl",
        watcher="Ben",
        watcher_gender="boy",
        forester_name="Pavel",
        guesser_trait="bold",
        watcher_trait="steady",
    ),
]


def explain_rejection(land: Land, cause: Cause) -> str:
    need = ", ".join(sorted(cause.requires))
    have = ", ".join(sorted(land.allows))
    return (
        f"(No story: {cause.id} needs land features {need}, but {land.id} only offers {have}. "
        f"The mystery must fit the land before the forester can solve it.)"
    )


ASP_RULES = r"""
fits(L, C) :- land(L), cause(C), requires(C, Need), allows(L, Need).
missing_need(L, C) :- land(L), cause(C), requires(C, Need), not allows(L, Need).
cause_ok(L, C) :- cause(C), land(L), not missing_need(L, C).
valid(L, C, M) :- land(L), cause(C), lesson(M), cause_ok(L, C).

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for land_id, land in LANDS.items():
        lines.append(asp.fact("land", land_id))
        for feat in sorted(land.allows):
            lines.append(asp.fact("allows", land_id, feat))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        for req in sorted(cause.requires):
            lines.append(asp.fact("requires", cause_id, req))
    for lesson_id in LESSONS:
        lines.append(asp.fact("lesson", lesson_id))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and valid_combos():")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "forester" not in sample.story.lower() or "fiat" not in sample.story.lower():
            raise StoryError("Smoke test story is missing required content.")
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: pirate-flavored mystery with a forester, a fiat, and a piece of land."
    )
    ap.add_argument("--land", choices=LANDS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from ASP")
    ap.add_argument("--verify", action="store_true", help="verify ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.land and args.cause:
        land = LANDS[args.land]
        cause = CAUSES[args.cause]
        if not cause_fits(land, cause):
            raise StoryError(explain_rejection(land, cause))

    combos = [
        combo
        for combo in valid_combos()
        if (args.land is None or combo[0] == args.land)
        and (args.cause is None or combo[1] == args.cause)
        and (args.lesson is None or combo[2] == args.lesson)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    land_id, cause_id, lesson_id = rng.choice(sorted(combos))
    theme_id = args.theme or rng.choice(sorted(THEMES))
    guesser_gender = rng.choice(["girl", "boy"])
    watcher_gender = "boy" if guesser_gender == "girl" and rng.random() < 0.5 else "girl"
    guesser = _pick_name(rng, guesser_gender)
    watcher = _pick_name(rng, watcher_gender, avoid=guesser)
    return StoryParams(
        land=land_id,
        cause=cause_id,
        lesson=lesson_id,
        theme=theme_id,
        guesser=guesser,
        guesser_gender=guesser_gender,
        watcher=watcher,
        watcher_gender=watcher_gender,
        forester_name=rng.choice(FORESTER_NAMES),
        guesser_trait=rng.choice(BOLD_TRAITS),
        watcher_trait=rng.choice(WATCHER_TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.land not in LANDS:
        raise StoryError(f"(Unknown land: {params.land})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.lesson not in LESSONS:
        raise StoryError(f"(Unknown lesson: {params.lesson})")
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    land = LANDS[params.land]
    cause = CAUSES[params.cause]
    if not cause_fits(land, cause):
        raise StoryError(explain_rejection(land, cause))

    world = tell(
        land=land,
        cause=cause,
        lesson=LESSONS[params.lesson],
        theme=THEMES[params.theme],
        guesser=params.guesser,
        guesser_gender=params.guesser_gender,
        watcher=params.watcher,
        watcher_gender=params.watcher_gender,
        forester_name=params.forester_name,
        guesser_trait=params.guesser_trait,
        watcher_trait=params.watcher_trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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

    if args.show_asp:
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (land, cause, lesson) combos:\n")
        for land_id, cause_id, lesson_id in combos:
            print(f"  {land_id:12} {cause_id:14} {lesson_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.guesser} & {p.watcher}: {p.cause} on {p.land} ({p.lesson})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
