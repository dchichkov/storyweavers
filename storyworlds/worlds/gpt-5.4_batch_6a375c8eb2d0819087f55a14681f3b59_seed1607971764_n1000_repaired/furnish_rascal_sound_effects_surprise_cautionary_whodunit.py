#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/furnish_rascal_sound_effects_surprise_cautionary_whodunit.py
========================================================================================

A standalone story world about two children helping furnish a cozy room when a
mysterious noise turns the job into a tiny whodunit. The cautionary turn comes
from an unsafe attempt to solve the mystery by climbing on wobbly furniture;
the surprise ending reveals the harmless culprit.

Run it
------
    python storyworlds/worlds/gpt-5.4/furnish_rascal_sound_effects_surprise_cautionary_whodunit.py
    python storyworlds/worlds/gpt-5.4/furnish_rascal_sound_effects_surprise_cautionary_whodunit.py --project reading_nook --culprit kitten --spot curtain_rod
    python storyworlds/worlds/gpt-5.4/furnish_rascal_sound_effects_surprise_cautionary_whodunit.py --spot curtain_rod --perch crate_stack
    python storyworlds/worlds/gpt-5.4/furnish_rascal_sound_effects_surprise_cautionary_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/furnish_rascal_sound_effects_surprise_cautionary_whodunit.py --qa --json
    python storyworlds/worlds/gpt-5.4/furnish_rascal_sound_effects_surprise_cautionary_whodunit.py --verify
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "sensible", "patient"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Project:
    id: str
    room: str
    task: str
    props: str
    goal: str
    finish_line: str
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
    phrase: str
    level: str
    risk: int
    capacity: int
    reveal_place: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class Culprit:
    id: str
    label: str
    article: str
    size: int
    reaches: set[str]
    likes: set[str]
    sound: str
    motion: str
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
class Perch:
    id: str
    label: str
    phrase: str
    reaches: set[str]
    stability: int
    creak: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_wobble(world: World) -> list[str]:
    perch = world.get("perch")
    spot = world.get("spot")
    if perch.meters["climbed"] < THRESHOLD:
        return []
    sig = ("wobble", perch.id)
    if sig in world.fired:
        return []
    need = int(spot.attrs.get("risk", 0)) + int(world.facts.get("delay", 0))
    if int(perch.attrs.get("stability", 0)) >= need:
        return []
    world.fired.add(sig)
    perch.meters["wobble"] += 1
    world.get("room").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["__wobble__"]


def _r_scatter(world: World) -> list[str]:
    perch = world.get("perch")
    supply = world.get("supply")
    if perch.meters["wobble"] < THRESHOLD or supply.meters["standing"] < THRESHOLD:
        return []
    sig = ("scatter", supply.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    supply.meters["standing"] = 0.0
    supply.meters["scattered"] += 1
    world.get("room").meters["mess"] += 1
    return ["__scatter__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="scatter", tag="physical", apply=_r_scatter),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(s for s in items if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def culprit_plausible(project: Project, culprit: Culprit, spot: Spot) -> bool:
    return bool(project.tags & culprit.likes) and culprit.size <= spot.capacity and spot.level in culprit.reaches


def perch_can_reach(perch: Perch, spot: Spot) -> bool:
    return spot.level in perch.reaches


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for project_id, project in PROJECTS.items():
        for culprit_id, culprit in CULPRITS.items():
            for spot_id, spot in SPOTS.items():
                if not culprit_plausible(project, culprit, spot):
                    continue
                for perch_id, perch in PERCHES.items():
                    if perch_can_reach(perch, spot):
                        combos.append((project_id, culprit_id, spot_id, perch_id))
    return sorted(combos)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def is_contained(perch: Perch, spot: Spot, delay: int) -> bool:
    return perch.stability >= spot.risk + delay


def outcome_of(params: "StoryParams") -> str:
    if would_avert(
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        trait=params.trait,
    ):
        return "averted"
    if is_contained(PERCHES[params.perch], SPOTS[params.spot], params.delay):
        return "contained"
    return "spilled"


def predict_climb(world: World) -> dict:
    sim = world.copy()
    sim.get("perch").meters["climbed"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": sim.get("perch").meters["wobble"] >= THRESHOLD,
        "mess": sim.get("room").meters["mess"] >= THRESHOLD,
    }


def project_setup(world: World, a: Entity, b: Entity, project: Project) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"After lunch, {a.id} and {b.id} helped {world.get('parent').label_word} furnish {project.task}. "
        f"{project.props}"
    )
    world.say(
        f"They wanted the place to feel like {project.goal}."
    )


def mystery_noise(world: World, a: Entity, b: Entity, culprit: Culprit, spot: Spot) -> None:
    for kid in (a, b):
        kid.memes["curiosity"] += 1
    world.say(
        f"Just as {b.id} straightened a cushion, {culprit.sound} came from {spot.phrase}. "
        f"Both children froze."
    )
    world.say(
        f'"Who did that?" {a.id} whispered. Suddenly the furnishing job felt like a real whodunit.'
    )


def tempt(world: World, a: Entity, perch: Perch, spot: Spot) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} pointed at {world.get("perch").label}. "I can climb {perch.phrase} and peek into {spot.the}," '
        f'{a.pronoun()} said.'
    )


