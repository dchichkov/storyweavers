#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/alpha_sharing_teamwork_whodunit.py
=============================================================

A small story world for a child-friendly whodunit: an "alpha" game piece goes
missing during a classroom project, one child is suspected, and the children
solve the mystery by sharing clues and working together.

The world prefers only reasonable combinations:
- the missing item must be movable in the chosen way,
- the setting must plausibly allow that cause,
- the hiding spot must fit the item and cause,
- the shared tool must actually help reach the hiding spot.

Run it
------
    python storyworlds/worlds/gpt-5.4/alpha_sharing_teamwork_whodunit.py
    python storyworlds/worlds/gpt-5.4/alpha_sharing_teamwork_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/alpha_sharing_teamwork_whodunit.py --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/alpha_sharing_teamwork_whodunit.py --asp
    python storyworlds/worlds/gpt-5.4/alpha_sharing_teamwork_whodunit.py --verify
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher_f"}
        male = {"boy", "father", "man", "teacher_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "teacher_f": "teacher",
            "teacher_m": "teacher",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    project: str
    afford_causes: set[str] = field(default_factory=set)
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
class LostItem:
    id: str
    label: str
    phrase: str
    shape: str
    move_modes: set[str] = field(default_factory=set)
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
class Cause:
    id: str
    label: str
    mode: str
    text: str
    clue: str
    allowed_spots: set[str] = field(default_factory=set)
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
class Spot:
    id: str
    label: str
    the: str
    prep: str
    search_text: str
    found_text: str
    accepts: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class Aid:
    id: str
    label: str
    phrase: str
    action: str
    supports: set[str] = field(default_factory=set)
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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"owner", "sleuth", "suspect"}]

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


def _r_missing_worry(world: World) -> list[str]:
    item = world.get("item")
    room = world.get("room")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["mystery"] += 1
    for child in world.children():
        child.memes["worry"] += 1
    return []


