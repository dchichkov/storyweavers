#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/posy_husband_foreshadowing_lesson_learned_bedtime_story.py
=====================================================================================

A standalone storyworld for a gentle bedtime tale about a posy, a husband, and a
small lesson learned before sleep. The world models a simple household problem:
one grown-up arranges a bedtime posy for a child's room, but an unstable cup set
in a breezy place can spill. A calm husband notices the signs, a small mishap
happens or is prevented, and the family learns to choose the steadier, safer
spot.

The simulation uses typed entities with physical meters and emotional memes.
Foreshadowing comes from the state of the room -- a draft, a wobble, a low rumble
of weather -- not from a frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4/posy_husband_foreshadowing_lesson_learned_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/posy_husband_foreshadowing_lesson_learned_bedtime_story.py --flower daisies --container teacup --spot windowsill
    python storyworlds/worlds/gpt-5.4/posy_husband_foreshadowing_lesson_learned_bedtime_story.py --container basket
    python storyworlds/worlds/gpt-5.4/posy_husband_foreshadowing_lesson_learned_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/posy_husband_foreshadowing_lesson_learned_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/posy_husband_foreshadowing_lesson_learned_bedtime_story.py --verify
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
CAREFUL_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"woman", "mother", "wife", "girl"}
        male = {"man", "father", "husband", "boy"}
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
class Flower:
    id: str
    label: str
    scent: str
    color: str
    stem: str
    bedtime_image: str
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
class Container:
    id: str
    label: str
    phrase: str
    stable: bool
    water_safe: bool
    wobble_text: str
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
class Spot:
    id: str
    label: str
    phrase: str
    breezy: bool
    near_bed: bool
    hush_text: str
    foreshadow_text: str
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
class Fix:
    id: str
    label: str
    phrase: str
    careful: int
    works_on_breeze: bool
    move_text: str
    qa_text: str
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


def _r_risk(world: World) -> list[str]:
    posy = world.get("posy")
    room = world.get("room")
    container = world.get("container")
    if posy.attrs.get("breezy") and not container.attrs.get("stable"):
        sig = ("risk",)
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["spill_risk"] += 1
            posy.memes["uneasy"] += 1
    return []


def _r_spill(world: World) -> list[str]:
    posy = world.get("posy")
    room = world.get("room")
    if posy.meters["tipped"] < THRESHOLD:
        return []
    sig = ("spill",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["wetness"] += 1
    room.meters["mess"] += 1
    posy.meters["droop"] += 1
    for eid in ("wife", "husband", "child"):
        if eid in world.entities:
            world.get(eid).memes["worry"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="risk", tag="physical", apply=_r_risk),
    Rule(name="spill", tag="physical", apply=_r_spill),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                produced.extend(out)
                changed = True
            else:
                # detect silent meter changes by comparing fired growth through repeated pass
                pass
        # if any new fact fired on this pass, another pass may matter
        if produced:
            changed = False
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def hazard_at_risk(container: Container, spot: Spot) -> bool:
    return spot.breezy and not container.stable


def sensible_fixes() -> list[Fix]:
    return [fx for fx in FIXES.values() if fx.careful >= CAREFUL_MIN]


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda fx: fx.careful)


def spill_happens(container: Container, spot: Spot, wind: int) -> bool:
    if not hazard_at_risk(container, spot):
        return False
    return wind >= 1


def fix_prevents(fix: Fix, spot: Spot) -> bool:
    if spot.breezy and not fix.works_on_breeze:
        return False
    return True


def predict_spill(world: World) -> dict:
    sim = world.copy()
    container = sim.get("container")
    spot = sim.get("spot")
    posy = sim.get("posy")
    posy.attrs["breezy"] = bool(spot.attrs.get("breezy"))
    container.attrs["stable"] = bool(container.attrs.get("stable"))
    propagate(sim, narrate=False)
    if sim.get("room").meters["spill_risk"] >= THRESHOLD:
        posy.meters["tipped"] += 1
        propagate(sim, narrate=False)
    return {
        "risk": sim.get("room").meters["spill_risk"],
        "wetness": sim.get("room").meters["wetness"],
    }


