#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/exhibition_scrounge_misunderstanding_whodunit.py
============================================================================

A small storyworld about a child's "whodunit" at an exhibition: something from a
display seems to vanish, a helpful friend slips away to scrounge repair supplies,
and a misunderstanding turns that ordinary errand into a mystery. The live world
state decides what went missing, why it disappeared, where it ended up, what clue
misled the sleuth, and how the apology and repair play out.

Run it
------
    python storyworlds/worlds/gpt-5.4/exhibition_scrounge_misunderstanding_whodunit.py
    python storyworlds/worlds/gpt-5.4/exhibition_scrounge_misunderstanding_whodunit.py --exhibition space --missing label_card
    python storyworlds/worlds/gpt-5.4/exhibition_scrounge_misunderstanding_whodunit.py --cause roll
    python storyworlds/worlds/gpt-5.4/exhibition_scrounge_misunderstanding_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/exhibition_scrounge_misunderstanding_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/exhibition_scrounge_misunderstanding_whodunit.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
        female = {"girl", "mother", "woman", "teacher"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "teacher": "teacher"}.get(self.type, self.type)
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
class Exhibition:
    id: str
    title: str
    place: str
    setup: str
    affordances: set[str] = field(default_factory=set)
    ending_image: str = ""
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
class MissingThing:
    id: str
    label: str
    phrase: str
    exhibit_phrase: str
    trait: str
    repair_kind: str
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    affordance: str
    traits: set[str]
    hide_place: str
    evidence: str
    action: str
    find_line: str
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
class Supply:
    id: str
    label: str
    phrase: str
    fixes: set[str]
    errand: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
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
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        return clone


def _r_missing_alarm(world: World) -> list[str]:
    item = world.get("item")
    sleuth = world.get("sleuth")
    room = world.get("room")
    if item.meters["missing"] >= THRESHOLD and ("missing_alarm",) not in world.fired:
        world.fired.add(("missing_alarm",))
        sleuth.memes["worry"] += 1
        room.meters["mystery"] += 1
    return []


def _r_accusation_hurts(world: World) -> list[str]:
    sleuth = world.get("sleuth")
    suspect = world.get("suspect")
    if suspect.memes["accused"] >= THRESHOLD and suspect.attrs.get("innocent") and ("hurt",) not in world.fired:
        world.fired.add(("hurt",))
        suspect.memes["hurt"] += 1
        sleuth.memes["guilt"] += 1
    return []


