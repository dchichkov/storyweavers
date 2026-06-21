#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/wing_founding_systematic_train_station_suspense_transformation.py
===========================================================================================

A standalone storyworld for a child-facing mystery at a train station.

Premise
-------
A child is waiting in an old train station when a treasured item from the
station's founding display goes missing. A small clue appears in the hush before
the train arrives. Instead of panicking, the child and a calm helper make a
systematic search, follow the clue to a plausible hiding place, and bring the
display back to life. The story's transformation is both emotional and physical:
the hero grows braver, and the worried, dim station corner becomes bright and
welcoming again.

Run it
------
    python storyworlds/worlds/gpt-5.4/wing_founding_systematic_train_station_suspense_transformation.py
    python storyworlds/worlds/gpt-5.4/wing_founding_systematic_train_station_suspense_transformation.py --object wing_badge --spot high_ledge --tool broom
    python storyworlds/worlds/gpt-5.4/wing_founding_systematic_train_station_suspense_transformation.py --object founding_ledger --clue silver_scuff
    python storyworlds/worlds/gpt-5.4/wing_founding_systematic_train_station_suspense_transformation.py --all --qa
    python storyworlds/worlds/gpt-5.4/wing_founding_systematic_train_station_suspense_transformation.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "aunt"}
        male = {"boy", "father", "grandfather", "man", "porter", "stationmaster"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "aunt": "aunt",
            "porter": "porter",
            "stationmaster": "stationmaster",
        }.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    short: str
    display_text: str
    trace_text: str
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
class ClueCfg:
    id: str
    label: str
    phrase: str
    trace_text: str
    points_to: set[str] = field(default_factory=set)
    fits_objects: set[str] = field(default_factory=set)
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
class SpotCfg:
    id: str
    label: str
    phrase: str
    search_text: str
    found_text: str
    atmosphere: str
    holds: set[str] = field(default_factory=set)
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
class ToolCfg:
    id: str
    label: str
    phrase: str
    action_text: str
    reaches: set[str] = field(default_factory=set)
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
class HelperCfg:
    id: str
    type: str
    intro: str
    style: str
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


def _r_missing_hush(world: World) -> list[str]:
    relic = world.entities.get("relic")
    station = world.entities.get("station")
    master = world.entities.get("master")
    if not relic or not station or not master:
        return []
    sig = ("missing_hush",)
    if relic.meters["lost"] >= THRESHOLD and sig not in world.fired:
        world.fired.add(sig)
        station.meters["hush"] += 1
        master.memes["worry"] += 1
    return []


def _r_clue_curiosity(world: World) -> list[str]:
    hero = world.entities.get("hero")
    clue = world.entities.get("clue")
    if not hero or not clue:
        return []
    sig = ("clue_curiosity",)
    if clue.meters["noticed"] >= THRESHOLD and sig not in world.fired:
        world.fired.add(sig)
        hero.memes["curiosity"] += 1
        hero.memes["courage"] += 1
    return []


def _r_plan_steadies(world: World) -> list[str]:
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    if not hero or not helper:
        return []
    sig = ("plan_steadies",)
    if world.facts.get("systematic") and sig not in world.fired:
        world.fired.add(sig)
        hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1.0)
        helper.memes["calm"] += 1
    return []


def _r_found_restores(world: World) -> list[str]:
    relic = world.entities.get("relic")
    display = world.entities.get("display")
    station = world.entities.get("station")
    hero = world.entities.get("hero")
    master = world.entities.get("master")
    if not relic or not display or not station or not hero or not master:
        return []
    sig = ("found_restores",)
    if relic.meters["found"] >= THRESHOLD and sig not in world.fired:
        world.fired.add(sig)
        display.meters["restored"] += 1
        station.meters["glow"] += 1
        master.memes["relief"] += 1
        hero.memes["courage"] += 1
    return []