def introduce_evening(world: World, wife: Entity, husband: Entity, child: Entity,
                      flower: Flower, spot: Spot) -> None:
    wife.memes["care"] += 1
    husband.memes["care"] += 1
    child.memes["sleepy"] += 1
    world.say(
        f"In a little lamp-lit house, {wife.id} wanted the nursery to feel soft and sleepy "
        f"before {child.id} went to bed."
    )
    world.say(
        f"She picked a small posy of {flower.label}, and the {flower.scent} smell drifted "
        f"through the hall. {husband.id}, her husband, smiled when he saw the flowers."
    )
    world.say(
        f"The room already felt hushed. {spot.hush_text}."
    )


def choose_place(world: World, wife: Entity, flower: Flower, container: Container,
                 spot: Spot) -> None:
    posy = world.get("posy")
    posy.attrs["breezy"] = bool(spot.breezy)
    container_ent = world.get("container")
    spot_ent = world.get("spot")
    container_ent.attrs["stable"] = bool(container.stable)
    spot_ent.attrs["breezy"] = bool(spot.breezy)
    wife.memes["pleased"] += 1
    world.say(
        f'"These {flower.label} will look lovely here," {wife.id} whispered. '
        f"She set the posy in {container.phrase} on {spot.phrase}."
    )


def foreshadow(world: World, husband: Entity, container: Container, spot: Spot) -> None:
    pred = predict_spill(world)
    world.facts["predicted_risk"] = pred["risk"]
    husband.memes["notice"] += 1
    world.say(spot.foreshadow_text)
    if pred["risk"] >= THRESHOLD:
        husband.memes["caution"] += 1
        world.say(
            f"{husband.id} noticed that {container.wobble_text}. "
            f'He said softly, "That little posy may not stay put there all night."'
        )
    else:
        world.say(
            f"{husband.id} listened to the room for a moment, but nothing there seemed likely to bother the flowers."
        )


def warn(world: World, husband: Entity, spot: Spot, container: Container) -> None:
    if world.facts.get("predicted_risk", 0) < THRESHOLD:
        return
    world.say(
        f'"The breeze from {spot.label} could tip {container.phrase}," {husband.pronoun()} '
        f"said. \"We still have time to move it before the house grows sleepy.\""
    )


def decide_ignore(world: World, wife: Entity, child: Entity) -> None:
    wife.memes["hurry"] += 1
    child.memes["sleepier"] += 1
    world.say(
        f"But the blankets were warm, and {child.id} was already rubbing {child.pronoun('possessive')} eyes."
    )
    world.say(
        f'"Just for tonight," {wife.id} said. "I think it will be fine."'
    )


def decide_move_early(world: World, wife: Entity, husband: Entity, fix: Fix) -> None:
    wife.memes["trust"] += 1
    husband.memes["relief"] += 1
    world.say(
        f"{wife.id} looked again, then nodded. "
        f'"You are right," she said to her husband. "A bedtime room should feel calm, not tippy."'
    )
    world.say(f"{fix.move_text}.")
    world.facts["moved_early"] = True


def night_turn(world: World, flower: Flower, container: Container, spot: Spot) -> None:
    posy = world.get("posy")
    if not spill_happens(container, spot, int(world.facts["wind"])):
        world.say(
            f"The night stayed still. The {flower.label} kept their little heads up, and the room stayed dry and quiet."
        )
        return
    posy.meters["tipped"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Later, when the house had gone almost completely quiet, a cool puff slipped in from {spot.label}."
    )
    world.say(
        f"The posy leaned, {container.wobble_text}, and then a tiny splash darkened the floor beside the bed."
    )


