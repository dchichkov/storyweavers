#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hypocritical_gospel_teamwork_tall_tale.py
====================================================================

A standalone storyworld about a giant frontier chore told in a playful tall-tale
voice: a boastful town helper talks like the whole gospel of teamwork belongs to
him, then proves himself hypocritical by trying to grab the glory alone. The
load is too big for one person, the job goes crooked, and the town only succeeds
when everyone works together for real.

The world model tracks:
- physical meters: strain, tilt, stuck, moved, steady
- emotional/social memes: pride, embarrassment, trust, resolve, joy

Reasonableness constraint
-------------------------
Not every giant chore is plausible in every place. A hay wagon works on the
prairie road but not on a narrow mountain footbridge; a raft makes sense on the
river but not on dry ground. The storyworld refuses impossible combinations.
Within a valid setting, the chosen gear and number of helpers must also be
strong enough for the chosen load.

Run it
------
    python storyworlds/worlds/gpt-5.4/hypocritical_gospel_teamwork_tall_tale.py
    python storyworlds/worlds/gpt-5.4/hypocritical_gospel_teamwork_tall_tale.py --place riverbank --load organ --gear raft
    python storyworlds/worlds/gpt-5.4/hypocritical_gospel_teamwork_tall_tale.py --place canyon --gear raft
    python storyworlds/worlds/gpt-5.4/hypocritical_gospel_teamwork_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/hypocritical_gospel_teamwork_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/hypocritical_gospel_teamwork_tall_tale.py --verify
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
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


# ---------------------------------------------------------------------------
# Domain configuration
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
class Place:
    id: str
    label: str
    path: str
    horizon: str
    allows: set[str] = field(default_factory=set)
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
class Load:
    id: str
    label: str
    phrase: str
    weight: int
    purpose: str
    opening: str
    ending: str
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
class Gear:
    id: str
    label: str
    phrase: str
    capacity: int
    allows: set[str] = field(default_factory=set)
    action: str = ""
    failure: str = ""
    success: str = ""
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
class Crew:
    id: str
    label: str
    helpers: int
    chant: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
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


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
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


def teamwork_power(world: World) -> int:
    load_cfg: Load = world.facts["load_cfg"]
    gear_cfg: Gear = world.facts["gear_cfg"]
    crew_cfg: Crew = world.facts["crew_cfg"]
    foreman = world.get("foreman")
    joined = foreman.memes["joins_team"] >= THRESHOLD
    helpers = crew_cfg.helpers + (1 if joined else 0)
    return helpers * gear_cfg.capacity


def solo_power(world: World) -> int:
    gear_cfg: Gear = world.facts["gear_cfg"]
    foreman = world.get("foreman")
    return gear_cfg.capacity + int(foreman.memes["brag_strength"])


