#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/vocabulary_passive_stop_gerund_inner_monologue_rhyme.py
==================================================================================

A standalone storyworld in a folk-tale mode about a child, a thirsty word tree,
and a feared helper who is not what they seem.

Seed requirements carried into the simulated world:
- words: "vocabulary", "passive", "stop-gerund"
- features: Inner Monologue, Rhyme, Twist
- style: Folk Tale

World premise
-------------
In a small village, an old word tree usually drops bright leaves with unusual
words written on them. After a dry wind, the tree falls silent. A child carries
water to the tree and meets a creature everyone mistrusts. The turn comes from
the child's inner monologue and the eventual twist: the feared helper was not
stealing the silver word-leaves, but keeping them safe.

Reasonableness gate
-------------------
Not every vessel can carry enough water, and not every helper can reach every
place. This world refuses combinations that do not make physical sense:
- a leaky vessel or too-small vessel cannot revive a thirsty tree;
- a helper must be able to reach the tree's terrain in order to return the
  missing word-leaves.

Run it
------
    python storyworlds/worlds/gpt-5.4/vocabulary_passive_stop_gerund_inner_monologue_rhyme.py
    python storyworlds/worlds/gpt-5.4/vocabulary_passive_stop_gerund_inner_monologue_rhyme.py --tree pear --place island --helper otter
    python storyworlds/worlds/gpt-5.4/vocabulary_passive_stop_gerund_inner_monologue_rhyme.py --vessel basket
    python storyworlds/worlds/gpt-5.4/vocabulary_passive_stop_gerund_inner_monologue_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/vocabulary_passive_stop_gerund_inner_monologue_rhyme.py --qa --json
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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
class TreeKind:
    id: str
    label: str
    phrase: str
    need: int
    blossom: str
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
class Place:
    id: str
    label: str
    terrain: str
    path: str
    spring: str
    closing: str
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
class Vessel:
    id: str
    label: str
    phrase: str
    capacity: int
    leaky: bool = False
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
class Helper:
    id: str
    label: str
    kind_name: str
    entrance: str
    access: set[str]
    feared: bool
    bundle: str
    rhyme: str
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


TREES = {
    "pear": TreeKind(
        id="pear",
        label="pear tree",
        phrase="the old pear tree by the village edge",
        need=2,
        blossom="white pear blossoms",
        tags={"tree", "fruit"},
    ),
    "linden": TreeKind(
        id="linden",
        label="linden tree",
        phrase="the humming linden above the path",
        need=3,
        blossom="pale yellow linden flowers",
        tags={"tree", "flower"},
    ),
    "plum": TreeKind(
        id="plum",
        label="plum tree",
        phrase="the bent plum tree near the field wall",
        need=2,
        blossom="small pink plum blossoms",
        tags={"tree", "fruit"},
    ),
}

PLACES = {
    "hill": Place(
        id="hill",
        label="the hill above the village",
        terrain="steep",
        path="a goat path that climbed in crooked steps",
        spring="a spring tucked under a flat gray stone",
        closing="From the hill, the village looked small as a toy, and the tree's song drifted down into every chimney.",
        tags={"hill"},
    ),
    "island": Place(
        id="island",
        label="the willow island in the ford",
        terrain="water",
        path="a line of wet stepping stones through the ford",
        spring="a clear bubbling spring under the willow roots",
        closing="Around the island, the ford flashed like a silver belt, and the tree's song skipped from ripple to ripple.",
        tags={"water"},
    ),
    "marsh": Place(
        id="marsh",
        label="the reed edge beyond the marsh",
        terrain="mud",
        path="a narrow path laid with old boards over the soft ground",
        spring="a cold spring hidden behind the reeds",
        closing="The marsh lamps winked among the reeds, and the tree's song floated over them as lightly as mist.",
        tags={"mud"},
    ),
}