def mend(world: World, wife: Entity, husband: Entity, child: Entity,
         fix: Fix, flower: Flower) -> None:
    room = world.get("room")
    wife.memes["care"] += 1
    husband.memes["care"] += 1
    child.memes["safe"] += 1
    world.say(
        f"{child.id} made one small sleepy sound, and both grown-ups hurried in at once."
    )
    world.say(
        f"{husband.id} lifted the posy while {wife.id} patted the wet spot dry with a soft cloth."
    )
    if room.meters["wetness"] >= THRESHOLD:
        world.say(f"{fix.move_text}.")
    world.say(
        f"Soon the room was tidy again, and the {flower.bedtime_image} looked peaceful in its new place."
    )


def lesson(world: World, wife: Entity, husband: Entity, child: Entity,
           flower: Flower, fix: Fix) -> None:
    wife.memes["learned"] += 1
    husband.memes["learned"] += 1
    child.memes["calm"] += 1
    world.say(
        f'"A pretty thing should also be a steady thing," {husband.id} whispered.'
    )
    world.say(
        f'{wife.id} kissed {child.id} on the forehead and nodded. '
        f'"That is our lesson for tonight. Next time, we will put a posy where it can stay lovely and safe."'
    )
    world.say(
        f"{child.id} drifted back toward sleep while the {flower.color} flowers rested {fix.phrase}, proving the room had learned how to be gentle."
    )


def peaceful_ending(world: World, wife: Entity, husband: Entity, child: Entity,
                    flower: Flower, fix: Fix) -> None:
    wife.memes["learned"] += 1
    husband.memes["learned"] += 1
    child.memes["calm"] += 1
    world.say(
        f"{child.id} tucked deeper under the blanket while the {flower.color} posy stood {fix.phrase}."
    )
    world.say(
        f'{wife.id} smiled at her husband. "You noticed the trouble before it came," she said.'
    )
    world.say(
        f'He answered, "Bedtime feels best when we choose the calm place first."'
    )


FLOWERS = {
    "daisies": Flower(
        id="daisies",
        label="daisies",
        scent="clean, green",
        color="white-and-gold",
        stem="short",
        bedtime_image="petals like tiny moons",
        tags={"flowers", "daisies"},
    ),
    "lavender": Flower(
        id="lavender",
        label="lavender sprigs",
        scent="sweet, sleepy",
        color="purple",
        stem="slender",
        bedtime_image="purple stems like quiet little candles",
        tags={"flowers", "lavender"},
    ),
    "clover": Flower(
        id="clover",
        label="clover blossoms",
        scent="honey-soft",
        color="pink",
        stem="small",
        bedtime_image="round blossoms soft as pom-poms",
        tags={"flowers", "clover"},
    ),
}

CONTAINERS = {
    "teacup": Container(
        id="teacup",
        label="teacup",
        phrase="a small teacup",
        stable=False,
        water_safe=True,
        wobble_text="the teacup gave the faintest wobble on its saucer",
        tags={"teacup", "container"},
    ),
    "jamjar": Container(
        id="jamjar",
        label="jam jar",
        phrase="a sturdy jam jar",
        stable=True,
        water_safe=True,
        wobble_text="the jam jar sat square and still",
        tags={"jar", "container"},
    ),
    "tin": Container(
        id="tin",
        label="little tin",
        phrase="a little painted tin",
        stable=True,
        water_safe=True,
        wobble_text="the little tin stayed planted where it was put",
        tags={"tin", "container"},
    ),
    "basket": Container(
        id="basket",
        label="woven basket",
        phrase="a woven basket",
        stable=True,
        water_safe=False,
        wobble_text="the basket itself was steady, but it was never meant to hold a wet posy",
        tags={"basket", "container"},
    ),
}

