#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bound_farmyard_surprise_heartwarming.py
==================================================================

A standalone story world for a heartwarming farmyard surprise.

Premise
-------
A child in the farmyard plans a tiny breakfast surprise for a favorite mother
animal. But something in the yard blocks or frightens the animal before she can
reach the treat. A calm grown-up helps the child choose the sensible fix. Once
the path feels safe, the mother comes forward -- and then a hidden baby animal
bounds out after her, turning the ending into a warm surprise.

Run it
------
python storyworlds/worlds/gpt-5.4/bound_farmyard_surprise_heartwarming.py
python storyworlds/worlds/gpt-5.4/bound_farmyard_surprise_heartwarming.py --animal sheep --treat clover_bundle --obstacle puddle --response lay_straw
python storyworlds/worlds/gpt-5.4/bound_farmyard_surprise_heartwarming.py --animal pony --treat clover_bundle
python storyworlds/worlds/gpt-5.4/bound_farmyard_surprise_heartwarming.py --all
python storyworlds/worlds/gpt-5.4/bound_farmyard_surprise_heartwarming.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/bound_farmyard_surprise_heartwarming.py --verify
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"pony", "goat", "sheep", "cow", "foal", "kid_goat", "lamb", "calf"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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


@dataclass
class AnimalFamily:
    id: str
    mother_type: str
    mother_label: str
    baby_type: str
    baby_label: str
    call_sound: str
    move_verb: str
    baby_move: str
    surprise_noun: str
    safe_treats: set[str] = field(default_factory=set)
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
class Treat:
    id: str
    label: str
    phrase: str
    smell: str
    safe_for: set[str] = field(default_factory=set)
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
class Obstacle:
    id: str
    label: str
    phrase: str
    detail: str
    fear_text: str
    kind: str
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
class Response:
    id: str
    sense: int
    clears: set[str] = field(default_factory=set)
    text: str = ""
    qa_text: str = ""
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


