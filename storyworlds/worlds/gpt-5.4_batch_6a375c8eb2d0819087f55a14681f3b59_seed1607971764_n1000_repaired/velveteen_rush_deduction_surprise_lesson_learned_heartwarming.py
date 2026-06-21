#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/velveteen_rush_deduction_surprise_lesson_learned_heartwarming.py
=============================================================================================

A standalone story world about a child trying to prepare a heartwarming surprise
too quickly, a helper making a careful deduction from clues, and a gentle lesson
about slowing down.

The tiny domain:
- A child wants to mend and decorate a beloved velveteen object as a surprise.
- Because the child works in a rush, a small problem appears.
- A sibling or grandparent notices clues, makes a deduction, and helps.
- The surprise still reaches its owner, and the ending image proves the lesson:
  love works better with patient hands than hurried ones.

Run it
------
    python storyworlds/worlds/gpt-5.4/velveteen_rush_deduction_surprise_lesson_learned_heartwarming.py
    python storyworlds/worlds/gpt-5.4/velveteen_rush_deduction_surprise_lesson_learned_heartwarming.py --project rabbit --helper sibling
    python storyworlds/worlds/gpt-5.4/velveteen_rush_deduction_surprise_lesson_learned_heartwarming.py --mishap paint
    python storyworlds/worlds/gpt-5.4/velveteen_rush_deduction_surprise_lesson_learned_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/velveteen_rush_deduction_surprise_lesson_learned_heartwarming.py --qa --json
    python storyworlds/worlds/gpt-5.4/velveteen_rush_deduction_surprise_lesson_learned_heartwarming.py --verify
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
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Project:
    id: str
    item_label: str
    item_phrase: str
    owner_role: str
    worn_tired: str
    repair: str
    fix_materials: set[str]
    mark_words: dict[str, str]
    reveal_line: str
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
class Mishap:
    id: str
    clue: str
    trail: str
    spot: str
    residue: str
    cause: str
    requires: set[str]
    clean_fix: str
    qa_fix: str
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
class HelperKind:
    id: str
    role_label: str
    actor_type: str
    relation_line: str
    comfort_style: str
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
class Finish:
    id: str
    label: str
    phrase: str
    materials: set[str]
    effect: str
    closing_image: str
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


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