SPOTS = {
    "windowsill": Spot(
        id="windowsill",
        label="the open window",
        phrase="the windowsill by the open window",
        breezy=True,
        near_bed=True,
        hush_text="Moonlight lay on the quilt, and the curtain breathed in and out",
        foreshadow_text="Outside, faraway leaves rubbed together, and the curtain puffed once like a quiet warning",
        tags={"window", "breeze"},
    ),
    "dresser": Spot(
        id="dresser",
        label="the dresser",
        phrase="the top of the dresser across the room",
        breezy=False,
        near_bed=False,
        hush_text="The dresser stood still under a round pool of lamplight",
        foreshadow_text="The lamp hummed softly, and nothing in the room stirred",
        tags={"dresser", "safe_spot"},
    ),
    "shelf": Spot(
        id="shelf",
        label="the wall shelf",
        phrase="the wall shelf near the storybooks",
        breezy=False,
        near_bed=False,
        hush_text="The shelf sat quiet beside the books with their sleepy spines",
        foreshadow_text="Only the clock made a tiny tick, and the room kept its balance",
        tags={"shelf", "safe_spot"},
    ),
}

FIXES = {
    "move_to_dresser": Fix(
        id="move_to_dresser",
        label="move to dresser",
        phrase="safely on the dresser",
        careful=3,
        works_on_breeze=True,
        move_text="Together they moved the flowers to the still dresser across the room",
        qa_text="They moved the posy to the dresser, where the breeze could not tip it",
        tags={"dresser", "safety"},
    ),
    "move_to_shelf": Fix(
        id="move_to_shelf",
        label="move to shelf",
        phrase="safely on the wall shelf",
        careful=3,
        works_on_breeze=True,
        move_text="Together they carried the flowers to the quiet shelf by the books",
        qa_text="They carried the posy to the shelf, where it could stay steady all night",
        tags={"shelf", "safety"},
    ),
    "straighten_saucer": Fix(
        id="straighten_saucer",
        label="straighten saucer",
        phrase="back on the same sill",
        careful=1,
        works_on_breeze=False,
        move_text="They only straightened the saucer and set the teacup back in the same place",
        qa_text="They only straightened the saucer, which did not really solve the breeze problem",
        tags={"window", "weak_fix"},
    ),
}

WIFE_NAMES = ["Mara", "Elsie", "Nell", "Ivy", "June", "Tessa"]
HUSBAND_NAMES = ["Oren", "Bram", "Hugo", "Ned", "Silas", "Theo"]
CHILD_NAMES = ["Pip", "Mina", "Toby", "Wren", "Lulu", "Kit"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for flower in FLOWERS:
        for container_id, container in CONTAINERS.items():
            for spot_id, spot in SPOTS.items():
                if not CONTAINERS[container_id].water_safe:
                    continue
                combos.append((flower, container_id, spot_id))
    return combos


@dataclass
class StoryParams:
    flower: str
    container: str
    spot: str
    fix: str
    wife_name: str
    husband_name: str
    child_name: str
    child_gender: str
    wind: int = 0
    heed_warning: bool = False
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
    "flowers": [
        (
            "What is a posy?",
            "A posy is a small bunch of flowers tied or gathered together. People often keep one in a cup or jar because it is little and pretty."
        )
    ],
    "window": [
        (
            "Why can an open window be risky for a small flower cup?",
            "A breeze from an open window can nudge light things and make them wobble. If the container is small or tippy, the flowers and water can spill."
        )
    ],
    "teacup": [
        (
            "Why is a teacup less steady than a jar for flowers?",
            "A teacup is usually narrower and easier to tip than a heavy jar. That means it can wobble more if something bumps it or a breeze reaches it."
        )
    ],
    "jar": [
        (
            "Why is a sturdy jar good for flowers?",
            "A sturdy jar has a solid bottom and stands more firmly. That helps flowers stay upright and keeps the water where it belongs."
        )
    ],
    "dresser": [
        (
            "Why is a dresser a calmer place than a windowsill at night?",
            "A dresser away from the window does not get the same moving air. Things set there are less likely to wobble or tip."
        )
    ],
    "shelf": [
        (
            "Why can a shelf be a safe place for a bedtime decoration?",
            "A quiet shelf can hold a small decoration where it will not be bumped by curtains or drafts. Safe places help the room stay calm through the night."
        )
    ],
    "safety": [
        (
            "What is the lesson in choosing a steady place for something pretty?",
            "Pretty things need safe places too. When you notice a small risk early and fix it, the whole room stays peaceful."
        )
    ],
    "lavender": [
        (
            "Why do some people like lavender at bedtime?",
            "Lavender has a soft smell that many people connect with calm evenings. Its gentle scent can make a room feel restful."
        )
    ],
    "daisies": [
        (
            "What do daisies look like?",
            "Daisies often have white petals around yellow centers. Their bright, simple shape makes them look cheerful and clean."
        )
    ],
    "clover": [
        (
            "What are clover blossoms like?",
            "Clover blossoms are small, round flowers that can look soft and puffy. They often grow low and gather in little groups."
        )
    ],
}
KNOWLEDGE_ORDER = ["flowers", "window", "teacup", "jar", "dresser", "shelf", "safety", "lavender", "daisies", "clover"]


