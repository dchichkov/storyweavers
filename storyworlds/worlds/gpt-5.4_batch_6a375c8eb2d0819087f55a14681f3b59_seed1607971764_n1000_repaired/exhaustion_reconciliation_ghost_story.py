#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/exhaustion_reconciliation_ghost_story.py
===================================================================

A small storyworld about two children in an old house, a quarrel left hanging,
and a ghostly night made worse by exhaustion. The "ghost" is always grounded in
the physical world: a draft, a moving keepsake, and tired minds. The turn is not
a jump scare but reconciliation -- the children face the spooky feeling together,
repair what was left wrong, and make peace with each other before the house feels
quiet again.

Run it
------
    python storyworlds/worlds/gpt-5.4/exhaustion_reconciliation_ghost_story.py
    python storyworlds/worlds/gpt-5.4/exhaustion_reconciliation_ghost_story.py --setting attic --keepsake shell_mobile --action retie_ribbon
    python storyworlds/worlds/gpt-5.4/exhaustion_reconciliation_ghost_story.py --keepsake portrait --action polish_frame
    python storyworlds/worlds/gpt-5.4/exhaustion_reconciliation_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/exhaustion_reconciliation_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/exhaustion_reconciliation_ghost_story.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/exhaustion_reconciliation_ghost_story.py --verify
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
    tags: set[str] = field(default_factory=set)
    movable: bool = False
    hanging: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    atmosphere: str
    bed_line: str
    draft: int
    window_text: str
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
class Keepsake:
    id: str
    label: str
    phrase: str
    problem: str
    min_draft: int
    sign_text: str
    sound_text: str
    resting_place: str
    memory_text: str
    movable: bool = True
    hanging: bool = True
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
class Action:
    id: str
    fixes: set[str]
    text: str
    qa_text: str
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
class Rift:
    id: str
    opening: str
    reminder: str
    fault: str
    apology_watcher: str
    apology_other: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "late_investigation": False,
            "ghost_feeling": False,
            "reconciled": False,
            "fear_spike": False,
            "sign_seen": False,
            "draft_found": False,
            "apology_done": False,
        }

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


