#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bastard_trucker_strength_lesson_learned_happy_ending.py
==================================================================================

A standalone storyworld for a tall-tale-flavored trucking story about bragging,
real strength, and learning to use help the sensible way.

Seed requirements rebuilt as a simulation
-----------------------------------------
This world always includes the words "bastard", "trucker", and "strength".
The story is a tall tale: the trucker boasts bigger than life, the cargo is
impossibly grand, and the road trouble is exaggerated. But the causal lesson is
grounded: brute force alone is not the best answer when a heavy load gets stuck.
Real strength means slowing down, using the right tool, and letting a helper
lend a hand.

Run it
------
    python storyworlds/worlds/gpt-5.4/bastard_trucker_strength_lesson_learned_happy_ending.py
    python storyworlds/worlds/gpt-5.4/bastard_trucker_strength_lesson_learned_happy_ending.py --cargo jars --obstacle loading_step
    python storyworlds/worlds/gpt-5.4/bastard_trucker_strength_lesson_learned_happy_ending.py --aid brute_yank
    python storyworlds/worlds/gpt-5.4/bastard_trucker_strength_lesson_learned_happy_ending.py --all --qa
    python storyworlds/worlds/gpt-5.4/bastard_trucker_strength_lesson_learned_happy_ending.py --verify
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Cargo:
    id: str
    label: str
    phrase: str
    weight: int
    delicate: int
    destination: str
    image: str
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
class Obstacle:
    id: str
    label: str
    scene: str
    need_force: int
    need_steady: int
    risk_text: str
    solved_text: str
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
class Aid:
    id: str
    label: str
    force: int
    steady: int
    sense: int
    apply_text: str
    qa_text: str
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
class HelperRole:
    id: str
    label: str
    authority: int
    line: str
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    cargo = world.get("cargo")
    if cargo.meters["wobble"] >= THRESHOLD and ("wobble", "cargo") not in world.fired:
        world.fired.add(("wobble", "cargo"))
        cargo.meters["danger"] += 1
        world.get("helper").memes["alarm"] += 1
        out.append("__wobble__")
    return out