def warn(world: World, b: Entity, a: Entity, perch: Perch, spot: Spot) -> None:
    pred = predict_climb(world)
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_mess"] = pred["mess"]
    b.memes["caution"] += 1
    caution = ""
    if pred["mess"]:
        caution = " If you do that, the room could end up in a noisy tumble."
    elif pred["wobble"]:
        caution = " That thing will wobble."
    world.say(
        f'{b.id} caught {a.id} by the sleeve. "Wait. {perch.label.capitalize()} is not for climbing.{caution}"'
    )


def back_down(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} looked at the wobbly perch, then at {b.id}, and let out a slow breath. '
        f'"You are right," {a.pronoun()} said.'
    )
    world.say(
        f'Together they called for {parent.label_word}, who came over with a calm smile instead of a scold.'
    )


def defy(world: World, a: Entity, b: Entity, perch: Perch) -> None:
    a.memes["defiance"] += 1
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        world.say(
            f'"It will be quick," {a.id} said, and because {a.pronoun()} was the older one, '
            f'{b.id} could not stop {a.pronoun("object")}.'
        )
    else:
        world.say(f'"It will be quick," {a.id} said, and reached for {perch.phrase}.')
    world.say(f"{perch.creak} went {perch.label} under {a.id}'s feet.")


def climb(world: World, a: Entity) -> None:
    world.get("perch").meters["climbed"] += 1
    propagate(world, narrate=False)
    if world.get("perch").meters["wobble"] >= THRESHOLD:
        world.say(
            f"{a.id} had barely lifted one knee when the perch wriggled under {a.pronoun('object')}."
        )
    else:
        world.say(
            f"{a.id} got one careful look upward, but even that made the mystery feel more risky than fun."
        )


def spill(world: World, project: Project, spot: Spot) -> None:
    if world.get("supply").meters["scattered"] >= THRESHOLD:
        world.say(
            f"Then came the turn: BANG! FLOP! One of the things they were using to furnish the room tipped over, "
            f"and the neat little scene broke apart beneath {spot.the}."
        )
        world.say(
            f"Cushions slid, a basket rolled, and the room no longer looked ready for {project.goal}."
        )


def parent_investigates(world: World, parent: Entity, spot: Spot) -> None:
    if spot.level == "low":
        method = "knelt down with a flashlight and looked in slowly"
    elif spot.level == "medium":
        method = "set a sturdy step stool in place and looked in carefully"
    else:
        method = "brought the stepladder from the hall and climbed up one safe step at a time"
    world.facts["safe_method"] = method
    world.say(
        f"{parent.label_word.capitalize()} {method}."
    )


def reveal(world: World, parent: Entity, culprit: Culprit, spot: Spot) -> None:
    world.get("culprit").meters["found"] += 1
    world.say(
        f"Another soft rustle came from {spot.the}. Then {parent.label_word} laughed."
    )
    world.say(
        f'"It was {culprit.article} {culprit.label} all along!" {parent.pronoun()} said. '
        f"{culprit.reveal_line} The little rascal blinked as if the whole mystery had been a game."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, perch: Perch) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
        kid.memes["fear"] = 0.0
    extra = ""
    if world.get("supply").meters["scattered"] >= THRESHOLD:
        extra = " A mystery is never a good reason to scramble onto something wobbly."
    world.say(
        f'{parent.label_word.capitalize()} hugged them close. "When something goes bump in the room, '
        f'we stop, think, and use safe feet on the floor.{extra} {perch.label.capitalize()} is for sitting or moving, not climbing."'
    )