def _r_shared_clues(world: World) -> list[str]:
    room = world.get("room")
    if room.meters["shared_clues"] < THRESHOLD:
        return []
    sig = ("shared_clues",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["cooperation"] += 1
    if room.meters["blame"] >= THRESHOLD:
        room.meters["blame"] = max(0.0, room.meters["blame"] - 1.0)
    for child in world.children():
        child.memes["trust"] += 1
    return []


def _r_found_relief(world: World) -> list[str]:
    item = world.get("item")
    room = world.get("room")
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["missing"] = 0.0
    room.meters["mystery"] = 0.0
    for child in world.children():
        child.memes["relief"] += 1
        child.memes["worry"] = 0.0
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_worry", tag="emotion", apply=_r_missing_worry),
    Rule(name="shared_clues", tag="social", apply=_r_shared_clues),
    Rule(name="found_relief", tag="emotion", apply=_r_found_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def valid_combo(setting: Setting, item: LostItem, cause: Cause, spot: Spot, aid: Aid) -> bool:
    return (
        cause.id in setting.afford_causes
        and cause.mode in item.move_modes
        and spot.id in cause.allowed_spots
        and item.shape in spot.accepts
        and spot.id in aid.supports
    )


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for item_id, item in ITEMS.items():
            for cause_id, cause in CAUSES.items():
                for spot_id, spot in SPOTS.items():
                    for aid_id, aid in AIDS.items():
                        if valid_combo(setting, item, cause, spot, aid):
                            combos.append((setting_id, item_id, cause_id, spot_id, aid_id))
    return combos


def explain_invalid(item: LostItem, cause: Cause, spot: Spot, aid: Aid, setting: Setting) -> str:
    if cause.id not in setting.afford_causes:
        return (
            f"(No story: {setting.place.capitalize()} does not give a good reason for "
            f"{cause.label}. Pick a setting where that accident could really happen.)"
        )
    if cause.mode not in item.move_modes:
        return (
            f"(No story: {item.label} would not {cause.mode} that way, so it would not "
            f"vanish because of {cause.label}.)"
        )
    if spot.id not in cause.allowed_spots:
        return (
            f"(No story: {cause.label} would not send {item.label} to {spot.the}. "
            f"That hiding place does not fit the accident.)"
        )
    if item.shape not in spot.accepts:
        return (
            f"(No story: {item.label} would not fit in {spot.the}, so the mystery "
            f"would feel fake.)"
        )
    if spot.id not in aid.supports:
        return (
            f"(No story: {aid.label} would not help reach {spot.the}. The shared tool "
            f"must actually help solve the mystery.)"
        )
    return "(No story: this combination is unreasonable.)"


def predict_solution(item: LostItem, cause: Cause, spot: Spot, aid: Aid, setting: Setting) -> dict:
    if not valid_combo(setting, item, cause, spot, aid):
        return {"solved": False, "verdict": "invalid"}
    return {"solved": True, "verdict": "accident"}


def introduce(world: World, owner: Entity, sleuth: Entity, suspect: Entity,
              teacher: Entity, item: LostItem) -> None:
    world.say(
        f"In {world.setting.place}, {owner.id}, {sleuth.id}, and {suspect.id} were making "
        f"{world.setting.project}. On the middle table sat {item.phrase}, the piece they "
        f"needed first."
    )
    world.say(
        f'"That one goes at the front," {teacher.label_word} said. "The alpha piece helps '
        f'everyone know where to begin."'
    )


def bustle(world: World, owner: Entity, sleuth: Entity, suspect: Entity, setting: Setting) -> None:
    for child in (owner, sleuth, suspect):
        child.memes["joy"] += 1
    world.say(setting.scene)
    world.say(
        f"{owner.id} sorted papers, {suspect.id} carried glue sticks, and {sleuth.id} kept "
        f"the markers in a neat row."
    )


def vanish(world: World, owner: Entity, item: LostItem) -> None:
    thing = world.get("item")
    thing.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"A little later, {owner.id} reached for {item.label} and stopped. "
        f'"Oh no," {owner.pronoun()} whispered. "{item.label.capitalize()} is gone."'
    )


def accuse(world: World, owner: Entity, suspect: Entity, item: LostItem) -> None:
    room = world.get("room")
    room.meters["blame"] += 1
    owner.memes["suspicion"] += 1
    suspect.memes["hurt"] += 1
    world.say(
        f"{owner.id} looked at {suspect.id}. "
        f'"You were standing closest to {item.label}," {owner.pronoun()} said. '
        f'"Did you take it?"'
    )
    world.say(
        f'{suspect.id} blinked hard. "No," {suspect.pronoun()} said. '
        f'"I was only carrying the glue."'
    )


def propose_teamwork(world: World, sleuth: Entity) -> None:
    world.say(
        f'{sleuth.id} put both hands on the table. "This is a mystery," '
        f'{sleuth.pronoun()} said, "but we do not have to guess. Let\'s share what '
        f'each of us saw and solve it together."'
    )


def share_clues(world: World, owner: Entity, sleuth: Entity, suspect: Entity,
                cause: Cause, spot: Spot) -> None:
    room = world.get("room")
    room.meters["shared_clues"] += 1
    world.facts["shared_clue_text"] = cause.clue
    world.facts["owner_clue"] = f"{owner.id} remembered setting the piece near the edge of the table."
    world.facts["suspect_clue"] = f"{suspect.id} remembered holding glue sticks with both hands, not the missing piece."
    world.facts["sleuth_clue"] = cause.clue
    propagate(world, narrate=False)
    world.say(
        f"{owner.id} thought for a moment. "
        f'"I set it down by the edge while I fixed the tape," {owner.pronoun()} said.'
    )
    world.say(
        f'{suspect.id} opened both palms. "My hands were full of glue sticks the whole time," '
        f'{suspect.pronoun()} said.'
    )
    world.say(
        f'{sleuth.id} pointed toward {spot.prep}. "{cause.clue}"'
    )


def deduce(world: World, sleuth: Entity, cause: Cause, spot: Spot, item: LostItem) -> None:
    world.say(
        f"{sleuth.id}'s eyes grew bright. "
        f'"Then nobody stole {item.label}," {sleuth.pronoun()} said. '
        f'"{cause.text}, and it must have slipped to {spot.the}."'
    )


def retrieve(world: World, owner: Entity, sleuth: Entity, suspect: Entity,
             aid: Aid, spot: Spot, item: LostItem) -> None:
    room = world.get("room")
    thing = world.get("item")
    room.meters["teamwork"] += 1
    world.say(
        f"{suspect.id} hurried to get {aid.phrase} and shared it at once. "
        f"{owner.id} used it while {sleuth.id} knelt beside {owner.pronoun('object')} to help look."
    )
    world.say(
        f"They searched {spot.search_text}, and together they {aid.action}."
    )
    thing.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{spot.found_text} There was {item.label}, waiting quietly all along."
    )