def _r_delivered(world: World) -> list[str]:
    out: list[str] = []
    truck = world.get("truck")
    if truck.meters["rolling"] >= THRESHOLD and ("delivered", "truck") not in world.fired:
        world.fired.add(("delivered", "truck"))
        world.get("trucker").memes["relief"] += 1
        world.get("helper").memes["joy"] += 1
        world.get("cargo").meters["delivered"] += 1
        out.append("__delivered__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="delivered", tag="physical", apply=_r_delivered),
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


def required_steady(cargo: Cargo, obstacle: Obstacle) -> int:
    return max(cargo.delicate, obstacle.need_steady)


def valid_combo(cargo: Cargo, obstacle: Obstacle, aid: Aid) -> bool:
    return aid.force >= obstacle.need_force and aid.steady >= required_steady(cargo, obstacle)


def sensible_aids() -> list[Aid]:
    return [aid for aid in AIDS.values() if aid.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for cargo_id, cargo in CARGOS.items():
        for obstacle_id, obstacle in OBSTACLES.items():
            for aid_id, aid in AIDS.items():
                if aid.sense >= SENSE_MIN and valid_combo(cargo, obstacle, aid):
                    combos.append((cargo_id, obstacle_id, aid_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    helper = HELPERS[params.helper_role]
    return "learned_fast" if helper.authority > params.pride else "learned_after_scare"


def predict_bruteforce(world: World, cargo: Cargo) -> dict:
    sim = world.copy()
    trucker = sim.get("trucker")
    cargo_ent = sim.get("cargo")
    helper = sim.get("helper")
    trucker.meters["strain"] += 1
    trucker.memes["pride"] += 1
    cargo_ent.meters["wobble"] += 1
    helper.memes["worry"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": cargo_ent.meters["wobble"] >= THRESHOLD,
        "danger": cargo_ent.meters["danger"],
        "strain": trucker.meters["strain"],
    }


def introduce(world: World, trucker: Entity, helper: Entity, cargo: Cargo) -> None:
    trucker.memes["joy"] += 1
    world.say(
        f"{trucker.id} was the kind of trucker tall tales grow around. "
        f"Folks said {trucker.pronoun()} once backed a rattling rig between two fence posts "
        f"while whistling through {trucker.pronoun('possessive')} teeth."
    )
    world.say(
        f"That morning {trucker.pronoun()} was hauling {cargo.phrase} toward {cargo.destination}, "
        f"and the load looked so enormous it seemed to nudge clouds out of the sky."
    )
    world.say(
        f"Beside {trucker.pronoun('object')} rode {helper.id}, {HELPERS[helper.attrs['helper_role']].label}, "
        f"who knew ropes, wheels, and weather better than some folks know their own kitchens."
    )


def boast(world: World, trucker: Entity, cargo: Cargo) -> None:
    world.say(
        f'"I have enough strength to tug the moon into a lower orbit if I set my boots right," '
        f'{trucker.id} said. "{cargo.label.capitalize()} will not keep me waiting."'
    )
    world.say(
        'Across the cab hung an old iron pry bar with the rude shop nickname "the bastard bar," '
        "and just seeing it made the trucker grin as if brute force were already a plan."
    )


def road_trouble(world: World, trucker: Entity, cargo: Cargo, obstacle: Obstacle) -> None:
    truck = world.get("truck")
    cargo_ent = world.get("cargo")
    truck.meters["stuck"] = 1.0
    cargo_ent.meters["loaded"] = 1.0
    world.say(
        f"But at {obstacle.scene}, the whole rig lurched and stopped. "
        f"The wheels bit deep, the chains sang tight, and {cargo.the if False else cargo.label} "
        f"gave one long unhappy shiver."
    )
    world.say(
        f"The trouble was {obstacle.label}: {obstacle.risk_text}."
    )


def helper_warning(world: World, trucker: Entity, helper: Entity, cargo: Cargo, obstacle: Obstacle, aid: Aid) -> None:
    pred = predict_bruteforce(world, cargo)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_strain"] = pred["strain"]
    helper.memes["care"] += 1
    extra = "That load will wobble and maybe crack." if cargo.delicate >= 2 else "You will only make the load buck harder."
    world.say(
        f'{helper.id} squinted at the wheels, the load, and the slope. "{HELPERS[helper.attrs["helper_role"]].line} '
        f'If you muscle it wrong, {extra} Use {aid.label} instead."'
    )


def listen_early(world: World, trucker: Entity, helper: Entity) -> None:
    trucker.memes["humility"] += 1
    trucker.memes["pride"] = max(0.0, trucker.memes["pride"] - 1.0)
    helper.memes["trust"] += 1
    world.say(
        f"For once, {trucker.id} did not answer with a brag. "
        f"{trucker.pronoun().capitalize()} tipped {trucker.pronoun('possessive')} hat, looked at the slant of the load again, "
        f"and let the good advice settle in."
    )
    world.say(
        f'"Maybe real strength is knowing when not to yank first," {trucker.pronoun()} admitted.'
    )


def brute_try(world: World, trucker: Entity, helper: Entity, cargo: Cargo) -> None:
    trucker.meters["strain"] += 1
    trucker.memes["pride"] += 1
    trucker.memes["defiance"] += 1
    helper.memes["worry"] += 1
    cargo_ent = world.get("cargo")
    cargo_ent.meters["wobble"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But pride reached the pedals before sense did. {trucker.id} jumped down, planted {trucker.pronoun('possessive')} boots, "
        "and heaved on the bastard bar as if the road owed money."
    )
    world.say(
        f"The truck groaned, {cargo.label} rocked side to side, and even the crows on the fence posts "
        f"leaned away from the fuss."
    )


def scare_and_learn(world: World, trucker: Entity, helper: Entity, cargo: Cargo) -> None:
    trucker.memes["humility"] += 1
    trucker.memes["pride"] = 0.0
    helper.memes["trust"] += 1
    cargo_ent = world.get("cargo")
    if cargo_ent.meters["danger"] >= THRESHOLD:
        world.say(
            f'When {cargo.label} wobbled high enough to make sunlight flash under one edge, '
            f'{trucker.id} let go at once. "{trucker.pronoun().capitalize()}h," {trucker.pronoun()} said softly. '
            f'"That was foolish strength."'
        )
    else:
        world.say(
            f'{trucker.id} heard the load creak and stepped back. '
            f'"That is enough showing off for one day," {trucker.pronoun()} muttered.'
        )
    world.say(
        f'{helper.id} did not laugh. {helper.pronoun().capitalize()} only handed {trucker.pronoun("object")} the good plan again, '
        "which made the lesson easier to take."
    )


def apply_aid(world: World, trucker: Entity, helper: Entity, cargo: Cargo, obstacle: Obstacle, aid: Aid) -> None:
    truck = world.get("truck")
    cargo_ent = world.get("cargo")
    truck.meters["stuck"] = 0.0
    truck.meters["rolling"] += 1
    cargo_ent.meters["stable"] += 1
    cargo_ent.meters["wobble"] = 0.0
    cargo_ent.meters["danger"] = 0.0
    helper.memes["joy"] += 1
    trucker.memes["relief"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the two of them set to work the sensible way. {aid.apply_text}."
    )
    world.say(
        f"The load came free so smooth it seemed the road had changed its mind. "
        f"{obstacle.solved_text}"
    )


def arrive_and_lesson(world: World, trucker: Entity, helper: Entity, cargo: Cargo, obstacle: Obstacle, aid: Aid) -> None:
    trucker.memes["lesson"] += 1
    helper.memes["pride_in_friend"] += 1
    world.say(
        f"By sunset the truck rolled into {cargo.destination}, and people came out smiling at the sight of {cargo.image}."
    )
    world.say(
        f'{trucker.id} swung down from the cab and told everyone, "A trucker may brag about strength all morning, '
        f'but the road teaches better manners by afternoon. The right tool and a steady helper beat foolish yanking every time."'
    )
    world.say(
        f"{helper.id} laughed, the load arrived safe, and the evening ended with lanterns glowing on the truck's polished fenders."
    )


def tell(
    cargo: Cargo,
    obstacle: Obstacle,
    aid: Aid,
    helper_role: HelperRole,
    trucker_name: str = "Hank",
    trucker_gender: str = "man",
    helper_name: str = "May",
    helper_gender: str = "woman",
    pride: int = 4,
) -> World:
    world = World()
    trucker = world.add(Entity(
        id=trucker_name,
        kind="character",
        type=trucker_gender,
        label="the trucker",
        role="trucker",
        attrs={},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        label=helper_role.label,
        role="helper",
        attrs={"helper_role": helper_role.id},
    ))
    truck = world.add(Entity(
        id="truck",
        kind="thing",
        type="truck",
        label="truck",
    ))
    cargo_ent = world.add(Entity(
        id="cargo",
        kind="thing",
        type="cargo",
        label=cargo.label,
    ))

    trucker.memes["pride"] = float(pride)
    trucker.memes["humility"] = 0.0
    trucker.meters["strain"] = 0.0
    helper.memes["care"] = 0.0
    helper.memes["worry"] = 0.0
    helper.memes["joy"] = 0.0
    cargo_ent.meters["wobble"] = 0.0
    cargo_ent.meters["danger"] = 0.0
    truck.meters["stuck"] = 0.0
    truck.meters["rolling"] = 0.0

    introduce(world, trucker, helper, cargo)
    boast(world, trucker, cargo)

    world.para()
    road_trouble(world, trucker, cargo, obstacle)
    helper_warning(world, trucker, helper, cargo, obstacle, aid)

    world.para()
    if helper_role.authority > pride:
        listen_early(world, trucker, helper)
        learned = "learned_fast"
    else:
        brute_try(world, trucker, helper, cargo)
        scare_and_learn(world, trucker, helper, cargo)
        learned = "learned_after_scare"

    world.para()
    apply_aid(world, trucker, helper, cargo, obstacle, aid)
    arrive_and_lesson(world, trucker, helper, cargo, obstacle, aid)

    world.facts.update(
        cargo_cfg=cargo,
        obstacle_cfg=obstacle,
        aid_cfg=aid,
        helper_role=helper_role,
        trucker=trucker,
        helper=helper,
        truck=truck,
        cargo=cargo_ent,
        outcome=learned,
        pride=pride,
        required_force=obstacle.need_force,
        required_steady=required_steady(cargo, obstacle),
        used_bruteforce=learned == "learned_after_scare",
        delivered=cargo_ent.meters["delivered"] >= THRESHOLD,
    )
    return world


CARGOS = {
    "pumpkin": Cargo(
        id="pumpkin",
        label="pumpkin",
        phrase="a county-fair pumpkin as big as a porch swing",
        weight=2,
        delicate=1,
        destination="the county fair",
        image="that grand orange pumpkin gleaming like a second sunset",
        tags={"pumpkin", "heavy_load"},
    ),
    "jars": Cargo(
        id="jars",
        label="glass jars of peach jam",
        phrase="a tower of glass jars of peach jam wrapped in straw",
        weight=1,
        delicate=2,
        destination="the Saturday market",
        image="rows of peach jam shining amber in the last light",
        tags={"jars", "fragile_load"},
    ),
    "bell": Cargo(
        id="bell",
        label="brass bell",
        phrase="a brass bell wide enough to ring noon across three counties",
        weight=3,
        delicate=0,
        destination="the church picnic grounds",
        image="the giant brass bell catching the sunset in one bright curve",
        tags={"bell", "heavy_load"},
    ),
}

OBSTACLES = {
    "mud_rut": Obstacle(
        id="mud_rut",
        label="a mud rut deep as a washtub",
        scene="a clay road by a hay field",
        need_force=2,
        need_steady=1,
        risk_text="one wheel had sunk so far that the axle nearly kissed the mud",
        solved_text="The tires climbed out clean, leaving only one broad ripple in the clay.",
        tags={"mud", "road_trouble"},
    ),
    "creek_bank": Obstacle(
        id="creek_bank",
        label="a washed creek bank slick as soap",
        scene="the low crossing where the creek had eaten the shoulder away",
        need_force=3,
        need_steady=1,
        risk_text="the rear wheels had nothing under them but slick dirt and bragging room",
        solved_text="The truck eased up the bank in one patient pull, not one foolish leap.",
        tags={"creek", "road_trouble"},
    ),
    "loading_step": Obstacle(
        id="loading_step",
        label="a loading step high as a mule's shoulder",
        scene="the old warehouse lane",
        need_force=2,
        need_steady=2,
        risk_text="the crate had to rise level or the whole load would lurch sideways",
        solved_text="The cargo slid up level and easy, as neat as a spoon slipping into soup.",
        tags={"loading", "road_trouble"},
    ),
}

AIDS = {
    "winch": Aid(
        id="winch",
        label="the hand winch and a patient chain",
        force=3,
        steady=2,
        sense=3,
        apply_text="They set the hand winch, snugged the chain true, and turned it a click at a time",
        qa_text="used the hand winch and a patient chain",
        tags={"winch", "tool_use"},
    ),
    "ramp": Aid(
        id="ramp",
        label="a plank ramp and wheel chocks",
        force=2,
        steady=2,
        sense=3,
        apply_text="They laid a plank ramp, chocked the wheels, and walked the load forward slow and level",
        qa_text="used a plank ramp and wheel chocks",
        tags={"ramp", "tool_use"},
    ),
    "mules": Aid(
        id="mules",
        label="two calm mules and a tow line",
        force=3,
        steady=1,
        sense=2,
        apply_text="They hitched up two calm mules, kept the line straight, and let steady pulling do the work",
        qa_text="hitched up two calm mules and pulled steadily",
        tags={"mules", "help_use"},
    ),
    "brute_yank": Aid(
        id="brute_yank",
        label="a wild yank with the bastard bar",
        force=1,
        steady=0,
        sense=1,
        apply_text="The trucker tried to solve it with one hard yank",
        qa_text="gave it one hard yank",
        tags={"bragging"},
    ),
}

HELPERS = {
    "mechanic": HelperRole(
        id="mechanic",
        label="the mechanic",
        authority=5,
        line="Easy now. Iron likes patience better than shouting.",
        tags={"mechanic", "helper"},
    ),
    "farmer": HelperRole(
        id="farmer",
        label="the farmer",
        authority=4,
        line="Heavy things move best when they feel steady under them.",
        tags={"farmer", "helper"},
    ),
    "cousin": HelperRole(
        id="cousin",
        label="the cousin",
        authority=2,
        line="You know I trust your hands, but trust a good plan too.",
        tags={"family", "helper"},
    ),
}

TRUCKER_NAMES = ["Hank", "Pearl", "Mabel", "Rex", "June", "Otis", "Dora", "Beau"]
HELPER_NAMES = ["May", "Clem", "Ruth", "Eli", "Dot", "Ned", "Ivy", "Lou"]


KNOWLEDGE = {
    "winch": [(
        "What does a winch do?",
        "A winch pulls heavy things slowly with a rope or chain. Slow pulling gives people more control than one big jerk."
    )],
    "ramp": [(
        "Why is a ramp helpful for a heavy load?",
        "A ramp makes the climb gentler, so a heavy load can move upward without one sudden bump. That keeps the load steadier."
    )],
    "mules": [(
        "Why can steady pulling help more than one hard yank?",
        "Steady pulling spreads the work over time, so the load is less likely to wobble. One hard yank can make heavy things jump the wrong way."
    )],
    "mud": [(
        "Why do truck wheels get stuck in mud?",
        "Mud is soft and slippery, so heavy wheels sink and lose their grip. Then the truck needs traction or a careful pull to move again."
    )],
    "creek": [(
        "Why is a creek bank hard for a truck to climb?",
        "A creek bank can be slick and crumbly, so the tires cannot push well. A careful pull or better support helps the truck climb."
    )],
    "loading": [(
        "Why must a fragile load stay level?",
        "A fragile load can crack if one side jumps or drops. Keeping it level protects what is inside."
    )],
    "tool_use": [(
        "What is the lesson about using the right tool?",
        "The right tool makes a hard job safer and smarter. Being strong is good, but using strength wisely is better."
    )],
    "helper": [(
        "Why is asking for help a kind of strength?",
        "Asking for help shows you care more about solving the problem than showing off. It lets two people make a safer plan together."
    )],
    "tall_tale": [(
        "What is a tall tale?",
        "A tall tale is a story that stretches things bigger and wilder for fun. The lesson inside can still be true even when the details are grand."
    )],
}
KNOWLEDGE_ORDER = ["winch", "ramp", "mules", "mud", "creek", "loading", "tool_use", "helper", "tall_tale"]


@dataclass
class StoryParams:
    cargo: str
    obstacle: str
    aid: str
    helper_role: str
    trucker_name: str
    trucker_gender: str
    helper_name: str
    helper_gender: str
    pride: int = 4
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cargo = f["cargo_cfg"]
    obstacle = f["obstacle_cfg"]
    aid = f["aid_cfg"]
    helper_role = f["helper_role"]
    trucker = f["trucker"]
    if f["outcome"] == "learned_fast":
        turn = "listens before trying anything foolish"
    else:
        turn = "tries brute force first, then learns from the scare"
    return [
        'Write a tall-tale story that includes the words "bastard", "trucker", and "strength", and ends with a lesson learned and a happy ending.',
        f"Tell a tall tale about a trucker named {trucker.id} hauling {cargo.label} who gets stuck at {obstacle.label} and {turn}.",
        f"Write a warm, exaggerated road story where {helper_role.label} helps a proud trucker use {aid.label} so the load reaches {cargo.destination} safely.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    trucker = f["trucker"]
    helper = f["helper"]
    cargo = f["cargo_cfg"]
    obstacle = f["obstacle_cfg"]
    aid = f["aid_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {trucker.id}, a proud trucker, and {helper.id}, the helpful {HELPERS[helper.attrs['helper_role']].label}. Together they were trying to bring {cargo.label} to {cargo.destination}."
        ),
        (
            "What problem stopped the truck?",
            f"The truck got hung up at {obstacle.label}. The trouble mattered because {obstacle.risk_text}, so forcing it the wrong way could make the load wobble."
        ),
        (
            "Why did the helper tell the trucker not to yank first?",
            f"{helper.id} could see that a brute-force pull might make the load wobble and turn the problem worse. The warning came from the shape of the road and from how heavy or delicate the cargo was."
        ),
    ]
    if f["outcome"] == "learned_after_scare":
        qa.append((
            "What made the trucker change his mind?",
            f"When {trucker.id} tried brute force, the load rocked and looked unsafe. That scare showed him that bragging about strength was not the same as solving the problem well."
        ))
    else:
        qa.append((
            "How did the trucker show real strength?",
            f"{trucker.id} showed real strength by listening before anything went wrong. He chose a smart plan instead of trying to prove something with one wild yank."
        ))
    qa.append((
        "How did they solve the problem?",
        f"They {aid.qa_text}. That worked because it gave the truck enough force and enough steadiness for this kind of obstacle."
    ))
    qa.append((
        "What lesson did the trucker learn?",
        f"He learned that real strength includes patience, tools, and help from other people. The happy ending happened because he stopped showing off and started working wisely."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["aid_cfg"].tags) | set(f["obstacle_cfg"].tags) | {"helper", "tall_tale"}
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
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        cargo="pumpkin",
        obstacle="mud_rut",
        aid="ramp",
        helper_role="mechanic",
        trucker_name="Hank",
        trucker_gender="man",
        helper_name="May",
        helper_gender="woman",
        pride=3,
    ),
    StoryParams(
        cargo="jars",
        obstacle="loading_step",
        aid="winch",
        helper_role="farmer",
        trucker_name="Pearl",
        trucker_gender="woman",
        helper_name="Clem",
        helper_gender="man",
        pride=5,
    ),
    StoryParams(
        cargo="bell",
        obstacle="creek_bank",
        aid="mules",
        helper_role="cousin",
        trucker_name="Otis",
        trucker_gender="man",
        helper_name="Ruth",
        helper_gender="woman",
        pride=4,
    ),
    StoryParams(
        cargo="pumpkin",
        obstacle="creek_bank",
        aid="winch",
        helper_role="mechanic",
        trucker_name="June",
        trucker_gender="woman",
        helper_name="Ned",
        helper_gender="man",
        pride=2,
    ),
    StoryParams(
        cargo="bell",
        obstacle="mud_rut",
        aid="winch",
        helper_role="farmer",
        trucker_name="Beau",
        trucker_gender="man",
        helper_name="Ivy",
        helper_gender="woman",
        pride=4,
    ),
]


def explain_combo(cargo: Cargo, obstacle: Obstacle, aid: Aid) -> str:
    need_s = required_steady(cargo, obstacle)
    if aid.force < obstacle.need_force:
        return (
            f"(No story: {aid.label} is not strong enough for {obstacle.label}. "
            f"It gives force {aid.force}, but this problem needs at least {obstacle.need_force}.)"
        )
    if aid.steady < need_s:
        return (
            f"(No story: {aid.label} is too shaky for {cargo.label} at {obstacle.label}. "
            f"It gives steadiness {aid.steady}, but this story needs at least {need_s}.)"
        )
    return "(No story: this combination does not make a reasonable fix.)"


def explain_aid(aid_id: str) -> str:
    aid = AIDS[aid_id]
    return (
        f"(Refusing aid '{aid_id}': it scores too low on common sense "
        f"(sense={aid.sense} < {SENSE_MIN}). This world prefers safer, steadier plans.)"
    )


ASP_RULES = r"""
valid(C,O,A) :-
    cargo(C), obstacle(O), aid(A),
    sense(A,S), sense_min(M), S >= M,
    need_force(O,NF), force(A,F), F >= NF,
    required_steady(C,O,RS), steady(A,ST), ST >= RS.

required_steady(C,O,R1) :- delicate(C,D), need_steady(O,S), D >= S, R1 = D.
required_steady(C,O,R1) :- delicate(C,D), need_steady(O,S), S > D,  R1 = S.

learned_fast :- helper_authority(H), pride(P), H > P.
learned_after_scare :- helper_authority(H), pride(P), H <= P.

outcome(learned_fast) :- learned_fast.
outcome(learned_after_scare) :- learned_after_scare.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cargo_id, cargo in CARGOS.items():
        lines.append(asp.fact("cargo", cargo_id))
        lines.append(asp.fact("delicate", cargo_id, cargo.delicate))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("need_force", obstacle_id, obstacle.need_force))
        lines.append(asp.fact("need_steady", obstacle_id, obstacle.need_steady))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("force", aid_id, aid.force))
        lines.append(asp.fact("steady", aid_id, aid.steady))
        lines.append(asp.fact("sense", aid_id, aid.sense))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper_role", helper_id))
        lines.append(asp.fact("authority", helper_id, helper.authority))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
        asp.fact("helper_authority", HELPERS[params.helper_role].authority),
        asp.fact("pride", params.pride),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: a trucker learns that real strength uses help and the right tool."
    )
    ap.add_argument("--cargo", choices=CARGOS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--helper-role", choices=HELPERS, dest="helper_role")
    ap.add_argument("--pride", type=int, choices=[1, 2, 3, 4, 5, 6])
    ap.add_argument("--trucker-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--trucker-gender", choices=["man", "woman"])
    ap.add_argument("--helper-gender", choices=["man", "woman"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid cargo/obstacle/aid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.aid and AIDS[args.aid].sense < SENSE_MIN:
        raise StoryError(explain_aid(args.aid))
    if args.cargo and args.obstacle and args.aid:
        cargo = CARGOS[args.cargo]
        obstacle = OBSTACLES[args.obstacle]
        aid = AIDS[args.aid]
        if not valid_combo(cargo, obstacle, aid):
            raise StoryError(explain_combo(cargo, obstacle, aid))

    combos = [
        combo for combo in valid_combos()
        if (args.cargo is None or combo[0] == args.cargo)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.aid is None or combo[2] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    cargo_id, obstacle_id, aid_id = rng.choice(sorted(combos))
    helper_role = args.helper_role or rng.choice(sorted(HELPERS))
    pride = args.pride if args.pride is not None else rng.randint(1, 6)
    trucker_gender = args.trucker_gender or rng.choice(["man", "woman"])
    helper_gender = args.helper_gender or rng.choice(["man", "woman"])
    trucker_pool = [n for n in TRUCKER_NAMES if n != args.helper_name]
    helper_pool = [n for n in HELPER_NAMES if n != args.trucker_name]
    trucker_name = args.trucker_name or rng.choice(trucker_pool)
    helper_name = args.helper_name or rng.choice([n for n in helper_pool if n != trucker_name] or helper_pool)
    return StoryParams(
        cargo=cargo_id,
        obstacle=obstacle_id,
        aid=aid_id,
        helper_role=helper_role,
        trucker_name=trucker_name,
        trucker_gender=trucker_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        pride=pride,
    )


def generate(params: StoryParams) -> StorySample:
    if params.cargo not in CARGOS:
        raise StoryError(f"(Unknown cargo: {params.cargo})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")
    if params.helper_role not in HELPERS:
        raise StoryError(f"(Unknown helper role: {params.helper_role})")
    cargo = CARGOS[params.cargo]
    obstacle = OBSTACLES[params.obstacle]
    aid = AIDS[params.aid]
    if aid.sense < SENSE_MIN:
        raise StoryError(explain_aid(params.aid))
    if not valid_combo(cargo, obstacle, aid):
        raise StoryError(explain_combo(cargo, obstacle, aid))

    world = tell(
        cargo=cargo,
        obstacle=obstacle,
        aid=aid,
        helper_role=HELPERS[params.helper_role],
        trucker_name=params.trucker_name,
        trucker_gender=params.trucker_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        pride=params.pride,
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
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: valid_combos matches ASP ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            rc = 1
            print(f"resolve_params unexpectedly failed for seed {seed}")
            continue
        cases.append(p)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(sample, trace=False, qa=False, header="")
        finally:
            sys.stdout = old
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke generation/emit succeeded.")
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
        print(f"{len(combos)} compatible (cargo, obstacle, aid) combos:\n")
        for cargo, obstacle, aid in combos:
            print(f"  {cargo:8} {obstacle:12} {aid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = (
                f"### {p.trucker_name}: {p.cargo} at {p.obstacle} "
                f"({p.aid}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