def finish_room(world: World, a: Entity, b: Entity, parent: Entity, project: Project, culprit: Culprit) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    if world.get("supply").meters["scattered"] >= THRESHOLD:
        world.say(
            f"Together they picked everything up and put it back where it belonged."
        )
    world.say(
        f"Soon the room looked right again, and at last it felt like {project.goal}."
    )
    world.say(
        f"{a.id} set the final piece in place, {b.id} gave a proud nod, and {culprit.article} {culprit.label} curled up nearby as if {project.finish_line}."
    )
def tell(
    culprit: Culprit,
    spot: Spot,
    perch: Perch,
    instigator: Instigator,
    instigator_gender: str,
    cautioner: Cautioner,
    cautioner_gender: str,
    trait: Trait,
    parent_type: ParentType,
    delay: Delay,
    instigator_age: InstigatorAge,
    cautioner_age: CautionerAge,
    relation: Relation,
    project=None,
) -> World:
    world = World()
    a = world.add(
        Entity(
            id=instigator,
            kind="character",
            type=instigator_gender,
            role="instigator",
            age=instigator_age,
            attrs={"relation": relation},
            traits=["bold"],
        )
    )
    b = world.add(
        Entity(
            id=cautioner,
            kind="character",
            type=cautioner_gender,
            role="cautioner",
            age=cautioner_age,
            attrs={"relation": relation},
            traits=[trait],
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
        )
    )
    room = world.add(Entity(id="room", type="room", label=project.room))
    supply = world.add(
        Entity(
            id="supply",
            type="supply",
            label="the furnishing pile",
            attrs={"project": project.id},
        )
    )
    supply.meters["standing"] = 1.0
    perch_ent = world.add(
        Entity(
            id="perch",
            type="perch",
            label=perch.label,
            attrs={"stability": perch.stability},
        )
    )
    spot_ent = world.add(
        Entity(
            id="spot",
            type="spot",
            label=spot.label,
            attrs={"risk": spot.risk, "level": spot.level},
        )
    )
    culprit_ent = world.add(
        Entity(
            id="culprit",
            type="animal",
            label=culprit.label,
            attrs={"size": culprit.size},
        )
    )

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)
    world.facts["delay"] = delay
    world.facts["relation"] = relation
    world.facts["project_cfg"] = project
    world.facts["culprit_cfg"] = culprit
    world.facts["spot_cfg"] = spot
    world.facts["perch_cfg"] = perch

    project_setup(world, a, b, project)
    world.para()
    mystery_noise(world, a, b, culprit, spot)
    tempt(world, a, perch, spot)
    warn(world, b, a, perch, spot)

    averted = would_avert(
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        trait=trait,
    )

    if averted:
        back_down(world, a, b, parent)
        world.para()
        parent_investigates(world, parent, spot)
        reveal(world, parent, culprit, spot)
        lesson(world, parent, a, b, perch)
    else:
        defy(world, a, b, perch)
        world.para()
        climb(world, a)
        if world.get("supply").meters["scattered"] >= THRESHOLD:
            spill(world, project, spot)
        world.say(f'"{parent.label_word.upper()}!" {b.id} cried.')
        world.para()
        parent_investigates(world, parent, spot)
        reveal(world, parent, culprit, spot)
        lesson(world, parent, a, b, perch)

    world.para()
    finish_room(world, a, b, parent, project, culprit)

    outcome = outcome_of(
        StoryParams(
            project=project.id,
            culprit=culprit.id,
            spot=spot.id,
            perch=perch.id,
            instigator=instigator,
            instigator_gender=instigator_gender,
            cautioner=cautioner,
            cautioner_gender=cautioner_gender,
            parent=parent_type,
            trait=trait,
            delay=delay,
            instigator_age=instigator_age,
            cautioner_age=cautioner_age,
            relation=relation,
            seed=None,
        )
    )
    world.facts.update(
        instigator=a,
        cautioner=b,
        parent=parent,
        room=room,
        supply=supply,
        perch=perch_ent,
        spot=spot_ent,
        culprit=culprit_ent,
        outcome=outcome,
        project=project,
        culprit_cfg=culprit,
        spot_cfg=spot,
        perch_cfg=perch,
        mystery_solved=culprit_ent.meters["found"] >= THRESHOLD,
        mess=supply.meters["scattered"] >= THRESHOLD,
    )
    return world
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