def _r_draft_sign(world: World) -> list[str]:
    room = world.get("room")
    keepsake = world.get("keepsake")
    if room.meters["draft"] < THRESHOLD:
        return []
    if keepsake.meters["misplaced"] < THRESHOLD:
        return []
    if keepsake.attrs.get("min_draft", 99) > int(room.meters["draft"]):
        return []
    sig = ("draft_sign",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    keepsake.meters["swaying"] += 1
    if keepsake.attrs.get("sound_text"):
        keepsake.meters["sounding"] += 1
    world.facts["sign_seen"] = True
    return ["__sign__"]


def _r_exhausted_fear(world: World) -> list[str]:
    watcher = world.get("watcher")
    keepsake = world.get("keepsake")
    room = world.get("room")
    if watcher.meters["exhaustion"] < THRESHOLD:
        return []
    if room.meters["dark"] < THRESHOLD:
        return []
    if keepsake.meters["swaying"] < THRESHOLD and keepsake.meters["sounding"] < THRESHOLD:
        return []
    sig = ("exhausted_fear",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    watcher.memes["fear"] += 1
    room.memes["ghost_feeling"] += 1
    world.facts["ghost_feeling"] = True
    world.facts["fear_spike"] = True
    return ["__fear__"]


def _r_reconcile(world: World) -> list[str]:
    watcher = world.get("watcher")
    other = world.get("other")
    keepsake = world.get("keepsake")
    if watcher.memes["apology"] < THRESHOLD and other.memes["apology"] < THRESHOLD:
        return []
    if keepsake.meters["repaired"] < THRESHOLD and keepsake.meters["returned"] < THRESHOLD:
        return []
    sig = ("reconcile",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    watcher.memes["hurt"] = 0.0
    other.memes["hurt"] = 0.0
    watcher.memes["relief"] += 1
    other.memes["relief"] += 1
    watcher.memes["trust"] += 1
    other.memes["trust"] += 1
    room = world.get("room")
    room.memes["ghost_feeling"] = 0.0
    room.memes["peace"] += 1
    world.facts["reconciled"] = True
    world.facts["apology_done"] = True
    return ["__peace__"]


CAUSAL_RULES = [
    Rule(name="draft_sign", tag="physical", apply=_r_draft_sign),
    Rule(name="exhausted_fear", tag="emotional", apply=_r_exhausted_fear),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def spooky_possible(setting: Setting, keepsake: Keepsake) -> bool:
    return keepsake.movable and keepsake.hanging and setting.draft >= keepsake.min_draft


def action_fits(keepsake: Keepsake, action: Action) -> bool:
    return keepsake.problem in action.fixes


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for keepsake_id, keepsake in KEEPSAKES.items():
            if not spooky_possible(setting, keepsake):
                continue
            for action_id, action in ACTIONS.items():
                if action_fits(keepsake, action):
                    combos.append((setting_id, keepsake_id, action_id))
    return combos


def investigation_late(exhaustion: int, courage: int) -> bool:
    return exhaustion > courage + 1


def pair_noun(watcher: Entity, other: Entity, relation: str) -> str:
    if relation == "siblings":
        if watcher.type == "girl" and other.type == "girl":
            return "two sisters"
        if watcher.type == "boy" and other.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two friends"


def explain_invalid_combo(setting: Setting, keepsake: Keepsake, action: Action) -> str:
    if not spooky_possible(setting, keepsake):
        return (
            f"(No story: {keepsake.phrase} would not make a believable ghostly sign in "
            f"{setting.place}. The draft there is too weak for something with that much weight or stiffness.)"
        )
    if not action_fits(keepsake, action):
        return (
            f"(No story: {action.id.replace('_', ' ')} does not actually fix what is wrong with "
            f"{keepsake.phrase}. The reconciliation must include a repair that makes sense.)"
        )
    return "(No story: this combination does not make a reasonable ghostly misunderstanding.)"


def predict_ghost_feeling(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    return {
        "sign_seen": sim.facts["sign_seen"],
        "fear": sim.get("watcher").memes["fear"],
        "ghost_feeling": sim.get("room").memes["ghost_feeling"],
    }


def introduce_house(world: World, watcher: Entity, other: Entity, grandma: Entity, setting: Setting) -> None:
    world.say(
        f"{watcher.id} and {other.id} were staying in {grandma.label_word}'s old house, "
        f"where {setting.atmosphere}"
    )
    world.say(
        f"All day the house had only seemed old and interesting, full of corners where stories might hide."
    )


def start_rift(world: World, watcher: Entity, other: Entity, keepsake: Keepsake, rift: Rift) -> None:
    watcher.memes["hurt"] += 1 if rift.fault in {"other", "both"} else 0
    other.memes["hurt"] += 1 if rift.fault in {"watcher", "both"} else 0
    watcher.memes["trust"] = 2.0
    other.memes["trust"] = 2.0
    keepsake_ent = world.get("keepsake")
    keepsake_ent.meters["misplaced"] += 1
    world.say(
        f"By supper, though, a quarrel had crept between them. {rift.opening}"
    )
    world.say(
        f"The keepsake was left wrong afterward: {keepsake.memory_text.lower()}, and now it was hanging badly near {keepsake.resting_place}."
    )


def bed_down(world: World, watcher: Entity, setting: Setting, exhaustion: int) -> None:
    watcher.meters["exhaustion"] = float(exhaustion)
    world.get("room").meters["dark"] = 1.0
    world.get("room").meters["draft"] = float(world.setting.draft)
    tired = {
        1: "a little tired",
        2: "heavy with exhaustion",
        3: "so tired that even pulling the blanket up felt like work",
    }[exhaustion]
    world.say(
        f"That night, {watcher.id} lay awake in {setting.place}, {tired}. {setting.bed_line}"
    )


def haunting(world: World, watcher: Entity, keepsake: Keepsake, other: Entity) -> None:
    pred = predict_ghost_feeling(world)
    world.facts["predicted_fear"] = pred["fear"]
    world.facts["predicted_ghost_feeling"] = pred["ghost_feeling"]
    propagate(world, narrate=False)
    if world.get("keepsake").meters["sounding"] >= THRESHOLD:
        world.say(
            f"Then {keepsake.phrase} {keepsake.sign_text}, and {keepsake.sound_text}. In the dark, it sounded to {watcher.id} as if somebody lonely were trying to be heard."
        )
    else:
        world.say(
            f"Then {keepsake.phrase} {keepsake.sign_text}. In the dark, and through pure exhaustion, it looked to {watcher.id} like the room itself had begun to stir."
        )
    if world.get("watcher").memes["fear"] >= THRESHOLD:
        world.say(
            f"{watcher.id}'s heart thumped hard. {watcher.pronoun().capitalize()} remembered the afternoon quarrel and suddenly wondered if the house was holding onto it."
        )
    world.say(
        f'"{other.id}?" {watcher.id} whispered into the dark. "I think something is awake."'
    )


def ask_for_help(world: World, watcher: Entity, other: Entity, rift: Rift) -> None:
    other.memes["care"] += 1
    line = (
        f'{other.id} sat up and listened. {rift.reminder} Instead of teasing, {other.pronoun()} slid closer and said, '
        f'"If it is something, we will look together."'
    )
    world.say(line)


def wait_for_morning(world: World, watcher: Entity, other: Entity, grandma: Entity) -> None:
    world.facts["late_investigation"] = True
    watcher.memes["fear"] += 1
    other.memes["care"] += 1
    world.say(
        f"They did not go exploring right then. The shadows felt too deep, and {watcher.id} was too full of exhaustion to trust {watcher.pronoun('possessive')} own eyes."
    )
    world.say(
        f"So the two of them huddled under one blanket until pale morning crept in, and then they went to find {grandma.label_word} and the truth."
    )


def investigate_now(world: World, watcher: Entity, other: Entity, setting: Setting) -> None:
    other.memes["care"] += 1
    other.memes["courage"] += 1
    watcher.memes["courage"] += 1
    world.say(
        f"Together they padded across the floorboards. The hall felt colder near the window, and the moon made a silver strip across {setting.place}."
    )


def discover_draft(world: World, watcher: Entity, other: Entity, keepsake: Keepsake, setting: Setting) -> None:
    world.facts["draft_found"] = True
    world.get("room").meters["dark"] = 0.0
    world.say(
        f"It was not a ghost at all. The latch on the window was loose, so every small breath of night air slipped in, and {keepsake.phrase} {keepsake.sign_text}."
    )
    if keepsake.sound_text:
        world.say(
            f"Once they stood close enough, the sound was only {keepsake.sound_text}, small and ordinary instead of haunted."
        )
    world.say(
        f"Then both children saw the sadder part: the keepsake had been left wrong after their quarrel."
    )


def repair_keepsake(world: World, watcher: Entity, other: Entity, keepsake: Keepsake, action: Action, grandma: Entity) -> None:
    keepsake_ent = world.get("keepsake")
    keepsake_ent.meters["repaired"] += 1
    keepsake_ent.meters["returned"] += 1
    keepsake_ent.meters["misplaced"] = 0.0
    world.say(
        f"By the first good light, they {action.text} and settled it back near {keepsake.resting_place}. {grandma.label_word.capitalize()} had once kept it there because {keepsake.memory_text.lower()}."
    )


def apologize(world: World, watcher: Entity, other: Entity, rift: Rift) -> None:
    if rift.fault == "watcher":
        watcher.memes["apology"] += 1
        world.say(
            f'"I am sorry," {watcher.id} said. "{rift.apology_watcher}"'
        )
        world.say(
            f'{other.id} nodded and answered softly, "{rift.apology_other}"'
        )
    elif rift.fault == "other":
        other.memes["apology"] += 1
        world.say(
            f'"I am sorry," {other.id} said. "{rift.apology_other}"'
        )
        world.say(
            f'{watcher.id} let out a slow breath and answered, "{rift.apology_watcher}"'
        )
    else:
        watcher.memes["apology"] += 1
        other.memes["apology"] += 1
        world.say(
            f'"I was unfair," {watcher.id} admitted. "{rift.apology_watcher}"'
        )
        world.say(
            f'"And I was unfair too," {other.id} said. "{rift.apology_other}"'
        )
    propagate(world, narrate=False)


def peaceful_end(world: World, watcher: Entity, other: Entity, setting: Setting) -> None:
    watcher.memes["fear"] = 0.0
    other.memes["fear"] = 0.0
    room = world.get("room")
    room.meters["draft"] = 0.0
    mood = "morning" if world.facts["late_investigation"] else "night"
    world.say(
        f"After that, {setting.place} no longer felt haunted. In the quiet {mood}, the old house only creaked the way old houses do."
    )
    world.say(
        f"{watcher.id} and {other.id} stood shoulder to shoulder, no longer cross, and the place that had seemed full of ghosts now felt full of peace."
    )


def tell(
    setting: Setting,
    keepsake: Keepsake,
    action: Action,
    rift: Rift,
    watcher_name: str = "Nora",
    watcher_gender: str = "girl",
    other_name: str = "Eli",
    other_gender: str = "boy",
    relation: str = "siblings",
    grandma_type: str = "grandmother",
    courage: int = 1,
    exhaustion: int = 2,
) -> World:
    world = World(setting)
    watcher = world.add(
        Entity(
            id=watcher_name,
            kind="character",
            type=watcher_gender,
            role="watcher",
            traits=["tired"],
            attrs={"relation": relation},
        )
    )
    other = world.add(
        Entity(
            id=other_name,
            kind="character",
            type=other_gender,
            role="other",
            traits=["kind"],
            attrs={"relation": relation},
        )
    )
    grandma = world.add(
        Entity(
            id="Grandma",
            kind="character",
            type=grandma_type,
            role="elder",
            label="the grandmother",
        )
    )
    room = world.add(
        Entity(
            id="room",
            type="room",
            label=setting.place,
            attrs={"draft_level": setting.draft},
            tags=set(setting.tags),
        )
    )
    keepsake_ent = world.add(
        Entity(
            id="keepsake",
            type="keepsake",
            label=keepsake.label,
            movable=keepsake.movable,
            hanging=keepsake.hanging,
            attrs={
                "problem": keepsake.problem,
                "min_draft": keepsake.min_draft,
                "sound_text": keepsake.sound_text,
                "resting_place": keepsake.resting_place,
            },
            tags=set(keepsake.tags),
        )
    )
    watcher.memes["courage"] = float(courage)
    watcher.memes["fear"] = 0.0
    other.memes["courage"] = float(max(courage, 1))
    other.memes["fear"] = 0.0
    other.memes["care"] = 0.0
    room.memes["ghost_feeling"] = 0.0
    room.memes["peace"] = 0.0
    keepsake_ent.meters["misplaced"] = 0.0
    keepsake_ent.meters["swaying"] = 0.0
    keepsake_ent.meters["sounding"] = 0.0
    keepsake_ent.meters["repaired"] = 0.0
    keepsake_ent.meters["returned"] = 0.0

    introduce_house(world, watcher, other, grandma, setting)
    start_rift(world, watcher, other, keepsake, rift)

    world.para()
    bed_down(world, watcher, setting, exhaustion)
    haunting(world, watcher, keepsake, other)
    ask_for_help(world, watcher, other, rift)

    world.para()
    if investigation_late(exhaustion, courage):
        wait_for_morning(world, watcher, other, grandma)
    else:
        investigate_now(world, watcher, other, setting)
    discover_draft(world, watcher, other, keepsake, setting)
    repair_keepsake(world, watcher, other, keepsake, action, grandma)
    apologize(world, watcher, other, rift)

    world.para()
    peaceful_end(world, watcher, other, setting)

    world.facts.update(
        watcher=watcher,
        other=other,
        grandma=grandma,
        setting_cfg=setting,
        keepsake_cfg=keepsake,
        action_cfg=action,
        rift_cfg=rift,
        relation=relation,
        courage=courage,
        exhaustion=exhaustion,
        outcome="dawn" if world.facts["late_investigation"] else "night",
    )
    return world


SETTINGS = {
    "attic": Setting(
        id="attic",
        place="the attic room",
        atmosphere="the rafters whispered above them and moonlight sifted through the slanted ceiling",
        bed_line="Even the old trunks seemed to be listening.",
        draft=3,
        window_text="the small attic window",
        tags={"house", "draft", "attic"},
    ),
    "hallway": Setting(
        id="hallway",
        place="the upstairs hallway",
        atmosphere="the wallpaper held faded flowers and the floorboards answered every step with a sigh",
        bed_line="The shadows stretched between the bedroom doors like long gray ribbons.",
        draft=2,
        window_text="the tall hallway window",
        tags={"house", "draft", "hallway"},
    ),
    "nursery": Setting(
        id="nursery",
        place="the old nursery",
        atmosphere="the rocking chair sat still in the corner and the moon glazed the toy shelf silver",
        bed_line="The room smelled faintly of cedar and old blankets.",
        draft=1,
        window_text="the nursery window",
        tags={"house", "draft", "nursery"},
    ),
}

KEEPSAKES = {
    "paper_stars": Keepsake(
        id="paper_stars",
        label="paper stars",
        phrase="the string of paper stars",
        problem="retie",
        min_draft=1,
        sign_text="fluttered and brushed the wall",
        sound_text="",
        resting_place="the small bed",
        memory_text="it had once glowed over the bed when Grandma sang lullabies there",
        movable=True,
        hanging=True,
        tags={"stars", "ghost", "keepsake"},
    ),
    "shell_mobile": Keepsake(
        id="shell_mobile",
        label="shell mobile",
        phrase="the shell mobile",
        problem="retie",
        min_draft=1,
        sign_text="turned slowly in the air",
        sound_text="a thin clinking of shells touching shells",
        resting_place="the window seat",
        memory_text="Grandma had hung it there after one summer at the sea",
        movable=True,
        hanging=True,
        tags={"shell", "ghost", "keepsake"},
    ),
    "rag_doll": Keepsake(
        id="rag doll",
        label="rag doll",
        phrase="the rag doll on its ribbon loop",
        problem="sew",
        min_draft=2,
        sign_text="rocked against the wall",
        sound_text="",
        resting_place="the cedar chest",
        memory_text="Grandma had mended it for every child who had ever stayed the night",
        movable=True,
        hanging=True,
        tags={"doll", "ghost", "keepsake"},
    ),
    "portrait": Keepsake(
        id="portrait",
        label="portrait",
        phrase="the framed family portrait",
        problem="polish",
        min_draft=5,
        sign_text="barely shifted at all",
        sound_text="",
        resting_place="the stair landing",
        memory_text="it watched over the stairs for many years",
        movable=False,
        hanging=True,
        tags={"portrait", "keepsake"},
    ),
}

ACTIONS = {
    "retie_ribbon": Action(
        id="retie_ribbon",
        fixes={"retie"},
        text="retied the loosened ribbon",
        qa_text="They retied the loosened ribbon and put the keepsake back where it belonged.",
        tags={"repair", "ribbon"},
    ),
    "stitch_seam": Action(
        id="stitch_seam",
        fixes={"sew"},
        text="stitched the loose seam with Grandma's little sewing kit",
        qa_text="They stitched the loose seam and settled the keepsake back in its proper place.",
        tags={"repair", "sew"},
    ),
    "polish_frame": Action(
        id="polish_frame",
        fixes={"polish"},
        text="rubbed the frame with a soft cloth until it shone",
        qa_text="They polished the frame gently and hung it straight again.",
        tags={"repair", "polish"},
    ),
}

RIFTS = {
    "borrowed_without_asking": Rift(
        id="borrowed_without_asking",
        opening="Earlier, one child had borrowed the keepsake for a game without asking, and the other had felt brushed aside.",
        reminder="The argument still hurt, but so did the trembling in the dark.",
        fault="watcher",
        apology_watcher="I should have asked first, and I should not have left it hanging loose.",
        apology_other="Thank you for saying that. I was upset because it mattered to me.",
        tags={"apology", "ownership"},
    ),
    "blamed_each_other": Rift(
        id="blamed_each_other",
        opening="When the keepsake snagged and slipped, each child had blamed the other, and the words between them turned sharp.",
        reminder="The silence after the fight had been almost as spooky as the room.",
        fault="both",
        apology_watcher="I blamed you too fast.",
        apology_other="And I blamed you too fast. We should have fixed it together right away.",
        tags={"apology", "blame"},
    ),
    "forgot_to_put_back": Rift(
        id="forgot_to_put_back",
        opening="They had promised to put the keepsake back after looking at it, but only one remembered, and the forgotten promise stung.",
        reminder="The dark made the unfinished promise feel even heavier.",
        fault="other",
        apology_watcher="I was scared, but I still wanted to make it right with you.",
        apology_other="I should have put it back when I said I would, and I am sorry I left you to worry.",
        tags={"apology", "promise"},
    ),
}

GIRL_NAMES = ["Nora", "Lila", "Mia", "Ivy", "Tessa", "Wren", "Ella", "Sophie"]
BOY_NAMES = ["Eli", "Owen", "Sam", "Noah", "Finn", "Theo", "Jude", "Ben"]
TRAITS = ["tired", "gentle", "watchful", "careful"]


@dataclass
class StoryParams:
    setting: str
    keepsake: str
    action: str
    rift: str
    watcher: str
    watcher_gender: str
    other: str
    other_gender: str
    relation: str
    grandma_type: str
    courage: int = 1
    exhaustion: int = 2
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
    "ghost": [
        (
            "Why can a tired person think something ordinary is a ghost?",
            "When you are very tired, your brain can rush to the scariest guess before you look closely. Shadows, drafts, and little sounds can seem much bigger than they really are."
        )
    ],
    "draft": [
        (
            "What is a draft in a house?",
            "A draft is moving air that slips in through a gap or loose window. It can make curtains, paper, or hanging things move."
        )
    ],
    "repair": [
        (
            "Why does fixing something together help after a quarrel?",
            "Fixing something together gives both people one gentle job to share. It can turn hurt feelings into helpful actions and make it easier to apologize."
        )
    ],
    "apology": [
        (
            "What makes a good apology?",
            "A good apology says what was wrong and shows that you want to make it right. It helps the other person feel seen and cared for."
        )
    ],
    "sew": [
        (
            "What does sewing do?",
            "Sewing joins cloth together with thread. It can close a tear or mend a loose seam so something can be used again."
        )
    ],
    "ribbon": [
        (
            "What does a ribbon do for a hanging decoration?",
            "A ribbon can hold a light decoration in place. If the ribbon comes loose, the decoration can droop or swing the wrong way."
        )
    ],
    "polish": [
        (
            "What does polishing mean?",
            "Polishing means rubbing something gently to clean it and make it shine. It helps some objects look cared for again."
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "draft", "repair", "apology", "sew", "ribbon", "polish"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    watcher = f["watcher"]
    other = f["other"]
    keepsake = f["keepsake_cfg"]
    setting = f["setting_cfg"]
    outcome = "morning" if f["late_investigation"] else "night"
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the word "exhaustion" and ends in reconciliation.',
        f"Tell a ghost-story-like tale where {watcher.id} mistakes a moving keepsake in {setting.place} for something haunted, but {other.id} helps uncover the real cause.",
        f"Write a child-facing story set in an old house where fear grows out of tiredness, a family keepsake, and a quarrel, and the children make peace by {ACTIONS[f['action_cfg'].id].text if False else 'repairing what they left wrong'} by {outcome}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    watcher = f["watcher"]
    other = f["other"]
    grandma = f["grandma"]
    keepsake = f["keepsake_cfg"]
    action = f["action_cfg"]
    setting = f["setting_cfg"]
    rift = f["rift_cfg"]
    relation = f["relation"]
    pair = pair_noun(watcher, other, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {watcher.id} and {other.id}, staying in {grandma.label_word}'s old house. The ghostly feeling starts around a family keepsake and an unfinished quarrel."
        ),
        (
            f"Why did {watcher.id} think something spooky was happening?",
            f"{watcher.id} was worn down by exhaustion, lying in the dark after the argument, when {keepsake.phrase} moved. Because the room was dark and the quarrel was still on {watcher.pronoun('possessive')} mind, the ordinary movement felt haunted."
        ),
        (
            "What was really causing the ghostly sign?",
            f"A loose window let in a draft, and the draft made {keepsake.phrase} move. Once the children came close and looked carefully, the strange sign became something small and explainable."
        ),
        (
            "How did the children solve the problem?",
            f"{action.qa_text} Then they apologized for the quarrel and made the room feel peaceful again."
        ),
    ]
    if f["late_investigation"]:
        qa.append(
            (
                "Did they investigate right away?",
                f"No. {watcher.id} was too full of exhaustion and fear to trust the dark, so the children waited for morning. That pause helped them face the problem more calmly."
            )
        )
    else:
        qa.append(
            (
                "Did they face the spooky feeling together that night?",
                f"Yes. They walked together through {setting.place} and checked the moving keepsake instead of letting fear grow larger. Working side by side helped the reconciliation begin before the apology was even spoken."
            )
        )
    if rift.fault == "watcher":
        qa.append(
            (
                f"Who needed to apologize most, and why?",
                f"{watcher.id} did, because {watcher.pronoun()} had caused the quarrel by handling the keepsake carelessly. The apology mattered because the repair alone could not mend hurt feelings."
            )
        )
    elif rift.fault == "other":
        qa.append(
            (
                f"Who needed to apologize most, and why?",
                f"{other.id} did, because {other.pronoun()} had left a promise unfinished. Saying sorry mattered because the fear in the night was tangled up with that broken promise."
            )
        )
    else:
        qa.append(
            (
                "Why did both children apologize?",
                f"They had both made the quarrel worse by blaming each other. Repairing the keepsake gave them a quiet moment to admit that and choose reconciliation."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"ghost", "draft", "repair", "apology"}
    tags |= set(f["action_cfg"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v not in ("", 0, 0.0, None, False)}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="attic",
        keepsake="shell_mobile",
        action="retie_ribbon",
        rift="blamed_each_other",
        watcher="Nora",
        watcher_gender="girl",
        other="Eli",
        other_gender="boy",
        relation="siblings",
        grandma_type="grandmother",
        courage=2,
        exhaustion=2,
    ),
    StoryParams(
        setting="nursery",
        keepsake="paper_stars",
        action="retie_ribbon",
        rift="borrowed_without_asking",
        watcher="Ivy",
        watcher_gender="girl",
        other="Sam",
        other_gender="boy",
        relation="friends",
        grandma_type="grandmother",
        courage=1,
        exhaustion=3,
    ),
    StoryParams(
        setting="hallway",
        keepsake="rag_doll",
        action="stitch_seam",
        rift="forgot_to_put_back",
        watcher="Finn",
        watcher_gender="boy",
        other="Lila",
        other_gender="girl",
        relation="siblings",
        grandma_type="grandmother",
        courage=1,
        exhaustion=2,
    ),
    StoryParams(
        setting="attic",
        keepsake="rag_doll",
        action="stitch_seam",
        rift="blamed_each_other",
        watcher="Mia",
        watcher_gender="girl",
        other="Theo",
        other_gender="boy",
        relation="friends",
        grandma_type="grandmother",
        courage=0,
        exhaustion=3,
    ),
]


ASP_RULES = r"""
spooky_possible(S, K) :- setting(S), keepsake(K),
                         draft(S, D), min_draft(K, M), D >= M,
                         movable(K), hanging(K).

fits(A, K) :- action(A), keepsake(K), problem(K, P), fixes(A, P).

valid(S, K, A) :- spooky_possible(S, K), fits(A, K).

late :- exhaustion(E), courage(C), E > C + 1.
outcome(dawn) :- late.
outcome(night) :- not late.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("draft", sid, setting.draft))
    for kid, keepsake in KEEPSAKES.items():
        lines.append(asp.fact("keepsake", kid))
        lines.append(asp.fact("problem", kid, keepsake.problem))
        lines.append(asp.fact("min_draft", kid, keepsake.min_draft))
        if keepsake.movable:
            lines.append(asp.fact("movable", kid))
        if keepsake.hanging:
            lines.append(asp.fact("hanging", kid))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for fix in sorted(action.fixes):
            lines.append(asp.fact("fixes", aid, fix))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("exhaustion", params.exhaustion),
            asp.fact("courage", params.courage),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def explain_gender(prize: str, gender: str) -> str:
    return f"(No story: {prize} was requested with unsupported gender value {gender}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A ghost-story-flavored world about exhaustion, a mistaken haunting, and reconciliation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--rift", choices=RIFTS)
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("--grandma-type", choices=["grandmother", "grandfather"], dest="grandma_type")
    ap.add_argument("--courage", type=int, choices=[0, 1, 2])
    ap.add_argument("--exhaustion", type=int, choices=[1, 2, 3])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP model and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.keepsake and args.action:
        setting = SETTINGS[args.setting]
        keepsake = KEEPSAKES[args.keepsake]
        action = ACTIONS[args.action]
        if not (spooky_possible(setting, keepsake) and action_fits(keepsake, action)):
            raise StoryError(explain_invalid_combo(setting, keepsake, action))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.keepsake is None or combo[1] == args.keepsake)
        and (args.action is None or combo[2] == args.action)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, keepsake_id, action_id = rng.choice(sorted(combos))
    rift = args.rift or rng.choice(sorted(RIFTS))
    watcher, watcher_gender = _pick_child(rng)
    other, other_gender = _pick_child(rng, avoid=watcher)
    relation = args.relation or rng.choice(["siblings", "friends"])
    grandma_type = args.grandma_type or rng.choice(["grandmother", "grandfather"])
    courage = args.courage if args.courage is not None else rng.choice([0, 1, 2])
    exhaustion = args.exhaustion if args.exhaustion is not None else rng.choice([1, 2, 3])

    return StoryParams(
        setting=setting_id,
        keepsake=keepsake_id,
        action=action_id,
        rift=rift,
        watcher=watcher,
        watcher_gender=watcher_gender,
        other=other,
        other_gender=other_gender,
        relation=relation,
        grandma_type=grandma_type,
        courage=courage,
        exhaustion=exhaustion,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        keepsake = KEEPSAKES[params.keepsake]
        action = ACTIONS[params.action]
        rift = RIFTS[params.rift]
    except KeyError as err:
        raise StoryError(f"(Invalid option: {err.args[0]})") from None

    if not spooky_possible(setting, keepsake) or not action_fits(keepsake, action):
        raise StoryError(explain_invalid_combo(setting, keepsake, action))
    if params.courage not in {0, 1, 2}:
        raise StoryError("(Courage must be 0, 1, or 2.)")
    if params.exhaustion not in {1, 2, 3}:
        raise StoryError("(Exhaustion must be 1, 2, or 3.)")
    if params.relation not in {"siblings", "friends"}:
        raise StoryError("(Relation must be siblings or friends.)")

    world = tell(
        setting=setting,
        keepsake=keepsake,
        action=action,
        rift=rift,
        watcher_name=params.watcher,
        watcher_gender=params.watcher_gender,
        other_name=params.other,
        other_gender=params.other_gender,
        relation=params.relation,
        grandma_type=params.grandma_type,
        courage=params.courage,
        exhaustion=params.exhaustion,
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


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    rng = random.Random(123)
    parser = build_parser()
    empty_args = parser.parse_args([])
    for i in range(30):
        p = resolve_params(empty_args, random.Random(i))
        p.seed = i
        cases.append(p)
    mismatches = [p for p in cases if asp_outcome(p) != ("dawn" if investigation_late(p.exhaustion, p.courage) else "night")]
    if not mismatches:
        print(f"OK: ASP outcome matches Python outcome on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH in outcomes on {len(mismatches)} scenarios.")

    try:
        sample = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover - explicit verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, keepsake, action) combos:\n")
        for setting, keepsake, action in combos:
            print(f"  {setting:8} {keepsake:13} {action}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
                f"### {p.watcher} & {p.other}: {p.keepsake} in {p.setting} "
                f"({p.action}, {'dawn' if investigation_late(p.exhaustion, p.courage) else 'night'})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
