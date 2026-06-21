#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/candid_student_repetition_reconciliation_kindness_space_adventure.py
================================================================================================

A standalone storyworld about two students on a tiny classroom space adventure.

The seed asked for:
- the words "candid" and "student"
- the features Repetition, Reconciliation, and Kindness
- a Space Adventure style

This world models a child-sized, concrete domain: two students build a mission
project for a pretend launch. One student speaks too candidly after a small
accident ruins part of the project. The hurt can be healed only if the same
student becomes kind in action as well as words: apologising, helping with the
right repair, and repeating a gentle promise that proves the friendship changed.

The reasonableness gate is simple and strict:
- a damage type must actually threaten the chosen project material
- the chosen repair method must be suitable for that kind of damage
- low-sense repair methods are known but refused

The ASP twin mirrors both the compatibility gate and the outcome model
(unrepaired | repaired | reconciled).

Run it
------
python storyworlds/worlds/gpt-5.4/candid_student_repetition_reconciliation_kindness_space_adventure.py
python storyworlds/worlds/gpt-5.4/candid_student_repetition_reconciliation_kindness_space_adventure.py --asp
python storyworlds/worlds/gpt-5.4/candid_student_repetition_reconciliation_kindness_space_adventure.py --verify
python storyworlds/worlds/gpt-5.4/candid_student_repetition_reconciliation_kindness_space_adventure.py -n 5 --seed 7 --qa
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    material: str = ""
    damage_kind: str = ""
    repairable_by: set[str] = field(default_factory=set)
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
        return {"teacher": "teacher", "mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Mission:
    id: str
    scene: str
    opening: str
    goal: str
    launch_place: str
    ending_image: str
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
class Project:
    id: str
    label: str
    phrase: str
    material: str
    detail: str
    launch_use: str
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
class Accident:
    id: str
    label: str
    verb: str
    result: str
    damage: str
    cause_text: str
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
class RepairMethod:
    id: str
    label: str
    sense: int
    fixes: set[str]
    action_text: str
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


def _r_hurt(world: World) -> list[str]:
    out: list[str] = []
    speaker = world.get("speaker")
    partner = world.get("partner")
    project = world.get("project")
    if project.meters["damaged"] >= THRESHOLD and speaker.memes["blunt"] >= THRESHOLD:
        sig = ("hurt", partner.id)
        if sig not in world.fired:
            world.fired.add(sig)
            partner.memes["hurt"] += 1
            partner.memes["confidence"] -= 1
            out.append("__hurt__")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    speaker = world.get("speaker")
    partner = world.get("partner")
    project = world.get("project")
    method = world.get("method")
    if speaker.memes["helping"] >= THRESHOLD and speaker.memes["apology"] >= THRESHOLD:
        if project.damage_kind and method.label and project.damage_kind in method.repairable_by:
            sig = ("repair", project.id)
            if sig not in world.fired:
                world.fired.add(sig)
                project.meters["damaged"] = 0.0
                project.meters["ready"] += 1
                partner.memes["hope"] += 1
                speaker.memes["care"] += 1
                out.append("__repair__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    speaker = world.get("speaker")
    partner = world.get("partner")
    project = world.get("project")
    if project.meters["ready"] >= THRESHOLD and speaker.memes["kind_phrase_count"] >= 2:
        sig = ("reconcile", partner.id)
        if sig not in world.fired:
            world.fired.add(sig)
            partner.memes["hurt"] = 0.0
            partner.memes["trust"] += 1
            speaker.memes["relief"] += 1
            partner.memes["relief"] += 1
            out.append("__reconcile__")
    return out


CAUSAL_RULES = [
    Rule(name="hurt", tag="social", apply=_r_hurt),
    Rule(name="repair", tag="physical", apply=_r_repair),
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


MISSIONS = {
    "moon_garden": Mission(
        id="moon_garden",
        scene="the classroom looked like a silver moon base",
        opening="foil stars hung above the tables, and a cardboard airlock stood by the reading rug",
        goal="carry a moon flower safely to the crater greenhouse",
        launch_place="the painted crater ramp",
        ending_image="their little ship glided over the paper moon, and the two students smiled at each other again",
        tags={"space", "moon"},
    ),
    "comet_mail": Mission(
        id="comet_mail",
        scene="the classroom felt like a bright mail station in the stars",
        opening="tiny parcel boxes were stacked like cargo, and a blue tunnel became a comet gate",
        goal="deliver a message pod through the comet gate",
        launch_place="the glowing tape runway",
        ending_image="their message pod slid through the comet gate, and the whole launch felt warm again",
        tags={"space", "comet"},
    ),
    "ring_rescue": Mission(
        id="ring_rescue",
        scene="the classroom turned into a rescue deck beside a ringed planet",
        opening="paper planets swung from string, and the chairs made a brave little command ship",
        goal="guide a rescue craft between the shining rings",
        launch_place="the launch mat by the window",
        ending_image="their rescue craft skimmed past the rings, and both students laughed in the soft classroom light",
        tags={"space", "planet"},
    ),
}

PROJECTS = {
    "rocket": Project(
        id="rocket",
        label="rocket",
        phrase="a paper rocket with a blue window",
        material="paper",
        detail="The nose had one bright blue window and three careful fins.",
        launch_use="to fly their mission ship",
        tags={"rocket", "paper"},
    ),
    "star_map": Project(
        id="star_map",
        label="star map",
        phrase="a foil star map with dotted paths",
        material="foil",
        detail="Silver paths curved between sticker stars like roads in the sky.",
        launch_use="to guide their mission route",
        tags={"map", "foil"},
    ),
    "moon_model": Project(
        id="moon_model",
        label="moon model",
        phrase="a clay moon with tiny craters",
        material="clay",
        detail="Little thumbprint craters circled the top like sleepy ponds.",
        launch_use="to show where the mission would land",
        tags={"moon", "clay"},
    ),
}

ACCIDENTS = {
    "juice_spill": Accident(
        id="juice_spill",
        label="juice spill",
        verb="bumped the cup with an elbow",
        result="orange juice splashed across the table",
        damage="wet",
        cause_text="A wobble of the elbow sent the cup tipping over.",
        tags={"spill", "wet"},
    ),
    "boot_bump": Accident(
        id="boot_bump",
        label="boot bump",
        verb="backed into the table in clumsy pretend moon boots",
        result="the project bent out of shape",
        damage="bent",
        cause_text="The pretend moon boots were wide, and one careful step went wrong.",
        tags={"bump", "bent"},
    ),
    "marker_smudge": Accident(
        id="marker_smudge",
        label="marker smudge",
        verb="dragged a sleeve through the fresh lines",
        result="dark marker streaks blurred the careful parts",
        damage="smudged",
        cause_text="The lines were still fresh when the sleeve brushed past them.",
        tags={"smudge", "marker"},
    ),
}

REPAIRS = {
    "dry_patch": RepairMethod(
        id="dry_patch",
        label="dry patch",
        sense=3,
        fixes={"wet"},
        action_text="dabbed up the spill, dried the soggy spot, and patched the weak part with a fresh piece",
        qa_text="dried the wet part and patched it with a fresh piece",
        tags={"repair", "paper"},
    ),
    "smooth_tape": RepairMethod(
        id="smooth_tape",
        label="smooth and tape",
        sense=3,
        fixes={"bent"},
        action_text="smoothed the bent part flat and held it steady with shiny tape",
        qa_text="smoothed the bent part and fixed it with shiny tape",
        tags={"repair", "foil", "tape"},
    ),
    "wipe_redraw": RepairMethod(
        id="wipe_redraw",
        label="wipe and redraw",
        sense=3,
        fixes={"smudged"},
        action_text="carefully wiped the blur away and redrew the lost lines together",
        qa_text="wiped the smudge away and redrew the lost lines together",
        tags={"repair", "marker"},
    ),
    "blow_on_it": RepairMethod(
        id="blow_on_it",
        label="blow on it",
        sense=1,
        fixes=set(),
        action_text="blew on the mess and hoped it would somehow fix itself",
        qa_text="only blew on it and hoped",
        tags={"weak_fix"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Zoe", "Ava", "Iris"]
BOY_NAMES = ["Finn", "Leo", "Milo", "Theo", "Eli", "Sam"]
TRAITS = ["patient", "curious", "careful", "thoughtful", "brave", "gentle"]
CANDID_LINES = [
    "That won't fly like that.",
    "That looks all wrong now.",
    "That mission piece is a mess.",
]
KIND_PHRASES = [
    "We can mend it together.",
    "We can mend it together.",
    "Side by side, space friend.",
]


def project_harmed(project: Project, accident: Accident) -> bool:
    if project.material == "paper":
        return accident.damage in {"wet", "smudged"}
    if project.material == "foil":
        return accident.damage in {"bent", "smudged"}
    if project.material == "clay":
        return accident.damage in {"wet", "bent"}
    return False


def repair_fits(accident: Accident, repair: RepairMethod) -> bool:
    return accident.damage in repair.fixes


def sensible_repairs() -> list[RepairMethod]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mission_id in MISSIONS:
        for project_id, project in PROJECTS.items():
            for accident_id, accident in ACCIDENTS.items():
                if project_harmed(project, accident) and any(
                    repair_fits(accident, rep) for rep in sensible_repairs()
                ):
                    combos.append((mission_id, project_id, accident_id))
    return combos


def predict_outcome(world: World, accident_id: str, repair_id: str) -> dict:
    sim = world.copy()
    accident = ACCIDENTS[accident_id]
    repair = REPAIRS[repair_id]
    project = sim.get("project")
    method = sim.get("method")
    project.damage_kind = accident.damage
    project.meters["damaged"] += 1
    sim.get("speaker").memes["blunt"] += 1
    method.repairable_by = set(repair.fixes)
    sim.get("speaker").memes["apology"] += 1
    sim.get("speaker").memes["helping"] += 1
    sim.get("speaker").memes["kind_phrase_count"] += 2
    propagate(sim, narrate=False)
    return {
        "hurt": sim.get("partner").memes["hurt"] >= THRESHOLD,
        "ready": sim.get("project").meters["ready"] >= THRESHOLD,
        "reconciled": sim.get("partner").memes["trust"] >= THRESHOLD,
    }


def introduce(world: World, speaker: Entity, partner: Entity, teacher: Entity, mission: Mission) -> None:
    speaker.memes["excitement"] += 1
    partner.memes["excitement"] += 1
    world.say(
        f"It was launch day in class, and {mission.scene}. {mission.opening}."
    )
    world.say(
        f"{speaker.id} and {partner.id} were each a student in the front row of "
        f"{teacher.id}'s space lesson, and together they had one job: {mission.goal}."
    )


def show_project(world: World, partner: Entity, project: Project) -> None:
    world.say(
        f"{partner.id} set down {project.phrase} on the table. {project.detail} "
        f"They needed it {project.launch_use}."
    )


def accident_happens(world: World, speaker: Entity, partner: Entity, accident: Accident) -> None:
    project = world.get("project")
    project.damage_kind = accident.damage
    project.meters["damaged"] += 1
    partner.memes["alarm"] += 1
    world.say(
        f"Then {speaker.id} {accident.verb}, and {accident.result}. "
        f"{accident.cause_text}"
    )


def candid_blurt(world: World, speaker: Entity, partner: Entity, line: str) -> None:
    speaker.memes["blunt"] += 1
    world.facts["candid_line"] = line
    propagate(world, narrate=False)
    world.say(
        f'{speaker.id} was a candid student, and the first words jumped out too fast. '
        f'"{line}"'
    )
    if partner.memes["hurt"] >= THRESHOLD:
        world.say(
            f"{partner.id}'s face fell. {partner.pronoun().capitalize()} looked at the table "
            f"as if the whole launch had gone dim."
        )


def teacher_pause(world: World, teacher: Entity, speaker: Entity) -> None:
    speaker.memes["reflection"] += 1
    world.say(
        f'{teacher.id} touched the edge of the table and spoke softly. '
        f'"Candid can be honest," {teacher.pronoun()} said, "but honest words should help."'
    )


def apology(world: World, speaker: Entity, partner: Entity) -> None:
    speaker.memes["apology"] += 1
    speaker.memes["care"] += 1
    world.say(
        f'{speaker.id} took a breath. "I am sorry," {speaker.pronoun()} said. '
        f'"I spoke like a bumping meteor. I want to help now."'
    )


def offer_kindness(world: World, speaker: Entity, partner: Entity, phrase: str) -> None:
    speaker.memes["kind_phrase_count"] += 1
    world.say(f'"{phrase}" {speaker.id} said.')


def repair_scene(world: World, speaker: Entity, partner: Entity, repair: RepairMethod) -> None:
    method = world.get("method")
    method.label = repair.label
    method.repairable_by = set(repair.fixes)
    speaker.memes["helping"] += 1
    world.say(
        f"Then {speaker.id} and {partner.id} {repair.action_text}."
    )
    propagate(world, narrate=False)


def launch(world: World, mission: Mission, speaker: Entity, partner: Entity, project: Project) -> None:
    world.say(
        f"When the project was ready again, they carried it to {mission.launch_place} "
        f"and counted together, \"Three, two, one, launch!\""
    )
    world.say(mission.ending_image)


def tell(
    mission: Mission,
    project_cfg: Project,
    accident: Accident,
    repair: RepairMethod,
    *,
    speaker_name: str = "Finn",
    speaker_gender: str = "boy",
    partner_name: str = "Lina",
    partner_gender: str = "girl",
    teacher_name: str = "Ms. Sol",
    teacher_gender: str = "woman",
    speaker_trait: str = "curious",
    partner_trait: str = "patient",
    candid_line: str = "That won't fly like that.",
    repeat_phrase: str = "We can mend it together.",
) -> World:
    world = World()
    speaker = world.add(
        Entity(
            id=speaker_name,
            kind="character",
            type=speaker_gender,
            role="speaker",
            traits=[speaker_trait, "candid"],
            attrs={"student": True},
        )
    )
    partner = world.add(
        Entity(
            id=partner_name,
            kind="character",
            type=partner_gender,
            role="partner",
            traits=[partner_trait],
            attrs={"student": True},
        )
    )
    teacher = world.add(
        Entity(
            id=teacher_name,
            kind="character",
            type="teacher",
            role="teacher",
            label="the teacher",
        )
    )
    project = world.add(
        Entity(
            id="project",
            type="project",
            label=project_cfg.label,
            material=project_cfg.material,
            attrs={"owner": partner.id},
        )
    )
    method = world.add(
        Entity(
            id="method",
            type="repair",
            label="",
            repairable_by=set(),
        )
    )

    world.facts.update(
        mission=mission,
        project_cfg=project_cfg,
        accident=accident,
        repair=repair,
        speaker=speaker,
        partner=partner,
        teacher=teacher,
        repeat_phrase=repeat_phrase,
    )

    introduce(world, speaker, partner, teacher, mission)
    show_project(world, partner, project_cfg)

    world.para()
    accident_happens(world, speaker, partner, accident)
    candid_blurt(world, speaker, partner, candid_line)
    teacher_pause(world, teacher, speaker)

    world.para()
    apology(world, speaker, partner)
    offer_kindness(world, speaker, partner, repeat_phrase)
    repair_scene(world, speaker, partner, repair)
    offer_kindness(world, speaker, partner, repeat_phrase)

    world.para()
    if project.meters["ready"] >= THRESHOLD and partner.memes["trust"] >= THRESHOLD:
        launch(world, mission, speaker, partner, project_cfg)
        outcome = "reconciled"
    elif project.meters["ready"] >= THRESHOLD:
        world.say(
            f"The project worked again, but the room still felt a little quiet. "
            f"They finished the mission, though the friendship was still mending."
        )
        outcome = "repaired"
    else:
        world.say(
            f"The launch had to wait for later. Even so, {speaker.id} stayed beside "
            f"{partner.id} to keep trying."
        )
        outcome = "unrepaired"

    world.facts.update(
        hurt=partner.memes["hurt"] >= THRESHOLD,
        repaired=project.meters["ready"] >= THRESHOLD,
        reconciled=partner.memes["trust"] >= THRESHOLD,
        outcome=outcome,
        candid_line=candid_line,
    )
    return world


KNOWLEDGE = {
    "space": [
        (
            "What is a launch countdown?",
            "A launch countdown is when people count backward before something takes off. It helps everyone get ready at the same moment."
        )
    ],
    "rocket": [
        (
            "What does a rocket do?",
            "A rocket pushes itself upward or forward very fast. In stories, children often pretend a paper rocket is a real ship going into space."
        )
    ],
    "map": [
        (
            "What is a star map?",
            "A star map is a picture that helps you find where stars are. It is like a guide for the sky."
        )
    ],
    "moon": [
        (
            "What is a crater?",
            "A crater is a round hollow place on the moon or on a planet. It can be made by something hitting the ground long ago."
        )
    ],
    "repair": [
        (
            "What does repair mean?",
            "Repair means to fix something that got damaged or broken. You make it useful again."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness means choosing words and actions that help someone feel cared for. It can be as small as helping, listening, or saying sorry."
        )
    ],
    "honesty": [
        (
            "Can honest words still hurt?",
            "Yes. Honest words can hurt if they are said too sharply. Honest words are best when they are also gentle and helpful."
        )
    ],
    "tape": [
        (
            "What does tape do in a craft project?",
            "Tape can hold pieces together so they stay in place. It is useful for quick fixes."
        )
    ],
    "marker": [
        (
            "Why do marker lines smudge?",
            "Marker lines can smudge when the ink is still fresh and something rubs across them. Then the color spreads into a blur."
        )
    ],
    "paper": [
        (
            "Why does paper get weak when it gets wet?",
            "Paper is made of tiny fibers. When it gets wet, the fibers loosen and the paper can tear or sag."
        )
    ],
}
KNOWLEDGE_ORDER = ["space", "rocket", "map", "moon", "repair", "kindness", "honesty", "tape", "marker", "paper"]


@dataclass
class StoryParams:
    mission: str
    project: str
    accident: str
    repair: str
    speaker: str
    speaker_gender: str
    partner: str
    partner_gender: str
    teacher: str
    speaker_trait: str
    partner_trait: str
    candid_line: str
    repeat_phrase: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mission = f["mission"]
    project = f["project_cfg"]
    speaker = f["speaker"]
    partner = f["partner"]
    phrase = f["repeat_phrase"]
    return [
        f'Write a short space adventure for young children that includes the words "candid" and "student".',
        f"Tell a classroom space story where {speaker.id}, a candid student, hurts {partner.id}'s feelings after an accident with a {project.label}, then apologises and helps repair it.",
        f'Write a gentle story with repetition, reconciliation, and kindness, and repeat the line "{phrase}" as the friendship heals during a pretend mission.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    mission = f["mission"]
    project = f["project_cfg"]
    accident = f["accident"]
    repair = f["repair"]
    speaker = f["speaker"]
    partner = f["partner"]
    teacher = f["teacher"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two students, {speaker.id} and {partner.id}, during {teacher.id}'s pretend space lesson. They are trying to finish a mission together."
        ),
        (
            f"What went wrong with the {project.label}?",
            f"{speaker.id} {accident.verb}, and {accident.result}. That left the {project.label} damaged right before launch."
        ),
        (
            f"Why did {partner.id} feel hurt?",
            f"{partner.id} felt hurt because the accident already felt bad, and then {speaker.id} spoke too sharply. The candid words came out fast instead of kindly."
        ),
        (
            f"How did {teacher.id} help?",
            f"{teacher.id} reminded {speaker.id} that being candid should still be helpful. That pause helped turn the moment from blame toward kindness."
        ),
    ]
    if outcome == "reconciled":
        qa.append(
            (
                f"How did {speaker.id} and {partner.id} make peace again?",
                f"{speaker.id} said sorry, repeated, \"{f['repeat_phrase']}\", and helped repair the {project.label}. The apology mattered because it was followed by kind work side by side."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"They launched their mission together at {mission.launch_place}. The ending shows reconciliation because the project was fixed and their friendship felt bright again."
            )
        )
    elif outcome == "repaired":
        qa.append(
            (
                "Did they fix the project?",
                f"Yes, they repaired it with {repair.label}. But feelings take longer than paper or tape, so the friendship was still mending."
            )
        )
    else:
        qa.append(
            (
                "Why did the launch have to wait?",
                f"The chosen repair did not really solve the damage. They needed more time because kindness had begun, but the project was not ready yet."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"space", "repair", "kindness", "honesty"}
    mission = world.facts["mission"]
    project = world.facts["project_cfg"]
    repair = world.facts["repair"]
    accident = world.facts["accident"]
    tags |= set(mission.tags)
    tags |= set(project.tags)
    tags |= set(repair.tags)
    tags |= set(accident.tags)
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.material:
            bits.append(f"material={ent.material}")
        if ent.damage_kind:
            bits.append(f"damage={ent.damage_kind}")
        if ent.repairable_by:
            bits.append(f"repairable_by={sorted(ent.repairable_by)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mission="moon_garden",
        project="rocket",
        accident="juice_spill",
        repair="dry_patch",
        speaker="Finn",
        speaker_gender="boy",
        partner="Lina",
        partner_gender="girl",
        teacher="Ms. Sol",
        speaker_trait="curious",
        partner_trait="patient",
        candid_line="That won't fly like that.",
        repeat_phrase="We can mend it together.",
    ),
    StoryParams(
        mission="comet_mail",
        project="star_map",
        accident="boot_bump",
        repair="smooth_tape",
        speaker="Maya",
        speaker_gender="girl",
        partner="Leo",
        partner_gender="boy",
        teacher="Ms. Sol",
        speaker_trait="thoughtful",
        partner_trait="careful",
        candid_line="That looks all wrong now.",
        repeat_phrase="We can mend it together.",
    ),
    StoryParams(
        mission="ring_rescue",
        project="star_map",
        accident="marker_smudge",
        repair="wipe_redraw",
        speaker="Theo",
        speaker_gender="boy",
        partner="Iris",
        partner_gender="girl",
        teacher="Ms. Sol",
        speaker_trait="gentle",
        partner_trait="brave",
        candid_line="That mission piece is a mess.",
        repeat_phrase="Side by side, space friend.",
    ),
    StoryParams(
        mission="moon_garden",
        project="moon_model",
        accident="boot_bump",
        repair="smooth_tape",
        speaker="Nora",
        speaker_gender="girl",
        partner="Milo",
        partner_gender="boy",
        teacher="Ms. Sol",
        speaker_trait="careful",
        partner_trait="patient",
        candid_line="That looks all wrong now.",
        repeat_phrase="We can mend it together.",
    ),
]


def explain_rejection(project: Project, accident: Accident, repair: Optional[RepairMethod] = None) -> str:
    if not project_harmed(project, accident):
        return (
            f"(No story: {accident.label} does not make the right kind of damage for a {project.material} "
            f"{project.label}. The accident would not honestly threaten the project.)"
        )
    if repair is not None and repair.sense < SENSE_MIN:
        return (
            f"(Refusing repair '{repair.id}': it scores too low on common sense "
            f"(sense={repair.sense} < {SENSE_MIN}). Pick a repair that actually fixes the damage.)"
        )
    if repair is not None and not repair_fits(accident, repair):
        return (
            f"(No story: {repair.label} does not fix {accident.damage} damage. "
            f"The repair must match what went wrong.)"
        )
    return "(No story: no valid combination matches the given options.)"


def outcome_of(params: StoryParams) -> str:
    repair = REPAIRS[params.repair]
    accident = ACCIDENTS[params.accident]
    if repair.sense < SENSE_MIN or not repair_fits(accident, repair):
        return "unrepaired"
    return "reconciled"


ASP_RULES = r"""
harms(P, A) :- project(P), accident(A), material(P, paper), damage(A, wet).
harmS(P, A) :- project(P), accident(A), material(P, paper), damage(A, smudged).
harms(P, A) :- project(P), accident(A), material(P, foil), damage(A, bent).
harmS(P, A) :- project(P), accident(A), material(P, foil), damage(A, smudged).
harms(P, A) :- project(P), accident(A), material(P, clay), damage(A, wet).
harmS(P, A) :- project(P), accident(A), material(P, clay), damage(A, bent).

harms(P, A) :- harmS(P, A).

sensible(R) :- repair(R), sense(R, S), sense_min(M), S >= M.
fits(A, R) :- accident(A), repair(R), damage(A, D), fixes(R, D).
valid(M, P, A) :- mission(M), project(P), accident(A), harms(P, A), 1 { repair(R) : sensible(R), fits(A, R) }.

outcome(unrepaired) :- chosen_repair(R), not sensible(R).
outcome(unrepaired) :- chosen_accident(A), chosen_repair(R), sensible(R), not fits(A, R).
outcome(reconciled) :- chosen_accident(A), chosen_repair(R), sensible(R), fits(A, R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mid in MISSIONS:
        lines.append(asp.fact("mission", mid))
    for pid, p in PROJECTS.items():
        lines.append(asp.fact("project", pid))
        lines.append(asp.fact("material", pid, p.material))
    for aid, a in ACCIDENTS.items():
        lines.append(asp.fact("accident", aid))
        lines.append(asp.fact("damage", aid, a.damage))
    for rid, r in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        for d in sorted(r.fixes):
            lines.append(asp.fact("fixes", rid, d))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join(
        [
            asp.fact("chosen_accident", params.accident),
            asp.fact("chosen_repair", params.repair),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a candid student, a small hurt, a kind repair, and a classroom space adventure."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--accident", choices=ACCIDENTS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.project and args.accident:
        project = PROJECTS[args.project]
        accident = ACCIDENTS[args.accident]
        if not project_harmed(project, accident):
            raise StoryError(explain_rejection(project, accident))
    if args.repair:
        repair = REPAIRS[args.repair]
        if repair.sense < SENSE_MIN:
            project = PROJECTS[args.project] if args.project else next(iter(PROJECTS.values()))
            accident = ACCIDENTS[args.accident] if args.accident else next(iter(ACCIDENTS.values()))
            raise StoryError(explain_rejection(project, accident, repair))
        if args.accident and not repair_fits(ACCIDENTS[args.accident], repair):
            project = PROJECTS[args.project] if args.project else next(iter(PROJECTS.values()))
            raise StoryError(explain_rejection(project, ACCIDENTS[args.accident], repair))

    combos = [
        c for c in valid_combos()
        if (args.mission is None or c[0] == args.mission)
        and (args.project is None or c[1] == args.project)
        and (args.accident is None or c[2] == args.accident)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, project_id, accident_id = rng.choice(sorted(combos))
    accident = ACCIDENTS[accident_id]

    fitting_repairs = [
        r.id for r in sensible_repairs()
        if repair_fits(accident, r)
        and (args.repair is None or r.id == args.repair)
    ]
    if not fitting_repairs:
        raise StoryError("(No valid repair matches the given options.)")
    repair_id = rng.choice(sorted(fitting_repairs))

    speaker, speaker_gender = _pick_name(rng)
    partner, partner_gender = _pick_name(rng, avoid=speaker)
    speaker_trait = rng.choice(TRAITS)
    partner_trait = rng.choice(TRAITS)
    return StoryParams(
        mission=mission_id,
        project=project_id,
        accident=accident_id,
        repair=repair_id,
        speaker=speaker,
        speaker_gender=speaker_gender,
        partner=partner,
        partner_gender=partner_gender,
        teacher="Ms. Sol",
        speaker_trait=speaker_trait,
        partner_trait=partner_trait,
        candid_line=rng.choice(CANDID_LINES),
        repeat_phrase=rng.choice(KIND_PHRASES),
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.accident not in ACCIDENTS:
        raise StoryError(f"(Unknown accident: {params.accident})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")

    mission = MISSIONS[params.mission]
    project = PROJECTS[params.project]
    accident = ACCIDENTS[params.accident]
    repair = REPAIRS[params.repair]

    if not project_harmed(project, accident):
        raise StoryError(explain_rejection(project, accident))
    if repair.sense < SENSE_MIN:
        raise StoryError(explain_rejection(project, accident, repair))
    if not repair_fits(accident, repair):
        raise StoryError(explain_rejection(project, accident, repair))

    world = tell(
        mission=mission,
        project_cfg=project,
        accident=accident,
        repair=repair,
        speaker_name=params.speaker,
        speaker_gender=params.speaker_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
        teacher_name=params.teacher,
        speaker_trait=params.speaker_trait,
        partner_trait=params.partner_trait,
        candid_line=params.candid_line,
        repeat_phrase=params.repeat_phrase,
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
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_sens = set(asp_sensible())
    python_sens = {r.id for r in sensible_repairs()}
    if clingo_sens == python_sens:
        print(f"OK: sensible repairs match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible repairs: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(p)

    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        emit(sample, trace=False, qa=False)
        print("OK: smoke-test generation/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible repairs: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (mission, project, accident) combos:\n")
        for mission, project, accident in combos:
            print(f"  {mission:12} {project:10} {accident}")
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
            header = f"### {p.speaker} & {p.partner}: {p.project} / {p.accident} / {p.mission}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