PROJECTS = {
    "reading_nook": Project(
        id="reading_nook",
        room="the attic nook",
        task="the attic nook with a round rug, two cushions, and a lamp shaped like a moon",
        props="A basket of books sat open on the floor, a striped blanket waited on the trunk, and a tassel tie for the curtain dangled nearby.",
        goal="the sort of corner where a story could whisper all by itself",
        finish_line="the nook had been waiting for exactly that guest",
        tags={"soft", "tassel", "yarn"},
    ),
    "guest_room": Project(
        id="guest_room",
        room="the little guest room",
        task="the little guest room with a folded quilt, fresh pillows, and a ribbon-tied basket of soaps",
        props="A quilt puffed on the bed, a pillow leaned against the chair, and the ribbon on the basket shone bright in the window.",
        goal="a room that looked ready to welcome someone with a gentle sigh",
        finish_line="the room had finally found its first napper",
        tags={"soft", "blanket", "ribbon"},
    ),
    "music_corner": Project(
        id="music_corner",
        room="the hall corner",
        task="the hall corner with a small stool, a bell garland, and a shiny music stand",
        props="The brass bell garland chimed when it moved, and a silver frame for sheet music glinted by the wall.",
        goal="a cheerful place where every little sound felt invited",
        finish_line="the corner had discovered its own funny song",
        tags={"shiny", "bell", "ribbon"},
    ),
}

SPOTS = {
    "trunk": Spot(
        id="trunk",
        label="trunk",
        the="the trunk",
        phrase="the old trunk by the wall",
        level="low",
        risk=0,
        capacity=2,
        reveal_place="inside the trunk with the blanket",
        tags={"low"},
    ),
    "window_seat": Spot(
        id="window_seat",
        label="window seat",
        the="the window seat",
        phrase="the wide window seat",
        level="medium",
        risk=1,
        capacity=2,
        reveal_place="inside the window seat box",
        tags={"medium"},
    ),
    "curtain_rod": Spot(
        id="curtain_rod",
        label="curtain rod",
        the="the curtain rod",
        phrase="the curtain rod above the window",
        level="high",
        risk=2,
        capacity=1,
        reveal_place="up by the curtain rod",
        tags={"high"},
    ),
    "bookcase_top": Spot(
        id="bookcase_top",
        label="top of the bookcase",
        the="the top of the bookcase",
        phrase="the top of the bookcase",
        level="high",
        risk=2,
        capacity=1,
        reveal_place="on top of the bookcase behind a stack of folded paper",
        tags={"high"},
    ),
}

CULPRITS = {
    "kitten": Culprit(
        id="kitten",
        label="kitten",
        article="a",
        size=1,
        reaches={"low", "medium", "high"},
        likes={"soft", "tassel", "ribbon"},
        sound="Scritch-scritch! Bump!",
        motion="pawing at dangling cloth",
        reveal_line="There was a kitten batting at the tassel and making the curtain shake",
        tags={"kitten", "pet"},
    ),
    "puppy": Culprit(
        id="puppy",
        label="puppy",
        article="a",
        size=2,
        reaches={"low", "medium"},
        likes={"soft", "blanket"},
        sound="Snuffle-snuff! Bonk!",
        motion="burrowing into soft things",
        reveal_line="A puppy had pushed into the blanket and bonked the wood with its wagging tail",
        tags={"puppy", "pet"},
    ),
    "magpie": Culprit(
        id="magpie",
        label="magpie",
        article="a",
        size=1,
        reaches={"medium", "high"},
        likes={"shiny", "bell", "ribbon"},
        sound="Clink! Flap-flap!",
        motion="pecking at shiny things",
        reveal_line="A magpie was pecking at the shiny bell garland and making it ring",
        tags={"bird", "shiny"},
    ),
    "ferret": Culprit(
        id="ferret",
        label="ferret",
        article="a",
        size=1,
        reaches={"low", "medium"},
        likes={"soft", "yarn"},
        sound="Rustle-rustle! Thump!",
        motion="tunneling through cloth",
        reveal_line="A ferret had wriggled into the soft blanket and knocked the lid from inside",
        tags={"ferret", "pet"},
    ),
}