VESSELS = {
    "bucket": Vessel(
        id="bucket",
        label="bucket",
        phrase="a stout wooden bucket",
        capacity=3,
        leaky=False,
        tags={"water"},
    ),
    "jug": Vessel(
        id="jug",
        label="clay jug",
        phrase="a round clay jug",
        capacity=2,
        leaky=False,
        tags={"water"},
    ),
    "dipper": Vessel(
        id="dipper",
        label="dipper",
        phrase="a long-handled dipper",
        capacity=1,
        leaky=False,
        tags={"water"},
    ),
    "basket": Vessel(
        id="basket",
        label="basket",
        phrase="a willow basket with wide gaps",
        capacity=0,
        leaky=True,
        tags={"basket"},
    ),
}

HELPERS = {
    "crow": Helper(
        id="crow",
        label="crow",
        kind_name="crow",
        entrance="A black crow dropped from a branch and landed beside the path.",
        access={"steep", "water", "mud"},
        feared=True,
        bundle="three silver leaves tucked under one wing",
        rhyme="Root to drink and leaf to sing; mend the word and wake the spring.",
        tags={"crow", "twist"},
    ),
    "goat": Helper(
        id="goat",
        label="goat",
        kind_name="goat",
        entrance="A sure-footed goat stepped from the rocks and shook its beard.",
        access={"steep", "mud"},
        feared=False,
        bundle="three silver leaves hanging from one horn by a grass string",
        rhyme="Climb the rise and do not fret; what seems lost is not lost yet.",
        tags={"goat", "twist"},
    ),
    "otter": Helper(
        id="otter",
        label="otter",
        kind_name="otter",
        entrance="An otter lifted its whiskered head from the water and blinked like a wet little lord.",
        access={"water", "mud"},
        feared=False,
        bundle="three silver leaves balanced on its chest like tiny boats",
        rhyme="Water bright and word made right; carry both from night to light.",
        tags={"otter", "twist"},
    ),
    "mole": Helper(
        id="mole",
        label="mole",
        kind_name="mole",
        entrance="A mole pushed up through the earth in a soft puff of soil.",
        access={"mud"},
        feared=True,
        bundle="three silver leaves wrapped in a dock leaf bundle",
        rhyme="Under clod and under log, I keep safe what strayed in fog.",
        tags={"mole", "twist"},
    ),
}

GIRL_NAMES = ["Mara", "Anya", "Lina", "Tessa", "Brina", "Nell", "Iva", "Elsa"]
BOY_NAMES = ["Ivo", "Pavel", "Milan", "Toma", "Nico", "Sava", "Rudi", "Bram"]
TRAITS = ["brave", "curious", "kind", "cautious", "timid", "steady"]
FEARLESS_TRAITS = {"brave", "curious", "kind"}

WORD_LEAVES = ["vocabulary", "passive", "stop-gerund"]


# ---------------------------------------------------------------------------
# World and rules
# ---------------------------------------------------------------------------
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "leaves_returned": False,
            "accepted_help": False,
            "outcome": "",
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


