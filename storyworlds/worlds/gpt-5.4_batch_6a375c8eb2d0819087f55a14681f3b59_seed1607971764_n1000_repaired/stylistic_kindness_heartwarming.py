#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/stylistic_kindness_heartwarming.py
=============================================================

A standalone story world about a small act of kindness in a classroom craft
corner. Two children are making something welcoming for a new classmate. A
mishap damages one child's project, another child notices the hurt, and the
right kind offer helps the project -- and the friendship -- come back together.

This world stays close to a heartwarming style: soft tension, a concrete turn,
and an ending image that proves belonging changed in the room.

Run it
------
    python storyworlds/worlds/gpt-5.4/stylistic_kindness_heartwarming.py
    python storyworlds/worlds/gpt-5.4/stylistic_kindness_heartwarming.py --project name_card --damage tear
    python storyworlds/worlds/gpt-5.4/stylistic_kindness_heartwarming.py --tool blotter
    python storyworlds/worlds/gpt-5.4/stylistic_kindness_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/stylistic_kindness_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/stylistic_kindness_heartwarming.py --trace
    python storyworlds/worlds/gpt-5.4/stylistic_kindness_heartwarming.py --json
    python storyworlds/worlds/gpt-5.4/stylistic_kindness_heartwarming.py --asp
    python storyworlds/worlds/gpt-5.4/stylistic_kindness_heartwarming.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
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
    owner: str = ""
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
class Place:
    id: str
    label: str
    detail: str
    affords: set[str] = field(default_factory=set)
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
class Project:
    id: str
    label: str
    phrase: str
    material: str
    display_spot: str
    opening_line: str
    closing_line: str
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
class Damage:
    id: str
    kind: str
    severity: int
    cause: str
    mark: str
    comfort_line: str
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
class Tool:
    id: str
    label: str
    phrase: str
    handles: set[str]
    materials: set[str]
    power: int
    remake: bool = False
    offer: str = ""
    fix_text: str = ""
    qa_text: str = ""
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_damage_worry(world: World) -> list[str]:
    out: list[str] = []
    project = world.get("project")
    owner = world.get(project.owner)
    if project.meters["damaged"] >= THRESHOLD:
        sig = ("worry", project.id)
        if sig not in world.fired:
            world.fired.add(sig)
            owner.memes["worry"] += 1
            owner.memes["small"] += 1
            out.append("__damage__")
    return out


