#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/kazoo_doohicky_precision_flashback_lesson_learned_mystery.py
========================================================================================

A standalone story world for a child-friendly whodunit: a tiny doohicky goes
missing from a kazoo-powered showpiece, the children notice concrete clues, a
flashback reveals what really happened, and a careful repair with precision
solves the mystery and teaches a lesson.

Run it
------
    python storyworlds/worlds/gpt-5.4/kazoo_doohicky_precision_flashback_lesson_learned_mystery.py
    python storyworlds/worlds/gpt-5.4/kazoo_doohicky_precision_flashback_lesson_learned_mystery.py --showpiece dragon --clue glitter
    python storyworlds/worlds/gpt-5.4/kazoo_doohicky_precision_flashback_lesson_learned_mystery.py --tool hex_key
    python storyworlds/worlds/gpt-5.4/kazoo_doohicky_precision_flashback_lesson_learned_mystery.py --all --qa
    python storyworlds/worlds/gpt-5.4/kazoo_doohicky_precision_flashback_lesson_learned_mystery.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "teacher", "woman"}
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
class Showpiece:
    id: str
    label: str
    phrase: str
    opening: str
    motion: str
    fail_line: str
    finish_line: str
    required_tool: str
    precision_need: int
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
class Tool:
    id: str
    label: str
    phrase: str
    precise_for: set[str] = field(default_factory=set)
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
class Suspect:
    id: str
    name: str
    type: str
    role: str
    clue: str
    accesses: set[str] = field(default_factory=set)
    mishaps: set[str] = field(default_factory=set)
    traits: list[str] = field(default_factory=list)
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
class Clue:
    id: str
    text: str
    question: str
    inference: str
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
class HidingPlace:
    id: str
    label: str
    phrase: str
    found_line: str
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
class Mishap:
    id: str
    name: str
    setup: str
    flashback: str
    apology: str
    lesson: str
    allowed_hidings: set[str] = field(default_factory=set)
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


