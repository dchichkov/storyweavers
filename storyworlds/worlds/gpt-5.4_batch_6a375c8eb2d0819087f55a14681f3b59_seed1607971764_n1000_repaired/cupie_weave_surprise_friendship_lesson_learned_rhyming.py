#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cupie_weave_surprise_friendship_lesson_learned_rhyming.py
====================================================================================

A standalone storyworld for a tiny rhyming craft tale: children plan a woven
surprise for a friend, something goes wrong in the secret or in the weave, and
the ending proves a friendship lesson learned.

The world is built around three ingredients:

* a gift that can truly be woven from the chosen material,
* a social choice about how secretive the surprise feels,
* a physical choice about whether the children weave slowly or too fast.

The surprise is meant to be kind, not chilly; the weave is meant to be careful,
not willy-nilly. In every generated story, at least one strain appears:
someone's feelings get pinched by too much hush, or the weaving snags because
the children rush. By the end, they mend the gift, mend the feeling, or both.

Run it
------
    python storyworlds/worlds/gpt-5.4/cupie_weave_surprise_friendship_lesson_learned_rhyming.py
    python storyworlds/worlds/gpt-5.4/cupie_weave_surprise_friendship_lesson_learned_rhyming.py --project basket --material ribbon
    python storyworlds/worlds/gpt-5.4/cupie_weave_surprise_friendship_lesson_learned_rhyming.py --pace quick --secrecy hush --qa
    python storyworlds/worlds/gpt-5.4/cupie_weave_surprise_friendship_lesson_learned_rhyming.py --repair glue_blob
    python storyworlds/worlds/gpt-5.4/cupie_weave_surprise_friendship_lesson_learned_rhyming.py --all
    python storyworlds/worlds/gpt-5.4/cupie_weave_surprise_friendship_lesson_learned_rhyming.py --verify
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
SHY_TRAITS = {"shy", "quiet"}
NEARBY_SECRECY = {"hush"}
PACE_ORDER = {"slow": 0, "quick": 1}


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Place:
    id: str
    label: str
    scene: str
    detail: str
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
    rows: int
    need_flex: int
    need_strength: int
    reveal_line: str
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
class Material:
    id: str
    label: str
    phrase: str
    flex: int
    strength: int
    texture: str
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
class Repair:
    id: str
    label: str
    sense: int
    power: int
    materials: set[str]
    success_text: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "purpose_shared": False,
            "recipient_near": False,
            "secrecy": "",
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


