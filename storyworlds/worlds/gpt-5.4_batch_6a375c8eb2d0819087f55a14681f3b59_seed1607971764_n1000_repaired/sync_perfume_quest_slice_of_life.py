#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sync_perfume_quest_slice_of_life.py
==============================================================

A small slice-of-life storyworld about a child on a tiny household quest:
making a simple flower perfume to welcome a loved one home.

The story shape is state-driven:
- a child chooses a flower and a bottle for the perfume quest
- they and a helper prepare it together
- the middle turn comes while carrying it through the house
- if they move in sync, the perfume reaches the room safely
- if they hurry out of sync on a tricky route, some spills, and they rescue the
  quest by turning the remaining perfume into a smaller but heartfelt gift

The world has a Python reasonableness gate plus an inline ASP twin:
- only fragrant flowers make a believable perfume
- an open cup is refused as a perfume gift container
- narrow bottles need a real filter, or petals clog them

Run:
    python storyworlds/worlds/gpt-5.4/sync_perfume_quest_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/sync_perfume_quest_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/sync_perfume_quest_slice_of_life.py --qa
    python storyworlds/worlds/gpt-5.4/sync_perfume_quest_slice_of_life.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman", "grandmother"}
        male = {"boy", "father", "uncle", "man", "grandfather"}
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
    phrase: str
    color: str
    scent_word: str
    fragrant: bool = True
    strength: int = 2
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
class Vessel:
    id: str
    label: str
    phrase: str
    narrow: bool = False
    sealed: bool = False
    suitable: bool = True
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
class FilterTool:
    id: str
    label: str
    phrase: str
    strains: bool = True
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
class Route:
    id: str
    label: str
    place_phrase: str
    bumpy: bool = False
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
class Goal:
    id: str
    visitor_label: str
    room_label: str
    welcome_line: str
    ending_image: str
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


def _r_perfume_strength(world: World) -> list[str]:
    out: list[str] = []
    jar = world.get("mixture")
    if jar.meters["petals_crushed"] < THRESHOLD:
        return out
    if not world.facts.get("flower_fragrant", False):
        sig = ("weak", "mixture")
        if sig not in world.fired:
            world.fired.add(sig)
            jar.meters["fragrance"] += 0.5
        return out
    sig = ("fragrant", "mixture")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    jar.meters["fragrance"] += float(world.facts.get("flower_strength", 2))
    out.append("__fragrance__")
    return out


