#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/nation_flamingo_slope_foreshadowing_quest_pirate_tale.py
===================================================================================

A standalone story world for a tiny pirate-style quest tale with foreshadowing.

Premise
-------
Two children turn an ordinary place into a pirate land and set out on a quest.
They want to reach a bright treasure on the far side of a steep slope. One child
notices a danger first: the slope is slippery, and a borrowed rolling object
would make the climb worse. A grown-up helps them choose a safer way, so the
quest can continue.

The world includes the required seed words:
    nation, flamingo, slope

And the seed features:
    Foreshadowing, Quest

Design notes
------------
This world models a simple, concrete causal problem:

    steep/slippery slope + rolling ride -> unsafe
    helper offers proper climbing gear/path -> safe

The foreshadowing comes from an early warning sign on the slope and a prediction
beat where the cautious child imagines what could happen. The quest shape is:
map -> goal -> risky shortcut idea -> warning -> trouble or near-trouble ->
grown-up fix -> changed ending image.

Run it
------
    python storyworlds/worlds/gpt-5.4/nation_flamingo_slope_foreshadowing_quest_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/nation_flamingo_slope_foreshadowing_quest_pirate_tale.py --terrain dune --ride wagon
    python storyworlds/worlds/gpt-5.4/nation_flamingo_slope_foreshadowing_quest_pirate_tale.py --terrain stairs
    python storyworlds/worlds/gpt-5.4/nation_flamingo_slope_foreshadowing_quest_pirate_tale.py --assist rope
    python storyworlds/worlds/gpt-5.4/nation_flamingo_slope_foreshadowing_quest_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/nation_flamingo_slope_foreshadowing_quest_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/nation_flamingo_slope_foreshadowing_quest_pirate_tale.py --verify
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
SENSE_MIN = 2


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
class Theme:
    id: str
    scene: str
    rig: str
    crew_word: str
    goal: str
    send_off: str
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
class Terrain:
    id: str
    label: str
    phrase: str
    steepness: int
    slippery: bool
    climb_text: str
    warning_sign: str
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
class Ride:
    id: str
    label: str
    phrase: str
    rolls: bool
    balance: int
    where_from: str
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
    label: str
    phrase: str
    shine: str
    animal_mark: str
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
class HelperTool:
    id: str
    label: str
    phrase: str
    traction: int
    steadying: bool
    text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"leader", "mate"}]

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