def _r_missing_part(world: World) -> list[str]:
    machine = world.get("machine")
    if machine.meters["missing_part"] < THRESHOLD:
        return []
    sig = ("missing_part",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    machine.meters["stuck"] += 1
    world.get("builder").memes["worry"] += 1
    world.get("detective").memes["curiosity"] += 1
    return []


def _r_clue_points(world: World) -> list[str]:
    clue_id = world.facts.get("clue_id", "")
    suspect_id = world.facts.get("culprit_id", "")
    if not clue_id or not suspect_id:
        return []
    detective = world.get("detective")
    if detective.meters["clue_seen"] < THRESHOLD:
        return []
    sig = ("clue_points", clue_id, suspect_id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["certainty"] += 1
    world.get(suspect_id).memes["pressure"] += 1
    return []


def _r_found_part(world: World) -> list[str]:
    machine = world.get("machine")
    if world.facts.get("part_found", False) is not True:
        return []
    sig = ("found_part",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    machine.meters["missing_part"] = 0.0
    world.get("builder").memes["hope"] += 1
    return []


def _r_precise_repair(world: World) -> list[str]:
    machine = world.get("machine")
    if world.facts.get("tool_fit", False) is not True:
        return []
    if world.facts.get("part_found", False) is not True:
        return []
    if world.facts.get("repair_attempted", False) is not True:
        return []
    sig = ("precise_repair",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    machine.meters["aligned"] += 1
    machine.meters["stuck"] = 0.0
    world.get("builder").memes["relief"] += 1
    world.get("detective").memes["pride"] += 1
    world.get(world.facts["culprit_id"]).memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_part", tag="physical", apply=_r_missing_part),
    Rule(name="clue_points", tag="social", apply=_r_clue_points),
    Rule(name="found_part", tag="physical", apply=_r_found_part),
    Rule(name="precise_repair", tag="physical", apply=_r_precise_repair),
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
        for line in produced:
            world.say(line)
    return produced


def tool_fits(showpiece: Showpiece, tool: Tool) -> bool:
    return tool.id == showpiece.required_tool and showpiece.id in tool.precise_for


def culprit_for_clue(clue_id: str) -> Optional[Suspect]:
    for suspect in SUSPECTS.values():
        if suspect.clue == clue_id:
            return suspect
    return None


def combo_valid(showpiece_id: str, tool_id: str, clue_id: str, hiding_id: str, mishap_id: str) -> bool:
    if showpiece_id not in SHOWPIECES or tool_id not in TOOLS or clue_id not in CLUES:
        return False
    if hiding_id not in HIDING_PLACES or mishap_id not in MISHAPS:
        return False
    suspect = culprit_for_clue(clue_id)
    if suspect is None:
        return False
    if hiding_id not in suspect.accesses:
        return False
    if mishap_id not in suspect.mishaps:
        return False
    if hiding_id not in MISHAPS[mishap_id].allowed_hidings:
        return False
    return tool_fits(SHOWPIECES[showpiece_id], TOOLS[tool_id])


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for showpiece_id in SHOWPIECES:
        for tool_id in TOOLS:
            for clue_id in CLUES:
                for hiding_id in HIDING_PLACES:
                    for mishap_id in MISHAPS:
                        if combo_valid(showpiece_id, tool_id, clue_id, hiding_id, mishap_id):
                            combos.append((showpiece_id, tool_id, clue_id, hiding_id, mishap_id))
    return combos


def lesson_for_mishap(mishap_id: str) -> str:
    if mishap_id not in MISHAPS:
        raise StoryError(f"(Unknown mishap: {mishap_id})")
    return MISHAPS[mishap_id].lesson


def predict_repair(world: World, tool_id: str) -> dict:
    sim = world.copy()
    sim.facts["part_found"] = True
    sim.facts["repair_attempted"] = True
    sim.facts["tool_fit"] = tool_fits(sim.facts["showpiece_cfg"], TOOLS[tool_id])
    propagate(sim, narrate=False)
    machine = sim.get("machine")
    return {
        "fixed": machine.meters["aligned"] >= THRESHOLD and machine.meters["stuck"] < THRESHOLD,
    }


def introduce(world: World, detective: Entity, builder: Entity, teacher: Entity, showpiece: Showpiece) -> None:
    world.say(
        f"On the morning of the school fair, {builder.id} set {showpiece.phrase} on the long craft table. "
        f"{showpiece.opening}"
    )
    world.say(
        f"{detective.id}, who loved small mysteries, stood beside {builder.id} while {teacher.label_word} "
        f"checked the room list and smiled."
    )


def demonstration(world: World, builder: Entity, showpiece: Showpiece) -> None:
    builder.memes["pride"] += 1
    world.say(
        f'"Listen to this," {builder.id} said, giving the little kazoo inside the machine a careful puff. '
        f"{showpiece.motion}"
    )


def failure(world: World, builder: Entity, detective: Entity, showpiece: Showpiece) -> None:
    machine = world.get("machine")
    machine.meters["missing_part"] += 1
    world.facts["part_found"] = False
    world.facts["repair_attempted"] = False
    world.facts["tool_fit"] = False
    propagate(world, narrate=False)
    world.say(showpiece.fail_line)
    world.say(
        f"{builder.id} blinked. The tiny brass doohicky that held the moving part in place was gone."
    )
    world.say(
        f'"That doohicky needs precision," {builder.id} whispered. "{showpiece.label} cannot perform without it."'
    )
    detective.memes["focus"] += 1


def inspect_clue(world: World, detective: Entity, clue: Clue, suspect: Suspect) -> None:
    detective.meters["clue_seen"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{detective.id} bent close to the table and found {clue.text}. "
        f'"{clue.question}" {detective.pronoun()} murmured.'
    )
    world.say(
        f"That clue made {detective.pronoun('object')} think of {suspect.name}, because {clue.inference}"
    )


def ask_questions(world: World, detective: Entity, suspect_ent: Entity, suspect: Suspect) -> None:
    world.say(
        f'Soon {detective.id} walked over to {suspect.name}. "{suspect.name}," {detective.pronoun()} asked, '
        f'"were you near the craft table before the bell?"'
    )
    world.say(
        f"{suspect.name} looked at the floor, then at the machine, and {suspect_ent.pronoun()} remembered."
    )


def flashback(world: World, suspect_ent: Entity, suspect: Suspect, hiding: HidingPlace, mishap: Mishap) -> None:
    suspect_ent.memes["honesty"] += 1
    world.say(
        f"Then the memory came back like a flashback in a detective book: {mishap.flashback} "
        f"In the hurry, the little doohicky ended up in {hiding.phrase}."
    )


def retrieval(world: World, suspect_ent: Entity, hiding: HidingPlace, mishap: Mishap) -> None:
    world.facts["part_found"] = True
    propagate(world, narrate=False)
    world.say(
        f'"Oh!" {suspect_ent.id} said. "{mishap.apology}"'
    )
    world.say(
        f"{suspect_ent.pronoun().capitalize()} hurried to look, and {hiding.found_line}"
    )


def repair(world: World, detective: Entity, builder: Entity, showpiece: Showpiece, tool: Tool) -> None:
    world.facts["repair_attempted"] = True
    world.facts["tool_fit"] = tool_fits(showpiece, tool)
    pred = predict_repair(world, tool.id)
    propagate(world, narrate=False)
    world.say(
        f"{builder.id} held the tiny piece steady while {detective.id} used {tool.phrase} with great precision."
    )
    if pred["fixed"]:
        world.say(
            f"The doohicky clicked back where it belonged, snug and true."
        )
        world.say(showpiece.finish_line)
    else:
        raise StoryError("(Repair prediction failed: an invalid tool was chosen.)")


def lesson_scene(world: World, teacher: Entity, builder: Entity, detective: Entity, suspect_ent: Entity,
                 mishap: Mishap) -> None:
    for ent in (builder, detective, suspect_ent):
        ent.memes["relief"] += 1
        ent.memes["lesson"] += 1
    world.say(
        f"{teacher.label_word.capitalize()} knelt beside the table. "
        f'"Mysteries feel smaller when everyone tells the truth," {teacher.pronoun()} said.'
    )
    world.say(
        f'"And tiny parts need slow hands and labels," {teacher.pronoun()} added. "{mishap.lesson}"'
    )


def ending(world: World, builder: Entity, detective: Entity, showpiece: Showpiece) -> None:
    builder.memes["joy"] += 1
    detective.memes["joy"] += 1
    world.say(
        f"When the fair began, {showpiece.label} moved just as {builder.id} had hoped, and the kazoo note made the whole table grin."
    )
    world.say(
        f"{detective.id} did not get a gold badge or a trumpet fanfare, but {detective.pronoun()} did get the best ending for a whodunit: "
        f"the mystery was solved, a friend was forgiven, and everyone had learned to be careful with little things."
    )


def tell(showpiece: Showpiece, tool: Tool, clue: Clue, hiding: HidingPlace, mishap: Mishap,
         detective_name: str = "Mina", detective_type: str = "girl",
         builder_name: str = "Theo", builder_type: str = "boy",
         teacher_type: str = "teacher") -> World:
    suspect_cfg = culprit_for_clue(clue.id)
    if suspect_cfg is None:
        raise StoryError("(No suspect matches that clue.)")
    if not combo_valid(showpiece.id, tool.id, clue.id, hiding.id, mishap.id):
        raise StoryError(explain_rejection(showpiece, tool, clue, hiding, mishap))

    world = World()
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_type,
        label=detective_name,
        role="detective",
        traits=["observant", "patient"],
    ))
    builder = world.add(Entity(
        id=builder_name,
        kind="character",
        type=builder_type,
        label=builder_name,
        role="builder",
        traits=["inventive", "careful"],
    ))
    suspect_ent = world.add(Entity(
        id=suspect_cfg.name,
        kind="character",
        type=suspect_cfg.type,
        label=suspect_cfg.name,
        role=suspect_cfg.role,
        traits=list(suspect_cfg.traits),
    ))
    teacher = world.add(Entity(
        id="Teacher",
        kind="character",
        type=teacher_type,
        label="the teacher",
        role="teacher",
        traits=["calm"],
    ))
    machine = world.add(Entity(
        id="machine",
        kind="thing",
        type="machine",
        label=showpiece.label,
        attrs={"requires_tool": showpiece.required_tool, "precision_need": showpiece.precision_need},
    ))
    part = world.add(Entity(
        id="doohicky",
        kind="thing",
        type="part",
        label="doohicky",
    ))

    world.facts.update(
        showpiece_cfg=showpiece,
        tool_cfg=tool,
        clue_cfg=clue,
        hiding_cfg=hiding,
        mishap_cfg=mishap,
        culprit_cfg=suspect_cfg,
        clue_id=clue.id,
        culprit_id=suspect_cfg.name,
        part_found=False,
        repair_attempted=False,
        tool_fit=False,
    )

    introduce(world, detective, builder, teacher, showpiece)
    demonstration(world, builder, showpiece)

    world.para()
    failure(world, builder, detective, showpiece)
    inspect_clue(world, detective, clue, suspect_cfg)
    ask_questions(world, detective, suspect_ent, suspect_cfg)

    world.para()
    flashback(world, suspect_ent, suspect_cfg, hiding, mishap)
    retrieval(world, suspect_ent, hiding, mishap)
    repair(world, detective, builder, showpiece, tool)

    world.para()
    lesson_scene(world, teacher, builder, detective, suspect_ent, mishap)
    ending(world, builder, detective, showpiece)

    world.facts.update(
        detective=detective,
        builder=builder,
        suspect=suspect_ent,
        teacher=teacher,
        machine=machine,
        part=part,
        solved=machine.meters["aligned"] >= THRESHOLD,
        lesson=lesson_for_mishap(mishap.id),
    )
    return world


SHOWPIECES = {
    "dragon": Showpiece(
        id="dragon",
        label="the kazoo dragon",
        phrase="a bright paper dragon with a kazoo in its chest",
        opening="Its foil scales winked in the light, and its neck was built to sway when the hidden wheel turned.",
        motion="The dragon gave a proud buzz and bobbed its head over the paint jars.",
        fail_line="But when the next test began, the head only sagged and gave a sad little burr.",
        finish_line="At once the dragon lifted its head and sang one brave kazoo note while its paper wings trembled.",
        required_tool="mini_screwdriver",
        precision_need=2,
        tags={"kazoo", "machine", "precision"},
    ),
    "submarine": Showpiece(
        id="submarine",
        label="the kazoo submarine",
        phrase="a shoebox submarine with a yellow kazoo periscope",
        opening="Silver circles for windows ran down its side, and the tiny periscope was meant to pop up in time with the music.",
        motion="The periscope bounced up and down and tooted like a tiny harbor horn.",
        fail_line="But at the next test, the periscope drooped sideways and the sound came out in a weak wobble.",
        finish_line="The periscope sprang tall again, and the kazoo toot sounded clear enough for the back row to hear.",
        required_tool="tweezers",
        precision_need=3,
        tags={"kazoo", "machine", "precision"},
    ),
    "clockbird": Showpiece(
        id="clockbird",
        label="the kazoo clock-bird",
        phrase="a cardboard clock-bird with a kazoo beak",
        opening="Its paper tail was covered with painted numbers, and the beak was supposed to open each time the little gear rolled forward.",
        motion="The bird dipped its head and gave a brisk kazoo chirp.",
        fail_line="But on the next try, the beak stuck shut and only a fuzzy hum slipped out.",
        finish_line="The beak clicked open and closed in neat time, singing a bright kazoo chirp to the whole room.",
        required_tool="hex_key",
        precision_need=4,
        tags={"kazoo", "machine", "precision"},
    ),
}

TOOLS = {
    "mini_screwdriver": Tool(
        id="mini_screwdriver",
        label="mini screwdriver",
        phrase="the mini screwdriver",
        precise_for={"dragon"},
        tags={"tool", "precision"},
    ),
    "tweezers": Tool(
        id="tweezers",
        label="tweezers",
        phrase="the tiny tweezers",
        precise_for={"submarine"},
        tags={"tool", "precision"},
    ),
    "hex_key": Tool(
        id="hex_key",
        label="hex key",
        phrase="the little hex key",
        precise_for={"clockbird"},
        tags={"tool", "precision"},
    ),
}

SUSPECTS = {
    "pippa": Suspect(
        id="pippa",
        name="Pippa",
        type="girl",
        role="stage helper",
        clue="glitter",
        accesses={"toolbox", "apron_pocket", "parts_tray"},
        mishaps={"borrowed", "tidied"},
        traits=["busy", "kind"],
        tags={"helper"},
    ),
    "omar": Suspect(
        id="omar",
        name="Omar",
        type="boy",
        role="costume helper",
        clue="blue_thread",
        accesses={"costume_box", "under_stage"},
        mishaps={"borrowed", "knocked"},
        traits=["hurrying", "friendly"],
        tags={"costume"},
    ),
    "june": Suspect(
        id="june",
        name="June",
        type="girl",
        role="music helper",
        clue="kazoo_hum",
        accesses={"music_bin", "toolbox", "parts_tray"},
        mishaps={"borrowed", "tidied"},
        traits=["musical", "gentle"],
        tags={"music"},
    ),
}

CLUES = {
    "glitter": Clue(
        id="glitter",
        text="a pinch of gold glitter caught beside the empty screw hole",
        question="Who had been sprinkling stars near the machine?",
        inference="Pippa had been decorating stage signs with glitter just minutes before",
        tags={"clue", "glitter"},
    ),
    "blue_thread": Clue(
        id="blue_thread",
        text="a short blue thread snagged under the wheel arm",
        question="Whose costume thread had brushed this close?",
        inference="Omar had been carrying the blue sailor capes from the costume rack",
        tags={"clue", "thread"},
    ),
    "kazoo_hum": Clue(
        id="kazoo_hum",
        text="a soft kazoo hum still hanging near the music shelf",
        question="Who had been testing sounds when nobody else was listening?",
        inference="June always checked the music shelf and hummed along with every instrument",
        tags={"clue", "kazoo"},
    ),
}

HIDING_PLACES = {
    "toolbox": HidingPlace(
        id="toolbox",
        label="toolbox",
        phrase="the red toolbox",
        found_line="inside the red toolbox, under a strip of felt, lay the missing doohicky.",
        tags={"toolbox"},
    ),
    "apron_pocket": HidingPlace(
        id="apron_pocket",
        label="apron pocket",
        phrase="the side pocket of a paint-splashed apron",
        found_line="from the side pocket of the apron, the little doohicky rolled into a waiting palm.",
        tags={"pocket"},
    ),
    "parts_tray": HidingPlace(
        id="parts_tray",
        label="parts tray",
        phrase="the labeled parts tray by the window",
        found_line="there in the labeled parts tray was the doohicky, small as a bean and easy to miss.",
        tags={"tray"},
    ),
    "costume_box": HidingPlace(
        id="costume_box",
        label="costume box",
        phrase="the striped costume box",
        found_line="inside the striped costume box, between two capes, glinted the missing doohicky.",
        tags={"costume"},
    ),
    "music_bin": HidingPlace(
        id="music_bin",
        label="music bin",
        phrase="the blue music bin",
        found_line="in the blue music bin, beside spare rhythm sticks, sat the little doohicky.",
        tags={"music"},
    ),
    "under_stage": HidingPlace(
        id="under_stage",
        label="under the stage",
        phrase="the shadow under the low stage riser",
        found_line="under the low stage riser, shining in the dust, was the missing doohicky.",
        tags={"floor"},
    ),
}

MISHAPS = {
    "borrowed": Mishap(
        id="borrowed",
        name="borrowed",
        setup="borrowed the tiny part for just one moment",
        flashback="earlier, the helper had seen the doohicky and thought it might match another wobbly prop, so the helper borrowed it for a quick comparison.",
        apology="I only meant to borrow it and bring it right back.",
        lesson="Ask before you borrow a part, especially when it is tiny.",
        allowed_hidings={"toolbox", "costume_box", "music_bin"},
        tags={"borrowing", "lesson"},
    ),
    "tidied": Mishap(
        id="tidied",
        name="tidied",
        setup="tidied too fast",
        flashback="earlier, the helper had swept the table in a hurry, trying to be useful, and tucked the tiny part away without checking what it belonged to.",
        apology="I was trying to tidy up, but I moved it too fast.",
        lesson="When parts are tiny, label them and put them back with care.",
        allowed_hidings={"parts_tray", "toolbox", "apron_pocket"},
        tags={"tidy", "lesson"},
    ),
    "knocked": Mishap(
        id="knocked",
        name="knocked",
        setup="bumped the table in a rush",
        flashback="earlier, the helper had hurried past with full arms, bumped the table, and never noticed the tiny part skitter away.",
        apology="I rushed by and must have knocked it loose.",
        lesson="Slow feet and careful eyes save a lot of trouble.",
        allowed_hidings={"under_stage", "costume_box"},
        tags={"rush", "lesson"},
    ),
}

GIRL_NAMES = ["Mina", "Nora", "Lila", "Tess", "Ruby", "Ava", "Maya", "Zoe"]
BOY_NAMES = ["Theo", "Ben", "Max", "Eli", "Noah", "Sam", "Finn", "Leo"]


@dataclass
class StoryParams:
    showpiece: str
    tool: str
    clue: str
    hiding: str
    mishap: str
    detective_name: str
    detective_type: str
    builder_name: str
    builder_type: str
    teacher_type: str
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
    "kazoo": [
        (
            "What is a kazoo?",
            "A kazoo is a small musical instrument that buzzes when you hum into it. It makes a funny, wiggly sound instead of a clear whistle."
        )
    ],
    "precision": [
        (
            "What does precision mean?",
            "Precision means doing something very carefully and exactly. You use precision when a tiny part has to go in just the right place."
        )
    ],
    "tool": [
        (
            "Why do small repairs need the right tool?",
            "Small parts are easier to fix with the right tool because the tool can hold or turn them safely. The wrong tool can slip and make the problem worse."
        )
    ],
    "clue": [
        (
            "What is a clue in a mystery?",
            "A clue is a small sign that helps you figure out what happened. Good detectives notice clues and think carefully before they guess."
        )
    ],
    "borrowing": [
        (
            "Why should you ask before borrowing something?",
            "You should ask first because the other person may need it, and tiny things are easy to lose. Asking helps people trust each other."
        )
    ],
    "tidy": [
        (
            "Why can tidying too fast cause problems?",
            "When you tidy too fast, you can move important things without noticing where they belong. Careful tidying keeps little parts from getting lost."
        )
    ],
    "rush": [
        (
            "Why is rushing risky around tiny parts?",
            "Rushing makes it easier to bump things and miss what fell. Slow, careful hands and feet help you notice small changes."
        )
    ],
}


def pair_phrase(det: Entity, build: Entity) -> str:
    return f"{det.id} and {build.id}"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    showpiece = f["showpiece_cfg"]
    mishap = f["mishap_cfg"]
    detective = f["detective"]
    builder = f["builder"]
    suspect = f["suspect"]
    return [
        f'Write a short whodunit for a 3-to-5-year-old that includes the words "kazoo", "doohicky", and "precision".',
        f"Tell a gentle mystery where {detective.id} notices a clue, solves why {showpiece.label} stopped working, and a flashback shows what {suspect.id} really did.",
        f'Write a story with a missing tiny part, a school-fair mystery to solve, and a lesson learned about being careful: "{mishap.lesson}"',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    builder = f["builder"]
    suspect = f["suspect"]
    teacher = f["teacher"]
    showpiece = f["showpiece_cfg"]
    clue = f["clue_cfg"]
    hiding = f["hiding_cfg"]
    mishap = f["mishap_cfg"]
    tool = f["tool_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_phrase(detective, builder)}, who were trying to get {showpiece.label} ready for the fair, and {suspect.id}, who unknowingly caused the trouble."
        ),
        (
            f"What was the mystery to solve?",
            f"The mystery was why {showpiece.label} suddenly stopped working. The tiny doohicky that held the moving part in place was missing, so the machine could not move the right way."
        ),
        (
            f"How did {detective.id} know whom to question?",
            f"{detective.id} found {clue.text}. That clue pointed toward {suspect.id} because {clue.inference}"
        ),
        (
            f"What happened in the flashback?",
            f"In the flashback, {suspect.id} remembered that {mishap.flashback} That is how the doohicky ended up in {hiding.phrase}."
        ),
        (
            f"How did they fix {showpiece.label}?",
            f"{builder.id} held the tiny part steady while {detective.id} used {tool.phrase} with precision. Because it was the right tool for that machine, the doohicky clicked back into place and the showpiece worked again."
        ),
        (
            "What lesson did everyone learn?",
            f"{teacher.label_word.capitalize()} said that mysteries feel smaller when people tell the truth. The bigger lesson was: {mishap.lesson}"
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"kazoo", "precision", "tool", "clue"} | set(world.facts["mishap_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in ["kazoo", "precision", "tool", "clue", "borrowing", "tidy", "rush"]:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: part_found={world.facts.get('part_found')} tool_fit={world.facts.get('tool_fit')} lesson={world.facts.get('lesson')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        showpiece="dragon",
        tool="mini_screwdriver",
        clue="glitter",
        hiding="parts_tray",
        mishap="tidied",
        detective_name="Mina",
        detective_type="girl",
        builder_name="Theo",
        builder_type="boy",
        teacher_type="teacher",
    ),
    StoryParams(
        showpiece="submarine",
        tool="tweezers",
        clue="blue_thread",
        hiding="under_stage",
        mishap="knocked",
        detective_name="Nora",
        detective_type="girl",
        builder_name="Max",
        builder_type="boy",
        teacher_type="teacher",
    ),
    StoryParams(
        showpiece="clockbird",
        tool="hex_key",
        clue="kazoo_hum",
        hiding="music_bin",
        mishap="borrowed",
        detective_name="Ben",
        detective_type="boy",
        builder_name="Lila",
        builder_type="girl",
        teacher_type="teacher",
    ),
]


def explain_rejection(showpiece: Showpiece, tool: Tool, clue: Clue, hiding: HidingPlace, mishap: Mishap) -> str:
    suspect = culprit_for_clue(clue.id)
    if suspect is None:
        return "(No story: that clue does not belong to any suspect in this mystery.)"
    if not tool_fits(showpiece, tool):
        return (
            f"(No story: {tool.label} is not the precise tool for {showpiece.label}. "
            f"This world only tells repairs that can honestly work.)"
        )
    if hiding.id not in suspect.accesses:
        return (
            f"(No story: {suspect.name} would not naturally leave the doohicky in {hiding.label}. "
            f"Pick a hiding place the clue-owner could really reach.)"
        )
    if mishap.id not in suspect.mishaps:
        return (
            f"(No story: {suspect.name} is not a good fit for the mishap '{mishap.name}'. "
            f"Pick a mishap that matches that helper's role and habits.)"
        )
    if hiding.id not in mishap.allowed_hidings:
        return (
            f"(No story: the mishap '{mishap.name}' does not plausibly lead to {hiding.label}. "
            f"Choose a hiding place that follows from what happened.)"
        )
    return "(No story: this combination is not a reasonable whodunit.)"


ASP_RULES = r"""
valid(Sh,T,C,H,M) :- showpiece(Sh), tool(T), clue(C), hiding(H), mishap(M),
                     clue_of(S,C), can_hide(S,H), does_mishap(S,M),
                     hiding_fits(M,H), tool_for(Sh,T).

lesson(ask_first)   :- chosen_mishap(borrowed).
lesson(label_parts) :- chosen_mishap(tidied).
lesson(slow_down)   :- chosen_mishap(knocked).

#show valid/5.
#show lesson/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for showpiece_id, showpiece in SHOWPIECES.items():
        lines.append(asp.fact("showpiece", showpiece_id))
        lines.append(asp.fact("tool_for", showpiece_id, showpiece.required_tool))
    for tool_id in TOOLS:
        lines.append(asp.fact("tool", tool_id))
    for suspect_id, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", suspect_id))
        lines.append(asp.fact("clue_of", suspect_id, suspect.clue))
        for hiding in sorted(suspect.accesses):
            lines.append(asp.fact("can_hide", suspect_id, hiding))
        for mishap in sorted(suspect.mishaps):
            lines.append(asp.fact("does_mishap", suspect_id, mishap))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for hiding_id in HIDING_PLACES:
        lines.append(asp.fact("hiding", hiding_id))
    for mishap_id, mishap in MISHAPS.items():
        lines.append(asp.fact("mishap", mishap_id))
        for hiding in sorted(mishap.allowed_hidings):
            lines.append(asp.fact("hiding_fits", mishap_id, hiding))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_lesson(mishap_id: str) -> str:
    import asp
    model = asp.one_model(asp_program(asp.fact("chosen_mishap", mishap_id)))
    atoms = asp.atoms(model, "lesson")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    lesson_map = {"borrowed": "ask_first", "tidied": "label_parts", "knocked": "slow_down"}
    for mishap_id, expected in lesson_map.items():
        got = asp_lesson(mishap_id)
        if got != expected:
            rc = 1
            print(f"MISMATCH in lesson for {mishap_id}: asp={got} python={expected}")
    if rc == 0:
        print("OK: ASP lesson mapping matches Python.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or sample.world is None:
            raise StoryError("(Smoke test failed: empty story sample.)")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Child-friendly whodunit: a missing doohicky, a kazoo machine, a flashback, and a careful repair."
    )
    ap.add_argument("--showpiece", choices=SHOWPIECES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--hiding", choices=HIDING_PLACES)
    ap.add_argument("--mishap", choices=MISHAPS)
    ap.add_argument("--detective-name")
    ap.add_argument("--builder-name")
    ap.add_argument("--detective-type", choices=["girl", "boy"])
    ap.add_argument("--builder-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.showpiece and args.tool:
        showpiece = SHOWPIECES[args.showpiece]
        tool = TOOLS[args.tool]
        if not tool_fits(showpiece, tool):
            raise StoryError(
                f"(No story: {tool.label} does not fit {showpiece.label}. Pick {SHOWPIECES[args.showpiece].required_tool} instead.)"
            )

    combos = [
        combo for combo in valid_combos()
        if (args.showpiece is None or combo[0] == args.showpiece)
        and (args.tool is None or combo[1] == args.tool)
        and (args.clue is None or combo[2] == args.clue)
        and (args.hiding is None or combo[3] == args.hiding)
        and (args.mishap is None or combo[4] == args.mishap)
    ]
    if not combos:
        if all(x is not None for x in (args.showpiece, args.tool, args.clue, args.hiding, args.mishap)):
            raise StoryError(
                explain_rejection(
                    SHOWPIECES[args.showpiece],
                    TOOLS[args.tool],
                    CLUES[args.clue],
                    HIDING_PLACES[args.hiding],
                    MISHAPS[args.mishap],
                )
            )
        raise StoryError("(No valid combination matches the given options.)")

    showpiece_id, tool_id, clue_id, hiding_id, mishap_id = rng.choice(sorted(combos))
    detective_type = args.detective_type or rng.choice(["girl", "boy"])
    builder_type = args.builder_type or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or _pick_name(rng, detective_type)
    builder_name = args.builder_name or _pick_name(rng, builder_type, avoid=detective_name)
    return StoryParams(
        showpiece=showpiece_id,
        tool=tool_id,
        clue=clue_id,
        hiding=hiding_id,
        mishap=mishap_id,
        detective_name=detective_name,
        detective_type=detective_type,
        builder_name=builder_name,
        builder_type=builder_type,
        teacher_type="teacher",
    )


def generate(params: StoryParams) -> StorySample:
    if not combo_valid(params.showpiece, params.tool, params.clue, params.hiding, params.mishap):
        raise StoryError(
            explain_rejection(
                SHOWPIECES.get(params.showpiece, SHOWPIECES["dragon"]),
                TOOLS.get(params.tool, TOOLS["mini_screwdriver"]),
                CLUES.get(params.clue, CLUES["glitter"]),
                HIDING_PLACES.get(params.hiding, HIDING_PLACES["toolbox"]),
                MISHAPS.get(params.mishap, MISHAPS["borrowed"]),
            )
        )
    try:
        showpiece = SHOWPIECES[params.showpiece]
        tool = TOOLS[params.tool]
        clue = CLUES[params.clue]
        hiding = HIDING_PLACES[params.hiding]
        mishap = MISHAPS[params.mishap]
    except KeyError as err:
        raise StoryError(f"(Unknown parameter value: {err})") from err

    world = tell(
        showpiece=showpiece,
        tool=tool,
        clue=clue,
        hiding=hiding,
        mishap=mishap,
        detective_name=params.detective_name,
        detective_type=params.detective_type,
        builder_name=params.builder_name,
        builder_type=params.builder_type,
        teacher_type=params.teacher_type,
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
        print(f"{len(combos)} compatible (showpiece, tool, clue, hiding, mishap) combos:\n")
        for showpiece_id, tool_id, clue_id, hiding_id, mishap_id in combos:
            suspect = culprit_for_clue(clue_id)
            who = suspect.name if suspect else "?"
            print(f"  {showpiece_id:10} {tool_id:17} {clue_id:11} {hiding_id:12} {mishap_id:8} [{who}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.showpiece} / {p.clue} / {p.mishap}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