def _r_clog(world: World) -> list[str]:
    out: list[str] = []
    jar = world.get("mixture")
    vessel = world.get("vessel")
    if jar.meters["poured"] < THRESHOLD:
        return out
    if not world.facts.get("needs_filter", False):
        return out
    if world.facts.get("used_filter", False):
        return out
    sig = ("clog", vessel.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    vessel.meters["clogged"] += 1
    out.append("__clog__")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    vessel = world.get("vessel")
    if vessel.meters["carried"] < THRESHOLD:
        return out
    if not world.facts.get("route_bumpy", False):
        return out
    if world.facts.get("sync_mode") == "together":
        return out
    sig = ("spill", vessel.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    vessel.meters["spill"] += 1
    vessel.meters["liquid"] = max(0.0, vessel.meters["liquid"] - 1.0)
    out.append("__spill__")
    return out


CAUSAL_RULES = [
    Rule(name="perfume_strength", tag="physical", apply=_r_perfume_strength),
    Rule(name="clog", tag="physical", apply=_r_clog),
    Rule(name="spill", tag="physical", apply=_r_spill),
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


def flower_works(flower: Flower) -> bool:
    return flower.fragrant and flower.strength >= 2


def vessel_works(vessel: Vessel) -> bool:
    return vessel.suitable


def filter_works(vessel: Vessel, filter_tool: FilterTool) -> bool:
    if not vessel.narrow:
        return True
    return filter_tool.strains


def valid_combo(flower: Flower, vessel: Vessel, filter_tool: FilterTool) -> bool:
    return flower_works(flower) and vessel_works(vessel) and filter_works(vessel, filter_tool)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for flower_id, flower in FLOWERS.items():
        for vessel_id, vessel in VESSELS.items():
            for filter_id, filter_tool in FILTERS.items():
                if valid_combo(flower, vessel, filter_tool):
                    combos.append((flower_id, vessel_id, filter_id))
    return combos


def explain_rejection(flower: Flower, vessel: Vessel, filter_tool: FilterTool) -> str:
    if not flower_works(flower):
        return (
            f"(No story: {flower.phrase} would not make a strong enough perfume here. "
            f"Choose a fragrant flower like rose, lavender, or jasmine.)"
        )
    if not vessel_works(vessel):
        return (
            f"(No story: {vessel.phrase} is not a sensible perfume container for a gift. "
            f"An open cup would spill before the quest was done.)"
        )
    if not filter_works(vessel, filter_tool):
        return (
            f"(No story: {vessel.phrase} has a narrow top, so petals need to be strained first. "
            f"Choose muslin cloth or a tea strainer.)"
        )
    return "(No story: this combination is not reasonable.)"


def outcome_of(params: "StoryParams") -> str:
    route = ROUTES[params.route]
    vessel = VESSELS[params.vessel]
    if vessel.narrow and not FILTERS[params.filter].strains:
        return "clogged"
    if route.bumpy and params.sync_mode == "rushed":
        return "spilled"
    return "welcomed"


def predict_carry(world: World) -> dict:
    sim = world.copy()
    sim.get("vessel").meters["carried"] += 1
    propagate(sim, narrate=False)
    vessel = sim.get("vessel")
    return {
        "spill": vessel.meters["spill"],
        "liquid": vessel.meters["liquid"],
    }


def introduce(world: World, kid: Entity, helper: Entity, goal: Goal) -> None:
    kid.memes["joy"] += 1
    helper.memes["care"] += 1
    world.say(
        f"After lunch, {kid.id} decided on a small quest. {kid.pronoun().capitalize()} wanted to make "
        f"a homemade perfume to welcome {goal.visitor_label} and leave {goal.room_label} feeling special."
    )
    world.say(
        f"{helper.id} was folding tea towels nearby and looked up with a smile. "
        f'"A quest can be done," {helper.pronoun()} said, "if we do it one calm step at a time."'
    )


def choose_supplies(world: World, kid: Entity, flower: Flower, vessel: Vessel, filter_tool: FilterTool) -> None:
    world.say(
        f"{kid.id} picked {flower.phrase}, a little bowl of warm water, {vessel.phrase}, "
        f"and {filter_tool.phrase} from the kitchen drawer."
    )
    world.say(
        f"The {flower.color} petals looked soft in {kid.pronoun('possessive')} hands, and even before anything was mixed, "
        f"they carried a light {flower.scent_word} smell."
    )


def make_mixture(world: World, kid: Entity, helper: Entity, flower: Flower) -> None:
    mixture = world.get("mixture")
    mixture.meters["petals_crushed"] += 1
    kid.memes["focus"] += 1
    helper.memes["care"] += 1
    propagate(world, narrate=False)
    if mixture.meters["fragrance"] >= THRESHOLD:
        world.say(
            f"Together they pressed the {flower.label} petals into the warm water. "
            f"Soon the little bowl smelled gently of {flower.scent_word}, and the kitchen air changed."
        )


def strain(world: World, kid: Entity, filter_tool: FilterTool, vessel: Vessel) -> None:
    world.facts["used_filter"] = filter_tool.strains
    world.get("mixture").meters["strained"] += 1 if filter_tool.strains else 0
    if filter_tool.strains:
        world.say(
            f"{kid.id} poured the flower water through {filter_tool.phrase}. "
            f"The soft bits stayed behind, and the clear perfume slipped neatly into {vessel.phrase}."
        )
    else:
        world.say(
            f"{kid.id} skipped the straining step and tipped the flower water straight toward {vessel.phrase}."
        )
    world.get("mixture").meters["poured"] += 1
    world.get("vessel").meters["liquid"] += 2
    propagate(world, narrate=False)


def warn_about_steps(world: World, helper: Entity, kid: Entity, route: Route) -> None:
    pred = predict_carry(world)
    world.facts["predicted_spill"] = pred["spill"]
    if route.bumpy:
        world.say(
            f'{helper.id} glanced toward {route.place_phrase}. "{route.label.capitalize()} can wobble a bottle," '
            f'{helper.pronoun()} said. "Let us walk in sync."'
        )
    else:
        world.say(
            f'"The last part is easy," {helper.id} said. "Still, the quest will go best if we carry it in sync."'
        )


def carry(world: World, kid: Entity, helper: Entity, route: Route, sync_mode: str) -> None:
    world.get("vessel").meters["carried"] += 1
    if sync_mode == "together":
        kid.memes["trust"] += 1
        helper.memes["trust"] += 1
        world.say(
            f"{kid.id} and {helper.id} went {route.place_phrase} side by side, their steps small and in sync."
        )
    else:
        kid.memes["hurry"] += 1
        world.say(
            f"But the quest felt so exciting that {kid.id} hurried ahead {route.place_phrase}, and the two of them fell out of sync."
        )
    propagate(world, narrate=False)


def describe_turn(world: World, vessel: Vessel) -> None:
    if vessel.meters["clogged"] >= THRESHOLD:
        world.say(
            f"When {world.facts['kid'].id} pressed the top of the {vessel.label}, nothing came out but a stubborn little snort. "
            f"A petal bit had clogged the opening."
        )
    elif vessel.meters["spill"] >= THRESHOLD:
        world.say(
            f"At the middle of the trip, the bottle tipped and a bright little ribbon of perfume splashed onto their hands. "
            f"The room did not smell ruined, but the quest suddenly felt much smaller and more precious."
        )


def resolve_welcome(world: World, kid: Entity, helper: Entity, goal: Goal, vessel: Vessel) -> None:
    kid.memes["pride"] += 1
    helper.memes["relief"] += 1
    room = world.get("room")
    room.meters["fragrant"] += 1
    world.say(
        f"In {goal.room_label}, {kid.id} gave one careful spray into the air. "
        f"The perfume drifted softly through the room, and the whole place felt ready."
    )
    world.say(goal.welcome_line)
    world.say(goal.ending_image)


def resolve_small_gift(world: World, kid: Entity, helper: Entity, goal: Goal, flower: Flower) -> None:
    kid.memes["pride"] += 1
    helper.memes["relief"] += 1
    room = world.get("room")
    room.meters["fragrant"] += 1
    world.say(
        f"{helper.id} squeezed {kid.pronoun('possessive')} fingers gently. "
        f'"We still have enough for kindness," {helper.pronoun()} said.'
    )
    world.say(
        f"So instead of scenting the whole room, they dabbed the remaining {flower.scent_word} perfume onto a clean handkerchief "
        f"and laid it on the pillow in {goal.room_label}."
    )
    world.say(
        f"When {goal.visitor_label} arrived, the first thing {kid.pronoun()} noticed was the small smile that came at once."
    )
    world.say(goal.ending_image)


def clear_clog(world: World, kid: Entity, helper: Entity, filter_tool: FilterTool, vessel: Vessel, goal: Goal) -> None:
    kid.memes["worry"] += 1
    helper.memes["care"] += 1
    world.say(
        f'{helper.id} did not scold. "{filter_tool.label.capitalize()} first," {helper.pronoun()} reminded {kid.pronoun("object")}. '
        f'"That is what keeps small jobs gentle."'
    )
    world.say(
        f"They poured the mixture back, strained it properly, and this time the {vessel.label} behaved."
    )
    resolve_welcome(world, kid, helper, goal, vessel)
def tell(
    flower: Flower,
    vessel: Vessel,
    filter_tool: FilterTool,
    route: Route,
    sync_mode: SyncMode,
    kid_name: str,
    kid_type: KidType,
    helper_name: str,
    helper_type: HelperType,
    goal=None,
) -> World:
    world = World()
    kid = world.add(Entity(id=kid_name, kind="character", type=kid_type, role="kid", label=kid_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper", label=helper_name))
    world.add(Entity(id="room", type="room", label=goal.room_label))
    world.add(Entity(id="mixture", type="mixture", label="flower water"))
    world.add(Entity(id="vessel", type="vessel", label=vessel.label))

    world.facts.update(
        flower=flower,
        vessel_cfg=vessel,
        filter_cfg=filter_tool,
        route=route,
        goal=goal,
        kid=kid,
        helper=helper,
        flower_fragrant=flower.fragrant,
        flower_strength=flower.strength,
        needs_filter=vessel.narrow,
        used_filter=False,
        route_bumpy=route.bumpy,
        sync_mode=sync_mode,
    )

    introduce(world, kid, helper, goal)
    choose_supplies(world, kid, flower, vessel, filter_tool)

    world.para()
    make_mixture(world, kid, helper, flower)
    strain(world, kid, filter_tool, vessel)
    warn_about_steps(world, helper, kid, route)

    world.para()
    carry(world, kid, helper, route, sync_mode)
    describe_turn(world, world.get("vessel"))

    outcome = outcome_of(
        StoryParams(
            flower=flower.id,
            vessel=vessel.id,
            filter=filter_tool.id,
            route=route.id,
            goal=goal.id,
            sync_mode=sync_mode,
            kid_name=kid_name,
            kid_type=kid_type,
            helper_name=helper_name,
            helper_type=helper_type,
            seed=None,
        )
    )
    if outcome == "clogged":
        world.para()
        clear_clog(world, kid, helper, filter_tool, vessel, goal)
    elif outcome == "spilled":
        world.para()
        resolve_small_gift(world, kid, helper, goal, flower)
    else:
        world.para()
        resolve_welcome(world, kid, helper, goal, vessel)

    world.facts.update(
        outcome=outcome,
        welcomed=outcome in {"welcomed", "clogged"},
        spill=world.get("vessel").meters["spill"],
        clogged=world.get("vessel").meters["clogged"],
        liquid_left=world.get("vessel").meters["liquid"],
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


FLOWERS = {
    "rose": Flower(
        id="rose",
        label="rose",
        phrase="pink rose petals",
        color="pink",
        scent_word="sweet-rose",
        fragrant=True,
        strength=3,
        tags={"flower", "perfume", "rose"},
    ),
    "lavender": Flower(
        id="lavender",
        label="lavender",
        phrase="purple lavender sprigs",
        color="purple",
        scent_word="calm lavender",
        fragrant=True,
        strength=2,
        tags={"flower", "perfume", "lavender"},
    ),
    "jasmine": Flower(
        id="jasmine",
        label="jasmine",
        phrase="white jasmine blossoms",
        color="white",
        scent_word="soft jasmine",
        fragrant=True,
        strength=3,
        tags={"flower", "perfume", "jasmine"},
    ),
    "marigold": Flower(
        id="marigold",
        label="marigold",
        phrase="orange marigold petals",
        color="orange",
        scent_word="green marigold",
        fragrant=False,
        strength=1,
        tags={"flower"},
    ),
}

VESSELS = {
    "spray_bottle": Vessel(
        id="spray_bottle",
        label="spray bottle",
        phrase="a little glass spray bottle",
        narrow=True,
        sealed=True,
        suitable=True,
        tags={"bottle", "spray"},
    ),
    "vial": Vessel(
        id="vial",
        label="stoppered vial",
        phrase="a tiny stoppered vial",
        narrow=True,
        sealed=True,
        suitable=True,
        tags={"bottle", "vial"},
    ),
    "jar": Vessel(
        id="jar",
        label="small jar",
        phrase="a small jar with a lid",
        narrow=False,
        sealed=True,
        suitable=True,
        tags={"jar"},
    ),
    "cup": Vessel(
        id="cup",
        label="teacup",
        phrase="a teacup with no lid",
        narrow=False,
        sealed=False,
        suitable=False,
        tags={"cup"},
    ),
}

FILTERS = {
    "muslin": FilterTool(
        id="muslin",
        label="muslin cloth",
        phrase="a square of muslin cloth",
        strains=True,
        tags={"filter", "cloth"},
    ),
    "strainer": FilterTool(
        id="strainer",
        label="tea strainer",
        phrase="a tea strainer",
        strains=True,
        tags={"filter", "strainer"},
    ),
    "none": FilterTool(
        id="none",
        label="no filter",
        phrase="no filter at all",
        strains=False,
        tags=set(),
    ),
}

ROUTES = {
    "hall": Route(
        id="hall",
        label="the hall",
        place_phrase="through the hall",
        bumpy=False,
        tags={"home"},
    ),
    "stairs": Route(
        id="stairs",
        label="the stairs",
        place_phrase="up the stairs",
        bumpy=True,
        tags={"stairs"},
    ),
    "porch": Route(
        id="porch",
        label="the back porch",
        place_phrase="across the back porch",
        bumpy=False,
        tags={"home"},
    ),
}

GOALS = {
    "grandma_visit": Goal(
        id="grandma_visit",
        visitor_label="Grandma",
        room_label="the guest room",
        welcome_line='"It smells like someone was thinking of me," Grandma said when she stepped inside.',
        ending_image="The curtain moved in the late breeze, and the room held a quiet perfume that felt like a hug.",
        tags={"family", "guest"},
    ),
    "aunt_visit": Goal(
        id="aunt_visit",
        visitor_label="Auntie June",
        room_label="the little spare room",
        welcome_line='"Oh, what a lovely welcome," Auntie June said, touching the bedspread with one hand.',
        ending_image="The afternoon light lay in a soft square on the bed, and the room smelled gentle and ready.",
        tags={"family", "guest"},
    ),
    "neighbor_thankyou": Goal(
        id="neighbor_thankyou",
        visitor_label="Mrs. Lin from next door",
        room_label="the sunroom",
        welcome_line='"You made this for me?" Mrs. Lin asked, smiling so warmly that the whole room seemed brighter.',
        ending_image="On the side table, the little gift waited beside a plate of biscuits, smelling fresh and homemade.",
        tags={"neighbor", "gift"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Anna", "Nora", "Ella", "Zoe"]
BOY_NAMES = ["Leo", "Ben", "Sam", "Theo", "Max", "Eli"]


KNOWLEDGE = {
    "perfume": [
        (
            "What is perfume?",
            "Perfume is a liquid with a pleasant smell. People use a little of it to make a room, cloth, or person smell nice."
        )
    ],
    "sync": [
        (
            "What does it mean to move in sync?",
            "It means two people are moving together in the same rhythm or at the same time. That can make carrying something easier and steadier."
        )
    ],
    "rose": [
        (
            "Why do roses smell strong?",
            "Roses make scented oils inside their petals. That is why even a few petals can smell sweet."
        )
    ],
    "lavender": [
        (
            "What is lavender?",
            "Lavender is a purple flowering plant with a calm, clean smell. People often use it to make rooms or cloth smell fresh."
        )
    ],
    "jasmine": [
        (
            "What is jasmine?",
            "Jasmine is a flower with a soft, rich smell. A little jasmine scent can travel a long way."
        )
    ],
    "filter": [
        (
            "Why do you strain flower water?",
            "You strain flower water to catch the petal bits. That helps the liquid stay smooth and keeps small bottle tops from clogging."
        )
    ],
    "stairs": [
        (
            "Why is carrying a bottle on stairs tricky?",
            "Stairs make your body go up and down, so a bottle can wobble if you hurry. Slow steps help keep the liquid inside."
        )
    ],
}
KNOWLEDGE_ORDER = ["perfume", "sync", "rose", "lavender", "jasmine", "filter", "stairs"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    kid = f["kid"]
    goal = f["goal"]
    flower = f["flower"]
    return [
        f'Write a slice-of-life quest story for a 3-to-5-year-old that includes the words "sync" and "perfume".',
        f"Tell a gentle home story where {kid.id} makes a small perfume to welcome {goal.visitor_label}, and the middle turn depends on whether the helpers move in sync.",
        f"Write a simple quest about {flower.label} petals, careful hands, and a homemade gift that changes how {goal.room_label} feels at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid = f["kid"]
    helper = f["helper"]
    goal = f["goal"]
    flower = f["flower"]
    vessel = f["vessel_cfg"]
    route = f["route"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "What was the quest in the story?",
            f"The quest was to make a homemade perfume and carry it to {goal.room_label} before {goal.visitor_label} arrived. It was a small household job, but it mattered because {kid.id} wanted the room to feel welcoming."
        ),
        (
            f"Why did {helper.id} tell {kid.id} to move in sync?",
            f"{helper.id} wanted the bottle to stay steady while they carried it {route.place_phrase}. Moving in sync helped them protect the perfume instead of sloshing or spilling it."
        ),
        (
            f"What did {kid.id} use to make the perfume?",
            f"{kid.id} used {flower.phrase}, warm water, and {vessel.phrase}. Those simple things turned an ordinary afternoon into a careful little project."
        ),
    ]
    if outcome == "welcomed":
        qa.append(
            (
                "How did the story end?",
                f"It ended with the perfume reaching {goal.room_label} safely and making the room smell gentle and ready. The ending shows that calm teamwork helped the quest succeed."
            )
        )
    elif outcome == "spilled":
        qa.append(
            (
                "What went wrong, and how did they fix it?",
                f"Some perfume spilled because {kid.id} hurried and the trip went out of sync on a tricky route. They fixed the quest by turning the remaining perfume into a smaller gift, so the kindness still reached {goal.visitor_label}."
            )
        )
    elif outcome == "clogged":
        qa.append(
            (
                "Why did the bottle stop working at first?",
                f"The bottle clogged because petal bits had not been strained out before the perfume was poured in. After they filtered it properly, the perfume could come out smoothly."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"perfume", "sync"}
    flower = world.facts["flower"]
    if flower.id in {"rose", "lavender", "jasmine"}:
        tags.add(flower.id)
    if world.facts["vessel_cfg"].narrow:
        tags.add("filter")
    if world.facts["route"].bumpy:
        tags.add("stairs")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    flower: str
    vessel: str
    filter: str
    route: str
    goal: str
    sync_mode: str
    kid_name: str
    kid_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        flower="rose",
        vessel="spray_bottle",
        filter="muslin",
        route="stairs",
        goal="grandma_visit",
        sync_mode="together",
        kid_name="Mia",
        kid_type="girl",
        helper_name="Dad",
        helper_type="father",
        seed=None,
    ),
    StoryParams(
        flower="lavender",
        vessel="jar",
        filter="none",
        route="hall",
        goal="aunt_visit",
        sync_mode="together",
        kid_name="Ben",
        kid_type="boy",
        helper_name="Mom",
        helper_type="mother",
        seed=None,
    ),
    StoryParams(
        flower="jasmine",
        vessel="vial",
        filter="strainer",
        route="stairs",
        goal="neighbor_thankyou",
        sync_mode="rushed",
        kid_name="Anna",
        kid_type="girl",
        helper_name="Grandpa",
        helper_type="grandfather",
        seed=None,
    ),
    StoryParams(
        flower="rose",
        vessel="spray_bottle",
        filter="none",
        route="porch",
        goal="grandma_visit",
        sync_mode="together",
        kid_name="Leo",
        kid_type="boy",
        helper_name="Mom",
        helper_type="mother",
        seed=None,
    ),
]

ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
usable_flower(F) :- flower(F), fragrant(F), strength(F,S), S >= 2.
usable_vessel(V) :- vessel(V), suitable(V).
good_filter(V,T) :- vessel(V), not narrow(V), filter(T).
good_filter(V,T) :- narrow(V), filter(T), strains(T).
valid(F,V,T) :- usable_flower(F), usable_vessel(V), good_filter(V,T).

% --- outcome model ---------------------------------------------------------
clogged :- chosen_vessel(V), narrow(V), chosen_filter(T), not strains(T).
spilled :- not clogged, chosen_route(R), bumpy(R), sync_mode(rushed).
welcomed :- not clogged, not spilled.

outcome(clogged) :- clogged.
outcome(spilled) :- spilled.
outcome(welcomed) :- welcomed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for fid, flower in FLOWERS.items():
        lines.append(asp.fact("flower", fid))
        if flower.fragrant:
            lines.append(asp.fact("fragrant", fid))
        lines.append(asp.fact("strength", fid, flower.strength))
    for vid, vessel in VESSELS.items():
        lines.append(asp.fact("vessel", vid))
        if vessel.narrow:
            lines.append(asp.fact("narrow", vid))
        if vessel.suitable:
            lines.append(asp.fact("suitable", vid))
    for tid, tool in FILTERS.items():
        lines.append(asp.fact("filter", tid))
        if tool.strains:
            lines.append(asp.fact("strains", tid))
    for rid, route in ROUTES.items():
        lines.append(asp.fact("route", rid))
        if route.bumpy:
            lines.append(asp.fact("bumpy", rid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_vessel", params.vessel),
            asp.fact("chosen_filter", params.filter),
            asp.fact("chosen_route", params.route),
            asp.fact("sync_mode", params.sync_mode),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    found = asp.atoms(model, "outcome")
    return found[0][0] if found else "?"


def asp_verify() -> int:
    rc = 0
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child makes a homemade perfume on a gentle household quest."
    )
    ap.add_argument("--flower", choices=FLOWERS)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--filter", choices=FILTERS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--sync-mode", choices=["together", "rushed"])
    ap.add_argument("--kid-name")
    ap.add_argument("--kid-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def helper_name_for(helper_type: str) -> str:
    return {
        "mother": "Mom",
        "father": "Dad",
        "grandmother": "Grandma",
        "grandfather": "Grandpa",
    }[helper_type]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.flower and args.vessel and args.filter:
        flower = FLOWERS[args.flower]
        vessel = VESSELS[args.vessel]
        filter_tool = FILTERS[args.filter]
        if not valid_combo(flower, vessel, filter_tool):
            raise StoryError(explain_rejection(flower, vessel, filter_tool))

    combos = [
        combo for combo in valid_combos()
        if (args.flower is None or combo[0] == args.flower)
        and (args.vessel is None or combo[1] == args.vessel)
        and (args.filter is None or combo[2] == args.filter)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    flower_id, vessel_id, filter_id = rng.choice(sorted(combos))
    route_id = args.route or rng.choice(sorted(ROUTES))
    goal_id = args.goal or rng.choice(sorted(GOALS))
    sync_mode = args.sync_mode or rng.choice(["together", "rushed"])
    kid_type = args.kid_type or rng.choice(["girl", "boy"])
    kid_name = args.kid_name or rng.choice(GIRL_NAMES if kid_type == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(["mother", "father", "grandmother", "grandfather"])
    helper_name = helper_name_for(helper_type)

    return StoryParams(
        flower=flower_id,
        vessel=vessel_id,
        filter=filter_id,
        route=route_id,
        goal=goal_id,
        sync_mode=sync_mode,
        kid_name=kid_name,
        kid_type=kid_type,
        helper_name=helper_name,
        helper_type=helper_type,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.flower not in FLOWERS:
        raise StoryError(f"(Unknown flower: {params.flower})")
    if params.vessel not in VESSELS:
        raise StoryError(f"(Unknown vessel: {params.vessel})")
    if params.filter not in FILTERS:
        raise StoryError(f"(Unknown filter: {params.filter})")
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route: {params.route})")
    if params.goal not in GOALS:
        raise StoryError(f"(Unknown goal: {params.goal})")
    if params.sync_mode not in {"together", "rushed"}:
        raise StoryError(f"(Unknown sync mode: {params.sync_mode})")

    flower = FLOWERS[params.flower]
    vessel = VESSELS[params.vessel]
    filter_tool = FILTERS[params.filter]
    if not valid_combo(flower, vessel, filter_tool):
        raise StoryError(explain_rejection(flower, vessel, filter_tool))

    world = tell(
        goal=GOALS[params.goal],
        flower=flower,
        vessel=vessel,
        filter_tool=filter_tool,
        route=ROUTES[params.route],
        sync_mode=params.sync_mode,
        kid_name=params.kid_name,
        kid_type=params.kid_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
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
        print(f"{len(combos)} compatible (flower, vessel, filter) combos:\n")
        for flower, vessel, filter_tool in combos:
            print(f"  {flower:10} {vessel:12} {filter_tool}")
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
            header = (
                f"### {p.kid_name}: {p.flower} perfume quest "
                f"({p.vessel}, {p.route}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