def resolve(world: World, owner: Entity, sleuth: Entity, suspect: Entity, teacher: Entity,
            item: LostItem) -> None:
    owner.memes["apology"] += 1
    owner.memes["kindness"] += 1
    suspect.memes["forgiven"] += 1
    world.say(
        f'{owner.id} turned pink. "I am sorry I blamed you," {owner.pronoun()} told {suspect.id}. '
        f'"You helped us find it."'
    )
    world.say(
        f'{suspect.id} smiled a little. "It is okay," {suspect.pronoun()} said. '
        f'"We solved it together."'
    )
    world.say(
        f'{teacher.label_word.capitalize()} nodded. "That was real detective work," '
        f'{teacher.pronoun()} said. "Good detectives share clues, and good teams share tools."'
    )
    world.say(
        f"Soon the children set {item.label} at the front of the project, and the whole line "
        f"looked ready at last."
    )


def ending_image(world: World, owner: Entity, sleuth: Entity, suspect: Entity, item: LostItem) -> None:
    for child in (owner, sleuth, suspect):
        child.memes["joy"] += 1
    world.say(
        f"When they stepped back, {owner.id}, {sleuth.id}, and {suspect.id} all touched "
        f"{item.label} for one tiny second before letting go. Then they laughed and finished "
        f"the work shoulder to shoulder."
    )