def _r_return_leaves(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    tree = world.get("tree")
    if child.memes["trust"] < THRESHOLD:
        return []
    if helper.meters["carrying_leaves"] < THRESHOLD:
        return []
    sig = ("return_leaves",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    tree.meters["leaf_count"] = float(len(WORD_LEAVES))
    helper.meters["carrying_leaves"] = 0.0
    world.facts["leaves_returned"] = True
    return ["__leaves__"]


def _r_drink(world: World) -> list[str]:
    tree = world.get("tree")
    if tree.meters["water"] < tree.attrs["need"]:
        return []
    if tree.meters["voice"] >= THRESHOLD:
        return []
    sig = ("drink",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    tree.meters["thirst"] = 0.0
    tree.meters["voice"] = 1.0
    return ["__voice__"]


def _r_bloom(world: World) -> list[str]:
    tree = world.get("tree")
    if tree.meters["voice"] < THRESHOLD or tree.meters["leaf_count"] < len(WORD_LEAVES):
        return []
    sig = ("bloom",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    tree.meters["bloom"] = 1.0
    return ["__bloom__"]


CAUSAL_RULES = [
    Rule(name="return_leaves", tag="story", apply=_r_return_leaves),
    Rule(name="drink", tag="physical", apply=_r_drink),
    Rule(name="bloom", tag="physical", apply=_r_bloom),
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
                produced.extend(sents)
    if narrate:
        for sentence in produced:
            if not sentence.startswith("__"):
                world.say(sentence)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def vessel_works(vessel: Vessel, tree: TreeKind) -> bool:
    return (not vessel.leaky) and vessel.capacity >= tree.need


def helper_reaches(helper: Helper, place: Place) -> bool:
    return place.terrain in helper.access


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for tree_id, tree in TREES.items():
        for place_id, place in PLACES.items():
            for vessel_id, vessel in VESSELS.items():
                for helper_id, helper in HELPERS.items():
                    if vessel_works(vessel, tree) and helper_reaches(helper, place):
                        combos.append((tree_id, place_id, vessel_id, helper_id))
    return combos


def explain_vessel(tree: TreeKind, vessel: Vessel) -> str:
    if vessel.leaky:
        return (
            f"(No story: {vessel.phrase} leaks, so no water would reach the {tree.label}. "
            f"The tree needs real water, not a pretend carrying trick.)"
        )
    return (
        f"(No story: {vessel.phrase} holds too little water for the thirsty {tree.label}. "
        f"Choose a vessel that can carry at least {tree.need} measures of water.)"
    )


def explain_helper(place: Place, helper: Helper) -> str:
    return (
        f"(No story: a {helper.kind_name} cannot reasonably reach {place.label}. "
        f"The helper must be able to cross {place.terrain} ground to return the missing leaves.)"
    )


def accepts_help(trait: str, helper: Helper) -> bool:
    return (trait in FEARLESS_TRAITS) or (not helper.feared)


def outcome_of(params: "StoryParams") -> str:
    helper = HELPERS[params.helper]
    return "restored_now" if accepts_help(params.trait, helper) else "restored_by_morning"


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, elder: Entity, tree_cfg: TreeKind) -> None:
    child.memes["care"] = 1.0
    world.say(
        f"In the days when village doors were latched with willow pegs, {child.id} lived where "
        f"every child watched {tree_cfg.phrase} for its morning gifts."
    )
    world.say(
        f"On good dawns, silver leaves fell from its branches, and each leaf carried a hard, shining word."
    )
    world.say(
        f"{child.id} had kept the finest three in a rag-wrapped packet: vocabulary, passive, and stop-gerund."
    )
    world.say(
        f"{elder.label_word.capitalize()} said those words were strange, but strange words were still words, "
        f"and a village grew wiser when its vocabulary grew wide."
    )


def silence(world: World, child: Entity, tree: Entity, place: Place) -> None:
    child.memes["worry"] = 1.0
    world.say(
        f"Then a dry wind came creeping over {place.label}, and the tree went still. "
        f"No leaf rang down. No branch whispered."
    )
    world.say(
        f"When {child.id} laid a palm against the bark, it felt warm and tired, as though the song inside "
        f"had been shut away in a passive little room."
    )


def task(world: World, elder: Entity, child: Entity, place: Place, vessel: Vessel, tree_cfg: TreeKind) -> None:
    world.say(
        f'"Take {vessel.phrase}," said {elder.label_word}. "Find {place.spring}, and carry water to the roots. '
        f'If root and word return together, the song may wake."'
    )
    world.say(
        f"So {child.id} set out by {place.path}, carrying hope in one hand and the {vessel.label} in the other."
    )


def inner_monologue(world: World, child: Entity, helper: Helper) -> None:
    if helper.feared:
        child.memes["fear"] = 1.0
        world.say(
            f'{helper.entrance} {child.id} froze. "Black wing, dark thing; is this the thief?" '
            f'{child.pronoun().capitalize()} wondered.'
        )
        world.say(
            f'Inside, a smaller voice answered, "If I turn back now, the tree stays dumb. '
            f'If I stay, I may learn what is true."'
        )
    else:
        child.memes["wonder"] = 1.0
        world.say(
            f'{helper.entrance} {child.id} blinked and thought, "This is no market road creature. '
            f'Something old is walking beside me today."'
        )


def offer_help(world: World, helper: Entity, helper_cfg: Helper) -> None:
    world.say(
        f'The {helper_cfg.kind_name} bowed over {helper_cfg.bundle} and spoke in rhyme: "{helper_cfg.rhyme}"'
    )


def accept_scene(world: World, child: Entity, helper: Entity, helper_cfg: Helper, vessel: Vessel, place: Place) -> None:
    child.memes["trust"] = 1.0
    child.memes["relief"] = 1.0
    helper.meters["guiding"] = 1.0
    world.facts["accepted_help"] = True
    world.say(
        f"{child.id} took a breath, gripped the {vessel.label}, and chose not to run."
    )
    world.say(
        f'"Come then," {child.pronoun()} said softly. The {helper_cfg.kind_name} led {child.pronoun("object")} to '
        f"{place.spring}, where the water rose clear and cold."
    )
    world.get("tree").meters["water"] = float(vessel.capacity)
    propagate(world, narrate=False)
    world.say(
        f"Together they poured the water at the roots. Then the {helper_cfg.kind_name} laid the silver leaves "
        f"against the bark one by one."
    )
    propagate(world, narrate=False)


def hesitate_scene(world: World, child: Entity, helper_cfg: Helper, vessel: Vessel, place: Place) -> None:
    child.memes["fear"] = max(child.memes["fear"], 1.0)
    world.say(
        f"But fear tugged harder than trust. {child.id} backed away, clutching the {vessel.label}, and said nothing."
    )
    world.say(
        f"The {helper_cfg.kind_name} did not snap or chase. It only watched while {child.id} hurried on to {place.spring}."
    )
    world.get("tree").meters["water"] = float(vessel.capacity)
    propagate(world, narrate=False)
    world.say(
        f"{child.id} poured the water around the roots alone. The tree gave one faint shiver, but no silver leaf came down."
    )


def twist_morning(world: World, child: Entity, helper: Entity, helper_cfg: Helper, tree_cfg: TreeKind, place: Place) -> None:
    child.memes["trust"] = 1.0
    child.memes["wonder"] = 1.0
    world.say(
        f"At dawn {child.id} returned and found the three silver leaves waiting in the crook of the trunk, dry and safe."
    )
    world.say(
        f"Only then did {child.pronoun()} understand the twist of the matter: the {helper_cfg.kind_name} had not stolen them at all. "
        f"It had carried them through the dry night so the wind would not tear them away."
    )
    propagate(world, narrate=False)
    world.say(
        f"Shame and gratitude warmed {child.pronoun('possessive')} face together, and {child.pronoun()} whispered thanks to the empty path."
    )


def wake_tree(world: World, child: Entity, tree_cfg: TreeKind) -> None:
    tree = world.get("tree")
    if tree.meters["bloom"] >= THRESHOLD:
        world.say(
            f"The bark gave a low hum. Then buds loosened, and {tree_cfg.blossom} opened as if dawn had been folded inside them."
        )
        world.say(
            f"Three silver leaves spun down at last. One read vocabulary, one read passive, and one read stop-gerund."
        )
        world.say(
            f'"Word by word and spring by spring, a thirsty root makes language sing," murmured the tree.'
        )
    elif tree.meters["voice"] >= THRESHOLD:
        world.say(
            f"The tree found enough breath for a whisper, but not yet for blossom or song."
        )


def ending_now(world: World, child: Entity, helper_cfg: Helper, place: Place) -> None:
    world.say(
        f'{child.id} laughed then, half from relief and half from wonder. "All night I feared a thief," '
        f'{child.pronoun()} said, "and all along I had met a keeper."'
    )
    world.say(place.closing)


def ending_morning(world: World, child: Entity, place: Place) -> None:
    world.say(
        f"From that day on, {child.id} listened longer before judging what looked dark or odd."
    )
    world.say(place.closing)


def tell(
    tree_cfg: TreeKind,
    place: Place,
    vessel: Vessel,
    helper_cfg: Helper,
    name: str = "Mara",
    gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "curious",
) -> World:
    world = World()
    child = world.add(Entity(id=name, kind="character", type=gender, role="child", traits=[trait], label=name))
    elder = world.add(Entity(id="Elder", kind="character", type=parent_type, role="elder", label="the elder"))
    tree = world.add(Entity(id="tree", kind="thing", type="tree", role="tree", label=tree_cfg.label))
    helper = world.add(Entity(id="helper", kind="thing", type="creature", role="helper", label=helper_cfg.label))
    vessel_ent = world.add(Entity(id="vessel", kind="thing", type="vessel", role="vessel", label=vessel.label))
    place_ent = world.add(Entity(id="place", kind="thing", type="place", role="place", label=place.label))

    # Explicit initialization for all rule-read values.
    tree.attrs["need"] = tree_cfg.need
    tree.meters["thirst"] = float(tree_cfg.need)
    tree.meters["water"] = 0.0
    tree.meters["voice"] = 0.0
    tree.meters["leaf_count"] = 0.0
    tree.meters["bloom"] = 0.0
    helper.meters["carrying_leaves"] = float(len(WORD_LEAVES))
    helper.meters["guiding"] = 0.0
    child.memes["trust"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["wonder"] = 0.0
    vessel_ent.meters["capacity"] = float(vessel.capacity)
    place_ent.attrs["terrain"] = place.terrain

    introduce(world, child, elder, tree_cfg)
    silence(world, child, tree, place)

    world.para()
    task(world, elder, child, place, vessel, tree_cfg)
    inner_monologue(world, child, helper_cfg)
    offer_help(world, helper, helper_cfg)

    world.para()
    if accepts_help(trait, helper_cfg):
        accept_scene(world, child, helper, helper_cfg, vessel, place)
        wake_tree(world, child, tree_cfg)
        world.facts["outcome"] = "restored_now"
        world.para()
        ending_now(world, child, helper_cfg, place)
    else:
        hesitate_scene(world, child, helper_cfg, vessel, place)
        twist_morning(world, child, helper, helper_cfg, tree_cfg, place)
        wake_tree(world, child, tree_cfg)
        world.facts["outcome"] = "restored_by_morning"
        world.para()
        ending_morning(world, child, place)

    world.facts.update(
        child=child,
        elder=elder,
        tree=tree,
        helper=helper,
        vessel=vessel,
        place=place,
        tree_cfg=tree_cfg,
        helper_cfg=helper_cfg,
        leaf_words=list(WORD_LEAVES),
        feared=helper_cfg.feared,
        trait=trait,
    )
    return world


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    tree: str
    place: str
    vessel: str
    helper: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
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


KNOWLEDGE = {
    "vocabulary": [
        (
            "What is vocabulary?",
            "Vocabulary is the group of words a person knows and can use. When your vocabulary grows, you have more words to think and speak with.",
        )
    ],
    "passive": [
        (
            "What does passive mean as a word?",
            "Passive can mean quiet or not taking action. In grammar, it can also describe a sentence where the thing receiving the action is put first.",
        )
    ],
    "stop-gerund": [
        (
            "What is stop-gerund in this story?",
            "In this tale, stop-gerund is one of the strange silver word-leaves. It sounds like an old grammar charm, which fits a folk tale about magical words.",
        )
    ],
    "crow": [
        (
            "Why are crows sometimes feared in tales?",
            "Crows are dark birds and can seem mysterious, so stories often make people suspicious of them. But in many tales, a crow can also be clever or helpful.",
        )
    ],
    "water": [
        (
            "Why does a thirsty tree need water?",
            "A tree needs water in its roots to stay alive and strong. Without enough water, leaves droop and the tree cannot grow well.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme happens when words end with the same or almost the same sound, like sing and spring. Rhymes make lines easier to remember and give them a song-like feeling.",
        )
    ],
}
KNOWLEDGE_ORDER = ["vocabulary", "passive", "stop-gerund", "crow", "water", "rhyme"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    tree_cfg = world.facts["tree_cfg"]
    place = world.facts["place"]
    helper_cfg = world.facts["helper_cfg"]
    outcome = world.facts["outcome"]
    twist_bit = (
        f"Use an inner monologue where {child.id} first mistrusts the {helper_cfg.kind_name}, "
        f"then reveal the twist that it was protecting the missing leaves."
    )
    end_bit = (
        "End with the tree singing again that very night."
        if outcome == "restored_now"
        else "End with a morning-after twist and a gentler, wiser ending."
    )
    return [
        'Write a short folk-tale for a 3-to-5-year-old that includes the words "vocabulary", "passive", and "stop-gerund".',
        f"Tell a village tale about a child carrying water to a silent {tree_cfg.label} at {place.label}, with rhyme in the helper's speech.",
        f"{twist_bit} {end_bit}",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    elder = world.facts["elder"]
    tree = world.facts["tree"]
    tree_cfg = world.facts["tree_cfg"]
    helper_cfg = world.facts["helper_cfg"]
    vessel = world.facts["vessel"]
    place = world.facts["place"]
    outcome = world.facts["outcome"]
    leaf_words = world.facts["leaf_words"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child from a village with a magical {tree_cfg.label}, and the strange {helper_cfg.kind_name} met on the way. "
            f"The elder sends {child.pronoun('object')} to help the silent tree.",
        ),
        (
            "Why did the child carry water to the tree?",
            f"The tree had gone silent after a dry wind, and it was thirsty. "
            f"{elder.label_word.capitalize()} believed water at the roots might wake its voice again.",
        ),
        (
            f"What was {child.id} thinking when the {helper_cfg.kind_name} appeared?",
            (
                f"{child.id} was deciding whether the creature was a thief or a helper. "
                f"The inner monologue matters because {child.pronoun()} had to choose between fear and truth before the twist could be understood."
            ),
        ),
        (
            "What words were written on the silver leaves?",
            f"They were {leaf_words[0]}, {leaf_words[1]}, and {leaf_words[2]}. "
            f"The story treats them as precious word-gifts, showing that even odd words belong in a village's treasure of speech.",
        ),
    ]
    if outcome == "restored_now":
        qa.append(
            (
                f"How was the problem solved?",
                f"{child.id} trusted the {helper_cfg.kind_name}, carried water from {place.spring}, and helped return the silver leaves to the bark. "
                f"Because the roots drank and the leaves came home together, the tree bloomed and sang again at once.",
            )
        )
        qa.append(
            (
                "What was the twist?",
                f"The creature that looked suspicious was actually keeping the leaves safe. "
                f"{child.id} first feared a thief, but discovered a keeper instead.",
            )
        )
    else:
        qa.append(
            (
                "How was the problem solved if the child was too afraid at first?",
                f"{child.id} still watered the tree, which gave it strength, but the song stayed faint until dawn. "
                f"In the morning the missing leaves were found safe on the trunk, proving the {helper_cfg.kind_name} had protected them through the night.",
            )
        )
        qa.append(
            (
                "What did the child learn at the end?",
                f"{child.id} learned not to judge too quickly by a dark shape or a strange face. "
                f"The twist taught {child.pronoun('object')} that truth can hide under surprising fur, feather, or mud.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    helper_cfg = world.facts["helper_cfg"]
    tags = {"vocabulary", "passive", "stop-gerund", "water", "rhyme"}
    if helper_cfg.id == "crow":
        tags.add("crow")
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} leaves_returned={world.facts.get('leaves_returned')} accepted_help={world.facts.get('accepted_help')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
usable_vessel(V, T) :- vessel(V), tree(T), not leaky(V), capacity(V, C), need(T, N), C >= N.
reachable(H, P)     :- helper(H), place(P), terrain(P, R), can_cross(H, R).
valid(T, P, V, H)   :- tree(T), place(P), vessel(V), helper(H),
                       usable_vessel(V, T), reachable(H, P).

fearless(Trait)     :- trait_name(Trait), fearless_trait(Trait).
accept_help         :- chosen_helper(H), not feared(H).
accept_help         :- chosen_trait(T), chosen_helper(H), feared(H), fearless(T).
outcome(restored_now)       :- accept_help.
outcome(restored_by_morning) :- not accept_help.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tree_id, tree in TREES.items():
        lines.append(asp.fact("tree", tree_id))
        lines.append(asp.fact("need", tree_id, tree.need))
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("terrain", place_id, place.terrain))
    for vessel_id, vessel in VESSELS.items():
        lines.append(asp.fact("vessel", vessel_id))
        lines.append(asp.fact("capacity", vessel_id, vessel.capacity))
        if vessel.leaky:
            lines.append(asp.fact("leaky", vessel_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        if helper.feared:
            lines.append(asp.fact("feared", helper_id))
        for terrain in sorted(helper.access):
            lines.append(asp.fact("can_cross", helper_id, terrain))
    for trait in TRAITS:
        lines.append(asp.fact("trait_name", trait))
    for trait in sorted(FEARLESS_TRAITS):
        lines.append(asp.fact("fearless_trait", trait))
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
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid combos match ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve_params failure for seed {seed}.")
            break

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
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        tree="pear",
        place="hill",
        vessel="jug",
        helper="crow",
        name="Mara",
        gender="girl",
        parent="mother",
        trait="curious",
    ),
    StoryParams(
        tree="linden",
        place="island",
        vessel="bucket",
        helper="otter",
        name="Ivo",
        gender="boy",
        parent="father",
        trait="steady",
    ),
    StoryParams(
        tree="plum",
        place="marsh",
        vessel="jug",
        helper="mole",
        name="Anya",
        gender="girl",
        parent="mother",
        trait="timid",
    ),
    StoryParams(
        tree="pear",
        place="hill",
        vessel="bucket",
        helper="goat",
        name="Bram",
        gender="boy",
        parent="father",
        trait="kind",
    ),
]


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a thirsty word tree, a feared helper, and a folk-tale twist."
    )
    ap.add_argument("--tree", choices=TREES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tree and args.vessel:
        tree = TREES[args.tree]
        vessel = VESSELS[args.vessel]
        if not vessel_works(vessel, tree):
            raise StoryError(explain_vessel(tree, vessel))
    if args.place and args.helper:
        place = PLACES[args.place]
        helper = HELPERS[args.helper]
        if not helper_reaches(helper, place):
            raise StoryError(explain_helper(place, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.tree is None or combo[0] == args.tree)
        and (args.place is None or combo[1] == args.place)
        and (args.vessel is None or combo[2] == args.vessel)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    tree_id, place_id, vessel_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        tree=tree_id,
        place=place_id,
        vessel=vessel_id,
        helper=helper_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.tree not in TREES:
        raise StoryError(f"(Unknown tree: {params.tree})")
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.vessel not in VESSELS:
        raise StoryError(f"(Unknown vessel: {params.vessel})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.gender})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent: {params.parent})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")

    tree_cfg = TREES[params.tree]
    place = PLACES[params.place]
    vessel = VESSELS[params.vessel]
    helper_cfg = HELPERS[params.helper]

    if not vessel_works(vessel, tree_cfg):
        raise StoryError(explain_vessel(tree_cfg, vessel))
    if not helper_reaches(helper_cfg, place):
        raise StoryError(explain_helper(place, helper_cfg))

    world = tell(
        tree_cfg=tree_cfg,
        place=place,
        vessel=vessel,
        helper_cfg=helper_cfg,
        name=params.name,
        gender=params.gender,
        parent_type=params.parent,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (tree, place, vessel, helper) combos:\n")
        for tree, place, vessel, helper in combos:
            print(f"  {tree:7} {place:7} {vessel:7} {helper}")
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
            header = f"### {p.name}: {p.tree} at {p.place} with {p.vessel} and {p.helper} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
