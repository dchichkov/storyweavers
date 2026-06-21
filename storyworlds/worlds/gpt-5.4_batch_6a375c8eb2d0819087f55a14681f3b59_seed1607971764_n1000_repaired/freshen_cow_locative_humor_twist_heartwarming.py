#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/freshen_cow_locative_humor_twist_heartwarming.py
============================================================================

A standalone story world about a child who wants to freshen the barn before a
visitor arrives, while also practicing a new school word: "locative." The
child tries to keep a beloved cow in just the right place for a welcome
surprise. The humor comes from giving a cow careful position words as if she
were a classroom helper; the twist comes when the cow solves the moment in her
own gentle, funny way.

Run it
------
    python storyworlds/worlds/gpt-5.4/freshen_cow_locative_humor_twist_heartwarming.py
    python storyworlds/worlds/gpt-5.4/freshen_cow_locative_humor_twist_heartwarming.py --location by_gate --lure apple_pail
    python storyworlds/worlds/gpt-5.4/freshen_cow_locative_humor_twist_heartwarming.py --lure hay_net --location under_tree
    python storyworlds/worlds/gpt-5.4/freshen_cow_locative_humor_twist_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/freshen_cow_locative_humor_twist_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/freshen_cow_locative_humor_twist_heartwarming.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
SMOOTH_MIN = 4
STEADY_TRAITS = {"patient", "careful", "gentle"}


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
        female = {"girl", "woman", "mother", "grandmother", "teacher_woman"}
        male = {"boy", "man", "father", "grandfather", "teacher_man"}
        animal = {"cow"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "teacher_woman": "teacher",
            "teacher_man": "teacher",
        }.get(self.type, self.type)
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
class FreshenMethod:
    id: str
    sense: int
    label: str
    action: str
    scent: str
    twist_phrase: str
    drift_to: str
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
class Lure:
    id: str
    label: str
    phrase: str
    works_at: set[str] = field(default_factory=set)
    patience_bonus: int = 0
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
class Location:
    id: str
    phrase: str
    locative_word: str
    comfy: int
    detail: str
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
class Visitor:
    id: str
    type: str
    label: str
    arrival: str
    gift: str
    asks_words: bool = True
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


def _r_wait(world: World) -> list[str]:
    cow = world.get("cow")
    if cow.attrs.get("spot") != world.facts["chosen_location"]:
        return []
    if not world.facts.get("lure_placed"):
        return []
    sig = ("wait", cow.id, world.facts["chosen_location"])
    if sig in world.fired:
        return []
    world.fired.add(sig)
    score = (
        world.facts["patience"]
        + world.facts["lure_bonus"]
        + world.facts["location_comfy"]
    )
    world.facts["wait_score"] = score
    if score >= SMOOTH_MIN:
        cow.meters["waiting"] += 1
        cow.memes["calm"] += 1
    else:
        cow.memes["itchy_feet"] += 1
    return []


def _r_reveal(world: World) -> list[str]:
    barn = world.get("barn")
    cow = world.get("cow")
    if barn.meters["fresh"] < THRESHOLD:
        return []
    if cow.attrs.get("spot") != world.facts.get("final_location"):
        return []
    sig = ("reveal", cow.id, cow.attrs.get("spot"))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.facts["reveal_ready"] = True
    return []