def tell(setting: Setting, item_cfg: LostItem, cause: Cause, spot: Spot, aid: Aid,
         owner_name: str = "Lily", owner_gender: str = "girl",
         sleuth_name: str = "Ben", sleuth_gender: str = "boy",
         suspect_name: str = "Mia", suspect_gender: str = "girl",
         teacher_type: str = "teacher_f") -> World:
    world = World(setting)
    owner = world.add(Entity(
        id=owner_name,
        kind="character",
        type=owner_gender,
        role="owner",
        traits=["careful"],
    ))
    sleuth = world.add(Entity(
        id=sleuth_name,
        kind="character",
        type=sleuth_gender,
        role="sleuth",
        traits=["thoughtful"],
    ))
    suspect = world.add(Entity(
        id=suspect_name,
        kind="character",
        type=suspect_gender,
        role="suspect",
        traits=["helpful"],
    ))
    teacher = world.add(Entity(
        id="Teacher",
        kind="character",
        type=teacher_type,
        role="teacher",
        label="the teacher",
    ))
    room = world.add(Entity(id="room", type="room", label=setting.place))
    thing = world.add(Entity(
        id="item",
        type="item",
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        attrs={"shape": item_cfg.shape},
    ))

    room.meters["mystery"] = 0.0
    room.meters["blame"] = 0.0
    room.meters["cooperation"] = 0.0
    room.meters["teamwork"] = 0.0
    room.meters["shared_clues"] = 0.0
    thing.meters["missing"] = 0.0
    thing.meters["found"] = 0.0

    introduce(world, owner, sleuth, suspect, teacher, item_cfg)
    bustle(world, owner, sleuth, suspect, setting)

    world.para()
    vanish(world, owner, item_cfg)
    accuse(world, owner, suspect, item_cfg)
    propose_teamwork(world, sleuth)

    world.para()
    share_clues(world, owner, sleuth, suspect, cause, spot)
    deduce(world, sleuth, cause, spot, item_cfg)
    retrieve(world, owner, sleuth, suspect, aid, spot, item_cfg)

    world.para()
    resolve(world, owner, sleuth, suspect, teacher, item_cfg)
    ending_image(world, owner, sleuth, suspect, item_cfg)

    world.facts.update(
        owner=owner,
        sleuth=sleuth,
        suspect=suspect,
        teacher=teacher,
        setting=setting,
        item_cfg=item_cfg,
        cause=cause,
        spot=spot,
        aid=aid,
        found=thing.meters["found"] >= THRESHOLD,
        teamwork=room.meters["teamwork"] >= THRESHOLD,
        sharing=room.meters["shared_clues"] >= THRESHOLD,
        verdict="accident",
        apology=owner.memes["apology"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "classroom": Setting(
        id="classroom",
        place="the classroom",
        scene="Sunlight lay across the rug, and the little fan by the window hummed softly.",
        project="a giant alphabet train for the wall",
        afford_causes={"breeze", "slide"},
        tags={"classroom", "breeze"},
    ),
    "library": Setting(
        id="library",
        place="the library corner",
        scene="The book cart squeaked nearby, and a low shelf made a shadowy strip along the floor.",
        project="an alphabet story board beside the reading pillows",
        afford_causes={"slide", "roll"},
        tags={"library", "shelf"},
    ),
    "art_room": Setting(
        id="art_room",
        place="the art room",
        scene="Paint cups glimmered on the sink, and drying papers fluttered whenever someone passed.",
        project="an alphabet parade for the hallway",
        afford_causes={"breeze", "roll"},
        tags={"art", "breeze"},
    ),
}

ITEMS = {
    "alpha_card": LostItem(
        id="alpha_card",
        label="the alpha card",
        phrase="a shiny alpha card with a silver star in the corner",
        shape="flat",
        move_modes={"breeze", "slide"},
        tags={"alpha", "clues"},
    ),
    "alpha_button": LostItem(
        id="alpha_button",
        label="the alpha button",
        phrase="a round alpha button painted bright blue",
        shape="round",
        move_modes={"roll"},
        tags={"alpha", "roll"},
    ),
    "alpha_ribbon": LostItem(
        id="alpha_ribbon",
        label="the alpha ribbon",
        phrase="a light alpha ribbon with a paper letter tied at the end",
        shape="soft",
        move_modes={"breeze", "slide"},
        tags={"alpha", "sharing"},
    ),
}

CAUSES = {
    "breeze": Cause(
        id="breeze",
        label="a little breeze",
        mode="breeze",
        text="a little breeze from the moving air lifted it",
        clue="Look at that fluttering paper and the way the corner is still trembling.",
        allowed_spots={"behind_cubby", "under_shelf"},
        tags={"breeze", "clues"},
    ),
    "slide": Cause(
        id="slide",
        label="a slippery slide",
        mode="slide",
        text="it must have slid when the stack of paper was bumped",
        clue="See that thin scrape line on the table edge and down toward the floor?",
        allowed_spots={"under_shelf", "behind_cubby"},
        tags={"clues"},
    ),
    "roll": Cause(
        id="roll",
        label="a quiet roll",
        mode="roll",
        text="it rolled away the moment the table gave a tiny wobble",
        clue="Round things do not stay still, and there is a little wobble mark near the leg.",
        allowed_spots={"under_shelf", "behind_bin"},
        tags={"roll", "clues"},
    ),
}

SPOTS = {
    "under_shelf": Spot(
        id="under_shelf",
        label="under the shelf",
        the="the shelf",
        prep="the shelf",
        search_text="under the shelf where the shadows were thick",
        found_text="At the very back, something gave a bright little gleam.",
        accepts={"flat", "round", "soft"},
        tags={"shelf"},
    ),
    "behind_cubby": Spot(
        id="behind_cubby",
        label="behind the cubby",
        the="the cubby",
        prep="the cubby",
        search_text="behind the cubby where paper scraps liked to hide",
        found_text="Something peeked out from the narrow gap.",
        accepts={"flat", "soft"},
        tags={"cubby"},
    ),
    "behind_bin": Spot(
        id="behind_bin",
        label="behind the paint bin",
        the="the paint bin",
        prep="the paint bin",
        search_text="behind the paint bin by the wall",
        found_text="A small blue edge winked out from the dust-free strip.",
        accepts={"round"},
        tags={"bin"},
    ),
}

AIDS = {
    "flashlight": Aid(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight",
        action="shone the beam into the dark gap while one pair of hands reached carefully in",
        supports={"under_shelf"},
        tags={"flashlight"},
    ),
    "grabber": Aid(
        id="grabber",
        label="grabber",
        phrase="the long classroom grabber",
        action="took turns guiding the long reacher into the narrow space",
        supports={"behind_cubby", "behind_bin"},
        tags={"grabber"},
    ),
    "ruler": Aid(
        id="ruler",
        label="ruler",
        phrase="a long wooden ruler",
        action="slid the ruler in slowly while another friend watched from the side",
        supports={"under_shelf", "behind_cubby"},
        tags={"ruler"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo", "Owen"]


@dataclass
class StoryParams:
    setting: str
    item: str
    cause: str
    spot: str
    aid: str
    owner: str
    owner_gender: str
    sleuth: str
    sleuth_gender: str
    suspect: str
    suspect_gender: str
    teacher: str = "teacher_f"
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


CURATED = [
    StoryParams(
        setting="classroom",
        item="alpha_card",
        cause="breeze",
        spot="under_shelf",
        aid="flashlight",
        owner="Lily",
        owner_gender="girl",
        sleuth="Ben",
        sleuth_gender="boy",
        suspect="Mia",
        suspect_gender="girl",
        teacher="teacher_f",
    ),
    StoryParams(
        setting="library",
        item="alpha_button",
        cause="roll",
        spot="behind_bin",
        aid="grabber",
        owner="Max",
        owner_gender="boy",
        sleuth="Nora",
        sleuth_gender="girl",
        suspect="Leo",
        suspect_gender="boy",
        teacher="teacher_m",
    ),
    StoryParams(
        setting="art_room",
        item="alpha_ribbon",
        cause="breeze",
        spot="behind_cubby",
        aid="grabber",
        owner="Ava",
        owner_gender="girl",
        sleuth="Theo",
        sleuth_gender="boy",
        suspect="Rose",
        suspect_gender="girl",
        teacher="teacher_f",
    ),
    StoryParams(
        setting="classroom",
        item="alpha_card",
        cause="slide",
        spot="behind_cubby",
        aid="ruler",
        owner="Finn",
        owner_gender="boy",
        sleuth="Maya",
        sleuth_gender="girl",
        suspect="Ella",
        suspect_gender="girl",
        teacher="teacher_m",
    ),
    StoryParams(
        setting="library",
        item="alpha_card",
        cause="slide",
        spot="under_shelf",
        aid="ruler",
        owner="Zoe",
        owner_gender="girl",
        sleuth="Owen",
        sleuth_gender="boy",
        suspect="Lucy",
        suspect_gender="girl",
        teacher="teacher_f",
    ),
]

KNOWLEDGE = {
    "sharing": [
        (
            "Why does sharing help in a mystery?",
            "Sharing helps because one person may notice a clue that someone else missed. When children pool what they know, the answer becomes clearer."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help one another on the same job instead of trying to do everything alone. It often makes a hard problem easier and kinder to solve."
        )
    ],
    "clues": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. A good clue points toward what really happened."
        )
    ],
    "breeze": [
        (
            "What can a breeze do to light things?",
            "A breeze can push light things like paper or ribbon so they slide or flutter away. That is why loose things can end up in surprising places."
        )
    ],
    "roll": [
        (
            "Why do round things roll away?",
            "Round things can move when a surface tips or wobbles a little. Because they have no flat side to stop them, they may keep going until something blocks them."
        )
    ],
    "flashlight": [
        (
            "What is a flashlight for?",
            "A flashlight shines a beam into dark places so you can see safely. It helps people search without guessing."
        )
    ],
    "grabber": [
        (
            "What is a grabber tool?",
            "A grabber is a long reaching tool that helps you pick up something from far away or from a narrow gap. It is useful when hands cannot fit."
        )
    ],
    "ruler": [
        (
            "How can a ruler help you reach something?",
            "A long ruler can gently slide or nudge a small thing out from under furniture. It works best when someone else watches carefully and guides you."
        )
    ],
}
KNOWLEDGE_ORDER = ["sharing", "teamwork", "clues", "breeze", "roll", "flashlight", "grabber", "ruler"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    owner, sleuth, suspect = f["owner"], f["sleuth"], f["suspect"]
    item, cause = f["item_cfg"], f["cause"]
    return [
        'Write a short whodunit-style story for a 3-to-5-year-old that includes the word "alpha" and ends with children solving the mystery by sharing and teamwork.',
        f"Tell a gentle classroom mystery where {owner.id} thinks {suspect.id} took {item.label}, but {sleuth.id} asks everyone to share clues first.",
        f"Write a child-friendly detective story where a missing alpha item was really moved by {cause.label}, and the children solve it together."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    owner, sleuth, suspect, teacher = f["owner"], f["sleuth"], f["suspect"], f["teacher"]
    item, cause, spot, aid = f["item_cfg"], f["cause"], f["spot"], f["aid"]
    qa: list[tuple[str, str]] = [
        (
            "What was missing?",
            f"The missing thing was {item.label}. It mattered because the children needed it at the front of their alphabet project."
        ),
        (
            f"Why did {owner.id} first blame {suspect.id}?",
            f"{owner.id} blamed {suspect.id} because {suspect.pronoun()} had been standing closest to the table. At that moment {owner.pronoun()} guessed before checking the clues."
        ),
        (
            f"How did {sleuth.id} help solve the mystery?",
            f"{sleuth.id} told everyone to share what they had seen instead of arguing. That changed the mystery from blaming one friend to looking for the real reason."
        ),
        (
            "What really happened to the alpha piece?",
            f"No one stole it. {cause.text.capitalize()}, and it ended up by {spot.the}."
        ),
        (
            "How did the children find it?",
            f"They used {aid.phrase} together while one child searched and another helped guide the search. Because they shared the tool and worked as a team, they could reach the hiding place safely."
        ),
        (
            f"What changed at the end?",
            f"{owner.id} apologized to {suspect.id}, and the children finished the project together. The ending shows they trusted one another more than they did at the start."
        ),
    ]
    if f.get("apology"):
        qa.append(
            (
                f"What did {teacher.label_word} say the children learned?",
                f"{teacher.label_word.capitalize()} said good detectives share clues and good teams share tools. The mystery was solved kindly because the children did both."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"sharing", "teamwork", "clues"} | set(f["item_cfg"].tags) | set(f["cause"].tags) | set(f["aid"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
movable(I, C) :- item(I), cause(C), item_mode(I, M), cause_mode(C, M).
spot_ok(I, S) :- item(I), spot(S), item_shape(I, Sh), spot_accepts(S, Sh).
cause_to_spot(C, S) :- cause(C), cause_allows(C, S).
tool_ok(A, S) :- aid(A), aid_supports(A, S).

valid(St, I, C, S, A) :-
    setting(St), item(I), cause(C), spot(S), aid(A),
    affords(St, C), movable(I, C), cause_to_spot(C, S),
    spot_ok(I, S), tool_ok(A, S).

verdict(accident) :- chosen_setting(St), chosen_item(I), chosen_cause(C),
                     chosen_spot(S), chosen_aid(A),
                     valid(St, I, C, S, A).

outcome(solved) :- verdict(accident).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for cid in sorted(setting.afford_causes):
            lines.append(asp.fact("affords", sid, cid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_shape", iid, item.shape))
        for mode in sorted(item.move_modes):
            lines.append(asp.fact("item_mode", iid, mode))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("cause_mode", cid, cause.mode))
        for sid in sorted(cause.allowed_spots):
            lines.append(asp.fact("cause_allows", cid, sid))
    for sid, spot in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        for shape in sorted(spot.accepts):
            lines.append(asp.fact("spot_accepts", sid, shape))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        for sid in sorted(aid.supports):
            lines.append(asp.fact("aid_supports", aid_id, sid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> tuple[str, str]:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_setting", params.setting),
        asp.fact("chosen_item", params.item),
        asp.fact("chosen_cause", params.cause),
        asp.fact("chosen_spot", params.spot),
        asp.fact("chosen_aid", params.aid),
    ])
    model = asp.one_model(asp_program(scenario, "#show verdict/1.\n#show outcome/1."))
    verdict_atoms = asp.atoms(model, "verdict")
    outcome_atoms = asp.atoms(model, "outcome")
    verdict = verdict_atoms[0][0] if verdict_atoms else "invalid"
    outcome = outcome_atoms[0][0] if outcome_atoms else "invalid"
    return verdict, outcome


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid combos match ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = 0
    for params in cases:
        py = predict_solution(
            item=ITEMS[params.item],
            cause=CAUSES[params.cause],
            spot=SPOTS[params.spot],
            aid=AIDS[params.aid],
            setting=SETTINGS[params.setting],
        )
        asp_verdict, asp_outcome_name = asp_outcome(params)
        py_verdict = py["verdict"]
        py_outcome = "solved" if py["solved"] else "invalid"
        if (py_verdict, py_outcome) != (asp_verdict, asp_outcome_name):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: ASP verdict/outcome match Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} verdict/outcome cases differ.")

    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Child-friendly whodunit story world: a missing alpha item solved by sharing and teamwork."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--teacher", choices=["teacher_f", "teacher_m"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n not in avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if all(v is not None for v in (args.setting, args.item, args.cause, args.spot, args.aid)):
        setting = SETTINGS[args.setting]
        item = ITEMS[args.item]
        cause = CAUSES[args.cause]
        spot = SPOTS[args.spot]
        aid = AIDS[args.aid]
        if not valid_combo(setting, item, cause, spot, aid):
            raise StoryError(explain_invalid(item, cause, spot, aid, setting))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.cause is None or combo[2] == args.cause)
        and (args.spot is None or combo[3] == args.spot)
        and (args.aid is None or combo[4] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, item_id, cause_id, spot_id, aid_id = rng.choice(sorted(combos))
    owner_gender = rng.choice(["girl", "boy"])
    sleuth_gender = rng.choice(["girl", "boy"])
    suspect_gender = rng.choice(["girl", "boy"])
    used: set[str] = set()
    owner = _pick_name(rng, owner_gender, used)
    used.add(owner)
    sleuth = _pick_name(rng, sleuth_gender, used)
    used.add(sleuth)
    suspect = _pick_name(rng, suspect_gender, used)
    teacher = args.teacher or rng.choice(["teacher_f", "teacher_m"])
    return StoryParams(
        setting=setting_id,
        item=item_id,
        cause=cause_id,
        spot=spot_id,
        aid=aid_id,
        owner=owner,
        owner_gender=owner_gender,
        sleuth=sleuth,
        sleuth_gender=sleuth_gender,
        suspect=suspect,
        suspect_gender=suspect_gender,
        teacher=teacher,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        item = ITEMS[params.item]
        cause = CAUSES[params.cause]
        spot = SPOTS[params.spot]
        aid = AIDS[params.aid]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from None

    if not valid_combo(setting, item, cause, spot, aid):
        raise StoryError(explain_invalid(item, cause, spot, aid, setting))

    world = tell(
        setting=setting,
        item_cfg=item,
        cause=cause,
        spot=spot,
        aid=aid,
        owner_name=params.owner,
        owner_gender=params.owner_gender,
        sleuth_name=params.sleuth,
        sleuth_gender=params.sleuth_gender,
        suspect_name=params.suspect,
        suspect_gender=params.suspect_gender,
        teacher_type=params.teacher,
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
        print(asp_program("", "#show valid/5.\n#show verdict/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, item, cause, spot, aid) combos:\n")
        for setting, item, cause, spot, aid in combos:
            print(f"  {setting:10} {item:12} {cause:7} {spot:13} {aid}")
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
            header = (
                f"### {p.owner}, {p.sleuth}, and {p.suspect}: "
                f"{p.item} in {p.setting} ({p.cause} -> {p.spot}, {p.aid})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