def explain_rejection(container: Container, spot: Spot) -> str:
    if not container.water_safe:
        return (
            f"(No story: {container.phrase} is not a sensible water-holder for a bedtime posy. "
            f"Use a container that can safely hold stems in water, like a jam jar or little tin.)"
        )
    return (
        f"(No story: this combination does not fit the bedtime-posy world.)"
    )


def explain_fix(fix_id: str) -> str:
    fix = FIXES[fix_id]
    better = ", ".join(sorted(fx.id for fx in sensible_fixes()))
    return (
        f"(Refusing fix '{fix_id}': it is too weak for this world (careful={fix.careful} < {CAREFUL_MIN}). "
        f"Try one of the steadier fixes: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    container = CONTAINERS[params.container]
    spot = SPOTS[params.spot]
    fix = FIXES[params.fix]
    if params.heed_warning and fix_prevents(fix, spot):
        return "averted"
    return "spilled" if spill_happens(container, spot, params.wind) else "calm"


def tell(flower: Flower, container: Container, spot: Spot, fix: Fix,
         wife_name: str = "Mara", husband_name: str = "Oren", child_name: str = "Pip",
         child_gender: str = "girl", wind: int = 1, heed_warning: bool = False) -> World:
    world = World()
    wife = world.add(Entity(id=wife_name, kind="character", type="wife", role="wife", label="the wife"))
    husband = world.add(Entity(id=husband_name, kind="character", type="husband", role="husband", label="the husband"))
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", label="the child"))
    room = world.add(Entity(id="room", type="room", label="the nursery"))
    posy = world.add(Entity(id="posy", type="flowers", label="the posy"))
    container_ent = world.add(Entity(id="container", type="container", label=container.label))
    spot_ent = world.add(Entity(id="spot", type="spot", label=spot.label))

    room.meters["spill_risk"] = 0.0
    room.meters["wetness"] = 0.0
    room.meters["mess"] = 0.0
    posy.meters["tipped"] = 0.0
    posy.meters["droop"] = 0.0
    posy.attrs["breezy"] = False
    container_ent.attrs["stable"] = bool(container.stable)
    spot_ent.attrs["breezy"] = bool(spot.breezy)
    wife.memes["care"] = 0.0
    husband.memes["care"] = 0.0
    husband.memes["caution"] = 0.0
    child.memes["sleepy"] = 0.0

    world.facts["wind"] = int(wind)
    world.facts["moved_early"] = False

    introduce_evening(world, wife, husband, child, flower, spot)
    world.para()
    choose_place(world, wife, flower, container, spot)
    foreshadow(world, husband, container, spot)
    warn(world, husband, spot, container)

    if heed_warning and fix_prevents(fix, spot):
        world.para()
        decide_move_early(world, wife, husband, fix)
        world.para()
        peaceful_ending(world, wife, husband, child, flower, fix)
    else:
        if world.facts.get("predicted_risk", 0) >= THRESHOLD:
            decide_ignore(world, wife, child)
        world.para()
        night_turn(world, flower, container, spot)
        if world.get("room").meters["wetness"] >= THRESHOLD:
            world.para()
            mend(world, wife, husband, child, fix, flower)
            world.para()
            lesson(world, wife, husband, child, flower, fix)
        else:
            world.para()
            peaceful_ending(world, wife, husband, child, flower, fix)

    world.facts.update(
        wife=wife,
        husband=husband,
        child=child,
        flower=flower,
        container_cfg=container,
        spot_cfg=spot,
        fix=fix,
        outcome=outcome_of(
            StoryParams(
                flower=flower.id,
                container=container.id,
                spot=spot.id,
                fix=fix.id,
                wife_name=wife_name,
                husband_name=husband_name,
                child_name=child_name,
                child_gender=child_gender,
                wind=wind,
                heed_warning=heed_warning,
            )
        ),
        spilled=world.get("room").meters["wetness"] >= THRESHOLD,
        risk=world.get("room").meters["spill_risk"],
        moved_early=world.facts["moved_early"],
        wind=wind,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    flower = f["flower"]
    container = f["container_cfg"]
    spot = f["spot_cfg"]
    wife = f["wife"]
    husband = f["husband"]
    outcome = f["outcome"]
    if outcome == "spilled":
        return [
            f'Write a bedtime story that includes the words "posy" and "husband".',
            f"Tell a gentle bedtime story where {wife.id} places a posy of {flower.label} in {container.phrase}, "
            f"her husband notices trouble coming, and a small spill teaches the family a lesson.",
            f"Write a sleepy story with foreshadowing: the curtain stirs near {spot.label}, something tips, and the ending shows what the family learned."
        ]
    if outcome == "averted":
        return [
            f'Write a bedtime story that includes the words "posy" and "husband".',
            f"Tell a calm bedtime story where {husband.id}, the husband, notices a risk before it happens and helps move a posy to a safer place.",
            f"Write a story with gentle foreshadowing and a lesson learned, but no real disaster -- only a wiser choice before sleep."
        ]
    return [
        f'Write a bedtime story that includes the words "posy" and "husband".',
        f"Tell a peaceful bedtime story where a little posy of {flower.label} makes a nursery feel calm and the grown-ups choose a steady place for it.",
        f"Write a story with a soft warning in the middle and an ending image that proves the room is quiet and safe for sleep."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    wife = f["wife"]
    husband = f["husband"]
    child = f["child"]
    flower = f["flower"]
    container = f["container_cfg"]
    spot = f["spot_cfg"]
    fix = f["fix"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {wife.id}, her husband {husband.id}, and {child.id} getting ready for bed. "
            f"They were trying to make the room feel gentle with a little posy of {flower.label}."
        ),
        (
            "What did they put in the room?",
            f"They put a posy of {flower.label} in {container.phrase}. "
            f"The flowers were meant to make the nursery feel soft and sleepy."
        ),
        (
            f"How did the story foreshadow that something might go wrong?",
            f"The curtain moved and {husband.id} noticed that {container.wobble_text}. "
            f"Those details warned that the breeze near {spot.label} might tip the posy later."
        ),
    ]
    if f["outcome"] == "spilled":
        qa.append(
            (
                "Why did the posy spill?",
                f"It spilled because {container.phrase} was set by {spot.label}, where the night breeze could reach it. "
                f"The husband noticed the risk first, and later a puff of air made the posy lean and splash."
            )
        )
        qa.append(
            (
                "How did they solve the problem after the spill?",
                f"They dried the wet spot and then {fix.qa_text}. "
                f"That changed the room from messy and worried back to calm and bedtime-safe."
            )
        )
        qa.append(
            (
                "What lesson did the family learn?",
                "They learned that something pretty should also be placed somewhere steady. "
                "Choosing the calm place early keeps the whole room peaceful."
            )
        )
    elif f["outcome"] == "averted":
        qa.append(
            (
                "What did the husband do?",
                f"{husband.id} noticed the danger before bedtime and spoke up gently. "
                f"Because the grown-ups listened and moved the posy, nothing spilled at all."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the posy standing {fix.phrase} while {child.id} settled under the blanket. "
                f"The quiet ending shows that they learned to choose the steadier place first."
            )
        )
    else:
        qa.append(
            (
                "Why did nothing spill in this story?",
                f"Nothing spilled because the flowers were not in a risky place to begin with. "
                f"The room stayed still through the night, so the posy could rest peacefully."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["flower"].tags) | set(f["spot_cfg"].tags) | set(f["fix"].tags)
    container = f["container_cfg"]
    if "teacup" in container.tags:
        tags.add("teacup")
    if "jar" in container.tags:
        tags.add("jar")
    tags.add("flowers")
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% validity
valid(F,C,S) :- flower(F), container(C), spot(S), water_safe(C).
hazard(C,S)  :- unstable(C), breezy(S).

% sensible fixes
sensible_fix(X) :- fix(X), careful(X,N), careful_min(M), N >= M.

% outcome
risk :- chosen_container(C), chosen_spot(S), hazard(C,S).
spill :- risk, wind(W), W >= 1, not heed_warning.
works :- chosen_fix(X), chosen_spot(S), sensible_fix(X), not breezy(S).
works :- chosen_fix(X), chosen_spot(S), sensible_fix(X), works_on_breeze(X), breezy(S).
outcome(averted) :- heed_warning, works.
outcome(spilled) :- not outcome(averted), spill.
outcome(calm) :- not outcome(averted), not spill.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for fid in FLOWERS:
        lines.append(asp.fact("flower", fid))
    for cid, c in CONTAINERS.items():
        lines.append(asp.fact("container", cid))
        if not c.stable:
            lines.append(asp.fact("unstable", cid))
        if c.water_safe:
            lines.append(asp.fact("water_safe", cid))
    for sid, s in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        if s.breezy:
            lines.append(asp.fact("breezy", sid))
    for xid, x in FIXES.items():
        lines.append(asp.fact("fix", xid))
        lines.append(asp.fact("careful", xid, x.careful))
        if x.works_on_breeze:
            lines.append(asp.fact("works_on_breeze", xid))
    lines.append(asp.fact("careful_min", CAREFUL_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_fixes() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_fix/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible_fix"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra_lines = [
        asp.fact("chosen_container", params.container),
        asp.fact("chosen_spot", params.spot),
        asp.fact("chosen_fix", params.fix),
        asp.fact("wind", params.wind),
    ]
    if params.heed_warning:
        extra_lines.append(asp.fact("heed_warning"))
    model = asp.one_model(asp_program("\n".join(extra_lines), "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a bedtime posy, a husband who notices trouble, and a lesson about choosing the steady place."
    )
    ap.add_argument("--flower", choices=FLOWERS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--wind", type=int, choices=[0, 1], help="0 keeps the air still; 1 allows a bedtime puff of breeze")
    ap.add_argument("--heed-warning", action="store_true", help="have the grown-ups move the posy before any spill")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.container:
        container = CONTAINERS[args.container]
        if not container.water_safe:
            spot = SPOTS[args.spot] if args.spot else next(iter(SPOTS.values()))
            raise StoryError(explain_rejection(container, spot))
    if args.fix and FIXES[args.fix].careful < CAREFUL_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        combo for combo in valid_combos()
        if (args.flower is None or combo[0] == args.flower)
        and (args.container is None or combo[1] == args.container)
        and (args.spot is None or combo[2] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    flower_id, container_id, spot_id = rng.choice(sorted(combos))
    sensible = sorted(fx.id for fx in sensible_fixes())
    fix_id = args.fix or rng.choice(sensible)
    wife_name = rng.choice(WIFE_NAMES)
    husband_name = rng.choice([n for n in HUSBAND_NAMES if n != wife_name])
    child_name = rng.choice([n for n in CHILD_NAMES if n not in {wife_name, husband_name}])
    child_gender = rng.choice(["girl", "boy"])
    wind = args.wind if args.wind is not None else rng.choice([0, 1])
    heed_warning = bool(args.heed_warning)
    if heed_warning and not fix_prevents(FIXES[fix_id], SPOTS[spot_id]):
        raise StoryError("(No story: that chosen fix would not really solve the breeze problem.)")
    return StoryParams(
        flower=flower_id,
        container=container_id,
        spot=spot_id,
        fix=fix_id,
        wife_name=wife_name,
        husband_name=husband_name,
        child_name=child_name,
        child_gender=child_gender,
        wind=wind,
        heed_warning=heed_warning,
    )


def generate(params: StoryParams) -> StorySample:
    if params.flower not in FLOWERS:
        raise StoryError(f"(Unknown flower: {params.flower})")
    if params.container not in CONTAINERS:
        raise StoryError(f"(Unknown container: {params.container})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    container = CONTAINERS[params.container]
    spot = SPOTS[params.spot]
    fix = FIXES[params.fix]
    if not container.water_safe:
        raise StoryError(explain_rejection(container, spot))
    if fix.careful < CAREFUL_MIN:
        raise StoryError(explain_fix(params.fix))
    if params.heed_warning and not fix_prevents(fix, spot):
        raise StoryError("(No story: that chosen fix would not really solve the breeze problem.)")

    world = tell(
        flower=FLOWERS[params.flower],
        container=container,
        spot=spot,
        fix=fix,
        wife_name=params.wife_name,
        husband_name=params.husband_name,
        child_name=params.child_name,
        child_gender=params.child_gender,
        wind=params.wind,
        heed_warning=params.heed_warning,
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


CURATED = [
    StoryParams(
        flower="lavender",
        container="teacup",
        spot="windowsill",
        fix="move_to_dresser",
        wife_name="Mara",
        husband_name="Oren",
        child_name="Pip",
        child_gender="girl",
        wind=1,
        heed_warning=False,
    ),
    StoryParams(
        flower="daisies",
        container="jamjar",
        spot="dresser",
        fix="move_to_shelf",
        wife_name="Elsie",
        husband_name="Hugo",
        child_name="Mina",
        child_gender="girl",
        wind=0,
        heed_warning=False,
    ),
    StoryParams(
        flower="clover",
        container="teacup",
        spot="windowsill",
        fix="move_to_shelf",
        wife_name="Nell",
        husband_name="Theo",
        child_name="Kit",
        child_gender="boy",
        wind=1,
        heed_warning=True,
    ),
    StoryParams(
        flower="lavender",
        container="tin",
        spot="shelf",
        fix="move_to_dresser",
        wife_name="June",
        husband_name="Silas",
        child_name="Wren",
        child_gender="girl",
        wind=0,
        heed_warning=False,
    ),
]


def asp_verify() -> int:
    rc = 0

    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_fixes = set(asp_sensible_fixes())
    python_fixes = {fx.id for fx in sensible_fixes()}
    if clingo_fixes == python_fixes:
        print(f"OK: sensible fixes match ({sorted(clingo_fixes)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(clingo_fixes)} python={sorted(python_fixes)}")

    cases = list(CURATED)
    for s in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    bad = 0
    for params in cases:
        ao = asp_outcome(params)
        po = outcome_of(params)
        if ao != po:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible_fix/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        fixes = asp_sensible_fixes()
        combos = asp_valid_combos()
        print(f"sensible fixes: {', '.join(fixes)}\n")
        print(f"{len(combos)} compatible (flower, container, spot) combos:\n")
        for flower, container, spot in combos:
            print(f"  {flower:10} {container:8} {spot}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.wife_name}, {p.husband_name}, and {p.child_name}: {p.flower} in {p.container} at {p.spot} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