def _r_slide(world: World) -> list[str]:
    out: list[str] = []
    hill = world.get("terrain")
    ride = world.get("ride")
    if hill.meters["attempt"] < THRESHOLD or ride.meters["used"] < THRESHOLD:
        return out
    if not ride.attrs.get("rolls", False):
        return out
    sig = ("slide", hill.id, ride.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    risk = hill.attrs.get("risk", 0)
    if risk >= 1:
        hill.meters["slid"] += 1
        for kid in world.kids():
            kid.memes["fear"] += 1
        out.append("__slide__")
    return out


def _r_drop(world: World) -> list[str]:
    out: list[str] = []
    hill = world.get("terrain")
    token = world.get("treasure")
    if hill.meters["slid"] < THRESHOLD:
        return out
    sig = ("drop", token.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    token.meters["dropped"] += 1
    out.append("__drop__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="slide", tag="physical", apply=_r_slide),
    Rule(name="drop", tag="physical", apply=_r_drop),
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
        for sent in produced:
            world.say(sent)
    return produced


def terrain_risk(terrain: Terrain, ride: Ride) -> int:
    return terrain.steepness + (1 if terrain.slippery else 0) + (1 if ride.rolls else 0) - ride.balance


def helper_works(terrain: Terrain, ride: Ride, assist: HelperTool) -> bool:
    return assist.traction >= terrain_risk(terrain, ride)


def sensible_helpers() -> list[HelperTool]:
    return [a for a in ASSISTS.values() if a.traction >= SENSE_MIN]


def hazard_at_risk(terrain: Terrain, ride: Ride) -> bool:
    return terrain_risk(terrain, ride) >= 2


def predict_slide(world: World) -> dict:
    sim = world.copy()
    sim.get("terrain").meters["attempt"] += 1
    sim.get("ride").meters["used"] += 1
    propagate(sim, narrate=False)
    return {
        "slides": sim.get("terrain").meters["slid"] >= THRESHOLD,
        "drops": sim.get("treasure").meters["dropped"] >= THRESHOLD,
    }


def play_setup(world: World, leader: Entity, mate: Entity, theme: Theme, treasure: Treasure) -> None:
    leader.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {leader.id} and {mate.id} turned the yard into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f"They called it the Shell-Feather Nation, the tiniest nation in the world, "
        f"and promised to cross it like brave {theme.crew_word}."
    )
    world.say(
        f'At the end of the map waited {treasure.phrase}, {treasure.shine}, marked with a tiny {treasure.animal_mark}.'
    )


def foreshadow(world: World, mate: Entity, terrain: Terrain) -> None:
    world.say(
        f"But between them and the treasure stood {terrain.phrase}. "
        f"{terrain.warning_sign}"
    )
    world.say(
        f"{mate.id} looked at the ground and noticed that the {terrain.label} looked ready to slip under quick feet."
    )


def tempt(world: World, leader: Entity, ride: Ride) -> None:
    leader.memes["boldness"] += 1
    world.say(
        f'{leader.id} grinned. "No problem. We can use {ride.phrase} {ride.where_from} and zoom right up."'
    )


def warn(world: World, mate: Entity, leader: Entity, ride: Ride, parent: Entity) -> None:
    pred = predict_slide(world)
    mate.memes["caution"] += 1
    world.facts["predicted_slide"] = pred["slides"]
    world.facts["predicted_drop"] = pred["drops"]
    second = " It would scoot downhill instead of helping." if pred["slides"] else ""
    world.say(
        f'{mate.id} shook {mate.pronoun("possessive")} head. "{ride.label.capitalize()} are for flat ground, not this slope," '
        f'{mate.pronoun()} said. "If we try that, someone could slip and the treasure could tumble away.{second}"'
    )
    world.say(
        f'For one quiet moment, the warning hung in the air like a bell from a ship mast.'
    )


def defy(world: World, leader: Entity, ride: Ride) -> None:
    leader.memes["defiance"] += 1
    world.say(
        f'"We are on a quest," {leader.id} said, and grabbed {ride.phrase}.'
    )


def attempt(world: World, terrain: Terrain, ride: Ride, treasure: Treasure) -> None:
    world.get("terrain").meters["attempt"] += 1
    world.get("ride").meters["used"] += 1
    propagate(world, narrate=False)
    if world.get("terrain").meters["slid"] >= THRESHOLD:
        world.say(
            f"The wheels bumped once, then skittered. On the middle of the {terrain.label}, the whole plan wobbled sideways."
        )
        if world.get("treasure").meters["dropped"] >= THRESHOLD:
            world.say(
                f"{treasure.phrase.capitalize()} slipped from their hands and bumped back down to the bottom with a small, unhappy clack."
            )
    else:
        world.say(
            f"They started up the {terrain.label}, but even before anyone fell, the rolling ride felt wrong under them."
        )


def alarm(world: World, mate: Entity, parent: Entity) -> None:
    world.say(f'"Careful!" {mate.id} cried. "{parent.label_word.capitalize()}!"')


def rescue(world: World, parent: Entity, assist: HelperTool, terrain: Terrain, treasure: Treasure, theme: Theme) -> None:
    world.get("terrain").meters["safe_crossing"] += 1
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["trust"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came over at once and {assist.text}"
    )
    world.say(
        f"Step by step, they crossed the {terrain.label} the steady way and reached {treasure.phrase} at last."
    )
    world.say(
        f'This time the quest felt less like rushing and more like real {theme.crew_word} work.'
    )


def lesson(world: World, parent: Entity, leader: Entity, mate: Entity, ride: Ride) -> None:
    leader.memes["lesson"] += 1
    mate.memes["lesson"] += 1
    world.say(
        f'{parent.label_word.capitalize()} knelt beside them. "A brave explorer notices when a fast plan is a shaky plan," '
        f'{parent.pronoun()} said softly.'
    )
    world.say(
        f'"{ride.label.capitalize()} can be fun on the right ground, but not on a steep slope. On adventures, we slow down when the ground asks us to."'
    )
    world.say(f'"We will remember," said {mate.id} and {leader.id} together.')


def ending(world: World, leader: Entity, mate: Entity, treasure: Treasure, theme: Theme) -> None:
    leader.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"When they opened the prize box, they found shiny shells, a paper flag, and a pink flamingo sticker for the map."
    )
    world.say(
        f'{leader.id} pressed the flamingo sticker above the crossed-out danger mark, and {mate.id} drew a safer path beside it.'
    )
    world.say(
        f"Then the two {theme.crew_word} marched across their little nation again, not racing now, but laughing and sure-footed."
    )


def tell(
    theme: Theme,
    terrain: Terrain,
    ride: Ride,
    treasure: Treasure,
    assist: HelperTool,
    leader_name: str = "Tom",
    leader_gender: str = "boy",
    mate_name: str = "Lily",
    mate_gender: str = "girl",
    parent_type: str = "mother",
) -> World:
    world = World()
    leader = world.add(Entity(id=leader_name, kind="character", type=leader_gender, role="leader", attrs={}))
    mate = world.add(Entity(id=mate_name, kind="character", type=mate_gender, role="mate", attrs={}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent", attrs={}))
    world.add(
        Entity(
            id="terrain",
            type="terrain",
            label=terrain.label,
            attrs={"risk": terrain_risk(terrain, ride), "slippery": terrain.slippery},
        )
    )
    world.add(
        Entity(
            id="ride",
            type="ride",
            label=ride.label,
            attrs={"rolls": ride.rolls, "balance": ride.balance},
        )
    )
    world.add(Entity(id="treasure", type="treasure", label=treasure.label, attrs={}))
    world.facts["predicted_slide"] = False
    world.facts["predicted_drop"] = False

    play_setup(world, leader, mate, theme, treasure)
    foreshadow(world, mate, terrain)

    world.para()
    tempt(world, leader, ride)
    warn(world, mate, leader, ride, parent)
    defy(world, leader, ride)

    world.para()
    attempt(world, terrain, ride, treasure)
    alarm(world, mate, parent)

    world.para()
    rescue(world, parent, assist, terrain, treasure, theme)
    lesson(world, parent, leader, mate, ride)

    world.para()
    ending(world, leader, mate, treasure, theme)

    world.facts.update(
        leader=leader,
        mate=mate,
        parent=parent,
        theme=theme,
        terrain_cfg=terrain,
        ride_cfg=ride,
        treasure_cfg=treasure,
        assist_cfg=assist,
        slid=world.get("terrain").meters["slid"] >= THRESHOLD,
        dropped=world.get("treasure").meters["dropped"] >= THRESHOLD,
        safe=world.get("terrain").meters["safe_crossing"] >= THRESHOLD,
    )
    return world


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a windy island nation of blankets and chalk lines",
        rig="The sandbox became the harbor, a laundry basket became the captain's skiff, and a chalk map curled across the stones like an old sea chart.",
        crew_word="pirates",
        goal="the feathered treasure of the pink cove",
        send_off="set off to claim the treasure",
    ),
    "captains": Theme(
        id="captains",
        scene="a tiny nation of coves, cliffs, and secret paths",
        rig="A broom was the mast, two towels were sails, and a cardboard box became their supply chest.",
        crew_word="captains",
        goal="the shell chest on the high side of the island",
        send_off="headed off for the high shell chest",
    ),
    "explorers": Theme(
        id="explorers",
        scene="a proud island nation drawn in blue chalk",
        rig="The porch steps became sea cliffs, a bucket became the cargo hold, and a paper map showed a trail to hidden treasure.",
        crew_word="explorers",
        goal="the bright box beyond the ridge",
        send_off="hurried toward the ridge treasure",
    ),
}

TERRAINS = {
    "dune": Terrain(
        id="dune",
        label="dune slope",
        phrase="a sandy slope that leaned down toward the fence",
        steepness=2,
        slippery=True,
        climb_text="sand slipped under every step",
        warning_sign="Tiny trickles of sand were already sliding to the bottom.",
        tags={"slope", "sand"},
    ),
    "grassy_bank": Terrain(
        id="grassy_bank",
        label="grassy slope",
        phrase="a grassy slope above the flower bed",
        steepness=2,
        slippery=True,
        climb_text="wet grass bent under their shoes",
        warning_sign="A few bent blades of grass showed where feet had slid before.",
        tags={"slope", "grass"},
    ),
    "porch_hill": Terrain(
        id="porch_hill",
        label="porch slope",
        phrase="a short wooden slope by the porch ramp",
        steepness=1,
        slippery=True,
        climb_text="the boards were smooth and slick",
        warning_sign="The wood gave off a shiny gleam that looked pretty and tricky at the same time.",
        tags={"slope", "wood"},
    ),
    "stairs": Terrain(
        id="stairs",
        label="garden stairs",
        phrase="a line of broad garden stairs",
        steepness=0,
        slippery=False,
        climb_text="the steps held still under careful feet",
        warning_sign="Each step sat flat and square, with room for slow feet.",
        tags={"steps"},
    ),
}

RIDES = {
    "wagon": Ride(
        id="wagon",
        label="wagon",
        phrase="the red wagon",
        rolls=True,
        balance=0,
        where_from="from beside the shed",
        tags={"wagon", "rolling"},
    ),
    "scooter": Ride(
        id="scooter",
        label="scooter",
        phrase="the little scooter",
        rolls=True,
        balance=0,
        where_from="from near the porch",
        tags={"scooter", "rolling"},
    ),
    "crate": Ride(
        id="crate",
        label="wooden crate",
        phrase="the wooden crate with rope handles",
        rolls=False,
        balance=1,
        where_from="from under the table",
        tags={"crate", "carrying"},
    ),
}

TREASURES = {
    "shell_chest": Treasure(
        id="shell_chest",
        label="shell chest",
        phrase="a painted shell chest",
        shine="glinting in the sun",
        animal_mark="flamingo",
        tags={"treasure", "flamingo"},
    ),
    "feather_box": Treasure(
        id="feather_box",
        label="feather box",
        phrase="a feather-trimmed box",
        shine="shining with silver paper stars",
        animal_mark="flamingo",
        tags={"treasure", "flamingo"},
    ),
    "map_tube": Treasure(
        id="map_tube",
        label="map tube",
        phrase="a blue treasure tube",
        shine="gleaming like a polished spyglass",
        animal_mark="flamingo",
        tags={"treasure", "flamingo"},
    ),
}

ASSISTS = {
    "rope": HelperTool(
        id="rope",
        label="rope",
        phrase="a rope line",
        traction=3,
        steadying=True,
        text="looped a thick rope along the side and showed them how to hold on with one hand while carrying the treasure with the other",
        qa_text="set a rope along the side so they could climb steadily",
        tags={"rope", "safety"},
    ),
    "stairs_path": HelperTool(
        id="stairs_path",
        label="stairs path",
        phrase="the stair path",
        traction=2,
        steadying=True,
        text="pointed to the nearby steps and led them around to the safer path",
        qa_text="led them around by the safer steps",
        tags={"stairs", "safety"},
    ),
    "sand_steps": HelperTool(
        id="sand_steps",
        label="sand steps",
        phrase="little sand steps",
        traction=2,
        steadying=True,
        text="pressed deep footprints into the sand to make little steps and walked beside them while they climbed",
        qa_text="made little steps in the sand so they could climb carefully",
        tags={"sand", "safety"},
    ),
    "push_faster": HelperTool(
        id="push_faster",
        label="push faster",
        phrase="a hard push",
        traction=1,
        steadying=False,
        text="gave the wagon a quick push, but then stopped and chose a steadier idea instead",
        qa_text="tried to make it go faster",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Eli"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for theme_id in THEMES:
        for terrain_id, terrain in TERRAINS.items():
            for ride_id, ride in RIDES.items():
                if not hazard_at_risk(terrain, ride):
                    continue
                for assist_id, assist in ASSISTS.items():
                    if assist.traction >= SENSE_MIN and helper_works(terrain, ride, assist):
                        combos.append((theme_id, terrain_id, ride_id, assist_id))
    return combos


@dataclass
class StoryParams:
    theme: str
    terrain: str
    ride: str
    treasure: str
    assist: str
    leader: str
    leader_gender: str
    mate: str
    mate_gender: str
    parent: str
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
    "slope": [
        (
            "What is a slope?",
            "A slope is ground that goes up or down instead of staying flat. On a steep slope, things and people can slip or roll."
        )
    ],
    "wagon": [
        (
            "Why can a wagon be tricky on a hill?",
            "A wagon has wheels, so it likes to roll. On a hill it can move faster than you want if the ground is steep or slippery."
        )
    ],
    "scooter": [
        (
            "Why should you be careful with a scooter on a hill?",
            "A scooter rolls quickly on smooth ground. On a hill, quick wheels can make balancing much harder."
        )
    ],
    "rope": [
        (
            "What does a rope help with on a climb?",
            "A rope gives your hands something steady to hold. That can help you keep your balance while you go up."
        )
    ],
    "stairs": [
        (
            "Why are stairs easier than a slippery hill?",
            "Stairs give your feet flat places to land. That makes it easier to climb slowly and safely."
        )
    ],
    "sand": [
        (
            "Why does loose sand slide?",
            "Loose sand is made of many tiny grains that move past each other. When you step on it, the grains can slip away."
        )
    ],
    "flamingo": [
        (
            "What is a flamingo?",
            "A flamingo is a tall pink bird with long legs. Children often use flamingos in stories and pictures because they look bright and funny."
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a trip with a special goal, like finding treasure or reaching a far place. In stories, a quest usually has a problem that must be solved on the way."
        )
    ],
}
KNOWLEDGE_ORDER = ["slope", "wagon", "scooter", "rope", "stairs", "sand", "flamingo", "quest"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader = f["leader"]
    mate = f["mate"]
    terrain = f["terrain_cfg"]
    ride = f["ride_cfg"]
    treasure = f["treasure_cfg"]
    assist = f["assist_cfg"]
    return [
        f'Write a pirate-style story for a 3-to-5-year-old that includes the words "nation", "flamingo", and "slope".',
        f"Tell a quest story where {leader.id} and {mate.id} cross a tiny pretend nation to reach {treasure.phrase}, but a warning about a {terrain.label} foreshadows trouble.",
        f"Write a gentle adventure where a rolling {ride.label} is the wrong idea, a grown-up helps with {assist.label}, and the children finish the quest safely.",
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "boy" and b.type == "boy":
        return "two children"
    if a.type == "girl" and b.type == "girl":
        return "two children"
    return "two children"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    mate = f["mate"]
    parent = f["parent"]
    terrain = f["terrain_cfg"]
    ride = f["ride_cfg"]
    treasure = f["treasure_cfg"]
    assist = f["assist_cfg"]
    theme = f["theme"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(leader, mate)}, {leader.id} and {mate.id}, on a pretend pirate quest. {parent.label_word.capitalize()} helps them when the climb turns risky."
        ),
        (
            "What was their quest?",
            f"They wanted to cross their little nation and reach {treasure.phrase}. The treasure gave their game a clear goal, so the adventure felt important from the start."
        ),
        (
            "What was the foreshadowing in the story?",
            f"The foreshadowing came when {mate.id} noticed signs that the {terrain.label} was slippery before they tried to climb it. That early warning hinted that the fast plan would go wrong."
        ),
        (
            f"Why did {mate.id} warn {leader.id} about the {ride.label}?",
            f"{mate.id} knew the {ride.label} could roll on the {terrain.label} instead of staying steady. {mate.pronoun().capitalize()} also guessed that if it slipped, the treasure might tumble away."
        ),
    ]
    if f["slid"]:
        qa.append(
            (
                "What happened when they tried the fast plan?",
                f"The rolling ride wobbled on the slope, and the climb turned shaky. That proved the warning was right because the ground and the wheels did not work well together."
            )
        )
    if f["dropped"]:
        qa.append(
            (
                "What happened to the treasure box?",
                f"It slipped from their hands and bumped back down to the bottom. The fall showed how one wobbly choice could spoil the whole quest."
            )
        )
    qa.append(
        (
            f"How did {parent.label_word} help them finish the quest?",
            f"{parent.label_word.capitalize()} {assist.qa_text}. That gave them a slower, steadier way to cross the slope and reach the treasure safely."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with them opening the treasure and putting a flamingo sticker on the map beside a safer path. The ending image shows they did not just finish the quest—they learned how to travel their little nation more wisely."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"quest", "slope"} | set(f["terrain_cfg"].tags) | set(f["treasure_cfg"].tags)
    ride = f["ride_cfg"]
    assist = f["assist_cfg"]
    if "wagon" in ride.tags:
        tags.add("wagon")
    if "scooter" in ride.tags:
        tags.add("scooter")
    if "rope" in assist.tags:
        tags.add("rope")
    if "stairs" in assist.tags:
        tags.add("stairs")
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="pirates",
        terrain="dune",
        ride="wagon",
        treasure="shell_chest",
        assist="rope",
        leader="Tom",
        leader_gender="boy",
        mate="Lily",
        mate_gender="girl",
        parent="mother",
    ),
    StoryParams(
        theme="captains",
        terrain="grassy_bank",
        ride="scooter",
        treasure="feather_box",
        assist="stairs_path",
        leader="Max",
        leader_gender="boy",
        mate="Mia",
        mate_gender="girl",
        parent="father",
    ),
    StoryParams(
        theme="explorers",
        terrain="porch_hill",
        ride="wagon",
        treasure="map_tube",
        assist="sand_steps",
        leader="Ava",
        leader_gender="girl",
        mate="Leo",
        mate_gender="boy",
        parent="mother",
    ),
]


def explain_rejection(terrain: Terrain, ride: Ride) -> str:
    if not hazard_at_risk(terrain, ride):
        return (
            f"(No story: {ride.phrase} is not a believable hazard on {terrain.phrase}. "
            f"The slope must be steep or slippery enough for the warning and rescue to matter.)"
        )
    return "(No story: this combination does not support the quest problem.)"


def explain_assist(aid: str) -> str:
    assist = ASSISTS[aid]
    good = ", ".join(sorted(a.id for a in sensible_helpers()))
    return (
        f"(Refusing assist '{aid}': it is too weak for this world's safety gate "
        f"(traction={assist.traction} < {SENSE_MIN}). Try: {good}.)"
    )


ASP_RULES = r"""
hazard(Tg, R) :- terrain(Tg), ride(R),
                 steepness(Tg, S), slippery(Tg), rolls(R), balance(R, B),
                 V = S + 1 + 1 - B, V >= 2.
hazard(Tg, R) :- terrain(Tg), ride(R),
                 steepness(Tg, S), not slippery(Tg), rolls(R), balance(R, B),
                 V = S + 1 - B, V >= 2.
hazard(Tg, R) :- terrain(Tg), ride(R),
                 steepness(Tg, S), slippery(Tg), not rolls(R), balance(R, B),
                 V = S + 1 - B, V >= 2.
hazard(Tg, R) :- terrain(Tg), ride(R),
                 steepness(Tg, S), not slippery(Tg), not rolls(R), balance(R, B),
                 V = S - B, V >= 2.

sensible(A) :- assist(A), traction(A, T), sense_min(M), T >= M.

works(Tg, R, A) :- terrain(Tg), ride(R), assist(A), traction(A, T),
                   steepness(Tg, S), balance(R, B), slippery(Tg), rolls(R),
                   V = S + 1 + 1 - B, T >= V.
works(Tg, R, A) :- terrain(Tg), ride(R), assist(A), traction(A, T),
                   steepness(Tg, S), balance(R, B), not slippery(Tg), rolls(R),
                   V = S + 1 - B, T >= V.
works(Tg, R, A) :- terrain(Tg), ride(R), assist(A), traction(A, T),
                   steepness(Tg, S), balance(R, B), slippery(Tg), not rolls(R),
                   V = S + 1 - B, T >= V.
works(Tg, R, A) :- terrain(Tg), ride(R), assist(A), traction(A, T),
                   steepness(Tg, S), balance(R, B), not slippery(Tg), not rolls(R),
                   V = S - B, T >= V.

valid(Th, Tg, R, A) :- theme(Th), terrain(Tg), ride(R), assist(A), hazard(Tg, R), sensible(A), works(Tg, R, A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for tid, terrain in TERRAINS.items():
        lines.append(asp.fact("terrain", tid))
        lines.append(asp.fact("steepness", tid, terrain.steepness))
        if terrain.slippery:
            lines.append(asp.fact("slippery", tid))
    for rid, ride in RIDES.items():
        lines.append(asp.fact("ride", rid))
        if ride.rolls:
            lines.append(asp.fact("rolls", rid))
        lines.append(asp.fact("balance", rid, ride.balance))
    for aid, assist in ASSISTS.items():
        lines.append(asp.fact("assist", aid))
        lines.append(asp.fact("traction", aid, assist.traction))
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
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


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

    c_sens = set(asp_sensible())
    p_sens = {x.id for x in sensible_helpers()}
    if c_sens == p_sens:
        print(f"OK: sensible assists match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible assists: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: pirate-style quest with foreshadowing on a slope."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--terrain", choices=TERRAINS)
    ap.add_argument("--ride", choices=RIDES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--assist", choices=ASSISTS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.terrain and args.ride:
        terrain = TERRAINS[args.terrain]
        ride = RIDES[args.ride]
        if not hazard_at_risk(terrain, ride):
            raise StoryError(explain_rejection(terrain, ride))
    if args.assist and ASSISTS[args.assist].traction < SENSE_MIN:
        raise StoryError(explain_assist(args.assist))

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.terrain is None or c[1] == args.terrain)
        and (args.ride is None or c[2] == args.ride)
        and (args.assist is None or c[3] == args.assist)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, terrain, ride, assist = rng.choice(sorted(combos))
    treasure = args.treasure or rng.choice(sorted(TREASURES))
    leader, leader_gender = _pick_kid(rng)
    mate, mate_gender = _pick_kid(rng, avoid=leader)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        theme=theme,
        terrain=terrain,
        ride=ride,
        treasure=treasure,
        assist=assist,
        leader=leader,
        leader_gender=leader_gender,
        mate=mate,
        mate_gender=mate_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.terrain not in TERRAINS:
        raise StoryError(f"(Unknown terrain: {params.terrain})")
    if params.ride not in RIDES:
        raise StoryError(f"(Unknown ride: {params.ride})")
    if params.treasure not in TREASURES:
        raise StoryError(f"(Unknown treasure: {params.treasure})")
    if params.assist not in ASSISTS:
        raise StoryError(f"(Unknown assist: {params.assist})")

    terrain = TERRAINS[params.terrain]
    ride = RIDES[params.ride]
    assist = ASSISTS[params.assist]
    if not hazard_at_risk(terrain, ride):
        raise StoryError(explain_rejection(terrain, ride))
    if assist.traction < SENSE_MIN:
        raise StoryError(explain_assist(params.assist))
    if not helper_works(terrain, ride, assist):
        raise StoryError("(No story: the chosen help is too weak for this slope.)")

    world = tell(
        theme=THEMES[params.theme],
        terrain=terrain,
        ride=ride,
        treasure=TREASURES[params.treasure],
        assist=assist,
        leader_name=params.leader,
        leader_gender=params.leader_gender,
        mate_name=params.mate,
        mate_gender=params.mate_gender,
        parent_type=params.parent,
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
        print(f"sensible assists: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, terrain, ride, assist) combos:\n")
        for theme, terrain, ride, assist in combos:
            print(f"  {theme:10} {terrain:12} {ride:8} {assist}")
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
            header = f"### {p.leader} & {p.mate}: {p.ride} on {p.terrain} ({p.theme}, {p.assist})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