def _r_solo_strain(world: World) -> list[str]:
    load = world.get("load")
    foreman = world.get("foreman")
    load_cfg: Load = world.facts["load_cfg"]
    if foreman.memes["tries_alone"] < THRESHOLD:
        return []
    sig = ("solo_strain",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if solo_power(world) < load_cfg.weight:
        foreman.meters["strain"] += 1
        load.meters["tilt"] += 1
        load.meters["stuck"] += 1
        return ["__solo_fail__"]
    load.meters["moved"] += 1
    return ["__solo_move__"]


def _r_team_move(world: World) -> list[str]:
    load = world.get("load")
    foreman = world.get("foreman")
    load_cfg: Load = world.facts["load_cfg"]
    if foreman.memes["joins_team"] < THRESHOLD:
        return []
    sig = ("team_move",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if teamwork_power(world) >= load_cfg.weight:
        load.meters["moved"] += 1
        load.meters["steady"] += 1
        foreman.memes["relief"] += 1
        foreman.memes["respect"] += 1
        return ["__team_success__"]
    load.meters["stuck"] += 1
    return ["__team_fail__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="solo_strain", tag="physical", apply=_r_solo_strain),
    Rule(name="team_move", tag="physical", apply=_r_team_move),
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
        for sentence in produced:
            world.say(sentence)
    return produced


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------
def place_supports(place: Place, gear: Gear) -> bool:
    return gear.id in place.allows and place.id in gear.allows


def enough_strength(load: Load, gear: Gear, crew: Crew) -> bool:
    return (crew.helpers + 1) * gear.capacity >= load.weight


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for load_id, load in LOADS.items():
            for gear_id, gear in GEARS.items():
                for crew_id, crew in CREWS.items():
                    if place_supports(place, gear) and enough_strength(load, gear, crew):
                        combos.append((place_id, load_id, gear_id, crew_id))
    return combos


def explain_place_gear(place: Place, gear: Gear) -> str:
    return (
        f"(No story: {gear.phrase} does not make sense on {place.label}. "
        f"The route there is {place.path}, so pick gear that belongs in that place.)"
    )


def explain_strength(load: Load, gear: Gear, crew: Crew) -> str:
    total = (crew.helpers + 1) * gear.capacity
    return (
        f"(No story: {crew.label} with {gear.label} can manage strength {total}, "
        f"but {load.phrase} needs {load.weight}. Pick a lighter load, stronger gear, or a bigger crew.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_solo(world: World) -> dict:
    sim = world.copy()
    sim.get("foreman").memes["tries_alone"] = 1.0
    propagate(sim, narrate=False)
    load = sim.get("load")
    return {
        "tilt": load.meters["tilt"] >= THRESHOLD,
        "stuck": load.meters["stuck"] >= THRESHOLD,
        "moved": load.meters["moved"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def introduce(world: World, foreman: Entity, helper: Entity, place: Place, load: Load) -> None:
    world.say(
        f"Out on {place.label}, where {place.horizon}, the town had a chore so big "
        f"it looked as if it ought to be done by weather instead of people."
    )
    world.say(
        f"They meant to move {load.phrase} {place.path} so the whole town could use it for {load.purpose}."
    )
    world.say(
        f"{load.opening}"
    )
    foreman.memes["pride"] += 1
    helper.memes["trust"] += 1


def brag(world: World, foreman: Entity, helper: Entity, crew: Crew, gear: Gear) -> None:
    foreman.memes["gives_speech"] += 1
    world.say(
        f'{foreman.id}, the loudest foreman west of anywhere, slapped {gear.phrase} and cried, '
        f'"Neighbors, I know the whole gospel of teamwork! With {crew.label} and my grand instructions, '
        f'we shall roll this job smooth as butter on a hot biscuit."'
    )
    world.say(
        f"{helper.id} tipped {helper.pronoun('possessive')} hat, ready to help before the dust had even settled."
    )


def hypocrisy_warning(world: World, helper: Entity, load: Load, place: Place) -> None:
    pred = predict_solo(world)
    world.facts["predicted_solo_tilt"] = pred["tilt"]
    helper.memes["doubt"] += 1
    extra = "lean crooked as a sleepy fence" if pred["tilt"] else "fight back"
    world.say(
        f'"Then let us all put our shoulders to it," said {helper.id}. '
        f'"Because if one person grabs all the glory alone, {load.label} will {extra} on {place.path}."'
    )


def turn_hypocritical(world: World, foreman: Entity, helper: Entity) -> None:
    foreman.memes["tries_alone"] += 1
    foreman.memes["hypocrisy"] += 1
    helper.memes["embarrassment"] += 1
    world.say(
        f"But {foreman.id} puffed up bigger than a parade balloon. "
        f'"Stand back," {foreman.pronoun()} boomed. "I will show you how a master does it."'
    )
    world.say(
        f"And that was downright hypocritical, because a moment earlier {foreman.pronoun()} had been preaching teamwork to everybody else."
    )


def solo_mishap(world: World, foreman: Entity, load: Load, gear: Gear, place: Place) -> None:
    propagate(world, narrate=False)
    if world.get("load").meters["moved"] >= THRESHOLD:
        world.say(
            f"By pure tall-tale luck, {foreman.id} gave {gear.phrase} such a yank that {load.label} hopped forward once."
        )
        return
    foreman.memes["embarrassment"] += 1
    world.say(
        f"{foreman.id} heaved on {gear.phrase}. The earth grunted back. "
        f"{load.label.capitalize()} lurched, tilted, and stuck halfway across {place.path} like a biscuit in a bottle."
    )
    world.say(
        f"{foreman.pronoun().capitalize()} slid through the dust, boots first, while the whole town stared with round eyes."
    )


def invitation(world: World, helper: Entity, crew: Crew) -> None:
    helper.memes["resolve"] += 1
    world.say(
        f'{helper.id} did not laugh. {helper.pronoun().capitalize()} cupped {helper.pronoun("possessive")} hands and called, '
        f'"{crew.chant}! If the job is for everybody, the pull should be too."'
    )


def join_team(world: World, foreman: Entity, helper: Entity) -> None:
    foreman.memes["joins_team"] += 1
    foreman.memes["pride"] = 0.0
    foreman.memes["honesty"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"{foreman.id} spat out a mouthful of dust, looked at the crooked load, and finally nodded."
    )
    world.say(
        f'"You were right," {foreman.pronoun()} told {helper.id}. "A speech is easy. A pull is harder. '
        f'Let me take hold with the rest of you."'
    )


def team_success(world: World, foreman: Entity, helper: Entity, place: Place, load: Load, gear: Gear, crew: Crew) -> None:
    propagate(world, narrate=False)
    if world.get("load").meters["steady"] < THRESHOLD or world.get("load").meters["moved"] < THRESHOLD:
        raise StoryError("(Internal story error: the team ending did not succeed in simulation.)")
    foreman.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"So they gripped {gear.phrase} together: {crew.label}, {helper.id}, and even {foreman.id} with no room left for bragging."
    )
    world.say(
        f"On the count of three, they pulled so steady that the sun seemed to stop and watch. "
        f"{load.label.capitalize()} rolled true along {place.path}, straighter than a preacher's finger and smoother than river glass."
    )
    world.say(
        f"When the job was done, the town cheered, not for the loudest voice, but for all the hands that had made one strong pair after another."
    )
    world.say(
        f"{load.ending}"
    )


def record_facts(world: World, outcome: str) -> None:
    world.facts["outcome"] = outcome
    world.facts["solo_failed"] = world.get("load").meters["stuck"] >= THRESHOLD
    world.facts["worked_together"] = world.get("foreman").memes["joins_team"] >= THRESHOLD


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
def tell(
    place: Place,
    load_cfg: Load,
    gear_cfg: Gear,
    crew_cfg: Crew,
    foreman_name: str = "Buck",
    foreman_type: str = "man",
    helper_name: str = "Mollie",
    helper_type: str = "woman",
) -> World:
    world = World()
    world.facts.update(
        place=place,
        load_cfg=load_cfg,
        gear_cfg=gear_cfg,
        crew_cfg=crew_cfg,
    )

    foreman = world.add(Entity(
        id=foreman_name,
        kind="character",
        type=foreman_type,
        label=foreman_name,
        role="foreman",
        traits=["boastful"],
        attrs={},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        label=helper_name,
        role="helper",
        traits=["steady"],
        attrs={},
    ))
    load = world.add(Entity(
        id="load",
        kind="thing",
        type="load",
        label=load_cfg.label,
        attrs={},
    ))
    rig = world.add(Entity(
        id="gear",
        kind="thing",
        type="gear",
        label=gear_cfg.label,
        attrs={},
    ))

    foreman.memes["brag_strength"] = 0.0
    foreman.memes["tries_alone"] = 0.0
    foreman.memes["joins_team"] = 0.0
    load.meters["tilt"] = 0.0
    load.meters["stuck"] = 0.0
    load.meters["moved"] = 0.0
    load.meters["steady"] = 0.0

    introduce(world, foreman, helper, place, load_cfg)
    brag(world, foreman, helper, crew_cfg, gear_cfg)

    world.para()
    hypocrisy_warning(world, helper, load_cfg, place)
    turn_hypocritical(world, foreman, helper)
    solo_mishap(world, foreman, load_cfg, gear_cfg, place)

    world.para()
    invitation(world, helper, crew_cfg)
    join_team(world, foreman, helper)
    team_success(world, foreman, helper, place, load_cfg, gear_cfg, crew_cfg)

    world.facts.update(
        foreman=foreman,
        helper=helper,
        load=load,
        rig=rig,
    )
    record_facts(world, "teamwork")
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "prairie": Place(
        id="prairie",
        label="the open prairie",
        path="over the long wagon road",
        horizon="the grass bent in waves clear to next Tuesday",
        allows={"wagon", "rollers"},
        tags={"prairie"},
    ),
    "riverbank": Place(
        id="riverbank",
        label="the broad riverbank",
        path="across the slow shining river",
        horizon="the water flashed like a sheet of nickels under the sky",
        allows={"raft", "rollers"},
        tags={"river"},
    ),
    "canyon": Place(
        id="canyon",
        label="the red canyon rim",
        path="over the narrow footbridge",
        horizon="the cliffs stood up so high they seemed to hold the clouds by the suspenders",
        allows={"rollers"},
        tags={"canyon"},
    ),
}

LOADS = {
    "bell": Load(
        id="bell",
        label="the bell",
        phrase="a gospel bell so big it could ring freckles onto a trout",
        weight=8,
        purpose="Sunday singing on the hill",
        opening="Folks said one peal from that bell could shake dust from a mile of fence posts.",
        ending="By sunset the gospel bell hung high, and its first note rolled over the town like warm bread smell.",
        tags={"bell", "gospel"},
    ),
    "organ": Load(
        id="organ",
        label="the organ",
        phrase="an organ with pipes tall enough to comb the clouds",
        weight=10,
        purpose="the town's gospel jamboree",
        opening="The old organ was said to wheeze so mighty that sparrows kept time in the rafters.",
        ending="At dusk the organ stood in place, and every note of the gospel song sounded bigger than the river.",
        tags={"organ", "gospel"},
    ),
    "water_tub": Load(
        id="water_tub",
        label="the cedar tub",
        phrase="a cedar tub large enough to bathe a team of mules side by side",
        weight=6,
        purpose="the supper after the singing",
        opening="That tub had served beans, washwater, and one famous watermelon all in the same summer.",
        ending="Soon the great cedar tub sat ready, and the supper steam climbed into the sky like a happy ghost.",
        tags={"tub", "supper"},
    ),
}

GEARS = {
    "wagon": Gear(
        id="wagon",
        label="hay wagon",
        phrase="the hay wagon",
        capacity=2,
        allows={"prairie"},
        action="rolled",
        failure="buckled on the rough edge",
        success="rumbled steady",
        tags={"wagon"},
    ),
    "raft": Gear(
        id="raft",
        label="log raft",
        phrase="the log raft",
        capacity=3,
        allows={"riverbank"},
        action="floated",
        failure="yawed sideways",
        success="glided square",
        tags={"raft"},
    ),
    "rollers": Gear(
        id="rollers",
        label="cottonwood rollers",
        phrase="the cottonwood rollers and ropes",
        capacity=2,
        allows={"prairie", "riverbank", "canyon"},
        action="creaked",
        failure="skidded crooked",
        success="creaked true",
        tags={"rollers"},
    ),
}

CREWS = {
    "quartet": Crew(
        id="quartet",
        label="four singing neighbors",
        helpers=4,
        chant="One pull, all pull",
        tags={"small_crew"},
    ),
    "choir": Crew(
        id="choir",
        label="six choir folks",
        helpers=6,
        chant="Heave in harmony",
        tags={"medium_crew", "gospel"},
    ),
    "whole_town": Crew(
        id="whole_town",
        label="eight stout townspeople",
        helpers=8,
        chant="Many hands, one road",
        tags={"big_crew"},
    ),
}

NAMES_MALE = ["Buck", "Jed", "Hank", "Wes", "Eli", "Cal"]
NAMES_FEMALE = ["Mollie", "June", "Pearl", "Ada", "Rose", "Mae"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    load: str
    gear: str
    crew: str
    foreman_name: str
    foreman_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
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
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when people help each other on the same job instead of each person trying to do everything alone. Sharing the work can make a big hard job possible."
        )
    ],
    "hypocritical": [
        (
            "What does hypocritical mean?",
            "Hypocritical means telling other people to follow a rule while you do not follow it yourself. In a story, a hypocritical person says one thing but acts the opposite way."
        )
    ],
    "gospel": [
        (
            "What is gospel singing?",
            "Gospel singing is a kind of joyful singing that people often do together. Many voices joining can sound warm, strong, and hopeful."
        )
    ],
    "wagon": [
        (
            "What is a wagon for?",
            "A wagon is a strong cart with wheels for carrying heavy things over land. It helps people move loads that would be hard to drag by hand."
        )
    ],
    "raft": [
        (
            "What is a raft?",
            "A raft is a floating platform, often made from logs or boards tied together. People can use it to carry things across water."
        )
    ],
    "rollers": [
        (
            "How do rollers help move something heavy?",
            "Round rollers let a heavy thing roll forward instead of scraping across the ground. That lowers the drag, so many people pulling together can move it more easily."
        )
    ],
    "bell": [
        (
            "What does a bell do?",
            "A bell makes a loud ringing sound when it swings and strikes. People use bells to call others together or mark an important time."
        )
    ],
    "organ": [
        (
            "What is an organ?",
            "An organ is a large musical instrument that pushes air through pipes to make sound. Big organs can fill a whole room with music."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    place: Place = world.facts["place"]
    load_cfg: Load = world.facts["load_cfg"]
    crew_cfg: Crew = world.facts["crew_cfg"]
    foreman: Entity = world.facts["foreman"]
    helper: Entity = world.facts["helper"]
    return [
        f'Write a tall tale for a young child that includes the words "hypocritical" and "gospel" and ends by praising teamwork.',
        f"Tell a frontier story where {foreman.id} boasts about teamwork, acts hypocritical by trying to do a giant job alone, and then joins {crew_cfg.label} to move {load_cfg.label} at {place.label}.",
        f"Write a playful exaggerated story where a helper named {helper.id} reminds everyone that big jobs for the whole town should be done together, not by the loudest bragger.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    place: Place = world.facts["place"]
    load_cfg: Load = world.facts["load_cfg"]
    gear_cfg: Gear = world.facts["gear_cfg"]
    crew_cfg: Crew = world.facts["crew_cfg"]
    foreman: Entity = world.facts["foreman"]
    helper: Entity = world.facts["helper"]
    solo_failed = world.facts["solo_failed"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {foreman.id}, a bragging foreman, and {helper.id}, the steady helper who keeps the town focused on working together."
        ),
        (
            f"What huge job did the town need to do?",
            f"They needed to move {load_cfg.phrase} {place.path}. The town wanted it there for {load_cfg.purpose}."
        ),
        (
            f"Why was {foreman.id} called hypocritical?",
            f"{foreman.id} talked about the gospel of teamwork, but then tried to take the whole job and the whole glory alone. That was hypocritical because {foreman.pronoun()} preached one rule and acted the opposite way."
        ),
    ]
    if solo_failed:
        qa.append(
            (
                f"What happened when {foreman.id} tried to do the job alone?",
                f"The load tilted and stuck instead of moving cleanly. It was too heavy for one person, so the proud solo try made a crooked mess instead of real progress."
            )
        )
    qa.append(
        (
            f"How did the town finally solve the problem?",
            f"{helper.id} called everyone in, and even {foreman.id} admitted the job needed all the hands together. With {crew_cfg.label} using {gear_cfg.phrase}, they pulled steadily and the load moved the right way."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the town cheering for teamwork instead of bragging. The finished job showed that many honest helpers were stronger than one loud voice."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    load_cfg: Load = world.facts["load_cfg"]
    gear_cfg: Gear = world.facts["gear_cfg"]
    tags = {"teamwork", "hypocritical"} | set(load_cfg.tags) | set(gear_cfg.tags)
    out: list[tuple[str, str]] = []
    order = ["teamwork", "hypocritical", "gospel", "wagon", "raft", "rollers", "bell", "organ"]
    for tag in order:
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place_supports(P,G) :- allows(P,G), gear_allows(G,P).
enough_strength(L,G,C) :- load(L), gear(G), crew(C),
                          weight(L,W), capacity(G,Cap), helpers(C,H),
                          Cap*(H+1) >= W.
valid(P,L,G,C) :- place(P), load(L), gear(G), crew(C),
                  place_supports(P,G), enough_strength(L,G,C).

solo_fail(L,G) :- weight(L,W), capacity(G,Cap), Cap < W.
team_success(L,G,C) :- weight(L,W), capacity(G,Cap), helpers(C,H), Cap*(H+1) >= W.
outcome(teamwork) :- chosen_load(L), chosen_gear(G), chosen_crew(C), team_success(L,G,C).

#show valid/4.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for gear_id in sorted(place.allows):
            lines.append(asp.fact("allows", place_id, gear_id))
    for load_id, load in LOADS.items():
        lines.append(asp.fact("load", load_id))
        lines.append(asp.fact("weight", load_id, load.weight))
    for gear_id, gear in GEARS.items():
        lines.append(asp.fact("gear", gear_id))
        lines.append(asp.fact("capacity", gear_id, gear.capacity))
        for place_id in sorted(gear.allows):
            lines.append(asp.fact("gear_allows", gear_id, place_id))
    for crew_id, crew in CREWS.items():
        lines.append(asp.fact("crew", crew_id))
        lines.append(asp.fact("helpers", crew_id, crew.helpers))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_load", params.load),
        asp.fact("chosen_gear", params.gear),
        asp.fact("chosen_crew", params.crew),
    ])
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != "teamwork":
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome agrees on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} ASP outcomes were unexpected.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: generate() smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="prairie",
        load="bell",
        gear="wagon",
        crew="quartet",
        foreman_name="Buck",
        foreman_type="man",
        helper_name="Mollie",
        helper_type="woman",
    ),
    StoryParams(
        place="riverbank",
        load="organ",
        gear="raft",
        crew="choir",
        foreman_name="Jed",
        foreman_type="man",
        helper_name="June",
        helper_type="woman",
    ),
    StoryParams(
        place="canyon",
        load="water_tub",
        gear="rollers",
        crew="quartet",
        foreman_name="Hank",
        foreman_type="man",
        helper_name="Ada",
        helper_type="woman",
    ),
    StoryParams(
        place="prairie",
        load="organ",
        gear="rollers",
        crew="whole_town",
        foreman_name="Cal",
        foreman_type="man",
        helper_name="Pearl",
        helper_type="woman",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: a hypocritical boaster learns the real gospel of teamwork."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--load", choices=LOADS)
    ap.add_argument("--gear", choices=GEARS)
    ap.add_argument("--crew", choices=CREWS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = NAMES_FEMALE if gender == "woman" else NAMES_MALE
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.gear:
        place = PLACES[args.place]
        gear = GEARS[args.gear]
        if not place_supports(place, gear):
            raise StoryError(explain_place_gear(place, gear))
    if args.load and args.gear and args.crew:
        load = LOADS[args.load]
        gear = GEARS[args.gear]
        crew = CREWS[args.crew]
        if not enough_strength(load, gear, crew):
            raise StoryError(explain_strength(load, gear, crew))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.load is None or combo[1] == args.load)
        and (args.gear is None or combo[2] == args.gear)
        and (args.crew is None or combo[3] == args.crew)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, load_id, gear_id, crew_id = rng.choice(sorted(combos))
    foreman_type = "man"
    helper_type = "woman"
    foreman_name = _pick_name(rng, foreman_type)
    helper_name = _pick_name(rng, helper_type, avoid=foreman_name)
    return StoryParams(
        place=place_id,
        load=load_id,
        gear=gear_id,
        crew=crew_id,
        foreman_name=foreman_name,
        foreman_type=foreman_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.load not in LOADS:
        raise StoryError(f"(Unknown load: {params.load})")
    if params.gear not in GEARS:
        raise StoryError(f"(Unknown gear: {params.gear})")
    if params.crew not in CREWS:
        raise StoryError(f"(Unknown crew: {params.crew})")

    place = PLACES[params.place]
    load = LOADS[params.load]
    gear = GEARS[params.gear]
    crew = CREWS[params.crew]
    if not place_supports(place, gear):
        raise StoryError(explain_place_gear(place, gear))
    if not enough_strength(load, gear, crew):
        raise StoryError(explain_strength(load, gear, crew))

    world = tell(
        place=place,
        load_cfg=load,
        gear_cfg=gear,
        crew_cfg=crew,
        foreman_name=params.foreman_name,
        foreman_type=params.foreman_type,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, load, gear, crew) combos:\n")
        for place_id, load_id, gear_id, crew_id in combos:
            print(f"  {place_id:10} {load_id:10} {gear_id:8} {crew_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.foreman_name}: {p.load} by {p.gear} at {p.place} with {p.crew}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
