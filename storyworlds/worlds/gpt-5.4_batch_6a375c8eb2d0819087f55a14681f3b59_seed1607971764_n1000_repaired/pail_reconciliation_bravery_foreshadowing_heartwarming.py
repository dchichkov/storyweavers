#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pail_reconciliation_bravery_foreshadowing_heartwarming.py
====================================================================================

A standalone story world about two children, one pail, a small quarrel, a brave
walk into a scary corner, and a warm reconciliation. The domain is intentionally
small and child-facing: the children need the pail to carry water to thirsty
plants, they argue over it, something goes wrong, and then the same object
becomes the center of repair.

The world model tracks both physical meters (thirst, dampness, distance, rolling,
watering) and emotional memes (hurt, fear, courage, trust, apology, relief,
love). Prose comes from simulated state, not from swapping nouns in a frozen
paragraph.

Run it
------
    python storyworlds/worlds/gpt-5.4/pail_reconciliation_bravery_foreshadowing_heartwarming.py
    python storyworlds/worlds/gpt-5.4/pail_reconciliation_bravery_foreshadowing_heartwarming.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/pail_reconciliation_bravery_foreshadowing_heartwarming.py --all --qa
    python storyworlds/worlds/gpt-5.4/pail_reconciliation_bravery_foreshadowing_heartwarming.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/pail_reconciliation_bravery_foreshadowing_heartwarming.py --json
    python storyworlds/worlds/gpt-5.4/pail_reconciliation_bravery_foreshadowing_heartwarming.py --verify
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
COURAGE_MIN = 5
TRUST_FOR_SOLO = 7


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
class Place:
    id: str
    label: str
    plant_spot: str
    water_source: str
    scary_corner: str
    opening: str
    ending_image: str
    afford_fears: set[str] = field(default_factory=set)
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
class PlantGoal:
    id: str
    label: str
    plural_label: str
    thirst_word: str
    bloom_word: str
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
class Fear:
    id: str
    sign: str
    noise: str
    shape: str
    brave_line: str
    reveal: str
    courage: int
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
class Repair:
    id: str
    apology: str
    join_line: str
    ending_line: str
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    patch = world.get("patch")
    pail = world.get("pail")
    if patch.meters["thirst"] >= THRESHOLD and pail.meters["reachable"] < THRESHOLD:
        sig = ("worry",)
        if sig not in world.fired:
            world.fired.add(sig)
            for kid in (world.get("child1"), world.get("child2")):
                kid.memes["worry"] += 1
            out.append("__worry__")
    return out