def _r_secret_sting(world: World) -> list[str]:
    if world.facts.get("secrecy") not in NEARBY_SECRECY:
        return []
    if not world.facts.get("recipient_near"):
        return []
    if world.facts.get("purpose_shared"):
        return []
    recipient = world.get("recipient")
    sig = ("secret_sting", recipient.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    recipient.memes["left_out"] += 1
    recipient.memes["worry"] += 1
    return ["__left_out__"]


def _r_snag_worry(world: World) -> list[str]:
    gift = world.get("gift")
    if gift.meters["torn"] < THRESHOLD and gift.meters["tangle"] < THRESHOLD:
        return []
    sig = ("snag_worry", gift.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("lead").memes["worry"] += 1
    world.get("helper").memes["worry"] += 1
    return ["__snag__"]


def _r_ready_glow(world: World) -> list[str]:
    gift = world.get("gift")
    rows = int(gift.attrs.get("rows", 0))
    if gift.meters["progress"] < rows:
        return []
    sig = ("ready_glow", gift.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    gift.meters["ready"] += 1
    world.get("lead").memes["pride"] += 1
    world.get("helper").memes["pride"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="secret_sting", tag="social", apply=_r_secret_sting),
    Rule(name="snag_worry", tag="social", apply=_r_snag_worry),
    Rule(name="ready_glow", tag="physical", apply=_r_ready_glow),
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


def weaveable(project: Project, material: Material) -> bool:
    return material.flex >= project.need_flex and material.strength >= project.need_strength


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def repair_works(repair: Repair, material: Material) -> bool:
    return material.id in repair.materials and repair.power >= 1


def pace_causes_snag(project: Project, material: Material, pace: str) -> bool:
    return pace == "quick" and material.strength < project.need_strength + 1


def secrecy_hurts(secrecy: str, recipient_trait: str) -> bool:
    return secrecy == "hush" and recipient_trait in SHY_TRAITS


def has_turn(pace: str, secrecy: str, project: Project, material: Material,
             recipient_trait: str) -> bool:
    return pace_causes_snag(project, material, pace) or secrecy_hurts(secrecy, recipient_trait)


def outcome_of(params: "StoryParams") -> str:
    project = PROJECTS[params.project]
    material = MATERIALS[params.material]
    snag = pace_causes_snag(project, material, params.pace)
    sting = secrecy_hurts(params.secrecy, params.recipient_trait)
    if snag and sting:
        return "mended_and_shared"
    if snag:
        return "mended"
    return "shared"


def predict(world: World, project: Project, material: Material, pace: str,
            secrecy: str, recipient_trait: str) -> dict:
    sim = world.copy()
    sim.facts["secrecy"] = secrecy
    sim.facts["recipient_near"] = secrecy in NEARBY_SECRECY
    sim.facts["purpose_shared"] = False
    if pace_causes_snag(project, material, pace):
        gift = sim.get("gift")
        gift.meters["tangle"] += 1
        gift.meters["torn"] += 1
    propagate(sim, narrate=False)
    return {
        "snag": sim.get("gift").meters["torn"] >= THRESHOLD,
        "left_out": sim.get("recipient").memes["left_out"] >= THRESHOLD
        or secrecy_hurts(secrecy, recipient_trait),
    }


def introduce(world: World, lead: Entity, helper: Entity, recipient: Entity, place: Place) -> None:
    for kid in (lead, helper, recipient):
        kid.memes["friendship"] += 1
    world.say(
        f"In {place.scene}, where {place.detail}, "
        f"{lead.id}, {helper.id}, and {recipient.id} liked to laugh and play."
    )
    world.say(
        f"They were the sort of friends who could turn a quiet minute into a bright little day."
    )


def wish_surprise(world: World, lead: Entity, helper: Entity, recipient: Entity,
                  project: Project, material: Material) -> None:
    lead.memes["excitement"] += 1
    helper.memes["excitement"] += 1
    world.say(
        f'That morning, {lead.id} whispered, "Let us weave {project.phrase} for {recipient.id} today."'
    )
    world.say(
        f'{helper.id} nodded at the {material.phrase}. "And on the top we can tie a tiny cupie charm, so small and sweet and bright."'
    )


def start_weave(world: World, lead: Entity, helper: Entity, project: Project,
                material: Material, pace: str) -> None:
    gift = world.get("gift")
    gift.meters["progress"] = float(max(1, project.rows - 1))
    lead.memes["focus"] += 1
    helper.memes["focus"] += 1
    speed = "quick and slick" if pace == "quick" else "slow and low"
    world.say(
        f"So snip went the strips, and slip went the hands, as they began to weave in a {speed} little flow."
    )
    world.say(
        f"The {material.label} crossed over and under, over and under, with a soft {material.texture} glow."
    )
    propagate(world, narrate=False)


def recipient_nears(world: World, recipient: Entity, secrecy: str) -> None:
    world.facts["secrecy"] = secrecy
    world.facts["recipient_near"] = True
    if secrecy == "hush":
        world.say(
            f"But soon {recipient.id} came near, and the whispers grew hush-hush, low as a mouse in a house."
        )
    else:
        world.say(
            f"Just then {recipient.id} skipped near, and the makers hid their smiles behind their hands with a playful little bounce."
        )
    propagate(world, narrate=False)


def snag(world: World, lead: Entity, helper: Entity, project: Project, material: Material) -> None:
    gift = world.get("gift")
    gift.meters["tangle"] += 1
    gift.meters["torn"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then tug met rush, and rush met trouble: the {material.label} gave a tiny rip in the middle of the {project.label}."
    )
    world.say(
        f'"Oh dear," said {lead.id}, and {helper.id} drew close, because a too-fast weave can wobble and wiggle.'
    )


def stung_feeling(world: World, recipient: Entity) -> None:
    if recipient.memes["left_out"] < THRESHOLD:
        return
    world.say(
        f'{recipient.id} slowed to a stop. "Are you keeping me out?" {recipient.pronoun()} asked in a voice small as a sprout.'
    )


def explain_surprise(world: World, lead: Entity, helper: Entity, recipient: Entity,
                     project: Project) -> None:
    world.facts["purpose_shared"] = True
    recipient.memes["left_out"] = 0.0
    recipient.memes["worry"] = 0.0
    recipient.memes["trust"] += 1
    lead.memes["care"] += 1
    helper.memes["care"] += 1
    world.say(
        f'{lead.id} set the half-made gift down at once. "No, not out," {lead.pronoun()} said. "We hoped to surprise you with {project.phrase}."'
    )
    world.say(
        f'"But a surprise should feel warm, not cold," said {helper.id}. "Come closer, and we will make the last part together."'
    )


def mend(world: World, recipient: Entity, repair: Repair, material: Material) -> None:
    gift = world.get("gift")
    gift.meters["torn"] = 0.0
    gift.meters["tangle"] = 0.0
    gift.meters["mended"] += 1
    recipient.memes["helpful"] += 1
    world.say(
        f"{recipient.id} knelt beside them, and together they {repair.success_text.format(material=material.label)}."
    )
    world.say(
        "Little by little, the broken bit grew neat again, and the worried faces softened into grins."
    )


def finish_together(world: World, lead: Entity, helper: Entity, recipient: Entity,
                    project: Project) -> None:
    gift = world.get("gift")
    gift.meters["progress"] = float(project.rows)
    recipient.memes["joy"] += 1
    lead.memes["joy"] += 1
    helper.memes["joy"] += 1
    recipient.memes["belonging"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then three small sets of fingers finished the final weave, row by row, slow enough to stay strong and bright."
    )


def reveal(world: World, lead: Entity, helper: Entity, recipient: Entity,
           project: Project) -> None:
    gift = world.get("gift")
    gift.meters["gifted"] += 1
    world.say(
        f'At last {lead.id} lifted the finished {project.label}. {project.reveal_line}'
    )
    world.say(
        f"The tiny cupie charm gave a cheerful swing, and {recipient.id}'s eyes shone wide with delight."
    )


def lesson(world: World, lead: Entity, helper: Entity, recipient: Entity,
           snag_happened: bool, sting_happened: bool) -> None:
    lead.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    recipient.memes["lesson"] += 1
    lines = []
    if sting_happened and snag_happened:
        lines.append(
            f'"Now I know," said {recipient.id}, "a gift can be sweet, but sweeter still when friends mend the feeling and mend the thing."'
        )
        lines.append(
            f'"And I know," said {lead.id}, "if we rush the weave or hush too hard, joy loses some of its ring."'
        )
    elif snag_happened:
        lines.append(
            f'"Now I know," said {lead.id}, "when we weave too fast, the pretty part can part and bend."'
        )
        lines.append(
            f'"So we go slow," said {helper.id}, "and when a strip goes wrong, a friend can help it mend."'
        )
    else:
        lines.append(
            f'"Now I know," said {lead.id}, "a surprise should never make a friend feel far away."'
        )
        lines.append(
            f'"Best weave a gift with open hearts," said {recipient.id}, "so everyone has room to stay."'
        )
    for line in lines:
        world.say(line)
    world.say(
        "And under the gentle afternoon light, the three friends sat close, the finished gift between them like a promise kept just right."
    )


def tell(place: Place, project: Project, material: Material, repair: Repair,
         pace: str, secrecy: str,
         lead_name: str = "Lila", lead_gender: str = "girl", lead_trait: str = "thoughtful",
         helper_name: str = "Ben", helper_gender: str = "boy", helper_trait: str = "steady",
         recipient_name: str = "Mina", recipient_gender: str = "girl",
         recipient_trait: str = "shy") -> World:
    world = World(place)
    lead = world.add(Entity(
        id=lead_name, kind="character", type=lead_gender, role="lead",
        traits=[lead_trait], attrs={"trait": lead_trait},
    ))
    helper = world.add(Entity(
        id=helper_name, kind="character", type=helper_gender, role="helper",
        traits=[helper_trait], attrs={"trait": helper_trait},
    ))
    recipient = world.add(Entity(
        id=recipient_name, kind="character", type=recipient_gender, role="recipient",
        traits=[recipient_trait], attrs={"trait": recipient_trait},
    ))
    gift = world.add(Entity(
        id="gift", kind="thing", type=project.id, label=project.label,
        attrs={"rows": project.rows, "project": project.id, "material": material.id},
    ))

    for child in (lead, helper, recipient):
        child.memes["left_out"] = 0.0
        child.memes["worry"] = 0.0
        child.memes["joy"] = 0.0
        child.memes["lesson"] = 0.0
    gift.meters["progress"] = 0.0
    gift.meters["tangle"] = 0.0
    gift.meters["torn"] = 0.0
    gift.meters["mended"] = 0.0

    introduce(world, lead, helper, recipient, place)
    wish_surprise(world, lead, helper, recipient, project, material)

    world.para()
    start_weave(world, lead, helper, project, material, pace)
    recipient_nears(world, recipient, secrecy)

    snag_happened = pace_causes_snag(project, material, pace)
    sting_happened = secrecy_hurts(secrecy, recipient_trait)

    if snag_happened:
        snag(world, lead, helper, project, material)
    if sting_happened:
        stung_feeling(world, recipient)

    world.para()
    explain_surprise(world, lead, helper, recipient, project)
    if snag_happened:
        mend(world, recipient, repair, material)
    finish_together(world, lead, helper, recipient, project)

    world.para()
    reveal(world, lead, helper, recipient, project)
    lesson(world, lead, helper, recipient, snag_happened, sting_happened)

    world.facts.update(
        place=place,
        project=project,
        material=material,
        repair=repair,
        pace=pace,
        secrecy=secrecy,
        lead=lead,
        helper=helper,
        recipient=recipient,
        gift=gift,
        snag=snag_happened,
        sting=sting_happened,
        outcome=("mended_and_shared" if snag_happened and sting_happened
                 else "mended" if snag_happened else "shared"),
    )
    return world


PLACES = {
    "classroom": Place(
        id="classroom",
        label="classroom",
        scene="the sunny classroom art corner",
        detail="paper squares, ribbons, and crayons made bright little hills on the table",
    ),
    "porch": Place(
        id="porch",
        label="porch",
        scene="the back porch after lunch",
        detail="the boards were warm, and the breeze made the hanging strings sway",
    ),
    "garden": Place(
        id="garden",
        label="garden",
        scene="the school garden nook",
        detail="bees hummed by the marigolds and a picnic cloth lay flat on the grass",
    ),
}

PROJECTS = {
    "bracelet": Project(
        id="bracelet",
        label="bracelet",
        phrase="a friendship bracelet",
        rows=3,
        need_flex=2,
        need_strength=1,
        reveal_line='"For you," said the friends, "to wear on your wrist when you skip and twirl and play."',
        tags={"bracelet", "weave"},
    ),
    "bookmark": Project(
        id="bookmark",
        label="bookmark",
        phrase="a woven bookmark",
        rows=4,
        need_flex=2,
        need_strength=1,
        reveal_line='"For you," they said, "to keep your place where the story dragons sleep and the moonboats sway."',
        tags={"bookmark", "weave", "book"},
    ),
    "basket": Project(
        id="basket",
        label="basket",
        phrase="a tiny gift basket",
        rows=5,
        need_flex=2,
        need_strength=2,
        reveal_line='"For you," they said, "to hold small treasures, smooth stones, and petals you may find one day."',
        tags={"basket", "weave"},
    ),
}

MATERIALS = {
    "ribbon": Material(
        id="ribbon",
        label="ribbon",
        phrase="a bundle of satin ribbon",
        flex=3,
        strength=1,
        texture="silky",
        tags={"ribbon"},
    ),
    "paper": Material(
        id="paper",
        label="paper strips",
        phrase="a stack of paper strips",
        flex=2,
        strength=1,
        texture="crinkly",
        tags={"paper"},
    ),
    "yarn": Material(
        id="yarn",
        label="yarn",
        phrase="three balls of soft yarn",
        flex=3,
        strength=2,
        texture="woolly",
        tags={"yarn"},
    ),
    "reed": Material(
        id="reed",
        label="reed strips",
        phrase="a neat bunch of reed strips",
        flex=2,
        strength=3,
        texture="rustly",
        tags={"reed"},
    ),
}

REPAIRS = {
    "tape": Repair(
        id="tape",
        label="clear tape",
        sense=3,
        power=1,
        materials={"paper", "ribbon"},
        success_text="pressed the torn {material} flat and mended it with a neat piece of clear tape",
        qa_text="They flattened the torn part and fixed it with clear tape.",
        tags={"tape", "mend"},
    ),
    "knot": Repair(
        id="knot",
        label="a small knot",
        sense=3,
        power=1,
        materials={"ribbon", "yarn"},
        success_text="tied the loose {material} back together with a tiny careful knot",
        qa_text="They tied the loose part back together with a tiny careful knot.",
        tags={"knot", "mend"},
    ),
    "fresh_strip": Repair(
        id="fresh_strip",
        label="a fresh strip",
        sense=3,
        power=2,
        materials={"paper", "ribbon", "yarn", "reed"},
        success_text="slid in a fresh piece of {material} and wove the weak place over again",
        qa_text="They replaced the weak piece and wove that part again.",
        tags={"replace", "mend"},
    ),
    "glue_blob": Repair(
        id="glue_blob",
        label="a big blob of glue",
        sense=1,
        power=1,
        materials={"paper"},
        success_text="squished a sticky blob over the torn {material}",
        qa_text="They covered the torn part with a sticky blob of glue.",
        tags={"glue"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Ruby", "Tess", "Nora", "Ava", "Zoe", "Pia", "Ella", "Maya"]
BOY_NAMES = ["Ben", "Sam", "Leo", "Owen", "Max", "Finn", "Eli", "Noah", "Theo", "Jude"]
LEAD_TRAITS = ["thoughtful", "bouncy", "cheerful", "careful"]
HELPER_TRAITS = ["steady", "kind", "patient", "gentle"]
RECIPIENT_TRAITS = ["shy", "quiet", "sunny", "patient"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for project_id, project in PROJECTS.items():
        for material_id, material in MATERIALS.items():
            if weaveable(project, material):
                combos.append((project_id, material_id))
    return combos


def explain_combo_rejection(project: Project, material: Material) -> str:
    return (
        f"(No story: {material.label} cannot honestly carry {project.phrase}. "
        f"The weave needs flex ≥ {project.need_flex} and strength ≥ {project.need_strength}, "
        f"but this material has flex {material.flex} and strength {material.strength}.)"
    )


def explain_repair_rejection(repair_id: str, material_id: str) -> str:
    repair = REPAIRS[repair_id]
    material = MATERIALS[material_id]
    if repair.sense < SENSE_MIN:
        better = ", ".join(sorted(r.id for r in sensible_repairs()))
        return (
            f"(Refusing repair '{repair_id}': it scores too low on common sense "
            f"(sense={repair.sense} < {SENSE_MIN}). Try one of: {better}.)"
        )
    return (
        f"(No story: {repair.label} is not a good way to mend {material.label} in this world. "
        f"Pick a repair that really works for that material.)"
    )


def explain_flat_story() -> str:
    return (
        "(No story: this choice makes the surprise too flat. Pick a pace or secrecy "
        "that creates a real turn, such as --pace quick or --secrecy hush.)"
    )


@dataclass
class StoryParams:
    place: str
    project: str
    material: str
    repair: str
    pace: str
    secrecy: str
    lead_name: str
    lead_gender: str
    lead_trait: str
    helper_name: str
    helper_gender: str
    helper_trait: str
    recipient_name: str
    recipient_gender: str
    recipient_trait: str
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
    "weave": [
        (
            "What does weave mean?",
            "To weave means to cross one strip over and under another again and again until they hold together. That is how flat strips can turn into something strong and pretty."
        )
    ],
    "friendship": [
        (
            "What makes a surprise kind?",
            "A kind surprise is meant to bring joy, not worry. If a secret starts to hurt someone's feelings, it is time to explain and bring them close."
        )
    ],
    "cupie": [
        (
            "What is a cupie charm in this story?",
            "It is a tiny doll-like decoration tied onto the gift. It does not do the weaving, but it makes the finished present look extra cheerful."
        )
    ],
    "ribbon": [
        (
            "Why can ribbon tear if you pull too fast?",
            "Ribbon can bend very well, but some ribbon is not very strong. If you tug too hard and too quickly, the fibers can split or fray."
        )
    ],
    "paper": [
        (
            "Why can paper strips rip while weaving?",
            "Paper bends for a little while, but if it is folded or tugged too hard, it can tear. Slow hands help paper stay neat."
        )
    ],
    "yarn": [
        (
            "Why is yarn good for weaving?",
            "Yarn is soft and bendy, so it can cross over and under many times. Good yarn also has enough strength that it does not snap easily."
        )
    ],
    "reed": [
        (
            "Why are reed strips useful for a small basket?",
            "Reed strips are stiffer and stronger than many soft craft materials. That extra strength helps a basket keep its shape."
        )
    ],
    "mend": [
        (
            "What does it mean to mend something?",
            "To mend something is to fix a broken or torn part so it can be used again. Mending takes patience and care."
        )
    ],
    "book": [
        (
            "What is a bookmark for?",
            "A bookmark holds your place in a book so you can stop reading and come back later. It keeps you from losing the page you were on."
        )
    ],
}
KNOWLEDGE_ORDER = ["weave", "friendship", "cupie", "ribbon", "paper", "yarn", "reed", "mend", "book"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    project: Project = f["project"]
    material: Material = f["material"]
    lead: Entity = f["lead"]
    helper: Entity = f["helper"]
    recipient: Entity = f["recipient"]
    outcome = f["outcome"]
    base = (
        f'Write a rhyming story for a 3-to-5-year-old that includes the words "cupie" and "weave", '
        f"and features friendship, a surprise, and a lesson learned."
    )
    if outcome == "mended_and_shared":
        return [
            base,
            f"Tell a gentle rhyming story where {lead.id} and {helper.id} rush while making {project.phrase} from {material.label}, "
            f"and {recipient.id} also feels left out by too much hush, but everyone mends both the gift and the feeling.",
            "Write a child-friendly story in rhyme where a secret and a snag both cause trouble, and the ending teaches that good surprises should feel warm and careful."
        ]
    if outcome == "mended":
        return [
            base,
            f"Tell a rhyming story where friends make {project.phrase}, the weave snags because they hurry, and a friend helps mend it.",
            "Write a short rhyming craft story with a surprise gift, a small mistake, and a lesson about going slowly and helping kindly."
        ]
    return [
        base,
        f"Tell a rhyming story where {lead.id} and {helper.id} plan a woven surprise for {recipient.id}, but too much secrecy makes the surprise feel lonely until they invite {recipient.pronoun('object')} in.",
        "Write a gentle rhyming story that teaches the best surprises leave room for friendship and explanation."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead: Entity = f["lead"]
    helper: Entity = f["helper"]
    recipient: Entity = f["recipient"]
    project: Project = f["project"]
    material: Material = f["material"]
    repair: Repair = f["repair"]
    snag = bool(f["snag"])
    sting = bool(f["sting"])
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about three friends: {lead.id}, {helper.id}, and {recipient.id}. {lead.id} and {helper.id} begin the surprise, and by the end all three friends finish it together."
        ),
        (
            "What were they making?",
            f"They were making {project.phrase}. They wanted it to be a cheerful surprise, and they planned to add a tiny cupie charm on top."
        ),
        (
            "Why did the story have a problem in the middle?",
            (
                "The middle became tense because the surprise was not handled gently enough."
                if sting and not snag else
                "The middle became tense because the children rushed the weave and the gift snagged."
                if snag and not sting else
                "The middle became tense for two reasons: the children rushed the weave so it tore, and too much hush made the surprise feel hurtful."
            ),
        ),
    ]
    if sting:
        qa.append((
            f"Why did {recipient.id} feel bad for a moment?",
            f"{recipient.id} heard the hush-hush whispering and thought {recipient.pronoun()} might be left out. The secret was meant to be kind, but without an explanation it felt chilly instead of friendly."
        ))
    if snag:
        qa.append((
            "How did the weaving go wrong?",
            f"They pulled the {material.label} too quickly, and the weave tore in the middle. The material could be woven, but rushing made the weak spot give way."
        ))
        qa.append((
            "How did they fix the gift?",
            f"{recipient.id} helped mend it: {repair.qa_text} That repair worked because it matched the material they were using."
        ))
    qa.append((
        "What lesson did the friends learn?",
        (
            "They learned that a surprise should make a friend feel welcomed, not pushed away. They also learned to explain the secret once feelings began to hurt."
            if sting and not snag else
            "They learned that careful hands make a stronger weave, and friends can help mend small mistakes. Going slowly turned the gift back into something sturdy and sweet."
            if snag and not sting else
            "They learned two lessons at once: careful hands keep a weave strong, and caring words keep a friendship strong too. By mending the gift and the feeling together, they made the surprise truly kind."
        )
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"weave", "friendship", "cupie"}
    project: Project = f["project"]
    material: Material = f["material"]
    tags |= set(project.tags)
    tags |= set(material.tags)
    if f["snag"]:
        tags.add("mend")
        tags |= set(f["repair"].tags)
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts['secrecy']}, shared={world.facts['purpose_shared']}, near={world.facts['recipient_near']}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="classroom",
        project="bracelet",
        material="ribbon",
        repair="knot",
        pace="quick",
        secrecy="wink",
        lead_name="Lila",
        lead_gender="girl",
        lead_trait="cheerful",
        helper_name="Ben",
        helper_gender="boy",
        helper_trait="steady",
        recipient_name="Mina",
        recipient_gender="girl",
        recipient_trait="sunny",
    ),
    StoryParams(
        place="garden",
        project="bookmark",
        material="paper",
        repair="fresh_strip",
        pace="slow",
        secrecy="hush",
        lead_name="Ruby",
        lead_gender="girl",
        lead_trait="thoughtful",
        helper_name="Sam",
        helper_gender="boy",
        helper_trait="kind",
        recipient_name="Nora",
        recipient_gender="girl",
        recipient_trait="shy",
    ),
    StoryParams(
        place="porch",
        project="basket",
        material="yarn",
        repair="fresh_strip",
        pace="quick",
        secrecy="hush",
        lead_name="Maya",
        lead_gender="girl",
        lead_trait="bouncy",
        helper_name="Leo",
        helper_gender="boy",
        helper_trait="gentle",
        recipient_name="Pia",
        recipient_gender="girl",
        recipient_trait="quiet",
    ),
    StoryParams(
        place="garden",
        project="basket",
        material="reed",
        repair="fresh_strip",
        pace="slow",
        secrecy="hush",
        lead_name="Theo",
        lead_gender="boy",
        lead_trait="careful",
        helper_name="Ella",
        helper_gender="girl",
        helper_trait="patient",
        recipient_name="Zoe",
        recipient_gender="girl",
        recipient_trait="shy",
    ),
]

ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
weaveable(P, M) :- project(P), material(M), need_flex(P, PF), flex(M, MF), MF >= PF,
                   need_strength(P, PS), strength(M, MS), MS >= PS.
sensible(R) :- repair(R), sense(R, S), sense_min(MN), S >= MN.
repair_works(R, M) :- repair_material(R, M), repair_power(R, P), P >= 1.

% At least one real strain must exist, so the story has a turn.
snag(P, M, quick) :- need_strength(P, PS), strength(M, MS), MS < PS + 1.
sting(hush, T) :- shy_trait(T).

valid_story(P, M, R, Pace, Sec, T) :-
    weaveable(P, M),
    sensible(R),
    repair_works(R, M),
    (snag(P, M, Pace); sting(Sec, T)).

% --- outcome inference -----------------------------------------------------
outcome(mended_and_shared) :- chosen_project(P), chosen_material(M), chosen_pace(quick),
                              snag(P, M, quick), chosen_secrecy(hush), chosen_trait(T), sting(hush, T).
outcome(mended) :- chosen_project(P), chosen_material(M), chosen_pace(quick),
                   snag(P, M, quick), not outcome(mended_and_shared).
outcome(shared) :- not outcome(mended_and_shared), not outcome(mended).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for project_id, project in PROJECTS.items():
        lines.append(asp.fact("project", project_id))
        lines.append(asp.fact("need_flex", project_id, project.need_flex))
        lines.append(asp.fact("need_strength", project_id, project.need_strength))
    for material_id, material in MATERIALS.items():
        lines.append(asp.fact("material", material_id))
        lines.append(asp.fact("flex", material_id, material.flex))
        lines.append(asp.fact("strength", material_id, material.strength))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("sense", repair_id, repair.sense))
        lines.append(asp.fact("repair_power", repair_id, repair.power))
        for material_id in sorted(repair.materials):
            lines.append(asp.fact("repair_material", repair_id, material_id))
    for pace in ("slow", "quick"):
        lines.append(asp.fact("pace", pace))
    for secrecy in ("wink", "hush"):
        lines.append(asp.fact("secrecy", secrecy))
    for trait in sorted(RECIPIENT_TRAITS):
        lines.append(asp.fact("trait", trait))
    for trait in sorted(SHY_TRAITS):
        lines.append(asp.fact("shy_trait", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show weaveable/2."))
    return sorted(set(asp.atoms(model, "weaveable")))


def asp_sensible_repairs() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_story/6."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_project", params.project),
        asp.fact("chosen_material", params.material),
        asp.fact("chosen_pace", params.pace),
        asp.fact("chosen_secrecy", params.secrecy),
        asp.fact("chosen_trait", params.recipient_trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming storyworld: a woven surprise, a friendship wobble, and a lesson learned."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--pace", choices=["slow", "quick"])
    ap.add_argument("--secrecy", choices=["wink", "hush"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n not in avoid]
    return rng.choice(choices)


def _pick_gender(rng: random.Random) -> str:
    return rng.choice(["girl", "boy"])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.project and args.material:
        project = PROJECTS[args.project]
        material = MATERIALS[args.material]
        if not weaveable(project, material):
            raise StoryError(explain_combo_rejection(project, material))

    project_materials = [
        combo for combo in valid_combos()
        if (args.project is None or combo[0] == args.project)
        and (args.material is None or combo[1] == args.material)
    ]
    if not project_materials:
        raise StoryError("(No valid project/material combination matches the given options.)")

    project_id, material_id = rng.choice(sorted(project_materials))
    project = PROJECTS[project_id]
    material = MATERIALS[material_id]

    repair_choices = [
        repair.id for repair in sensible_repairs()
        if repair_works(repair, material)
    ]
    if args.repair:
        if args.repair not in REPAIRS:
            raise StoryError("(Unknown repair.)")
        if REPAIRS[args.repair].sense < SENSE_MIN or not repair_works(REPAIRS[args.repair], material):
            raise StoryError(explain_repair_rejection(args.repair, material_id))
        repair_id = args.repair
    else:
        repair_id = rng.choice(sorted(repair_choices))

    pace = args.pace or rng.choice(["slow", "quick"])
    secrecy = args.secrecy or rng.choice(["wink", "hush"])

    recipient_trait = rng.choice(RECIPIENT_TRAITS)
    if not has_turn(pace, secrecy, project, material, recipient_trait):
        candidate_pairs = [
            (p, s, t)
            for p in ["slow", "quick"]
            for s in ["wink", "hush"]
            for t in RECIPIENT_TRAITS
            if (args.pace is None or p == args.pace)
            and (args.secrecy is None or s == args.secrecy)
            and has_turn(p, s, project, material, t)
        ]
        if not candidate_pairs:
            raise StoryError(explain_flat_story())
        pace, secrecy, recipient_trait = rng.choice(sorted(candidate_pairs))

    if args.pace and args.secrecy and not any(
        has_turn(args.pace, args.secrecy, project, material, trait)
        for trait in RECIPIENT_TRAITS
    ):
        raise StoryError(explain_flat_story())

    place = args.place or rng.choice(sorted(PLACES))

    lead_gender = _pick_gender(rng)
    lead_name = _pick_name(rng, lead_gender, set())
    helper_gender = _pick_gender(rng)
    helper_name = _pick_name(rng, helper_gender, {lead_name})
    recipient_gender = _pick_gender(rng)
    recipient_name = _pick_name(rng, recipient_gender, {lead_name, helper_name})

    return StoryParams(
        place=place,
        project=project_id,
        material=material_id,
        repair=repair_id,
        pace=pace,
        secrecy=secrecy,
        lead_name=lead_name,
        lead_gender=lead_gender,
        lead_trait=rng.choice(LEAD_TRAITS),
        helper_name=helper_name,
        helper_gender=helper_gender,
        helper_trait=rng.choice(HELPER_TRAITS),
        recipient_name=recipient_name,
        recipient_gender=recipient_gender,
        recipient_trait=recipient_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place '{params.place}'.)")
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project '{params.project}'.)")
    if params.material not in MATERIALS:
        raise StoryError(f"(Unknown material '{params.material}'.)")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair '{params.repair}'.)")
    if params.pace not in {"slow", "quick"}:
        raise StoryError("(Pace must be 'slow' or 'quick'.)")
    if params.secrecy not in {"wink", "hush"}:
        raise StoryError("(Secrecy must be 'wink' or 'hush'.)")
    if params.recipient_trait not in RECIPIENT_TRAITS:
        raise StoryError(f"(Unknown recipient trait '{params.recipient_trait}'.)")

    project = PROJECTS[params.project]
    material = MATERIALS[params.material]
    repair = REPAIRS[params.repair]

    if not weaveable(project, material):
        raise StoryError(explain_combo_rejection(project, material))
    if repair.sense < SENSE_MIN or not repair_works(repair, material):
        raise StoryError(explain_repair_rejection(params.repair, params.material))
    if not has_turn(params.pace, params.secrecy, project, material, params.recipient_trait):
        raise StoryError(explain_flat_story())

    world = tell(
        place=PLACES[params.place],
        project=project,
        material=material,
        repair=repair,
        pace=params.pace,
        secrecy=params.secrecy,
        lead_name=params.lead_name,
        lead_gender=params.lead_gender,
        lead_trait=params.lead_trait,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        helper_trait=params.helper_trait,
        recipient_name=params.recipient_name,
        recipient_gender=params.recipient_gender,
        recipient_trait=params.recipient_trait,
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


def python_valid_stories() -> list[tuple[str, str, str, str, str, str]]:
    out: list[tuple[str, str, str, str, str, str]] = []
    for project_id, material_id in valid_combos():
        project = PROJECTS[project_id]
        material = MATERIALS[material_id]
        for repair in sensible_repairs():
            if not repair_works(repair, material):
                continue
            for pace in ("slow", "quick"):
                for secrecy in ("wink", "hush"):
                    for trait in RECIPIENT_TRAITS:
                        if has_turn(pace, secrecy, project, material, trait):
                            out.append((project_id, material_id, repair.id, pace, secrecy, trait))
    return sorted(set(out))


def asp_verify() -> int:
    rc = 0

    clingo_weaveable = set(asp_valid_combos())
    python_weaveable = set(valid_combos())
    if clingo_weaveable == python_weaveable:
        print(f"OK: weaveable combos match valid_combos() ({len(clingo_weaveable)} combos).")
    else:
        rc = 1
        print("MISMATCH in weaveable combos:")
        if clingo_weaveable - python_weaveable:
            print("  only in clingo:", sorted(clingo_weaveable - python_weaveable))
        if python_weaveable - clingo_weaveable:
            print("  only in python:", sorted(python_weaveable - clingo_weaveable))

    clingo_repairs = set(asp_sensible_repairs())
    python_repairs = {r.id for r in sensible_repairs()}
    if clingo_repairs == python_repairs:
        print(f"OK: sensible repairs match ({sorted(clingo_repairs)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible repairs: clingo={sorted(clingo_repairs)} python={sorted(python_repairs)}")

    clingo_valid = set(asp_valid_stories())
    python_valid = set(python_valid_stories())
    if clingo_valid == python_valid:
        print(f"OK: full valid-story space matches ({len(clingo_valid)} cases).")
    else:
        rc = 1
        print("MISMATCH in valid_story/6:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid)[:20])
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid)[:20])

    cases = list(CURATED)
    for s in range(60):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {s}.")
            break

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show weaveable/2.\n#show sensible/1.\n#show valid_story/6.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"sensible repairs: {', '.join(asp_sensible_repairs())}\n")
        print(f"{len(combos)} weaveable (project, material) combos:\n")
        for project_id, material_id in combos:
            count = sum(1 for p, m, *_ in stories if (p, m) == (project_id, material_id))
            print(f"  {project_id:10} {material_id:10} [{count} valid story settings]")
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
            header = f"### {p.project} from {p.material} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