def _r_kindness_trust(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    newcomer = world.get("newcomer")
    if helper.memes["kind_offer"] >= THRESHOLD:
        sig = ("trust", helper.id)
        if sig not in world.fired:
            world.fired.add(sig)
            helper.memes["kindness"] += 1
            newcomer.memes["trust"] += 1
            out.append("__kindness__")
    return out


def _r_fix_relief(world: World) -> list[str]:
    out: list[str] = []
    project = world.get("project")
    newcomer = world.get("newcomer")
    if project.meters["fixed"] >= THRESHOLD or project.meters["remade"] >= THRESHOLD:
        sig = ("relief", project.id)
        if sig not in world.fired:
            world.fired.add(sig)
            newcomer.memes["relief"] += 1
            newcomer.memes["hope"] += 1
            newcomer.memes["worry"] = 0.0
            out.append("__fixed__")
    return out


def _r_display_belonging(world: World) -> list[str]:
    out: list[str] = []
    project = world.get("project")
    helper = world.get("helper")
    newcomer = world.get("newcomer")
    if project.meters["display_ready"] >= THRESHOLD:
        sig = ("belonging", project.id)
        if sig not in world.fired:
            world.fired.add(sig)
            newcomer.memes["belonging"] += 1
            helper.memes["joy"] += 1
            newcomer.memes["joy"] += 1
            out.append("__display__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="damage_worry", tag="emotional", apply=_r_damage_worry),
    Rule(name="kindness_trust", tag="social", apply=_r_kindness_trust),
    Rule(name="fix_relief", tag="emotional", apply=_r_fix_relief),
    Rule(name="display_belonging", tag="social", apply=_r_display_belonging),
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


def damage_affects(project: Project, damage: Damage) -> bool:
    if project.material == "fabric" and damage.kind == "smudge":
        return False
    if project.material == "fabric" and damage.kind == "crease":
        return False
    return True


def tool_works(project: Project, damage: Damage, tool: Tool) -> bool:
    if project.material not in tool.materials:
        return False
    if damage.kind not in tool.handles:
        return False
    if tool.remake:
        return True
    return tool.power >= damage.severity


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for project_id in sorted(place.affords):
            project = PROJECTS[project_id]
            for damage_id, damage in DAMAGES.items():
                if not damage_affects(project, damage):
                    continue
                for tool_id, tool in TOOLS.items():
                    if tool_works(project, damage, tool):
                        combos.append((place_id, project_id, damage_id, tool_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    project = PROJECTS[params.project]
    damage = DAMAGES[params.damage]
    tool = TOOLS[params.tool]
    if not damage_affects(project, damage):
        return "invalid"
    if not tool_works(project, damage, tool):
        return "invalid"
    return "remade" if tool.remake else "repaired"


def predict_fix(project: Project, damage: Damage, tool: Tool) -> dict[str, object]:
    return {
        "works": tool_works(project, damage, tool),
        "outcome": "remade" if tool.remake else "repaired",
    }


def introduce(world: World, helper: Entity, newcomer: Entity, teacher: Entity, project: Project) -> None:
    world.say(
        f"In {world.place.label}, {teacher.label} set out paper, ribbons, and crayons for a small welcome craft."
    )
    world.say(
        f"{helper.id} and {newcomer.id} sat side by side to make {project.phrase}."
    )
    world.say(
        f"{teacher.label.capitalize()} showed them how a few stylistic loops and tiny stars could make each piece feel warm and special."
    )
    helper.memes["attention"] += 1
    newcomer.memes["hope"] += 1


def build_project(world: World, newcomer: Entity, project: Project) -> None:
    project_ent = world.get("project")
    project_ent.meters["made"] += 1
    world.say(project.opening_line.replace("{name}", newcomer.id))
    world.say(
        f"{newcomer.id} worked very carefully, wanting the finished {project.label} to look just right."
    )


def accident(world: World, newcomer: Entity, damage: Damage) -> None:
    project = world.get("project")
    project.meters["damaged"] += 1
    project.meters[damage.kind] += 1
    world.facts["damage_seen"] = True
    propagate(world, narrate=False)
    world.say(
        f"Then {damage.cause}, and a {damage.mark} spread across the project."
    )
    if newcomer.memes["worry"] >= THRESHOLD:
        world.say(
            f"{newcomer.id} grew very still. {damage.comfort_line}"
        )


def notice(world: World, helper: Entity, newcomer: Entity) -> None:
    helper.memes["notice"] += 1
    world.say(
        f"{helper.id} saw {newcomer.id}'s face change and scooted a little closer instead of looking away."
    )
    world.say(
        f'"It does not have to stay ruined," {helper.pronoun()} said softly.'
    )


def offer_help(world: World, helper: Entity, newcomer: Entity, tool: Tool, project: Project, damage: Damage) -> None:
    helper.memes["kind_offer"] += 1
    pred = predict_fix(project, damage, tool)
    world.facts["predicted_outcome"] = pred["outcome"]
    propagate(world, narrate=False)
    world.say(
        f"{helper.id} held up {tool.phrase}. {tool.offer}"
    )
    world.say(
        f'"If you want, I can help," {helper.pronoun()} added, making room on the table for {newcomer.pronoun("object")}.'
    )


def fix_project(world: World, helper: Entity, newcomer: Entity, tool: Tool, project_cfg: Project) -> None:
    project = world.get("project")
    if tool.remake:
        project.meters["remade"] += 1
        project.meters["damaged"] = 0.0
        project.meters["fixed"] = 1.0
        world.say(
            f"Together they started again on a fresh piece, and {tool.fix_text}."
        )
    else:
        project.meters["fixed"] += 1
        project.meters["damaged"] = 0.0
        world.say(
            f"Together they leaned close over the table, and {tool.fix_text}."
        )
    propagate(world, narrate=False)
    world.say(
        f"Soon the {project_cfg.label} looked whole and cared for again."
    )


def display(world: World, helper: Entity, newcomer: Entity, teacher: Entity, project: Project) -> None:
    project_ent = world.get("project")
    project_ent.meters["display_ready"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When {teacher.label} came by, {teacher.pronoun()} smiled and placed it {project.display_spot}."
    )
    world.say(
        f"{newcomer.id} looked up at it, then over at {helper.id}, with a much easier smile."
    )


def ending(world: World, helper: Entity, newcomer: Entity, project: Project) -> None:
    helper.memes["friendship"] += 1
    newcomer.memes["friendship"] += 1
    world.say(
        f"After that, {helper.id} saved a seat for {newcomer.id} and slid the crayon tray to the middle so they could share."
    )
    world.say(
        project.closing_line.replace("{helper}", helper.id).replace("{newcomer}", newcomer.id)
    )


def tell(
    place: Place,
    project_cfg: Project,
    damage_cfg: Damage,
    tool_cfg: Tool,
    helper_name: str = "Nora",
    helper_gender: str = "girl",
    newcomer_name: str = "Owen",
    newcomer_gender: str = "boy",
    teacher_type: str = "teacher",
    helper_trait: str = "gentle",
    newcomer_trait: str = "shy",
) -> World:
    world = World(place)
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            label=helper_name,
            role="helper",
            traits=[helper_trait],
            attrs={"trait": helper_trait},
        )
    )
    newcomer = world.add(
        Entity(
            id=newcomer_name,
            kind="character",
            type=newcomer_gender,
            label=newcomer_name,
            role="newcomer",
            traits=[newcomer_trait],
            attrs={"trait": newcomer_trait},
        )
    )
    teacher_label = "the teacher"
    teacher = world.add(
        Entity(
            id="Teacher",
            kind="character",
            type=teacher_type,
            label=teacher_label,
            role="teacher",
            attrs={},
        )
    )
    project = world.add(
        Entity(
            id="project",
            kind="thing",
            type=project_cfg.material,
            label=project_cfg.label,
            owner=newcomer.id,
            attrs={"display_spot": project_cfg.display_spot},
        )
    )
    tool = world.add(
        Entity(
            id="tool",
            kind="thing",
            type="tool",
            label=tool_cfg.label,
            owner=helper.id,
            attrs={"remake": tool_cfg.remake},
        )
    )

    world.facts.update(
        place=place,
        project_cfg=project_cfg,
        damage_cfg=damage_cfg,
        tool_cfg=tool_cfg,
        helper=helper,
        newcomer=newcomer,
        teacher=teacher,
        project=project,
        tool=tool,
        damage_seen=False,
        predicted_outcome="",
    )

    introduce(world, helper, newcomer, teacher, project_cfg)
    build_project(world, newcomer, project_cfg)

    world.para()
    accident(world, newcomer, damage_cfg)
    notice(world, helper, newcomer)

    world.para()
    offer_help(world, helper, newcomer, tool_cfg, project_cfg, damage_cfg)
    fix_project(world, helper, newcomer, tool_cfg, project_cfg)
    display(world, helper, newcomer, teacher, project_cfg)

    world.para()
    ending(world, helper, newcomer, project_cfg)

    world.facts.update(
        outcome="remade" if tool_cfg.remake else "repaired",
        display_ready=world.get("project").meters["display_ready"] >= THRESHOLD,
        belonging=newcomer.memes["belonging"] >= THRESHOLD,
        kindness=helper.memes["kindness"] >= THRESHOLD,
    )
    return world


PLACES = {
    "classroom": Place(
        id="classroom",
        label="the classroom art corner",
        detail="sunlight on the shelf of glue sticks",
        affords={"name_card", "welcome_poster", "paper_chain"},
    ),
    "library": Place(
        id="library",
        label="the library craft table",
        detail="quiet shelves and a basket of bright paper",
        affords={"name_card", "paper_chain"},
    ),
    "hallway": Place(
        id="hallway",
        label="the sunny hallway table",
        detail="hooks, cubbies, and a wall ready for cheerful work",
        affords={"name_card", "welcome_poster"},
    ),
}

PROJECTS = {
    "name_card": Project(
        id="name_card",
        label="name card",
        phrase="a name card for the cubby",
        material="paper",
        display_spot="above the new cubby",
        opening_line="{name} wrote the letters slowly, tracing each one with bright color.",
        closing_line="By the end of the morning, the little card above the cubby looked like it had been waiting all along for {newcomer}.",
        tags={"paper", "welcome", "classroom"},
    ),
    "welcome_poster": Project(
        id="welcome_poster",
        label="welcome poster",
        phrase="a welcome poster for the wall",
        material="cardstock",
        display_spot="on the wall by the door",
        opening_line="{name} drew a wide sun at the top and left room for a big friendly hello.",
        closing_line="When the poster fluttered by the door, it felt as if the whole room had opened its arms to {newcomer}.",
        tags={"poster", "welcome", "classroom"},
    ),
    "paper_chain": Project(
        id="paper_chain",
        label="paper chain",
        phrase="a paper chain for the reading nook",
        material="paper",
        display_spot="across the reading nook",
        opening_line="{name} looped colored strips into careful circles, one after another.",
        closing_line="The chain swayed gently over the books, and {helper} and {newcomer} kept glancing up at it as if it were smiling back.",
        tags={"paper", "reading", "welcome"},
    ),
}

DAMAGES = {
    "tear": Damage(
        id="tear",
        kind="tear",
        severity=2,
        cause="one eager tug pulled too hard",
        mark="small rip",
        comfort_line="For a second, it seemed as if all the careful work had come undone.",
        tags={"tear", "paper"},
    ),
    "smudge": Damage(
        id="smudge",
        kind="smudge",
        severity=1,
        cause="a damp sleeve brushed the fresh colors",
        mark="soft smear",
        comfort_line="The colors blurred together, and the project no longer looked the way it had a moment before.",
        tags={"smudge", "paper"},
    ),
    "crease": Damage(
        id="crease",
        kind="crease",
        severity=1,
        cause="a bent corner folded under a little elbow",
        mark="deep crease",
        comfort_line="It was not broken all the way through, but it looked tired and crumpled.",
        tags={"crease", "paper"},
    ),
}

TOOLS = {
    "tape": Tool(
        id="tape",
        label="clear tape",
        phrase="the roll of clear tape",
        handles={"tear"},
        materials={"paper", "cardstock"},
        power=2,
        remake=False,
        offer='"We can line the edges up and mend it together."',
        fix_text="the tear was matched edge to edge and held neatly with clear tape",
        qa_text="They lined up the torn edges and mended the project with clear tape.",
        tags={"tape", "repair"},
    ),
    "blotter": Tool(
        id="blotter",
        label="blotting paper",
        phrase="a square of blotting paper",
        handles={"smudge"},
        materials={"paper", "cardstock"},
        power=1,
        remake=False,
        offer='"We can lift the extra wet color before it spreads any more."',
        fix_text="the wet color was gently blotted away until the letters could be seen clearly again",
        qa_text="They gently blotted the wet color away so the project could be seen clearly again.",
        tags={"blotting", "repair"},
    ),
    "sticker_border": Tool(
        id="sticker_border",
        label="a box of heart stickers",
        phrase="a box of heart stickers",
        handles={"crease"},
        materials={"paper"},
        power=1,
        remake=False,
        offer='"We can smooth it down and make the corner pretty again with these."',
        fix_text="the crease was smoothed, then covered with a tiny border of heart stickers",
        qa_text="They smoothed the bent spot and covered it with heart stickers.",
        tags={"stickers", "repair"},
    ),
    "fresh_sheet": Tool(
        id="fresh_sheet",
        label="fresh cardstock",
        phrase="a fresh sheet of paper",
        handles={"tear", "smudge", "crease"},
        materials={"paper", "cardstock"},
        power=0,
        remake=True,
        offer='"We still have time. We can start over on a fresh sheet, and I will help with every part."',
        fix_text="the old mistake stayed behind while a new bright version took shape",
        qa_text="They started again on a fresh sheet and rebuilt the project together.",
        tags={"paper", "redo", "repair"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Maya", "Ava", "Ella", "Mina", "Ruby", "Zoe"]
BOY_NAMES = ["Owen", "Theo", "Ben", "Leo", "Eli", "Max", "Noah", "Sam"]
HELPER_TRAITS = ["gentle", "kind", "patient", "thoughtful", "warm"]
NEWCOMER_TRAITS = ["shy", "quiet", "careful", "hopeful"]


@dataclass
class StoryParams:
    place: str
    project: str
    damage: str
    tool: str
    helper_name: str
    helper_gender: str
    newcomer_name: str
    newcomer_gender: str
    teacher_type: str = "teacher"
    helper_trait: str = "gentle"
    newcomer_trait: str = "shy"
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
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to help, comfort, or include someone else. Even a small kind act can make another person feel safer and less alone.",
        )
    ],
    "welcome": [
        (
            "Why is welcoming someone new important?",
            "Welcoming someone new helps them feel that they belong. A friendly word or shared activity can make a strange place feel softer and safer.",
        )
    ],
    "tape": [
        (
            "What does tape do on torn paper?",
            "Tape holds the torn edges together so the paper can stay in one piece. It cannot make the tear disappear, but it can help the page work again.",
        )
    ],
    "blotting": [
        (
            "What does blotting paper do?",
            "Blotting paper soaks up extra wet ink or paint. That can stop a smudge from spreading farther.",
        )
    ],
    "stickers": [
        (
            "How can stickers help in a craft?",
            "Stickers can decorate a craft, and they can also cover a bent or messy little spot. They turn a mistake into part of the design.",
        )
    ],
    "redo": [
        (
            "Is it okay to start a project over?",
            "Yes. Starting over can be a calm, brave choice when something is too messy to fix the first way.",
        )
    ],
    "paper": [
        (
            "Why does paper tear or crease easily?",
            "Paper is light and thin, so a hard tug or bend can damage it quickly. That is why careful hands help during crafts.",
        )
    ],
    "poster": [
        (
            "What is a poster for?",
            "A poster is a big paper sign people can see from across the room. It can share a message or help a place feel cheerful.",
        )
    ],
    "reading": [
        (
            "What is a reading nook?",
            "A reading nook is a small cozy place for sitting with books. Soft decorations can make it feel inviting and calm.",
        )
    ],
}
KNOWLEDGE_ORDER = ["kindness", "welcome", "paper", "tape", "blotting", "stickers", "redo", "poster", "reading"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    helper = f["helper"]
    newcomer = f["newcomer"]
    project = f["project_cfg"]
    damage = f["damage_cfg"]
    tool = f["tool_cfg"]
    outcome = f["outcome"]
    return [
        'Write a heartwarming story for a 3-to-5-year-old about kindness during a classroom craft, and include the word "stylistic".',
        f"Tell a gentle story where {newcomer.id} damages {newcomer.pronoun('possessive')} {project.label}, and {helper.id} notices the hurt and helps with {tool.label}.",
        f"Write a warm school story where a small {damage.kind} almost ruins a welcome craft, but a kind child turns the moment into friendship and a {outcome} ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    helper = f["helper"]
    newcomer = f["newcomer"]
    teacher = f["teacher"]
    project = f["project_cfg"]
    damage = f["damage_cfg"]
    tool = f["tool_cfg"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {helper.id} and {newcomer.id} making {project.phrase} with {teacher.label}. The story follows how one child's kindness changes a hard moment.",
        ),
        (
            f"What went wrong with {newcomer.id}'s {project.label}?",
            f"{damage.cause.capitalize()}, and a {damage.mark} hurt the project. That made {newcomer.id} worry because the careful work no longer looked the way {newcomer.pronoun('subject')} wanted.",
        ),
        (
            f"How did {helper.id} show kindness?",
            f"{helper.id} noticed {newcomer.id}'s face right away and moved closer instead of ignoring the problem. Then {helper.pronoun('subject')} offered {tool.label} and gentle help, which made the table feel safer.",
        ),
    ]
    if outcome == "repaired":
        qa.append(
            (
                f"How was the project fixed?",
                f"{tool.qa_text} The repair worked because {tool.label} matched the kind of damage on the {project.label}.",
            )
        )
    else:
        qa.append(
            (
                "Did they fix the old project or make a new one?",
                f"They made a new one together on a fresh sheet. Starting over helped because the damage was left behind while the kindness stayed with them.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"The finished {project.label} was placed {project.display_spot}, and {newcomer.id} felt that {newcomer.pronoun('subject')} belonged there. The last part feels warm because the project was mended, but so was the lonely feeling too.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"kindness", "welcome"} | set(f["project_cfg"].tags) | set(f["damage_cfg"].tags) | set(f["tool_cfg"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="classroom",
        project="name_card",
        damage="tear",
        tool="tape",
        helper_name="Nora",
        helper_gender="girl",
        newcomer_name="Owen",
        newcomer_gender="boy",
        teacher_type="teacher",
        helper_trait="gentle",
        newcomer_trait="shy",
    ),
    StoryParams(
        place="hallway",
        project="welcome_poster",
        damage="smudge",
        tool="blotter",
        helper_name="Ben",
        helper_gender="boy",
        newcomer_name="Maya",
        newcomer_gender="girl",
        teacher_type="teacher",
        helper_trait="patient",
        newcomer_trait="quiet",
    ),
    StoryParams(
        place="library",
        project="paper_chain",
        damage="crease",
        tool="sticker_border",
        helper_name="Ella",
        helper_gender="girl",
        newcomer_name="Theo",
        newcomer_gender="boy",
        teacher_type="teacher",
        helper_trait="kind",
        newcomer_trait="careful",
    ),
    StoryParams(
        place="classroom",
        project="welcome_poster",
        damage="tear",
        tool="fresh_sheet",
        helper_name="Leo",
        helper_gender="boy",
        newcomer_name="Ruby",
        newcomer_gender="girl",
        teacher_type="teacher",
        helper_trait="thoughtful",
        newcomer_trait="hopeful",
    ),
]


def explain_rejection(project: Project, damage: Damage, tool: Tool) -> str:
    if not damage_affects(project, damage):
        return (
            f"(No story: a {damage.kind} is not a sensible damage type for a {project.material} {project.label} here.)"
        )
    if project.material not in tool.materials:
        return (
            f"(No story: {tool.label} is not a sensible way to fix a {project.material} {project.label}.)"
        )
    if damage.kind not in tool.handles:
        return (
            f"(No story: {tool.label} does not address a {damage.kind}. Pick a tool that matches the damage.)"
        )
    return (
        f"(No story: {tool.label} is too weak for this {damage.kind}; it would not honestly fix the problem.)"
    )


ASP_RULES = r"""
damage_affects(P, D) :- project(P), damage(D), material(P, paper).
damage_affects(P, D) :- project(P), damage(D), material(P, cardstock).
:- damage_affects(P, D), material(P, fabric), kind(D, smudge).
:- damage_affects(P, D), material(P, fabric), kind(D, crease).

tool_works(P, D, T) :- tool(T), project(P), damage(D),
                       material(P, M), works_on_material(T, M),
                       kind(D, K), handles(T, K), remake(T).
tool_works(P, D, T) :- tool(T), project(P), damage(D),
                       material(P, M), works_on_material(T, M),
                       kind(D, K), handles(T, K),
                       severity(D, S), power(T, Pwr), Pwr >= S, not remake(T).

valid(Place, P, D, T) :- affords(Place, P), damage_affects(P, D), tool_works(P, D, T).

outcome(remade) :- chosen_tool(T), remake(T).
outcome(repaired) :- chosen_tool(T), not remake(T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for project_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, project_id))
    for project_id, project in PROJECTS.items():
        lines.append(asp.fact("project", project_id))
        lines.append(asp.fact("material", project_id, project.material))
    for damage_id, damage in DAMAGES.items():
        lines.append(asp.fact("damage", damage_id))
        lines.append(asp.fact("kind", damage_id, damage.kind))
        lines.append(asp.fact("severity", damage_id, damage.severity))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("power", tool_id, tool.power))
        if tool.remake:
            lines.append(asp.fact("remake", tool_id))
        for kind in sorted(tool.handles):
            lines.append(asp.fact("handles", tool_id, kind))
        for material in sorted(tool.materials):
            lines.append(asp.fact("works_on_material", tool_id, material))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_tool", params.tool),
            asp.fact("chosen_project", params.project),
            asp.fact("chosen_damage", params.damage),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = []
    for params in cases:
        py = outcome_of(params)
        cl = asp_outcome(params)
        if py != cl:
            bad.append((params, py, cl))
    if not bad:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)} outcomes differ.")
        for params, py, cl in bad[:5]:
            print(f"  {params} -> python={py} clingo={cl}")

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(0))
        smoke_params.seed = 0
        sample = generate(smoke_params)
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke test")
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming kindness storyworld: a damaged welcome craft, a kind helper, and a repaired belonging."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--damage", choices=DAMAGES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--newcomer-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--newcomer-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP model against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.project and args.damage and args.tool:
        project = PROJECTS[args.project]
        damage = DAMAGES[args.damage]
        tool = TOOLS[args.tool]
        if not tool_works(project, damage, tool) or not damage_affects(project, damage):
            raise StoryError(explain_rejection(project, damage, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.project is None or combo[1] == args.project)
        and (args.damage is None or combo[2] == args.damage)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, project_id, damage_id, tool_id = rng.choice(sorted(combos))
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    newcomer_gender = args.newcomer_gender or rng.choice(["girl", "boy"])
    helper_name = args.helper_name or _pick_name(rng, helper_gender)
    newcomer_name = args.newcomer_name or _pick_name(rng, newcomer_gender, avoid=helper_name)
    return StoryParams(
        place=place_id,
        project=project_id,
        damage=damage_id,
        tool=tool_id,
        helper_name=helper_name,
        helper_gender=helper_gender,
        newcomer_name=newcomer_name,
        newcomer_gender=newcomer_gender,
        teacher_type="teacher",
        helper_trait=rng.choice(HELPER_TRAITS),
        newcomer_trait=rng.choice(NEWCOMER_TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        project = PROJECTS[params.project]
        damage = DAMAGES[params.damage]
        tool = TOOLS[params.tool]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if not damage_affects(project, damage) or not tool_works(project, damage, tool):
        raise StoryError(explain_rejection(project, damage, tool))

    world = tell(
        place=place,
        project_cfg=project,
        damage_cfg=damage,
        tool_cfg=tool,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        newcomer_name=params.newcomer_name,
        newcomer_gender=params.newcomer_gender,
        teacher_type=params.teacher_type,
        helper_trait=params.helper_trait,
        newcomer_trait=params.newcomer_trait,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, project, damage, tool) combos:\n")
        for place, project, damage, tool in combos:
            print(f"  {place:10} {project:14} {damage:8} {tool}")
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
            header = f"### {p.helper_name} helps {p.newcomer_name}: {p.project} / {p.damage} / {p.tool} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