def _r_obstacle_holds(world: World) -> list[str]:
    out: list[str] = []
    obstacle = world.get("obstacle")
    mother = world.get("mother")
    if obstacle.meters["active"] < THRESHOLD:
        return out
    sig = ("obstacle_holds", obstacle.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    mother.memes["hesitant"] += 1
    mother.meters["stopped"] += 1
    out.append("__hesitation__")
    return out


def _r_safe_path(world: World) -> list[str]:
    out: list[str] = []
    obstacle = world.get("obstacle")
    mother = world.get("mother")
    child = world.get("child")
    if obstacle.meters["active"] >= THRESHOLD:
        return out
    if child.meters["offering_treat"] < THRESHOLD:
        return out
    sig = ("safe_path", mother.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    mother.meters["approaching"] += 1
    mother.meters["stopped"] = 0.0
    mother.memes["trust"] += 1
    out.append("__approach__")
    return out


def _r_baby_follows(world: World) -> list[str]:
    out: list[str] = []
    mother = world.get("mother")
    baby = world.get("baby")
    if mother.meters["approaching"] < THRESHOLD:
        return out
    if baby.attrs.get("hidden", 0) != 1:
        return out
    sig = ("baby_follows", baby.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    baby.attrs["hidden"] = 0
    baby.meters["approaching"] += 1
    baby.memes["surprise"] += 1
    out.append("__surprise__")
    return out


CAUSAL_RULES = [
    Rule(name="obstacle_holds", tag="physical", apply=_r_obstacle_holds),
    Rule(name="safe_path", tag="physical", apply=_r_safe_path),
    Rule(name="baby_follows", tag="social", apply=_r_baby_follows),
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


ANIMALS = {
    "sheep": AnimalFamily(
        id="sheep",
        mother_type="sheep",
        mother_label="ewe",
        baby_type="lamb",
        baby_label="lamb",
        call_sound="baa",
        move_verb="picked her way",
        baby_move="bound",
        surprise_noun="woolly surprise",
        safe_treats={"clover_bundle", "apple_slices"},
        tags={"sheep", "lamb"},
    ),
    "goat": AnimalFamily(
        id="goat",
        mother_type="goat",
        mother_label="goat",
        baby_type="kid_goat",
        baby_label="kid",
        call_sound="maa",
        move_verb="stepped neatly",
        baby_move="bound",
        surprise_noun="spring surprise",
        safe_treats={"apple_slices", "hay_basket"},
        tags={"goat", "kid"},
    ),
    "pony": AnimalFamily(
        id="pony",
        mother_type="pony",
        mother_label="pony",
        baby_type="foal",
        baby_label="foal",
        call_sound="nickered",
        move_verb="clopped softly",
        baby_move="bound",
        surprise_noun="long-legged surprise",
        safe_treats={"carrot_slices", "apple_slices"},
        tags={"pony", "foal"},
    ),
    "cow": AnimalFamily(
        id="cow",
        mother_type="cow",
        mother_label="cow",
        baby_type="calf",
        baby_label="calf",
        call_sound="lowed",
        move_verb="ambled slowly",
        baby_move="bound",
        surprise_noun="small hoofed surprise",
        safe_treats={"hay_basket", "apple_slices"},
        tags={"cow", "calf"},
    ),
}

TREATS = {
    "clover_bundle": Treat(
        id="clover_bundle",
        label="clover bundle",
        phrase="a sweet bundle of clover",
        smell="smelled green and sunny",
        safe_for={"sheep"},
        tags={"clover"},
    ),
    "apple_slices": Treat(
        id="apple_slices",
        label="apple slices",
        phrase="a little tin of apple slices",
        smell="smelled crisp and sweet",
        safe_for={"sheep", "goat", "pony", "cow"},
        tags={"apple"},
    ),
    "carrot_slices": Treat(
        id="carrot_slices",
        label="carrot slices",
        phrase="a small bowl of carrot slices",
        smell="smelled fresh from the garden",
        safe_for={"pony"},
        tags={"carrot"},
    ),
    "hay_basket": Treat(
        id="hay_basket",
        label="hay basket",
        phrase="a neat basket of soft hay",
        smell="smelled warm and dry",
        safe_for={"goat", "cow"},
        tags={"hay"},
    ),
}

OBSTACLES = {
    "puddle": Obstacle(
        id="puddle",
        label="puddle",
        phrase="a cold puddle",
        detail="Rain from the night before had left a cold puddle shining between the pen and the open yard.",
        fear_text="She stopped at the water and would not step through the splashy patch.",
        kind="wet",
        tags={"puddle", "wet"},
    ),
    "flapping_tarp": Obstacle(
        id="flapping_tarp",
        label="flapping tarp",
        phrase="a loose blue tarp",
        detail="A loose blue tarp had come half untied on the fence, and every puff of wind made it flap and snap.",
        fear_text="Each flap made her ears twitch, and she stayed back where the shadows felt safer.",
        kind="motion",
        tags={"tarp", "wind"},
    ),
    "latched_gate": Obstacle(
        id="latched_gate",
        label="latched gate",
        phrase="a latched gate",
        detail="The small gate between the pen and the breakfast corner was still latched shut.",
        fear_text="She could smell the treat, but the gate blocked the easy way into the yard.",
        kind="barrier",
        tags={"gate"},
    ),
}

RESPONSES = {
    "lay_straw": Response(
        id="lay_straw",
        sense=3,
        clears={"puddle"},
        text="spread a dry line of straw over the puddle until the path looked soft and easy",
        qa_text="spread dry straw over the puddle to make a safe path",
        tags={"straw", "dry_path"},
    ),
    "tie_tarp": Response(
        id="tie_tarp",
        sense=3,
        clears={"flapping_tarp"},
        text="walked over to the fence and tied the loose tarp still so it stopped snapping in the wind",
        qa_text="tied the tarp still so it would stop flapping",
        tags={"tarp", "quiet"},
    ),
    "lift_latch": Response(
        id="lift_latch",
        sense=3,
        clears={"latched_gate"},
        text="lifted the wooden latch and swung the gate open wide",
        qa_text="lifted the latch and opened the gate",
        tags={"gate", "open"},
    ),
    "pull_hard": Response(
        id="pull_hard",
        sense=1,
        clears=set(),
        text="pulled hard on the lead rope and tried to drag the animal closer",
        qa_text="pulled hard on the rope",
        tags={"rough"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Ruby"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo", "Eli"]
TRAITS = ["gentle", "eager", "cheerful", "patient", "bright", "kind"]


def treat_suits(animal_id: str, treat_id: str) -> bool:
    return animal_id in TREATS[treat_id].safe_for and treat_id in ANIMALS[animal_id].safe_treats


def response_solves(obstacle_id: str, response_id: str) -> bool:
    return obstacle_id in RESPONSES[response_id].clears


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    sensible = {r.id for r in sensible_responses()}
    for animal_id in ANIMALS:
        for treat_id in TREATS:
            if not treat_suits(animal_id, treat_id):
                continue
            for obstacle_id in OBSTACLES:
                for response_id in sensible:
                    if response_solves(obstacle_id, response_id):
                        combos.append((animal_id, treat_id, obstacle_id, response_id))
    return sorted(combos)


def explain_treat(animal_id: str, treat_id: str) -> str:
    return (
        f"(No story: {TREATS[treat_id].label} is not a sensible farmyard treat for the "
        f"{ANIMALS[animal_id].mother_label} here. Pick one of: "
        f"{', '.join(sorted(ANIMALS[animal_id].safe_treats))}.)"
    )


def explain_response(obstacle_id: str, response_id: str) -> str:
    response = RESPONSES[response_id]
    if response.sense < SENSE_MIN:
        better = ", ".join(sorted(r.id for r in sensible_responses()))
        return (
            f"(Refusing response '{response_id}': it scores too low on common sense "
            f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
        )
    return (
        f"(No story: {response_id} does not sensibly solve the {obstacle_id.replace('_', ' ')}.)"
    )


def predict_arrival(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    return {
        "mother_approaches": sim.get("mother").meters["approaching"] >= THRESHOLD,
        "baby_revealed": sim.get("baby").attrs.get("hidden", 0) == 0,
    }


def introduce(world: World, child: Entity, helper: Entity, family: AnimalFamily, treat: Treat) -> None:
    child.memes["joy"] += 1
    world.say(
        f"Early one golden morning, {child.id} carried {treat.phrase} into the farmyard. "
        f"It {treat.smell}, and {child.pronoun()} could hardly keep from smiling."
    )
    world.say(
        f'"Let\'s make a little breakfast surprise for the {family.mother_label}," '
        f"{helper.label_word} said. {child.id} nodded and held the treat basket close."
    )


def prepare_corner(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} set the treat by an upside-down crate near the sunny side of the yard, "
        f"where the hens scratched and the morning light warmed the straw."
    )


def show_obstacle(world: World, obstacle: Obstacle, mother: Entity) -> None:
    mother.meters["waiting"] += 1
    world.say(obstacle.detail)
    propagate(world, narrate=False)
    world.say(
        f"The {mother.label} looked toward the treat and {mother.attrs['call']}. "
        f"{obstacle.fear_text}"
    )


def child_rushes(world: World, child: Entity, mother: Entity) -> None:
    child.memes["worry"] += 1
    mother.memes["hesitant"] += 1
    world.say(
        f"{child.id} took one quick step forward, almost ready to hurry the {mother.label} along, "
        f"but {child.pronoun('possessive')} shoes stopped in the straw."
    )


def helper_guides(world: World, helper: Entity, child: Entity, response: Response, obstacle: Obstacle) -> None:
    pred = predict_arrival(world)
    world.facts["predicted_mother_approaches"] = pred["mother_approaches"]
    world.say(
        f'"No pulling," {helper.label_word} said softly. "If we make the way feel safe, '
        f'she will choose to come on her own."'
    )
    world.say(
        f"Then {helper.pronoun()} {response.text}. The farmyard grew calmer at once."
    )


def offer_treat(world: World, child: Entity, mother: Entity, treat: Treat, family: AnimalFamily) -> None:
    child.meters["offering_treat"] += 1
    world.say(
        f"{child.id} held out the {treat.label} with both hands and stood very still. "
        f'"Here you are," {child.pronoun()} whispered.'
    )
    propagate(world, narrate=False)
    if mother.meters["approaching"] >= THRESHOLD:
        world.say(
            f"The {mother.label} {family.move_verb} into the open yard, nose first, "
            f"drawn by the good smell and the quiet path."
        )


def surprise_reveal(world: World, child: Entity, helper: Entity, baby: Entity, family: AnimalFamily) -> None:
    if baby.meters["approaching"] < THRESHOLD:
        return
    child.memes["surprise"] += 1
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"But that was not the whole surprise. From behind the hay bales, a tiny {baby.label} "
        f"gave a high little cry and {family.baby_move} into the light after her."
    )
    world.say(
        f"{child.id}'s mouth made a round O. Then {child.pronoun()} laughed, and even "
        f"the old rooster seemed to stand taller to see the new {family.surprise_noun}."
    )


def ending(world: World, child: Entity, helper: Entity, mother: Entity, baby: Entity, family: AnimalFamily) -> None:
    child.memes["relief"] += 1
    child.memes["love"] += 1
    mother.memes["trust"] += 1
    baby.memes["trust"] += 1
    world.say(
        f"Soon the {mother.label} was eating from the basket while the {baby.label} nosed the straw near "
        f"{child.id}'s boots."
    )
    world.say(
        f'{helper.label_word.capitalize()} rested a hand on {child.id}\'s shoulder. '
        f'"The best surprises come gently," {helper.pronoun()} said.'
    )
    world.say(
        f"{child.id} looked around the bright farmyard and knew the morning felt bigger now -- "
        f"warmer, quieter, and full of welcome."
    )


def tell(
    family: AnimalFamily,
    treat: Treat,
    obstacle: Obstacle,
    response: Response,
    *,
    child_name: str = "Lily",
    child_gender: str = "girl",
    helper_type: str = "grandmother",
    trait: str = "gentle",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        attrs={"trait": trait},
        tags={"child"},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type="mother" if helper_type == "grandmother" else "father",
        label=helper_type,
        role="helper",
        attrs={"helper_type": helper_type},
        tags={"grownup"},
    ))
    mother = world.add(Entity(
        id="mother",
        kind="character",
        type=family.mother_type,
        label=family.mother_label,
        role="mother_animal",
        attrs={"call": family.call_sound},
        tags=set(family.tags),
    ))
    baby = world.add(Entity(
        id="baby",
        kind="character",
        type=family.baby_type,
        label=family.baby_label,
        role="baby_animal",
        attrs={"hidden": 1},
        tags=set(family.tags),
    ))
    obstacle_ent = world.add(Entity(
        id="obstacle",
        kind="thing",
        type="obstacle",
        label=obstacle.label,
        role="obstacle",
        tags=set(obstacle.tags),
    ))
    obstacle_ent.meters["active"] = 1.0
    child.meters["offering_treat"] = 0.0
    mother.meters["waiting"] = 0.0
    mother.meters["approaching"] = 0.0
    mother.meters["stopped"] = 0.0
    baby.meters["approaching"] = 0.0
    mother.memes["hesitant"] = 0.0
    mother.memes["trust"] = 0.0
    baby.memes["surprise"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["surprise"] = 0.0

    world.facts.update(
        child=child,
        helper=helper,
        family=family,
        treat=treat,
        obstacle_cfg=obstacle,
        response=response,
        mother=mother,
        baby=baby,
        helper_type=helper_type,
    )

    introduce(world, child, helper, family, treat)
    prepare_corner(world, child)

    world.para()
    show_obstacle(world, obstacle, mother)
    child_rushes(world, child, mother)

    world.para()
    helper_guides(world, helper, child, response, obstacle)
    obstacle_ent.meters["active"] = 0.0
    offer_treat(world, child, mother, treat, family)
    surprise_reveal(world, child, helper, baby, family)

    world.para()
    ending(world, child, helper, mother, baby, family)

    world.facts.update(
        path_cleared=obstacle_ent.meters["active"] < THRESHOLD,
        mother_arrived=mother.meters["approaching"] >= THRESHOLD,
        baby_revealed=baby.attrs.get("hidden", 0) == 0,
        ending="surprise" if baby.attrs.get("hidden", 0) == 0 else "plain",
    )
    return world


@dataclass
class StoryParams:
    animal: str
    treat: str
    obstacle: str
    response: str
    child_name: str
    child_gender: str
    helper_type: str
    trait: str
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
    "farmyard": [
        (
            "What is a farmyard?",
            "A farmyard is the open space around a barn, pens, and sheds where farm animals and people move from place to place."
        )
    ],
    "puddle": [
        (
            "Why might an animal stop at a puddle?",
            "Some animals do not like stepping into cold splashes when they are unsure of the ground. A dry path can help them feel safe enough to move."
        )
    ],
    "tarp": [
        (
            "Why can a flapping tarp scare animals?",
            "A tarp can snap and wave suddenly in the wind. Fast movement and sharp sounds can make an animal step back."
        )
    ],
    "gate": [
        (
            "What does a gate do on a farm?",
            "A gate opens and closes a path between pens or yards. When it stays latched, animals cannot walk through easily."
        )
    ],
    "clover": [
        (
            "What is clover?",
            "Clover is a soft green plant that some grazing animals like to nibble. It smells fresh and sweet."
        )
    ],
    "apple": [
        (
            "Why do farm animals sometimes like apple slices?",
            "Apple slices smell sweet and juicy, so they can be a pleasant treat in small pieces for some farm animals."
        )
    ],
    "carrot": [
        (
            "Why are carrot slices a common pony treat?",
            "Carrots are crisp and easy to bite, and many ponies enjoy them. People still give them in sensible little pieces."
        )
    ],
    "hay": [
        (
            "What is hay for?",
            "Hay is dried grass that animals can eat, and it also smells warm and familiar in a barn or yard."
        )
    ],
    "lamb": [
        (
            "What is a lamb?",
            "A lamb is a baby sheep. Lambs are often springtime babies and can move in quick bouncy hops."
        )
    ],
    "kid": [
        (
            "What is a kid on a farm?",
            "A kid is a baby goat. Baby goats are lively and often spring about when they feel safe and playful."
        )
    ],
    "foal": [
        (
            "What is a foal?",
            "A foal is a baby horse or pony. Foals have long legs and often stay close to their mothers."
        )
    ],
    "calf": [
        (
            "What is a calf?",
            "A calf is a baby cow. Calves learn by following their mothers and watching where to step."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "farmyard",
    "puddle",
    "tarp",
    "gate",
    "clover",
    "apple",
    "carrot",
    "hay",
    "lamb",
    "kid",
    "foal",
    "calf",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    family = f["family"]
    obstacle = f["obstacle_cfg"]
    treat = f["treat"]
    return [
        f'Write a heartwarming farmyard story for a 3-to-5-year-old that includes the word "bound" and ends with a surprise baby {family.baby_label}.',
        f"Tell a gentle story where {child.id} prepares {treat.phrase} for a {family.mother_label}, but {obstacle.label.replace('_', ' ')} keeps her back until a grown-up helps.",
        f"Write a simple farmyard story with a calm problem, a kind fix, and a sweet surprise ending when a baby animal comes out into the yard."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    family = f["family"]
    treat = f["treat"]
    obstacle = f["obstacle_cfg"]
    response = f["response"]
    helper_word = helper.label
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {helper_word}, and a {family.mother_label} in the farmyard. They are trying to make a small breakfast surprise feel safe and welcoming."
        ),
        (
            f"Why did the {family.mother_label} stay back at first?",
            f"She stayed back because of the {obstacle.label.replace('_', ' ')}, which made the way feel unsafe or blocked. She could smell the treat, but the path did not feel calm enough yet."
        ),
        (
            f"How did {helper_word} help?",
            f"{helper_word.capitalize()} {response.qa_text}. That changed the farmyard from a worrying place into one the {family.mother_label} could trust."
        ),
        (
            f"Why did {child.id} stand still with the {treat.label}?",
            f"{child.id} stood still so the {family.mother_label} would not feel chased or rushed. The quiet body and the good smell together helped her choose to come forward."
        ),
    ]
    if f.get("baby_revealed"):
        qa.append(
            (
                "What was the surprise at the end?",
                f"The surprise was that a baby {family.baby_label} had been hidden behind the hay bales and then came out after its mother. It made the morning feel suddenly bigger and happier for everyone."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"farmyard"}
    obstacle = f["obstacle_cfg"]
    treat = f["treat"]
    family = f["family"]
    tags |= set(obstacle.tags)
    tags |= set(treat.tags)
    if family.baby_label == "lamb":
        tags.add("lamb")
    elif family.baby_label == "kid":
        tags.add("kid")
    elif family.baby_label == "foal":
        tags.add("foal")
    elif family.baby_label == "calf":
        tags.add("calf")
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
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        shown_attrs = {k: v for k, v in ent.attrs.items() if v}
        if shown_attrs:
            parts.append(f"attrs={shown_attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        animal="sheep",
        treat="clover_bundle",
        obstacle="puddle",
        response="lay_straw",
        child_name="Lily",
        child_gender="girl",
        helper_type="grandmother",
        trait="gentle",
    ),
    StoryParams(
        animal="goat",
        treat="hay_basket",
        obstacle="flapping_tarp",
        response="tie_tarp",
        child_name="Ben",
        child_gender="boy",
        helper_type="grandfather",
        trait="cheerful",
    ),
    StoryParams(
        animal="pony",
        treat="carrot_slices",
        obstacle="latched_gate",
        response="lift_latch",
        child_name="Nora",
        child_gender="girl",
        helper_type="grandmother",
        trait="patient",
    ),
    StoryParams(
        animal="cow",
        treat="hay_basket",
        obstacle="puddle",
        response="lay_straw",
        child_name="Max",
        child_gender="boy",
        helper_type="grandfather",
        trait="kind",
    ),
]


ASP_RULES = r"""
safe_treat(A,T) :- animal(A), treat(T), treat_ok(A,T).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
fixes(O,R) :- obstacle(O), response(R), clears(R,O).

valid(A,T,O,R) :- animal(A), safe_treat(A,T), obstacle(O), response(R), sensible(R), fixes(O,R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for animal_id, family in ANIMALS.items():
        lines.append(asp.fact("animal", animal_id))
        for treat_id in sorted(family.safe_treats):
            lines.append(asp.fact("treat_ok", animal_id, treat_id))
    for treat_id in TREATS:
        lines.append(asp.fact("treat", treat_id))
    for obstacle_id in OBSTACLES:
        lines.append(asp.fact("obstacle", obstacle_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        for obstacle_id in sorted(response.clears):
            lines.append(asp.fact("clears", response_id, obstacle_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    py_sense = {r.id for r in sensible_responses()}
    cl_sense = set(asp_sensible())
    if py_sense == cl_sense:
        print(f"OK: sensible responses match ({sorted(py_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: python={sorted(py_sense)} clingo={sorted(cl_sense)}")

    try:
        sample = generate(CURATED[0])
        with io.StringIO() as buf:
            old = sys.stdout
            sys.stdout = buf
            try:
                emit(sample, trace=True, qa=True, header="### smoke")
            finally:
                sys.stdout = old
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generation/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming farmyard surprise world. Unspecified choices are chosen at random from sensible combinations."
    )
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list sensible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.animal and args.treat and not treat_suits(args.animal, args.treat):
        raise StoryError(explain_treat(args.animal, args.treat))
    if args.obstacle and args.response and not response_solves(args.obstacle, args.response):
        raise StoryError(explain_response(args.obstacle, args.response))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.obstacle or "obstacle", args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.animal is None or combo[0] == args.animal)
        and (args.treat is None or combo[1] == args.treat)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.response is None or combo[3] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    animal_id, treat_id, obstacle_id, response_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        animal=animal_id,
        treat=treat_id,
        obstacle=obstacle_id,
        response=response_id,
        child_name=child_name,
        child_gender=gender,
        helper_type=helper_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.animal not in ANIMALS:
        raise StoryError(f"Unknown animal: {params.animal}")
    if params.treat not in TREATS:
        raise StoryError(f"Unknown treat: {params.treat}")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"Unknown obstacle: {params.obstacle}")
    if params.response not in RESPONSES:
        raise StoryError(f"Unknown response: {params.response}")
    if not treat_suits(params.animal, params.treat):
        raise StoryError(explain_treat(params.animal, params.treat))
    if RESPONSES[params.response].sense < SENSE_MIN or not response_solves(params.obstacle, params.response):
        raise StoryError(explain_response(params.obstacle, params.response))

    world = tell(
        ANIMALS[params.animal],
        TREATS[params.treat],
        OBSTACLES[params.obstacle],
        RESPONSES[params.response],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper_type,
        trait=params.trait,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (animal, treat, obstacle, response) combos:\n")
        for animal_id, treat_id, obstacle_id, response_id in combos:
            print(f"  {animal_id:6} {treat_id:14} {obstacle_id:13} {response_id}")
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.animal}, {p.obstacle}, {p.response}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