CAUSAL_RULES = [
    Rule(name="wait", tag="social", apply=_r_wait),
    Rule(name="reveal", tag="social", apply=_r_reveal),
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


def sensible_freshen_methods() -> list[FreshenMethod]:
    return [m for m in FRESHEN_METHODS.values() if m.sense >= SENSE_MIN]


def location_fits_lure(lure: Lure, location: Location) -> bool:
    return location.id in lure.works_at


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for freshen_id, freshen in FRESHEN_METHODS.items():
        if freshen.sense < SENSE_MIN:
            continue
        for lure_id, lure in LURES.items():
            for location_id, location in LOCATIONS.items():
                if location_fits_lure(lure, location):
                    combos.append((freshen_id, lure_id, location_id))
    return combos


def patience_of(trait: str) -> int:
    return 2 if trait in STEADY_TRAITS else 1


def outcome_of(params: "StoryParams") -> str:
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")
    if params.lure not in LURES or params.location not in LOCATIONS:
        raise StoryError("(Unknown lure or location.)")
    score = (
        patience_of(params.trait)
        + LURES[params.lure].patience_bonus
        + LOCATIONS[params.location].comfy
    )
    return "smooth" if score >= SMOOTH_MIN else "twist"


def predict_wait(world: World, location_id: str) -> dict:
    sim = world.copy()
    sim.facts["chosen_location"] = location_id
    sim.facts["final_location"] = location_id
    sim.get("cow").attrs["spot"] = location_id
    sim.facts["lure_placed"] = True
    propagate(sim, narrate=False)
    return {
        "wait_score": sim.facts.get("wait_score", 0),
        "will_wait": sim.get("cow").meters["waiting"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, cow: Entity, visitor: Visitor) -> None:
    world.say(
        f"{child.id} loved the little farm behind the house, especially {cow.id}, "
        f"the soft-eyed cow who always seemed to be smiling."
    )
    world.say(
        f"That morning, {visitor.label} was coming {visitor.arrival}, and {child.id} "
        f"wanted the barn to look extra nice."
    )


def school_word(world: World, child: Entity) -> None:
    child.memes["pride"] += 1
    world.say(
        f"At school, {child.id} had just learned a grand new word: locative. "
        f'"It means where something is," {child.pronoun()} told {child.pronoun("possessive")} cow, '
        f"as if {cow_name(world)} might want a lesson too."
    )


def plan(world: World, child: Entity, freshen: FreshenMethod, location: Location) -> None:
    world.say(
        f'{child.id} clapped {child.pronoun("possessive")} hands. "I can freshen the barn '
        f'and have {cow_name(world)} stand {location.phrase}!"'
    )
    world.say(location.detail)


def place_lure(world: World, child: Entity, lure: Lure, location: Location) -> None:
    world.facts["lure_placed"] = True
    world.say(
        f"{child.id} set {lure.phrase} {location.phrase} and pointed very seriously. "
        f'"Please stand {location.phrase}, {cow_name(world)}. This is locative work."'
    )


def freshen_barn(world: World, child: Entity, freshen: FreshenMethod) -> None:
    barn = world.get("barn")
    cow = world.get("cow")
    barn.meters["fresh"] += 1
    cow.meters["freshened"] += 1
    child.memes["hope"] += 1
    world.say(
        f"Then {child.id} {freshen.action}. Soon the barn smelled {freshen.scent}, "
        f"and even {cow.id}'s warm coat seemed to freshen with it."
    )


def smooth_wait(world: World, child: Entity, cow: Entity, location: Location) -> None:
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    cow.attrs["spot"] = location.id
    world.facts["final_location"] = location.id
    propagate(world, narrate=False)
    world.say(
        f"For once, {cow.id} did exactly as asked. She stayed {location.phrase}, "
        f"chewing happily and blinking as if she had understood every single word."
    )


def twist_wander(world: World, child: Entity, cow: Entity, freshen: FreshenMethod) -> None:
    child.memes["worry"] += 1
    cow.meters["wandered"] += 1
    cow.attrs["spot"] = freshen.drift_to
    world.facts["final_location"] = freshen.drift_to
    propagate(world, narrate=False)
    world.say(
        f"But cows have their own ideas. {cow.id} gave one slow swish of her tail, "
        f"ambled away, and stopped {LOCATIONS[freshen.drift_to].phrase} instead."
    )
    world.say(
        f"There she stood, looking pleased with herself, with {freshen.twist_phrase}. "
        f"{child.id} could not help laughing, even while feeling a little flustered."
    )


def arrival_and_reveal(world: World, child: Entity, cow: Entity, visitor_ent: Entity,
                       visitor_cfg: Visitor, planned: Location) -> None:
    final_loc = LOCATIONS[world.facts["final_location"]]
    child.memes["love"] += 1
    child.memes["pride"] += 1
    cow.memes["content"] += 1
    world.say(
        f"A moment later, {visitor_cfg.label} came {visitor_cfg.arrival} and stopped at the barn door."
    )
    if world.facts["outcome"] == "smooth":
        world.say(
            f'"Oh!" {visitor_ent.pronoun()} laughed. "There is {cow.id}, exactly {planned.phrase}."'
        )
    else:
        world.say(
            f'{child.id} opened {child.pronoun("possessive")} mouth to explain the plan, '
            f"but {visitor_cfg.label} laughed first."
        )
        world.say(
            f'"Well," {visitor_ent.pronoun()} said, "she chose a better answer all by herself. '
            f'There is {cow.id} {final_loc.phrase}."'
        )
    if visitor_cfg.asks_words:
        world.say(
            f'{child.id} beamed. "That is a locative word," {child.pronoun()} said. '
            f'"I was practicing where she should be."'
        )
    world.say(
        f"{visitor_cfg.label} stepped inside, breathed the sweet air, and admired the clean boards and the shining cow."
    )


def warm_ending(world: World, child: Entity, cow: Entity, visitor_ent: Entity, visitor_cfg: Visitor) -> None:
    gift = visitor_cfg.gift
    child.memes["belonging"] += 1
    world.say(
        f'{visitor_cfg.label} gave {child.id} {gift} and scratched {cow.id} between the ears.'
    )
    if world.facts["outcome"] == "twist":
        world.say(
            f'"Sometimes," {visitor_ent.pronoun()} said, "the funniest helper in the barn is the best one."'
        )
    else:
        world.say(
            f'"You and {cow.id} make a fine team," {visitor_ent.pronoun()} said softly.'
        )
    world.say(
        f"{child.id} leaned against {cow.id}'s side, warm and proud. The barn was fresh, "
        f"the visitor was smiling, and the little locative lesson had turned into a family story everyone would tell again."
    )


def cow_name(world: World) -> str:
    return world.get("cow").id
def tell(
    lure: Lure,
    location: Location,
    visitor_cfg: Visitor,
    child_name: str,
    child_gender: str,
    child_trait: ChildTrait,
    parent_type: ParentType,
    cow_name_value: CowNameValue,
    freshen=None,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[child_trait],
    ))
    world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    visitor_ent = world.add(Entity(
        id="Visitor",
        kind="character",
        type=visitor_cfg.type,
        role="visitor",
        label=visitor_cfg.label,
    ))
    cow = world.add(Entity(
        id=cow_name_value,
        kind="character",
        type="cow",
        role="cow",
        label="the cow",
        attrs={"spot": location.id},
    ))
    barn = world.add(Entity(
        id="barn",
        kind="thing",
        type="barn",
        label="the barn",
    ))

    world.facts["chosen_location"] = location.id
    world.facts["final_location"] = location.id
    world.facts["lure_placed"] = False
    world.facts["patience"] = patience_of(child_trait)
    world.facts["lure_bonus"] = lure.patience_bonus
    world.facts["location_comfy"] = location.comfy
    world.facts["wait_score"] = 0
    world.facts["outcome"] = outcome_of(StoryParams(
        freshen=freshen.id,
        lure=lure.id,
        location=location.id,
        visitor=visitor_cfg.id,
        child_name=child_name,
        child_gender=child_gender,
        parent=parent_type,
        trait=child_trait,
        cow_name=cow_name_value,
        seed=None,
    ))
    world.facts["predicted"] = predict_wait(world, location.id)

    introduce(world, child, cow, visitor_cfg)
    school_word(world, child)
    plan(world, child, freshen, location)

    world.para()
    place_lure(world, child, lure, location)
    pred = world.facts["predicted"]
    world.say(
        f"{child.id} guessed that if {cow.id} had a good nibble and a cozy place, "
        f"she would stay put long enough. In {child.pronoun('possessive')} head, the score for that plan felt like {pred['wait_score']}."
    )
    freshen_barn(world, child, freshen)

    world.para()
    if world.facts["outcome"] == "smooth":
        smooth_wait(world, child, cow, location)
    else:
        twist_wander(world, child, cow, freshen)

    world.para()
    arrival_and_reveal(world, child, cow, visitor_ent, visitor_cfg, location)
    warm_ending(world, child, cow, visitor_ent, visitor_cfg)

    world.facts.update(
        child=child,
        cow=cow,
        barn=barn,
        visitor_ent=visitor_ent,
        visitor_cfg=visitor_cfg,
        freshen=freshen,
        lure=lure,
        location_cfg=location,
        final_location_cfg=LOCATIONS[world.facts["final_location"]],
        planned_location_cfg=location,
        predicted_wait=pred["will_wait"],
        reveal_ready=bool(world.facts.get("reveal_ready")),
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


FRESHEN_METHODS = {
    "mint_brush": FreshenMethod(
        id="mint_brush",
        sense=3,
        label="mint brush",
        action="rubbed Clover down with a soft brush and hung fresh mint by the door",
        scent="cool and green",
        twist_phrase="a sprig of mint dangling from one ear like a fancy earring",
        drift_to="by_gate",
        tags={"freshen", "mint"},
    ),
    "sunny_towel": FreshenMethod(
        id="sunny_towel",
        sense=2,
        label="warm towel",
        action="wiped the railings and Clover's nose with a warm towel from the sun",
        scent="warm and clean",
        twist_phrase="the towel slipping over her horn like a crooked little flag",
        drift_to="in_stall",
        tags={"freshen", "clean"},
    ),
    "herb_broom": FreshenMethod(
        id="herb_broom",
        sense=3,
        label="herb broom",
        action="swept the floor with a broom tied with lavender and sweet hay",
        scent="sweet and sleepy",
        twist_phrase="a bit of lavender caught by her collar",
        drift_to="under_tree",
        tags={"freshen", "lavender"},
    ),
    "perfume_spray": FreshenMethod(
        id="perfume_spray",
        sense=1,
        label="perfume spray",
        action="sprayed perfume into the air",
        scent="far too strong",
        twist_phrase="a sneezy look on her face",
        drift_to="by_gate",
        tags={"freshen"},
    ),
}

LURES = {
    "apple_pail": Lure(
        id="apple_pail",
        label="apple pail",
        phrase="a small pail of apple slices",
        works_at={"by_gate", "under_tree"},
        patience_bonus=1,
        tags={"apple"},
    ),
    "hay_net": Lure(
        id="hay_net",
        label="hay net",
        phrase="a tidy hay net",
        works_at={"in_stall"},
        patience_bonus=2,
        tags={"hay"},
    ),
    "clover_pan": Lure(
        id="clover_pan",
        label="clover pan",
        phrase="a blue pan full of clover",
        works_at={"by_gate", "in_stall"},
        patience_bonus=1,
        tags={"clover"},
    ),
}

LOCATIONS = {
    "by_gate": Location(
        id="by_gate",
        phrase="beside the red gate",
        locative_word="beside",
        comfy=1,
        detail="The red gate made a neat frame, and the morning light fell there in a bright stripe.",
        tags={"gate", "beside"},
    ),
    "in_stall": Location(
        id="in_stall",
        phrase="in the clean stall",
        locative_word="in",
        comfy=2,
        detail="The clean stall was shady and still, with dry straw that smelled cozy.",
        tags={"stall", "in"},
    ),
    "under_tree": Location(
        id="under_tree",
        phrase="under the apple tree",
        locative_word="under",
        comfy=1,
        detail="Under the old apple tree, the shade made a soft round patch on the ground.",
        tags={"tree", "under"},
    ),
}

VISITORS = {
    "grandma": Visitor(
        id="grandma",
        type="grandmother",
        label="Grandma",
        arrival="up the path with a pie box",
        gift="a warm hug and a little paper ribbon",
        asks_words=True,
        tags={"family"},
    ),
    "teacher": Visitor(
        id="teacher",
        type="teacher_woman",
        label="Ms. Lane",
        arrival="for the class farm visit",
        gift="a shiny gold star sticker",
        asks_words=True,
        tags={"school"},
    ),
    "grandpa": Visitor(
        id="grandpa",
        type="grandfather",
        label="Grandpa",
        arrival="through the gate carrying a camera",
        gift="a bright photograph tucked into his pocket for later",
        asks_words=True,
        tags={"family"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Ella", "Lena", "Ruby", "Ava", "June", "Maya"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Finn", "Eli", "Noah", "Jack", "Theo"]
COW_NAMES = ["Clover", "Daisy", "Buttercup", "Mabel", "Poppy"]
TRAITS = ["patient", "careful", "gentle", "bouncy", "chatty", "curious"]


KNOWLEDGE = {
    "freshen": [(
        "What does freshen mean?",
        "To freshen something means to make it feel or smell cleaner and nicer. You might sweep, brush, or open things up so the place feels bright again."
    )],
    "cow": [(
        "What does a cow like in a calm barn?",
        "A cow likes a place that feels safe, quiet, and comfortable. Food, shade, and familiar smells can help her stay calm."
    )],
    "locative": [(
        "What is a locative word?",
        "A locative word tells where something is, like in, under, or beside. It helps you describe the place of a person, animal, or thing."
    )],
    "apple": [(
        "Why might a cow follow a pail of apple slices?",
        "Many cows like sweet treats, and apple slices smell strong enough to notice. A treat can help guide an animal to a certain spot."
    )],
    "hay": [(
        "Why does hay help a cow wait?",
        "Hay gives a cow something familiar to nibble slowly. That can help her stay calm and stand in one place longer."
    )],
    "clover": [(
        "Why would a cow like clover?",
        "Clover is soft and tasty for grazing animals. Its smell can make a feeding spot feel inviting."
    )],
    "stall": [(
        "What is a stall in a barn?",
        "A stall is a small space inside a barn where an animal can stand or rest. It is often lined with straw to feel dry and comfortable."
    )],
    "gate": [(
        "What is a farm gate for?",
        "A gate helps people and animals move in and out in an orderly way. It also marks a clear place to stop or gather."
    )],
    "tree": [(
        "Why do animals stand under a tree on a warm day?",
        "A tree can make cool shade under its branches. Shade helps an animal feel more comfortable and less bothered by the sun."
    )],
}
KNOWLEDGE_ORDER = ["freshen", "cow", "locative", "apple", "hay", "clover", "stall", "gate", "tree"]
@dataclass
class StoryParams:
    freshen: str
    lure: str
    location: str
    visitor: str
    child_name: str
    child_gender: str
    parent: str
    trait: str
    cow_name: str
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        freshen="herb_broom",
        lure="hay_net",
        location="in_stall",
        visitor="grandma",
        child_name="Nora",
        child_gender="girl",
        parent="mother",
        trait="patient",
        cow_name="Clover",
        seed=None,
    ),
    StoryParams(
        freshen="mint_brush",
        lure="apple_pail",
        location="by_gate",
        visitor="teacher",
        child_name="Ben",
        child_gender="boy",
        parent="father",
        trait="curious",
        cow_name="Buttercup",
        seed=None,
    ),
    StoryParams(
        freshen="sunny_towel",
        lure="clover_pan",
        location="by_gate",
        visitor="grandpa",
        child_name="Ella",
        child_gender="girl",
        parent="mother",
        trait="chatty",
        cow_name="Daisy",
        seed=None,
    ),
    StoryParams(
        freshen="herb_broom",
        lure="apple_pail",
        location="under_tree",
        visitor="teacher",
        child_name="Leo",
        child_gender="boy",
        parent="father",
        trait="gentle",
        cow_name="Mabel",
        seed=None,
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    cow = f["cow"]
    visitor = f["visitor_cfg"]
    planned = f["planned_location_cfg"]
    return [
        'Write a heartwarming story for a 3-to-5-year-old that includes the words "freshen", "cow", and "locative".',
        f"Tell a gentle farm story where {child.id} tries to freshen a barn before {visitor.label} arrives and asks a {cow.type} named {cow.id} to stand {planned.phrase}.",
        f"Write a warm, funny story with a small twist where a child uses a new school word, locative, while getting a beloved cow ready for a visitor.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    cow = f["cow"]
    visitor = f["visitor_cfg"]
    freshen = f["freshen"]
    lure = f["lure"]
    planned = f["planned_location_cfg"]
    final_loc = f["final_location_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child on a little farm, and {cow.id}, the family cow. {visitor.label} is coming too, which is why the barn matters so much that day."
        ),
        (
            f"Why did {child.id} want to freshen the barn?",
            f"{child.id} wanted the barn to look and smell nice before {visitor.label} arrived. Freshening it was a way to welcome someone loved and make the visit feel special."
        ),
        (
            "What did the child mean by the word locative?",
            f"{child.id} said locative means where something is. That is why {child.pronoun()} kept telling {cow.id} to stand {planned.phrase}."
        ),
        (
            f"How did {child.id} try to help {cow.id} stay in place?",
            f"{child.pronoun().capitalize()} put {lure.phrase} {planned.phrase} and used it as a gentle lure. The plan worked around what cows enjoy, not just around what {child.id} wished."
        ),
    ]
    if f["outcome"] == "smooth":
        qa.append((
            f"Did {cow.id} stay where {child.id} planned?",
            f"Yes. {cow.id} stayed {planned.phrase} while the barn was being freshened. That happened because the spot was comfortable and the lure gave her a calm reason to wait."
        ))
    else:
        qa.append((
            f"What was the funny twist in the story?",
            f"{cow.id} did not stay where {child.id} planned. She wandered and ended up {final_loc.phrase} with a funny extra detail on her, and that surprise made everyone laugh."
        ))
    qa.append((
        "How did the story end?",
        f"It ended warmly, with the barn fresh, the visitor smiling, and {child.id} feeling proud. The little lesson about where the cow was turned into a happy family memory."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"freshen", "cow", "locative"}
    tags |= set(f["lure"].tags)
    tags |= set(f["planned_location_cfg"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} wait_score={world.facts.get('wait_score')} final_location={world.facts.get('final_location')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(lure: Lure, location: Location) -> str:
    return (
        f"(No story: {lure.label} does not make sense {location.phrase}. "
        f"This world only allows waiting spots that the lure can honestly support.)"
    )


def explain_freshen_rejection(method: FreshenMethod) -> str:
    return (
        f"(Refusing freshen method '{method.id}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). The storyworld prefers gentle, sensible ways to freshen a barn.)"
    )


ASP_RULES = r"""
sensible(F) :- freshen(F), sense(F,S), sense_min(M), S >= M.
fits(Lu,Loc) :- works_at(Lu,Loc).
valid(F,Lu,Loc) :- sensible(F), lure(Lu), location(Loc), fits(Lu,Loc).

patience_init(2) :- chosen_trait(T), steady(T).
patience_init(1) :- chosen_trait(T), not steady(T).
score(P + B + C) :- patience_init(P), chosen_lure(Lu), bonus(Lu,B),
                    chosen_location(Loc), comfy(Loc,C).
smooth :- score(S), smooth_min(M), S >= M.
outcome(smooth) :- smooth.
outcome(twist) :- not smooth.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for fid, f in FRESHEN_METHODS.items():
        lines.append(asp.fact("freshen", fid))
        lines.append(asp.fact("sense", fid, f.sense))
    for lid, l in LURES.items():
        lines.append(asp.fact("lure", lid))
        lines.append(asp.fact("bonus", lid, l.patience_bonus))
        for loc in sorted(l.works_at):
            lines.append(asp.fact("works_at", lid, loc))
    for loc_id, loc in LOCATIONS.items():
        lines.append(asp.fact("location", loc_id))
        lines.append(asp.fact("comfy", loc_id, loc.comfy))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("smooth_min", SMOOTH_MIN))
    for tr in sorted(STEADY_TRAITS):
        lines.append(asp.fact("steady", tr))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_lure", params.lure),
        asp.fact("chosen_location", params.location),
        asp.fact("chosen_trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
    parser = build_parser()
    for s in range(50):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(s))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {s}.")
            break
    bad = 0
    for params in cases:
        try:
            if asp_outcome(params) != outcome_of(params):
                bad += 1
        except StoryError as err:
            rc = 1
            print(f"Outcome check crashed: {err}")
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(sample, trace=False, qa=False, header="### smoke")
        finally:
            sys.stdout = old
        print("OK: smoke generate/emit test passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child tries to freshen a barn, place a cow, and practice a locative word."
    )
    ap.add_argument("--freshen", choices=FRESHEN_METHODS)
    ap.add_argument("--lure", choices=LURES)
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--visitor", choices=VISITORS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--cow-name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.freshen:
        method = FRESHEN_METHODS[args.freshen]
        if method.sense < SENSE_MIN:
            raise StoryError(explain_freshen_rejection(method))
    if args.lure and args.location:
        lure = LURES[args.lure]
        location = LOCATIONS[args.location]
        if not location_fits_lure(lure, location):
            raise StoryError(explain_rejection(lure, location))

    combos = [
        combo for combo in valid_combos()
        if (args.freshen is None or combo[0] == args.freshen)
        and (args.lure is None or combo[1] == args.lure)
        and (args.location is None or combo[2] == args.location)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    freshen_id, lure_id, location_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    cow_name_value = args.cow_name or rng.choice(COW_NAMES)
    visitor_id = args.visitor or rng.choice(sorted(VISITORS))
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        freshen=freshen_id,
        lure=lure_id,
        location=location_id,
        visitor=visitor_id,
        child_name=child_name,
        child_gender=gender,
        parent=parent,
        trait=trait,
        cow_name=cow_name_value,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.freshen not in FRESHEN_METHODS:
        raise StoryError(f"(Unknown freshen method: {params.freshen})")
    if params.lure not in LURES:
        raise StoryError(f"(Unknown lure: {params.lure})")
    if params.location not in LOCATIONS:
        raise StoryError(f"(Unknown location: {params.location})")
    if params.visitor not in VISITORS:
        raise StoryError(f"(Unknown visitor: {params.visitor})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")

    freshen = FRESHEN_METHODS[params.freshen]
    lure = LURES[params.lure]
    location = LOCATIONS[params.location]
    if freshen.sense < SENSE_MIN:
        raise StoryError(explain_freshen_rejection(freshen))
    if not location_fits_lure(lure, location):
        raise StoryError(explain_rejection(lure, location))

    world = tell(
        freshen=freshen,
        lure=lure,
        location=location,
        visitor_cfg=VISITORS[params.visitor],
        child_name=params.child_name,
        child_gender=params.child_gender,
        child_trait=params.trait,
        parent_type=params.parent,
        cow_name_value=params.cow_name,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (freshen, lure, location) combos:\n")
        for freshen_id, lure_id, location_id in combos:
            print(f"  {freshen_id:12} {lure_id:11} {location_id}")
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
            header = f"### {p.child_name} and {p.cow_name}: {p.freshen}, {p.lure}, {p.location} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
