#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/oomph_twist_adventure.py
==================================================

A standalone story world for a tiny adventure tale with a twist: two children
follow a map toward "treasure," meet one sensible physical obstacle, and discover
that the treasure is something warmer and more surprising than coins.

The world is constraint-checked. A barrier has a required method and resistance;
a tool must actually suit that barrier, and the children's combined oomph must be
enough to make progress. The prose is driven by simulated state: excitement,
doubt, teamwork, effort, the barrier opening, and the final surprise.

Run it
------
    python storyworlds/worlds/gpt-5.4/oomph_twist_adventure.py
    python storyworlds/worlds/gpt-5.4/oomph_twist_adventure.py --trail orchard --barrier gate --tool red_wagon
    python storyworlds/worlds/gpt-5.4/oomph_twist_adventure.py --barrier brambles --tool branch_lever
    python storyworlds/worlds/gpt-5.4/oomph_twist_adventure.py --all
    python storyworlds/worlds/gpt-5.4/oomph_twist_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/oomph_twist_adventure.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/oomph_twist_adventure.py --json
    python storyworlds/worlds/gpt-5.4/oomph_twist_adventure.py --verify
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Trail:
    id: str
    place: str
    opening: str
    path_line: str
    marker: str
    affords: set[str] = field(default_factory=set)
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
class Barrier:
    id: str
    label: str
    phrase: str
    need: str
    resistance: int
    looks: str
    clear_text: str
    cross_text: str
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
class Tool:
    id: str
    label: str
    phrase: str
    method: str
    leverage: int
    carry_text: str
    use_text: str
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
class Treasure:
    id: str
    expected: str
    note_text: str
    reveal_place: str
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
    def __init__(self, trail: Trail) -> None:
        self.trail = trail
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
        return [e for e in self.entities.values() if e.role in {"leader", "partner"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.trail)
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


def _r_open_barrier(world: World) -> list[str]:
    barrier = world.get("barrier")
    tool = world.get("tool")
    if barrier.attrs.get("need") != tool.attrs.get("method"):
        return []
    if barrier.meters["open"] >= THRESHOLD:
        return []
    effort = barrier.meters["push"] + tool.meters["oomph"]
    if effort < barrier.attrs.get("resistance", 99):
        return []
    sig = ("open", barrier.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    barrier.meters["open"] += 1
    barrier.meters["blocked"] = 0.0
    world.get("path").meters["open"] += 1
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["hope"] += 1
    return ["__opened__"]


def _r_reach_cache(world: World) -> list[str]:
    barrier = world.get("barrier")
    cache = world.get("cache")
    if barrier.meters["open"] < THRESHOLD:
        return []
    if cache.meters["reachable"] >= THRESHOLD:
        return []
    sig = ("reachable", cache.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cache.meters["reachable"] += 1
    world.get("path").meters["progress"] += 1
    return ["__reachable__"]


def _r_read_note(world: World) -> list[str]:
    cache = world.get("cache")
    if cache.meters["opened"] < THRESHOLD:
        return []
    sig = ("note", cache.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("surprise").meters["revealed"] += 1
    for kid in world.kids():
        kid.memes["surprise"] += 1
        kid.memes["delight"] += 1
    return ["__note__"]


CAUSAL_RULES = [
    Rule(name="open_barrier", tag="physical", apply=_r_open_barrier),
    Rule(name="reach_cache", tag="physical", apply=_r_reach_cache),
    Rule(name="read_note", tag="social", apply=_r_read_note),
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


TRAILS = {
    "orchard": Trail(
        id="orchard",
        place="the old orchard behind the shed",
        opening="The apple trees made cool green tunnels above the path.",
        path_line="A paper map showed a dotted line past the watering barrel and the stone birdbath.",
        marker="a mossy stump",
        affords={"gate", "log"},
        tags={"orchard", "map"},
    ),
    "cliffs": Trail(
        id="cliffs",
        place="the windy path below the little cliffs",
        opening="Salt wind tugged at their sleeves and made the grass bow one way, then the other.",
        path_line="Their map showed a dotted line past a driftwood post and a tide-smoothed rock.",
        marker="a flat lookout stone",
        affords={"crate", "log"},
        tags={"cliff", "map", "wind"},
    ),
    "marsh": Trail(
        id="marsh",
        place="the boardwalk near the cattail marsh",
        opening="The reeds whispered and dragonflies stitched bright lines over the water.",
        path_line="Their map showed a dotted line past the bent sign and the wooden rail.",
        marker="a sun-bleached post",
        affords={"gate", "brambles"},
        tags={"marsh", "map"},
    ),
}

BARRIERS = {
    "gate": Barrier(
        id="gate",
        label="gate",
        phrase="a stuck wooden gate",
        need="roll",
        resistance=4,
        looks="Its bottom edge had sunk into the dirt and would not budge.",
        clear_text="The gate lurched, then swung open with a tired creak.",
        cross_text="Beyond it, the hidden path curled away toward the map's last mark.",
        tags={"gate"},
    ),
    "log": Barrier(
        id="log",
        label="log",
        phrase="a fallen log",
        need="lever",
        resistance=3,
        looks="The log lay across the narrow trail like a sleepy brown giant.",
        clear_text="With one hard heave, the log rolled just far enough to clear the path.",
        cross_text="A stripe of bare ground appeared on the other side, safe for little boots.",
        tags={"log"},
    ),
    "brambles": Barrier(
        id="brambles",
        label="brambles",
        phrase="a wall of brambles",
        need="clip",
        resistance=3,
        looks="Thorny loops had knit themselves across the trail, tight as a prickly net.",
        clear_text="The front of the brambles opened into a neat little doorway.",
        cross_text="Through the gap, the path ran straight to the last marker on the map.",
        tags={"brambles"},
    ),
    "crate": Barrier(
        id="crate",
        label="crate",
        phrase="a heavy supply crate",
        need="roll",
        resistance=5,
        looks="Someone had left it squarely across the trail, too heavy to drag by hand.",
        clear_text="The crate bumped aside over the ground and thudded out of the way.",
        cross_text="At once, the path to the lookout stone was clear again.",
        tags={"crate"},
    ),
}

TOOLS = {
    "branch_lever": Tool(
        id="branch_lever",
        label="sturdy branch",
        phrase="a sturdy branch",
        method="lever",
        leverage=2,
        carry_text="a sturdy branch with a bend near one end",
        use_text="wedged the branch underneath and pushed down together",
        tags={"lever"},
    ),
    "garden_snips": Tool(
        id="garden_snips",
        label="garden snips",
        phrase="the small garden snips",
        method="clip",
        leverage=2,
        carry_text="the small garden snips hanging from the fence post",
        use_text="carefully clipped the bendiest stems first, then the thick ones",
        tags={"snips"},
    ),
    "red_wagon": Tool(
        id="red_wagon",
        label="red wagon",
        phrase="a red wagon",
        method="roll",
        leverage=3,
        carry_text="a red wagon tipped on its side nearby",
        use_text="looped the wagon rope around it and pulled with all their might",
        tags={"wagon", "roll"},
    ),
    "rope_loop": Tool(
        id="rope_loop",
        label="rope loop",
        phrase="a rope loop",
        method="roll",
        leverage=2,
        carry_text="a coil of rope tucked beside the trail post",
        use_text="made a loop and pulled with their feet planted wide",
        tags={"rope", "roll"},
    ),
}

TREASURES = {
    "picnic": Treasure(
        id="picnic",
        expected="gold coins",
        note_text='Instead of gold, the box held a folded note: "The best treasure is where everyone can share it. Look under the striped blanket."',
        reveal_place="under a striped blanket in the grass",
        ending_image="There waited sliced peaches, warm muffins, and a smiling grown-up waving them over.",
        tags={"sharing", "picnic"},
    ),
    "birthday": Treasure(
        id="birthday",
        expected="jewels",
        note_text='Instead of jewels, the box held a folded note: "Adventure first, surprise second. Climb to the big stump and look behind the ribbon."',
        reveal_place="behind a ribbon tied to the big stump",
        ending_image="There hung a bright birthday banner and a little paper crown just their size.",
        tags={"birthday", "surprise"},
    ),
    "telescope": Treasure(
        id="telescope",
        expected="silver bars",
        note_text='Instead of silver, the box held a folded note: "Real treasure helps you see farther. Follow the arrow to the lookout."',
        reveal_place="at the little lookout",
        ending_image="There stood a small telescope already pointed at the shining water and the birds beyond it.",
        tags={"telescope", "lookout"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["bold", "careful", "eager", "steady", "curious", "brave"]
ADULTS = ["mother", "father", "aunt", "uncle"]


def tool_fits(barrier: Barrier, tool: Tool) -> bool:
    return barrier.need == tool.method


def enough_total_oomph(barrier: Barrier, tool: Tool, leader_oomph: int, partner_oomph: int) -> bool:
    return tool.leverage + leader_oomph + partner_oomph >= barrier.resistance


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for trail_id, trail in TRAILS.items():
        for barrier_id in sorted(trail.affords):
            barrier = BARRIERS[barrier_id]
            for tool_id, tool in TOOLS.items():
                if tool_fits(barrier, tool):
                    combos.append((trail_id, barrier_id, tool_id))
    return combos


@dataclass
class StoryParams:
    trail: str
    barrier: str
    tool: str
    treasure: str
    leader: str
    leader_gender: str
    partner: str
    partner_gender: str
    adult: str
    leader_trait: str
    partner_trait: str
    leader_oomph: int = 2
    partner_oomph: int = 1
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


def base_oomph_for_trait(trait: str) -> int:
    return {
        "bold": 2,
        "careful": 1,
        "eager": 2,
        "steady": 2,
        "curious": 1,
        "brave": 2,
    }.get(trait, 1)


def predicted_effort(barrier: Barrier, tool: Tool, leader_oomph: int, partner_oomph: int) -> dict:
    solo = tool.leverage + leader_oomph
    together = solo + partner_oomph
    return {
        "solo": solo,
        "together": together,
        "barrier": barrier.resistance,
        "can_solo": solo >= barrier.resistance,
        "can_together": together >= barrier.resistance,
    }


def explain_rejection(trail: Trail, barrier: Barrier, tool: Tool) -> str:
    if barrier.id not in trail.affords:
        return (
            f"(No story: {barrier.phrase} does not belong on the {trail.id} trail here. "
            f"Pick a barrier that the trail can reasonably contain.)"
        )
    if not tool_fits(barrier, tool):
        return (
            f"(No story: {tool.label} is not a sensible way to move {barrier.phrase}. "
            f"This world requires a tool that actually matches the barrier.)"
        )
    return "(No story: this combination is not part of the adventure world.)"


def explain_oomph(barrier: Barrier, tool: Tool, leader_oomph: int, partner_oomph: int) -> str:
    need = barrier.resistance
    got = tool.leverage + leader_oomph + partner_oomph
    return (
        f"(No story: even with the right tool, the children do not have enough oomph. "
        f"They need {need} total effort to move {barrier.phrase}, but this setup only gives {got}.)"
    )


def outcome_of(params: StoryParams) -> str:
    barrier = BARRIERS[params.barrier]
    tool = TOOLS[params.tool]
    pred = predicted_effort(barrier, tool, params.leader_oomph, params.partner_oomph)
    if pred["can_solo"]:
        return "solo"
    if pred["can_together"]:
        return "together"
    return "stuck"


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def introduce(world: World, leader: Entity, partner: Entity, adult: Entity, trail: Trail) -> None:
    for kid in (leader, partner):
        kid.memes["excitement"] += 1
        kid.memes["trust"] += 1
    world.say(
        f"On a bright afternoon, {leader.id} and {partner.id} set out for an adventure in {trail.place}. "
        f"{trail.opening}"
    )
    world.say(
        f"{adult.label_word.capitalize()} had slipped them a hand-drawn map that promised treasure at {trail.marker}. "
        f"{trail.path_line}"
    )


def search(world: World, leader: Entity, partner: Entity, trail: Trail) -> None:
    world.say(
        f'"Last one to {trail.marker} is a sleepy snail!" {leader.id} cried, and the two explorers hurried along the path.'
    )
    world.say(
        f"{partner.id} kept the map flat with both hands and checked each turn as carefully as a real trail captain."
    )


def face_barrier(world: World, leader: Entity, partner: Entity, barrier: Barrier) -> None:
    barrier_ent = world.get("barrier")
    barrier_ent.meters["blocked"] = 1.0
    for kid in (leader, partner):
        kid.memes["doubt"] += 1
    world.say(
        f"But before they reached {world.trail.marker}, they found {barrier.phrase}. {barrier.looks}"
    )
    world.say(
        f"{leader.id} stared at it. \"That was not on the map,\" {leader.pronoun()} said."
    )


def spot_tool(world: World, partner: Entity, tool: Tool) -> None:
    world.say(
        f"{partner.id} looked around and spotted {tool.carry_text}."
    )
    world.say(
        f'"Maybe this can help," {partner.pronoun()} said.'
    )


def try_solo(world: World, leader: Entity, barrier: Barrier, tool: Tool, solo_success: bool) -> None:
    leader.memes["determination"] += 1
    leader.meters["oomph"] += 1
    world.get("barrier").meters["push"] += leader.attrs["oomph"]
    world.get("tool").meters["oomph"] = float(tool.leverage)
    if solo_success:
        world.say(
            f"{leader.id} grabbed {tool.phrase}, took a deep breath, and gave one mighty shove with all {leader.pronoun('possessive')} oomph."
        )
    else:
        world.say(
            f"{leader.id} grabbed {tool.phrase}, braced {leader.pronoun('possessive')} feet, and gave one big pull with all {leader.pronoun('possessive')} oomph."
        )
        world.say(
            f"The barrier shifted only a tiny bit. It was the sort of problem that laughed at one pair of hands."
        )


def join_in(world: World, leader: Entity, partner: Entity, tool: Tool) -> None:
    leader.memes["teamwork"] += 1
    partner.memes["teamwork"] += 1
    partner.meters["oomph"] += 1
    world.get("barrier").meters["push"] += partner.attrs["oomph"]
    world.say(
        f'"Together," {partner.id} said. {partner.pronoun().capitalize()} put {partner.pronoun("possessive")} hands beside {leader.id}\'s, and they {tool.use_text}.'
    )


def open_barrier(world: World, barrier: Barrier) -> None:
    propagate(world, narrate=False)
    world.say(barrier.clear_text)
    world.say(barrier.cross_text)


def reach_cache(world: World, leader: Entity, partner: Entity, trail: Trail) -> None:
    cache = world.get("cache")
    cache.meters["opened"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At {trail.marker}, they found a little tin box tucked behind the roots."
    )
    world.say(
        f"{leader.id} opened it slowly, already picturing {world.facts['treasure'].expected} shining inside."
    )


def twist_reveal(world: World, leader: Entity, partner: Entity, treasure: Treasure) -> None:
    world.say(treasure.note_text)
    world.say(
        f"{leader.id} blinked. {partner.id} blinked too. Then both of them smiled the same surprised smile."
    )


def final_reveal(world: World, adult: Entity, treasure: Treasure) -> None:
    for kid in world.kids():
        kid.memes["delight"] += 1
        kid.memes["wonder"] += 1
    world.say(
        f"They ran to {treasure.reveal_place} as fast as their legs could carry them."
    )
    world.say(treasure.ending_image)
    world.say(
        f'"So that was the treasure," {adult.label_word} said with a grin. "Not just finding a box. Finding it together."'
    )


def tell(
    trail: Trail,
    barrier: Barrier,
    tool: Tool,
    treasure: Treasure,
    *,
    leader_name: str,
    leader_gender: str,
    partner_name: str,
    partner_gender: str,
    adult_type: str,
    leader_trait: str,
    partner_trait: str,
    leader_oomph: int,
    partner_oomph: int,
) -> World:
    if barrier.id not in trail.affords or not tool_fits(barrier, tool):
        raise StoryError(explain_rejection(trail, barrier, tool))
    if not enough_total_oomph(barrier, tool, leader_oomph, partner_oomph):
        raise StoryError(explain_oomph(barrier, tool, leader_oomph, partner_oomph))

    world = World(trail)
    leader = world.add(
        Entity(
            id=leader_name,
            kind="character",
            type=leader_gender,
            role="leader",
            traits=[leader_trait],
            attrs={"oomph": leader_oomph},
        )
    )
    partner = world.add(
        Entity(
            id=partner_name,
            kind="character",
            type=partner_gender,
            role="partner",
            traits=[partner_trait],
            attrs={"oomph": partner_oomph},
        )
    )
    adult = world.add(
        Entity(
            id="Adult",
            kind="character",
            type=adult_type,
            role="adult",
            label="the grown-up",
        )
    )
    world.add(
        Entity(
            id="barrier",
            type="barrier",
            label=barrier.label,
            phrase=barrier.phrase,
            attrs={"need": barrier.need, "resistance": barrier.resistance},
        )
    )
    world.add(
        Entity(
            id="tool",
            type="tool",
            label=tool.label,
            phrase=tool.phrase,
            attrs={"method": tool.method, "leverage": tool.leverage},
        )
    )
    world.add(Entity(id="path", type="path", label="the path"))
    world.add(Entity(id="cache", type="cache", label="the tin box"))
    world.add(Entity(id="surprise", type="surprise", label="the real treasure"))

    world.facts.update(
        trail=trail,
        barrier_cfg=barrier,
        tool_cfg=tool,
        treasure=treasure,
        leader=leader,
        partner=partner,
        adult=adult,
        predicted=predicted_effort(barrier, tool, leader_oomph, partner_oomph),
    )

    introduce(world, leader, partner, adult, trail)
    search(world, leader, partner, trail)

    world.para()
    face_barrier(world, leader, partner, barrier)
    spot_tool(world, partner, tool)

    pred = world.facts["predicted"]
    try_solo(world, leader, barrier, tool, solo_success=pred["can_solo"])
    if pred["can_solo"]:
        open_barrier(world, barrier)
        effort_kind = "solo"
    else:
        join_in(world, leader, partner, tool)
        open_barrier(world, barrier)
        effort_kind = "together"

    world.para()
    reach_cache(world, leader, partner, trail)
    twist_reveal(world, leader, partner, treasure)

    world.para()
    final_reveal(world, adult, treasure)

    world.facts.update(
        outcome=effort_kind,
        opened=world.get("barrier").meters["open"] >= THRESHOLD,
        note_revealed=world.get("surprise").meters["revealed"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "map": [
        (
            "What does a map do?",
            "A map helps you find your way from one place to another. It gives clues about where to turn and what to look for.",
        )
    ],
    "gate": [
        (
            "Why can a wooden gate get stuck?",
            "A wooden gate can sink into dirt or swell when it gets damp. Then it rubs too hard and will not swing easily.",
        )
    ],
    "log": [
        (
            "Why is a lever useful for moving a log?",
            "A lever helps you push with more force than your arms alone. It turns a hard lift into a rolling motion.",
        )
    ],
    "brambles": [
        (
            "What are brambles?",
            "Brambles are thorny, twisty plants that can grow in a thick tangle. Their sharp points can scratch you, so you move carefully around them.",
        )
    ],
    "crate": [
        (
            "Why can wheels help move a heavy crate?",
            "Wheels help a heavy thing roll instead of scrape. Rolling takes less force than dragging across the ground.",
        )
    ],
    "wagon": [
        (
            "What is a wagon good for?",
            "A wagon can carry things, but its rope and wheels can also help pull or roll something heavy a little at a time.",
        )
    ],
    "rope": [
        (
            "Why does a rope help with pulling?",
            "A rope lets you pull from a safer, steadier position. It also gives your hands a better grip than a smooth surface does.",
        )
    ],
    "snips": [
        (
            "What are garden snips used for?",
            "Garden snips are small cutting tools for stems and little branches. Grown-ups or careful helpers use them to trim plants neatly.",
        )
    ],
    "sharing": [
        (
            "Can a treasure be something other than gold?",
            "Yes. A treasure can be anything precious to you, like time together, a surprise meal, or a beautiful thing to see.",
        )
    ],
    "telescope": [
        (
            "What does a telescope help you do?",
            "A telescope helps you see faraway things more clearly. It makes distant birds, boats, or stars look closer.",
        )
    ],
    "birthday": [
        (
            "Why do surprises feel exciting?",
            "A surprise is exciting because you do not know exactly what is coming. When it turns out kind and joyful, the feeling becomes even bigger.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "map",
    "gate",
    "log",
    "brambles",
    "crate",
    "wagon",
    "rope",
    "snips",
    "sharing",
    "telescope",
    "birthday",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    trail = f["trail"]
    barrier = f["barrier_cfg"]
    treasure = f["treasure"]
    outcome = f["outcome"]
    team_line = (
        f"the first push is not enough, so {partner.id} joins in"
        if outcome == "together"
        else f"{leader.id} manages it with one brave shove"
    )
    return [
        'Write an adventure story for a 3-to-5-year-old that includes the word "oomph" and ends with a warm twist.',
        f"Tell a gentle treasure-hunt story where {leader.id} and {partner.id} follow a map through {trail.place}, meet {barrier.phrase}, and discover that the real treasure is not {treasure.expected}.",
        f"Write a small adventure where {team_line}, and the final note leads them to a sweeter surprise than treasure coins.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    adult = f["adult"]
    trail = f["trail"]
    barrier = f["barrier_cfg"]
    tool = f["tool_cfg"]
    treasure = f["treasure"]
    pred = f["predicted"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {leader.id} and {partner.id}, two children on a treasure-hunt adventure. {adult.label_word.capitalize()} started the game by giving them the map.",
        ),
        (
            "What were they trying to find?",
            f"They thought they were looking for {treasure.expected} hidden near {trail.marker}. The map made the trip feel like a real expedition.",
        ),
        (
            f"What problem stopped them on the trail?",
            f"They found {barrier.phrase} blocking the way. It mattered because the path to {trail.marker} could not be reached until the barrier moved.",
        ),
        (
            f"How did {tool.label} help?",
            f"The {tool.label} matched the problem and gave them extra force. It turned their pulling and pushing into enough oomph to open the way.",
        ),
    ]
    if f["outcome"] == "solo":
        qa.append(
            (
                f"Did {leader.id} need help to move the barrier?",
                f"No. {leader.id} made the first try with all that oomph, and this time it was enough. {partner.id} still helped by spotting the right tool and cheering the plan on.",
            )
        )
    else:
        qa.append(
            (
                f"Why did {partner.id} join in?",
                f"{leader.id}'s first try moved the barrier only a little, so one child alone was not enough. When {partner.id} added more oomph, the barrier finally opened.",
            )
        )
    qa.append(
        (
            "What was the twist in the story?",
            f"The box did not hold {treasure.expected} at all. It held a note that sent them to {treasure.reveal_place}, where the real surprise was waiting.",
        )
    )
    qa.append(
        (
            "What changed by the end?",
            f"At first they were hunting treasure the way adventurers do in stories. By the end they understood that the best treasure was the shared surprise they reached together.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"map"} | set(world.facts["barrier_cfg"].tags) | set(world.facts["tool_cfg"].tags) | set(world.facts["treasure"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != 0}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        trail="orchard",
        barrier="log",
        tool="branch_lever",
        treasure="picnic",
        leader="Lily",
        leader_gender="girl",
        partner="Tom",
        partner_gender="boy",
        adult="mother",
        leader_trait="bold",
        partner_trait="steady",
        leader_oomph=2,
        partner_oomph=1,
    ),
    StoryParams(
        trail="marsh",
        barrier="brambles",
        tool="garden_snips",
        treasure="telescope",
        leader="Max",
        leader_gender="boy",
        partner="Mia",
        partner_gender="girl",
        adult="aunt",
        leader_trait="careful",
        partner_trait="curious",
        leader_oomph=1,
        partner_oomph=1,
    ),
    StoryParams(
        trail="cliffs",
        barrier="crate",
        tool="red_wagon",
        treasure="birthday",
        leader="Nora",
        leader_gender="girl",
        partner="Finn",
        partner_gender="boy",
        adult="father",
        leader_trait="brave",
        partner_trait="steady",
        leader_oomph=2,
        partner_oomph=1,
    ),
    StoryParams(
        trail="marsh",
        barrier="gate",
        tool="red_wagon",
        treasure="picnic",
        leader="Theo",
        leader_gender="boy",
        partner="Ava",
        partner_gender="girl",
        adult="uncle",
        leader_trait="eager",
        partner_trait="careful",
        leader_oomph=2,
        partner_oomph=1,
    ),
]


ASP_RULES = r"""
fits(B,T) :- needs(B,M), method(T,M).
valid(Tr,B,T) :- affords(Tr,B), barrier(B), tool(T), fits(B,T).

solo_success :- chosen_barrier(B), chosen_tool(T), fits(B,T),
                resistance(B,R), leverage(T,L), leader_oomph(O), L + O >= R.

together_success :- chosen_barrier(B), chosen_tool(T), fits(B,T),
                    resistance(B,R), leverage(T,L), leader_oomph(O1), partner_oomph(O2),
                    L + O1 + O2 >= R.

outcome(solo) :- solo_success.
outcome(together) :- not solo_success, together_success.
outcome(stuck) :- not together_success.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for trail_id, trail in TRAILS.items():
        lines.append(asp.fact("trail", trail_id))
        for barrier_id in sorted(trail.affords):
            lines.append(asp.fact("affords", trail_id, barrier_id))
    for barrier_id, barrier in BARRIERS.items():
        lines.append(asp.fact("barrier", barrier_id))
        lines.append(asp.fact("needs", barrier_id, barrier.need))
        lines.append(asp.fact("resistance", barrier_id, barrier.resistance))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("method", tool_id, tool.method))
        lines.append(asp.fact("leverage", tool_id, tool.leverage))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_barrier", params.barrier),
            asp.fact("chosen_tool", params.tool),
            asp.fact("leader_oomph", params.leader_oomph),
            asp.fact("partner_oomph", params.partner_oomph),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a small adventure with oomph, a blocked trail, and a twist ending."
    )
    ap.add_argument("--trail", choices=TRAILS)
    ap.add_argument("--barrier", choices=BARRIERS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--adult", choices=ADULTS)
    ap.add_argument("--leader-oomph", type=int, choices=[1, 2, 3])
    ap.add_argument("--partner-oomph", type=int, choices=[1, 2])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.trail and args.barrier and args.tool:
        trail = TRAILS[args.trail]
        barrier = BARRIERS[args.barrier]
        tool = TOOLS[args.tool]
        if barrier.id not in trail.affords or not tool_fits(barrier, tool):
            raise StoryError(explain_rejection(trail, barrier, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.trail is None or combo[0] == args.trail)
        and (args.barrier is None or combo[1] == args.barrier)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    tries = 0
    while tries < 200:
        tries += 1
        trail_id, barrier_id, tool_id = rng.choice(sorted(combos))
        treasure_id = args.treasure or rng.choice(sorted(TREASURES))
        adult = args.adult or rng.choice(ADULTS)

        leader_gender = rng.choice(["girl", "boy"])
        partner_gender = rng.choice(["girl", "boy"])
        leader_name = _pick_name(rng, leader_gender)
        partner_name = _pick_name(rng, partner_gender, avoid=leader_name)

        leader_trait = rng.choice(TRAITS)
        partner_trait = rng.choice(TRAITS)
        leader_oomph = args.leader_oomph if args.leader_oomph is not None else base_oomph_for_trait(leader_trait)
        partner_oomph = args.partner_oomph if args.partner_oomph is not None else max(1, base_oomph_for_trait(partner_trait) - 1)

        barrier = BARRIERS[barrier_id]
        tool = TOOLS[tool_id]
        if enough_total_oomph(barrier, tool, leader_oomph, partner_oomph):
            return StoryParams(
                trail=trail_id,
                barrier=barrier_id,
                tool=tool_id,
                treasure=treasure_id,
                leader=leader_name,
                leader_gender=leader_gender,
                partner=partner_name,
                partner_gender=partner_gender,
                adult=adult,
                leader_trait=leader_trait,
                partner_trait=partner_trait,
                leader_oomph=leader_oomph,
                partner_oomph=partner_oomph,
            )

    if args.trail and args.barrier and args.tool:
        raise StoryError(
            explain_oomph(BARRIERS[args.barrier], TOOLS[args.tool], args.leader_oomph or 1, args.partner_oomph or 1)
        )
    raise StoryError("(No valid combination matches the given options once oomph is considered.)")


def generate(params: StoryParams) -> StorySample:
    if params.trail not in TRAILS:
        raise StoryError(f"(Unknown trail: {params.trail})")
    if params.barrier not in BARRIERS:
        raise StoryError(f"(Unknown barrier: {params.barrier})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.treasure not in TREASURES:
        raise StoryError(f"(Unknown treasure: {params.treasure})")
    if params.adult not in ADULTS:
        raise StoryError(f"(Unknown adult type: {params.adult})")

    world = tell(
        TRAILS[params.trail],
        BARRIERS[params.barrier],
        TOOLS[params.tool],
        TREASURES[params.treasure],
        leader_name=params.leader,
        leader_gender=params.leader_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
        adult_type=params.adult,
        leader_trait=params.leader_trait,
        partner_trait=params.partner_trait,
        leader_oomph=params.leader_oomph,
        partner_oomph=params.partner_oomph,
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

    py_gate = set(valid_combos())
    asp_gate = set(asp_valid_combos())
    if py_gate == asp_gate:
        print(f"OK: gate matches valid_combos() ({len(py_gate)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_gate - py_gate:
            print("  only in clingo:", sorted(asp_gate - py_gate))
        if py_gate - asp_gate:
            print("  only in python:", sorted(py_gate - asp_gate))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(40):
        try:
            args = parser.parse_args(["--seed", str(s)])
            params = resolve_params(args, random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {s}.")
            break

    mismatches = 0
    for params in cases:
        py_out = outcome_of(params)
        asp_out = asp_outcome(params)
        if py_out != asp_out:
            mismatches += 1
            print(f"MISMATCH outcome for {params}: python={py_out} asp={asp_out}")
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:
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
        print(f"{len(combos)} compatible (trail, barrier, tool) combos:\n")
        for trail, barrier, tool in combos:
            print(f"  {trail:8} {barrier:9} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.leader} & {p.partner}: {p.barrier} on {p.trail} with {p.tool} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