def _r_hurt_needs_repair(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("child1")
    b = world.get("child2")
    if a.memes["hurt"] >= THRESHOLD or b.memes["hurt"] >= THRESHOLD:
        sig = ("repair_needed",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.facts["repair_needed"] = True
            out.append("__repair__")
    return out


def _r_shared_task_builds_trust(world: World) -> list[str]:
    out: list[str] = []
    patch = world.get("patch")
    if patch.meters["watered"] >= THRESHOLD:
        sig = ("shared_task_builds_trust",)
        if sig not in world.fired:
            world.fired.add(sig)
            for kid in (world.get("child1"), world.get("child2")):
                kid.memes["trust"] += 1
                kid.memes["relief"] += 1
                kid.memes["joy"] += 1
            out.append("__trust__")
    return out


CAUSAL_RULES = [
    Rule(name="worry", tag="emotional", apply=_r_worry),
    Rule(name="hurt_needs_repair", tag="social", apply=_r_hurt_needs_repair),
    Rule(name="shared_task_builds_trust", tag="social", apply=_r_shared_task_builds_trust),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(s for s in got if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def fear_fits(place: Place, fear: Fear) -> bool:
    return fear.id in place.afford_fears


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for plant_id in PLANTS:
            for fear_id, fear in FEARS.items():
                if fear_fits(place, fear):
                    combos.append((place_id, plant_id, fear_id))
    return combos


def expected_courage(trait: str) -> int:
    return {"timid": 2, "careful": 3, "kind": 4, "steady": 4, "bold": 5, "gentle": 3}[trait]


def can_fetch_alone(fear: Fear, brave_trait: str, trust: int) -> bool:
    return expected_courage(brave_trait) + trust >= fear.courage + TRUST_FOR_SOLO


def can_fetch_together(fear: Fear, brave_trait: str) -> bool:
    return expected_courage(brave_trait) + 2 >= fear.courage


def predict_retrieval(fear: Fear, brave_trait: str, trust: int) -> dict:
    return {
        "solo": can_fetch_alone(fear, brave_trait, trust),
        "together": can_fetch_together(fear, brave_trait),
    }


def explain_rejection(place: Place, fear: Fear) -> str:
    return (
        f"(No story: {fear.id} does not fit {place.label}. "
        f"The scary corner there would not honestly make that kind of sound or shape.)"
    )


def predict_outcome(params: "StoryParams") -> str:
    fear = FEARS[params.fear]
    if can_fetch_alone(fear, params.brave_trait, params.trust):
        return "solo_retrieval"
    if can_fetch_together(fear, params.brave_trait):
        return "together_retrieval"
    return "call_parent"


def foreshadow(world: World, place: Place, fear: Fear, child2: Entity) -> None:
    child2.memes["fear"] += 1
    world.say(
        f"After breakfast, {place.opening} At the far edge, near {place.scary_corner}, "
        f"{fear.sign}."
    )
    world.say(
        f'{child2.id} looked that way and pressed {child2.pronoun("possessive")} lips together. '
        f'"That corner sounds funny," {child2.pronoun()} said.'
    )


def introduce_task(world: World, place: Place, plant: PlantGoal, child1: Entity, child2: Entity) -> None:
    patch = world.get("patch")
    patch.meters["thirst"] = 1
    child1.memes["joy"] += 1
    child2.memes["joy"] += 1
    world.say(
        f"{child1.id} and {child2.id} had promised to help water the {plant.plural_label} "
        f"by carrying water from {place.water_source} in a small red pail."
    )
    world.say(
        f"The {plant.plural_label} looked {plant.thirst_word}, and both children wanted to be the one "
        f"who tipped in the first shining splash."
    )


def quarrel(world: World, child1: Entity, child2: Entity) -> None:
    child1.memes["hurt"] += 1
    child2.memes["hurt"] += 1
    child1.memes["anger"] += 1
    child2.memes["anger"] += 1
    world.say(
        f'"It is my turn," {child1.id} said, reaching for the pail handle. '
        f'"No, you had it yesterday," said {child2.id}.'
    )
    world.say(
        f"Their hands bumped. The pail wobbled on the path, and the warm feeling of the morning "
        f"slipped away."
    )
    propagate(world, narrate=False)


def lose_pail(world: World, place: Place, fear: Fear) -> None:
    pail = world.get("pail")
    pail.meters["reachable"] = 0
    pail.meters["distance"] = 1
    pail.meters["rolled"] = 1
    propagate(world, narrate=False)
    world.say(
        f"Then the pail tipped, spun in a bright little circle, and rolled all the way toward "
        f"{place.scary_corner}. It stopped beside {fear.shape}."
    )
    world.say(
        f"For a moment, nobody moved. From that corner came {fear.noise}."
    )


def pause_and_regret(world: World, child1: Entity, child2: Entity, plant: PlantGoal) -> None:
    child1.memes["regret"] += 1
    child2.memes["regret"] += 1
    world.say(
        f"{child1.id} looked at the {plant.plural_label}, then at {child2.id}. "
        f"{child2.id} looked down at the empty hands between them."
    )
    world.say(
        "It was hard to stay cross when something small and important needed help."
    )


def brave_step(world: World, fear: Fear, brave: Entity, other: Entity, outcome: str) -> None:
    brave.memes["courage"] += 1
    if outcome == "solo_retrieval":
        brave.memes["care_for_other"] += 1
        world.say(
            f'{brave.id} took a breath. "{fear.brave_line} I will go get the pail," '
            f'{brave.pronoun()} said.'
        )
        world.say(
            f"{other.id} started to follow, but {brave.id} shook "
            f"{brave.pronoun('possessive')} head gently. "
            f'"Stay where it feels bright. I will come right back."'
        )
    elif outcome == "together_retrieval":
        brave.memes["care_for_other"] += 1
        other.memes["courage"] += 1
        world.say(
            f'{brave.id} took a breath. "{fear.brave_line} We can go together," '
            f'{brave.pronoun()} said.'
        )
        world.say(
            f"{other.id} slid a hand into {brave.id}'s hand. They walked more slowly than before, "
            f"but this time they walked side by side."
        )
    else:
        world.say(
            f'{brave.id} took a breath. "{fear.brave_line} Let\'s ask {world.get("parent").label_word} '
            f'to come with us," {brave.pronoun()} said.'
        )


def retrieve_pail(world: World, fear: Fear, outcome: str) -> None:
    pail = world.get("pail")
    pail.meters["reachable"] = 1
    pail.meters["distance"] = 0
    if outcome == "call_parent":
        world.say(
            f"When they reached the corner with their grown-up, {fear.reveal}. The pail was only resting "
            f"against a root after all."
        )
    else:
        world.say(
            f"As they came close, {fear.reveal}. The scary part shrank at once, and the pail was only resting "
            f"against a root after all."
        )


def apologize(world: World, repair: Repair, child1: Entity, child2: Entity, brave: Entity) -> None:
    child1.memes["apology"] += 1
    child2.memes["apology"] += 1
    child1.memes["anger"] = 0
    child2.memes["anger"] = 0
    child1.memes["hurt"] = 0
    child2.memes["hurt"] = 0
    if brave.id == child1.id:
        first, second = child1, child2
    else:
        first, second = child2, child1
    world.say(
        f'"{repair.apology}" {first.id} said softly. "{repair.join_line}"'
    )
    world.say(
        f'{second.id} nodded. "I am sorry too," {second.pronoun()} said, and the knot between them loosened.'
    )


def water_plants(world: World, plant: PlantGoal, place: Place, outcome: str) -> None:
    patch = world.get("patch")
    pail = world.get("pail")
    patch.meters["thirst"] = 0
    patch.meters["watered"] = 1
    pail.meters["filled"] = 1
    pail.meters["shared"] = 1
    propagate(world, narrate=False)
    if outcome == "solo_retrieval":
        world.say(
            f"Back at the {plant.plural_label}, they held the pail together and poured slowly, taking turns "
            f"with the handle."
        )
    elif outcome == "together_retrieval":
        world.say(
            f"At the {plant.plural_label}, they tipped the pail together, and the water ran in a silver ribbon "
            f"around the roots."
        )
    else:
        world.say(
            f"With their grown-up beside them, they carried the pail back to the {plant.plural_label} and poured "
            f"until the dry earth turned dark and cool."
        )
    world.say(
        f"Soon the {plant.plural_label} no longer looked {plant.thirst_word}. {place.ending_image}."
    )


def ending(world: World, repair: Repair, child1: Entity, child2: Entity, outcome: str) -> None:
    parent = world.get("parent")
    if outcome == "call_parent":
        world.say(
            f'{parent.label_word.capitalize()} smiled at both children. "Brave does not always mean going alone," '
            f'{parent.pronoun()} said. "Sometimes brave means asking for help and then making things right."'
        )
    else:
        world.say(
            repair.ending_line
        )
    world.say(
        f"{child1.id} and {child2.id} carried the pail back between them, one small hand on each side of the handle."
    )
def tell(
    plant: Plant,
    fear: Fear,
    repair: Repair,
    child1_name: str,
    child1_gender: str,
    child2_name: str,
    child2_gender: str,
    brave_child: BraveChild,
    brave_trait: BraveTrait,
    parent_type: ParentType,
    trust: Trust,
    place=None,
) -> World:
    world = World()
    child1 = world.add(Entity(
        id=child1_name,
        kind="character",
        type=child1_gender,
        role="child1",
        traits=["helpful"],
        attrs={"trust": trust},
    ))
    child2 = world.add(Entity(
        id=child2_name,
        kind="character",
        type=child2_gender,
        role="child2",
        traits=["tender"],
        attrs={"trust": trust},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
        attrs={},
    ))
    brave = child1 if brave_child == "child1" else child2
    other = child2 if brave is child1 else child1
    brave.traits.append(brave_trait)
    brave.memes["courage"] = float(expected_courage(brave_trait))
    other.memes["fear"] = 0.0
    child1.memes["trust"] = float(trust)
    child2.memes["trust"] = float(trust)
    world.add(Entity(id="patch", type="plants", label=plant.plural_label, attrs={}))
    world.add(Entity(id="pail", type="pail", label="pail", attrs={}))

    world.facts.update(
        place=place,
        plant=plant,
        fear=fear,
        repair=repair,
        brave_id=brave.id,
        brave_trait=brave_trait,
        trust=trust,
        repair_needed=False,
    )

    foreshadow(world, place, fear, other)
    introduce_task(world, place, plant, child1, child2)

    world.para()
    quarrel(world, child1, child2)
    lose_pail(world, place, fear)
    pause_and_regret(world, child1, child2, plant)

    world.para()
    outcome = predict_outcome(StoryParams(
        place=place.id,
        plant=plant.id,
        fear=fear.id,
        repair=repair.id,
        child1=child1_name,
        child1_gender=child1_gender,
        child2=child2_name,
        child2_gender=child2_gender,
        brave_child=brave_child,
        brave_trait=brave_trait,
        parent=parent_type,
        trust=trust,
        seed=None,
    ))
    brave_step(world, fear, brave, other, outcome)
    retrieve_pail(world, fear, outcome)
    apologize(world, repair, child1, child2, brave)

    world.para()
    water_plants(world, plant, place, outcome)
    ending(world, repair, child1, child2, outcome)

    world.facts.update(
        child1=child1,
        child2=child2,
        parent=parent,
        outcome=outcome,
        feared_corner=True,
        pail_lost=True,
        reconciled=True,
        asked_help=(outcome == "call_parent"),
        together=(outcome == "together_retrieval"),
        solo=(outcome == "solo_retrieval"),
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


PLACES = {
    "garden": Place(
        id="garden",
        label="the garden",
        plant_spot="the sunflower bed",
        water_source="the hand pump",
        scary_corner="the old tool shed",
        opening="the garden still held little beads of morning dew.",
        ending_image="A bee bobbed above the leaves, and the whole bed seemed to lift its face again",
        afford_fears={"shed_shadow", "gate_creak"},
        tags={"garden", "watering"},
    ),
    "yard": Place(
        id="yard",
        label="the backyard",
        plant_spot="the bean row",
        water_source="the rain barrel",
        scary_corner="the long fence corner",
        opening="the backyard smelled warm and green.",
        ending_image="The beans stood a little straighter, and the fence no longer seemed stern at all",
        afford_fears={"reeds_rustle", "gate_creak"},
        tags={"yard", "watering"},
    ),
    "orchard": Place(
        id="orchard",
        label="the little orchard",
        plant_spot="the young apple trees",
        water_source="the stone trough",
        scary_corner="the blackberry hedge",
        opening="the little orchard was quiet except for birds in the branches.",
        ending_image="The young trees gleamed with droplets, and the orchard felt friendly again",
        afford_fears={"reeds_rustle", "crow_flap"},
        tags={"orchard", "watering"},
    ),
}

PLANTS = {
    "sunflowers": PlantGoal(
        id="sunflowers",
        label="sunflower",
        plural_label="sunflowers",
        thirst_word="droopy and thirsty",
        bloom_word="golden and tall",
        tags={"plants", "flowers"},
    ),
    "beans": PlantGoal(
        id="beans",
        label="bean plant",
        plural_label="bean plants",
        thirst_word="thin and thirsty",
        bloom_word="green and climbing",
        tags={"plants", "beans"},
    ),
    "saplings": PlantGoal(
        id="saplings",
        label="young tree",
        plural_label="young apple trees",
        thirst_word="dry and thirsty",
        bloom_word="bright and leafy",
        tags={"plants", "trees"},
    ),
}

FEARS = {
    "shed_shadow": Fear(
        id="shed_shadow",
        sign="the shed threw a cool shadow across the dirt",
        noise="a soft thump from inside the shed",
        shape="a crooked rake leaning by the door",
        brave_line="It only looks bigger from far away.",
        reveal="it was only a loose shutter tapping in the breeze",
        courage=5,
        tags={"shadow", "shed"},
    ),
    "gate_creak": Fear(
        id="gate_creak",
        sign="the old gate moved a finger-width and gave a slow little squeak",
        noise="another long creak from the gate hinge",
        shape="the bent latch shining in the light",
        brave_line="A squeak can sound spooky and still be only a squeak.",
        reveal="it was only the gate moving back and forth on its hinge",
        courage=4,
        tags={"gate", "sound"},
    ),
    "reeds_rustle": Fear(
        id="reeds_rustle",
        sign="the tall grass at the edge kept whispering to itself",
        noise="a hush-hush rustle in the dry stems",
        shape="a bundle of grass bowing and lifting again",
        brave_line="Let us look close before we let the sound grow bigger in our heads.",
        reveal="it was only the wind combing through the reeds",
        courage=5,
        tags={"grass", "wind"},
    ),
    "crow_flap": Fear(
        id="crow_flap",
        sign="a dark bird hopped once behind the hedge and vanished",
        noise="a sudden flap of wings over the leaves",
        shape="a glossy black feather caught in a branch",
        brave_line="It startled me too, but we can still take one careful step.",
        reveal="a crow burst up from the hedge and flew away into the blue",
        courage=6,
        tags={"bird", "wings"},
    ),
}

REPAIRS = {
    "share_turns": Repair(
        id="share_turns",
        apology="I was grabbing and not listening. We can share turns from now on.",
        join_line="Will you hold the other side with me?",
        ending_line="The children smiled at each other, not because the morning had gone perfectly, but because they had mended it together.",
        tags={"sharing", "apology"},
    ),
    "kind_words": Repair(
        id="kind_words",
        apology="I said it in a sharp voice. I wanted the pail too much and forgot to be kind.",
        join_line="Can we try again with softer words?",
        ending_line="The cross voices were gone, and in their place was the warm, easy sound of being friends again.",
        tags={"kindness", "apology"},
    ),
    "take_turns": Repair(
        id="take_turns",
        apology="I wanted to win instead of help. We can take turns and help at the same time.",
        join_line="Will you start, and then I will?",
        ending_line="By the time the last drop fell from the pail, the quarrel had faded into something much smaller than the care they shared.",
        tags={"turns", "repair"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Eli", "Theo"]
TRAITS = ["timid", "careful", "kind", "steady", "bold", "gentle"]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    return "two children"


KNOWLEDGE = {
    "watering": [
        ("Why do plants need water?",
         "Plants need water to stay firm and alive. Their roots drink it from the soil so their stems and leaves do not droop.")
    ],
    "pail": [
        ("What is a pail?",
         "A pail is a small bucket with a handle. People can use it to carry water, sand, or other small things from one place to another.")
    ],
    "shadow": [
        ("Why can a shadow look scary from far away?",
         "A shadow can hide the true shape of something when you are far away. When you get closer in a safe way, it often turns out to be something ordinary.")
    ],
    "gate": [
        ("Why does an old gate creak?",
         "An old gate can creak because its hinge rubs as it moves. The sound may be loud, but it is often only wood or metal shifting.")
    ],
    "wind": [
        ("Why does grass rustle in the wind?",
         "Grass rustles when moving air pushes the stems and leaves against each other. The sound can seem mysterious until you know what is making it.")
    ],
    "bird": [
        ("Why do birds flap suddenly out of bushes?",
         "A bird may flap out quickly when it was resting or looking for food. Sudden movement can surprise us even when there is no danger.")
    ],
    "sharing": [
        ("What does taking turns mean?",
         "Taking turns means one person uses something first and then lets another person use it next. It helps people share fairly.")
    ],
    "apology": [
        ("What is an apology?",
         "An apology is when you say you are sorry for something unkind or hurtful. A good apology helps people start repairing the hurt.")
    ],
    "bravery": [
        ("What is bravery?",
         "Bravery means doing the next right thing even when you feel scared. Sometimes that means taking a careful step, and sometimes it means asking for help.")
    ],
}
KNOWLEDGE_ORDER = ["watering", "pail", "shadow", "gate", "wind", "bird", "sharing", "apology", "bravery"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c1, c2 = f["child1"], f["child2"]
    place, plant, fear = f["place"], f["plant"], f["fear"]
    outcome = f["outcome"]
    if outcome == "call_parent":
        return [
            'Write a heartwarming story for a 3-to-5-year-old that includes the word "pail", a small quarrel, foreshadowing, bravery, and reconciliation.',
            f"Tell a gentle story where {c1.id} and {c2.id} lose a pail near {place.scary_corner}, feel scared by {fear.noise}, and make peace while asking a grown-up for help.",
            f"Write a warm story about children watering {plant.plural_label}, mending a hurt feeling, and learning that brave can mean asking for help.",
        ]
    return [
        'Write a heartwarming story for a 3-to-5-year-old that includes the word "pail", a small quarrel, foreshadowing, bravery, and reconciliation.',
        f"Tell a gentle story where {c1.id} and {c2.id} argue over a pail, then face a scary corner near {place.scary_corner} and become close again while watering {plant.plural_label}.",
        f"Write a simple story with an early hint that a place might feel spooky later, and end with children sharing the pail kindly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    c1, c2 = f["child1"], f["child2"]
    place, plant, fear = f["place"], f["plant"], f["fear"]
    brave = c1 if f["brave_id"] == c1.id else c2
    other = c2 if brave is c1 else c1
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(c1, c2)}, {c1.id} and {c2.id}, who were trying to water {plant.plural_label} with a pail. Their small quarrel and their later kindness both shape what happens."
        ),
        (
            "Why did the children need the pail?",
            f"They needed the pail to carry water from {place.water_source} to the {plant.plural_label}. The plants looked {plant.thirst_word}, so the pail was the tool that could help them."
        ),
        (
            "What was the foreshadowing at the beginning?",
            f"The story hinted early that the far corner might feel spooky because {fear.sign}. That clue matters later when the pail rolls toward the same place."
        ),
        (
            "Why did the children stop arguing?",
            f"They saw that the pail was gone and the {plant.plural_label} still needed water. It became harder to stay cross because something outside their quarrel needed care."
        ),
    ]
    if outcome == "solo_retrieval":
        qa.append((
            f"How was {brave.id} brave?",
            f"{brave.id} felt the scary place too, but still went to fetch the pail carefully. {brave.pronoun().capitalize()} was brave because {brave.pronoun()} chose to help both {other.id} and the thirsty plants even while afraid."
        ))
    elif outcome == "together_retrieval":
        qa.append((
            "How were the children brave?",
            f"They walked to the scary corner together instead of running away from it. Holding hands helped them take a careful brave step while they were still uncertain."
        ))
    else:
        qa.append((
            "How were the children brave?",
            f"They were brave enough to admit they needed help and asked their grown-up to come with them. That was brave because they chose the safe right thing instead of pretending not to be scared."
        ))
    qa.append((
        "How did the children reconcile?",
        f"They apologized and chose to share the pail kindly after getting it back. The repair became real when they worked together to water the {plant.plural_label} instead of fighting over the handle."
    ))
    qa.append((
        "How did the story end?",
        f"It ended with the {plant.plural_label} watered and the children carrying the pail together. The final picture shows that both the dry plants and the hurt feelings had been cared for."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"watering", "pail", "apology", "bravery"}
    fear_tags = world.facts["fear"].tags
    repair_tags = world.facts["repair"].tags
    if "shadow" in fear_tags or "shed" in fear_tags:
        tags.add("shadow")
    if "gate" in fear_tags or "sound" in fear_tags:
        tags.add("gate")
    if "grass" in fear_tags or "wind" in fear_tags:
        tags.add("wind")
    if "bird" in fear_tags or "wings" in fear_tags:
        tags.add("bird")
    if "sharing" in repair_tags or "turns" in repair_tags:
        tags.add("sharing")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} brave={world.facts.get('brave_id')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits(P,F) :- place(P), fear(F), afford_fear(P,F).
valid(P,Pl,F) :- place(P), plant(Pl), fits(P,F).

trait_courage(T,C) :- brave_trait(T), courage_of(T,C).
solo_retrieval :- chosen_fear(F), fear_need(F,Need),
                  chosen_trait(T), courage_of(T,C),
                  chosen_trust(Tr), C + Tr >= Need + trust_for_solo.
together_retrieval :- chosen_fear(F), fear_need(F,Need),
                      chosen_trait(T), courage_of(T,C),
                      C + 2 >= Need, not solo_retrieval.
call_parent :- not solo_retrieval, not together_retrieval.

outcome(solo_retrieval) :- solo_retrieval.
outcome(together_retrieval) :- together_retrieval.
outcome(call_parent) :- call_parent.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for fear_id in sorted(place.afford_fears):
            lines.append(asp.fact("afford_fear", place_id, fear_id))
    for plant_id in PLANTS:
        lines.append(asp.fact("plant", plant_id))
    for fear_id, fear in FEARS.items():
        lines.append(asp.fact("fear", fear_id))
        lines.append(asp.fact("fear_need", fear_id, fear.courage))
    for trait in TRAITS:
        lines.append(asp.fact("brave_trait", trait))
        lines.append(asp.fact("courage_of", trait, expected_courage(trait)))
    lines.append(asp.fact("trust_for_solo", TRUST_FOR_SOLO))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_fear", params.fear),
        asp.fact("chosen_trait", params.brave_trait),
        asp.fact("chosen_trust", params.trust),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"
@dataclass
class StoryParams:
    place: str
    plant: str
    fear: str
    repair: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    brave_child: str
    brave_trait: str
    parent: str
    trust: int = 5
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        place="garden",
        plant="sunflowers",
        fear="shed_shadow",
        repair="share_turns",
        child1="Lily",
        child1_gender="girl",
        child2="Ben",
        child2_gender="boy",
        brave_child="child1",
        brave_trait="bold",
        parent="mother",
        trust=8,
    ),
    StoryParams(
        place="yard",
        plant="beans",
        fear="gate_creak",
        repair="kind_words",
        child1="Max",
        child1_gender="boy",
        child2="Mia",
        child2_gender="girl",
        brave_child="child2",
        brave_trait="steady",
        parent="father",
        trust=5,
    ),
    StoryParams(
        place="orchard",
        plant="saplings",
        fear="crow_flap",
        repair="take_turns",
        child1="Nora",
        child1_gender="girl",
        child2="Theo",
        child2_gender="boy",
        brave_child="child2",
        brave_trait="careful",
        parent="mother",
        trust=3,
    ),
    StoryParams(
        place="yard",
        plant="sunflowers",
        fear="reeds_rustle",
        repair="share_turns",
        child1="Ella",
        child1_gender="girl",
        child2="Rose",
        child2_gender="girl",
        brave_child="child1",
        brave_trait="kind",
        parent="father",
        trust=6,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a pail, a quarrel, a brave step, and reconciliation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--fear", choices=FEARS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trust", type=int, choices=list(range(0, 11)))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.fear:
        place = PLACES[args.place]
        fear = FEARS[args.fear]
        if not fear_fits(place, fear):
            raise StoryError(explain_rejection(place, fear))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.plant is None or c[1] == args.plant)
        and (args.fear is None or c[2] == args.fear)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, plant, fear = rng.choice(sorted(combos))
    repair = args.repair or rng.choice(sorted(REPAIRS))
    child1, child1_gender = _pick_child(rng)
    child2, child2_gender = _pick_child(rng, avoid=child1)
    brave_child = rng.choice(["child1", "child2"])
    brave_trait = rng.choice(TRAITS)
    parent = args.parent or rng.choice(["mother", "father"])
    trust = args.trust if args.trust is not None else rng.randint(0, 10)

    return StoryParams(
        place=place,
        plant=plant,
        fear=fear,
        repair=repair,
        child1=child1,
        child1_gender=child1_gender,
        child2=child2,
        child2_gender=child2_gender,
        brave_child=brave_child,
        brave_trait=brave_trait,
        parent=parent,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.plant not in PLANTS:
        raise StoryError(f"(Unknown plant: {params.plant})")
    if params.fear not in FEARS:
        raise StoryError(f"(Unknown fear: {params.fear})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")
    if params.brave_child not in {"child1", "child2"}:
        raise StoryError(f"(Unknown brave_child: {params.brave_child})")
    if params.brave_trait not in TRAITS:
        raise StoryError(f"(Unknown brave_trait: {params.brave_trait})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent: {params.parent})")

    place = PLACES[params.place]
    fear = FEARS[params.fear]
    if not fear_fits(place, fear):
        raise StoryError(explain_rejection(place, fear))

    world = tell(
        place=place,
        plant=PLANTS[params.plant],
        fear=fear,
        repair=REPAIRS[params.repair],
        child1_name=params.child1,
        child1_gender=params.child1_gender,
        child2_name=params.child2,
        child2_gender=params.child2_gender,
        brave_child=params.brave_child,
        brave_trait=params.brave_trait,
        parent_type=params.parent,
        trust=params.trust,
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
    for s in range(80):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    mismatches = []
    for params in cases:
        py = predict_outcome(params)
        asp = asp_outcome(params)
        if py != asp:
            mismatches.append((params, py, asp))
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")
        for params, py, asp in mismatches[:5]:
            print(" ", params, "python=", py, "asp=", asp)

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
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
        print(f"{len(combos)} compatible (place, plant, fear) combos:\n")
        for place, plant, fear in combos:
            print(f"  {place:8} {plant:11} {fear}")
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
            header = f"### {p.child1} & {p.child2}: {p.place}, {p.fear}, {predict_outcome(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