def _r_transformation(world: World) -> list[str]:
    hero = world.entities.get("hero")
    station = world.entities.get("station")
    display = world.entities.get("display")
    sig = ("transformation",)
    if not hero or not station or not display:
        return []
    if display.meters["restored"] >= THRESHOLD and hero.memes["courage"] >= THRESHOLD and sig not in world.fired:
        world.fired.add(sig)
        hero.memes["transformed"] += 1
        station.memes["welcome"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_hush", tag="mystery", apply=_r_missing_hush),
    Rule(name="clue_curiosity", tag="emotion", apply=_r_clue_curiosity),
    Rule(name="plan_steadies", tag="emotion", apply=_r_plan_steadies),
    Rule(name="found_restores", tag="physical", apply=_r_found_restores),
    Rule(name="transformation", tag="ending", apply=_r_transformation),
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
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
    if narrate:
        for line in produced:
            world.say(line)
    return produced


OBJECTS = {
    "wing_badge": ObjectCfg(
        id="wing_badge",
        label="wing badge",
        phrase="the brass wing badge from the station's founding display",
        short="wing badge",
        display_text="the founding display's wing badge",
        trace_text="A tiny curl of brass dust glittered where a wing edge had scraped.",
        tags={"wing_badge", "founding"},
    ),
    "founding_ledger": ObjectCfg(
        id="founding_ledger",
        label="founding ledger",
        phrase="the founding ledger with a silver wing stamped on its cover",
        short="founding ledger",
        display_text="the old founding ledger",
        trace_text="A square breath of paper dust lay on the floor, as if a book had been slid away.",
        tags={"ledger", "founding"},
    ),
    "station_lantern": ObjectCfg(
        id="station_lantern",
        label="station lantern",
        phrase="the little lantern painted with a blue wing from the station's founding table",
        short="station lantern",
        display_text="the founding lantern",
        trace_text="A tiny soot mark and one thread of blue paint showed that a lantern had brushed past.",
        tags={"lantern", "wing_badge", "founding"},
    ),
}

CLUES = {
    "silver_scuff": ClueCfg(
        id="silver_scuff",
        label="silver scuff",
        phrase="a silver scuff on the dusty floorboards",
        trace_text="The mark was thin and bright, as if something metal had bumped and then slid away.",
        points_to={"under_bench", "high_ledge"},
        fits_objects={"wing_badge", "station_lantern"},
        tags={"clue", "metal"},
    ),
    "paper_dust": ClueCfg(
        id="paper_dust",
        label="paper dust",
        phrase="a soft square of paper dust near the timetable wall",
        trace_text="It looked exactly the size of a missing book corner.",
        points_to={"ticket_drawer", "parcel_cubby"},
        fits_objects={"founding_ledger"},
        tags={"clue", "paper"},
    ),
    "soot_speck": ClueCfg(
        id="soot_speck",
        label="soot speck",
        phrase="one soot speck beside the old signal map",
        trace_text="Someone had carried something smoky and small through there.",
        points_to={"signal_cabinet", "high_ledge"},
        fits_objects={"station_lantern"},
        tags={"clue", "soot"},
    ),
    "blue_thread": ClueCfg(
        id="blue_thread",
        label="blue thread",
        phrase="a blue thread caught on a splinter",
        trace_text="The thread matched the ribbon used on special station things.",
        points_to={"parcel_cubby", "under_bench"},
        fits_objects={"wing_badge", "founding_ledger"},
        tags={"clue", "thread"},
    ),
}

SPOTS = {
    "under_bench": SpotCfg(
        id="under_bench",
        label="under the wooden bench",
        phrase="under the long wooden bench by platform two",
        search_text="The shadows under the bench looked thick enough to hide a secret.",
        found_text="Far back in the gloom, something small caught the light.",
        atmosphere="Every time a train wheel clicked outside, the bench seemed to hold its breath.",
        holds={"wing_badge", "founding_ledger"},
        tags={"bench", "train_station"},
    ),
    "high_ledge": SpotCfg(
        id="high_ledge",
        label="on the high ledge",
        phrase="on the narrow ledge beneath the glass roof",
        search_text="The ledge was so high that only a stretching shadow could reach it.",
        found_text="Above them, beyond the drifting dust, a shape waited on the ledge.",
        atmosphere="Rain tapped the roof overhead, making the dark glass seem even farther away.",
        holds={"wing_badge", "station_lantern"},
        tags={"ledge", "train_station"},
    ),
    "ticket_drawer": SpotCfg(
        id="ticket_drawer",
        label="in the ticket drawer",
        phrase="inside the old ticket drawer",
        search_text="The drawer sat half-shut, as if it knew more than it should.",
        found_text="When the drawer slid open, a hidden thing rested behind the ticket rolls.",
        atmosphere="The brass handle gave a tiny creak that sounded loud in the quiet station.",
        holds={"founding_ledger"},
        tags={"drawer", "train_station"},
    ),
    "parcel_cubby": SpotCfg(
        id="parcel_cubby",
        label="in the parcel cubby",
        phrase="inside the parcel cubby by the wall clock",
        search_text="The cubby smelled of string, old paper, and long waits.",
        found_text="Behind a stack of labels, something special had been tucked away.",
        atmosphere="The wall clock clicked so neatly that each second felt like a clue.",
        holds={"founding_ledger", "station_lantern"},
        tags={"parcel", "train_station"},
    ),
    "signal_cabinet": SpotCfg(
        id="signal_cabinet",
        label="in the signal cabinet",
        phrase="inside the old signal cabinet",
        search_text="The cabinet door was narrow and dark, with one patient line of light at the edge.",
        found_text="Inside the cabinet, tucked beside old levers, the missing thing waited.",
        atmosphere="The little metal latch trembled when a train rumbled somewhere far down the line.",
        holds={"station_lantern"},
        tags={"signal", "train_station"},
    ),
}

TOOLS = {
    "broom": ToolCfg(
        id="broom",
        label="broom",
        phrase="a long station broom",
        action_text="used the broom to reach where hands could not",
        reaches={"under_bench", "high_ledge"},
        tags={"broom"},
    ),
    "step_stool": ToolCfg(
        id="step_stool",
        label="step stool",
        phrase="a folding step stool",
        action_text="opened the stool with a soft snap and climbed carefully",
        reaches={"high_ledge", "ticket_drawer", "parcel_cubby"},
        tags={"step_stool"},
    ),
    "key_ring": ToolCfg(
        id="key_ring",
        label="key ring",
        phrase="a ring of station keys",
        action_text="turned the proper key and opened the place with care",
        reaches={"ticket_drawer", "signal_cabinet"},
        tags={"key_ring"},
    ),
}

HELPERS = {
    "aunt": HelperCfg(
        id="aunt",
        type="aunt",
        intro="Aunt Mira knew how to speak softly in echoing places.",
        style="She never rushed a guess; she liked to think one careful step at a time.",
        tags={"family_helper"},
    ),
    "porter": HelperCfg(
        id="porter",
        type="porter",
        intro="Old Porter Hale knew every cart, latch, and lamp in the station.",
        style="He moved slowly, as if every answer deserved a fair chance to appear.",
        tags={"porter"},
    ),
    "grandmother": HelperCfg(
        id="grandmother",
        type="grandmother",
        intro="Grandma June smiled like someone who had solved many little puzzles.",
        style="She believed a calm mind could hear what a noisy place was trying to say.",
        tags={"family_helper"},
    ),
}

GIRL_NAMES = ["Nora", "Lila", "Mina", "Tess", "Ivy", "Clara", "Rosa", "Etta"]
BOY_NAMES = ["Owen", "Felix", "Milo", "Theo", "Jasper", "Eli", "Hugo", "Noel"]
TRAITS = ["careful", "quiet", "curious", "observant", "thoughtful", "steady"]


def object_can_hide(object_id: str, spot_id: str) -> bool:
    return object_id in SPOTS[spot_id].holds


def clue_fits(clue_id: str, object_id: str, spot_id: str) -> bool:
    clue = CLUES[clue_id]
    return object_id in clue.fits_objects and spot_id in clue.points_to


def tool_reaches(tool_id: str, spot_id: str) -> bool:
    return spot_id in TOOLS[tool_id].reaches


def valid_combo(object_id: str, clue_id: str, spot_id: str, tool_id: str) -> bool:
    return (
        object_id in OBJECTS
        and clue_id in CLUES
        and spot_id in SPOTS
        and tool_id in TOOLS
        and object_can_hide(object_id, spot_id)
        and clue_fits(clue_id, object_id, spot_id)
        and tool_reaches(tool_id, spot_id)
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for object_id in OBJECTS:
        for clue_id in CLUES:
            for spot_id in SPOTS:
                for tool_id in TOOLS:
                    if valid_combo(object_id, clue_id, spot_id, tool_id):
                        out.append((object_id, clue_id, spot_id, tool_id))
    return sorted(out)


@dataclass
class StoryParams:
    object: str
    clue: str
    spot: str
    tool: str
    helper: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None
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


def station_opening() -> str:
    return (
        "Rain tapped the glass roof of the train station, and the departures board clicked "
        "its little letters into place."
    )


def introduce(world: World, hero: Entity, helper: Entity, helper_cfg: HelperCfg) -> None:
    world.say(station_opening())
    world.say(
        f"{hero.id} stood beside {helper.label_word} in the waiting hall, trying to be {hero.traits[0]} "
        "while the shadows stretched between the benches."
    )
    world.say(helper_cfg.intro)
    world.say(helper_cfg.style)


def missing_setup(world: World, hero: Entity, master: Entity, object_cfg: ObjectCfg) -> None:
    relic = world.get("relic")
    relic.meters["lost"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Near the ticket window, the stationmaster gave a worried sigh. "
        f'"The train for the evening guests is nearly here," {master.pronoun()} said, '
        f'"and {object_cfg.display_text} is gone."'
    )
    world.say(
        f"The little founding table by the wall clock looked wrong without {object_cfg.short}. "
        "That empty space made the whole station feel quieter."
    )
    hero.memes["fear"] += 1
    world.facts["mystery_started"] = True


def clue_appears(world: World, hero: Entity, clue_cfg: ClueCfg, object_cfg: ObjectCfg) -> None:
    clue = world.get("clue")
    clue.meters["noticed"] += 1
    clue.attrs["text"] = clue_cfg.phrase
    propagate(world, narrate=False)
    world.say(
        f"Then {hero.id} noticed {clue_cfg.phrase}. {clue_cfg.trace_text}"
    )
    world.say(
        f"{object_cfg.trace_text} It was only a tiny sign, but in a mystery, tiny signs matter."
    )
    world.facts["clue_noticed"] = clue_cfg.id


def make_plan(world: World, hero: Entity, helper: Entity, spot_cfg: SpotCfg, tool_cfg: ToolCfg) -> None:
    world.facts["systematic"] = True
    propagate(world, narrate=False)
    world.say(
        f'"Let\'s be systematic," said {helper.label_word}. "We will follow the clue and check one good place, '
        'not ten wild guesses."'
    )
    world.say(
        f"{hero.id} nodded. The plan made the station feel less like a scary maze and more like a puzzle "
        "that could be solved."
    )
    world.say(
        f"They chose to search {spot_cfg.phrase}, and {helper.label_word} brought {tool_cfg.phrase} just in case."
    )


def search_spot(world: World, hero: Entity, helper: Entity, spot_cfg: SpotCfg) -> None:
    hero.memes["suspense"] += 1
    world.say(spot_cfg.search_text)
    world.say(spot_cfg.atmosphere)
    world.say(
        f"{hero.id} stayed close to {helper.label_word}, listening to the faraway rails sing under the storm."
    )


def recover(world: World, hero: Entity, helper: Entity, object_cfg: ObjectCfg, spot_cfg: SpotCfg, tool_cfg: ToolCfg) -> None:
    relic = world.get("relic")
    relic.meters["found"] += 1
    relic.meters["lost"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{helper.label_word.capitalize()} {tool_cfg.action_text}. {spot_cfg.found_text}"
    )
    world.say(
        f'"There it is," whispered {hero.id}. {object_cfg.phrase.capitalize()} had been hidden {spot_cfg.label}.'
    )
    world.facts["found_with"] = tool_cfg.id
    world.facts["found_in"] = spot_cfg.id


def restore_display(world: World, hero: Entity, master: Entity, object_cfg: ObjectCfg) -> None:
    world.say(
        f"When they carried {object_cfg.short} back to the founding table, the stationmaster's face changed at once."
    )
    world.say(
        f'"You found it," {master.pronoun()} said. {master.pronoun("possessive").capitalize()} worried voice turned warm, '
        "and the waiting hall did not seem lonely anymore."
    )
    world.say(
        f"Soon the little display was whole again, with old tickets, a brass clock key, and {object_cfg.short} glowing under the lamp."
    )


def ending(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} looked around and felt the transformation clearly. A little while ago the train station had felt full "
        "of secrets and missing pieces. Now it felt bright, proud, and ready to welcome people."
    )
    world.say(
        f"When the next train sighed into the platform, {hero.id} did not shrink from the echoing hall. "
        "The mystery had made room for courage."
    )


def tell(
    object_cfg: ObjectCfg,
    clue_cfg: ClueCfg,
    spot_cfg: SpotCfg,
    tool_cfg: ToolCfg,
    helper_cfg: HelperCfg,
    *,
    name: str,
    gender: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=name,
            kind="character",
            type=gender,
            label=name,
            role="hero",
            traits=[trait],
            tags={"child"},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_cfg.type,
            label=helper_cfg.type,
            role="helper",
            tags=set(helper_cfg.tags),
        )
    )
    master = world.add(
        Entity(
            id="Master",
            kind="character",
            type="stationmaster",
            label="stationmaster",
            role="stationmaster",
            tags={"stationmaster"},
        )
    )
    station = world.add(
        Entity(
            id="station",
            type="place",
            label="train station",
            tags={"train_station"},
        )
    )
    display = world.add(
        Entity(
            id="display",
            type="display",
            label="founding table",
            tags={"founding"},
        )
    )
    world.add(
        Entity(
            id="relic",
            type="relic",
            label=object_cfg.label,
            attrs={"object_id": object_cfg.id},
            tags=set(object_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="clue",
            type="clue",
            label=clue_cfg.label,
            attrs={"clue_id": clue_cfg.id},
            tags=set(clue_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="tool",
            type="tool",
            label=tool_cfg.label,
            attrs={"tool_id": tool_cfg.id},
            tags=set(tool_cfg.tags),
        )
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        master=master,
        object_cfg=object_cfg,
        clue_cfg=clue_cfg,
        spot_cfg=spot_cfg,
        tool_cfg=tool_cfg,
        helper_cfg=helper_cfg,
        setting="train station",
        systematic=False,
    )

    introduce(world, hero, helper, helper_cfg)
    world.para()
    missing_setup(world, hero, master, object_cfg)
    clue_appears(world, hero, clue_cfg, object_cfg)
    world.para()
    make_plan(world, hero, helper, spot_cfg, tool_cfg)
    search_spot(world, hero, helper, spot_cfg)
    recover(world, hero, helper, object_cfg, spot_cfg, tool_cfg)
    world.para()
    restore_display(world, hero, master, object_cfg)
    ending(world, hero)

    world.facts.update(
        recovered=True,
        restored=world.get("display").meters["restored"] >= THRESHOLD,
        transformed=hero.memes["transformed"] >= THRESHOLD,
    )
    return world


def explain_invalid_combo(object_id: str, clue_id: str, spot_id: str, tool_id: str) -> str:
    if object_id not in OBJECTS:
        return f"(No story: unknown object '{object_id}'.)"
    if clue_id not in CLUES:
        return f"(No story: unknown clue '{clue_id}'.)"
    if spot_id not in SPOTS:
        return f"(No story: unknown spot '{spot_id}'.)"
    if tool_id not in TOOLS:
        return f"(No story: unknown tool '{tool_id}'.)"
    if not object_can_hide(object_id, spot_id):
        return (
            f"(No story: {OBJECTS[object_id].short} would not reasonably be hidden {SPOTS[spot_id].label}. "
            "Pick a spot that can actually hold that missing thing.)"
        )
    if not clue_fits(clue_id, object_id, spot_id):
        return (
            f"(No story: {CLUES[clue_id].label} does not honestly point to {SPOTS[spot_id].label} for "
            f"{OBJECTS[object_id].short}. The clue must match both the object and the hiding place.)"
        )
    if not tool_reaches(tool_id, spot_id):
        return (
            f"(No story: {TOOLS[tool_id].label} cannot reach {SPOTS[spot_id].label}. "
            "The helper needs a tool that can really get to the hidden item.)"
        )
    return "(No story: that combination is not reasonable in this world.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    obj = f["object_cfg"]
    clue = f["clue_cfg"]
    return [
        f'Write a short mystery for a 3-to-5-year-old set in a train station. Include the words "wing", "founding", and "systematic".',
        f"Tell a suspenseful but gentle story where {hero.id} spots {clue.phrase}, follows it with a systematic search, and finds {obj.phrase}.",
        "Write a mystery in which a worried station changes into a warm, welcoming place after a child solves a missing-object puzzle.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    master = f["master"]
    obj = f["object_cfg"]
    clue = f["clue_cfg"]
    spot = f["spot_cfg"]
    tool = f["tool_cfg"]

    return [
        (
            "What was missing at the train station?",
            f"{obj.phrase.capitalize()} was missing from the station's founding display. "
            f"That is why the stationmaster sounded worried and the waiting hall felt so hushed."
        ),
        (
            f"What clue did {hero.id} notice?",
            f"{hero.id} noticed {clue.phrase}. {clue.trace_text} That tiny sign gave them a real place to search instead of making random guesses."
        ),
        (
            f"Why did {helper.label_word} say they should be systematic?",
            f"{helper.label_word.capitalize()} wanted the search to stay calm and careful. "
            "Checking one sensible place at a time kept the mystery from feeling bigger than it really was."
        ),
        (
            f"Where did they find the missing thing, and how did they reach it?",
            f"They found it {spot.label}. {helper.label_word.capitalize()} used {tool.phrase} to reach the spot because that tool could really get to the hidden place."
        ),
        (
            "How did the station change at the end?",
            "At first the train station felt dim, worried, and full of missing pieces. "
            "After the object came back, the founding table looked whole again and the hall felt bright and welcoming."
        ),
        (
            f"How did {hero.id} change during the story?",
            f"{hero.id} started out nervous in the echoing station. "
            "By helping solve the mystery, the child grew brave and could face the big hall with confidence."
        ),
        (
            f"How did the stationmaster feel when {hero.id} and {helper.label_word} returned?",
            f"The stationmaster felt relieved and grateful. "
            f"The missing {obj.short} meant the founding display could be shown properly when the train arrived."
        ),
    ]


KNOWLEDGE = {
    "train_station": [
        (
            "What is a train station?",
            "A train station is a place where trains stop so people can get on and off. It often has platforms, benches, signs, and a waiting area."
        )
    ],
    "founding": [
        (
            "What does founding mean?",
            "Founding means the beginning of something important, like when a town or station was first started. A founding display helps people remember that beginning."
        )
    ],
    "wing_badge": [
        (
            "What is a badge?",
            "A badge is a small piece of metal or cloth that shows a sign or symbol. Sometimes people keep badges to remember a place or event."
        )
    ],
    "ledger": [
        (
            "What is a ledger?",
            "A ledger is a book used to write down important records. Long ago, people used ledgers to keep careful notes."
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a light with a cover around it. Before bright electric lights were common, lanterns helped people see in dark places."
        )
    ],
    "broom": [
        (
            "What is a broom used for?",
            "A broom is used for sweeping dust and dirt. A long broom can also help reach something that is a little too far away."
        )
    ],
    "step_stool": [
        (
            "What is a step stool?",
            "A step stool is a small set of steps that helps you reach something higher. Grown-ups often use one to get to a shelf safely."
        )
    ],
    "key_ring": [
        (
            "What is a key ring?",
            "A key ring is a loop that holds several keys together. It helps someone keep the right keys ready for doors, drawers, or cabinets."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a problem with something hidden or unknown. People solve mysteries by noticing clues and thinking carefully."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "train_station",
    "founding",
    "mystery",
    "wing_badge",
    "ledger",
    "lantern",
    "broom",
    "step_stool",
    "key_ring",
]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"train_station", "mystery", "founding"} | set(f["object_cfg"].tags) | set(f["tool_cfg"].tags)
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
    for entity in list(world.entities.values()):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        bits = []
        if entity.role:
            bits.append(f"role={entity.role}")
        if entity.traits:
            bits.append(f"traits={entity.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if entity.attrs:
            shown = {k: v for k, v in entity.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if entity.tags:
            bits.append(f"tags={sorted(entity.tags)}")
        lines.append(f"  {entity.id:8} ({entity.type:13}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
can_hide(O,S) :- object(O), spot(S), holds(S,O).
clue_match(C,O,S) :- clue(C), object(O), spot(S), clue_object(C,O), clue_spot(C,S).
reachable(T,S) :- tool(T), spot(S), reach(T,S).

valid(O,C,S,T) :- can_hide(O,S), clue_match(C,O,S), reachable(T,S).

recovered(O,C,S,T) :- valid(O,C,S,T).
restored(O,C,S,T) :- recovered(O,C,S,T).

#show valid/4.
#show restored/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for object_id in OBJECTS:
        lines.append(asp.fact("object", object_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        for object_id in sorted(clue.fits_objects):
            lines.append(asp.fact("clue_object", clue_id, object_id))
        for spot_id in sorted(clue.points_to):
            lines.append(asp.fact("clue_spot", clue_id, spot_id))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        for object_id in sorted(spot.holds):
            lines.append(asp.fact("holds", spot_id, object_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for spot_id in sorted(tool.reaches):
            lines.append(asp.fact("reach", tool_id, spot_id))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_restored_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "restored")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a gentle mystery at a train station with a systematic search and a transforming ending."
    )
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    explicit_object = args.object
    explicit_clue = args.clue
    explicit_spot = args.spot
    explicit_tool = args.tool

    if all(v is not None for v in [explicit_object, explicit_clue, explicit_spot, explicit_tool]):
        if not valid_combo(explicit_object, explicit_clue, explicit_spot, explicit_tool):
            raise StoryError(explain_invalid_combo(explicit_object, explicit_clue, explicit_spot, explicit_tool))

    combos = [
        combo
        for combo in valid_combos()
        if (explicit_object is None or combo[0] == explicit_object)
        and (explicit_clue is None or combo[1] == explicit_clue)
        and (explicit_spot is None or combo[2] == explicit_spot)
        and (explicit_tool is None or combo[3] == explicit_tool)
    ]
    if not combos:
        if any(v is not None for v in [explicit_object, explicit_clue, explicit_spot, explicit_tool]):
            object_id = explicit_object or next(iter(OBJECTS))
            clue_id = explicit_clue or next(iter(CLUES))
            spot_id = explicit_spot or next(iter(SPOTS))
            tool_id = explicit_tool or next(iter(TOOLS))
            raise StoryError(explain_invalid_combo(object_id, clue_id, spot_id, tool_id))
        raise StoryError("(No valid combination matches the given options.)")

    object_id, clue_id, spot_id, tool_id = rng.choice(combos)
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    trait = rng.choice(TRAITS)

    return StoryParams(
        object=object_id,
        clue=clue_id,
        spot=spot_id,
        tool=tool_id,
        helper=helper_id,
        name=name,
        gender=gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        object_cfg = OBJECTS[params.object]
        clue_cfg = CLUES[params.clue]
        spot_cfg = SPOTS[params.spot]
        tool_cfg = TOOLS[params.tool]
        helper_cfg = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"(No story: unknown parameter value {err.args[0]!r}.)") from None

    if not valid_combo(params.object, params.clue, params.spot, params.tool):
        raise StoryError(explain_invalid_combo(params.object, params.clue, params.spot, params.tool))

    world = tell(
        object_cfg=object_cfg,
        clue_cfg=clue_cfg,
        spot_cfg=spot_cfg,
        tool_cfg=tool_cfg,
        helper_cfg=helper_cfg,
        name=params.name,
        gender=params.gender,
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


CURATED = [
    StoryParams(
        object="wing_badge",
        clue="silver_scuff",
        spot="high_ledge",
        tool="broom",
        helper="aunt",
        name="Nora",
        gender="girl",
        trait="observant",
    ),
    StoryParams(
        object="founding_ledger",
        clue="paper_dust",
        spot="ticket_drawer",
        tool="key_ring",
        helper="porter",
        name="Owen",
        gender="boy",
        trait="careful",
    ),
    StoryParams(
        object="station_lantern",
        clue="soot_speck",
        spot="signal_cabinet",
        tool="key_ring",
        helper="grandmother",
        name="Lila",
        gender="girl",
        trait="quiet",
    ),
    StoryParams(
        object="founding_ledger",
        clue="blue_thread",
        spot="under_bench",
        tool="broom",
        helper="aunt",
        name="Theo",
        gender="boy",
        trait="thoughtful",
    ),
    StoryParams(
        object="station_lantern",
        clue="silver_scuff",
        spot="high_ledge",
        tool="step_stool",
        helper="porter",
        name="Mina",
        gender="girl",
        trait="steady",
    ),
]


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: ASP valid combos match Python ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in ASP:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in Python:", sorted(py_valid - asp_valid))

    asp_restored = set(asp_restored_combos())
    if asp_restored == py_valid:
        print(f"OK: ASP restored outcomes match valid combos ({len(asp_restored)} combos).")
    else:
        rc = 1
        print("MISMATCH in restored outcomes:")
        if asp_restored - py_valid:
            print("  only restored in ASP:", sorted(asp_restored - py_valid))
        if py_valid - asp_restored:
            print("  missing restored combos in ASP:", sorted(py_valid - asp_restored))

    smoke_cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        args = parser.parse_args([])
        try:
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            smoke_cases.append(params)
        except StoryError as err:
            rc = 1
            print(f"SMOKE resolve failed on seed {seed}: {err}")

    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story.strip():
                rc = 1
                print(f"SMOKE generate produced empty story for {params}")
        except Exception as err:
            rc = 1
            print(f"SMOKE generate crashed for {params}: {err}")

    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (object, clue, spot, tool) combos:\n")
        for object_id, clue_id, spot_id, tool_id in combos:
            print(f"  {object_id:16} {clue_id:13} {spot_id:15} {tool_id}")
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
            header = f"### {p.name}: {p.object} via {p.clue} at {p.spot} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
