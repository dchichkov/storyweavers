#!/usr/bin/env python3
"""
A standalone storyworld about carrying living plankton through a mythic night
and trying to retain their light until moonrise.
"""

from __future__ import annotations

import argparse
import copy
import contextlib
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    watertight: bool = False
    covered: bool = False
    # physical + emotional
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "grandmother", "priestess"}
        male = {"boy", "man", "grandfather", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "priestess": "priestess",
            "priest": "priest",
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
class Shore:
    id: str
    label: str
    water_desc: str
    shrine_desc: str
    path_desc: str
    deity: str
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
class Hazard:
    id: str
    label: str
    verb: str
    danger_text: str
    ritual_warning: str
    loss: str
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
    watertight: bool
    covered: bool
    steady: bool
    built_in_guards: set[str] = field(default_factory=set)
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
class Charm:
    id: str
    label: str
    phrase: str
    guards: set[str] = field(default_factory=set)
    surprise_text: str = ""
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
class Offering:
    id: str
    label: str
    phrase: str
    moon_favor: bool = False
    end_text: str = ""
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


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


def protected_against(world: World, hazard_id: str) -> bool:
    vessel = world.get("vessel")
    charm = world.get("charm")
    guards = set(vessel.attrs.get("guards", set())) | set(charm.attrs.get("guards", set()))
    if vessel.covered and hazard_id == "wind":
        guards.add("wind")
    if vessel.steady and hazard_id == "stairs":
        guards.add("stairs")
    return hazard_id in guards


def _r_leak(world: World) -> list[str]:
    plankton = world.get("plankton")
    vessel = world.get("vessel")
    child = world.get("child")
    if plankton.meters["carried"] < THRESHOLD or vessel.watertight:
        return []
    sig = ("leak",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    plankton.meters["water"] -= 2
    plankton.meters["glow"] -= 2
    child.memes["worry"] += 2
    return ["__leak__"]


def _r_hazard(world: World) -> list[str]:
    plankton = world.get("plankton")
    child = world.get("child")
    hazard_id = world.facts["hazard"].id
    if plankton.meters["carried"] < THRESHOLD or protected_against(world, hazard_id):
        return []
    sig = ("hazard", hazard_id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    plankton.meters["water"] -= 1
    plankton.meters["glow"] -= 1
    child.memes["worry"] += 1
    return ["__hazard__"]


def _r_retain(world: World) -> list[str]:
    plankton = world.get("plankton")
    child = world.get("child")
    if plankton.meters["carried"] < THRESHOLD:
        return []
    if plankton.meters["glow"] < THRESHOLD or plankton.meters["water"] < THRESHOLD:
        return []
    sig = ("retain",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    plankton.meters["retained"] += 1
    child.memes["courage"] += 1
    return []


def _r_blessing(world: World) -> list[str]:
    basin = world.get("basin")
    plankton = world.get("plankton")
    offering = world.facts["offering"]
    child = world.get("child")
    if basin.meters["filled"] < THRESHOLD or plankton.meters["retained"] < THRESHOLD:
        return []
    if not offering.moon_favor:
        return []
    sig = ("blessing", offering.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    basin.meters["blessed"] += 1
    child.memes["awe"] += 1
    return ["__blessing__"]


CAUSAL_RULES = [
    Rule(name="leak", tag="physical", apply=_r_leak),
    Rule(name="hazard", tag="physical", apply=_r_hazard),
    Rule(name="retain", tag="physical", apply=_r_retain),
    Rule(name="blessing", tag="myth", apply=_r_blessing),
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
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


def plankton_can_retain(vessel: Vessel) -> bool:
    return vessel.watertight


def can_guard(vessel: Vessel, charm: Charm, hazard: Hazard) -> bool:
    guards = set(vessel.built_in_guards) | set(charm.guards)
    if vessel.covered and hazard.id == "wind":
        guards.add("wind")
    if vessel.steady and hazard.id == "stairs":
        guards.add("stairs")
    return hazard.id in guards


def valid_combo(vessel: Vessel, charm: Charm, hazard: Hazard) -> bool:
    return plankton_can_retain(vessel) and can_guard(vessel, charm, hazard)


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for shore_id in SHORES:
        for vessel_id, vessel in VESSELS.items():
            for charm_id, charm in CHARMS.items():
                for hazard_id, hazard in HAZARDS.items():
                    if valid_combo(vessel, charm, hazard):
                        out.append((shore_id, vessel_id, charm_id, hazard_id))
    return out


def outcome_of(params: "StoryParams") -> str:
    vessel = VESSELS[params.vessel]
    charm = CHARMS[params.charm]
    hazard = HAZARDS[params.hazard]
    offering = OFFERINGS[params.offering]
    if not valid_combo(vessel, charm, hazard):
        return "dim"
    if offering.moon_favor:
        return "blessed"
    return "bright"


def predict_trip(world: World) -> dict:
    sim = world.copy()
    sim.get("plankton").meters["carried"] += 1
    propagate(sim, narrate=False)
    return {
        "glow": sim.get("plankton").meters["glow"],
        "water": sim.get("plankton").meters["water"],
        "retained": sim.get("plankton").meters["retained"] >= THRESHOLD,
    }


def opening(world: World, child: Entity, elder: Entity, shore: Shore) -> None:
    world.say(
        f"Long ago, when the sea still whispered advice to little villages, "
        f"{shore.label} waited each dark-moon night for a child to climb from the water to the hill shrine."
    )
    world.say(
        f"That night the task belonged to {child.id}. Below the rocks, {shore.water_desc}, "
        f"and above them {shore.shrine_desc} looked down like a quiet star."
    )
    child.memes["duty"] += 1


def charge_task(world: World, child: Entity, elder: Entity, shore: Shore,
                hazard: Hazard, vessel: Vessel, offering: Offering) -> None:
    world.say(
        f'{elder.label_word.capitalize()} placed {vessel.phrase} in {child.id}\'s hands and said, '
        f'"Carry the living plankton to the moon basin before moonrise. '
        f'The harbor lamps retain their courage only when the sea-light reaches the shrine alive."'
    )
    world.say(
        f'{elder.pronoun("possessive").capitalize()} voice dropped softer. '
        f'"Beware {hazard.label}. {hazard.ritual_warning}. Take {offering.phrase} too, '
        f'for {shore.deity} listens at the basin."'
    )


def gather_plankton(world: World, child: Entity, vessel: Entity, plankton: Entity,
                    shore: Shore, charm: Charm) -> None:
    plankton.meters["water"] = 2.0
    plankton.meters["glow"] = 2.0
    plankton.meters["in_vessel"] = 1.0
    child.memes["wonder"] += 1
    world.say(
        f"At the tide line, {child.id} dipped the vessel into the black water. "
        f"The plankton swirled up at once, green-blue and bright as tiny stars caught in a cup."
    )
    world.say(
        f"{child.id} tucked {charm.phrase} close beside the vessel and began the climb along {shore.path_desc}."
    )


def warning_beat(world: World, child: Entity, elder: Entity, hazard: Hazard) -> None:
    pred = predict_trip(world)
    world.facts["predicted_glow"] = pred["glow"]
    world.facts["predicted_retained"] = pred["retained"]
    child.memes["worry"] += 1
    if pred["retained"]:
        world.say(
            f"For a few steps {child.id} felt brave, yet every sound in the dark seemed larger than daytime. "
            f"{hazard.danger_text}."
        )
    else:
        world.say(
            f"Before the stairway even bent out of sight, {child.id} remembered the warning and felt a cold squeeze of fear. "
            f"{hazard.danger_text}."
        )


def journey(world: World, child: Entity, hazard: Hazard) -> None:
    world.get("plankton").meters["carried"] += 1
    propagate(world, narrate=False)
    plankton = world.get("plankton")
    if ("leak",) in world.fired:
        world.say(
            f"As {child.id} climbed, water slipped away through the vessel. {hazard.loss}, "
            f"and the shining cloud thinned inside the dark."
        )
    elif ("hazard", hazard.id) in world.fired:
        world.say(
            f"Halfway up the path, {hazard.verb}. {hazard.loss}, and {child.id} gripped the vessel so hard "
            f"{child.pronoun('possessive')} fingers ached."
        )
    else:
        world.say(
            f"Halfway up the path, {hazard.verb}, but the charm held true. "
            f"The little sea-stars trembled and still kept their glow."
        )


def surprise_turn(world: World, child: Entity, charm: Charm) -> None:
    plankton = world.get("plankton")
    if plankton.meters["retained"] < THRESHOLD:
        return
    child.memes["hope"] += 1
    if charm.surprise_text:
        world.say(charm.surprise_text.replace("{child}", child.id))
    else:
        world.say(
            f"Then something unexpected happened: the light inside the vessel brightened instead of fading, "
            f"as if the sea itself had leaned close to help."
        )


def pour_basin(world: World, child: Entity, basin: Entity, offering: Offering, shore: Shore) -> None:
    plankton = world.get("plankton")
    basin.meters["filled"] += 1
    world.say(
        f"At last {child.id} reached the hill shrine and poured the living light into the stone basin. "
        f"Then {child.pronoun()} laid down {offering.phrase} for {shore.deity}."
    )
    propagate(world, narrate=False)
    if plankton.meters["retained"] < THRESHOLD:
        basin.meters["dim"] += 1
        world.say(
            "For one long breath nothing happened except the scratching of night insects in the grass."
        )
    elif basin.meters["blessed"] >= THRESHOLD:
        world.say(
            f"{offering.end_text} The basin flared silver, and the harbor below answered with a necklace of lights."
        )
    else:
        world.say(
            "A clear glow spread through the basin, and one by one the boats below lit their lamps from the reflected shimmer."
        )


def ending(world: World, child: Entity, elder: Entity, shore: Shore, outcome: str) -> None:
    if outcome == "dim":
        child.memes["sadness"] += 1
        child.memes["lesson"] += 1
        world.say(
            f"{elder.label_word.capitalize()} came up the last steps and rested a hand on {child.id}'s shoulder. "
            f'"Even sacred light must be cared for the right way," {elder.pronoun()} said. '
            f'"Next dark moon, we will carry it better and retain every spark."'
        )
        world.say(
            f"Below them the sea stayed black, but {child.id} watched closely and promised to remember what living things need."
        )
    elif outcome == "bright":
        child.memes["relief"] += 1
        child.memes["lesson"] += 1
        world.say(
            f"When {child.id} looked down from the shrine, the fishing boats were no longer drifting in fear. "
            f"They moved homeward over the water by the plankton's steady gleam."
        )
        world.say(
            f"From that night on, people of {shore.label} said that courage was not loud. "
            f"Sometimes it was only two careful hands, climbing in the dark and retaining a small, bright life."
        )
    else:
        child.memes["relief"] += 1
        child.memes["awe"] += 1
        child.memes["lesson"] += 1
        world.say(
            f"Then a surprise passed over the bay: the shining plankton gathered themselves into a pale road upon the sea, "
            f"and every boat found the harbor mouth at once."
        )
        world.say(
            f"People remembered that miracle for years and said {shore.deity} had smiled on {child.id}, "
            f"who had climbed through suspense without spilling the sea's smallest stars."
        )


def tell(shore: Shore, hazard: Hazard, vessel_cfg: Vessel, charm_cfg: Charm, offering: Offering,
         child_name: str = "Neri", child_type: str = "girl",
         elder_type: str = "grandmother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child", label=child_name))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, role="elder", label="the elder"))
    vessel = world.add(
        Entity(
            id="vessel",
            type="vessel",
            label=vessel_cfg.label,
            watertight=vessel_cfg.watertight,
            covered=vessel_cfg.covered,
            attrs={"guards": set(vessel_cfg.built_in_guards), "steady": vessel_cfg.steady},
        )
    )
    vessel.steady = vessel_cfg.steady
    charm = world.add(Entity(id="charm", type="charm", label=charm_cfg.label, attrs={"guards": set(charm_cfg.guards)}))
    plankton = world.add(Entity(id="plankton", type="plankton", label="plankton"))
    basin = world.add(Entity(id="basin", type="basin", label="moon basin"))

    world.facts.update(
        shore=shore,
        hazard=hazard,
        vessel_cfg=vessel_cfg,
        charm_cfg=charm_cfg,
        offering=offering,
        child=child,
        elder=elder,
    )

    opening(world, child, elder, shore)
    charge_task(world, child, elder, shore, hazard, vessel_cfg, offering)

    world.para()
    gather_plankton(world, child, vessel, plankton, shore, charm_cfg)
    warning_beat(world, child, elder, hazard)
    journey(world, child, hazard)

    world.para()
    surprise_turn(world, child, charm_cfg)
    pour_basin(world, child, basin, offering, shore)

    outcome = "dim"
    if plankton.meters["retained"] >= THRESHOLD and basin.meters["blessed"] >= THRESHOLD:
        outcome = "blessed"
    elif plankton.meters["retained"] >= THRESHOLD:
        outcome = "bright"

    world.para()
    ending(world, child, elder, shore, outcome)

    world.facts.update(
        vessel=vessel,
        charm=charm,
        plankton=plankton,
        basin=basin,
        retained=plankton.meters["retained"] >= THRESHOLD,
        outcome=outcome,
        blessed=basin.meters["blessed"] >= THRESHOLD,
    )
    return world


SHORES = {
    "moon_cove": Shore(
        id="moon_cove",
        label="Moon Cove",
        water_desc="the tide foamed around black stones and every ripple hid a glimmer",
        shrine_desc="the chalk-white shrine of the hill moon",
        path_desc="the old cliff stair",
        deity="the Hill Moon",
        tags={"sea", "shrine"},
    ),
    "whale_bay": Shore(
        id="whale_bay",
        label="Whale Bay",
        water_desc="the curved bay breathed in and out like a sleeping giant",
        shrine_desc="the shrine tower with its shell windows",
        path_desc="the whale-back path of worn stone",
        deity="the Listening Tide",
        tags={"sea", "shrine"},
    ),
    "reef_hollow": Shore(
        id="reef_hollow",
        label="Reef Hollow",
        water_desc="the reef pools blinked with trapped stars beneath the foam",
        shrine_desc="the high basin cut into red cliff",
        path_desc="the narrow steps above the reef",
        deity="the Lantern Sea",
        tags={"sea", "shrine"},
    ),
}

HAZARDS = {
    "wind": Hazard(
        id="wind",
        label="the cliff wind",
        verb="the cliff wind came whistling sideways from the sea",
        danger_text="The night felt full of suspense, because one rough gust could toss precious seawater into the dark",
        ritual_warning="Shield the water, or the wind will snatch the glow from the bowl",
        loss="Spray flew away in silver drops",
        tags={"wind"},
    ),
    "heat": Hazard(
        id="heat",
        label="the fire-stone breath",
        verb="warm breath rose from the day-heated stones",
        danger_text="The climb held suspense, because heat could warm the seawater and make the fragile glow grow weak",
        ritual_warning="Keep the water cool, or the heat of the stones will dull the living light",
        loss="The water grew warm and the glow shrank low",
        tags={"heat"},
    ),
    "stairs": Hazard(
        id="stairs",
        label="the broken stair",
        verb="the broken stair jolted under each footstep",
        danger_text="The path was all suspense, because one stumble could shake the vessel and spill what had to be retained",
        ritual_warning="Steady your hands, or the broken steps will splash the light away",
        loss="The vessel lurched and the shining water slapped against its sides",
        tags={"stairs"},
    ),
}

VESSELS = {
    "moon_jar": Vessel(
        id="moon_jar",
        label="moon jar",
        phrase="the sealed moon jar",
        watertight=True,
        covered=True,
        steady=True,
        built_in_guards={"wind", "stairs"},
        tags={"jar"},
    ),
    "shell_bowl": Vessel(
        id="shell_bowl",
        label="shell bowl",
        phrase="a deep shell bowl",
        watertight=True,
        covered=False,
        steady=False,
        built_in_guards=set(),
        tags={"shell"},
    ),
    "reed_basket": Vessel(
        id="reed_basket",
        label="reed basket",
        phrase="a woven reed basket lined only with hope",
        watertight=False,
        covered=False,
        steady=False,
        built_in_guards=set(),
        tags={"basket"},
    ),
}

CHARMS = {
    "shell_lid": Charm(
        id="shell_lid",
        label="shell lid",
        phrase="a round shell lid",
        guards={"wind"},
        surprise_text="Just then a white moth settled on the lid and rode with {child} all the way to the shrine, as if the moon had sent a tiny escort.",
        tags={"cover"},
    ),
    "cool_kelp": Charm(
        id="cool_kelp",
        label="cool kelp",
        phrase="cool kelp wrapped in wet moss",
        guards={"heat"},
        surprise_text="Just then the kelp gave off a fresh salt smell, and the vessel cooled in {child}'s hands as if hidden tidewater still flowed inside it.",
        tags={"cooling"},
    ),
    "sling": Charm(
        id="sling",
        label="carrying sling",
        phrase="a carrying sling of braided cord",
        guards={"stairs"},
        surprise_text="Just then the sling tightened gently on its own, and {child} felt the vessel settle against {child}'s heartbeat instead of bouncing from step to step.",
        tags={"steady"},
    ),
    "prayer_thread": Charm(
        id="prayer_thread",
        label="prayer thread",
        phrase="a silver prayer thread",
        guards=set(),
        surprise_text="",
        tags={"prayer"},
    ),
}

OFFERINGS = {
    "moon_song": Offering(
        id="moon_song",
        label="moon song",
        phrase="the old moon song",
        moon_favor=True,
        end_text="At that sound the basin rose in a ring of light, and tiny fish-shapes leapt from it before melting back into stars",
        tags={"song"},
    ),
    "white_pearl": Offering(
        id="white_pearl",
        label="white pearl",
        phrase="a white pearl",
        moon_favor=True,
        end_text="The pearl flashed once like an extra moon, and the plankton spun around it in a bright crown",
        tags={"pearl"},
    ),
    "honey_cake": Offering(
        id="honey_cake",
        label="honey cake",
        phrase="a little honey cake",
        moon_favor=False,
        end_text="",
        tags={"gift"},
    ),
}

GIRL_NAMES = ["Neri", "Sela", "Iria", "Mira", "Tali", "Luma", "Ena", "Riva"]
BOY_NAMES = ["Taren", "Ivo", "Maro", "Soren", "Niko", "Pavel", "Rian", "Toma"]
TRAITS = ["careful", "quiet", "brave", "watchful", "patient"]


@dataclass
class StoryParams:
    shore: str
    hazard: str
    vessel: str
    charm: str
    offering: str
    child_name: str
    child_gender: str
    elder: str
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
    "plankton": [
        (
            "What is plankton?",
            "Plankton are tiny living things that float in water. Some kinds can glow, which is why they can make the sea sparkle at night.",
        )
    ],
    "biolight": [
        (
            "Why can some seawater glow at night?",
            "Some tiny sea creatures make a little light when the water moves around them. That is why waves can look bright in the dark.",
        )
    ],
    "wind": [
        (
            "Why is wind a problem when you carry a bowl of water?",
            "Wind can push the water and make it splash out. If the water holds something delicate, losing even a little can matter.",
        )
    ],
    "heat": [
        (
            "Why do living things need the right water and temperature?",
            "Living things do best when their surroundings stay close to what they need. If water gets too warm or too dry, fragile life can weaken.",
        )
    ],
    "stairs": [
        (
            "Why can broken stairs be dangerous when you carry something precious?",
            "Broken stairs can make you stumble or jolt your hands. That can spill or damage the thing you are trying to protect.",
        )
    ],
    "jar": [
        (
            "Why is a sealed jar good for carrying water?",
            "A sealed jar helps keep water from splashing out. It also protects what is inside from wind and bumps.",
        )
    ],
    "shell": [
        (
            "What is a shell bowl?",
            "A shell bowl is a bowl made from a large shell. It can hold water for a while, but an open bowl is easier to spill than a covered jar.",
        )
    ],
    "cover": [
        (
            "Why does a lid help protect water?",
            "A lid helps keep splashes in and gusts out. That makes it easier to retain what is floating in the water.",
        )
    ],
    "cooling": [
        (
            "Why does cool wet wrapping help?",
            "Cool wet wrapping can help keep the inside of a container from warming too fast. That matters when heat is part of the danger.",
        )
    ],
    "steady": [
        (
            "Why would a carrying sling help on stairs?",
            "A sling can hold a container closer and steadier to the body. That means less bouncing and less spilling.",
        )
    ],
    "song": [
        (
            "Why do myths use songs in important moments?",
            "Songs help people remember old promises and rituals. In myths, a song can also show respect to the powers of the world.",
        )
    ],
    "pearl": [
        (
            "Why is a pearl often special in myths?",
            "A pearl comes from the sea and shines softly, so stories often use it as a sign of beauty and blessing. It feels like a treasure made by water itself.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "plankton",
    "biolight",
    "wind",
    "heat",
    "stairs",
    "jar",
    "shell",
    "cover",
    "cooling",
    "steady",
    "song",
    "pearl",
]


CURATED = [
    StoryParams(
        shore="moon_cove",
        hazard="wind",
        vessel="shell_bowl",
        charm="shell_lid",
        offering="moon_song",
        child_name="Neri",
        child_gender="girl",
        elder="grandmother",
        trait="careful",
        seed=1,
    ),
    StoryParams(
        shore="whale_bay",
        hazard="heat",
        vessel="shell_bowl",
        charm="cool_kelp",
        offering="honey_cake",
        child_name="Taren",
        child_gender="boy",
        elder="priestess",
        trait="patient",
        seed=2,
    ),
    StoryParams(
        shore="reef_hollow",
        hazard="stairs",
        vessel="moon_jar",
        charm="prayer_thread",
        offering="white_pearl",
        child_name="Iria",
        child_gender="girl",
        elder="grandfather",
        trait="watchful",
        seed=3,
    ),
    StoryParams(
        shore="moon_cove",
        hazard="heat",
        vessel="reed_basket",
        charm="cool_kelp",
        offering="honey_cake",
        child_name="Maro",
        child_gender="boy",
        elder="priest",
        trait="brave",
        seed=4,
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    shore = f["shore"]
    hazard = f["hazard"]
    vessel = f["vessel_cfg"]
    offering = f["offering"]
    outcome = f["outcome"]
    base = (
        f'Write a short mythic story for a 3-to-5-year-old about a child carrying glowing plankton in {vessel.phrase} up to a shrine at {shore.label}. '
        f'Include the word "retain".'
    )
    if outcome == "blessed":
        return [
            base,
            f"Tell a suspenseful sea-myth where {child.id} protects living plankton from {hazard.label}, and a surprising blessing answers {offering.phrase} at the end.",
            f"Write a gentle myth in which careful hands retain the sea-light through danger, and the ending reveals that the god of the place was listening all along.",
        ]
    if outcome == "bright":
        return [
            base,
            f"Tell a mythic night-climb story where {child.id} keeps the plankton alive through {hazard.label} and brings light home to the boats below.",
            f"Write a story with suspense on a dark path and a calm ending image that proves the child really retained the sea's light.",
        ]
    return [
        base,
        f"Tell a cautionary myth where {child.id} tries to carry living plankton through {hazard.label}, but the wrong way of carrying them lets the light fade.",
        f"Write a sea-myth with suspense and a gentle lesson about caring for small living things the right way.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    shore = f["shore"]
    hazard = f["hazard"]
    vessel_cfg = f["vessel_cfg"]
    charm_cfg = f["charm_cfg"]
    offering = f["offering"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child of {shore.label}, and the village elder who trusted {child.pronoun('object')} with a sacred errand. The story follows {child.pronoun('object')} on one dark climb from the shore to the shrine.",
        ),
        (
            "What was {name} trying to do?".format(name=child.id),
            f"{child.id} was trying to carry living plankton up to the moon basin before moonrise. The child had to retain their seawater and their glow so the harbor lights could shine.",
        ),
        (
            f"Why did {hazard.label} make the climb frightening?",
            f"{hazard.label.capitalize()} threatened the seawater the plankton needed. That made the journey full of suspense, because if the water or glow was lost, the sacred light could fail before reaching the shrine.",
        ),
    ]
    if outcome == "dim":
        qa.append(
            (
                f"Why did the plankton fade?",
                f"They faded because {vessel_cfg.label} could not truly retain the seawater on the climb. Even though {child.id} carried {charm_cfg.label}, the vessel itself let the living light slip away.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The basin stayed dim, and {elder.label_word} gently explained what had gone wrong. The ending is sad but hopeful, because {child.id} learns to care better for living things next time.",
            )
        )
    elif outcome == "bright":
        qa.append(
            (
                f"How did {child.id} keep the plankton safe?",
                f"{child.id} used a way of carrying them that matched the danger from {hazard.label}. Because the seawater and glow were retained, the basin lit up and guided the boats home.",
            )
        )
        qa.append(
            (
                "Was there a surprise at the end?",
                f"There was a quiet kind of surprise: after so much suspense, the small light truly lasted. The proof came when the harbor lamps answered from below and the bay stopped looking afraid.",
            )
        )
    else:
        qa.append(
            (
                f"What was the surprise after {child.id} reached the shrine?",
                f"After all the suspense of the climb, the offering called down an unexpected blessing. The plankton did more than glow; they turned the bay into a shining road and helped every boat find home.",
            )
        )
        qa.append(
            (
                f"Why was the ending special?",
                f"It showed that {child.id} had not only retained the plankton's life but also earned the favor of the holy place. The surprise blessing changed the whole bay, not just the basin on the hill.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"plankton", "biolight"} | set(f["hazard"].tags) | set(f["vessel_cfg"].tags) | set(f["charm_cfg"].tags)
    if f["offering"].moon_favor:
        tags |= set(f["offering"].tags)
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.watertight:
            bits.append("watertight=True")
        if ent.covered:
            bits.append("covered=True")
        if ent.attrs:
            shown = {k: sorted(v) if isinstance(v, set) else v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


def explain_rejection(vessel: Vessel, charm: Charm, hazard: Hazard) -> str:
    if not vessel.watertight:
        return (
            f"(No story: {vessel.label} cannot retain seawater, so the plankton would fade before the shrine. "
            f"Pick a watertight vessel such as the shell bowl or moon jar.)"
        )
    return (
        f"(No story: {charm.label} does not protect against {hazard.label}. "
        f"The child needs a way to guard the plankton from that exact danger.)"
    )


ASP_RULES = r"""
hazard_guarded(V, C, H) :- vessel(V), charm(C), hazard(H), built_guard(V, H).
hazard_guarded(V, C, H) :- vessel(V), charm(C), hazard(H), charm_guard(C, H).

valid(S, V, C, H) :- shore(S), vessel(V), charm(C), hazard(H), watertight(V), hazard_guarded(V, C, H).

bright_outcome(V, C, H) :- valid(_, V, C, H).
blessed_outcome(V, C, H, O) :- valid(_, V, C, H), offering(O), moon_favor(O).
dim_outcome(V, C, H) :- vessel(V), charm(C), hazard(H), not watertight(V).
dim_outcome(V, C, H) :- vessel(V), charm(C), hazard(H), watertight(V), not hazard_guarded(V, C, H).

outcome(dim) :- chosen_vessel(V), chosen_charm(C), chosen_hazard(H), dim_outcome(V, C, H).
outcome(blessed) :- chosen_vessel(V), chosen_charm(C), chosen_hazard(H), chosen_offering(O), blessed_outcome(V, C, H, O).
outcome(bright) :- chosen_vessel(V), chosen_charm(C), chosen_hazard(H), chosen_offering(O), bright_outcome(V, C, H), not moon_favor(O).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SHORES:
        lines.append(asp.fact("shore", sid))
    for vid, vessel in VESSELS.items():
        lines.append(asp.fact("vessel", vid))
        if vessel.watertight:
            lines.append(asp.fact("watertight", vid))
        for h in sorted(vessel.built_in_guards):
            lines.append(asp.fact("built_guard", vid, h))
    for cid, charm in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        for h in sorted(charm.guards):
            lines.append(asp.fact("charm_guard", cid, h))
    for hid in HAZARDS:
        lines.append(asp.fact("hazard", hid))
    for oid, offering in OFFERINGS.items():
        lines.append(asp.fact("offering", oid))
        if offering.moon_favor:
            lines.append(asp.fact("moon_favor", oid))
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
            asp.fact("chosen_vessel", params.vessel),
            asp.fact("chosen_charm", params.charm),
            asp.fact("chosen_hazard", params.hazard),
            asp.fact("chosen_offering", params.offering),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    got = asp.atoms(model, "outcome")
    return got[0][0] if got else "?"


def _smoke_generate() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("smoke test generated an empty story")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        emit(sample, trace=False, qa=True, header="### smoke")
    if "smoke" not in buf.getvalue():
        raise StoryError("smoke test emit() produced unexpected output")


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid combo gate matches ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combo gate:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for case in cases:
        if asp_outcome(case) != outcome_of(case):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        _smoke_generate()
        print("OK: smoke generation and emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic storyworld: a child carries glowing plankton to a hill shrine and tries to retain their light."
    )
    ap.add_argument("--shore", choices=SHORES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--offering", choices=OFFERINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather", "priestess", "priest"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the inline ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.vessel and args.charm and args.hazard:
        vessel = VESSELS[args.vessel]
        charm = CHARMS[args.charm]
        hazard = HAZARDS[args.hazard]
        if not valid_combo(vessel, charm, hazard):
            raise StoryError(explain_rejection(vessel, charm, hazard))

    combos = [
        c
        for c in valid_combos()
        if (args.shore is None or c[0] == args.shore)
        and (args.vessel is None or c[1] == args.vessel)
        and (args.charm is None or c[2] == args.charm)
        and (args.hazard is None or c[3] == args.hazard)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    shore_id, vessel_id, charm_id, hazard_id = rng.choice(sorted(combos))
    offering_id = args.offering or rng.choice(sorted(OFFERINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["grandmother", "grandfather", "priestess", "priest"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        shore=shore_id,
        hazard=hazard_id,
        vessel=vessel_id,
        charm=charm_id,
        offering=offering_id,
        child_name=name,
        child_gender=gender,
        elder=elder,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.shore not in SHORES:
        raise StoryError(f"Unknown shore: {params.shore}")
    if params.hazard not in HAZARDS:
        raise StoryError(f"Unknown hazard: {params.hazard}")
    if params.vessel not in VESSELS:
        raise StoryError(f"Unknown vessel: {params.vessel}")
    if params.charm not in CHARMS:
        raise StoryError(f"Unknown charm: {params.charm}")
    if params.offering not in OFFERINGS:
        raise StoryError(f"Unknown offering: {params.offering}")

    shore = SHORES[params.shore]
    hazard = HAZARDS[params.hazard]
    vessel = VESSELS[params.vessel]
    charm = CHARMS[params.charm]
    offering = OFFERINGS[params.offering]

    world = tell(
        shore=shore,
        hazard=hazard,
        vessel_cfg=vessel,
        charm_cfg=charm,
        offering=offering,
        child_name=params.child_name,
        child_type=params.child_gender,
        elder_type=params.elder,
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
        print(f"{len(combos)} compatible (shore, vessel, charm, hazard) combos:\n")
        for shore, vessel, charm, hazard in combos:
            print(f"  {shore:12} {vessel:11} {charm:13} {hazard}")
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
            header = f"### {p.child_name}: {p.vessel} + {p.charm} against {p.hazard} at {p.shore} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