def _r_rush_creates_mishap(world: World) -> list[str]:
    child = world.get("child")
    item = world.get("project")
    if child.memes["rushing"] < THRESHOLD:
        return []
    if item.meters["unfixed"] < THRESHOLD:
        return []
    sig = ("rushed_mishap", world.facts["mishap"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["mess"] += 1
    child.memes["worry"] += 1
    child.memes["guilt"] += 1
    return ["__mishap__"]


def _r_clues_trigger_deduction(world: World) -> list[str]:
    helper = world.get("helper")
    item = world.get("project")
    if item.meters["mess"] < THRESHOLD:
        return []
    if helper.memes["noticed_clue"] < THRESHOLD:
        return []
    sig = ("deduction", world.facts["mishap"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.memes["deduction"] += 1
    helper.memes["care"] += 1
    return ["__deduction__"]


def _r_help_repairs(world: World) -> list[str]:
    helper = world.get("helper")
    item = world.get("project")
    if helper.memes["helping"] < THRESHOLD:
        return []
    if item.meters["mess"] < THRESHOLD:
        return []
    sig = ("repair_help", world.facts["finish"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["mess"] = 0.0
    item.meters["mended"] += 1
    child = world.get("child")
    child.memes["relief"] += 1
    child.memes["gratitude"] += 1
    helper.memes["warmth"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="rush_creates_mishap", tag="physical", apply=_r_rush_creates_mishap),
    Rule(name="clues_trigger_deduction", tag="social", apply=_r_clues_trigger_deduction),
    Rule(name="help_repairs", tag="physical", apply=_r_help_repairs),
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
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def can_fix(project: Project, mishap: Mishap, finish: Finish) -> bool:
    needs = set(project.fix_materials) | set(mishap.requires)
    return needs.issubset(set(finish.materials))


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for project_id, project in PROJECTS.items():
        for mishap_id, mishap in MISHAPS.items():
            for helper_id in HELPERS:
                for finish_id, finish in FINISHES.items():
                    if can_fix(project, mishap, finish):
                        combos.append((project_id, mishap_id, helper_id, finish_id))
    return combos


def explain_rejection(project: Project, mishap: Mishap, finish: Finish) -> str:
    needs = sorted(set(project.fix_materials) | set(mishap.requires))
    have = sorted(set(finish.materials))
    return (
        f"(No story: {finish.label} cannot honestly fix this surprise. "
        f"Mending {project.item_label} after a {mishap.id} mishap needs "
        f"{', '.join(needs)}, but {finish.label} only brings {', '.join(have)}.)"
    )


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    sim.get("child").memes["rushing"] += 1
    sim.get("project").meters["unfixed"] += 1
    propagate(sim, narrate=False)
    return {
        "mess": sim.get("project").meters["mess"] >= THRESHOLD,
        "child_worry": sim.get("child").memes["worry"],
    }


def opening(world: World, child: Entity, owner: Entity, project: Project) -> None:
    child.memes["love"] += 1
    owner.memes["love"] += 1
    item = world.get("project")
    item.meters["unfixed"] += 1
    world.say(
        f"On a soft afternoon, {child.id} sat by the window with {owner.id}'s "
        f"{project.item_phrase}. It was old and much loved, with {project.worn_tired}."
    )
    world.say(
        f"{child.id} wanted to make a surprise for {owner.id}. "
        f"If {child.pronoun()} could {project.repair}, the beloved thing might feel special again."
    )


def gather(world: World, child: Entity, project: Project, finish: Finish) -> None:
    world.say(
        f"{child.id} carried the little project to a sunny corner and laid out "
        f"{finish.phrase}. The room felt full of quiet purpose."
    )


def rush(world: World, child: Entity, mishap: Mishap) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_mess"] = pred["mess"]
    world.facts["predicted_worry"] = pred["child_worry"]
    child.memes["rushing"] += 1
    world.say(
        f"But then {child.id} heard the front gate and felt a rush in {child.pronoun('possessive')} chest. "
        f'"Oh no," {child.pronoun()} whispered. "The surprise has to be ready before anyone sees."'
    )
    world.say(
        f"{child.pronoun().capitalize()} worked too fast, and soon {mishap.cause}. "
        f"{mishap.trail.capitalize()} lay where careful hands would never have left it."
    )
    propagate(world, narrate=False)


def hide(world: World, child: Entity, mishap: Mishap) -> None:
    child.memes["embarrassment"] += 1
    world.say(
        f"{child.id} tucked the half-finished gift behind a cushion and tried to smooth away "
        f"{mishap.spot}, but {mishap.residue} still showed."
    )


def notice(world: World, helper: Entity, mishap: Mishap, helper_kind: HelperKind) -> None:
    helper.memes["noticed_clue"] += 1
    helper.memes["curiosity"] += 1
    world.say(
        f"Soon {helper.id} came in. {helper_kind.relation_line} "
        f"{helper.pronoun().capitalize()} paused when {helper.pronoun()} noticed {mishap.clue}."
    )
    propagate(world, narrate=False)


def deduce(world: World, helper: Entity, child: Entity, project: Project, mishap: Mishap) -> None:
    helper.memes["gentleness"] += 1
    world.say(
        f'"I have a deduction," {helper.id} said softly. '
        f'"There is {mishap.residue}, the sewing basket is open, and you are guarding that cushion with both hands."'
    )
    world.say(
        f"{helper.id} smiled instead of scolding. "
        f'"You are fixing {owner_phrase(world)} {project.item_label} as a surprise, aren\'t you?"'
    )


def owner_phrase(world: World) -> str:
    owner = world.get("owner")
    return owner.id + "'s"


def confess(world: World, child: Entity, owner: Entity, project: Project, mishap: Mishap) -> None:
    child.memes["honesty"] += 1
    world.say(
        f"{child.id}'s eyes grew shiny. "
        f'"I wanted to {project.repair} for {owner.id}," {child.pronoun()} admitted. '
        f'"But I was in such a rush that {mishap.cause}."'
    )


def comfort_and_help(
    world: World,
    helper: Entity,
    child: Entity,
    helper_kind: HelperKind,
    finish: Finish,
    mishap: Mishap,
) -> None:
    helper.memes["helping"] += 1
    child.memes["trust"] += 1
    world.say(
        f'{helper.id} sat beside {child.id} and {helper_kind.comfort_style}. '
        f'"A loving surprise does not have to be a hurried surprise," {helper.pronoun()} said.'
    )
    world.say(
        f"Together they used {finish.phrase} to set things right. "
        f"{mishap.clean_fix.capitalize()}, and {finish.effect}."
    )
    propagate(world, narrate=False)


def reveal(world: World, child: Entity, owner: Entity, project: Project, finish: Finish) -> None:
    child.memes["joy"] += 1
    owner.memes["surprise"] += 1
    owner.memes["joy"] += 1
    world.say(
        f"When {owner.id} came in, {child.id} held out the mended gift with both hands. "
        f"{project.reveal_line}"
    )
    world.say(
        f"{owner.id} looked at the {project.item_label}, then at {child.id}, and smiled the kind of smile "
        f"that makes a whole room warmer."
    )
    world.say(
        f'The surprise was even sweeter because it had been saved with patience. '
        f'Soon the {project.item_label} {finish.closing_image}, and {child.id} remembered the lesson: '
        f'when love is doing the work, it is better to slow down than to rush.'
    )


def tell(
    project: Project,
    mishap: Mishap,
    helper_kind: HelperKind,
    finish: Finish,
    child_name: str = "Nora",
    child_gender: str = "girl",
    helper_name: str = "Eli",
    owner_name: str = "Mina",
    owner_gender: str = "girl",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        label=child_name,
        attrs={},
        tags={"child"},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_kind.actor_type,
        role="helper",
        label=helper_name,
        attrs={"helper_kind": helper_kind.id},
        tags=set(helper_kind.tags),
    ))
    owner = world.add(Entity(
        id=owner_name,
        kind="character",
        type=owner_gender,
        role="owner",
        label=owner_name,
        attrs={"owner_role": project.owner_role},
        tags={"owner"},
    ))
    item = world.add(Entity(
        id="project",
        kind="thing",
        type="gift",
        label=project.item_label,
        phrase=project.item_phrase,
        owner=owner.id,
        attrs={"project_id": project.id},
        tags=set(project.tags),
    ))

    child.memes["rushing"] = 0.0
    child.memes["worry"] = 0.0
    helper.memes["noticed_clue"] = 0.0
    helper.memes["helping"] = 0.0
    item.meters["unfixed"] = 0.0
    item.meters["mess"] = 0.0
    item.meters["mended"] = 0.0

    world.facts.update(
        project=project,
        mishap=mishap,
        helper_kind=helper_kind,
        finish=finish,
        child=child,
        helper=helper,
        owner=owner,
        item=item,
        predicted_mess=False,
        predicted_worry=0.0,
    )

    opening(world, child, owner, project)
    gather(world, child, project, finish)

    world.para()
    rush(world, child, mishap)
    hide(world, child, mishap)

    world.para()
    notice(world, helper, mishap, helper_kind)
    deduce(world, helper, child, project, mishap)
    confess(world, child, owner, project, mishap)

    world.para()
    comfort_and_help(world, helper, child, helper_kind, finish, mishap)
    reveal(world, child, owner, project, finish)

    world.facts.update(
        mess_happened=item.meters["mended"] >= THRESHOLD,
        deduction_happened=helper.memes["deduction"] >= THRESHOLD,
        lesson_learned=child.memes["relief"] >= THRESHOLD and child.memes["honesty"] >= THRESHOLD,
    )
    return world


PROJECTS = {
    "rabbit": Project(
        id="rabbit",
        item_label="velveteen rabbit",
        item_phrase="a velveteen rabbit with one tired ear",
        owner_role="younger_sibling",
        worn_tired="one ear drooping and a seam coming loose at the paw",
        repair="stitch the ear and paw neatly again",
        fix_materials={"needle", "thread", "patch"},
        mark_words={"thread": "thread", "paint": "paint", "stuffing": "stuffing"},
        reveal_line='"I fixed your velveteen rabbit," {child} said.',
        tags={"velveteen", "rabbit", "sewing"},
    ),
    "bear": Project(
        id="bear",
        item_label="velveteen bear",
        item_phrase="a velveteen bear with a worn little coat",
        owner_role="cousin",
        worn_tired="a coat button missing and a tear along one sleeve",
        repair="sew the sleeve and add a bright heart button",
        fix_materials={"needle", "thread", "button"},
        mark_words={"thread": "thread", "paint": "paint", "stuffing": "stuffing"},
        reveal_line='"Your velveteen bear is ready for another hundred hugs," {child} said.',
        tags={"velveteen", "bear", "sewing"},
    ),
    "pillow": Project(
        id="pillow",
        item_label="velveteen star pillow",
        item_phrase="a velveteen star pillow that had gone flat at one point",
        owner_role="grandparent",
        worn_tired="a corner split open and the star looking a little sleepy",
        repair="close the seam and make the star plump again",
        fix_materials={"needle", "thread", "stuffing"},
        mark_words={"thread": "thread", "paint": "paint", "stuffing": "stuffing"},
        reveal_line='"I wanted your reading chair to have this cozy star again," {child} said.',
        tags={"velveteen", "pillow", "sewing"},
    ),
}

MISHAPS = {
    "thread": Mishap(
        id="thread",
        clue="a bright thread curling across the floorboards",
        trail="a bright thread trail",
        spot="the little table",
        residue="a loose tail of red thread near the cushion",
        cause="the thread tangled into a tiny knot and the stitches pulled sideways",
        requires={"needle", "thread"},
        clean_fix="They snipped the knot, threaded the needle again, and made calm even stitches",
        qa_fix="They took out the tangled stitches and sewed again slowly",
        tags={"thread", "sewing", "deduction"},
    ),
    "button": Mishap(
        id="button",
        clue="a runaway button resting by the teacup",
        trail="a runaway button on the rug",
        spot="the rug",
        residue="one shiny button glinting where it had rolled",
        cause="a button popped free and rolled under the chair",
        requires={"needle", "thread", "button"},
        clean_fix="They found the button, looped strong thread through it, and fastened it tight",
        qa_fix="They found the button and sewed it back on tightly",
        tags={"button", "sewing", "deduction"},
    ),
    "stuffing": Mishap(
        id="stuffing",
        clue="a little cloud of stuffing peeking from under the cushion",
        trail="a little cloud of stuffing",
        spot="the floor",
        residue="soft fluff clinging to the hem of the blanket",
        cause="the seam opened wider and soft stuffing puffed out",
        requires={"needle", "thread", "stuffing"},
        clean_fix="They tucked the fluff back inside, added a little fresh stuffing, and closed the seam carefully",
        qa_fix="They tucked the stuffing back in and stitched the seam closed",
        tags={"stuffing", "sewing", "deduction"},
    ),
}

HELPERS = {
    "sibling": HelperKind(
        id="sibling",
        role_label="older sibling",
        actor_type="boy",
        relation_line="As the older sibling in the house, he knew the sounds of secret plans.",
        comfort_style="gave a small sideways hug",
        tags={"family", "sibling"},
    ),
    "grandma": HelperKind(
        id="grandma",
        role_label="grandma",
        actor_type="grandmother",
        relation_line="Grandma had a way of noticing little things before anyone else did.",
        comfort_style="rubbed gentle circles on the child's back",
        tags={"family", "grandparent"},
    ),
    "grandpa": HelperKind(
        id="grandpa",
        role_label="grandpa",
        actor_type="grandfather",
        relation_line="Grandpa always noticed clues the way bird-watchers notice feathers.",
        comfort_style="patted the child's shoulder with a warm hand",
        tags={"family", "grandparent"},
    ),
}

FINISHES = {
    "heart_patch": Finish(
        id="heart_patch",
        label="heart patch kit",
        phrase="a small tin of thread, a needle, and a soft heart-shaped patch",
        materials={"needle", "thread", "patch"},
        effect="the mended place looked sturdy and kind",
        closing_image="rested in its owner's arms with the little heart patch shining like a secret thank-you",
        tags={"patch", "sewing", "gift"},
    ),
    "button_tin": Finish(
        id="button_tin",
        label="button tin",
        phrase="a round tin of buttons, thread, and a tiny silver needle",
        materials={"needle", "thread", "button"},
        effect="the repaired place looked neat and cheerful",
        closing_image="sat on the bed with its bright button catching the lamplight",
        tags={"button", "sewing", "gift"},
    ),
    "mending_basket": Finish(
        id="mending_basket",
        label="mending basket",
        phrase="a wicker mending basket with thread, needles, and soft clean stuffing",
        materials={"needle", "thread", "stuffing"},
        effect="the repaired seam looked smooth and full again",
        closing_image="propped in the reading chair, plump and cozy as an evening star",
        tags={"stuffing", "sewing", "gift"},
    ),
    "full_basket": Finish(
        id="full_basket",
        label="full basket",
        phrase="a full mending basket with thread, buttons, patches, needles, and soft stuffing",
        materials={"needle", "thread", "button", "patch", "stuffing"},
        effect="the little repair looked careful, strong, and ready for many more hugs",
        closing_image="looked almost new, though even dearer because everyone knew how much love had gone into it",
        tags={"sewing", "gift"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Ella", "Lucy", "Anna", "Rose", "Maya", "Zoe"]
BOY_NAMES = ["Eli", "Ben", "Leo", "Max", "Sam", "Theo", "Finn", "Noah", "Jack", "Owen"]


@dataclass
class StoryParams:
    project: str
    mishap: str
    helper: str
    finish: str
    child_name: str
    child_gender: str
    helper_name: str
    owner_name: str
    owner_gender: str
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
    "velveteen": [
        (
            "What does velveteen feel like?",
            "Velveteen feels soft and a little fuzzy, almost like velvet. That soft cloth is why old toys made from it can feel extra cozy."
        )
    ],
    "sewing": [
        (
            "What is sewing?",
            "Sewing is joining cloth with thread and a needle. When people sew carefully, they can mend tears or make something strong again."
        )
    ],
    "thread": [
        (
            "What is thread used for?",
            "Thread is a thin string used for sewing fabric together. It helps hold seams, patches, and buttons in place."
        )
    ],
    "button": [
        (
            "Why do buttons need strong thread?",
            "Buttons get tugged when people hold or hug a toy or coat. Strong thread helps keep them from popping off."
        )
    ],
    "stuffing": [
        (
            "What is stuffing inside a pillow or toy?",
            "Stuffing is the soft filling inside some toys and pillows. It helps them feel puffy and comfortable."
        )
    ],
    "deduction": [
        (
            "What is a deduction?",
            "A deduction is a careful guess you make from clues. You notice small signs and use them to figure out what probably happened."
        )
    ],
    "surprise": [
        (
            "How can you keep a kind surprise without hiding a problem?",
            "You can keep the gift secret but still ask a trusted grown-up or helper for help. Telling the truth about the problem protects the surprise and fixes the trouble."
        )
    ],
    "patience": [
        (
            "Why is patience useful when you make something by hand?",
            "Patient hands make fewer mistakes because they move slowly and check each step. That is why many careful jobs turn out better when you do not rush."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "velveteen",
    "sewing",
    "thread",
    "button",
    "stuffing",
    "deduction",
    "surprise",
    "patience",
]


def generation_prompts(world: World) -> list[str]:
    project = world.facts["project"]
    mishap = world.facts["mishap"]
    helper = world.facts["helper_kind"]
    child = world.facts["child"]
    return [
        'Write a heartwarming story for a 3-to-5-year-old that includes the words "velveteen", "rush", and "deduction".',
        f"Tell a gentle story where {child.id} tries to mend a {project.item_label} as a surprise, makes a mistake in a rush, and a {helper.role_label} solves it with deduction.",
        f"Write a warm family story about a secret repair, a small clue like {mishap.clue}, and a lesson learned about slowing down.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    project = world.facts["project"]
    mishap = world.facts["mishap"]
    helper_kind = world.facts["helper_kind"]
    child = world.facts["child"]
    helper = world.facts["helper"]
    owner = world.facts["owner"]
    finish = world.facts["finish"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who wanted to mend {owner.id}'s {project.item_label} as a surprise, and {helper.id}, the {helper_kind.role_label} who helped. The story stays close to their loving little problem."
        ),
        (
            f"Why was {child.id} in a rush?",
            f"{child.id} wanted the surprise ready before anyone saw it. That hurry made careful sewing harder, so the trouble began when loving hands moved too fast."
        ),
        (
            f"What clue helped {helper.id} make a deduction?",
            f"{helper.id} noticed {mishap.clue}. Along with the open sewing things and {child.id}'s worried face, that clue pointed straight to the hidden surprise."
        ),
        (
            f"What was {helper.id}'s deduction?",
            f"{helper.id} figured out that {child.id} was secretly fixing {owner.id}'s {project.item_label}. The deduction came from small trace signs, not from being told at first."
        ),
        (
            f"How did they fix the problem?",
            f"They used {finish.phrase} and worked slowly together. {mishap.qa_fix}, which turned the rushed mistake into a careful repair."
        ),
        (
            "What lesson did the child learn?",
            f"{child.id} learned that a loving surprise should not be made in a rush. Slowing down and asking for help kept the gift kind and made the ending sweeter."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"velveteen", "sewing", "deduction", "surprise", "patience"}
    tags |= set(world.facts["project"].tags)
    tags |= set(world.facts["mishap"].tags)
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
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
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
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        project="rabbit",
        mishap="thread",
        helper="grandma",
        finish="full_basket",
        child_name="Nora",
        child_gender="girl",
        helper_name="Grandma June",
        owner_name="Mina",
        owner_gender="girl",
    ),
    StoryParams(
        project="bear",
        mishap="button",
        helper="sibling",
        finish="button_tin",
        child_name="Lily",
        child_gender="girl",
        helper_name="Ben",
        owner_name="Owen",
        owner_gender="boy",
    ),
    StoryParams(
        project="pillow",
        mishap="stuffing",
        helper="grandpa",
        finish="mending_basket",
        child_name="Ava",
        child_gender="girl",
        helper_name="Grandpa Ray",
        owner_name="Grandma Mae",
        owner_gender="grandmother",
    ),
    StoryParams(
        project="rabbit",
        mishap="button",
        helper="sibling",
        finish="full_basket",
        child_name="Mia",
        child_gender="girl",
        helper_name="Leo",
        owner_name="Zoe",
        owner_gender="girl",
    ),
]


ASP_RULES = r"""
repair_need(P,M) :- project(P), mishap(M), project_needs(P,R), mishap_needs(M,R).
repair_need(P,M) :- project(P), project_needs(P,R), not mishap_needs(M,R), mishap(M).
repair_need(P,M) :- mishap(M), mishap_needs(M,R), not project_needs(P,R), project(P).

can_fix(P,M,F) :- project(P), mishap(M), finish(F),
                  not missing_need(P,M,F).

missing_need(P,M,F) :- project(P), mishap(M), finish(F),
                       repair_need(P,M), need(P,M,R), not provides(F,R).

need(P,M,R) :- project_needs(P,R).
need(P,M,R) :- mishap_needs(M,R).

valid(P,M,H,F) :- project(P), mishap(M), helper(H), finish(F), can_fix(P,M,F).
#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for project_id, project in PROJECTS.items():
        lines.append(asp.fact("project", project_id))
        for material in sorted(project.fix_materials):
            lines.append(asp.fact("project_needs", project_id, material))
    for mishap_id, mishap in MISHAPS.items():
        lines.append(asp.fact("mishap", mishap_id))
        for material in sorted(mishap.requires):
            lines.append(asp.fact("mishap_needs", mishap_id, material))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
    for finish_id, finish in FINISHES.items():
        lines.append(asp.fact("finish", finish_id))
        for material in sorted(finish.materials):
            lines.append(asp.fact("provides", finish_id, material))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for idx, params in enumerate(CURATED, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            print(f"OK: curated story {idx} generated.")
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"CURATED STORY {idx} FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a heartwarming surprise repair, a rush, and a careful deduction."
    )
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--mishap", choices=MISHAPS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--finish", choices=FINISHES)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--owner-gender", choices=["girl", "boy", "grandmother", "grandfather"])
    ap.add_argument("--child-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--owner-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    if gender in {"girl", "grandmother"}:
        pool = [n for n in GIRL_NAMES if n not in avoid]
    elif gender in {"boy", "grandfather"}:
        pool = [n for n in BOY_NAMES if n not in avoid]
    else:
        pool = [n for n in GIRL_NAMES if n not in avoid]
    if not pool:
        pool = GIRL_NAMES + BOY_NAMES
    name = rng.choice(pool)
    if gender == "grandmother":
        return f"Grandma {name}"
    if gender == "grandfather":
        return f"Grandpa {name}"
    return name


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.project and args.mishap and args.finish:
        project = PROJECTS[args.project]
        mishap = MISHAPS[args.mishap]
        finish = FINISHES[args.finish]
        if not can_fix(project, mishap, finish):
            raise StoryError(explain_rejection(project, mishap, finish))

    combos = [
        combo for combo in valid_combos()
        if (args.project is None or combo[0] == args.project)
        and (args.mishap is None or combo[1] == args.mishap)
        and (args.helper is None or combo[2] == args.helper)
        and (args.finish is None or combo[3] == args.finish)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    project_id, mishap_id, helper_id, finish_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])

    project = PROJECTS[project_id]
    if project.owner_role == "grandparent":
        owner_gender = args.owner_gender or rng.choice(["grandmother", "grandfather"])
    else:
        owner_gender = args.owner_gender or rng.choice(["girl", "boy"])

    child_name = args.child_name or _pick_name(rng, child_gender, set())
    helper_kind = HELPERS[helper_id]
    helper_name = args.helper_name or (
        _pick_name(rng, helper_kind.actor_type, {child_name})
        if helper_kind.id == "sibling"
        else ("Grandma June" if helper_kind.id == "grandma" else "Grandpa Ray")
    )
    owner_name = args.owner_name or _pick_name(rng, owner_gender, {child_name, helper_name})

    return StoryParams(
        project=project_id,
        mishap=mishap_id,
        helper=helper_id,
        finish=finish_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        owner_name=owner_name,
        owner_gender=owner_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.mishap not in MISHAPS:
        raise StoryError(f"(Unknown mishap: {params.mishap})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.finish not in FINISHES:
        raise StoryError(f"(Unknown finish: {params.finish})")

    project = PROJECTS[params.project]
    mishap = MISHAPS[params.mishap]
    helper_kind = HELPERS[params.helper]
    finish = FINISHES[params.finish]

    if not can_fix(project, mishap, finish):
        raise StoryError(explain_rejection(project, mishap, finish))

    world = tell(
        project=project,
        mishap=mishap,
        helper_kind=helper_kind,
        finish=finish,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        owner_name=params.owner_name,
        owner_gender=params.owner_gender,
    )

    story = world.render()
    story = story.replace('{child}', world.get("child").id)

    return StorySample(
        params=params,
        story=story,
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
        print(f"{len(combos)} valid (project, mishap, helper, finish) combos:\n")
        for project, mishap, helper, finish in combos:
            print(f"  {project:8} {mishap:8} {helper:8} {finish}")
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
            header = f"### {p.project}: {p.mishap} with {p.helper} using {p.finish}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