def _r_repair_relief(world: World) -> list[str]:
    item = world.get("item")
    sleuth = world.get("sleuth")
    suspect = world.get("suspect")
    if item.meters["restored"] >= THRESHOLD and ("relief",) not in world.fired:
        world.fired.add(("relief",))
        sleuth.memes["relief"] += 1
        suspect.memes["relief"] += 1
        sleuth.memes["trust"] += 1
        suspect.memes["trust"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_alarm", tag="mystery", apply=_r_missing_alarm),
    Rule(name="accusation_hurts", tag="social", apply=_r_accusation_hurts),
    Rule(name="repair_relief", tag="resolution", apply=_r_repair_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def cause_possible(exhibition: Exhibition, item: MissingThing, cause: Cause) -> bool:
    return cause.affordance in exhibition.affordances and item.trait in cause.traits


def supply_fits(item: MissingThing, supply: Supply) -> bool:
    return item.repair_kind in supply.fixes


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for ex_id, ex in EXHIBITIONS.items():
        for item_id, item in MISSING_THINGS.items():
            for cause_id, cause in CAUSES.items():
                if not cause_possible(ex, item, cause):
                    continue
                for supply_id, supply in SUPPLIES.items():
                    if supply_fits(item, supply):
                        out.append((ex_id, item_id, cause_id, supply_id))
    return out


def explain_rejection(exhibition: Exhibition, item: MissingThing, cause: Cause, supply: Optional[Supply] = None) -> str:
    if not cause_possible(exhibition, item, cause):
        return (
            f"(No story: {cause.id} needs {cause.affordance}, but {exhibition.title} does not provide that, "
            f"or {item.the} is the wrong kind of object for that accident. Pick a cause that can really move "
            f"{item.the} in this exhibition.)"
        )
    if supply is not None and not supply_fits(item, supply):
        return (
            f"(No story: {supply.label} would not honestly fix {item.the}. The friend can scrounge only a "
            f"supply that helps restore the missing part of the exhibit.)"
        )
    return "(No story: that combination is not reasonable.)"


def predict_hiding_place(world: World, cause: Cause) -> dict:
    sim = world.copy()
    item = sim.get("item")
    item.meters["missing"] += 1
    item.attrs["hidden_at"] = cause.hide_place
    propagate(sim, narrate=False)
    return {
        "hide_place": item.attrs.get("hidden_at", cause.hide_place),
        "evidence": cause.evidence,
    }


def opening(world: World, sleuth: Entity, suspect: Entity, adult: Entity,
            exhibition: Exhibition, item: MissingThing) -> None:
    sleuth.memes["pride"] += 1
    suspect.memes["helpful"] += 1
    world.say(
        f"On exhibition day at {exhibition.place}, {sleuth.id} felt like a tiny detective and a proud curator all at once. "
        f"{exhibition.setup}"
    )
    world.say(
        f"{suspect.id} helped straighten the display while {adult.label_word} checked the tables and smiled at the busy room."
    )
    world.say(
        f"In the middle of it all sat {item.exhibit_phrase}, and {sleuth.id} kept glancing back at {item.the} just to make sure it still looked perfect."
    )


def helpful_errand(world: World, suspect: Entity, supply: Supply) -> None:
    suspect.attrs["went_for_supply"] = supply.id
    suspect.memes["purpose"] += 1
    world.say(
        f"Then {suspect.id} noticed the display looked a little loose. \"I'll go scrounge {supply.phrase},\" {suspect.pronoun()} said, and hurried toward the supply cupboard."
    )


def disappearance(world: World, sleuth: Entity, item: Entity, item_cfg: MissingThing, cause: Cause) -> None:
    item.meters["missing"] += 1
    item.attrs["hidden_at"] = cause.hide_place
    item.attrs["cause"] = cause.id
    propagate(world, narrate=False)
    world.say(
        f"When {sleuth.id} turned back, {item_cfg.the} was gone. In its place there was only {cause.evidence}, which made the whole table feel suddenly suspicious."
    )


def misunderstanding(world: World, sleuth: Entity, suspect: Entity, cause: Cause) -> None:
    pred = predict_hiding_place(world, cause)
    world.facts["predicted_hide_place"] = pred["hide_place"]
    world.facts["predicted_evidence"] = pred["evidence"]
    suspect.memes["accused"] += 1
    propagate(world, narrate=False)
    tone = "very small" if sleuth.memes["worry"] < 2 else "shaky"
    world.say(
        f"{sleuth.id} followed the clue with a {tone} voice. \"{suspect.id}, did you take it? You were the one who slipped away.\""
    )
    if suspect.memes["hurt"] >= THRESHOLD:
        world.say(
            f"{suspect.id} stopped short and blinked. \"No,\" {suspect.pronoun()} said. \"I was trying to help.\""
        )


def investigate(world: World, sleuth: Entity, suspect: Entity, exhibition: Exhibition,
                item_cfg: MissingThing, cause: Cause, adult: Entity) -> None:
    sleuth.memes["curious"] += 1
    world.say(
        f"But a good whodunit needs more than one clue, so {adult.label_word} crouched beside them and said, \"Let's look before we decide.\""
    )
    world.say(
        f"They studied the display. {cause.action.capitalize()}, and that made {cause.find_line}"
    )
    world.say(
        f"{sleuth.id} looked where the clue pointed, not where the worry pointed, and suddenly the mystery began to shrink."
    )


def reveal(world: World, sleuth: Entity, suspect: Entity, item: Entity,
           item_cfg: MissingThing, cause: Cause, supply: Supply) -> None:
    item.meters["missing"] = 0.0
    item.meters["found"] += 1
    item.attrs["found_at"] = cause.hide_place
    suspect.memes["helpful"] += 1
    world.say(
        f"There, at {cause.hide_place}, they found {item_cfg.the}. It had not been stolen at all; {cause.action}, and the clue only made it look like a crime."
    )
    world.say(
        f"At that very moment {suspect.id} came back with {supply.phrase}. \"See? I told you I was helping,\" {suspect.pronoun()} said, holding it up."
    )


def apology_and_repair(world: World, sleuth: Entity, suspect: Entity, adult: Entity,
                       item: Entity, item_cfg: MissingThing, supply: Supply) -> None:
    sleuth.memes["sorry"] += 1
    suspect.memes["forgiven"] += 1
    item.meters["restored"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{sleuth.id}'s cheeks turned pink. \"I'm sorry,\" {sleuth.pronoun()} said. \"I saw you run off and I misunderstood.\""
    )
    world.say(
        f"{adult.label_word.capitalize()} nodded. \"A clue is not the same as the truth,\" {adult.pronoun()} said gently."
    )
    world.say(
        f"Together they used {supply.phrase} to set {item_cfg.the} back where it belonged. The display stood neat again, and the little mystery ended with everyone closer than before."
    )


def ending(world: World, sleuth: Entity, suspect: Entity, exhibition: Exhibition) -> None:
    world.say(
        f"After that, whenever {sleuth.id} felt a mystery bubbling up, {sleuth.pronoun()} remembered to look twice before blaming anyone. Soon the room filled with visitors, and {exhibition.ending_image}"
    )


def tell(exhibition: Exhibition, item_cfg: MissingThing, cause: Cause, supply: Supply,
         sleuth_name: str = "Nora", sleuth_gender: str = "girl",
         suspect_name: str = "Ben", suspect_gender: str = "boy",
         adult_type: str = "teacher") -> World:
    world = World()
    sleuth = world.add(Entity(
        id=sleuth_name,
        kind="character",
        type=sleuth_gender,
        role="sleuth",
        traits=["careful"],
        attrs={},
    ))
    suspect = world.add(Entity(
        id=suspect_name,
        kind="character",
        type=suspect_gender,
        role="helper",
        traits=["helpful"],
        attrs={"innocent": True},
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        role="adult",
        label="the adult",
        attrs={},
    ))
    adult.label = adult.label_word
    room = world.add(Entity(
        id="room",
        type="room",
        label=exhibition.place,
        attrs={},
    ))
    item = world.add(Entity(
        id="item",
        type="display_part",
        label=item_cfg.label,
        role="missing",
        attrs={"hidden_at": "", "found_at": "", "cause": ""},
    ))
    world.facts.update(
        exhibition=exhibition,
        item_cfg=item_cfg,
        cause=cause,
        supply=supply,
        sleuth=sleuth,
        suspect=suspect,
        adult=adult,
        item=item,
    )

    opening(world, sleuth, suspect, adult, exhibition, item_cfg)
    world.para()
    helpful_errand(world, suspect, supply)
    disappearance(world, sleuth, item, item_cfg, cause)
    misunderstanding(world, sleuth, suspect, cause)
    world.para()
    investigate(world, sleuth, suspect, exhibition, item_cfg, cause, adult)
    reveal(world, sleuth, suspect, item, item_cfg, cause, supply)
    world.para()
    apology_and_repair(world, sleuth, suspect, adult, item, item_cfg, supply)
    ending(world, sleuth, suspect, exhibition)

    world.facts.update(
        hidden_at=item.attrs.get("hidden_at", cause.hide_place),
        found_at=item.attrs.get("found_at", cause.hide_place),
        misunderstanding=suspect.memes["accused"] >= THRESHOLD,
        apology=sleuth.memes["sorry"] >= THRESHOLD,
        restored=item.meters["restored"] >= THRESHOLD,
    )
    return world


EXHIBITIONS = {
    "shells": Exhibition(
        id="shells",
        title="the Seashell Corner",
        place="the school hall",
        setup="A blue cloth covered one table, tiny shells shone in rows, and a sign said THE SEASHELL CORNER in big careful letters.",
        affordances={"breeze", "cloth"},
        ending_image="the shell table gleamed under the paper fish, and the two helpers stood side by side, guarding it with happier smiles.",
        tags={"exhibition", "school"},
    ),
    "space": Exhibition(
        id="space",
        title="the Space Window",
        place="the library room",
        setup="Black paper stars hung above a tall easel, a cardboard moon leaned nearby, and a sign called the display THE SPACE WINDOW.",
        affordances={"breeze", "slope"},
        ending_image="the moon display looked steady again, and the children watched the line of visitors snake past like a parade of astronauts.",
        tags={"exhibition", "school"},
    ),
    "dinosaur": Exhibition(
        id="dinosaur",
        title="the Tiny Dinosaur Museum",
        place="the classroom",
        setup="A green cloth draped the table, toy bones sat in little trays, and a wooden stand lifted one proud paper tyrannosaur above the rest.",
        affordances={"cloth", "slope"},
        ending_image="the dinosaur table stood brave and tidy, and the paper tyrannosaur seemed to grin over a mystery solved the fair way.",
        tags={"exhibition", "school"},
    ),
}

MISSING_THINGS = {
    "label_card": MissingThing(
        id="label_card",
        label="label card",
        phrase="a neat label card",
        exhibit_phrase="a neat label card explaining the star of the exhibit",
        trait="flat",
        repair_kind="tape",
        tags={"label", "paper"},
    ),
    "rosette_badge": MissingThing(
        id="rosette_badge",
        label="rosette badge",
        phrase="a bright rosette badge",
        exhibit_phrase="a bright rosette badge pinned to the front of the display",
        trait="pinned",
        repair_kind="string",
        tags={"badge", "pin"},
    ),
    "marble_planet": MissingThing(
        id="marble_planet",
        label="marble planet",
        phrase="a shiny marble planet",
        exhibit_phrase="a shiny marble planet balanced in a little cardboard ring",
        trait="round",
        repair_kind="putty",
        tags={"marble", "planet"},
    ),
}

CAUSES = {
    "draft": Cause(
        id="draft",
        affordance="breeze",
        traits={"flat"},
        hide_place="the floor under the table",
        evidence="a corner fluttering and the window cracked open",
        action="a breeze from the open window had whisked it away",
        find_line="a trail of paper-edge peeking from the floor under the table",
        tags={"breeze", "window"},
    ),
    "snag": Cause(
        id="snag",
        affordance="cloth",
        traits={"pinned"},
        hide_place="the fold of the hanging cloth",
        evidence="one thread pulled loose in the cloth",
        action="the cloth had snagged it when someone brushed past",
        find_line="a bright edge tucked in the fold of the hanging cloth",
        tags={"cloth", "snag"},
    ),
    "roll": Cause(
        id="roll",
        affordance="slope",
        traits={"round"},
        hide_place="the shadow behind the slanted stand",
        evidence="a tiny scrape and a wobbling cardboard ring",
        action="the slanted stand had let it roll away",
        find_line="a glint in the shadow behind the slanted stand",
        tags={"slope", "roll"},
    ),
}

SUPPLIES = {
    "tape": Supply(
        id="tape",
        label="tape",
        phrase="a roll of tape",
        fixes={"tape"},
        errand="to fasten paper parts",
        tags={"tape", "repair"},
    ),
    "string": Supply(
        id="string",
        label="string",
        phrase="a piece of string",
        fixes={"string"},
        errand="to tie decorations back on",
        tags={"string", "repair"},
    ),
    "putty": Supply(
        id="putty",
        label="museum putty",
        phrase="a blob of soft putty",
        fixes={"putty"},
        errand="to stop round things from rolling",
        tags={"putty", "repair"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Zoe", "Ella", "Ruby", "Anna"]
BOY_NAMES = ["Ben", "Max", "Leo", "Finn", "Theo", "Sam", "Eli", "Noah"]


@dataclass
class StoryParams:
    exhibition: str
    missing: str
    cause: str
    supply: str
    sleuth_name: str
    sleuth_gender: str
    suspect_name: str
    suspect_gender: str
    adult: str
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
    "exhibition": [
        ("What is an exhibition?", "An exhibition is a place where people set out things to show and explain them to visitors. It is a way to share collections, art, or ideas.")
    ],
    "scrounge": [
        ("What does scrounge mean?", "To scrounge means to look around and gather something you need, often by checking drawers, shelves, or spare boxes. In a story, someone might scrounge tape or string to fix a problem.")
    ],
    "misunderstanding": [
        ("What is a misunderstanding?", "A misunderstanding happens when someone gets the wrong idea about what another person meant or did. It can make people feel hurt until the truth is explained.")
    ],
    "tape": [
        ("What is tape used for?", "Tape can hold paper or light things in place. It helps fix displays when a label or picture comes loose.")
    ],
    "string": [
        ("What can string do in a display?", "String can tie or hang light decorations and badges. It helps fasten something without making it too heavy.")
    ],
    "putty": [
        ("Why would a museum use putty?", "Soft putty can hold small objects still on a stand. That is useful when something round might roll away.")
    ],
    "breeze": [
        ("How can a breeze move paper?", "A breeze can push light paper because paper does not weigh very much. Even a small draft from a window can slide or lift it.")
    ],
    "roll": [
        ("Why do round things roll?", "Round things roll because their curved shape lets them move when a surface tips or gets bumped. That is why marbles can escape so quickly.")
    ],
    "cloth": [
        ("How can cloth catch something?", "Loose cloth can snag light things if an edge, pin, or thread catches on it. Then the object may get tucked into a fold.")
    ],
}
KNOWLEDGE_ORDER = ["exhibition", "scrounge", "misunderstanding", "breeze", "cloth", "roll", "tape", "string", "putty"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    ex = f["exhibition"]
    item = f["item_cfg"]
    cause = f["cause"]
    supply = f["supply"]
    sleuth = f["sleuth"]
    suspect = f["suspect"]
    return [
        f'Write a short whodunit for a 3-to-5-year-old set at an exhibition, where a child thinks {suspect.id} took {item.the} but the mystery is really a misunderstanding.',
        f'Write a gentle mystery story using the words "exhibition" and "scrounge" in which {suspect.id} goes to scrounge {supply.label}, a clue points the wrong way, and {sleuth.id} learns not to blame too quickly.',
        f"Tell a child-facing detective story at {ex.title} where {cause.action}, the missing object is found at {cause.hide_place}, and the ending includes an apology and a repaired display.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    sleuth = f["sleuth"]
    suspect = f["suspect"]
    adult = f["adult"]
    ex = f["exhibition"]
    item = f["item_cfg"]
    cause = f["cause"]
    supply = f["supply"]
    hide_place = f["hidden_at"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {sleuth.id}, who feels like a little detective at an exhibition, and {suspect.id}, who is trying to help. {adult.label_word.capitalize()} also helps them slow down and solve the mystery fairly."
        ),
        (
            f"What went missing at the exhibition?",
            f"{item.the.capitalize()} seemed to vanish from the display. That is what made the table feel like the start of a whodunit."
        ),
        (
            f"Why did {sleuth.id} think {suspect.id} took it?",
            f"{sleuth.id} saw {suspect.id} hurry away just before the object disappeared, so the clue and the timing pointed at the wrong person. It was a misunderstanding because {suspect.id} had gone to scrounge {supply.phrase} to help fix the display."
        ),
        (
            "What was the real reason the object went missing?",
            f"It had not been stolen at all. {cause.action.capitalize()}, which moved it to {hide_place}."
        ),
        (
            f"How did they solve the mystery?",
            f"They stopped blaming and looked carefully at the display and the clue. When they searched where the evidence really pointed, they found {item.the} and understood what had happened."
        ),
    ]
    if f.get("apology"):
        qa.append(
            (
                f"What did {sleuth.id} do after learning the truth?",
                f"{sleuth.id} apologized to {suspect.id} for blaming {suspect.pronoun('object')} too quickly. Then they used {supply.phrase} to repair the display, which showed the friendship had mended too."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"exhibition", "scrounge", "misunderstanding"}
    tags |= set(world.facts["cause"].tags)
    tags |= set(world.facts["supply"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        attrs = {k: v for k, v in ent.attrs.items() if v not in ("", None, False)}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        exhibition="space",
        missing="label_card",
        cause="draft",
        supply="tape",
        sleuth_name="Nora",
        sleuth_gender="girl",
        suspect_name="Ben",
        suspect_gender="boy",
        adult="teacher",
    ),
    StoryParams(
        exhibition="dinosaur",
        missing="rosette_badge",
        cause="snag",
        supply="string",
        sleuth_name="Max",
        sleuth_gender="boy",
        suspect_name="Lily",
        suspect_gender="girl",
        adult="teacher",
    ),
    StoryParams(
        exhibition="space",
        missing="marble_planet",
        cause="roll",
        supply="putty",
        sleuth_name="Ava",
        sleuth_gender="girl",
        suspect_name="Theo",
        suspect_gender="boy",
        adult="teacher",
    ),
    StoryParams(
        exhibition="shells",
        missing="label_card",
        cause="draft",
        supply="tape",
        sleuth_name="Ruby",
        sleuth_gender="girl",
        suspect_name="Finn",
        suspect_gender="boy",
        adult="teacher",
    ),
    StoryParams(
        exhibition="dinosaur",
        missing="rosette_badge",
        cause="snag",
        supply="string",
        sleuth_name="Leo",
        sleuth_gender="boy",
        suspect_name="Mia",
        suspect_gender="girl",
        adult="teacher",
    ),
]


ASP_RULES = r"""
possible_cause(E, I, C) :- exhibition(E), item(I), cause(C),
                           affords(E, A), cause_needs(C, A),
                           trait(I, T), cause_allows(C, T).

good_supply(I, S) :- item(I), supply(S), repair_kind(I, R), fixes(S, R).

valid(E, I, C, S) :- possible_cause(E, I, C), good_supply(I, S).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for ex_id, ex in EXHIBITIONS.items():
        lines.append(asp.fact("exhibition", ex_id))
        for aff in sorted(ex.affordances):
            lines.append(asp.fact("affords", ex_id, aff))
    for item_id, item in MISSING_THINGS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("trait", item_id, item.trait))
        lines.append(asp.fact("repair_kind", item_id, item.repair_kind))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("cause_needs", cause_id, cause.affordance))
        for trait in sorted(cause.traits):
            lines.append(asp.fact("cause_allows", cause_id, trait))
    for supply_id, supply in SUPPLIES.items():
        lines.append(asp.fact("supply", supply_id))
        for fix in sorted(supply.fixes):
            lines.append(asp.fact("fixes", supply_id, fix))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def smoke_generate() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story was empty.")
    if not sample.story_qa or not sample.world_qa or not sample.prompts:
        raise StoryError("Smoke test failed: story generation did not produce QA/prompts.")
    with contextlib.redirect_stdout(io.StringIO()):
        emit(sample, trace=False, qa=False, header="")


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: valid combo gate matches ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
    try:
        smoke_generate()
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    for params in CURATED:
        try:
            sample = generate(params)
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"CURATED GENERATION FAILED for {params}: {err}")
            continue
        if not sample.story.strip():
            rc = 1
            print(f"CURATED STORY EMPTY for {params}")
    if rc == 0:
        print(f"OK: curated stories generated ({len(CURATED)} cases).")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a gentle whodunit at an exhibition, with a misunderstanding and a child who learns to look twice before blaming."
    )
    ap.add_argument("--exhibition", choices=EXHIBITIONS)
    ap.add_argument("--missing", choices=MISSING_THINGS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--supply", choices=SUPPLIES)
    ap.add_argument("--adult", choices=["teacher", "mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.exhibition and args.missing and args.cause:
        ex = EXHIBITIONS[args.exhibition]
        item = MISSING_THINGS[args.missing]
        cause = CAUSES[args.cause]
        if not cause_possible(ex, item, cause):
            raise StoryError(explain_rejection(ex, item, cause))
    if args.missing and args.supply:
        item = MISSING_THINGS[args.missing]
        supply = SUPPLIES[args.supply]
        if not supply_fits(item, supply):
            ex = EXHIBITIONS[args.exhibition] if args.exhibition else next(iter(EXHIBITIONS.values()))
            cause = CAUSES[args.cause] if args.cause else next(iter(CAUSES.values()))
            raise StoryError(explain_rejection(ex, item, cause, supply))

    combos = [
        c for c in valid_combos()
        if (args.exhibition is None or c[0] == args.exhibition)
        and (args.missing is None or c[1] == args.missing)
        and (args.cause is None or c[2] == args.cause)
        and (args.supply is None or c[3] == args.supply)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    exhibition, missing, cause, supply = rng.choice(sorted(combos))
    sleuth_gender = rng.choice(["girl", "boy"])
    suspect_gender = rng.choice(["girl", "boy"])
    sleuth_name = _pick_name(rng, sleuth_gender)
    suspect_name = _pick_name(rng, suspect_gender, avoid=sleuth_name)
    adult = args.adult or "teacher"
    return StoryParams(
        exhibition=exhibition,
        missing=missing,
        cause=cause,
        supply=supply,
        sleuth_name=sleuth_name,
        sleuth_gender=sleuth_gender,
        suspect_name=suspect_name,
        suspect_gender=suspect_gender,
        adult=adult,
    )


def generate(params: StoryParams) -> StorySample:
    if params.exhibition not in EXHIBITIONS:
        raise StoryError(f"(Unknown exhibition: {params.exhibition})")
    if params.missing not in MISSING_THINGS:
        raise StoryError(f"(Unknown missing item: {params.missing})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.supply not in SUPPLIES:
        raise StoryError(f"(Unknown supply: {params.supply})")

    exhibition = EXHIBITIONS[params.exhibition]
    item = MISSING_THINGS[params.missing]
    cause = CAUSES[params.cause]
    supply = SUPPLIES[params.supply]

    if not cause_possible(exhibition, item, cause):
        raise StoryError(explain_rejection(exhibition, item, cause))
    if not supply_fits(item, supply):
        raise StoryError(explain_rejection(exhibition, item, cause, supply))

    world = tell(
        exhibition=exhibition,
        item_cfg=item,
        cause=cause,
        supply=supply,
        sleuth_name=params.sleuth_name,
        sleuth_gender=params.sleuth_gender,
        suspect_name=params.suspect_name,
        suspect_gender=params.suspect_gender,
        adult_type=params.adult,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (exhibition, missing, cause, supply) combos:\n")
        for exhibition, missing, cause, supply in combos:
            print(f"  {exhibition:10} {missing:13} {cause:6} {supply}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.sleuth_name} at {p.exhibition}: {p.missing} / {p.cause} / {p.supply}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