PERCHES = {
    "rolling_chair": Perch(
        id="rolling_chair",
        label="rolling chair",
        phrase="onto the rolling chair",
        reaches={"medium", "high"},
        stability=1,
        creak="Eeek",
        tags={"chair", "wheels"},
    ),
    "crate_stack": Perch(
        id="crate_stack",
        label="stack of crates",
        phrase="onto the stack of crates",
        reaches={"high"},
        stability=0,
        creak="Creeeak",
        tags={"crate", "stack"},
    ),
    "ottoman": Perch(
        id="ottoman",
        label="ottoman",
        phrase="onto the ottoman",
        reaches={"medium"},
        stability=1,
        creak="Whuff",
        tags={"ottoman"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo", "Eli"]
TRAITS = ["careful", "cautious", "sensible", "patient", "curious", "thoughtful"]


KNOWLEDGE = {
    "kitten": [
        (
            "Why do kittens get into funny places?",
            "Kittens are curious and love to pounce on dangling or moving things. That is why a kitten can turn a quiet room into a tiny mystery very quickly.",
        )
    ],
    "puppy": [
        (
            "Why does a puppy make bumping sounds indoors?",
            "A puppy can wag, sniff, and tumble into blankets or baskets without meaning to. Soft things can hide a puppy, but the bumping noises give it away.",
        )
    ],
    "bird": [
        (
            "Why do some birds like shiny things?",
            "Some birds notice bright, glinty objects and peck at them. A shiny thing can make small clinks and rattles that sound mysterious in a room.",
        )
    ],
    "ferret": [
        (
            "Why do ferrets hide in soft places?",
            "Ferrets like to wriggle into cozy little spaces. Blankets and baskets can feel like tunnels to them.",
        )
    ],
    "chair": [
        (
            "Why is a rolling chair not safe to climb on?",
            "A rolling chair can slide away when your weight shifts. That makes it a bad place for feet, even if you only want one quick look.",
        )
    ],
    "crate": [
        (
            "Why is it unsafe to climb a stack of crates?",
            "A stack can tip or wobble because the pieces are not fixed together. If one crate shifts, the whole pile can tumble.",
        )
    ],
    "ottoman": [
        (
            "Should children stand on furniture to reach something?",
            "No. Furniture can wobble or slide, so it is safer to ask a grown-up for help and use the right step stool or ladder.",
        )
    ],
    "pet": [
        (
            "What should you do before reaching into a place where an animal is hiding?",
            "Go slowly and ask a grown-up for help first. A scared animal might wiggle, scratch, or dart away if it feels startled.",
        )
    ],
    "shiny": [
        (
            "What kind of sound can a bell or shiny hanging thing make?",
            "It can make a light clink or jingle when it moves. Those little sounds can help you figure out what is happening nearby.",
        )
    ],
}
KNOWLEDGE_ORDER = ["kitten", "puppy", "bird", "ferret", "chair", "crate", "ottoman", "pet", "shiny"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    project = f["project"]
    culprit = f["culprit_cfg"]
    spot = f["spot_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short whodunit for a 3-to-5-year-old where two children help furnish a room, '
        f'hear a strange noise in {spot.the}, and discover the culprit is {culprit.article} {culprit.label}. '
        f'Include the words "furnish" and "rascal".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle mystery where {a.id} wants to climb up for a look, but {b.id} stops {a.pronoun('object')} and the grown-up solves the puzzle safely.",
            f"Write a surprise story with sound effects and a cautionary lesson about keeping safe feet on the floor while a room is being furnished.",
        ]
    if outcome == "spilled":
        return [
            base,
            f"Tell a cautionary whodunit where {a.id} ignores the warning, something topples with a crash, and then the harmless culprit is revealed.",
            f"Write a cozy mystery with sound effects, a near-accident, and a warm ending that teaches children not to climb on wobbly furniture.",
        ]
    return [
        base,
        f"Tell a small mystery where {a.id} tries to peek, the perch feels risky, and a grown-up steps in before the room turns messy.",
        f"Write a child-facing whodunit with a surprising reveal, playful sounds, and a calm lesson about asking for help.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    project = f["project"]
    culprit = f["culprit_cfg"]
    spot = f["spot_cfg"]
    perch = f["perch_cfg"]
    pair = pair_noun(a, b, f.get("relation", "friends"))
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, helping their {parent.label_word} furnish {project.room}. The noisy mystery begins while they are trying to make the room feel special.",
        ),
        (
            "What made the room feel like a mystery?",
            f"They heard {culprit.sound.lower()} from {spot.phrase} and did not know what was hiding there. The sudden noise turned the furnishing job into a little whodunit.",
        ),
        (
            f"Why did {b.id} tell {a.id} not to climb?",
            f"{b.id} knew {perch.label} was not safe for climbing. In this story, the children could hear a mystery, but solving it on wobbly furniture might have made someone fall or the room turn messy.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What did {a.id} do after the warning?",
                f"{a.id} backed down and called for {parent.label_word} instead. That choice kept the mystery exciting without letting it become dangerous.",
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                f"What happened when {a.id} tried to climb?",
                f"{a.id} felt how risky it was and did not go farther. The moment showed why the warning mattered, even before anything crashed.",
            )
        )
    else:
        qa.append(
            (
                "What happened when the perch wobbled?",
                f"Part of the furnishing pile tipped over with a loud crash, and the room became messy for a moment. That happened because the mystery was chased in an unsafe way instead of a calm one.",
            )
        )
    qa.append(
        (
            "Who was really making the noise?",
            f"It was {culprit.article} {culprit.label}. The surprise is that the scary-sounding mystery came from a playful little rascal instead of something bad.",
        )
    )
    qa.append(
        (
            "How did the grown-up solve the problem?",
            f"{parent.label_word.capitalize()} {f['safe_method']}. Using the safe method let the grown-up find the culprit without climbing on the wrong thing or making the mystery worse.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"They finished furnishing the room, and it felt cozy at last. The ending image shows that the mystery was solved and the room could become welcoming again.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["culprit_cfg"].tags) | set(world.facts["perch_cfg"].tags)
    if "shiny" in world.facts["project"].tags:
        tags.add("shiny")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    project: str
    culprit: str
    spot: str
    perch: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        project="reading_nook",
        culprit="kitten",
        spot="curtain_rod",
        perch="crate_stack",
        instigator="Ben",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
    ),
    StoryParams(
        project="guest_room",
        culprit="puppy",
        spot="window_seat",
        perch="ottoman",
        instigator="Ava",
        instigator_gender="girl",
        cautioner="Theo",
        cautioner_gender="boy",
        parent="father",
        trait="patient",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
    ),
    StoryParams(
        project="music_corner",
        culprit="magpie",
        spot="bookcase_top",
        perch="rolling_chair",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Mia",
        cautioner_gender="girl",
        parent="mother",
        trait="curious",
        delay=1,
        instigator_age=6,
        cautioner_age=6,
        relation="friends",
    ),
    StoryParams(
        project="reading_nook",
        culprit="ferret",
        spot="window_seat",
        perch="ottoman",
        instigator="Rose",
        instigator_gender="girl",
        cautioner="Lucy",
        cautioner_gender="girl",
        parent="father",
        trait="cautious",
        delay=0,
        instigator_age=4,
        cautioner_age=6,
        relation="siblings",
    ),
]


def explain_rejection(project: Project, culprit: Culprit, spot: Spot, perch: Perch) -> str:
    if not (project.tags & culprit.likes):
        return (
            f"(No story: {culprit.article} {culprit.label} has no good reason to be in {spot.the} "
            f"during this furnishing project. Pick a project with the soft or shiny thing that would attract it.)"
        )
    if culprit.size > spot.capacity:
        return (
            f"(No story: {culprit.article} {culprit.label} is too big to fit in {spot.the}, "
            f"so the mystery would not make sense there.)"
        )
    if spot.level not in culprit.reaches:
        return (
            f"(No story: {culprit.article} {culprit.label} would not reasonably reach {spot.the}.)"
        )
    if not perch_can_reach(perch, spot):
        return (
            f"(No story: {perch.label} would not even reach {spot.the}, so the tempting wrong move does not fit this mystery.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
likes_match(P, C) :- project_tag(P, T), culprit_likes(C, T).
fit(C, S) :- culprit_size(C, Cz), spot_capacity(S, Sz), Cz <= Sz.
reachable(C, S) :- culprit_reach(C, L), spot_level(S, L).
tempting(Pe, S) :- perch(Pe), perch_reach(Pe, L), spot_level(S, L).

valid(P, C, S, Pe) :- project(P), culprit(C), spot(S), perch(Pe),
                      likes_match(P, C), fit(C, S), reachable(C, S), tempting(Pe, S).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

needed(R + D) :- chosen_spot(S), spot_risk(S, R), delay(D).
contained :- chosen_perch(Pe), perch_stability(Pe, St), needed(N), St >= N.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(spilled) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for project_id, project in PROJECTS.items():
        lines.append(asp.fact("project", project_id))
        for tag in sorted(project.tags):
            lines.append(asp.fact("project_tag", project_id, tag))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        lines.append(asp.fact("culprit_size", culprit_id, culprit.size))
        for level in sorted(culprit.reaches):
            lines.append(asp.fact("culprit_reach", culprit_id, level))
        for tag in sorted(culprit.likes):
            lines.append(asp.fact("culprit_likes", culprit_id, tag))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        lines.append(asp.fact("spot_level", spot_id, spot.level))
        lines.append(asp.fact("spot_capacity", spot_id, spot.capacity))
        lines.append(asp.fact("spot_risk", spot_id, spot.risk))
    for perch_id, perch in PERCHES.items():
        lines.append(asp.fact("perch", perch_id))
        lines.append(asp.fact("perch_stability", perch_id, perch.stability))
        for level in sorted(perch.reaches):
            lines.append(asp.fact("perch_reach", perch_id, level))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_spot", params.spot),
            asp.fact("chosen_perch", params.perch),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a cozy-room whodunit with a mystery noise, a tempting unsafe climb, and a surprising culprit."
    )
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra time before the grown-up steps in")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.project and args.culprit and args.spot and args.perch:
        if (args.project, args.culprit, args.spot, args.perch) not in valid_combos():
            raise StoryError(
                explain_rejection(
                    project=PROJECTS[args.project],
                    culprit=CULPRITS[args.culprit],
                    spot=SPOTS[args.spot],
                    perch=PERCHES[args.perch],
                )
            )

    combos = [
        combo
        for combo in valid_combos()
        if (args.project is None or combo[0] == args.project)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.spot is None or combo[2] == args.spot)
        and (args.perch is None or combo[3] == args.perch)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    project_id, culprit_id, spot_id, perch_id = rng.choice(sorted(combos))
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)

    return StoryParams(
        project=project_id,
        culprit=culprit_id,
        spot=spot_id,
        perch=perch_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        parent=parent,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.perch not in PERCHES:
        raise StoryError(f"(Unknown perch: {params.perch})")
    if (params.project, params.culprit, params.spot, params.perch) not in valid_combos():
        raise StoryError(
            explain_rejection(
                project=PROJECTS[params.project],
                culprit=CULPRITS[params.culprit],
                spot=SPOTS[params.spot],
                perch=PERCHES[params.perch],
            )
        )

    world = tell(
        project=PROJECTS[params.project],
        culprit=CULPRITS[params.culprit],
        spot=SPOTS[params.spot],
        perch=PERCHES[params.perch],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        parent_type=params.parent,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
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

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story or "rascal" not in sample.story or "furnish" not in sample.story:
            raise StoryError("(Smoke test failed: story text missing required content.)")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover - used only in CLI verification
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (project, culprit, spot, perch) combos:\n")
        for project_id, culprit_id, spot_id, perch_id in combos:
            print(f"  {project_id:12} {culprit_id:8} {spot_id:13} {perch_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.project}: {p.culprit} in {p.spot} ({p.perch}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
