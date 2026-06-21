#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fabricate_malleable_dialogue_slice_of_life.py
========================================================================

A small storyworld about a child making something by hand at home. The object is
still malleable when a little accident bends or squashes it. For one moment the
child is tempted to fabricate an excuse, then the grown-up's calm response turns
the afternoon toward honesty and repair.

The domain is intentionally narrow and slice-of-life:
- a child and a caregiver at a table
- a handmade project from a soft material
- a small household accident
- a choice between telling the truth and trying to fabricate a story
- a gentle ending that proves what changed

The world model tracks both physical meters (damage, dryness, repaired) and
emotional memes (worry, relief, trust). Prose is rendered from simulated state,
not from swapping a few nouns into a frozen paragraph.
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

# Make the shared result containers importable when this script is run directly
# from a nested world directory: add storyworlds/ to sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "aunt"}
        male = {"boy", "father", "grandfather", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Material:
    id: str
    label: str
    phrase: str
    malleable: bool = True
    softness: int = 2
    color: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Project:
    id: str
    label: str
    phrase: str
    feature: str
    ending_place: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Accident:
    id: str
    text: str
    line: str
    damage: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    sense: int = 3
    max_damage: int = 1
    needs_malleable: bool = True
    text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    material: str
    project: str
    accident: str
    repair: str
    honesty: str
    child_name: str
    child_gender: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


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


def _r_damage_feelings(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    project = world.get("project")
    if project.meters["damaged"] < THRESHOLD:
        return out
    sig = ("damage_feelings",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    child.memes["attachment"] += 1
    out.append("__damage__")
    return out


def _r_honesty_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["confessed"] < THRESHOLD or helper.memes["calm"] < THRESHOLD:
        return out
    sig = ("honesty_relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["trust"] += 1
    helper.memes["trust"] += 1
    out.append("__relief__")
    return out


def _r_lie_delay(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    material = world.get("material")
    if child.memes["lied"] < THRESHOLD:
        return out
    sig = ("lie_delay",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    material.meters["drying"] += 1
    child.memes["shame"] += 1
    out.append("__delay__")
    return out


CAUSAL_RULES = [
    Rule(name="damage_feelings", tag="emotional", apply=_r_damage_feelings),
    Rule(name="honesty_relief", tag="emotional", apply=_r_honesty_relief),
    Rule(name="lie_delay", tag="physical", apply=_r_lie_delay),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


PLACES = {
    "kitchen": Place(
        id="kitchen",
        label="the kitchen table",
        detail="Sunlight made a warm square on the table, and a damp towel waited by the craft tray.",
        tags={"home", "kitchen"},
    ),
    "porch": Place(
        id="porch",
        label="the back porch table",
        detail="The screen door clicked softly, and the air smelled like afternoon grass.",
        tags={"home", "porch"},
    ),
    "desk": Place(
        id="desk",
        label="the little desk by the window",
        detail="The window was open a crack, and a thin breeze kept lifting the corner of a paper towel.",
        tags={"home", "window"},
    ),
}

MATERIALS = {
    "clay": Material(
        id="clay",
        label="clay",
        phrase="a lump of soft, malleable clay",
        malleable=True,
        softness=2,
        color="blue",
        tags={"clay", "malleable"},
    ),
    "dough": Material(
        id="dough",
        label="salt dough",
        phrase="a round of warm, malleable salt dough",
        malleable=True,
        softness=2,
        color="cream",
        tags={"dough", "malleable"},
    ),
    "cold_putty": Material(
        id="cold_putty",
        label="putty",
        phrase="a ball of cool putty that was only a little malleable",
        malleable=True,
        softness=1,
        color="green",
        tags={"putty", "malleable"},
    ),
    "baked_dough": Material(
        id="baked_dough",
        label="baked dough",
        phrase="a piece of baked dough that was no longer malleable",
        malleable=False,
        softness=0,
        color="tan",
        tags={"baked"},
    ),
}

PROJECTS = {
    "star": Project(
        id="star",
        label="star ornament",
        phrase="a little star ornament",
        feature="one point",
        ending_place="the windowsill",
        tags={"star"},
    ),
    "bowl": Project(
        id="bowl",
        label="pinch bowl",
        phrase="a tiny pinch bowl",
        feature="the rim",
        ending_place="the shelf above the sink",
        tags={"bowl"},
    ),
    "turtle": Project(
        id="turtle",
        label="turtle",
        phrase="a tiny turtle",
        feature="one front flipper",
        ending_place="the bookcase",
        tags={"turtle"},
    ),
}

ACCIDENTS = {
    "sleeve_drag": Accident(
        id="sleeve_drag",
        text="When the child reached for a ribbon, a sweater sleeve dragged across the project.",
        line="the sleeve had brushed it sideways",
        damage=1,
        tags={"sleeve"},
    ),
    "elbow_bump": Accident(
        id="elbow_bump",
        text="While turning to answer a question, the child bumped the tray with an elbow.",
        line="the elbow had nudged the tray",
        damage=1,
        tags={"elbow"},
    ),
    "tray_tilt": Accident(
        id="tray_tilt",
        text="On the way to show it off, the tray tipped and the project slumped against one edge.",
        line="the tray had tipped in those excited hands",
        damage=2,
        tags={"tray"},
    ),
}

REPAIRS = {
    "smooth": Repair(
        id="smooth",
        label="smooth it",
        sense=3,
        max_damage=1,
        needs_malleable=True,
        text="pressed the surface gently with damp fingertips until the bent part softened and settled back into place",
        qa_text="smoothed the bent part back into shape with damp fingertips",
        tags={"repair", "smooth"},
    ),
    "pinch_back": Repair(
        id="pinch_back",
        label="pinch it back",
        sense=3,
        max_damage=2,
        needs_malleable=True,
        text="pinched the soft edges back together and shaped the little form again, slow and careful",
        qa_text="pinched the soft edges back together and shaped it again",
        tags={"repair", "reshape"},
    ),
    "restart": Repair(
        id="restart",
        label="start again",
        sense=2,
        max_damage=3,
        needs_malleable=False,
        text="set the squashed piece aside and rolled a fresh piece to begin again, this time smaller and steadier",
        qa_text="started again with a fresh piece",
        tags={"repair", "restart"},
    ),
    "tape": Repair(
        id="tape",
        label="tape it",
        sense=1,
        max_damage=1,
        needs_malleable=False,
        text="tried to wrap tape around the soft shape",
        qa_text="tried to tape it",
        tags={"bad_fix"},
    ),
}

HONESTY_CHOICES = ["confess", "fabricate"]

GIRL_NAMES = ["Mia", "Lila", "Nora", "Zoe", "Ava", "Ella", "Ruby", "Tessa"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Eli", "Noah", "Owen", "Theo"]
TRAITS = ["careful", "chatty", "eager", "thoughtful", "busy", "bright"]


def sensible_repairs() -> list[Repair]:
    return [repair for repair in REPAIRS.values() if repair.sense >= SENSE_MIN]


def damage_after_choice(accident: Accident, honesty: str) -> int:
    return accident.damage + (1 if honesty == "fabricate" else 0)


def can_repair(repair: Repair, material: Material, severity: int) -> bool:
    if repair.sense < SENSE_MIN:
        return False
    if repair.needs_malleable and not material.malleable:
        return False
    if repair.needs_malleable and material.softness <= 0:
        return False
    return repair.max_damage >= severity


def combo_valid(material: Material, accident: Accident, repair: Repair) -> bool:
    if repair.sense < SENSE_MIN:
        return False
    if repair.needs_malleable and not material.malleable:
        return False
    if repair.needs_malleable and material.softness <= 0:
        return False
    return repair.max_damage >= accident.damage


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for material_id, material in MATERIALS.items():
            for project_id in PROJECTS:
                for accident_id, accident in ACCIDENTS.items():
                    for repair_id, repair in REPAIRS.items():
                        if combo_valid(material, accident, repair):
                            combos.append((place_id, material_id, project_id, accident_id, repair_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    material = MATERIALS[params.material]
    accident = ACCIDENTS[params.accident]
    repair = REPAIRS[params.repair]
    severity = damage_after_choice(accident, params.honesty)
    if can_repair(repair, material, severity):
        return "repaired" if params.honesty == "confess" else "repaired_after_lie"
    return "restarted_after_lie" if params.honesty == "fabricate" else "restarted"


def explain_rejection(material: Material, accident: Accident, repair: Repair) -> str:
    if repair.sense < SENSE_MIN:
        return (
            f"(No story: '{repair.id}' is not a sensible fix here. "
            f"Pick a repair like {', '.join(sorted(r.id for r in sensible_repairs()))}.)"
        )
    if repair.needs_malleable and not material.malleable:
        return (
            f"(No story: {material.label} is not malleable anymore, so '{repair.id}' "
            f"cannot honestly reshape it.)"
        )
    if repair.max_damage < accident.damage:
        return (
            f"(No story: '{repair.id}' is too weak for a {accident.id} accident. "
            f"Choose a stronger repair or a smaller accident.)"
        )
    return "(No story: this combination is not reasonable.)"


def helper_label_word(helper: Entity) -> str:
    return helper.label_word


def introduce(world: World, place: Place, child: Entity, helper: Entity,
              material: Material, project: Project) -> None:
    world.say(
        f"After school, {child.id} sat with {helper_label_word(helper)} at {place.label}. "
        f"{place.detail}"
    )
    world.say(
        f"In the middle of the tray lay {material.phrase}. "
        f'"Can I fabricate {project.phrase}?" {child.id} asked.'
    )
    world.say(
        f'"Of course," said {helper_label_word(helper)}. "That is what soft hands and a slow afternoon are for."'
    )


def shape_project(world: World, child: Entity, material: Material, project: Project) -> None:
    child.memes["focus"] += 1
    world.say(
        f"{child.id} rolled and pressed the {material.label} until it looked almost right. "
        f"Soon {project.phrase} was taking shape."
    )


def accident_happens(world: World, child: Entity, project_ent: Entity, material_ent: Entity,
                     accident: Accident, project: Project) -> None:
    project_ent.meters["damaged"] += accident.damage
    material_ent.meters["soft"] = 1.0 if MATERIALS[world.facts['material'].id].malleable else 0.0
    propagate(world, narrate=False)
    world.say(accident.text)
    if accident.damage == 1:
        world.say(
            f"When they both looked down, {project.feature} was bent, and {child.id}'s smile went small."
        )
    else:
        world.say(
            f"When they both looked down, {project.phrase} had slumped to one side, and {child.id} went very still."
        )


def confess(world: World, child: Entity, helper: Entity, accident: Accident) -> None:
    child.memes["confessed"] += 1
    helper.memes["calm"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I did that," {child.id} said quietly. "I was hurrying, and {accident.line}."'
    )
    world.say(
        f'"Thank you for telling me the true part first," said {helper_label_word(helper)}. '
        f'"That helps us know what to do next."'
    )


def fabricate_then_admit(world: World, child: Entity, helper: Entity) -> None:
    child.memes["lied"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{child.id} looked at the dent and then at the window. '
        f'"Maybe... maybe the breeze did it," {child.pronoun()} said.'
    )
    world.say(
        f'{helper_label_word(helper).capitalize()} saw a little streak of clay on {child.pronoun("possessive")} sleeve and did not scold. '
        f'"Was it the breeze," {helper.pronoun()} asked gently, "or are you trying to fabricate a story because you feel bad?"'
    )
    child.memes["confessed"] += 1
    helper.memes["calm"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{child.id} swallowed. "I feel bad," {child.pronoun()} admitted. '
        f'"It was me."'
    )


def repair_story(world: World, child: Entity, helper: Entity, project_ent: Entity,
                 material_ent: Entity, repair: Repair, project: Project, outcome: str) -> None:
    severity = damage_after_choice(world.facts["accident"], world.facts["honesty"])
    project_ent.meters["severity"] = float(severity)
    if outcome in {"repaired", "repaired_after_lie"}:
        project_ent.meters["repaired"] += 1
        project_ent.meters["damaged"] = 0.0
        child.memes["hope"] += 1
        child.memes["relief"] += 1
        world.say(
            f'Together they {repair.text}. "{project.phrase.capitalize()} can still be itself," '
            f'said {helper_label_word(helper)}.'
        )
    else:
        project_ent.meters["restarted"] += 1
        child.memes["disappointed"] += 1
        child.memes["hope"] += 1
        world.say(
            f'The soft shape had sagged too much to save neatly. '
            f'So they {repair.text}.'
        )
        world.say(
            f'"We lost the first try," said {helper_label_word(helper)}, "but not the whole afternoon."'
        )
    if outcome == "repaired_after_lie":
        world.say(
            f'{child.id} nodded and touched the tray. "Next time I will tell the true part right away," {child.pronoun()} said.'
        )
    elif outcome == "repaired":
        world.say(
            f'{child.id} let out a long breath. "I thought it was ruined," {child.pronoun()} said.'
        )
    elif outcome == "restarted_after_lie":
        world.say(
            f'{child.id} looked sorry, then steadier. "The lie made it take longer," {child.pronoun()} said. '
            f'"I do not want that again."'
        )
    else:
        world.say(
            f'"A fresh start is still a start," {child.id} said, trying the words until they sounded true.'
        )
    material_ent.meters["used"] += 1


def ending(world: World, child: Entity, helper: Entity, project: Project, outcome: str) -> None:
    child.memes["joy"] += 1
    helper.memes["love"] += 1
    if outcome in {"repaired", "repaired_after_lie"}:
        world.say(
            f"By the end of the afternoon, {project.phrase} was resting on {project.ending_place}. "
            f"Its shape was not perfect, but it looked cared for."
        )
    else:
        world.say(
            f"By the end of the afternoon, a new version of {project.phrase} was resting on {project.ending_place}. "
            f"It was a little smaller than the first try, and somehow calmer too."
        )
    world.say(
        f'{helper_label_word(helper).capitalize()} set two cups of milk on the table. '
        f'"What did we make today?" {helper.pronoun()} asked.'
    )
    if outcome == "repaired":
        answer = "A star, and a brave true sentence"
    elif outcome == "repaired_after_lie":
        answer = "A star, and then a truer ending"
    elif outcome == "restarted_after_lie":
        answer = "A second try, and a better choice"
    else:
        answer = "A fresh start"
    if world.facts["project"].id != "star":
        answer = {
            "repaired": f"{project.label}, and a brave true sentence",
            "repaired_after_lie": f"{project.label}, and then a truer ending",
            "restarted_after_lie": "A second try, and a better choice",
            "restarted": "A fresh start",
        }[outcome]
    world.say(f'"{answer}," said {child.id}. And this time the answer came out easily.')


def tell(place: Place, material: Material, project: Project, accident: Accident,
         repair: Repair, honesty: str, child_name: str, child_gender: str,
         helper_type: str, trait: str) -> World:
    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        phrase=child_name,
        role="child",
        traits=[trait],
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label=helper_type,
        phrase=helper_type,
        role="helper",
    ))
    material_ent = world.add(Entity(
        id="material",
        type="material",
        label=material.label,
        phrase=material.phrase,
        tags=set(material.tags),
    ))
    project_ent = world.add(Entity(
        id="project",
        type="project",
        label=project.label,
        phrase=project.phrase,
        tags=set(project.tags),
    ))

    world.facts.update(
        place=place,
        material=material,
        project=project,
        accident=accident,
        repair=repair,
        honesty=honesty,
        outcome="",
    )

    introduce(world, place, child, helper, material, project)
    shape_project(world, child, material, project)

    world.para()
    accident_happens(world, child, project_ent, material_ent, accident, project)

    world.para()
    if honesty == "confess":
        confess(world, child, helper, accident)
    else:
        fabricate_then_admit(world, child, helper)

    world.para()
    outcome = outcome_of(StoryParams(
        place=place.id,
        material=material.id,
        project=project.id,
        accident=accident.id,
        repair=repair.id,
        honesty=honesty,
        child_name=child_name,
        child_gender=child_gender,
        helper_type=helper_type,
        trait=trait,
    ))
    world.facts["outcome"] = outcome
    repair_story(world, child, helper, project_ent, material_ent, repair, project, outcome)

    world.para()
    ending(world, child, helper, project, outcome)

    world.facts.update(
        child=child,
        helper=helper,
        material_ent=material_ent,
        project_ent=project_ent,
        confessed=child.memes["confessed"] >= THRESHOLD,
        lied=child.memes["lied"] >= THRESHOLD,
        repaired=project_ent.meters["repaired"] >= THRESHOLD,
        restarted=project_ent.meters["restarted"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    material = world.facts["material"]
    project = world.facts["project"]
    accident = world.facts["accident"]
    outcome = world.facts["outcome"]
    child = world.facts["child"]
    helper = world.facts["helper"]
    if outcome == "repaired":
        ending_note = "The child tells the truth right away, and they repair it together."
    elif outcome == "repaired_after_lie":
        ending_note = "The child first tries to fabricate an excuse, then admits the truth and helps repair it."
    else:
        ending_note = "The child first tries to fabricate an excuse, and the delay means they need a fresh start."
    return [
        (
            f'Write a slice-of-life story for a young child that uses dialogue and includes the words '
            f'"fabricate" and "malleable". The story should happen at home during a craft afternoon.'
        ),
        (
            f"Tell a gentle story where {child.label} is shaping {project.phrase} from {material.phrase}, "
            f"then {accident.id.replace('_', ' ')} bends it. {ending_note}"
        ),
        (
            f'Write a domestic story with spoken lines, a small accident, and a calm grown-up. '
            f'The child is tempted to fabricate a story because the material is still malleable and the project matters.'
        ),
    ]


KNOWLEDGE = {
    "malleable": [
        (
            "What does malleable mean?",
            "Malleable means soft enough to press, bend, or shape with your hands. Clay and dough can be malleable when they are fresh.",
        )
    ],
    "fabricate": [
        (
            "What can fabricate mean?",
            "Fabricate can mean make something with your hands, like a craft. It can also mean making up a false story, which is why people should use it carefully.",
        )
    ],
    "clay": [
        (
            "Why can clay be fixed while it is still soft?",
            "Soft clay can be pressed and shaped again before it dries. That is why a small dent can often be smoothed out.",
        )
    ],
    "dough": [
        (
            "Why does dough change shape so easily?",
            "Dough is soft and stretchy, so your fingers can press it into new shapes. That also means it can be bent by accident.",
        )
    ],
    "repair": [
        (
            "Why is telling the truth helpful when something breaks?",
            "Telling the truth helps grown-ups understand what really happened, so they can choose the best way to help. It also keeps trust strong.",
        )
    ],
    "restart": [
        (
            "Is starting again the same as failing?",
            "No. Starting again means using what you learned from the first try to make a better second try.",
        )
    ],
    "honesty": [
        (
            "Why can a lie make a problem bigger?",
            "A lie can waste time and hide the real problem. When people tell the truth sooner, they can fix things sooner too.",
        )
    ],
}
KNOWLEDGE_ORDER = ["malleable", "fabricate", "clay", "dough", "repair", "restart", "honesty"]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    material = world.facts["material"]
    project = world.facts["project"]
    accident = world.facts["accident"]
    repair = world.facts["repair"]
    outcome = world.facts["outcome"]
    helper_word = helper_label_word(helper)

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label} and {helper_word} during a quiet craft afternoon at home. "
            f"They are working together on {project.phrase}.",
        ),
        (
            f"What was {child.label} making?",
            f"{child.label} was shaping {project.phrase} from {material.phrase}. "
            f"The material mattered because it was soft enough to change shape.",
        ),
        (
            "What went wrong?",
            f"A small accident happened: {accident.text.lower()} "
            f"That bent or slumped the project and made {child.label} worry right away.",
        ),
    ]

    if outcome == "repaired":
        qa.append(
            (
                f"How was the problem solved?",
                f"{child.label} told the truth as soon as the accident happened, and {helper_word} stayed calm. "
                f"Because the material was still malleable enough, they {repair.qa_text} and kept the same project.",
            )
        )
    elif outcome == "repaired_after_lie":
        qa.append(
            (
                f"Did {child.label} tell the truth right away?",
                f"No. {child.label} first tried to fabricate an excuse, but {helper_word} gently asked again and {child.pronoun()} admitted the truth. "
                f"They could still repair the project because the material had not stiffened too much yet.",
            )
        )
        qa.append(
            (
                "What changed after the child admitted the truth?",
                f"The grown-up could help with the real problem instead of the made-up one. "
                f"That let them {repair.qa_text}, and it also made the room feel easier again.",
            )
        )
    elif outcome == "restarted_after_lie":
        qa.append(
            (
                "Why did they have to start again?",
                f"{child.label} first tried to fabricate a story instead of telling the truth, and that cost them time. "
                f"By the time the truth came out, the project had sagged too much for {repair.label}, so they made a fresh start instead.",
            )
        )
    else:
        qa.append(
            (
                "Why did they start again instead of saving the first project?",
                f"The damage was too big for the chosen repair, even though {child.label} was honest. "
                f"So they used the afternoon differently and made a smaller second try.",
            )
        )

    qa.append(
        (
            "How did the story end?",
            f"It ended with {project.phrase} resting on {project.ending_place} and a calm question at the table. "
            f"The last image shows that the afternoon became gentle again, not spoiled.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"malleable", "fabricate", "repair", "honesty"}
    material = world.facts["material"]
    outcome = world.facts["outcome"]
    if material.id == "clay":
        tags.add("clay")
    if material.id == "dough":
        tags.add("dough")
    if "restart" in outcome:
        tags.add("restart")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="kitchen",
        material="clay",
        project="star",
        accident="sleeve_drag",
        repair="smooth",
        honesty="confess",
        child_name="Mia",
        child_gender="girl",
        helper_type="mother",
        trait="careful",
    ),
    StoryParams(
        place="porch",
        material="dough",
        project="bowl",
        accident="elbow_bump",
        repair="pinch_back",
        honesty="fabricate",
        child_name="Ben",
        child_gender="boy",
        helper_type="grandmother",
        trait="chatty",
    ),
    StoryParams(
        place="desk",
        material="cold_putty",
        project="turtle",
        accident="tray_tilt",
        repair="pinch_back",
        honesty="fabricate",
        child_name="Nora",
        child_gender="girl",
        helper_type="father",
        trait="eager",
    ),
    StoryParams(
        place="kitchen",
        material="dough",
        project="star",
        accident="tray_tilt",
        repair="restart",
        honesty="confess",
        child_name="Leo",
        child_gender="boy",
        helper_type="grandfather",
        trait="thoughtful",
    ),
]


ASP_RULES = r"""
% --- base reasonableness gate ----------------------------------------------
valid(P, M, Pr, A, R) :- place(P), material(M), project(Pr), accident(A), repair(R),
                         sensible(R), base_repairable(M, A, R).

base_repairable(M, A, R) :- not needs_malleable(R), damage(A, D), max_damage(R, X), X >= D.
base_repairable(M, A, R) :- needs_malleable(R), malleable(M), softness(M, S), S > 0,
                            damage(A, D), max_damage(R, X), X >= D.

sensible(R) :- repair(R), sense(R, S), sense_min(Min), S >= Min.

% --- outcome model ----------------------------------------------------------
lie_delay(1) :- honesty(fabricate).
lie_delay(0) :- honesty(confess).
severity(V) :- chosen_accident(A), damage(A, D), lie_delay(L), V = D + L.

can_fix_now :- chosen_repair(R), chosen_material(M), severity(V),
               not needs_malleable(R), max_damage(R, X), X >= V.
can_fix_now :- chosen_repair(R), chosen_material(M), severity(V),
               needs_malleable(R), malleable(M), softness(M, S), S > 0, max_damage(R, X), X >= V.

outcome(repaired) :- honesty(confess), can_fix_now.
outcome(repaired_after_lie) :- honesty(fabricate), can_fix_now.
outcome(restarted) :- honesty(confess), not can_fix_now.
outcome(restarted_after_lie) :- honesty(fabricate), not can_fix_now.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for material_id, material in MATERIALS.items():
        lines.append(asp.fact("material", material_id))
        lines.append(asp.fact("softness", material_id, material.softness))
        if material.malleable:
            lines.append(asp.fact("malleable", material_id))
    for project_id in PROJECTS:
        lines.append(asp.fact("project", project_id))
    for accident_id, accident in ACCIDENTS.items():
        lines.append(asp.fact("accident", accident_id))
        lines.append(asp.fact("damage", accident_id, accident.damage))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("sense", repair_id, repair.sense))
        lines.append(asp.fact("max_damage", repair_id, repair.max_damage))
        if repair.needs_malleable:
            lines.append(asp.fact("needs_malleable", repair_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_material", params.material),
        asp.fact("chosen_accident", params.accident),
        asp.fact("chosen_repair", params.repair),
        asp.fact("honesty", params.honesty),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a bent craft, honesty, and repair."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--accident", choices=ACCIDENTS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--honesty", choices=HONESTY_CHOICES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        raise StoryError(explain_rejection(MATERIALS.get(args.material or "clay", MATERIALS["clay"]),
                                           ACCIDENTS.get(args.accident or "sleeve_drag", ACCIDENTS["sleeve_drag"]),
                                           REPAIRS[args.repair]))

    if args.material and args.accident and args.repair:
        material = MATERIALS[args.material]
        accident = ACCIDENTS[args.accident]
        repair = REPAIRS[args.repair]
        if not combo_valid(material, accident, repair):
            raise StoryError(explain_rejection(material, accident, repair))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.material is None or combo[1] == args.material)
        and (args.project is None or combo[2] == args.project)
        and (args.accident is None or combo[3] == args.accident)
        and (args.repair is None or combo[4] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, material_id, project_id, accident_id, repair_id = rng.choice(sorted(combos))
    honesty = args.honesty or rng.choice(HONESTY_CHOICES)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    if args.child_name:
        child_name = args.child_name
    else:
        child_name = rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_type = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        place=place_id,
        material=material_id,
        project=project_id,
        accident=accident_id,
        repair=repair_id,
        honesty=honesty,
        child_name=child_name,
        child_gender=child_gender,
        helper_type=helper_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        material = MATERIALS[params.material]
        project = PROJECTS[params.project]
        accident = ACCIDENTS[params.accident]
        repair = REPAIRS[params.repair]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter value: {exc.args[0]})") from exc

    if not combo_valid(material, accident, repair):
        raise StoryError(explain_rejection(material, accident, repair))
    if params.honesty not in HONESTY_CHOICES:
        raise StoryError(f"(Invalid honesty choice: {params.honesty})")

    world = tell(
        place=place,
        material=material,
        project=project,
        accident=accident,
        repair=repair,
        honesty=params.honesty,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper_type,
        trait=params.trait,
    )

    # Replace display label after generation so story text can use the chosen name.
    world.get("child").label = params.child_name
    return StorySample(
        params=params,
        story=world.render().replace("child", params.child_name, 0) if False else world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story.replace("child", sample.params.child_name) if False else sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
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
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    # Smoke test: normal generation should not crash.
    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        print("OK: smoke generation succeeded.")
    except Exception as exc:  # pragma: no cover - defensive for CLI verify
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, material, project, accident, repair) combos:\n")
        for combo in combos:
            place_id, material_id, project_id, accident_id, repair_id = combo
            print(f"  {place_id:8} {material_id:11} {project_id:8} {accident_id:12} {repair_id}")
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
            header = (
                f"### {p.child_name}: {p.material} / {p.project} / {p.accident} / "
                f"{p.repair} / {p.honesty} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
